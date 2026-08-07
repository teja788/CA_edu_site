"""Verifier for intermediate/corporate-and-other-laws/preliminary.json.

CA Intermediate Paper 2, Chapter 1 (Preliminary) is a definitions chapter, so
the computable questions are counting and threshold tests rather than money
sums. Each function recomputes the answer from the stem's parameters and maps
the computed value to an option key; nothing is copied from the bank.

Recurring Ch 1 mechanics (law as on 28 Feb 2026):

  s.2(68)(ii) member count   count = individual members
                             + ONE per joint shareholding (first proviso)
                             + members who are neither current employees nor
                               ex-employees who became members while employed
                               (second proviso (A)/(B));
                             debenture-holders are never members
  s.2(85) small company      NOT a public company, AND paid-up capital
                             <= Rs 4 crore, AND turnover of the immediately
                             preceding FY <= Rs 40 crore, AND not a holding /
                             subsidiary / s.8 / special-Act company.
                             Comparator is "does not exceed" — equality passes.
                             THRESHOLDS ARE RULES-LEVEL AND AMENDMENT-SENSITIVE:
                             they are defined once below so a future change is
                             a one-line edit.
  s.2(45) Government co.     aggregate of Central + every State holding of
                             paid-up capital >= 51%
  s.2(87)(ii) subsidiary     control of MORE THAN one-half of TOTAL VOTING
                             POWER — voting power, not paid-up capital, since
                             the Companies (Amendment) Act 2017. Non-voting
                             preference shares are excluded from the base.
  s.2(87) Expl. (a) chain    control by a subsidiary of the holding company
                             counts; percentages are NEVER multiplied down a
                             chain
  s.2(6) associate           significant influence = AT LEAST 20% of total
                             voting power (inclusive boundary), or control of
                             or participation in business decisions by
                             agreement; and NOT a subsidiary

Classification questions map a tuple (percentage, status) or a plain label,
because the bare number alone is not unique across their options.
"""

# ── Rules-level thresholds (s.2(85)) — verify before each attempt ─────────
SMALL_CAPITAL_LIMIT = 4_00_00_000       # Rs 4 crore
SMALL_TURNOVER_LIMIT = 40_00_00_000     # Rs 40 crore
ASSOCIATE_MIN_PCT = 20.0                # "at least twenty per cent"
GOVT_MIN_PCT = 51.0                     # "not less than fifty-one per cent"


def _pick(options, value, tolerance=0.01):
    """Map a computed value to its option key."""
    for key, v in options.items():
        if isinstance(v, tuple) or isinstance(value, tuple) or isinstance(v, str):
            if v == value:
                return key
            continue
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value!r} matches no option in {options}")


def _members(individuals, joint_holdings, employees=0, ex_employee_members=0,
             post_employment_buyers=0, debenture_holders=0):
    """s.2(68)(ii) member count.

    joint_holdings: list/tuple of the number of persons in each joint holding —
    each holding contributes exactly ONE member however many persons hold it.
    employees / ex_employee_members are excluded by the second proviso;
    post_employment_buyers (who became members only AFTER leaving) are counted;
    debenture-holders are not members at all.
    """
    return individuals + len(joint_holdings) + post_employment_buyers


def _voting_pct(votes_held, total_votes):
    return round(votes_held / total_votes * 100, 2)


def _classify(pct, board_control=False, agreement=False):
    """s.2(87) then s.2(6), in that order."""
    if board_control or pct > 50.0:
        return "subsidiary"
    if pct >= ASSOCIATE_MIN_PCT or agreement:
        return "associate"
    return "neither"


def _is_small(public, capital, turnover, holding_or_subsidiary=False,
              section_8=False, special_act=False):
    if public or holding_or_subsidiary or section_8 or special_act:
        return False
    return capital <= SMALL_CAPITAL_LIMIT and turnover <= SMALL_TURNOVER_LIMIT


# ── standalone MCQs ──────────────────────────────────────────────────────

def q_i2c1_013():
    # 176 individuals; 9 joint holdings of 4 persons each; 31 current
    # employee-members; 12 ex-employees who became members while employed
    count = _members(individuals=176, joint_holdings=[4] * 9,
                     employees=31, ex_employee_members=12)
    key = _pick({"D": 185, "A": 212, "B": 228, "C": 255}, count)
    return {"answer": key, "computed": count}


def q_i2c1_015():
    # 154 individuals; 8 joint holdings of 2; 22 current employee-members
    counted = _members(individuals=154, joint_holdings=[2] * 8, employees=22)
    headroom = 200 - counted
    key = _pick({"A": 30, "B": 16, "D": 8, "C": 38}, headroom)
    return {"answer": key, "computed": {"counted": counted, "headroom": headroom}}


def q_i2c1_023():
    # exactly one of the four companies described in the options is small
    candidates = {
        "bellary": _is_small(public=False, capital=1_20_00_000, turnover=47_00_00_000),
        "amrut": _is_small(public=False, capital=3_60_00_000, turnover=36_00_00_000),
        "chandra": _is_small(public=False, capital=50_00_000, turnover=6_00_00_000,
                             holding_or_subsidiary=True),
        "everest": _is_small(public=True, capital=1_00_00_000, turnover=5_00_00_000),
    }
    qualifying = [name for name, ok in candidates.items() if ok]
    assert len(qualifying) == 1, qualifying
    key = _pick({"A": "bellary", "D": "amrut", "B": "chandra", "C": "everest"},
                qualifying[0])
    return {"answer": key, "computed": candidates}


