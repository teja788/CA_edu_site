"""Verifier for intermediate/corporate-and-other-laws/companies-incorporated-outside-india.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

Chapter XXII produces two kinds of numerical: filing clocks and the s. 379(2)
shareholding aggregation. Three primitives do all the work:

  _add_days(d, n)     a period expressed in DAYS is counted from the trigger
                      date, exclusive of the trigger day (day 1 is the next
                      day). 30 days from 9 Mar -> 8 Apr.
  _add_months(d, n)   a period expressed in MONTHS lands on the same day of
                      the later month (6 months from 31 Mar -> 30 Sep), with a
                      clamp for short months.
  _pct(part, whole)   an EXACT percentage, computed with fractions.Fraction so
                      that 47.5% and 125/3% compare without float error.

Which primitive applies is a legal question, not a coding one:

  s. 380(2)   documents delivered to the Registrar within 30 DAYS of the
              ESTABLISHMENT of the place of business in India   -> _add_days
  s. 380(3)   return of an alteration in those particulars within
              30 DAYS of the ALTERATION                         -> _add_days
  s. 381 +    financial statements filed within SIX MONTHS of
  Rules       the CLOSE of the financial year (the Registrar may
              extend by up to three further months)             -> _add_months
  s. 384(2)   annual return within 60 DAYS from the LAST DAY of
  + Rules     the financial year                                -> _add_days
  s. 379(2)   NOT LESS THAN 50% of the PAID-UP SHARE CAPITAL —
              equity or preference or partly both — held by
              citizens of India and/or bodies corporate
              incorporated in India, singly or in the aggregate -> _pct

Two traps are deliberately encoded as distractors and are recomputed here so
that a wrong bank key cannot slip past: reading a DAYS period as calendar
months (30 days from 9 Mar is 8 Apr, not 9 Apr; 60 days from 31 Mar is
30 May, not 31 May), and running the s. 379(2) numerator over the equity base
alone instead of over total paid-up share capital.

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from fractions import Fraction


def _add_days(d: date, n: int) -> date:
    """A period of n days counted from (and excluding) the trigger date."""
    return d + timedelta(days=n)


def _add_months(d: date, n: int) -> date:
    """A period of n calendar months landing on the same day of the month."""
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _pct(part: int, whole: int) -> Fraction:
    """An exact percentage."""
    return Fraction(part, whole) * 100


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


# ── s. 379(2) · the fifty per cent aggregation ───────────────────────────

def q_i2c11_006():
    # Equity 40,00,000 + preference 10,00,000 = 50,00,000 paid-up capital.
    # Qualifying: Indian citizens 12,00,000 (equity); Indian-incorporated
    # company 9,00,000 (equity) + 4,00,000 (preference).
    equity, preference = 40_00_000, 10_00_000
    citizens_equity = 12_00_000
    indian_co_equity, indian_co_pref = 9_00_000, 4_00_000

    total = equity + preference
    qualifying = citizens_equity + indian_co_equity + indian_co_pref
    share = _pct(qualifying, total)
    key = _pick(
        {
            "A": _pct(citizens_equity, total),                     # citizens only
            "B": _pct(citizens_equity + indian_co_equity, total),   # preference dropped
            "C": share,
            # the right numerator over the EQUITY base only
            "D": _pct(citizens_equity + indian_co_equity, equity),
        },
        share,
    )
    return {"answer": key, "computed": f"{float(share)}%"}


def q_i2c11_007():
    # 80,00,000 paid-up. Citizens of India 18,00,000; companies incorporated
    # in India 20,00,000. Non-citizen persons of Indian origin (6,00,000) do
    # NOT qualify; nor does the UK parent (36,00,000).
    total = 80_00_000
    citizens, indian_cos, non_citizen_pio = 18_00_000, 20_00_000, 6_00_000

    qualifying = citizens + indian_cos
    share = _pct(qualifying, total)
    key = _pick(
        {
            "A": _pct(citizens, total),                              # citizens only
            "B": share,
            "C": _pct(qualifying + non_citizen_pio, total),          # PIOs wrongly added
            "D": Fraction(105, 2),                                   # 52.5% — no basis
        },
        share,
    )
    return {"answer": key, "computed": f"{float(share)}%"}


def cs_i2c11_01_c():
    # Equity 52,00,000 + preference 8,00,000 = 60,00,000 paid-up capital.
    # Qualifying: citizens 14,00,000 (equity); Indian company 22,00,000
    # (equity) + 3,00,000 (preference).
    equity, preference = 52_00_000, 8_00_000
    citizens_equity = 14_00_000
    indian_co_equity, indian_co_pref = 22_00_000, 3_00_000

    total = equity + preference
    qualifying = citizens_equity + indian_co_equity + indian_co_pref
    share = _pct(qualifying, total)
    key = _pick(
        {
            # equity of the qualifying holders only — preference dropped
            "A": _pct(citizens_equity + indian_co_equity, total),
            "B": _pct(citizens_equity, total),                       # citizens only
            "C": _pct(indian_co_equity + indian_co_pref, total),     # the company only
            "D": share,
        },
        share,
    )
    return {"answer": key, "computed": f"{float(share)}%"}


# ── s. 380(2) · documents on establishing a place of business (FC-1) ─────

def q_i2c11_013():
    # place of business established 9 March 2026; 30 DAYS under s. 380(2).
    established = date(2026, 3, 9)
    due = _add_days(established, 30)
    key = _pick(
        {
            "A": _add_days(established, 15),      # a period nowhere in Ch XXII
            "B": due,
            "C": _add_months(established, 1),     # 30 days read as one month
            "D": _add_days(established, 60),      # the annual-return period
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c11_014():
    # place of business established 20 January 2027; 30 DAYS under s. 380(2).
    established = date(2027, 1, 20)
    due = _add_days(established, 30)
    key = _pick(
        {
            "A": due,
            "B": _add_months(established, 1),     # one calendar month
            "C": _add_days(established, 15),      # fifteen days
            "D": _add_days(established, 60),      # the annual-return period
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c11_01_a():
    # branch office established 14 May 2026; 30 DAYS under s. 380(2).
    established = date(2026, 5, 14)
    due = _add_days(established, 30)
    key = _pick(
        {
            "A": _add_days(established, 15),      # fifteen days
            "B": _add_months(established, 1),     # one calendar month
            "C": due,
            "D": _add_days(established, 60),      # the annual-return period
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 380(3) · return of an alteration (FC-2) ───────────────────────────

def q_i2c11_018():
    # authorised person replaced 6 November 2026; 30 DAYS from the ALTERATION.
    altered = date(2026, 11, 6)
    due = _add_days(altered, 30)
    key = _pick(
        {
            "A": _add_days(altered, 15),          # fifteen days
            "B": _add_days(altered, 60),          # the annual-return period
            "C": _add_months(altered, 6),         # the accounts window
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 381 + Rules · financial statements (FC-3), six MONTHS ─────────────

def q_i2c11_021():
    # financial year closed 31 March 2027; SIX MONTHS, extension ignored.
    year_end = date(2027, 3, 31)
    due = _add_months(year_end, 6)
    key = _pick(
        {
            "A": _add_days(year_end, 60),         # the annual-return period
            "B": due,
            "C": _add_days(year_end, 180),        # six months counted as 180 days
            "D": _add_months(year_end, 9),        # six months PLUS the extension
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 384(2) + Rules · annual return (FC-4), sixty DAYS ────────────────

def q_i2c11_024():
    # financial year ends 31 March 2027; 60 DAYS from the LAST DAY of the year.
    year_end = date(2027, 3, 31)
    due = _add_days(year_end, 60)
    key = _pick(
        {
            "A": _add_days(year_end, 30),         # the s. 380 period
            "B": _add_months(year_end, 2),        # 60 days read as two months
            "C": due,
            "D": _add_months(year_end, 6),        # the accounts window
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c11_025():
    # financial year ends 31 December 2026; 60 DAYS. 2027 is not a leap year,
    # so the day-count (1 Mar) and the month-count (28 Feb) diverge.
    year_end = date(2026, 12, 31)
    due = _add_days(year_end, 60)
    key = _pick(
        {
            "A": _add_days(year_end, 30),         # thirty days
            "B": due,
            "C": _add_months(year_end, 2),        # two calendar months
            "D": _add_months(year_end, 6),        # the accounts window
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c11_03_a():
    # financial year ends 30 June 2026; 60 DAYS from the last day of the year.
    year_end = date(2026, 6, 30)
    due = _add_days(year_end, 60)
    key = _pick(
        {
            "A": due,
            "B": _add_months(year_end, 2),        # two calendar months
            "C": _add_days(year_end, 30),         # the s. 380 period
            "D": _add_months(year_end, 6),        # the accounts window
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}
