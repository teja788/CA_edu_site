"""Verifier for foundation/accounting/financial-statements-of-not-for-profit-organisations.json (P1 Ch 8).

Each function recomputes the answer from the stem's own parameters —
subscription income in every outstanding/advance permutation (and the reverse
direction), consumables consumed, credit purchases, opening and closing capital
fund, special-fund balances, sale of consumables versus sale of a fixed asset,
and full Receipts & Payments to Income & Expenditure conversions — and then maps
the computed value to the option key. Nothing is copied from the answer key.

Sign conventions used below:
  * subscriptions / expenses: the "belongs-to-this-year" test drives every sign.
    Anything OUTSTANDING at the start is last year's income (or expense) settled
    in this year's cash, so it is DEDUCTED from the cash figure; the same item at
    the END is this year's, not yet in cash, so it is ADDED. Anything received or
    paid in ADVANCE (or PREPAID) reverses those two signs.
  * fund balances: +ve = a credit balance standing on the liabilities side. A
    computed balance that would be negative means the fund is exhausted, and the
    shortfall (its absolute value) is debited to the I&E Account.
  * profit/loss on the sale of a fixed asset: proceeds - book value; +ve = profit
    credited to I&E, -ve = loss debited to I&E. The proceeds themselves are a
    capital receipt and never enter the I&E Account.
  * bank balances: +ve = favourable (debit) balance, -ve = overdraft.
"""


# ------------------------------------------------------- §5 subscriptions


def subscription_income(received, out_start=0, out_end=0, adv_start=0, adv_end=0):
    """Income = Received - Outstanding at start + Outstanding at end
    + Advance at start - Advance at end."""
    return received - out_start + out_end + adv_start - adv_end


def q_f1c8_011():
    income = subscription_income(
        received=2_46_000, out_start=15_000, out_end=21_000, adv_start=8_000, adv_end=5_000
    )
    key = {2_85_000: "A", 2_49_000: "B", 2_37_000: "C", 2_55_000: "D"}[income]
    return {"answer": key, "computed": income}


def q_f1c8_012():
    income = subscription_income(received=1_72_000, out_start=9_500, out_end=14_000)
    key = {1_67_500: "A", 1_76_500: "B", 1_95_500: "C", 1_48_500: "D"}[income]
    return {"answer": key, "computed": income}


def q_f1c8_013():
    income = subscription_income(received=3_10_000, adv_start=12_000, adv_end=18_000)
    key = {3_16_000: "A", 2_80_000: "B", 3_40_000: "C", 3_04_000: "D"}[income]
    return {"answer": key, "computed": income}


def q_f1c8_014():
    # The ₹12,000 of 2024-25 inside the receipts IS the opening outstanding that
    # was collected this year; the ₹9,000 for 2026-27 IS the closing advance.
    income = subscription_income(
        received=2_15_000, out_start=12_000, out_end=17_000, adv_end=9_000
    )
    key = {1_94_000: "A", 2_11_000: "B", 2_35_000: "C", 2_29_000: "D"}[income]
    return {"answer": key, "computed": income}


def q_f1c8_015():
    income = subscription_income(
        received=1_96_000, out_start=11_000, out_end=13_500, adv_start=6_000, adv_end=7_500
    )
    key = {1_83_500: "A", 2_19_000: "B", 1_97_000: "C", 1_85_000: "D"}[income]
    return {"answer": key, "computed": income}


def q_f1c8_016():
    # Reverse direction: re-arrange the same equation for the cash figure.
    income = 2_90_000
    out_start, out_end, adv_start, adv_end = 16_000, 11_000, 7_000, 9_000
    received = income + out_start - out_end - adv_start + adv_end
    # Sanity: running the forward equation on this cash figure must return the income.
    assert subscription_income(received, out_start, out_end, adv_start, adv_end) == income
    key = {2_97_000: "A", 2_83_000: "B", 2_93_000: "C", 2_87_000: "D"}[received]
    return {"answer": key, "computed": received}


