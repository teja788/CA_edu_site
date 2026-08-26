"""Verifier for intermediate/corporate-and-other-laws/share-capital-and-debentures.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

The numericals in this chapter fall into two families:

  money and share-count arithmetic (fractions.Fraction, so 12% x 8/12 is exact):
    s. 48(2)   dissent threshold = 10% of the issued shares of the class
    s. 51      dividend in proportion to the PAID-UP amount, not nominal value
    s. 53(3)   refund interest at 12% p.a. from the date of issue, time-apportioned
    s. 55(2)(c) CRR = nominal amount redeemed OUT OF PROFITS
               (nominal redeemed minus fresh-issue proceeds; premium excluded)
    s. 63(1)   bonus capitalisation = free reserves + securities premium + CRR
               (never the revaluation reserve)
    s. 68(2)(b) special-resolution ceiling = 25% of (paid-up capital + free
               reserves), free reserves INCLUDING securities premium (Expl. II)
    s. 68(2)   Board route = 10% of the same base
    s. 68(2)(d) debt ceiling = 2 x (paid-up capital + free reserves)
    s. 69(1)   CRR on buy-back = NOMINAL value bought back, not consideration

  timeline arithmetic (datetime.date):
    s. 56(1)   SH-4 delivered within 60 DAYS of execution        -> _add_days
    s. 62(1)(a) offer open not more than 30 DAYS from the offer  -> _add_days
    rules      secured debentures redeemable within 10 YEARS     -> _add_years

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


def _add_years(d: date, n: int) -> date:
    """A period of n years landing on the same day of the same month."""
    return _add_months(d, 12 * n)


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


# -- s. 48(2) - the 10% dissent threshold ---------------------------------

def q_i2c4_006():
    # class of 8,00,000 issued preference shares; applicants must hold not
    # less than 10% of the issued shares of the class.
    issued = 800_000
    threshold = issued * Fraction(10, 100)
    key = _pick(
        {
            "A": issued * Fraction(5, 100),    # 5% -- wrong percentage
            "B": threshold,
            "C": issued * Fraction(15, 100),   # 15%
            "D": issued * Fraction(25, 100),   # 25% -- confuses the 3/4 consent
        },
        threshold,
    )
    return {"answer": key, "computed": int(threshold)}


# -- s. 51 - dividend in proportion to the amount paid-up -----------------

def q_i2c4_009():
    # 5,000 shares of Rs 10 each, Rs 6 paid-up; dividend 12% on the PAID-UP
    # amount under a s. 51 article.
    shares, nominal, paid_up = 5_000, 10, 6
    rate = Fraction(12, 100)
    dividend = shares * paid_up * rate
    key = _pick(
        {
            "A": shares * nominal * rate,             # on nominal value
            "B": shares * (nominal - paid_up) * rate, # on the unpaid Rs 4
            "C": dividend,
            "D": shares * 8 * rate,                   # on a split-the-difference Rs 8
        },
        dividend,
    )
    return {"answer": key, "computed": int(dividend)}


# -- s. 53(3) - refund with 12% p.a. interest from the date of issue ------

def q_i2c4_013():
    # Rs 4,50,000 received on 1 May 2026; refunded 1 Jan 2027 = 8 months.
    monies = 450_000
    rate = Fraction(12, 100)
    months = 8
    interest = monies * rate * Fraction(months, 12)
    key = _pick(
        {
            "A": interest,
            "B": monies * rate,                        # a full year
            "C": monies * rate * Fraction(9, 12),      # nine months, miscounted
            "D": monies * rate * Fraction(6, 12),      # six months
        },
        interest,
    )
    return {"answer": key, "computed": int(interest)}


# -- s. 55(2)(c) - CRR on a redemption financed two ways ------------------

def q_i2c4_017():
    # 2,00,000 preference shares of Rs 100 fully paid, redeemed at par;
    # fresh-issue proceeds Rs 80,00,000; CRR = nominal redeemed out of profits.
    nominal_total = 200_000 * 100
    fresh_issue = 8_000_000
    crr = nominal_total - fresh_issue
    key = _pick(
        {
            "A": nominal_total,   # the whole nominal amount
            "B": crr,
            "C": fresh_issue,     # the slice that needs NO CRR
            "D": 0,               # nil
        },
        crr,
    )
    return {"answer": key, "computed": crr}


# -- s. 56(1) - SH-4 delivered within 60 days of execution ----------------

def q_i2c4_019():
    executed = date(2026, 4, 10)
    due = _add_days(executed, 60)
    key = _pick(
        {
            "A": _add_days(executed, 30),   # the s. 58 refusal-notice clock
            "B": _add_months(executed, 2),  # read as two calendar months
            "C": _add_days(executed, 90),   # 90 days
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# -- s. 62(1)(a)(i) - rights offer open at most 30 days from the offer ----

def q_i2c4_027():
    offered = date(2026, 9, 1)
    latest_close = _add_days(offered, 30)
    key = _pick(
        {
            "A": _add_days(offered, 15),    # the EARLIEST close, not the latest
            "B": latest_close,
            "C": _add_days(offered, 60),    # 60 days
            "D": _add_months(offered, 2),   # two calendar months
        },
        latest_close,
    )
    return {"answer": key, "computed": latest_close.isoformat()}


# -- s. 63(1) - the bonus capitalisation base -----------------------------

def q_i2c4_031():
    free_reserves = 3_200_000
    securities_premium = 1_000_000
    crr = 800_000
    revaluation_reserve = 1_200_000
    capitalisable = free_reserves + securities_premium + crr
    key = _pick(
        {
            "A": capitalisable + revaluation_reserve,   # wrongly adds revaluation
            "B": free_reserves + securities_premium,    # drops the CRR
            "C": capitalisable,
            "D": free_reserves,                         # free reserves alone
        },
        capitalisable,
    )
    return {"answer": key, "computed": capitalisable}


# -- cs-01 - the buy-back case: one balance sheet, four ceilings ----------

_BS = {
    "paid_up_equity": 10_000_000,
    "free_reserves": 22_000_000,
    "securities_premium": 8_000_000,
    "secured_loans": 50_000_000,
    "unsecured_loans": 26_000_000,
}
# Explanation II to s. 68: free reserves include the securities premium account.
_BASE = _BS["paid_up_equity"] + _BS["free_reserves"] + _BS["securities_premium"]


def cs_i2c4_01_a():
    # special-resolution ceiling = 25% of the aggregate base.
    ceiling = _BASE * Fraction(25, 100)
    base_excl_premium = _BS["paid_up_equity"] + _BS["free_reserves"]
    key = _pick(
        {
            "A": base_excl_premium * Fraction(25, 100),      # premium excluded
            "B": _BS["paid_up_equity"] * Fraction(25, 100),  # capital alone
            "C": ceiling,
            "D": _BASE * Fraction(10, 100),                  # the Board route
        },
        ceiling,
    )
    return {"answer": key, "computed": int(ceiling)}


def cs_i2c4_01_b():
    # Board route = 10% of paid-up equity capital and free reserves.
    ceiling = _BASE * Fraction(10, 100)
    base_excl_premium = _BS["paid_up_equity"] + _BS["free_reserves"]
    key = _pick(
        {
            "A": ceiling,
            "B": _BS["paid_up_equity"] * Fraction(10, 100),   # capital alone
            "C": _BASE * Fraction(25, 100),                   # the SR ceiling
            "D": base_excl_premium * Fraction(10, 100),       # premium excluded
        },
        ceiling,
    )
    return {"answer": key, "computed": int(ceiling)}


def cs_i2c4_01_c():
    # s. 68(2)(d): post-buy-back debts must not exceed 2 x the base.
    ceiling = 2 * _BASE
    existing_debt = _BS["secured_loans"] + _BS["unsecured_loans"]
    key = _pick(
        {
            "A": _BASE,          # the base itself, not twice it
            "B": ceiling,
            "C": 4 * _BASE,      # four times
            "D": existing_debt,  # the figure to be tested, not the ceiling
        },
        ceiling,
    )
    return {"answer": key, "computed": ceiling}


def cs_i2c4_01_d():
    # s. 69: CRR = nominal value bought back (2,50,000 shares of Rs 10).
    shares, nominal, price = 250_000, 10, 40
    crr = shares * nominal
    key = _pick(
        {
            "A": shares * price,             # the full consideration
            "B": shares * (price - nominal), # the premium element
            "C": 0,                          # nil
            "D": crr,
        },
        crr,
    )
    return {"answer": key, "computed": crr}


# -- cs-02 - preference redemption: the CRR again -------------------------

def cs_i2c4_02_b():
    # 1,00,000 preference shares of Rs 100 fully paid; fresh issue of 40,000
    # equity shares of Rs 100 at par -> proceeds Rs 40,00,000; premium 10%.
    nominal_total = 100_000 * 100
    fresh_issue = 40_000 * 100
    premium = nominal_total * Fraction(10, 100)
    crr = nominal_total - fresh_issue
    key = _pick(
        {
            "A": nominal_total,            # the whole nominal amount
            "B": fresh_issue,              # the no-CRR slice
            "C": crr,
            "D": nominal_total + premium,  # wrongly adds the 10% premium
        },
        crr,
    )
    return {"answer": key, "computed": crr}


# -- cs-03 - secured debentures: the 10-year tenure -----------------------

def cs_i2c4_03_b():
    # issued 1 July 2026; ordinary (non-infrastructure) company -> redeem
    # within 10 YEARS of the date of issue (rules-level).
    issued = date(2026, 7, 1)
    latest = _add_years(issued, 10)
    key = _pick(
        {
            "A": _add_years(issued, 5),    # five years
            "B": latest,
            "C": _add_years(issued, 20),   # the s. 55 preference ceiling
            "D": _add_years(issued, 30),   # the infrastructure outer limit
        },
        latest,
    )
    return {"answer": key, "computed": latest.isoformat()}
