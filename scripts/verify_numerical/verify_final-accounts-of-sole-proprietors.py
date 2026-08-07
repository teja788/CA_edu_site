"""Verifier for foundation/accounting/final-accounts-of-sole-proprietors.json (P1 Ch 7).

Every function recomputes its answer from the stem's own parameters — trading
account casts, cost of goods sold, the adjustment battery, the bad-debts
provision chain, the manager's-commission formulas, capital workings, abnormal
losses and approval-goods reversals — and only then maps the computed value on
to an option key through a dict holding all four option values. Nothing is
copied from the answer key, so a wrong key in the bank shows up as a mismatch.

Conventions used below:
  * Trading Account: gross profit = (net sales + closing stock + cost of stock
    lost otherwise than by sale) − (opening stock + net purchases + direct
    expenses).  Direct expenses are those incurred to bring goods to a saleable
    condition; carriage OUTWARDS, advertising and office salaries are excluded.
  * P&L charge for debtors (the "provision chain"):
        charge = bad_debts_TB + further_bad_debts + new_provision − old_provision
    A NEGATIVE charge is a CREDIT to the P&L (excess provision written back);
    the sign is preserved and carried into the option lookup.
  * The doubtful-debts provision is a percentage of debtors AFTER further bad
    debts.  Any provision for discount on debtors is a percentage of "good
    debtors" = debtors after further bad debts MINUS the doubtful-debts
    provision, i.e. strictly later in the chain.
  * Manager's commission: `rate/100` of the pre-commission profit when the
    entitlement is a % of profit BEFORE charging it, and `rate/(100 + rate)` of
    the same pre-commission profit when it is a % of profit AFTER charging it.
  * Capital working: opening + additional + interest on capital + net profit
    − drawings (cash and in kind, at cost) − interest on drawings.
"""

from __future__ import annotations


# --------------------------------------------------------- helpers (formulas)


def gross_profit(
    *,
    opening_stock: float,
    purchases: float,
    purchase_returns: float = 0,
    direct_expenses: float = 0,
    sales: float,
    sales_returns: float = 0,
    closing_stock: float = 0,
    abnormal_loss_at_cost: float = 0,
) -> float:
    """Trading Account balancing figure, from first principles."""
    net_purchases = purchases - purchase_returns
    net_sales = sales - sales_returns
    debit = opening_stock + net_purchases + direct_expenses
    credit = net_sales + closing_stock + abnormal_loss_at_cost
    return credit - debit


def provision_chain(
    *,
    bad_debts_tb: float = 0,
    further_bad_debts: float = 0,
    new_provision: float,
    old_provision: float = 0,
) -> float:
    """+ve = debit to the P&L; -ve = credit (excess old provision written back)."""
    return bad_debts_tb + further_bad_debts + new_provision - old_provision


def commission_before_charging(net_profit: float, rate: float) -> float:
    return net_profit * rate / 100


def commission_after_charging(net_profit: float, rate: float) -> float:
    return net_profit * rate / (100 + rate)


# ---------------------------------------------- §3 Trading Account computations


def q_f1c7_007():
    # Wages and carriage inwards are DIRECT expenses; both belong on the Trading debit.
    gp = gross_profit(
        opening_stock=62_000,
        purchases=485_000,
        purchase_returns=12_000,
        direct_expenses=14_000 + 38_000,  # carriage inwards + wages
        sales=720_000,
        sales_returns=8_000,
        closing_stock=71_000,
    )
    key = {
        196_000: "B",
        234_000: "A",  # wages treated as indirect
        172_000: "C",  # purchase returns added instead of deducted
        125_000: "D",  # closing stock omitted
    }[round(gp)]
    return {"answer": key, "computed": gp}


def q_f1c7_008():
    # COGS = opening stock + net purchases + direct expenses - closing stock.
    opening, purchases, returns_outward = 45_000, 310_000, 10_000
    carriage_inwards = 9_000  # direct
    carriage_outwards = 0  # selling expense -> excluded from COGS
    closing = 52_000
    cogs = opening + (purchases - returns_outward) + carriage_inwards + carriage_outwards - closing
    key = {
        302_000: "D",
        354_000: "A",  # closing stock not deducted
        309_000: "B",  # carriage outwards wrongly included
        284_000: "C",  # carriage inwards deducted instead of added
    }[round(cogs)]
    return {"answer": key, "computed": cogs}


