"""Verifier for intermediate/advanced-accounting/as-items-impacting-fs.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring Ch 7 mechanics (SM Ch 7 U1–U4):
  AS 4 insolvency       provision = year-end debt × (1 − recovery paise/₹);
                        adjusting event, provided at the balance sheet date
  AS 4 NRV evidence     inventory = lower(cost, post-year-end sale price
                        evidencing year-end NRV)
  AS 4 suit settled     adjust provision UP TO the settled amount (top-up
                        = settled − existing provision)
  AS 5 prior period     error/omission of an earlier year → charge in the
                        CURRENT P&L, separately disclosed (no restatement)
  AS 5 estimate change  new depreciation = carrying amount at date of
                        revision ÷ revised REMAINING life (prospective)
  AS 5 policy impact    profit impact = closing inventory under new formula
                        − under old formula; disclosed quantified
  AS 11 monetary        restate at closing rate; difference → P&L
  AS 11 non-monetary    historical-cost items stay at transaction-date rate
  AS 11 non-integral    ALL assets at closing rate; difference → FCTR
  AS 11 forward hedge   premium = (forward − spot at inception) × FC amount,
                        amortised straight-line over the contract life
  AS 11 forward spec    MTM gain = (forward rate for remaining maturity −
                        contracted forward rate) × FC amount
  AS 22 current tax     taxable = book profit + permanent add-backs
                        + timing add-backs − extra tax depreciation
  AS 22 deferred        DTL/DTA = timing difference × enacted rate;
                        permanent differences carry no deferred tax
  AS 22 loss DTA        capped at virtually-certain future income × rate

Treatment-sensitive questions (q-i1c07-013/017/019/020/023/031, the cs
prior-period and suit-settlement subs) map (treatment, amount) tuples —
the rupee figure alone is not unique across their options.
"""


def _pick(options, value, tolerance=0.5):
    """Map a computed value to its option key (rupee amounts may float)."""
    for key, v in options.items():
        if isinstance(v, tuple) or isinstance(value, tuple):
            if v == value:
                return key
            continue
        if abs(v - value) <= tolerance:
            return key
    raise AssertionError(f"computed {value} matches no option in {options}")


# ── standalone MCQs · AS 4 ───────────────────────────────────────────────

def q_i1c07_003():
    # debtor 5,00,000; recovery 30 paise/₹ → provide the irrecoverable slice
    provision = 500_000 * (1 - 0.30)
    key = _pick({"A": 500_000, "B": 350_000, "C": 150_000, "D": 0}, provision)
    return {"answer": key, "computed": provision}


def q_i1c07_007():
    # post-year-end sale evidences year-end NRV → lower of cost and NRV
    carrying = min(800_000, 650_000)
    key = _pick({"A": 800_000, "B": 725_000, "C": 650_000, "D": 150_000}, carrying)
    return {"answer": key, "computed": carrying}


# ── standalone MCQs · AS 5 ───────────────────────────────────────────────

def q_i1c07_013():
    # omitted prior-year repairs → current P&L, prior period item, disclosed
    amount = 260_000
    treatment = "current_pl"          # AS 5 never restates or routes via reserves
    key = _pick({"A": ("current_pl", 260_000), "B": ("restate", 260_000),
                 "C": ("reserves", 260_000), "D": ("extraordinary", 260_000)},
                (treatment, amount))
    return {"answer": key, "computed": (treatment, amount)}


def q_i1c07_014():
    # cost 12,00,000, 10-yr SLM; after 5 yrs remaining life revised to 2
    carrying = 1_200_000 - 5 * (1_200_000 / 10)
    dep = carrying / 2
    key = _pick({"A": 120_000, "B": 240_000, "C": 300_000, "D": 600_000}, dep)
    return {"answer": key, "computed": dep}


def q_i1c07_017():
    # WA 15,40,000 → FIFO 16,10,000: higher closing inventory = higher profit
    impact = 1_610_000 - 1_540_000
    direction = "higher" if impact > 0 else "lower"
    key = _pick({"A": ("higher", 70_000), "B": ("lower", 70_000),
                 "C": ("none", 0), "D": ("closing_only", 1_610_000)},
                (direction, impact))
    return {"answer": key, "computed": (direction, impact)}


