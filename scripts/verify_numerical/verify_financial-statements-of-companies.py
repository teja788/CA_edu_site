"""Verifier for intermediate/advanced-accounting/financial-statements-of-companies.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring Ch 11 mechanics (Schedule III Division I; AS 3):
  operating cycle    sum of the inventory-to-cash legs (RM + WIP + FG + collection)
  current maturity   instalments due within 12 months of the reporting date
  revenue            billings − GST collected for government
  cash equivalents   ≤ 3 months to maturity FROM ACQUISITION; no value risk
  indirect method    NP + non-cash charges ± other-activity items ± working capital
  tax paid           opening provision + P&L charge − closing provision
  asset account      purchases = closing + depreciation + WDV sold − opening

Options in (₹…) parentheses are outflows/negative in the option maps below.
"""


def _pick(options, value, tolerance=0.5):
    """Map a computed value to its option key (rupee amounts may float)."""
    for key, v in options.items():
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value} matches no option in {options}")


# ── standalone MCQs ──────────────────────────────────────────────────────

def q_i1c11_004():
    # RM 2 + WIP 1 + FG 2 + collection 3 (months)
    cycle = 2 + 1 + 2 + 3
    key = _pick({"A": 3, "B": 5, "C": 12, "D": 8}, cycle, tolerance=0.001)
    return {"answer": key, "computed": cycle}


def q_i1c11_006():
    # 10,00,000 / 5 annual instalments; first at month 4, next at month 16
    instalment = 1_000_000 / 5
    due_within_12m = instalment * 1
    key = _pick({"A": 1_000_000, "B": 200_000, "C": 0, "D": 400_000}, due_within_12m)
    return {"answer": key, "computed": due_within_12m}


def q_i1c11_009():
    # 5,00,000 shares + bonus 1:5
    closing = 500_000 + 500_000 // 5
    key = _pick({"A": 600_000, "B": 520_000, "C": 500_000, "D": 1_000_000}, closing)
    return {"answer": key, "computed": closing}


def q_i1c11_011():
    # billings 59,00,000 incl GST 9,00,000
    rfo = 5_900_000 - 900_000
    key = _pick({"A": 4_500_000, "B": 6_800_000, "C": 5_900_000, "D": 5_000_000}, rfo)
    return {"answer": key, "computed": rfo}


def q_i1c11_015():
    # 2-month T-bills 3,00,000 + cash 50,000 (6-month FD and equity fail)
    ce = 300_000 + 50_000
    key = _pick({"A": 850_000, "B": 1_050_000, "C": 350_000, "D": 50_000}, ce)
    return {"answer": key, "computed": ce}


def q_i1c11_017():
    # NP + dep + loss on sale − ↑debtors + ↓inventory + ↑creditors
    cgo = 420_000 + 80_000 + 10_000 - 30_000 + 20_000 + 15_000
    key = _pick({"A": 500_000, "B": 545_000, "C": 515_000, "D": 495_000}, cgo)
    return {"answer": key, "computed": cgo}


def q_i1c11_020():
    # −machinery + sale proceeds − investments + dividend received
    investing = -600_000 + 150_000 - 200_000 + 40_000
    key = _pick({"A": -810_000, "B": -650_000, "C": -610_000, "D": -410_000}, investing)
    return {"answer": key, "computed": investing}


def q_i1c11_021():
    # +shares − loan repaid − dividend paid − interest paid
    financing = 800_000 - 300_000 - 120_000 - 60_000
    key = _pick({"A": 380_000, "B": 500_000, "C": 320_000, "D": 260_000}, financing)
    return {"answer": key, "computed": financing}


def q_i1c11_023():
    # opening provision + charge − closing provision
    paid = 90_000 + 120_000 - 105_000
    key = _pick({"A": 90_000, "B": 120_000, "C": 105_000, "D": 135_000}, paid)
    return {"answer": key, "computed": paid}


