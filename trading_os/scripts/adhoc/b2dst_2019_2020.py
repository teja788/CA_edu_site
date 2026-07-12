"""b2d-ST (the champion) on the 2019-2020 window — COVID-crash exam.

Trades 2019-01-01 .. 2020-12-31 (needs the 2017-07 backfill first:
scripts/adhoc/backfill_2017.py). Same config as run 1346 except the
window. Heavier survivorship caveat than 2021-26: the pool is today's
listed names, so 2020-2026 delistings are invisible — treat results as
an upper bound; the interesting output is the GATE's behavior through
Mar-2020, which is relative.
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
    run_variants(base, {"b2dst_2019_2020": {"regime.signals": GATE4}},
                 settings, family_prefix="oow_b2dst")


if __name__ == "__main__":
    sys.exit(main())
