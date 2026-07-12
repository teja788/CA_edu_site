"""Filter-series caching (``engine/dataview.py::FilterStore``): parity + call counts.

``_apply_filters`` used to call each filter fn on the truncated visible frame
for every candidate at EVERY rebalance date — recomputing the whole series from
scratch each time (quadratic in run length). ``FilterStore`` now precomputes
the full causal series once per (filter, params, symbol) per run and slices it
at ``now``, mirroring ``SignalStore``. These tests prove:

1. **Parity**: at every date of a run, the cached path returns exactly the
   ``(eligible, to_cash)`` the pre-cache per-date computation returns —
   including warm-up dates where the visible frame is empty (-> False), and
   dates where the regime/eligibility values flip mid-run (so the slice must
   read the value AT ``now``, not the end of the full series).
2. **Call counts**: each (filter, symbol) computes exactly once per run,
   shared across ``dv.at()`` clones; a filter fn is never invoked for a
   symbol whose frame is empty.
3. ``_latest_bool`` semantics are preserved: last value at or before ``now``;
   empty -> False.
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd
from fixtures.synthetic import trading_days

from tradingos.config.schemas import FilterSpec, StrategyConfig, UniverseSpec
from tradingos.core.models import Timeframe
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.engine.event.strategy_runtime import _apply_filters, _latest_bool
from tradingos.strategies.registry import get_filter, register_filter

_INDEX = "NIFTYTEST"
_CLOSE = pd.Timedelta(hours=15, minutes=30)


def _frame(dates: pd.DatetimeIndex, closes: list[float]) -> pd.DataFrame:
    assert len(dates) == len(closes)
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
            "volume": [1_000_000] * len(dates),
        },
        index=dates,
    )


def _config(filters: list[FilterSpec], symbols: list[str]) -> StrategyConfig:
    return StrategyConfig(
        name="filter-store-test",
        start=date(2021, 1, 1),
        end=date(2021, 12, 31),
        capital=1_000_000.0,
        universe=UniverseSpec(symbols=symbols, point_in_time=False),
        filters=filters,
    )


def _apply_filters_direct(
    config: StrategyConfig, dv: DataView, candidates: list[str]
) -> tuple[list[str], bool]:
    """The pre-cache implementation, verbatim: recompute each filter on the
    TRUNCATED visible frame at this date. The reference for parity."""
    eligible = set(candidates)
    for fspec in config.filters:
        params = dict(fspec.params)
        routed = params.pop("symbol", None)
        fdef = get_filter(fspec.name)
        if routed is not None:
            df = dv.history(routed)
            passed = _latest_bool(fdef.fn(df, **params)) if not df.empty else False
            if not passed:
                return [], True
        else:
            for sym in list(eligible):
                df = dv.history(sym)
                ok = _latest_bool(fdef.fn(df, **params)) if not df.empty else False
                if not ok:
                    eligible.discard(sym)
    return sorted(eligible), False


# ---------------------------------------------------------------------------
# 1. parity: cached slice == direct per-date computation, at every date
# ---------------------------------------------------------------------------


def test_cached_filters_match_direct_per_date_computation() -> None:
    dates = trading_days(date(2021, 1, 4), date(2021, 1, 22))  # 15 business days
    n = len(dates)
    # Index rises, then crashes: index_above_ma(window=3) flips True -> False
    # mid-run (plus a False warm-up head under min_periods).
    idx_closes = [100.0 + i for i in range(8)] + [50.0] * (n - 8)
    # BBB starts below the min_price threshold and rises above it mid-run.
    bbb_closes = [8.0 + 0.5 * i for i in range(n)]  # crosses 10.0 at i=4
    data = MarketData(
        {
            _INDEX: _frame(dates, idx_closes),
            "AAA": _frame(dates, [100.0] * n),
            "BBB": _frame(dates, bbb_closes),
        },
        timeframe=Timeframe.DAY,
        snapshot_id="filter-parity",
    )
    config = _config(
        [
            FilterSpec(name="index_above_ma", params={"window": 3, "symbol": _INDEX}),
            FilterSpec(name="min_price", params={"threshold": 10.0}),
        ],
        ["AAA", "BBB"],
    )
    candidates = ["AAA", "BBB"]

    # ONE base DataView for the whole run: at() clones share the filter cache,
    # exactly as both engines drive it.
    base_dv = DataView(data, SignalStore(data), datetime(1970, 1, 1))

    # Include a date BEFORE the first bar: empty visible frame -> False.
    probe_times = [dates[0] - pd.Timedelta(days=1) + _CLOSE] + [t + _CLOSE for t in dates]
    results = []
    for now in probe_times:
        dv = base_dv.at(now.to_pydatetime())
        cached = _apply_filters(config, dv, candidates)
        direct = _apply_filters_direct(config, dv, candidates)
        assert cached == direct, f"filter parity broke at {now}"
        results.append(cached)

    # Guard against a trivially-constant scenario: the run must exercise
    # to_cash in BOTH states and BBB both excluded and included.
    assert any(to_cash for _, to_cash in results)
    assert any(not to_cash for _, to_cash in results)
    assert any(eligible == ["AAA"] for eligible, _ in results)
    assert any(eligible == ["AAA", "BBB"] for eligible, _ in results)


# ---------------------------------------------------------------------------
# 2. call counts: once per (filter, symbol) per run
# ---------------------------------------------------------------------------

_SPY_CALLS: dict[str, int] = {}
_SPY_FRAMES: dict[str, pd.DataFrame] = {}


@register_filter("test_filterstore_spy", description="call-count spy (tests only)")
def _spy_filter(df: pd.DataFrame) -> pd.Series:
    """Constant-True filter (trivially causal — the look-ahead detector suite
    sweeps EVERY registered filter, this one included) that counts calls per
    known frame. Frames it does not recognise (e.g. the detector's own
    synthetic ones) are passed through uncounted."""
    # MarketData owns defensive copies, so identify the corresponding fixture
    # by value rather than relying on caller-frame object identity.
    sym = next((s for s, f in _SPY_FRAMES.items() if f.equals(df)), None)
    if sym is not None:
        _SPY_CALLS[sym] = _SPY_CALLS.get(sym, 0) + 1
    return pd.Series(True, index=df.index)


def test_each_filter_symbol_pair_computes_exactly_once_per_run() -> None:
    _SPY_CALLS.clear()
    _SPY_FRAMES.clear()
    dates = trading_days(date(2021, 1, 4), date(2021, 1, 15))
    n = len(dates)
    _SPY_FRAMES.update(
        {
            _INDEX: _frame(dates, [100.0] * n),
            "AAA": _frame(dates, [50.0] * n),
            "BBB": _frame(dates, [60.0] * n),
            "CCC": _frame(dates, [70.0] * n),
        }
    )
    data = MarketData(dict(_SPY_FRAMES), timeframe=Timeframe.DAY, snapshot_id="filter-spy")
    config = _config(
        [
            FilterSpec(name="test_filterstore_spy", params={"symbol": _INDEX}),  # regime
            FilterSpec(name="test_filterstore_spy", params={}),  # eligibility
        ],
        ["AAA", "BBB", "CCC"],
    )
    candidates = ["AAA", "BBB", "CCC"]

    base_dv = DataView(data, SignalStore(data), datetime(1970, 1, 1))
    for t in dates:  # many rebalance dates, one run
        dv = base_dv.at((t + _CLOSE).to_pydatetime())
        eligible, to_cash = _apply_filters(config, dv, candidates)
        assert (eligible, to_cash) == (candidates, False)

    # One computation per (filter, symbol) for the whole run — NOT per date.
    assert _SPY_CALLS == {_INDEX: 1, "AAA": 1, "BBB": 1, "CCC": 1}

    # A separate run (fresh DataView) recomputes: the cache is per run.
    dv2 = DataView(data, SignalStore(data), (dates[-1] + _CLOSE).to_pydatetime())
    _apply_filters(config, dv2, candidates)
    assert _SPY_CALLS == {_INDEX: 2, "AAA": 2, "BBB": 2, "CCC": 2}


def test_filter_fn_never_called_on_empty_frame() -> None:
    _SPY_CALLS.clear()
    _SPY_FRAMES.clear()
    dates = trading_days(date(2021, 1, 4), date(2021, 1, 8))
    empty = _frame(pd.DatetimeIndex([]), [])
    _SPY_FRAMES.update({_INDEX: empty, "AAA": _frame(dates, [50.0] * len(dates))})
    data = MarketData(dict(_SPY_FRAMES), timeframe=Timeframe.DAY, snapshot_id="filter-empty")
    config = _config(
        [FilterSpec(name="test_filterstore_spy", params={"symbol": _INDEX})], ["AAA"]
    )

    dv = DataView(data, SignalStore(data), (dates[-1] + _CLOSE).to_pydatetime())
    # Empty routed frame -> regime False -> whole book to cash; fn not invoked.
    assert _apply_filters(config, dv, ["AAA"]) == ([], True)
    assert _SPY_CALLS == {}


# ---------------------------------------------------------------------------
# 3. _latest_bool semantics through the cached slice
# ---------------------------------------------------------------------------


def test_filter_series_slices_at_now_and_empty_is_false() -> None:
    dates = trading_days(date(2021, 1, 4), date(2021, 1, 15))
    n = len(dates)
    closes = [5.0] * 5 + [20.0] * (n - 5)  # crosses min_price threshold at i=5
    data = MarketData(
        {"AAA": _frame(dates, closes)}, timeframe=Timeframe.DAY, snapshot_id="latest-bool"
    )
    base_dv = DataView(data, SignalStore(data), datetime(1970, 1, 1))
    params = {"threshold": 10.0}

    before_first = base_dv.at((dates[0] - pd.Timedelta(days=1) + _CLOSE).to_pydatetime())
    assert _latest_bool(before_first.filter_series("AAA", "min_price", params)) is False

    while_low = base_dv.at((dates[4] + _CLOSE).to_pydatetime())
    s = while_low.filter_series("AAA", "min_price", params)
    assert s.index[-1] == dates[4]  # slice ends AT now, not at the series end
    assert _latest_bool(s) is False

    after_cross = base_dv.at((dates[5] + _CLOSE).to_pydatetime())
    assert _latest_bool(after_cross.filter_series("AAA", "min_price", params)) is True

    # Intraday before the 15:30 close: the day's own bar is not visible yet.
    same_day_open = base_dv.at(datetime.combine(dates[5].date(), datetime.min.time().replace(hour=9, minute=30)))
    assert _latest_bool(same_day_open.filter_series("AAA", "min_price", params)) is False
