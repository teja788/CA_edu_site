"""Verifier for foundation/accounting/depreciation-and-amortisation.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.
"""


def q_f1c5_001():
    # SLM: cost 3,10,000, residual 10,000, life 5
    charge = (310_000 - 10_000) / 5
    key = {62_000: "A", 60_000: "B", 64_000: "C", 50_000: "D"}[charge]
    return {"answer": key, "computed": charge}


def q_f1c5_002():
    # Depreciable amount: price 5,00,000 + freight 20,000 + installation 40,000 − scrap 60,000
    amount = 500_000 + 20_000 + 40_000 - 60_000
    key = {560_000: "A", 500_000: "B", 440_000: "C", 540_000: "D"}[amount]
    return {"answer": key, "computed": amount}


def q_f1c5_003():
    # SLM rate on cost: cost 2,00,000, residual 20,000, life 9
    charge = (200_000 - 20_000) / 9
    rate_pct = round(charge / 200_000 * 100, 2)
    key = {10.0: "A", 11.11: "B", 12.5: "C", 9.09: "D"}[rate_pct]
    return {"answer": key, "computed": rate_pct}


def q_f1c5_004():
    # WDV year 2: cost 5,00,000 @10%
    wdv1 = 500_000 * 0.9
    y2 = wdv1 * 0.10
    key = {50_000: "A", 45_000: "B", 40_500: "C", 47_500: "D"}[y2]
    return {"answer": key, "computed": y2}


def q_f1c5_005():
    # WDV closing after 3 years: 1,00,000 @20%
    value = 100_000 * 0.8**3
    key = {40_000: "A", 51_200: "B", 48_800: "C", 64_000: "D"}[round(value)]
    return {"answer": key, "computed": value}


def q_f1c5_006():
    # WDV rate: cost 8,00,000 → residual 1,00,000 in 3 years
    rate_pct = round((1 - (100_000 / 800_000) ** (1 / 3)) * 100, 2)
    key = {50.0: "A", 29.17: "B", 12.5: "C", 87.5: "D"}[rate_pct]
    return {"answer": key, "computed": rate_pct}


def q_f1c5_007():
    # Units method: (3,50,000 − 50,000) × 24,000/1,50,000
    charge = (350_000 - 50_000) * 24_000 / 150_000
    key = {56_000: "A", 48_000: "B", 60_000: "C", 70_000: "D"}[charge]
    return {"answer": key, "computed": charge}


def q_f1c5_008():
    # Pro-rata: 2,50,000 × 12% × 9/12 (1 Jul → 31 Mar)
    charge = 250_000 * 0.12 * 9 / 12
    key = {30_000: "A", 22_500: "B", 15_000: "C", 25_000: "D"}[charge]
    return {"answer": key, "computed": charge}


def q_f1c5_009():
    # SLM 10% on 4,00,000 from 1 Apr 2022; sold 30 Sep 2024 for 3,20,000
    dep = 40_000 + 40_000 + 40_000 * 6 / 12
    result = 320_000 - (400_000 - dep)  # +ve = profit
    key = {20_000: "A", -80_000: "B", 40_000: "C", 0: "D"}[result]
    return {"answer": key, "computed": result}


def q_f1c5_010():
    # WDV 25% on 6,40,000, two full years, sold 4,00,000
    wdv = 640_000 * 0.75**2
    result = 400_000 - wdv
    key = {40_000: "A", -240_000: "B", 80_000: "C", -40_000: "D"}[round(result)]
    return {"answer": key, "computed": result}


def q_f1c5_011():
    # Revision: cost 9,00,000, residual 60,000, life 7, 4 years charged;
    # revised total life 6, revised residual 20,000
    old_charge = (900_000 - 60_000) / 7
    carrying = 900_000 - 4 * old_charge
    charge = (carrying - 20_000) / (6 - 4)
    key = {120_000: "A", 200_000: "B", 210_000: "C", 180_000: "D"}[round(charge)]
    return {"answer": key, "computed": charge}


