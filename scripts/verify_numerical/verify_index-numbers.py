"""Verifier for foundation/quantitative-aptitude/index-numbers.json (P3 Ch 18).

Every function recomputes its answer from the stem's own price/quantity table.
The four building-block sums (Σp₀q₀, Σp₁q₀, Σp₀q₁, Σp₁q₁) are carried as exact
``fractions.Fraction`` so that Laspeyres, Paasche, Marshall-Edgeworth, the value
index and every relative are exact. Fisher's ideal index is a geometric mean, so
it is computed with ``math.sqrt`` on the float value and matched to an option by
a tolerance. In every case the computed value is mapped to an option key through
a dict of the four option VALUES — never through the bank's answer key. A wrong
key in the bank therefore shows up as a mismatch.

Conventions applied throughout (they match the chapter's notes, and a reviewer
should confirm them against the study material):

  * Prices are current over base in every price index; only the quantity weight
    changes between Laspeyres (q₀) and Paasche (q₁).
  * Indices are quoted to two decimal places. Where an index is exact (a ratio of
    integers) it is rounded half-up at the last step; Fisher and the reversal
    tests are matched within a small tolerance.
  * In the time-reversal and factor-reversal tests the indices are used as
    ratios (the ×100 is stripped) before multiplying.
  * A cost of living index by the aggregate expenditure method is the Laspeyres
    formula; by the family budget method it is Σ(RW) ÷ ΣW; the two agree.
"""

from __future__ import annotations

import math
from fractions import Fraction as Fr


# ------------------------------------------------------------ helpers


def sums(items):
    """Return the four building-block sums as exact Fractions.

    `items` is a list of (p0, q0, p1, q1). Returns (Sp0q0, Sp1q0, Sp0q1, Sp1q1).
    """
    Sp0q0 = sum((Fr(p0 * q0) for p0, q0, p1, q1 in items), Fr(0))
    Sp1q0 = sum((Fr(p1 * q0) for p0, q0, p1, q1 in items), Fr(0))
    Sp0q1 = sum((Fr(p0 * q1) for p0, q0, p1, q1 in items), Fr(0))
    Sp1q1 = sum((Fr(p1 * q1) for p0, q0, p1, q1 in items), Fr(0))
    return Sp0q0, Sp1q0, Sp0q1, Sp1q1


def _round2(x) -> float:
    """Round to two decimals, half-up — the last step of an exact computation.

    Accepts a Fraction or a float and returns a float with two-decimal value.
    """
    q = Fr(x) * 100
    n = q.numerator
    d = q.denominator
    # half-up on n/d
    whole, rem = divmod(n, d)
    if 2 * rem >= d:
        whole += 1
    return whole / 100


def pick(computed, options, tol=0.01) -> str:
    """Map a computed value to exactly one option key.

    `options` is {option key: option value as a number}. Exactly one option must
    sit within `tol` of the computed value, otherwise the verifier raises.
    """
    computed = float(computed)
    hits = [k for k, v in options.items() if abs(float(v) - computed) <= tol]
    if len(hits) != 1:
        raise AssertionError(f"computed {computed} matched {hits} in {options}")
    return hits[0]


def result(computed, options, tol=0.01):
    return {"answer": pick(computed, options, tol), "computed": str(computed)}


# price indices as ratios (no ×100), from the four sums -------------------


def laspeyres(items) -> float:
    Sp0q0, Sp1q0, Sp0q1, Sp1q1 = sums(items)
    return _round2(Sp1q0 / Sp0q0 * 100)


def paasche(items) -> float:
    Sp0q0, Sp1q0, Sp0q1, Sp1q1 = sums(items)
    return _round2(Sp1q1 / Sp0q1 * 100)


def fisher(items) -> float:
    Sp0q0, Sp1q0, Sp0q1, Sp1q1 = sums(items)
    L = Sp1q0 / Sp0q0 * 100
    P = Sp1q1 / Sp0q1 * 100
    return round(math.sqrt(float(L) * float(P)), 2)


def marshall_edgeworth(items) -> float:
    Sp0q0, Sp1q0, Sp0q1, Sp1q1 = sums(items)
    return _round2((Sp1q0 + Sp1q1) / (Sp0q0 + Sp0q1) * 100)


def dorbish_bowley(items) -> float:
    Sp0q0, Sp1q0, Sp0q1, Sp1q1 = sums(items)
    L = Sp1q0 / Sp0q0 * 100
    P = Sp1q1 / Sp0q1 * 100
    return _round2((L + P) / 2)


def value_index(items) -> float:
    Sp0q0, Sp1q0, Sp0q1, Sp1q1 = sums(items)
    return _round2(Sp1q1 / Sp0q0 * 100)


def laspeyres_quantity(items) -> float:
    # weight quantities by base prices: Σq1p0 / Σq0p0 = Σp0q1 / Σp0q0
    Sp0q0, Sp1q0, Sp0q1, Sp1q1 = sums(items)
    return _round2(Sp0q1 / Sp0q0 * 100)


