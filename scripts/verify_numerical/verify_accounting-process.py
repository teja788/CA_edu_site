"""Verifier for foundation/accounting/accounting-process.json (P1 Ch 2).

Each function recomputes the answer from the stem's own parameters — journal
totals, ledger balances, subsidiary-book casts, cash-book columns, imprest
reimbursements, trial-balance columns, suspense balances and effect-on-profit
adjustments — and then maps the computed value to the option key. Nothing is
copied from the answer key.

Sign conventions used below:
  * ledger / cash-book balances: +ve = DEBIT balance, -ve = CREDIT balance
    (a credit balance in the bank column is an overdraft).
  * `debit_shortfall` of a one-sided error: +ve = the trial balance's DEBIT
    column falls SHORT by that much because of the error; -ve = the debit
    column carries that much EXCESS. Suspense is opened on the shorter column,
    so opening suspense (signed) = sum(debit_shortfall). The rectification leg
    that Suspense takes is the mirror image: -debit_shortfall.
  * effect on profit: an adjustment is +ve when rectification RAISES the draft
    profit (an expense wrongly charged, or an income wrongly left out).
"""


# ---------------------------------------------------------------- §3 journal


def q_f1c2_007():
    # Opening entry: capital is the balancing figure = assets - liabilities.
    assets = 12_000 + 58_000 + 90_000 + 45_000 + 35_000  # cash, bank, stock, debtors, furniture
    liabilities = 60_000 + 30_000  # creditors, bank loan
    capital = assets - liabilities
    key = {150_000: "C", 240_000: "A", 330_000: "D", 115_000: "B"}[capital]
    return {"answer": key, "computed": capital}


def q_f1c2_008():
    # Compound entry: Machinery Dr 84,000 = Bank 50,000 + supplier (balance).
    price, paid_by_cheque = 84_000, 50_000
    owed = price - paid_by_cheque
    key = {84_000: "A", 34_000: "D", 50_000: "B", 42_000: "C"}[owed]
    return {"answer": key, "computed": owed}


def q_f1c2_009():
    # Debit column: Cash (capital brought in), Purchases, Farhan (credit sale), Rent.
    debits = [250_000, 30_000, 42_000, 8_000]
    total = sum(debits)
    key = {330_000: "A", 288_000: "B", 322_000: "D", 660_000: "C"}[total]
    return {"answer": key, "computed": total}


# ----------------------------------------------------------------- §4 ledger


def q_f1c2_011():
    # Farhan: Dr credit sale 42,000; Cr returns 4,000 and cash 25,000.
    balance = 42_000 - 4_000 - 25_000  # +ve => debit balance
    side = "Dr" if balance > 0 else "Cr"
    key = {("Dr", 13_000): "C", ("Cr", 13_000): "B", ("Dr", 17_000): "D", ("Dr", 9_000): "A"}[
        (side, abs(balance))
    ]
    return {"answer": key, "computed": f"{side} {abs(balance)}"}


def q_f1c2_012():
    # After the Balance c/d is inserted, BOTH sides total the heavier side's total.
    debit_side = 10_000 + 35_000
    credit_side = 28_000 + 2_000
    ruled_off_total = max(debit_side, credit_side)
    key = {45_000: "D", 30_000: "C", 15_000: "B", 75_000: "A"}[ruled_off_total]
    return {"answer": key, "computed": ruled_off_total}


# ------------------------------------------------------- §5 subsidiary books


def q_f1c2_015():
    # Purchases book takes ONLY credit purchases of goods, entered net of trade discount.
    anand_net = 40_000 - 40_000 * 0.10  # credit purchase of goods, 10% trade discount
    cash_purchase = 0  # 12,000 cash -> cash book, not the purchases book
    computer = 0  # 25,000 credit purchase of an ASSET -> journal proper
    bharat = 18_000  # credit purchase of goods
    total = anand_net + cash_purchase + computer + bharat
    key = {54_000: "C", 58_000: "D", 66_000: "A", 79_000: "B"}[round(total)]
    return {"answer": key, "computed": total}


