"""Verifier for intermediate/advanced-accounting/branches-including-foreign.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring Ch 15 mechanics (SM Ch 15; AS 11):
  loading fraction   margin-on-cost m% → m/(100+m) of invoice price
  debtors method     profit = credits (remittances + closing assets)
                     − debits (opening assets + goods sent + expenses)
  shortage split     loading part → Branch Adjustment; cost part → Branch P&L
  wholesale method   branch profit = retail sales − wholesale value sold;
                     stock reserve = closing stock × wholesale-margin fraction
  reconciliation     HO balance − goods in transit − cash in transit
                     = branch's HO Account balance
  AS 11 integral     monetary at closing; non-monetary at historical;
                     income at average; difference → P&L
  AS 11 non-integral everything on the balance sheet at closing; income at
                     average; difference → FCTR

cs-i1c15-003-d is numerical:false — two options share ₹47,000 and the
distinguishing factor is asset-vs-liability classification, not arithmetic;
the blind consistency pass covers it.
"""


def _pick(options, value, tolerance=0.5):
    """Map a computed value to its option key (rupee amounts may float)."""
    for key, v in options.items():
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value} matches no option in {options}")


# ── standalone MCQs ──────────────────────────────────────────────────────

def q_i1c15_001():
    # goods sent at IP 4,00,000; cost + 25% → loading = 25/125 of IP
    loading = 400_000 * 25 / 125
    key = _pick({"A": 320_000, "B": 100_000, "C": 64_000, "D": 80_000}, loading)
    return {"answer": key, "computed": loading}


def q_i1c15_003():
    # closing stock at IP 90,000; cost + 20% → reserve = 20/120 of IP
    reserve = 90_000 * 20 / 120
    key = _pick({"A": 75_000, "B": 18_000, "C": 12_500, "D": 15_000}, reserve)
    return {"answer": key, "computed": reserve}


def q_i1c15_005():
    # debtors method at cost: credits (remit + cl. stock) − debits
    profit = (230_000 + 30_000) - (25_000 + 200_000 + 15_000)
    key = _pick({"A": 50_000, "B": 30_000, "C": 35_000, "D": 20_000}, profit)
    return {"answer": key, "computed": profit}


def q_i1c15_007():
    # shortage 6,000 at IP; cost + 50% → cost part = 2/3 hits P&L
    to_pnl = 6_000 * 100 / 150
    key = _pick({"A": 6_000, "B": 0, "C": 2_000, "D": 4_000}, to_pnl)
    return {"answer": key, "computed": to_pnl}


def q_i1c15_008():
    # memorandum debtors: op + credit sales − cash − bad − discounts − returns
    closing = 40_000 + 300_000 - 280_000 - 5_000 - 3_000 - 12_000
    key = _pick({"A": 52_000, "B": 48_000, "C": 43_000, "D": 40_000}, closing)
    return {"answer": key, "computed": closing}


def q_i1c15_010():
    # wholesale method: branch profit = retail sales − wholesale value sold
    profit = 240_000 - 192_000
    key = _pick({"A": 90_000, "B": 48_000, "C": 42_000, "D": 24_000}, profit)
    return {"answer": key, "computed": profit}


def q_i1c15_011():
    # closing stock at wholesale 70,000; wholesale = cost + 25% → 25/125
    reserve = 70_000 * 25 / 125
    key = _pick({"A": 11_200, "B": 17_500, "C": 56_000, "D": 14_000}, reserve)
    return {"answer": key, "computed": reserve}


def q_i1c15_013():
    # goods in transit = dispatched − received
    transit = 560_000 - 535_000
    key = _pick({"A": 535_000, "B": 35_000, "C": 25_000, "D": 0}, transit)
    return {"answer": key, "computed": transit}


def q_i1c15_015():
    # HO balance − cash in transit − goods in transit
    branch_side = 346_000 - 16_000 - 30_000
    key = _pick({"A": 300_000, "B": 346_000, "C": 330_000, "D": 392_000}, branch_side)
    return {"answer": key, "computed": branch_side}


def q_i1c15_017():
    # 2,40,000 at 10% WDV — second year's charge
    year2 = 240_000 * 0.9 * 0.10
    key = _pick({"A": 24_000, "B": 19_440, "C": 21_600, "D": 48_000}, year2)
    return {"answer": key, "computed": year2}


def q_i1c15_019():
    # incorporation: COGS = op + goods from HO − cl; NP = sales − COGS − exp
    cogs = 40_000 + 320_000 - 60_000
    profit = 480_000 - cogs - 90_000
    key = _pick({"A": 180_000, "B": 70_000, "C": 90_000, "D": 130_000}, profit)
    return {"answer": key, "computed": profit}


def q_i1c15_022():
    # integral: fixed assets at historical rate
    translated = 20_000 * 64
    key = _pick({"A": 1_600_000, "B": 1_280_000, "C": 1_640_000, "D": 1_200_000}, translated)
    return {"answer": key, "computed": translated}


def q_i1c15_023():
    # non-integral: fixed assets at closing rate
    translated = 20_000 * 82
    key = _pick({"A": 1_280_000, "B": 1_600_000, "C": 1_460_000, "D": 1_640_000}, translated)
    return {"answer": key, "computed": translated}


