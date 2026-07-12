"""Backfill daily bars 2017-07-01 .. (existing first bar - 1) for the pool.

One-shot for the 2019-2020 out-of-window test of b2d-ST: the store starts
2020-01-01; trading Jan-2019 needs ~18 months of warmup (12m signal +
skip + 126d universe seasoning). write_raw is an append-only MERGE keyed
by ts, so prepending history is safe by construction (collisions with
different OHLCV raise).

Symbols whose Kite listing is later than the requested range simply
return fewer/no rows. Failures are collected and reported, not fatal.
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.auth import KiteAuth
from tradingos.data.fetcher import HistoricalFetcher
from tradingos.data.sync import HISTORICAL_BURST, HISTORICAL_RATE
from tradingos.data.instruments import token_for
from tradingos.data.ratelimit import TokenBucket
from tradingos.data.store import BarStore

SCRATCH = Path(__file__).resolve().parent
BACKFILL_START = date(2017, 7, 1)

def main() -> None:
    settings = get_settings()
    store = BarStore(settings)
    kite = KiteAuth(settings).kite()
    fetcher = HistoricalFetcher(kite, TokenBucket(HISTORICAL_RATE, HISTORICAL_BURST))

    with open(SCRATCH / "nse2000.csv", newline="") as fh:
        pool = [r["Symbol"] for r in csv.DictReader(fh)]
    symbols = sorted((set(pool) & set(store.symbols(Timeframe.DAY))) | {"NIFTYBEES"})

    done = skipped = 0
    failed: list[str] = []
    total_rows = 0
    for i, sym in enumerate(symbols):
        try:
            first = store.read_raw(sym, Timeframe.DAY)["ts"].min()
            end = (first.date() if hasattr(first, "date") else first) - timedelta(days=1)
            if end <= BACKFILL_START:
                skipped += 1
                continue
            token = token_for(sym, settings)
            df = fetcher.fetch(sym, token, Timeframe.DAY, BACKFILL_START, end)
            if df.height:
                total_rows += store.write_raw(sym, Timeframe.DAY, df)
            done += 1
        except Exception as exc:  # noqa: BLE001 — collect, report, continue
            failed.append(f"{sym}:{type(exc).__name__}")
        if (i + 1) % 100 == 0:
            print(f"{i + 1}/{len(symbols)} processed, {done} backfilled, "
                  f"{len(failed)} failed", flush=True)

    print(json.dumps({
        "backfilled": done, "already_early_enough": skipped,
        "rows_added": total_rows, "failed_n": len(failed),
        "failed": failed[:40],
    }), flush=True)


if __name__ == "__main__":
    sys.exit(main())
