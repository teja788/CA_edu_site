"""Engine reconciliation: the same strategy must agree on both engines.

The vectorized (fast) engine and the event (realistic) engine model execution
differently, but under a config that makes their execution models COINCIDE
(same-close fills, zero slippage, no participation cap via huge synthetic
volumes, no overlays) they must produce nearly identical results. The residual
gap is the documented fast-engine approximation:

  * the event engine sizes off NET equity (charges drag buying power) while the
    fast engine sizes off a cost-free gross-equity simulation and subtracts
    charges afterwards, so integer-share floors diverge slightly over time;
  * charge timing granularity differs at the paisa.

Tolerances below are the spec's acceptance thresholds; this implementation
reconciles roughly 4x tighter (see the achieved numbers in the asserts).
"""

from __future__ import annotations

from datetime import date

import pandas as pd
from fixtures.synthetic import synthetic_universe

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
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import MarketData
from tradingos.engine.event.engine import EventEngine
from tradingos.engine.vectorized.engine import VectorizedEngine
from tradingos.strategies.registry import register_signal


@register_signal("test_recon_mom", tier="custom", window=63)
def _recon_mom(df: pd.DataFrame, **params: object) -> pd.Series:
    """Trailing return over ``window`` bars (causal) — distinct registry name."""
    return df["close"].pct_change(int(params["window"]))


def _recon_config() -> StrategyConfig:
    # Monthly top-2 of 3 names with a one-rank retention buffer: real rebalancing
    # (costs land near ~1.7% of capital) yet the engines still track tightly.
    return StrategyConfig(
        name="recon_top2",
        start=date(2019, 1, 1),
        end=date(2021, 12, 31),
        capital=1_000_000,
        universe=UniverseSpec(symbols=["AAA", "BBB", "CCC"], point_in_time=False),
        signals=[SignalSpec(id="mom", name="test_recon_mom", params={"window": 63})],
        score=ScoreSpec(type="single"),
        selection=SelectionSpec(method="top_n", n=2, exit_rank=2),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.6),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        # Make the two execution models coincide:
        execution=ExecutionSpec(timing="same_close", slippage_bps=0.0, max_participation=1.0),
    )


def test_event_and_vectorized_engines_reconcile() -> None:
    frames = synthetic_universe(["AAA", "BBB", "CCC"], start=date(2019, 1, 1), end=date(2021, 12, 31))
    data = MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="recon")
    cfg = _recon_config()

    ev = EventEngine().run(cfg, data, StaticUniverseResolver())
    vz = VectorizedEngine().run(cfg, data, StaticUniverseResolver())

    # Both engines must actually have traded (guards against a trivial pass).
    assert ev.total_costs > 0 and vz.total_costs > 0
    assert vz.engine.value == "vectorized"

    common = ev.equity.index.intersection(vz.equity.index)
    assert len(common) == len(ev.equity) == len(vz.equity)  # identical calendars
    e = ev.equity.reindex(common)
    v = vz.equity.reindex(common)

    # 1. final net equity relative difference < 1e-2 (achieved ~2.5e-3).
    fin_ev, fin_vz = float(e.iloc[-1]), float(v.iloc[-1])
    rel_final = abs(fin_vz - fin_ev) / abs(fin_ev)
    assert rel_final < 1e-2, f"final equity rel diff {rel_final:.3e} (ev={fin_ev}, vz={fin_vz})"

    # 2. total_costs relative difference < 5e-2 (achieved ~7e-3).
    rel_costs = abs(vz.total_costs - ev.total_costs) / abs(ev.total_costs)
    assert rel_costs < 5e-2, f"costs rel diff {rel_costs:.3e} (ev={ev.total_costs}, vz={vz.total_costs})"

    # 3. equity curves track: max relative divergence over the common index < 2e-2
    #    (achieved ~3.3e-3).
    max_div = float((v.sub(e).abs() / e.abs()).max())
    assert max_div < 2e-2, f"max curve divergence {max_div:.3e}"


def test_vectorized_engine_is_deterministic() -> None:
    frames = synthetic_universe(["AAA", "BBB", "CCC"], start=date(2019, 1, 1), end=date(2021, 12, 31))
    data = MarketData(frames, timeframe=Timeframe.DAY, snapshot_id="recon")
    cfg = _recon_config()
    r1 = VectorizedEngine().run(cfg, data, StaticUniverseResolver())
    r2 = VectorizedEngine().run(cfg, data, StaticUniverseResolver())
    assert r1.equity.equals(r2.equity)
    assert r1.gross_equity.equals(r2.gross_equity)
    assert r1.total_costs == r2.total_costs
