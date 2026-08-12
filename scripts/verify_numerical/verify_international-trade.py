"""Verifier for foundation/business-economics/international-trade.json (P4 Ch 9).

Every function recomputes its answer from the stem's own parameters. Nothing is
copied from the answer key: each computed value is mapped to an option key
through a dict of the four option values, so a wrong key in the bank surfaces as
a KeyError or as a mismatch the runner reports.

Conventions used below:
  * `Fraction` (F) gives exact rational opportunity-cost ratios and conversions;
    no rounding is ever needed, because every stem is built so the exact answer
    is a clean value. Option texts that quote a rounded decimal map to the exact
    fraction they stand for.
  * Opportunity cost of good X in terms of good Y = units of Y given up / units
    of X gained, taken from the two per-resource outputs in the stem.
  * Comparative advantage in a good goes to the country with the LOWER
    opportunity cost of that good; those stems return a country name string.
  * Terms of trade = (export price index / import price index) * 100.
  * A specific tariff adds a fixed sum to the price; an ad valorem tariff
    multiplies the price by (1 + rate).
  * Currency conversion: dollars -> rupees multiplies by the rate; rupees ->
    dollars divides by it. A cross rate multiplies through the common currency.
  * Balance of trade = exports of goods - imports of goods (goods only). The
    current-account balance adds net services, net income and net current
    transfers to the balance of trade.
"""

from __future__ import annotations

from fractions import Fraction as F


# ------------------------------------------------------------ shared helpers


def opportunity_cost(other_given_up, units_gained):
    """Opportunity cost of one unit = other good given up / units of it gained."""
    return F(other_given_up, units_gained)


def terms_of_trade(export_index, import_index):
    """(export price index / import price index) * 100, exact."""
    return F(export_index, import_index) * 100


# ---------------------------------------------- absolute / comparative advantage
# Shared two-country two-good table (output per unit of resources):
#   India:   80 shirts OR 40 kg rice
#   Vietnam: 60 shirts OR 60 kg rice
INDIA = {"shirts": 80, "rice": 40}
VIETNAM = {"shirts": 60, "rice": 60}


def q_f4c9_003():
    # Absolute advantage in shirts = larger shirt output from the same resources.
    winner = "India" if INDIA["shirts"] > VIETNAM["shirts"] else "Vietnam"
    key = {"Vietnam": "A", "India": "B"}[winner]
    return {"answer": key, "computed": "%s (shirts %d vs %d)" % (winner, INDIA["shirts"], VIETNAM["shirts"])}


def q_f4c9_005():
    # Opportunity cost of 1 shirt in India, in kg of rice = rice / shirts.
    oc = opportunity_cost(INDIA["rice"], INDIA["shirts"])  # 40/80 = 1/2
    key = {F(2): "A", F(1): "B", F(1, 2): "C", F(3, 2): "D"}[oc]
    return {"answer": key, "computed": str(oc)}


def q_f4c9_006():
    # Opportunity cost of 1 kg rice in India, in shirts = shirts / rice.
    oc = opportunity_cost(INDIA["shirts"], INDIA["rice"])  # 80/40 = 2
    key = {F(2): "A", F(1, 2): "B", F(1): "C", F(4): "D"}[oc]
    return {"answer": key, "computed": str(oc)}


def q_f4c9_007():
    # Comparative advantage in rice = country with the lower opportunity cost of
    # rice (shirts given up per kg).
    oc_india = opportunity_cost(INDIA["shirts"], INDIA["rice"])      # 2
    oc_vietnam = opportunity_cost(VIETNAM["shirts"], VIETNAM["rice"])  # 1
    winner = "India" if oc_india < oc_vietnam else "Vietnam"
    key = {"India": "A", "Vietnam": "D"}[winner]
    return {"answer": key, "computed": "%s (rice OC: India %s vs Vietnam %s)" % (winner, oc_india, oc_vietnam)}


# ---------------------------------------------------------------- terms of trade


def q_f4c9_011():
    tot = terms_of_trade(120, 96)  # (120/96)*100 = 125
    key = {F(96): "A", F(120): "B", F(125): "C", F(80): "D"}[tot]
    return {"answer": key, "computed": str(tot)}


# -------------------------------------------------------------------- tariffs


def q_f4c9_014():
    # Specific tariff: world price + fixed sum per unit.
    price = 450 + 90
    key = {450: "A", 540: "B", 360: "C", 500: "D"}[price]
    return {"answer": key, "computed": price}


def q_f4c9_015():
    # Ad valorem tariff: value * (1 + rate).
    price = F(1200) * (1 + F(15, 100))  # 1380
    assert price.denominator == 1
    key = {180: "A", 1020: "B", 1215: "C", 1380: "D"}[int(price)]
    return {"answer": key, "computed": int(price)}


# --------------------------------------------------------- currency conversion


def q_f4c9_031():
    # Dollars to rupees: multiply by the rate.
    rupees = 600 * 83
    key = {49800: "A", 49080: "B", "7.23": "C", 4980: "D"}[rupees]
    return {"answer": key, "computed": rupees}


def q_f4c9_032():
    # Rupees to dollars: divide by the rate.
    dollars = F(332000, 83)  # exactly 4000
    assert dollars.denominator == 1
    key = {3320: "A", 2766: "B", 4000: "C", 400: "D"}[int(dollars)]
    return {"answer": key, "computed": int(dollars)}


def q_f4c9_033():
    # Cross rate: (rupees per dollar) * (dollars per pound).
    rupees_per_pound = F(80) * F(5, 4)  # 80 * 1.25 = 100
    key = {F(64): "A", F(100): "B", F(325, 4): "C", F(105): "D"}[rupees_per_pound]
    return {"answer": key, "computed": str(rupees_per_pound)}


# ------------------------------------------------- depreciation effect on flows


def q_f4c9_037():
    # Extra export earnings = dollars * (new rate - old rate).
    extra = 50000 * (85 - 80)
    key = {4000000: "A", 4250000: "B", 500000: "C", 250000: "D"}[extra]
    return {"answer": key, "computed": extra}


def q_f4c9_038():
    # Extra import cost = dollars * (new rate - old rate).
    extra = 100000 * (80 - 78)
    key = {200000: "A", 8000000: "B", 7800000: "C", 100000: "D"}[extra]
    return {"answer": key, "computed": extra}


# --------------------------------------------------------- balance of payments


def q_f4c9_049():
    # Balance of trade = exports of goods - imports of goods.
    bot = 6200 - 7900  # -1700
    state = "surplus" if bot > 0 else "deficit" if bot < 0 else "balanced"
    tag = "%s_%d" % (state, abs(bot))
    key = {"surplus_1700": "A", "deficit_1700": "B", "deficit_14100": "C", "balanced_0": "D"}[tag]
    return {"answer": key, "computed": "BoT = %d (%s)" % (bot, state)}


def q_f4c9_050():
    # Current-account balance = balance of trade + net services + net income
    #                           + net current transfers.
    bot = 600 - 800          # -200
    ca = bot + 250 + (-40) + 90  # +100
    state = "surplus" if ca > 0 else "deficit" if ca < 0 else "balanced"
    tag = "%s_%d" % (state, abs(ca))
    key = {"deficit_200": "A", "deficit_100": "B", "surplus_100": "C", "surplus_300": "D"}[tag]
    return {"answer": key, "computed": "CA = %d (%s)" % (ca, state)}
