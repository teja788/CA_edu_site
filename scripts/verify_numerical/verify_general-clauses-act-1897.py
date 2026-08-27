"""Verifier for intermediate/corporate-and-other-laws/general-clauses-act-1897.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

The numericals in this chapter are all time arithmetic under the General
Clauses Act 1897, so three primitives do all the work:

  _from(d, n)          a period of n DAYS expressed as "n days FROM d".
                       Section 9 says the word "from" EXCLUDES the first day,
                       so day 1 is the day after d and the last day is
                       d + n days.  21 days from 5 Mar 2027 -> 26 Mar 2027.

  _next_open(d, shut)  section 10.  Where the act is to be done in a court or
                       office and the LAST day of the period is a day on which
                       that court or office is closed, the act is in due time
                       if done on the next day afterwards on which it is open.
                       A closure on an intermediate day is irrelevant.

  _add_months(d, n)    a period expressed in calendar MONTHS, "month" meaning a
                       month of the British (Gregorian) calendar under s. 3.
                       Used only to build distractors, never a correct answer.

Section 27 questions use _from as well: service is deemed effected at the time
the letter would be delivered in the ordinary course of post, which the stems
state as "the n-th day after posting" -> posting date + n days.

Which primitive applies is a legal question, not a coding one:

  s. 9   "within N days from <date>"                     -> _from
  s. 9   "from <date A> to <date B>", counting the days  -> (B - A).days,
         the first day excluded and the last day included
  s. 10  last day closed -> next day the office is open  -> _next_open
  s. 27  properly addressed, pre-paid, registered post;
         deemed served in the ordinary course of post    -> _from

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta


def _from(d: date, n: int) -> date:
    """The last day of a period of n days running "from" d (s. 9 — first day excluded)."""
    return d + timedelta(days=n)


def _add_months(d: date, n: int) -> date:
    """A period of n British-calendar months landing on the corresponding day."""
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _next_open(last_day: date, closed: set) -> date:
    """s. 10 — step forward from the last day to the next day the office is open."""
    d = last_day
    guard = 0
    while d in closed:
        d += timedelta(days=1)
        guard += 1
        if guard > 60:  # a runaway loop means the stem was mis-transcribed
            raise AssertionError("no open day within 60 days of %s" % last_day)
    return d


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


# ── s. 9 · "from" excludes the first day ─────────────────────────────────

def q_i2c13_020():
    # 21 days from 5 March 2027.  5 March is excluded, so day 1 is 6 March.
    start = date(2027, 3, 5)
    last = _from(start, 21)
    key = _pick(
        {
            "A": _from(start, 20),        # first day counted as day one
            "B": last,
            "C": _from(start, 22),        # an extra day at the end
            "D": _add_months(start, 1),   # "21 days" read as a calendar month
        },
        last,
    )
    return {"answer": key, "computed": last.isoformat()}


def q_i2c13_021():
    # 60 days from 15 January 2027.  February 2027 has 28 days.
    start = date(2027, 1, 15)
    last = _from(start, 60)
    key = _pick(
        {
            "A": last,
            "B": _from(start, 59),        # first day counted as day one
            "C": _from(start, 61),        # an extra day at the end
            "D": _from(start, 90),        # 90 days instead of 60
        },
        last,
    )
    return {"answer": key, "computed": last.isoformat()}


def q_i2c13_022():
    # "from 10 June 2026 to 9 September 2026": the first day is excluded by
    # "from" and the last day is included by "to", so the count is simply the
    # difference between the two dates in days.
    start, end = date(2026, 6, 10), date(2026, 9, 9)
    days = (end - start).days
    key = _pick(
        {
            "A": days - 1,   # the last day wrongly excluded as well
            "B": days + 1,   # the first day wrongly included as well
            "C": days,
            "D": days - 2,   # a day dropped at each end
        },
        days,
    )
    return {"answer": key, "computed": days}


# ── ss. 9 and 10 · a closed last day ─────────────────────────────────────

def q_i2c13_024():
    # 30 days from 2 February 2027 -> last day 4 March 2027 (February 2027 has
    # 28 days).  The office is closed 4-7 March and reopens on 8 March.
    start = date(2027, 2, 2)
    last = _from(start, 30)
    closed = {date(2027, 3, d) for d in (4, 5, 6, 7)}
    due = _next_open(last, closed)
    key = _pick(
        {
            "A": last,                       # s. 10 ignored
            "B": due,
            "C": last + timedelta(days=1),   # next day, not next OPEN day
            "D": _from(start, 29),           # first day counted as day one
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c13_025():
    # 15 days from 20 August 2026 -> last day 4 September 2026.  The office is
    # closed on 4, 5 and 6 September and reopens on 7 September.
    start = date(2026, 8, 20)
    last = _from(start, 15)
    closed = {date(2026, 9, d) for d in (4, 5, 6)}
    due = _next_open(last, closed)
    key = _pick(
        {
            "A": due,
            "B": last,                       # s. 10 ignored
            "C": last + timedelta(days=1),   # next day, still a closed day
            "D": _from(start, 14),           # first day counted as day one
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 27 · deemed service in the ordinary course of post ────────────────

def q_i2c13_028():
    # Registered post on 3 February 2027; ordinary course of post = the fourth
    # day after posting.
    posted = date(2027, 2, 3)
    served = _from(posted, 4)
    key = _pick(
        {
            "A": _from(posted, 3),   # the third day
            "B": served,
            "C": posted,             # the date of posting
            "D": _from(posted, 7),   # an invented seven-day rule
        },
        served,
    )
    return {"answer": key, "computed": served.isoformat()}


def q_i2c13_029():
    # Registered post on 27 February 2027; ordinary course of post = the fourth
    # day after posting.  2027 is NOT a leap year, so February has 28 days.
    posted = date(2027, 2, 27)
    served = _from(posted, 4)
    leap_error = served - timedelta(days=1)   # as if February had 29 days
    key = _pick(
        {
            "A": served,
            "B": leap_error,
            "C": posted,             # the date of posting
            "D": _from(posted, 5),   # the fifth day
        },
        served,
    )
    return {"answer": key, "computed": served.isoformat()}


# ── case sets ────────────────────────────────────────────────────────────

def cs_i2c13_01_b():
    # Registered post on 24 December 2026; ordinary course of post = the fifth
    # day after posting (s. 27).
    posted = date(2026, 12, 24)
    served = _from(posted, 5)
    key = _pick(
        {
            "A": posted,             # the date of posting
            "B": _from(posted, 4),   # the fourth day
            "C": served,
            "D": _from(posted, 7),   # an invented seven-day rule
        },
        served,
    )
    return {"answer": key, "computed": served.isoformat()}


def cs_i2c13_03_a():
    # 45 days from 18 November 2026 (s. 9 — 18 November excluded).
    start = date(2026, 11, 18)
    last = _from(start, 45)
    key = _pick(
        {
            "A": _from(start, 44),        # first day counted as day one
            "B": last,
            "C": _from(start, 46),        # an extra day at the end
            "D": _add_months(start, 1),   # read as one calendar month
        },
        last,
    )
    return {"answer": key, "computed": last.isoformat()}


def cs_i2c13_03_b():
    # The same period, with s. 10 applied: the last day (2 January 2027) and the
    # following day are days on which the Commissioner's office is closed; it
    # reopens on 4 January 2027.  The 25 December closure is an intermediate day
    # and is deliberately NOT in the set that matters.
    start = date(2026, 11, 18)
    last = _from(start, 45)
    closed = {date(2027, 1, 2), date(2027, 1, 3)}
    due = _next_open(last, closed)
    key = _pick(
        {
            "A": last,                       # s. 10 ignored
            "B": last + timedelta(days=1),   # next day, still a closed day
            "C": due,
            "D": last - timedelta(days=1),   # a s. 9 miscount
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}
