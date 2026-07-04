"""Verifier for intermediate/advanced-accounting/presentation-and-disclosures-based-as.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring Ch 4 mechanics (SM Ch 4 U2/U3/U5/U7):
  cash equivalents   short maturity (~3 months or less from acquisition) +
                     insignificant risk of change in value
  indirect method    PBT + depreciation + interest expense − profit on sale
                     − interest income ± working capital − tax paid
  AS 17 revenue test 10% of combined (external + inter-segment) revenue
  AS 17 result test  10% of the GREATER absolute pool: all-profit vs all-loss
  AS 20 weighting    shares × months outstanding / 12; bonus never weighted
  AS 20 options      free shares = options × (fair − exercise)/fair
  AS 25 tax          weighted average annual effective rate × interim income

cs-i1c04-004-c is numerical:false — it tests the prospective treatment of a
change in estimate, not arithmetic; the blind consistency pass covers it.
"""


def _pick(options, value, tolerance=0.5):
    """Map a computed value to its option key (rupee amounts may float)."""
    for key, v in options.items():
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value} matches no option in {options}")


# ── standalone MCQs ──────────────────────────────────────────────────────

def q_i1c04_006():
    # cash 40,000 + demand deposits 1,10,000 + T-bill (≈2.5-month maturity,
    # qualifies) 50,000; 9-month FD and equity shares fail the tests
    total = 40_000 + 110_000 + 50_000
    key = _pick({"A": 300_000, "B": 275_000, "C": 200_000, "D": 150_000}, total)
    return {"answer": key, "computed": total}


def q_i1c04_023():
    # 90,000 (Apr–Jun) → +30,000 on 1 Jul → −12,000 on 1 Jan; year to 31 Mar
    wanes = 90_000 * 3 / 12 + 120_000 * 6 / 12 + 108_000 * 3 / 12
    key = _pick({"A": 109_500, "B": 108_000, "C": 120_000, "D": 105_000}, wanes)
    return {"answer": key, "computed": wanes}


def q_i1c04_024():
    # cumulative preference dividend deducted whether or not declared
    eps = (1_800_000 - 2_000_000 * 0.10) / 400_000
    key = _pick({"A": 3.60, "B": 4.00, "C": 5.00, "D": 4.50}, eps, tolerance=0.005)
    return {"answer": key, "computed": eps}


def q_i1c04_026():
    # bonus element of options: 50,000 × (75 − 60)/75
    free = 50_000 * (75 - 60) / 75
    key = _pick({"A": 12_500, "B": 50_000, "C": 40_000, "D": 10_000}, free)
    return {"answer": key, "computed": free}


def q_i1c04_037():
    # slab tax on estimated annual income 8,00,000: 30% × 5L + 40% × 3L
    rate = (0.30 * 500_000 + 0.40 * 300_000) / 800_000 * 100
    key = _pick({"A": 40.0, "B": 33.75, "C": 35.0, "D": 30.0}, rate, tolerance=0.005)
    return {"answer": key, "computed": rate}


# ── cs-i1c04-001 · Vindhya Engineering (AS 3 indirect method) ────────────

PBT, DEP, INT_EXP, PROFIT_SALE, INT_INC = 640_000, 150_000, 60_000, 40_000, 30_000
WC = -70_000 + 45_000 + 25_000          # receivables up, inventory down, payables up
TAX_PAID = 180_000
MACHINE_BOUGHT, SALE_PROCEEDS, INV_BOUGHT = 400_000, 190_000, 120_000
SHARES_ISSUED, DEB_REPAID, INT_PAID, DIV_PAID = 300_000, 200_000, 60_000, 90_000
OPENING_CASH = 125_000


def _operating():
    return PBT + DEP + INT_EXP - PROFIT_SALE - INT_INC + WC - TAX_PAID


def _investing():
    return -MACHINE_BOUGHT + SALE_PROCEEDS - INV_BOUGHT + INT_INC


def _financing():
    return SHARES_ISSUED - DEB_REPAID - INT_PAID - DIV_PAID


def cs_i1c04_001_a():
    op = _operating()
    key = _pick({"A": 630_000, "B": 600_000, "C": 780_000, "D": 540_000}, op)
    return {"answer": key, "computed": op}


def cs_i1c04_001_b():
    inv = _investing()               # options quote outflow magnitudes
    key = _pick({"A": -330_000, "B": -260_000, "C": -340_000, "D": -300_000}, inv)
    return {"answer": key, "computed": inv}


def cs_i1c04_001_c():
    fin = _financing()               # A/B/C are outflows, D an inflow
    key = _pick({"A": -140_000, "B": -90_000, "C": -50_000, "D": 10_000}, fin)
    return {"answer": key, "computed": fin}


def cs_i1c04_001_d():
    closing = OPENING_CASH + _operating() + _investing() + _financing()
    key = _pick({"A": 125_000, "B": 375_000, "C": 500_000, "D": 250_000}, closing)
    return {"answer": key, "computed": closing}


