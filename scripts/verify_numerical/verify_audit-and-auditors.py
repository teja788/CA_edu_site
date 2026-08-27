"""Verifier for intermediate/corporate-and-other-laws/audit-and-auditors.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

Chapter X of the Companies Act 2013 is a chapter of clocks, counts and rupee
thresholds, so four primitives do all the work:

  _add_days(d, n)     a period expressed in DAYS is counted from the trigger
                      date, exclusive of the trigger day (day 1 is the next
                      day). 30 days from 12 May -> 11 June.
  _add_months(d, n)   a period expressed in MONTHS lands on the same day of
                      the later month (3 months from 10 Jul -> 10 Oct), with a
                      clamp for short months.
  Fraction            every rupee amount and share count is exact; no floats
                      are used anywhere in this module.
  plain arithmetic    audit-ceiling counts and rotation term arithmetic.

Which primitive applies is a legal question, not a coding one:

  s. 139(1)     notice of appointment to the Registrar within 15 DAYS of the
                MEETING (not of the consent, the audit committee's
                recommendation or the engagement letter)      -> _add_days
  s. 139(5)     subsequent auditor of a government company appointed by the
                C&AG within 180 DAYS from the COMMENCEMENT OF
                THE FINANCIAL YEAR                            -> _add_days
  s. 139(6)     first auditor of a non-government company: Board within 30
                DAYS of REGISTRATION; on failure, members within 90 DAYS of
                the Board's information                        -> _add_days
  s. 139(7)     first auditor of a government company: C&AG within 60 DAYS of
                REGISTRATION                                   -> _add_days
  s. 139(8)(i)  casual vacancy caused by RESIGNATION: members' approval in a
                general meeting convened within 3 MONTHS of the BOARD'S
                RECOMMENDATION (not of the resignation)        -> _add_months
  s. 139(2)     an audit firm's two terms of five consecutive years, then a
                5-YEAR cooling-off in that company             -> year count
  s. 140(1)     special resolution within 60 DAYS of RECEIPT of the Central
                Government's approval (Rule 7)                 -> _add_days
  s. 140(2)     auditor's resignation statement within 30 DAYS of the DATE OF
                RESIGNATION                                    -> _add_days
  s. 141(3)(d)  relative's securities capped at 1,00,000 rupees of FACE value;
                indebtedness capped at 5,00,000 rupees         -> Fraction
  s. 141(3)(g)  20-company ceiling, EXCLUDING one-person, dormant and small
                companies and private companies with paid-up
                capital below 100 crore rupees                 -> plain count
  s. 143(12)    fraud of 1 crore rupees or more: 2 DAYS to the Board or audit
                committee, 45 DAYS for their reply, 15 DAYS from the reply or
                from the EXPIRY of the 45 days to the Central
                Government (Rule 13)                           -> _add_days
  s. 148(6)     cost audit report furnished to the Central Government within
                30 DAYS of the company's RECEIPT of it          -> _add_days

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from fractions import Fraction

LAKH = Fraction(100_000)
CRORE = Fraction(10_000_000)


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


# ── s. 139(1) · notice of the appointment to the Registrar ───────────────

def q_i2c10_005():
    # AGM held 25 Aug 2026; notice within 15 DAYS of the MEETING. The audit
    # committee's recommendation (30 Jul) and the engagement letter (2 Sep)
    # are noise: neither starts the clock.
    meeting = date(2026, 8, 25)
    due = _add_days(meeting, 15)
    key = _pick(
        {
            "A": _add_days(meeting, 30),      # the s. 139(6)/(8) 30-day window
            "B": due,
            "C": _add_days(meeting, 14),      # off-by-one
            "D": _add_months(meeting, 1),     # read as one calendar month
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 139(6) and 139(7) · the first auditor ─────────────────────────────

def q_i2c10_006():
    # non-government company registered 12 May 2026; Board has 30 DAYS from
    # the date of REGISTRATION.
    registered = date(2026, 5, 12)
    due = _add_days(registered, 30)
    key = _pick(
        {
            "A": due,
            "B": _add_days(registered, 90),   # the members' fallback window
            "C": _add_days(registered, 60),   # the government-company window
            "D": _add_months(registered, 3),  # read as three calendar months
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c10_008():
    # GOVERNMENT company registered 3 Aug 2026; the C&AG has 60 DAYS from the
    # date of registration (s. 139(7)).
    registered = date(2026, 8, 3)
    due = _add_days(registered, 60)
    key = _pick(
        {
            "A": _add_days(registered, 30),   # the Board's fallback window
            "B": _add_days(registered, 90),   # a s. 139(6) period
            "C": due,
            "D": _add_days(registered, 180),  # the s. 139(5) period
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c10_01_b():
    # Board failed and informed the members on 20 Jun 2026; the members appoint
    # at an EGM within 90 DAYS of that information (s. 139(6)).
    informed = date(2026, 6, 20)
    due = _add_days(informed, 90)
    key = _pick(
        {
            "A": _add_days(informed, 30),     # the Board's own window
            "B": _add_days(informed, 60),     # the government-company members' window
            "C": due,
            "D": _add_months(informed, 3),    # read as three calendar months
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 139(5) · subsequent auditor of a government company ───────────────

def q_i2c10_010():
    # financial year commences 1 Apr 2026; the C&AG has 180 DAYS from the
    # COMMENCEMENT OF THE FINANCIAL YEAR.
    fy_start = date(2026, 4, 1)
    due = _add_days(fy_start, 180)
    key = _pick(
        {
            "A": _add_days(fy_start, 60),     # the s. 139(7) first-auditor window
            "B": _add_days(fy_start, 90),     # a s. 139(6) period
            "C": _add_months(fy_start, 6),    # read as six calendar months
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 139(8)(i) · casual vacancy caused by resignation ──────────────────

def q_i2c10_012():
    # resignation 2 Jul 2026, Board's RECOMMENDATION 10 Jul 2026, Board's
    # appointment 20 Jul 2026. The members' approval runs 3 MONTHS from the
    # Board's recommendation.
    recommended = date(2026, 7, 10)
    due = _add_months(recommended, 3)
    key = _pick(
        {
            "A": _add_days(recommended, 30),   # the Board's window to fill it
            "B": due,
            "C": _add_days(recommended, 90),   # 90 days instead of three months
            "D": _add_months(recommended, 6),  # six months
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 139(2) · rotation tenure and cooling-off ──────────────────────────

def q_i2c10_016():
    # audit firm appointed at the 2016 AGM and re-appointed at the 2021 AGM;
    # two terms of five consecutive years end at the conclusion of the AGM held
    # in 2016 + 5 + 5 = 2026. A five-year cooling-off then runs in that company.
    first_term_from = 2016
    term_years = 5
    terms_for_a_firm = 2
    completed = first_term_from + term_years * terms_for_a_firm   # 2026
    cooling_off = 5
    earliest = completed + cooling_off                            # 2031
    key = _pick(
        {
            "A": completed + 3,                       # the transition window, misused
            "B": earliest,
            "C": completed + term_years * terms_for_a_firm,  # tenure used as cooling-off
            "D": completed + 1,                       # bar treated as one year
        },
        earliest,
    )
    return {"answer": key, "computed": earliest}


# ── s. 140 · removal and resignation ─────────────────────────────────────

def q_i2c10_019():
    # Board resolution 18 May 2026; Central Government approval RECEIVED
    # 8 Jun 2026. The special resolution must be passed within 60 DAYS of
    # receipt of the approval (Rule 7), not of the Board resolution.
    approval = date(2026, 6, 8)
    due = _add_days(approval, 60)
    key = _pick(
        {
            "A": _add_days(approval, 30),     # the window for the APPLICATION
            "B": _add_months(approval, 2),    # read as two calendar months
            "C": due,
            "D": _add_days(approval, 90),     # 90 days
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c10_021():
    # resignation 18 Sep 2026; the auditor's statement goes to the company and
    # the Registrar within 30 DAYS of the DATE OF RESIGNATION.
    resigned = date(2026, 9, 18)
    due = _add_days(resigned, 30)
    key = _pick(
        {
            "A": _add_days(resigned, 15),     # the s. 139(1) notice period
            "B": _add_days(resigned, 45),     # the s. 143(12) reply period
            "C": _add_days(resigned, 7),      # a week
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 141(3) · the disqualification thresholds ──────────────────────────

def q_i2c10_028():
    # 20-company ceiling. Excluded from the reckoning: one-person companies,
    # dormant companies, small companies, and private companies with paid-up
    # share capital below 100 crore rupees.
    ceiling = 20
    unlisted_public = 9
    listed = 4
    one_person, dormant, small = 3, 2, 5          # all excluded
    private_paid_up = [Fraction(140) * CRORE] + [Fraction(60) * CRORE] * 5
    private_counted = sum(1 for cap in private_paid_up if cap >= Fraction(100) * CRORE)
    counted = unlisted_public + listed + private_counted          # 14
    headroom = ceiling - counted                                  # 6
    key = _pick(
        {
            "A": max(0, ceiling - (unlisted_public + listed + one_person
                                   + dormant + small + len(private_paid_up))),  # counts all 29 -> 0
            "B": ceiling - (unlisted_public + listed + len(private_paid_up)),    # counts all privates
            "C": headroom,
            "D": ceiling - unlisted_public,                                      # counts public only
        },
        headroom,
    )
    return {"answer": key, "computed": headroom}


def q_i2c10_030():
    # a relative may hold securities of FACE value up to 1,00,000 rupees.
    # 1,200 shares of 100 rupees face value = 1,20,000 rupees.
    face_value_per_share = Fraction(100)
    held = 1200
    limit = 1 * LAKH
    excess_value = face_value_per_share * held - limit            # 20,000
    shares_to_go = excess_value / face_value_per_share            # 200
    key = _pick(
        {
            "A": shares_to_go,
            "B": Fraction(held),                                  # dispose of everything
            "C": excess_value / Fraction(1000),                   # face value read as 1,000
            "D": Fraction(held) - shares_to_go,                   # subtraction inverted
        },
        shares_to_go,
    )
    return {"answer": key, "computed": int(shares_to_go)}


def cs_i2c10_02_c():
    # indebtedness to the company, its subsidiary, its holding or associate
    # company is capped at 5,00,000 rupees in total; 4,80,000 is outstanding.
    limit = 5 * LAKH
    outstanding = Fraction(480_000)
    headroom = limit - outstanding                                # 20,000
    key = _pick(
        {
            "A": limit,                                           # limit read as fresh headroom
            "B": 1 * LAKH,                                        # the relative/guarantee limit
            "C": Fraction(0),                                     # treated as already disqualified
            "D": headroom,
        },
        headroom,
    )
    return {"answer": key, "computed": int(headroom)}


# ── s. 143(12) · the fraud-reporting clock ───────────────────────────────

def cs_i2c10_03_b():
    # knowledge 4 May 2026; fraud of 1.6 crore rupees, so 1 crore or more and
    # the Central Government is the ultimate recipient. Report to the audit
    # committee on the last permitted day (2 DAYS), reply sought within
    # 45 DAYS, and — no reply having come — 15 DAYS from the EXPIRY of that
    # period to forward the report.
    knowledge = date(2026, 5, 4)
    amount = Fraction(16, 10) * CRORE
    assert amount >= 1 * CRORE, "below the threshold this route does not apply"
    to_committee = _add_days(knowledge, 2)
    reply_expiry = _add_days(to_committee, 45)
    due = _add_days(reply_expiry, 15)
    key = _pick(
        {
            "A": _add_days(to_committee, 15),   # 15 days without waiting out the 45
            "B": reply_expiry,                  # the reply deadline itself
            "C": _add_days(reply_expiry, 30),   # 30 days instead of 15
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── s. 148(6) · filing the cost audit report ─────────────────────────────

def q_i2c10_038():
    # report RECEIVED by the company 12 Aug 2026; furnished to the Central
    # Government within 30 DAYS of receipt.
    received = date(2026, 8, 12)
    due = _add_days(received, 30)
    key = _pick(
        {
            "A": _add_days(received, 15),     # 15 days
            "B": _add_days(received, 60),     # 60 days
            "C": _add_months(received, 1),    # read as one calendar month
            "D": due,
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def cs_i2c10_03_d():
    # report RECEIVED by the company 5 Oct 2026; same 30-DAY clock.
    received = date(2026, 10, 5)
    due = _add_days(received, 30)
    key = _pick(
        {
            "A": _add_days(received, 15),     # 15 days
            "B": _add_days(received, 60),     # 60 days
            "C": due,
            "D": _add_days(received, 180),    # the cost auditor's own rules-level period
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}
