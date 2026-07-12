"""Tier-2 tests on the champion b2d: mcap universe / churn veto / both.

Three variants, all on the b2d config (vol-adj 6m+12m score, exit 50,
graded asymmetric regime gate), 2021-07-13..2026-07-10, Rs 4cr:

  t2a_mcap   universe = top-1000 by trailing 126d median MARKET CAP
             (snapshot shares x adjusted close via data/shares.py) instead
             of by traded value; existing Rs 5cr traded-value floor stays
             downstream. The Capitalmind pattern: size ranks, liquidity
             only floors.
  t2b_churn  universe = the usual traded-value top-1000 MINUS the top
             churn quintile at each rebalance (churn = 126d median traded
             value / mcap, the BacktestIndia scaled-turnover split; names
             without a shares snapshot are kept — only measured churn
             vetoes).
  t2c_both   mcap-ranked top-1000 minus the churn top quintile.

Reference: b2d = +283.4% / DD -24.8% / Sharpe 1.32 (run 1333).
Caveat: mcap is NOT point-in-time share counts (issuance drift between
snapshots) — quintile/rank consumers only, per docs/assumptions.md.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.shares import latest_shares, scaled_turnover_panel
from tradingos.data.store import BarStore
from tradingos.engine.dataview import MarketData
from tradingos.engine.event.engine import EventEngine
from batch1_m2_improvements import REGIME_SYMBOL, SeasonedTopNResolver
from batch2_m2_overlays import make_config
from nse200_dynamic import max_drawdown

SCRATCH = Path(__file__).resolve().parent
CAPITAL = 40_000_000.0
TOP_N = 1000
RANK_LOOKBACK = 126
CHURN_QUANTILE = 0.80  # veto members above the 80th churn percentile
TAG = "tier2_b2d"

VARIANTS = ["t2a_mcap", "t2b_churn", "t2c_both"]
if len(sys.argv) > 1:
    VARIANTS = [v for v in sys.argv[1].split(",") if v in VARIANTS]


class McapTopNResolver(SeasonedTopNResolver):
    """Top-N by trailing 126d median MARKET CAP over the candidate pool."""

    def __init__(self, data: MarketData, top_n: int, symbols: list[str],
                 shares: dict[str, int]) -> None:
        mc = {}
        for sym in symbols:
            if sym not in shares:
                continue  # no snapshot -> cannot be ranked by mcap
            f = data.full_frame(sym)
            mc[sym] = (f["close"] * shares[sym]).rolling(
                RANK_LOOKBACK, min_periods=RANK_LOOKBACK).median()
        self._panel = pd.DataFrame(mc).sort_index()
        self._top_n = top_n
        self._cache = {}
        self._warnings = []


class ChurnVetoResolver:
    """Wrap a base resolver; drop members above the churn quantile as of the
    resolve date. Members without measurable churn are KEPT."""

    def __init__(self, base, churn: pd.DataFrame, quantile: float) -> None:
        self._base = base
        self._churn = churn.sort_index()
        self._q = quantile
        self._cache: dict[date, list[str]] = {}
        self._warnings: list[str] = []

    @property
    def warnings(self) -> list[str]:
        return self._warnings

    def membership(self, on: date) -> list[str]:
        if on not in self._cache:
            members = self._base.membership(on)
            rows = self._churn.loc[:pd.Timestamp(on)]
            if rows.empty or not members:
                self._cache[on] = members
            else:
                row = rows.iloc[-1]
                measured = row.reindex(members).dropna()
                if measured.empty:
                    self._cache[on] = members
                else:
                    cutoff = measured.quantile(self._q)
                    vetoed = set(measured[measured > cutoff].index)
                    self._cache[on] = [s for s in members if s not in vetoed]
        return self._cache[on]

    def resolve(self, spec, on: date, data: MarketData) -> list[str]:
        return self.membership(on)


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
    shares = latest_shares(settings)
    covered = sorted(set(universe) & set(shares))
    print(json.dumps({"pool": len(universe), "with_shares": len(covered)}),
          flush=True)

    churn = scaled_turnover_panel(
        store.load_market_data(covered, Timeframe.DAY, start=None, end=None),
        shares, window=RANK_LOOKBACK)

    tv_resolver = SeasonedTopNResolver(md_all, TOP_N, universe)
    mcap_resolver = McapTopNResolver(md_all, TOP_N, universe, shares)
    resolvers = {
        "t2a_mcap": mcap_resolver,
        "t2b_churn": ChurnVetoResolver(tv_resolver, churn, CHURN_QUANTILE),
        "t2c_both": ChurnVetoResolver(mcap_resolver, churn, CHURN_QUANTILE),
    }

    run_ts = datetime.now()
    git_hash = code_git_hash()
    comparison: list[dict] = []

    for variant in VARIANTS:
        family = f"adhoc_{variant}_{TAG}"
        run_dir = (settings.artifacts_dir / "adhoc" / family
                   / run_ts.strftime("%Y-%m-%d_%H%M%S"))
        run_dir.mkdir(parents=True, exist_ok=True)
        cfg = make_config("b2d_graded_score", universe).model_copy(
            update={"name": f"{TAG}_{variant}"})
        started = datetime.now()
        res = EventEngine().run(cfg, md_all, resolvers[variant])
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
            "variant": variant, "kind": "b2d on tier-2 universe",
            "net_return_pct": round(npnl / CAPITAL * 100, 1),
            "net_max_dd_pct": round(max_drawdown(neq) * 100, 1),
            "total_trades": len(res.trades),
            "total_charges": round(gpnl - npnl, 0),
            "sharpe": metrics.get("sharpe"),
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
           / f"{TAG}_comparison_{run_ts.strftime('%Y-%m-%d_%H%M%S')}.json")
    out.write_text(json.dumps({
        "run_at": run_ts.isoformat(timespec="seconds"),
        "baseline": "b2d = +283.4% / -24.8% / 1.32 (run 1333)",
        "churn_quantile_veto": CHURN_QUANTILE,
        "caveats": [
            "mcap = current snapshot shares x adjusted close (NOT PIT counts)",
            "delisted names absent from Kite data",
            "price returns, no dividends; zerodha_2026 charges throughout",
        ],
        "variants": comparison,
    }, indent=2))
    print(f"comparison -> {out}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
