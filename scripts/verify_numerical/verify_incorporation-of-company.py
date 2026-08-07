"""Verifier for intermediate/corporate-and-other-laws/incorporation-of-company.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

The numericals in this chapter are timeline arithmetic and member counts, so
two primitives do all the work:

  _add_days(d, n)     a period expressed in DAYS is counted from the trigger
                      date, exclusive of the trigger day (day 1 is the next
                      day). 20 days from 14 Sep -> 4 Oct.
  _add_months(d, n)   a period expressed in MONTHS lands on the same day of
                      the later month (6 months from 12 Jun -> 12 Dec), with a
                      clamp for short months.

Which primitive applies is a legal question, not a coding one:

  s. 3A       six MONTHS of continued short-handed trading   -> _add_months
  s. 3(1)(a)  seven members minimum, public company          -> plain count
  s. 4(5)(i)  name reserved 20 DAYS (new company) / 60 DAYS
              (existing company changing its name), in both
              cases from the date of APPROVAL, not application -> _add_days
  s. 4(5)(ii) change of name within three MONTHS of the
              Registrar's direction                           -> _add_months
  s. 10A(1)(a) declaration within 180 DAYS of the date of
              INCORPORATION (not of payment by subscribers)   -> _add_days
  s. 12(2)    verification of registered office within 30 DAYS
              of incorporation                                -> _add_days
  s. 12(6)    confirmation filed with the Registrar within 60
              DAYS of the date of the RD's CONFIRMATION       -> _add_days
  s. 16(2)    notice to the Registrar within 15 DAYS of the
              date of the CHANGE of name                      -> _add_days

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


# ── s. 3A · the six-month grace, and the member count ────────────────────

def q_i2c2_005():
    # public company; membership fell to five on 12 June 2026.
    # s. 3A allows six MONTHS of continued trading before liability attaches.
    fell = date(2026, 6, 12)
    expiry = _add_months(fell, 6)
    key = _pick(
        {
            "A": _add_months(fell, 3),      # three months — wrong period
            "B": _add_days(fell, 180),      # 180 days instead of six months
            "C": expiry,
            "D": _add_months(fell, 12),     # twelve months
        },
        expiry,
    )
    return {"answer": key, "computed": expiry.isoformat()}


def q_i2c2_006():
    # eleven members, six transfer out to existing members -> five remain.
    # s. 3(1)(a) floor for a public company is seven.
    remaining = 11 - 6
    shortfall = max(0, 7 - remaining)
    key = _pick({"A": 1, "B": 6, "C": shortfall, "D": 0}, shortfall)
    return {"answer": key, "computed": shortfall}


# ── s. 4(5) · name reservation ───────────────────────────────────────────

def q_i2c2_018():
    # proposed NEW company: 20 days from the date of APPROVAL (14 Sep 2026),
    # not from the date of application (8 Sep 2026).
    applied, approved = date(2026, 9, 8), date(2026, 9, 14)
    valid_to = _add_days(approved, 20)
    key = _pick(
        {
            "A": _add_days(applied, 20),     # counted from the application
            "B": valid_to,
            "C": _add_days(approved, 60),    # the existing-company period
            "D": _add_months(approved, 1),   # read as one calendar month
        },
        valid_to,
    )
    return {"answer": key, "computed": valid_to.isoformat()}


def q_i2c2_019():
    # EXISTING company changing its name: 60 days from approval (20 Jan 2027).
    approved = date(2027, 1, 20)
    valid_to = _add_days(approved, 60)
    key = _pick(
        {
            "A": _add_days(approved, 20),    # the new-company period
            "B": _add_months(approved, 2),   # read as two calendar months
            "C": valid_to,
            "D": _add_months(approved, 6),   # six months
        },
        valid_to,
    )
    return {"answer": key, "computed": valid_to.isoformat()}


# ── s. 10A · declaration for commencement of business ────────────────────

def q_i2c2_029():
    # incorporated 20 April 2026; 180 DAYS from the date of incorporation.
    incorporated = date(2026, 4, 20)
    due = _add_days(incorporated, 180)
    key = _pick(
        {
            "A": _add_days(incorporated, 90),      # 90 days
            "B": _add_months(incorporated, 6),     # six calendar months
            "C": due,
            "D": _add_months(incorporated, 12),    # one year
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 12 · registered office ────────────────────────────────────────────

def q_i2c2_032():
    # incorporated 3 August 2026; verification within 30 DAYS (s. 12(2)).
    incorporated = date(2026, 8, 3)
    due = _add_days(incorporated, 30)
    key = _pick(
        {
            "A": _add_days(incorporated, 15),    # the pre-amendment 15 days
            "B": due - timedelta(days=1),        # off-by-one
            "C": _add_days(incorporated, 180),   # the s. 10A clock
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c2_03_a():
    # RD confirmation communicated 4 May 2026; the company files it with the
    # Registrar within 60 DAYS of the date of confirmation (s. 12(6)).
    confirmed = date(2026, 5, 4)
    due = _add_days(confirmed, 60)
    key = _pick(
        {
            "A": _add_days(confirmed, 30),     # the RD's own 30-day clock
            "B": due,
            "C": _add_months(confirmed, 2),    # read as two calendar months
            "D": _add_days(confirmed, 90),     # 90 days
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── ss. 4(5)(ii) and 16(2) · name-change clocks ──────────────────────────

def cs_i2c2_01_c():
    # Registrar's direction 6 July 2026; change of name within three MONTHS
    # after an ordinary resolution (s. 4(5)(ii)(b)(i)).
    direction = date(2026, 7, 6)
    due = _add_months(direction, 3)
    key = _pick(
        {
            "A": _add_days(direction, 15),     # the s. 16(2) notice period
            "B": due,
            "C": _add_months(direction, 6),    # the pre-amendment six months
            "D": _add_months(direction, 2),    # two months
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c2_03_b():
    # name changed 18 August 2026; notice to the Registrar within 15 DAYS of
    # the date of the CHANGE (s. 16(2)).
    changed = date(2026, 8, 18)
    due = _add_days(changed, 15)
    key = _pick(
        {
            "A": _add_days(changed, 30),       # the s. 12(4) period
            "B": due - timedelta(days=1),      # off-by-one
            "C": _add_months(changed, 3),      # the period to MAKE the change
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}
