"""Verifier for foundation/business-economics/determination-of-national-income.json (P4 Ch 6).

Every function recomputes its answer from the stem's own parameters. Nothing is
copied from the answer key: each computed value is mapped to an option key
through a dict of the four option values, so a wrong key in the bank surfaces as
a KeyError or as a mismatch the runner reports.

Conventions used below:
  * `Fraction` (F) gives exact rational propensities, deflators and prices; no
    rounding is ever needed, because every stem is built so the exact answer is a
    clean value. Option texts that quote a rounded decimal map to the exact
    fraction they stand for.
  * The national income identities follow the standard directions:
      GNP = GDP + net factor income from abroad (NFIA)   -> ADD NFIA
      Net = Gross - depreciation                          -> SUBTRACT depreciation
      Factor cost = Market price - net indirect taxes     -> SUBTRACT net indirect taxes
      Market price = Factor cost + net indirect taxes     -> ADD net indirect taxes
    where net indirect taxes = indirect taxes - subsidies.
  * National Income = NNP at factor cost.
  * GDP deflator = (nominal GDP / real GDP) * 100; real GDP = nominal / deflator * 100.
  * Consumption function C = a + bY, with APC = C/Y, MPC = dC/dY = b.
  * Saving function S = -a + (1 - b)Y, with APS = S/Y, MPS = dS/dY = 1 - b, and
    MPC + MPS = 1, APC + APS = 1.
  * Investment multiplier k = 1 / (1 - MPC) = 1 / MPS, and dY = k * dI.
  * Equilibrium income solves Y = C + I (equivalently S = I).
"""

from __future__ import annotations

from fractions import Fraction as F


# ------------------------------------------------------------ shared helpers


def net_indirect_taxes(indirect_taxes, subsidies):
    """Net indirect taxes = indirect taxes - subsidies."""
    return indirect_taxes - subsidies


def multiplier_from_mpc(mpc):
    """Investment multiplier k = 1 / (1 - MPC)."""
    return F(1) / (F(1) - mpc)


# ------------------------------------------------- national income aggregates


def q_f4c6_004():
    # GNP = GDP + NFIA = 5000 + 200.
    gnp = 5000 + 200
    key = {5200: "A", 4800: "B", 5000: "C", 5400: "D"}[gnp]  # correct 5200 -> A
    return {"answer": key, "computed": gnp}


def q_f4c6_007():
    # NNP = GNP - depreciation = 6000 - 500.
    nnp = 6000 - 500
    key = {500: "A", 5500: "B", 6500: "C", 5000: "D"}[nnp]  # correct 5500 -> B
    return {"answer": key, "computed": nnp}


def q_f4c6_009():
    # Net indirect taxes = 700 - 150.
    nit = net_indirect_taxes(700, 150)
    key = {700: "A", 150: "B", 550: "C", 850: "D"}[nit]  # correct 550 -> C
    return {"answer": key, "computed": nit}


def q_f4c6_010():
    # Market price = factor cost + net indirect taxes = 4000 + 600.
    gdp_mp = 4000 + 600
    key = {3400: "A", 4000: "B", 600: "C", 4600: "D"}[gdp_mp]  # correct 4600 -> D
    return {"answer": key, "computed": gdp_mp}


def q_f4c6_011():
    # NI = NNP at market price - net indirect taxes = 4900 - (500 - 100).
    nit = net_indirect_taxes(500, 100)
    ni = 4900 - nit
    key = {4900: "A", 4500: "B", 5300: "C", 4400: "D"}[ni]  # correct 4500 -> B
    return {"answer": key, "computed": ni}


def q_f4c6_015():
    # Full chain from GDP at market price down to National Income.
    gdp_mp = 8000
    nfia = -100
    depreciation = 700
    indirect_taxes = 900
    subsidies = 200
    gnp_mp = gdp_mp + nfia            # add NFIA
    nnp_mp = gnp_mp - depreciation    # subtract depreciation
    nit = net_indirect_taxes(indirect_taxes, subsidies)
    ni = nnp_mp - nit                 # subtract net indirect taxes
    key = {6600: "A", 5900: "B", 6500: "C", 7200: "D"}[ni]  # correct 6500 -> C
    return {"answer": key, "computed": ni}


def q_f4c6_017():
    # GDP deflator = (nominal / real) * 100 = 6000/5000 * 100.
    deflator = F(6000, 5000) * 100
    key = {F(250, 3): "A", F(100): "B", F(130): "C", F(120): "D"}[deflator]  # correct 120 -> D
    return {"answer": key, "computed": str(deflator)}


