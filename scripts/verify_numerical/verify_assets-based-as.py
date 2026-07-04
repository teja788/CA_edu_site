"""Verifier for intermediate/advanced-accounting/assets-based-as.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring Ch 5 mechanics (SM Ch 5 U1–U7):
  AS 2 NRV           selling price − completion costs − selling costs
  AS 2 fixed OH      absorbed at NORMAL capacity; shortfall expensed
  AS 10 cost         price − trade discount + directly attributable (net
                     testing) ; refundable taxes / admin OH / op losses OUT
  AS 13 transfers    LT→current: lower(cost, carrying); current→LT:
                     lower(cost, fair value)
  AS 16 specific     actual costs − temporary-investment income
  AS 16 general      weighted-average rate × qualifying expenditure
  AS 19 lessee       initial = min(fair value, PV of MLP); liability rolls
                     at implicit rate minus payments
  AS 19 lessor       UFI = gross investment − PV(net investment)
  AS 28 CGU          loss = carrying − recoverable; goodwill first, then
                     pro-rata on carrying amounts

cs-i1c05-003-a is numerical:false — classification judgement (the 94.8%
computation appears inside cs-003-b's verification); the blind pass covers it.
"""


def _pick(options, value, tolerance=0.5):
    """Map a computed value to its option key (rupee amounts may float)."""
    for key, v in options.items():
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value} matches no option in {options}")


# ── standalone MCQs ──────────────────────────────────────────────────────

def q_i1c05_006():
    # WIP cost 90; finished SP 120, completion 30, selling 5 → NRV; lower-of
    nrv = 120 - 30 - 5
    carry = min(90, nrv)
    key = _pick({"A": 85, "B": 90, "C": 80, "D": 115}, carry)
    return {"answer": key, "computed": carry}


def q_i1c05_008():
    # list 10,00,000 − 2% discount + freight + installation + net testing;
    # refundable GST, admin OH, initial operating loss all excluded
    cost = 1_000_000 * 0.98 + 40_000 + 25_000 + 15_000
    key = _pick({"A": 1_045_000, "B": 1_060_000, "C": 1_180_000, "D": 1_110_000}, cost)
    return {"answer": key, "computed": cost}


def q_i1c05_012():
    # increase 1,50,000; first reverses prior P&L decrease 50,000; rest → surplus
    to_surplus = 150_000 - 50_000
    key = _pick({"A": 100_000, "B": 150_000, "C": 0, "D": 50_000}, to_surplus)
    return {"answer": key, "computed": to_surplus}


def q_i1c05_018():
    # 1,000 @150 + 200 rights @120 → blended per-share cost
    avg = (1_000 * 150 + 200 * 120) / 1_200
    key = _pick({"A": 150, "B": 120, "C": 135, "D": 145}, avg, tolerance=0.005)
    return {"answer": key, "computed": avg}


def q_i1c05_020():
    # LT→current: lower of cost (5,00,000) and carrying (4,20,000); FV a decoy
    transfer = min(500_000, 420_000)
    key = _pick({"A": 420_000, "B": 410_000, "C": 500_000, "D": 460_000}, transfer)
    return {"answer": key, "computed": transfer}


def q_i1c05_025():
    # 14% × 10,00,000 − temporary investment income 35,000
    cap = 0.14 * 1_000_000 - 35_000
    key = _pick({"A": 35_000, "B": 140_000, "C": 175_000, "D": 105_000}, cap)
    return {"answer": key, "computed": cap}


def q_i1c05_030():
    # UFI = gross investment (MLP 12,00,000 + UGR 1,00,000) − PV 9,90,000
    ufi = (1_200_000 + 100_000) - 990_000
    key = _pick({"A": 210_000, "B": 990_000, "C": 310_000, "D": 1_300_000}, ufi)
    return {"answer": key, "computed": ufi}


def q_i1c05_036():
    # 8,00,000 over best-estimate life 8 yrs (≤ legal 12, within 10-yr presumption)
    life = min(8, 12, 10)
    amort = 800_000 / life
    key = _pick({"A": 160_000, "B": 100_000, "C": 80_000, "D": 66_667}, amort, tolerance=1)
    return {"answer": key, "computed": amort}


def q_i1c05_040():
    # recoverable = max(NSP 8,20,000, VIU 8,80,000); loss vs carrying 10,00,000
    loss = 1_000_000 - max(820_000, 880_000)
    key = _pick({"A": 120_000, "B": 60_000, "C": 0, "D": 180_000}, loss)
    return {"answer": key, "computed": loss}


# ── cs-i1c05-001 · Narmada Fabrics (AS 2 valuation) ──────────────────────

