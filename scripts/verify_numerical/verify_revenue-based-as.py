"""Verifier for intermediate/advanced-accounting/revenue-based-as.json.

Each function recomputes the answer from the parameters stated in the stem and
maps the computed value onto the option key. Nothing is copied from the bank's
answer key.

Recurring Ch 8 mechanics (SM Ch 8 U1–U2):
  AS 7 contract revenue   agreed price + escalation actually passed on by the
                          clause + approved variations + claims/incentives ONLY
                          where probable and reliably measurable − penalties
  AS 7 contract cost      direct + allocable costs, LESS incidental income not
                          forming part of contract revenue (surplus material,
                          plant sold at the end); general administration and R&D
                          without a reimbursement clause, selling costs and
                          idle-plant depreciation are excluded
  AS 7 stage (cost basis) costs of work performed to date ÷ estimated total
                          contract cost, with costs relating to FUTURE activity
                          (materials at site, unused) taken out of the numerator
                          and left out of the total as well
  AS 7 revenue/profit     revenue = contract price × stage, cumulative; the
                          period figure is the cumulative figure less what was
                          recognised in earlier periods
  AS 7 expected loss      total expected cost > contract revenue → the WHOLE
                          loss is expensed at once; the provision is the loss
                          less the loss already carried by the period's own
                          revenue-less-cost figures
  AS 7 outcome unreliable revenue = contract costs incurred whose recovery is
                          probable; all contract costs incurred are expensed
  AS 7 due from/to        costs incurred + recognised profits − recognised
                          losses − progress billings; positive = due FROM
                          customers, negative = due TO customers (advances and
                          retentions are disclosed separately)
  AS 9 agent              revenue = the entity's own charge; the principal's
                          share and indirect taxes collected are not revenue
  AS 9 approval sales     revenue on acceptance, an adopting act, or lapse of
                          the rejection period — not on despatch
  AS 9 consignment        revenue = the price at which the consignee sells to
                          third parties (not the pro-forma invoice value); the
                          consignee's commission is an expense
  AS 9 discounts          trade discounts and volume rebates are deducted in
                          determining revenue; cash discounts are an expense
  AS 9 interest/royalty   interest = amount outstanding × rate × time held;
                          royalty accrues on the licensee's sales per the
                          agreement, whatever has been collected

Treatment-sensitive questions (q-i1c8-016 and cs-i1c8-02-d) map tuples — the
rupee figure alone is not unique across their options.
"""


def _pick(options, value, tolerance=0.01):
    """Map a computed value to its option key (amounts may carry decimals)."""
    for key, v in options.items():
        if isinstance(v, tuple) or isinstance(value, tuple):
            if v == value:
                return key
            continue
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value} matches no option in {options}")


# ── AS 7 · contract revenue ──────────────────────────────────────────────

def q_i1c8_007():
    # 1,200 price; clause passes 40% of the 50 material increase; 45 variation
    # approved; 30 incentive probable + measurable; 18 claim NOT probable
    price = 1200
    escalation = 0.40 * 50
    variation = 45
    incentive = 30                      # probable and reliably measurable
    claim = 0                           # acceptance not probable → excluded
    revenue = price + escalation + variation + incentive + claim
    key = _pick({"A": 1325, "B": 1295, "C": 1313, "D": 1265}, revenue)
    return {"answer": key, "computed": revenue}


def q_i1c8_009():
    # 600 price; 50% of the 36 material increase; whole labour increase passes
    # because the 20% wage rise is within the 25% ceiling; 14 incentive not
    # probable → excluded
    price = 600
    material_escalation = 0.50 * 36
    wage_rise, ceiling, labour_estimate = 0.20, 0.25, 80
    labour_escalation = labour_estimate * wage_rise if wage_rise <= ceiling else 0
    incentive = 0
    revenue = price + material_escalation + labour_escalation + incentive
    key = _pick({"A": 652, "B": 634, "C": 618, "D": 648}, revenue)
    return {"answer": key, "computed": revenue}


# ── AS 7 · contract costs ────────────────────────────────────────────────

def q_i1c8_011():
    direct = 180 + 240 + 60 + 25        # labour, materials, depreciation, hire
    allocable = 20                      # insurance allocable to the contract
    incidental_income = 8               # surplus materials sold → credit
    excluded = 28 + 15 + 12             # admin (no reimbursement), selling, idle plant
    cost = direct + allocable - incidental_income
    assert excluded == 55
    key = _pick({"A": 572, "B": 517, "C": 525, "D": 545}, cost)
    return {"answer": key, "computed": cost}


# ── AS 7 · percentage of completion ──────────────────────────────────────

def q_i1c8_016():
    # outcome not reliably estimable: revenue = probably recoverable costs,
    # ALL costs incurred expensed
    costs_incurred = 260
    recoverable = 230
    revenue, expense = recoverable, costs_incurred
    computed = (f"rev{revenue:.0f}", f"exp{expense:.0f}")
    key = _pick({"A": ("rev260", "exp260"), "B": ("rev0", "exp260"),
                 "C": ("rev230", "exp230"), "D": ("rev230", "exp260")}, computed)
    return {"answer": key, "computed": computed}


