"""Write top-N 2020-traded-value universes (N=500, 1000, all-eligible).

Same ranking as build_nse200_2020.py: median close*volume over calendar
2020, >=200 trading days in 2020. Kite has no delisted names, so the
eligible pool is ~1,224 — the '2000-name' rung of the scaling study is
therefore 'all eligible', and 4000 is not constructible from Kite data.
"""

from __future__ import annotations

import csv
from pathlib import Path

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
        y2020 = md.full_frame(sym).loc["2020-01-01":"2020-12-31"]
        if len(y2020) >= MIN_2020_BARS:
            scores[sym] = float((y2020["close"] * y2020["volume"]).median())

    ranked = sorted(scores, key=scores.get, reverse=True)
    for n in (500, 1000, len(ranked)):
        with open(SCRATCH / f"nse{n}_2020.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["Symbol"])
            w.writeheader()
            w.writerows({"Symbol": s} for s in sorted(ranked[:n]))
        print(f"nse{n}_2020.csv: {min(n, len(ranked))} symbols")


if __name__ == "__main__":
    main()