# ── standalone MCQs · AS 11 ──────────────────────────────────────────────

def q_i1c07_019():
    # $80,000 creditor: 82.50 → 84.00; monetary item, difference to P&L
    diff = round((84.00 - 82.50) * 80_000)
    treatment = "pl_loss" if diff > 0 else "pl_gain"   # rupee cost rose → loss
    key = _pick({"A": ("nil", 0), "B": ("inventory", 120_000),
                 "C": ("pl_gain", 120_000), "D": ("pl_loss", 120_000)},
                (treatment, diff))
    return {"answer": key, "computed": (treatment, diff)}


def q_i1c07_020():
    # land $2,00,000 at ₹75, historical cost → transaction-date rate holds
    carrying = round(200_000 * 75)
    key = _pick({"A": ("hist", 15_000_000), "B": ("closing", 16_800_000),
                 "C": ("hist_fctr", 15_000_000), "D": ("closing_pl", 16_800_000)},
                ("hist", carrying))
    return {"answer": key, "computed": ("hist", carrying)}


def q_i1c07_023():
    # non-integral: fixed assets at CLOSING rate, difference to FCTR
    translated = round(100_000 * 70)
    key = _pick({"A": ("transaction_rate", 6_000_000),
                 "B": ("closing_fctr", 7_000_000),
                 "C": ("average", 6_500_000),
                 "D": ("closing_pl", 7_000_000)},
                ("closing_fctr", translated))
    return {"answer": key, "computed": ("closing_fctr", translated)}


def q_i1c07_026():
    # premium (83.72 − 83.00) × 50,000 over 6 months; 3 months expired (Jan–Mar)
    premium = (83.72 - 83.00) * 50_000
    amortised = premium * 3 / 6
    key = _pick({"A": 36_000, "B": 0, "C": 18_000, "D": 6_000}, amortised)
    return {"answer": key, "computed": amortised}


def q_i1c07_027():
    # speculation: MTM against the forward rate for the REMAINING maturity
    gain = (84.90 - 84.00) * 100_000
    key = _pick({"A": 50_000, "B": 90_000, "C": 0, "D": 130_000}, gain)
    return {"answer": key, "computed": gain}


# ── standalone MCQs · AS 22 ──────────────────────────────────────────────

def q_i1c07_031():
    # tax dep 3,60,000 > book dep 2,40,000 → tax postponed → DTL at 30%
    timing = 360_000 - 240_000
    deferred = round(timing * 30 / 100)
    direction = "dtl" if 360_000 > 240_000 else "dta"
    key = _pick({"A": ("dta", 36_000), "B": ("dtl", 36_000),
                 "C": ("dtl", 120_000), "D": ("nil", 0)},
                (direction, deferred))
    return {"answer": key, "computed": (direction, deferred)}


def q_i1c07_034():
    # loss 8,00,000; convincing evidence covers only 5,00,000 of future income
    supported = min(800_000, 500_000)
    dta = supported * 30 / 100
    key = _pick({"A": 240_000, "B": 0, "C": 90_000, "D": 150_000}, dta)
    return {"answer": key, "computed": dta}


# ── cs-i1c07-001 · Godavari Chemicals (AS 4 events) ──────────────────────

def cs_i1c07_001_a():
    # debtor 4,50,000; recovery 20 paise/₹ → provide the balance
    provision = 450_000 * (1 - 0.20)
    key = _pick({"A": 450_000, "B": 90_000, "C": 360_000, "D": 0}, provision)
    return {"answer": key, "computed": provision}


def cs_i1c07_001_d():
    # suit settled at 3,10,000 vs provision 2,50,000 → adjusting top-up
    top_up = 310_000 - 250_000
    key = _pick({"A": ("none", 0), "B": ("adjust_additional", 60_000),
                 "C": ("charge_full", 310_000), "D": ("contingent", 60_000)},
                ("adjust_additional", top_up))
    return {"answer": key, "computed": ("adjust_additional", top_up)}


