"""Verifier for intermediate/corporate-and-other-laws/prospectus-and-allotment.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

Three primitives do all the work in this chapter:

  _add_days(d, n)     a period expressed in DAYS runs from the trigger date,
                      exclusive of the trigger day (day 1 is the next day).
                      60 days from 12 May -> 11 Jul.
  _months_between(a, b)
                      the number of COMPLETE calendar months between two dates,
                      used for the s. 42(6) simple-interest computation.
  Fraction            all money is computed in exact rational arithmetic, so a
                      percentage of a percentage never drifts.

Which primitive applies is a legal question, not a coding one:

  s. 39(2)   minimum application money = 5% of the NOMINAL amount of the
             security (never of the issue price)                -> Fraction
  s. 39(3)   minimum subscription within 30 DAYS from the date of
             ISSUE OF THE PROSPECTUS                            -> _add_days
  s. 39(4)   return of allotment within 30 DAYS of the allotment
             (rules-level period; the section itself says "as may
             be prescribed")                                    -> _add_days
  s. 40(6)   commission capped at the LOWER of the rate in the
             articles and 5% (shares) / 2.5% (debentures) of the
             PRICE at which the securities are issued
             (rules-level: r. 13, Companies (Share Capital and
             Debentures) Rules 2014)                            -> Fraction
  s. 42(2)   200 identified persons per FINANCIAL YEAR, in the
             aggregate, EXCLUDING qualified institutional buyers
             and employees under an ESOP scheme (rules-level:
             r. 14, Companies (Prospectus and Allotment of
             Securities) Rules 2014)                            -> plain count
  s. 42(6)   allot within 60 DAYS of RECEIPT OF THE APPLICATION
             MONEY; else repay within 15 DAYS of the expiry of
             those 60 days; else 12% p.a. from the expiry of the
             SIXTIETH DAY (not from the end of the 15-day window)
                                                                -> _add_days
                                                                   + Fraction

Amendment-sensitivity note for the reviewer: the 5% / 2.5% commission caps and
the 200-person cap are RULES-level. If either moves, q-i2c3-034, q-i2c3-035,
q-i2c3-036 and cs-i2c3-01-d must be reworked together with the bank.

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from fractions import Fraction

# Rules-level constants, isolated so a reviewer can see exactly what moves.
COMMISSION_CAP_SHARES = Fraction(5, 100)        # r. 13 — 5% of the issue price
COMMISSION_CAP_DEBENTURES = Fraction(25, 1000)  # r. 13 — 2.5% of the issue price
PRIVATE_PLACEMENT_CAP = 200                     # r. 14 — persons per financial year

# Act-level constants.
MIN_APPLICATION_MONEY = Fraction(5, 100)        # s. 39(2) — 5% of the NOMINAL amount
PP_INTEREST_RATE = Fraction(12, 100)            # s. 42(6) — 12% per annum


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


def _months_between(start: date, end: date) -> int:
    """Complete calendar months between two dates (start exclusive of overshoot)."""
    n = (end.year - start.year) * 12 + (end.month - start.month)
    if _add_months(start, n) > end:
        n -= 1
    return n


def _simple_interest(principal, rate: Fraction, months: int) -> Fraction:
    """Simple interest for a whole number of months at an annual rate."""
    return Fraction(principal) * rate * Fraction(months, 12)


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


# ── s. 39 · minimum application money and the allotment clocks ───────────

def q_i2c3_029():
    # 25,00,000 shares of NOMINAL ₹10 issued at ₹50 (₹10 + ₹40 premium).
    # s. 39(2) floor = 5% of the NOMINAL amount, not of the price.
    qty, nominal, price = 25_00_000, Fraction(10), Fraction(50)
    floor = MIN_APPLICATION_MONEY * nominal * qty
    key = _pick(
        {
            "A": MIN_APPLICATION_MONEY * price * qty,       # 5% of the issue price
            "B": Fraction(10, 100) * nominal * qty,         # 10% of the nominal
            "C": Fraction(25, 1000) * nominal * qty,        # 2.5% of the nominal
            "D": floor,
        },
        floor,
    )
    return {"answer": key, "computed": f"₹{int(floor):,}"}


def q_i2c3_030():
    # prospectus issued 4 June 2026; s. 39(3) allows 30 DAYS from the date of
    # ISSUE of the prospectus for the minimum amount to be subscribed.
    issued = date(2026, 6, 4)
    due = _add_days(issued, 30)
    key = _pick(
        {
            "A": due,
            "B": _add_days(issued, 29),   # off-by-one
            "C": _add_days(issued, 45),   # 45 days
            "D": _add_days(issued, 90),   # the s. 26(8) prospectus-validity period
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c3_031():
    # allotment on 14 September 2026; the return of allotment on a PUBLIC
    # allotment goes in 30 DAYS (rules made for s. 39(4)) — not the 15 days
    # that s. 42(8) allows on a private placement.
    allotted = date(2026, 9, 14)
    due = _add_days(allotted, 30)
    key = _pick(
        {
            "A": _add_days(allotted, 15),   # the s. 42(8) private-placement period
            "B": _add_days(allotted, 29),   # off-by-one
            "C": due,
            "D": _add_days(allotted, 60),   # the s. 42(6) allotment window
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 40(6) · underwriting commission caps (rules-level) ────────────────

def q_i2c3_034():
    # 50,00,000 equity shares of ₹10 each issued at ₹40; articles allow 6%.
    # Cap = LOWER of (articles rate) and (5% of the PRICE at which issued).
    qty, nominal, price = 50_00_000, Fraction(10), Fraction(40)
    articles = Fraction(6, 100)
    issue_value = price * qty
    cap = min(articles * issue_value, COMMISSION_CAP_SHARES * issue_value)
    key = _pick(
        {
            "A": cap,
            "B": articles * issue_value,                      # the articles' rate
            "C": COMMISSION_CAP_SHARES * nominal * qty,       # 5% of the FACE value
            "D": COMMISSION_CAP_DEBENTURES * issue_value,     # the debenture cap
        },
        cap,
    )
    return {"answer": key, "computed": f"₹{int(cap):,}"}


def q_i2c3_035():
    # 2,00,000 debentures of ₹100 each at par; articles allow 4%.
    # Cap = LOWER of (articles rate) and (2.5% of the PRICE at which issued).
    qty, price = 2_00_000, Fraction(100)
    articles = Fraction(4, 100)
    issue_value = price * qty
    cap = min(articles * issue_value, COMMISSION_CAP_DEBENTURES * issue_value)
    key = _pick(
        {
            "A": articles * issue_value,                      # the articles' rate
            "B": Fraction(125, 10000) * issue_value,          # half the correct rate
            "C": cap,
            "D": COMMISSION_CAP_SHARES * issue_value,         # the share cap
        },
        cap,
    )
    return {"answer": key, "computed": f"₹{int(cap):,}"}


# ── s. 42 · the private-placement cap and the 60 / 15 / 12 chain ─────────

def q_i2c3_036():
    # 88 identified persons already offered in FY 2026-27; 30 QIBs and 45 ESOP
    # employees are EXCLUDED from the count entirely.
    identified, qibs, esop = 88, 30, 45
    headroom = PRIVATE_PLACEMENT_CAP - identified
    key = _pick(
        {
            "A": PRIVATE_PLACEMENT_CAP - identified - qibs,          # QIBs counted
            "B": headroom,
            "C": PRIVATE_PLACEMENT_CAP - identified - esop,          # ESOP counted
            "D": PRIVATE_PLACEMENT_CAP - identified - qibs - esop,   # both counted
        },
        headroom,
    )
    return {"answer": key, "computed": headroom}


def q_i2c3_037():
    # application money received 12 May 2026; allot within 60 DAYS of RECEIPT.
    received = date(2026, 5, 12)
    due = _add_days(received, 60)
    key = _pick(
        {
            "A": _add_days(received, 75),   # 60 + 15, i.e. the repayment date
            "B": _add_days(received, 61),   # off-by-one
            "C": _add_days(received, 90),   # the s. 26(8) period
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c3_038():
    # application money received 18 August 2026; no allotment. Repay within
    # 15 DAYS of the expiry of the 60 days.
    received = date(2026, 8, 18)
    allot_by = _add_days(received, 60)
    repay_by = _add_days(allot_by, 15)
    key = _pick(
        {
            "A": repay_by,
            "B": allot_by,                        # the allotment date
            "C": _add_days(allot_by, 16),         # off-by-one
            "D": _add_days(allot_by, 30),         # 30 days instead of 15
        },
        repay_by,
    )
    return {"answer": key, "computed": repay_by.isoformat()}


def cs_i2c3_01_a():
    # ₹6,00,00,000 received 20 June 2026; s. 42(6) allows 60 DAYS to allot.
    received = date(2026, 6, 20)
    due = _add_days(received, 60)
    key = _pick(
        {
            "A": _add_days(received, 59),   # off-by-one
            "B": _add_days(received, 75),   # 60 + 15, the repayment date
            "C": _add_days(received, 90),   # the s. 26(8) period
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c3_01_b():
    # Interest under s. 42(6) runs at 12% p.a. from the EXPIRY OF THE SIXTIETH
    # DAY (19 Aug 2026) to the date of repayment (19 Feb 2027) — six complete
    # months — NOT from the end of the further 15-day window.
    principal = 6_00_00_000
    received = date(2026, 6, 20)
    interest_from = _add_days(received, 60)
    repaid = date(2027, 2, 19)
    months = _months_between(interest_from, repaid)
    interest = _simple_interest(principal, PP_INTEREST_RATE, months)
    key = _pick(
        {
            "A": interest,
            "B": _simple_interest(principal, PP_INTEREST_RATE, 12),   # a full year
            "C": _simple_interest(principal, Fraction(6, 100), months),  # 6% p.a.
            "D": _simple_interest(principal, PP_INTEREST_RATE, months - 1),
        },
        interest,
    )
    return {"answer": key, "computed": f"{months} months → ₹{int(interest):,}"}


def cs_i2c3_01_d():
    # 120 identified persons offered in FY 2026-27; 25 QIBs and 40 ESOP
    # employees are excluded from the 200-person count.
    identified, qibs, esop = 120, 25, 40
    headroom = PRIVATE_PLACEMENT_CAP - identified
    key = _pick(
        {
            "A": PRIVATE_PLACEMENT_CAP - identified - qibs,          # QIBs counted
            "B": headroom,
            "C": PRIVATE_PLACEMENT_CAP - identified - esop,          # ESOP counted
            "D": PRIVATE_PLACEMENT_CAP - identified - qibs - esop,   # both counted
        },
        headroom,
    )
    return {"answer": key, "computed": headroom}


def cs_i2c3_03_b():
    # 12,00,000 shares of NOMINAL ₹100 issued at ₹250.
    # s. 39(2) floor = 5% of the NOMINAL amount.
    qty, nominal, price = 12_00_000, Fraction(100), Fraction(250)
    floor = MIN_APPLICATION_MONEY * nominal * qty
    key = _pick(
        {
            "A": floor,
            "B": MIN_APPLICATION_MONEY * price * qty,        # 5% of the issue price
            "C": Fraction(25, 1000) * nominal * qty,         # 2.5% of the nominal
            "D": Fraction(10, 100) * nominal * qty,          # 10% of the nominal
        },
        floor,
    )
    return {"answer": key, "computed": f"₹{int(floor):,}"}