def q_f1c2_016():
    # Sales book is entered net of TRADE discount only; cash discount is ignored at sale.
    net_of_trade = 50_000 - 50_000 * 0.15
    key = {42_500: "D", 50_000: "A", 41_650: "C", 7_500: "B"}[round(net_of_trade)]
    return {"answer": key, "computed": net_of_trade}


# -------------------------------------------------------------- §6 cash book


def q_f1c2_021():
    # Discount allowed = amount due - amount received, for each debtor.
    bela = 20_000 - 19_600
    chirag = 15_000 - 14_550
    total = bela + chirag
    key = {850: "A", 1_700: "D", 450: "B", 400: "C"}[total]
    return {"answer": key, "computed": total}


def q_f1c2_022():
    # Cash column: opening + receipts - payments; both contra legs hit the cash column.
    cash = 9_000
    cash += 26_500  # cash sales
    cash -= 15_000  # contra: cash deposited into bank
    cash -= 4_800  # wages
    cash += 3_000  # contra: withdrawn from bank for shop use
    cash -= 2_200  # electricity
    key = {16_500: "B", 10_500: "C", 31_500: "A", 13_500: "D"}[cash]
    return {"answer": key, "computed": cash}


def q_f1c2_023():
    # Bank column: opening + receipts - payments; both contra legs hit the bank column.
    bank = 42_000
    bank += 14_700  # cheque from Bela banked same day
    bank += 15_000  # contra: cash deposited
    bank -= 9_800  # cheque to Prakash
    bank -= 3_000  # contra: withdrawal for shop use
    bank -= 250  # bank charges (not a contra)
    key = {58_650: "C", 61_650: "A", 43_650: "D", 58_900: "B"}[bank]
    return {"answer": key, "computed": bank}


def q_f1c2_024():
    # Overdraft opens as a CREDIT balance, so start negative.
    bank = -12_000
    bank += 30_000  # cheques deposited
    bank -= 26_500  # payments by cheque
    nature = "favourable" if bank > 0 else "overdraft"
    key = {
        ("overdraft", 8_500): "D",
        ("favourable", 15_500): "C",
        ("favourable", 8_500): "A",
        ("overdraft", 15_500): "B",
    }[(nature, abs(bank))]
    return {"answer": key, "computed": f"{nature} {abs(bank)}"}


def q_f1c2_025():
    # Contra: cash column debited, bank column credited, both legs inside the cash book.
    cash, bank = 5_000, 40_000
    withdrawal = 10_000
    cash += withdrawal
    bank -= withdrawal
    key = {
        (15_000, 30_000): "A",
        (5_000, 30_000): "D",
        (15_000, 40_000): "B",
        (5_000, 40_000): "C",
    }[(cash, bank)]
    return {"answer": key, "computed": f"cash {cash} / bank {bank}"}


def q_f1c2_026():
    # Cash discount allowed = amount due - cheque received.
    discount = 10_000 - 9_750
    key = {250: "B", 0: "C", 500: "A", 9_750: "D"}[discount]
    return {"answer": key, "computed": discount}


# -------------------------------------------------------------- §7 petty cash


def q_f1c2_031():
    # Imprest: reimbursement = exactly the period's petty expenses.
    expenses = 1_240 + 860 + 1_375 + 525
    key = {4_000: "C", 6_000: "B", 2_000: "D", 10_000: "A"}[expenses]
    return {"answer": key, "computed": expenses}


def q_f1c2_032():
    # Before reimbursement: float - spending. After: back to the imprest.
    imprest, spent = 5_000, 3_720
    before = imprest - spent
    after = before + spent  # the chief cashier reimburses exactly what was spent
    key = {
        (1_280, 5_000): "D",
        (5_000, 5_000): "A",
        (1_280, 1_280): "B",
        (3_720, 5_000): "C",
    }[(before, after)]
    return {"answer": key, "computed": f"{before} before / {after} after"}


# ---------------------------------------------------------- §8 trial balance


def q_f1c2_034():
    # Place each balance on its correct side, then total one column.
    debit_column = (
        150_000  # purchases (expense)
        + 5_000  # returns inward / sales returns
        + 30_000  # cash
        + 80_000  # debtors
        + 39_000  # wages
        + 190_000  # machinery
    )
    credit_column = (
        200_000  # capital
        + 240_000  # sales
        + 4_000  # returns outward / purchase returns
        + 50_000  # creditors
    )
    assert debit_column == credit_column, (debit_column, credit_column)
    key = {494_000: "B", 489_000: "C", 498_000: "D", 988_000: "A"}[debit_column]
    return {"answer": key, "computed": debit_column}


