"""Verifier for foundation/business-laws/negotiable-instruments-act-1881.json.

Every function recomputes its answer from the parameters stated in the stem and
then maps the computed value onto an option key. No answer key is copied.

Four families of computable question live in this chapter.

1. MATURITY of a note or bill (ss. 21 to 25). Three steps, always in this order:
     (i)  find the day the instrument is EXPRESSED to be payable —
          `_add_months` for a period in months (s. 23: corresponding day of the
          later month; where there is none, the last day of that month) and
          `_add_days` for a period in days (s. 24: the trigger day is excluded).
          Section 21 decides what the clock starts from — the date of the
          instrument for "after date", the date of ACCEPTANCE for "after sight"
          on a bill.
     (ii) add the three days of grace (s. 22), which apply to every instrument
          not payable on demand, at sight or on presentment.
     (iii) test THAT date under s. 25 and, if it is a public holiday, step BACK
          to the next preceding business day.

2. The s. 138 CLOCK. Proviso (b) runs 30 days from the day the payee RECEIVED
   the information of dishonour; proviso (c) runs 15 days from the day the
   drawer RECEIVED the demand notice; the cause of action arises on the day
   after that 15-day period expires; and s. 142(1)(b) allows one month from
   the date the cause of action arises.

3. INTEREST. s. 79 — a rate specified on the instrument runs at that rate from
   the DATE OF THE INSTRUMENT until realisation. s. 80 — no rate specified,
   so 18% per annum from the date the money OUGHT TO HAVE BEEN PAID. The
   stems state the periods in whole months, so the arithmetic is
   principal * rate * months / 12.

4. PART PAYMENT under s. 56. A writing transferring only part of the amount due
   is invalid for negotiation; where the amount has been partly paid, a note of
   that fact lets the instrument be negotiated for the RESIDUE.

DAY-COUNTING CONVENTION (stated in the chapter and flagged in the review
queue): a period expressed in DAYS is counted from and EXCLUDING the trigger
date, so day 1 is the day after — which is what s. 24 says for maturity and
which this module applies to the s. 138 periods by analogy, matching the
convention the sibling Foundation chapters use. A period expressed in MONTHS
ends on the CORRESPONDING date of the later month, and where there is no
corresponding date, on the last day of that month (s. 23), again applied to
s. 142(1)(b) by analogy.

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta

DAYS_OF_GRACE = 3
STATUTORY_INTEREST_RATE = 0.18          # s. 80


def _add_days(d: date, n: int) -> date:
    """A period of n days counted from (and excluding) the trigger date."""
    return d + timedelta(days=n)


def _add_months(d: date, n: int) -> date:
    """s. 23: the corresponding day of the later month, else its last day."""
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _grace(expressed_payable: date) -> date:
    """s. 22: at maturity on the third day after the day expressed to be payable."""
    return expressed_payable + timedelta(days=DAYS_OF_GRACE)


def _preceding_business_day(d: date, holidays) -> date:
    """s. 25: a maturity on a public holiday moves BACK, Sundays included."""
    while d.weekday() == 6 or (d.month, d.day) in holidays:
        d -= timedelta(days=1)
    return d


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


# ---------------------------------------------------------------------------
# q-f2c7-029 — s. 56: an instrument partly paid may be negotiated for the
# RESIDUE once a note of the part payment is endorsed on it.
# ---------------------------------------------------------------------------
def q_f2c7_029():
    face = 800000
    part_paid = 300000

    residue = face - part_paid                       # 8,00,000 - 3,00,000

    options = {
        "A": face,                                   # ignores the part payment
        "B": residue,
        "C": part_paid,                              # the sum already paid
        "D": 0,                                      # negotiation thought barred
    }
    return {"answer": _pick(options, residue), "computed": residue}


# ---------------------------------------------------------------------------
# q-f2c7-037 — ss. 22 and 23: three months after 30 November 2026. February
# has no 30th, so the period ends on the LAST DAY of February; then grace.
# ---------------------------------------------------------------------------
def q_f2c7_037():
    drawn = date(2026, 11, 30)
    months = 3

    expressed = _add_months(drawn, months)           # 28 February 2027
    due = _grace(expressed)                          # 3 March 2027

    # the distractor that rolls a missing 30 February forward into March
    rolled_forward = date(2027, 2, 28) + timedelta(days=30 - 28)

    options = {
        "A": expressed,                              # grace forgotten
        "B": due,
        "C": expressed + timedelta(days=DAYS_OF_GRACE - 1),   # grace miscounted
        "D": _grace(rolled_forward),                 # s. 23 misread
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ---------------------------------------------------------------------------
# q-f2c7-038 — ss. 22 and 24: 100 days after 3 August 2026, the day of the date
# being excluded, then three days of grace.
# ---------------------------------------------------------------------------
def q_f2c7_038():
    drawn = date(2026, 8, 3)
    days = 100

    expressed = _add_days(drawn, days)               # 11 November 2026
    due = _grace(expressed)                          # 14 November 2026

    inclusive_count = _add_days(drawn, days - 1)     # counts 3 August as day 1

    options = {
        "A": expressed,                              # grace forgotten
        "B": _grace(inclusive_count),                # s. 24 exclusion ignored
        "C": due,
        "D": None,                                   # "no due date can be fixed"
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ---------------------------------------------------------------------------
# q-f2c7-039 — ss. 21, 22 and 23: "after sight" on a BILL runs from acceptance.
# ---------------------------------------------------------------------------
def q_f2c7_039():
    drawn = date(2026, 1, 5)
    accepted = date(2026, 1, 10)
    months = 2

    expressed = _add_months(accepted, months)        # 10 March 2026
    due = _grace(expressed)                          # 13 March 2026

    from_date_of_bill = _add_months(drawn, months)   # 5 March 2026

    options = {
        "A": from_date_of_bill,                      # wrong start, no grace
        "B": _grace(from_date_of_bill),              # wrong start, with grace
        "C": expressed,                              # right start, no grace
        "D": due,
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ---------------------------------------------------------------------------
# q-f2c7-040 — ss. 22, 23 and 25: maturity lands on 2 October, a notified
# public holiday, so the instrument is due on the next PRECEDING business day.
# ---------------------------------------------------------------------------
def q_f2c7_040():
    drawn = date(2026, 6, 29)
    months = 3
    holidays = {(10, 2)}                             # 2 October, notified

    expressed = _add_months(drawn, months)           # 29 September 2026
    on_grace = _grace(expressed)                     # 2 October 2026
    due = _preceding_business_day(on_grace, holidays)        # 1 October 2026

    options = {
        "A": due,
        "B": on_grace + timedelta(days=1),           # moved forward instead
        "C": on_grace,                               # s. 25 ignored
        "D": expressed,                              # grace forgotten
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ---------------------------------------------------------------------------
# q-f2c7-041 — s. 79: a rate specified on the instrument runs at that rate
# from the DATE OF THE INSTRUMENT until realisation.
# ---------------------------------------------------------------------------
def q_f2c7_041():
    principal = 600000
    specified_rate = 0.12
    months_from_date_of_instrument = 15              # 1 Jun 2026 to 1 Sep 2027
    tenor_months = 12

    interest = round(principal * specified_rate * months_from_date_of_instrument / 12)

    options = {
        "A": round(principal * specified_rate * tenor_months / 12),   # tenor only
        "B": interest,
        "C": round(principal * STATUTORY_INTEREST_RATE
                   * months_from_date_of_instrument / 12),            # s. 80 rate
        "D": round(principal * specified_rate
                   * (months_from_date_of_instrument - tenor_months) / 12),
    }
    return {"answer": _pick(options, interest), "computed": interest}


# ---------------------------------------------------------------------------
# q-f2c7-042 — s. 80: no rate specified, so 18% per annum from the date the
# money OUGHT TO HAVE BEEN PAID.
# ---------------------------------------------------------------------------
def q_f2c7_042():
    principal = 450000
    months_from_due_date = 8

    interest = round(principal * STATUTORY_INTEREST_RATE * months_from_due_date / 12)

    options = {
        "A": round(principal * STATUTORY_INTEREST_RATE * 12 / 12),    # a full year
        "B": round(principal * (STATUTORY_INTEREST_RATE / 2)
                   * months_from_due_date / 12),                      # half rate
        "C": interest,
        "D": 0,                                      # "no rate, so no interest"
    }
    return {"answer": _pick(options, interest), "computed": interest}


# ---------------------------------------------------------------------------
# cs-f2c7-03-b — s. 138 proviso (b): 30 days from and excluding the day the
# PAYEE received the information of dishonour.
# ---------------------------------------------------------------------------
def cs_f2c7_03_b():
    presented = date(2026, 6, 24)
    payee_informed = date(2026, 6, 27)
    drawer_received_notice = date(2026, 7, 6)
    notice_window_days = 30

    last_day = _add_days(payee_informed, notice_window_days)    # 27 July 2026

    options = {
        "A": _add_days(presented, notice_window_days),          # from presentment
        "B": last_day,
        "C": _add_days(payee_informed, notice_window_days - 1),  # trigger counted
        "D": _add_days(drawer_received_notice, notice_window_days),  # wrong clock
    }
    return {"answer": _pick(options, last_day), "computed": last_day.isoformat()}


# ---------------------------------------------------------------------------
# cs-f2c7-03-c — s. 138 proviso (c) with s. 142(1)(b): 15 days from and
# excluding the drawer's receipt of the notice; the cause of action arises the
# day after that period expires; the complaint follows within one month of it.
# ---------------------------------------------------------------------------
def cs_f2c7_03_c():
    payee_informed = date(2026, 6, 27)
    drawer_received_notice = date(2026, 7, 6)
    pay_window_days = 15
    notice_window_days = 30
    complaint_window_months = 1

    last_day_to_pay = _add_days(drawer_received_notice, pay_window_days)  # 21 Jul
    cause_of_action = _add_days(last_day_to_pay, 1)                       # 22 Jul
    last_day_to_complain = _add_months(cause_of_action, complaint_window_months)

    options = {
        "A": _add_months(last_day_to_pay, complaint_window_months),
        "B": _add_months(drawer_received_notice, complaint_window_months),
        "C": _add_days(payee_informed, notice_window_days),   # the notice deadline
        "D": last_day_to_complain,
    }
    return {
        "answer": _pick(options, last_day_to_complain),
        "computed": last_day_to_complain.isoformat(),
    }
