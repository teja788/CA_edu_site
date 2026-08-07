"""Verifier for foundation/accounting/accounts-from-incomplete-records.json (P1 Ch 9).

Every function recomputes its answer from the stem's own parameters and only
then maps the computed value on to an option key through a dict holding all
four option values.  Nothing is copied from the answer key, so a wrong key in
the bank shows up as a mismatch.

The workhorse is `solve()`: a T-account is written out as two dicts (debits and
credits) with exactly ONE value left as None, and the missing figure is
whatever makes the two sides agree.  Every debtors, creditors, bills and cash
book question below is walked that way — opening balance plus additions minus
reductions equals closing balance — rather than by a rearranged formula, so a
mis-sided item in the bank surfaces as a wrong number.

Conventions used below:
  * Net worth (statement of affairs) method:
        profit = closing capital + drawings - further capital - opening capital
    A negative result is a LOSS and the sign is preserved into the option
    lookup (q-f1c9-009 offers signed alternatives).
  * Statement of Affairs: capital = total assets - total liabilities, capital
    being the balancing figure.
  * Total Debtors A/c — DEBIT: opening debtors, credit sales, bills receivable
    dishonoured.  CREDIT: cash received, discount allowed, returns inward, bad
    debts, bills receivable received, set-off to the creditors ledger, closing
    debtors.  Cash sales never appear.
  * Total Creditors A/c — CREDIT: opening creditors, credit purchases, bills
    payable dishonoured.  DEBIT: payments, discount received, returns outward,
    bills payable accepted, set-off from the debtors ledger, closing creditors.
    Cash purchases never appear.
  * Bills Receivable A/c — DEBIT: opening B/R, bills received.  CREDIT:
    collections on maturity, bills discounted, bills endorsed, bills
    dishonoured, closing B/R.
  * Bills Payable A/c — CREDIT: opening B/P, bills accepted.  DEBIT: payments
    on maturity, bills dishonoured, closing B/P.
  * Cash book: opening balance and every receipt on the debit; every payment
    and the closing balance on the credit.  Capital payments and loans go
    through it; only the Profit and Loss items are filtered out later.
  * Memorandum Trading A/c — DEBIT: opening stock, net purchases, direct
    expenses, gross profit.  CREDIT: net sales, closing stock.  A gross profit
    ratio quoted "on sales" gives GP = sales x ratio; a ratio quoted "on cost"
    (mark-up) gives GP = cost x ratio, i.e. sales = cost x (1 + mark-up).
"""

from __future__ import annotations


# --------------------------------------------------------------- the workhorse


def solve(debits: dict, credits: dict) -> float:
    """Balance a T-account written as two dicts with exactly one None value.

    Returns the value that the missing item must take for the two sides of the
    account to agree.  Raising on anything other than exactly one unknown keeps
    a mis-specified account from silently returning a plausible number.
    """
    unknown_d = [k for k, v in debits.items() if v is None]
    unknown_c = [k for k, v in credits.items() if v is None]
    if len(unknown_d) + len(unknown_c) != 1:
        raise ValueError(f"expected exactly one unknown, got {unknown_d + unknown_c}")
    dsum = sum(v for v in debits.values() if v is not None)
    csum = sum(v for v in credits.values() if v is not None)
    return csum - dsum if unknown_d else dsum - csum


def statement_of_affairs_capital(assets: dict, liabilities: dict) -> float:
    """Capital is the balancing figure: assets - liabilities."""
    return sum(assets.values()) - sum(liabilities.values())


def net_worth_profit(*, closing_capital, drawings=0, further_capital=0, opening_capital):
    """+ve = profit, -ve = loss.  Drawings added back, fresh capital taken out."""
    return closing_capital + drawings - further_capital - opening_capital


def cogs_from_margin(sales: float, margin_on_sales: float) -> float:
    """Gross profit quoted as a fraction OF SALES -> cost of goods sold."""
    return sales * (1 - margin_on_sales)


# ------------------------------------- §2 Statement of Affairs -> opening capital