# ── cs-i1c04-002 · Panchtatva Industries (AS 17 reportable segments) ─────

EXT = {"A": 500, "B": 200, "C": 90, "D": 60, "E": 50}
INTER = {"A": 100, "B": 0, "C": 10, "D": 40, "E": 0}
RESULT = {"A": 90, "B": -140, "C": 25, "D": -10, "E": 12}
ASSETS = {"A": 400, "B": 300, "C": 80, "D": 150, "E": 70}


def _revenue_passers():
    threshold = 0.10 * (sum(EXT.values()) + sum(INTER.values()))
    return {s for s in EXT if EXT[s] + INTER[s] >= threshold}, threshold


def _result_pool():
    profits = sum(v for v in RESULT.values() if v > 0)
    losses = sum(-v for v in RESULT.values() if v < 0)
    return max(profits, losses)


def cs_i1c04_002_a():
    passers, threshold = _revenue_passers()
    key = {frozenset("ABC"): "A", frozenset("A"): "B",
           frozenset("ABD"): "C", frozenset("AB"): "D"}[frozenset(passers)]
    return {"answer": key, "computed": f"threshold {threshold}, passers {sorted(passers)}"}


def cs_i1c04_002_b():
    pool = _result_pool()            # options name the pool the 10% applies to
    key = _pick({"A": 23, "B": 127, "C": 150, "D": 277}, pool)
    return {"answer": key, "computed": pool}


def cs_i1c04_002_c():
    rev, _ = _revenue_passers()
    res_thr = 0.10 * _result_pool()
    res = {s for s, v in RESULT.items() if abs(v) >= res_thr}
    ast_thr = 0.10 * sum(ASSETS.values())
    ast = {s for s, v in ASSETS.items() if v >= ast_thr}
    reportable = rev | res | ast
    ext_share = sum(EXT[s] for s in reportable) / sum(EXT.values())
    assert ext_share >= 0.75, "75% floor would force additions"
    key = {frozenset("ABCDE"): "A", frozenset("AB"): "B",
           frozenset("ABCD"): "C", frozenset("ABD"): "D"}[frozenset(reportable)]
    return {"answer": key, "computed": f"{sorted(reportable)}, ext share {ext_share:.3f}"}


# ── cs-i1c04-003 · Saraswati Textiles (AS 20 EPS suite) ──────────────────

OPENING_SHARES, BONUS_RATIO = 240_000, 1 / 4
NP_EQUITY = 1_200_000
PRIOR_EPS = 6.00
DEB_FACE, DEB_RATE, CONV_SHARES, TAX_RATE = 1_000_000, 0.12, 50_000, 0.25


def _wanes():
    # bonus shares outstanding from the start of the year, never weighted
    return OPENING_SHARES * (1 + BONUS_RATIO)


def cs_i1c04_003_a():
    w = _wanes()
    key = _pick({"A": 280_000, "B": 240_000, "C": 300_000, "D": 270_000}, w)
    return {"answer": key, "computed": w}


def cs_i1c04_003_b():
    eps = NP_EQUITY / _wanes()
    key = _pick({"A": 5.00, "B": 4.29, "C": 4.00, "D": 3.75}, eps, tolerance=0.005)
    return {"answer": key, "computed": eps}


def cs_i1c04_003_c():
    restated = PRIOR_EPS * OPENING_SHARES / _wanes()
    key = _pick({"A": 4.80, "B": 5.00, "C": 6.00, "D": 7.50}, restated, tolerance=0.005)
    return {"answer": key, "computed": restated}


def cs_i1c04_003_d():
    adj_earnings = NP_EQUITY + DEB_FACE * DEB_RATE * (1 - TAX_RATE)
    diluted = adj_earnings / (_wanes() + CONV_SHARES)
    assert diluted < NP_EQUITY / _wanes(), "must be dilutive to be included"
    key = _pick({"A": 3.77, "B": 3.43, "C": 4.00, "D": 3.69}, diluted, tolerance=0.005)
    return {"answer": key, "computed": diluted}


# ── cs-i1c04-004 · Kaveri Foods (AS 25 interim tax) ──────────────────────

EST_ANNUAL, SLAB1_CAP, RATE1, RATE2 = 1_200_000, 600_000, 0.30, 0.40
Q1_INCOME = 300_000


def _annual_rate():
    tax = RATE1 * SLAB1_CAP + RATE2 * (EST_ANNUAL - SLAB1_CAP)
    return tax / EST_ANNUAL * 100


def cs_i1c04_004_a():
    rate = _annual_rate()
    key = _pick({"A": 30.0, "B": 35.0, "C": 32.5, "D": 40.0}, rate, tolerance=0.005)
    return {"answer": key, "computed": rate}


def cs_i1c04_004_b():
    tax = Q1_INCOME * _annual_rate() / 100
    key = _pick({"A": 120_000, "B": 114_000, "C": 105_000, "D": 90_000}, tax)
    return {"answer": key, "computed": tax}