def q_f4c6_018():
    # Real GDP = (nominal / deflator) * 100 = 7200/120 * 100.
    real = F(7200) / F(120) * 100
    key = {F(6000): "A", F(8640): "B", F(7200): "C", F(6600): "D"}[real]
    return {"answer": key, "computed": str(real)}


def q_f4c6_020():
    # Per capita income = National Income / population = 500000 / 25.
    per_capita = F(500000, 25)
    assert per_capita.denominator == 1
    key = {25000: "A", 500000: "B", 20000: "C", 12500: "D"}[int(per_capita)]  # correct 20000 -> C
    return {"answer": key, "computed": int(per_capita)}


# ---------------------------------------------------- methods of measurement


def q_f4c6_024():
    # Expenditure method: GDP = C + I + G + (X - M).
    gdp = 3000 + 800 + 1200 + (500 - 400)
    key = {5900: "A", 5000: "B", 4900: "C", 5100: "D"}[gdp]  # correct 5100 -> D
    return {"answer": key, "computed": gdp}


def q_f4c6_025():
    # Income method: rent + wages + interest + profit + mixed income.
    domestic_income = 2500 + 400 + 300 + 600 + 700
    key = {5000: "A", 4500: "B", 3800: "C", 4100: "D"}[domestic_income]  # correct 4500 -> B
    return {"answer": key, "computed": domestic_income}


# ------------------------------------------------- consumption and saving


def q_f4c6_037():
    # APC = C / Y = 800 / 1000.
    apc = F(800, 1000)
    key = {F(4, 5): "A", F(5, 4): "B", F(1, 5): "C", F(2, 25): "D"}[apc]
    return {"answer": key, "computed": str(apc)}


def q_f4c6_038():
    # MPC = dC / dY = 60 / 100.
    mpc = F(60, 100)
    key = {F(2, 5): "A", F(3, 50): "B", F(3, 5): "C", F(5, 3): "D"}[mpc]  # correct 0.6 -> C
    return {"answer": key, "computed": str(mpc)}


def q_f4c6_040():
    # APS = S / Y = (2000 - 1500) / 2000.
    saving = 2000 - 1500
    aps = F(saving, 2000)
    key = {F(3, 4): "A", F(1, 2): "B", F(1, 5): "C", F(1, 4): "D"}[aps]  # correct 0.25 -> D
    return {"answer": key, "computed": str(aps)}


def q_f4c6_041():
    # MPS = 1 - MPC = 1 - 0.75.
    mps = F(1) - F(3, 4)
    key = {F(1, 2): "A", F(1, 4): "B", F(3, 4): "C", F(4, 3): "D"}[mps]  # correct 0.25 -> B
    return {"answer": key, "computed": str(mps)}


# ------------------------------------------------------ multiplier and equilibrium


def q_f4c6_043():
    # k = 1 / (1 - MPC) = 1 / (1 - 0.8).
    k = multiplier_from_mpc(F(4, 5))
    key = {F(5, 4): "A", F(4): "B", F(4, 5): "C", F(5): "D"}[k]  # correct 5 -> D
    return {"answer": key, "computed": str(k)}


def q_f4c6_044():
    # k = 1 / MPS = 1 / 0.25.
    k = F(1) / F(1, 4)
    key = {F(5): "A", F(4, 3): "B", F(4): "C", F(1, 4): "D"}[k]  # correct 4 -> C
    return {"answer": key, "computed": str(k)}


def q_f4c6_045():
    # dY = k * dI, k = 1 / (1 - 0.75) = 4, dI = 200.
    k = multiplier_from_mpc(F(3, 4))
    delta_y = k * 200
    assert delta_y.denominator == 1
    key = {250: "A", 800: "B", 200: "C", 1000: "D"}[int(delta_y)]  # correct 800 -> B
    return {"answer": key, "computed": int(delta_y)}


def q_f4c6_046():
    # Equilibrium: Y = C + I with C = 100 + 0.8Y, I = 100.
    # Y = (100 + 0.8Y) + 100 -> (1 - 0.8)Y = 200 -> Y = 200 / 0.2.
    a = 100
    b = F(4, 5)
    inv = 100
    y = F(a + inv) / (F(1) - b)
    assert y.denominator == 1
    key = {200: "A", 800: "B", 250: "C", 1000: "D"}[int(y)]  # correct 1000 -> D
    return {"answer": key, "computed": int(y)}


def q_f4c6_049():
    # Consumption from the function C = 200 + 0.6Y at Y = 2000.
    c = 200 + F(3, 5) * 2000
    assert c.denominator == 1
    key = {1300: "A", 2000: "B", 1400: "C", 1200: "D"}[int(c)]  # correct 1400 -> C
    return {"answer": key, "computed": int(c)}
