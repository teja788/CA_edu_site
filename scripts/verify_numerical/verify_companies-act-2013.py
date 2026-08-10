"""Verifier for foundation/business-laws/companies-act-2013.json.

Every function recomputes its answer from the parameters stated in the stem and
then maps the computed value onto an option key. No answer key is copied.

Four families of computable question live in this chapter, and in every one of
them the arithmetic is trivial while the LEGAL step that selects the arithmetic
is the thing being examined:

1. Counting members against the 200-member cap in s. 2(68)(ii). The arithmetic
   is addition; the law decides WHAT is added. Joint holders of one or more
   shares count as ONE member; persons in the employment of the company, and
   ex-employees who became members while employed and continued afterwards, are
   excluded; debenture-holders are not members at all.

2. Small-company status under s. 2(85). The clause is run in a fixed order:
   public company -> stop; holding/subsidiary, s. 8 or special-Act company ->
   stop; only then the two CUMULATIVE thresholds, paid-up share capital and
   turnover of the IMMEDIATELY PRECEDING financial year. The prescribed figures
   (₹ 4,00,00,000 and ₹ 40,00,00,000) are set by the Companies (Specification of
   Definitions Details) Rules, not by the Act, and are stated as on 2026-02-28.

3. Control tests. s. 2(87)(ii) runs on TOTAL VOTING POWER, so non-voting
   preference shares are stripped out of the base before dividing; voting power
   held by the company itself may be added to that held by its subsidiaries;
   control exercised through a subsidiary carries the relationship up the chain
   and percentages are NEVER multiplied. s. 2(6) is reached only if the
   subsidiary test has failed, and its comparator is inclusive ("at least 20%")
   where s. 2(87)(ii) is exclusive ("more than one-half").

4. s. 2(45), which is the one control-style definition in the chapter that runs
   on PAID-UP SHARE CAPITAL rather than voting power, aggregating the Central
   and State Government holdings and asking for "not less than" 51 per cent.

Law as on 2026-02-28; applicable to the Sept 2026 and Jan 2027 attempts.
"""

from __future__ import annotations

from fractions import Fraction

# Prescribed under the Companies (Specification of Definitions Details) Rules
# 2014 as on 28 February 2026. Rules-level figures — see the citations file.
SMALL_COMPANY_CAPITAL_LIMIT = 4_00_00_000
SMALL_COMPANY_TURNOVER_LIMIT = 40_00_00_000


def _pick(options, value):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if v == value:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


def _pct(part: int, whole: int) -> float:
    """Percentage as a float, computed exactly and then rounded to 2 places."""
    return float(round(Fraction(part, whole) * 100, 2))


def _control_verdict(pct: float) -> str:
    """s. 2(87)(ii) first, then s. 2(6). Order and comparators both matter."""
    if pct > 50:
        return "subsidiary"
    if pct >= 20:
        return "associate"
    return "no-relationship"


# ---------------------------------------------------------------------------
# q-f2c6-017 — s. 2(68)(ii): joint holders are ONE member, employee and
# qualifying ex-employee members are excluded, debenture-holders never counted.
# ---------------------------------------------------------------------------
def q_f2c6_017():
    individuals_own_name = 96
    joint_holdings = 21
    persons_per_joint_holding = 2
    current_employee_members = 34
    ex_employee_members_from_employment = 5
    debenture_holders = 48

    counted = individuals_own_name + joint_holdings          # 96 + 21 = 117

    joint_persons = joint_holdings * persons_per_joint_holding      # 42
    joint_counted_separately = individuals_own_name + joint_persons  # 138
    raw_register = (individuals_own_name + joint_persons
                    + current_employee_members
                    + ex_employee_members_from_employment)           # 177

    options = {
        "A": counted,
        "B": joint_counted_separately,      # joint holders counted one by one
        "C": raw_register,                  # neither proviso applied
        "D": raw_register + debenture_holders,   # debenture-holders added in
    }
    return {"answer": _pick(options, counted), "computed": counted}


# ---------------------------------------------------------------------------
# q-f2c6-024 — s. 2(85): both limbs are cumulative, and the turnover limb is
# the one that fails here.
# ---------------------------------------------------------------------------
def q_f2c6_024():
    paid_up_capital = 3_20_00_000
    turnover_preceding_fy = 44_00_00_000
    is_public = False
    excluded = False            # not holding/subsidiary, not s. 8, not special Act

    capital_ok = paid_up_capital <= SMALL_COMPANY_CAPITAL_LIMIT
    turnover_ok = turnover_preceding_fy <= SMALL_COMPANY_TURNOVER_LIMIT
    small = (not is_public) and (not excluded) and capital_ok and turnover_ok

    if small:
        verdict = ("small", "both-limbs")
    elif not turnover_ok:
        verdict = ("not-small", "turnover")
    elif not capital_ok:
        verdict = ("not-small", "capital")
    else:
        verdict = ("not-small", "excluded")

    options = {
        "A": ("small", "capital"),        # one limb treated as enough
        "B": ("small", "either-limb"),    # limbs treated as alternatives
        "C": ("not-small", "private"),    # private companies wrongly ruled out
        "D": ("not-small", "turnover"),
    }
    return {"answer": _pick(options, verdict),
            "computed": f"capital_ok={capital_ok}, turnover_ok={turnover_ok}"}


