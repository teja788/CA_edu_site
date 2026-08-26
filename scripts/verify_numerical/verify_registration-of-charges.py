"""Verifier for intermediate/corporate-and-other-laws/registration-of-charges.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

Chapter VI of the Companies Act 2013 is pure timeline arithmetic, and every
period in it is expressed in DAYS — never in months. So one primitive does
almost all the work, and a second exists only to build the "student converted
days into calendar months" distractors:

  _add_days(d, n)     a period expressed in DAYS runs from the trigger date,
                      exclusive of the trigger day (day 1 is the next day).
                      30 days from 5 May -> 4 June.
  _add_months(d, n)   a period expressed in MONTHS would land on the same day
                      of the later month, with a clamp for short months. NO
                      period in ss. 77-87 is expressed this way except the
                      six-month transitional fallback in the second proviso to
                      s. 77(1), which no question in this bank uses.

Which period applies is a legal question, not a coding one:

  s. 77(1)          registration of a CREATION: 30 DAYS from the date of
                    creation, as of right, normal fees          -> _add_days 30
  s. 77(1) prov 1(b) Registrar may allow up to 60 DAYS FROM CREATION on an
                    application, additional fees                -> _add_days 60
  s. 77(1) prov 2(b) a FURTHER 60 days, i.e. 120 DAYS FROM CREATION, on an
                    application, ad valorem fees                -> _add_days 120
                    NOTE: 60 and 120 are both measured from CREATION, so the
                    windows are not cumulative (not 30 + 60 + 120).
  s. 77(1) prov 1(a) charge created BEFORE the commencement of the Companies
                    (Amendment) Ordinance 2019: 300 DAYS from creation
                                                                -> _add_days 300
  s. 78             the charge-holder's right arises once the company's 30
                    days LAPSE, i.e. from the next day  -> _add_days 30 then +1
  s. 78             the Registrar may allow registration within 14 DAYS AFTER
                    GIVING NOTICE TO THE COMPANY (not from the application)
                                                                -> _add_days 14
  s. 82(1)          intimation of satisfaction: 30 DAYS from the date of
                    payment or satisfaction                     -> _add_days 30
  s. 82(1) proviso  extended to 300 DAYS from the payment or satisfaction, on
                    an application by the company OR the charge-holder
                                                                -> _add_days 300
  s. 82(2)          the charge-holder shows cause within a period NOT
                    EXCEEDING 14 DAYS of the Registrar's notice -> _add_days 14
  s. 84(1)          notice of the appointment of a receiver or manager within
                    30 DAYS of the ORDER or of the APPOINTMENT  -> _add_days 30

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta


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


# ── s. 77(1) · the three creation windows, all measured from CREATION ────

_VINDHYA_CREATED = date(2026, 5, 5)


def q_i2c6_010():
    # 30 DAYS from the date of creation, as of right, normal fees.
    created = _VINDHYA_CREATED
    due = _add_days(created, 30)
    key = _pick(
        {
            "A": _add_months(created, 1),    # days read as one calendar month
            "B": _add_days(created, 60),     # the first extension
            "C": due,
            "D": _add_days(created, 15),     # a 15-day period that does not exist
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c6_011():
    # First proviso (b): up to 60 DAYS FROM CREATION on additional fees --
    # NOT 60 days from the end of the first window.
    created = _VINDHYA_CREATED
    due = _add_days(created, 60)
    key = _pick(
        {
            "A": due,
            "B": _add_days(created, 30),     # the window already lapsed
            "C": _add_months(created, 2),    # read as two calendar months
            "D": _add_days(created, 120),    # the ad valorem outer limit
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c6_012():
    # Second proviso (b): a FURTHER 60 days after the 60-day window, i.e. an
    # outer limit of 120 DAYS FROM CREATION, on ad valorem fees.
    created = _VINDHYA_CREATED
    due = _add_days(created, 60 + 60)
    key = _pick(
        {
            "A": _add_months(created, 4),    # 120 days read as four months
            "B": _add_days(created, 60),     # the first extension
            "C": _add_days(created, 180),    # a 180-day period that does not exist
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c6_013():
    # First proviso (a): charge created BEFORE the commencement of the 2019
    # Ordinance -- 300 DAYS from creation on additional fees.
    created = date(2018, 7, 10)
    due = _add_days(created, 300)
    key = _pick(
        {
            "A": _add_days(created, 60),     # the post-commencement window
            "B": due,
            "C": _add_months(created, 10),   # 300 days read as ten months
            "D": _add_days(created, 120),    # the post-commencement outer limit
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 78 · the charge-holder's route ────────────────────────────────────

def q_i2c6_022():
    # The company's 30 days under s. 77(1) run from creation on 12 Feb 2026.
    # The failure is complete when they expire, so the holder's right under
    # s. 78 arises on the NEXT day.
    created = date(2026, 2, 12)
    company_window_ends = _add_days(created, 30)
    earliest = company_window_ends + timedelta(days=1)
    key = _pick(
        {
            "A": company_window_ends,        # still the company's own window
            "B": _add_days(created, 60),     # waiting for the first extension
            "C": earliest,
            "D": _add_days(created, 120),    # waiting for every window to close
        },
        earliest,
    )
    return {"answer": key, "computed": earliest.isoformat()}


def q_i2c6_023():
    # The Registrar may allow registration within 14 DAYS AFTER GIVING NOTICE
    # TO THE COMPANY -- the clock starts at the notice, not the application.
    notice = date(2026, 4, 20)
    due = _add_days(notice, 14)
    key = _pick(
        {
            "A": due,
            "B": _add_days(notice, 7),       # 7 days
            "C": _add_days(notice, 30),      # the 30-day periods elsewhere
            "D": _add_days(notice, 21),      # 21 days
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 82 · satisfaction ─────────────────────────────────────────────────

_TRILOK_SATISFIED = date(2026, 9, 9)


def q_i2c6_030():
    # s. 82(1): 30 DAYS from the date of payment or satisfaction, as of right.
    satisfied = _TRILOK_SATISFIED
    due = _add_days(satisfied, 30)
    key = _pick(
        {
            "A": _add_days(satisfied, 14),   # the s. 82(2) show-cause period
            "B": _add_days(satisfied, 60),   # the s. 77 first extension
            "C": due,
            "D": _add_days(satisfied, 300),  # the extended window
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c6_031():
    # Proviso to s. 82(1): 300 DAYS from the payment or satisfaction, on an
    # application by the company OR the charge-holder, additional fees.
    # The 300-day window survived the 2019 recast only for SATISFACTION.
    satisfied = _TRILOK_SATISFIED
    due = _add_days(satisfied, 300)
    key = _pick(
        {
            "A": _add_months(satisfied, 10),  # 300 days read as ten months
            "B": _add_days(satisfied, 30),    # the window already lapsed
            "C": _add_months(satisfied, 6),   # the transitional six months
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c6_032():
    # s. 82(2): the holder shows cause within a period NOT EXCEEDING 14 DAYS
    # specified in the Registrar's notice; the stem says the maximum was set.
    notice = date(2026, 11, 3)
    due = _add_days(notice, 14)
    key = _pick(
        {
            "A": due,
            "B": due + timedelta(days=1),    # off-by-one: notice day counted
            "C": _add_days(notice, 30),      # the s. 82(1) intimation period
            "D": _add_days(notice, 7),       # 7 days
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 84 · receiver or manager ──────────────────────────────────────────

def q_i2c6_036():
    # s. 84(1): 30 DAYS from the date of the order or of the making of the
    # appointment -- here an appointment under a power in the debenture.
    appointed = date(2027, 1, 7)
    due = _add_days(appointed, 30)
    key = _pick(
        {
            "A": due,
            "B": _add_months(appointed, 1),  # read as one calendar month
            "C": _add_days(appointed, 15),   # a 15-day period that does not exist
            "D": _add_days(appointed, 60),   # the s. 77 first extension
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── case sub-questions ───────────────────────────────────────────────────

def cs_i2c6_01_b():
    # Charge created 18 March 2026. Outer limit on ad valorem fees is 120 DAYS
    # from creation (second proviso (b) adds a further 60 to the 60).
    created = date(2026, 3, 18)
    due = _add_days(created, 60 + 60)
    key = _pick(
        {
            "A": _add_days(created, 30),     # as of right
            "B": _add_days(created, 60),     # additional fees
            "C": due,
            "D": _add_months(created, 4),    # 120 days read as four months
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c6_02_b():
    # Loan repaid 25 June 2026; s. 82(1) allows 30 DAYS as of right.
    satisfied = date(2026, 6, 25)
    due = _add_days(satisfied, 30)
    key = _pick(
        {
            "A": due,
            "B": _add_days(satisfied, 60),   # a window s. 82 does not have
            "C": _add_days(satisfied, 300),  # the extended window
            "D": _add_months(satisfied, 6),  # the transitional six months
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c6_03_b():
    # Charge created 6 Oct 2026; the Registrar's notice to the company on the
    # holder's s. 78 application issued 16 Nov 2026. The Registrar's own window
    # is 14 DAYS AFTER THAT NOTICE.
    created = date(2026, 10, 6)
    notice = date(2026, 11, 16)
    due = _add_days(notice, 14)
    key = _pick(
        {
            "A": _add_days(created, 30),     # expiry of the company's window
            "B": due,
            "C": due + timedelta(days=1),    # off-by-one: notice day counted
            "D": _add_days(notice, 30),      # 30 days instead of 14
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}
