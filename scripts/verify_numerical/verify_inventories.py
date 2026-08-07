"""Verifier for foundation/accounting/inventories.json (P1 Ch 4).

Every function recomputes its answer from the stem's own parameters — the
receipts/issues ledger is actually walked for the FIFO, periodic-average and
moving-average questions, the cost build-ups are re-added item by item, the
lower-of-cost-and-NRV tables are re-compared line by line, and the cut-off
questions re-apply the ownership test to each adjustment. Nothing is copied
from the answer key: the computed value is mapped to an option key through a
dict of the four option values, so a wrong key in the bank shows up as a
KeyError or a mismatch.

Conventions used below:
  * `lots` are (units, rate) tuples in chronological order; `issues` is the
    list of quantities issued, also in order.
  * profit adjustments: +ve raises the reported profit, -ve reduces it.
  * cut-off adjustments: +ve = the goods are OURS but were not counted;
    -ve = the goods were counted but are NOT ours.
"""


# ------------------------------------------------------------ shared helpers


def fifo_closing(lots, issues):
    """Walk the lots, consuming the OLDEST units first; value what is left."""
    remaining = [[u, r] for u, r in lots]
    for qty in issues:
        to_issue = qty
        for layer in remaining:
            if to_issue == 0:
                break
            taken = min(layer[0], to_issue)
            layer[0] -= taken
            to_issue -= taken
        assert to_issue == 0, "issued more units than were available"
    return sum(u * r for u, r in remaining)


def lifo_closing(lots, issues):
    """Same walk, but consuming the NEWEST units first (not permitted by AS 2;
    computed only to confirm that the distractor really is the LIFO figure)."""
    remaining = [[u, r] for u, r in lots]
    for qty in issues:
        to_issue = qty
        for layer in reversed(remaining):
            if to_issue == 0:
                break
            taken = min(layer[0], to_issue)
            layer[0] -= taken
            to_issue -= taken
        assert to_issue == 0
    return sum(u * r for u, r in remaining)


def periodic_average_closing(lots, issues):
    """One rate for the whole period: cost available / units available."""
    units = sum(u for u, _ in lots)
    cost = sum(u * r for u, r in lots)
    closing_units = units - sum(issues)
    return closing_units * (cost / units)


def moving_average_closing(events):
    """`events` is a list of ("buy", units, rate) / ("issue", units) tuples in
    date order. A fresh average is struck after every purchase."""
    units = 0.0
    cost = 0.0
    for ev in events:
        if ev[0] == "buy":
            units += ev[1]
            cost += ev[1] * ev[2]
        else:
            rate = cost / units
            units -= ev[1]
            cost -= ev[1] * rate
    return cost


# The April 2025 record shared by q-030 to q-033 (and by worked example 1).
CLOTH_LOTS = [(200, 50), (300, 60), (500, 64)]
CLOTH_ISSUES = [200, 450]
CLOTH_EVENTS = [
    ("buy", 200, 50),  # opening stock
    ("buy", 300, 60),  # 5 Apr
    ("issue", 200),  # 10 Apr
    ("buy", 500, 64),  # 18 Apr
    ("issue", 450),  # 25 Apr
]
CLOTH_POOL = sum(u * r for u, r in CLOTH_LOTS)

# The four lines shared by q-009 and q-010, as (cost, NRV).
NANDINI = [(60_000, 68_000), (45_000, 39_000), (30_000, 25_500), (25_000, 27_000)]


# ------------------------------------------------ §2/§3 errors and write-downs


def q_f1c4_006():
    # Only the FALL below cost is written off; profit drops by that much.
    draft = 360_000
    lot_cost, lot_nrv = 70_000, 45_000
    write_down = max(0, lot_cost - lot_nrv)
    corrected = draft - write_down
    key = {385_000: "A", 315_000: "B", 335_000: "C", 360_000: "D"}[corrected]
    return {"answer": key, "computed": corrected}


def q_f1c4_007():
    # An overstated closing stock overstates year 1 and understates year 2.
    y1_reported, y2_reported = 400_000, 500_000
    overstatement = 60_000
    y1 = y1_reported - overstatement
    y2 = y2_reported + overstatement  # it became year 2's opening stock
    assert y1 + y2 == y1_reported + y2_reported  # the error is counterbalancing
    key = {
        (340_000, 440_000): "A",
        (340_000, 560_000): "B",
        (460_000, 440_000): "C",
        (400_000, 560_000): "D",
    }[(y1, y2)]
    return {"answer": key, "computed": f"{y1} / {y2}"}


def q_f1c4_009():
    # Lower of cost and NRV, taken line by line.
    value = sum(min(c, n) for c, n in NANDINI)
    key = {160_000: "A", 159_500: "B", 149_500: "C", 170_000: "D"}[value]
    return {"answer": key, "computed": value}


def q_f1c4_010():
    # Write-down = sum of the item-wise falls below cost.
    write_down = sum(max(0, c - n) for c, n in NANDINI)
    assert write_down == sum(c for c, _ in NANDINI) - sum(min(c, n) for c, n in NANDINI)
    key = {10_500: "A", 500: "B", 6_000: "C", 4_500: "D"}[write_down]
    return {"answer": key, "computed": write_down}


