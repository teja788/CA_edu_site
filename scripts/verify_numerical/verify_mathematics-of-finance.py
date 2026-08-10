"""Verifier for foundation/quantitative-aptitude/mathematics-of-finance.json (P3 Ch 4).

Every function recomputes its answer from the stem's own parameters. Money is
carried in ``decimal.Decimal`` under an explicit 28-digit context so that the
rounding is deliberate rather than an artefact of binary floating point, and the
computed value is mapped to an option key through a dict of the four option
VALUES — never through the bank's answer key. A wrong key in the bank therefore
shows up as a mismatch, and a wrong option value shows up as an assertion.

Conventions applied throughout (they match the chapter's notes, and a reviewer
should confirm them against the study material):

  * Factors are carried unrounded; money is rounded only at the final step,
    to the nearest paisa, half-up. Interest is NOT rounded period by period.
  * A year is 365 days for simple interest; months are exact twelfths.
  * An annuity is an ORDINARY annuity (payment at the end of the period)
    unless the stem says the payments fall at the beginning.
  * Amortisation schedules are built from the unrounded instalment, row by row,
    and the closing balance is allowed to fall out rather than being asserted.
  * Rates quoted as percentages are compared to four decimal places of a
    percentage point (e.g. 12.5509%).
"""

from __future__ import annotations

from decimal import Context, Decimal, ROUND_HALF_UP

# One explicit context for the whole module: 28 significant digits, half-up.
CTX = Context(prec=28, rounding=ROUND_HALF_UP)

ONE = Decimal(1)
PAISA = Decimal("0.01")


def D(x) -> Decimal:
    """Decimal from an int/str/Decimal. Floats are never accepted silently."""
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


# ------------------------------------------------------------ shared factors


def compound_factor(i, n) -> Decimal:
    """(1 + i)^n. n may be fractional (a part conversion period)."""
    i, n = D(i), D(n)
    return CTX.power(ONE + i, n)


def discount_factor(i, n) -> Decimal:
    """(1 + i)^(-n) — the reciprocal of the compound factor."""
    return CTX.divide(ONE, compound_factor(i, n))


def fv_annuity_factor(i, n) -> Decimal:
    """A(n, i) = [(1 + i)^n - 1] / i — always greater than n."""
    i = D(i)
    return CTX.divide(compound_factor(i, n) - ONE, i)


def pv_annuity_factor(i, n) -> Decimal:
    """P(n, i) = [1 - (1 + i)^(-n)] / i — always less than n."""
    i = D(i)
    return CTX.divide(ONE - discount_factor(i, n), i)


def money(x) -> Decimal:
    """Round to the nearest paisa, half-up — the LAST step of a computation."""
    return D(x).quantize(PAISA, rounding=ROUND_HALF_UP)


def pick(computed, options, tol="0.01") -> str:
    """Map a computed value to exactly one option key.

    `options` is {option key: option value as printed in the bank}. Exactly one
    option must sit within `tol` of the computed value, otherwise the verifier
    raises — which the runner reports as a failure.
    """
    computed, tol = D(computed), D(tol)
    hits = [k for k, v in options.items() if abs(D(v) - computed) <= tol]
    if len(hits) != 1:
        raise AssertionError(f"computed {computed} matched {hits} in {options}")
    return hits[0]


def result(computed, options, tol="0.01"):
    return {"answer": pick(computed, options, tol), "computed": str(computed)}


# ------------------------------------------------------------ §2 simple interest


def q_f3c4_004():
    # I = P i t. Simple interest: the base never changes. Exact, no rounding.
    p, i, t = D(75000), D("0.085"), D(4)
    interest = money(p * i * t)
    return result(
        interest,
        {"A": "28939.40", "B": "100500", "C": "25500", "D": "6375"},
    )


def q_f3c4_005():
    # P = I / (i t), with 3 years 6 months carried as the exact fraction 3.5.
    interest, i, t = D(18900), D("0.09"), D(3) + CTX.divide(D(6), D(12))
    principal = money(CTX.divide(interest, i * t))
    return result(
        principal,
        {"A": "60000", "B": "70000", "C": "78900", "D": "600"},
    )


