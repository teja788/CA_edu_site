"""Re-run V6 (momentum top-25, NIFTY 200) to persist trade-level detail.

Identical config to nifty200_variants.py's v6; adds trades.csv and
per_stock_pnl.csv to the artifacts so which-stock-did-well questions are
answerable without another rerun. Persisted per the standing rules.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime

import pandas as pd

from nifty200_variants import (
    PORTFOLIO_CAPITAL,
    REGIME_SYMBOL,
    experiment_row,
    load_symbols,
    max_drawdown,
    portfolio_config,
)
from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore
from tradingos.engine.base import StaticUniverseResolver
from tradingos.engine.event.engine import EventEngine


def main() -> None:
    from tradingos.analytics.metrics import compute_metrics
    from tradingos.experiments.db import session_scope
    from tradingos.experiments.models import ExperimentRun
    from tradingos.experiments.runner import code_git_hash

    settings = get_settings()
    store = BarStore(settings)
    available = set(store.symbols(Timeframe.DAY))
    symbols = [s for s in load_symbols() if s in available]

    run_ts = datetime.now()
    family = "adhoc_v6_momentum_top25_nifty200"
    run_dir = (settings.artifacts_dir / "adhoc" / family
               / run_ts.strftime("%Y-%m-%d_%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=True)

    md_all = store.load_market_data(sorted(set(symbols) | {REGIME_SYMBOL}),
                                    Timeframe.DAY, start=None, end=None)
    cfg = portfolio_config("v6_momentum_top25", symbols)
    started = datetime.now()
    res = EventEngine().run(cfg, md_all, StaticUniverseResolver())
    finished = datetime.now()
    metrics = compute_metrics(res)

    neq = res.equity.sort_index()
    npnl = float(neq.iloc[-1]) - PORTFOLIO_CAPITAL
    print(json.dumps({
        "net_return_pct": round(npnl / PORTFOLIO_CAPITAL * 100, 1),
        "net_max_dd_pct": round(max_drawdown(neq) * 100, 1),
        "total_trades": len(res.trades),
    }))

    trades = pd.DataFrame([{
        "symbol": t.symbol, "qty": t.qty,
        "entry_ts": t.entry_ts, "exit_ts": t.exit_ts,
        "entry_price": t.entry_price, "exit_price": t.exit_price,
        "gross_pnl": round(t.gross_pnl, 0), "costs": round(t.costs, 0),
        "net_pnl": round(t.net_pnl, 0), "exit_reason": t.exit_reason,
    } for t in res.trades])
    trades.to_csv(run_dir / "trades.csv", index=False)

    per_stock = (trades.groupby("symbol")
                 .agg(trades=("net_pnl", "size"), net_pnl=("net_pnl", "sum"),
                      gross_pnl=("gross_pnl", "sum"), costs=("costs", "sum"))
                 .sort_values("net_pnl", ascending=False))
    per_stock.to_csv(run_dir / "per_stock_pnl.csv")

    neq.to_csv(run_dir / "net_equity_curve.csv")
    (run_dir / "summary.json").write_text(json.dumps({
        "variant": "v6_momentum_top25", "kind": "portfolio top-25",
        "note": "rerun of 2026-07-11_180115 to capture trade detail",
        "net_return_pct": round(npnl / PORTFOLIO_CAPITAL * 100, 1),
        "net_max_dd_pct": round(max_drawdown(neq) * 100, 1),
        "total_trades": len(res.trades),
        "sharpe": metrics.get("sharpe"),
    }, indent=2))

    with session_scope(settings) as session:
        session.add(experiment_row(
            ExperimentRun, family, "v6_momentum_top25", cfg, res, metrics,
            started, finished, run_dir, code_git_hash(), md_all.snapshot_id,
            len(neq)))
    print(f"artifacts -> {run_dir}")


if __name__ == "__main__":
    sys.exit(main())
