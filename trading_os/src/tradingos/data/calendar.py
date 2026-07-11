"""NSE (National Stock Exchange of India) trading-day calendar.

``_NSE_HOLIDAYS`` below is a **best-effort, embedded** table of NSE trading
holidays for 2015-2026. Fixed-date holidays (Republic Day, Ambedkar Jayanti,
Maharashtra Day, Independence Day, Gandhi Jayanti, Christmas) are reliable.
Everything else is tied to the Hindu lunisolar and Islamic calendars
(Mahashivratri, Holi, Ram Navami, Mahavir Jayanti, Eid-ul-Fitr, Bakri Id,
Ganesh Chaturthi, Muharram, Dussehra, Diwali Laxmi Pujan/Balipratipada,
Gurunanak Jayanti) and, in practice, the *exact* set NSE observes each year is
an exchange announcement that can differ from any formula — dates here are
compiled from memory of typical published NSE holiday calendars and are
approximations, especially for 2015-2018 (further back, less certain) and
2026 (not yet finalized at authoring time). **Do not rely on this table alone
for anything accuracy-critical.** Drop the official NSE holiday list
(https://www.nseindia.com, "Market Holidays") as a CSV with columns
``date,name`` (ISO dates) at ``<settings.data_dir>/nse_holidays.csv`` --
:class:`NSECalendar` unions it with the embedded table, which both fills gaps
and lets you override/extend per-year without touching this file.

Muhurat trading (the short special evening session NSE runs on the Diwali
Laxmi Pujan holiday) is intentionally **not** modeled -- that date is treated
as an ordinary holiday (no regular session), consistent with excluding it
from ``is_trading_day``/``trading_days``.
"""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

from tradingos.config.settings import Settings
from tradingos.core.errors import DataError
from tradingos.core.logging import get_logger

logger = get_logger(__name__)

