"""Verifier for intermediate/advanced-accounting/other-accounting-standards.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring Ch 9 mechanics (SM Ch 9 U1–U2):
  AS 12 Method I      depreciation = (cost − grant − salvage) / life
  AS 12 Method II     depreciation on full cost less salvage + grant/life
                      released from deferred income
  AS 12 revenue grant lump sum / supported years, straight-line
  AS 12 refund        revenue: first against unamortised deferred credit,
                      excess to P&L; asset: add to book value, depreciate
                      revised amount prospectively over residual life
  q-i1c09-007 and cs-i1c09-001-b map (depreciation, grant income) tuples —
  the depreciation figures alone are not unique across options.
"""


def _pick(options, value, tolerance=0.5):
    """Map a computed value to its option key (rupee amounts may float)."""
    for key, v in options.items():
        if isinstance(v, tuple) or isinstance(value, tuple):
            if v == value:
                return key
            continue
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value} matches no option in {options}")


# ── standalone MCQs · AS 12 ──────────────────────────────────────────────

def q_i1c09_006():
    # Method I: (60,00,000 − 12,00,000 grant − 8,00,000 salvage) / 5
    dep = (6_000_000 - 1_200_000 - 800_000) / 5
    key = _pick({"A": 1_200_000, "B": 1_040_000, "C": 960_000, "D": 800_000}, dep)
    return {"answer": key, "computed": dep}


def q_i1c09_007():
    # Method II: depreciation (60,00,000 − 8,00,000)/5 + grant 12,00,000/5
    dep = (6_000_000 - 800_000) / 5
    grant = 1_200_000 / 5
    key = _pick({"A": (1_040_000, 0), "B": (1_040_000, 240_000),
                 "C": (1_200_000, 240_000), "D": (800_000, 0)}, (dep, grant))
    return {"answer": key, "computed": (dep, grant)}


def q_i1c09_010():
    # 1,20,00,000 lump sum over 4 supported years
    income = 12_000_000 / 4
    key = _pick({"A": 1_500_000, "B": 12_000_000, "C": 4_500_000, "D": 3_000_000},
                income)
    return {"answer": key, "computed": income}


def q_i1c09_012():
    # refund 24,00,000 first absorbs deferred credit 10,00,000; excess to P&L
    charge = 2_400_000 - min(1_000_000, 2_400_000)
    key = _pick({"A": 1_400_000, "B": 1_000_000, "C": 0, "D": 2_400_000}, charge)
    return {"answer": key, "computed": charge}


def q_i1c09_014():
    # (1,000 − 200) lakh at 20% WDV for 2 years, then add refund 200 lakh
    book = (1_000 - 200) * 0.8 * 0.8
    revised = book + 200
    key = _pick({"A": 512, "B": 800, "C": 712, "D": 840}, revised)
    return {"answer": key, "computed": revised}


# ── cs-i1c09-001 · Tungabhadra Textiles (asset grant, both methods) ──────

COST1, GRANT1, SALVAGE1, LIFE1 = 4_800_000, 1_200_000, 600_000, 6


def cs_i1c09_001_a():
    dep = (COST1 - GRANT1 - SALVAGE1) / LIFE1
    key = _pick({"A": 200_000, "B": 600_000, "C": 700_000, "D": 500_000}, dep)
    return {"answer": key, "computed": dep}


def cs_i1c09_001_b():
    dep = (COST1 - SALVAGE1) / LIFE1
    grant = GRANT1 / LIFE1
    key = _pick({"A": (800_000, 200_000), "B": (700_000, 200_000),
                 "C": (500_000, 0), "D": (700_000, 0)}, (dep, grant))
    return {"answer": key, "computed": (dep, grant)}


def cs_i1c09_001_c():
    dep = (COST1 - GRANT1 - SALVAGE1) / LIFE1
    bv = (COST1 - GRANT1) - 2 * dep
    key = _pick({"A": 2_000_000, "B": 3_400_000, "C": 2_600_000, "D": 3_100_000}, bv)
    return {"answer": key, "computed": bv}


# ── cs-i1c09-002 · Penganga Chemicals (refund of asset grant) ────────────

COST2, GRANT2, SALVAGE2, LIFE2, REFUND2 = 3_600_000, 900_000, 300_000, 4, 600_000


def _bv_after_refund():
    net = COST2 - GRANT2
    dep = (net - SALVAGE2) / LIFE2
    return net - 2 * dep + REFUND2


def cs_i1c09_002_a():
    bv = _bv_after_refund()
    key = _pick({"A": 2_100_000, "B": 1_800_000, "C": 2_700_000, "D": 1_500_000}, bv)
    return {"answer": key, "computed": bv}


def cs_i1c09_002_b():
    # prospective: (revised book value − salvage) over the 2 remaining years
    dep = (_bv_after_refund() - SALVAGE2) / 2
    key = _pick({"A": 450_000, "B": 900_000, "C": 600_000, "D": 1_050_000}, dep)
    return {"answer": key, "computed": dep}


# ── cs-i1c09-003 · Sharavati Hospitals (revenue grant + refund) ──────────

GRANT3, YEARS3, ELAPSED3 = 7_500_000, 5, 3


def cs_i1c09_003_a():
    income = GRANT3 / YEARS3
    key = _pick({"A": 500_000, "B": 7_500_000, "C": 1_500_000, "D": 2_500_000},
                income)
    return {"answer": key, "computed": income}


def cs_i1c09_003_b():
    deferred = GRANT3 - ELAPSED3 * GRANT3 / YEARS3
    key = _pick({"A": 4_500_000, "B": 1_500_000, "C": 3_000_000, "D": 7_500_000},
                deferred)
    return {"answer": key, "computed": deferred}


def cs_i1c09_003_c():
    deferred = GRANT3 - ELAPSED3 * GRANT3 / YEARS3
    charge = GRANT3 - deferred   # excess of refund over deferred credit
    key = _pick({"A": 4_500_000, "B": 3_000_000, "C": 0, "D": 7_500_000}, charge)
    return {"answer": key, "computed": charge}
