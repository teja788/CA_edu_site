"""Verifier for intermediate/advanced-accounting/buyback-of-securities.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring statutory mechanics (Companies Act 2013):
  shares test      25% of paid-up equity share COUNT              s.68(2)(c) proviso
  resources test   25% of (paid-up capital + free reserves) / price   s.68(2)(c)
  board route      10% of the same base                           s.68(2)(b) proviso
  debt-equity      max outflow = shareholders' funds - debt/2     s.68(2)(d)
  CRR              nominal value bought back - fresh-issue proceeds    s.69(1)
Free reserves for these tests INCLUDES securities premium (s.68 Explanation).
"""


def _pick(options, value, tolerance=0.5):
    """Map a computed value to its option key (rupee amounts may float)."""
    for key, v in options.items():
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value} matches no option in {options}")


# ── standalone MCQs ──────────────────────────────────────────────────────

def q_i1c12_001():
    # shares test: 25% of 3,00,000 shares
    n = 0.25 * 300_000
    key = _pick({"A": 30_000, "B": 75_000, "C": 150_000, "D": 300_000}, n)
    return {"answer": key, "computed": n}


def q_i1c12_002():
    # resources test: 25% × (30,00,000 + 18,00,000) ÷ ₹30
    n = 0.25 * (3_000_000 + 1_800_000) / 30
    key = _pick({"A": 40_000, "B": 120_000, "C": 16_000, "D": 75_000}, n)
    return {"answer": key, "computed": n}


def q_i1c12_003():
    # debt-equity max outflow: SF 60,00,000, debt 90,00,000
    amount = 6_000_000 - 9_000_000 / 2
    key = _pick({"A": 3_000_000, "B": 4_500_000, "C": 1_500_000, "D": 6_000_000}, amount)
    return {"answer": key, "computed": amount}


def q_i1c12_004():
    # board route: 10% × (16,00,000 + 24,00,000)
    amount = 0.10 * (1_600_000 + 2_400_000)
    key = _pick({"A": 1_000_000, "B": 400_000, "C": 160_000, "D": 240_000}, amount)
    return {"answer": key, "computed": amount}


def q_i1c12_005():
    # CRR fully from free reserves: nominal value 40,000 × ₹10
    crr = 40_000 * 10
    key = _pick({"A": 600_000, "B": 200_000, "C": 400_000, "D": 0}, crr)
    return {"answer": key, "computed": crr}


def q_i1c12_006():
    # CRR with fresh issue: 80,000 × 10 − 3,00,000
    crr = 80_000 * 10 - 300_000
    key = _pick({"A": 800_000, "B": 300_000, "C": 1_100_000, "D": 500_000}, crr)
    return {"answer": key, "computed": crr}


def q_i1c12_007():
    # premium to free reserves: 25,000 × (22−10) − securities premium 1,80,000
    to_free_reserves = 25_000 * (22 - 10) - 180_000
    key = _pick({"A": 120_000, "B": 300_000, "C": 180_000, "D": 0}, to_free_reserves)
    return {"answer": key, "computed": to_free_reserves}


def q_i1c12_008():
    # consideration: 60,000 × ₹35
    total = 60_000 * 35
    key = _pick({"A": 600_000, "B": 2_100_000, "C": 1_500_000, "D": 2_700_000}, total)
    return {"answer": key, "computed": total}


def q_i1c12_009():
    # post-buyback capital: 50,00,000 − 80,000 × ₹10 (nominal only)
    capital = 5_000_000 - 80_000 * 10
    key = _pick({"A": 1_800_000, "B": 5_000_000, "C": 4_200_000, "D": 4_600_000}, capital)
    return {"answer": key, "computed": capital}


def q_i1c12_010():
    # post-buyback D/E: debt 24,00,000 ÷ (40,00,000 − 10,00,000); complies if ≤ 2
    ratio = 2_400_000 / (4_000_000 - 1_000_000)
    assert ratio <= 2, "should comply"
    key = _pick({"A": 0.8, "B": 0.6, "C": 2.4, "D": 1.25}, ratio, tolerance=0.001)
    return {"answer": key, "computed": ratio}


def q_i1c12_011():
    # min of three tests: 1,00,000 sh ×10; FR 14,00,000; debt 30,00,000; price 20
    shares_test = 0.25 * 100_000
    resources_test = 0.25 * (1_000_000 + 1_400_000) / 20
    de_test = (2_400_000 - 3_000_000 / 2) / 20
    n = min(shares_test, resources_test, de_test)
    key = _pick({"A": 30_000, "B": 45_000, "C": 25_000, "D": 100_000}, n)
    return {"answer": key, "computed": n}


def q_i1c12_012():
    # CRR after 1:4 bonus on 2,00,000 shares of ₹10, CRR opening 7,50,000
    remaining = 750_000 - (200_000 / 4) * 10
    key = _pick({"A": 250_000, "B": 750_000, "C": 0, "D": 500_000}, remaining)
    return {"answer": key, "computed": remaining}


