"""Verifier for intermediate/corporate-and-other-laws/management-and-administration.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

Chapter 7 is almost entirely day-counting, member-counting and threshold
arithmetic, so four primitives do all the work:

  _add_days(d, n)     a period expressed in DAYS is counted from the trigger
                      date, exclusive of the trigger day (day 1 is the next
                      day). 30 days from 12 May -> 11 Jun.
  _add_months(d, n)   a period expressed in MONTHS lands on the same day of the
                      later month (6 months from 31 Mar -> 30 Sep, clamped for
                      short months).
  _clear_days_meeting(served, n)
                      the earliest date of a meeting where n CLEAR days' notice
                      is required: BOTH the day of service and the day of the
                      meeting are excluded, so the meeting falls on
                      served + n + 1.
  _deemed_service_by_post(posted)
                      rule 35(6) of the Companies (Incorporation) Rules 2014
                      deems a notice of a MEETING served at the expiration of
                      48 hours after posting, i.e. posted + 2 days. Every stem
                      that relies on this states the rule expressly.

Which primitive applies is a legal question, not a coding one:

  s. 89(2)    declaration by the beneficial owner within 30 DAYS of
              acquiring the beneficial interest                  -> _add_days
  s. 92(4)    annual return within 60 DAYS from the date the AGM
              IS HELD, or from the last date on which it SHOULD
              have been held                                     -> _add_days
  s. 96(1)    first AGM within 9 MONTHS of the close of the FIRST
              financial year; every other AGM within 6 MONTHS of
              the close of the financial year; and never more
              than 15 MONTHS after the previous AGM — the two
              limits apply together and the EARLIER governs;
              the Registrar may extend a non-first AGM by up to
              3 MONTHS                                           -> _add_months + min
  s. 100(4)   Board proceeds to call within 21 DAYS of RECEIPT of
              the requisition, for a meeting not later than
              45 DAYS from RECEIPT; failing which the
              requisitionists meet within 3 MONTHS from the date
              of the REQUISITION                                 -> _add_days / _add_months
  s. 101(1)   not less than 21 CLEAR days' notice                -> _clear_days_meeting
  s. 103(1)   public company quorum 5 / 15 / 30 at 1,000 / 5,000
              members; private company 2                         -> slab lookup
  s. 109(1)(a) poll on 1/10th of the total voting power OR shares
              on which >= Rs 5,00,000 is paid up — alternatives,
              so the LOWER requirement governs                   -> Fraction
  s. 114(2)(c) special resolution needs votes in favour >= 3 x
              votes against                                      -> Fraction

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


def _deemed_service_by_post(posted: date) -> date:
    """Rule 35(6): a notice of a meeting is served 48 hours after posting."""
    return _add_days(posted, 2)


def _clear_days_meeting(served: date, n: int) -> date:
    """Earliest meeting date on n CLEAR days' notice.

    Clear days exclude the day of service and the day of the meeting, so
    n whole days must lie between them: served + n + 1.
    """
    return _add_days(served, n + 1)


def _public_quorum(members: int) -> int:
    """s. 103(1)(a) — members personally present required in a public company."""
    if members <= 1000:
        return 5
    if members <= 5000:
        return 15
    return 30


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


# ── s. 89 · declaration of beneficial interest ───────────────────────────

def q_i2c7_004():
    # beneficial interest acquired 12 May 2026; s. 89(2) allows 30 DAYS from
    # the date of acquiring the beneficial interest.
    acquired = date(2026, 5, 12)
    due = _add_days(acquired, 30)
    key = _pick(
        {
            "A": _add_days(acquired, 15),      # fifteen days
            "B": due,
            "C": _add_months(acquired, 1),     # read as one calendar month
            "D": _add_days(acquired, 90),      # ninety days
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 92(4) · filing the annual return ──────────────────────────────────

def q_i2c7_013():
    # AGM actually held 18 Sep 2026; 60 DAYS from the date the AGM IS HELD.
    fy_close = date(2026, 3, 31)
    agm_held = date(2026, 9, 18)
    due = _add_days(agm_held, 60)
    key = _pick(
        {
            "A": _add_days(fy_close, 60),                       # from the year-end
            "B": _add_days(agm_held, 30),                       # thirty days
            "C": _add_days(_add_months(fy_close, 6), 60),       # the no-AGM start point
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 96 · annual general meeting deadlines ─────────────────────────────

def q_i2c7_014():
    # incorporated 5 Aug 2025, first financial year closed 31 Mar 2026.
    # FIRST AGM: 9 MONTHS from the close of the first financial year.
    incorporated = date(2025, 8, 5)
    fy_close = date(2026, 3, 31)
    due = _add_months(fy_close, 9)
    key = _pick(
        {
            "A": due,
            "B": _add_months(fy_close, 6),        # the subsequent-AGM period
            "C": _add_months(incorporated, 9),    # counted from incorporation
            "D": _add_months(fy_close, 12),       # twelve months
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c7_015():
    # financial year closed 31 Mar 2026; previous AGM held 2 May 2025.
    # Both limits apply: 6 MONTHS from the year-end and a 15-MONTH gap.
    fy_close = date(2026, 3, 31)
    previous_agm = date(2025, 5, 2)
    six_month_limit = _add_months(fy_close, 6)
    gap_limit = _add_months(previous_agm, 15)
    due = min(six_month_limit, gap_limit)
    key = _pick(
        {
            "A": six_month_limit,                  # six-month rule alone
            "B": _add_months(previous_agm, 18),    # eighteen-month gap
            "C": due,
            "D": _add_months(fy_close, 9),         # the first-AGM period
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 100(4) · the requisition clocks ───────────────────────────────────

def q_i2c7_021():
    # requisition dated 2 Jun 2026, received 4 Jun 2026. The meeting must be
    # held not later than 45 DAYS from the date of RECEIPT.
    requisition = date(2026, 6, 2)
    received = date(2026, 6, 4)
    due = _add_days(received, 45)
    key = _pick(
        {
            "A": _add_days(requisition, 45),    # counted from the requisition
            "B": _add_days(received, 21),       # the Board's 21-day clock
            "C": due,
            "D": _add_months(requisition, 3),   # the requisitionists' 3 months
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 101(1) · twenty-one clear days, with deemed service by post ───────

def q_i2c7_023():
    # notice POSTED 1 Sep 2026. Rule 35(6) deems service 48 hours after
    # posting; s. 101(1) then requires 21 CLEAR days.
    posted = date(2026, 9, 1)
    served = _deemed_service_by_post(posted)
    earliest = _clear_days_meeting(served, 21)
    key = _pick(
        {
            "A": _add_days(posted, 21),              # 21 plain days from posting
            "B": _clear_days_meeting(posted, 21),    # clear days, no deemed service
            "C": _add_days(served, 21),              # deemed service, but not clear
            "D": earliest,
        },
        earliest,
    )
    return {"answer": key, "computed": earliest.isoformat()}


# ── s. 103(1) · quorum ───────────────────────────────────────────────────

def q_i2c7_026():
    # public company, 4,200 members on the date of the meeting.
    members = 4200
    quorum = _public_quorum(members)
    key = _pick({"A": quorum, "B": 5, "C": 30, "D": 2}, quorum)
    return {"answer": key, "computed": quorum}


# ── s. 109(1)(a) · demand for a poll ─────────────────────────────────────

def q_i2c7_033():
    # 40,00,000 equity shares of Rs 10 each, fully paid, one vote per share.
    # Limb 1: 1/10th of the total voting power.
    # Limb 2: shares on which an aggregate of Rs 5,00,000 is paid up.
    # The limbs are alternatives, so the LOWER requirement governs.
    total_shares = 4000000
    paid_up_per_share = Fraction(10)
    limb_voting_power = int(Fraction(total_shares, 10))
    limb_paid_up_value = int(Fraction(500000) / paid_up_per_share)
    required = min(limb_voting_power, limb_paid_up_value)
    key = _pick(
        {
            "A": limb_voting_power,                            # voting-power limb alone
            "B": limb_voting_power + limb_paid_up_value,       # the limbs added
            "C": required,
            "D": 500000,                                       # rupees read as shares
        },
        required,
    )
    return {"answer": key, "computed": required}


# ── Case 1 · AGM extension, and the annual-return clock ──────────────────

def cs_i2c7_01_a():
    # financial year closed 31 Mar 2026; previous AGM held 20 Sep 2025.
    # Unextended due date = EARLIER of (year-end + 6 months) and
    # (previous AGM + 15 months); the Registrar may add up to 3 MONTHS.
    fy_close = date(2026, 3, 31)
    previous_agm = date(2025, 9, 20)
    base = min(_add_months(fy_close, 6), _add_months(previous_agm, 15))
    extended = _add_months(base, 3)
    key = _pick(
        {
            "A": extended,
            "B": date(2026, 12, 31),                 # the calendar year-end
            "C": _add_months(previous_agm, 18),      # gap limb extended instead
            "D": base,                               # no extension applied
        },
        extended,
    )
    return {"answer": key, "computed": extended.isoformat()}


def cs_i2c7_01_b():
    # AGM held and concluded 15 Dec 2026; s. 92(4) allows 60 DAYS from the
    # date on which the AGM IS HELD.
    fy_close = date(2026, 3, 31)
    agm_held = date(2026, 12, 15)
    due = _add_days(agm_held, 60)
    key = _pick(
        {
            "A": _add_days(agm_held, 30),                    # thirty days
            "B": due,
            "C": _add_months(agm_held, 2),                   # two calendar months
            "D": _add_days(_add_months(fy_close, 6), 60),    # the no-AGM start point
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── Case 2 · the section 100(4) clocks, from two different events ────────

def cs_i2c7_02_a():
    # requisition dated 5 May 2026, received 8 May 2026. The Board must
    # PROCEED TO CALL within 21 DAYS of RECEIPT.
    requisition = date(2026, 5, 5)
    received = date(2026, 5, 8)
    due = _add_days(received, 21)
    key = _pick(
        {
            "A": _add_days(requisition, 21),    # counted from the requisition
            "B": due,
            "C": _add_days(received, 45),       # the 45-day outer date
            "D": _add_months(requisition, 3),   # the requisitionists' 3 months
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c7_02_b():
    # the requisitionists' own meeting: 3 MONTHS from the date of the
    # REQUISITION (not of its receipt, and not from the expiry of 21 days).
    requisition = date(2026, 5, 5)
    received = date(2026, 5, 8)
    due = _add_months(requisition, 3)
    key = _pick(
        {
            "A": _add_months(received, 3),                        # from receipt
            "B": _add_months(_add_days(received, 21), 3),         # from the 21-day expiry
            "C": due,
            "D": _add_days(received, 45),                         # the 45-day date
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── Case 3 · quorum and the special-resolution majority ──────────────────

def cs_i2c7_03_a():
    # public company, 6,200 members on the date of the meeting.
    members = 6200
    quorum = _public_quorum(members)
    key = _pick({"A": 5, "B": 15, "C": quorum, "D": 2}, quorum)
    return {"answer": key, "computed": quorum}


def cs_i2c7_03_b():
    # s. 114(2)(c): votes in favour must be NOT LESS THAN THREE TIMES the
    # votes cast against. 2,00,000 votes were cast against.
    votes_against = 200000
    required_in_favour = int(Fraction(3, 1) * votes_against)
    key = _pick(
        {
            "A": votes_against + 1,                              # simple majority
            "B": required_in_favour,
            "C": int(Fraction(2, 1) * votes_against),            # two-to-one
            "D": int(Fraction(4, 1) * votes_against),            # four-to-one
        },
        required_in_favour,
    )
    return {"answer": key, "computed": required_in_favour}
