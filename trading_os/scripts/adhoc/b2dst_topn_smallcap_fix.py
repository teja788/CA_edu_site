"""Corrected small-N rungs for the b2d-ST portfolio-size sweep.

The first sweep (b2dst_topn_sweep.py) kept the champion's flat
max_position_pct=0.05, which caps a 10-slot portfolio at ~50% invested and
a 15-slot one at ~75% — those rungs measured cash drag, not concentration.
Here the cap scales with N keeping the champion's headroom ratio
(cap = 1.25 * equal weight): n10 -> 12.5%, n15 -> 8.33%, n20 -> 6.25%.
n20 re-runs because the flat cap left it zero headroom vs the champion's
1.25x. Exit buffer stays 2*N as before.
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
    f"n{n}cap": {"regime.signals": GATE4,
                 "selection.n": n, "selection.exit_rank": 2 * n,
                 "sizing.max_position_pct": round(1.25 / n, 4)}
    for n in (10, 15, 20)
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