def q_f1c9_005():
    capital = statement_of_affairs_capital(
        assets={
            "cash": 18_000,
            "bank": 62_000,
            "debtors": 1_45_000,
            "stock": 2_10_000,
            "furniture": 75_000,
        },
        liabilities={"creditors": 1_32_000, "bills payable": 28_000, "rent outstanding": 10_000},
    )
    key = {
        3_40_000: "A",
        5_10_000: "B",  # liabilities ignored altogether
        3_50_000: "C",  # outstanding rent not treated as a liability
        3_60_000: "D",  # outstanding rent added to assets as if prepaid
    }[round(capital)]
    return {"answer": key, "computed": capital}


# ------------------------------------------------- §3 net worth method


def q_f1c9_006():
    profit = net_worth_profit(
        closing_capital=6_80_000, drawings=1_20_000, further_capital=0, opening_capital=5_00_000
    )
    key = {
        3_00_000: "C",
        1_80_000: "A",  # drawings ignored (bare increase in capital)
        60_000: "B",  # drawings deducted instead of added
        4_20_000: "D",  # drawings counted twice
    }[round(profit)]
    return {"answer": key, "computed": profit}


def q_f1c9_007():
    drawings = 8_000 * 12  # "Rs 8,000 per month throughout the year"
    profit = net_worth_profit(
        closing_capital=4_90_000,
        drawings=drawings,
        further_capital=50_000,
        opening_capital=3_60_000,
    )
    key = {
        1_76_000: "B",
        2_76_000: "A",  # fresh capital added instead of deducted
        80_000: "C",  # drawings ignored
        88_000: "D",  # Rs 8,000 read as the whole year's drawings
    }[round(profit)]
    return {"answer": key, "computed": profit}


def q_f1c9_008():
    profit = net_worth_profit(
        closing_capital=3_95_000,
        drawings=60_000,
        further_capital=75_000,
        opening_capital=2_40_000,
    )
    key = {
        1_40_000: "D",
        2_90_000: "A",  # fresh capital added instead of deducted
        20_000: "B",  # drawings deducted instead of added
        80_000: "C",  # drawings ignored
    }[round(profit)]
    return {"answer": key, "computed": profit}


def q_f1c9_009():
    profit = net_worth_profit(
        closing_capital=4_10_000,
        drawings=90_000,
        further_capital=40_000,
        opening_capital=5_60_000,
    )
    # Signed: a negative net-worth figure is a loss.  The options are signed too.
    key = {
        -1_00_000: "A",  # loss of 1,00,000
        -1_50_000: "B",  # bare fall in capital, drawings and fresh capital ignored
        -20_000: "C",  # fresh capital added instead of deducted
        1_00_000: "D",  # right magnitude, sign dropped
    }[round(profit)]
    return {"answer": key, "computed": profit}


def q_f1c9_011():
    # Adjustments bite on the CLOSING capital, then the formula is applied once.
    closing = 6_00_000
    closing -= 15_000  # depreciation not provided
    closing -= 9_000  # further bad debts
    closing -= 6_000  # outstanding loan interest
    closing += 12_000  # bill receivable omitted from the assets
    profit = net_worth_profit(
        closing_capital=closing, drawings=1_00_000, further_capital=0, opening_capital=4_50_000
    )
    key = {
        2_32_000: "C",
        2_50_000: "A",  # no adjustments made at all
        2_08_000: "B",  # omitted B/R deducted instead of added
        1_32_000: "D",  # drawings left out of the formula
    }[round(profit)]
    return {"answer": key, "computed": profit}


def q_f1c9_012():
    # Capital A/c walked forward: opening + fresh capital + profit - drawings.
    closing = solve(
        debits={"drawings": 85_000, "closing capital c/d": None},
        credits={"opening capital": 3_20_000, "further capital": 60_000, "net profit": 1_45_000},
    )
    key = {
        4_40_000: "A",
        3_20_000: "B",  # fresh capital deducted instead of added
        6_10_000: "C",  # drawings added instead of deducted
        2_95_000: "D",  # profit omitted
    }[round(closing)]
    return {"answer": key, "computed": closing}


