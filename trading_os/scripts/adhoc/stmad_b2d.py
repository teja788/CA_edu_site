"""Supertrend-gate / MAD-score variants on the champion b2d.

Three variants via the run_variants harness (first real dogfood):
  st_gate    supertrend(10,3) on NIFTYBEES added as a 4th graded-gate
             signal -> f in {0, 1/4, 1/2, 3/4, 1}
  mad_score  ma_distance (MAD 21/200) added to the score at 0.25 weight
  both       both changes

Base = b2d (vol-adj 6m+12m score, exit 50, graded gate) on the
first-class dynamic top-1000 universe (parity with run 1333's resolver
proven at commit aa6aa6e). Reference: b2d = +283.4% / -24.8% / 1.32.
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
SIGNALS_MAD = [
    {"id": "ram6", "name": "risk_adjusted_momentum",
     "params": {"window": 126, "skip": 21, "vol_window": 252}},
    {"id": "ram12", "name": "risk_adjusted_momentum",
     "params": {"window": 252, "skip": 21, "vol_window": 252}},
    {"id": "mad", "name": "ma_distance", "params": {"fast": 21, "slow": 200}},
]
WEIGHTS_MAD = {"ram6": 0.5, "ram12": 0.5, "mad": 0.25}

VARIANTS = {
    "st_gate": {"regime.signals": GATE4},
    "mad_score": {"signals": SIGNALS_MAD, "score.weights": WEIGHTS_MAD},
    "both": {"regime.signals": GATE4, "signals": SIGNALS_MAD,
             "score.weights": WEIGHTS_MAD},
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
    run_variants(base, VARIANTS, settings, family_prefix="stmad_b2d")


if __name__ == "__main__":
    sys.exit(main())
