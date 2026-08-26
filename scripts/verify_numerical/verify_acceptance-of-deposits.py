"""Verifier for intermediate/corporate-and-other-laws/acceptance-of-deposits.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

Two kinds of numerical live in this chapter — date arithmetic and percentage
ceilings computed off a balance-sheet base — so three primitives do all the
work:

  _add_days(d, n)     a period expressed in DAYS is counted from the trigger
                      date, exclusive of the trigger day (day 1 is the next
                      day). 365 days from 5 May 2026 -> 5 May 2027.
  _add_months(d, n)   a period expressed in MONTHS lands on the same day of
                      the later month, with a clamp for short months. Used
                      only to build the "read it as calendar months"
                      distractors, never for a period the law states in days.
  _base(capital, free_reserves, securities_premium)
                      the base on which EVERY percentage ceiling in rule 3 is
                      computed: paid-up share capital + free reserves +
                      securities premium account. Money is carried as
                      fractions.Fraction so that a percentage never loses a
                      rupee to binary floating point.

Which primitive applies is a legal question, not a coding one:

  r. 2(1)(c)  share application money: allot within 60 DAYS of receipt, else
              refund within 15 DAYS from the expiry of those 60 days ->
              _add_days twice
  r. 2(1)(c)  advance against goods or services appropriated within 365 DAYS
              of ACCEPTANCE (not one calendar year — the difference bites in
              a period spanning 29 February)             -> _add_days
  s. 73(2)(c) deposit repayment reserve = 20% of the deposits MATURING in the
              following financial year                    -> Fraction(20, 100)
  r. 3(2)     members' deposits of a non-eligible company: 35% of the base,
              tested on the proposed deposit TOGETHER WITH deposits already
              outstanding                                 -> Fraction(35, 100)
  exemption   members' deposits of an exempt private company: 100% of the base
  r. 3(3)(a)  members' deposits of an eligible company: 10% of the base
  r. 3(3)(b)  public deposits of an eligible company: 25% of the base
  r. 3(1)     short-term (sub-six-month) deposits: 10% of the base
  r. 16       return of deposits in Form DPT-3: information as on 31 MARCH,
              filed on or before 30 JUNE of the same calendar year
  r. 17       penal interest at 18% p.a. for the OVERDUE period only, counted
              in days from maturity to actual repayment
  r. 15       premature repayment: the rate the company would have paid for
              the period the deposit ACTUALLY RAN, reduced by 1 percentage
              point (never the contracted rate less 1%)
  s. 76A(a)   company's minimum penalty = the LOWER of Rs 1 crore and twice
              the deposits accepted, capped at Rs 10 crore

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from fractions import Fraction

CRORE = 10 ** 7
LAKH = 10 ** 5


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


def _base(capital, free_reserves, securities_premium) -> Fraction:
    """Paid-up share capital + free reserves + securities premium account."""
    return Fraction(capital) + Fraction(free_reserves) + Fraction(securities_premium)


def _pct(amount: Fraction, numerator: int) -> Fraction:
    return amount * Fraction(numerator, 100)


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


def _money(value: Fraction) -> str:
    assert value.denominator == 1, value
    return str(int(value))


# ── rule 2(1)(c) · share application money and trade advances ────────────

def q_i2c5_004():
    # Share application money received 10 March 2026, nothing allotted.
    # Allot within 60 DAYS of receipt; failing that, refund within 15 DAYS
    # from the expiry of those 60 days, else it becomes a deposit.
    received = date(2026, 3, 10)
    allot_by = _add_days(received, 60)
    refund_by = _add_days(allot_by, 15)
    key = _pick(
        {
            "A": allot_by,                    # the allotment deadline
            "B": refund_by,
            "C": _add_days(allot_by, 30),     # 30 days to refund instead of 15
            "D": _add_months(received, 2),    # 60 days read as two months
        },
        refund_by,
    )
    return {"answer": key, "computed": refund_by.isoformat()}


def q_i2c5_007():
    # Advance against the supply of goods accepted 5 May 2026: 365 DAYS to
    # appropriate it against supply. The window spans no 29 February.
    accepted = date(2026, 5, 5)
    due = _add_days(accepted, 365)
    key = _pick(
        {
            "A": _add_months(accepted, 6),    # six months
            "B": due,
            "C": _add_days(accepted, 364),    # off-by-one
            "D": _add_months(accepted, 24),   # two years
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c5_01_b():
    # Same 365-day rule, but the window spans 29 February 2028, so 365 days
    # from 20 June 2027 fall ONE DAY SHORT of 20 June 2028.
    accepted = date(2027, 6, 20)
    due = _add_days(accepted, 365)
    assert _add_months(accepted, 12) - accepted == timedelta(days=366)
    key = _pick(
        {
            "A": _add_months(accepted, 12),   # read as one calendar year
            "B": _add_months(accepted, 6),    # six months
            "C": due,
            "D": date(2028, 3, 31),           # the financial-year end
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 73(2)(c) · deposit repayment reserve account ──────────────────────

def q_i2c5_017():
    # 20% of the deposits maturing during the following financial year.
    maturing = Fraction(6_25_00_000)
    reserve = _pct(maturing, 20)
    key = _pick(
        {
            "A": _pct(maturing, 25),
            "B": _pct(maturing, 15),
            "C": reserve,
            "D": _pct(maturing, 10),
        },
        reserve,
    )
    return {"answer": key, "computed": _money(reserve)}


def cs_i2c5_03_b():
    maturing = Fraction(4_60_00_000)
    reserve = _pct(maturing, 20)
    key = _pick(
        {
            "A": _pct(maturing, 25),
            "B": reserve,
            "C": _pct(maturing, 10),
            "D": _pct(maturing, 35),
        },
        reserve,
    )
    return {"answer": key, "computed": _money(reserve)}


# ── rule 3 · the percentage ceilings, all on the same base ───────────────

def q_i2c5_021():
    # Exempt PRIVATE company: members' deposits up to 100% of the base.
    capital, reserves, premium = 2_00_00_000, 1_20_00_000, 80_00_000
    base = _base(capital, reserves, premium)
    ceiling = _pct(base, 100)
    key = _pick(
        {
            "A": _pct(base, 35),                       # the s. 73(2) ceiling
            "B": Fraction(capital),                    # capital alone
            "C": ceiling,
            "D": Fraction(capital) + Fraction(reserves),  # premium omitted
        },
        ceiling,
    )
    return {"answer": key, "computed": _money(ceiling)}


def q_i2c5_025():
    # ELIGIBLE company, deposits from the PUBLIC: 25% of the base.
    capital, reserves, premium = 60 * CRORE, 36 * CRORE, 24 * CRORE
    base = _base(capital, reserves, premium)
    ceiling = _pct(base, 25)
    key = _pick(
        {
            "A": ceiling,
            "B": _pct(base, 10),                                   # members' limb
            "C": _pct(base, 35),                                   # the aggregate
            "D": _pct(Fraction(capital) + Fraction(reserves), 25),  # premium omitted
        },
        ceiling,
    )
    return {"answer": key, "computed": _money(ceiling)}


def q_i2c5_026():
    # ELIGIBLE company, deposits from MEMBERS: 10% of the base, tested on the
    # proposed deposit together with deposits already outstanding.
    base = _base(60 * CRORE, 36 * CRORE, 24 * CRORE)
    outstanding = Fraction(6 * CRORE)
    headroom = _pct(base, 10) - outstanding
    key = _pick(
        {
            "A": _pct(base, 10),                  # outstanding not deducted
            "B": headroom,
            "C": _pct(base, 35) - outstanding,    # 35% applied
            "D": _pct(base, 25) - outstanding,    # the public limb applied
        },
        headroom,
    )
    return {"answer": key, "computed": _money(headroom)}


def q_i2c5_030():
    # Short-term deposits repayable earlier than six months: 10% of the base.
    capital, reserves, premium = 9 * CRORE, 4 * CRORE, 2 * CRORE
    base = _base(capital, reserves, premium)
    ceiling = _pct(base, 10)
    key = _pick(
        {
            "A": _pct(base, 35),
            "B": ceiling,
            "C": _pct(base, 25),
            "D": _pct(Fraction(capital), 10),   # 10% of capital alone
        },
        ceiling,
    )
    return {"answer": key, "computed": _money(ceiling)}


def cs_i2c5_03_a():
    # NON-eligible public company, members' deposits: 35% of the base, less
    # the deposits already outstanding.
    base = _base(8 * CRORE, Fraction(35, 10) * CRORE, Fraction(25, 10) * CRORE)
    outstanding = Fraction(14, 10) * CRORE
    headroom = _pct(base, 35) - outstanding
    key = _pick(
        {
            "A": _pct(base, 35),                   # outstanding not deducted
            "B": _pct(base, 100) - outstanding,    # the private-company ceiling
            "C": headroom,
            "D": _pct(base, 10),                   # the eligible-company limb
        },
        headroom,
    )
    return {"answer": key, "computed": _money(headroom)}


# ── rule 16 · the annual return of deposits ──────────────────────────────

def q_i2c5_033():
    # DPT-3 carries the position as on 31 March and is filed on or before
    # 30 June of the SAME calendar year.
    as_on = date(2027, 3, 31)
    assert (as_on.month, as_on.day) == (3, 31)
    due = date(as_on.year, 6, 30)
    key = _pick(
        {
            "A": due,
            "B": date(as_on.year, 4, 30),    # the s. 73(2)(c) reserve date
            "C": date(as_on.year, 9, 30),    # the outer AGM date
            "D": date(as_on.year, 12, 31),
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── rules 17 and 15 · penal interest and premature repayment ─────────────

def q_i2c5_035():
    # Penal interest at 18% p.a. for the OVERDUE period: 20 June 2026 to
    # 1 September 2026.
    matured, repaid = date(2026, 6, 20), date(2026, 9, 1)
    overdue = (repaid - matured).days
    assert overdue == 73
    principal = Fraction(15_00_000)

    def interest(rate_pct, days):
        return principal * Fraction(rate_pct, 100) * Fraction(days, 365)

    penal = interest(18, overdue)
    key = _pick(
        {
            "A": interest(12, overdue),
            "B": interest(15, overdue),
            "C": penal,
            "D": interest(18, 365),      # a full year instead of the overdue days
        },
        penal,
    )
    return {"answer": key, "computed": _money(penal)}


def q_i2c5_036():
    # Premature repayment after the deposit has run 18 months: the rate the
    # company WOULD HAVE PAID for an 18-month deposit, less 1 percentage
    # point. The 36-month contracted rate of 11% is a distractor.
    principal = Fraction(5_00_000)
    months_run = 18
    contracted_rate = Fraction(11)
    rate_for_period_run = Fraction(95, 10)
    payable_rate = rate_for_period_run - 1

    def interest(rate):
        return principal * rate / 100 * Fraction(months_run, 12)

    payable = interest(payable_rate)
    key = _pick(
        {
            "A": interest(contracted_rate),          # contracted rate, no cut
            "B": interest(contracted_rate - 1),      # 1% off the CONTRACTED rate
            "C": interest(rate_for_period_run),      # right rate, no 1% cut
            "D": payable,
        },
        payable,
    )
    return {"answer": key, "computed": _money(payable)}


# ── s. 76A(a) · the company's minimum penalty ────────────────────────────

def cs_i2c5_02_d():
    # LOWER of Rs 1 crore and twice the deposits accepted, capped at Rs 10
    # crore. Deposits accepted = Rs 35 lakh.
    deposits = Fraction(35 * LAKH)
    floor = min(Fraction(1 * CRORE), 2 * deposits)
    penalty = min(floor, Fraction(10 * CRORE))
    key = _pick(
        {
            "A": Fraction(1 * CRORE),     # Rs 1 crore treated as an absolute floor
            "B": penalty,
            "C": deposits,                # the deposit itself
            "D": Fraction(10 * CRORE),    # the ceiling
        },
        penalty,
    )
    return {"answer": key, "computed": _money(penalty)}
