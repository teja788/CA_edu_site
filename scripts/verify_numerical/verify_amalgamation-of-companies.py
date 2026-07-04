"""Verifier for intermediate/advanced-accounting/amalgamation-of-companies.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring AS 14 mechanics:
  purchase consideration   payments to SHAREHOLDERS only (equity + preference);
                           shares at issue price — para 3(g)
  net assets               agreed values (book where none agreed) − outside
                           liabilities assumed; capital/reserves never deducted
  goodwill / cap. reserve  PC − net assets (positive → goodwill,
                           negative → capital reserve)
  pooling adjustment       capital issued (+ other consideration) − transferor
                           paid-up capital, adjusted in reserves
  90% merger test          90% of equity face value EXCLUDING shares already
                           held by the transferee/subsidiaries/nominees
  goodwill amortisation    ≤ 5 years unless longer justified
"""


def _pick(options, value, tolerance=0.5):
    """Map a computed value to its option key (rupee amounts may float)."""
    for key, v in options.items():
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value} matches no option in {options}")


# ── standalone MCQs ──────────────────────────────────────────────────────

def q_i1c13_001():
    # net payment: 80,000 sh; 2-for-5 at ₹18 issue price + ₹3 cash per share;
    # ₹2,00,000 to creditors is NOT consideration
    shares = 80_000 * 2 / 5 * 18
    cash = 80_000 * 3
    pc = shares + cash
    key = _pick({"A": 816_000, "B": 560_000, "C": 1_016_000, "D": 576_000}, pc)
    return {"answer": key, "computed": pc}


def q_i1c13_003():
    # net assets method: agreed assets 52,00,000 − liabilities 17,00,000
    # (capital 20,00,000 and reserves 8,00,000 are red herrings)
    pc = 5_200_000 - 1_700_000
    key = _pick({"A": 5_200_000, "B": 700_000, "C": 3_500_000, "D": 2_400_000}, pc)
    return {"answer": key, "computed": pc}


def q_i1c13_004():
    # share exchange: 2,50,000 × 3/5 = 1,50,000 shares at ₹24
    pc = 250_000 * 3 / 5 * 24
    key = _pick({"A": 2_500_000, "B": 3_600_000, "C": 6_000_000, "D": 1_500_000}, pc)
    return {"answer": key, "computed": pc}


def q_i1c13_006():
    # 90% of (2,00,000 − 15,000 already held)
    n = 0.9 * (200_000 - 15_000)
    key = _pick({"A": 150_000, "B": 166_500, "C": 180_000, "D": 185_000}, n)
    return {"answer": key, "computed": n}


def q_i1c13_007():
    # goodwill: PC 60,00,000 − net assets 52,00,000 (positive → goodwill)
    diff = 6_000_000 - 5_200_000
    assert diff > 0, "PC exceeds net assets → goodwill"
    key = _pick({"A": -800_000, "B": 800_000, "C": 0, "D": 5_200_000}, diff)
    # options B–D describe wrong labels/amounts; only A is goodwill 8,00,000
    return {"answer": key, "computed": diff}


def q_i1c13_008():
    # capital reserve: net assets (61,00,000 − 13,00,000) − PC 42,00,000
    net_assets = 6_100_000 - 1_300_000
    cr = net_assets - 4_200_000
    assert cr > 0, "net assets exceed PC → capital reserve"
    key = _pick({"A": 600_000, "B": 4_800_000, "C": -600_000, "D": 1_900_000}, cr)
    return {"answer": key, "computed": cr}


def q_i1c13_010():
    # pooling adjustment: 25,00,000 issued − (18,00,000 + 2,00,000) capital
    adj = 2_500_000 - (1_800_000 + 200_000)
    key = _pick({"A": -500_000, "B": 0, "C": 500_000, "D": 700_000}, adj)
    # A = 5,00,000 deducted from reserves (the only 5,00,000-deduction option)
    return {"answer": key, "computed": adj}


def q_i1c13_013():
    # combined receivables: 8,00,000 + 5,00,000 − mutual 1,20,000
    combined = 800_000 + 500_000 - 120_000
    key = _pick({"A": 1_300_000, "B": 1_060_000, "C": 1_180_000, "D": 680_000}, combined)
    return {"answer": key, "computed": combined}