def q_i1c8_017():
    # whole expected loss expensed at once, whatever the stage
    price, incurred, to_complete = 800, 360, 540
    loss = (incurred + to_complete) - price
    key = _pick({"A": 60, "B": 0, "C": 100, "D": 40}, loss)
    return {"answer": key, "computed": loss}


def q_i1c8_018():
    price = 1000
    costs_to_date = 450 - 50            # unused site materials are future activity
    total_cost = costs_to_date + 400
    revenue = price * costs_to_date / total_cost
    key = _pick({"A": 500, "B": 562.5, "C": 450, "D": 400}, revenue)
    return {"answer": key, "computed": revenue}


# ── AS 9 · agency, goods, discounts ──────────────────────────────────────

def q_i1c8_026():
    collected, restaurants, delivery, gst = 960_000, 720_000, 180_000, 60_000
    assert collected == restaurants + delivery + gst
    revenue = delivery                  # agent: only its own charge
    key = _pick({"A": 960_000, "B": 900_000, "C": 240_000, "D": 180_000}, revenue)
    return {"answer": key, "computed": revenue}


def q_i1c8_031():
    accepted, lapsed, still_open = 350_000, 150_000, 100_000
    assert accepted + lapsed + still_open == 600_000
    revenue = accepted + lapsed
    key = _pick({"A": 450_000, "B": 500_000, "C": 350_000, "D": 600_000}, revenue)
    return {"answer": key, "computed": revenue}


def q_i1c8_034():
    # revenue = the consignee's sale to third parties, gross of commission
    sold_to_customers, commission = 480_000, 24_000
    revenue = sold_to_customers
    assert sold_to_customers - commission == 456_000
    key = _pick({"A": 480_000, "B": 500_000, "C": 456_000, "D": 375_000}, revenue)
    return {"answer": key, "computed": revenue}


def q_i1c8_035():
    gross, trade_rate, rebate, cash_discount = 2_500_000, 0.06, 40_000, 18_000
    revenue = gross - gross * trade_rate - rebate      # cash discount is an expense
    assert cash_discount == 18_000
    key = _pick({"A": 2_292_000, "B": 2_350_000, "C": 2_500_000, "D": 2_310_000}, revenue)
    return {"answer": key, "computed": revenue}


# ── AS 9 · interest and royalties ────────────────────────────────────────

def q_i1c8_037():
    principal, rate, months_held = 2_400_000, 0.12, 8    # 1 Aug to 31 Mar
    interest = principal * rate * months_held / 12
    key = _pick({"A": 192_000, "B": 288_000, "C": 216_000, "D": 0}, interest)
    return {"answer": key, "computed": interest}


def q_i1c8_038():
    net_sales, rate, received = 9_000_000, 0.05, 210_000
    royalty = net_sales * rate          # accrual, not receipts
    assert royalty - received == 240_000
    key = _pick({"A": 210_000, "B": 240_000, "C": 0, "D": 450_000}, royalty)
    return {"answer": key, "computed": royalty}


# ── case set 01 · Vindhya Infrastructure (three-year progression) ─────────

_V_PRICE = 2000
_V_Y1_COSTS, _V_Y1_TO_COMPLETE = 400, 1200
_V_Y2_COSTS, _V_Y2_TO_COMPLETE = 960, 640
_V_TOTAL_ACTUAL = 1650


def _vindhya_year1():
    total = _V_Y1_COSTS + _V_Y1_TO_COMPLETE
    stage = _V_Y1_COSTS / total
    revenue = _V_PRICE * stage
    return revenue, revenue - _V_Y1_COSTS


def _vindhya_year2():
    total = _V_Y2_COSTS + _V_Y2_TO_COMPLETE
    cumulative_revenue = _V_PRICE * (_V_Y2_COSTS / total)
    revenue = cumulative_revenue - _vindhya_year1()[0]
    costs = _V_Y2_COSTS - _V_Y1_COSTS
    return revenue, revenue - costs


def cs_i1c8_01_a():
    revenue = _vindhya_year1()[0]
    key = _pick({"A": 0, "B": 500, "C": 400, "D": 100}, revenue)
    return {"answer": key, "computed": revenue}


def cs_i1c8_01_b():
    profit = _vindhya_year1()[1]
    key = _pick({"A": 100, "B": 400, "C": 500, "D": 0}, profit)
    return {"answer": key, "computed": profit}


def cs_i1c8_01_c():
    revenue = _vindhya_year2()[0]
    key = _pick({"A": 700, "B": 1200, "C": 560, "D": 900}, revenue)
    return {"answer": key, "computed": revenue}


