"""Survivorship-bias fix for the 2019-2020 backtest window via NSE bhavcopies.

Today's Kite pool (scripts/adhoc/nse2000.csv) is only names LISTED TODAY;
companies delisted 2020-2026 are invisible to a 2019-2020 backtest -> a
momentum universe silently drops its losers. NSE daily bhavcopies carry
OHLCV for EVERY security that traded each day, so they let us recover the
price history of names that traded 2017-2020 but are gone from Kite today,
and ingest them so the PIT universe resolver can include them.

Adhoc, resumable pipeline (NOT core src/). Stages:

  1 download   daily bhavcopy zips 2017-07-01..2020-12-31 (weekdays), polite
               pacing, retry-once, skip 404 (holidays), skip already-present.
  2 panel      parse EQ/BE rows, build ISIN-keyed panel (cached to scratchpad).
  3 classify   latest-window-symbol per ISIN; survivor if present in Kite store
               (or nse2000.csv) -> skip; else DELISTED/DISAPPEARED candidate.
  4 filter     candidates with >=126 trading days AND median TOTTRDVAL >=1cr.
  5 ca-guard   flag close-to-close moves < -40% or > +80% (next day trading) as
               EXCLUDED_SUSPECT_CA (unadjusted split/bonus poison for momentum).
  6 ingest     write survivors' raw OHLCV under latest-window symbol (collision
               guard vs the store + within-run), append to a new pool file.

Run from the trading_os project root:  uv run python scripts/adhoc/bhav_pipeline.py
Data-store WRITES happen only in stage 6, after all downloading/parsing, so a
concurrent Kite backfill of EXISTING symbols (different files) cannot conflict.
"""

from __future__ import annotations

import csv
import io
import json
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

import polars as pl

from tradingos.config.settings import get_settings
from tradingos.core.models import Timeframe
from tradingos.data.store import BarStore

# -- config ---------------------------------------------------------------

ADHOC = Path(__file__).resolve().parent
SCRATCH = Path(
    "/tmp/claude-1000/-workspaces-CA-edu-site/"
    "24e99e2a-3205-414e-b781-5b35b4b1d2ec/scratchpad/bhav"
)
ZIP_DIR = SCRATCH / "zips"
PANEL_PARQUET = SCRATCH / "panel_eqbe.parquet"
IDENTITY_SNAPSHOT = SCRATCH / "kite_identity_snapshot.json"

WINDOW_START = date(2017, 7, 1)
WINDOW_END = date(2020, 12, 31)
KEEP_SERIES = ("EQ", "BE")

MIN_TRADING_DAYS = 126
MIN_MEDIAN_TOTTRDVAL = 1e7  # Rs 1 crore
CA_DROP = -0.40  # close-to-close <= -40% (next day trading) => suspect CA
CA_JUMP = 0.80   # close-to-close >= +80% (next day trading) => suspect CA

UA = "Mozilla/5.0 (compatible; tradingos-adhoc-bhav/1.0)"
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
PACE_SECONDS = 0.28  # ~3.5 requests/sec

VERIFY_NAMES = ["DHFL", "RCOM", "JETAIRWAYS", "COFFEEDAY", "RELCAPITAL",
                "RELIANCECAPITAL", "SINTEX", "MCDOWELL-N", "GITANJALI",
                "VIDEOIND", "MANPASAND", "RELINFRA", "COX&KINGS"]


def _log(msg: str) -> None:
    print(msg, flush=True)


# -- stage 1: download ----------------------------------------------------

def _bhav_url_and_name(d: date) -> tuple[str, str]:
    mon = MONTHS[d.month - 1]
    fname = f"cm{d.day:02d}{mon}{d.year}bhav.csv.zip"
    url = (
        "https://nsearchives.nseindia.com/content/historical/EQUITIES/"
        f"{d.year}/{mon}/{fname}"
    )
    return url, fname


def _weekdays(start: date, end: date):
    d = start
    while d <= end:
        if d.weekday() < 5:  # Mon-Fri
            yield d
        d += timedelta(days=1)


