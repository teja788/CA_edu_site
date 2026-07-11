"""Eight variants of the NIFTY 200 trend system, compared on one window.

V1-V5 are per-stock independent systems (Rs 2L per stock, like the baseline);
V6-V8 are true portfolio strategies (one Rs 4 crore pot, top-25 selection).
All reported returns NET of charges. Everything persisted to the experiments
DB + timestamped artifacts (owner standing rules).
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

SCRATCH = str(Path(__file__).resolve().parent)  # universe CSVs live next to the scripts
START = date(2021, 7, 13)
END = date(2026, 7, 10)
PER_STOCK_CAPITAL = 200_000.0
PORTFOLIO_CAPITAL = 40_000_000.0
REGIME_SYMBOL = "NIFTYBEES"


def load_symbols() -> list[str]:
    with open(f"{SCRATCH}/nifty200.csv", newline="") as fh:
        return [row["Symbol"].strip() for row in csv.DictReader(fh)]


def _base(name: str, capital: float, symbols: list[str]) -> dict:
    return dict(
        name=name,
        engine=EngineMode.EVENT,
        start=START,
        end=END,
        capital=capital,
        universe=UniverseSpec(symbols=symbols, point_in_time=False),
        execution=ExecutionSpec(timing="next_open", max_participation=0.05),
    )


def per_stock_config(variant: str, sym: str) -> StrategyConfig:
    b = _base(f"{variant}_{sym}", PER_STOCK_CAPITAL, [sym])
    single = dict(
        selection=SelectionSpec(method="top_n", n=1, exit_rank=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=1.0),
    )
    if variant == "v1_weekly":
        return StrategyConfig(
            **b, **single,
            filters=[FilterSpec(name="index_above_ma", params={"window": 200})],
            rebalance=RebalanceSpec(frequency="weekly"),
        )
    if variant == "v2_golden_cross":
        return StrategyConfig(
            **b, **single,
            filters=[FilterSpec(name="fast_ma_above_slow_ma",
                                params={"fast": 50, "slow": 200})],
            rebalance=RebalanceSpec(frequency="daily"),
        )
    if variant == "v3_band":
        return StrategyConfig(
            **b, **single,
            filters=[FilterSpec(name="above_ma_band",
                                params={"window": 200, "entry_mult": 1.02,
                                        "exit_mult": 0.98})],
            rebalance=RebalanceSpec(frequency="daily"),
        )
    if variant == "v4_confirm":
        return StrategyConfig(
            **b, **single,
            filters=[FilterSpec(name="above_ma_confirm",
                                params={"window": 200, "days": 3})],
            rebalance=RebalanceSpec(frequency="daily"),
        )
    if variant == "v5_wide_stop":
        return StrategyConfig(
            **b, **single,
            filters=[FilterSpec(name="index_above_ma", params={"window": 200})],
            overlays=[OverlaySpec(name="trailing_stop_atr",
                                  params={"atr_window": 14, "multiple": 5.0})],
            rebalance=RebalanceSpec(frequency="daily"),
        )
    raise ValueError(variant)


def portfolio_config(variant: str, symbols: list[str]) -> StrategyConfig:
    b = _base(variant, PORTFOLIO_CAPITAL, symbols)
    mom = dict(
        signals=[SignalSpec(id="mom", name="return_over_window",
                            params={"window": 252, "skip": 21})],
        score=ScoreSpec(type="weighted_zscore", weights={"mom": 1.0}),
        selection=SelectionSpec(method="top_n", n=25, exit_rank=35),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
    )
    sma_gate = FilterSpec(name="index_above_ma", params={"window": 200})
    regime_gate = FilterSpec(name="index_above_ma",
                             params={"window": 200, "symbol": REGIME_SYMBOL})
    if variant == "v6_momentum_top25":
        return StrategyConfig(
            **b, **mom,
            filters=[sma_gate],
            sizing=SizingSpec(method="equal_weight", max_position_pct=0.05),
        )
    if variant == "v7_momentum_regime":
        return StrategyConfig(
            **b, **mom,
            filters=[sma_gate, regime_gate],
            sizing=SizingSpec(method="equal_weight", max_position_pct=0.05),
        )
    if variant == "v8_momentum_invvol":
        return StrategyConfig(
            **b, **mom,
            filters=[sma_gate],
            sizing=SizingSpec(method="inverse_volatility", max_position_pct=0.05),
        )
    raise ValueError(variant)


def max_drawdown(equity: pd.Series) -> float:
    if len(equity) == 0:
        return 0.0
    peak = equity.cummax()
    return float((equity / peak - 1.0).min())


def experiment_row(ExperimentRun, family, variant_name, cfg, res, metrics,
                   started, finished, run_dir, git_hash, snapshot_id, n_bars):
    return ExperimentRun(
        family=family, variant_name=variant_name,
        config_hash=cfg.config_hash(),
        config_json=json.dumps(cfg.model_dump(mode="json")),
        overrides_json="{}", code_git_hash=git_hash, snapshot_id=snapshot_id,
        engine="event", status="done", started_at=started,
        finished_at=finished, artifacts_path=str(run_dir),
        sharpe=metrics.get("sharpe"), cagr=metrics.get("cagr"),
        max_drawdown=metrics.get("max_drawdown"), calmar=metrics.get("calmar"),
        vol=metrics.get("vol"), total_costs_pct=metrics.get("total_costs_pct"),
        final_equity=metrics.get("final_equity"), n_trades=metrics.get("n_trades"),
        n_bars=n_bars, ret_skew=metrics.get("ret_skew"),
        ret_kurt=metrics.get("ret_kurt"), metrics_json=json.dumps(metrics),
        warnings_json=json.dumps(list(res.warnings)),
    )


def main() -> None:
    from tradingos.analytics.metrics import compute_metrics
    from tradingos.experiments.db import session_scope
    from tradingos.experiments.models import ExperimentRun
    from tradingos.experiments.runner import code_git_hash

    symbols = load_symbols()
    settings = get_settings()
    store = BarStore(settings)
    available = set(store.symbols(Timeframe.DAY))
    symbols = [s for s in symbols if s in available]

    run_ts = datetime.now()
    git_hash = code_git_hash()
    comparison: list[dict] = []

    # ---- per-stock variants V1-V5 --------------------------------------
    frames: dict[str, pd.DataFrame] = {}
    snap = ""
    for sym in symbols:
        md = store.load_market_data([sym], Timeframe.DAY, start=None, end=None)
        f = md.full_frame(sym)
        if not f.empty:
            frames[sym] = f
            snap = md.snapshot_id

    for variant in ["v1_weekly", "v2_golden_cross", "v3_band",
                    "v4_confirm", "v5_wide_stop"]:
        family = f"adhoc_{variant}_nifty200"
        run_dir = (settings.artifacts_dir / "adhoc" / family
                   / run_ts.strftime("%Y-%m-%d_%H%M%S"))
        run_dir.mkdir(parents=True, exist_ok=True)
        rows, curves, db_rows = [], {}, []
        for sym, frame in frames.items():
            data = MarketData({sym: frame}, timeframe=Timeframe.DAY,
                              snapshot_id=snap)
            cfg = per_stock_config(variant, sym)
            started = datetime.now()
            res = EventEngine().run(cfg, data, StaticUniverseResolver())
            finished = datetime.now()
            metrics = compute_metrics(res)
            neq = res.equity.sort_index()
            geq = res.gross_equity.sort_index()
            curves[sym] = neq
            npnl = float(neq.iloc[-1]) - PER_STOCK_CAPITAL if len(neq) else 0.0
            gpnl = float(geq.iloc[-1]) - PER_STOCK_CAPITAL if len(geq) else 0.0
            rows.append({"symbol": sym, "trades": len(res.trades),
                         "net_pnl": round(npnl, 0), "gross_pnl": round(gpnl, 0),
                         "charges": round(gpnl - npnl, 0),
                         "net_max_dd_pct": round(max_drawdown(neq) * 100, 1)})
            db_rows.append(experiment_row(
                ExperimentRun, family, sym, cfg, res, metrics, started,
                finished, run_dir, git_hash, snap, len(neq)))
        with session_scope(settings) as session:
            for r in db_rows:
                session.add(r)
        df = pd.DataFrame(rows)
        df.to_csv(run_dir / "per_stock_results.csv", index=False)
        idx = sorted(set().union(*[set(c.index) for c in curves.values()]))
        combined = pd.DataFrame(index=pd.Index(idx))
        for sym, c in curves.items():
            combined[sym] = c.reindex(combined.index).ffill().fillna(PER_STOCK_CAPITAL)
        total = combined.sum(axis=1)
        deployed = PER_STOCK_CAPITAL * len(curves)
        stats = {
            "variant": variant, "kind": "per-stock x200",
            "net_return_pct": round((float(total.iloc[-1]) / deployed - 1) * 100, 1),
            "net_max_dd_pct": round(max_drawdown(total) * 100, 1),
            "total_trades": int(df["trades"].sum()),
            "total_charges": round(float(df["charges"].sum()), 0),
            "profitable_stocks": int((df["net_pnl"] > 0).sum()),
        }
        total.to_csv(run_dir / "combined_net_equity_curve.csv")
        (run_dir / "summary.json").write_text(json.dumps(stats, indent=2))
        comparison.append(stats)
        print(json.dumps(stats))

    # ---- portfolio variants V6-V8 ---------------------------------------
    md_all = store.load_market_data(sorted(set(symbols) | {REGIME_SYMBOL}),
                                    Timeframe.DAY, start=None, end=None)
    for variant in ["v6_momentum_top25", "v7_momentum_regime",
                    "v8_momentum_invvol"]:
        family = f"adhoc_{variant}_nifty200"
        run_dir = (settings.artifacts_dir / "adhoc" / family
                   / run_ts.strftime("%Y-%m-%d_%H%M%S"))
        run_dir.mkdir(parents=True, exist_ok=True)
        cfg = portfolio_config(variant, symbols)
        started = datetime.now()
        res = EventEngine().run(cfg, md_all, StaticUniverseResolver())
        finished = datetime.now()
        metrics = compute_metrics(res)
        neq = res.equity.sort_index()
        geq = res.gross_equity.sort_index()
        npnl = float(neq.iloc[-1]) - PORTFOLIO_CAPITAL
        gpnl = float(geq.iloc[-1]) - PORTFOLIO_CAPITAL
        stats = {
            "variant": variant, "kind": "portfolio top-25",
            "net_return_pct": round(npnl / PORTFOLIO_CAPITAL * 100, 1),
            "net_max_dd_pct": round(max_drawdown(neq) * 100, 1),
            "total_trades": len(res.trades),
            "total_charges": round(gpnl - npnl, 0),
            "sharpe": metrics.get("sharpe"),
        }
        neq.to_csv(run_dir / "net_equity_curve.csv")
        (run_dir / "summary.json").write_text(json.dumps(stats, indent=2))
        with session_scope(settings) as session:
            session.add(experiment_row(
                ExperimentRun, family, variant, cfg, res, metrics, started,
                finished, run_dir, git_hash, md_all.snapshot_id, len(neq)))
        comparison.append(stats)
        print(json.dumps(stats))

    out = settings.artifacts_dir / "adhoc" / f"variants_comparison_{run_ts.strftime('%Y-%m-%d_%H%M%S')}.json"
    out.write_text(json.dumps({
        "run_at": run_ts.isoformat(timespec="seconds"),
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "baseline_reference": "adhoc_sma200_cross_nifty200 = +108.9% net, dd -14.4%, 6298 trades",
        "caveats": ["survivorship: today's NIFTY 200 for all 5y",
                    "price returns, no dividends",
                    "V7 regime proxy = NIFTYBEES ETF"],
        "variants": comparison,
    }, indent=2))
    print(f"\ncomparison -> {out}")


if __name__ == "__main__":
    sys.exit(main())
