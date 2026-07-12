"""Tests for the dynamic traded-value universe (``UniverseSpec.dynamic_top_n``).

Covers, in order:

* **Parity** — the src ``DynamicTopNResolver`` reproduces, bit-for-bit, an inline
  reimplementation of the adhoc runners' resolver logic
  (``scripts/adhoc/nse200_dynamic.py`` + ``batch1_m2_improvements.py``), including
  pre-seasoning NaN behaviour and ``min_history`` masking.
* **Causality** — ``membership(on)`` is unchanged when bars dated after ``on`` move.
* **Config** — YAML round-trip via the loader, ConfigError on bad combos, and
  config_hash sensitivity to the new fields.
* **Auto-wiring** — a config with ``dynamic_top_n`` runs end-to-end through the
  event engine with only the default ``PITUniverseResolver`` (no caller resolver).
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
import yaml

from tradingos.config.loader import load_strategy
from tradingos.config.schemas import (
    RebalanceSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.config.settings import Settings
from tradingos.core.errors import ConfigError
from tradingos.core.models import Timeframe
from tradingos.data.universe import DynamicTopNResolver, PITUniverseResolver
from tradingos.engine.dataview import MarketData
from tradingos.engine.event.engine import EventEngine

RANK_LOOKBACK = 126


# --------------------------------------------------------------------------- #
# synthetic data + inline reference (mirrors the adhoc runners exactly)
# --------------------------------------------------------------------------- #
# One shared trading calendar, as on a real exchange: 400 business days
# (2020-01-01 .. 2021-07-13). AAA..DDD trade the whole span; EEE lists with
# 200 bars of history by the end and FFF with 160 — so at the calendar's end
# both are seasoned under a 126-bar gate but NOT under a 252-bar one.
_CAL = pd.date_range(date(2020, 1, 1), periods=400, freq="B")


def _sym_frame(idx: pd.DatetimeIndex, close: float, volume: int = 1_000_000) -> pd.DataFrame:
    """Flat OHLCV frame at a constant close/volume (traded value is a stable,
    distinct number per symbol, so top-N ordering is unambiguous)."""
    return pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close, "volume": volume},
        index=idx,
    )


def _panel_data() -> MarketData:
    """Six symbols with distinct traded values and staggered listing dates.

    Traded value (close*volume) descends A>B>C>D>E>F.
    """
    frames = {
        "AAA": _sym_frame(_CAL, 100.0),        # tv 1.0e8, 400 bars
        "BBB": _sym_frame(_CAL, 90.0),         # tv 9.0e7, 400 bars
        "CCC": _sym_frame(_CAL, 80.0),         # tv 8.0e7, 400 bars
        "DDD": _sym_frame(_CAL, 70.0),         # tv 7.0e7, 400 bars
        "EEE": _sym_frame(_CAL[-200:], 60.0),  # tv 6.0e7, seasons(126) at _CAL[325]
        "FFF": _sym_frame(_CAL[-160:], 50.0),  # tv 5.0e7, seasons(126) at _CAL[365]
    }
    return MarketData(frames, timeframe=Timeframe.DAY)


def _ref_panel(data: MarketData, symbols: list[str], rank_lookback: int,
               min_history: int) -> pd.DataFrame:
    """Inline copy of the adhoc runners' panel construction."""
    tv: dict[str, pd.Series] = {}
    for sym in symbols:
        f = data.full_frame(sym)
        m = (f["close"] * f["volume"]).rolling(
            rank_lookback, min_periods=rank_lookback).median()
        if min_history > rank_lookback:
            m = m.where(f["close"].expanding().count() >= min_history)
        tv[sym] = m
    return pd.DataFrame(tv).sort_index()


def _ref_membership(panel: pd.DataFrame, on: date, top_n: int) -> list[str]:
    rows = panel.loc[: pd.Timestamp(on)]
    if rows.empty:
        return []
    row = rows.iloc[-1].dropna()
    return sorted(row.sort_values(ascending=False).head(top_n).index)


_POOL = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
# spans: before any seasoning (bar 50), just after AAA..DDD season (130),
# mid-run (260), after EEE seasons (330), and the final bar (399); plus a
# date before the calendar starts entirely.
_DATES = [date(2019, 6, 1)] + [_CAL[i].date() for i in (50, 130, 260, 330, 399)]