def q_f1c7_009():
    # Only freight inwards, octroi and factory fuel/power are direct expenses.
    direct = 16_000 + 6_000 + 12_000
    gp = gross_profit(
        opening_stock=90_000,
        purchases=560_000,
        purchase_returns=20_000,
        direct_expenses=direct,
        sales=840_000,
        sales_returns=15_000,
        closing_stock=105_000,
    )
    # carriage outwards 15,000, advertising 22,000 and office salaries 55,000 stay in the P&L
    key = {
        266_000: "A",
        251_000: "B",  # carriage outwards pulled into Trading
        229_000: "C",  # carriage outwards + advertising pulled into Trading
        278_000: "D",  # factory fuel and power left out
    }[round(gp)]
    return {"answer": key, "computed": gp}


def q_f1c7_011():
    # Adjusted purchases have already absorbed opening AND closing stock, so no
    # stock figure enters the Trading Account at all; direct expenses still do.
    adjusted_purchases, closing_stock_in_tb = 615_000, 84_000
    sales, wages, carriage_inwards = 850_000, 40_000, 12_000
    debit = adjusted_purchases + wages + carriage_inwards
    credit = sales  # closing stock is NOT credited again
    gp = credit - debit
    assert closing_stock_in_tb not in (debit, credit)  # it belongs to the balance sheet only
    key = {
        183_000: "B",
        267_000: "A",  # closing stock credited to Trading a second time
        195_000: "C",  # carriage inwards treated as indirect
        99_000: "D",  # closing stock deducted from sales
    }[round(gp)]
    return {"answer": key, "computed": gp}


# ------------------------------------------------- §4 P&L / adjustment battery


def q_f1c7_014():
    salaries = 60_000 + 5_000  # outstanding March salary ADDED
    rent = 48_000 - 8_000  # prepaid portion DEDUCTED
    insurance = 12_000 - 3_000  # prepaid portion DEDUCTED
    carriage_outwards = 14_000  # indirect: a P&L debit
    expenses = salaries + rent + insurance + carriage_outwards

    gross_profit_bd = 240_000
    discount_received = 6_000
    commission_income = 15_000 - 4_000  # received in advance DEDUCTED
    incomes = gross_profit_bd + discount_received + commission_income

    net_profit = incomes - expenses
    key = {
        129_000: "A",
        127_000: "B",  # no adjustment applied at all
        125_000: "C",  # outstanding/prepaid signs reversed, advance left in income
        133_000: "D",  # commission received in advance not deducted
    }[round(net_profit)]
    return {"answer": key, "computed": net_profit}


def q_f1c7_015():
    depreciation_machinery = 400_000 * 0.10
    depreciation_furniture = 60_000 * 0.15
    interest_on_loan = 8_000 + 2_000  # outstanding interest added
    expenses = 72_000 + 9_000 + depreciation_machinery + depreciation_furniture + interest_on_loan

    rent_received = 24_000 + 3_000  # accrued rent added to income
    incomes = 310_000 + rent_received

    net_profit = incomes - expenses
    key = {
        197_000: "B",
        194_000: "A",  # accrued rent omitted
        199_000: "C",  # outstanding interest omitted
        200_000: "D",  # furniture depreciated at 10% instead of 15%
    }[round(net_profit)]
    return {"answer": key, "computed": net_profit}


# ------------------------------------------- §5 balance sheet / capital working


def q_f1c7_017():
    machinery = 300_000 - 300_000 * 0.10  # second effect of depreciation
    closing_stock = 96_000
    debtors = 150_000 - 150_000 * 0.05  # second effect of the provision
    bank = 38_000
    prepaid_insurance = 4_000  # second effect of the prepayment: an asset
    total = machinery + closing_stock + debtors + bank + prepaid_insurance
    key = {
        550_500: "C",
        580_500: "A",  # machinery shown gross
        558_000: "B",  # provision not deducted from debtors
        546_500: "D",  # prepaid insurance omitted
    }[round(total)]
    return {"answer": key, "computed": total}


def q_f1c7_018():
    opening, additional, drawings, net_profit = 500_000, 80_000, 96_000, 142_000
    closing = opening + additional + net_profit - drawings
    key = {
        626_000: "A",
        818_000: "B",  # drawings added instead of deducted
        466_000: "C",  # additional capital deducted instead of added
        546_000: "D",  # additional capital ignored
    }[round(closing)]
    return {"answer": key, "computed": closing}