def q_f3c4_006():
    # 365-day year, as the stem states. On a 360-day year the answer is 7,300.
    p, i, days = D(240000), D("0.075"), D(146)
    interest = money(p * i * CTX.divide(days, D(365)))
    assert money(p * i * CTX.divide(days, D(360))) == D("7300.00")
    return result(
        interest,
        {"A": "7300", "B": "7200", "C": "18000", "D": "247200"},
    )


def q_f3c4_007():
    # Doubling under simple interest: I = P, so i t = 1 and i = 1 / t.
    t = D("12.5")
    rate_pct = CTX.divide(D(100), t)  # per cent per annum
    return result(
        rate_pct,
        {"A": "16", "B": "5.76", "C": "8", "D": "12.5"},
        tol="0.005",
    )


def q_f3c4_008():
    # Two slices, each on the ORIGINAL principal, then added.
    p = D(90000)
    interest = money(p * D("0.06") * D(2) + p * D("0.09") * D(3))
    return result(
        interest,
        {"A": "40958.51", "B": "33750", "C": "67500", "D": "35100"},
    )


def q_f3c4_009():
    # 8 months = 8/12 of a year exactly.
    p, i = D(150000), D("0.11")
    interest = money(p * i * CTX.divide(D(8), D(12)))
    return result(
        interest,
        {"A": "11000", "B": "16500", "C": "132000", "D": "161000"},
    )


def q_f3c4_010():
    # t = I / (P i), where I is the AMOUNT less the principal.
    p, amount, i = D(50000), D(68000), D("0.09")
    years = CTX.divide(amount - p, p * i)
    return result(
        years,
        {"A": "15.11", "B": "4", "C": "3.57", "D": "2"},
        tol="0.02",
    )


# ---------------------------------------------------------- §3 compound interest


def q_f3c4_011():
    # CI = P[(1+i)^n - 1], yearly conversion. Rounded to paise at the end only.
    p, i, n = D(180000), D("0.07"), 3
    ci = money(p * (compound_factor(i, n) - ONE))
    # the D distractor really is the half-yearly figure
    assert money(p * (compound_factor(D("0.035"), 6) - ONE)) == D("41265.96")
    return result(
        ci,
        {"A": "220507.74", "B": "37800", "C": "40507.74", "D": "41265.96"},
    )


def q_f3c4_012():
    # Difference over TWO years, computed the long way and cross-checked by P i².
    p, i, n = D(250000), D("0.08"), 2
    ci = p * (compound_factor(i, n) - ONE)
    si = p * i * D(n)
    difference = money(ci - si)
    assert difference == money(p * i * i)
    return result(
        difference,
        {"A": "20000", "B": "41600", "C": "40000", "D": "1600"},
    )


def q_f3c4_013():
    # Difference over THREE years, cross-checked by the P i²(3 + i) shortcut.
    p, i, n = D(100000), D("0.10"), 3
    ci = p * (compound_factor(i, n) - ONE)
    si = p * i * D(n)
    difference = money(ci - si)
    assert difference == money(p * i * i * (D(3) + i))
    return result(
        difference,
        {"A": "3100", "B": "1000", "C": "33100", "D": "30000"},
    )


def q_f3c4_014():
    # Work back: P = (CI - SI over two years) / i², then prove it forwards.
    difference, i = D(4320), D("0.12")
    principal = money(CTX.divide(difference, i * i))
    ci = principal * (compound_factor(i, 2) - ONE)
    si = principal * i * D(2)
    assert money(ci - si) == difference
    return result(
        principal,
        {"A": "36000", "B": "300000", "C": "30000", "D": "96153.85"},
    )


def q_f3c4_015():
    # Constant-rate decay: value = P(1 - d)^n. The base shrinks every year.
    p, d, n = D(960000), D("0.12"), 4
    value = money(p * compound_factor(-d, n))
    assert money(p - value) == D("384292.45")  # the B distractor is the fall
    return result(
        value,
        {"A": "499200", "B": "384292.45", "C": "575707.55", "D": "1510578.59"},
    )