# --------------------------------------------------------------------------- #
# parity
# --------------------------------------------------------------------------- #
class TestParity:
    @pytest.mark.parametrize("top_n", [2, 4, 6, 10])
    def test_matches_reference_default_seasoning(self, top_n: int) -> None:
        data = _panel_data()
        ref = _ref_panel(data, _POOL, RANK_LOOKBACK, RANK_LOOKBACK)
        resolver = DynamicTopNResolver(data, top_n, _POOL, rank_lookback=RANK_LOOKBACK)
        for on in _DATES:
            assert resolver.membership(on) == _ref_membership(ref, on, top_n), on

    def test_pre_seasoning_is_empty(self) -> None:
        # 126-bar min_periods -> no symbol is ranked before 126 trading days.
        data = _panel_data()
        resolver = DynamicTopNResolver(data, 6, _POOL, rank_lookback=RANK_LOOKBACK)
        assert resolver.membership(_CAL[50].date()) == []
        assert resolver.membership(_CAL[124].date()) == []  # one bar short
        # at bar 125 (the 126th) the four long-history names season together;
        # EEE and FFF are not even listed yet
        assert resolver.membership(_CAL[125].date()) == ["AAA", "BBB", "CCC", "DDD"]

    @pytest.mark.parametrize("min_history", [126, 189, 252])
    def test_min_history_masking_matches_reference(self, min_history: int) -> None:
        data = _panel_data()
        ref = _ref_panel(data, _POOL, RANK_LOOKBACK, min_history)
        resolver = DynamicTopNResolver(
            data, 6, _POOL, rank_lookback=RANK_LOOKBACK, min_history=min_history)
        for on in _DATES:
            assert resolver.membership(on) == _ref_membership(ref, on, 6), (on, min_history)

    def test_min_history_delays_late_listing(self) -> None:
        # At the final bar EEE has 200 bars and FFF 160: both seasoned under
        # the default 126-bar gate, neither under a 252-bar listing-age gate.
        data = _panel_data()
        r126 = DynamicTopNResolver(data, 6, _POOL, min_history=126)
        r252 = DynamicTopNResolver(data, 6, _POOL, min_history=252)
        on = _CAL[399].date()
        assert r126.membership(on) == ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
        assert r252.membership(on) == ["AAA", "BBB", "CCC", "DDD"]

    def test_none_min_history_defaults_to_rank_lookback(self) -> None:
        data = _panel_data()
        a = DynamicTopNResolver(data, 6, _POOL, rank_lookback=100)
        b = DynamicTopNResolver(data, 6, _POOL, rank_lookback=100, min_history=100)
        for on in _DATES:
            assert a.membership(on) == b.membership(on)

    def test_benchmark_frame_excluded_from_pool(self) -> None:
        # A regime ETF loaded into MarketData but NOT in the pool must never rank.
        data = _panel_data()
        frames = dict(data._frames)  # noqa: SLF001 - test-only introspection
        frames["NIFTYBEES"] = _sym_frame(_CAL, 1000.0, volume=10_000_000)
        md = MarketData(frames, timeframe=Timeframe.DAY)
        resolver = DynamicTopNResolver(md, 10, _POOL)  # pool excludes NIFTYBEES
        members = resolver.membership(_CAL[399].date())
        assert "NIFTYBEES" not in members
        assert members  # the pool itself still ranks


# --------------------------------------------------------------------------- #
# causality
# --------------------------------------------------------------------------- #
class TestCausality:
    def test_future_bars_do_not_change_membership(self) -> None:
        data = _panel_data()
        on = _CAL[260].date()
        base = DynamicTopNResolver(data, 4, _POOL).membership(on)
        assert base  # non-trivial membership, or the test proves nothing

        # perturb every bar strictly AFTER `on` (flip the ranking wildly)
        mutated: dict[str, pd.DataFrame] = {}
        for sym, f in data._frames.items():  # noqa: SLF001
            g = f.copy()
            after = g.index > pd.Timestamp(on)
            g.loc[after, ["close", "volume"]] = [1.0, 999_999_999]
            mutated[sym] = g
        md2 = MarketData(mutated, timeframe=Timeframe.DAY)
        assert DynamicTopNResolver(md2, 4, _POOL).membership(on) == base


