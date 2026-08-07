"""Verifier for foundation/accounting/bills-of-exchange-and-promissory-notes.json (P1 Ch 6).

Every numerical question is recomputed from the stem's own parameters and the
computed value is then mapped to an option key. No answer key is copied.

Two families of function live here.

DUE DATES (q-f1c6-011 .. 020) implement the Negotiable Instruments Act 1881
mechanically with `datetime.date` arithmetic, in the statutory order:

  1. `expressed_day()` — the day the instrument is *expressed* to be payable.
     * after date  -> counted from the date of the bill;
       after sight -> counted from the date of ACCEPTANCE (s. 23).
     * months (s. 23): the corresponding day of the later month; where that
       month has no corresponding day, the LAST day of that month. The period
       never spills over into the following month.
     * days (s. 24): actual calendar days, EXCLUDING the day of the date.
  2. `add_grace()` — three days of grace for a time instrument (s. 22); an
     instrument payable on demand / at sight / on presentment gets none.
  3. `apply_holiday()` — s. 25: a maturity date falling on a public holiday
     (Sundays plus the days notified in NOTIFIED_HOLIDAYS) moves to the next
     PRECEDING business day. An emergency holiday, unknown when the bill was
     drawn, moves the date to the next SUCCEEDING business day instead.

     Saturdays are treated as ordinary business days, which is the convention
     the chapter states explicitly; only Sundays and notified holidays move a
     date. This assumption is flagged for human review.

MONEY (q-f1c6-021 .. 032) recomputes discount, proceeds, renewal interest,
rebate, insolvency dividends and accommodation-bill shares from first
principles. Money is held in whole rupees (every figure in the bank is exact).
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta

GRACE_DAYS = 3

# Days notified as public holidays for the purposes of these questions, as
# stated in the stems and in notes §5. (month, day) pairs, recurring yearly.
NOTIFIED_HOLIDAYS = {(1, 26), (8, 15), (10, 2)}


# --------------------------------------------------------------- date engine


def is_public_holiday(d: date) -> bool:
    """s. 25 — Sundays plus the days notified by the Central Government."""
    return d.weekday() == 6 or (d.month, d.day) in NOTIFIED_HOLIDAYS


def add_months(d: date, months: int) -> date:
    """s. 23 — corresponding day; if the month has no such day, its last day."""
    m = d.month - 1 + months
    year = d.year + m // 12
    month = m % 12 + 1
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


def expressed_day(start: date, *, months: int = 0, days: int = 0) -> date:
    """The day the instrument is expressed to be payable.

    `start` is the date of the bill for an after-date bill and the date of
    acceptance for an after-sight bill — the caller makes that choice, which is
    exactly the distinction the questions test.
    """
    if months and days:
        raise ValueError("a tenor is stated either in months or in days, not both")
    if months:
        return add_months(start, months)
    # s. 24: exclude the day of the date, so day 1 of the count is the next day.
    return start + timedelta(days=days)


def add_grace(d: date, *, on_demand: bool = False) -> date:
    """s. 22 — three days of grace, but none on a demand/sight instrument."""
    return d if on_demand else d + timedelta(days=GRACE_DAYS)


def apply_holiday(d: date, *, emergency: date | None = None) -> date:
    """s. 25 and the emergency-holiday convention.

    A notified public holiday (or Sunday) pulls maturity BACK to the preceding
    business day. An emergency holiday declared for the maturity date pushes it
    FORWARD to the next succeeding business day.
    """
    if emergency is not None and d == emergency:
        d += timedelta(days=1)
        while is_public_holiday(d) or d == emergency:
            d += timedelta(days=1)
        return d
    while is_public_holiday(d):
        d -= timedelta(days=1)
    return d


def due_date(
    start: date,
    *,
    months: int = 0,
    days: int = 0,
    on_demand: bool = False,
    emergency: date | None = None,
) -> date:
    """The three statutory steps, in order: expressed day, grace, holiday test."""
    d = expressed_day(start, months=months, days=days)
    d = add_grace(d, on_demand=on_demand)
    return apply_holiday(d, emergency=emergency)


def date_answer(computed: date, options: dict[str, date]) -> dict:
    """Map a computed ISO date onto the option key that carries it."""
    matches = [k for k, v in options.items() if v == computed]
    if len(matches) != 1:
        raise AssertionError(f"{computed.isoformat()} matches option keys {matches}")
    return {"answer": matches[0], "computed": computed.isoformat()}


def money_answer(computed, options: dict[str, object]) -> dict:
    matches = [k for k, v in options.items() if v == computed]
    if len(matches) != 1:
        raise AssertionError(f"{computed!r} matches option keys {matches}")
    return {"answer": matches[0], "computed": computed}


# ------------------------------------------------------- §4 plain due dates


def q_f1c6_011():
    # Bill dated 3 May 2026, three months after date, no holiday intervening.
    computed = due_date(date(2026, 5, 3), months=3)
    return date_answer(
        computed,
        {
            "A": date(2026, 8, 3),   # expressed day, grace omitted
            "B": date(2026, 8, 6),
            "C": date(2026, 7, 6),   # only two months counted
            "D": date(2026, 8, 5),   # two days of grace
        },
    )


def q_f1c6_012():
    # Dated 30 Nov 2026, three months after date. February 2027 has no 30th, so
    # s. 23 ends the period on 28 Feb 2027; grace then gives 3 March 2027.
    computed = due_date(date(2026, 11, 30), months=3)
    assert expressed_day(date(2026, 11, 30), months=3) == date(2027, 2, 28)
    return date_answer(
        computed,
        {
            "A": date(2027, 2, 28),  # grace omitted
            "B": date(2027, 3, 2),   # '30 Feb' rolled into March, grace omitted
            "C": date(2027, 3, 5),   # '30 Feb' rolled into March, then grace
            "D": date(2027, 3, 3),
        },
    )


def q_f1c6_013():
    # Dated 12 May 2026, 60 days after date (s. 24 excludes the day of date).
    computed = due_date(date(2026, 5, 12), days=60)
    assert expressed_day(date(2026, 5, 12), days=60) == date(2026, 7, 11)
    return date_answer(
        computed,
        {
            "A": date(2026, 7, 14),
            "B": date(2026, 7, 11),  # grace omitted
            "C": date(2026, 7, 15),  # 60 days read as two months
            "D": date(2026, 7, 13),  # counted the day of the date
        },
    )


def q_f1c6_014():
    # Dated 1 June 2026, ACCEPTED 8 June 2026, two months after sight: the
    # clock starts at acceptance (s. 23).
    computed = due_date(date(2026, 6, 8), months=2)
    return date_answer(
        computed,
        {
            "A": due_date(date(2026, 6, 1), months=2),   # ran from the bill's date
            "B": date(2026, 8, 8),                       # grace omitted
            "C": date(2026, 8, 11),
            "D": date(2026, 8, 1),                       # both slips together
        },
    )


def q_f1c6_020():
    # Promissory note payable ON DEMAND, made 4 May 2026, presented 20 May 2026.
    # No grace (s. 22); maturity is presentment itself.
    presented = date(2026, 5, 20)
    computed = due_date(presented, on_demand=True)
    return date_answer(
        computed,
        {
            "A": presented + timedelta(days=GRACE_DAYS),          # grace added
            "B": date(2026, 5, 4) + timedelta(days=GRACE_DAYS),   # grace from making
            "C": date(2026, 5, 4),                                # date of making
            "D": date(2026, 5, 20),
        },
    )


# ------------------------------------------------------- §5 the holiday rules


def q_f1c6_015():
    # Dated 12 May 2026 + 3 months + grace = 15 Aug 2026, Independence Day.
    computed = due_date(date(2026, 5, 12), months=3)
    ungraced = add_grace(expressed_day(date(2026, 5, 12), months=3))
    assert ungraced == date(2026, 8, 15) and is_public_holiday(ungraced)
    # The 'moved forward' distractor, computed the same way an emergency
    # holiday would be handled, lands on 17 August (16 August is a Sunday).
    forward = apply_holiday(ungraced, emergency=ungraced)
    return date_answer(
        computed,
        {
            "A": date(2026, 8, 15),  # holiday ignored
            "B": date(2026, 8, 12),  # grace omitted
            "C": forward,            # moved forward instead of back
            "D": date(2026, 8, 14),
        },
    )


def q_f1c6_016():
    # Dated 29 June 2026 + 3 months + grace = 2 Oct 2026, Gandhi Jayanti.
    computed = due_date(date(2026, 6, 29), months=3)
    ungraced = add_grace(expressed_day(date(2026, 6, 29), months=3))
    assert ungraced == date(2026, 10, 2) and is_public_holiday(ungraced)
    return date_answer(
        computed,
        {
            "A": date(2026, 10, 2),                      # holiday ignored
            "B": date(2026, 10, 1),
            "C": apply_holiday(ungraced, emergency=ungraced),  # moved forward
            "D": date(2026, 9, 29),                      # grace omitted
        },
    )


def q_f1c6_017():
    # Dated 1 June 2026 + 4 months + grace = 4 Oct 2026, a Sunday.
    computed = due_date(date(2026, 6, 1), months=4)
    ungraced = add_grace(expressed_day(date(2026, 6, 1), months=4))
    assert ungraced == date(2026, 10, 4) and ungraced.weekday() == 6
    return date_answer(
        computed,
        {
            "A": date(2026, 10, 3),
            "B": date(2026, 10, 4),                      # Sunday ignored
            "C": apply_holiday(ungraced, emergency=ungraced),  # moved forward
            "D": date(2026, 10, 1),                      # grace omitted
        },
    )


def q_f1c6_018():
    # Dated 23 Oct 2026 + 3 months + grace = 26 Jan 2027, Republic Day.
    computed = due_date(date(2026, 10, 23), months=3)
    ungraced = add_grace(expressed_day(date(2026, 10, 23), months=3))
    assert ungraced == date(2027, 1, 26) and is_public_holiday(ungraced)
    return date_answer(
        computed,
        {
            "A": date(2027, 1, 26),                      # holiday ignored
            "B": apply_holiday(ungraced, emergency=ungraced),  # moved forward
            "C": date(2027, 1, 25),
            "D": date(2027, 1, 23),                      # grace omitted
        },
    )


def q_f1c6_019():
    # Ordinary maturity 6 Aug 2026 (a Thursday); an EMERGENCY holiday is
    # declared for that day, so maturity moves to the next business day.
    maturity = date(2026, 8, 6)
    assert not is_public_holiday(maturity)
    computed = apply_holiday(maturity, emergency=maturity)
    return date_answer(
        computed,
        {
            "A": apply_holiday(maturity - timedelta(days=1)),  # s. 25 misapplied
            "B": date(2026, 8, 7),
            "C": date(2026, 8, 6),                             # holiday ignored
            "D": date(2026, 8, 10),                            # jumped to Monday
        },
    )


# --------------------------------------------------------- §8 discounting


def discount(face: int, rate_pct: float, months: float) -> float:
    return face * rate_pct / 100 * months / 12


def q_f1c6_021():
    # ₹60,000 bill dated 3 May 2026 for 3 months -> due 6 Aug 2026; discounted
    # 6 June 2026, so exactly two months are unexpired.
    face, rate = 60_000, 12
    due = due_date(date(2026, 5, 3), months=3)
    discounted_on = date(2026, 6, 6)
    unexpired_months = round((due - discounted_on).days / 30.4375 * 2) / 2
    assert due == date(2026, 8, 6) and unexpired_months == 2
    computed = round(discount(face, rate, unexpired_months))
    return money_answer(
        computed,
        {
            "A": 1_200,
            "B": round(discount(face, rate, 3)),   # whole tenor discounted
            "C": round(discount(face, rate, 1)),   # one month only
            "D": round(discount(face, rate, 12)),  # rate applied for a year
        },
    )


def q_f1c6_022():
    face, rate, unexpired = 60_000, 12, 2
    computed = face - round(discount(face, rate, unexpired))
    return money_answer(
        computed,
        {
            "A": face - round(discount(face, rate, 3)),  # whole tenor
            "B": face,                                    # no discount deducted
            "C": 58_800,
            "D": face - round(discount(face, rate, 1)),   # one month only
        },
    )


def q_f1c6_032():
    # A four-month bill of ₹48,000 discounted exactly three months before
    # maturity at 10% p.a.: the unexpired period, not the tenor, is charged.
    face, rate, unexpired, tenor = 48_000, 10, 3, 4
    computed = face - round(discount(face, rate, unexpired))
    return money_answer(
        computed,
        {
            "A": face,                                        # no discount
            "B": face - round(discount(face, rate, tenor)),    # whole tenor
            "C": face - round(discount(face, rate, 1)),        # one month only
            "D": 46_800,
        },
    )


# ------------------------------------------------- §13 accommodation bills


def q_f1c6_023():
    face, rate, tenor = 90_000, 12, 3
    computed = face - round(discount(face, rate, tenor))
    return money_answer(
        computed,
        {
            "A": face,
            "B": face - round(discount(face, rate, 2)),
            "C": face - round(discount(face, rate, 4)),
            "D": 87_300,
        },
    )


def q_f1c6_024():
    # ₹90,000 / 12% / 3 months, proceeds shared Anita : Bharat = 2 : 1.
    face, rate, tenor = 90_000, 12, 3
    disc = round(discount(face, rate, tenor))
    proceeds = face - disc
    bharat_ratio = 1 / 3
    computed = round(proceeds * bharat_ratio)
    return money_answer(
        computed,
        {
            "A": round(face * bharat_ratio),       # share of FACE value
            "B": 29_100,
            "C": round(proceeds * 2 / 3),          # the other party's share
            "D": round(proceeds / 2),              # split equally
        },
    )


def q_f1c6_025():
    face, rate, tenor = 90_000, 12, 3
    disc = round(discount(face, rate, tenor))
    computed = round(disc * 1 / 3)
    return money_answer(
        computed,
        {
            "A": 900,
            "B": round(disc * 2 / 3),  # the other party's share
            "C": disc,                 # whole discount loaded on one party
            "D": 0,                    # 'nil' option
        },
    )


def q_f1c6_031():
    # ₹1,20,000 / 15% / 4 months, proceeds shared A : B = 3 : 1.
    face, rate, tenor = 1_20_000, 15, 4
    disc = round(discount(face, rate, tenor))
    proceeds = face - disc
    b_ratio = 1 / 4
    computed = round(proceeds * b_ratio)
    assert disc == 6_000 and proceeds == 1_14_000
    return money_answer(
        computed,
        {
            "A": round(face * b_ratio),            # share of FACE value
            "B": 28_500,
            "C": round(proceeds * 3 / 4),          # the other party's share
            "D": round(face * b_ratio) - disc,     # whole discount off his share
        },
    )


# ------------------------------------------------------------- §10 renewal


def q_f1c6_026():
    # ₹36,000 bill dishonoured, ₹400 noting charges, ₹16,400 cash received,
    # balance renewed for three months at 12% p.a.
    face, noting, cash, rate, extension = 36_000, 400, 16_400, 12, 3
    owing = face + noting
    renewed = owing - cash
    computed = round(renewed * rate / 100 * extension / 12)
    assert renewed == 20_000
    return money_answer(
        computed,
        {
            "A": round(face * rate / 100 * extension / 12),      # on face value
            "B": round(owing * rate / 100 * extension / 12),     # on amount owing
            "C": 600,
            "D": round(renewed * rate / 100),                    # full year
        },
    )


def q_f1c6_027():
    face, noting, cash, rate, extension = 36_000, 400, 16_400, 12, 3
    renewed = face + noting - cash
    interest = round(renewed * rate / 100 * extension / 12)
    computed = renewed + interest
    # Cross-check the acceptor's account closes: debits == credits.
    assert (face + noting) + interest == cash + computed
    return money_answer(
        computed,
        {
            "A": renewed,                                                  # interest omitted
            "B": renewed + round(face * rate / 100 * extension / 12),       # interest on face
            "C": renewed + round(renewed * rate / 100 * 1 / 12),            # one month
            "D": 20_600,
        },
    )


# ------------------------------------ §9 dishonour, §11 rebate, §12 insolvency


def q_f1c6_028():
    # Discounted bill dishonoured: the bank recovers face value + noting.
    face, noting, proceeds = 60_000, 500, 58_800
    computed = face + noting
    return money_answer(
        computed,
        {
            "A": face,                 # noting charges omitted
            "B": 60_500,
            "C": face - noting,        # noting charges deducted
            "D": proceeds + noting,    # proceeds used as the base
        },
    )


def q_f1c6_029():
    # ₹50,000 bill due 6 Aug 2026, retired 6 July 2026, rebate at 12% p.a.
    face, rate = 50_000, 12
    due, retired_on = date(2026, 8, 6), date(2026, 7, 6)
    unexpired_months = round((due - retired_on).days / 30.4375)
    assert unexpired_months == 1
    computed = round(face * rate / 100 * unexpired_months / 12)
    return money_answer(
        computed,
        {
            "A": 500,
            "B": round(face * rate / 100 * 3 / 12),   # three months
            "C": round(face * rate / 100),            # a full year
            "D": round(face * 6 / 100 * 1 / 12),      # rate halved to 6%
        },
    )


def q_f1c6_030():
    # ₹25,000 bill + ₹300 noting; dividend 40 paise in the rupee.
    face, noting, paise = 25_000, 300, 40
    owing = face + noting
    received = round(owing * paise / 100)
    computed = owing - received
    return money_answer(
        computed,
        {
            "A": face - round(face * paise / 100),  # noting charges ignored
            "B": received,                          # the recovery, not the write-off
            "C": 15_180,
            "D": round(face * paise / 100),         # 40% of face value
        },
    )
