"""Incremental top-up sync used by the `data sync` CLI command.

For each symbol x timeframe: resume one bar after the store's last known
timestamp (or `default_start` on first sync), fetch via HistoricalFetcher,
and write into the store. A failure on one symbol/timeframe is captured on
its SyncResult rather than aborting the whole batch.

Completed bars only: Kite serves the CURRENT, still-forming candle for the
in-progress period. The raw store is append-only and never re-fetches, so a
forming bar written today would either stay permanently wrong (daily) or
brick the next sync with an immutability conflict (minute). Daily fetches
are therefore clamped to the previous session until 15:30 IST, and minute
bars that have not yet completed (bar T covers [T, T+1min)) are dropped
before the write. See docs/assumptions.md.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import polars as pl

from tradingos.config.settings import Settings
from tradingos.core.logging import get_logger
from tradingos.core.models import Timeframe
from tradingos.core.timeutils import MARKET_CLOSE, now_ist
from tradingos.data.fetcher import HistoricalFetcher
from tradingos.data.instruments import token_for
from tradingos.data.ratelimit import TokenBucket

logger = get_logger(__name__)

# Kite minute-candle history is huge; on a symbol's first sync, don't try to
# backfill all the way to `default_start` for minute data -- cap it.
MINUTE_LOOKBACK_DAYS = 120

_BAR_DELTA: dict[Timeframe, timedelta] = {
    Timeframe.DAY: timedelta(days=1),
    Timeframe.MINUTE: timedelta(minutes=1),
}

# Kite historical API: 3 requests/second, shared across the whole sync run.
HISTORICAL_RATE = 3.0
HISTORICAL_BURST = 3


@dataclass
class SyncResult:
    symbol: str
    timeframe: Timeframe
    rows_added: int
    from_ts: datetime | None
    to_ts: datetime | None
    error: str | None = None


def _initial_start(timeframe: Timeframe, default_start: date, today: date) -> date:
    if timeframe == Timeframe.MINUTE:
        cap = today - timedelta(days=MINUTE_LOOKBACK_DAYS)
        return max(default_start, cap)
    return default_start


def _completed_fetch_end(timeframe: Timeframe, now: datetime) -> date:
    """Latest date whose `timeframe` bars can all be COMPLETE at `now`.

    Daily bars complete at 15:30 IST (CLAUDE.md convention), so before the
    close today's candle is still forming and the fetch is clamped to
    yesterday (on a non-trading day the clamped date simply returns no
    bars). Minute bars complete continuously through the session, so the
    date bound is today and the per-bar cutoff is applied after the fetch
    (see _drop_forming_bars)."""
    if timeframe == Timeframe.DAY and now.time() < MARKET_CLOSE:
        return now.date() - timedelta(days=1)
    return now.date()


def _drop_forming_bars(df: pl.DataFrame, timeframe: Timeframe, now: datetime) -> pl.DataFrame:
    """Drop minute bars not yet complete at `now`. A minute bar stamped T
    covers [T, T+1min) and completes at T+1min; keeping a forming bar would
    permanently conflict with its final values in the append-only store."""
    if timeframe != Timeframe.MINUTE or df.height == 0:
        return df
    latest_complete = now - _BAR_DELTA[Timeframe.MINUTE]
    return df.filter(pl.col("ts") <= latest_complete)


def sync_symbols(
    kite: object,
    settings: Settings,
    symbols: list[str],
    timeframes: list[Timeframe],
    *,
    store: object | None = None,
    default_start: date = date(2010, 1, 1),
    on_synced: Callable[[str, Timeframe], None] | None = None,
    now: datetime | None = None,
) -> list[SyncResult]:
    """Top up local storage for each symbol x timeframe to the latest
    COMPLETED candle (never a still-forming one; see module docstring).

    `store` must provide `last_ts(symbol, timeframe) -> datetime | None` and
    `write_raw(symbol, timeframe, df: pl.DataFrame) -> int`. If omitted, the
    real `BarStore` is constructed (imported lazily so this module always
    imports cleanly even before that module exists). `now` (tz-naive IST)
    defaults to the wall clock; injectable for tests.
    """
    if store is None:
        from tradingos.data.store import BarStore  # lazy: avoid a hard import-time dependency

        store = BarStore(settings)

    rate_limiter = TokenBucket(HISTORICAL_RATE, HISTORICAL_BURST)
    fetcher = HistoricalFetcher(kite, rate_limiter)
    now = now if now is not None else now_ist()

    results: list[SyncResult] = []
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                result = _sync_one(
                    fetcher, store, settings, symbol, timeframe, default_start, now
                )
            except Exception as exc:  # noqa: BLE001 -- one bad symbol must not abort the batch
                logger.error("sync failed for %s %s: %s", symbol, timeframe.value, exc)
                result = SyncResult(
                    symbol=symbol,
                    timeframe=timeframe,
                    rows_added=0,
                    from_ts=None,
                    to_ts=None,
                    error=str(exc),
                )
            results.append(result)
            if result.error is None and on_synced is not None:
                on_synced(symbol, timeframe)

    return results


def _sync_one(
    fetcher: HistoricalFetcher,
    store: object,
    settings: Settings,
    symbol: str,
    timeframe: Timeframe,
    default_start: date,
    now: datetime,
) -> SyncResult:
    today = now.date()
    instrument_token = token_for(symbol, settings)
    last_ts = store.last_ts(symbol, timeframe)
    if last_ts is not None:
        start_date = (last_ts + _BAR_DELTA[timeframe]).date()
    else:
        start_date = _initial_start(timeframe, default_start, today)

    fetch_end = _completed_fetch_end(timeframe, now)
    if start_date > fetch_end:
        logger.info(
            "%s %s already up to date (last completed session: %s)",
            symbol,
            timeframe.value,
            fetch_end,
        )
        return SyncResult(symbol=symbol, timeframe=timeframe, rows_added=0, from_ts=None, to_ts=None)

    df = fetcher.fetch(symbol, instrument_token, timeframe, start_date, fetch_end)
    df = _drop_forming_bars(df, timeframe, now)
    rows_added = store.write_raw(symbol, timeframe, df)
    from_ts = df["ts"].min() if df.height > 0 else None
    to_ts = df["ts"].max() if df.height > 0 else None
    logger.info(
        "synced %s %s: %d row(s) added (%s..%s)", symbol, timeframe.value, rows_added, from_ts, to_ts
    )
    return SyncResult(
        symbol=symbol, timeframe=timeframe, rows_added=rows_added, from_ts=from_ts, to_ts=to_ts
    )
