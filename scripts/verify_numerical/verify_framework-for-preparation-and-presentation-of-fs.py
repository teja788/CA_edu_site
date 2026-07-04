"""Verifier for intermediate/advanced-accounting/framework-for-preparation-and-presentation-of-fs.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring Ch 2 mechanics (ICAI Framework; SM Ch 2 §10-11):
  profit equation      P = (CA − CL) − (OA − OL) − C + D
  CPP restatement      opening equity × closing index / opening index
  physical maintenance profit = sales − replacement cost of capacity consumed
  present value        future flow / (1 + r)^n
  mixed measurement    inventory at lower of cost and NRV
"""


def _pick(options, value, tolerance=0.5):
    """Map a computed value to its option key (rupee amounts may float)."""
    for key, v in options.items():
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value} matches no option in {options}")


# ── standalone MCQs ──────────────────────────────────────────────────────

def q_i1c02_021():
    # P = (CA − CL) − (OA − OL) − C + D
    p = (900_000 - 340_000) - (700_000 - 280_000) - 50_000 + 90_000
    key = _pick({"A": 220_000, "B": 180_000, "C": 100_000, "D": 140_000}, p)
    return {"answer": key, "computed": p}


def q_i1c02_022():
    # opening equity restated by the general index
    restated = 400_000 * 115 / 100
    key = _pick({"A": 347_826, "B": 415_000, "C": 460_000, "D": 400_000}, restated)
    return {"answer": key, "computed": restated}


def q_i1c02_023():
    # single inflow discounted two years at 10%
    pv = 121_000 / (1.10 ** 2)
    key = _pick({"A": 100_000, "B": 110_000, "C": 96_800, "D": 121_000}, pv)
    return {"answer": key, "computed": pv}


def q_i1c02_024():
    # lower of cost and NRV
    carrying = min(80_000, 72_000)
    key = _pick({"A": 72_000, "B": 8_000, "C": 80_000, "D": 76_000}, carrying)
    return {"answer": key, "computed": carrying}


# ── case set 3: Tawa Traders (three capital-maintenance verdicts) ────────
# Opening 20,000 = 5,000 units @ ₹4; sales 25,000 (all units @ ₹5);
# drawings 3,000; replacement price 4.60; index 100 → 110.

def cs_i1c02_003_a():
    profit_hc = 25_000 - 20_000
    key = _pick({"A": 3_000, "B": 2_000, "C": 5_000, "D": 25_000}, profit_hc)
    return {"answer": key, "computed": profit_hc}


def cs_i1c02_003_b():
    cpp_capital = 20_000 * 110 / 100
    key = _pick({"A": 21_000, "B": 22_000, "C": 23_000, "D": 20_000}, cpp_capital)
    return {"answer": key, "computed": cpp_capital}


def cs_i1c02_003_c():
    replacement = 5_000 * 4.60
    profit_phys = 25_000 - replacement
    key = _pick({"A": 3_000, "B": 2_000, "C": 5_000, "D": 0}, profit_phys)
    return {"answer": key, "computed": profit_phys}


def cs_i1c02_003_d():
    retained_phys = (25_000 - 5_000 * 4.60) - 3_000
    assert retained_phys < 0, "physical capital not maintained on these facts"
    key = _pick({"A": -1_000, "B": 1_000, "C": 0, "D": 2_000}, retained_phys)
    return {"answer": key, "computed": retained_phys}