def fisher_quantity(items) -> float:
    Sp0q0, Sp1q0, Sp0q1, Sp1q1 = sums(items)
    Lq = Sp0q1 / Sp0q0 * 100
    Pq = Sp1q1 / Sp1q0 * 100
    return round(math.sqrt(float(Lq) * float(Pq)), 2)


# shared datasets (the tables printed in the stems) ------------------------

MA = [(5, 50, 8, 60), (8, 40, 10, 30), (12, 20, 15, 25), (4, 100, 5, 90)]
MB = [(6, 10, 10, 12), (2, 20, 3, 25), (4, 15, 5, 10)]
MD = [(10, 12, 12, 15), (8, 15, 10, 10), (6, 24, 8, 20)]


# =========================================================== §2 price relatives


def q_f3c18_003():
    # Price relative = p1 / p0 * 100, exact.
    p0, p1 = 25, 30
    rel = _round2(Fr(p1, p0) * 100)
    return result(rel, {"A": 120, "B": 83.33, "C": 20, "D": 105})


def q_f3c18_004():
    p0, p1 = 80, 100
    rel = _round2(Fr(p1, p0) * 100)
    return result(rel, {"A": 80, "B": 25, "C": 20, "D": 125})


def q_f3c18_044():
    p0, p1 = 150, 180
    rel = _round2(Fr(p1, p0) * 100)
    return result(rel, {"A": 83.33, "B": 30, "C": 20, "D": 120})


# =========================================================== §3 simple aggregate


def q_f3c18_005():
    p0 = [25, 20, 15, 40]
    p1 = [30, 24, 20, 46]
    idx = _round2(Fr(sum(p1), sum(p0)) * 100)
    return result(idx, {"A": 122.08, "B": 120, "C": 83.33, "D": 125})


def q_f3c18_042():
    p0 = [50, 30, 20]
    p1 = [60, 39, 24]
    idx = _round2(Fr(sum(p1), sum(p0)) * 100)
    return result(idx, {"A": 81.30, "B": 123, "C": 123.33, "D": 120})


# ============================================== §4 simple average of relatives


def q_f3c18_006():
    pairs = [(40, 50), (20, 25), (50, 60), (25, 30)]
    rels = [Fr(p1, p0) * 100 for p0, p1 in pairs]
    idx = _round2(sum(rels, Fr(0)) / len(rels))
    return result(idx, {"A": 122.22, "B": 490, "C": 122.5, "D": 120})


def q_f3c18_043():
    pairs = [(30, 36), (50, 65), (20, 23), (40, 44)]
    rels = [Fr(p1, p0) * 100 for p0, p1 in pairs]
    idx = _round2(sum(rels, Fr(0)) / len(rels))
    return result(idx, {"A": 120, "B": 475, "C": 118.75, "D": 117.5})


# =============================================== §6/§7/§8/§9 weighted indices


def q_f3c18_008():
    return result(laspeyres(MB), {"A": 151.23, "B": 153.13, "C": 146.88, "D": 149.04})


def q_f3c18_009():
    return result(paasche(MB), {"A": 151.23, "B": 146.88, "C": 149.04, "D": 153.13})


def q_f3c18_010():
    return result(fisher(MA), {"A": 133.75, "B": 132.99, "C": 132.23, "D": 132.64})


def q_f3c18_011():
    return result(laspeyres(MA), {"A": 133.75, "B": 132.99, "C": 132.64, "D": 132.23})


def q_f3c18_012():
    return result(paasche(MA), {"A": 133.75, "B": 132.23, "C": 132.99, "D": 132.64})


def q_f3c18_013():
    return result(marshall_edgeworth(MD), {"A": 126.56, "B": 125.71, "C": 126.16, "D": 114.58})


def q_f3c18_014():
    return result(dorbish_bowley(MB), {"A": 146.88, "B": 149.05, "C": 151.23, "D": 298.11})


def q_f3c18_016():
    return result(laspeyres(MD), {"A": 126.56, "B": 125.71, "C": 126.14, "D": 114.58})


def q_f3c18_017():
    return result(paasche(MD), {"A": 126.56, "B": 126.14, "C": 125.71, "D": 114.58})


def q_f3c18_018():
    return result(fisher(MB), {"A": 146.88, "B": 149.04, "C": 151.23, "D": 153.13})


def q_f3c18_037():
    return result(fisher(MD), {"A": 126.56, "B": 126.14, "C": 125.71, "D": 114.58})


def q_f3c18_045():
    return result(marshall_edgeworth(MB), {"A": 149.07, "B": 146.88, "C": 151.23, "D": 153.13})


def q_f3c18_046():
    return result(dorbish_bowley(MA), {"A": 132.23, "B": 132.99, "C": 133.75, "D": 265.98})


# =============================================== §10 reversal tests