def q_f3c4_016():
    # Rates changing mid-term: the compound factors multiply.
    p = D(400000)
    amount = money(p * compound_factor(D("0.06"), 2) * compound_factor(D("0.09"), 3))
    return result(
        amount,
        {"A": "556000", "B": "574251.73", "C": "182037.83", "D": "582037.83"},
    )


def q_f3c4_017():
    # P = A / (1 + i)^n, then proved forwards.
    amount, i, n = D(133100), D("0.10"), 3
    principal = money(CTX.divide(amount, compound_factor(i, n)))
    assert money(principal * compound_factor(i, n)) == amount
    return result(
        principal,
        {"A": "100000", "B": "102384.62", "C": "93170", "D": "177156.10"},
    )


# ------------------------------------------------------------ §4 conversion periods


def q_f3c4_018():
    # Quarterly conversion: BOTH the rate and the count are converted.
    p, annual, m, years = D(160000), D("0.10"), 4, 3
    i = CTX.divide(annual, D(m))
    amount = money(p * compound_factor(i, m * years))
    return result(
        amount,
        {"A": "212960", "B": "215182.21", "C": "502148.54", "D": "172302.50"},
    )


def q_f3c4_019():
    # Monthly conversion: i = r/12, n = years x 12.
    p, annual, m, years = D(300000), D("0.09"), 12, 2
    i = CTX.divide(annual, D(m))
    amount = money(p * compound_factor(i, m * years))
    return result(
        amount,
        {"A": "356430", "B": "2373324.95", "C": "358924.06", "D": "304516.88"},
    )


def q_f3c4_020():
    # Build all four amounts, then choose the largest — the key is not assumed.
    p, r, years = D(100000), D("0.12"), 1
    amounts = {}
    for key, m in (("A", 1), ("B", 2), ("C", 4), ("D", 12)):
        i = CTX.divide(r, D(m))
        amounts[key] = money(p * compound_factor(i, m * years))
    largest = max(amounts, key=lambda k: amounts[k])
    # the amounts must rise strictly with the conversion frequency
    assert amounts["A"] < amounts["B"] < amounts["C"] < amounts["D"]
    return {"answer": largest, "computed": str(amounts[largest])}


def q_f3c4_021():
    # 4 years 6 months at half-yearly conversion is exactly 9 periods.
    p, annual, m = D(200000), D("0.08"), 2
    i = CTX.divide(annual, D(m))
    n = D("4.5") * D(m)
    amount = money(p * compound_factor(i, n))
    assert n == D(9)
    return result(
        amount,
        {"A": "284662.36", "B": "238605.27", "C": "399800.93", "D": "282772.32"},
    )


# --------------------------------------------------- §5 solving for rate and time


def q_f3c4_022():
    # i = (A/P)^(1/n) - 1, expressed as a percentage per annum.
    p, amount, n = D(150000), D(250000), D(6)
    growth = CTX.divide(amount, p)
    rate_pct = (CTX.power(growth, CTX.divide(ONE, n)) - ONE) * D(100)
    return result(
        rate_pct,
        {"A": "11.11", "B": "66.67", "C": "108.89", "D": "8.89"},
        tol="0.005",
    )


def q_f3c4_023():
    # n = ln(A/P) / ln(1 + i). The principal cancels: only the ratio matters.
    ratio, i = D(2), D("0.07")
    n = CTX.divide(ratio.ln(), (ONE + i).ln())
    # the same figure from the stem's four-decimal common logs
    assert abs(n - CTX.divide(D("0.3010"), D("0.0294"))) < D("0.01")
    return result(
        n,
        {"A": "14.29", "B": "10.24", "C": "10.29", "D": "20.48"},
        tol="0.02",
    )


