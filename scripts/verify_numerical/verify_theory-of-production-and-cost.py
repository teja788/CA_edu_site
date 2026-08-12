"""Verifier for foundation/business-economics/theory-of-production-and-cost.json (P4 Ch 3).

Every function recomputes its answer from the stem's own parameters. Nothing is
copied from the answer key: each computed value is mapped to an option key
through a dict of the four option values, so a wrong key in the bank surfaces as
a KeyError or as a mismatch the runner reports.

Conventions used below:
  * `Fraction` (F) gives exact rational products, costs and revenues; no rounding
    is ever needed, because every stem is built so the exact answer is a clean
    value. Option texts that quote a rounded decimal (for example "54.29" for
    380/7) map to the exact fraction they stand for.
  * Marginal product MP = ΔTP = TP(n) − TP(n − 1); average product AP = TP ÷ L.
  * Marginal cost MC = ΔTC = TC(n) − TC(n − 1) (equal to ΔTVC, since fixed cost
    does not change from one unit to the next).
  * AFC = TFC ÷ Q, AVC = TVC ÷ Q, ATC = TC ÷ Q, TC = TFC + TVC.
  * Marginal revenue MR = ΔTR; average revenue AR = TR ÷ Q = price. Under perfect
    competition (constant price) MR = AR = price.
  * Returns to scale is judged by comparing the output factor with the input
    factor: output up by more than the input factor → increasing, exactly →
    constant, less than → decreasing returns to scale.
"""

from __future__ import annotations

from fractions import Fraction as F


# ------------------------------------------------------------ shared helpers


def marginal(curr, prev):
    """A marginal magnitude is the change from the previous total."""
    return curr - prev


def average(total, quantity):
    """An average is a total divided by the quantity, exact."""
    return F(total, quantity)


# ------------------------------------------------------------ theory of production


def q_f4c3_008():
    # MP of the 3rd worker: TP(2) = 24, TP(3) = 39.
    mp = marginal(39, 24)
    key = {39: "A", 15: "B", 13: "C", 24: "D"}[mp]
    return {"answer": key, "computed": mp}


def q_f4c3_009():
    # AP of 4 workers: TP(4) = 52.
    ap = average(52, 4)
    key = {F(52): "A", F(48): "B", F(13): "C", F(15): "D"}[ap]
    return {"answer": key, "computed": str(ap)}


def q_f4c3_010():
    # MP of the 5th worker: TP(4) = 52, TP(5) = 60.
    mp = marginal(60, 52)
    key = {12: "A", 8: "B", 60: "C", 4: "D"}[mp]
    return {"answer": key, "computed": mp}


def q_f4c3_011():
    # AP of 6 workers: TP(6) = 66.
    ap = average(66, 6)
    key = {F(11): "A", F(66): "B", F(60): "C", F(13): "D"}[ap]
    return {"answer": key, "computed": str(ap)}


def q_f4c3_014():
    # MP of the 8th worker: TP(7) = 70, TP(8) = 70 (TP maximum, MP = 0).
    mp = marginal(70, 70)
    key = {70: "A", F(70, 8): "B", 0: "C", 4: "D"}[mp]
    return {"answer": key, "computed": mp}


def q_f4c3_020():
    # Inputs doubled (factor 2); output 500 -> 900.
    input_factor = F(2)
    output_factor = F(900, 500)
    if output_factor > input_factor:
        tag = "increasing"
    elif output_factor == input_factor:
        tag = "constant"
    else:
        tag = "decreasing"
    key = {"increasing": "A", "constant": "B", "decreasing": "C", "negative": "D"}[tag]
    return {"answer": key, "computed": "output factor %s vs input factor %s -> %s" % (output_factor, input_factor, tag)}


def q_f4c3_024():
    # Least-cost combination: MRTS of labour for capital = w / r = 200 / 100.
    w, r = 200, 100
    mrts = F(w, r)
    key = {F(1, 2): "A", F(2): "B", F(100): "C", F(300): "D"}[mrts]
    return {"answer": key, "computed": str(mrts)}


# ------------------------------------------------------------ theory of cost


def q_f4c3_036():
    # Economic cost = explicit + implicit.
    explicit = 8000 + 5000 + 12000
    implicit = 15000 + 3000
    economic = explicit + implicit
    key = {25000: "A", 43000: "B", 18000: "C", 40000: "D"}[economic]
    return {"answer": key, "computed": "explicit %d + implicit %d = %d" % (explicit, implicit, economic)}


def q_f4c3_039():
    # TC = TFC + TVC = 100 + 150.
    tc = 100 + 150
    key = {100: "A", 150: "B", 250: "C", 50: "D"}[tc]
    return {"answer": key, "computed": tc}


def q_f4c3_040():
    # AFC = TFC / Q = 100 / 4.
    afc = average(100, 4)
    key = {F(25): "A", F(30): "B", F(55): "C", F(20): "D"}[afc]
    return {"answer": key, "computed": str(afc)}


def q_f4c3_041():
    # AVC = TVC / Q = 120 / 4.
    avc = average(120, 4)
    key = {F(25): "A", F(30): "B", F(55): "C", F(40): "D"}[avc]
    return {"answer": key, "computed": str(avc)}


def q_f4c3_042():
    # MC of the 5th unit: TC(4) = 220, TC(5) = 250.
    mc = marginal(250, 220)
    key = {50: "A", 30: "B", 250: "C", 20: "D"}[mc]
    return {"answer": key, "computed": mc}


def q_f4c3_043():
    # MC of the 7th unit: TC(6) = 300, TC(7) = 380.
    mc = marginal(380, 300)
    key = {80: "A", 50: "B", 380: "C", F(380, 7): "D"}[mc]
    return {"answer": key, "computed": mc}


def q_f4c3_046():
    # ATC(5) = 250 / 5 and MC(6) = 300 - 250; both = 50 (the ATC minimum).
    atc5 = average(250, 5)
    mc6 = marginal(300, 250)
    tag = (atc5, mc6)
    key = {
        (F(125, 2), F(50)): "A",
        (F(50), F(50)): "B",
        (F(30), F(50)): "C",
        (F(55), F(80)): "D",
    }[tag]
    return {"answer": key, "computed": "ATC(5)=%s, MC(6)=%s" % (atc5, mc6)}


# ------------------------------------------------------------ revenue


def q_f4c3_048():
    # Imperfect competition: TR(2) = 18*2, TR(3) = 16*3; MR of 3rd unit.
    tr2 = 18 * 2
    tr3 = 16 * 3
    mr = marginal(tr3, tr2)
    key = {16: "A", 12: "B", 48: "C", 2: "D"}[mr]
    return {"answer": key, "computed": "TR2=%d, TR3=%d, MR=%d" % (tr2, tr3, mr)}


def q_f4c3_050():
    # Perfect competition: constant price 20 -> MR = AR = price.
    price = 20
    mr = price  # each extra unit adds exactly the constant price
    key = {20: "A", 80: "B", 5: "C", 0: "D"}[mr]
    return {"answer": key, "computed": mr}
