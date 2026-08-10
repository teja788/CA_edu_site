"""Verifier for foundation/business-economics/nature-and-scope-of-business-economics.json (P4 Ch 1).

Business Economics Ch 1 is a concept chapter, so only a handful of questions are
computable. Each function below recomputes its answer from the stem's own
parameters and maps the computed value to an option key through a dict of the
four option values — the key is never hard-coded, so a wrong key in the bank
surfaces as a KeyError or as a mismatch the runner reports.

The two recurring computations are:
  * opportunity cost as the value of the next best alternative forgone, or the
    quantity of one good given up per unit of another (a ratio); and
  * reading opportunity cost off a production-possibility schedule as the fall
    in one good when the other rises by one unit.

`Fraction` is used wherever an exact rational answer is wanted, so that a ratio
such as 2/5 compares exactly with the option value 0.4 without any float error.
"""

from __future__ import annotations

from fractions import Fraction as F


# ---------------------------------------------------------------- shared data

# Rice (tonnes) -> cloth (units) production-possibility schedule used by the
# PPC opportunity-cost questions. Marginal opportunity cost 4, 6, 8, 10 rises.
PPF = {0: 48, 1: 44, 2: 38, 3: 30, 4: 20}


def marginal_costs(schedule):
    """Cloth given up for each successive unit of rice, as an ordered list."""
    xs = sorted(schedule)
    return [schedule[a] - schedule[b] for a, b in zip(xs, xs[1:])]


# ------------------------------------------------------ opportunity cost items


def q_f4c1_025():
    # Opportunity cost of a year in the boutique = salary forgone + interest
    # forgone on the savings (the principal is invested, not given up).
    salary = 360_000
    savings, rate = 150_000, F(10, 100)
    interest = savings * rate
    cost = salary + interest
    key = {F(360_000): "A", F(375_000): "B", F(15_000): "C", F(510_000): "D"}[cost]
    return {"answer": key, "computed": str(cost)}


def q_f4c1_026():
    # Only one crop can be grown; opportunity cost = value of the single BEST
    # forgone alternative, i.e. the maximum over the crops not chosen.
    values = {"wheat": 80_000, "sugarcane": 95_000, "pulses": 70_000}
    chosen = "sugarcane"
    forgone = [v for c, v in values.items() if c != chosen]
    cost = max(forgone)
    key = {70_000: "A", 95_000: "B", 150_000: "C", 80_000: "D"}[cost]
    return {"answer": key, "computed": str(cost)}


# ------------------------------------------------------- PPC opportunity costs


def q_f4c1_031():
    # Opportunity cost of the 3rd tonne of rice = cloth lost moving rice 2 -> 3.
    cost = PPF[2] - PPF[3]
    key = {4: "A", 6: "B", 8: "C", 10: "D"}[cost]
    return {"answer": key, "computed": str(cost)}


def q_f4c1_032():
    # Total cloth given up moving from B (rice 1) to E (rice 4).
    cost = PPF[1] - PPF[4]
    key = {24: "A", 18: "B", 10: "C", 28: "D"}[cost]
    return {"answer": key, "computed": str(cost)}


def q_f4c1_033():
    # Successive opportunity costs as rice rises 0 -> 4, one tonne at a time.
    seq = marginal_costs(PPF)  # [4, 6, 8, 10]
    rising = all(b > a for a, b in zip(seq, seq[1:]))
    label = "rising" if rising else "not rising"
    key = {
        ((10, 8, 6, 4), "falling"): "A",
        ((4, 4, 4, 4), "constant"): "B",
        ((6, 8, 10, 12), "rising"): "C",
        ((4, 6, 8, 10), "rising"): "D",
    }[(tuple(seq), label)]
    return {"answer": key, "computed": "%s (%s)" % (seq, label)}


def q_f4c1_034():
    # Opportunity cost of one scooter = cars given up per scooter gained.
    cars_given_up, scooters_gained = 2, 5
    cost = F(cars_given_up, scooters_gained)  # 2/5 = 0.4 car
    key = {F(5, 2): "A", F(2, 5): "B", F(2): "C", F(5): "D"}[cost]
    return {"answer": key, "computed": str(float(cost))}