def q_f1c9_013():
    drawings = solve(
        debits={"drawings": None, "closing capital c/d": 3_50_000},
        credits={"opening capital": 2_80_000, "further capital": 45_000, "net profit": 1_60_000},
    )
    key = {
        1_35_000: "D",
        45_000: "A",  # fresh capital deducted instead of added
        2_75_000: "B",  # opening and closing capital swapped
        70_000: "C",  # bare increase in capital
    }[round(drawings)]
    return {"answer": key, "computed": drawings}


def q_f1c9_014():
    further = solve(
        debits={"drawings": 1_20_000, "closing capital c/d": 6_10_000},
        credits={"opening capital": 4_00_000, "further capital": None, "net profit": 1_80_000},
    )
    key = {
        1_50_000: "B",
        30_000: "A",  # drawings ignored
        5_10_000: "C",  # profit added instead of deducted
        2_10_000: "D",  # bare increase in capital
    }[round(further)]
    return {"answer": key, "computed": further}


# ------------------------------------------- §7 Total Debtors Account


def q_f1c9_016():
    credit_sales = solve(
        debits={"opening debtors": 1_20_000, "credit sales": None},
        credits={"cash received": 8_40_000, "discount allowed": 18_000, "closing debtors": 1_55_000},
    )
    key = {
        8_93_000: "A",
        8_75_000: "B",  # discount allowed ignored
        8_57_000: "C",  # discount allowed deducted instead of added
        8_23_000: "D",  # opening and closing debtors swapped
    }[round(credit_sales)]
    return {"answer": key, "computed": credit_sales}


def q_f1c9_017():
    credit_sales = solve(
        debits={"opening debtors": 2_40_000, "credit sales": None},
        credits={
            "cash received": 9_60_000,
            "discount allowed": 22_000,
            "sales returns": 35_000,
            "bad debts": 18_000,
            "B/R received": 1_50_000,
            "closing debtors": 2_85_000,
        },
    )
    key = {
        12_30_000: "D",
        10_80_000: "A",  # bills receivable omitted
        11_60_000: "B",  # sales returns deducted instead of added
        12_12_000: "C",  # bad debts omitted
    }[round(credit_sales)]
    return {"answer": key, "computed": credit_sales}


def q_f1c9_018():
    closing = solve(
        debits={"opening debtors": 1_80_000, "credit sales": 11_40_000},
        credits={
            "cash received": 10_20_000,
            "discount allowed": 25_000,
            "bad debts": 15_000,
            "returns inward": 40_000,
            "closing debtors": None,
        },
    )
    key = {
        2_20_000: "B",
        2_35_000: "A",  # bad debts not deducted
        2_60_000: "C",  # returns inward not deducted
        2_45_000: "D",  # discount allowed not deducted
    }[round(closing)]
    return {"answer": key, "computed": closing}


def q_f1c9_019():
    receipts = solve(
        debits={"opening debtors": 95_000, "credit sales": 6_50_000},
        credits={
            "cash received": None,
            "discount allowed": 12_000,
            "bad debts": 8_000,
            "B/R received": 75_000,
            "closing debtors": 1_30_000,
        },
    )
    key = {
        5_20_000: "C",
        5_95_000: "A",  # bills receivable ignored
        5_40_000: "B",  # discount and bad debts ignored
        4_45_000: "D",  # bills receivable deducted twice
    }[round(receipts)]
    return {"answer": key, "computed": receipts}


def q_f1c9_027():
    # The dishonoured bill is a DEBIT in the debtors account, so it eats into
    # the credit sales that fall out as the balancing figure.
    credit_sales = solve(
        debits={
            "opening debtors": 1_90_000,
            "credit sales": None,
            "B/R dishonoured": 35_000,
        },
        credits={
            "cash received": 7_40_000,
            "discount allowed": 20_000,
            "bad debts": 12_000,
            "B/R received": 3_00_000,
            "closing debtors": 2_25_000,
        },
    )
    key = {
        10_72_000: "C",
        11_07_000: "A",  # dishonour ignored
        11_42_000: "B",  # dishonour put on the credit side instead
        7_72_000: "D",  # bills receivable received omitted
    }[round(credit_sales)]
    return {"answer": key, "computed": credit_sales}


