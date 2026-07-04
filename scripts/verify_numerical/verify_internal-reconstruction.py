"""Verifier for intermediate/advanced-accounting/internal-reconstruction.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring Ch 14 mechanics (Companies Act 2013 ss. 61, 66; SM Ch 14):
  sub-division      count × (old FV / new FV); paid proportion preserved
  reduction credit  paid-up value cancelled → Capital Reduction A/c
  mode (a)          cancelling UNCALLED capital → NO reconstruction credit
  sacrifice         claim − amount accepted (creditors / debenture holders)
  surrender         surrendered − re-allotted = cancelled → Reconstruction A/c
  account balance   credits − write-offs → Capital Reserve

Entry-selection MCQs whose options share a rupee amount (q-011, q-013,
q-023, q-025) are numerical:false — the blind consistency pass covers them.
"""


def _pick(options, value, tolerance=0.5):
    """Map a computed value to its option key (rupee amounts may float)."""
    for key, v in options.items():
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value} matches no option in {options}")


# ── standalone MCQs ──────────────────────────────────────────────────────

def q_i1c14_001():
    # ₹100 share, ₹60 paid, sub-divided into ₹10 shares → paid per new share
    paid = 60 / 100 * 10
    key = _pick({"A": 6, "B": 4, "C": 60, "D": 10}, paid, tolerance=0.001)
    return {"answer": key, "computed": paid}


def q_i1c14_003():
    # 5,00,000 × ₹2 consolidated into ₹10 shares
    n = 500_000 * 2 / 10
    key = _pick({"A": 100_000, "B": 500_000, "C": 50_000, "D": 250_000}, n)
    return {"answer": key, "computed": n}


def q_i1c14_005():
    # 60,000 × ₹10 fully paid reduced to ₹6 paid (FV retained)
    credit = 60_000 * (10 - 6)
    key = _pick({"A": 360_000, "B": 240_000, "C": 0, "D": 600_000}, credit)
    return {"answer": key, "computed": credit}


def q_i1c14_007():
    # 25,000 × ₹100 reduced to ₹25 (both values)
    credit = 25_000 * (100 - 25)
    key = _pick({"A": 625_000, "B": 1_250_000, "C": 1_875_000, "D": 2_500_000}, credit)
    return {"answer": key, "computed": credit}


def q_i1c14_008():
    # cancelling the uncalled ₹2 on 50,000 shares → NO reconstruction credit
    credit = 0
    key = _pick({"A": 400_000, "B": 100_000, "C": 500_000, "D": 0}, credit)
    return {"answer": key, "computed": credit}


def q_i1c14_009():
    # creditors 4,80,000 accept 75 paise in the rupee → sacrifice 25%
    sacrifice = 480_000 * 0.25
    key = _pick({"A": 360_000, "B": 480_000, "C": 120_000, "D": 96_000}, sacrifice)
    return {"answer": key, "computed": sacrifice}


def q_i1c14_010():
    # debentures 5,00,000 exchanged for new debentures at 85%
    sacrifice = 500_000 * (1 - 0.85)
    key = _pick({"A": 75_000, "B": 500_000, "C": 425_000, "D": 50_000}, sacrifice)
    return {"answer": key, "computed": sacrifice}


def q_i1c14_012():
    # write-offs: P&L 2,60,000 + goodwill 80,000 + prelim 15,000 + patents 45,000
    total = 260_000 + 80_000 + 15_000 + 45_000
    key = _pick({"A": 385_000, "B": 400_000, "C": 320_000, "D": 355_000}, total)
    return {"answer": key, "computed": total}


def q_i1c14_017():
    # surrendered 7,20,000 − re-allotted 5,20,000 = cancelled
    cancelled = 720_000 - 520_000
    key = _pick({"A": 0, "B": 200_000, "C": 520_000, "D": 720_000}, cancelled)
    return {"answer": key, "computed": cancelled}


def q_i1c14_020():
    # 30,000 × ₹100 reduced to ₹40 fully paid → new capital
    capital = 30_000 * 40
    key = _pick({"A": 300_000, "B": 1_200_000, "C": 1_800_000, "D": 3_000_000}, capital)
    return {"answer": key, "computed": capital}


def q_i1c14_027():
    # credits 6,00,000 + 90,000 + 60,000; debits 4,80,000 + 1,20,000 + 90,000 + 20,000
    credits = 600_000 + 90_000 + 60_000
    debits = 480_000 + 120_000 + 90_000 + 20_000
    balance = credits - debits
    assert balance > 0, "credit balance → capital reserve"
    key = _pick({"A": 40_000, "B": 0, "C": 710_000, "D": 750_000}, balance)
    return {"answer": key, "computed": balance}


