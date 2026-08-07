"""Verifier for foundation/accounting/partnership-and-llp-accounts.json (P1 Ch 10).

Every function recomputes its answer from the stem's own parameters — the
appropriation cascade, the product/average-period machinery for interest on
drawings, guarantee deficiencies, past-adjustment statements, all four goodwill
methods, sacrificing/gaining ratio arithmetic (done in exact `Fraction`s), and
the executor's build-up on death — and only then maps the computed value on to
an option key through a dict holding all four option values.  Nothing is copied
from the answer key, so a wrong key in the bank shows up as a mismatch.

Conventions used below:
  * CHARGE vs APPROPRIATION.  Interest on a partner's advance (Indian
    Partnership Act 1932, s.13(d), 6% p.a. when the deed is silent) and rent
    payable to a partner are CHARGES: they are deducted before the profit
    reaching the Appropriation Account.  Interest on capital, a partner's
    salary/commission and transfers to reserve are APPROPRIATIONS.
  * Divisible profit = net profit (after charges) + interest on drawings
    − interest on capital − partners' salary/commission − transfer to reserve.
  * Where the profit is insufficient for the appropriations claimed, the
    available profit is split in the RATIO OF THE AMOUNTS CLAIMED.
  * Interest on drawings uses the product method as the primitive; the
    average-period shortcuts are derived from it, never assumed:
        average period = (months left after first drawing + months left after
                          last drawing) / 2
    so equal monthly drawings give 6.5 (beginning) / 6.0 (middle) / 5.5 (end)
    and equal quarterly drawings give 7.5 / 6.0 / 4.5.
  * Goodwill: average profit is ADJUSTED first (abnormal/non-trading gains
    deducted, abnormal losses added back, future recurring costs deducted);
    normal profit = capital employed × normal rate; super profit = adjusted
    average − normal.  Capitalisation of average profit and capitalisation of
    super profit are computed independently and asserted equal.
  * Ratios (sacrificing, gaining, new) are handled as exact Fractions and
    reduced to smallest integers before being matched against an option.
  * On admission, revaluation results and reserves go to the OLD partners in
    the OLD ratio; the premium for goodwill goes in the SACRIFICING ratio.  On
    retirement and death, the outgoing partner's goodwill is borne by the
    gainers in the GAINING ratio.
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd
from functools import reduce


# --------------------------------------------------------- helpers (formulas)


def interest_on_advance(amount: float, months: float = 12, rate: float = 6.0) -> float:
    """s.13(d): 6% p.a. on a partner's advance beyond his agreed capital."""
    return amount * rate / 100 * months / 12


def divisible_profit(
    *,
    net_profit_after_charges: float,
    interest_on_drawings: float = 0,
    interest_on_capital: float = 0,
    partners_salary: float = 0,
    transfer_to_reserve: float = 0,
) -> float:
    return (
        net_profit_after_charges
        + interest_on_drawings
        - interest_on_capital
        - partners_salary
        - transfer_to_reserve
    )


def drawings_interest_by_products(drawings: list[tuple[float, float]], rate: float) -> float:
    """drawings = [(amount, months the money stayed out of the firm), ...]."""
    products = sum(amount * months for amount, months in drawings)
    return products * rate / 100 / 12


def average_period(first_months_left: float, last_months_left: float) -> float:
    return (first_months_left + last_months_left) / 2


def equal_instalment_drawings(
    *, amount_each: float, instalments: int, timing: str
) -> list[tuple[float, float]]:
    """Build the (amount, months-out) list for equal, evenly spaced drawings.

    timing is 'beginning', 'middle' or 'end' of each period.  Used so the
    6.5/5.5/7.5/4.5 shortcuts are DERIVED here rather than assumed.
    """
    period_len = 12 / instalments
    offset = {"beginning": 0.0, "middle": period_len / 2, "end": period_len}[timing]
    out = []
    for i in range(instalments):
        elapsed = i * period_len + offset  # months gone when the money leaves
        out.append((amount_each, 12 - elapsed))
    return out


def normal_profit(capital_employed: float, normal_rate_pct: float) -> float:
    return capital_employed * normal_rate_pct / 100


def super_profit(adjusted_average: float, capital_employed: float, normal_rate_pct: float) -> float:
    return adjusted_average - normal_profit(capital_employed, normal_rate_pct)