def q_f3c4_024():
    ratio = CTX.divide(D(900000), D(500000))
    i = D("0.08")
    n = CTX.divide(ratio.ln(), (ONE + i).ln())
    assert ratio == D("1.8")
    return result(
        n,
        {"A": "10", "B": "22.5", "C": "7.64", "D": "9"},
        tol="0.02",
    )


def q_f3c4_025():
    # (1+i)^15 = 3, so the rate itself is recovered, then the time to reach 9x.
    n_triple, multiple_now, multiple_wanted = D(15), D(3), D(9)
    i = CTX.power(multiple_now, CTX.divide(ONE, n_triple)) - ONE
    n = CTX.divide(multiple_wanted.ln(), (ONE + i).ln())
    assert abs(compound_factor(i, n_triple) - multiple_now) < D("0.0000001")
    return result(
        n,
        {"A": "135", "B": "22.5", "C": "45", "D": "30"},
        tol="0.01",
    )


# ------------------------------------------- §6 effective and continuous rates


def q_f3c4_026():
    # E = (1 + r/m)^m - 1, as a percentage to four decimals.
    r, m = D("0.12"), 4
    e_pct = (compound_factor(CTX.divide(r, D(m)), m) - ONE) * D(100)
    return result(
        e_pct,
        {"A": "12.5509", "B": "12", "C": "12.36", "D": "3"},
        tol="0.0001",
    )


def q_f3c4_027():
    # Both offers are converted to effective annual rates before comparison.
    e_p = (compound_factor(CTX.divide(D("0.10"), D(2)), 2) - ONE) * D(100)
    e_q = (compound_factor(CTX.divide(D("0.099"), D(12)), 12) - ONE) * D(100)
    assert e_q > e_p, "Bank Q must win on effective rates despite the lower nominal"
    # option C carries no figure, so only the three numbered options are mapped
    return result(
        e_q,
        {"A": "10.25", "B": "10.3618", "D": "10.1450"},
        tol="0.0001",
    )


def q_f3c4_028():
    # r = m[(1 + E)^(1/m) - 1], then proved forwards through the effective rate.
    e, m = D("0.0816"), 2
    r = D(m) * (CTX.power(ONE + e, CTX.divide(ONE, D(m))) - ONE)
    assert abs((compound_factor(CTX.divide(r, D(m)), m) - ONE) - e) < D("0.0000001")
    return result(
        r * D(100),
        {"A": "8.16", "B": "4.08", "C": "8", "D": "7.92"},
        tol="0.005",
    )


def q_f3c4_029():
    # Continuous compounding: A = P e^(r t). The exponent carries the time.
    p, r, t = D(250000), D("0.06"), D(4)
    amount = money(p * CTX.exp(r * t))
    assert amount > money(p * compound_factor(r, 4))  # beats yearly conversion
    return result(
        amount,
        {"A": "315619.24", "B": "317812.29", "C": "310000", "D": "265459.14"},
    )


def q_f3c4_030():
    # Effective rate under continuous compounding = e^r - 1, the ceiling that
    # no finite conversion frequency reaches.
    r = D("0.10")
    e_pct = (CTX.exp(r) - ONE) * D(100)
    monthly_pct = (compound_factor(CTX.divide(r, D(12)), 12) - ONE) * D(100)
    assert e_pct > monthly_pct
    return result(
        e_pct,
        {"A": "10", "B": "10.4713", "C": "27.1828", "D": "10.5171"},
        tol="0.0001",
    )


# ------------------------------------------- §7 present and future value


def q_f3c4_031():
    fv, i, n = D(600000), D("0.11"), 5
    pv = money(fv * discount_factor(i, n))
    # discounting undoes compounding, to within the paisa rounding of the PV
    assert abs(pv * compound_factor(i, n) - fv) < D("0.05")
    return result(
        pv,
        {"A": "356070.80", "B": "1011034.89", "C": "387096.77", "D": "330000"},
    )


def q_f3c4_032():
    # Unequal flows: each carries the factor for its own year.
    flows = [(1, D(200000)), (2, D(250000)), (3, D(180000))]
    i = D("0.09")
    pv = money(sum((cash * discount_factor(i, year) for year, cash in flows), Decimal(0)))
    return result(
        pv,
        {"A": "630000", "B": "532899.26", "C": "531571.88", "D": "486475.59"},
    )