# ── case set 1: Vetravati Engineering (full scheme) ──────────────────────
# equity 80,000 × ₹10 → ₹2.50; pref 3,000 × ₹100 → ₹75; creditors 2,40,000
# forgo 25%; property +90,000; write off P&L 5,80,000 + goodwill 1,00,000 +
# inventory 60,000 + prelim 10,000.

def cs_i1c14_001_a():
    credit = 80_000 * (10 - 2.50)
    key = _pick({"A": 800_000, "B": 200_000, "C": 750_000, "D": 600_000}, credit)
    return {"answer": key, "computed": credit}


def cs_i1c14_001_b():
    credits = 80_000 * 7.50 + 3_000 * (100 - 75) + 240_000 * 0.25 + 90_000
    key = _pick({"A": 765_000, "B": 750_000, "C": 735_000, "D": 825_000}, credits)
    return {"answer": key, "computed": credits}


def cs_i1c14_001_c():
    debits = 580_000 + 100_000 + 60_000 + 10_000
    key = _pick({"A": 750_000, "B": 740_000, "C": 650_000, "D": 690_000}, debits)
    return {"answer": key, "computed": debits}


def cs_i1c14_001_d():
    balance = 825_000 - 750_000
    assert balance > 0, "credit balance → capital reserve"
    key = _pick({"A": 75_000, "B": 825_000, "C": 150_000, "D": 0}, balance)
    return {"answer": key, "computed": balance}


# ── case set 2: Tapti Sugars (alteration) ────────────────────────────────
# 20,000 × ₹50, ₹40 paid → sub-divided into ₹10 shares.

def cs_i1c14_002_a():
    n = 20_000 * 50 / 10
    key = _pick({"A": 200_000, "B": 100_000, "C": 20_000, "D": 40_000}, n)
    return {"answer": key, "computed": n}


def cs_i1c14_002_b():
    paid = 40 / 50 * 10
    key = _pick({"A": 8, "B": 2, "C": 10, "D": 40}, paid, tolerance=0.001)
    return {"answer": key, "computed": paid}


# ── case set 3: Pennar Fabrics (surrender) ───────────────────────────────
# 30,000 × ₹20 → sub-divide into ₹4 (1,50,000 shares); surrender 50%;
# creditors 2,60,000 accept 60,000 shares (₹2,40,000); rest cancelled.

def cs_i1c14_003_a():
    surrendered = 30_000 * 5 * 0.5 * 4
    key = _pick({"A": 600_000, "B": 150_000, "C": 75_000, "D": 300_000}, surrendered)
    return {"answer": key, "computed": surrendered}


def cs_i1c14_003_b():
    sacrifice = 260_000 - 60_000 * 4
    key = _pick({"A": 260_000, "B": 240_000, "C": 20_000, "D": 60_000}, sacrifice)
    return {"answer": key, "computed": sacrifice}


def cs_i1c14_003_c():
    cancelled = (75_000 - 60_000) * 4
    key = _pick({"A": 60_000, "B": 300_000, "C": 15_000, "D": 240_000}, cancelled)
    return {"answer": key, "computed": cancelled}


def cs_i1c14_003_d():
    total = (260_000 - 240_000) + (75_000 - 60_000) * 4
    key = _pick({"A": 320_000, "B": 60_000, "C": 80_000, "D": 20_000}, total)
    return {"answer": key, "computed": total}


# ── case set 4: Bhima Alloys (reduction + account) ───────────────────────
# 1,20,000 × ₹10 → ₹5; plant +45,000; debentures 4,00,000 settled at
# 3,25,000; write off P&L 5,10,000 + goodwill 95,000 + discount 15,000;
# scheme expenses 10,000.

def cs_i1c14_004_a():
    credit = 120_000 * (10 - 5)
    key = _pick({"A": 1_200_000, "B": 90_000, "C": 720_000, "D": 600_000}, credit)
    return {"answer": key, "computed": credit}


def cs_i1c14_004_b():
    credits = 120_000 * 5 + 45_000 + (400_000 - 325_000)
    key = _pick({"A": 600_000, "B": 675_000, "C": 645_000, "D": 720_000}, credits)
    return {"answer": key, "computed": credits}


def cs_i1c14_004_c():
    credits = 720_000
    debits = 510_000 + 95_000 + 15_000 + 10_000
    balance = credits - debits
    assert balance > 0, "credit balance → capital reserve"
    key = _pick({"A": 105_000, "B": 90_000, "C": 0, "D": 100_000}, balance)
    return {"answer": key, "computed": balance}


def cs_i1c14_004_d():
    capital = 120_000 * 5
    key = _pick({"A": 690_000, "B": 1_200_000, "C": 720_000, "D": 600_000}, capital)
    return {"answer": key, "computed": capital}