def q_i1c11_025():
    # purchases = closing + dep + WDV sold − opening
    purchases = 950_000 + 100_000 + 50_000 - 800_000
    key = _pick({"A": 200_000, "B": 150_000, "C": 300_000, "D": 250_000}, purchases)
    return {"answer": key, "computed": purchases}


def q_i1c11_027():
    # receipts = sales − increase in receivables
    receipts = 2_000_000 - 160_000
    key = _pick({"A": 2_160_000, "B": 1_840_000, "C": 2_000_000, "D": 1_680_000}, receipts)
    return {"answer": key, "computed": receipts}


# ── case set 1: Narmada Shipworks (classification, long cycle) ───────────
# RM 4 + WIP 3 + FG 5 + collection 3; term loan 12,00,000 in six
# half-yearly instalments of 2,00,000 starting month 6.

def cs_i1c11_001_a():
    cycle = 4 + 3 + 5 + 3
    key = _pick({"A": 12, "B": 3, "C": 15, "D": 9}, cycle, tolerance=0.001)
    return {"answer": key, "computed": cycle}


def cs_i1c11_001_c():
    # instalments at months 6 and 12 fall within twelve months
    current = 200_000 * 2
    key = _pick({"A": 1_200_000, "B": 400_000, "C": 0, "D": 200_000}, current)
    return {"answer": key, "computed": current}


# ── case set 2: Chenab Textiles (capital and P&L disclosures) ────────────
# 8,00,000 shares; rights 1:4; billings 62,40,000 incl GST 6,40,000.

def cs_i1c11_002_a():
    closing = 800_000 + 800_000 // 4
    key = _pick({"A": 1_000_000, "B": 900_000, "C": 800_000, "D": 1_200_000}, closing)
    return {"answer": key, "computed": closing}


def cs_i1c11_002_b():
    rfo = 6_240_000 - 640_000
    key = _pick({"A": 6_240_000, "B": 4_960_000, "C": 5_600_000, "D": 6_880_000}, rfo)
    return {"answer": key, "computed": rfo}


# ── case set 3: Periyar Chemicals (indirect method, all sections) ────────
# NPBT 6,50,000; dep 1,20,000; profit on sale of investments 20,000;
# interest 45,000; ↑debtors 70,000; ↓inventory 40,000; ↑creditors 25,000;
# tax paid 1,80,000; plant −3,00,000; investment proceeds 1,20,000;
# loan +2,00,000; dividend −90,000; interest paid −45,000.

def cs_i1c11_003_a():
    before_wc = 650_000 + 120_000 - 20_000 + 45_000
    key = _pick({"A": 750_000, "B": 650_000, "C": 795_000, "D": 835_000}, before_wc)
    return {"answer": key, "computed": before_wc}


def cs_i1c11_003_b():
    generated = 795_000 - 70_000 + 40_000 + 25_000
    cfo = generated - 180_000
    key = _pick({"A": 565_000, "B": 610_000, "C": 680_000, "D": 790_000}, cfo)
    return {"answer": key, "computed": cfo}


def cs_i1c11_003_c():
    investing = -300_000 + 120_000
    key = _pick({"A": -200_000, "B": -180_000, "C": -300_000, "D": -160_000}, investing)
    return {"answer": key, "computed": investing}


def cs_i1c11_003_d():
    financing = 200_000 - 90_000 - 45_000
    key = _pick({"A": -135_000, "B": 110_000, "C": 65_000, "D": 200_000}, financing)
    return {"answer": key, "computed": financing}


def cs_i1c11_003_e():
    net = 610_000 - 180_000 + 65_000
    # sanity: the three sections must be internally consistent
    assert net == (795_000 - 70_000 + 40_000 + 25_000 - 180_000) + (-300_000 + 120_000) + (200_000 - 90_000 - 45_000)
    key = _pick({"A": 495_000, "B": 430_000, "C": 610_000, "D": 515_000}, net)
    return {"answer": key, "computed": net}