def q_f3c4_033():
    fv, annual, m, years = D(1000000), D("0.09"), 4, 8
    i = CTX.divide(annual, D(m))
    pv = money(fv * discount_factor(i, m * years))
    return result(
        pv,
        {"A": "501866.28", "B": "836938.35", "C": "490652.33", "D": "581395.35"},
    )


# ------------------------------------------------------------- §9 annuities


def q_f3c4_034():
    # Ordinary annuity: the last deposit earns nothing, so A(n, i) > n.
    r, i, n = D(30000), D("0.10"), 6
    factor = fv_annuity_factor(i, n)
    assert factor > D(n)
    fv = money(r * factor)
    return result(
        fv,
        {"A": "180000", "B": "254615.13", "C": "130657.82", "D": "231468.30"},
    )


def q_f3c4_035():
    r, annual, m, years = D(12000), D("0.08"), 4, 5
    i = CTX.divide(annual, D(m))
    fv = money(r * fv_annuity_factor(i, m * years))
    return result(
        fv,
        {"A": "291568.44", "B": "240000", "C": "196217.20", "D": "70399.21"},
    )


def q_f3c4_036():
    # Sinking-fund rearrangement: R = S i / [(1+i)^n - 1], proved forwards.
    target, i, n = D(2000000), D("0.07"), 10
    deposit = money(CTX.divide(target, fv_annuity_factor(i, n)))
    # forwards check, allowing for the paisa rounding of the deposit magnified
    # by the ten-period annuity factor
    assert abs(deposit * fv_annuity_factor(i, n) - target) < D("0.10")
    return result(
        deposit,
        {"A": "200000", "B": "144755.01", "C": "284755.01", "D": "135285.05"},
    )


def q_f3c4_037():
    # Ordinary annuity present value: the factor must be BELOW the payment count.
    r, i, n = D(75000), D("0.12"), 8
    factor = pv_annuity_factor(i, n)
    assert factor < D(n)
    pv = money(r * factor)
    return result(
        pv,
        {"A": "600000", "B": "922476.99", "C": "372572.98", "D": "417281.74"},
    )


def q_f3c4_038():
    # Drawing a fund down to nothing: R = PV / P(n, i).
    fund, i, n = D(1200000), D("0.10"), 5
    withdrawal = money(CTX.divide(fund, pv_annuity_factor(i, n)))
    # walk the fund down year by year and let the closing balance fall out
    balance = fund
    for _ in range(n):
        balance = balance * (ONE + i) - withdrawal
    assert abs(balance) < D("0.05")
    return result(
        withdrawal,
        {"A": "240000", "B": "196556.98", "C": "287779.07", "D": "316556.98"},
    )


# ------------------------------------------------------- §11 annuity due


def q_f3c4_039():
    # Annuity due = ordinary annuity value x (1 + i): one extra period each.
    r, i, n = D(20000), D("0.09"), 7
    ordinary = r * fv_annuity_factor(i, n)
    due = money(ordinary * (ONE + i))
    assert money(ordinary) == D("184008.69")  # the A distractor
    return result(
        due,
        {"A": "184008.69", "B": "140000", "C": "200569.48", "D": "100659.06"},
    )


def q_f3c4_040():
    # Rent payable in advance is an annuity due on the PRESENT value side.
    r, i, n = D(180000), D("0.10"), 6
    ordinary = r * pv_annuity_factor(i, n)
    due = money(ordinary * (ONE + i))
    # the same figure built the other way: today's payment plus P(n-1, i)
    assert money(r + r * pv_annuity_factor(i, n - 1)) == due
    return result(
        due,
        {"A": "862341.62", "B": "783946.93", "C": "1080000", "D": "1388809.80"},
    )


# ------------------------------------------------------------ §12 perpetuity