def q_f1c5_012():
    # Method change: 5,00,000 @20% WDV × 2 yrs → SLM, remaining 4, residual 40,000
    wdv = 500_000 * 0.8**2
    charge = (wdv - 40_000) / 4
    key = {70_000: "A", 80_000: "B", 76_667: "C", 64_000: "D"}[round(charge)]
    return {"answer": key, "computed": charge}


def q_f1c5_013():
    # Revision: cost 6,00,000, nil residual, life 10, 6 years charged, 2 more years
    carrying = 600_000 - 6 * (600_000 / 10)
    charge = carrying / 2
    key = {60_000: "A", 120_000: "B", 80_000: "C", 30_000: "D"}[charge]
    return {"answer": key, "computed": charge}


def q_f1c5_014():
    # Provision balance after 4 years: (2,40,000 − 40,000)/10 × 4
    balance = (240_000 - 40_000) / 10 * 4
    key = {80_000: "A", 96_000: "B", 160_000: "C", 60_000: "D"}[balance]
    return {"answer": key, "computed": balance}


def q_f1c5_015():
    # Machine hours: (4,20,000 − 20,000) × 2,500/20,000
    charge = (420_000 - 20_000) * 2_500 / 20_000
    key = {52_500: "A", 50_000: "B", 40_000: "C", 42_000: "D"}[charge]
    return {"answer": key, "computed": charge}


def q_f1c5_016():
    # WDV year 3: cost 2,00,000 @10%
    y3 = 200_000 * 0.9**2 * 0.10
    key = {20_000: "A", 16_200: "B", 18_000: "C", 14_580: "D"}[round(y3)]
    return {"answer": key, "computed": y3}


def q_f1c5_017():
    # Amortisation: 1,50,000 / 10
    charge = 150_000 / 10
    key = {15_000: "A", 30_000: "C", 150_000: "D"}.get(charge, "B")
    return {"answer": key, "computed": charge}


def q_f1c5_018():
    # Depletion: 50,00,000 × 15,000/2,00,000
    charge = 5_000_000 * 15_000 / 200_000
    key = {375_000: "A", 250_000: "B", 750_000: "C", 500_000: "D"}[charge]
    return {"answer": key, "computed": charge}


def q_f1c5_019():
    # Provision-method disposal: cost 3,00,000, provision 1,10,000, sold 1,75,000
    result = 175_000 - (300_000 - 110_000)  # −ve = loss
    key = {-15_000: "A", -125_000: "B", 65_000: "C", 15_000: "D"}[result]
    return {"answer": key, "computed": result}


def q_f1c5_020():
    # Lifetime total = depreciable amount: 5,00,000 − 50,000
    total = 500_000 - 50_000
    key = {450_000: "A", 500_000: "B", 75_000: "C", 550_000: "D"}[total]
    return {"answer": key, "computed": total}


def q_f1c5_021():
    # Reverse: charge 36,000, life 8, residual 12,000 → cost
    cost = 36_000 * 8 + 12_000
    key = {300_000: "A", 288_000: "B", 276_000: "C", 372_000: "D"}[cost]
    return {"answer": key, "computed": cost}


def q_f1c5_022():
    # WDV book value after 2 years: 2,50,000 @20%
    value = 250_000 * 0.8**2
    key = {160_000: "A", 150_000: "B", 200_000: "C", 128_000: "D"}[round(value)]
    return {"answer": key, "computed": value}


def q_f1c5_023():
    # SLM 10% on 1,80,000 from 1 Apr 2023; sold 31 Dec 2025 for 1,25,000
    dep = 18_000 + 18_000 + 18_000 * 9 / 12
    result = 125_000 - (180_000 - dep)  # −ve = loss
    key = {-5_500: "A", -55_000: "B", -1_000: "C", 5_500: "D"}[round(result)]
    return {"answer": key, "computed": result}


def q_f1c5_024():
    # Cost build-up then WDV 25%: (3,00,000 + 20,000 + 16,000) × 25%; maintenance excluded
    cost = 300_000 + 20_000 + 16_000
    charge = cost * 0.25
    key = {75_000: "A", 80_000: "B", 84_000: "C", 89_000: "D"}[charge]
    return {"answer": key, "computed": charge}