# ------------------------------------------------- §9 rectification / suspense


def q_f1c2_037():
    # Signed debit_shortfall of each one-sided error (+ve = debit column short).
    purchases_undercast = +3_000  # purchases book undercast -> Purchases debit short
    ravi_short_posting = +(5_400 - 4_500)  # Ravi debited 4,500 instead of 5,400
    discount_not_posted = +800  # discount-allowed total never debited
    opening = purchases_undercast + ravi_short_posting + discount_not_posted
    side = "Dr" if opening > 0 else "Cr"  # suspense sits on the SHORTER column
    key = {("Dr", 4_700): "A", ("Cr", 4_700): "C", ("Dr", 3_900): "B", ("Dr", 2_900): "D"}[
        (side, abs(opening))
    ]
    return {"answer": key, "computed": f"{side} {abs(opening)}"}


def q_f1c2_038():
    # Karan should carry a CREDIT of 6,200 but carries a DEBIT of 6,200.
    amount = 6_200
    should_be = -amount  # -ve = credit balance
    actually_is = +amount  # wrongly debited
    correction = should_be - actually_is  # -12,400 => a CREDIT of 12,400 to Karan
    assert correction < 0
    key = {12_400: "B", 6_200: "C", 3_100: "D", 0: "A"}[abs(correction)]
    return {"answer": key, "computed": abs(correction)}


def q_f1c2_039():
    draft = 180_000
    adjustments = [
        -12_000,  # (i) repairs capitalised: an expense is MISSING from the P&L
        -5_000,  # (ii) sales book overcast: income overstated
        +7_000,  # (iii) purchases book overcast: expense overstated
        +15_000,  # (iv) credit sale omitted: income missing
        0,  # (v) stationery in purchases: expense-to-expense swap, net profit unmoved
    ]
    corrected = draft + sum(adjustments)
    key = {185_000: "C", 209_000: "A", 182_500: "D", 170_000: "B"}[corrected]
    return {"answer": key, "computed": corrected}


def q_f1c2_040():
    # Installation wages are capital expenditure: the P&L was charged an expense
    # it should never have carried, so profit was UNDERSTATED by that amount.
    draft = 96_000
    wrongly_charged_expense = 20_000
    corrected = draft + wrongly_charged_expense
    key = {116_000: "D", 76_000: "C", 96_000: "B", 136_000: "A"}[corrected]
    return {"answer": key, "computed": corrected}


def q_f1c2_041():
    # Stationery wrongly in Purchases: +3,000 out of purchases (gross profit up),
    # -3,000 charged as stationery. Net profit is unchanged.
    draft = 125_000
    out_of_purchases = +3_000
    charged_as_stationery = -3_000
    corrected = draft + out_of_purchases + charged_as_stationery
    key = {125_000: "A", 128_000: "B", 122_000: "D", 131_000: "C"}[corrected]
    return {"answer": key, "computed": corrected}


def q_f1c2_042():
    # Opening suspense given in the stem: a DEBIT balance of 600 (+ve).
    opening = +600

    # Each one-sided error, as its signed debit_shortfall:
    purchases_overcast = -3_400  # excess purchases DEBIT => debit column in excess
    meera_not_posted = +4_000  # Meera's debit missing => debit column short

    # Sanity: the difference originally parked in Suspense must equal the sum
    # of the shortfalls of the errors that caused it.
    assert purchases_overcast + meera_not_posted == opening

    # Suspense takes the mirror leg of each rectification.
    suspense_legs = [-purchases_overcast, -meera_not_posted]  # +3,400 Dr and -4,000 Cr
    closing = opening + sum(suspense_legs)

    key = {0: "B", -3_400: "C", +4_000: "A", +600: "D"}[closing]
    label = "nil" if closing == 0 else f"{'Dr' if closing > 0 else 'Cr'} {abs(closing)}"
    return {"answer": key, "computed": label}
