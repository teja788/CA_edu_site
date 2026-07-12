"""Momentum-window geometry sweep on the champion b2d-ST (2021-26).

Eight config-only variants (brainstorm 2026-07-12; #6 'don't touch' items
excluded by owner instruction). Base = run 1346 (vol-adj 6m+12m 50/50,
skip 21, exit 50, 4-signal graded gate). Reference: +291.8% / -24.3% / 1.35.

  skip0        both windows include the most recent month (NSE-index style;
               tests whether the US skip convention costs money in India)
  skip10       half-skip compromise
  w6heavy      6m/12m weights 0.7/0.3 (faster blend)
  w12heavy     0.3/0.7 (slower blend)
  add3m        + 63d component: 12m 0.5 / 6m 0.25 / 3m 0.25
  add9m        + 189d component: 12m 0.5 / 9m 0.25 / 6m 0.25
  nine_for_six 9m replaces 6m: 9m/12m 50/50
  pure1m       21d-only ranking (the reject-check)
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
from stmad_b2d import GATE4

SCRATCH = Path(__file__).resolve().parent


def ram(id_: str, window: int, skip: int = 21) -> dict:
    return {"id": id_, "name": "risk_adjusted_momentum",
            "params": {"window": window, "skip": skip, "vol_window": 252}}


VARIANTS = {
    "skip0": {"signals": [ram("ram6", 126, 0), ram("ram12", 252, 0)],
              "score.weights": {"ram6": 0.5, "ram12": 0.5}},
    "skip10": {"signals": [ram("ram6", 126, 10), ram("ram12", 252, 10)],
               "score.weights": {"ram6": 0.5, "ram12": 0.5}},
    "w6heavy": {"score.weights": {"ram6": 0.7, "ram12": 0.3}},
    "w12heavy": {"score.weights": {"ram6": 0.3, "ram12": 0.7}},
    "add3m": {"signals": [ram("ram3", 63), ram("ram6", 126), ram("ram12", 252)],
              "score.weights": {"ram3": 0.25, "ram6": 0.25, "ram12": 0.5}},
    "add9m": {"signals": [ram("ram6", 126), ram("ram9", 189), ram("ram12", 252)],
              "score.weights": {"ram6": 0.25, "ram9": 0.25, "ram12": 0.5}},
    "nine_for_six": {"signals": [ram("ram9", 189), ram("ram12", 252)],
                     "score.weights": {"ram9": 0.5, "ram12": 0.5}},
    "pure1m": {"signals": [ram("ram1", 21, 0)],
               "score.weights": {"ram1": 1.0}},
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
    # base carries the champion's 4-signal gate on every variant
    variants = {name: {"regime.signals": GATE4, **ov}
                for name, ov in VARIANTS.items()}
    run_variants(base, variants, settings, family_prefix="win_b2dst")


if __name__ == "__main__":
    sys.exit(main())
