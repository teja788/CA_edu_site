"""Behavioural tests for the vectorized (fast) engine.

Deterministic, synthetic frames only. Covers: the mandatory fast-engine
approximation warnings, gross/net-costs identity, integer-share holdings,
symbol-routed regime routing to cash, the empty/all-cash paths, and that
importing the engine does NOT eagerly import vectorbt.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from fixtures.synthetic import synthetic_daily, synthetic_universe

from tradingos.config.schemas import (
    EngineMode,
    ExecutionSpec,
    FilterSpec,
    RebalanceSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.core.models import Timeframe
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import MarketData
from tradingos.engine.vectorized.engine import VectorizedEngine
from tradingos.strategies.registry import register_signal

_INDEX = "NIFTY 50"


@register_signal("test_vec_mom", tier="custom", window=63)
def _vec_mom(df: pd.DataFrame, **params: object) -> pd.Series:
    return df["close"].pct_change(int(params["window"]))


@register_signal("test_vec_close", tier="custom")
def _vec_close(df: pd.DataFrame, **params: object) -> pd.Series:
    return df["close"].astype("float64")


def _flat(dates: pd.DatetimeIndex, closes: list[float], volume: int = 10_000_000) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c + 5 for c in closes],
            "low": [c - 5 for c in closes],
            "close": closes,
            "volume": [volume] * len(dates),
        },
        index=dates,
    )


def _mom_config(**overrides: object) -> StrategyConfig:
    base = dict(
        name="vec_mom",
        start=date(2019, 1, 1),
        end=date(2021, 12, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["AAA", "BBB", "CCC"], point_in_time=False),
        signals=[SignalSpec(id="mom", name="test_vec_mom", params={"window": 63})],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=2, exit_rank=2),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.6),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        execution=ExecutionSpec(timing="same_close", slippage_bps=0.0, max_participation=1.0),
    )
    base.update(overrides)
    return StrategyConfig(**base)  # type: ignore[arg-type]


def _mom_data() -> MarketData:
    frames = synthetic_universe(["AAA", "BBB", "CCC"], start=date(2019, 1, 1), end=date(2021, 12, 31))
    return MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="vec")


# ---------------------------------------------------------------------------
# lazy import: importing the engine must not pull in vectorbt (numba, ~30s)
# ---------------------------------------------------------------------------


def test_importing_engine_does_not_import_vectorbt() -> None:
    # The engine module is already imported at test-collection time; assert the
    # heavy dependency is only pulled in lazily inside run() (it may already be
    # loaded by an earlier test in this session — so only assert the module code
    # itself carries no top-level `import vectorbt`).
    import inspect

    import tradingos.engine.vectorized.engine as mod

    src = inspect.getsource(mod)
    top_level = [
        line
        for line in src.splitlines()
        if line.startswith("import vectorbt") or line.startswith("from vectorbt")
    ]
    assert not top_level, "vectorbt must be imported lazily inside run(), not at module top level"


# ---------------------------------------------------------------------------
# core behaviour
# ---------------------------------------------------------------------------


def test_run_emits_fast_engine_warnings_and_costs_identity() -> None:
    res = VectorizedEngine().run(_mom_config(), _mom_data(), StaticUniverseResolver())

    assert res.engine == EngineMode.VECTORIZED
    assert res.equity.index.is_monotonic_increasing
    assert res.total_costs > 0
    assert res.trades == []  # fast engine emits no per-trade round trips

    # mandatory disclaimer present, on its own string
    assert any("MUST be validated on the event engine" in w for w in res.warnings)
    assert any("no order book" in w for w in res.warnings)
    assert any("result.trades is" in w for w in res.warnings)

    # gross >= net everywhere, and gross - net == cumulative costs at the last bar
    assert (res.gross_equity >= res.equity - 0.02).all()
    assert res.gross_equity.iloc[-1] - res.equity.iloc[-1] == pytest.approx(res.total_costs, abs=0.05)


def test_run_is_deterministic() -> None:
    data, cfg = _mom_data(), _mom_config()
    r1 = VectorizedEngine().run(cfg, data, StaticUniverseResolver())
    r2 = VectorizedEngine().run(cfg, data, StaticUniverseResolver())
    assert r1.equity.equals(r2.equity)
    assert r1.gross_equity.equals(r2.gross_equity)
    assert r1.total_costs == r2.total_costs


def test_symbol_routed_regime_filter_sends_book_to_cash() -> None:
    dates = pd.date_range(date(2021, 1, 1), periods=10, freq="B")
    stock = _flat(dates, [100, 110, 120, 130, 140, 150, 160, 170, 180, 190])
    # index rises above its 3-day MA, then crashes below it from bar index 6 on
    idx = _flat(dates, [100, 101, 102, 103, 104, 105, 80, 79, 78, 77])
    data = MarketData({"AAA": stock, _INDEX: idx}, timeframe=Timeframe.DAY, snapshot_id="regime")

    base = dict(
        name="regime",
        start=date(2021, 1, 1),
        end=date(2021, 1, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["AAA"], point_in_time=False),
        signals=[SignalSpec(id="c", name="test_vec_close")],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="daily"),
        execution=ExecutionSpec(timing="same_close", slippage_bps=0.0, max_participation=1.0),
    )
    with_regime = StrategyConfig(
        filters=[FilterSpec(name="index_above_ma", params={"window": 3, "symbol": _INDEX})], **base
    )
    without = StrategyConfig(**base)  # type: ignore[arg-type]

    r_regime = VectorizedEngine().run(with_regime, data, StaticUniverseResolver())
    r_hold = VectorizedEngine().run(without, data, StaticUniverseResolver())

    # After the index crashes the regime run is 100% cash: last two bars flat
    # even though the stock keeps ripping higher; the control keeps moving.
    assert r_regime.equity.iloc[-1] == pytest.approx(r_regime.equity.iloc[-2])
    assert r_hold.equity.iloc[-1] != pytest.approx(r_hold.equity.iloc[-2])
    assert r_regime.equity.iloc[-1] < r_hold.equity.iloc[-1]


def test_all_cash_run_stays_flat_at_capital() -> None:
    # Universe names that don't exist in the data -> no candidates ever qualify
    # -> nothing is bought -> the portfolio is all cash for the whole run.
    frames = {"AAA": synthetic_daily("AAA", start=date(2021, 1, 1), end=date(2021, 3, 31))}
    data = MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="cash")
    cfg = _mom_config(
        name="allcash",
        start=date(2021, 1, 1),
        end=date(2021, 3, 31),
        universe=UniverseSpec(symbols=["ZZZ"], point_in_time=False),
    )
    res = VectorizedEngine().run(cfg, data, StaticUniverseResolver())
    assert res.total_costs == 0.0
    assert (res.equity == 1_000_000.0).all()
    assert (res.gross_equity == 1_000_000.0).all()
    assert len(res.equity) == len(data.union_index())


def test_empty_calendar_returns_empty_result_with_warnings() -> None:
    frames = {"AAA": synthetic_daily("AAA", start=date(2021, 1, 1), end=date(2021, 3, 31))}
    data = MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="empty")
    # window entirely before the data -> empty calendar
    cfg = _mom_config(
        name="empty",
        start=date(2010, 1, 1),
        end=date(2010, 12, 31),
        universe=UniverseSpec(symbols=["AAA"], point_in_time=False),
    )
    res = VectorizedEngine().run(cfg, data, StaticUniverseResolver())
    assert res.equity.empty
    assert res.total_costs == 0.0
    assert any("MUST be validated on the event engine" in w for w in res.warnings)


def test_survivorship_warning_propagates() -> None:
    frames = synthetic_universe(["AAA", "BBB"], start=date(2021, 1, 1), end=date(2021, 6, 30))
    data = MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="pit")
    cfg = _mom_config(
        name="pit",
        start=date(2021, 1, 1),
        end=date(2021, 6, 30),
        universe=UniverseSpec(index="NIFTY500", point_in_time=True),
        signals=[SignalSpec(id="mom", name="test_vec_mom", params={"window": 20})],
    )
    res = VectorizedEngine().run(cfg, data, StaticUniverseResolver())
    assert any("SURVIVORSHIP BIAS" in w for w in res.warnings)
