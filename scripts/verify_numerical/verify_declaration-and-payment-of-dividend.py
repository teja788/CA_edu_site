"""Verifier for intermediate/corporate-and-other-laws/declaration-and-payment-of-dividend.json.

Every function recomputes its answer from the stem's parameters and then maps
the computed value to an option key. Nothing is copied from the answer key.

Two families of numerical appear in this chapter, so two sets of primitives do
all the work:

  MONEY AND RATES — exact rational arithmetic with fractions.Fraction, so that
  one-tenth caps, fifteen-per-cent floors, three-year averages and simple
  interest for a part of a year never drift on binary floats.

      _avg(rates)             the Rule 3(1) / s. 123(3) proviso average of the
                              three immediately preceding years' rates
      _one_tenth(cap, res)    Rule 3(2): 1/10 x (paid-up capital + free reserves)
      _floor_headroom(...)    Rule 3(4): reserves - 15% of paid-up capital, i.e.
                              the most that may be drawn without breaching the
                              floor. NOTE the different bases — condition (2) is
                              measured on capital PLUS free reserves, condition
                              (4) on paid-up capital ALONE.
      _simple_interest(...)   principal x rate x days / 365

  DATES — datetime.date, with a period expressed in DAYS counted from (and
  excluding) the trigger date, so day 1 is the next day.

      _add_days(d, n)         5 days from 12 Aug -> 17 Aug

Which clock starts from which event is a legal question, not a coding one, and
it is where the marks are:

  s. 123(4)   deposit in a separate scheduled-bank account within 5 DAYS
              of the date of DECLARATION
  s. 127      pay, or post the warrant, within 30 DAYS of the date of
              DECLARATION; the default, and the 18% simple interest, run only
              from the EXPIRY of those 30 days
  s. 124(1)   transfer the unpaid or unclaimed balance to the Unpaid Dividend
              Account within 7 DAYS of the EXPIRY of the 30-day period — never
              7 days from the declaration
  s. 124(2)   website statement within 90 DAYS of the date of THAT TRANSFER
  s. 124(3)   12% per annum from the date of the DEFAULT in transferring
  ss. 124(5)/(6)  money and shares to the IEPF 7 YEARS from the date of THAT
              TRANSFER

Rate ceilings:

  Rule 3(1)   final dividend out of accumulated profits, current profits being
              inadequate or absent -> rate <= average of the three preceding
              years' rates, with the one-tenth cap, the fifteen-per-cent floor
              and the current-year-loss set-off attached
  s. 123(3)   interim dividend where there is a LOSS up to the end of the
              quarter immediately preceding declaration -> rate <= the same
              three-year average, but with NO draw cap and NO reserve floor

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

from datetime import date, timedelta
from fractions import Fraction

CRORE = 1_00_00_000
LAKH = 1_00_000


def _add_days(d: date, n: int) -> date:
    """A period of n days counted from (and excluding) the trigger date."""
    return d + timedelta(days=n)


def _avg(rates) -> Fraction:
    """Average of the rates at which dividend was declared, as a Fraction."""
    return Fraction(sum(Fraction(r) for r in rates), len(rates))


def _pct(rate: Fraction, base: int) -> Fraction:
    """`rate` per cent of `base`."""
    return Fraction(rate, 100) * base


def _one_tenth(paid_up: int, free_reserves: int) -> Fraction:
    """Rule 3(2) — one-tenth of paid-up share capital PLUS free reserves."""
    return Fraction(paid_up + free_reserves, 10)


def _floor_headroom(paid_up: int, free_reserves: int) -> Fraction:
    """Rule 3(4) — the most drawable while leaving 15% of PAID-UP CAPITAL."""
    return free_reserves - Fraction(15, 100) * paid_up


def _simple_interest(principal: int, rate_pct, days: int) -> Fraction:
    """Simple interest for `days` on a 365-day year."""
    return Fraction(principal) * Fraction(rate_pct, 100) * Fraction(days, 365)


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


def _money(v: Fraction) -> str:
    """Render an exact Fraction of rupees for the runner's reviewer output."""
    if v.denominator == 1:
        return f"Rs {int(v):,}"
    return f"Rs {float(v):,.2f}"


# ── Rule 3 · the three ceilings, taken one at a time ─────────────────────

def q_i2c8_011():
    # Rule 3(1): rate <= average of the three immediately preceding years'
    # rates. Declared 12%, 9% and 6%.
    rates = [12, 9, 6]
    cap = _avg(rates)
    key = _pick(
        {
            "A": cap,
            "B": Fraction(max(rates)),          # highest instead of average
            "C": Fraction(min(rates)),          # lowest instead of average
            "D": Fraction(sum(rates)),          # sum, averaging step omitted
        },
        cap,
    )
    return {"answer": key, "computed": f"{cap} per cent"}


