"""Verifier for foundation/quantitative-aptitude/statistical-description-of-data.json (P3 Ch 13).

Every function recomputes its answer from the stem's own parameters and maps the
computed value to an option key through a dict of the four option VALUES — never
through the bank's answer key. A wrong key in the bank therefore shows up as a
mismatch, and a wrong option value shows up as an assertion.

Exact rationals (relative frequencies, proportional allocation, pie-chart shares)
are carried in ``fractions.Fraction`` so no rounding creeps in; the result is then
handed to ``pick`` as a Decimal. Rounding is applied explicitly and only where a
stem asks for it.

Conventions applied throughout (they match the chapter's notes, and a reviewer
should confirm them against the study material):

  * Class boundaries close the gap between adjacent inclusive classes by HALF the
    gap (0.5 for a one-unit gap): lower boundary = lower limit − ½(gap),
    upper boundary = upper limit + ½(gap).
  * Class width = upper boundary − lower boundary; mid-value = (lower + upper) ÷ 2.
  * Sturges' rule gives k = 1 + 3.322 log₁₀ N, ROUNDED to a whole number of
    classes (half-up); the class width is then range ÷ (rounded k).
  * Relative frequency = f ÷ N and the relative frequencies sum to exactly 1.
  * A pie sector angle = (component ÷ total) × 360°, so 1% of the total = 3.6°.
  * The median read off a less-than ogive sits at the cumulative position N ÷ 2,
    interpolated inside the median class as L + [(N/2 − cf)/f] × h.
"""

from __future__ import annotations

from decimal import Context, Decimal, ROUND_HALF_UP
from fractions import Fraction

# One explicit context for the whole module: 28 significant digits, half-up.
CTX = Context(prec=28, rounding=ROUND_HALF_UP)

ONE = Decimal(1)


def D(x) -> Decimal:
    """Decimal from an int/str/Decimal/Fraction. Floats are never accepted."""
    if isinstance(x, Decimal):
        return x
    if isinstance(x, Fraction):
        return CTX.divide(Decimal(x.numerator), Decimal(x.denominator))
    return Decimal(str(x))


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


def sturges_classes(n) -> Decimal:
    """k = 1 + 3.322 log10 N, rounded to a whole number of classes (half-up)."""
    k_raw = ONE + D("3.322") * Decimal(n).log10()
    return k_raw.quantize(ONE, rounding=ROUND_HALF_UP)


# ------------------------------------------------------------ §4 sampling


def q_f3c13_011():
    # Systematic sampling interval k = N / n.
    population, sample = D(2400), D(60)
    k = CTX.divide(population, sample)
    return result(k, {"A": "40", "B": "60", "C": "2460", "D": "30"})


def q_f3c13_012():
    # Proportional allocation: units from a stratum = (stratum / N) * sample size.
    stratum, population, sample = 900, 1500, 100
    drawn = D(Fraction(stratum, population) * sample)
    # the two strata must add back to the whole sample
    other = D(Fraction(population - stratum, population) * sample)
    assert drawn + other == D(sample)
    return result(drawn, {"A": "40", "B": "60", "C": "45", "D": "50"})


# ------------------------------------------- §8 class structure


def q_f3c13_017():
    # Exclusive class: width = upper limit - lower limit.
    lower, upper = D(150), D(200)
    width = upper - lower
    return result(width, {"A": "200", "B": "175", "C": "350", "D": "50"})


def q_f3c13_018():
    # Mid-value = (lower + upper) / 2.
    lower, upper = D(118), D(126)
    mid = CTX.divide(lower + upper, D(2))
    return result(mid, {"A": "244", "B": "8", "C": "122", "D": "118"})


def q_f3c13_019():
    # Lower boundary of an inclusive class = lower limit - half the gap.
    lower_limit, gap = D(30), D(1)
    boundary = lower_limit - CTX.divide(gap, D(2))
    return result(boundary, {"A": "29.5", "B": "30", "C": "29", "D": "34.5"})


