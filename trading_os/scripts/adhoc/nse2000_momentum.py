"""Momentum top-25 on the ~2000-name NSE mainboard universe, four variants.

Same core as nifty200_variants.py V6 (12-1 momentum, monthly rebalance,
top-25 / exit-rank-35, Rs 4 crore, equal weight, 5% cap), scaled to the full
mainboard universe with a Rs 5 crore median-daily-traded-value liquidity
screen (63-day lookback, point-in-time inside the engine):

  m1_sma_gate       — V6 as-is: momentum + own-stock 200-SMA eligibility gate
  m2_returns_only   — momentum ranking alone, no SMA gate
  m3_sma_gate_atr3  — m1 + 3x ATR(14) chandelier trailing stop
  m4_returns_atr3   — m2 + 3x ATR(14) chandelier trailing stop

All returns NET of charges. Every run persisted to the experiments DB plus a
timestamped artifacts dir with equity curve, trades.csv and per_stock_pnl.csv
(owner standing rules). Baseline: equal-weight buy & hold of the *liquid*
subset is not comparable across a 2000-name universe with listings mid-window,
so the NIFTY 200 study numbers remain the reference frame.
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
    FilterSpec,
    OverlaySpec,
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
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.dataview import MarketData
from tradingos.engine.event.engine import EventEngine

SCRATCH = Path(__file__).resolve().parent
START = date(2021, 7, 13)
END = date(2026, 7, 10)
CAPITAL = 40_000_000.0
MIN_TRADED_VALUE = 50_000_000.0  # Rs 5 cr median daily traded value

VARIANTS = ["m1_sma_gate", "m2_returns_only", "m3_sma_gate_atr3", "m4_returns_atr3"]

# optional args: universe CSV basename, family tag, comma-separated variant
# subset (defaults: full nse2000 sweep, all four variants)
UNIVERSE_CSV = sys.argv[1] if len(sys.argv) > 1 else "nse2000.csv"
TAG = sys.argv[2] if len(sys.argv) > 2 else "nse2000"
if len(sys.argv) > 3:
    VARIANTS = [v for v in sys.argv[3].split(",") if v in VARIANTS]


def load_symbols() -> list[str]:
    with open(SCRATCH / UNIVERSE_CSV, newline="") as fh:
        return [row["Symbol"].strip() for row in csv.DictReader(fh)]


def make_config(variant: str, symbols: list[str]) -> StrategyConfig:
    sma_gate = FilterSpec(name="index_above_ma", params={"window": 200})
    atr_stop = OverlaySpec(name="trailing_stop_atr",
                           params={"atr_window": 14, "multiple": 3.0})
    return StrategyConfig(
        name=f"{TAG}_{variant}",
        engine=EngineMode.EVENT,
        start=START,
        end=END,
        capital=CAPITAL,
        universe=UniverseSpec(symbols=symbols, point_in_time=False,
                              min_median_traded_value=MIN_TRADED_VALUE),
        execution=ExecutionSpec(timing="next_open", max_participation=0.05),
        signals=[SignalSpec(id="mom", name="return_over_window",
                            params={"window": 252, "skip": 21})],
        score=ScoreSpec(type="weighted_zscore", weights={"mom": 1.0}),
        selection=SelectionSpec(method="top_n", n=25, exit_rank=35),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.05),
        filters=[sma_gate] if variant in ("m1_sma_gate", "m3_sma_gate_atr3") else [],
        overlays=[atr_stop] if variant in ("m3_sma_gate_atr3", "m4_returns_atr3") else [],
    )


def max_drawdown(equity: pd.Series) -> float:
    if len(equity) == 0:
        return 0.0
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def main() -> None:
    from tradingos.analytics.metrics import compute_metrics
    from tradingos.experiments.db import session_scope
    from tradingos.experiments.models import ExperimentRun
    from tradingos.experiments.runner import code_git_hash
    from nifty200_variants import experiment_row

    settings = get_settings()
    store = BarStore(settings)
    available = set(store.symbols(Timeframe.DAY))
    symbols = [s for s in load_symbols() if s in available]
    print(f"universe: {len(symbols)} symbols with data", flush=True)

    md_all = store.load_market_data(sorted(symbols), Timeframe.DAY,
                                    start=None, end=None)
    run_ts = datetime.now()
    git_hash = code_git_hash()
    comparison: list[dict] = []

    for variant in VARIANTS:
        family = f"adhoc_{variant}_{TAG}"
        run_dir = (settings.artifacts_dir / "adhoc" / family
                   / run_ts.strftime("%Y-%m-%d_%H%M%S"))
        run_dir.mkdir(parents=True, exist_ok=True)
        cfg = make_config(variant, symbols)
        started = datetime.now()
        res = EventEngine().run(cfg, md_all, StaticUniverseResolver())
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
            "variant": variant, "kind": "portfolio top-25 nse2000",
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
           / f"{TAG}_momentum_comparison_{run_ts.strftime('%Y-%m-%d_%H%M%S')}.json")
    out.write_text(json.dumps({
        "run_at": run_ts.isoformat(timespec="seconds"),
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "universe": f"NSE mainboard {len(symbols)} names, "
                    f"liquidity screen Rs 5cr median daily traded value (63d)",
        "reference": "NIFTY200 v6 = +389.6% net, dd -26.0%; v7 = +320.5%, dd -20.1%",
        "caveats": [
            "survivorship: currently-listed names only, no delisted stocks",
            "price returns, no dividends",
            "charges before 2026 use the zerodha_2026 schedule (approximate)",
        ],
        "variants": comparison,
    }, indent=2))
    print(f"comparison -> {out}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