# NOTE: dates are best-effort; see module docstring. Comments name the
# holiday for auditability. Fixed-date holidays are included every year even
# when they land on a weekend -- harmless, since is_trading_day already
# excludes weekends first.
_NSE_HOLIDAYS: dict[int, set[date]] = {
    2015: {
        date(2015, 1, 26),  # Republic Day
        date(2015, 2, 17),  # Mahashivratri
        date(2015, 3, 6),  # Holi
        date(2015, 4, 2),  # Mahavir Jayanti
        date(2015, 4, 3),  # Good Friday
        date(2015, 4, 14),  # Ambedkar Jayanti
        date(2015, 5, 1),  # Maharashtra Day
        date(2015, 7, 18),  # Eid-ul-Fitr (approx.)
        date(2015, 9, 17),  # Ganesh Chaturthi
        date(2015, 9, 25),  # Bakri Id
        date(2015, 10, 2),  # Gandhi Jayanti
        date(2015, 10, 22),  # Dussehra (approx.)
        date(2015, 11, 11),  # Diwali Laxmi Pujan
        date(2015, 11, 12),  # Diwali Balipratipada (approx.)
        date(2015, 11, 25),  # Gurunanak Jayanti
        date(2015, 12, 25),  # Christmas
    },
    2016: {
        date(2016, 1, 26),  # Republic Day
        date(2016, 3, 7),  # Mahashivratri (approx.)
        date(2016, 3, 24),  # Holi
        date(2016, 3, 25),  # Good Friday
        date(2016, 4, 14),  # Ambedkar Jayanti
        date(2016, 4, 15),  # Ram Navami (approx.)
        date(2016, 5, 1),  # Maharashtra Day
        date(2016, 7, 6),  # Eid-ul-Fitr (approx.)
        date(2016, 8, 15),  # Independence Day
        date(2016, 9, 5),  # Ganesh Chaturthi
        date(2016, 9, 13),  # Bakri Id (approx.)
        date(2016, 10, 2),  # Gandhi Jayanti
        date(2016, 10, 11),  # Dussehra (approx.)
        date(2016, 10, 30),  # Diwali Laxmi Pujan
        date(2016, 10, 31),  # Diwali Balipratipada (approx.)
        date(2016, 11, 14),  # Gurunanak Jayanti
        date(2016, 12, 25),  # Christmas
    },
    2017: {
        date(2017, 1, 26),  # Republic Day
        date(2017, 2, 24),  # Mahashivratri (approx.)
        date(2017, 3, 13),  # Holi
        date(2017, 4, 4),  # Ram Navami (approx.)
        date(2017, 4, 9),  # Mahavir Jayanti (approx.)
        date(2017, 4, 14),  # Ambedkar Jayanti / Good Friday (approx., overlap year)
        date(2017, 5, 1),  # Maharashtra Day
        date(2017, 6, 26),  # Eid-ul-Fitr (approx.)
        date(2017, 8, 15),  # Independence Day
        date(2017, 8, 25),  # Ganesh Chaturthi (approx.)
        date(2017, 9, 1),  # Bakri Id (approx.)
        date(2017, 9, 30),  # Dussehra (approx.)
        date(2017, 10, 2),  # Gandhi Jayanti
        date(2017, 10, 19),  # Diwali Laxmi Pujan
        date(2017, 10, 20),  # Diwali Balipratipada
        date(2017, 11, 4),  # Gurunanak Jayanti
        date(2017, 12, 25),  # Christmas
    },
    2018: {
        date(2018, 1, 26),  # Republic Day
        date(2018, 2, 13),  # Mahashivratri (approx.)
        date(2018, 3, 2),  # Holi
        date(2018, 3, 29),  # Mahavir Jayanti (approx.)
        date(2018, 3, 30),  # Good Friday
        date(2018, 4, 14),  # Ambedkar Jayanti
        date(2018, 5, 1),  # Maharashtra Day
        date(2018, 6, 15),  # Eid-ul-Fitr (approx.)
        date(2018, 8, 15),  # Independence Day
        date(2018, 8, 22),  # Bakri Id (approx.)
        date(2018, 9, 13),  # Ganesh Chaturthi (approx.)
        date(2018, 9, 20),  # Muharram (approx.)
        date(2018, 10, 2),  # Gandhi Jayanti
        date(2018, 10, 18),  # Dussehra (approx.)
        date(2018, 11, 7),  # Diwali Laxmi Pujan
        date(2018, 11, 8),  # Diwali Balipratipada (approx.)
        date(2018, 11, 23),  # Gurunanak Jayanti
        date(2018, 12, 25),  # Christmas
    },
    2019: {
        date(2019, 1, 26),  # Republic Day
        date(2019, 3, 4),  # Mahashivratri (approx.)
        date(2019, 3, 21),  # Holi
        date(2019, 4, 17),  # Ram Navami (approx.)
        date(2019, 4, 19),  # Good Friday
        date(2019, 4, 14),  # Ambedkar Jayanti / Mahavir Jayanti (approx., overlap year)
        date(2019, 5, 1),  # Maharashtra Day
        date(2019, 6, 5),  # Eid-ul-Fitr (approx.)
        date(2019, 8, 12),  # Bakri Id (approx.)
        date(2019, 8, 15),  # Independence Day
        date(2019, 9, 2),  # Ganesh Chaturthi (approx.)
        date(2019, 9, 10),  # Muharram (approx.)
        date(2019, 10, 2),  # Gandhi Jayanti / Dussehra (combined)
        date(2019, 10, 8),  # Dussehra (approx., alt.)
        date(2019, 10, 27),  # Diwali Laxmi Pujan
        date(2019, 10, 28),  # Diwali Balipratipada (approx.)
        date(2019, 11, 12),  # Gurunanak Jayanti
        date(2019, 12, 25),  # Christmas
    },
    2020: {
        date(2020, 1, 26),  # Republic Day (Sun)
        date(2020, 2, 21),  # Mahashivratri (approx.)
        date(2020, 3, 10),  # Holi
        date(2020, 4, 2),  # Ram Navami (approx.)
        date(2020, 4, 6),  # Mahavir Jayanti (approx.)
        date(2020, 4, 10),  # Good Friday
        date(2020, 4, 14),  # Ambedkar Jayanti
        date(2020, 5, 1),  # Maharashtra Day
        date(2020, 5, 25),  # Eid-ul-Fitr (approx.)
        date(2020, 8, 1),  # Bakri Id (approx.)
        date(2020, 8, 15),  # Independence Day
        date(2020, 10, 2),  # Gandhi Jayanti
        date(2020, 11, 14),  # Diwali Laxmi Pujan
        date(2020, 11, 16),  # Diwali Balipratipada (approx.)
        date(2020, 11, 30),  # Gurunanak Jayanti
        date(2020, 12, 25),  # Christmas
    },
    2021: {
        date(2021, 1, 26),  # Republic Day
        date(2021, 3, 11),  # Mahashivratri (approx.)
        date(2021, 3, 29),  # Holi
        date(2021, 4, 2),  # Good Friday
        date(2021, 4, 14),  # Ambedkar Jayanti
        date(2021, 4, 21),  # Ram Navami (approx.)
        date(2021, 5, 1),  # Maharashtra Day
        date(2021, 5, 14),  # Eid-ul-Fitr (approx.)
        date(2021, 7, 21),  # Bakri Id (approx.)
        date(2021, 8, 15),  # Independence Day
        date(2021, 9, 10),  # Ganesh Chaturthi (approx.)
        date(2021, 10, 15),  # Dussehra (approx.)
        date(2021, 11, 4),  # Diwali Laxmi Pujan
        date(2021, 11, 5),  # Diwali Balipratipada (approx.)
        date(2021, 11, 19),  # Gurunanak Jayanti
        date(2021, 12, 25),  # Christmas
    },
    2022: {
        date(2022, 1, 26),  # Republic Day
        date(2022, 3, 1),  # Mahashivratri (approx.)
        date(2022, 3, 18),  # Holi
        date(2022, 4, 14),  # Ambedkar Jayanti / Mahavir Jayanti (overlap year, approx.)
        date(2022, 4, 15),  # Good Friday
        date(2022, 5, 1),  # Maharashtra Day
        date(2022, 5, 3),  # Eid-ul-Fitr (approx.)
        date(2022, 7, 10),  # Bakri Id (approx.)
        date(2022, 8, 15),  # Independence Day
        date(2022, 8, 31),  # Ganesh Chaturthi (approx.)
        date(2022, 10, 5),  # Dussehra (approx.)
        date(2022, 10, 2),  # Gandhi Jayanti
        date(2022, 10, 24),  # Diwali Laxmi Pujan
        date(2022, 10, 26),  # Diwali Balipratipada
        date(2022, 11, 8),  # Gurunanak Jayanti
        date(2022, 12, 25),  # Christmas
    },
    2023: {
        date(2023, 1, 26),  # Republic Day
        date(2023, 3, 7),  # Holi
        date(2023, 3, 30),  # Ram Navami
        date(2023, 4, 4),  # Mahavir Jayanti
        date(2023, 4, 7),  # Good Friday
        date(2023, 4, 14),  # Ambedkar Jayanti
        date(2023, 5, 1),  # Maharashtra Day
        date(2023, 6, 29),  # Bakri Id
        date(2023, 8, 15),  # Independence Day
        date(2023, 9, 19),  # Ganesh Chaturthi
        date(2023, 10, 2),  # Gandhi Jayanti
        date(2023, 10, 24),  # Dussehra
        date(2023, 11, 14),  # Diwali Laxmi Pujan
        date(2023, 11, 27),  # Gurunanak Jayanti
        date(2023, 12, 25),  # Christmas
    },
    2024: {
        date(2024, 1, 22),  # special one-time holiday (Ram Mandir consecration)
        date(2024, 1, 26),  # Republic Day
        date(2024, 3, 8),  # Mahashivratri
        date(2024, 3, 25),  # Holi
        date(2024, 3, 29),  # Good Friday
        date(2024, 4, 11),  # Eid-ul-Fitr
        date(2024, 4, 14),  # Ambedkar Jayanti
        date(2024, 4, 17),  # Ram Navami
        date(2024, 5, 1),  # Maharashtra Day
        date(2024, 5, 20),  # Lok Sabha general election (Mumbai polling)
        date(2024, 6, 17),  # Bakri Id
        date(2024, 7, 17),  # Muharram
        date(2024, 8, 15),  # Independence Day
        date(2024, 10, 2),  # Gandhi Jayanti / Dussehra (combined)
        date(2024, 11, 1),  # Diwali Laxmi Pujan
        date(2024, 11, 15),  # Gurunanak Jayanti
        date(2024, 11, 20),  # Maharashtra state assembly election
        date(2024, 12, 25),  # Christmas
    },
    2025: {
        date(2025, 1, 26),  # Republic Day
        date(2025, 2, 26),  # Mahashivratri
        date(2025, 3, 14),  # Holi
        date(2025, 3, 31),  # Eid-ul-Fitr (approx.)
        date(2025, 4, 6),  # Ram Navami (approx.)
        date(2025, 4, 10),  # Mahavir Jayanti (approx.)
        date(2025, 4, 14),  # Ambedkar Jayanti
        date(2025, 4, 18),  # Good Friday
        date(2025, 5, 1),  # Maharashtra Day
        date(2025, 6, 7),  # Bakri Id (approx.)
        date(2025, 8, 15),  # Independence Day
        date(2025, 8, 27),  # Ganesh Chaturthi (approx.)
        date(2025, 10, 2),  # Gandhi Jayanti / Dussehra (combined, approx.)
        date(2025, 10, 21),  # Diwali Laxmi Pujan (approx.)
        date(2025, 10, 22),  # Diwali Balipratipada (approx.)
        date(2025, 11, 5),  # Gurunanak Jayanti (approx.)
        date(2025, 12, 25),  # Christmas
    },
    2026: {
        # 2026 is the least certain year in this table -- not yet finalized
        # by the exchange at authoring time; all movable dates are rough
        # forward projections. Supply the CSV override once NSE publishes
        # the official 2026 list.
        date(2026, 1, 26),  # Republic Day
        date(2026, 2, 15),  # Mahashivratri (est.)
        date(2026, 3, 4),  # Holi (est.)
        date(2026, 3, 20),  # Eid-ul-Fitr (est.)
        date(2026, 3, 26),  # Ram Navami (est.)
        date(2026, 3, 31),  # Mahavir Jayanti (est.)
        date(2026, 4, 3),  # Good Friday
        date(2026, 4, 14),  # Ambedkar Jayanti
        date(2026, 5, 1),  # Maharashtra Day
        date(2026, 5, 27),  # Bakri Id (est.)
        date(2026, 8, 15),  # Independence Day
        date(2026, 9, 14),  # Ganesh Chaturthi (est.)
        date(2026, 10, 2),  # Gandhi Jayanti
        date(2026, 10, 20),  # Dussehra (est.)
        date(2026, 11, 8),  # Diwali Laxmi Pujan (est.)
        date(2026, 11, 9),  # Diwali Balipratipada (est.)
        date(2026, 11, 24),  # Gurunanak Jayanti (est.)
        date(2026, 12, 25),  # Christmas
    },
}


