"""Four momentum variants on a DYNAMIC top-200 universe, recomputed monthly.

Point-in-time universe from Zerodha data alone: at every rebalance the
candidate set is the top 200 names by trailing 126-day median traded value
(close * volume), computed from bars <= the decision date only. Newly listed
names qualify once they have 126 trading days of history (~6 months, akin to
real index seasoning rules); names that decay out of the top 200 drop out at
the next rebalance. Note 12-1 momentum itself needs ~273 bars, so a new
listing enters the *universe* at ~6 months but can't be *selected* before
~13 months — inherent to the signal, not the resolver.

Variants and everything else identical to nse2000_momentum.py:
m1 momentum+SMA gate, m2 returns-only, m3/m4 = +3x ATR(14) stop.
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
from tradingos.engine.dataview import MarketData
from tradingos.engine.event.engine import EventEngine

SCRATCH = Path(__file__).resolve().parent
START = date(2021, 7, 13)
END = date(2026, 7, 10)
CAPITAL = 40_000_000.0
MIN_TRADED_VALUE = 50_000_000.0
RANK_LOOKBACK = 126  # trading days of traded value; also the seasoning minimum

VARIANTS = ["m1_sma_gate", "m2_returns_only", "m3_sma_gate_atr3", "m4_returns_atr3"]

# optional args: top-N (int, or "all"), family tag, comma-separated variants
_n_arg = sys.argv[1] if len(sys.argv) > 1 else "200"
TOP_N = 10_000 if _n_arg == "all" else int(_n_arg)
TAG = sys.argv[2] if len(sys.argv) > 2 else "nse200dyn"
if len(sys.argv) > 3:
    VARIANTS = [v for v in sys.argv[3].split(",") if v in VARIANTS]


class DynamicTopNResolver:
    """Top-N by trailing median traded value, causal as of the resolve date.

    The panel row used for a resolve on date D is the last row with index
    <= D, and each cell is a median over the RANK_LOOKBACK bars ending at
    that row (min_periods = RANK_LOOKBACK -> NaN until seasoned).
    """

    def __init__(self, data: MarketData, top_n: int) -> None:
        tv = {}
        for sym in data.symbols:
            f = data.full_frame(sym)
            tv[sym] = (f["close"] * f["volume"]).rolling(
                RANK_LOOKBACK, min_periods=RANK_LOOKBACK).median()
        self._panel = pd.DataFrame(tv).sort_index()
        self._top_n = top_n
        self._cache: dict[date, list[str]] = {}
        self._warnings: list[str] = []

    @property
    def warnings(self) -> list[str]:
        return self._warnings

    def membership(self, on: date) -> list[str]:
        if on not in self._cache:
            rows = self._panel.loc[:pd.Timestamp(on)]
            if rows.empty:
                self._cache[on] = []
            else:
                row = rows.iloc[-1].dropna()
                self._cache[on] = sorted(
                    row.sort_values(ascending=False).head(self._top_n).index)
        return self._cache[on]

    def resolve(self, spec: UniverseSpec, on: date, data: MarketData) -> list[str]:
        return self.membership(on)


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
    with open(SCRATCH / "nse2000.csv", newline="") as fh:
        syms = [r["Symbol"] for r in csv.DictReader(fh)]
    symbols = sorted(set(syms) & set(store.symbols(Timeframe.DAY)))
    md_all = store.load_market_data(symbols, Timeframe.DAY, start=None, end=None)
    resolver = DynamicTopNResolver(md_all, TOP_N)

    # membership churn stats over the run's month starts
    months = pd.date_range(START, END, freq="MS")
    sets = [set(resolver.membership(m.date())) for m in months]
    ever = set().union(*sets)
    turnover = [len(sets[i] ^ sets[i - 1]) / 2 for i in range(1, len(sets))]
    print(json.dumps({
        "months": len(sets), "ever_member": len(ever),
        "avg_monthly_adds_drops": round(sum(turnover) / len(turnover), 1),
    }), flush=True)

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
           / f"{TAG}_momentum_comparison_{run_ts.strftime('%Y-%m-%d_%H%M%S')}.json")
    out.write_text(json.dumps({
        "run_at": run_ts.isoformat(timespec="seconds"),
        "window": {"start": START.isoformat(), "end": END.isoformat()},
        "universe": f"dynamic top-{TOP_N} by trailing {RANK_LOOKBACK}d median "
                    "traded value, recomputed each rebalance, new listings "
                    "eligible after 126 bars",
        "reference": "static 2020-vintage top-200 m2 = +183.2%; "
                     "current-constituent NIFTY200 v6 = +389.6%",
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