def q_f1c8_017():
    # Accrued income comes from the membership roll, not from the cash book.
    accrued = 500 * 600
    received_total = 2_88_000
    for_last_year, for_next_year = 9_000, 6_000
    received_for_this_year = received_total - for_last_year - for_next_year
    outstanding_at_end = accrued - received_for_this_year
    key = {27_000: "A", 12_000: "B", 21_000: "C", 18_000: "D"}[outstanding_at_end]
    return {"answer": key, "computed": outstanding_at_end}


# ------------------------------------------------- §6 consumables consumed


def q_f1c8_018():
    paid_to_creditors = 1_12_000
    cred_open, cred_close = 16_000, 21_500
    credit_purchases = paid_to_creditors + cred_close - cred_open
    total_purchases = credit_purchases + 18_000  # cash purchases
    stock_open, stock_close = 14_000, 11_000
    consumed = stock_open + total_purchases - stock_close
    key = {1_27_500: "A", 1_32_500: "B", 1_38_500: "C", 1_33_000: "D"}[consumed]
    return {"answer": key, "computed": consumed}


def q_f1c8_019():
    stock_open, purchases, stock_close = 22_000, 1_45_000, 19_500
    consumed = stock_open + purchases - stock_close
    key = {1_42_500: "A", 1_47_500: "B", 1_86_500: "C", 1_03_500: "D"}[consumed]
    return {"answer": key, "computed": consumed}


def q_f1c8_020():
    paid, cred_open, cred_close = 58_000, 9_000, 6_500
    credit_purchases = paid + cred_close - cred_open
    key = {60_500: "A", 73_500: "B", 42_500: "C", 55_500: "D"}[credit_purchases]
    return {"answer": key, "computed": credit_purchases}


# ------------------------------------------------------- §7 special receipts


def q_f1c8_028():
    proceeds, book_value = 24_500, 32_000
    result = proceeds - book_value  # -ve => loss debited to I&E
    side = "credited" if result > 0 else "debited"
    key = {
        ("credited", 24_500): "A",
        ("debited", 7_500): "B",
        ("debited", 32_000): "C",
        ("credited", 7_500): "D",
    }[(side, abs(result))]
    return {"answer": key, "computed": f"{abs(result)} {side}"}


def q_f1c8_029():
    # Consumable already expensed -> full proceeds are income.
    old_material = 6_200
    # Fixed asset -> only the result of the sale.
    furniture_result = 21_000 - 18_000  # +ve => profit credited
    credited = old_material + max(furniture_result, 0)
    key = {27_200: "A", 6_200: "B", 3_000: "C", 9_200: "D"}[credited]
    return {"answer": key, "computed": credited}


# ---------------------------------------------------------- §8 special funds


def q_f1c8_032():
    fund = 72_000
    fund += 34_000  # tournament donations: an income OF the fund
    fund += 6_500  # interest on the fund's own investments
    fund -= 88_000  # tournament expenses: an expense OF the fund
    assert fund > 0, "fund survives, so nothing reaches the I&E Account"
    key = {24_500: "A", 1_12_500: "B", 18_000: "C", 72_000: "D"}[fund]
    return {"answer": key, "computed": fund}


def q_f1c8_033():
    available = 40_000 + 15_000 + 3_000  # opening fund + fund donations + fund interest
    prizes = 71_000
    balance = available - prizes  # -ve => the fund is exhausted
    assert balance < 0
    to_ie = -balance  # only the excess is debited to the I&E Account
    key = {13_000: "A", 71_000: "B", 31_000: "C", 16_000: "D"}[to_ie]
    return {"answer": key, "computed": to_ie}


def q_f1c8_034():
    fund = 6_00_000
    fund += 1_50_000  # further building donation, credited to the fund
    utilised = 5_20_000  # transferred OUT of the fund to the capital fund
    fund -= utilised
    key = {7_50_000: "A", 80_000: "B", 2_30_000: "C", 5_20_000: "D"}[fund]
    return {"answer": key, "computed": fund}


# ------------------------------------------------- §9 balance sheet / capital fund


def q_f1c8_037():
    assets = (
        18_500  # cash
        + 1_50_000  # investments
        + 62_000  # furniture
        + 90_000  # books
        + 11_000  # subscriptions outstanding — an ASSET
    )
    liabilities = (
        4_500  # subscriptions received in advance — a LIABILITY
        + 7_000  # salaries outstanding
        + 50_000  # Building Fund — a separate liability, not part of the capital fund
    )
    capital_fund = assets - liabilities
    key = {2_57_000: "A", 2_70_000: "B", 3_20_000: "C", 2_59_000: "D"}[capital_fund]
    return {"answer": key, "computed": capital_fund}


