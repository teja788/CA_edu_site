"""Portfolio-size sweep on the champion b2d-ST: top-N in {10,15,20,25,30}.

Owner ask (2026-07-12): try 10/15/20/30 stocks in the best strategy and
compare with the existing top-25. The exit buffer keeps the champion's 2x
ratio (exit_rank = 2*N) so each rung tests SIZE, not a different buffer
geometry. n25 re-runs as the same-snapshot control (reference: run 1346,
+291.8% / -24.3% / Sharpe 1.35).

Base = b2d-ST: vol-adj 6m+12m score, graded asymmetric 4-signal gate
(100SMA / 200SMA / 12m return / supertrend(10,3) on NIFTYBEES), monthly,
dynamic top-1000 universe. See docs/champion_strategy_b2dst.md.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore
from tradingos.experiments.variants import run_variants
from batch2_m2_overlays import make_config

SCRATCH = Path(__file__).resolve().parent

GATE4 = [
    {"kind": "above_ma", "params": {"window": 100}},
    {"kind": "above_ma", "params": {"window": 200}},
    {"kind": "positive_return", "params": {"window": 252}},
    {"kind": "supertrend", "params": {"period": 10, "multiplier": 3.0}},
]

VARIANTS = {
    f"n{n}": {"regime.signals": GATE4,
              "selection.n": n, "selection.exit_rank": 2 * n}
    for n in (10, 15, 20, 25, 30)
}


def main() -> None:
    settings = get_settings()
    store = BarStore(settings)
    with open(SCRATCH / "nse2000.csv", newline="") as fh:
        syms = [r["Symbol"] for r in csv.DictReader(fh)]
    universe = sorted(set(syms) & set(store.symbols(Timeframe.DAY)))

    base = make_config("b2d_graded_score", universe)
    base = base.model_copy(update={
        "universe": base.universe.model_copy(update={"dynamic_top_n": 1000}),
    })
    run_variants(base, VARIANTS, settings, family_prefix="b2dst_topn")


if __name__ == "__main__":
    sys.exit(main())