def q_f3c4_041():
    # PV = R / i. Cross-check: the limit of the annuity factor is 1 / i.
    r, i = D(60000), D("0.08")
    pv = money(CTX.divide(r, i))
    assert pv > money(r * pv_annuity_factor(i, 20))  # more than 20 years' worth
    return result(
        pv,
        {"A": "7500", "B": "750000", "C": "4800", "D": "589088.84"},
    )


def q_f3c4_042():
    # Growing perpetuity: PV = R / (i - g), and g must stay below i.
    r, i, g = D(90000), D("0.11"), D("0.05")
    assert g < i
    pv = money(CTX.divide(r, i - g))
    return result(
        pv,
        {"A": "818181.82", "B": "1800000", "C": "1575000", "D": "1500000"},
    )


# --------------------------------------------- §13/§14 sinking funds and loans


def q_f3c4_043():
    target, i, n = D(2500000), D("0.10"), 5
    deposit = money(CTX.divide(target, fv_annuity_factor(i, n)))
    # accumulate the fund deposit by deposit and let the closing figure fall out
    fund = Decimal(0)
    for _ in range(n):
        fund = fund * (ONE + i) + deposit
    assert abs(fund - target) < D("0.10")
    return result(
        deposit,
        {"A": "409493.70", "B": "500000", "C": "659493.70", "D": "372267"},
    )


def q_f3c4_044():
    # Monthly instalment: i = 0.12/12 = 0.01 per month, n = 36 months.
    loan, annual, m, years = D(600000), D("0.12"), 12, 3
    i = CTX.divide(annual, D(m))
    n = m * years
    instalment = money(CTX.divide(loan, pv_annuity_factor(i, n)))
    # amortise row by row from the unrounded instalment; the balance falls out
    exact = CTX.divide(loan, pv_annuity_factor(i, n))
    balance = loan
    for _ in range(n):
        balance = balance + balance * i - exact
    assert abs(balance) < D("0.01")
    return result(
        instalment,
        {"A": "16666.67", "B": "19928.59", "C": "22666.67", "D": "19731.27"},
    )


def q_f3c4_045():
    # Balance after k instalments = R x P(n - k, i), cross-checked by walking
    # the schedule row by row on the unrounded instalment.
    loan, i, n, k = D(1000000), D("0.11"), 6, 4
    instalment = CTX.divide(loan, pv_annuity_factor(i, n))
    balance = loan
    for _ in range(k):
        interest = balance * i
        balance = balance + interest - instalment
    by_formula = instalment * pv_annuity_factor(i, n - k)
    assert abs(balance - by_formula) < D("0.01")
    return result(
        money(balance),
        {"A": "333333.33", "B": "472753.13", "C": "404800.38", "D": "449328.42"},
    )


# ------------------------------------------------- §15/§16 NPV and the index


def q_f3c4_046():
    # The outlay is spent today and is never discounted.
    outlay, inflow, i, n = D(1500000), D(500000), D("0.10"), 4
    npv = money(inflow * pv_annuity_factor(i, n) - outlay)
    assert npv > 0  # a positive NPV means the project clears the 10% hurdle
    return result(
        npv,
        {"A": "500000", "B": "1584932.72", "C": "221296.36", "D": "84932.72"},
    )


def q_f3c4_047():
    # The same project at a higher required return. The decision follows the
    # SIGN of the NPV, so both are computed here.
    outlay, inflow, i, n = D(1500000), D(500000), D("0.14"), 4
    npv = money(inflow * pv_annuity_factor(i, n) - outlay)
    decision = "accept" if npv > 0 else "reject"
    assert decision == "reject"
    # options A and D share the figure; only A pairs it with the right decision
    return {"answer": "A" if npv < 0 else "B", "computed": f"{npv} -> {decision}"}


def q_f3c4_048():
    outlay, inflow, i, n = D(800000), D(250000), D("0.12"), 5
    pi = CTX.divide(inflow * pv_annuity_factor(i, n), outlay)
    assert pi > ONE  # acceptable, matching the positive NPV
    return result(
        pi,
        {"A": "1.5625", "B": "1.1265", "C": "0.8877", "D": "0.1265"},
        tol="0.0001",
    )