def q_i1c15_025():
    # net monetary assets × closing rate (either classification)
    translated = (6_000 + 1_000 - 2_500) * 84
    key = _pick({"A": 588_000, "B": 294_000, "C": 378_000, "D": 360_000}, translated)
    return {"answer": key, "computed": translated}


def q_i1c15_027():
    # income at average rate
    translated = 50_000 * 79
    key = _pick({"A": 4_150_000, "B": 3_950_000, "C": 4_050_000, "D": 3_900_000}, translated)
    return {"answer": key, "computed": translated}


# ── case set 1: Deccan Textiles, Nashik (debtors method at IP) ───────────
# cost + 20% → loading 20/120 = 1/6 of IP; op stock 48,000; goods sent
# 6,00,000; remittances 6,10,000; expenses 54,000; cl stock 72,000.

def cs_i1c15_001_a():
    loading = 600_000 * 20 / 120
    key = _pick({"A": 120_000, "B": 83_333, "C": 100_000, "D": 500_000}, loading)
    return {"answer": key, "computed": loading}


def cs_i1c15_001_b():
    reserve = 72_000 * 20 / 120
    key = _pick({"A": 12_000, "B": 14_400, "C": 60_000, "D": 8_000}, reserve)
    return {"answer": key, "computed": reserve}


def cs_i1c15_001_c():
    apparent = (610_000 + 72_000) - (48_000 + 600_000 + 54_000)  # −20,000
    loading_goods_sent = 600_000 * 20 / 120
    closing_reserve = 72_000 * 20 / 120
    opening_reserve = 48_000 * 20 / 120
    profit = apparent + loading_goods_sent - closing_reserve + opening_reserve
    key = _pick({"A": 80_000, "B": 100_000, "C": 76_000, "D": 96_000}, profit)
    return {"answer": key, "computed": profit}


# ── case set 2: Sahyadri Footwear (stock & debtors, shortage) ────────────
# cost + 50% → loading 1/3 of IP; op stock 30,000; sent 3,00,000;
# cash sales at IP 2,85,000; physical closing 36,000.

def cs_i1c15_002_a():
    shortage = (30_000 + 300_000) - (285_000 + 36_000)
    key = _pick({"A": 6_000, "B": 0, "C": 15_000, "D": 9_000}, shortage)
    return {"answer": key, "computed": shortage}


def cs_i1c15_002_b():
    shortage = 9_000
    to_pnl = shortage * 100 / 150
    key = _pick({"A": 9_000, "B": 6_000, "C": 4_500, "D": 3_000}, to_pnl)
    return {"answer": key, "computed": to_pnl}


def cs_i1c15_002_c():
    reserve = 36_000 * 50 / 150
    key = _pick({"A": 10_000, "B": 24_000, "C": 12_000, "D": 18_000}, reserve)
    return {"answer": key, "computed": reserve}


def cs_i1c15_002_d():
    realised_loading = 285_000 * 50 / 150
    key = _pick({"A": 100_000, "B": 142_500, "C": 95_000, "D": 89_000}, realised_loading)
    return {"answer": key, "computed": realised_loading}


# ── case set 3: Yamuna Electricals, Kanpur (reconciliation) ──────────────
# HO Branch A/c dr 4,52,000; branch HO A/c cr 4,00,000; goods in transit
# 32,000; cash in transit 15,000; unrecorded branch depreciation 5,000.

def cs_i1c15_003_a():
    adjusted = 452_000 - 32_000 - 15_000
    key = _pick({"A": 452_000, "B": 405_000, "C": 420_000, "D": 499_000}, adjusted)
    return {"answer": key, "computed": adjusted}


def cs_i1c15_003_c():
    branch_balance = 400_000 + 5_000
    # sanity: must now equal HO's transit-adjusted balance
    assert branch_balance == 452_000 - 32_000 - 15_000
    key = _pick({"A": 452_000, "B": 405_000, "C": 400_000, "D": 395_000}, branch_balance)
    return {"answer": key, "computed": branch_balance}


# ── case set 4: Krishna Exports, Singapore (AS 11 translation) ───────────
# FA $25,000 at hist ₹58; inventory $8,000 at ₹81; receivables $12,000;
# payables $7,000; cash $3,000; closing ₹84; average ₹80.

def cs_i1c15_004_a():
    translated = 25_000 * 58
    key = _pick({"A": 2_100_000, "B": 2_000_000, "C": 1_450_000, "D": 1_400_000}, translated)
    return {"answer": key, "computed": translated}


def cs_i1c15_004_b():
    translated = 25_000 * 84
    key = _pick({"A": 2_250_000, "B": 2_000_000, "C": 2_100_000, "D": 1_450_000}, translated)
    return {"answer": key, "computed": translated}


def cs_i1c15_004_c():
    translated = 12_000 * 84
    key = _pick({"A": 960_000, "B": 1_050_000, "C": 1_008_000, "D": 696_000}, translated)
    return {"answer": key, "computed": translated}


def cs_i1c15_004_e():
    translated = 8_000 * 81
    key = _pick({"A": 672_000, "B": 648_000, "C": 464_000, "D": 640_000}, translated)
    return {"answer": key, "computed": translated}