def q_f3c18_020():
    # Time-reversal for Fisher: P01 (ratio) * P10 (ratio) = 1.
    Sp0q0, Sp1q0, Sp0q1, Sp1q1 = sums(MA)
    P01 = math.sqrt(float(Sp1q0 / Sp0q0) * float(Sp1q1 / Sp0q1))
    P10 = math.sqrt(float(Sp0q1 / Sp1q1) * float(Sp0q0 / Sp1q0))
    product = P01 * P10
    return result(round(product, 4), {"A": 0, "B": 100, "C": 1, "D": 132.99}, tol=0.001)


def q_f3c18_021():
    # Factor-reversal for Fisher: Pf (ratio) * Qf (ratio) = value ratio Σp1q1/Σp0q0.
    Sp0q0, Sp1q0, Sp0q1, Sp1q1 = sums(MB)
    Pf = math.sqrt(float(Sp1q0 / Sp0q0) * float(Sp1q1 / Sp0q1))
    Qf = math.sqrt(float(Sp0q1 / Sp0q0) * float(Sp1q1 / Sp1q0))
    lhs = Pf * Qf
    value_ratio = float(Sp1q1 / Sp0q0)
    assert abs(lhs - value_ratio) < 1e-9  # Fisher satisfies the test exactly
    return result(round(value_ratio, 4), {"A": 1.0000, "B": 1.5313, "C": 1.4904, "D": 153.13}, tol=0.001)


# =============================================== §11 quantity and value indices


def q_f3c18_024():
    return result(laspeyres_quantity(MA), {"A": 100.83, "B": 132.23, "C": 99.17, "D": 99.74})


def q_f3c18_025():
    return result(value_index(MA), {"A": 132.23, "B": 133.75, "C": 132.99, "D": 132.64})


def q_f3c18_038():
    return result(laspeyres_quantity(MD), {"A": 91.15, "B": 126.56, "C": 109.71, "D": 114.58})


def q_f3c18_039():
    return result(value_index(MB), {"A": 146.88, "B": 151.23, "C": 153.13, "D": 149.04})


def q_f3c18_047():
    return result(fisher_quantity(MA), {"A": 99.17, "B": 132.99, "C": 99.74, "D": 100.31})


# =============================================== §12 cost of living


def q_f3c18_026():
    # Aggregate expenditure = Laspeyres. Table is (p0, q0, p1).
    table = [(8, 25, 10), (6, 50, 7), (5, 20, 6)]
    Sp1q0 = sum(Fr(p1 * q0) for p0, q0, p1 in table)
    Sp0q0 = sum(Fr(p0 * q0) for p0, q0, p1 in table)
    idx = _round2(Sp1q0 / Sp0q0 * 100)
    return result(idx, {"A": 120, "B": 120.56, "C": 83.33, "D": 130})


def q_f3c18_027():
    # Family budget = Σ(RW) / ΣW.
    RW = [(140, 50), (120, 10), (110, 15), (125, 15), (130, 10)]
    idx = _round2(Fr(sum(R * W for R, W in RW), sum(W for R, W in RW)))
    return result(idx, {"A": 13025, "B": 130.25, "C": 125, "D": 100})


def q_f3c18_048():
    RW = [(160, 40), (120, 20), (130, 25), (110, 15)]
    idx = _round2(Fr(sum(R * W for R, W in RW), sum(W for R, W in RW)))
    return result(idx, {"A": 13700, "B": 130, "C": 100, "D": 137})


# =============================================== §13 deflating


def q_f3c18_029():
    money_wage, cli = 18000, 120
    real = _round2(Fr(money_wage, cli) * 100)
    return result(real, {"A": 21600, "B": 18000, "C": 14400, "D": 15000})


def q_f3c18_030():
    cli = 125
    pp = _round2(Fr(100, cli))
    return result(pp, {"A": 0.80, "B": 1.25, "C": 0.75, "D": 1.00})


def q_f3c18_031():
    money_wage, cli = 24000, 150
    real = _round2(Fr(money_wage, cli) * 100)
    return result(real, {"A": 36000, "B": 24000, "C": 16000, "D": 15000})


def q_f3c18_040():
    money_wage, cli = 30000, 125
    real = _round2(Fr(money_wage, cli) * 100)
    return result(real, {"A": 37500, "B": 30000, "C": 25000, "D": 24000})


def q_f3c18_041():
    cli = 250
    pp = _round2(Fr(100, cli))
    return result(pp, {"A": 0.40, "B": 2.50, "C": 0.25, "D": 0.60})


# =============================================== §14/§15 base shift and splice


def q_f3c18_033():
    # Base shift: old index of year / old index of new base year * 100.
    year_index, new_base_index = 180, 150
    shifted = _round2(Fr(year_index, new_base_index) * 100)
    return result(shifted, {"A": 150, "B": 83.33, "C": 30, "D": 120})


def q_f3c18_034():
    # Splice new onto old base: new index * old overlap value / 100.
    new_index, old_overlap = 125, 150
    spliced = _round2(Fr(new_index * old_overlap, 100))
    return result(spliced, {"A": 187.5, "B": 83.33, "C": 275, "D": 125})