def q_f3c4_049():
    # CAGR counts the INTERVALS between the two years: 2019-20 to 2025-26 = 6.
    begin, end, years = D(4000000), D(9000000), D(6)
    cagr_pct = (CTX.power(CTX.divide(end, begin), CTX.divide(ONE, years)) - ONE) * D(100)
    assert abs(begin * compound_factor(cagr_pct / D(100), years) - end) < D("0.01")
    return result(
        cagr_pct,
        {"A": "20.83", "B": "125", "C": "14.47", "D": "17.61"},
        tol="0.005",
    )


def q_f3c4_050():
    # Coupon rate fixes the rupee coupon; the yield does the discounting.
    face, coupon_rate, yield_, n = D(1000), D("0.10"), D("0.08"), 4
    coupon = face * coupon_rate
    value = money(coupon * pv_annuity_factor(yield_, n) + face * discount_factor(yield_, n))
    assert value > face  # a coupon above the yield means a premium
    return result(
        value,
        {"A": "1000", "B": "1400", "C": "936.60", "D": "1066.24"},
    )


# =================================================== case 1: the housing loan
# ₹ 36,00,000 at 9% p.a. compounded monthly, 240 monthly instalments, the first
# one month after disbursement. The schedule below is built row by row from the
# UNROUNDED instalment; the closing balance is allowed to fall out.

HOME_LOAN = D(3600000)
HOME_I = CTX.divide(D("0.09"), D(12))
HOME_N = 240
HOME_EMI_EXACT = CTX.divide(HOME_LOAN, pv_annuity_factor(HOME_I, HOME_N))


def _home_schedule():
    """Yield (month, opening, interest, principal, closing) for all 240 rows."""
    balance = HOME_LOAN
    for month in range(1, HOME_N + 1):
        interest = balance * HOME_I
        principal = HOME_EMI_EXACT - interest
        opening, balance = balance, balance - principal
        yield month, opening, interest, principal, balance


def cs_f3c4_01_a():
    return result(
        money(HOME_EMI_EXACT),
        {"A": "32390.13", "B": "42000", "C": "15000", "D": "27000"},
    )


def cs_f3c4_01_b():
    # Interest is the OPENING balance times the periodic rate — row 1 only.
    _, opening, interest, principal, _ = next(iter(_home_schedule()))
    assert opening == HOME_LOAN
    assert money(interest + principal) == money(HOME_EMI_EXACT)
    return result(
        money(interest),
        {"A": "32390.13", "B": "5390.13", "C": "27000", "D": "3324000"},
        tol="0.01",
    )


def cs_f3c4_01_c():
    # Balance after 60 rows of the schedule, cross-checked against R x P(180, i).
    balance = None
    for month, _, _, _, closing in _home_schedule():
        if month == 60:
            balance = closing
            break
    by_formula = HOME_EMI_EXACT * pv_annuity_factor(HOME_I, HOME_N - 60)
    assert abs(balance - by_formula) < D("0.01")
    return result(
        money(balance),
        {"A": "2700000", "B": "5830224.19", "C": "1656591.94", "D": "3193453.76"},
    )


def cs_f3c4_01_d():
    # Total interest = the sum of the interest column; the final balance must
    # come out at zero, which is the proof that the instalment was right.
    total_interest = Decimal(0)
    closing = None
    for _, _, interest, _, closing in _home_schedule():
        total_interest += interest
    assert abs(closing) < D("0.01")
    assert abs(total_interest - (D(HOME_N) * HOME_EMI_EXACT - HOME_LOAN)) < D("0.01")
    return result(
        money(total_interest),
        {"A": "6480000", "B": "4173632.26", "C": "7773632.26", "D": "3600000"},
    )


# ============================================ case 2: two mutually exclusive machines

MACHINE_RATE = D("0.13")
MACHINE_A = (D(2000000), [D(600000)] * 5)
MACHINE_B = (D(2400000), [D(500000), D(700000), D(800000), D(900000), D(600000)])


