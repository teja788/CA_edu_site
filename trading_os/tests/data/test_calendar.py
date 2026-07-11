from __future__ import annotations

from datetime import date

import pytest

from tradingos.config.settings import Settings
from tradingos.core.errors import DataError
from tradingos.data.calendar import NSECalendar

# 2024-01-24 Wed, 2024-01-25 Thu: ordinary trading days.
# 2024-01-26 Fri: Republic Day (embedded holiday).
# 2024-01-27/28: Sat/Sun weekend.
# 2024-01-29 Mon: ordinary trading day.


class TestIsTradingDay:
    def test_ordinary_weekday_is_a_trading_day(self) -> None:
        cal = NSECalendar()
        assert cal.is_trading_day(date(2024, 1, 25)) is True

    def test_saturday_and_sunday_are_not_trading_days(self) -> None:
        cal = NSECalendar()
        assert cal.is_trading_day(date(2024, 1, 27)) is False
        assert cal.is_trading_day(date(2024, 1, 28)) is False

    def test_holiday_on_a_weekday_is_not_a_trading_day(self) -> None:
        cal = NSECalendar()
        assert cal.is_trading_day(date(2024, 1, 26)) is False

    def test_unknown_year_has_no_holidays(self) -> None:
        cal = NSECalendar()
        # far outside the embedded table -> no holiday entries, weekday logic still applies
        assert cal.is_trading_day(date(1999, 3, 3)) is True  # Wednesday
        assert cal.holidays(1999) == set()


class TestHolidays:
    def test_returns_a_defensive_copy(self) -> None:
        cal = NSECalendar()
        first = cal.holidays(2024)
        first.add(date(2024, 1, 25))  # mutate the returned set
        assert date(2024, 1, 25) not in cal.holidays(2024)

    def test_known_fixed_holidays_present(self) -> None:
        cal = NSECalendar()
        h = cal.holidays(2024)
        assert date(2024, 1, 26) in h  # Republic Day
        assert date(2024, 8, 15) in h  # Independence Day
        assert date(2024, 10, 2) in h  # Gandhi Jayanti
        assert date(2024, 12, 25) in h  # Christmas


class TestTradingDays:
    def test_excludes_weekends_and_holidays(self) -> None:
        cal = NSECalendar()
        days = cal.trading_days(date(2024, 1, 24), date(2024, 1, 29))
        assert days == [date(2024, 1, 24), date(2024, 1, 25), date(2024, 1, 29)]

    def test_single_day_range(self) -> None:
        cal = NSECalendar()
        assert cal.trading_days(date(2024, 1, 25), date(2024, 1, 25)) == [date(2024, 1, 25)]
        assert cal.trading_days(date(2024, 1, 27), date(2024, 1, 27)) == []

    def test_start_after_end_raises(self) -> None:
        cal = NSECalendar()
        with pytest.raises(DataError):
            cal.trading_days(date(2024, 1, 2), date(2024, 1, 1))


class TestNextPrevTradingDay:
    def test_next_trading_day_plain_weekday(self) -> None:
        cal = NSECalendar()
        assert cal.next_trading_day(date(2024, 1, 24)) == date(2024, 1, 25)

    def test_next_trading_day_skips_holiday_then_weekend(self) -> None:
        cal = NSECalendar()
        # Thu 25 (trading) -> Fri 26 (holiday) -> Sat/Sun (weekend) -> Mon 29
        assert cal.next_trading_day(date(2024, 1, 25)) == date(2024, 1, 29)

    def test_next_trading_day_from_the_holiday_itself(self) -> None:
        cal = NSECalendar()
        assert cal.next_trading_day(date(2024, 1, 26)) == date(2024, 1, 29)

    def test_prev_trading_day_skips_weekend_then_holiday(self) -> None:
        cal = NSECalendar()
        # Mon 29 -> Sun/Sat (weekend) -> Fri 26 (holiday) -> Thu 25
        assert cal.prev_trading_day(date(2024, 1, 29)) == date(2024, 1, 25)

    def test_next_and_prev_trading_day_are_never_a_weekend_or_holiday(self) -> None:
        cal = NSECalendar()
        for d in cal.trading_days(date(2024, 1, 1), date(2024, 2, 1)):
            assert cal.is_trading_day(cal.next_trading_day(d))
            assert cal.is_trading_day(cal.prev_trading_day(d))


class TestCsvOverride:
    def test_no_csv_file_falls_back_to_embedded_table_only(self, settings: Settings) -> None:
        cal = NSECalendar(settings)
        assert date(2024, 1, 26) in cal.holidays(2024)
        assert cal.is_trading_day(date(2024, 7, 15)) is True  # ordinary Monday, no override

    def test_csv_dates_are_added_as_holidays(self, settings: Settings) -> None:
        csv_path = settings.data_dir / "nse_holidays.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text("date,name\n2024-07-15,Special One-Off Holiday\n")

        cal = NSECalendar(settings)
        assert cal.is_trading_day(date(2024, 7, 15)) is False
        assert date(2024, 7, 15) in cal.holidays(2024)

    def test_csv_union_does_not_drop_embedded_holidays(self, settings: Settings) -> None:
        csv_path = settings.data_dir / "nse_holidays.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text("date,name\n2024-07-15,Special One-Off Holiday\n")

        cal = NSECalendar(settings)
        # embedded Republic Day still present alongside the CSV addition
        assert date(2024, 1, 26) in cal.holidays(2024)
        assert date(2024, 7, 15) in cal.holidays(2024)

    def test_csv_can_add_a_year_absent_from_the_embedded_table(self, settings: Settings) -> None:
        csv_path = settings.data_dir / "nse_holidays.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text("date,name\n2030-05-06,Some Future Holiday\n")

        cal = NSECalendar(settings)
        assert date(2030, 5, 6) in cal.holidays(2030)
        # 2030-05-06 is a Monday
        assert cal.is_trading_day(date(2030, 5, 6)) is False

    def test_csv_missing_date_column_raises_dataerror(self, settings: Settings) -> None:
        csv_path = settings.data_dir / "nse_holidays.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text("day,name\n2024-07-15,Bad Header\n")

        with pytest.raises(DataError):
            NSECalendar(settings)

    def test_csv_bad_date_format_raises_dataerror(self, settings: Settings) -> None:
        csv_path = settings.data_dir / "nse_holidays.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text("date,name\n15-07-2024,Bad Format\n")

        with pytest.raises(DataError):
            NSECalendar(settings)

    def test_csv_blank_lines_are_skipped(self, settings: Settings) -> None:
        csv_path = settings.data_dir / "nse_holidays.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_path.write_text("date,name\n2024-07-15,Holiday\n\n")

        cal = NSECalendar(settings)  # must not raise on the trailing blank row
        assert cal.is_trading_day(date(2024, 7, 15)) is False