# -------------------------------------- §6/§9 goods removed otherwise than sold


def q_f1c7_022():
    purchases, returns_outward = 480_000, 18_000
    drawings_in_kind_at_cost = 9_000  # selling price 12,000 is irrelevant
    free_samples_at_cost = 6_000
    trading_purchases = (
        purchases - returns_outward - drawings_in_kind_at_cost - free_samples_at_cost
    )
    key = {
        447_000: "C",
        453_000: "A",  # free samples not deducted
        444_000: "B",  # drawings in kind removed at selling price 12,000
        462_000: "D",  # neither removal deducted
    }[round(trading_purchases)]
    return {"answer": key, "computed": trading_purchases}


def q_f1c7_023():
    cash_drawings = 84_000
    goods_at_cost = 11_000  # NOT the 14,000 selling price
    income_tax = 18_000  # personal cost of a sole trader -> drawings
    lic_premium = 9_000  # personal cost -> drawings
    total = cash_drawings + goods_at_cost + income_tax + lic_premium
    key = {
        122_000: "B",
        95_000: "A",  # income tax and LIC treated as P&L expenses
        125_000: "C",  # goods valued at selling price
        104_000: "D",  # income tax treated as a P&L expense
    }[round(total)]
    return {"answer": key, "computed": total}


# ------------------------------------------------------- §7 the provision chain


def q_f1c7_027():
    debtors_tb, bad_debts_tb, old_provision = 305_000, 9_000, 12_000
    further = 5_000
    base = debtors_tb - further  # write off FIRST, then provide
    new_provision = base * 0.05
    charge = provision_chain(
        bad_debts_tb=bad_debts_tb,
        further_bad_debts=further,
        new_provision=new_provision,
        old_provision=old_provision,
    )
    key = {
        17_000: "B",
        41_000: "A",  # old provision ADDED instead of deducted
        17_250: "C",  # 5% taken on the trial-balance debtors 3,05,000
        8_000: "D",  # trial-balance bad debts omitted
    }[round(charge)]
    return {"answer": key, "computed": charge}


def q_f1c7_028():
    debtors_tb, bad_debts_tb, old_provision = 250_000, 4_000, 26_000
    further = 10_000
    new_provision = (debtors_tb - further) * 0.04
    charge = provision_chain(
        bad_debts_tb=bad_debts_tb,
        further_bad_debts=further,
        new_provision=new_provision,
        old_provision=old_provision,
    )
    side = "debited" if charge > 0 else "credited"
    key = {
        ("credited", 2_400): "D",
        ("debited", 2_400): "B",  # right magnitude, wrong side
        ("debited", 49_600): "A",  # old provision added instead of deducted
        ("credited", 2_000): "C",  # 4% taken on 2,50,000 instead of 2,40,000
    }[(side, round(abs(charge)))]
    return {"answer": key, "computed": f"{side} {abs(charge):,.0f}"}


def q_f1c7_029():
    debtors_tb, further = 186_000, 6_000
    after_write_off = debtors_tb - further
    new_provision = after_write_off * 0.05
    # Bad debts already in the trial balance are NOT deducted from debtors again.
    balance_sheet_figure = after_write_off - new_provision
    key = {
        171_000: "C",
        167_000: "A",  # trial-balance bad debts 4,000 deducted as well
        173_000: "B",  # old provision 7,000 deducted instead of the new one
        170_700: "D",  # 5% taken on 1,86,000
    }[round(balance_sheet_figure)]
    return {"answer": key, "computed": balance_sheet_figure}


def q_f1c7_030():
    debtors_tb, irrecoverable = 260_000, 10_000
    after_write_off = debtors_tb - irrecoverable
    doubtful_provision = after_write_off * 0.05
    good_debtors = after_write_off - doubtful_provision  # discount comes LAST
    new_discount_provision = good_debtors * 0.02
    old_discount_provision = 2_000
    charge = new_discount_provision - old_discount_provision
    key = {
        2_750: "A",
        4_750: "B",  # old discount provision not deducted
        3_000: "C",  # 2% taken before deducting the doubtful-debts provision
        5_200: "D",  # 2% of the full trial-balance debtors, old provision ignored
    }[round(charge)]
    return {"answer": key, "computed": charge}


