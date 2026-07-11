"""Build the ~2000-name NSE mainboard universe and sync daily bars.

Universe = plain-series NSE cash equities from the instrument master,
excluding ETF/iNAV/SGB/G-sec tickers. Written to scripts/adhoc/nse2000.csv
(same shape as nifty200.csv: a Symbol column).

Uses the cached Kite access token directly (bypassing KiteAuth's calendar-day
staleness check): Kite invalidates tokens ~07:30 IST, not at midnight, and
the raw store is append-only so an interrupted sync just resumes later.
"""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

from kiteconnect import KiteConnect

from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.sync import sync_symbols

SCRATCH = Path(__file__).resolve().parent
EXCLUDE_LIKE = ("%-%", "%INAV", "SGB%", "%ETF%", "%BEES%")


def build_universe(settings) -> list[str]:
    con = sqlite3.connect(settings.data_dir / "meta.sqlite")
    where = " AND ".join(f"tradingsymbol NOT LIKE '{p}'" for p in EXCLUDE_LIKE)
    rows = con.execute(
        f"SELECT tradingsymbol FROM instrument WHERE {where} "
        "AND name NOT LIKE '%ETF%' AND name NOT LIKE '%INAV%' "
        "AND tradingsymbol NOT GLOB '*[0-9]GS[0-9]*' "
        "ORDER BY tradingsymbol"
    ).fetchall()
    con.close()
    return [r[0] for r in rows]


def main() -> None:
    settings = get_settings()
    symbols = build_universe(settings)
    with open(SCRATCH / "nse2000.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["Symbol"])
        w.writeheader()
        w.writerows({"Symbol": s} for s in symbols)
    print(f"universe: {len(symbols)} symbols -> nse2000.csv", flush=True)

    token = json.loads((settings.data_dir / "kite_token.json").read_text())
    kite = KiteConnect(api_key=settings.kite_api_key)
    kite.set_access_token(token["access_token"])

    done = 0

    def progress(sym: str, tf: Timeframe) -> None:
        nonlocal done
        done += 1
        if done % 50 == 0:
            print(f"synced {done}/{len(symbols)}", flush=True)

    results = sync_symbols(
        kite, settings, symbols, [Timeframe.DAY],
        default_start=date(2020, 1, 1), on_synced=progress,
    )
    errors = [r for r in results if getattr(r, "error", None)]
    print(f"done: {len(results)} results, {len(errors)} errors", flush=True)
    for r in errors[:20]:
        print("ERROR", r.symbol, r.error, flush=True)


if __name__ == "__main__":
    sys.exit(main())