def _download_one(url: str, dest: Path) -> str:
    """Return 'ok' | 'missing' (404 = holiday) | 'fail'."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return "ok"
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return "missing"
        return "fail"
    except Exception:  # noqa: BLE001 — network flakiness, retry handles it
        return "fail"


def stage_download() -> dict:
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    days = list(_weekdays(WINDOW_START, WINDOW_END))
    present = skipped = downloaded = holidays = failed = 0
    fail_list: list[str] = []
    for i, d in enumerate(days):
        url, fname = _bhav_url_and_name(d)
        dest = ZIP_DIR / fname
        # A holiday marker (empty file) means we already learned it's a 404.
        marker = ZIP_DIR / (fname + ".404")
        if dest.exists() and dest.stat().st_size > 0:
            present += 1
            continue
        if marker.exists():
            holidays += 1
            skipped += 1
            continue
        status = _download_one(url, dest)
        if status == "fail":
            time.sleep(0.6)
            status = _download_one(url, dest)  # retry once
        if status == "ok":
            downloaded += 1
        elif status == "missing":
            marker.write_text("")  # remember the holiday (resumable)
            holidays += 1
        else:
            failed += 1
            fail_list.append(fname)
        time.sleep(PACE_SECONDS)
        if (i + 1) % 100 == 0:
            _log(f"  download {i + 1}/{len(days)}: present={present} "
                 f"new={downloaded} holidays={holidays} failed={failed}")
    result = {
        "weekdays_in_window": len(days),
        "already_present": present,
        "downloaded_now": downloaded,
        "holidays_404": holidays,
        "failed": failed,
        "fail_list": fail_list[:40],
    }
    _log("STAGE 1 download: " + json.dumps(result))
    return result


# -- stage 2: parse panel -------------------------------------------------

def _date_from_zipname(name: str) -> date:
    # cm01JUL2019bhav.csv.zip
    core = name[2:-len("bhav.csv.zip")]  # 01JUL2019
    day = int(core[:2])
    mon = MONTHS.index(core[2:5]) + 1
    year = int(core[5:9])
    return date(year, mon, day)


def stage_panel(force: bool = False) -> pl.DataFrame:
    if PANEL_PARQUET.exists() and not force:
        _log(f"STAGE 2 panel: cached {PANEL_PARQUET}")
        return pl.read_parquet(PANEL_PARQUET)

    zip_paths = sorted(p for p in ZIP_DIR.glob("*.csv.zip") if p.stat().st_size > 0)
    frames: list[pl.DataFrame] = []
    bad = 0
    for zp in zip_paths:
        d = _date_from_zipname(zp.name)
        try:
            with zipfile.ZipFile(zp) as zf:
                inner = zf.namelist()[0]
                raw = zf.read(inner)
        except Exception:  # noqa: BLE001 — corrupt download, skip + count
            bad += 1
            continue
        df = pl.read_csv(
            io.BytesIO(raw),
            columns=["SYMBOL", "SERIES", "OPEN", "HIGH", "LOW", "CLOSE",
                     "PREVCLOSE", "TOTTRDQTY", "TOTTRDVAL", "ISIN"],
            schema_overrides={
                "OPEN": pl.Float64, "HIGH": pl.Float64, "LOW": pl.Float64,
                "CLOSE": pl.Float64, "PREVCLOSE": pl.Float64,
                "TOTTRDQTY": pl.Int64, "TOTTRDVAL": pl.Float64,
            },
        )
        df = df.filter(pl.col("SERIES").is_in(KEEP_SERIES))
        df = df.with_columns(pl.lit(d).alias("d"))
        frames.append(df)
    panel = pl.concat(frames, how="vertical")
    panel = panel.with_columns(pl.col("d").cast(pl.Date))
    panel.write_parquet(PANEL_PARQUET)
    _log(f"STAGE 2 panel: parsed {len(zip_paths)} zips ({bad} corrupt), "
         f"{panel.height} EQ/BE rows, {panel['ISIN'].n_unique()} ISINs "
         f"-> {PANEL_PARQUET}")
    return panel


# -- stage 3-4: classify + filter ----------------------------------------

def _kite_identity_set(store: BarStore) -> set[str]:
    """The PRISTINE Kite current-identity set (survivors), persisted so re-runs
    are stable and idempotent.

    Subtlety: stage 6 writes recovered delisted names into the SAME raw/day
    store, so a naive ``store.symbols()`` on a second run would count our own
    ingested names as Kite survivors and wrongly skip them. We pin the identity
    once: on first build we take Kite symbols with data past the backtest
    window (last bar >= 2021-01-01 -- every recovered delisted name ends by
    WINDOW_END 2020-12-31, so this cleanly excludes them even if the store was
    already written to) unioned with today's nse2000.csv pool, and cache it.
    """
    if IDENTITY_SNAPSHOT.exists():
        return set(json.loads(IDENTITY_SNAPSHOT.read_text()))
    cutoff = datetime(WINDOW_END.year + 1, 1, 1)  # 2021-01-01
    kite = {
        sym for sym in store.symbols(Timeframe.DAY)
        if (store.last_ts(sym, Timeframe.DAY) or datetime(1900, 1, 1)) >= cutoff
    }
    with open(ADHOC / "nse2000.csv", newline="") as fh:
        pool = {r["Symbol"] for r in csv.DictReader(fh)}
    identity = kite | pool
    IDENTITY_SNAPSHOT.write_text(json.dumps(sorted(identity)))
    _log(f"  built pristine Kite identity snapshot: {len(identity)} symbols "
         f"-> {IDENTITY_SNAPSHOT}")
    return identity


def stage_classify_filter(panel: pl.DataFrame, identity: set[str]) -> dict:
    # latest symbol per ISIN (by date), + per-ISIN stats over the window.
    latest_sym = (
        panel.sort("d")
        .group_by("ISIN")
        .agg(pl.col("SYMBOL").last().alias("latest_symbol"))
    )
    stats = panel.group_by("ISIN").agg(
        pl.col("d").n_unique().alias("trading_days"),
        pl.col("TOTTRDVAL").median().alias("median_tottrdval"),
        pl.col("d").min().alias("first_date"),
        pl.col("d").max().alias("last_date"),
    )
    isin_tbl = latest_sym.join(stats, on="ISIN")

    n_isins = isin_tbl.height
    survivors = isin_tbl.filter(pl.col("latest_symbol").is_in(list(identity)))
    candidates = isin_tbl.filter(~pl.col("latest_symbol").is_in(list(identity)))

    liq = candidates.filter(
        (pl.col("trading_days") >= MIN_TRADING_DAYS)
        & (pl.col("median_tottrdval") >= MIN_MEDIAN_TOTTRDVAL)
    )

    result = {
        "isins_seen": n_isins,
        "survivors_matched": survivors.height,
        "candidates_delisted": candidates.height,
        "liquidity_filtered_kept": liq.height,
        "identity_set_size": len(identity),
    }
    _log("STAGE 3-4 classify+filter: " + json.dumps(result))
    return {"result": result, "liq": liq}


# -- stage 5a: corporate-action guard ------------------------------------

def _series_for_isin(panel: pl.DataFrame, isin: str) -> pl.DataFrame:
    return (
        panel.filter(pl.col("ISIN") == isin)
        .sort("d")
        .select("d", "OPEN", "HIGH", "LOW", "CLOSE", "TOTTRDQTY")
    )


def stage_ca_guard(panel: pl.DataFrame, liq: pl.DataFrame) -> dict:
    kept: list[dict] = []
    excluded: list[str] = []
    for row in liq.iter_rows(named=True):
        s = _series_for_isin(panel, row["ISIN"])
        close = s["CLOSE"]
        # close-to-close return across consecutive trading rows; the "next day
        # still trading" condition holds by construction (we have the next row).
        ret = (close.shift(-1) / close - 1.0).slice(0, s.height - 1)
        suspect = ((ret <= CA_DROP) | (ret >= CA_JUMP)).any()
        if suspect:
            excluded.append(row["latest_symbol"])
        else:
            kept.append(row)
    result = {
        "ca_excluded_suspect": len(excluded),
        "kept_after_ca": len(kept),
        "ca_excluded_examples": sorted(excluded)[:30],
    }
    _log("STAGE 5a CA-guard: " + json.dumps(result))
    return {"result": result, "kept": kept}


# -- stage 6: ingest ------------------------------------------------------

def _ohlcv_frame(panel: pl.DataFrame, isin: str) -> pl.DataFrame:
    s = _series_for_isin(panel, isin)
    return s.select(
        pl.col("d").cast(pl.Datetime("us")).alias("ts"),
        pl.col("OPEN").alias("open"),
        pl.col("HIGH").alias("high"),
        pl.col("LOW").alias("low"),
        pl.col("CLOSE").alias("close"),
        pl.col("TOTTRDQTY").alias("volume"),
    )


def stage_ingest(
    panel: pl.DataFrame, kept: list[dict], store: BarStore, identity: set[str]
) -> dict:
    ingested: list[str] = []
    collisions: list[str] = []
    rows_written = 0
    seen_targets: set[str] = set()
    date_ranges: dict[str, list[str]] = {}

    for row in kept:
        sym = row["latest_symbol"]
        # NSE reuses tradingsymbols: never clobber a pristine Kite-store symbol
        # (checked against the pinned identity, NOT live has_raw -- our own
        # prior-run ingests live in the store and must not read as collisions;
        # write_raw's append-only merge still raises on any genuine data
        # conflict), and never let two candidates write the same target.
        if sym in identity or sym in seen_targets:
            collisions.append(sym)
            continue
        frame = _ohlcv_frame(panel, row["ISIN"])
        try:
            rows_written += store.write_raw(sym, Timeframe.DAY, frame)
        except Exception as exc:  # noqa: BLE001 — report, keep going
            collisions.append(f"{sym}:{type(exc).__name__}")
            continue
        seen_targets.add(sym)
        ingested.append(sym)
        date_ranges[sym] = [str(row["first_date"]), str(row["last_date"])]

    # new pool file = nse2000 symbols + ingested delisted names
    with open(ADHOC / "nse2000.csv", newline="") as fh:
        base_pool = [r["Symbol"] for r in csv.DictReader(fh)]
    combined = sorted(set(base_pool) | set(ingested))
    pool_path = ADHOC / "nse2000_plus_delisted_2019.csv"
    with open(pool_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Symbol"])
        for sym in combined:
            w.writerow([sym])

    result = {
        "ingested": len(ingested),
        "rows_written": rows_written,
        "collisions_skipped": len(collisions),
        "collision_list": sorted(collisions)[:40],
        "pool_file": str(pool_path),
        "pool_size": len(combined),
    }
    _log("STAGE 6 ingest: " + json.dumps(result))
    return {"result": result, "ingested": ingested, "date_ranges": date_ranges}


# -- stage 6b: verification ----------------------------------------------

def stage_verify(store: BarStore, ingested: list[str], date_ranges: dict) -> dict:
    ingested_set = set(ingested)
    checks: dict[str, dict] = {}
    for name in VERIFY_NAMES:
        if name not in ingested_set:
            continue
        md = store.load_market_data(
            [name], Timeframe.DAY,
            start=datetime(WINDOW_START.year, WINDOW_START.month, WINDOW_START.day),
            end=datetime(WINDOW_END.year, WINDOW_END.month, WINDOW_END.day),
            adjusted=False, strict=False,
        )
        frame = md.full_frame(name) if name in md.symbols else None
        checks[name] = {
            "served_by_store": frame is not None and not frame.empty,
            "rows": 0 if frame is None else len(frame),
            "first": None if frame is None or frame.empty else str(frame.index.min().date()),
            "last": None if frame is None or frame.empty else str(frame.index.max().date()),
            "panel_range": date_ranges.get(name),
        }
        if len(checks) >= 3:
            break
    result = {"verified": checks, "total_ingested": len(ingested)}
    _log("STAGE 6b verify: " + json.dumps(result, indent=2))
    return result


# -- driver ---------------------------------------------------------------

def main() -> int:
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    settings = get_settings()
    store = BarStore(settings)

    if stage in ("download", "all"):
        stage_download()
        if stage == "download":
            return 0

    panel = stage_panel()
    identity = _kite_identity_set(store)
    cf = stage_classify_filter(panel, identity)
    ca = stage_ca_guard(panel, cf["liq"])

    if stage == "analyze":
        return 0

    ing = stage_ingest(panel, ca["kept"], store, identity)
    stage_verify(store, ing["ingested"], ing["date_ranges"])

    _log("\n=== SUMMARY ===")
    _log(json.dumps({
        **cf["result"], **ca["result"], **ing["result"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