class NSECalendar:
    """NSE trading-day calendar: Mon-Fri minus holidays.

    Holiday source = the embedded ``_NSE_HOLIDAYS`` best-effort table, unioned
    with an optional CSV override/extension at
    ``settings.data_dir / "nse_holidays.csv"`` (columns ``date,name``, ISO
    dates) when a ``settings`` object is supplied. The CSV only ever *adds*
    dates -- it cannot remove an embedded holiday.

    Muhurat trading (the special Diwali evening session) is intentionally
    ignored: that date is treated as a normal holiday, not a trading day.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._holidays: dict[int, set[date]] = {
            year: set(days) for year, days in _NSE_HOLIDAYS.items()
        }
        self._warned_years: set[int] = set()
        if settings is not None:
            csv_path = Path(settings.data_dir) / "nse_holidays.csv"
            self._load_csv_override(csv_path)

    def _load_csv_override(self, path: Path) -> None:
        if not path.exists():
            return
        added = 0
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None or "date" not in reader.fieldnames:
                raise DataError(f"{path}: expected a 'date' column (got {reader.fieldnames})")
            for row in reader:
                raw = (row.get("date") or "").strip()
                if not raw:
                    continue
                try:
                    d = date.fromisoformat(raw)
                except ValueError as exc:
                    raise DataError(f"{path}: invalid ISO date {raw!r} in row {row!r}") from exc
                self._holidays.setdefault(d.year, set()).add(d)
                added += 1
        logger.info("loaded %d holiday override date(s) from %s", added, path)

    def holidays(self, year: int) -> set[date]:
        """Holiday dates for `year` (embedded table unioned with any CSV override)."""
        return set(self._holidays.get(year, set()))

    def covers(self, year: int) -> bool:
        """True when this calendar has ANY holiday knowledge for `year`
        (embedded table or CSV override). Outside covered years the calendar
        degrades to weekday-only logic and its answers are unreliable for
        anything accuracy-critical (see the loud warning in is_trading_day)."""
        return year in self._holidays

    def is_trading_day(self, d: date) -> bool:
        """True for Mon-Fri dates not present in the holiday set.

        Muhurat trading sessions are not modeled -- Diwali/Laxmi Pujan is
        always a non-trading day here even though NSE runs a short evening
        session on it.

        For years OUTSIDE the calendar's holiday coverage this degrades to
        weekday-only logic (every weekday "trades"); that fallback is loud --
        a WARNING is logged once per uncovered year per instance -- because
        it silently misclassifies real holidays as trading days.
        """
        if d.weekday() >= 5:
            return False
        year_holidays = self._holidays.get(d.year)
        if year_holidays is None:
            if d.year not in self._warned_years:
                self._warned_years.add(d.year)
                covered = sorted(self._holidays)
                logger.warning(
                    "NSECalendar has no holiday data for %d (coverage: %d-%d); "
                    "falling back to weekday-only logic -- trading-day answers and "
                    "missing-day checks for this year are unreliable. Supply "
                    "<data_dir>/nse_holidays.csv to extend coverage.",
                    d.year,
                    covered[0],
                    covered[-1],
                )
            return True
        return d not in year_holidays

    def trading_days(self, start: date, end: date) -> list[date]:
        """Sorted list of trading days in `[start, end]` inclusive."""
        if start > end:
            raise DataError(f"start {start} after end {end}")
        days: list[date] = []
        cur = start
        while cur <= end:
            if self.is_trading_day(cur):
                days.append(cur)
            cur += timedelta(days=1)
        return days

    def next_trading_day(self, d: date) -> date:
        """The first trading day strictly after `d` (even if `d` itself is one)."""
        cur = d + timedelta(days=1)
        while not self.is_trading_day(cur):
            cur += timedelta(days=1)
        return cur

    def prev_trading_day(self, d: date) -> date:
        """The first trading day strictly before `d` (even if `d` itself is one)."""
        cur = d - timedelta(days=1)
        while not self.is_trading_day(cur):
            cur -= timedelta(days=1)
        return cur
