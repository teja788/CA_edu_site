"""NIFTY 50: long above own 200-SMA with 3xATR(14) chandelier trailing stop.

Per-stock independent runs (Rs 2L capital each) + combined portfolio view.
Entry: first close above 200-SMA -> buy next open (daily rebalance).
Exit: chandelier stop (3xATR, closing basis) OR close below 200-SMA -> sell
next open. Re-entry: next day the stock is above its 200-SMA (level rule).
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime

import pandas as pd

from tradingos.config.schemas import (
    EngineMode,
    ExecutionSpec,
    FilterSpec,
    OverlaySpec,
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

SYMBOLS = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BEL", "BHARTIARTL",
    "CIPLA", "COALINDIA", "DRREDDY", "EICHERMOT", "ETERNAL",
    "GRASIM", "HCLTECH", "HDFCBANK", "HDFCLIFE", "HINDALCO",
    "HINDUNILVR", "ICICIBANK", "INDIGO", "INFY", "ITC",
    "JIOFIN", "JSWSTEEL", "KOTAKBANK", "LT", "M&M",
    "MARUTI", "MAXHEALTH", "NESTLEIND", "NTPC", "ONGC",
    "POWERGRID", "RELIANCE", "SBILIFE", "SHRIRAMFIN", "SBIN",
    "SUNPHARMA", "TCS", "TATACONSUM", "TMPV", "TATASTEEL",
    "TECHM", "TITAN", "TRENT", "ULTRACEMCO", "WIPRO",
]

START = date(2021, 7, 13)
END = date(2026, 7, 10)
CAPITAL = 200_000.0


def config_for(sym: str) -> StrategyConfig:
    return StrategyConfig(
        name=f"sma200_atr3_{sym}",
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
        overlays=[OverlaySpec(name="trailing_stop_atr",
                              params={"atr_window": 14, "multiple": 3.0})],
    )


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = equity / peak - 1.0
    return float(dd.min())


FAMILY = "adhoc_sma200_atr3_nifty50"


def main() -> None:
    from tradingos.analytics.metrics import compute_metrics
    from tradingos.experiments.db import session_scope
    from tradingos.experiments.models import ExperimentRun
    from tradingos.experiments.runner import code_git_hash

    settings = get_settings()
    store = BarStore(settings)
    full = store.load_market_data(SYMBOLS, Timeframe.DAY, start=None, end=None)

    run_ts = datetime.now()
    run_dir = (settings.artifacts_dir / "adhoc" / FAMILY
               / run_ts.strftime("%Y-%m-%d_%H%M%S"))
    run_dir.mkdir(parents=True, exist_ok=True)
    git_hash = code_git_hash()

    rows = []
    curves: dict[str, pd.Series] = {}
    all_warnings: dict[str, list[str]] = {}
    db_rows: list[ExperimentRun] = []

    for sym in SYMBOLS:
        frame = full.full_frame(sym) if sym in set(full.symbols) else None
        if frame is None or frame.empty:
            rows.append({"symbol": sym, "status": "NO DATA"})
            continue
        data = MarketData({sym: frame}, timeframe=Timeframe.DAY,
                          snapshot_id=full.snapshot_id)
        cfg = config_for(sym)
        started = datetime.now()
        res = EventEngine().run(cfg, data, StaticUniverseResolver())
        finished = datetime.now()
        metrics = compute_metrics(res)
        eq = res.equity.sort_index()
        curves[sym] = eq
        trades = res.trades
        closed = [t for t in trades]
        wins = [t for t in closed
                if (t.exit_price - t.entry_price) * t.qty
                - t.entry_costs - t.exit_costs > 0]
        pnl = float(eq.iloc[-1]) - CAPITAL if len(eq) else 0.0
        charges = sum(t.entry_costs + t.exit_costs for t in closed)
        stop_exits = sum(1 for t in closed if t.exit_reason == "trailing_stop")
        rows.append({
            "symbol": sym,
            "status": "ok",
            "bars": len(frame),
            "trades": len(closed),
            "wins": len(wins),
            "win_rate": (len(wins) / len(closed) * 100) if closed else 0.0,
            "stop_exits": stop_exits,
            "pnl": round(pnl, 0),
            "return_pct": round(pnl / CAPITAL * 100, 1),
            "max_dd_pct": round(max_drawdown(eq) * 100, 1) if len(eq) else 0.0,
            "charges": round(charges, 0),
        })
        if res.warnings:
            all_warnings[sym] = list(res.warnings)
        db_rows.append(ExperimentRun(
            family=FAMILY,
            variant_name=sym,
            config_hash=cfg.config_hash(),
            config_json=json.dumps(cfg.model_dump(mode="json")),
            overrides_json="{}",
            code_git_hash=git_hash,
            snapshot_id=full.snapshot_id,
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
            n_bars=len(eq),
            ret_skew=metrics.get("ret_skew"),
            ret_kurt=metrics.get("ret_kurt"),
            metrics_json=json.dumps(metrics),
            warnings_json=json.dumps(list(res.warnings)),
        ))

    with session_scope(settings) as session:
        for r in db_rows:
            session.add(r)
    print(f"registered {len(db_rows)} runs in experiments DB "
          f"(family={FAMILY}) at {settings.experiments_db_path}")

    df = pd.DataFrame(rows)
    df.to_csv(run_dir / "per_stock_results.csv", index=False)

    ok = df[df["status"] == "ok"].copy()
    print(f"ran {len(ok)}/{len(SYMBOLS)} symbols; artifacts -> {run_dir}")
    print(ok.sort_values("pnl", ascending=False).to_string(index=False))

    # combined portfolio = sum of the independent equity curves
    combined_stats: dict[str, float] = {}
    if curves:
        idx = sorted(set().union(*[set(c.index) for c in curves.values()]))
        combined = pd.DataFrame(index=pd.Index(idx))
        for sym, c in curves.items():
            combined[sym] = c.reindex(combined.index).ffill().fillna(CAPITAL)
        total = combined.sum(axis=1)
        n = len(curves)
        combined_stats = {
            "stocks": n,
            "capital_deployed": CAPITAL * n,
            "final_equity": round(float(total.iloc[-1]), 0),
            "total_pnl": round(float(total.iloc[-1]) - CAPITAL * n, 0),
            "total_return_pct": round((float(total.iloc[-1]) / (CAPITAL * n) - 1) * 100, 1),
            "max_drawdown_pct": round(max_drawdown(total) * 100, 1),
        }
        print("\n=== combined (sum of independent runs) ===")
        for k, v in combined_stats.items():
            print(f"{k}: {v:,}" if isinstance(v, float) else f"{k}: {v}")
        total.to_csv(run_dir / "combined_equity_curve.csv")

    summary = {
        "family": FAMILY,
        "run_at": run_ts.isoformat(timespec="seconds"),
        "strategy": ("long while close > own 200-SMA (entry next open after "
                     "cross), exit on 3xATR(14) chandelier trailing stop "
                     "(closing basis, next-open exit) or close < 200-SMA; "
                     "re-entry next day if above SMA (level rule)"),
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "capital_per_stock": CAPITAL,
        "costs": "zerodha_2026 CNC, liquidity-tier slippage defaults",
        "code_git_hash": git_hash,
        "snapshot_id": full.snapshot_id,
        "caveats": [
            "survivorship bias: today's NIFTY 50 constituents applied to all 5 years",
            "price-return data (no dividends imported); Kite bars adjusted as of fetch",
            "re-entry is level-based (above SMA next day), not strict re-cross",
        ],
        "combined": combined_stats,
        "per_stock": rows,
    }
    (run_dir / "results.json").write_text(json.dumps(summary, indent=2, default=str))

    if all_warnings:
        print("\n=== warnings (first per symbol) ===")
        for sym, ws in sorted(all_warnings.items()):
            print(f"{sym}: {ws[0]}" + (f" (+{len(ws)-1} more)" if len(ws) > 1 else ""))


if __name__ == "__main__":
    sys.exit(main())
