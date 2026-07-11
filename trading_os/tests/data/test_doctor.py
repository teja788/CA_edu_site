from __future__ import annotations

from datetime import date, datetime, timedelta

import polars as pl
import pytest
from fixtures.synthetic import synthetic_daily

from tradingos.core.models import Timeframe
from tradingos.data.calendar import NSECalendar
from tradingos.data.doctor import DataDoctor, Finding, HealthReport

CAL = NSECalendar()
START = date(2024, 1, 2)  # Tue
END = date(2024, 3, 28)  # Thu -- last bar of the clean fixture


def _holidays_in_range(start: date, end: date) -> set[date]:
    hs: set[date] = set()
    for year in range(start.year, end.year + 1):
        hs |= CAL.holidays(year)
    return hs


def clean_frame(symbol: str = "TEST", start: date = START, end: date = END) -> pl.DataFrame:
    """A synthetic daily bar frame with no data-quality issues: exactly the
    trading days NSECalendar expects in [start, end], sane OHLC, positive
    volume, no duplicates."""
    pdf = synthetic_daily(symbol=symbol, start=start, end=end, seed=7, holidays=_holidays_in_range(start, end))
    pdf = pdf.reset_index().rename(columns={"index": "ts"})
    return pl.from_pandas(pdf[["ts", "open", "high", "low", "close", "volume"]])


def _replace_row(df: pl.DataFrame, index: int, **updates: object) -> pl.DataFrame:
    """Return a copy of df with row `index` patched by `updates` (supports
    setting a cell to None, unlike polars' in-place update expressions)."""
    rows = df.to_dicts()
    rows[index] = {**rows[index], **updates}
    return pl.DataFrame(rows, schema=df.schema)


class FakeStore:
    """Minimal double for the pinned BarStore API DataDoctor depends on:
    read_raw / symbols / last_ts. Never imports the real store."""

    def __init__(self, frames: dict[str, pl.DataFrame] | None = None) -> None:
        self.frames: dict[str, pl.DataFrame] = frames or {}
        self._last_ts_override: dict[str, datetime | None] = {}

    def read_raw(self, symbol: str, timeframe: Timeframe) -> pl.DataFrame:
        return self.frames[symbol]

    def symbols(self, timeframe: Timeframe) -> list[str]:
        return sorted(self.frames)

    def last_ts(self, symbol: str, timeframe: Timeframe) -> datetime | None:
        if symbol in self._last_ts_override:
            return self._last_ts_override[symbol]
        df = self.frames.get(symbol)
        if df is None or df.is_empty():
            return None
        return df.sort("ts").get_column("ts")[-1]

    def set_last_ts(self, symbol: str, ts: datetime | None) -> None:
        self._last_ts_override[symbol] = ts


def make_doctor(frames: dict[str, pl.DataFrame]) -> tuple[DataDoctor, FakeStore]:
    store = FakeStore(frames)
    return DataDoctor(store, CAL), store


class TestCleanData:
    def test_no_findings_at_all(self) -> None:
        doctor, _ = make_doctor({"TEST": clean_frame()})
        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        assert findings == []

    def test_no_data_symbol_gets_info_warn_not_error(self) -> None:
        empty = clean_frame().clear()
        doctor, _ = make_doctor({"TEST": empty})
        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        assert len(findings) == 1
        assert findings[0].check == "no_data"
        assert findings[0].severity == "warn"


class TestDuplicateTimestamps:
    def test_duplicate_row_flagged_as_error(self) -> None:
        df = clean_frame()
        dup_ts = df["ts"][10]
        corrupted = pl.concat([df, df.filter(pl.col("ts") == dup_ts)])
        doctor, _ = make_doctor({"TEST": corrupted})

        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        dup_findings = [f for f in findings if f.check == "duplicate_timestamps"]
        assert len(dup_findings) == 1
        assert dup_findings[0].severity == "error"
        assert dup_findings[0].count == 1
        assert not any(f.check == "missing_trading_days" for f in findings)


