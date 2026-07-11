"""Rate-limited, date-chunked, retrying fetcher over Kite's historical-data API.

Produces the canonical OHLCV polars schema (ts naive-IST us-precision Datetime,
open/high/low/close Float64, volume Int64), sorted and de-duplicated by ts.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import date, datetime

import polars as pl

from tradingos.core.errors import DataError, RateLimitError
from tradingos.core.logging import get_logger
from tradingos.core.models import OHLCV_COLUMNS, Timeframe
from tradingos.core.timeutils import date_chunks, to_naive_ist
from tradingos.data.ratelimit import TokenBucket

logger = get_logger(__name__)

# Kite's documented max span per historical_data request, by interval.
MAX_SPAN_DAYS: dict[Timeframe, int] = {
    Timeframe.DAY: 2000,
    Timeframe.MINUTE: 60,
}

_RETRY_BASE_SECONDS = 1.0
_RETRY_FACTOR = 2.0
_MAX_ATTEMPTS = 5

CANONICAL_SCHEMA: dict[str, pl.DataType] = {
    "ts": pl.Datetime("us"),
    "open": pl.Float64,
    "high": pl.Float64,
    "low": pl.Float64,
    "close": pl.Float64,
    "volume": pl.Int64,
}


class HistoricalFetcher:
    """Wraps `kite.historical_data` with rate limiting, date chunking, and
    retry/backoff. `kite` is any object exposing
    `historical_data(instrument_token, from_date, to_date, interval=...)`
    -- a real `kiteconnect.KiteConnect` in production, a stub in tests.
    """

    def __init__(
        self,
        kite: object,
        rate_limiter: TokenBucket,
        *,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.kite = kite
        self.rate_limiter = rate_limiter
        self._sleep = sleep

    def fetch(
        self,
        symbol: str,
        instrument_token: int,
        timeframe: Timeframe,
        start_date: date,
        end_date: date,
    ) -> pl.DataFrame:
        max_span = MAX_SPAN_DAYS[timeframe]
        chunks = date_chunks(start_date, end_date, max_span)
        logger.info(
            "fetching %s %s [%s..%s] in %d chunk(s)",
            symbol,
            timeframe.value,
            start_date,
            end_date,
            len(chunks),
        )
        rows: list[dict] = []
        for chunk_start, chunk_end in chunks:
            rows.extend(
                self._fetch_chunk(symbol, instrument_token, timeframe, chunk_start, chunk_end)
            )
        return self._to_frame(rows, symbol=symbol)

    # -- internals ---------------------------------------------------------

    def _fetch_chunk(
        self,
        symbol: str,
        instrument_token: int,
        timeframe: Timeframe,
        chunk_start: date,
        chunk_end: date,
    ) -> list[dict]:
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            self.rate_limiter.acquire()
            try:
                return self.kite.historical_data(
                    instrument_token,
                    chunk_start,
                    chunk_end,
                    interval=timeframe.value,
                )
            except Exception as exc:  # noqa: BLE001 -- kiteconnect raises varied types
                last_exc = exc
                if attempt == _MAX_ATTEMPTS:
                    break
                wait = _RETRY_BASE_SECONDS * (_RETRY_FACTOR ** (attempt - 1))
                logger.warning(
                    "historical_data failed for %s %s [%s..%s] (attempt %d/%d): %s; retrying in %.1fs",
                    symbol,
                    timeframe.value,
                    chunk_start,
                    chunk_end,
                    attempt,
                    _MAX_ATTEMPTS,
                    exc,
                    wait,
                )
                self._sleep(wait)

        assert last_exc is not None  # loop always sets it before breaking
        raise self._wrap_exception(last_exc, symbol, timeframe, chunk_start, chunk_end)

    @staticmethod
    def _wrap_exception(
        exc: Exception,
        symbol: str,
        timeframe: Timeframe,
        chunk_start: date,
        chunk_end: date,
    ) -> Exception:
        context = (
            f"{symbol} {timeframe.value} [{chunk_start}..{chunk_end}] "
            f"failed after {_MAX_ATTEMPTS} attempts: {exc}"
        )
        if isinstance(exc, RateLimitError):
            return RateLimitError(context)
        if isinstance(exc, DataError):
            return DataError(context)
        return DataError(context)

    @staticmethod
    def _to_frame(rows: list[dict], *, symbol: str) -> pl.DataFrame:
        if not rows:
            return pl.DataFrame(schema=CANONICAL_SCHEMA).select(OHLCV_COLUMNS)

        ts_list: list[datetime] = []
        open_list: list[float] = []
        high_list: list[float] = []
        low_list: list[float] = []
        close_list: list[float] = []
        volume_list: list[int] = []
        for row in rows:
            raw_ts = row["date"]
            if isinstance(raw_ts, str):
                raw_ts = datetime.fromisoformat(raw_ts)
            ts_list.append(to_naive_ist(raw_ts))
            open_list.append(float(row["open"]))
            high_list.append(float(row["high"]))
            low_list.append(float(row["low"]))
            close_list.append(float(row["close"]))
            volume_list.append(int(row["volume"]))

        df = pl.DataFrame(
            {
                "ts": ts_list,
                "open": open_list,
                "high": high_list,
                "low": low_list,
                "close": close_list,
                "volume": volume_list,
            },
            schema=CANONICAL_SCHEMA,
        )
        df = df.sort("ts").unique(subset=["ts"], keep="first", maintain_order=True)

        bad = df.filter(pl.col("close") <= 0)
        if bad.height > 0:
            raise DataError(
                f"{symbol}: {bad.height} bar(s) with zero/negative close in fetched data"
            )
        return df.select(OHLCV_COLUMNS)
