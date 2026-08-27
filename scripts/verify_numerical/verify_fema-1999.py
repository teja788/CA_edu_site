"""Verifier for intermediate/corporate-and-other-laws/fema-1999.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

The numericals in this chapter fall into three families, and each family has
one primitive:

  _span_days(a, b)    residence day count, INCLUSIVE of both the first and the
                      last day of the spell (1 Jun to 30 Nov -> 183, not 182).
                      s. 2(v) speaks of days "residing in India", so a day
                      present at either end is a day counted.

  _add_days(d, n)     a period expressed in DAYS runs from the trigger event
                      exclusive of the trigger day (day 1 is the next day).
                      90 days from 10 Jun 2026 -> 8 Sep 2026.

  Fraction arithmetic for every money and USD amount, so that no binary
  floating-point residue can ever decide which option matches.

Which primitive applies is a legal question, not a coding one:

  s. 2(v)      more than 182 days in the PRECEDING financial year; the spell
               is counted inclusively                             -> _span_days
  LRS          USD 2,50,000 per financial year per resident
               individual, current AND capital drawals aggregated -> Fraction
  s. 13(1)     up to THRICE the sum involved where quantifiable;
               else up to Rs 2,00,000; plus up to Rs 5,000 for
               every day AFTER THE FIRST DAY of a continuing
               contravention                                      -> Fraction
  s. 14(1)     90 DAYS from the date of service of the notice for
               payment of the penalty                             -> _add_days
  s. 15(1)     180 DAYS from the date of RECEIPT OF THE
               APPLICATION for compounding                        -> _add_days
  s. 17 / 19   45 DAYS from the date the copy of the order is
               RECEIVED by the aggrieved person                   -> _add_days
  s. 35        60 DAYS from the date the Tribunal's order is
               COMMUNICATED                                       -> _add_days

The month-based distractors are produced by _add_months so that "six calendar
months" and "180 days" can be shown to be different dates rather than asserted
to be.

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
The LRS ceiling of USD 2,50,000 is circular-level and amendment-sensitive; if
it moves, q-i2c15-022, q-i2c15-023 and cs-i2c15-01-b must be reworked here and
in the bank together.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from fractions import Fraction

LRS_CEILING = Fraction(250000)          # USD, per financial year, per resident individual
PENALTY_MULTIPLE = Fraction(3)          # s. 13(1) — thrice the sum involved
PENALTY_UNQUANTIFIABLE = Fraction(200000)   # s. 13(1) — Rs 2,00,000
PENALTY_PER_DAY = Fraction(5000)        # s. 13(1) — Rs 5,000 per day after the first day


def _span_days(start: date, end: date) -> int:
    """Days of residence in a spell, counting both the first and the last day."""
    return (end - start).days + 1


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


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


# ── s. 2(v) · residence day counts for the preceding financial year ──────

def q_i2c15_007():
    # FY 2026-27 -> preceding FY is 2025-26. Two spells, each inclusive.
    spell_1 = _span_days(date(2025, 4, 1), date(2025, 7, 15))    # 106
    spell_2 = _span_days(date(2026, 1, 1), date(2026, 3, 31))    # 90
    total = spell_1 + spell_2
    key = _pick(
        {
            "A": spell_1,                                   # first spell only
            "B": total - 6,                                 # a spell counted exclusively
            "C": total,
            "D": total + 90,                                # April-July read as four full months
        },
        total,
    )
    # the legal conclusion the option text also asserts
    assert total > 182, "stem is meant to produce a person resident in India"
    return {"answer": key, "computed": total}


def q_i2c15_008():
    # single spell, 1 June 2025 to 30 November 2025, both days inclusive.
    total = _span_days(date(2025, 6, 1), date(2025, 11, 30))     # 183
    key = _pick(
        {
            "A": 182,           # the threshold itself, mis-taken as the count
            "B": total,
            "C": 180,           # six months read as six 30-day months
            "D": 184,           # a day double-counted at one end
        },
        total,
    )
    assert total > 182, "she is meant to clear the gate by exactly one day"
    return {"answer": key, "computed": total}


# ── Schedule III / LRS · headroom and excess ─────────────────────────────

def q_i2c15_022():
    # tuition USD 90,000 + gift USD 35,000 already drawn in the same FY.
    tuition, gift = Fraction(90000), Fraction(35000)
    headroom = LRS_CEILING - (tuition + gift)
    key = _pick(
        {
            "A": LRS_CEILING,                   # earlier drawals ignored
            "B": headroom,
            "C": LRS_CEILING - tuition,         # only the tuition counted
            "D": LRS_CEILING - gift,            # only the gift counted
        },
        headroom,
    )
    return {"answer": key, "computed": f"USD {int(headroom):,}"}


def q_i2c15_023():
    # medical USD 1,20,000 + private visits USD 48,000 + donation USD 25,000.
    medical, visits, donation = Fraction(120000), Fraction(48000), Fraction(25000)
    headroom = LRS_CEILING - (medical + visits + donation)
    key = _pick(
        {
            "A": LRS_CEILING - (visits + donation),   # medical wrongly left out
            "B": LRS_CEILING - (medical + visits),    # donation wrongly left out
            "C": headroom,
            "D": LRS_CEILING - medical,               # only the medical leg counted
        },
        headroom,
    )
    return {"answer": key, "computed": f"USD {int(headroom):,}"}


def cs_i2c15_01_b():
    # Nandita's own drawals: tuition USD 62,000 + gift USD 2,05,000.
    # Rohit's USD 18,000 runs against HIS separate ceiling and is excluded.
    tuition, gift, spouse = Fraction(62000), Fraction(205000), Fraction(18000)
    drawn = tuition + gift
    excess = max(Fraction(0), drawn - LRS_CEILING)
    key = _pick(
        {
            "A": Fraction(0),                                       # said to be within the ceiling
            "B": excess,
            "C": (drawn + spouse) - LRS_CEILING,                    # spouse's drawal wrongly added
            "D": LRS_CEILING - tuition,                             # headroom mistaken for excess
        },
        excess,
    )
    return {"answer": key, "computed": f"USD {int(excess):,}"}


# ── s. 13(1) · penalty computations ──────────────────────────────────────

def q_i2c15_032():
    # quantifiable sum of Rs 42,00,000; contravention complete on one day.
    sum_involved = Fraction(4200000)
    maximum = PENALTY_MULTIPLE * sum_involved
    key = _pick(
        {
            "A": sum_involved,                      # the sum itself
            "B": Fraction(2) * sum_involved,        # twice, not thrice
            "C": PENALTY_UNQUANTIFIABLE,            # the not-quantifiable cap
            "D": maximum,
        },
        maximum,
    )
    return {"answer": key, "computed": f"Rs {int(maximum):,}"}


def q_i2c15_033():
    # amount NOT quantifiable; continuing for 40 days after the first day.
    days_after_first = 40
    maximum = PENALTY_UNQUANTIFIABLE + PENALTY_PER_DAY * days_after_first
    key = _pick(
        {
            "A": maximum,
            "B": PENALTY_UNQUANTIFIABLE,                                    # daily penalty dropped
            "C": PENALTY_UNQUANTIFIABLE + PENALTY_PER_DAY * 41,             # first day counted too
            "D": PENALTY_UNQUANTIFIABLE + PENALTY_PER_DAY,                  # daily penalty charged once
        },
        maximum,
    )
    return {"answer": key, "computed": f"Rs {int(maximum):,}"}


def q_i2c15_034():
    # quantifiable Rs 18,50,000 AND continuing for 25 days after the first day.
    sum_involved = Fraction(1850000)
    days_after_first = 25
    base = PENALTY_MULTIPLE * sum_involved
    continuing = PENALTY_PER_DAY * days_after_first
    maximum = base + continuing
    key = _pick(
        {
            "A": base,                                          # continuing penalty dropped
            "B": maximum,
            "C": sum_involved + continuing,                     # sum not trebled
            "D": base + PENALTY_PER_DAY * 26,                   # 26 continuing days
        },
        maximum,
    )
    return {"answer": key, "computed": f"Rs {int(maximum):,}"}


def cs_i2c15_02_b():
    # quantifiable sum of Rs 63,00,000; not a continuing contravention.
    sum_involved = Fraction(6300000)
    maximum = PENALTY_MULTIPLE * sum_involved
    key = _pick(
        {
            "A": sum_involved,                      # the sum itself
            "B": Fraction(2) * sum_involved,        # twice, not thrice
            "C": maximum,
            "D": PENALTY_UNQUANTIFIABLE,            # the not-quantifiable cap
        },
        maximum,
    )
    return {"answer": key, "computed": f"Rs {int(maximum):,}"}


# ── ss. 14, 15, 17 and 35 · the enforcement and appeal clocks ────────────

def q_i2c15_035():
    # notice for payment served 10 June 2026; s. 14(1) allows 90 DAYS.
    served = date(2026, 6, 10)
    due = _add_days(served, 90)
    key = _pick(
        {
            "A": _add_days(served, 45),      # the ss. 17/19 appeal window
            "B": _add_months(served, 3),     # three calendar months
            "C": due,
            "D": _add_days(served, 180),     # the s. 15 compounding period
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c15_036():
    # compounding application RECEIVED 12 May 2026; s. 15(1) allows 180 DAYS.
    received = date(2026, 5, 12)
    due = _add_days(received, 180)
    key = _pick(
        {
            "A": _add_months(received, 6),   # six calendar months
            "B": _add_days(received, 90),    # the s. 14 payment period
            "C": _add_days(received, 45),    # the appeal window
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c15_037():
    # Tribunal's order COMMUNICATED 3 December 2026; s. 35 allows 60 DAYS.
    communicated = date(2026, 12, 3)
    due = _add_days(communicated, 60)
    key = _pick(
        {
            "A": due,
            "B": _add_days(communicated, 45),      # the ss. 17/19 window
            "C": _add_months(communicated, 2),     # two calendar months
            "D": _add_days(communicated, 90),      # no 90-day appeal exists
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c15_03_b():
    # copy of the order RECEIVED 21 July 2026; s. 17 allows 45 DAYS.
    received = date(2026, 7, 21)
    due = _add_days(received, 45)
    key = _pick(
        {
            "A": _add_days(received, 30),      # no 30-day period exists
            "B": _add_days(received, 60),      # the s. 35 High Court window
            "C": _add_months(received, 3),     # three calendar months
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}
