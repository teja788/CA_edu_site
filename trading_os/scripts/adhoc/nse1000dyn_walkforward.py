"""Walk-forward on m2 (returns-only momentum top-N) over the dynamic top-1000.

Overfitting defense for the +296%/Sharpe-1.22 nse1000dyn result: rolling
3y-train / 1y-test windows; each window picks the best (selection.n, momentum
window) combo on train Sharpe, then earns it on the following unseen year.
Start is pulled back to 2021-02-01 (12-1 momentum is warm ~Feb 2021 given the
2020-01-01 data start) so the calendar fits more windows.
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
from nse200_dynamic import DynamicTopNResolver, make_config

SCRATCH = Path(__file__).resolve().parent
SWEEP = {
    "selection.n": [10, 25, 50],
    "signals.mom.params.window": [126, 252],
}


def main() -> None:
    settings = get_settings()
    store = BarStore(settings)
    with open(SCRATCH / "nse2000.csv", newline="") as fh:
        syms = [r["Symbol"] for r in csv.DictReader(fh)]
    symbols = sorted(set(syms) & set(store.symbols(Timeframe.DAY)))
    md_all = store.load_market_data(symbols, Timeframe.DAY, start=None, end=None)
    resolver = DynamicTopNResolver(md_all, 1000)

    base = make_config("m2_returns_only", symbols).model_copy(update={
        "start": date(2021, 2, 1),
        # selection.n=50 must not exceed exit_rank; widen the buffer once here
        # and let the sweep's re-validation keep every combo legal
    })
    base = base.model_copy(update={
        "selection": base.selection.model_copy(update={"exit_rank": 70}),
    })

    res = walk_forward(base, SWEEP, md_all, resolver,
                       train_bars=756, test_bars=252, metric="sharpe")

    run_ts = datetime.now()
    out_dir = settings.artifacts_dir / "adhoc" / "nse1000dyn_walkforward" \
        / run_ts.strftime("%Y-%m-%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    res.oos_equity.to_csv(out_dir / "oos_equity.csv")
    report = {
        "run_at": run_ts.isoformat(timespec="seconds"),
        "sweep": {k: v for k, v in SWEEP.items()},
        "train_bars": 756, "test_bars": 252, "metric": "sharpe",
        "oos_metrics": {k: (None if v != v else v)
                        for k, v in res.oos_metrics.items()},
        "oos_total_costs": res.oos_total_costs,
        "windows": [{
            "train": f"{w.train_start.date()}..{w.train_end.date()}",
            "test": f"{w.test_start.date()}..{w.test_end.date()}",
            "picked": w.best_overrides, "train_score": round(w.train_score, 3),
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
