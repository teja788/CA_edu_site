"""Delisted symbols must leave the buy/selection candidate set for good.

Regression for two related bugs:

(a) a delisted symbol (frame ends mid-run) could be re-BOUGHT at its
    pre-haircut last close by a ``same_close`` rebalance on the delist bar —
    the force-exit at ``close*(1-haircut)`` fired first, then the rebalance
    happily bought it back at the full close;
(b) the symbol's frozen final score (DataView keeps serving its last bars
    forever) kept it in the top-N selection on every later rebalance, wasting
    a slot (event engine) or holding a phantom flat-priced position
    (vectorized engine) until the end of the run.

Fix under test: from the delist date onward the symbol is excluded from the
candidate set (both engines share the pipeline), so the freed capital rotates
into the next-best name.
"""

from __future__ import annotations

from datetime import date, datetime

import pandas as pd
from fixtures.synthetic import trading_days

from tradingos.config.schemas import (
    ExecutionSpec,
    RebalanceSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import MARKET_CLOSE
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import DataView, MarketData, SignalStore
from tradingos.engine.event.engine import EventEngine
from tradingos.engine.event.strategy_runtime import evaluate_targets
from tradingos.engine.vectorized.engine import VectorizedEngine
from tradingos.strategies.registry import register_signal


@register_signal("test_delist_close", tier="custom")
def _close_signal(df: pd.DataFrame, **params: object) -> pd.Series:
    """Rank by the latest close (causal)."""
    return df["close"].astype("float64")


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


def _data() -> tuple[pd.DatetimeIndex, MarketData]:
    full = trading_days(date(2021, 1, 1), date(2021, 1, 12))  # 8 business days
    short = full[:5]  # DDD's frame ends mid-run -> delisted at bar index 4
    ddd = _frame(short, [300.0] * 5)  # highest close -> always ranks first
    eee = _frame(full, [100.0, 105.0, 110.0, 115.0, 120.0, 125.0, 130.0, 135.0])
    fff = _frame(full, [90.0] * 8)
    data = MarketData(
        {"DDD": ddd, "EEE": eee, "FFF": fff}, timeframe=Timeframe.DAY, snapshot_id="delist_excl"
    )
    return full, data


def _cfg(timing: str) -> StrategyConfig:
    return StrategyConfig(
        name="delist_excl",
        start=date(2021, 1, 1),
        end=date(2021, 1, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["DDD", "EEE", "FFF"], point_in_time=False),
        signals=[SignalSpec(id="c", name="test_delist_close")],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.9),
        rebalance=RebalanceSpec(frequency="daily"),
        execution=ExecutionSpec(timing=timing, slippage_bps=0.0, max_participation=1.0),
    )


# ---------------------------------------------------------------------------
# pipeline-level: candidate exclusion from the delist date onward
# ---------------------------------------------------------------------------


def test_evaluate_targets_excludes_delisted_from_delist_date_onward() -> None:
    full, data = _data()
    cfg = _cfg("same_close")
    store = SignalStore(data)
    warnings: list[str] = []

    # On the delist bar itself and on every later bar, DDD is out and the
    # next-best name (EEE) takes the slot — the frozen score no longer wins.
    for i in (4, 6):
        dv = DataView(data, store, datetime.combine(full[i].date(), MARKET_CLOSE))
        targets = evaluate_targets(
            cfg, dv, StaticUniverseResolver(), data, {}, 1_000_000.0, warnings,
            run_end=full[-1],
        )
        assert "DDD" not in targets, f"delisted DDD still targeted at bar {i}"
        assert "EEE" in targets

    # The bar BEFORE the delist bar, DDD is still a legitimate candidate.
    dv = DataView(data, store, datetime.combine(full[3].date(), MARKET_CLOSE))
    targets = evaluate_targets(
        cfg, dv, StaticUniverseResolver(), data, {}, 1_000_000.0, warnings,
        run_end=full[-1],
    )
    assert "DDD" in targets


# ---------------------------------------------------------------------------
# event engine, same_close: no re-buy at the pre-haircut close
# ---------------------------------------------------------------------------


def test_same_close_rebalance_does_not_rebuy_delisted_symbol() -> None:
    full, data = _data()
    res = EventEngine().run(_cfg("same_close"), data, StaticUniverseResolver())

    delists = [t for t in res.trades if t.exit_reason == "delisted"]
    assert len(delists) == 1 and delists[0].symbol == "DDD"

    # After the forced exit the freed cash rotates into EEE (steadily rising):
    # equity must keep rising instead of sitting in a phantom DDD position
    # re-bought at its pre-haircut close and marked flat at 300 forever.
    post = res.equity.iloc[5:]
    assert post.iloc[-1] > post.iloc[0], "equity flat after delist: DDD was re-bought"


# ---------------------------------------------------------------------------
# event engine, next_open: frozen score must not hog the top-N slot
# ---------------------------------------------------------------------------


def test_next_open_selection_drops_delisted_frozen_score() -> None:
    full, data = _data()
    res = EventEngine().run(_cfg("next_open"), data, StaticUniverseResolver())

    delists = [t for t in res.trades if t.exit_reason == "delisted"]
    assert len(delists) == 1 and delists[0].symbol == "DDD"

    # With DDD excluded, the delist-bar rebalance targets EEE and fills at the
    # next open; equity then tracks EEE's rise. (The bug kept targeting DDD —
    # whose orders can never fill — leaving the book 100% cash and flat.)
    post = res.equity.iloc[5:]
    assert post.iloc[-1] > post.iloc[0], "book stayed in cash: delisted DDD kept its slot"


# ---------------------------------------------------------------------------
# vectorized engine: same exclusion via the shared pipeline
# ---------------------------------------------------------------------------


def test_vectorized_engine_excludes_delisted_from_selection() -> None:
    full, data = _data()
    res = VectorizedEngine().run(_cfg("same_close"), data, StaticUniverseResolver())

    # With the frozen score neutralised, the book rotates into EEE after the
    # delist bar; the buggy behaviour held DDD at its forward-filled last
    # close forever (flat equity).
    post = res.equity.iloc[5:]
    assert post.iloc[-1] > post.iloc[0], "vectorized book stuck in delisted DDD"