def q_i2c8_012():
    # Rule 3(2): 1/10 of (paid-up share capital + free reserves).
    paid_up, reserves = 6 * CRORE, 4 * CRORE
    cap = _one_tenth(paid_up, reserves)
    key = _pick(
        {
            "A": Fraction(paid_up, 10),           # capital only
            "B": Fraction(reserves, 10),          # reserves only
            "C": Fraction(15, 100) * paid_up,     # the 15% floor base
            "D": cap,
        },
        cap,
    )
    return {"answer": key, "computed": _money(cap)}


def q_i2c8_013():
    # Rule 3(2) and 3(4) together: capital Rs 20 cr, free reserves Rs 4 cr.
    # The 15% floor bites before the one-tenth cap does.
    paid_up, reserves = 20 * CRORE, 4 * CRORE
    one_tenth = _one_tenth(paid_up, reserves)
    headroom = _floor_headroom(paid_up, reserves)
    max_draw = min(one_tenth, headroom)
    key = _pick(
        {
            "A": one_tenth,                       # one-tenth cap alone
            "B": max_draw,
            "C": Fraction(reserves),              # the whole of the reserves
            "D": Fraction(15, 100) * paid_up,     # the floor itself
        },
        max_draw,
    )
    return {"answer": key, "computed": _money(max_draw)}


def q_i2c8_014():
    # All of Rule 3 at once: capital Rs 9 cr, free reserves Rs 5 cr, current
    # year loss Rs 40 lakh, preceding rates 14 / 11 / 8 per cent.
    paid_up, reserves, loss = 9 * CRORE, 5 * CRORE, 40 * LAKH
    rates = [14, 11, 8]
    rate_cap = _pct(_avg(rates), paid_up)                       # condition (1)
    draw_cap = min(_one_tenth(paid_up, reserves),               # condition (2)
                   _floor_headroom(paid_up, reserves))          # condition (4)
    after_set_off = draw_cap - loss                             # condition (3)
    max_dividend = min(rate_cap, after_set_off)
    key = _pick(
        {
            "A": _one_tenth(paid_up, reserves),   # the draw cap, stopping there
            "B": after_set_off,                   # draw cap less the loss only
            "C": max_dividend,
            "D": _pct(Fraction(max(rates)), paid_up),   # highest rate, not average
        },
        max_dividend,
    )
    return {"answer": key, "computed": _money(max_dividend)}


def q_i2c8_015():
    # Proviso to s. 123(3): a loss up to the end of the quarter immediately
    # preceding declaration caps the INTERIM rate at the three-year average.
    paid_up = 3 * CRORE
    rates = [18, 15, 9]
    cap = _pct(_avg(rates), paid_up)
    key = _pick(
        {
            "A": cap,
            "B": _pct(Fraction(max(rates)), paid_up),   # highest rate
            "C": Fraction(paid_up, 10),                 # Rule 3 draw cap imported
            "D": _pct(Fraction(min(rates)), paid_up),   # lowest rate
        },
        cap,
    )
    return {"answer": key, "computed": _money(cap)}


# ── The clocks · ss. 123(4), 127 and 124(1) ──────────────────────────────