# ----------------------------------------- §8 Total Creditors Account


def q_f1c9_021():
    credit_purchases = solve(
        debits={
            "cash paid": 7_80_000,
            "discount received": 16_000,
            "purchase returns": 24_000,
            "closing creditors": 1_98_000,
        },
        credits={"opening creditors": 1_65_000, "credit purchases": None},
    )
    key = {
        8_53_000: "A",
        8_13_000: "B",  # discount received and purchase returns both ignored
        8_05_000: "C",  # purchase returns deducted instead of added
        8_21_000: "D",  # discount received deducted instead of added
    }[round(credit_purchases)]
    return {"answer": key, "computed": credit_purchases}


def q_f1c9_022():
    payments = solve(
        debits={
            "cash paid": None,
            "discount received": 18_000,
            "purchase returns": 32_000,
            "B/P accepted": 1_60_000,
            "closing creditors": 2_45_000,
        },
        credits={"opening creditors": 2_10_000, "credit purchases": 9_45_000},
    )
    key = {
        7_00_000: "C",
        8_60_000: "A",  # bills payable accepted ignored
        7_50_000: "B",  # discount and returns ignored
        6_68_000: "D",  # purchase returns deducted twice
    }[round(payments)]
    return {"answer": key, "computed": payments}


def q_f1c9_023():
    # The dishonoured acceptance returns to the CREDIT of creditors, so it must
    # be stripped out before the purchases figure is read off.
    credit_purchases = solve(
        debits={
            "cash paid": 6_20_000,
            "discount received": 14_000,
            "purchase returns": 21_000,
            "B/P accepted": 2_00_000,
            "closing creditors": 1_75_000,
        },
        credits={
            "opening creditors": 1_40_000,
            "credit purchases": None,
            "B/P dishonoured": 30_000,
        },
    )
    key = {
        8_60_000: "B",
        8_90_000: "A",  # dishonour ignored
        9_20_000: "C",  # dishonour put on the debit side as well
        6_60_000: "D",  # bills payable accepted omitted
    }[round(credit_purchases)]
    return {"answer": key, "computed": credit_purchases}


# ---------------------------------------------------- §9 bills accounts


def q_f1c9_025():
    br_received = solve(
        debits={"opening B/R": 45_000, "B/R received": None},
        credits={
            "cash collected on maturity": 3_10_000,
            "B/R endorsed": 80_000,
            "B/R dishonoured": 25_000,
            "closing B/R": 62_000,
        },
    )
    key = {
        4_32_000: "A",
        4_07_000: "B",  # dishonoured bills ignored
        3_52_000: "C",  # endorsed bills ignored
        5_22_000: "D",  # opening balance added instead of deducted
    }[round(br_received)]
    return {"answer": key, "computed": br_received}


def q_f1c9_026():
    bp_accepted = solve(
        debits={
            "cash paid on maturity": 2_45_000,
            "B/P dishonoured": 18_000,
            "closing B/P": 72_000,
        },
        credits={"opening B/P": 58_000, "B/P accepted": None},
    )
    key = {
        2_77_000: "B",
        2_59_000: "A",  # dishonoured bills ignored
        2_41_000: "C",  # dishonour deducted instead of added
        3_35_000: "D",  # opening balance never deducted
    }[round(bp_accepted)]
    return {"answer": key, "computed": bp_accepted}


# ------------------------------------------------ §6 cash book reconstruction


def q_f1c9_029():
    cash_sales = solve(
        debits={
            "opening balances b/d": 64_000,
            "received from debtors": 5_80_000,
            "cash sales": None,
        },
        credits={
            "paid to creditors": 4_10_000,
            "salaries": 96_000,
            "rent": 48_000,
            "drawings": 72_000,
            "furniture purchased": 35_000,
            "closing balances c/d": 85_000,
        },
    )
    key = {
        1_02_000: "D",
        1_74_000: "A",  # drawings left out of the payments
        67_000: "B",  # furniture purchase left out of the payments
        2_30_000: "C",  # opening balance added instead of deducted
    }[round(cash_sales)]
    return {"answer": key, "computed": cash_sales}