def q_f1c4_011():
    # NRV per shirt is ABOVE cost, so the stock stays at cost.
    units, cost_each, sell = 1_200, 400, 460
    nrv_each = sell - 15 - 0.05 * sell  # repacking + 5% commission
    value = units * min(cost_each, nrv_each)
    key = {552_000: "A", 480_000: "B", 506_400: "C", 462_000: "D"}[round(value)]
    return {"answer": key, "computed": f"NRV {nrv_each:g}/unit -> {round(value)}"}


def q_f1c4_012():
    units, cost_each, sell, sell_cost = 500, 900, 840, 40
    nrv_each = sell - sell_cost
    value = units * min(cost_each, nrv_each)
    key = {450_000: "A", 420_000: "B", 430_000: "C", 400_000: "D"}[value]
    return {"answer": key, "computed": value}


# --------------------------------------------------------- §4/§5 cost build-up


def q_f1c4_015():
    list_price = 500_000
    trade_discount = 0.10 * list_price
    included = [
        list_price - trade_discount,  # net purchase price
        22_000,  # non-refundable customs duty
        18_000,  # freight inward
        5_000,  # loading and unloading
    ]
    excluded = {
        "creditable GST": 81_000,
        "cash discount received": 4_000,
        "storage of finished bales": 12_000,
        "abnormal fire loss": 15_000,
        "salesmen's commission": 20_000,
        "interest on loan": 9_000,
    }
    cost = sum(included)
    assert excluded  # documented, never added
    key = {576_000: "A", 495_000: "B", 507_000: "C", 491_000: "D"}[round(cost)]
    return {"answer": key, "computed": round(cost)}


def q_f1c4_016():
    net_price = 240_000 * (1 - 0.125)
    cost = net_price + 15_000 + 9_000 + 3_000  # duty, freight inward, transit insurance
    # excluded: creditable GST 37,800 and post-arrival godown rent 6,000
    key = {274_800: "A", 243_000: "B", 210_000: "C", 237_000: "D"}[round(cost)]
    return {"answer": key, "computed": round(cost)}


def q_f1c4_018():
    price, gst, freight_inward = 100_000, 18_000, 4_000
    gst_recoverable = True
    cost = price + freight_inward + (0 if gst_recoverable else gst)
    key = {122_000: "A", 118_000: "B", 104_000: "C", 100_000: "D"}[cost]
    return {"answer": key, "computed": cost}


def q_f1c4_021():
    # Normal loss carries no cost of its own: the pool is spread over the good
    # units only. Abnormal loss is then valued at that rate and expensed.
    bought_kg, rate, freight_inward = 10_000, 58, 20_000
    normal_loss, abnormal_loss = 400, 600
    pool = bought_kg * rate + freight_inward
    good_units = bought_kg - normal_loss
    cost_per_good_kg = pool / good_units
    closing_kg = bought_kg - normal_loss - abnormal_loss
    assert closing_kg == 9_000
    value = closing_kg * cost_per_good_kg
    key = {562_500: "A", 540_000: "B", 522_000: "C", 600_000: "D"}[round(value)]
    return {"answer": key, "computed": f"{cost_per_good_kg:g}/kg -> {round(value)}"}


# ------------------------------------------------------- §6 NRV and materials


def q_f1c4_025():
    # Finished goods will sell AT OR ABOVE cost -> no write-down of materials.
    cost, replacement = 450_000, 390_000
    finished_goods_sell_below_cost = False
    value = replacement if finished_goods_sell_below_cost else cost
    key = {450_000: "A", 390_000: "B", 420_000: "C", 60_000: "D"}[value]
    return {"answer": key, "computed": value}


def q_f1c4_026():
    # Same figures, but the finished goods will sell BELOW cost -> write down,
    # replacement cost being the best available measure of NRV.
    cost, replacement = 450_000, 390_000
    finished_goods_sell_below_cost = True
    value = replacement if finished_goods_sell_below_cost else cost
    key = {450_000: "A", 420_000: "B", 390_000: "C", 330_000: "D"}[value]
    return {"answer": key, "computed": value}


def q_f1c4_027():
    cost = 700_000
    selling_price, cost_to_complete, commission_rate = 800_000, 120_000, 0.04
    nrv = selling_price - cost_to_complete - commission_rate * selling_price
    value = min(cost, nrv)
    key = {700_000: "A", 680_000: "B", 768_000: "C", 648_000: "D"}[round(value)]
    return {"answer": key, "computed": f"NRV {round(nrv)} -> {round(value)}"}


# ----------------------------------------------------------- §7 cost formulas


def q_f1c4_030():
    value = fifo_closing(CLOTH_LOTS, CLOTH_ISSUES)
    # sanity: the distractors really are the other formulas
    assert round(periodic_average_closing(CLOTH_LOTS, CLOTH_ISSUES)) == 21_000
    assert round(moving_average_closing(CLOTH_EVENTS)) == 21_350
    assert lifo_closing(CLOTH_LOTS, CLOTH_ISSUES) == 19_000
    key = {21_000: "A", 21_350: "B", 19_000: "C", 22_400: "D"}[round(value)]
    return {"answer": key, "computed": round(value)}


