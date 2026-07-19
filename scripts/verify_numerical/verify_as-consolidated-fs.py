"""Verifier for intermediate/advanced-accounting/as-consolidated-fs.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring Ch 10 mechanics (SM Ch 10 U1–U3):
  AS 21 cost of control   goodwill = cost − parent% × equity AT ACQUISITION
                          (capital reserve when negative); equity at
                          acquisition includes time-apportioned current-year
                          profit up to the acquisition date
  AS 21 minority interest MI% × ENTIRE equity at the balance sheet date
  AS 21 unrealised profit stock × margin fraction (m/(100+m) if on cost,
                          m% of invoice if on selling price), eliminated in
                          FULL both upstream and downstream
  AS 21 minority losses   excess of minority loss share over MI is adjusted
                          against the majority (no binding obligation)
  AS 23 equity method     cost + investor% × profits − investor% × dividends;
                          losses recognised only down to nil; resumption
                          only after unrecognised losses are matched;
                          eliminations at investor% only
  AS 27 proportionate     venturer% × each line item; sale to JV recognises
                          only the OTHER venturers' portion of the gain;
                          purchase from JV defers the venturer's own share

Goodwill-vs-capital-reserve questions (q-i1c10-006/007, cs-i1c10-001-b,
cs-i1c10-003-a) map (direction, amount) tuples because the same rupee figure
appears with both directions among the options. cs-i1c10-003-d maps
(loss recognised, additional provision) pairs for the same reason.
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


def _cost_of_control(cost, share, equity_at_acq):
    """(direction, amount): goodwill when cost exceeds the equity share."""
    diff = cost - share * equity_at_acq
    return ("goodwill", diff) if diff >= 0 else ("capital reserve", -diff)


# ── standalone MCQs · AS 21 ──────────────────────────────────────────────

def q_i1c10_006():
    # cost 7,50,000 vs 70% of acquisition-date equity (6,00,000 + 3,00,000);
    # the 31.3.X2 reserves of 4,50,000 are post-acquisition noise
    result = _cost_of_control(750_000, 0.70, 600_000 + 300_000)
    key = _pick({"A": ("goodwill", 120_000), "B": ("goodwill", 15_000),
                 "C": ("goodwill", 330_000), "D": ("capital reserve", 120_000)},
                result)
    return {"answer": key, "computed": result}


def q_i1c10_007():
    # cost 3,90,000 vs 60% of (5,00,000 + 2,00,000) = 4,20,000
    result = _cost_of_control(390_000, 0.60, 500_000 + 200_000)
    key = _pick({"A": ("goodwill", 30_000), "B": ("capital reserve", 30_000),
                 "C": ("goodwill", 90_000), "D": ("capital reserve", 310_000)},
                result)
    return {"answer": key, "computed": result}


def q_i1c10_008():
    # MI = 25% × entire equity at BS date (capital + all reserves + P&L)
    mi = 0.25 * (400_000 + 160_000 + 80_000)
    key = _pick({"A": 100_000, "B": 125_000, "C": 140_000, "D": 160_000}, mi)
    return {"answer": key, "computed": mi}


def q_i1c10_011():
    # upstream stock 1,80,000 at cost + 20% → 20/120 of invoice, in full
    up = 180_000 * 20 / 120
    key = _pick({"A": 22_500, "B": 30_000, "C": 36_000, "D": 7_500}, up)
    return {"answer": key, "computed": up}


def q_i1c10_012():
    # downstream stock 2,40,000 at 20X margin ON SELLING PRICE (25%), in full
    up = 0.25 * 240_000
    key = _pick({"A": 60_000, "B": 48_000, "C": 42_000, "D": 0}, up)
    return {"answer": key, "computed": up}


def q_i1c10_016():
    # minority loss share 1,30,000 vs MI 90,000 → excess borne by majority
    excess = 130_000 - 90_000
    key = _pick({"A": 40_000, "B": 0, "C": 130_000, "D": 90_000}, excess)
    return {"answer": key, "computed": excess}


# ── standalone MCQs · AS 23 ──────────────────────────────────────────────

def q_i1c10_023():
    # cost 6,00,000 + 40% × 3,00,000 profit − 40% × 1,00,000 dividend
    carrying = 600_000 + 0.40 * 300_000 - 0.40 * 100_000
    key = _pick({"A": 720_000, "B": 620_000, "C": 680_000, "D": 600_000},
                carrying)
    return {"answer": key, "computed": carrying}


def q_i1c10_026():
    # carrying 80,000 − year-1 loss 55,000 = 25,000; year-2 recognition
    # capped at the remaining carrying amount (no guaranteed obligations)
    remaining = 80_000 - 55_000
    recognised = min(45_000, remaining)
    key = _pick({"A": 45_000, "B": 25_000, "C": 0, "D": 20_000}, recognised)
    return {"answer": key, "computed": recognised}


def q_i1c10_027():
    # profit share 35,000 first absorbs unrecognised losses 20,000
    recognised = 35_000 - 20_000
    key = _pick({"A": 35_000, "B": 0, "C": 20_000, "D": 15_000}, recognised)
    return {"answer": key, "computed": recognised}


def q_i1c10_028():
    # associate elimination only to the investor's 30% interest
    eliminated = 0.30 * 60_000
    key = _pick({"A": 18_000, "B": 60_000, "C": 0, "D": 42_000}, eliminated)
    return {"answer": key, "computed": eliminated}


# ── standalone MCQs · AS 27 ──────────────────────────────────────────────

def q_i1c10_035():
    # proportionate consolidation: 30% of each line item, gross
    included = (0.30 * 900_000, 0.30 * 3_000_000)
    key = _pick({"A": (900_000, 3_000_000), "B": (0, 0),
                 "C": (270_000, 900_000), "D": (270_000, 0)}, included)
    return {"answer": key, "computed": included}


def q_i1c10_038():
    # sale TO the JV: recognise only the other venturers' 60% of the gain
    recognised = (1 - 0.40) * 90_000
    key = _pick({"A": 54_000, "B": 90_000, "C": 36_000, "D": 0}, recognised)
    return {"answer": key, "computed": recognised}


# ── cs-i1c10-001 · Himgiri Fabricators (AS 21 first consolidation) ───────

H_SHARE = 0.75
H_COST = 465_000
S_CAPITAL = 400_000
S_GEN_RES = 80_000
S_OPENING_PL = 40_000
S_YEAR_PROFIT = 96_000
PRE_MONTHS = 3   # 1 April → 1 July


def _pre_acq_profits():
    return S_GEN_RES + S_OPENING_PL + S_YEAR_PROFIT * PRE_MONTHS / 12


def _post_acq_profit():
    return S_YEAR_PROFIT * (12 - PRE_MONTHS) / 12


def cs_i1c10_001_a():
    pre = _pre_acq_profits()
    key = _pick({"A": 120_000, "B": 144_000, "C": 216_000, "D": 108_000}, pre)
    return {"answer": key, "computed": pre}


def cs_i1c10_001_b():
    result = _cost_of_control(H_COST, H_SHARE, S_CAPITAL + _pre_acq_profits())
    key = _pick({"A": ("goodwill", 75_000), "B": ("capital reserve", 57_000),
                 "C": ("goodwill", 3_000), "D": ("goodwill", 57_000)}, result)
    return {"answer": key, "computed": result}


def cs_i1c10_001_c():
    # MI = 25% × entire equity at 31.3.X2
    mi = (1 - H_SHARE) * (S_CAPITAL + S_GEN_RES + S_OPENING_PL + S_YEAR_PROFIT)
    key = _pick({"A": 154_000, "B": 136_000, "C": 130_000, "D": 100_000}, mi)
    return {"answer": key, "computed": mi}


def cs_i1c10_001_d():
    share = H_SHARE * _post_acq_profit()
    key = _pick({"A": 72_000, "B": 96_000, "C": 54_000, "D": 18_000}, share)
    return {"answer": key, "computed": share}


# ── cs-i1c10-002 · Vaigai Group (AS 21 eliminations) ─────────────────────

def cs_i1c10_002_a():
    # upstream: stock 1,50,000 at cost + 25% → 25/125 of invoice, in full
    up = 150_000 * 25 / 125
    key = _pick({"A": 37_500, "B": 24_000, "C": 30_000, "D": 6_000}, up)
    return {"answer": key, "computed": up}


def cs_i1c10_002_b():
    # downstream: stock 1,00,000 at 20% margin ON SELLING PRICE, in full
    up = 0.20 * 100_000
    key = _pick({"A": 20_000, "B": 16_667, "C": 16_000, "D": 0}, up)
    return {"answer": key, "computed": up}


# ── cs-i1c10-003 · Aravali Industries (AS 23 equity method) ──────────────

A_SHARE = 0.25
A_COST = 500_000
C_NET_ASSETS = 1_600_000
C_PROFIT_X2 = 240_000
C_DIVIDEND_X2 = 80_000
A_LOSS_SHARE_X3 = 590_000


def _carrying_x2():
    return A_COST + A_SHARE * C_PROFIT_X2 - A_SHARE * C_DIVIDEND_X2


def cs_i1c10_003_a():
    result = _cost_of_control(A_COST, A_SHARE, C_NET_ASSETS)
    key = _pick({"A": ("goodwill", 0), "B": ("goodwill", 100_000),
                 "C": ("capital reserve", 100_000), "D": ("goodwill", 400_000)},
                result)
    return {"answer": key, "computed": result}


def cs_i1c10_003_b():
    carrying = _carrying_x2()
    key = _pick({"A": 560_000, "B": 500_000, "C": 480_000, "D": 540_000},
                carrying)
    return {"answer": key, "computed": carrying}


def cs_i1c10_003_d():
    # loss recognised capped at the carrying amount; no obligations → no
    # additional provision. Options map (recognised, additional provision).
    recognised = min(A_LOSS_SHARE_X3, _carrying_x2())
    provision = 0    # nothing guaranteed
    key = _pick({"A": (590_000, 0), "B": (0, 0),
                 "C": (540_000, 0), "D": (540_000, 50_000)},
                (recognised, provision))
    return {"answer": key, "computed": (recognised, provision)}


# ── cs-i1c10-004 · Netravati Ventures (AS 27 JCE) ────────────────────────

V_SHARE = 0.40
W_PPE = 1_250_000
W_REVENUE = 2_500_000
W_EXPENSES = 2_000_000
W_PROFIT_ON_SALE = 50_000


def cs_i1c10_004_a():
    included = V_SHARE * W_PPE
    key = _pick({"A": 1_250_000, "B": 0, "C": 750_000, "D": 500_000}, included)
    return {"answer": key, "computed": included}


def cs_i1c10_004_b():
    # 40% of revenue and of expenses, netting to 40% of the profit
    effect = V_SHARE * (W_REVENUE - W_EXPENSES)
    key = _pick({"A": 500_000, "B": 200_000, "C": 300_000, "D": 0}, effect)
    return {"answer": key, "computed": effect}


def cs_i1c10_004_d():
    # purchase FROM the JV: defer the venturer's own share of the JV's profit
    deferred = V_SHARE * W_PROFIT_ON_SALE
    key = _pick({"A": 20_000, "B": 50_000, "C": 30_000, "D": 0}, deferred)
    return {"answer": key, "computed": deferred}