def q_i1c12_013():
    # free reserves for s.68: GR 12,00,000 + P&L 5,00,000 + sec premium 4,00,000
    # (revaluation reserve 6,00,000 excluded; premium INCLUDED per s.68 Expl.)
    fr = 1_200_000 + 500_000 + 400_000
    key = _pick({"A": 2_700_000, "B": 2_100_000, "C": 1_700_000, "D": 2_300_000}, fr)
    return {"answer": key, "computed": fr}


def q_i1c12_014():
    # resources test at premium price: 25% × (12,00,000 + 24,00,000) ÷ ₹12
    n = 0.25 * (1_200_000 + 2_400_000) / 12
    key = _pick({"A": 90_000, "B": 75_000, "C": 30_000, "D": 300_000}, n)
    return {"answer": key, "computed": n}


# ── case set 1: Precision Auto Components ───────────────────────────────
# capital 40,00,000 (4,00,000 × ₹10); GR 20L + P&L 12L + premium 8L → FR 40,00,000
# debt 70L secured + 20L unsecured = 90,00,000; price ₹25; SR passed.

def cs_i1c12_001_a():
    n = 0.25 * 400_000
    key = _pick({"A": 100_000, "B": 40_000, "C": 400_000, "D": 200_000}, n)
    return {"answer": key, "computed": n}


def cs_i1c12_001_b():
    n = 0.25 * (4_000_000 + 4_000_000) / 25
    key = _pick({"A": 200_000, "B": 80_000, "C": 72_000, "D": 32_000}, n)
    return {"answer": key, "computed": n}


def cs_i1c12_001_c():
    outflow = (4_000_000 + 4_000_000) - (7_000_000 + 2_000_000) / 2
    n = outflow / 25
    key = _pick({"A": 45_000, "B": 80_000, "C": 140_000, "D": 320_000}, n)
    return {"answer": key, "computed": n}


def cs_i1c12_001_d():
    shares_test = 0.25 * 400_000
    resources_test = 0.25 * 8_000_000 / 25
    de_test = (8_000_000 - 4_500_000) / 25
    n = min(shares_test, resources_test, de_test)
    key = _pick({"A": 140_000, "B": 100_000, "C": 80_000, "D": 40_000}, n)
    return {"answer": key, "computed": n}


# ── case set 2: Nimbus Softech (board route) ─────────────────────────────
# capital 10,00,00,000 + FR 50,00,00,000; price ₹120.

def cs_i1c12_002_a():
    amount = 0.10 * (100_000_000 + 500_000_000)
    key = _pick({"A": 150_000_000, "B": 60_000_000, "C": 50_000_000, "D": 10_000_000}, amount)
    return {"answer": key, "computed": amount}


def cs_i1c12_002_b():
    n = 0.10 * (100_000_000 + 500_000_000) / 120
    key = _pick({"A": 6_000_000, "B": 600_000, "C": 500_000, "D": 2_500_000}, n)
    return {"answer": key, "computed": n}


# ── case set 4: Kaveri Ceramics (entries) ────────────────────────────────
# capital 25,00,000 (2,50,000 × ₹10); premium a/c 2,40,000; GR 12,00,000;
# buyback 60,000 × ₹10 at ₹16, no fresh issue.

def cs_i1c12_004_a():
    total = 60_000 * 16
    key = _pick({"A": 600_000, "B": 960_000, "C": 360_000, "D": 1_600_000}, total)
    return {"answer": key, "computed": total}


def cs_i1c12_004_b():
    to_gr = 60_000 * (16 - 10) - 240_000
    key = _pick({"A": 360_000, "B": 240_000, "C": 120_000, "D": 0}, to_gr)
    return {"answer": key, "computed": to_gr}


def cs_i1c12_004_c():
    crr = 60_000 * 10 - 0  # no fresh issue
    key = _pick({"A": 960_000, "B": 600_000, "C": 360_000, "D": 240_000}, crr)
    return {"answer": key, "computed": crr}


def cs_i1c12_004_d():
    capital = 2_500_000 - 60_000 * 10
    key = _pick({"A": 1_900_000, "B": 1_540_000, "C": 2_500_000, "D": 2_140_000}, capital)
    return {"answer": key, "computed": capital}


# ── case set 5: Sagar Marine (fresh issue combo) ─────────────────────────
# buyback 80,000 × ₹10 at ₹15; fresh preference issue proceeds 3,00,000.

def cs_i1c12_005_a():
    crr = 80_000 * 10 - 300_000
    key = _pick({"A": 800_000, "B": 300_000, "C": 500_000, "D": 1_200_000}, crr)
    return {"answer": key, "computed": crr}


def cs_i1c12_005_c():
    total = 80_000 * 15
    key = _pick({"A": 1_200_000, "B": 800_000, "C": 900_000, "D": 400_000}, total)
    return {"answer": key, "computed": total}
