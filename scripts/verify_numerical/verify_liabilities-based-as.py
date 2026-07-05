"""Verifier for intermediate/advanced-accounting/liabilities-based-as.json.

Each function recomputes the answer from the stem's parameters and maps the
computed value to the option key. Never copies the key from the bank.

Recurring Ch 6 mechanics (SM Ch 6 U1–U2):
  AS 15 short-term      expense = undiscounted amount for service rendered;
                        unpaid gap = liability
  AS 15 leave           liability = EXTRA days expected from unused
                        entitlement at BS date × daily pay
  AS 15 DB liability    PV(DBO) − unrecognised past service cost − FV(assets)
  AS 15 asset ceiling   lower(surplus, PV of refunds/contribution cuts)
  AS 15 expected return rate × opening assets + half-period rate × net
                        mid-year inflow
  AS 15 actual return   closing − opening − contributions + benefits paid
  AS 15 curtailment     gain = obligation cut − proportionate unamortised
                        past service cost
  AS 29 warranty        % by remaining-warranty band on invoice value;
                        P&L = movement in required provision
  AS 29 expected loss   Σ probability × damages per class, disclosed when
                        loss not probable per case

q-i1c06-033/034/035 map (treatment, amount) pairs — the amounts alone are
not unique across options. cs-i1c06-001-c's reserves-route distractor
carries sentinel value 27001 (same rupee figure, wrong route); the P&L
route computes 27000 exactly, and _pick's 0.5 tolerance separates them.
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


# ── standalone MCQs · AS 15 ──────────────────────────────────────────────

def q_i1c06_005():
    # salary cost 288 lakh, paid 266 lakh → expense 288, liability = gap
    liability = 288 - 266
    key = _pick({"A": 22, "B": -1, "C": -22, "D": 0}, liability)
    return {"answer": key, "computed": liability}


def q_i1c06_006():
    # 10 employees overshoot by 1.8 days each × ₹2,000/day
    liability = 10 * 1.8 * 2_000
    key = _pick({"A": 120_000, "B": 36_000, "C": 960_000, "D": 20_000}, liability)
    return {"answer": key, "computed": liability}


def q_i1c06_010():
    # expected payout 2.5% of net profit 1,80,00,000 (3% is the no-turnover rate)
    expense = 0.025 * 18_000_000
    key = _pick({"A": 0, "B": 90_000, "C": 450_000, "D": 540_000}, expense)
    return {"answer": key, "computed": expense}


def q_i1c06_014():
    # PV DBO 16,80,000 − unrecognised PSC 80,000 − plan assets 11,50,000
    liability = 1_680_000 - 80_000 - 1_150_000
    key = _pick({"A": 610_000, "B": 530_000, "C": 450_000, "D": 1_600_000}, liability)
    return {"answer": key, "computed": liability}


def q_i1c06_015():
    # asset ceiling: lower(surplus 2,40,000, PV refunds/reductions 1,50,000)
    asset = min(240_000, 150_000)
    key = _pick({"A": 90_000, "B": 240_000, "C": 0, "D": 150_000}, asset)
    return {"answer": key, "computed": asset}


def q_i1c06_016():
    # 8% on 6,00,000 full year + 4% on net inflow (1,20,000 − 40,000) six months
    expected = 0.08 * 600_000 + 0.04 * (120_000 - 40_000)
    key = _pick({"A": 3_200, "B": 51_200, "C": 48_000, "D": 54_400}, expected)
    return {"answer": key, "computed": expected}


def q_i1c06_017():
    # closing 9,80,000 − opening 7,20,000 − contributions 2,10,000 + benefits 1,60,000
    actual = 980_000 - 720_000 - 210_000 + 160_000
    key = _pick({"A": 50_000, "B": 310_000, "C": 210_000, "D": 260_000}, actual)
    return {"answer": key, "computed": actual}


def q_i1c06_021():
    # VRS 6,00,000 due 2 years out → discounted at factor 0.857
    recognised = 600_000 * 0.857
    key = _pick({"A": 600_000, "B": 0, "C": 300_000, "D": 514_200}, recognised)
    return {"answer": key, "computed": recognised}


# ── standalone MCQs · AS 29 ──────────────────────────────────────────────

def q_i1c06_032():
    # provision falls 42,000 → 36,000: movement is a CREDIT (negative charge)
    movement = 36_000 - 42_000
    key = _pick({"A": -6_000, "B": 36_000, "C": 6_000, "D": -42_000}, movement)
    return {"answer": key, "computed": movement}


def q_i1c06_033():
    # per case: loss chance 40% (not probable) → disclose expected loss;
    # expected = (30% × 90,000 + 10% × 1,80,000) × 6 cases
    expected = (0.30 * 90_000 + 0.10 * 180_000) * 6
    loss_probable = 0.30 + 0.10 > 0.5
    treatment = "provide" if loss_probable else "disclose"
    key = _pick({"A": ("provide", 270_000), "B": ("disclose", 270_000),
                 "C": ("disclose", 1_080_000), "D": ("nothing", 0)},
                (treatment, expected))
    return {"answer": key, "computed": (treatment, expected)}


def q_i1c06_034():
    # unavoidable legal costs provided; not-probable claim disclosed
    provision = 75_000          # incurred irrespective of outcome
    disclosed = 600_000         # possible, not probable
    key = _pick({"A": (75_000, 600_000), "B": (675_000, 0),
                 "C": (0, 675_000), "D": (600_000, 75_000)},
                (provision, disclosed))
    return {"answer": key, "computed": (provision, disclosed)}


def q_i1c06_035():
    # gross provision stays; reimbursement asset capped at virtually-certain amount
    provision = 500_000
    asset = min(320_000, provision)
    key = _pick({"A": (500_000, 0), "B": (180_000, 0),
                 "C": (500_000, 500_000), "D": (500_000, 320_000)},
                (provision, asset))
    return {"answer": key, "computed": (provision, asset)}


# ── cs-i1c06-001 · Meghna Engineering (AS 15 plan assets) ────────────────

OPENING, BENEFITS, CONTRIB, CLOSING = 400_000, 40_000, 100_000, 530_000
RATE, HALF_RATE = 0.10, 0.05


def _expected_return():
    return RATE * OPENING + HALF_RATE * (CONTRIB - BENEFITS)


def _actual_return():
    return CLOSING - OPENING - CONTRIB + BENEFITS


def cs_i1c06_001_a():
    expected = _expected_return()
    key = _pick({"A": 40_000, "B": 46_000, "C": 53_000, "D": 43_000}, expected)
    return {"answer": key, "computed": expected}


def cs_i1c06_001_b():
    actual = _actual_return()
    key = _pick({"A": 130_000, "B": 30_000, "C": 70_000, "D": 90_000}, actual)
    return {"answer": key, "computed": actual}


def cs_i1c06_001_c():
    # positive difference = actuarial GAIN, recognised immediately in P&L;
    # 27001 is the reserves-route sentinel (see module docstring)
    gain = _actual_return() - _expected_return()
    key = _pick({"A": -27_000, "B": 0, "C": 27_001, "D": 27_000}, gain)
    return {"answer": key, "computed": gain}


# ── cs-i1c06-002 · Vindhya Textiles (AS 15 gratuity DBO) ─────────────────

SALARY, GROWTH, YEARS = 1_000_000, 0.10, 4
BENEFIT_PCT = 0.25
PV_FACTORS = {1: 0.926, 2: 0.857, 3: 0.794}   # years to retirement


def _final_salary():
    return SALARY * (1 + GROWTH) ** YEARS      # 4 yearly increments


def _dbo():
    return _final_salary() * BENEFIT_PCT * YEARS


def cs_i1c06_002_a():
    dbo = _dbo()
    key = _pick({"A": 1_610_510, "B": 1_000_000, "C": 1_464_100, "D": 1_331_000},
                dbo, tolerance=1)
    return {"answer": key, "computed": dbo}


def cs_i1c06_002_b():
    annual = _dbo() / YEARS
    key = _pick({"A": 292_820, "B": 250_000, "C": 366_025, "D": 1_464_100},
                annual, tolerance=1)
    return {"answer": key, "computed": annual}


def cs_i1c06_002_c():
    # year 2 slice discounts 2 years (payment at end of year 4)
    csc = (_dbo() / YEARS) * PV_FACTORS[2]
    key = _pick({"A": 313_683, "B": 366_025, "C": 290_624, "D": 338_939},
                csc, tolerance=1)
    return {"answer": key, "computed": csc}


# ── cs-i1c06-003 · Kaveri Appliances (AS 29 warranty) ────────────────────

INV_FEB_X0, INV_DEC_X0, INV_OCT_X1 = 80_000, 50_000, 160_000
RATE_UNDER_1YR, RATE_OVER_1YR = 0.02, 0.03


def _provision_x1():
    # at 31.3.X1: Feb-X0 sale has <1yr left; Dec-X0 has >1yr left
    return INV_FEB_X0 * RATE_UNDER_1YR + INV_DEC_X0 * RATE_OVER_1YR


def _provision_x2():
    # at 31.3.X2: Feb-X0 expired; Dec-X0 <1yr; Oct-X1 >1yr
    return INV_DEC_X0 * RATE_UNDER_1YR + INV_OCT_X1 * RATE_OVER_1YR


def cs_i1c06_003_a():
    prov = _provision_x1()
    key = _pick({"A": 3_100, "B": 3_900, "C": 3_400, "D": 2_600}, prov)
    return {"answer": key, "computed": prov}


def cs_i1c06_003_b():
    prov = _provision_x2()
    key = _pick({"A": 4_700, "B": 6_300, "C": 5_800, "D": 7_400}, prov)
    return {"answer": key, "computed": prov}


def cs_i1c06_003_c():
    charge = _provision_x2() - _provision_x1()
    key = _pick({"A": 8_900, "B": 5_800, "C": 2_700, "D": 4_800}, charge)
    return {"answer": key, "computed": charge}


# ── cs-i1c06-004 · Periyar Retail (AS 29 restructuring) ──────────────────

def cs_i1c06_004_a():
    # only severance qualifies: necessarily entailed + not ongoing-activity;
    # retraining 4,00,000 / marketing 2,50,000 / software 3,00,000 excluded;
    # operating losses 5,00,000 never provided; fixtures gain 1,20,000 never netted
    severance = 1_500_000
    provision = severance
    key = _pick({"A": 1_900_000, "B": 2_450_000, "C": 1_880_000, "D": 1_500_000},
                provision)
    return {"answer": key, "computed": provision}
