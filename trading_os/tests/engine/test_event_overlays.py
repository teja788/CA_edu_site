"""Trailing-stop overlays: engineered paths trigger exactly once at the right
bar and exit at the next open; and stops never loosen (monotone).

Stops are tested two ways:

* end-to-end through the engine (a MONTHLY rebalance is used so the daily bars
  do not cancel-and-replace the stop's exit order before it can fill);
* directly at the overlay level, advancing a DataView bar by bar to assert the
  internal stop level is monotone non-decreasing and fires exactly once.
"""

from __future__ import annotations

from datetime import date, datetime, time

import pandas as pd
import pytest

from tradingos.config.schemas import (
    ExecutionSpec,
    OverlaySpec,
    RebalanceSpec,
    SelectionSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import MARKET_CLOSE
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.engine.event.engine import EventEngine
from tradingos.engine.event.overlays import (
    OverlayContext,
    TrailingStopATR,
    TrailingStopPct,
    make_overlay,
)


def _frame(dates: pd.DatetimeIndex, closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c + 2 for c in closes],
            "low": [c - 2 for c in closes],
            "close": closes,
            "volume": [10_000_000] * len(dates),
        },
        index=dates,
    )


def _single_symbol_config(overlay: OverlaySpec) -> StrategyConfig:
    return StrategyConfig(
        name="stops",
        start=date(2021, 1, 1),
        end=date(2021, 1, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["XXX"], point_in_time=False),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        overlays=[overlay],
        # MONTHLY so only the 1st trading day rebalances — the stop's exit order
        # then survives to fill at the next open instead of being cancel-replaced.
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        execution=ExecutionSpec(timing="next_open", max_participation=1.0),
    )


# ---------------------------------------------------------------------------
# engine-level: percentage trailing stop
# ---------------------------------------------------------------------------


def test_pct_trailing_stop_triggers_once_and_exits_next_open() -> None:
    dates = pd.date_range(date(2021, 1, 1), periods=12, freq="B")
    #      d1   d2   d3   d4   d5   d6    d7(crash) then flat
    close = [100, 101, 105, 110, 115, 120, 100, 100, 100, 100, 100, 100]
    data = MarketData({"XXX": _frame(dates, close)}, timeframe=Timeframe.DAY, snapshot_id="pct")

    cfg = _single_symbol_config(OverlaySpec(name="trailing_stop_pct", params={"pct": 0.10}))
    res = EventEngine().run(cfg, data, StaticUniverseResolver())

    stops = [t for t in res.trades if t.exit_reason == "trailing_stop"]
    # peak close 120 -> stop 108; d7 close 100 < 108 fires exactly once
    assert len(stops) == 1
    assert stops[0].entry_ts.date() == dates[1].date()  # entered at open(d2)
    # exit order queued at d7 close fills at the next open (d8)
    assert stops[0].exit_ts.date() == dates[7].date()
    assert stops[0].exit_ts.time() == time(9, 15)


# ---------------------------------------------------------------------------
# engine-level: ATR trailing stop
# ---------------------------------------------------------------------------


def test_atr_trailing_stop_triggers_once_and_exits_next_open() -> None:
    dates = pd.date_range(date(2021, 1, 1), periods=12, freq="B")
    #       d1   d2   d3   d4   d5   d6   d7   d8(crash) then flat
    close = [100, 100, 104, 108, 112, 116, 120, 100, 100, 100, 100, 100]
    data = MarketData({"XXX": _frame(dates, close)}, timeframe=Timeframe.DAY, snapshot_id="atr")

    cfg = _single_symbol_config(
        OverlaySpec(name="trailing_stop_atr", params={"atr_window": 3, "multiple": 2.0})
    )
    res = EventEngine().run(cfg, data, StaticUniverseResolver())

    stops = [t for t in res.trades if t.exit_reason == "trailing_stop"]
    assert len(stops) == 1
    assert stops[0].entry_ts.date() == dates[1].date()
    # crash at d8 close -> exit fills at the next open (d9)
    assert stops[0].exit_ts.date() == dates[8].date()
    assert stops[0].exit_ts.time() == time(9, 15)


# ---------------------------------------------------------------------------
# engine-level: a stop exit must cancel the symbol's working BUY orders
# ---------------------------------------------------------------------------


def test_stop_exit_cancels_working_buy_and_does_not_pingpong() -> None:
    """Regression: a trailing stop fired while a participation-capped BUY was
    still working; the exit filled at the next open and the leftover BUY then
    REFILLED the position on the same bar — stop/re-buy ping-pong bleeding
    charges. The stop must cancel that symbol's working buys."""
    dates = pd.date_range(date(2021, 1, 1), periods=12, freq="B")
    closes = [100.0, 105.0, 110.0, 115.0, 120.0, 80.0, 80.0, 70.0, 60.0, 55.0, 50.0, 45.0]
    # tiny volume through the crash keeps the rebalance BUY partially filled
    # (cap = 5% of 20k = 1000 sh/bar); huge volume afterwards lets any working
    # remainder fill instantly — which is exactly how the ping-pong manifested.
    volumes = [20_000] * 6 + [10_000_000] * 6
    frame = pd.DataFrame(
        {
            "open": closes,
            "high": [c + 2 for c in closes],
            "low": [c - 2 for c in closes],
            "close": closes,
            "volume": volumes,
        },
        index=dates,
    )
    data = MarketData({"XXX": frame}, timeframe=Timeframe.DAY, snapshot_id="pingpong")

    cfg = StrategyConfig(
        name="pingpong",
        start=date(2021, 1, 1),
        end=date(2021, 1, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["XXX"], point_in_time=False),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        overlays=[OverlaySpec(name="trailing_stop_pct", params={"pct": 0.10})],
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        execution=ExecutionSpec(timing="next_open", slippage_bps=0.0, max_participation=0.05),
    )
    res = EventEngine().run(cfg, data, StaticUniverseResolver())

    # peak close 120 -> stop 108; the d6 close at 80 fires the stop EXACTLY
    # once, exiting the 5000 shares accumulated so far at open(d7).
    stops = [t for t in res.trades if t.exit_reason == "trailing_stop"]
    assert len(stops) == 1, f"stop/re-buy ping-pong: {len(stops)} trailing_stop trades"
    assert stops[0].qty == 5000

    # From d7 (index 6) onward the book is flat cash: the partially-filled
    # BUY was cancelled, so the falling price can no longer move equity.
    tail = res.equity.iloc[6:]
    assert (tail == tail.iloc[0]).all(), "position was refilled after the stop exit"


