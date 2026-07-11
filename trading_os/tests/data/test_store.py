from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd
import polars as pl
import pytest

from tradingos.core.errors import DataError
from tradingos.core.models import Timeframe
from tradingos.data.store import BAR_SCHEMA, BarStore, validate_bars

DAY1 = datetime(2024, 1, 1)
DAY2 = datetime(2024, 1, 2)
DAY3 = datetime(2024, 1, 3)

_ROWS = [
    (DAY1, 100.0, 101.0, 99.0, 100.5, 1000),
    (DAY2, 100.5, 102.0, 100.0, 101.5, 1500),
    (DAY3, 101.5, 103.0, 101.0, 102.5, 2000),
]


def bars(n: int = 3) -> pl.DataFrame:
    """First n rows of a small deterministic bar frame."""
    ts, o, hi, lo, c, v = zip(*_ROWS[:n], strict=True)
    return pl.DataFrame(
        {
            "ts": list(ts),
            "open": list(o),
            "high": list(hi),
            "low": list(lo),
            "close": list(c),
            "volume": list(v),
        }
    )


class TestValidateBars:
    def test_casts_sorts_and_matches_schema(self) -> None:
        df = pl.DataFrame(
            {
                "ts": [DAY2, DAY1],
                "open": [1, 2],  # int -> Float64
                "high": [1, 2],
                "low": [1, 2],
                "close": [1, 2],
                "volume": [10.0, 20.0],  # float -> Int64
            }
        )
        out = validate_bars(df)
        assert out["ts"].to_list() == [DAY1, DAY2]
        assert dict(out.schema) == BAR_SCHEMA

    def test_missing_column_raises(self) -> None:
        df = bars().drop("volume")
        with pytest.raises(DataError, match="missing required columns"):
            validate_bars(df)

    def test_null_raises(self) -> None:
        df = pl.DataFrame(
            {
                "ts": [DAY1, DAY2],
                "open": [1.0, 2.0],
                "high": [1.0, 2.0],
                "low": [1.0, 2.0],
                "close": [1.0, None],
                "volume": [10, 20],
            }
        )
        with pytest.raises(DataError, match="null"):
            validate_bars(df)

    def test_identical_duplicate_ts_deduped(self) -> None:
        df = pl.concat([bars(2), bars(1)])  # DAY1 row repeated, identical values
        out = validate_bars(df)
        assert out.height == 2
        assert out["ts"].to_list() == [DAY1, DAY2]

    def test_conflicting_duplicate_ts_raises(self) -> None:
        df1 = bars(1)
        df2 = df1.with_columns((pl.col("close") + 5).alias("close"))
        df = pl.concat([df1, df2])
        with pytest.raises(DataError, match="conflicting"):
            validate_bars(df)


class TestRawStore:
    def test_write_read_roundtrip_preserves_dtype_and_order(self, settings) -> None:
        store = BarStore(settings)
        added = store.write_raw("TEST", Timeframe.DAY, bars())
        assert added == 3
        out = store.read_raw("TEST", Timeframe.DAY)
        assert out["ts"].to_list() == [DAY1, DAY2, DAY3]
        assert dict(out.schema) == BAR_SCHEMA
        assert out.equals(validate_bars(bars()))

    def test_append_only_merge_skips_identical_rows(self, settings) -> None:
        store = BarStore(settings)
        first = store.write_raw("TEST", Timeframe.DAY, bars(2))
        assert first == 2
        second = store.write_raw("TEST", Timeframe.DAY, bars(3))  # DAY1/DAY2 repeat, DAY3 new
        assert second == 1
        assert store.read_raw("TEST", Timeframe.DAY).height == 3

    def test_conflicting_rewrite_raises_and_leaves_raw_untouched(self, settings) -> None:
        store = BarStore(settings)
        store.write_raw("TEST", Timeframe.DAY, bars(2))
        conflicting = bars(2).with_columns((pl.col("close") + 1.0).alias("close"))
        with pytest.raises(DataError, match="TEST"):
            store.write_raw("TEST", Timeframe.DAY, conflicting)
        # raw history unchanged after the failed write
        out = store.read_raw("TEST", Timeframe.DAY)
        assert out.equals(validate_bars(bars(2)))

    def test_read_absent_raises(self, settings) -> None:
        store = BarStore(settings)
        with pytest.raises(DataError):
            store.read_raw("NOPE", Timeframe.DAY)

    def test_has_raw(self, settings) -> None:
        store = BarStore(settings)
        assert not store.has_raw("TEST", Timeframe.DAY)
        store.write_raw("TEST", Timeframe.DAY, bars())
        assert store.has_raw("TEST", Timeframe.DAY)

    def test_range_filter(self, settings) -> None:
        store = BarStore(settings)
        store.write_raw("TEST", Timeframe.DAY, bars())
        out = store.read_raw("TEST", Timeframe.DAY, start=DAY2, end=DAY2)
        assert out["ts"].to_list() == [DAY2]


class TestAdjustedStore:
    def test_write_adjusted_fully_overwrites(self, settings) -> None:
        store = BarStore(settings)
        store.write_adjusted("TEST", Timeframe.DAY, bars(3))
        assert store.read_adjusted("TEST", Timeframe.DAY).height == 3
        n = store.write_adjusted("TEST", Timeframe.DAY, bars(2))
        assert n == 2
        assert store.read_adjusted("TEST", Timeframe.DAY).height == 2

    def test_has_adjusted(self, settings) -> None:
        store = BarStore(settings)
        assert not store.has_adjusted("TEST", Timeframe.DAY)
        store.write_adjusted("TEST", Timeframe.DAY, bars())
        assert store.has_adjusted("TEST", Timeframe.DAY)

    def test_read_absent_raises(self, settings) -> None:
        store = BarStore(settings)
        with pytest.raises(DataError):
            store.read_adjusted("TEST", Timeframe.DAY)