class TestInvalidPrices:
    def test_null_price_flagged_as_error_and_isolated(self) -> None:
        df = clean_frame()
        corrupted = _replace_row(df, 20, close=None)
        doctor, _ = make_doctor({"TEST": corrupted})

        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        price_findings = [f for f in findings if f.check == "invalid_price"]
        assert len(price_findings) == 1
        assert price_findings[0].severity == "error"
        assert price_findings[0].count == 1
        # a null close shouldn't also look like an OHLC violation or a price outlier
        assert not any(f.check == "ohlc_consistency" for f in findings)
        assert not any(f.check == "extreme_outlier" for f in findings)

    def test_negative_price_flagged_as_error(self) -> None:
        df = clean_frame()
        corrupted = _replace_row(df, 20, close=-1.0, low=-10.0)
        doctor, _ = make_doctor({"TEST": corrupted})

        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        price_findings = [f for f in findings if f.check == "invalid_price"]
        assert len(price_findings) == 1
        assert price_findings[0].count == 1


class TestOhlcConsistency:
    def test_high_below_low_flagged_as_error_and_isolated(self) -> None:
        df = clean_frame()
        bad_row = df.row(20, named=True)
        corrupted = _replace_row(df, 20, low=bad_row["high"] + 10.0)
        doctor, _ = make_doctor({"TEST": corrupted})

        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        ohlc_findings = [f for f in findings if f.check == "ohlc_consistency"]
        assert len(ohlc_findings) == 1
        assert ohlc_findings[0].severity == "error"
        assert ohlc_findings[0].count == 1
        assert not any(f.check == "invalid_price" for f in findings)
        assert not any(f.check == "extreme_outlier" for f in findings)


class TestMissingTradingDays:
    def test_dropped_bar_flagged_as_error(self) -> None:
        df = clean_frame()
        dropped_ts = df["ts"][20]
        corrupted = df.filter(pl.col("ts") != dropped_ts)
        doctor, _ = make_doctor({"TEST": corrupted})

        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        missing = [f for f in findings if f.check == "missing_trading_days"]
        assert len(missing) == 1
        assert missing[0].severity == "error"
        assert missing[0].count == 1
        assert str(dropped_ts.date()) in missing[0].message


class TestExtremeOutliers:
    def test_large_close_jump_on_last_bar_flagged_as_warn(self) -> None:
        df = clean_frame().sort("ts")
        last_idx = df.height - 1
        prev_close = df["close"][last_idx - 1]
        new_close = prev_close * 1.6  # +60% jump, well past the 40% threshold
        corrupted = _replace_row(
            df,
            last_idx,
            close=new_close,
            open=new_close,
            high=new_close + 1.0,
            low=new_close - 1.0,
        )
        doctor, _ = make_doctor({"TEST": corrupted})

        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        outliers = [f for f in findings if f.check == "extreme_outlier"]
        assert len(outliers) == 1
        assert outliers[0].severity == "warn"
        assert outliers[0].count == 1

    def test_first_bar_has_no_prior_close_and_is_never_flagged(self) -> None:
        df = clean_frame()
        # First bar's close is effectively arbitrary re: outlier detection --
        # nulling it out isolates invalid_price and confirms no crash / no
        # spurious outlier finding from a missing prev_close.
        corrupted = _replace_row(df, 0, close=None)
        doctor, _ = make_doctor({"TEST": corrupted})
        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        assert not any(f.check == "extreme_outlier" for f in findings)


class TestVolumeAnomalies:
    def test_few_zero_volume_bars_flagged_info(self) -> None:
        df = clean_frame()
        corrupted = _replace_row(df, 20, volume=0)
        doctor, _ = make_doctor({"TEST": corrupted})

        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        zero_vol = [f for f in findings if f.check == "zero_volume"]
        assert len(zero_vol) == 1
        assert zero_vol[0].severity == "info"
        assert zero_vol[0].count == 1

    def test_many_zero_volume_bars_flagged_warn(self) -> None:
        df = clean_frame()
        n_zero = max(int(df.height * 0.10), 4)  # >5% of bars
        for i in range(n_zero):
            df = _replace_row(df, i, volume=0)
        doctor, _ = make_doctor({"TEST": df})

        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        zero_vol = [f for f in findings if f.check == "zero_volume"]
        assert len(zero_vol) == 1
        assert zero_vol[0].severity == "warn"
        assert zero_vol[0].count == n_zero

    def test_volume_spike_flagged_info(self) -> None:
        df = clean_frame()
        corrupted = _replace_row(df, 30, volume=50_000_000)  # far above any 60-day median
        doctor, _ = make_doctor({"TEST": corrupted})

        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        spikes = [f for f in findings if f.check == "volume_spike"]
        assert len(spikes) == 1
        assert spikes[0].severity == "info"
        assert spikes[0].count == 1


