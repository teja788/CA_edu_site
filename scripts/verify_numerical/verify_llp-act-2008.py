"""Verifier for BOTH banks whose chapterSlug is "llp-act-2008":

    foundation/business-laws/llp-act-2008.json                  -> q_f2c5_* / cs_f2c5_*
    intermediate/corporate-and-other-laws/llp-act-2008.json     -> q_i2c12_* / cs_i2c12_*

run.py resolves the verify module from the chapterSlug alone, so the two
chapters necessarily share this file. The Foundation functions come first and
are unchanged; the Intermediate functions are in a clearly marked block at the
end and reuse the same helpers and threshold constants.

Every function recomputes its answer from the parameters stated in the stem and
then maps the computed value onto an option key. No answer key is copied.

The LLP Act carries few figures of its own, so the computable questions in this
chapter are of four families, and in each of them the arithmetic is trivial
while the LEGAL step that selects the arithmetic is the thing being examined:

1. Statutory day-counts. _add_days(d, n) counts a period expressed in DAYS
   from, and excluding, the trigger date, so day 1 is the day after the
   trigger — the same convention the Sale of Goods chapter uses for s. 24
   sale-or-return periods. _add_months(d, n) adds calendar months and clamps
   to the last valid day of the target month, so six months from 31 March is
   30 September. The dates that matter:
     - s. 34(2) Statement of Account and Solvency PREPARED within 6 months of
       the end of the financial year, and FILED within a further 30 days
       (s. 34(3) with r. 24, LLP Rules 2009);
     - s. 35 annual return within 60 days of the CLOSURE of the financial year;
     - s. 25 changes in partners: 15 days partner -> LLP, 30 days LLP ->
       Registrar;
     - s. 58(2) intimation to the Registrar of Firms or of Companies within
       15 days of the date of registration of a conversion.

2. Penalties and additional fees that run per day. s. 13(4) is ₹500 a day
   SUBJECT TO A MAXIMUM of ₹50,000, so the computation is min(rate * days,
   cap) and the uncapped product is always the trap option. s. 69 charges an
   additional fee of ₹100 for every day of delay, computed from the correct
   due date — and picking the wrong due date is what the distractors model.

3. First Schedule default splits. Clause 1 shares capital, profits and losses
   EQUALLY whatever each partner contributed, so the contribution ratio is
   never the divisor; the distractors are exactly the contribution-ratio
   shares. Section 24(5) pays a former partner the contribution ACTUALLY MADE
   plus his share of accumulated profits NET of accumulated losses at the date
   of cessation, so the two traps are the agreed-but-unpaid contribution and
   the gross profit figure.

4. Threshold tests. Audit is required if turnover exceeds ₹40,00,000 OR
   contribution exceeds ₹25,00,000 (r. 24, LLP Rules 2009), so either limb
   alone decides it; the small-LLP definition in s. 2(1)(ta) is by contrast
   cumulative. Section 6(2) is a threshold in time: only obligations incurred
   after the LLP has carried on business for MORE THAN six months below two
   partners reach the sole partner personally.

Law as on 2026-02-28, after the LLP (Amendment) Act 2021; applicable to the
Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from fractions import Fraction

# Thresholds and rates relied on, all stated once so a reviewer can retest the
# whole module by changing a single line if the law moves.
AUDIT_TURNOVER_LIMIT = 4000000       # r. 24, LLP Rules 2009
AUDIT_CONTRIBUTION_LIMIT = 2500000   # r. 24, LLP Rules 2009
RESIDENCE_DAYS = 120                 # s. 7 Explanation, as amended in 2021
S13_PENALTY_PER_DAY = 500            # s. 13(4)
S13_PENALTY_CAP = 50000              # s. 13(4)
S69_ADDITIONAL_FEE_PER_DAY = 100     # s. 69


def _add_days(d: date, n: int) -> date:
    """A period of n days counted from (and excluding) the trigger date."""
    return d + timedelta(days=n)


def _add_months(d: date, n: int) -> date:
    """n calendar months on, clamped to the last day of the target month."""
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _pick(options, value):
    """Map a computed value to its option key, insisting the match is unique."""
    hits = [key for key, v in options.items() if v == value]
    if len(hits) != 1:
        raise AssertionError(
            f"computed {value!r} matches {len(hits)} option(s) in {options}"
        )
    return hits[0]


# ---------------------------------------------------------------------------
# q-f2c5-009 — s. 13(4): ₹500 for each day of default in complying with s. 13,
# SUBJECT TO a maximum of ₹50,000 for the LLP.
# ---------------------------------------------------------------------------
def q_f2c5_009():
    days_in_default = 132

    uncapped = days_in_default * S13_PENALTY_PER_DAY      # 132 * 500 = 66,000
    payable = min(uncapped, S13_PENALTY_CAP)              # capped at 50,000

    options = {
        "A": uncapped,                                    # cap ignored
        "B": days_in_default * S69_ADDITIONAL_FEE_PER_DAY,  # s. 69 rate misused
        "C": S13_PENALTY_PER_DAY,                         # read as a one-off
        "D": payable,
    }
    return {"answer": _pick(options, payable), "computed": payable}


# ---------------------------------------------------------------------------
# q-f2c5-014 — First Schedule cl. 1: the agreement being silent, the partners
# share profits EQUALLY, whatever each contributed.
# ---------------------------------------------------------------------------
def q_f2c5_014():
    contributions = {"Ashwini": 1500000, "Bharath": 900000, "Chandana": 600000}
    profit = 1890000

    equal_share = profit // len(contributions)            # 18,90,000 / 3
    total_contribution = sum(contributions.values())

    def by_contribution(name):
        return profit * contributions[name] // total_contribution

    options = {
        "A": equal_share,
        "B": by_contribution("Chandana"),                 # contribution ratio
        "C": by_contribution("Ashwini"),                  # wrong partner too
        "D": by_contribution("Bharath"),                  # wrong partner too
    }
    return {"answer": _pick(options, equal_share), "computed": equal_share}


# ---------------------------------------------------------------------------
# q-f2c5-021 — s. 24(5): contribution ACTUALLY MADE plus a share of the
# accumulated profits NET of accumulated losses at the date of cessation, the
# share being equal under First Schedule cl. 1.
# ---------------------------------------------------------------------------
def q_f2c5_021():
    contribution_agreed = 1000000
    contribution_actually_made = 750000
    accumulated_profits = 2200000
    accumulated_losses = 600000
    partners = 4

    net_accumulated = accumulated_profits - accumulated_losses      # 16,00,000
    share_of_net = net_accumulated // partners                      # 4,00,000
    entitlement = contribution_actually_made + share_of_net         # 11,50,000

    options = {
        "A": contribution_agreed + share_of_net,          # agreed, not paid in
        "B": contribution_actually_made                   # gross profits used,
             + accumulated_profits // partners,           # losses not deducted
        "C": entitlement,
        "D": contribution_actually_made,                  # s. 24(5)(b) dropped
    }
    return {"answer": _pick(options, entitlement), "computed": entitlement}


# ---------------------------------------------------------------------------
# q-f2c5-030 — r. 24, LLP Rules 2009: audit is required if turnover exceeds
# ₹40,00,000 OR contribution exceeds ₹25,00,000. Each option asserts an audit
# outcome on these facts; only one of them asserts the outcome the rule
# actually produces.
# ---------------------------------------------------------------------------
def q_f2c5_030():
    turnover = 4260000
    contribution = 1800000

    turnover_limb = turnover > AUDIT_TURNOVER_LIMIT           # True
    contribution_limb = contribution > AUDIT_CONTRIBUTION_LIMIT  # False
    audit_required = turnover_limb or contribution_limb        # True

    # What each option asserts is the audit outcome on these numbers.
    options = {
        "A": False,   # only the contribution limb counts -> no audit
        "B": True,    # either limb alone triggers -> audit
        "C": False,   # both limbs must be exceeded -> no audit
        "D": False,   # audit only on a partners' resolution -> none compulsory
    }
    return {
        "answer": _pick(options, audit_required),
        "computed": (f"turnover>{AUDIT_TURNOVER_LIMIT}={turnover_limb}, "
                     f"contribution>{AUDIT_CONTRIBUTION_LIMIT}="
                     f"{contribution_limb} -> audit={audit_required}"),
    }


# ---------------------------------------------------------------------------
# q-f2c5-031 — s. 35: the annual return goes in within SIXTY DAYS of the
# closure of the financial year.
# ---------------------------------------------------------------------------
def q_f2c5_031():
    financial_year_end = date(2027, 3, 31)

    due = _add_days(financial_year_end, 60)                    # 30 May 2027
    six_months = _add_months(financial_year_end, 6)            # 30 Sept 2027

    options = {
        "A": date(2027, 5, 31),                    # 60 days read as 2 months
        "B": six_months,                           # s. 34(2) preparation date
        "C": _add_days(six_months, 30),            # s. 34(3) filing date
        "D": due,
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ---------------------------------------------------------------------------
# q-f2c5-032 — s. 69: an additional fee of ₹100 for every day of delay,
# measured from the s. 34(3) due date, which is 30 days after the six months
# from the end of the financial year have expired.
# ---------------------------------------------------------------------------
def q_f2c5_032():
    financial_year_end = date(2027, 3, 31)
    filed_on = date(2027, 12, 6)

    six_months_end = _add_months(financial_year_end, 6)        # 30 Sept 2027
    due = _add_days(six_months_end, 30)                        # 30 Oct 2027
    annual_return_due = _add_days(financial_year_end, 60)      # 30 May 2027

    def fee_from(reference: date) -> int:
        delay = (filed_on - reference).days
        return max(delay, 0) * S69_ADDITIONAL_FEE_PER_DAY

    payable = fee_from(due)                                    # 37 * 100

    options = {
        "A": payable,
        "B": fee_from(six_months_end),          # the 30 further days forgotten
        "C": fee_from(annual_return_due),       # the annual return clock used
        "D": S69_ADDITIONAL_FEE_PER_DAY,        # read as a flat fee
    }
    return {"answer": _pick(options, payable),
            "computed": f"{(filed_on - due).days} days late -> {payable}"}


# ---------------------------------------------------------------------------
# cs-f2c5-02-c — s. 6(2): the sole partner answers personally only for the
# obligations incurred after the LLP has carried on business for MORE THAN six
# months while the number of partners was below two.
# ---------------------------------------------------------------------------
def cs_f2c5_02_c():
    cessation = date(2026, 4, 14)                  # the second partner dies
    grace_expires = _add_months(cessation, 6)      # 14 October 2026

    # (period start, period end, obligations incurred in the period)
    ledger = [
        (date(2026, 4, 15), date(2026, 10, 14), 1150000),
        (date(2026, 10, 15), date(2027, 3, 31), 2380000),
    ]

    inside_grace = sum(amt for _, end, amt in ledger if end <= grace_expires)
    after_grace = sum(amt for start, _, amt in ledger if start > grace_expires)
    total = inside_grace + after_grace

    options = {
        "A": total,             # every obligation since the death
        "B": after_grace,       # s. 6(2) as written
        "C": inside_grace,      # the period s. 6(2) leaves with the LLP alone
        "D": 0,                 # s. 28(1) read as an absolute shield
    }
    return {"answer": _pick(options, after_grace), "computed": after_grace}


# ---------------------------------------------------------------------------
# cs-f2c5-03-b — s. 58(2): the converted LLP informs the Registrar of Firms
# within FIFTEEN DAYS of the date of registration.
# ---------------------------------------------------------------------------
def cs_f2c5_03_b():
    registration = date(2026, 8, 20)

    due = _add_days(registration, 15)                  # 4 September 2026

    options = {
        "A": due,
        "B": _add_days(registration, 30),              # the s. 25(2) period
        "C": registration,                             # read as same-day
        "D": _add_days(registration, 14),              # counted inclusively
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ===========================================================================
# CA INTERMEDIATE · Paper 2 · Ch 12 — The Limited Liability Partnership Act,
# 2008.  Bank: intermediate/corporate-and-other-laws/llp-act-2008.json.
#
# Everything below serves the Intermediate bank only. It reuses the helpers
# and the two Rule 24 threshold constants above; nothing above this line was
# altered. Function names carry the i2c12 prefix, so the two chapters cannot
# collide even though run.py resolves this module from the shared chapterSlug.
#
# Which primitive applies is a legal question, not a coding one:
#
#   s. 2(1)(ta)  small LLP: contribution <= Rs 25 lakh AND turnover of the
#                immediately preceding FY <= Rs 40 lakh    -> _small (AND)
#   r. 24        audit compulsory if turnover > Rs 40 lakh OR
#                contribution > Rs 25 lakh                 -> _audit (OR)
#   s. 6(2)      six MONTHS of continued business with a
#                sole partner                              -> _add_months
#   s. 7 Expl.   "resident in India" = stay of not less than
#                120 DAYS during the FINANCIAL YEAR (the
#                2021 test, replacing 182 days during the
#                immediately preceding one year)           -> plain count
#   s. 9         designated-partner vacancy filled within
#                30 DAYS of its arising                    -> _add_days
#   s. 17(1)     name changed within three MONTHS of the
#                Central Government's direction            -> _add_months
#   s. 24(1)     resignation on not less than 30 DAYS
#                notice where the agreement is silent      -> _add_days
#   s. 25(2)(a)  notice to the Registrar within 30 DAYS of
#                a person becoming or ceasing to be partner -> _add_days
#   s. 34(3)/r24 Form 8 within 30 DAYS from the END OF SIX
#                MONTHS of the financial year              -> _add_months then
#                                                             _add_days
#   s. 35(1)     Form 11 within 60 DAYS of the CLOSURE of
#                the financial year                        -> _add_days
#   s. 58(1)     the old Registrar informed within 15 DAYS
#                of registration of the conversion         -> _add_days
#
# Law as on 2026-02-28; Sept 2026 and Jan 2027 attempts. The small-LLP
# ceilings and the r. 24 audit thresholds are rules- and notification-level:
# if either moves, q-i2c12-004, cs-i2c12-03-c and the constants at the top of
# this module must be reworked together with the bank.
# ===========================================================================


def _small_llp(contribution: Fraction, turnover: Fraction) -> str:
    """s. 2(1)(ta): a small LLP only if BOTH ceilings are respected."""
    over_c = contribution > AUDIT_CONTRIBUTION_LIMIT
    over_t = turnover > AUDIT_TURNOVER_LIMIT
    if not over_c and not over_t:
        return "small LLP"
    if over_c and over_t:
        return "not small - both ceilings exceeded"
    if over_t:
        return "not small - turnover ceiling exceeded"
    return "not small - contribution ceiling exceeded"


def _audit_verdict(contribution: Fraction, turnover: Fraction) -> str:
    """r. 24: audit compulsory if EITHER threshold is crossed."""
    over_c = contribution > AUDIT_CONTRIBUTION_LIMIT
    over_t = turnover > AUDIT_TURNOVER_LIMIT
    if not over_c and not over_t:
        return "no audit - neither threshold crossed"
    if over_c and over_t:
        return "audit - both thresholds crossed"
    if over_t:
        return "audit - turnover threshold crossed"
    return "audit - contribution threshold crossed"


def _form8_due(fy_end: date) -> date:
    """s. 34(3) with r. 24: 30 DAYS from the END OF SIX MONTHS of the FY."""
    return _add_days(_add_months(fy_end, 6), 30)


# ---------------------------------------------------------------------------
# q-i2c12-004 — s. 2(1)(ta): contribution Rs 22,00,000 (within Rs 25 lakh) but
# turnover of the immediately preceding FY Rs 46,00,000 (above Rs 40 lakh).
# The limbs are joined by AND, so one breach is fatal.
# ---------------------------------------------------------------------------
def q_i2c12_004():
    contribution, turnover = Fraction(2200000), Fraction(4600000)

    verdict = _small_llp(contribution, turnover)

    options = {
        "A": "small LLP",
        "B": "not small - turnover ceiling exceeded",
        "C": "not small - contribution ceiling exceeded",
        "D": "not small - both ceilings exceeded",
    }
    return {"answer": _pick(options, verdict), "computed": verdict}


# ---------------------------------------------------------------------------
# q-i2c12-009 — s. 6(2): sole partner from 14 May 2026; six MONTHS of
# continued business before personal liability attaches.
# ---------------------------------------------------------------------------
def q_i2c12_009():
    alone_from = date(2026, 5, 14)

    expiry = _add_months(alone_from, 6)                # 14 November 2026

    options = {
        "A": _add_months(alone_from, 3),               # three months
        "B": _add_days(alone_from, 180),               # 180 days, not 6 months
        "C": expiry,
        "D": _add_months(alone_from, 12),              # twelve months
    }
    return {"answer": _pick(options, expiry), "computed": expiry.isoformat()}


# ---------------------------------------------------------------------------
# q-i2c12-012 — s. 7 Explanation: 96 days already spent in India during the
# financial year; the amended test is 120 DAYS during the FINANCIAL YEAR.
# ---------------------------------------------------------------------------
def q_i2c12_012():
    stayed = 96

    shortfall = max(0, RESIDENCE_DAYS - stayed)        # 24

    options = {
        "A": shortfall,
        "B": 182 - stayed,                             # the pre-2021 182 days
        "C": 180 - stayed,                             # a 180-day test that
        "D": 0,                                        # does not exist
    }
    return {"answer": _pick(options, shortfall), "computed": shortfall}


# ---------------------------------------------------------------------------
# cs-i2c12-02-a — s. 7 Explanation again, two days short of the 120.
# ---------------------------------------------------------------------------
def cs_i2c12_02_a():
    stayed = 118

    shortfall = max(0, RESIDENCE_DAYS - stayed)        # 2

    options = {
        "A": shortfall,
        "B": 180 - stayed,                             # a 180-day test
        "C": 182 - stayed,                             # the pre-2021 test
        "D": 0,                                        # "already resident"
    }
    return {"answer": _pick(options, shortfall), "computed": shortfall}


# ---------------------------------------------------------------------------
# q-i2c12-015 — s. 9: vacancy arising 22 June 2026, filled within 30 DAYS.
# ---------------------------------------------------------------------------
def q_i2c12_015():
    vacancy = date(2026, 6, 22)

    due = _add_days(vacancy, 30)                       # 22 July 2026

    options = {
        "A": _add_days(vacancy, 15),                   # the s. 25(1) period
        "B": due,
        "C": _add_days(vacancy, 60),                   # the s. 35 period
        "D": _add_months(vacancy, 3),                  # the s. 17(1) period
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ---------------------------------------------------------------------------
# q-i2c12-021 — s. 17(1): direction issued 11 August 2026, the name to be
# changed within three MONTHS of the date of the direction.
# ---------------------------------------------------------------------------
def q_i2c12_021():
    direction = date(2026, 8, 11)

    due = _add_months(direction, 3)                    # 11 November 2026

    options = {
        "A": _add_days(direction, 15),                 # the s. 17(2) notice
        "B": _add_days(direction, 60),                 # 60 days
        "C": due,
        "D": _add_months(direction, 6),                # six months
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ---------------------------------------------------------------------------
# q-i2c12-026 — s. 24(1): the LLP agreement being silent, a partner ceases on
# notice in writing of not less than 30 DAYS to the other partners.
# ---------------------------------------------------------------------------
def q_i2c12_026():
    notice = date(2026, 9, 9)

    ceases = _add_days(notice, 30)                     # 9 October 2026

    options = {
        "A": _add_days(notice, 15),                    # 15 days
        "B": ceases,
        "C": _add_days(notice, 60),                    # 60 days
        "D": _add_months(notice, 3),                   # three months
    }
    return {"answer": _pick(options, ceases), "computed": ceases.isoformat()}


# ---------------------------------------------------------------------------
# q-i2c12-028 — s. 25(2)(a): partner admitted 3 December 2026, notice to the
# Registrar within 30 DAYS of that date.
# ---------------------------------------------------------------------------
def q_i2c12_028():
    change = date(2026, 12, 3)

    due = _add_days(change, 30)                        # 2 January 2027

    options = {
        "A": _add_days(change, 15),                    # the s. 25(1) period
        "B": _add_days(change, 60),                    # the s. 35 period
        "C": due,
        "D": _add_months(change, 3),                   # the s. 17(1) period
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ---------------------------------------------------------------------------
# q-i2c12-035 — s. 34(3) with r. 24: Form 8 for the FY ending 31 March 2027.
# Six months from the FY end is 30 September 2027 (the clamp does the work),
# and 30 days beyond that is 30 October 2027.
# ---------------------------------------------------------------------------
def q_i2c12_035():
    fy_end = date(2027, 3, 31)

    due = _form8_due(fy_end)                           # 30 October 2027

    options = {
        "A": _add_days(fy_end, 60),                    # the s. 35 Form 11 date
        "B": _add_months(fy_end, 6),                   # the six months alone
        "C": due + timedelta(days=1),                  # off-by-one
        "D": due,
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ---------------------------------------------------------------------------
# cs-i2c12-03-a — the same Form 8 clock for the FY ending 31 March 2028.
# ---------------------------------------------------------------------------
def cs_i2c12_03_a():
    fy_end = date(2028, 3, 31)

    due = _form8_due(fy_end)                           # 30 October 2028

    options = {
        "A": _add_days(fy_end, 60),                    # the s. 35 Form 11 date
        "B": due,
        "C": _add_months(fy_end, 6),                   # the six months alone
        "D": due + timedelta(days=1),                  # off-by-one
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ---------------------------------------------------------------------------
# cs-i2c12-03-b — s. 35(1): the annual return within 60 DAYS of the CLOSURE
# of the financial year ending 31 March 2028.
# ---------------------------------------------------------------------------
def cs_i2c12_03_b():
    fy_end = date(2028, 3, 31)

    due = _add_days(fy_end, 60)                        # 30 May 2028

    options = {
        "A": due,
        "B": _add_months(fy_end, 2),                   # read as two months
        "C": _add_days(fy_end, 30),                    # 30 days
        "D": _form8_due(fy_end),                       # the Form 8 date
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}


# ---------------------------------------------------------------------------
# cs-i2c12-03-c — r. 24: contribution Rs 27,00,000 (above Rs 25 lakh) and
# turnover Rs 31,00,000 (below Rs 40 lakh). The limbs are joined by OR, so one
# breach is enough. Contrast q-i2c12-004, where the AND conjunction of
# s. 2(1)(ta) produces the opposite reading of the very same two figures.
# ---------------------------------------------------------------------------
def cs_i2c12_03_c():
    contribution, turnover = Fraction(2700000), Fraction(3100000)

    verdict = _audit_verdict(contribution, turnover)

    options = {
        "A": "no audit - neither threshold crossed",
        "B": "audit - turnover threshold crossed",
        "C": "audit - both thresholds crossed",
        "D": "audit - contribution threshold crossed",
    }
    return {"answer": _pick(options, verdict), "computed": verdict}


# ---------------------------------------------------------------------------
# cs-i2c12-01-c — s. 58(1): conversion registered 6 July 2026, the Registrar
# of Firms to be informed within 15 DAYS of the date of registration.
# ---------------------------------------------------------------------------
def cs_i2c12_01_c():
    registered = date(2026, 7, 6)

    due = _add_days(registered, 15)                    # 21 July 2026

    options = {
        "A": due - timedelta(days=1),                  # off-by-one
        "B": _add_days(registered, 30),                # the s. 25(2) period
        "C": due,
        "D": _add_months(registered, 3),               # the s. 17(1) period
    }
    return {"answer": _pick(options, due), "computed": due.isoformat()}