def simplify(fractions: list[Fraction]) -> tuple[int, ...]:
    """Reduce a list of Fractions to the smallest whole-number ratio."""
    denominators = [f.denominator for f in fractions]
    lcm = reduce(lambda a, b: a * b // gcd(a, b), denominators)
    ints = [int(f * lcm) for f in fractions]
    g = reduce(gcd, ints)
    return tuple(i // g for i in ints)


# ------------------------------------------- §2 rules in the absence of a deed


def q_f1c10_004():
    profit_before_loan_interest = 498_000
    loan = 300_000
    # s.13(d): 6% on the advance, and it is a CHARGE, not an appropriation.
    interest = interest_on_advance(loan)
    divisible = profit_before_loan_interest - interest
    # s.13(b): equal shares when the deed is silent, whatever the capitals.
    sunil_share = divisible / 2
    sunil_total = sunil_share + interest

    capitals = (800_000, 400_000)
    capital_ratio_share = divisible * capitals[1] / sum(capitals) + interest
    key = {
        249_000: "A",  # no interest on the advance at all
        258_000: "B",
        178_000: "C",  # profits split in the capital ratio 2:1
        240_000: "D",  # interest charged to the firm but never credited to Sunil
    }[round(sunil_total)]
    assert round(capital_ratio_share) == 178_000  # the distractor is reachable
    return {"answer": key, "computed": sunil_total}


# ---------------------------------------------- §3 charge vs appropriation


def q_f1c10_007():
    profit_before = 750_000
    rent_to_partner = 15_000 * 12          # CHARGE
    loan_interest = interest_on_advance(400_000)  # CHARGE, s.13(d)
    partner_salary = 10_000 * 12           # APPROPRIATION
    net_profit_after_charges = profit_before - rent_to_partner - loan_interest
    result = divisible_profit(
        net_profit_after_charges=net_profit_after_charges,
        partners_salary=partner_salary,
    )
    key = {
        450_000: "A",  # loan interest omitted because "the deed is silent"
        426_000: "B",
        606_000: "C",  # rent to a partner not treated as an expense
        546_000: "D",  # stops at net profit; the salary appropriation forgotten
    }[round(result)]
    return {"answer": key, "computed": result}


# ------------------------------------------------ §4 appropriation account


def q_f1c10_009():
    result = divisible_profit(
        net_profit_after_charges=800_000,
        interest_on_drawings=6_000 + 4_000,
        interest_on_capital=60_000 + 40_000,
        partners_salary=150_000,
        transfer_to_reserve=80_000,
    )
    key = {
        460_000: "A",  # interest on drawings deducted instead of added
        480_000: "B",
        560_000: "C",  # transfer to reserve omitted
        630_000: "D",  # partner's salary omitted
    }[round(result)]
    return {"answer": key, "computed": result}


def q_f1c10_010():
    capitals = {"A": 600_000, "B": 400_000}
    rate = 10
    claims = {p: c * rate / 100 for p, c in capitals.items()}
    available = 75_000
    total_claimed = sum(claims.values())
    assert total_claimed > available  # this is what forces the pro-rating
    allowed_a = available * claims["A"] / total_claimed
    key = {
        45_000: "A",
        60_000: "B",  # full entitlement allowed although profit is short
        37_500: "C",  # available profit split equally
        30_000: "D",  # the 6:4 ratio applied the wrong way round (B's figure)
    }[round(allowed_a)]
    return {"answer": key, "computed": allowed_a}


# ----------------------------------------------------- §5 interest on capital


def q_f1c10_011():
    rate = 9
    opening = 500_000
    introduced, introduced_months = 240_000, 8   # 1 Aug -> 31 Mar
    withdrawn, withdrawn_months = 120_000, 3     # 1 Jan -> 31 Mar
    interest = (
        opening * rate / 100
        + introduced * rate / 100 * introduced_months / 12
        - withdrawn * rate / 100 * withdrawn_months / 12
    )
    closing = opening + introduced - withdrawn
    key = {
        45_000: "A",  # opening capital only
        round(closing * rate / 100): "B",  # 9% of the closing capital
        56_700: "C",
        59_400: "D",  # permanent withdrawal ignored
    }[round(interest)]
    return {"answer": key, "computed": interest}


def q_f1c10_012():
    closing = 722_000
    additional, share_of_profit = 100_000, 180_000
    interest_on_capital, drawings, interest_on_drawings = 36_000, 90_000, 4_000
    opening = (
        closing
        - additional
        - share_of_profit
        - interest_on_capital
        + drawings
        + interest_on_drawings
    )
    # Self-check the stem's own consistency: 6% on capital employed all year.
    assert abs(interest_on_capital - (opening + additional) * 0.06) < 1e-6
    key = {
        320_000: "A",  # drawings deducted instead of added back
        536_000: "B",  # interest on capital not removed
        600_000: "C",  # additional capital not removed
        500_000: "D",
    }[round(opening)]
    return {"answer": key, "computed": opening}


# ---------------------------------------------------- §6 interest on drawings


def q_f1c10_013():
    rate = 12
    schedule = equal_instalment_drawings(amount_each=8_000, instalments=12, timing="beginning")
    interest = drawings_interest_by_products(schedule, rate)
    total = 8_000 * 12
    # the derived average period must be the textbook 6.5 months
    assert abs(average_period(12, 1) - 6.5) < 1e-9
    assert abs(interest - total * rate / 100 * 6.5 / 12) < 1e-6
    key = {
        5_280: "A",  # 5.5 months (end-of-month pattern)
        5_760: "B",  # 6 months (middle-of-month / no-date convention)
        6_240: "C",
        11_520: "D",  # full 12 months on the whole year's drawings
    }[round(interest)]
    return {"answer": key, "computed": interest}


def q_f1c10_014():
    rate = 10
    schedule = equal_instalment_drawings(amount_each=15_000, instalments=4, timing="beginning")
    interest = drawings_interest_by_products(schedule, rate)
    assert abs(average_period(12, 3) - 7.5) < 1e-9
    key = {
        2_250: "A",  # 4.5 months (end-of-quarter pattern)
        3_750: "B",
        3_000: "C",  # 6 months
        6_000: "D",  # full 12 months
    }[round(interest)]
    return {"answer": key, "computed": interest}


def q_f1c10_015():
    rate = 9
    # months from the date of drawing to 31 March 2026
    schedule = [(20_000, 11), (30_000, 8), (15_000, 4), (25_000, 2)]
    interest = drawings_interest_by_products(schedule, rate)

    total = sum(a for a, _ in schedule)
    flat_six = total * rate / 100 * 6 / 12
    full_year = total * rate / 100
    reversed_months = drawings_interest_by_products(
        [(20_000, 1), (30_000, 4), (15_000, 8), (25_000, 10)], rate
    )
    key = {
        4_275: "A",
        round(flat_six): "B",       # flat 6 months on the total drawings
        round(full_year): "C",      # a full year on the total drawings
        round(reversed_months): "D",  # months counted from 1 April to the drawing
    }[round(interest)]
    return {"answer": key, "computed": interest}


# --------------------------------------------------------------- §8 guarantee


def q_f1c10_019():
    profit = 480_000
    ratio = {"A": Fraction(3, 6), "B": Fraction(2, 6), "C": Fraction(1, 6)}
    shares = {p: profit * r for p, r in ratio.items()}
    guarantee = 100_000
    deficiency = max(0, guarantee - shares["C"])
    # borne by A and B in their MUTUAL ratio 3:2
    b_bears = deficiency * Fraction(2, 5)
    b_final = shares["B"] - b_bears
    assert shares["A"] - deficiency * Fraction(3, 5) + b_final + guarantee == profit
    key = {
        160_000: "A",  # guarantee ignored
        150_000: "B",  # deficiency split equally
        148_000: "C",  # 3:2 applied the wrong way round
        152_000: "D",
    }[round(b_final)]
    return {"answer": key, "computed": float(b_final)}


def q_f1c10_020():
    profit = 500_000
    ratio = {"X": Fraction(5, 10), "Y": Fraction(3, 10), "Z": Fraction(2, 10)}
    shares = {p: profit * r for p, r in ratio.items()}
    deficiency = max(0, 120_000 - shares["Z"])
    x_final = shares["X"] - deficiency  # guaranteed by X ALONE
    key = {
        230_000: "A",
        250_000: "B",  # guarantee ignored
        round(shares["X"] - deficiency * Fraction(5, 8)): "C",  # spread over X and Y in 5:3
        round(shares["X"] - deficiency / 2): "D",  # split equally between X and Y
    }[round(x_final)]
    return {"answer": key, "computed": float(x_final)}


# -------------------------------------------------------- §9 past adjustments


def q_f1c10_021():
    capitals = {"D": 500_000, "E": 400_000, "F": 100_000}
    psr = {"D": Fraction(2, 5), "E": Fraction(2, 5), "F": Fraction(1, 5)}
    rate = 8
    should_get = {p: c * rate / 100 for p, c in capitals.items()}
    total = sum(should_get.values())
    already_got = {p: float(total * psr[p]) for p in capitals}  # extra profit taken
    net = {p: should_get[p] - already_got[p] for p in capitals}
    assert abs(sum(net.values())) < 1e-6  # the statement must net to nil

    debited = sorted(p for p, v in net.items() if v < -1e-6)
    credited = sorted(p for p, v in net.items() if v > 1e-6)
    amount = round(max(net.values()))
    computed = (tuple(debited), tuple(credited), amount)
    key = {
        (("F",), ("D",), 8_000): "A",
        (("D",), ("F",), 8_000): "B",   # direction reversed
        (("F",), ("D",), 16_000): "C",  # gross column, not netted
    }.get(computed)
    if key is None:  # option D reopens the closed year through an adjustment a/c
        key = "D"
    return {"answer": key, "computed": f"{debited} Dr / {credited} Cr {amount:,.0f}"}


def q_f1c10_022():
    profits = [360_000, 480_000]
    total = sum(profits)
    correct = {"G": Fraction(5, 10), "H": Fraction(3, 10), "I": Fraction(2, 10)}
    actual = Fraction(1, 3)
    net = tuple(round(float(total * correct[p] - total * actual)) for p in ("G", "H", "I"))

    only_last = tuple(
        round(float(profits[1] * correct[p] - profits[1] * actual)) for p in ("G", "H", "I")
    )
    reversed_ratio = {"G": Fraction(2, 10), "H": Fraction(3, 10), "I": Fraction(5, 10)}
    reversed_net = tuple(
        round(float(total * reversed_ratio[p] - total * actual)) for p in ("G", "H", "I")
    )
    key = {
        tuple(-v for v in net): "A",  # every sign reversed
        net: "B",
        only_last: "C",  # only 2025-26 corrected
        reversed_net: "D",  # ratio read as 2:3:5
    }[net]
    return {"answer": key, "computed": f"G/H/I net {net}"}


# ---------------------------------------------------------------- §10 goodwill


def q_f1c10_023():
    reported = [240_000, 280_000, 320_000, 360_000, 300_000]
    abnormal_gain = 20_000   # profit on sale of the van, in 2024-25
    abnormal_loss = 40_000   # fire loss, charged in 2025-26
    adjusted = list(reported)
    adjusted[3] -= abnormal_gain
    adjusted[4] += abnormal_loss
    goodwill = sum(adjusted) / len(adjusted) * 2

    unadjusted = sum(reported) / len(reported) * 2
    backwards = list(reported)
    backwards[3] += abnormal_gain
    backwards[4] -= abnormal_loss
    key = {
        round(unadjusted): "A",                       # no adjustment at all
        608_000: "B",
        round(sum(backwards) / len(backwards) * 2): "C",  # both signs reversed
        round(sum(adjusted) / len(adjusted)): "D",    # average profit, not goodwill
    }[round(goodwill)]
    return {"answer": key, "computed": goodwill}


def q_f1c10_024():
    profits = [180_000, 220_000, 260_000, 300_000]
    weights = [1, 2, 3, 4]
    weighted_avg = sum(p * w for p, w in zip(profits, weights)) / sum(weights)
    goodwill = weighted_avg * 3

    simple = sum(profits) / len(profits) * 3
    rev = sum(p * w for p, w in zip(profits, reversed(weights))) / sum(weights) * 3
    key = {
        round(simple): "A",       # simple average used
        round(rev): "B",          # weights applied in reverse
        780_000: "C",
        round(weighted_avg): "D",  # weighted average itself
    }[round(goodwill)]
    return {"answer": key, "computed": goodwill}


def q_f1c10_025():
    capital_employed, rate, average = 1_500_000, 15, 300_000
    sp = super_profit(average, capital_employed, rate)
    goodwill = sp * 4
    key = {
        round(average * 4): "A",       # 4 years' purchase of the AVERAGE profit
        round(sp / (rate / 100)): "B",  # capitalisation of super profit
        round(sp): "C",                 # the super profit itself
        300_000: "D",
    }[round(goodwill)]
    return {"answer": key, "computed": goodwill}


def q_f1c10_026():
    average, rate = 420_000, 14
    assets_excl_goodwill, outside_liabilities = 3_600_000, 900_000
    capital_employed = assets_excl_goodwill - outside_liabilities
    capitalised_value = average / (rate / 100)
    goodwill = capitalised_value - capital_employed

    sp = super_profit(average, capital_employed, rate)
    # the two capitalisation routes must agree
    assert abs(sp / (rate / 100) - goodwill) < 1e-6
    key = {
        300_000: "A",
        round(capitalised_value): "B",  # capitalised value taken as goodwill
        round(sp): "C",                 # super profit taken as goodwill
        round(sp * 3): "D",             # super profit at 3 years' purchase
    }[round(goodwill)]
    return {"answer": key, "computed": goodwill}


def q_f1c10_027():
    sp, years, rate = 80_000, 5, 0.10
    pv_factor, fv_factor = 3.7908, 6.1051
    goodwill = sp * pv_factor
    key = {
        round(sp * years): "A",       # undiscounted total
        round(sp / rate): "B",        # capitalisation (perpetuity)
        round(sp * fv_factor): "C",   # future-value factor used
        303_264: "D",
    }[round(goodwill)]
    return {"answer": key, "computed": goodwill}


# --------------------------------------------------------------- §11 admission


def q_f1c10_030():
    old = {"A": Fraction(5, 8), "B": Fraction(3, 8)}
    acquired = {"A": Fraction(1, 8), "B": Fraction(1, 8)}
    new = {
        "A": old["A"] - acquired["A"],
        "B": old["B"] - acquired["B"],
        "C": acquired["A"] + acquired["B"],
    }
    assert sum(new.values()) == 1
    ratio = simplify([new["A"], new["B"], new["C"]])

    # distractor: sacrifice assumed in the OLD ratio instead
    c_share = Fraction(1, 4)
    old_ratio_variant = simplify(
        [old["A"] * (1 - c_share), old["B"] * (1 - c_share), c_share]
    )
    key = {
        (5, 3, 2): "A",             # C's share simply appended
        old_ratio_variant: "B",     # sacrifice assumed in the old ratio
        (2, 1, 1): "C",
        (4, 2, 1): "D",             # C credited with only 1/8
    }[ratio]
    return {"answer": key, "computed": ratio}


def q_f1c10_031():
    premium = 150_000
    old = {"P": Fraction(3, 5), "Q": Fraction(2, 5)}
    r_share = Fraction(1, 5)
    remaining = 1 - r_share
    new = {"P": remaining / 2, "Q": remaining / 2}  # P and Q share the rest equally
    sacrifice = {p: old[p] - new[p] for p in old}
    total_sacrifice = sum(sacrifice.values())
    split = tuple(
        round(float(premium * sacrifice[p] / total_sacrifice)) for p in ("P", "Q")
    )
    old_ratio_split = tuple(round(float(premium * old[p])) for p in ("P", "Q"))
    key = {
        (150_000, 0): "A",
        old_ratio_split: "B",           # shared in the old ratio 3:2
        (75_000, 75_000): "C",          # shared in the new mutual ratio 1:1
        (60_000, 90_000): "D",          # old ratio reversed
    }[split]
    return {"answer": key, "computed": f"P {split[0]:,} / Q {split[1]:,}"}


def q_f1c10_033():
    o_capital, o_share = 300_000, Fraction(1, 5)
    old_capitals = 600_000 + 400_000
    implied_total = float(o_capital / o_share)
    actual_total = old_capitals + o_capital
    hidden = implied_total - actual_total
    key = {
        round(hidden * float(o_share)): "A",   # O's share of the goodwill
        round(implied_total - o_capital): "B",  # old partners' required capital
        round(implied_total - old_capitals): "C",  # O's own capital not counted
        200_000: "D",
    }[round(hidden)]
    return {"answer": key, "computed": hidden}


def q_f1c10_034():
    credits = 500_000 * 0.12 + 35_000            # machinery appreciation + unrecorded asset
    debits = 240_000 * 0.10 + 18_000 + 9_000     # stock fall + provision + unrecorded liability
    profit = credits - debits
    old_ratio = {"X": Fraction(7, 10), "Y": Fraction(3, 10)}
    x_share = float(profit * old_ratio["X"])

    without_investment = (credits - 35_000) - debits
    key = {
        30_800: "A",
        round(float(profit * old_ratio["Y"])): "B",   # 7:3 reversed
        round(profit / 2): "C",                       # shared equally
        round(float(without_investment * old_ratio["X"])): "D",  # unrecorded asset omitted
    }[round(x_share)]
    return {"answer": key, "computed": x_share}


# -------------------------------------------------------------- §12 retirement


def q_f1c10_037():
    old = {"A": Fraction(4, 9), "C": Fraction(2, 9)}
    new = {"A": Fraction(5, 8), "C": Fraction(3, 8)}
    gain = {p: new[p] - old[p] for p in old}
    ratio = simplify([gain["A"], gain["C"]])
    key = {
        (5, 3): "A",   # the new ratio itself
        (13, 11): "B",
        (2, 1): "C",   # the continuing partners' old ratio
        (11, 13): "D",  # the two gains swapped
    }[ratio]
    return {"answer": key, "computed": ratio}


def q_f1c10_038():
    goodwill = 480_000
    old = {"P": Fraction(3, 6), "Q": Fraction(2, 6), "R": Fraction(1, 6)}
    new = {"P": Fraction(3, 5), "R": Fraction(2, 5)}
    q_goodwill = float(goodwill * old["Q"])
    gain = {p: new[p] - old[p] for p in ("P", "R")}
    total_gain = sum(gain.values())
    borne = tuple(round(float(q_goodwill * gain[p] / total_gain)) for p in ("P", "R"))

    # distractor: borne in the continuing partners' OLD mutual ratio 3:1
    old_mutual = {"P": old["P"], "R": old["R"]}
    old_split = tuple(
        round(float(q_goodwill * old_mutual[p] / sum(old_mutual.values()))) for p in ("P", "R")
    )
    key = {
        old_split: "B",
        (80_000, 80_000): "C",  # split equally
        (48_000, 112_000): "D",
    }.get(borne, "A")  # option A raises a Goodwill Account, which no computation reaches
    return {"answer": key, "computed": f"P {borne[0]:,} / R {borne[1]:,} to Q {q_goodwill:,.0f}"}


def q_f1c10_039():
    capital_after_adjustments, settlement = 640_000, 760_000
    t_share = Fraction(3, 10)
    t_goodwill = settlement - capital_after_adjustments
    firm_goodwill = float(t_goodwill / t_share)
    key = {
        round(t_goodwill): "A",            # his share taken as the firm's goodwill
        round(t_goodwill * 10): "B",       # grossed up by 10 instead of 10/3
        400_000: "C",
        settlement: "D",                   # whole settlement treated as goodwill
    }[round(firm_goodwill)]
    return {"answer": key, "computed": firm_goodwill}


# ------------------------------------------------------------------- §13 death


def q_f1c10_041():
    last_year_sales, last_year_profit = 5_000_000, 600_000
    sales_to_date = 900_000
    profit_rate = last_year_profit / last_year_sales
    profit_to_date = sales_to_date * profit_rate
    m_share = Fraction(1, 6)
    result = float(profit_to_date * m_share)

    time_basis = float(last_year_profit * Fraction(3, 12) * m_share)
    key = {
        18_000: "A",
        round(time_basis): "B",             # time basis instead of turnover basis
        round(profit_to_date): "C",         # the firm's profit, not his share
        round(float(profit_to_date * Fraction(1, 3))): "D",  # share taken as 1/3
    }[round(result)]
    return {"answer": key, "computed": result}


def q_f1c10_042():
    c_share = Fraction(1, 5)
    capital = 300_000
    reserve_share = float(200_000 * c_share)
    revaluation_loss_share = float(50_000 * c_share)
    goodwill_share = float(500_000 * c_share)
    profit_to_date = float(360_000 * Fraction(6, 12) * c_share)
    drawings = 40_000

    payable = (
        capital
        + reserve_share
        - revaluation_loss_share
        + goodwill_share
        + profit_to_date
        - drawings
    )
    key = {
        round(payable - goodwill_share): "A",              # goodwill share omitted
        426_000: "B",
        round(payable + 2 * revaluation_loss_share): "C",  # revaluation loss added
        round(payable + 2 * drawings): "D",                # drawings added back
    }[round(payable)]
    return {"answer": key, "computed": payable}


def q_f1c10_043():
    profits = [420_000, 480_000, 540_000]
    average = sum(profits) / len(profits)
    months = Fraction(5, 12)          # 1 April 2025 to 31 August 2025
    r_share = Fraction(2, 10)
    result = float(average * months * r_share)
    key = {
        round(float(average * r_share)): "A",                    # no time apportionment
        round(float(profits[-1] * months * r_share)): "B",       # latest year, not the average
        round(float(average * Fraction(7, 12) * r_share)): "C",  # seven months counted
        40_000: "D",
    }[round(result)]
    return {"answer": key, "computed": result}