class TestMetadata:
    def test_last_ts_and_symbols(self, settings) -> None:
        store = BarStore(settings)
        assert store.last_ts("TEST", Timeframe.DAY) is None
        assert store.symbols(Timeframe.DAY) == []

        store.write_raw("BBB", Timeframe.DAY, bars(2))
        store.write_raw("AAA", Timeframe.DAY, bars(3))

        assert store.last_ts("AAA", Timeframe.DAY) == DAY3
        assert store.last_ts("BBB", Timeframe.DAY) == DAY2
        assert store.symbols(Timeframe.DAY) == ["AAA", "BBB"]  # sorted

    def test_snapshot_id_stable_and_sensitive_to_new_bars(self, settings) -> None:
        store = BarStore(settings)
        store.write_raw("TEST", Timeframe.DAY, bars(2))
        id1 = store.snapshot_id(["TEST"], Timeframe.DAY)
        id2 = store.snapshot_id(["TEST"], Timeframe.DAY)
        assert id1 == id2
        assert len(id1) == 16
        int(id1, 16)  # valid hex string

        store.write_raw("TEST", Timeframe.DAY, bars(3))  # one new bar
        id3 = store.snapshot_id(["TEST"], Timeframe.DAY)
        assert id3 != id1

    def test_snapshot_id_independent_of_input_order(self, settings) -> None:
        store = BarStore(settings)
        store.write_raw("AAA", Timeframe.DAY, bars())
        store.write_raw("BBB", Timeframe.DAY, bars())
        assert store.snapshot_id(["AAA", "BBB"], Timeframe.DAY) == store.snapshot_id(
            ["BBB", "AAA"], Timeframe.DAY
        )


class TestLoadMarketData:
    def test_prefers_adjusted_when_present(self, settings) -> None:
        store = BarStore(settings)
        store.write_raw("TEST", Timeframe.DAY, bars())
        adjusted = bars().with_columns((pl.col("close") * 0.5).alias("close"))
        store.write_adjusted("TEST", Timeframe.DAY, adjusted)

        md = store.load_market_data(["TEST"], Timeframe.DAY, adjusted=True)
        assert md.symbols == ["TEST"]
        frame = md.full_frame("TEST")
        assert isinstance(frame.index, pd.DatetimeIndex)
        assert frame.index.name == "ts"
        assert frame.index.tz is None
        assert list(frame.columns) == ["open", "high", "low", "close", "volume"]
        assert frame["close"].iloc[0] == pytest.approx(50.25)  # adjusted value, not raw 100.5
        assert md.snapshot_id == store.snapshot_id(["TEST"], Timeframe.DAY)

    def test_falls_back_to_raw_with_warning_when_no_adjusted(self, settings, caplog) -> None:
        store = BarStore(settings)
        store.write_raw("TEST", Timeframe.DAY, bars())
        with caplog.at_level(logging.WARNING, logger="tradingos.data.store"):
            md = store.load_market_data(["TEST"], Timeframe.DAY, adjusted=True)
        assert "falling back to raw" in caplog.text
        assert md.full_frame("TEST")["close"].iloc[0] == pytest.approx(100.5)

    def test_skips_symbol_with_no_data_and_warns(self, settings, caplog) -> None:
        store = BarStore(settings)
        store.write_raw("TEST", Timeframe.DAY, bars())
        with caplog.at_level(logging.WARNING, logger="tradingos.data.store"):
            md = store.load_market_data(["TEST", "GHOST"], Timeframe.DAY, adjusted=True)
        assert md.symbols == ["TEST"]
        assert "GHOST" in caplog.text

    def test_unadjusted_mode_uses_raw_even_if_adjusted_exists(self, settings) -> None:
        store = BarStore(settings)
        store.write_raw("TEST", Timeframe.DAY, bars())
        adjusted = bars().with_columns((pl.col("close") * 0.5).alias("close"))
        store.write_adjusted("TEST", Timeframe.DAY, adjusted)
        md = store.load_market_data(["TEST"], Timeframe.DAY, adjusted=False)
        assert md.full_frame("TEST")["close"].iloc[0] == pytest.approx(100.5)


class TestDuckDB:
    def test_views_queryable_and_counts_rows_per_symbol(self, settings) -> None:
        store = BarStore(settings)
        store.write_raw("AAA", Timeframe.DAY, bars(2))
        store.write_raw("BBB", Timeframe.DAY, bars(3))
        out = store.query(
            "SELECT symbol, count(*) AS n FROM bars_raw_day GROUP BY symbol ORDER BY symbol"
        )
        assert out["symbol"].to_list() == ["AAA", "BBB"]
        assert out["n"].to_list() == [2, 3]

    def test_adjusted_view(self, settings) -> None:
        store = BarStore(settings)
        store.write_adjusted("TEST", Timeframe.DAY, bars())
        out = store.query("SELECT * FROM bars_adj_day ORDER BY ts")
        assert out.height == 3

    def test_no_view_created_for_empty_directory(self, settings) -> None:
        store = BarStore(settings)
        con = store.duckdb()
        try:
            tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
            assert "bars_raw_day" not in tables
            assert "bars_adj_minute" not in tables
        finally:
            con.close()