class TestStaleness:
    def test_last_bar_far_before_today_flagged_warn(self) -> None:
        doctor, _ = make_doctor({"TEST": clean_frame()})
        far_future = END + timedelta(days=60)

        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=far_future)
        stale = [f for f in findings if f.check == "staleness"]
        assert len(stale) == 1
        assert stale[0].severity == "warn"

    def test_last_bar_recent_enough_not_flagged(self) -> None:
        doctor, _ = make_doctor({"TEST": clean_frame()})
        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END)
        assert not any(f.check == "staleness" for f in findings)

    def test_no_last_ts_never_flags_staleness(self) -> None:
        # store.last_ts() reporting None (e.g. no bars, or a fake with no
        # metadata) must not raise or fabricate a staleness finding.
        doctor, store = make_doctor({"TEST": clean_frame()})
        store.set_last_ts("TEST", None)
        findings = doctor.check_symbol("TEST", Timeframe.DAY, today=END + timedelta(days=60))
        assert not any(f.check == "staleness" for f in findings)


class TestRun:
    def test_run_checks_all_symbols_by_default(self) -> None:
        doctor, _ = make_doctor(
            {
                "AAA": clean_frame("AAA"),
                "BBB": _replace_row(clean_frame("BBB"), 5, close=None),
            }
        )
        report = doctor.run(Timeframe.DAY, today=END)
        assert isinstance(report, HealthReport)
        assert report.symbols_checked == 2
        assert len(report.errors) == 1
        assert report.errors[0].symbol == "BBB"

    def test_run_respects_explicit_symbol_subset(self) -> None:
        doctor, _ = make_doctor(
            {
                "AAA": clean_frame("AAA"),
                "BBB": _replace_row(clean_frame("BBB"), 5, close=None),
            }
        )
        report = doctor.run(Timeframe.DAY, symbols=["AAA"], today=END)
        assert report.symbols_checked == 1
        assert report.errors == []

    def test_clean_multi_symbol_run_has_no_errors_or_warnings(self) -> None:
        doctor, _ = make_doctor({"AAA": clean_frame("AAA"), "BBB": clean_frame("BBB")})
        report = doctor.run(Timeframe.DAY, today=END)
        assert report.findings == []
        assert report.errors == []
        assert report.warnings == []


class TestFindingAndReportModels:
    def test_finding_defaults(self) -> None:
        f = Finding(symbol="X", timeframe="day", check="c", severity="info", message="m")
        assert f.ts is None
        assert f.count == 1

    def test_render_empty_report(self) -> None:
        report = HealthReport(generated_at=datetime(2024, 1, 1), findings=[], symbols_checked=0)
        text = report.render()
        assert "No findings" in text

    def test_render_groups_by_symbol_and_shows_counts(self) -> None:
        findings = [
            Finding(
                symbol="AAA",
                timeframe="day",
                check="invalid_price",
                severity="error",
                message="bad price",
                count=3,
            ),
            Finding(
                symbol="BBB",
                timeframe="day",
                check="staleness",
                severity="warn",
                message="stale data",
            ),
        ]
        report = HealthReport(generated_at=datetime(2024, 1, 1), findings=findings, symbols_checked=2)
        text = report.render()
        assert "[AAA]" in text
        assert "[BBB]" in text
        assert "ERROR" in text
        assert "WARN" in text
        assert "(x3)" in text
        assert "errors: 1" in text
        assert "warnings: 1" in text


@pytest.mark.parametrize("index", [0])
def test_clean_frame_matches_calendar_trading_days(index: int) -> None:
    # sanity check on the fixture itself: guards against the "clean" baseline
    # silently drifting out of sync with NSECalendar and making every test
    # above spuriously report missing_trading_days.
    df = clean_frame()
    present = sorted(set(df.select(pl.col("ts").dt.date()).to_series().to_list()))
    assert present == CAL.trading_days(START, END)
