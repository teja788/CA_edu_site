"""Walk-forward on the champion structure (owner-approved, Jul 12 evening).

Rolling 3y-train / 1y-test windows over 2018-09..2026-07 (the 2017-07
backfill makes ~5 windows fit). Each window picks the best of 12 combos on
train Sharpe and earns it on the following unseen year:

  score.weights        {50/50, 30/70}
  regime               {none, 3-signal gate, 4-signal gate (champion)}
  selection.exit_rank  {35, 50}

The informative outputs: the stitched OOS equity/metrics (what this
selection DISCIPLINE would have earned live) and per-window winner
stability (does each window independently rediscover the champion?).
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

from tradingos.analytics.walkforward import walk_forward
from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore
from batch1_m2_improvements import SeasonedTopNResolver, REGIME_SYMBOL
from batch2_m2_overlays import make_config

SCRATCH = Path(__file__).resolve().parent

GATE3 = [
    {"kind": "above_ma", "params": {"window": 100}},
    {"kind": "above_ma", "params": {"window": 200}},
    {"kind": "positive_return", "params": {"window": 252}},
]
GATE4 = GATE3 + [{"kind": "supertrend", "params": {"period": 10, "multiplier": 3.0}}]

def regime(signals):
    return {"symbol": REGIME_SYMBOL, "signals": signals,
            "mode": "graded_asymmetric", "adaptive_weights": None}

SWEEP = {
    "score.weights": [{"ram6": 0.5, "ram12": 0.5}, {"ram6": 0.3, "ram12": 0.7}],
    "regime": [None, regime(GATE3), regime(GATE4)],
    "selection.exit_rank": [35, 50],
}


def main() -> None:
    settings = get_settings()
    store = BarStore(settings)
    with open(SCRATCH / "nse2000.csv", newline="") as fh:
        syms = [r["Symbol"] for r in csv.DictReader(fh)]
    universe = sorted(set(syms) & set(store.symbols(Timeframe.DAY)))
    md_all = store.load_market_data(universe + [REGIME_SYMBOL], Timeframe.DAY,
                                    start=None, end=None)
    resolver = SeasonedTopNResolver(md_all, 1000, universe)

    base = make_config("b2d_graded_score", universe).model_copy(update={
        "start": date(2018, 9, 3),  # ram12 warm ~Aug-2018 given 2017-07 data
        "name": "b2dst_wf",
    })

    res = walk_forward(base, SWEEP, md_all, resolver,
                       train_bars=756, test_bars=252, metric="sharpe")

    run_ts = datetime.now()
    out_dir = (settings.artifacts_dir / "adhoc" / "b2dst_walkforward"
               / run_ts.strftime("%Y-%m-%d_%H%M%S"))
    out_dir.mkdir(parents=True, exist_ok=True)
    res.oos_equity.to_csv(out_dir / "oos_equity.csv")
    report = {
        "run_at": run_ts.isoformat(timespec="seconds"),
        "sweep": {k: [str(v) for v in vals] for k, vals in SWEEP.items()},
        "train_bars": 756, "test_bars": 252, "metric": "sharpe",
        "oos_metrics": {k: (None if v != v else round(v, 4))
                        for k, v in res.oos_metrics.items()},
        "windows": [{
            "train": f"{w.train_start.date()}..{w.train_end.date()}",
            "test": f"{w.test_start.date()}..{w.test_end.date()}",
            "picked": {k: str(v) for k, v in w.best_overrides.items()},
            "train_score": round(w.train_score, 3),
            "test_metrics": {k: (None if v != v else round(v, 4))
                             for k, v in w.test_metrics.items()},
            "skipped": w.skipped, "reason": w.reason,
        } for w in res.windows],
    }
    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report["oos_metrics"]), flush=True)
    for w in report["windows"]:
        print(json.dumps(w), flush=True)
    print(f"artifacts -> {out_dir}", flush=True)


if __name__ == "__main__":
    sys.exit(main())