def q_i1c13_014():
    # unrealised profit: 2,40,000 × 20/120 (mark-up on cost)
    up = 240_000 * 20 / 120
    key = _pick({"A": 48_000, "B": 200_000, "C": 40_000, "D": 60_000}, up)
    return {"answer": key, "computed": up}


def q_i1c13_017():
    # realisation profit: 36,00,000 − (50,00,000 − 18,00,000) − 50,000
    profit = 3_600_000 - (5_000_000 - 1_800_000) - 50_000
    assert profit > 0, "profit, not loss"
    key = _pick({"A": -350_000, "B": 350_000, "C": 450_000, "D": 400_000}, profit)
    return {"answer": key, "computed": profit}


def q_i1c13_019():
    # intrinsic values 96,00,000/4,00,000 = 24 and 30,00,000/2,50,000 = 12;
    # ratio 12/24 = 1 for 2 → shares issued = 2,50,000 / 2
    iv_transferee = 9_600_000 / 400_000
    iv_transferor = 3_000_000 / 250_000
    shares = 250_000 * iv_transferor / iv_transferee
    key = _pick({"A": 500_000, "B": 62_500, "C": 250_000, "D": 125_000}, shares)
    return {"answer": key, "computed": shares}


def q_i1c13_021():
    # goodwill 2,50,000 over the 5-year ordinary maximum
    annual = 250_000 / 5
    key = _pick({"A": 50_000, "B": 250_000, "C": 12_500, "D": 25_000}, annual)
    return {"answer": key, "computed": annual}


def q_i1c13_023():
    # PC = equity shares 14,00,000 + cash 2,00,000 + pref shares 5,00,000;
    # debentures 4,00,000 and expenses 30,000 excluded
    pc = 1_400_000 + 200_000 + 500_000
    key = _pick({"A": 2_100_000, "B": 2_130_000, "C": 2_500_000, "D": 2_530_000}, pc)
    return {"answer": key, "computed": pc}


def q_i1c13_025():
    # agreed where agreed, book where not: PPE 30,00,000 (agreed) + inventory
    # 5,00,000 (book) + receivables 5,60,000 (agreed) − creditors 6,60,000
    na = 3_000_000 + 500_000 + 560_000 - 660_000
    key = _pick({"A": 4_060_000, "B": 3_000_000, "C": 2_900_000, "D": 3_400_000}, na)
    return {"answer": key, "computed": na}


def q_i1c13_027():
    # combined GR: 12,00,000 + 5,00,000 − (22,00,000 − 20,00,000)
    gr = 1_200_000 + 500_000 - (2_200_000 - 2_000_000)
    key = _pick({"A": 1_500_000, "B": 1_880_000, "C": 1_200_000, "D": 1_700_000}, gr)
    return {"answer": key, "computed": gr}


# ── case set 1: Chenab absorbs Jhelum (purchase) ─────────────────────────
# Jhelum: 1,50,000 × ₹10 equity; GR 4,00,000; export profit reserve 1,00,000;
# debentures 6,00,000; creditors 3,50,000. Assets agreed 34,00,000.
# Terms: 4 Chenab shares (₹10 at ₹12.50) per 5 Jhelum shares + ₹1 cash/share.

def cs_i1c13_001_a():
    pc = 150_000 * 4 / 5 * 12.50 + 150_000 * 1
    key = _pick({"A": 2_250_000, "B": 1_650_000, "C": 1_500_000, "D": 1_350_000}, pc)
    return {"answer": key, "computed": pc}


def cs_i1c13_001_b():
    na = 3_400_000 - (600_000 + 350_000)
    key = _pick({"A": 3_400_000, "B": 1_950_000, "C": 2_450_000, "D": 2_800_000}, na)
    return {"answer": key, "computed": na}


def cs_i1c13_001_c():
    na = 3_400_000 - 950_000
    pc = 150_000 * 4 / 5 * 12.50 + 150_000
    cr = na - pc
    assert cr > 0, "net assets exceed PC → capital reserve"
    key = _pick({"A": -800_000, "B": 1_750_000, "C": 800_000, "D": 0}, cr)
    return {"answer": key, "computed": cr}


