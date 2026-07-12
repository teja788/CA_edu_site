"""US translation of the champion b2d-ST momentum strategy (one research run).

Mirrors scripts/adhoc/stmad_b2d.py's `st_gate` variant (the campaign champion)
but points the NSE platform at US data:

  * pool         = current S&P 500 + 400 + 600 (us1500.csv) INTERSECT store
  * universe     = dynamic top-1000 by trailing 126d median traded value,
                   min_median_traded_value $600k (Indian floor Rs 5cr ~ $600k)
  * score        = 50/50 z-blend of risk_adjusted_momentum 126/21/252 + 252/21/252
  * selection    = top-25 equal-weight, max 5%, exit_rank 50
  * rebalance    = monthly day 1, next_open execution
  * regime gate  = graded_asymmetric on SPY: above_ma 100, above_ma 200,
                   positive_return 252, supertrend(10, 3.0)
  * costs        = us_2026 (zero brokerage; SEC+TAF sell-side only)
  * capital      = $1,000,000

Run isolated so it never touches the Indian store:
  TOS_DATA_DIR=<repo>/us_data uv run python scripts/adhoc/us_b2dst.py

Caveats (reported): auto_adjust=True => TOTAL-RETURN momentum (mildly favorable
vs the Indian price-return runs); CURRENT S&P membership => survivorship bias;
2026 charge schedule applied to all years (approximate, warned once).
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from nifty200_variants import experiment_row

from tradingos.config.schemas import (
    CostSpec,
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
)
from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore
from tradingos.engine.event.engine import EventEngine
from tradingos.experiments.runner import make_universe_resolver

SCRATCH = Path(__file__).resolve().parent
START = date(2021, 7, 13)
CAPITAL = 1_000_000.0
MIN_TRADED_VALUE = 600_000.0  # Indian floor Rs 5cr ~ $600k (NOT $50M)
TOP_N = 1000
RANK_LOOKBACK = 126
REGIME_SYMBOL = "SPY"
TAG = "us_b2dst"

RAM6 = SignalSpec(id="ram6", name="risk_adjusted_momentum",
                  params={"window": 126, "skip": 21, "vol_window": 252})
RAM12 = SignalSpec(id="ram12", name="risk_adjusted_momentum",
                   params={"window": 252, "skip": 21, "vol_window": 252})
GATE4 = RegimeSpec(
    symbol=REGIME_SYMBOL,
    signals=[
        RegimeSignalSpec(kind="above_ma", params={"window": 100}),
        RegimeSignalSpec(kind="above_ma", params={"window": 200}),
        RegimeSignalSpec(kind="positive_return", params={"window": 252}),
        RegimeSignalSpec(kind="supertrend", params={"period": 10, "multiplier": 3.0}),
    ],
    mode="graded_asymmetric",
)


def make_config(symbols: list[str], end: date) -> StrategyConfig:
    return StrategyConfig(
        name=f"{TAG}_st_gate",
        engine=EngineMode.EVENT,
        start=START,
        end=end,
        capital=CAPITAL,
        universe=UniverseSpec(symbols=symbols, point_in_time=False,
                              dynamic_top_n=TOP_N, rank_lookback=RANK_LOOKBACK,
                              min_median_traded_value=MIN_TRADED_VALUE),
        execution=ExecutionSpec(timing="next_open", max_participation=0.05),
        signals=[RAM6, RAM12],
        score=ScoreSpec(type="weighted_zscore", weights={"ram6": 0.5, "ram12": 0.5}),
        selection=SelectionSpec(method="top_n", n=25, exit_rank=50),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.05),
        filters=[],
        overlays=[],
        regime=GATE4,
        vol_target=None,
        costs=CostSpec(schedule="us_2026"),
    )


def yearly_net_returns(neq: pd.Series, capital: float) -> dict[str, float]:
    """Per-CALENDAR-year net return (%) from the net equity curve. The first
    (partial) year is measured from the initial capital."""
    ye = neq.resample("YE").last()
    prev = ye.shift(1)
    if len(prev):
        prev.iloc[0] = capital
    yearly = (ye / prev - 1.0) * 100.0
    return {str(idx.year): round(float(v), 1) for idx, v in yearly.items()}


def main() -> None:
    from tradingos.analytics.metrics import compute_metrics
    from tradingos.experiments.db import session_scope
    from tradingos.experiments.models import ExperimentRun
    from tradingos.experiments.runner import code_git_hash

    settings = get_settings()
    print(f"data_dir = {settings.data_dir.resolve()}", flush=True)
    store = BarStore(settings)
    with open(SCRATCH / "us1500.csv", newline="") as fh:
        pool = [r["Symbol"] for r in csv.DictReader(fh)]
    stored = set(store.symbols(Timeframe.DAY))
    universe = sorted(set(pool) & stored - {REGIME_SYMBOL})
    print(f"pool={len(pool)} stored={len(stored)} universe(pool∩store)={len(universe)}",
          flush=True)

    md_all = store.load_market_data(universe + [REGIME_SYMBOL], Timeframe.DAY,
                                    start=None, end=None, adjusted=False)
    # end = latest available bar across the loaded frames
    last_ts = max(md_all.full_frame(s).index.max() for s in md_all.symbols)
    end = last_ts.date()
    print(f"latest available bar = {end}", flush=True)

    cfg = make_config(universe, end)
    family = f"adhoc_{TAG}"
    run_ts = datetime.now()
    run_dir = (settings.artifacts_dir / "adhoc" / family
               / run_ts.strftime("%Y-%m-%d_%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=True)

    started = datetime.now()
    res = EventEngine().run(cfg, md_all, make_universe_resolver(settings))
    finished = datetime.now()
    metrics = compute_metrics(res)

    neq = res.equity.sort_index()
    geq = res.gross_equity.sort_index()
    npnl = float(neq.iloc[-1]) - CAPITAL
    gpnl = float(geq.iloc[-1]) - CAPITAL

    dd = neq / neq.cummax() - 1.0
    dd_trough_ts = dd.idxmin()
    dd_depth = float(dd.min())

    trades = pd.DataFrame([{
        "symbol": t.symbol, "qty": t.qty,
        "entry_ts": t.entry_ts, "exit_ts": t.exit_ts,
        "entry_price": t.entry_price, "exit_price": t.exit_price,
        "gross_pnl": round(t.gross_pnl, 0), "costs": round(t.costs, 0),
        "net_pnl": round(t.net_pnl, 0), "exit_reason": t.exit_reason,
    } for t in res.trades])

    stats = {
        "variant": "st_gate", "market": "US",
        "kind": f"portfolio top-25, dynamic top-{TOP_N}",
        "window": {"start": START.isoformat(), "end": end.isoformat()},
        "capital": CAPITAL,
        "net_return_pct": round(npnl / CAPITAL * 100, 1),
        "net_max_dd_pct": round(dd_depth * 100, 1),
        "max_dd_trough": dd_trough_ts.date().isoformat(),
        "total_trades": len(res.trades),
        "total_charges": round(gpnl - npnl, 0),
        "sharpe": metrics.get("sharpe"),
        "cagr": metrics.get("cagr"),
        "vol": metrics.get("vol"),
        "final_equity": round(float(neq.iloc[-1]), 0),
        "exit_reasons": (trades.exit_reason.value_counts().to_dict()
                         if len(trades) else {}),
    }
    per_year = yearly_net_returns(neq, CAPITAL)

    neq.to_csv(run_dir / "net_equity_curve.csv")
    trades.to_csv(run_dir / "trades.csv", index=False)
    if len(trades):
        (trades.groupby("symbol")
         .agg(trades=("net_pnl", "size"), net_pnl=("net_pnl", "sum"),
              gross_pnl=("gross_pnl", "sum"), costs=("costs", "sum"))
         .sort_values("net_pnl", ascending=False)
         .to_csv(run_dir / "per_stock_pnl.csv"))
    (run_dir / "summary.json").write_text(
        json.dumps({**stats, "per_year_net_pct": per_year,
                    "warnings": list(res.warnings)}, indent=2, default=str))

    with session_scope(settings) as session:
        session.add(experiment_row(
            ExperimentRun, family, "st_gate", cfg, res, metrics, started,
            finished, run_dir, code_git_hash(), md_all.snapshot_id, len(neq)))

    print(json.dumps(stats, default=str), flush=True)
    print("PER_YEAR_NET_PCT " + json.dumps(per_year), flush=True)
    print(f"MAX_DD {round(dd_depth*100,1)}% trough {dd_trough_ts.date()}", flush=True)
    print(f"warnings: {list(res.warnings)}", flush=True)
    print(f"artifacts -> {run_dir}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
