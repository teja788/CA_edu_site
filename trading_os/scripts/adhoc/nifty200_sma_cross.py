"""NIFTY 200: long while close > own 200-SMA, sell when it crosses below.

No stop-loss. Per-stock independent runs (Rs 2L each) + combined view.
Reported returns are NET of brokerage/charges (owner preference); gross
figures are persisted in the artifacts alongside.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from datetime import date, datetime

import pandas as pd

from tradingos.config.schemas import (
    EngineMode,
    ExecutionSpec,
    FilterSpec,
    RebalanceSpec,
    SelectionSpec,
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

SCRATCH = str(Path(__file__).resolve().parent)  # universe CSVs live next to the scripts
START = date(2021, 7, 13)
END = date(2026, 7, 10)
CAPITAL = 200_000.0
FAMILY = "adhoc_sma200_cross_nifty200"


def load_symbols() -> list[str]:
    with open(f"{SCRATCH}/nifty200.csv", newline="") as fh:
        return [row["Symbol"].strip() for row in csv.DictReader(fh)]


def config_for(sym: str) -> StrategyConfig:
    return StrategyConfig(
        name=f"sma200_cross_{sym}",
        engine=EngineMode.EVENT,
        start=START,
        end=END,
        capital=CAPITAL,
        universe=UniverseSpec(symbols=[sym], point_in_time=False),
        filters=[FilterSpec(name="index_above_ma", params={"window": 200})],
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=1.0),
        rebalance=RebalanceSpec(frequency="daily"),
        execution=ExecutionSpec(timing="next_open", max_participation=0.05),
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

    symbols = load_symbols()
    settings = get_settings()
    store = BarStore(settings)
    available = set(store.symbols(Timeframe.DAY))
    missing = [s for s in symbols if s not in available]

    run_ts = datetime.now()
    run_dir = (settings.artifacts_dir / "adhoc" / FAMILY
               / run_ts.strftime("%Y-%m-%d_%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=True)
    git_hash = code_git_hash()

    rows = []
    net_curves: dict[str, pd.Series] = {}
    db_rows: list[ExperimentRun] = []

    for sym in symbols:
        if sym not in available:
            rows.append({"symbol": sym, "status": "NO DATA"})
            continue
        md = store.load_market_data([sym], Timeframe.DAY, start=None, end=None)
        frame = md.full_frame(sym)
        if frame.empty:
            rows.append({"symbol": sym, "status": "NO DATA"})
            continue
        data = MarketData({sym: frame}, timeframe=Timeframe.DAY,
                          snapshot_id=md.snapshot_id)
        cfg = config_for(sym)
        started = datetime.now()
        res = EventEngine().run(cfg, data, StaticUniverseResolver())
        finished = datetime.now()
        metrics = compute_metrics(res)
        geq = res.gross_equity.sort_index()
        neq = res.equity.sort_index()
        net_curves[sym] = neq
        closed = list(res.trades)
        gross_wins = [t for t in closed if (t.exit_price - t.entry_price) * t.qty > 0]
        gpnl = float(geq.iloc[-1]) - CAPITAL if len(geq) else 0.0
        npnl = float(neq.iloc[-1]) - CAPITAL if len(neq) else 0.0
        rows.append({
            "symbol": sym,
            "status": "ok",
            "bars": len(frame),
            "trades": len(closed),
            "win_rate_gross": round(len(gross_wins) / len(closed) * 100, 1) if closed else 0.0,
            "gross_pnl": round(gpnl, 0),
            "gross_return_pct": round(gpnl / CAPITAL * 100, 1),
            "net_pnl": round(npnl, 0),
            "net_return_pct": round(npnl / CAPITAL * 100, 1),
            "charges": round(gpnl - npnl, 0),
            "net_max_dd_pct": round(max_drawdown(neq) * 100, 1),
        })
        db_rows.append(ExperimentRun(
            family=FAMILY,
            variant_name=sym,
            config_hash=cfg.config_hash(),
            config_json=json.dumps(cfg.model_dump(mode="json")),
            overrides_json="{}",
            code_git_hash=git_hash,
            snapshot_id=md.snapshot_id,
            engine="event",
            status="done",
            started_at=started,
            finished_at=finished,
            artifacts_path=str(run_dir),
            sharpe=metrics.get("sharpe"),
            cagr=metrics.get("cagr"),
            max_drawdown=metrics.get("max_drawdown"),
            calmar=metrics.get("calmar"),
            vol=metrics.get("vol"),
            total_costs_pct=metrics.get("total_costs_pct"),
            final_equity=metrics.get("final_equity"),
            n_trades=metrics.get("n_trades"),
            n_bars=len(neq),
            ret_skew=metrics.get("ret_skew"),
            ret_kurt=metrics.get("ret_kurt"),
            metrics_json=json.dumps(metrics),
            warnings_json=json.dumps(list(res.warnings)),
        ))

    with session_scope(settings) as session:
        for r in db_rows:
            session.add(r)

    df = pd.DataFrame(rows)
    df.to_csv(run_dir / "per_stock_results.csv", index=False)
    ok = df[df["status"] == "ok"].copy().sort_values("net_pnl", ascending=False)

    combined_stats: dict[str, object] = {}
    if net_curves:
        idx = sorted(set().union(*[set(c.index) for c in net_curves.values()]))
        combined = pd.DataFrame(index=pd.Index(idx))
        for sym, c in net_curves.items():
            combined[sym] = c.reindex(combined.index).ffill().fillna(CAPITAL)
        total = combined.sum(axis=1)
        n = len(net_curves)
        combined_stats = {
            "stocks": n,
            "capital_deployed": CAPITAL * n,
            "final_net_equity": round(float(total.iloc[-1]), 0),
            "net_pnl": round(float(total.iloc[-1]) - CAPITAL * n, 0),
            "net_return_pct": round((float(total.iloc[-1]) / (CAPITAL * n) - 1) * 100, 1),
            "net_max_drawdown_pct": round(max_drawdown(total) * 100, 1),
            "total_charges": round(float(ok["charges"].sum()), 0),
            "gross_return_pct": round(float(ok["gross_pnl"].sum()) / (CAPITAL * n) * 100, 1),
            "profitable_stocks": int((ok["net_pnl"] > 0).sum()),
            "total_trades": int(ok["trades"].sum()),
        }
        total.to_csv(run_dir / "combined_net_equity_curve.csv")

    summary = {
        "family": FAMILY,
        "run_at": run_ts.isoformat(timespec="seconds"),
        "strategy": ("long while close > own 200-SMA (entry next open), sell "
                     "next open after close crosses below 200-SMA; NO stop"),
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "capital_per_stock": CAPITAL,
        "reporting": "returns NET of charges (owner pref); gross in per-stock rows",
        "code_git_hash": git_hash,
        "caveats": [
            "survivorship bias: today's NIFTY 200 constituents for all 5 years",
            "price-return data (no dividends)",
            "level rule: re-entry next day above SMA, not strict re-cross",
        ],
        "combined": combined_stats,
        "missing_symbols": missing,
        "per_stock": rows,
    }
    (run_dir / "results.json").write_text(json.dumps(summary, indent=2, default=str))

    print(f"ran {len(ok)}/{len(symbols)} symbols; artifacts -> {run_dir}")
    if missing:
        print(f"missing data ({len(missing)}): {', '.join(missing[:10])}"
              + (" ..." if len(missing) > 10 else ""))
    print(json.dumps(combined_stats, indent=2))
    print("\ntop 5 by gross pnl:")
    print(ok.head(5)[["symbol", "net_pnl", "net_return_pct", "net_max_dd_pct", "trades"]]
          .to_string(index=False))
    print("\nbottom 5:")
    print(ok.tail(5)[["symbol", "net_pnl", "net_return_pct", "net_max_dd_pct", "trades"]]
          .to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