def q_f1c4_031():
    value = periodic_average_closing(CLOTH_LOTS, CLOTH_ISSUES)
    simple_average = sum(r for _, r in CLOTH_LOTS) / len(CLOTH_LOTS)
    closing_units = sum(u for u, _ in CLOTH_LOTS) - sum(CLOTH_ISSUES)
    assert round(closing_units * simple_average) == 20_300  # the D distractor
    key = {22_400: "A", 21_000: "B", 21_350: "C", 20_300: "D"}[round(value)]
    return {"answer": key, "computed": round(value)}


def q_f1c4_032():
    value = moving_average_closing(CLOTH_EVENTS)
    key = {21_000: "A", 22_400: "B", 21_350: "C", 19_000: "D"}[round(value)]
    return {"answer": key, "computed": round(value)}


def q_f1c4_033():
    cogs = CLOTH_POOL - fifo_closing(CLOTH_LOTS, CLOTH_ISSUES)
    # cross-check by pricing the issues directly, oldest first
    assert cogs == 200 * 50 + 300 * 60 + 150 * 64
    key = {37_600: "A", 39_000: "B", 38_650: "C", 41_000: "D"}[round(cogs)]
    return {"answer": key, "computed": round(cogs)}


def q_f1c4_034():
    lots = [(40, 1_200), (60, 1_250), (50, 1_290)]
    issues = [110]
    value = fifo_closing(lots, issues)
    pool = sum(u * r for u, r in lots)
    assert round(periodic_average_closing(lots, issues)) == 50_000  # B distractor
    assert pool - value == 135_900  # C distractor is the FIFO cost of goods sold
    key = {48_000: "A", 50_000: "B", 135_900: "C", 51_600: "D"}[round(value)]
    return {"answer": key, "computed": round(value)}


# --------------------------------------------------------- §8 retail method


def q_f1c4_038():
    closing_at_retail, margin_on_selling_price = 600_000, 0.25
    cost = closing_at_retail * (1 - margin_on_selling_price)
    key = {600_000: "A", 480_000: "B", 150_000: "C", 450_000: "D"}[round(cost)]
    return {"answer": key, "computed": round(cost)}


def q_f1c4_039():
    opening, purchases, sales = 200_000, 1_200_000, 800_000  # all at selling prices
    closing_at_retail = opening + purchases - sales
    cost = closing_at_retail * (1 - 0.30)
    key = {600_000: "A", 420_000: "B", 560_000: "C", 280_000: "D"}[round(cost)]
    return {"answer": key, "computed": f"retail {closing_at_retail} -> {round(cost)}"}


# ------------------------------------------------ §9 periodic and perpetual


def q_f1c4_040():
    opening, purchases, returns_outward, carriage_inward = 120_000, 850_000, 20_000, 30_000
    closing_physical = 152_000
    available = opening + (purchases - returns_outward) + carriage_inward
    cogs = available - closing_physical
    key = {980_000: "A", 820_000: "B", 828_000: "C", 868_000: "D"}[cogs]
    return {"answer": key, "computed": cogs}


def q_f1c4_041():
    ledger, physical = 160_000, 152_000
    balance_sheet_figure = physical  # the verified figure always wins
    shortage = ledger - physical
    key = {
        (152_000, 8_000): "A",
        (160_000, 0): "B",
        (152_000, -8_000): "C",
        (168_000, 0): "D",
    }[(balance_sheet_figure, shortage)]
    return {"answer": key, "computed": f"stock {balance_sheet_figure}, shortage {shortage}"}


# ---------------------------------------------------------------- §10 cut-off


def q_f1c4_043():
    counted = 650_000
    adjustments = [
        +40_000,  # (i) goods in transit, title passed: ours, not counted
        -25_000,  # (ii) consignment inward: counted, but not ours
        +35_000,  # (iii) sale or return not approved: ours, not counted
        -18_000,  # (iv) sold and invoiced: counted, but no longer ours
    ]
    value = counted + sum(adjustments)
    key = {650_000: "A", 682_000: "B", 732_000: "C", 642_000: "D"}[value]
    return {"answer": key, "computed": value}


def q_f1c4_044():
    sent_at_cost, unsold_fraction = 120_000, 0.75
    value = sent_at_cost * unsold_fraction
    key = {0: "A", 120_000: "B", 90_000: "C", 30_000: "D"}[round(value)]
    return {"answer": key, "computed": round(value)}


def q_f1c4_045():
    draft = 500_000
    sale_wrongly_booked, cost_of_those_goods = 75_000, 60_000
    corrected = draft - sale_wrongly_booked + cost_of_those_goods
    assert draft - corrected == sale_wrongly_booked - cost_of_those_goods  # unearned profit
    key = {485_000: "A", 500_000: "B", 425_000: "C", 560_000: "D"}[corrected]
    return {"answer": key, "computed": corrected}
