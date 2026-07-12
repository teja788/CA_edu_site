"""Batch 2 of the momentum improvement plan: exposure overlays on dyn-1000.

Per docs/momentum_research_notes.md "Agreed test plan" (#8-10), using the
engine's new regime / vol_target StrategyConfig sections. Two base configs
carry over from Batch 1: the m2 baseline (+296.3% / 1.22 / -32.9%) and the
b1d balanced winner (vol-adjusted score + exit_rank 50, +280.7% / 1.23 /
-28.3%). Batch 1's binary gate (b1e, Sharpe 1.38) is the graded gate's
benchmark.

  b2a_graded        m2 + graded asymmetric regime (NIFTYBEES: 100SMA, 200SMA,
                    12m return -> f in {0, 1/3, 2/3, 1}; scales new buys only)
  b2b_voltgt        m2 + vol target (12% annual, 126d own-return vol, de-lever
                    only)
  b2c_stack         m2 + both
  b2d_graded_score  b1d config + graded regime
  b2e_full          b1d config + both
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
    RegimeSignalSpec,
    RegimeSpec,
    ScoreSpec,
    SelectionSpec,
    SignalSpec,
    SizingSpec,
    StrategyConfig,
    UniverseSpec,
    VolTargetSpec,
)
from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore
from tradingos.engine.event.engine import EventEngine
from batch1_m2_improvements import (
    MOM,
    RAM6,
    RAM12,
    REGIME_SYMBOL,
    SeasonedTopNResolver,
)
from nse200_dynamic import max_drawdown

SCRATCH = Path(__file__).resolve().parent
START = date(2021, 7, 13)
END = date(2026, 7, 10)
CAPITAL = 40_000_000.0
MIN_TRADED_VALUE = 50_000_000.0
TOP_N = 1000
TAG = "nse1000dyn"

VARIANTS = ["b2a_graded", "b2b_voltgt", "b2c_stack", "b2d_graded_score",
            "b2e_full"]
if len(sys.argv) > 1:
    VARIANTS = [v for v in sys.argv[1].split(",") if v in VARIANTS]

GRADED = RegimeSpec(
    symbol=REGIME_SYMBOL,
    signals=[
        RegimeSignalSpec(kind="above_ma", params={"window": 100}),
        RegimeSignalSpec(kind="above_ma", params={"window": 200}),
        RegimeSignalSpec(kind="positive_return", params={"window": 252}),
    ],
    mode="graded_asymmetric",
)
VOLTGT = VolTargetSpec(target_annual_vol=0.12, lookback_bars=126,
                       max_exposure=1.0)


def make_config(variant: str, symbols: list[str]) -> StrategyConfig:
    scored = variant in ("b2d_graded_score", "b2e_full")
    return StrategyConfig(
        name=f"{TAG}_{variant}",
        engine=EngineMode.EVENT,
        start=START,
        end=END,
        capital=CAPITAL,
        universe=UniverseSpec(symbols=symbols, point_in_time=False,
                              min_median_traded_value=MIN_TRADED_VALUE),
        execution=ExecutionSpec(timing="next_open", max_participation=0.05),
        signals=[RAM6, RAM12] if scored else [MOM],
        score=ScoreSpec(type="weighted_zscore",
                        weights={"ram6": 0.5, "ram12": 0.5} if scored
                        else {"mom": 1.0}),
        selection=SelectionSpec(method="top_n", n=25,
                                exit_rank=50 if scored else 35),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.05),
        filters=[],
        overlays=[],
        regime=None if variant == "b2b_voltgt" else GRADED,
        vol_target=VOLTGT if variant in ("b2b_voltgt", "b2c_stack",
                                         "b2e_full") else None,
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
           / f"{TAG}_batch2_comparison_{run_ts.strftime('%Y-%m-%d_%H%M%S')}.json")
    out.write_text(json.dumps({
        "run_at": run_ts.isoformat(timespec="seconds"),
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "universe": f"dynamic top-{TOP_N}, as nse200_dynamic.py",
        "baseline": "m2 = +296.3%/1.22/-32.9%; b1d = +280.7%/1.23/-28.3%; "
                    "b1e binary gate = +257.7%/1.38/-33.6%",
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