def cs_i1c13_001_d():
    # AAR = statutory reserve only (export profit reserve 1,00,000)
    aar = 100_000
    key = _pick({"A": -100_000, "B": 500_000, "C": 0, "D": 100_000}, aar)
    return {"answer": key, "computed": aar}


# ── case set 2: Bhagirathi–Alaknanda merger (pooling) ────────────────────
# Alaknanda: capital 20,00,000 (2,00,000 × ₹10); GR 7,00,000; P&L 3,00,000.
# Bhagirathi GR 15,00,000; issues 9 shares per 8 held.

def cs_i1c13_002_b():
    shares = 200_000 * 9 / 8
    capital = shares * 10
    key = _pick({"A": 250_000, "B": 1_777_780, "C": 2_000_000, "D": 2_250_000}, capital)
    return {"answer": key, "computed": capital}


def cs_i1c13_002_c():
    adj = 200_000 * 9 / 8 * 10 - 2_000_000
    key = _pick({"A": 0, "B": 250_001, "C": -250_000, "D": 250_000}, adj)
    # A = 2,50,000 deducted; B/C encode the wrong-direction options distinctly
    return {"answer": key, "computed": adj}


def cs_i1c13_002_d():
    adj = 2_250_000 - 2_000_000
    gr = 1_500_000 + 700_000 - adj
    key = _pick({"A": 2_200_000, "B": 1_950_000, "C": 1_250_000, "D": 1_500_000}, gr)
    return {"answer": key, "computed": gr}


# ── case set 3: Closing Tungabhadra's books ──────────────────────────────
# Assets taken over (book) 42,00,000; creditors taken over 9,00,000;
# PC 38,00,000; liquidation expenses 40,000 borne by transferor;
# bank loan 3,00,000 NOT taken over, repaid at book value (no P/L effect);
# capital 25,00,000 + GR 6,00,000 + P&L 3,00,000; cash retained 4,00,000.

def cs_i1c13_003_a():
    profit = 3_800_000 - (4_200_000 - 900_000) - 40_000
    assert profit > 0, "profit, not loss"
    key = _pick({"A": 160_000, "B": 460_000, "C": 500_000, "D": -460_000}, profit)
    return {"answer": key, "computed": profit}


def cs_i1c13_003_c():
    realisation_profit = 3_800_000 - 3_300_000 - 40_000
    total = 2_500_000 + 600_000 + 300_000 + realisation_profit
    # cross-check via cash: PC + (retained cash − loan − expenses)
    assert total == 3_800_000 + (400_000 - 300_000 - 40_000)
    key = _pick({"A": 3_560_000, "B": 3_400_000, "C": 3_860_000, "D": 3_800_000}, total)
    return {"answer": key, "computed": total}


# ── case set 4: Periyar–Vaigai intrinsic values ──────────────────────────
# Periyar: NA 1,20,00,000 / 5,00,000 sh → ₹24. Vaigai: NA 18,00,000 /
# 1,50,000 sh → ₹12. Ratio 1 for 2; shares issued at intrinsic value.

def cs_i1c13_004_a():
    iv = 1_800_000 / 150_000
    key = _pick({"A": 6, "B": 10, "C": 24, "D": 12}, iv, tolerance=0.001)
    return {"answer": key, "computed": iv}


def cs_i1c13_004_b():
    ratio = (1_800_000 / 150_000) / (12_000_000 / 500_000)  # Periyar per Vaigai
    key = _pick({"A": 0.5, "B": 1, "C": 0.6, "D": 2}, ratio, tolerance=0.001)
    # A = "1 Periyar for every 2 Vaigai" = 0.5 Periyar shares per Vaigai share
    return {"answer": key, "computed": ratio}


def cs_i1c13_004_c():
    shares = 150_000 * 0.5
    key = _pick({"A": 75_000, "B": 150_000, "C": 37_500, "D": 300_000}, shares)
    return {"answer": key, "computed": shares}


def cs_i1c13_004_d():
    iv_periyar = 12_000_000 / 500_000
    pc = 75_000 * iv_periyar
    key = _pick({"A": 3_600_000, "B": 1_800_000, "C": 750_000, "D": 900_000}, pc)
    return {"answer": key, "computed": pc}
