"""Verifier for foundation/business-laws/llp-act-2008.json.

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

# Thresholds and rates relied on, all stated once so a reviewer can retest the
# whole module by changing a single line if the law moves.
AUDIT_TURNOVER_LIMIT = 4000000       # r. 24, LLP Rules 2009
AUDIT_CONTRIBUTION_LIMIT = 2500000   # r. 24, LLP Rules 2009
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