# ---------------------------------------------------------------------------
# q-f2c6-027 — ss. 2(87)(ii) and 2(6): the base is TOTAL VOTING POWER, so the
# non-voting preference shares drop out before the division.
# ---------------------------------------------------------------------------
def q_f2c6_027():
    equity_shares = 9_00_000
    equity_face_value = 10
    votes_per_equity_share = 1
    preference_shares = 6_00_000
    preference_face_value = 10
    preference_votes_per_share = 0      # except on resolutions affecting them

    equity_held = 4_05_000
    preference_held = 6_00_000

    total_voting_power = (equity_shares * votes_per_equity_share
                          + preference_shares * preference_votes_per_share)
    votes_held = (equity_held * votes_per_equity_share
                  + preference_held * preference_votes_per_share)
    voting_pct = _pct(votes_held, total_voting_power)          # 45.0
    verdict = _control_verdict(voting_pct)                     # associate

    # The discarded base, kept only to build the distractor.
    total_capital = (equity_shares * equity_face_value
                     + preference_shares * preference_face_value)
    capital_held = (equity_held * equity_face_value
                    + preference_held * preference_face_value)
    capital_pct = _pct(capital_held, total_capital)            # 67.0

    options = {
        "A": (capital_pct, "subsidiary"),     # answered off paid-up capital
        "B": (voting_pct, "associate"),
        "C": (100.0, "subsidiary"),           # preference shares given full votes
        "D": (voting_pct, "no-relationship"),  # s. 2(6) never reached
    }
    return {"answer": _pick(options, (voting_pct, verdict)),
            "computed": f"{voting_pct}% of total voting power -> {verdict}"}


# ---------------------------------------------------------------------------
# q-f2c6-028 — s. 2(87), Explanation: control exercised through another
# subsidiary carries the relationship up the chain. Percentages are not
# multiplied; the product is computed here only to build the distractor.
# ---------------------------------------------------------------------------
def q_f2c6_028():
    a_in_b = 54.0        # Marudhar in Nalanda
    b_in_c = 51.0        # Nalanda in Palamau
    a_in_c_direct = 0.0  # Marudhar holds nothing in Palamau

    b_is_subsidiary_of_a = a_in_b > 50
    c_is_subsidiary_of_b = b_in_c > 50
    c_is_subsidiary_of_a = c_is_subsidiary_of_b and b_is_subsidiary_of_a

    if c_is_subsidiary_of_a:
        verdict = "subsidiary-of-both"
    elif c_is_subsidiary_of_b:
        verdict = "subsidiary-of-nalanda-only"
    else:
        verdict = "no-relationship"

    multiplied = round(a_in_b * b_in_c / 100, 2)      # 27.54 — never used in law

    options = {
        "A": ("associate", multiplied),                 # percentages multiplied
        "B": ("no-relationship", a_in_c_direct),        # direct holding demanded
        "C": ("subsidiary-of-nalanda-only", b_in_c),    # chain stops at Nalanda
        "D": ("subsidiary-of-both", a_in_b),
    }
    computed_pair = {
        "subsidiary-of-both": ("subsidiary-of-both", a_in_b),
        "subsidiary-of-nalanda-only": ("subsidiary-of-nalanda-only", b_in_c),
        "no-relationship": ("no-relationship", a_in_c_direct),
    }[verdict]
    return {"answer": _pick(options, computed_pair),
            "computed": f"{verdict} (the 54x51 product of {multiplied}% is not a legal test)"}


# ---------------------------------------------------------------------------
# q-f2c6-029 — s. 2(6): the comparator is "at least twenty per cent", so the
# boundary is inclusive and exactly 20.00% creates an associate relationship.
# ---------------------------------------------------------------------------
def q_f2c6_029():
    shares_held = 3_00_000
    total_shares = 15_00_000
    votes_per_share = 1
    agreement_on_business_decisions = False

    voting_pct = _pct(shares_held * votes_per_share,
                      total_shares * votes_per_share)      # 20.0
    verdict = _control_verdict(voting_pct)                  # associate
    if verdict == "no-relationship" and agreement_on_business_decisions:
        verdict = "associate"

    options = {
        "A": ("associate", voting_pct),
        "B": ("subsidiary", voting_pct),          # 20% read as control
        "C": ("no-relationship", voting_pct),     # "at least" read as "more than"
        "D": ("joint-venture", voting_pct),       # no joint arrangement on the facts
    }
    return {"answer": _pick(options, (verdict, voting_pct)),
            "computed": f"{voting_pct}% of total voting power -> {verdict}"}


