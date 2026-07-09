"""Time helpers. Convention: all timestamps in the platform are tz-naive IST.

Kite returns tz-aware (+05:30) datetimes; strip the tzinfo at the ingestion
boundary (after converting to IST) and never reattach it internally.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


def now_ist() -> datetime:
    """Current wall-clock time in IST, tz-naive."""
    return datetime.now(IST).replace(tzinfo=None)


def to_naive_ist(dt: datetime) -> datetime:
    """Convert any datetime to tz-naive IST. Naive input is assumed IST already."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(IST).replace(tzinfo=None)


def is_market_hours(dt: datetime | None = None) -> bool:
    """True if dt (naive IST) falls within NSE regular session hours.
    Does NOT check holidays — combine with the holiday calendar for that."""
    dt = dt or now_ist()
    if dt.weekday() >= 5:
        return False
    return MARKET_OPEN <= dt.time() <= MARKET_CLOSE


def session_bounds(d: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(d, MARKET_OPEN),
        datetime.combine(d, MARKET_CLOSE),
    )


def date_chunks(start: date, end: date, max_days: int) -> list[tuple[date, date]]:
    """Split [start, end] inclusive into consecutive chunks of at most max_days days.

    Used by the historical fetcher to respect Kite's max-span-per-request limits.
    """
    if start > end:
        raise ValueError(f"start {start} after end {end}")
    if max_days < 1:
        raise ValueError("max_days must be >= 1")
    chunks: list[tuple[date, date]] = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=max_days - 1), end)
        chunks.append((cur, chunk_end))
        cur = chunk_end + timedelta(days=1)
    return chunks
