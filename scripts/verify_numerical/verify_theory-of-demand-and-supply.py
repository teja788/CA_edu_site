"""Verifier for foundation/business-economics/theory-of-demand-and-supply.json (P4 Ch 2).

Every function recomputes its answer from the stem's own parameters. Nothing is
copied from the answer key: each computed value is mapped to an option key
through a dict of the four option values, so a wrong key in the bank surfaces as
a KeyError or as a mismatch the runner reports.

Conventions used below:
  * `Fraction` (F) gives exact rational elasticities and prices; no rounding is
    ever needed, because every stem is built so the exact answer is a clean
    value. Option texts that quote a rounded decimal (for example "0.67") map
    to the exact fraction (2/3) they stand for.
  * Price elasticity of demand is computed as a signed ratio and then quoted as
    an ABSOLUTE value, matching the "in magnitude" wording of those stems.
  * Income and cross elasticity KEEP their sign, because the sign classifies the
    good (inferior / substitute / complement); those stems ask for the signed
    value.
  * elasticity = (percentage change in quantity) / (percentage change in price),
    each percentage taken from the original value unless the stem names the arc
    (average-base) method.
  * A market equilibrium is found by solving quantity demanded = quantity
    supplied for the price, then substituting back for the quantity.
"""

from __future__ import annotations

from fractions import Fraction as F


# ------------------------------------------------------------ shared helpers


def pct_change(new, old):
    """Signed proportionate change (new - old) / old, exact."""
    return F(new - old, old)


def price_elasticity_pct(new_q, old_q, new_p, old_p):
    """Signed price elasticity by the percentage (original-base) method."""
    return pct_change(new_q, old_q) / pct_change(new_p, old_p)


def arc_elasticity(q1, q2, p1, p2):
    """Signed arc elasticity using the sum (average) of the two bases."""
    return F(q2 - q1, q1 + q2) / F(p2 - p1, p1 + p2)


def equilibrium(a_d, b_d, a_s, b_s):
    """For Qd = a_d + b_d*P and Qs = a_s + b_s*P, return (price, quantity)."""
    # a_d + b_d*P = a_s + b_s*P  ->  P = (a_s - a_d) / (b_d - b_s)
    p = F(a_s - a_d, b_d - b_s)
    q = a_d + b_d * p
    assert q == a_s + b_s * p, "demand and supply must give the same quantity"
    return p, q


# ------------------------------------------------------------- demand basics


def q_f4c2_009():
    # Market demand is the horizontal sum of the three individual quantities.
    total = 8 + 14 + 23
    key = {37: "A", 22: "B", 45: "C", 15: "D"}[total]
    return {"answer": key, "computed": total}


# ---------------------------------------------------- price elasticity of demand


def q_f4c2_019():
    # 10% rise in price, 25% fall in quantity; quoted in magnitude.
    e = abs(F(-25, 100) / F(10, 100))
    key = {F(2, 5): "A", F(5, 2): "B", F(2): "C", F(1, 4): "D"}[e]
    return {"answer": key, "computed": str(e)}


def q_f4c2_020():
    # Price 20 -> 25, quantity 400 -> 340, percentage method, magnitude.
    e = abs(price_elasticity_pct(340, 400, 25, 20))
    key = {F(5, 3): "A", F(3, 4): "B", F(2, 5): "C", F(3, 5): "D"}[e]
    return {"answer": key, "computed": str(e)}


def q_f4c2_021():
    # Price 8 -> 12, quantity 200 -> 120, arc method, magnitude.
    e = abs(arc_elasticity(200, 120, 8, 12))
    key = {F(4, 5): "A", F(1): "B", F(5, 4): "C", F(1, 2): "D"}[e]
    return {"answer": key, "computed": str(e)}


def q_f4c2_023():
    # Q = 300 - 6P at P = 20; point e = |slope| * P/Q, magnitude.
    slope = -6
    p = 20
    q = 300 - 6 * p
    e = abs(F(slope) * F(p, q))
    key = {F(2, 3): "A", F(3, 2): "B", F(1, 3): "C", F(2): "D"}[e]
    return {"answer": key, "computed": str(e)}


def q_f4c2_024():
    # e = 2 (magnitude), price up 10%, base quantity 800 -> new quantity.
    e = 2
    new_q = 800 * (1 - e * F(10, 100))
    assert new_q.denominator == 1
    key = {960: "A", 640: "B", 720: "C", 160: "D"}[int(new_q)]
    return {"answer": key, "computed": int(new_q)}


def q_f4c2_025():
    # Price 40 -> 30, quantity 500 -> 800; change in total revenue.
    tr_before = 40 * 500
    tr_after = 30 * 800
    change = tr_after - tr_before  # +4000 -> revenue rose
    key = {4000: "A", -4000: "B", 20000: "C", 0: "D"}[change]
    return {"answer": key, "computed": "TR %d -> %d, change %d" % (tr_before, tr_after, change)}


# ----------------------------------------------- income and cross elasticity


