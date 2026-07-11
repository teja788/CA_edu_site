"""Build a 2020-vintage top-200 universe from Zerodha data alone.

Ranks every synced mainboard name by median daily traded value
(close * volume) over calendar 2020 and keeps the top 200 — a
liquidity proxy for the NIFTY 200 using only information knowable
at end-2020. Names must have traded >= 200 days in 2020 (excludes
mid/late-2020 listings and suspended stocks). Output:
scripts/adhoc/nse200_2020.csv (Symbol column).
"""

from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore

SCRATCH = Path(__file__).resolve().parent
MIN_2020_BARS = 200


def main() -> None:
    with open(SCRATCH / "nse2000.csv", newline="") as fh:
        syms = [r["Symbol"] for r in csv.DictReader(fh)]

    store = BarStore(get_settings())
    md = store.load_market_data(sorted(syms), Timeframe.DAY,
                                start=None, end=None)
    scores: dict[str, float] = {}
    for sym in md.symbols:
        f = md.full_frame(sym)
        y2020 = f.loc["2020-01-01":"2020-12-31"]
        if len(y2020) < MIN_2020_BARS:
            continue
        scores[sym] = float((y2020["close"] * y2020["volume"]).median())

    top = sorted(scores, key=scores.get, reverse=True)[:200]
    with open(SCRATCH / "nse200_2020.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["Symbol"])
        w.writeheader()
        w.writerows({"Symbol": s} for s in sorted(top))
    print(f"eligible with full 2020 history: {len(scores)}; wrote top 200")

    for other, label in [("nifty200_2019.csv", "real Feb-2019 NIFTY 200"),
                         ("nifty200.csv", "current NIFTY 200")]:
        path = SCRATCH / other
        if not path.exists():
            continue
        with open(path, newline="") as fh:
            ref = {r["Symbol"].strip() for r in csv.DictReader(fh)}
        print(f"overlap with {label}: {len(ref & set(top))}/200")


if __name__ == "__main__":
    main()