def q_f1c7_031():
    debtors_tb, bad_debts_tb, old_provision = 320_000, 5_000, 14_000
    further = 20_000
    after_write_off = debtors_tb - further
    doubtful_provision = after_write_off * 0.05
    good_debtors = after_write_off - doubtful_provision
    discount_provision = good_debtors * 0.02  # no old discount provision exists
    total_charge = (
        provision_chain(
            bad_debts_tb=bad_debts_tb,
            further_bad_debts=further,
            new_provision=doubtful_provision,
            old_provision=old_provision,
        )
        + discount_provision
    )
    key = {
        31_700: "D",
        59_700: "A",  # old provision added instead of deducted
        32_000: "B",  # discount taken on 3,00,000, before the doubtful provision
        26_700: "C",  # trial-balance bad debts omitted
    }[round(total_charge)]
    return {"answer": key, "computed": total_charge}


def q_f1c7_032():
    debtors_tb, further = 450_000, 25_000
    after_write_off = debtors_tb - further
    doubtful_provision = after_write_off * 0.06
    good_debtors = after_write_off - doubtful_provision
    discount_provision = good_debtors * 0.02
    balance_sheet_figure = after_write_off - doubtful_provision - discount_provision
    key = {
        391_510: "B",
        391_000: "A",  # discount computed on 4,25,000, before the doubtful provision
        399_500: "C",  # discount provision never deducted
        389_540: "D",  # both provisions computed on 4,50,000
    }[round(balance_sheet_figure)]
    return {"answer": key, "computed": balance_sheet_figure}


# ------------------------------------------------------ §8 manager's commission


def q_f1c7_034():
    net_profit, rate = 420_000, 5
    commission = commission_before_charging(net_profit, rate)
    key = {
        21_000: "A",
        20_000: "B",  # after-charging formula used: 5/105
        19_950: "C",  # 5% of the profit already reduced by a 21,000 commission
        22_105: "D",  # divided by (100 - rate) = 95
    }[round(commission)]
    return {"answer": key, "computed": commission}


def q_f1c7_035():
    net_profit, rate = 462_000, 10
    commission = commission_after_charging(net_profit, rate)
    # Self-check the SM prescribes: commission must equal rate% of the reduced profit.
    assert abs(commission - (net_profit - commission) * rate / 100) < 1e-6
    key = {
        42_000: "B",
        46_200: "A",  # rate% of the profit BEFORE charging
        41_580: "C",  # one manual iteration instead of the closed formula
        51_333: "D",  # divided by (100 - rate) = 90
    }[round(commission)]
    return {"answer": key, "computed": commission}


def q_f1c7_036():
    gross_profit_bd, indirect_expenses = 500_000, 164_000
    rate = 12
    net_profit_before = gross_profit_bd - indirect_expenses
    commission = commission_after_charging(net_profit_before, rate)
    net_profit_after = net_profit_before - commission
    assert abs(commission - net_profit_after * rate / 100) < 1e-6  # self-check
    key = {
        300_000: "D",
        336_000: "A",  # commission never deducted
        295_680: "B",  # before-charging commission (12% of 3,36,000) deducted
        264_000: "C",  # the 36,000 commission deducted twice
    }[round(net_profit_after)]
    return {"answer": key, "computed": net_profit_after}


# --------------------------------------------------- §9 abnormal loss / approval


def q_f1c7_038():
    cost_of_goods_lost, claim_admitted = 85_000, 58_000
    abnormal_loss_to_pl = cost_of_goods_lost - claim_admitted
    key = {
        27_000: "C",
        85_000: "A",  # whole cost charged to the P&L, claim ignored
        58_000: "B",  # the claim, which is an ASSET, not the loss
        0: "D",  # "nil" — Trading credit mistaken for the whole treatment
    }[round(abnormal_loss_to_pl)]
    return {"answer": key, "computed": abnormal_loss_to_pl}


def q_f1c7_039():
    # The FULL cost of the stolen stock is credited to Trading; the insured /
    # uninsured split happens afterwards and never touches gross profit.
    cost_stolen, claim_admitted = 40_000, 25_000
    gp = gross_profit(
        opening_stock=70_000,
        purchases=520_000,
        direct_expenses=30_000,  # wages
        sales=710_000,
        closing_stock=60_000,
        abnormal_loss_at_cost=cost_stolen,
    )
    assert cost_stolen - claim_admitted == 15_000  # the P&L debit, outside gross profit
    key = {
        190_000: "B",
        150_000: "A",  # no Trading credit for the stolen stock
        165_000: "C",  # only the uninsured 15,000 credited
        175_000: "D",  # only the admitted claim 25,000 credited
    }[round(gp)]
    return {"answer": key, "computed": gp}


