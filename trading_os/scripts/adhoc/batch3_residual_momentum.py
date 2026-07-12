"""Batch 3 of the momentum improvement plan: residual momentum on dyn-1000.

Per docs/momentum_research_notes.md "Agreed test plan" #11, using the new
benchmark-aware residual_momentum factor (commit c339ae2): 12-1 momentum of
rolling market-model residuals vs NIFTYBEES, standardized by residual sigma
(Blitz-Huij-Martens 2011).

  b3a_resid         residual momentum score only, exit 35 (m2-comparable)
  b3b_resid_graded  b3a + graded asymmetric regime gate
  b3c_resid_champ   champion structure: residual momentum + exit 50 + graded
                    gate (b2d with the signal swapped)
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from tradingos.config.schemas import (
    EngineMode,
    ExecutionSpec,
    RebalanceSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
)
from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore
from tradingos.engine.event.engine import EventEngine
from batch1_m2_improvements import SeasonedTopNResolver, REGIME_SYMBOL
from batch2_m2_overlays import GRADED
from nse200_dynamic import max_drawdown

SCRATCH = Path(__file__).resolve().parent
START = date(2021, 7, 13)
END = date(2026, 7, 10)
CAPITAL = 40_000_000.0
MIN_TRADED_VALUE = 50_000_000.0
TOP_N = 1000
TAG = "nse1000dyn"

VARIANTS = ["b3a_resid", "b3b_resid_graded", "b3c_resid_champ"]
if len(sys.argv) > 1:
    VARIANTS = [v for v in sys.argv[1].split(",") if v in VARIANTS]

RESID = SignalSpec(id="resid", name="residual_momentum",
                   benchmark=REGIME_SYMBOL,
                   params={"window": 252, "skip": 21, "beta_window": 252})


def make_config(variant: str, symbols: list[str]) -> StrategyConfig:
    return StrategyConfig(
        name=f"{TAG}_{variant}",
        engine=EngineMode.EVENT,
        start=START,
        end=END,
        capital=CAPITAL,
        universe=UniverseSpec(symbols=symbols, point_in_time=False,
                              min_median_traded_value=MIN_TRADED_VALUE),
        execution=ExecutionSpec(timing="next_open", max_participation=0.05),
        signals=[RESID],
        score=ScoreSpec(type="weighted_zscore", weights={"resid": 1.0}),
        selection=SelectionSpec(
            method="top_n", n=25,
            exit_rank=50 if variant == "b3c_resid_champ" else 35),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.05),
        filters=[],
        overlays=[],
        regime=None if variant == "b3a_resid" else GRADED,
        vol_target=None,
    )


def main() -> None:
    from tradingos.analytics.metrics import compute_metrics
    from tradingos.experiments.db import session_scope
    from tradingos.experiments.models import ExperimentRun
    from tradingos.experiments.runner import code_git_hash
    from nifty200_variants import experiment_row

    settings = get_settings()
    store = BarStore(settings)
    with open(SCRATCH / "nse2000.csv", newline="") as fh:
        syms = [r["Symbol"] for r in csv.DictReader(fh)]
    universe = sorted(set(syms) & set(store.symbols(Timeframe.DAY)))
    md_all = store.load_market_data(universe + [REGIME_SYMBOL], Timeframe.DAY,
                                    start=None, end=None)
    resolver = SeasonedTopNResolver(md_all, TOP_N, universe)

    run_ts = datetime.now()
    git_hash = code_git_hash()
    comparison: list[dict] = []

    for variant in VARIANTS:
        family = f"adhoc_{variant}_{TAG}"
        run_dir = (settings.artifacts_dir / "adhoc" / family
                   / run_ts.strftime("%Y-%m-%d_%H%M%S"))
        run_dir.mkdir(parents=True, exist_ok=True)
        cfg = make_config(variant, universe)
        started = datetime.now()
        res = EventEngine().run(cfg, md_all, resolver)
        finished = datetime.now()
        metrics = compute_metrics(res)

        neq = res.equity.sort_index()
        npnl = float(neq.iloc[-1]) - CAPITAL
        gpnl = float(res.gross_equity.sort_index().iloc[-1]) - CAPITAL
        trades = pd.DataFrame([{
            "symbol": t.symbol, "qty": t.qty,
            "entry_ts": t.entry_ts, "exit_ts": t.exit_ts,
            "entry_price": t.entry_price, "exit_price": t.exit_price,
            "gross_pnl": round(t.gross_pnl, 0), "costs": round(t.costs, 0),
            "net_pnl": round(t.net_pnl, 0), "exit_reason": t.exit_reason,
        } for t in res.trades])
        stats = {
            "variant": variant, "kind": f"portfolio top-25, dynamic top-{TOP_N}",
            "net_return_pct": round(npnl / CAPITAL * 100, 1),
            "net_max_dd_pct": round(max_drawdown(neq) * 100, 1),
            "total_trades": len(res.trades),
            "total_charges": round(gpnl - npnl, 0),
            "sharpe": metrics.get("sharpe"),
            "exit_reasons": (trades.exit_reason.value_counts().to_dict()
                             if len(trades) else {}),
        }
        neq.to_csv(run_dir / "net_equity_curve.csv")
        trades.to_csv(run_dir / "trades.csv", index=False)
        if len(trades):
            (trades.groupby("symbol")
             .agg(trades=("net_pnl", "size"), net_pnl=("net_pnl", "sum"),
                  gross_pnl=("gross_pnl", "sum"), costs=("costs", "sum"))
             .sort_values("net_pnl", ascending=False)
             .to_csv(run_dir / "per_stock_pnl.csv"))
        (run_dir / "summary.json").write_text(json.dumps(stats, indent=2))
        with session_scope(settings) as session:
            session.add(experiment_row(
                ExperimentRun, family, variant, cfg, res, metrics, started,
                finished, run_dir, git_hash, md_all.snapshot_id, len(neq)))
        comparison.append(stats)
        print(json.dumps(stats), flush=True)

    out = (settings.artifacts_dir / "adhoc"
           / f"{TAG}_batch3_comparison_{run_ts.strftime('%Y-%m-%d_%H%M%S')}.json")
    out.write_text(json.dumps({
        "run_at": run_ts.isoformat(timespec="seconds"),
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "universe": f"dynamic top-{TOP_N}, as nse200_dynamic.py",
        "baseline": "m2 = +296.3%/1.22/-32.9%; b2d champion = "
                    "+283.4%/1.32/-24.8%",
        "caveats": [
            "delisted names absent from Kite data (bias remains, smaller)",
            "price returns, no dividends",
            "charges before 2026 use the zerodha_2026 schedule (approximate)",
        ],
        "variants": comparison,
    }, indent=2))
    print(f"comparison -> {out}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