def q_f1c9_030():
    drawings = solve(
        debits={
            "opening cash b/d": 22_000,
            "cash sales": 3_15_000,
            "received from debtors": 4_60_000,
            "loan taken": 1_00_000,
        },
        credits={
            "paid to creditors": 5_20_000,
            "wages": 1_30_000,
            "general expenses": 64_000,
            "machinery bought": 90_000,
            "drawings": None,
            "closing cash c/d": 18_000,
        },
    )
    key = {
        75_000: "B",
        93_000: "A",  # closing balance not left in the box
        1_65_000: "C",  # machinery treated as drawings
        57_000: "D",  # closing balance deducted twice
    }[round(drawings)]
    return {"answer": key, "computed": drawings}


# ------------------------------- §10 / §11 memorandum trading, ratios


def q_f1c9_033():
    sales = 12_00_000
    gross_profit = sales * 0.25  # "25% ON SALES"
    closing_stock = solve(
        debits={
            "opening stock": 1_40_000,
            "purchases": 9_20_000,
            "carriage inwards": 30_000,
            "gross profit c/d": gross_profit,
        },
        credits={"sales": sales, "closing stock": None},
    )
    key = {
        1_90_000: "D",
        1_60_000: "A",  # carriage inwards left out of the goods available
        1_30_000: "B",  # 25% treated as a mark-up on cost (COGS 9,60,000)
        7_90_000: "C",  # gross profit deducted instead of cost of goods sold
    }[round(closing_stock)]
    return {"answer": key, "computed": closing_stock}


def q_f1c9_034():
    cogs = solve(
        debits={"opening stock": 2_10_000, "purchases": 8_40_000, "wages": 60_000},
        credits={"closing stock": 1_80_000, "cost of goods sold": None},
    )
    sales = cogs / (1 - 0.20)  # 20% margin ON SALES -> cost is 80% of sales
    key = {
        11_62_500: "B",
        11_16_000: "A",  # 20% applied as a mark-up on cost
        7_44_000: "C",  # 80% taken OF the cost instead of cost = 80% of sales
        16_12_500: "D",  # closing stock added instead of deducted
    }[round(sales)]
    return {"answer": key, "computed": sales}


def q_f1c9_035():
    net_sales = 18_00_000
    cogs = cogs_from_margin(net_sales, 0.30)  # 30% ON SALES
    net_purchases = 14_50_000 - 50_000
    stock_on_date_of_fire = solve(
        debits={"opening stock": 3_20_000, "net purchases": net_purchases},
        credits={"cost of goods sold": cogs, "stock on date of fire": None},
    )
    loss = stock_on_date_of_fire - 65_000  # salvage
    key = {
        3_95_000: "C",
        4_60_000: "A",  # salvage never deducted
        4_45_000: "B",  # purchase returns ignored
        3_30_000: "D",  # salvage deducted twice
    }[round(loss)]
    return {"answer": key, "computed": loss}


def q_f1c9_036():
    cost = 6_00_000
    mark_up = 0.25  # ON COST
    sales = cost * (1 + mark_up)
    key = {
        7_50_000: "A",
        8_00_000: "B",  # 25% treated as a margin on sales (cost / 0.75)
        4_50_000: "C",  # mark-up deducted from cost
        7_20_000: "D",  # equivalent 20% margin applied to cost instead of sales
    }[round(sales)]
    return {"answer": key, "computed": sales}


def q_f1c9_038():
    sales = 15_00_000
    cogs = cogs_from_margin(sales, 0.20)  # 20% ON SALES
    purchases = solve(
        debits={
            "opening stock": 2_50_000,
            "purchases": None,
            "carriage inwards": 40_000,
        },
        credits={"closing stock": 3_10_000, "cost of goods sold": cogs},
    )
    key = {
        12_20_000: "C",
        12_60_000: "A",  # carriage inwards omitted, absorbed into purchases
        11_00_000: "B",  # opening and closing stock swapped
        12_70_000: "D",  # 20% read as a mark-up on cost (COGS 12,50,000)
    }[round(purchases)]
    return {"answer": key, "computed": purchases}
