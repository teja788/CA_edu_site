"""Batch 1 of the momentum improvement plan: config-only variants on dyn-1000 m2.

Baseline: m2 = 12-1 momentum top-25 equal-weight monthly on the dynamic
top-1000-by-liquidity universe (+296.3%, Sharpe 1.22, DD -32.9%). Seven
variants, per docs/momentum_research_notes.md "Agreed test plan":

  b1a_exit50      exit_rank 35 -> 50 (Novy-Marx/Velikov hysteresis, NSE buffers)
  b1b_exit60      exit_rank 35 -> 60
  b1c_nse_score   NSE-style score: 50/50 z-blend of 6m and 12m vol-adjusted
                  momentum (risk_adjusted_momentum, vol_window=252)
  b1d_score_exit50  b1c + exit_rank 50
  b1e_regime      binary NIFTYBEES 200-SMA regime gate (v7 transfer test)
  b1f_season252   new listings eligible after 252 bars (~12m) instead of 126
  b1g_fip         frog-in-the-pan: score = mom z + 0.5 * return_smoothness z

Universe and everything else identical to nse200_dynamic.py at N=1000.
NIFTYBEES is loaded for the regime frame only — excluded from the ranking
panel so the ETF can never enter the stock universe.
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
from tradingos.engine.dataview import MarketData
from tradingos.engine.event.engine import EventEngine
from nse200_dynamic import DynamicTopNResolver, max_drawdown

SCRATCH = Path(__file__).resolve().parent
START = date(2021, 7, 13)
END = date(2026, 7, 10)
CAPITAL = 40_000_000.0
MIN_TRADED_VALUE = 50_000_000.0
TOP_N = 1000
TAG = "nse1000dyn"
REGIME_SYMBOL = "NIFTYBEES"

VARIANTS = ["b1a_exit50", "b1b_exit60", "b1c_nse_score", "b1d_score_exit50",
            "b1e_regime", "b1f_season252", "b1g_fip"]
if len(sys.argv) > 1:
    VARIANTS = [v for v in sys.argv[1].split(",") if v in VARIANTS]


class SeasonedTopNResolver(DynamicTopNResolver):
    """DynamicTopNResolver over an explicit symbol list, with an optional
    longer listing-age requirement than the 126-bar ranking lookback."""

    def __init__(self, data: MarketData, top_n: int, symbols: list[str],
                 min_history: int = 126) -> None:
        tv = {}
        for sym in symbols:
            f = data.full_frame(sym)
            m = (f["close"] * f["volume"]).rolling(126, min_periods=126).median()
            if min_history > 126:
                m = m.where(f["close"].expanding().count() >= min_history)
            tv[sym] = m
        self._panel = pd.DataFrame(tv).sort_index()
        self._top_n = top_n
        self._cache = {}
        self._warnings = []


MOM = SignalSpec(id="mom", name="return_over_window",
                 params={"window": 252, "skip": 21})
RAM6 = SignalSpec(id="ram6", name="risk_adjusted_momentum",
                  params={"window": 126, "skip": 21, "vol_window": 252})
RAM12 = SignalSpec(id="ram12", name="risk_adjusted_momentum",
                   params={"window": 252, "skip": 21, "vol_window": 252})
FIP = SignalSpec(id="fip", name="return_smoothness", params={"window": 252})
REGIME_GATE = FilterSpec(name="index_above_ma",
                         params={"window": 200, "symbol": REGIME_SYMBOL})


def make_config(variant: str, symbols: list[str]) -> StrategyConfig:
    signals = [MOM]
    weights = {"mom": 1.0}
    exit_rank = 35
    filters: list[FilterSpec] = []
    if variant in ("b1c_nse_score", "b1d_score_exit50"):
        signals = [RAM6, RAM12]
        weights = {"ram6": 0.5, "ram12": 0.5}
    if variant == "b1g_fip":
        signals = [MOM, FIP]
        weights = {"mom": 1.0, "fip": 0.5}
    if variant in ("b1a_exit50", "b1d_score_exit50"):
        exit_rank = 50
    if variant == "b1b_exit60":
        exit_rank = 60
    if variant == "b1e_regime":
        filters = [REGIME_GATE]
    return StrategyConfig(
        name=f"{TAG}_{variant}",
        engine=EngineMode.EVENT,
        start=START,
        end=END,
        capital=CAPITAL,
        universe=UniverseSpec(symbols=symbols, point_in_time=False,
                              min_median_traded_value=MIN_TRADED_VALUE),
        execution=ExecutionSpec(timing="next_open", max_participation=0.05),
        signals=signals,
        score=ScoreSpec(type="weighted_zscore", weights=weights),
        selection=SelectionSpec(method="top_n", n=25, exit_rank=exit_rank),
        rebalance=RebalanceSpec(frequency="monthly", trading_day=1),
        sizing=SizingSpec(method="equal_weight", max_position_pct=0.05),
        filters=filters,
        overlays=[],
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
    resolvers = {
        126: SeasonedTopNResolver(md_all, TOP_N, universe, min_history=126),
        252: SeasonedTopNResolver(md_all, TOP_N, universe, min_history=252),
    }

    run_ts = datetime.now()
    git_hash = code_git_hash()
    comparison: list[dict] = []

    for variant in VARIANTS:
        family = f"adhoc_{variant}_{TAG}"
        run_dir = (settings.artifacts_dir / "adhoc" / family
                   / run_ts.strftime("%Y-%m-%d_%H%M%S"))
        run_dir.mkdir(parents=True, exist_ok=True)
        cfg = make_config(variant, universe)
        resolver = resolvers[252 if variant == "b1f_season252" else 126]
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
           / f"{TAG}_batch1_comparison_{run_ts.strftime('%Y-%m-%d_%H%M%S')}.json")
    out.write_text(json.dumps({
        "run_at": run_ts.isoformat(timespec="seconds"),
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "universe": f"dynamic top-{TOP_N}, as nse200_dynamic.py "
                    "(b1f seasons new listings at 252 bars)",
        "baseline": "m2 dyn-1000 = +296.3%, Sharpe 1.22, DD -32.9% (run 1321)",
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
