# -*- coding: utf-8 -*-
"""Verifier for intermediate/corporate-and-other-laws/accounts-of-companies.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

Chapter IX of the Companies Act 2013 works with four kinds of arithmetic, so
four primitives do all the work here:

  _add_days(d, n)     a period expressed in DAYS is counted from the trigger
                      date, exclusive of the trigger day (day 1 is the next
                      day). 30 days from 31 Mar -> 30 Apr.
  _add_months(d, n)   a period expressed in MONTHS lands on the same day of
                      the later month, clamped for short months.
                      6 months from 31 Mar -> 30 Sep.
  _fy(y)              a financial year LABEL from its opening calendar year:
                      _fy(2018) -> "2018-19".
  Fraction            money and percentages, so that 2% of an average of three
                      rupee figures is exact.

Which primitive applies is a legal question, not a coding one:

  s. 128(1) proviso  notice of the other place to the Registrar within 7 DAYS
                     of the BOARD'S DECISION                    -> _add_days
  s. 128(5)          books of the 8 FINANCIAL YEARS immediately
                     preceding the current financial year       -> _fy
  s. 130(3)          re-opening reaches back the same 8
                     FINANCIAL YEARS                            -> _fy
  s. 135(1)          net worth >= 500 cr OR turnover >= 1000 cr
                     OR net profit >= 5 cr, tested on the
                     IMMEDIATELY PRECEDING financial year       -> comparison
  s. 135(5)          2% of the AVERAGE s. 198 net profits of the
                     3 immediately preceding financial years    -> Fraction
  s. 135(5) 2nd pr.  unspent, NOT an ongoing project: to a
                     Schedule VII Fund within 6 MONTHS of the
                     EXPIRY OF THE FINANCIAL YEAR               -> _add_months
  s. 135(6)          unspent, ONGOING project: to the Unspent CSR
                     Account within 30 DAYS of the END OF THE
                     FINANCIAL YEAR; spend within 3 FINANCIAL
                     YEARS; then to a Fund within 30 DAYS of the
                     completion of the third financial year     -> _add_days
  s. 135(7)          company: min(2 x amount, Rs 1 crore);
                     officer: min(amount / 10, Rs 2 lakh)       -> Fraction
  s. 137(1)          30 DAYS from the date of the AGM (and from
                     the adjourned AGM for adopted statements)  -> _add_days
  s. 137(1) proviso  OPC: 180 DAYS from the CLOSURE of the
                     financial year, not from adoption          -> _add_days
  s. 137(2)          no AGM held: 30 DAYS from the LAST DATE the
                     AGM ought to have been held (itself 6
                     MONTHS from the close of the year)         -> both
  s. 138 / Rule 13   unlisted public: 50 / 200 / 100 / 25 crore;
                     private: 200 / 100 crore only, on the
                     PRECEDING financial year's figures         -> comparison

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from fractions import Fraction

CRORE = Fraction(10_000_000)
LAKH = Fraction(100_000)


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


def _fy(opening_year: int) -> str:
    """Financial-year label from its opening calendar year: 2018 -> '2018-19'."""
    return "%d-%02d" % (opening_year, (opening_year + 1) % 100)


def _fy_end(opening_year: int) -> date:
    """Closing date of a financial year: 2026 -> 31 March 2027."""
    return date(opening_year + 1, 3, 31)


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError("computed %r matches no option in %r" % (value, options))


# ── s. 128 · books of account ────────────────────────────────────────────

def q_i2c9_004():
    # current financial year 2026-27; s. 128(5) preserves the books of the 8
    # financial years IMMEDIATELY PRECEDING it, so the earliest is 2018-19.
    current_open = 2026
    earliest = _fy(current_open - 8)
    key = _pick(
        {
            "A": _fy(current_open - 10),   # ten years back
            "B": _fy(current_open - 9),    # off-by-one: current year counted in
            "C": earliest,
            "D": _fy(current_open - 7),    # one year short
        },
        earliest,
    )
    return {"answer": key, "computed": earliest}


def q_i2c9_006():
    # Board resolution 18 September 2026; notice of the full address to the
    # Registrar within 7 DAYS of that decision (first proviso to s. 128(1)).
    resolved = date(2026, 9, 18)
    due = _add_days(resolved, 7)
    key = _pick(
        {
            "A": due,
            "B": due - timedelta(days=1),   # off-by-one
            "C": _add_days(resolved, 15),   # a 15-day period, which s. 128 has not
            "D": _add_days(resolved, 30),   # the s. 137 filing clock
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 135(1) · CSR applicability ────────────────────────────────────────

def _csr_limb(net_worth_cr, turnover_cr, net_profit_cr):
    """Return the single s. 135(1) limb crossed, or None where none is."""
    crossed = []
    if Fraction(net_worth_cr) >= 500:
        crossed.append("net worth")
    if Fraction(turnover_cr) >= 1000:
        crossed.append("turnover")
    if Fraction(net_profit_cr) >= 5:
        crossed.append("net profit")
    assert len(crossed) <= 1, "stem was drafted so that at most one limb crosses"
    return crossed[0] if crossed else None


def q_i2c9_026():
    # immediately preceding FY 2025-26: net worth 420 cr, turnover 880 cr,
    # net profit 6.20 cr. Only the net-profit limb is crossed.
    limb = _csr_limb(420, 880, Fraction(620, 100))
    key = _pick(
        {
            "A": None,            # section 135 does not apply
            "B": "net profit",
            "C": "net worth",
            "D": "turnover",
        },
        limb,
    )
    return {"answer": key, "computed": "limb crossed: %s" % limb}


# ── s. 135(5) · two per cent of a three-year average ─────────────────────

def _csr_obligation(profits_rupees):
    """2% of the average of the three s. 198 net profits, exactly."""
    average = sum(profits_rupees, Fraction(0)) / len(profits_rupees)
    return Fraction(2, 100) * average


def q_i2c9_027():
    # s. 198 net profits 8.40 cr, 11.10 cr, 6.30 cr for 2023-24 to 2025-26.
    profits = [Fraction(840, 100) * CRORE, Fraction(1110, 100) * CRORE, Fraction(630, 100) * CRORE]
    amount = _csr_obligation(profits)
    total = sum(profits, Fraction(0))
    key = _pick(
        {
            "A": amount,
            "B": Fraction(2, 100) * profits[-1],   # 2% of the latest year alone
            "C": Fraction(2, 100) * total,         # 2% of the three-year TOTAL
            "D": Fraction(1, 100) * (total / 3),   # 1% instead of 2%
        },
        amount,
    )
    return {"answer": key, "computed": "Rs %s" % int(amount)}


def cs_i2c9_01_a():
    # s. 198 net profits 6.20 cr, 9.40 cr, 4.20 cr for 2023-24 to 2025-26.
    profits = [Fraction(620, 100) * CRORE, Fraction(940, 100) * CRORE, Fraction(420, 100) * CRORE]
    amount = _csr_obligation(profits)
    total = sum(profits, Fraction(0))
    key = _pick(
        {
            "A": amount,
            "B": Fraction(2, 100) * profits[-1],
            "C": Fraction(2, 100) * total,
            "D": Fraction(1, 100) * (total / 3),
        },
        amount,
    )
    return {"answer": key, "computed": "Rs %s" % int(amount)}


# ── ss. 135(5) and 135(6) · the unspent-amount clocks ────────────────────

def q_i2c9_029():
    # ongoing project: to the Unspent CSR Account within 30 DAYS of the end of
    # the financial year, which closed on 31 March 2027.
    fy_end = _fy_end(2026)
    due = _add_days(fy_end, 30)
    key = _pick(
        {
            "A": _add_months(fy_end, 3),      # three calendar months
            "B": due,
            "C": _add_months(fy_end, 6),      # the non-ongoing 6-month clock
            "D": due - timedelta(days=1),     # off-by-one
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c9_030():
    # NOT an ongoing project: to a Schedule VII Fund within 6 MONTHS of the
    # expiry of the financial year (31 March 2027) -> clamped to 30 September.
    fy_end = _fy_end(2026)
    due = _add_months(fy_end, 6)
    key = _pick(
        {
            "A": _add_days(fy_end, 30),           # the ongoing-project clock
            "B": due + timedelta(days=1),         # 1 October, ignoring the clamp
            "C": due,
            "D": _add_months(fy_end, 12),         # a full year
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c9_031():
    # money transferred for FY 2026-27 must be spent within 3 FINANCIAL YEARS;
    # the third of them (2029-30) closes on 31 March 2030, and the residue goes
    # to a Schedule VII Fund within 30 DAYS of that completion.
    third_fy_end = _fy_end(2026 + 3)
    due = _add_days(third_fy_end, 30)
    key = _pick(
        {
            "A": _add_days(_fy_end(2026 + 2), 30),      # only two financial years
            "B": _add_months(third_fy_end, 6),          # the 6-month clock misapplied
            "C": _add_days(_fy_end(2026 + 4), 30),      # four financial years
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c9_01_c():
    # the Rs 2,00,000 not relating to an ongoing project: Schedule VII Fund
    # within 6 MONTHS of the expiry of the financial year ended 31 March 2027.
    fy_end = _fy_end(2026)
    due = _add_months(fy_end, 6)
    key = _pick(
        {
            "A": _add_days(fy_end, 30),
            "B": due,
            "C": _add_months(fy_end, 3),
            "D": _fy_end(2029),                 # the end of the three-year window
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 135(7) · the penalty ──────────────────────────────────────────────

def q_i2c9_032():
    # amount required to be transferred Rs 68,00,000; the company pays twice
    # that amount OR Rs 1 crore, WHICHEVER IS LESS.
    amount = Fraction(68) * LAKH
    penalty = min(2 * amount, CRORE)
    key = _pick(
        {
            "A": 2 * amount,                 # twice, ignoring the cap
            "B": penalty,
            "C": amount,                     # the unspent amount itself
            "D": min(amount / 10, 2 * LAKH), # the OFFICER's penalty
        },
        penalty,
    )
    return {"answer": key, "computed": "Rs %s" % int(penalty)}


# ── s. 137 · filing with the Registrar ───────────────────────────────────

def q_i2c9_035():
    # AGM held 22 August 2026, statements adopted; file within 30 DAYS of the
    # date of the AGM.
    agm = date(2026, 8, 22)
    due = _add_days(agm, 30)
    key = _pick(
        {
            "A": due,
            "B": _add_months(agm, 1),        # read as one calendar month
            "C": _add_days(agm, 60),         # 60 days
            "D": _add_days(agm, 90),         # 90 days
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c9_036():
    # no AGM held. The financial year closed on 31 March 2026, so the meeting
    # ought to have been held by 30 September 2026 (six months); the filing
    # follows within 30 DAYS of that last date.
    fy_end = _fy_end(2025)
    agm_last_date = _add_months(fy_end, 6)
    assert agm_last_date == date(2026, 9, 30), agm_last_date
    due = _add_days(agm_last_date, 30)
    key = _pick(
        {
            "A": agm_last_date,                       # the meeting's own deadline
            "B": due - timedelta(days=1),             # off-by-one
            "C": due,
            "D": _add_days(agm_last_date, 90),        # 90 days
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c9_02_a():
    # One Person Company: 180 DAYS from the CLOSURE of the financial year
    # (31 March 2026). The date of adoption by the member is irrelevant.
    fy_end = _fy_end(2025)
    adopted = date(2026, 8, 2)
    due = _add_days(fy_end, 180)
    key = _pick(
        {
            "A": due,
            "B": _add_months(fy_end, 6),      # read as six calendar months
            "C": due - timedelta(days=1),     # off-by-one
            "D": _add_days(adopted, 30),      # 30 days from adoption
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c9_02_b():
    # statements NOT adopted at the AGM held 18 September 2026: the provisional
    # filing is due within 30 DAYS of the date of that AGM.
    agm = date(2026, 9, 18)
    due = _add_days(agm, 30)
    key = _pick(
        {
            "A": _add_days(agm, 15),         # 15 days
            "B": due - timedelta(days=1),    # off-by-one
            "C": due,
            "D": _add_days(agm, 90),         # 90 days
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 130(3) · the re-opening look-back ─────────────────────────────────

def cs_i2c9_03_b():
    # current financial year 2027-28; s. 130(3) reaches back the 8 financial
    # years immediately preceding it, so the earliest is 2019-20.
    current_open = 2027
    earliest = _fy(current_open - 8)
    key = _pick(
        {
            "A": _fy(current_open - 9),    # off-by-one
            "B": earliest,
            "C": _fy(current_open - 7),    # one year short
            "D": _fy(current_open - 6),    # two years short
        },
        earliest,
    )
    return {"answer": key, "computed": earliest}


# ── s. 138 with Rule 13 · internal-audit thresholds ──────────────────────

def _internal_audit_limb(kind, paid_up_cr, turnover_cr, borrowings_cr, deposits_cr):
    """Return the single prescribed limb crossed, or None where none is.

    The limbs differ by class: an unlisted public company is tested on all
    four, a private company only on turnover and borrowings.
    """
    crossed = []
    if kind == "unlisted public":
        if Fraction(paid_up_cr) >= 50:
            crossed.append("paid-up share capital")
        if Fraction(turnover_cr) >= 200:
            crossed.append("turnover")
        if Fraction(borrowings_cr) >= 100:
            crossed.append("borrowings")
        if Fraction(deposits_cr) >= 25:
            crossed.append("deposits")
    elif kind == "private":
        if Fraction(turnover_cr) >= 200:
            crossed.append("turnover")
        if Fraction(borrowings_cr) >= 100:
            crossed.append("borrowings")
    else:
        raise AssertionError("unknown class %r" % kind)
    assert len(crossed) <= 1, "stem was drafted so that at most one limb crosses"
    return crossed[0] if crossed else None


def q_i2c9_037():
    # unlisted public company: paid-up 38 cr, turnover 165 cr, borrowings that
    # touched 120 cr during the preceding FY, deposits 9 cr.
    limb = _internal_audit_limb("unlisted public", 38, 165, 120, 9)
    key = _pick(
        {
            "A": None,                      # not required
            "B": "turnover",
            "C": "borrowings",
            "D": "paid-up share capital",
        },
        limb,
    )
    return {"answer": key, "computed": "limb crossed: %s" % limb}


def q_i2c9_038():
    # PRIVATE company: paid-up 70 cr and deposits 30 cr are not tests for a
    # private company at all; turnover 90 cr and nil borrowings cross nothing.
    limb = _internal_audit_limb("private", 70, 90, 0, 30)
    key = _pick(
        {
            "A": "paid-up share capital",   # not a private-company limb
            "B": "deposits",                # not a private-company limb
            "C": "both",                    # neither limb exists
            "D": None,                      # internal audit not required
        },
        limb,
    )
    return {"answer": key, "computed": "limb crossed: %s" % limb}