# --------------------------------------------------------------------------- #
# config
# --------------------------------------------------------------------------- #
def _dynamic_config() -> StrategyConfig:
    return StrategyConfig(
        name="dyn_test",
        start=_CAL[0].date(),
        end=_CAL[399].date(),
        universe=UniverseSpec(
            symbols=_POOL, point_in_time=False, dynamic_top_n=4,
            rank_lookback=126, min_median_traded_value=50_000_000.0,
        ),
        signals=[SignalSpec(id="mom", name="return_over_window",
                            params={"window": 20, "skip": 1})],
        score=ScoreSpec(type="weighted_zscore", weights={"mom": 1.0}),
        selection=SelectionSpec(method="top_n", n=2, exit_rank=3),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.5),
    )


class TestConfig:
    def test_yaml_round_trip_via_loader(self, tmp_path) -> None:
        cfg = _dynamic_config()
        p = tmp_path / "dyn.yaml"
        p.write_text(yaml.safe_dump(cfg.model_dump(mode="json")))
        back = load_strategy(p)
        assert back.universe.dynamic_top_n == 4
        assert back.universe.rank_lookback == 126
        assert back.universe.min_history is None
        assert back.config_hash() == cfg.config_hash()

    def test_defaults(self) -> None:
        u = UniverseSpec(symbols=["A"], point_in_time=False, dynamic_top_n=3)
        assert u.rank_lookback == 126
        assert u.min_history is None

    def test_reject_dynamic_without_symbols(self) -> None:
        with pytest.raises(ConfigError, match="explicit `symbols` pool"):
            UniverseSpec(dynamic_top_n=5)

    def test_reject_dynamic_with_point_in_time(self) -> None:
        with pytest.raises(ConfigError, match="point-in-time"):
            UniverseSpec(symbols=["A"], dynamic_top_n=5)  # point_in_time defaults True

    def test_reject_min_history_below_rank_lookback(self) -> None:
        with pytest.raises(ConfigError, match="must be >="):
            UniverseSpec(symbols=["A"], point_in_time=False,
                         dynamic_top_n=5, rank_lookback=126, min_history=50)

    def test_reject_top_n_below_one(self) -> None:
        with pytest.raises(ValueError):
            UniverseSpec(symbols=["A"], point_in_time=False, dynamic_top_n=0)

    def test_config_hash_sensitive_to_fields(self) -> None:
        base = _dynamic_config()
        h = base.config_hash()
        for update in (
            {"dynamic_top_n": 5},
            {"rank_lookback": 200},
            {"min_history": 252},
        ):
            other = base.model_copy(
                update={"universe": base.universe.model_copy(update=update)})
            assert other.config_hash() != h, update


# --------------------------------------------------------------------------- #
# auto-wiring: no caller-supplied resolver
# --------------------------------------------------------------------------- #
class TestAutoWiring:
    def test_pit_resolver_dispatches_to_dynamic(self, settings: Settings) -> None:
        data = _panel_data()
        spec = _dynamic_config().universe
        resolver = PITUniverseResolver(settings)
        # PIT resolver builds + delegates to DynamicTopNResolver on the pool,
        # matching a standalone one bit-for-bit (no membership-DB lookup).
        direct = DynamicTopNResolver(data, 4, _POOL, rank_lookback=126)
        for on in _DATES:
            assert resolver.resolve(spec, on, data) == direct.membership(on), on
        assert resolver.warnings == []

    def test_end_to_end_event_engine(self, settings: Settings) -> None:
        data = _panel_data()
        cfg = _dynamic_config()
        # Only the default resolver — the engine must auto-wire the dynamic pool.
        result = EventEngine().run(cfg, data, PITUniverseResolver(settings))
        assert len(result.equity) > 0
        assert result.equity.index.is_monotonic_increasing
        # positions only ever come from the ranked pool (never a stray symbol)
        for t in result.trades:
            assert t.symbol in _POOL
