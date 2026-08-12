"""Verifier for foundation/business-economics/price-determination-in-different-markets.json (P4 Ch 4).

Every function recomputes its answer from the stem's own parameters. Nothing is
copied from the answer key: each computed value is mapped to an option key
through a dict of the four option values, so a wrong key in the bank surfaces as
a KeyError or as a mismatch the runner reports.

Conventions used below:
  * `Fraction` (F) gives exact rational prices, quantities and revenues; no
    rounding is ever needed, because every stem is built so the exact answer is a
    clean value.
  * Average revenue AR = total revenue / quantity = price.
  * Marginal revenue MR of the nth unit = TR(n) - TR(n - 1); it keeps its SIGN,
    because MR turns negative beyond the total-revenue maximum (q-f4c4-044).
  * Under perfect competition the firm is a price taker, so MR = AR = price.
  * The profit-maximising output is the largest output at which marginal cost
    does not exceed marginal revenue (MR = MC, with MC rising).
  * Profit = total revenue - total cost = TR - TC.
  * A market equilibrium is found by solving quantity demanded = quantity
    supplied for the price, then substituting back for the quantity.
"""

from __future__ import annotations

from fractions import Fraction as F


# ------------------------------------------------------------ shared helpers


def equilibrium(a_d, b_d, a_s, b_s):
    """For Qd = a_d + b_d*P and Qs = a_s + b_s*P, return (price, quantity)."""
    # a_d + b_d*P = a_s + b_s*P  ->  P = (a_s - a_d) / (b_d - b_s)
    p = F(a_s - a_d, b_d - b_s)
    q = a_d + b_d * p
    assert q == a_s + b_s * p, "demand and supply must give the same quantity"
    return p, q


def profit_max_output(marginal_costs, marginal_revenue):
    """Largest output at which MC does not exceed a constant MR."""
    output = 0
    for mc in marginal_costs:
        if mc <= marginal_revenue:
            output += 1
        else:
            break
    return output


# ----------------------------------------------------------- price determination


def q_f4c4_015():
    # Qd = 240 - 5P, Qs = -80 + 3P; equilibrium price.
    p, q = equilibrium(240, -5, -80, 3)
    key = {F(30): "A", F(40): "B", F(50): "C", F(20): "D"}[p]
    return {"answer": key, "computed": "P=%s, Q=%s" % (p, q)}


def q_f4c4_016():
    # Qd = 120 - 2P, Qs = -60 + 4P; equilibrium quantity.
    p, q = equilibrium(120, -2, -60, 4)
    key = {F(40): "A", F(50): "B", F(60): "C", F(30): "D"}[q]
    return {"answer": key, "computed": "P=%s, Q=%s" % (p, q)}


def q_f4c4_020():
    # Supply rises: Qd = 200 - 4P, Qs = -40 + 6P; new equilibrium price.
    p, q = equilibrium(200, -4, -40, 6)
    key = {F(30): "A", F(24): "B", F(20): "C", F(26): "D"}[p]
    return {"answer": key, "computed": "P=%s, Q=%s" % (p, q)}


# -------------------------------------------------------------------- revenue


def q_f4c4_024():
    # AR = TR / quantity.
    ar = F(2400, 20)
    key = {F(120): "A", F(48): "B", F(2400): "C", F(100): "D"}[ar]
    return {"answer": key, "computed": str(ar)}


def q_f4c4_025():
    # MR = change in total revenue for the 11th unit.
    mr = F(540 - 500)
    key = {F(40): "A", F(540): "B", F(500): "C", F(49): "D"}[mr]
    return {"answer": key, "computed": str(mr)}


def q_f4c4_028():
    # Perfect competition: MR = AR = price.
    mr = F(25)
    key = {F(25, 2): "A", F(25): "B", F(0): "C", F(50): "D"}[mr]
    return {"answer": key, "computed": str(mr)}


def q_f4c4_032():
    # TR = price * quantity.
    tr = F(50) * F(12)
    key = {F(600): "A", F(62): "B", F(50): "C", F(500): "D"}[tr]
    return {"answer": key, "computed": str(tr)}


def q_f4c4_040():
    # MR of the 6th unit from the AR (price) schedule.
    tr5 = 20 * 5
    tr6 = 18 * 6
    mr = F(tr6 - tr5)
    key = {F(18): "A", F(8): "B", F(2): "C", F(108): "D"}[mr]
    return {"answer": key, "computed": "TR %d -> %d, MR %s" % (tr5, tr6, mr)}


def q_f4c4_044():
    # MR keeps its sign: TR falls, so MR is negative.
    mr = F(231 - 240)
    key = {F(9): "A", F(-9): "B", F(21): "C", F(0): "D"}[mr]
    return {"answer": key, "computed": str(mr)}


# ---------------------------------------------------------- equilibrium of firm


def q_f4c4_031():
    # MR = MC with MC rising: largest output with MC <= MR 16.
    output = profit_max_output([12, 14, 16, 18, 20], 16)
    key = {2: "A", 3: "B", 4: "C", 5: "D"}[output]
    return {"answer": key, "computed": output}


def q_f4c4_033():
    # Profit = TR - TC.
    profit = F(9000 - 7200)
    key = {F(1800): "A", F(16200): "B", F(7200): "C", F(9000): "D"}[profit]
    return {"answer": key, "computed": str(profit)}


def q_f4c4_037():
    # Profit = (price - average cost) * quantity.
    profit = (F(24) - F(18)) * F(50)
    key = {F(300): "A", F(1200): "B", F(900): "C", F(6): "D"}[profit]
    return {"answer": key, "computed": str(profit)}