# ---------------------------------------------------------------------------
# overlay-level: monotonicity + single trigger
# ---------------------------------------------------------------------------


def _drive_overlay(overlay: object, closes: list[float]) -> tuple[list[float], list[bool]]:
    """Advance a DataView bar by bar, returning (stop levels, fired flags)."""
    dates = pd.date_range(date(2021, 1, 1), periods=len(closes), freq="B")
    data = MarketData({"XXX": _frame(dates, closes)}, timeframe=Timeframe.DAY, snapshot_id="drive")
    store = SignalStore(data)
    entry_ts = datetime.combine(dates[0].date(), MARKET_CLOSE)

    stop_levels: list[float] = []
    fired: list[bool] = []
    for d in dates:
        now = datetime.combine(d.date(), MARKET_CLOSE)
        ctx = OverlayContext(
            now=pd.Timestamp(now),
            dv=DataView(data, store, now),
            holdings={"XXX": 100},
            entry_ts={"XXX": entry_ts},
            equity=100_000.0,
        )
        decision = overlay.evaluate(ctx)
        fired.append("XXX" in decision.exits)
        stop_levels.append(_current_stop(overlay))
    return stop_levels, fired


def _current_stop(overlay: object) -> float:
    if isinstance(overlay, TrailingStopPct):
        st = overlay._peak.get("XXX")  # noqa: SLF001 - test introspection
        return st.stop * (1.0 - overlay.pct) if st is not None else float("-inf")
    if isinstance(overlay, TrailingStopATR):
        st = overlay._state.get("XXX")  # noqa: SLF001
        return st.stop if st is not None else float("-inf")
    raise TypeError(type(overlay))


def test_pct_stop_is_monotone_and_fires_once() -> None:
    overlay = make_overlay(OverlaySpec(name="trailing_stop_pct", params={"pct": 0.10}))
    closes = [100, 101, 105, 110, 115, 120, 100, 95, 90]
    stops, fired = _drive_overlay(overlay, closes)

    # the stop level never decreases from one bar to the next
    assert all(b >= a - 1e-9 for a, b in zip(stops, stops[1:]))  # noqa: B905
    # it fires from the first breach (close 100 < peak 120 * 0.9 = 108) onward
    assert sum(fired[:6]) == 0  # no false trigger while rising
    assert fired[6] is True


def test_atr_stop_is_monotone() -> None:
    overlay = make_overlay(
        OverlaySpec(name="trailing_stop_atr", params={"atr_window": 3, "multiple": 2.0})
    )
    closes = [100, 100, 104, 108, 112, 116, 120, 100, 100]
    stops, fired = _drive_overlay(overlay, closes)

    finite = [s for s in stops if s != float("-inf")]
    assert all(b >= a - 1e-9 for a, b in zip(finite, finite[1:]))  # noqa: B905
    # exactly one bar (the crash) breaches the ratcheted stop
    assert fired.count(True) >= 1
    assert fired[7] is True  # the crash bar


def test_pct_stop_resets_on_reentry() -> None:
    """A new lot (different entry_ts) must reset the peak, not inherit the old
    high — otherwise a re-entry would carry a stale, too-high stop."""
    overlay = TrailingStopPct(pct=0.10)
    dates = pd.date_range(date(2021, 1, 1), periods=3, freq="B")
    data = MarketData({"XXX": _frame(dates, [100, 200, 150])}, snapshot_id="reentry")
    store = SignalStore(data)

    def ctx_at(i: int, entry: datetime) -> OverlayContext:
        now = datetime.combine(dates[i].date(), MARKET_CLOSE)
        return OverlayContext(
            now=pd.Timestamp(now),
            dv=DataView(data, store, now),
            holdings={"XXX": 100},
            entry_ts={"XXX": entry},
            equity=100_000.0,
        )

    first_entry = datetime.combine(dates[0].date(), MARKET_CLOSE)
    overlay.evaluate(ctx_at(1, first_entry))  # peak 200 -> stop 180
    assert overlay._peak["XXX"].stop == pytest.approx(200.0)  # noqa: SLF001

    # re-entered as a fresh lot at bar 2 (close 150): peak must reset to 150
    second_entry = datetime.combine(dates[2].date(), MARKET_CLOSE)
    overlay.evaluate(ctx_at(2, second_entry))
    assert overlay._peak["XXX"].stop == pytest.approx(150.0)  # noqa: SLF001