def q_i2c8_021():
    # s. 123(4): deposit within 5 DAYS of the date of declaration (12 Aug 2026).
    declared = date(2026, 8, 12)
    due = _add_days(declared, 5)
    key = _pick(
        {
            "A": _add_days(declared, 4),      # declaration day counted as day one
            "B": due,
            "C": _add_days(declared, 7),      # the s. 124(1) period, wrongly based
            "D": _add_days(declared, 30),     # the s. 127 payment deadline
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c8_023():
    # s. 127: pay or post the warrant within 30 DAYS of declaration
    # (24 Aug 2026). August has 31 days, so this is NOT one calendar month.
    declared = date(2026, 8, 24)
    due = _add_days(declared, 30)
    key = _pick(
        {
            "A": due,
            "B": date(2026, 9, 24),           # read as one calendar month
            "C": _add_days(declared, 5),      # the s. 123(4) deposit deadline
            "D": _add_days(due, 7),           # the s. 124(1) transfer deadline
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


def q_i2c8_026():
    # s. 124(1): 7 DAYS from the EXPIRY of the 30-day payment period, the
    # dividend having been declared on 6 Nov 2026.
    declared = date(2026, 11, 6)
    expiry = _add_days(declared, 30)
    due = _add_days(expiry, 7)
    key = _pick(
        {
            "A": _add_days(declared, 7),      # 7 days from declaration
            "B": expiry,                      # the end of the 30 days itself
            "C": due,
            "D": _add_days(expiry, 30),       # a further 30 days
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── Interest · s. 124(3) at 12% and s. 127 at 18% ────────────────────────

def q_i2c8_029():
    # s. 124(3): 12% per annum from the date of the DEFAULT in transferring,
    # on Rs 15,00,000, from 20 Sep 2026 until the transfer on 13 Feb 2027.
    principal = 15 * LAKH
    due, transferred = date(2026, 9, 20), date(2027, 2, 13)
    days = (transferred - due).days
    interest = _simple_interest(principal, 12, days)
    key = _pick(
        {
            "A": _simple_interest(principal, 18, days),    # the s. 127 rate
            "B": interest,
            "C": _simple_interest(principal, 12, 365),     # a full year
            "D": _simple_interest(principal, 12, days // 2),  # half the period
        },
        interest,
    )
    return {"answer": key, "computed": f"{days} days -> {_money(interest)}"}


def q_i2c8_033():
    # s. 127: 18% simple interest on Rs 36,50,000. Declared 10 Jul 2026, so
    # the 30 days expire on 9 Aug 2026; paid 21 Oct 2026.
    principal = 36 * LAKH + 50000
    declared, paid = date(2026, 7, 10), date(2026, 10, 21)
    expiry = _add_days(declared, 30)
    days = (paid - expiry).days
    interest = _simple_interest(principal, 18, days)
    key = _pick(
        {
            "A": _simple_interest(principal, 12, days),           # the s. 124(3) rate
            "B": interest,
            "C": _simple_interest(principal, 18, 365),            # a full year
            "D": _simple_interest(principal, 18, (paid - declared).days),  # from declaration
        },
        interest,
    )
    return {"answer": key, "computed": f"{days} days -> {_money(interest)}"}


# ── s. 51 · dividend on the amount paid-up ───────────────────────────────

def q_i2c8_036():
    # Articles authorise s. 51 payment; 20,000 shares of Rs 10, Rs 7 paid up,
    # dividend declared at 12 per cent.
    shares, face, paid_per_share, rate = 20000, 10, 7, 12
    paid_up = shares * paid_per_share
    dividend = _pct(Fraction(rate), paid_up)
    key = _pick(
        {
            "A": _pct(Fraction(rate), shares * face),          # nominal-value basis
            "B": _pct(Fraction(10), paid_up),                  # 10% instead of 12%
            "C": _pct(Fraction(rate), (shares // 2) * paid_per_share),  # holding halved
            "D": dividend,
        },
        dividend,
    )
    return {"answer": key, "computed": _money(dividend)}


# ── Case set 1 · Rule 3 on a balance sheet ───────────────────────────────

def cs_i2c8_01_b():
    # Rule 3(2): capital Rs 12 cr, free reserves Rs 7 cr.
    paid_up, reserves = 12 * CRORE, 7 * CRORE
    cap = _one_tenth(paid_up, reserves)
    key = _pick(
        {
            "A": Fraction(paid_up, 10),            # capital only
            "B": Fraction(reserves, 10),           # reserves only
            "C": cap,
            "D": _floor_headroom(paid_up, reserves),   # headroom to the 15% floor
        },
        cap,
    )
    return {"answer": key, "computed": _money(cap)}


def cs_i2c8_01_c():
    # All conditions: preceding rates 15 / 12 / 9, current-year profit
    # Rs 18,00,000, no losses.
    paid_up, reserves, profit = 12 * CRORE, 7 * CRORE, 18 * LAKH
    rates = [15, 12, 9]
    rate_cap = _pct(_avg(rates), paid_up)
    draw_cap = min(_one_tenth(paid_up, reserves),
                   _floor_headroom(paid_up, reserves))
    max_dividend = min(rate_cap, profit + draw_cap)
    key = _pick(
        {
            "A": max_dividend,
            "B": _one_tenth(paid_up, reserves),           # the draw cap
            "C": Fraction(15, 100) * paid_up,             # the 15% floor base
            "D": profit + _one_tenth(paid_up, reserves),  # draw cap plus profit
        },
        max_dividend,
    )
    return {"answer": key, "computed": _money(max_dividend)}


# ── Case set 2 · the declaration-to-IEPF timeline ────────────────────────

def cs_i2c8_02_b():
    # s. 124(1): declared 24 Aug 2026; 30 days expire 23 Sep 2026; then 7 days.
    declared = date(2026, 8, 24)
    expiry = _add_days(declared, 30)
    due = _add_days(expiry, 7)
    key = _pick(
        {
            "A": _add_days(declared, 7),      # 7 days from declaration
            "B": due,
            "C": expiry,                      # the end of the 30 days itself
            "D": _add_days(declared, 5),      # the s. 123(4) deposit deadline
        },
        due,
    )
    return {"answer": key, "computed": due.isoformat()}


# ── Case set 3 · s. 127 interest ─────────────────────────────────────────

def cs_i2c8_03_c():
    # s. 127: Rs 50,00,000 declared 10 Jul 2026, paid 21 Oct 2026; the default
    # runs from the expiry of the 30 days on 9 Aug 2026.
    principal = 50 * LAKH
    declared, paid = date(2026, 7, 10), date(2026, 10, 21)
    expiry = _add_days(declared, 30)
    days = (paid - expiry).days
    interest = _simple_interest(principal, 18, days)
    key = _pick(
        {
            "A": interest,
            "B": _simple_interest(principal, 12, days),     # the s. 124(3) rate
            "C": _simple_interest(principal, 18, 365),      # a full year
            "D": _simple_interest(principal, 18, 365) / 2,  # half a year
        },
        interest,
    )
    return {"answer": key, "computed": f"{days} days -> {_money(interest)}"}