def q_f3c13_020():
    # True width of an inclusive class = upper boundary - lower boundary.
    lower_limit, upper_limit, gap = D(30), D(39), D(1)
    half = CTX.divide(gap, D(2))
    width = (upper_limit + half) - (lower_limit - half)
    # the apparent width (from raw limits) is one unit less — the B distractor
    assert upper_limit - lower_limit == D(9)
    return result(width, {"A": "10", "B": "9", "C": "9.5", "D": "39.5"})


def q_f3c13_024():
    # Lower limit = mid-value - half the class width.
    mid, width = D(42), D(8)
    lower = mid - CTX.divide(width, D(2))
    return result(lower, {"A": "34", "B": "46", "C": "38", "D": "42"})


def q_f3c13_031():
    # Upper boundary of an inclusive class = upper limit + half the gap.
    upper_limit, gap = D(199), D(1)
    boundary = upper_limit + CTX.divide(gap, D(2))
    return result(boundary, {"A": "199.5", "B": "200", "C": "199", "D": "149.5"})


def q_f3c13_032():
    # Class width = difference between two successive mid-values.
    mid1, mid2 = D(15), D(23)
    width = mid2 - mid1
    return result(width, {"A": "8", "B": "4", "C": "19", "D": "15"})


# ---------------------------------- §7 frequency distribution / Sturges


def q_f3c13_021():
    # Number of classes by Sturges' rule, rounded to a whole number.
    k = sturges_classes(100)
    assert k == D(8)
    return result(k, {"A": "8", "B": "7", "C": "6.64", "D": "100"})


def q_f3c13_022():
    # Class width = range / (rounded Sturges classes).
    low, high = D(10), D(90)
    k = sturges_classes(100)
    width = CTX.divide(high - low, k)
    return result(width, {"A": "8", "B": "10", "C": "80", "D": "11.43"})


def q_f3c13_023():
    # Number of classes = range / class width.
    low, high, width = D(100), D(160), D(10)
    classes = CTX.divide(high - low, width)
    return result(classes, {"A": "6", "B": "7", "C": "60", "D": "16"})


def q_f3c13_046():
    # Range = largest - smallest.
    largest, smallest = D(148), D(92)
    rng = largest - smallest
    return result(rng, {"A": "120", "B": "240", "C": "148", "D": "56"})


# ------------------------------------------ §9 cumulative / relative frequency


def q_f3c13_025():
    # Relative frequency = f / N.
    f, n = 45, 300
    rf = D(Fraction(f, n))
    return result(rf, {"A": "0.15", "B": "15", "C": "6.67", "D": "0.045"})


def q_f3c13_026():
    # Percentage frequency = (f / N) * 100.
    f, n = 18, 240
    pct = D(Fraction(f, n) * 100)
    return result(pct, {"A": "18", "B": "0.075", "C": "13.33", "D": "7.5"})


def q_f3c13_027():
    # Less-than cumulative frequency: sum the classes below the boundary.
    freqs_below_30 = [5, 12, 18]  # classes 0-10, 10-20, 20-30
    cum = D(sum(freqs_below_30))
    return result(cum, {"A": "35", "B": "44", "C": "30", "D": "18"})


def q_f3c13_028():
    # More-than cumulative frequency: sum the classes from 20 upward.
    freqs_from_20 = [18, 9]  # classes 20-30, 30-40
    cum = D(sum(freqs_from_20))
    return result(cum, {"A": "35", "B": "27", "C": "44", "D": "9"})


def q_f3c13_029():
    # Class frequency = difference of neighbouring less-than cumulatives.
    less_than_40, less_than_30 = D(52), D(35)
    freq = less_than_40 - less_than_30
    return result(freq, {"A": "17", "B": "87", "C": "52", "D": "35"})


def q_f3c13_030():
    # N = class frequency / relative frequency.
    freq, rel = D(24), D("0.16")
    n = CTX.divide(freq, rel)
    return result(n, {"A": "3.84", "B": "384", "C": "150", "D": "40"})


def q_f3c13_042():
    # Count at or above a value = N - less-than cumulative.
    n, less_than_50 = D(60), D(38)
    at_or_above = n - less_than_50
    return result(at_or_above, {"A": "22", "B": "38", "C": "60", "D": "12"})