def q_f1c7_041():
    sales_tb = 960_000
    approval_at_invoice_value = 45_000  # sales were recorded at invoice value
    corrected_sales = sales_tb - approval_at_invoice_value
    key = {
        915_000: "C",
        924_000: "A",  # cost 36,000 deducted instead of invoice value
        960_000: "B",  # no reversal at all
        951_000: "D",  # only the 9,000 margin removed
    }[round(corrected_sales)]
    return {"answer": key, "computed": corrected_sales}


def q_f1c7_042():
    stock_counted, debtors_tb = 128_000, 215_000
    approval_invoice_value, approval_cost = 50_000, 40_000
    closing_stock = stock_counted + approval_cost  # back at COST
    debtors = debtors_tb - approval_invoice_value  # out at SELLING price
    key = {
        (168_000, 165_000): "A",
        (178_000, 165_000): "B",  # stock brought back at selling price
        (168_000, 175_000): "C",  # cost deducted from debtors instead of invoice value
        (128_000, 165_000): "D",  # stock never brought back
    }[(round(closing_stock), round(debtors))]
    return {"answer": key, "computed": f"stock {closing_stock:,.0f} / debtors {debtors:,.0f}"}


# ---------------------------------------------- §10 capital with interest items


def q_f1c7_044():
    opening, additional = 600_000, 100_000
    cash_drawings, goods_drawn_at_cost = 120_000, 15_000
    interest_on_capital, interest_on_drawings = 36_000, 4_500
    profit_before_interest_items = 230_000

    # Interest on capital is a P&L DEBIT; interest on drawings a P&L CREDIT.
    net_profit = profit_before_interest_items - interest_on_capital + interest_on_drawings

    closing_capital = (
        opening
        + additional
        + interest_on_capital  # second effect: added to capital
        + net_profit
        - (cash_drawings + goods_drawn_at_cost)
        - interest_on_drawings  # second effect: deducted from capital
    )
    # Both interest items are internal, so they must cancel out overall:
    assert closing_capital == opening + additional + profit_before_interest_items - (
        cash_drawings + goods_drawn_at_cost
    )
    key = {
        795_000: "B",
        810_000: "A",  # goods withdrawn (15,000) omitted from drawings
        759_000: "C",  # interest on capital charged but never added back to capital
        804_000: "D",  # interest on drawings added to capital instead of deducted
    }[round(closing_capital)]
    return {"answer": key, "computed": closing_capital}


# --------------------------------------------------------- full battery (Ch 7)


def q_f1c7_045():
    # (i)-(vi) applied in order, each with both of its effects.
    opening_stock, purchases = 74_000, 530_000
    wages = 46_000 + 4_000  # (iii) outstanding wages added
    closing_stock = 88_000  # (i)
    sales = 760_000
    gp = gross_profit(
        opening_stock=opening_stock,
        purchases=purchases,
        direct_expenses=wages,
        sales=sales,
        closing_stock=closing_stock,
    )
    assert gp == 194_000

    salaries = 68_000
    rent = 24_000 - 3_000  # (iv) prepaid rent deducted
    depreciation = 100_000 * 0.10  # (ii) furniture

    # (v) the provision chain: no bad debts inside the trial balance here.
    further_bad_debts = 5_000
    debtors_after = 165_000 - further_bad_debts
    new_provision = debtors_after * 0.05
    debtors_charge = provision_chain(
        bad_debts_tb=0,
        further_bad_debts=further_bad_debts,
        new_provision=new_provision,
        old_provision=6_000,
    )

    net_profit_before_commission = gp - salaries - rent - depreciation - debtors_charge
    commission = commission_after_charging(net_profit_before_commission, 10)  # (vi)
    net_profit = net_profit_before_commission - commission
    assert abs(commission - net_profit * 0.10) < 1e-6  # self-check

    key = {
        80_000: "C",
        88_000: "A",  # commission not provided for
        79_200: "B",  # before-charging commission (10% of 88,000) deducted
        35_000: "D",  # drawings 45,000 wrongly deducted from net profit
    }[round(net_profit)]
    return {"answer": key, "computed": net_profit}