def q_i2c1_025():
    # capital and turnover exactly AT the prescribed limits — "does not exceed"
    small = _is_small(public=False, capital=4_00_00_000, turnover=40_00_00_000)
    # only one option asserts small-company status, so map on the boolean
    key = _pick({"A": True, "B": "capital-excess", "C": "turnover-excess",
                 "D": "margin-required"}, small)
    return {"answer": key, "computed": {"capital_ok": 4_00_00_000 <= SMALL_CAPITAL_LIMIT,
                                        "turnover_ok": 40_00_00_000 <= SMALL_TURNOVER_LIMIT,
                                        "small": small}}


def q_i2c1_026():
    # Central 14cr + Maharashtra 9cr + Karnataka 3cr of a 50cr paid-up capital
    total = 50_00_00_000
    govt = 14_00_00_000 + 9_00_00_000 + 3_00_00_000
    pct = round(govt / total * 100, 2)
    is_govt = pct >= GOVT_MIN_PCT
    key = _pick({"D": (52.0, True), "A": (28.0, False), "B": (46.0, False),
                 "C": (52.0, False)}, (pct, is_govt))
    return {"answer": key, "computed": {"aggregate_pct": pct, "government_company": is_govt}}


def q_i2c1_033():
    # 8,00,000 voting equity + 4,00,000 non-voting preference; Rewa holds
    # 3,60,000 equity and all the preference shares
    pct = _voting_pct(3_60_000, 8_00_000)
    status = _classify(pct)
    key = _pick({"B": (63.33, "subsidiary"), "C": (45.0, "subsidiary"),
                 "D": (45.0, "neither"), "A": (45.0, "associate")}, (pct, status))
    return {"answer": key, "computed": {"voting_pct": pct, "status": status}}


def q_i2c1_035():
    # A 58% of B, B 51% of C, C 70% of D — control tested step by step
    steps = {"bhadra": 58.0, "chitra": 51.0, "damodar": 70.0}
    chain_ok = all(p > 50.0 for p in steps.values())
    chitra = "subsidiary" if chain_ok else "associate"
    damodar = "subsidiary" if chain_ok else "neither"
    effective = round(58.0 * 51.0 / 100, 2)   # 29.58 — the multiplying trap
    key = _pick({"A": ("associate", "neither"), "B": ("subsidiary", "chitra-only"),
                 "D": ("subsidiary", "subsidiary"), "C": ("associate", "associate")},
                (chitra, damodar))
    return {"answer": key,
            "computed": {"chitra": chitra, "damodar": damodar,
                         "multiplied_trap_pct": effective}}


def q_i2c1_037():
    # 1,50,000 of 7,50,000 one-vote equity shares, no agreement
    pct = _voting_pct(1_50_000, 7_50_000)
    status = _classify(pct, agreement=False)
    key = _pick({"A": (20.0, "neither"), "C": (20.0, "associate"),
                 "B": (20.0, "subsidiary"), "D": (20.0, "no-agreement")}, (pct, status))
    return {"answer": key, "computed": {"voting_pct": pct, "status": status}}


# ── case-set sub-questions ───────────────────────────────────────────────

def cs_i2c1_01_c():
    # Varsha Coatings: 5,00,000 voting equity + 3,00,000 non-voting preference;
    # Sarvodaya holds 1,10,000 equity and 2,40,000 preference shares
    pct = _voting_pct(1_10_000, 5_00_000)
    status = _classify(pct)
    capital_trap = round((1_10_000 * 10 + 2_40_000 * 10) /
                         (5_00_000 * 10 + 3_00_000 * 10) * 100, 2)     # 43.75
    share_count_trap = round(1_10_000 / 8_00_000 * 100, 2)             # 13.75
    key = _pick({"A": (43.75, "subsidiary"), "B": (22.0, "associate"),
                 "C": (22.0, "neither"), "D": (13.75, "neither")}, (pct, status))
    return {"answer": key,
            "computed": {"voting_pct": pct, "status": status,
                         "capital_trap_pct": capital_trap,
                         "share_count_trap_pct": share_count_trap}}


def cs_i2c1_02_a():
    # 132 individuals; 15 joint holdings of 2; 6 joint holdings of 3;
    # 44 current employee-members; 18 continuing ex-employee members;
    # 7 who bought only after leaving; 260 debenture-holders
    count = _members(individuals=132,
                     joint_holdings=[2] * 15 + [3] * 6,
                     employees=44,
                     ex_employee_members=18,
                     post_employment_buyers=7,
                     debenture_holders=260)
    key = _pick({"A": 153, "B": 160, "C": 222, "D": 420}, count)
    return {"answer": key, "computed": count}


def cs_i2c1_03_a():
    # Ashwatha Tools: capital 3.90cr, preceding-year turnover 39.50cr
    small = _is_small(public=False, capital=3_90_00_000, turnover=39_50_00_000)
    key = _pick({"A": "no-margin", "B": "current-year", "C": True,
                 "D": "opc-required"}, small)
    return {"answer": key,
            "computed": {"capital_ok": 3_90_00_000 <= SMALL_CAPITAL_LIMIT,
                         "turnover_ok": 39_50_00_000 <= SMALL_TURNOVER_LIMIT,
                         "small": small}}