# ── cs-i1c07-002 · Narmada Exports (AS 11 transaction + forward) ─────────

FC_AMOUNT = 40_000
SPOT_TXN, SPOT_FWD_INCEPTION, FWD_RATE, SPOT_CLOSING = 83.00, 83.60, 84.20, 84.00


def cs_i1c07_002_a():
    initial = FC_AMOUNT * SPOT_TXN     # transaction-date spot rate
    key = _pick({"A": 3_368_000, "B": 3_344_000, "C": 3_360_000, "D": 3_320_000},
                initial)
    return {"answer": key, "computed": initial}


def cs_i1c07_002_b():
    # creditor restated at closing spot; hedge does not suspend restatement
    diff = round((SPOT_CLOSING - SPOT_TXN) * FC_AMOUNT)
    treatment = "pl_loss" if diff > 0 else "pl_gain"
    key = _pick({"A": ("pl_loss", 40_000), "B": ("pl_loss", 48_000),
                 "C": ("nil", 0), "D": ("inventory", 40_000)},
                (treatment, diff))
    return {"answer": key, "computed": (treatment, diff)}


def cs_i1c07_002_c():
    # premium (84.20 − 83.60) × 40,000 over 3 months; 1 month expired by 31 Mar
    premium = (FWD_RATE - SPOT_FWD_INCEPTION) * FC_AMOUNT
    amortised = premium * 1 / 3
    key = _pick({"A": 24_000, "B": 12_000, "C": 8_000, "D": 0}, amortised)
    return {"answer": key, "computed": amortised}


# ── cs-i1c07-003 · Tungabhadra Engineering (AS 22) ───────────────────────

BOOK_PROFIT, PENALTY, DOUBTFUL, EXTRA_TAX_DEP = 1_000_000, 50_000, 80_000, 130_000
TAX_RATE = 30


def _current_tax():
    taxable = BOOK_PROFIT + PENALTY + DOUBTFUL - EXTRA_TAX_DEP
    return taxable * TAX_RATE / 100


def _net_deferred_charge():
    # DTL on extra tax depreciation; DTA on doubtful debts; penalty = permanent
    dtl = EXTRA_TAX_DEP * TAX_RATE / 100
    dta = DOUBTFUL * TAX_RATE / 100
    return dtl - dta


def cs_i1c07_003_a():
    current = _current_tax()
    key = _pick({"A": 285_000, "B": 300_000, "C": 315_000, "D": 378_000}, current)
    return {"answer": key, "computed": current}


def cs_i1c07_003_b():
    # positive = charge, negative = credit
    net = _net_deferred_charge()
    key = _pick({"A": 39_000, "B": -24_000, "C": 63_000, "D": 15_000}, net)
    return {"answer": key, "computed": net}


def cs_i1c07_003_c():
    total = _current_tax() + _net_deferred_charge()
    key = _pick({"A": 315_000, "B": 300_000, "C": 339_000, "D": 285_000}, total)
    return {"answer": key, "computed": total}


# ── cs-i1c07-004 · Bhima Industries (AS 5 classification) ────────────────

def cs_i1c07_004_a():
    # omitted prior-year wages → prior period item through the current P&L
    amount = 180_000
    treatment = "current_pl"
    key = _pick({"A": ("restate", 180_000), "B": ("reserves", 180_000),
                 "C": ("current_pl", 180_000), "D": ("estimate", 180_000)},
                (treatment, amount))
    return {"answer": key, "computed": (treatment, amount)}


def cs_i1c07_004_b():
    # cost 9,00,000, 9-yr SLM; after 4 yrs remaining life revised to 2
    carrying = 900_000 - 4 * (900_000 / 9)
    dep = carrying / 2
    key = _pick({"A": 100_000, "B": 450_000, "C": 166_667, "D": 250_000}, dep)
    return {"answer": key, "computed": dep}
