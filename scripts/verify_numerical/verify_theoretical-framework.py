"""Verifier for foundation/accounting/theoretical-framework.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.
"""


def q_f1c1_029():
    # Kavya: cash 5,00,000; shelving 1,20,000 cash; fabric 2,00,000 on credit;
    # sells fabric costing 60,000 for 85,000 cash → total assets
    cash = 500_000 - 120_000 + 85_000
    shelving = 120_000
    stock = 200_000 - 60_000
    total_assets = cash + shelving + stock
    # cross-check the equation: liabilities + capital must equal assets
    liabilities = 200_000
    capital = 500_000 + (85_000 - 60_000)
    assert total_assets == liabilities + capital
    key = {785_000: "A", 525_000: "B", 725_000: "C", 700_000: "D"}[total_assets]
    return {"answer": key, "computed": total_assets}


def q_f1c1_030():
    # Rohan: machinery 3,20,000 + stock 1,50,000 + debtors 90,000 + cash 40,000;
    # creditors 1,10,000 + bank loan 80,000 → capital = assets − liabilities
    assets = 320_000 + 150_000 + 90_000 + 40_000
    liabilities = 110_000 + 80_000
    capital = assets - liabilities
    key = {410_000: "A", 600_000: "B", 490_000: "C", 790_000: "D"}[capital]
    return {"answer": key, "computed": capital}


def q_f1c1_031():
    # Sanjana: closing 3,80,000, opening 3,00,000, drawings 45,000, fresh 50,000
    profit = 380_000 - 300_000 - 50_000 + 45_000
    key = {125_000: "A", -15_000: "B", 80_000: "C", 75_000: "D"}[profit]
    return {"answer": key, "computed": profit}


def q_f1c1_032():
    # Farhan: opening 2,60,000, profit 96,000, fresh 40,000, closing 3,44,000
    drawings = 260_000 + 40_000 + 96_000 - 344_000
    key = {12_000: "A", 52_000: "B", 28_000: "C", 140_000: "D"}[drawings]
    return {"answer": key, "computed": drawings}


def q_f1c1_034():
    # Qureshi: assets 5,00,000, liabilities 1,80,000, capital 3,20,000;
    # pays creditor 30,000 by cheque → both sides fall equally
    assets = 500_000 - 30_000
    liabilities = 180_000 - 30_000
    capital = 320_000  # unchanged
    assert assets == liabilities + capital
    key = {
        (470_000, 150_000): "A",
        (500_000, 150_000): "B",
        (470_000, 180_000): "C",  # option D repeats these totals but drops capital
    }[(assets, liabilities)]
    return {"answer": key, "computed": (assets, liabilities)}


def q_f1c1_036():
    # Arjun Textiles capital expenditure: loom 4,00,000 + carriage 18,000
    # + installation 22,000 + new room 1,50,000 (maintenance 15,000 and
    # repainting 6,000 are revenue and excluded)
    capital_exp = 400_000 + 18_000 + 22_000 + 150_000
    key = {440_000: "A", 611_000: "B", 590_000: "C", 550_000: "D"}[capital_exp]
    return {"answer": key, "computed": capital_exp}


def q_f1c1_037():
    # Menon Motors revenue expenditure: in-use overhaul 48,000 + insurance
    # 12,000 + wages 1,20,000 + whitewashing 8,000 (hydraulic lift 2,20,000
    # is capital and excluded)
    revenue_exp = 48_000 + 12_000 + 120_000 + 8_000
    key = {140_000: "A", 188_000: "B", 408_000: "C", 68_000: "D"}[revenue_exp]
    return {"answer": key, "computed": revenue_exp}


def q_f1c1_039():
    # Prakash Traders capital receipts: van sale 65,000 + bank loan 3,00,000
    # + machinery insurance claim 90,000 + fresh capital 1,50,000
    # (sale of goods 8,20,000 and commission 25,000 are revenue receipts)
    capital_receipts = 65_000 + 300_000 + 90_000 + 150_000
    key = {605_000: "A", 515_000: "B", 630_000: "C", 455_000: "D"}[capital_receipts]
    return {"answer": key, "computed": capital_receipts}


def q_f1c1_041():
    # Bhavna Engineering lathe cost: price 1,80,000 + freight 12,000
    # + pre-use overhaul 35,000 (first-year operating labour 60,000 is revenue)
    cost = 180_000 + 12_000 + 35_000
    key = {192_000: "A", 287_000: "B", 180_000: "C", 227_000: "D"}[cost]
    return {"answer": key, "computed": cost}