# ---------------------------------------------------------------------------
# q-f2c6-032 — s. 2(45): Central and State holdings are AGGREGATED, the base is
# PAID-UP SHARE CAPITAL, and the comparator is "not less than" 51 per cent.
# ---------------------------------------------------------------------------
def q_f2c6_032():
    paid_up_capital = 80_00_00_000
    central_government = 18_00_00_000
    state_governments = [15_00_00_000, 9_00_00_000]   # Karnataka, Telangana

    aggregate = central_government + sum(state_governments)   # 42,00,00,000
    aggregate_pct = _pct(aggregate, paid_up_capital)          # 52.5
    central_only_pct = _pct(central_government, paid_up_capital)   # 22.5
    is_government_company = aggregate_pct >= 51

    verdict = "government-company" if is_government_company else "not-government"

    options = {
        "A": ("not-government", max([central_government] + state_governments)
              / paid_up_capital * 100),          # largest single holding only
        "B": ("government-company", aggregate_pct),
        "C": ("not-government", central_only_pct),   # State holdings ignored
        "D": ("government-company-voting", aggregate_pct),  # voting-power base
    }
    return {"answer": _pick(options, (verdict, aggregate_pct)),
            "computed": f"aggregate Government holding {aggregate} = {aggregate_pct}% of paid-up capital"}


# ---------------------------------------------------------------------------
# cs-f2c6-02-b — s. 2(87)(ii): voting power a company exercises on its own may
# be added to that exercised by one or more of its subsidiary companies.
# ---------------------------------------------------------------------------
def cs_f2c6_02_b():
    # Step 1 — is the intermediate company a subsidiary at all?
    parent_votes_in_intermediate = 7_20_000
    intermediate_total_votes = 12_00_000
    intermediate_pct = _pct(parent_votes_in_intermediate,
                            intermediate_total_votes)             # 60.0
    intermediate_is_subsidiary = intermediate_pct > 50

    # Step 2 — aggregate the parent's own holding with its subsidiary's.
    parent_direct = 34.0
    subsidiary_holding = 19.0
    combined = round(
        parent_direct + (subsidiary_holding if intermediate_is_subsidiary else 0),
        2,
    )                                                              # 53.0
    verdict = _control_verdict(combined)                           # subsidiary

    options = {
        "A": (combined, "subsidiary"),
        "B": (parent_direct, "associate"),        # only the direct holding counted
        "C": (subsidiary_holding, "no-relationship"),  # only the subsidiary's
        "D": (combined, "associate"),             # tests run in the wrong order
    }
    return {"answer": _pick(options, (combined, verdict)),
            "computed": f"{parent_direct}% + {subsidiary_holding}% = {combined}% -> {verdict}"}


# ---------------------------------------------------------------------------
# cs-f2c6-02-c — s. 2(85): being an ASSOCIATE is not one of the three
# exclusions, so a company held at 22 per cent may still be a small company.
# ---------------------------------------------------------------------------
def cs_f2c6_02_c():
    paid_up_capital = 3_90_00_000
    turnover_preceding_fy = 38_00_00_000
    held_pct = 22.0
    is_public = False
    is_section_8 = False
    is_special_act = False

    relationship = _control_verdict(held_pct)          # associate
    is_holding_or_subsidiary = relationship == "subsidiary"
    excluded = is_holding_or_subsidiary or is_section_8 or is_special_act

    capital_ok = paid_up_capital <= SMALL_COMPANY_CAPITAL_LIMIT
    turnover_ok = turnover_preceding_fy <= SMALL_COMPANY_TURNOVER_LIMIT
    small = (not is_public) and (not excluded) and capital_ok and turnover_ok

    if small:
        verdict = ("small", "both-limbs-no-exclusion")
    elif is_holding_or_subsidiary:
        verdict = ("not-small", "subsidiary")
    elif not turnover_ok:
        verdict = ("not-small", "turnover")
    elif not capital_ok:
        verdict = ("not-small", "capital")
    else:
        verdict = ("not-small", "excluded")

    options = {
        "A": ("not-small", "subsidiary"),       # 22% misread as control
        "B": ("not-small", "associate"),        # associate wrongly made an exclusion
        "C": ("not-small", "turnover"),         # turnover wrongly said to be over
        "D": ("small", "both-limbs-no-exclusion"),
    }
    return {"answer": _pick(options, verdict),
            "computed": (f"relationship={relationship}, capital_ok={capital_ok}, "
                         f"turnover_ok={turnover_ok}, small={small}")}
