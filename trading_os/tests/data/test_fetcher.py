"""HistoricalFetcher tests: chunking, retry/backoff, tz conversion, dedup,
schema validation. `kite` is a fake object -- never any network."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import polars as pl
import pytest

from tradingos.core.errors import DataError, RateLimitError
from tradingos.core.models import OHLCV_COLUMNS, Timeframe
from tradingos.core.timeutils import IST
from tradingos.data.fetcher import MAX_SPAN_DAYS, HistoricalFetcher
from tradingos.data.ratelimit import TokenBucket


class FakeKite:
    """Fake kiteconnect.KiteConnect exposing only historical_data."""

    def __init__(self, responder) -> None:
        self._responder = responder
        self.calls: list[tuple] = []

    def historical_data(self, instrument_token, from_date, to_date, interval):
        self.calls.append((instrument_token, from_date, to_date, interval))
        return self._responder(instrument_token, from_date, to_date, interval)


def generous_rate_limiter() -> TokenBucket:
    # High rate/capacity so acquire() never blocks; timing is ratelimit.py's job.
    return TokenBucket(rate=1000.0, capacity=1000)


def test_max_span_days_constants() -> None:
    assert MAX_SPAN_DAYS == {Timeframe.DAY: 2000, Timeframe.MINUTE: 60}


class TestChunking:
    def test_day_candles_5000_day_span_makes_3_requests(self) -> None:
        kite = FakeKite(lambda *_a: [])
        fetcher = HistoricalFetcher(kite, generous_rate_limiter())
        start = date(2010, 1, 1)
        end = start + timedelta(days=4999)  # 5000-day inclusive span

        fetcher.fetch("TEST", 111, Timeframe.DAY, start, end)

        assert len(kite.calls) == 3
        spans = [(c[1], c[2]) for c in kite.calls]
        assert spans[0] == (start, start + timedelta(days=1999))
        assert spans[1] == (start + timedelta(days=2000), start + timedelta(days=3999))
        assert spans[2] == (start + timedelta(days=4000), end)
        assert all(c[3] == "day" for c in kite.calls)

    def test_minute_candles_span_chunked_at_60_days(self) -> None:
        kite = FakeKite(lambda *_a: [])
        fetcher = HistoricalFetcher(kite, generous_rate_limiter())
        start = date(2024, 1, 1)
        end = start + timedelta(days=199)  # 200-day span -> ceil(200/60) = 4 chunks

        fetcher.fetch("TEST", 111, Timeframe.MINUTE, start, end)

        assert len(kite.calls) == 4
        assert all(c[3] == "minute" for c in kite.calls)
        assert kite.calls[0][1:3] == (start, start + timedelta(days=59))

    def test_single_day_request_is_one_chunk(self) -> None:
        kite = FakeKite(lambda *_a: [])
        fetcher = HistoricalFetcher(kite, generous_rate_limiter())
        d = date(2024, 5, 1)
        fetcher.fetch("TEST", 111, Timeframe.DAY, d, d)
        assert len(kite.calls) == 1


class TestRetryBackoff:
    def test_retries_then_succeeds(self) -> None:
        attempts = {"n": 0}

        def responder(*_a):
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise ConnectionError("transient network blip")
            return [
                {
                    "date": datetime(2020, 1, 1, 9, 15, tzinfo=IST),
                    "open": 1.0,
                    "high": 1.5,
                    "low": 0.9,
                    "close": 1.2,
                    "volume": 100,
                }
            ]

        kite = FakeKite(responder)
        sleeps: list[float] = []
        fetcher = HistoricalFetcher(kite, generous_rate_limiter(), sleep=sleeps.append)

        df = fetcher.fetch("TEST", 111, Timeframe.DAY, date(2020, 1, 1), date(2020, 1, 1))

        assert df.height == 1
        assert attempts["n"] == 3
        assert sleeps == [1.0, 2.0]  # base=1s, factor=2, two retries before success

    def test_exhaustion_raises_data_error_with_context(self) -> None:
        def responder(*_a):
            raise ConnectionError("down for good")

        kite = FakeKite(responder)
        sleeps: list[float] = []
        fetcher = HistoricalFetcher(kite, generous_rate_limiter(), sleep=sleeps.append)

        with pytest.raises(DataError, match="TEST"):
            fetcher.fetch("TEST", 111, Timeframe.DAY, date(2020, 1, 1), date(2020, 1, 1))

        assert len(kite.calls) == 5  # _MAX_ATTEMPTS
        assert sleeps == [1.0, 2.0, 4.0, 8.0]

    def test_exhaustion_preserves_rate_limit_error_type(self) -> None:
        def responder(*_a):
            raise RateLimitError("429 too many requests")

        kite = FakeKite(responder)
        fetcher = HistoricalFetcher(kite, generous_rate_limiter(), sleep=lambda _s: None)

        with pytest.raises(RateLimitError):
            fetcher.fetch("TEST", 111, Timeframe.DAY, date(2020, 1, 1), date(2020, 1, 1))


class TestTzConversion:
    def test_converts_utc_to_naive_ist(self) -> None:
        # 03:45 UTC == 09:15 IST (UTC+5:30)
        rows = [
            {
                "date": datetime(2020, 1, 1, 3, 45, tzinfo=UTC),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000,
            }
        ]
        kite = FakeKite(lambda *_a: rows)
        fetcher = HistoricalFetcher(kite, generous_rate_limiter())

        df = fetcher.fetch("TEST", 111, Timeframe.DAY, date(2020, 1, 1), date(2020, 1, 1))

        ts = df["ts"][0]
        assert ts == datetime(2020, 1, 1, 9, 15)
        assert ts.tzinfo is None

    def test_converts_ist_aware_to_naive(self) -> None:
        rows = [
            {
                "date": datetime(2020, 1, 1, 9, 15, tzinfo=IST),
                "open": 1.0,
                "high": 1.0,
                "low": 1.0,
                "close": 1.0,
                "volume": 1,
            }
        ]
        kite = FakeKite(lambda *_a: rows)
        fetcher = HistoricalFetcher(kite, generous_rate_limiter())
        df = fetcher.fetch("TEST", 111, Timeframe.DAY, date(2020, 1, 1), date(2020, 1, 1))
        assert df["ts"][0] == datetime(2020, 1, 1, 9, 15)


class TestDedupAndSchema:
    def test_dedups_overlapping_chunk_boundaries(self) -> None:
        calls = {"n": 0}

        def responder(*_a):
            idx = calls["n"]
            calls["n"] += 1
            if idx == 0:
                return [
                    {"date": datetime(2020, 1, 1, 9, 15), "open": 1, "high": 1, "low": 1, "close": 1, "volume": 10},
                    {"date": datetime(2020, 1, 2, 9, 15), "open": 2, "high": 2, "low": 2, "close": 2, "volume": 20},
                ]
            return [
                # duplicate of chunk 1's last bar (simulates an inclusive-boundary overlap)
                {"date": datetime(2020, 1, 2, 9, 15), "open": 2, "high": 2, "low": 2, "close": 2, "volume": 20},
                {"date": datetime(2020, 1, 3, 9, 15), "open": 3, "high": 3, "low": 3, "close": 3, "volume": 30},
            ]

        kite = FakeKite(responder)
        fetcher = HistoricalFetcher(kite, generous_rate_limiter())
        # force exactly 2 minute chunks (max span 60 days)
        df = fetcher.fetch("TEST", 111, Timeframe.MINUTE, date(2020, 1, 1), date(2020, 1, 1) + timedelta(days=65))

        assert calls["n"] == 2
        assert df.height == 3  # 4 raw rows, 1 duplicate ts -> 3 unique
        assert df["ts"].n_unique() == 3

    def test_output_schema_and_sort_order(self) -> None:
        rows = [
            {"date": datetime(2020, 1, 2, 9, 15), "open": 2, "high": 2, "low": 2, "close": 2, "volume": 20},
            {"date": datetime(2020, 1, 1, 9, 15), "open": 1, "high": 1, "low": 1, "close": 1, "volume": 10},
        ]
        kite = FakeKite(lambda *_a: rows)
        fetcher = HistoricalFetcher(kite, generous_rate_limiter())
        df = fetcher.fetch("TEST", 111, Timeframe.DAY, date(2020, 1, 1), date(2020, 1, 2))

        assert df.columns == OHLCV_COLUMNS
        assert df["ts"].to_list() == sorted(df["ts"].to_list())
        assert df.schema["volume"] == pl.Int64
        assert df.schema["close"] == pl.Float64

    def test_empty_result_returns_empty_frame_with_schema(self) -> None:
        kite = FakeKite(lambda *_a: [])
        fetcher = HistoricalFetcher(kite, generous_rate_limiter())
        df = fetcher.fetch("TEST", 111, Timeframe.DAY, date(2020, 1, 1), date(2020, 1, 1))
        assert df.height == 0
        assert df.columns == OHLCV_COLUMNS

    def test_rejects_zero_or_negative_close(self) -> None:
        rows = [
            {"date": datetime(2020, 1, 1, 9, 15), "open": 1, "high": 1, "low": 1, "close": 0.0, "volume": 10},
        ]
        kite = FakeKite(lambda *_a: rows)
        fetcher = HistoricalFetcher(kite, generous_rate_limiter())
        with pytest.raises(DataError):
            fetcher.fetch("TEST", 111, Timeframe.DAY, date(2020, 1, 1), date(2020, 1, 1))
