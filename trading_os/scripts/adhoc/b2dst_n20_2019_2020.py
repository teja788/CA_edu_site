"""n20 rung of the b2d-ST size sweep on 2019-2020 — the COVID exam.

The size sweep (b2dst_topn_sweep.py) had n20 (exit 40, cap 6.25%) beat
the n25 champion in-window (+313.2%/−25.6%/1.38 vs +291.8%/−24.3%/1.35).
This runs the SAME out-of-window exam the champion took (runner
b2dst_2019_2020.py, result +62.6%/−29.8%/1.35) with only the size rung
changed. Same survivors-only caveat: upper bound, relative reads only.
"""

from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore
from tradingos.experiments.variants import run_variants
from batch2_m2_overlays import make_config
from stmad_b2d import GATE4

SCRATCH = Path(__file__).resolve().parent


def main() -> None:
    settings = get_settings()
    store = BarStore(settings)
    with open(SCRATCH / "nse2000.csv", newline="") as fh:
        syms = [r["Symbol"] for r in csv.DictReader(fh)]
    universe = sorted(set(syms) & set(store.symbols(Timeframe.DAY)))

    base = make_config("b2d_graded_score", universe)
    base = base.model_copy(update={
        "universe": base.universe.model_copy(update={"dynamic_top_n": 1000}),
        "start": date(2019, 1, 1),
        "end": date(2020, 12, 31),
    })
    run_variants(base, {"n20_2019_2020": {
        "regime.signals": GATE4,
        "selection.n": 20, "selection.exit_rank": 40,
        "sizing.max_position_pct": 0.0625,
    }}, settings, family_prefix="oow_b2dst")


if __name__ == "__main__":
    sys.exit(main())
