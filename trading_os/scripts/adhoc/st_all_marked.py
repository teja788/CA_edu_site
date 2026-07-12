"""Supertrend gate across the marked strategies (b2d's run already exists).

  st_only_b1d   b1d (no gate today) + a supertrend(10,3)-ONLY gate on
                NIFTYBEES (binary f in {0,1}, asymmetric)
  st4_b2e       b2e with the 4-signal gate (100SMA/200SMA/12m + supertrend)
                — same change that beat b2d (+291.8/-24.3/1.35)

References: b1d +280.7/-28.3/1.23; b2e +196.5/-19.0/1.38 (Rs 4cr).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore
from tradingos.experiments.variants import run_variants
from batch1_m2_improvements import make_config as b1_config
from batch2_m2_overlays import make_config as b2_config
from stmad_b2d import GATE4

SCRATCH = Path(__file__).resolve().parent

ST_ONLY_GATE = {
    "symbol": "NIFTYBEES",
    "signals": [{"kind": "supertrend", "params": {"period": 10, "multiplier": 3.0}}],
    "mode": "graded_asymmetric",
}


def main() -> None:
    settings = get_settings()
    store = BarStore(settings)
    with open(SCRATCH / "nse2000.csv", newline="") as fh:
        syms = [r["Symbol"] for r in csv.DictReader(fh)]
    universe = sorted(set(syms) & set(store.symbols(Timeframe.DAY)))

    def dyn(cfg):
        return cfg.model_copy(update={
            "universe": cfg.universe.model_copy(update={"dynamic_top_n": 1000}),
        })

    b1d = dyn(b1_config("b1d_score_exit50", universe))
    run_variants(b1d, {"st_only_b1d": {"regime": ST_ONLY_GATE}}, settings,
                 family_prefix="st_b1d")

    b2e = dyn(b2_config("b2e_full", universe))
    run_variants(b2e, {"st4_b2e": {"regime.signals": GATE4}}, settings,
                 family_prefix="st_b2e")


if __name__ == "__main__":
    sys.exit(main())