def q_f3c13_044():
    # Relative frequencies sum to 1: the missing one is 1 - the rest.
    known = [Fraction(1, 10), Fraction(1, 4), Fraction(3, 10)]
    missing = D(Fraction(1) - sum(known))
    return result(missing, {"A": "0.35", "B": "0.65", "C": "0.30", "D": "1.00"})


def q_f3c13_047():
    # Class frequency = difference of neighbouring more-than cumulatives.
    more_than_100, more_than_120 = D(75), D(47)
    freq = more_than_100 - more_than_120
    return result(freq, {"A": "28", "B": "122", "C": "75", "D": "47"})


def q_f3c13_048():
    # Percentage above a value = (count / N) * 100.
    count, n = 30, 200
    pct = D(Fraction(count, n) * 100)
    return result(pct, {"A": "15", "B": "30", "C": "6.67", "D": "170"})


# ---------------------------------------------------- §10 pie charts


def q_f3c13_033():
    # Sector angle = (component / total) * 360.
    component, total = 1800, 7200
    angle = D(Fraction(component, total) * 360)
    return result(angle, {"A": "45", "B": "25", "C": "180", "D": "90"})


def q_f3c13_034():
    # Component = (angle / 360) * total.
    angle, total = 60, 36000
    amount = D(Fraction(angle, 360) * total)
    return result(amount, {"A": "60", "B": "6000", "C": "21600", "D": "216"})


def q_f3c13_035():
    # Percentage = (angle / 360) * 100.
    angle = 72
    pct = D(Fraction(angle, 360) * 100)
    return result(pct, {"A": "20", "B": "72", "C": "25.92", "D": "40"})


def q_f3c13_043():
    # Angle from a percentage: 1% = 3.6 degrees.
    pct = 35
    angle = D(Fraction(pct, 100) * 360)
    assert angle == D(pct) * D("3.6")  # the 1% = 3.6 degrees bridge
    return result(angle, {"A": "126", "B": "35", "C": "3.6", "D": "350"})


def q_f3c13_049():
    # Total = sector value * (360 / sector angle).
    sector_value, sector_angle = 5000, 45
    total = D(Fraction(sector_value) * Fraction(360, sector_angle))
    return result(total, {"A": "40000", "B": "5000", "C": "45000", "D": "625"})


# ------------------------------------------------- §11 histogram / ogive


def q_f3c13_037():
    # Frequency density = frequency / class width.
    freq, width = D(60), D(50) - D(30)
    density = CTX.divide(freq, width)
    return result(density, {"A": "3", "B": "60", "C": "20", "D": "1200"})


def q_f3c13_039():
    # Median position on a less-than ogive = N / 2.
    n = D(80)
    position = CTX.divide(n, D(2))
    return result(position, {"A": "40", "B": "80", "C": "41", "D": "20"})


def q_f3c13_040():
    # Median by ogive interpolation inside the median class.
    freqs = [6, 14, 20, 10]           # classes 0-10, 10-20, 20-30, 30-40
    boundaries = [0, 10, 20, 30, 40]
    width = 10
    n = sum(freqs)
    half = Fraction(n, 2)
    # locate the median class: first class whose cumulative reaches N/2
    cum = 0
    for idx, f in enumerate(freqs):
        prev_cum = cum
        cum += f
        if cum >= half:
            L = boundaries[idx]
            median = Fraction(L) + (half - prev_cum) / Fraction(f) * width
            break
    assert cum >= half
    return result(D(median), {"A": "20", "B": "25", "C": "22.5", "D": "22"})


# ---------------------------------------------------- §12 exam technique


def q_f3c13_050():
    # Expected mark of a blind guess: (1/4)(+1) + (3/4)(-0.25).
    ev = Fraction(1, 4) * 1 + Fraction(3, 4) * Fraction(-1, 4)
    return result(D(ev), {"A": "0.0625", "B": "0.25", "C": "0", "D": "-0.25"})