PRODUCED, NORMAL_CAP, CLOSING_UNITS = 10_000, 12_000, 1_500
MAT, LAB, VOH, FOH = 400_000, 240_000, 160_000, 300_000
SP, SELL_COST = 95, 3


def _foh_rate():
    return FOH / NORMAL_CAP


def _unit_cost():
    return MAT / PRODUCED + LAB / PRODUCED + VOH / PRODUCED + _foh_rate()


def cs_i1c05_001_a():
    rate = _foh_rate()
    key = _pick({"A": 20, "B": 27.5, "C": 25, "D": 30}, rate, tolerance=0.005)
    return {"answer": key, "computed": rate}


def cs_i1c05_001_b():
    cost = _unit_cost()
    key = _pick({"A": 89, "B": 105, "C": 80, "D": 110}, cost, tolerance=0.005)
    return {"answer": key, "computed": cost}


def cs_i1c05_001_c():
    nrv = SP - SELL_COST
    value = CLOSING_UNITS * min(_unit_cost(), nrv)
    key = _pick({"A": 138_000, "B": 132_000, "C": 157_500, "D": 142_500}, value)
    return {"answer": key, "computed": value}


def cs_i1c05_001_d():
    unabsorbed = FOH - _foh_rate() * PRODUCED
    key = _pick({"A": 60_000, "B": 50_000, "C": 25_000, "D": 0}, unabsorbed)
    return {"answer": key, "computed": unabsorbed}


# ── cs-i1c05-002 · Chambal Power (AS 16) ─────────────────────────────────

SPEC_LOAN, SPEC_RATE, TEMP_INCOME = 4_000_000, 0.12, 60_000
GEN = [(2_500_000, 0.10), (2_500_000, 0.14)]
GEN_EXPENDITURE = 1_000_000


def _specific_cap():
    return SPEC_LOAN * SPEC_RATE - TEMP_INCOME


def _gen_rate():
    total = sum(a for a, _ in GEN)
    return sum(a * r for a, r in GEN) / total


def cs_i1c05_002_a():
    cap = _specific_cap()
    key = _pick({"A": 540_000, "B": 60_000, "C": 420_000, "D": 480_000}, cap)
    return {"answer": key, "computed": cap}


def cs_i1c05_002_b():
    rate = _gen_rate() * 100
    key = _pick({"A": 10.0, "B": 12.0, "C": 14.0, "D": 11.5}, rate, tolerance=0.005)
    return {"answer": key, "computed": rate}


def cs_i1c05_002_c():
    total = _specific_cap() + _gen_rate() * GEN_EXPENDITURE
    key = _pick({"A": 420_000, "B": 540_000, "C": 120_000, "D": 600_000}, total)
    return {"answer": key, "computed": total}


# ── cs-i1c05-003 · Tapti Logistics (AS 19 lessee) ────────────────────────

RENTAL, FACTOR, FV, RATE = 250_000, 3.791, 1_000_000, 0.10


def _initial():
    return min(FV, RENTAL * FACTOR)


def cs_i1c05_003_b():
    init = _initial()
    key = _pick({"A": 1_250_000, "B": 900_000, "C": 1_000_000, "D": 947_750}, init)
    return {"answer": key, "computed": init}


def cs_i1c05_003_c():
    charge = _initial() * RATE
    key = _pick({"A": 125_000, "B": 100_000, "C": 94_775, "D": 250_000}, charge)
    return {"answer": key, "computed": charge}


def cs_i1c05_003_d():
    closing = _initial() * (1 + RATE) - RENTAL
    key = _pick({"A": 792_525, "B": 1_042_525, "C": 697_750, "D": 852_975}, closing)
    return {"answer": key, "computed": closing}


# ── cs-i1c05-004 · Sabarmati Chemicals (AS 28 CGU) ───────────────────────

GOODWILL, PLANT, INTANG = 100_000, 600_000, 200_000
RECOVERABLE = 675_000


def _cgu_loss():
    return (GOODWILL + PLANT + INTANG) - RECOVERABLE


def _plant_share():
    residual = _cgu_loss() - GOODWILL          # goodwill absorbed first
    return residual * PLANT / (PLANT + INTANG)


def cs_i1c05_004_a():
    loss = _cgu_loss()
    key = _pick({"A": 225_000, "B": 200_000, "C": 250_000, "D": 125_000}, loss)
    return {"answer": key, "computed": loss}


def cs_i1c05_004_b():
    share = _plant_share()
    key = _pick({"A": 168_750, "B": 150_000, "C": 93_750, "D": 125_000}, share)
    return {"answer": key, "computed": share}


def cs_i1c05_004_c():
    carrying = PLANT - _plant_share()
    key = _pick({"A": 506_250, "B": 431_250, "C": 600_000, "D": 450_000}, carrying)
    return {"answer": key, "computed": carrying}