def q_f4c2_027():
    # Income up 20%, quantity up 30%; sign kept.
    e = F(30, 100) / F(20, 100)
    key = {F(2, 3): "A", F(-3, 2): "B", F(5, 2): "C", F(3, 2): "D"}[e]
    return {"answer": key, "computed": str(e)}


def q_f4c2_028():
    # Income 16000 -> 20000, quantity 40 -> 34 (a fall); sign kept.
    e = pct_change(34, 40) / pct_change(20000, 16000)
    key = {F(3, 5): "A", F(-5, 3): "B", F(-3, 5): "C", F(-3, 20): "D"}[e]
    return {"answer": key, "computed": str(e)}


def q_f4c2_029():
    # Price of tea +20%, quantity of coffee +10%; cross elasticity, sign kept.
    e = F(10, 100) / F(20, 100)
    key = {F(-1, 2): "A", F(1, 2): "B", F(2): "C", F(2, 5): "D"}[e]
    return {"answer": key, "computed": str(e)}


def q_f4c2_030():
    # Price of printer +10%, quantity of cartridges -25%; cross elasticity.
    e = F(-25, 100) / F(10, 100)
    key = {F(-5, 2): "A", F(5, 2): "B", F(-2, 5): "C", F(-1, 4): "D"}[e]
    return {"answer": key, "computed": str(e)}


def q_f4c2_033():
    # Price 12 -> 10, quantity 250 -> 300, percentage method, magnitude.
    e = abs(price_elasticity_pct(300, 250, 10, 12))
    key = {F(5, 6): "A", F(1): "B", F(12, 5): "C", F(6, 5): "D"}[e]
    return {"answer": key, "computed": str(e)}


# --------------------------------------------------------- elasticity of supply


def q_f4c2_037():
    # Quantity supplied +30% when price +12%.
    e = F(30, 100) / F(12, 100)
    key = {F(5, 2): "A", F(2, 5): "B", F(18, 5): "C", F(3, 2): "D"}[e]
    return {"answer": key, "computed": str(e)}


def q_f4c2_038():
    # Price 50 -> 60, quantity supplied 300 -> 345.
    e = pct_change(345, 300) / pct_change(60, 50)
    key = {F(4, 3): "A", F(3, 2): "B", F(3, 4): "C", F(3, 5): "D"}[e]
    return {"answer": key, "computed": str(e)}


# ------------------------------------------------------------ market equilibrium


def q_f4c2_043():
    # Qd = 200 - 4P, Qs = -100 + 6P; equilibrium price.
    p, q = equilibrium(200, -4, -100, 6)
    key = {F(20): "A", F(30): "B", F(50): "C", F(10): "D"}[p]
    return {"answer": key, "computed": "P=%s, Q=%s" % (p, q)}


def q_f4c2_044():
    # Same market; equilibrium quantity.
    p, q = equilibrium(200, -4, -100, 6)
    key = {F(80): "A", F(120): "B", F(60): "C", F(100): "D"}[q]
    return {"answer": key, "computed": "P=%s, Q=%s" % (p, q)}


def q_f4c2_045():
    # Qd = 500 - 10P, Qs = -500 + 40P; equilibrium quantity.
    p, q = equilibrium(500, -10, -500, 40)
    key = {F(200): "A", F(250): "B", F(500): "C", F(300): "D"}[q]
    return {"answer": key, "computed": "P=%s, Q=%s" % (p, q)}


def q_f4c2_046():
    # Qd = 1200 - 3P, Qs = -300 + 2P; equilibrium price.
    p, q = equilibrium(1200, -3, -300, 2)
    key = {F(150): "A", F(250): "B", F(300): "C", F(500): "D"}[p]
    return {"answer": key, "computed": "P=%s, Q=%s" % (p, q)}


def q_f4c2_047():
    # Demand rises by 50 at every price: Qd = 250 - 4P; Qs = -100 + 6P.
    p, q = equilibrium(250, -4, -100, 6)
    key = {F(30): "A", F(35): "B", F(40): "C", F(25): "D"}[p]
    return {"answer": key, "computed": "P=%s, Q=%s" % (p, q)}


def q_f4c2_048():
    # Supply rises by 50 at every price: Qs = -50 + 6P; Qd = 200 - 4P.
    p, q = equilibrium(200, -4, -50, 6)
    key = {F(25): "A", F(30): "B", F(35): "C", F(20): "D"}[p]
    return {"answer": key, "computed": "P=%s, Q=%s" % (p, q)}


def q_f4c2_049():
    # At P = 40 (above equilibrium 30): compare quantities.
    p = 40
    qd = 200 - 4 * p
    qs = -100 + 6 * p
    gap = qs - qd  # positive -> surplus of this size
    state = "surplus" if gap > 0 else "shortage" if gap < 0 else "equilibrium"
    tag = "%s_%d" % (state, abs(gap))
    key = {"shortage_100": "A", "surplus_100": "B", "surplus_60": "C", "equilibrium_0": "D"}[tag]
    return {"answer": key, "computed": "Qd=%d, Qs=%d, %s" % (qd, qs, tag)}