def q_f1c8_038():
    assets = 26_000 + 84_000 + 4_000 + 6_500  # bank, equipment, stock, outstanding subs
    liabilities = 3_000 + 5_500 + 30_000  # advance subs, rent outstanding, Tournament Fund
    capital_fund = assets - liabilities
    key = {1_12_000: "A", 75_000: "B", 1_59_000: "C", 82_000: "D"}[capital_fund]
    return {"answer": key, "computed": capital_fund}


def q_f1c8_039():
    fund = 2_70_000
    fund += 46_500  # surplus (entrance fees of 18,000 are already inside it)
    fund += 25_000  # life membership fees — capitalised
    fund += 40_000  # legacy — capitalised
    key = {3_81_500: "A", 3_99_500: "B", 3_41_500: "C", 3_56_500: "D"}[fund]
    return {"answer": key, "computed": fund}


def q_f1c8_040():
    fund = 1_58_000
    fund += -12_400  # a DEFICIT reduces the fund
    fund += 9_000  # life membership fees — capitalised
    key = {1_79_400: "A", 1_45_600: "B", 1_54_600: "C", 1_36_600: "D"}[fund]
    return {"answer": key, "computed": fund}


# -------------------------------------------------------- §10 R&P -> I&E


def expense_for_the_year(paid, out_start=0, out_end=0, pre_start=0, pre_end=0):
    """Expense = Paid - Outstanding at start + Outstanding at end
    + Prepaid at start - Prepaid at end."""
    return paid - out_start + out_end + pre_start - pre_end


def q_f1c8_042():
    expense = expense_for_the_year(paid=3_36_000, out_start=24_000, out_end=31_000)
    key = {3_43_000: "A", 3_29_000: "B", 3_91_000: "C", 2_81_000: "D"}[expense]
    return {"answer": key, "computed": expense}


def q_f1c8_043():
    expense = expense_for_the_year(paid=96_000, pre_start=6_000, pre_end=9_000)
    key = {99_000: "A", 1_11_000: "B", 81_000: "C", 93_000: "D"}[expense]
    return {"answer": key, "computed": expense}


def q_f1c8_044():
    # Step 3 — re-time the revenue items.
    subscriptions = subscription_income(received=4_20_000, out_start=14_000, out_end=19_000)
    salaries = expense_for_the_year(paid=2_10_000, out_end=9_000)
    material_consumed = 7_000 + 66_000 - 10_000  # opening stock + purchases - closing stock

    # Step 2 — strip the capital items: the legacy (50,000) and the new equipment
    # (75,000) never enter; the furniture proceeds give only the result of sale.
    furniture_result = 9_500 - 12_000  # -ve => loss debited

    income = (
        subscriptions
        + 30_000  # entrance fees — income per the stem's direction
        + 5_000  # sale of old sports material — a consumable, income in full
        + 14_000  # interest on investments
        + 20_000  # general donations
    )
    expenditure = (
        salaries
        + 84_000  # rent
        + material_consumed
        + 18_000  # honorarium
        + 12_000  # printing
        + 11_000  # depreciation — Step 4, a non-cash charge
        + max(-furniture_result, 0)  # loss on sale of furniture
    )
    surplus = income - expenditure
    assert income == 4_94_000 and expenditure == 4_09_500, (income, expenditure)
    key = {1_34_500: "A", 84_500: "B", 96_500: "C", 98_000: "D"}[surplus]
    return {"answer": key, "computed": surplus}


def q_f1c8_045():
    bank = -15_000  # opening OVERDRAFT = a credit balance
    bank += 3_40_000  # receipts
    bank -= 3_02_000  # payments
    nature = "favourable" if bank > 0 else "overdraft"
    key = {
        ("overdraft", 23_000): "A",
        ("favourable", 53_000): "B",
        ("overdraft", 53_000): "C",
        ("favourable", 23_000): "D",
    }[(nature, abs(bank))]
    return {"answer": key, "computed": f"{nature} {abs(bank)}"}
