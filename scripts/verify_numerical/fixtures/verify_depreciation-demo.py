"""Fixture verify module for the toolkit self-test. Not real content.

Demonstrates the convention: one function per numerical question id
(dashes -> underscores), computing the answer from the stem's parameters
and mapping the computed value to an option key. Never hard-code the key.
"""


def _slm(cost, residual, life):
    return (cost - residual) / life


def q_dep_001():
    cost, residual, original_life = 500_000, 50_000, 10
    charge = _slm(cost, residual, original_life)          # 45,000/yr
    wdv_after_4 = cost - 4 * charge                       # 3,20,000
    revised = _slm(wdv_after_4, residual, 3)              # 90,000
    options = {"A": 45_000, "B": 110_000, "C": 100_000, "D": 90_000}
    answer = next(k for k, v in options.items() if v == revised)
    return {"answer": answer, "computed": revised}


def q_dep_002():
    charge = _slm(240_000, 40_000, 8)
    options = {"A": 30_000, "B": 25_000, "C": 35_000, "D": 20_000}
    answer = next(k for k, v in options.items() if v == charge)
    return {"answer": answer, "computed": charge}


def q_dep_004_a():
    # Case-set sub-question: SLM on the fixture lathe. The bank's key is a
    # PLANTED error (B); the runner must flatten case sets and catch it.
    charge = _slm(200_000, 20_000, 6)
    options = {"A": 30_000, "B": 33_333, "C": 20_000, "D": 36_000}
    answer = next(k for k, v in options.items() if v == charge)
    return {"answer": answer, "computed": charge}
