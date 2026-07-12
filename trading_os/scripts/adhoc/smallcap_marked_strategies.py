"""Marked strategies (b1d, b2d, + b2e) at a chosen per-position size.

Owner ask (Jul 12): rerun the strategies of record at retail position
sizes (originally Rs 10k/slot; argv[1] sets the per-slot rupees, default
10000; argv[2] optionally comma-separates variants). Capital = 25 x slot.
At small sizes the fixed cost floor (DP charge per scrip-day on sells) and
integer-share constraints (high-priced stocks exceed the slot) actually
bind, so this measures small-account viability, not just scaling. Equity
compounds fully — targets are recomputed from current equity each
rebalance, nothing is withdrawn.

Families: adhoc_{variant}_{slot}k_nse1000dyn.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore
from tradingos.engine.event.engine import EventEngine
from batch1_m2_improvements import SeasonedTopNResolver, REGIME_SYMBOL
from batch1_m2_improvements import make_config as b1_config
from batch2_m2_overlays import make_config as b2_config
from nse200_dynamic import max_drawdown

SCRATCH = Path(__file__).resolve().parent
PER_SLOT = float(sys.argv[1]) if len(sys.argv) > 1 else 10_000.0
CAPITAL = 25 * PER_SLOT
SLOT_TAG = f"{PER_SLOT / 1000:g}k"
TOP_N = 1000
TAG = "nse1000dyn"

MARKED = {
    "b1d_score_exit50": b1_config,
    "b2d_graded_score": b2_config,
    "b2e_full": b2_config,
}
if len(sys.argv) > 2:
    MARKED = {k: v for k, v in MARKED.items() if k in sys.argv[2].split(",")}


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

    for variant, make in MARKED.items():
        family = f"adhoc_{variant}_{SLOT_TAG}_{TAG}"
        run_dir = (settings.artifacts_dir / "adhoc" / family
                   / run_ts.strftime("%Y-%m-%d_%H%M%S"))
        run_dir.mkdir(parents=True, exist_ok=True)
        cfg = make(variant, universe).model_copy(
            update={"name": f"{TAG}_{variant}_{SLOT_TAG}", "capital": CAPITAL})
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
            "variant": f"{variant}_{SLOT_TAG}", "kind": f"Rs {PER_SLOT:g}/position, 25 slots",
            "capital": CAPITAL,
            "net_return_pct": round(npnl / CAPITAL * 100, 1),
            "gross_return_pct": round(gpnl / CAPITAL * 100, 1),
            "net_max_dd_pct": round(max_drawdown(neq) * 100, 1),
            "total_trades": len(res.trades),
            "total_charges": round(gpnl - npnl, 0),
            "charges_pct_of_gross_pnl": (round((gpnl - npnl) / gpnl * 100, 1)
                                         if gpnl else None),
            "sharpe": metrics.get("sharpe"),
            "final_equity": round(float(neq.iloc[-1]), 0),
        }
        neq.to_csv(run_dir / "net_equity_curve.csv")
        trades.to_csv(run_dir / "trades.csv", index=False)
        (run_dir / "summary.json").write_text(json.dumps(stats, indent=2))
        with session_scope(settings) as session:
            session.add(experiment_row(
                ExperimentRun, family, variant, cfg, res, metrics, started,
                finished, run_dir, git_hash, md_all.snapshot_id, len(neq)))
        comparison.append(stats)
        print(json.dumps(stats), flush=True)

    out = (settings.artifacts_dir / "adhoc"
           / f"{TAG}_{SLOT_TAG}_marked_{run_ts.strftime('%Y-%m-%d_%H%M%S')}.json")
    out.write_text(json.dumps({
        "run_at": run_ts.isoformat(timespec="seconds"),
        "reference_2L": {"b1d": "+280.7%/-28.3%/1.23",
                         "b2d": "+283.4%/-24.8%/1.32"},
        "variants": comparison,
    }, indent=2))
    print(f"comparison -> {out}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