def _npv(outlay, inflows, i=MACHINE_RATE):
    pv = sum(
        (cash * discount_factor(i, year) for year, cash in enumerate(inflows, start=1)),
        Decimal(0),
    )
    return pv, pv - outlay


def cs_f3c4_02_a():
    outlay, inflows = MACHINE_A
    pv, npv = _npv(outlay, inflows)
    # equal inflows, so the annuity factor must give the same present value
    assert abs(pv - inflows[0] * pv_annuity_factor(MACHINE_RATE, len(inflows))) < D("0.01")
    return result(
        money(npv),
        {"A": "1000000", "B": "2110338.76", "C": "110338.76", "D": "384682.80"},
    )


def cs_f3c4_02_b():
    outlay, inflows = MACHINE_B
    _, npv = _npv(outlay, inflows)
    return result(
        money(npv),
        {"A": "22763.50", "B": "1100000", "C": "2422763.50", "D": "62061.88"},
    )


def cs_f3c4_02_c():
    # Mutually exclusive, so the higher NPV decides. Both measures are computed
    # and both must point the same way before the option is selected.
    pv_a, npv_a = _npv(*MACHINE_A)
    pv_b, npv_b = _npv(*MACHINE_B)
    pi_a = CTX.divide(pv_a, MACHINE_A[0])
    pi_b = CTX.divide(pv_b, MACHINE_B[0])
    assert npv_a > npv_b and pi_a > pi_b, "A must win on both measures"
    winner = "A" if npv_a > npv_b else "B"
    # option B of the bank is the one naming Machine A with both figures
    answer = {"A": "B", "B": "A"}[winner]
    return {
        "answer": answer,
        "computed": f"NPV A {money(npv_a)} / B {money(npv_b)}; PI A {round(pi_a, 4)} / B {round(pi_b, 4)}",
    }


# ================================= case 3: building a fund and drawing it down

MEERA_DEPOSIT = D(120000)
MEERA_BUILD_RATE = D("0.09")
MEERA_BUILD_YEARS = 20
MEERA_DRAW_RATE = D("0.07")
MEERA_DRAW_YEARS = 15


def _meera_fund():
    """Accumulate the fund deposit by deposit, end-of-year deposits."""
    fund = Decimal(0)
    for _ in range(MEERA_BUILD_YEARS):
        fund = fund * (ONE + MEERA_BUILD_RATE) + MEERA_DEPOSIT
    return fund


def cs_f3c4_03_a():
    fund = _meera_fund()
    by_formula = MEERA_DEPOSIT * fv_annuity_factor(MEERA_BUILD_RATE, MEERA_BUILD_YEARS)
    assert abs(fund - by_formula) < D("0.01")
    return result(
        money(fund),
        {"A": "2400000", "B": "6691743.65", "C": "1095425.48", "D": "6139214.36"},
    )


def cs_f3c4_03_b():
    fund = _meera_fund()
    withdrawal = CTX.divide(fund, pv_annuity_factor(MEERA_DRAW_RATE, MEERA_DRAW_YEARS))
    # draw the fund down year by year; the closing balance must fall to zero
    balance = fund
    for _ in range(MEERA_DRAW_YEARS):
        balance = balance * (ONE + MEERA_DRAW_RATE) - withdrawal
    assert abs(balance) < D("0.01")
    return result(
        money(withdrawal),
        {"A": "409280.96", "B": "244307.73", "C": "674052.74", "D": "629955.83"},
    )


def cs_f3c4_03_c():
    # Deposits at the BEGINNING of each year: every deposit earns one more year.
    fund = Decimal(0)
    for _ in range(MEERA_BUILD_YEARS):
        fund = (fund + MEERA_DEPOSIT) * (ONE + MEERA_BUILD_RATE)
    assert abs(fund - _meera_fund() * (ONE + MEERA_BUILD_RATE)) < D("0.01")
    return result(
        money(fund),
        {"A": "6691743.65", "B": "6139214.36", "C": "5632306.75", "D": "2616000"},
    )
