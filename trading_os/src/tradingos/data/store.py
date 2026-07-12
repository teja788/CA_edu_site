"""Parquet(+DuckDB) bar store — the ONLY place OHLCV bars are persisted.

Canonical "bar frame" at the storage seam (see BAR_SCHEMA): a polars
DataFrame with columns ``ts, open, high, low, close, volume``, sorted
ascending by ``ts`` with no duplicate timestamps. Every public read/write
method on BarStore accepts or returns frames in this shape.

Layout on disk (paths derived from Settings):

    <raw_dir>/<timeframe.value>/<SYMBOL>.parquet         (immutable, append-only)
    <adjusted_dir>/<timeframe.value>/<SYMBOL>.parquet     (derived, full overwrite)

Raw data is a historical record of exactly what the broker returned and is
never overwritten in place — see write_raw(). Adjusted data is rebuildable
from raw + corporate actions, so write_adjusted() always replaces it wholesale.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd
import polars as pl

from tradingos.config.settings import Settings
from tradingos.core.errors import DataError
from tradingos.core.logging import get_logger
from tradingos.core.models import Timeframe
from tradingos.engine.dataview import MarketData

logger = get_logger(__name__)

# Canonical storage-seam schema. `validate_bars` casts every incoming frame to
# exactly these columns/dtypes before it is allowed to touch disk.
BAR_SCHEMA: dict[str, pl.DataType | type[pl.DataType]] = {
    "ts": pl.Datetime("us"),
    "open": pl.Float64,
    "high": pl.Float64,
    "low": pl.Float64,
    "close": pl.Float64,
    "volume": pl.Int64,
}

_OHLCV_COLS = ("open", "high", "low", "close", "volume")


def validate_bars(df: pl.DataFrame) -> pl.DataFrame:
    """Normalize a bar frame to the canonical BAR_SCHEMA.

    - raises DataError if any BAR_SCHEMA column is missing
    - casts every column to its BAR_SCHEMA dtype (raises DataError if a value
      can't be cast, e.g. a non-numeric close)
    - raises DataError if any cell is null
    - sorts ascending by ts
    - rows that share a ts but have identical OHLCV values are deduplicated
      (idempotent re-ingestion of the same source data); rows that share a ts
      with DIFFERENT values raise DataError — we never silently pick a winner
    """
    missing = [c for c in BAR_SCHEMA if c not in df.columns]
    if missing:
        raise DataError(f"bar frame missing required columns: {missing}")

    df = df.select(list(BAR_SCHEMA))
    try:
        df = df.cast(BAR_SCHEMA)  # type: ignore[arg-type]
    except pl.exceptions.PolarsError as exc:
        raise DataError(f"bar frame failed dtype cast to BAR_SCHEMA: {exc}") from exc

    if df.null_count().to_numpy().sum() > 0:
        raise DataError("bar frame contains null values")

    df = df.sort("ts")

    if df["ts"].is_duplicated().any():
        distinct = df.unique()
        if distinct["ts"].is_duplicated().any():
            bad_ts = (
                distinct.filter(distinct["ts"].is_duplicated())
                .get_column("ts")
                .unique()
                .sort()
                .to_list()
            )
            raise DataError(f"conflicting duplicate bars (same ts, different values) at ts={bad_ts}")
        df = distinct.sort("ts")

    return df


def _merge_append_only(
    existing: pl.DataFrame, incoming: pl.DataFrame, symbol: str, timeframe: Timeframe
) -> tuple[pl.DataFrame, int]:
    """Append-only merge for raw data: incoming rows whose ts is new are added;
    incoming rows whose ts already exists must match the stored values exactly
    or a DataError is raised (raw history is immutable)."""
    common = incoming.join(existing, on="ts", how="inner", suffix="_existing")
    if common.height > 0:
        conflict = pl.zeros(common.height, dtype=pl.Boolean, eager=True)
        for col in _OHLCV_COLS:
            conflict = conflict | (common[col] != common[f"{col}_existing"])
        if conflict.any():
            bad_ts = common.filter(conflict)["ts"].to_list()
            raise DataError(
                f"raw data conflict for {symbol} ({timeframe.value}): incoming bar(s) "
                f"differ from previously stored raw values at ts={bad_ts}; raw data is "
                "immutable and cannot be silently overwritten"
            )
    new_rows = incoming.join(existing.select("ts"), on="ts", how="anti")
    merged = pl.concat([existing, new_rows], how="vertical").sort("ts")
    return merged, new_rows.height


def _read_parquet_range(
    path: Path, start: datetime | None, end: datetime | None
) -> pl.DataFrame:
    """Read a date slice while allowing parquet predicate pushdown."""
    query = pl.scan_parquet(path)
    if start is not None:
        query = query.filter(pl.col("ts") >= start)
    if end is not None:
        query = query.filter(pl.col("ts") <= end)
    return query.collect()


class BarStore:
    """Reads and writes OHLCV bars for one Settings-rooted data directory."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # -- paths ----------------------------------------------------------

    def _raw_path(self, symbol: str, timeframe: Timeframe) -> Path:
        return self._settings.raw_dir / timeframe.value / f"{symbol}.parquet"

    def _adjusted_path(self, symbol: str, timeframe: Timeframe) -> Path:
        return self._settings.adjusted_dir / timeframe.value / f"{symbol}.parquet"

    def _adjmeta_path(self, symbol: str, timeframe: Timeframe) -> Path:
        return self._settings.adjusted_dir / timeframe.value / f"{symbol}.adjmeta.json"

    def _snapshot_meta_path(self, symbol: str, timeframe: Timeframe) -> Path:
        return self._settings.adjusted_dir / timeframe.value / f"{symbol}.snapshot.json"

    @staticmethod
    def _atomic_write(df: pl.DataFrame, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            df.write_parquet(tmp_path)
            os.replace(tmp_path, path)
        except BaseException:
            tmp_path.unlink(missing_ok=True)
            raise

    # -- raw (immutable, append-only) ------------------------------------

    def write_raw(self, symbol: str, timeframe: Timeframe, df: pl.DataFrame) -> int:
        """Append-only merge into raw storage. Returns the count of newly
        added rows. Raises DataError if an incoming row's ts already exists
        with different OHLCV values — raw history is never overwritten."""
        incoming = validate_bars(df)
        path = self._raw_path(symbol, timeframe)
        if path.exists():
            existing = pl.read_parquet(path)
            merged, added = _merge_append_only(existing, incoming, symbol, timeframe)
        else:
            merged, added = incoming, incoming.height
        self._atomic_write(merged, path)
        logger.info(
            "write_raw %s/%s: +%d new row(s), %d total", symbol, timeframe.value, added, merged.height
        )
        return added

    def read_raw(
        self,
        symbol: str,
        timeframe: Timeframe,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> pl.DataFrame:
        path = self._raw_path(symbol, timeframe)
        if not path.exists():
            raise DataError(f"no raw {timeframe.value} data stored for {symbol}")
        return _read_parquet_range(path, start, end)

    def has_raw(self, symbol: str, timeframe: Timeframe) -> bool:
        return self._raw_path(symbol, timeframe).exists()

    # -- adjusted (derived, full overwrite) ------------------------------

    def write_adjusted(self, symbol: str, timeframe: Timeframe, df: pl.DataFrame) -> int:
        """Full overwrite (adjusted data is derived/rebuildable from raw +
        corporate actions). Returns the row count written."""
        validated = validate_bars(df)
        path = self._adjusted_path(symbol, timeframe)
        self._atomic_write(validated, path)
        self._write_snapshot_meta(symbol, timeframe, path, validated["close"])
        logger.info(
            "write_adjusted %s/%s: %d row(s) (full overwrite)",
            symbol,
            timeframe.value,
            validated.height,
        )
        return validated.height

    def read_adjusted(
        self,
        symbol: str,
        timeframe: Timeframe,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> pl.DataFrame:
        path = self._adjusted_path(symbol, timeframe)
        if not path.exists():
            raise DataError(f"no adjusted {timeframe.value} data stored for {symbol}")
        return _read_parquet_range(path, start, end)

    def has_adjusted(self, symbol: str, timeframe: Timeframe) -> bool:
        return self._adjusted_path(symbol, timeframe).exists()

    def write_adjustment_meta(self, symbol: str, timeframe: Timeframe, meta: dict) -> None:
        """Record provenance for the adjusted series (sidecar JSON beside the
        adjusted parquet). ``data/actions.py::build_adjusted`` stores the
        signature of the price-affecting corporate actions it applied, so
        reads can detect a STALE adjusted series (see load_market_data)."""
        path = self._adjmeta_path(symbol, timeframe)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(meta, sort_keys=True))

    def read_adjustment_meta(self, symbol: str, timeframe: Timeframe) -> dict | None:
        """The adjustment provenance recorded by write_adjustment_meta, or
        None when the adjusted series was never built through build_adjusted."""
        path = self._adjmeta_path(symbol, timeframe)
        if not path.exists():
            return None
        return json.loads(path.read_text())

    # -- symbol migration (renames) ----------------------------------------

    def migrate_symbol(self, old_symbol: str, new_symbol: str, timeframe: Timeframe) -> int | None:
        """Relocate ``old_symbol``'s raw history under ``new_symbol`` after a
        symbol rename. Returns None when old_symbol has no raw file for this
        timeframe (nothing to do), else the number of rows contributed by the
        old name to the new name's raw store.

        Rename case (no raw under new_symbol): the parquet file is moved
        wholesale. Repair case (BOTH names hold raw bars -- e.g. syncs
        continued under the new name while history sat orphaned under the
        old): rows are merged with the same append-only semantics as
        write_raw; a shared ts with different OHLCV raises DataError and
        nothing is modified. Adjusted series + adjustment metadata for BOTH
        names are deleted -- they are derived and must be rebuilt (`platform
        data adjust`) against the migrated raw history.
        """
        old_path = self._raw_path(old_symbol, timeframe)
        if not old_path.exists():
            return None
        new_path = self._raw_path(new_symbol, timeframe)
        if new_path.exists():
            existing = pl.read_parquet(new_path)
            incoming = pl.read_parquet(old_path)
            merged, moved = _merge_append_only(existing, incoming, new_symbol, timeframe)
            self._atomic_write(merged, new_path)
            old_path.unlink()
        else:
            moved = pl.read_parquet(old_path, columns=["ts"]).height
            new_path.parent.mkdir(parents=True, exist_ok=True)
            os.replace(old_path, new_path)
        for sym in (old_symbol, new_symbol):
            self._adjusted_path(sym, timeframe).unlink(missing_ok=True)
            self._adjmeta_path(sym, timeframe).unlink(missing_ok=True)
            self._snapshot_meta_path(sym, timeframe).unlink(missing_ok=True)
        logger.info(
            "migrate_symbol %s -> %s (%s): %d raw row(s) relocated; stale adjusted data dropped",
            old_symbol,
            new_symbol,
            timeframe.value,
            moved,
        )
        return moved

    # -- metadata ---------------------------------------------------------

    def last_ts(self, symbol: str, timeframe: Timeframe) -> datetime | None:
        """Latest raw bar timestamp for symbol/timeframe, or None if absent."""
        path = self._raw_path(symbol, timeframe)
        if not path.exists():
            return None
        df = pl.read_parquet(path, columns=["ts"])
        if df.height == 0:
            return None
        return df["ts"].max()  # type: ignore[return-value]

    def symbols(self, timeframe: Timeframe) -> list[str]:
        """Sorted list of symbols with raw data for this timeframe."""
        d = self._settings.raw_dir / timeframe.value
        if not d.exists():
            return []
        return sorted(p.stem for p in d.glob("*.parquet"))

    def snapshot_id(self, symbols: list[str], timeframe: Timeframe) -> str:
        """Stable 16-hex-char fingerprint of the stored data for `symbols` at
        `timeframe`: sha256 over sorted (symbol, raw_row_count, raw_last_ts,
        adjusted_fingerprint) tuples, where adjusted_fingerprint hashes the
        adjusted close column's bytes (None when no adjusted series exists).
        Identical store state always yields the same id; any added/changed
        raw bar changes it, and so does any change in ADJUSTMENT state --
        two stores with identical raw data but different adjustment passes
        (e.g. one rebuilt after a new corporate action) never share an id.
        Used for reproducibility tracking and as part of signal cache keys
        (see engine/dataview.py::SignalStore)."""
        rows: list[tuple[str, int, str | None, str | None]] = []
        for sym in sorted(symbols):
            path = self._raw_path(sym, timeframe)
            if path.exists():
                # Parquet readers can answer these aggregates from row-group
                # metadata/statistics without materialising the timestamp column.
                facts = pl.scan_parquet(path).select(
                    pl.len().alias("row_count"), pl.col("ts").max().alias("last")
                ).collect().row(0, named=True)
                row_count = facts["row_count"]
                last = facts["last"]
            else:
                row_count = 0
                last = None
            adj_path = self._adjusted_path(sym, timeframe)
            if adj_path.exists():
                adj_fp = self._adjusted_fingerprint(sym, timeframe, adj_path)
            else:
                adj_fp = None
            rows.append(
                (sym, row_count, last.isoformat() if last is not None else None, adj_fp)
            )
        payload = json.dumps(rows, sort_keys=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def _write_snapshot_meta(
        self, symbol: str, timeframe: Timeframe, path: Path, close: pl.Series
    ) -> str:
        """Persist an adjusted-close digest keyed to the exact parquet file."""
        digest = hashlib.sha256(close.to_numpy().tobytes()).hexdigest()[:16]
        stat = path.stat()
        payload = {
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "ctime_ns": stat.st_ctime_ns,
            "inode": stat.st_ino,
            "close_sha256": digest,
        }
        meta_path = self._snapshot_meta_path(symbol, timeframe)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=meta_path.parent, prefix=f".{meta_path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, sort_keys=True)
            os.replace(tmp_name, meta_path)
        except BaseException:
            Path(tmp_name).unlink(missing_ok=True)
            raise
        return digest

    def _adjusted_fingerprint(
        self, symbol: str, timeframe: Timeframe, path: Path
    ) -> str:
        """Return the persisted digest, rebuilding it if the parquet changed."""
        stat = path.stat()
        meta_path = self._snapshot_meta_path(symbol, timeframe)
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
                unchanged = (
                    meta.get("size") == stat.st_size
                    and meta.get("mtime_ns") == stat.st_mtime_ns
                    and meta.get("ctime_ns") == stat.st_ctime_ns
                    and meta.get("inode") == stat.st_ino
                )
                if unchanged:
                    digest = meta.get("close_sha256")
                    if isinstance(digest, str):
                        return digest
            except (OSError, json.JSONDecodeError):
                pass
        close = pl.read_parquet(path, columns=["close"])["close"]
        return self._write_snapshot_meta(symbol, timeframe, path, close)

    # -- signal-seam access ------------------------------------------------

    def load_market_data(
        self,
        symbols: list[str],
        timeframe: Timeframe,
        start: datetime | None = None,
        end: datetime | None = None,
        adjusted: bool = True,
        strict: bool = True,
        allow_stale_adjusted: bool = False,
    ) -> MarketData:
        """Load per-symbol pandas frames (tz-naive DatetimeIndex named "ts",
        columns open/high/low/close/volume) into a MarketData container.

        When adjusted=True, adjusted parquet is preferred; a series whose
        recorded action signature no longer matches the corporate-actions
        table (an action landed after the last `data adjust` pass) raises a
        DataError by default. ``allow_stale_adjusted=True`` is an explicit
        unsafe diagnostic override that serves it with a loud warning. If no
        adjusted series exists for a symbol,
        raw fallback is allowed (with a warning) ONLY when no price-affecting
        corporate action is recorded: Kite serves candles adjusted as of
        FETCH time, so in this append-only store the raw series is
        mixed-scale across any split/bonus (see docs/assumptions.md) and a
        DataError is raised instead of serving it. Symbols with no data at
        all (neither adjusted nor raw, or no raw when adjusted=False) are
        skipped with a warning.

        Daily frames additionally carry a derived ``total_return_close``
        column (dividends chain-linked into close — see
        ``data/actions.py::total_return_close``) whenever dividend records
        exist for the symbol; signal code prefers it for momentum ranking
        (``strategies/signals/factors.py::_price_series``). The column is
        computed here at load time only — never written back to raw or
        adjusted storage (hard rule 8) — and is simply absent when no
        dividends are recorded.

        Fails loudly when a non-empty ``symbols`` request yields ZERO
        loadable symbols (every one skipped) — this is almost always a
        misconfigured store (e.g. a script launched from a subdirectory that
        silently resolved a different/empty data directory) rather than a
        legitimately empty universe, and left unchecked it surfaces much
        later as a confusing "empty universe" error deep in strategy/engine
        code. A PARTIAL hit (some symbols found, some missing) stays a
        per-symbol warning, unchanged. Paper/live sessions pass
        ``strict=False``: an empty historical store is legitimate there
        (bars are only indicator warm-up; quotes arrive from the live feed).
        """
        frames: dict[str, pd.DataFrame] = {}
        for sym in symbols:
            pdf: pl.DataFrame | None = None
            if adjusted and self.has_adjusted(sym, timeframe):
                self._guard_adjustments_stale(sym, timeframe, allow_stale_adjusted)
                pdf = self.read_adjusted(sym, timeframe, start, end)
            elif adjusted and self.has_raw(sym, timeframe):
                self._guard_raw_fallback(sym, timeframe)
                pdf = self.read_raw(sym, timeframe, start, end)
            elif not adjusted and self.has_raw(sym, timeframe):
                pdf = self.read_raw(sym, timeframe, start, end)

            if pdf is None:
                logger.warning("no %s data for %s; skipping", timeframe.value, sym)
                continue

            pandas_df = pdf.to_pandas().set_index("ts")[list(_OHLCV_COLS)]
            pandas_df.index.name = "ts"
            if timeframe == Timeframe.DAY:
                self._attach_total_return_close(sym, pandas_df)
            frames[sym] = pandas_df

        if strict and symbols and not frames:
            store_path = self._settings.raw_dir / timeframe.value
            raise DataError(
                f"load_market_data found 0 of {len(symbols)} requested symbol(s) "
                f"({timeframe.value}) in the store at {store_path}; if this is "
                "unexpected, check that you're running from the project root (or that "
                "TOS_DATA_DIR / .env resolves to the right data directory -- a wrong "
                "cwd is a common cause of an empty-looking store) and that data has "
                "actually been ingested (`platform data sync`)"
            )

        return MarketData(
            frames=frames,
            timeframe=timeframe,
            snapshot_id=self.snapshot_id(symbols, timeframe),
        )

    def _attach_total_return_close(self, symbol: str, frame: pd.DataFrame) -> None:
        """Add the derived ``total_return_close`` column in place, when dividends
        exist for ``symbol`` (daily frames only — dividend ex-dates are dates).

        DERIVED AT LOAD TIME ONLY: raw market data is immutable (hard rule 8)
        and even the adjusted parquet stays pure OHLCV — this column lives
        exclusively in the in-memory signal-seam frame. Point-in-time safe by
        construction: the value at row t chain-links only closes and dividend
        ex-dates <= t (see ``actions.total_return_close``), and DataView slices
        the column like any other (bars <= now). When no dividends are recorded
        the column is absent and signal code falls back to plain close.
        """
        from tradingos.data.actions import get_dividends, total_return_close

        dividends = get_dividends(symbol, self._settings)
        if not dividends:
            return
        frame["total_return_close"] = total_return_close(frame["close"], dividends)

    def _guard_adjustments_stale(
        self, symbol: str, timeframe: Timeframe, allow_stale: bool = False
    ) -> None:
        """Reject adjusted data when the corporate-actions table has changed since the
        adjusted series was last built: every bar before the new action's
        ex-date is mis-scaled until `platform data adjust` is re-run. A
        missing sidecar meta (adjusted data written outside build_adjusted)
        is treated as 'built with zero actions'. ``allow_stale`` is an unsafe
        diagnostics-only escape hatch and emits a warning when used."""
        from tradingos.data.actions import actions_signature, get_actions

        current_sig = actions_signature(get_actions(symbol, self._settings))
        meta = self.read_adjustment_meta(symbol, timeframe)
        built_sig = meta.get("actions_sig") if meta is not None else actions_signature([])
        if built_sig != current_sig:
            message = (
                f"adjusted {timeframe.value} data for {symbol} is STALE: the "
                "corporate-actions table changed since the adjusted series was last "
                "built (pre-action bars are mis-scaled until it is rebuilt) -- re-run "
                f"`platform data adjust {symbol} --timeframe {timeframe.value}`"
            )
            if not allow_stale:
                raise DataError(message)
            logger.warning(
                "%s; UNSAFE allow_stale_adjusted override enabled for diagnostics",
                message,
            )

    def _guard_raw_fallback(self, symbol: str, timeframe: Timeframe) -> None:
        """adjusted=True but no adjusted series exists. Serving raw is only
        acceptable when no price-affecting corporate action is recorded (then
        adjusted == raw under everything we know). With recorded actions, the
        append-only raw series is mixed-scale across each action's ex-date
        (Kite adjusts at fetch time, stored rows keep their fetch-time scale),
        so serving it would silently corrupt every backtest: raise instead."""
        from tradingos.data.actions import PRICE_ACTIONS, get_actions

        price_actions = [
            a for a in get_actions(symbol, self._settings) if a.action_type in PRICE_ACTIONS
        ]
        if price_actions:
            raise DataError(
                f"no adjusted {timeframe.value} data for {symbol}, but "
                f"{len(price_actions)} price-affecting corporate action(s) are recorded; "
                "raw bars in an append-only store are mixed-scale across an action and "
                "must not be served -- run "
                f"`platform data adjust {symbol} --timeframe {timeframe.value}` first"
            )
        logger.warning(
            "no adjusted %s data for %s; falling back to raw bars (no price-affecting "
            "corporate actions are recorded, so raw == adjusted under recorded "
            "knowledge; run `platform data adjust %s` to materialize the adjusted "
            "series and record that state)",
            timeframe.value,
            symbol,
            symbol,
        )

    # -- duckdb -------------------------------------------------------------

    def duckdb(self) -> duckdb.DuckDBPyConnection:
        """In-memory DuckDB connection with views over the parquet stores:
        bars_raw_day, bars_raw_minute, bars_adj_day, bars_adj_minute — each
        with columns symbol, ts, open, high, low, close, volume. A view is
        only created if its directory actually has parquet files."""
        con = duckdb.connect(database=":memory:")
        view_specs = (
            ("bars_raw_day", self._settings.raw_dir / Timeframe.DAY.value),
            ("bars_raw_minute", self._settings.raw_dir / Timeframe.MINUTE.value),
            ("bars_adj_day", self._settings.adjusted_dir / Timeframe.DAY.value),
            ("bars_adj_minute", self._settings.adjusted_dir / Timeframe.MINUTE.value),
        )
        for view_name, dir_path in view_specs:
            if not dir_path.exists() or not any(dir_path.glob("*.parquet")):
                continue
            glob = (dir_path / "*.parquet").as_posix()
            con.execute(
                f"""
                CREATE VIEW {view_name} AS
                SELECT
                    regexp_extract(filename, '([^/]+)\\.parquet$', 1) AS symbol,
                    ts, open, high, low, close, volume
                FROM read_parquet('{glob}', filename=true)
                """
            )
        return con

    def query(self, sql: str) -> pl.DataFrame:
        """Convenience: run `sql` against duckdb() and return a polars DataFrame."""
        con = self.duckdb()
        try:
            return con.execute(sql).pl()
        finally:
            con.close()