def cs_i1c8_01_d():
    total_profit = _V_PRICE - _V_TOTAL_ACTUAL
    already = _vindhya_year1()[1] + _vindhya_year2()[1]
    profit = total_profit - already
    # cross-check against the year-3 revenue and cost figures
    y3_revenue = _V_PRICE - (_vindhya_year1()[0] + _vindhya_year2()[0])
    y3_cost = _V_TOTAL_ACTUAL - _V_Y2_COSTS
    assert abs((y3_revenue - y3_cost) - profit) < 1e-9
    key = _pick({"A": 110, "B": 350, "C": 210, "D": 140}, profit)
    return {"answer": key, "computed": profit}


# ── case set 02 · Konkan Constructions (loss contract) ────────────────────

_K_PRICE = 1500
_K_COSTS_INCURRED, _K_MATERIALS_AT_SITE, _K_TO_COMPLETE = 640, 40, 1000
_K_BILLINGS, _K_ADVANCES, _K_RETENTION = 700, 90, 70


def _konkan():
    work_done_cost = _K_COSTS_INCURRED - _K_MATERIALS_AT_SITE
    total_cost = work_done_cost + _K_TO_COMPLETE
    stage = work_done_cost / total_cost
    revenue = _K_PRICE * stage
    expected_loss = max(0.0, total_cost - _K_PRICE)
    loss_in_period = work_done_cost - revenue       # cost charged less revenue
    provision = expected_loss - loss_in_period
    return work_done_cost, revenue, expected_loss, provision


def cs_i1c8_02_a():
    work_done_cost = _konkan()[0]
    key = _pick({"A": 640, "B": 560, "C": 680, "D": 600}, work_done_cost)
    return {"answer": key, "computed": work_done_cost}


def cs_i1c8_02_b():
    revenue = _konkan()[1]
    key = _pick({"A": 600, "B": 640, "C": 937.5, "D": 562.5}, revenue)
    return {"answer": key, "computed": revenue}


def cs_i1c8_02_c():
    provision = _konkan()[3]
    key = _pick({"A": 62.5, "B": 100, "C": 37.5, "D": 0}, provision)
    return {"answer": key, "computed": provision}


def cs_i1c8_02_d():
    work_done_cost, _, expected_loss, _ = _konkan()
    recognised_profits = 0
    net = work_done_cost + recognised_profits - expected_loss - _K_BILLINGS
    computed = ("from" if net > 0 else "to", abs(net))
    assert _K_ADVANCES == 90 and _K_RETENTION == 70   # disclosed separately
    key = _pick({"A": ("to", 160), "B": ("to", 100),
                 "C": ("to", 200), "D": ("from", 200)}, computed)
    return {"answer": key, "computed": computed}


# ── case set 03 · Malabar Traders (four transactions) ─────────────────────

_M_BILL_AND_HOLD = 320_000
_M_CONSIGNMENT_SENT, _M_CONSIGNMENT_SOLD = 800_000, 560_000
_M_APPROVAL_SENT, _M_APPROVAL_ACCEPTED = 400_000, 250_000
_M_COUNTER_GROSS, _M_TRADE_RATE = 1_250_000, 0.08
_M_MACHINE_GAIN = 60_000


def cs_i1c8_03_a():
    revenue = _M_CONSIGNMENT_SOLD           # only the onward sale
    key = _pick({"A": 0, "B": 560_000, "C": 800_000, "D": 240_000}, revenue)
    return {"answer": key, "computed": revenue}


def cs_i1c8_03_b():
    revenue = _M_APPROVAL_ACCEPTED          # approval period on the rest runs to 1 May
    key = _pick({"A": 0, "B": 250_000, "C": 400_000, "D": 150_000}, revenue)
    return {"answer": key, "computed": revenue}


def cs_i1c8_03_d():
    counter = _M_COUNTER_GROSS * (1 - _M_TRADE_RATE)
    revenue = (_M_BILL_AND_HOLD + _M_CONSIGNMENT_SOLD
               + _M_APPROVAL_ACCEPTED + counter)   # machine gain is not revenue
    assert _M_MACHINE_GAIN == 60_000
    key = _pick({"A": 2_430_000, "B": 2_340_000,
                 "C": 2_280_000, "D": 2_520_000}, revenue)
    return {"answer": key, "computed": revenue}


# ── case set 04 · Nilgiri Estates (interest, royalty) ─────────────────────

def cs_i1c8_04_a():
    interest = 3_000_000 * 0.10 * 6 / 12    # held 1 Oct to 31 Mar
    key = _pick({"A": 75_000, "B": 0, "C": 150_000, "D": 300_000}, interest)
    return {"answer": key, "computed": interest}


def cs_i1c8_04_b():
    royalty = 12_500_000 * 0.04             # accrual on the licensee's net sales
    key = _pick({"A": 500_000, "B": 200_000, "C": 300_000, "D": 0}, royalty)
    return {"answer": key, "computed": royalty}
