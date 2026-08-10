"""Verifier for foundation/quantitative-aptitude/theoretical-distributions.json (P3 Ch 16).

Every function recomputes its answer from the stem's own parameters and maps the
computed value to an option key through a dict of the four option VALUES — never
through the bank's answer key. A wrong key in the bank therefore shows up as a
mismatch, and a wrong option value shows up as an assertion.

Conventions applied throughout (they match the chapter's notes, and a reviewer
should confirm them against the study material):

  * Binomial probabilities are computed EXACTLY with ``math.comb`` and
    ``fractions.Fraction``; means, variances and modes are exact.
  * Poisson probabilities use ``math.exp`` and are compared with a tolerance.
  * z-scores and raw values from z are computed exactly from the stem.
  * Normal AREAS use only the standard values built into the stems:
      area(0 to 1) = 0.3413, area(0 to 1.96) = 0.4750, area(0 to 2) = 0.4772,
      area(0 to 2.58) = 0.4950, area(0 to 3) = 0.4987,
    and the empirical within-band areas 2 x 0.3413 = 0.6826, 2 x 0.4772 = 0.9544.
    No external z-table is consulted.
  * Probabilities are quoted to four decimal places, percentages to two.

The tolerance in ``pick`` (0.01) is wider than the worst rounding error of a
displayed option, and every distractor in the bank sits far outside it, so a
computed value matches exactly one option.
"""

from __future__ import annotations

import math
from fractions import Fraction

# ------------------------------------------------------------ standard normal areas
# area from the mean (z = 0) out to the stated z; these are the ONLY table values
# used, and each is also quoted in the stem of the question that relies on it.
AREA_0_TO = {
    "1": 0.3413,
    "1.96": 0.4750,
    "2": 0.4772,
    "2.58": 0.4950,
    "3": 0.4987,
}


# ------------------------------------------------------------ shared helpers


def binom_p(n, r, p):
    """Exact binomial probability nCr p^r q^(n-r) as a Fraction."""
    p = Fraction(p)
    q = 1 - p
    return math.comb(n, r) * (p ** r) * (q ** (n - r))


def poisson_p(x, m):
    """Poisson probability e^(-m) m^x / x! as a float."""
    return math.exp(-m) * (m ** x) / math.factorial(x)


def binom_mode(n, p):
    """Integer part of (n+1)p when it is not an integer (single mode)."""
    val = (n + 1) * p
    return math.floor(val)


def pick(computed, options, tol=0.01):
    """Map a computed value to exactly one option key by numeric value."""
    c = float(computed)
    hits = [k for k, v in options.items() if abs(float(v) - c) <= tol]
    if len(hits) != 1:
        raise AssertionError(f"computed {computed} matched {hits} in {options}")
    return hits[0]


def result(computed, options, tol=0.01):
    return {"answer": pick(computed, options, tol), "computed": str(computed)}


# ================================================================ §2-§4 binomial


def q_f3c16_004():
    # n = 6, p = 1/2, r = 4. Exact: 15/64.
    prob = binom_p(6, 4, Fraction(1, 2))
    assert prob == Fraction(15, 64)
    return result(
        prob,
        {"A": "0.2344", "B": "0.0938", "C": "0.3125", "D": "0.1563"},
    )


def q_f3c16_005():
    # n = 5, p = 1/3, r = 2. Exact: 80/243.
    prob = binom_p(5, 2, Fraction(1, 3))
    assert prob == Fraction(80, 243)
    return result(
        prob,
        {"A": "0.1646", "B": "0.3292", "C": "0.2963", "D": "0.0329"},
    )


def q_f3c16_006():
    # Mean = n p, exact.
    n, p = 20, Fraction(3, 10)
    mean = n * p
    return result(
        mean,
        {"A": "6", "B": "4.2", "C": "2.0494", "D": "20"},
    )


def q_f3c16_007():
    # Variance = n p q, exact; must be below the mean.
    n, p = 20, Fraction(3, 10)
    q = 1 - p
    variance = n * p * q
    assert variance < n * p
    return result(
        variance,
        {"A": "6", "B": "4.2", "C": "2.0494", "D": "14"},
    )


def q_f3c16_008():
    # SD = sqrt(n p q); here n p q = 25 exactly, so the root is exact.
    n, p = 100, Fraction(1, 2)
    npq = n * p * (1 - p)
    assert npq == 25
    sd = math.isqrt(int(npq))
    return result(
        sd,
        {"A": "25", "B": "50", "C": "5", "D": "7.07"},
    )


def q_f3c16_009():
    # P(at least one) = 1 - q^n, n = 4, p = 1/2. Exact 15/16.
    n, p = 4, Fraction(1, 2)
    prob = 1 - (1 - p) ** n
    assert prob == Fraction(15, 16)
    return result(
        prob,
        {"A": "0.0625", "B": "0.9375", "C": "0.25", "D": "0.5"},
    )


def q_f3c16_010():
    # P(X = 0) = q^n, n = 5, p = 0.2. Exact (0.8)^5 = 0.32768.
    n, p = 5, Fraction(2, 10)
    prob = (1 - p) ** n
    return result(
        prob,
        {"A": "0.3277", "B": "0.6723", "C": "0.2", "D": "0"},
    )


def q_f3c16_011():
    # Recover n from mean = 4 and variance = 2.4: q = var/mean, p = 1-q, n = mean/p.
    mean, variance = Fraction(4), Fraction(24, 10)
    q = variance / mean
    p = 1 - q
    n = mean / p
    assert p == Fraction(2, 5) and n == 10
    return result(
        n,
        {"A": "6", "B": "10", "C": "4", "D": "0.4"},
    )


def q_f3c16_012():
    # Mode = integer part of (n+1)p, n = 10, p = 0.4 -> 4.4 -> 4.
    mode = binom_mode(10, 0.4)
    assert mode == 4
    return result(
        mode,
        {"A": "4", "B": "5", "C": "4.4", "D": "0.4"},
    )


def q_f3c16_013():
    # n = 8, p = 1/2, r = 3. Exact 56/256 = 0.21875.
    prob = binom_p(8, 3, Fraction(1, 2))
    assert prob == Fraction(56, 256)
    return result(
        prob,
        {"A": "0.2188", "B": "0.1094", "C": "0.2734", "D": "0.0313"},
    )


def q_f3c16_014():
    # Expected frequency = N x P(X = r); N = 320, n = 5, p = 1/2, r = 2. Exact 100.
    N = 320
    freq = N * binom_p(5, 2, Fraction(1, 2))
    assert freq == 100
    return result(
        freq,
        {"A": "10", "B": "50", "C": "100", "D": "160"},
    )


# ================================================================ §5-§7 Poisson


def q_f3c16_017():
    # m = 2, x = 3.
    prob = poisson_p(3, 2)
    return result(
        prob,
        {"A": "0.1804", "B": "0.2707", "C": "0.1353", "D": "0.0902"},
    )


def q_f3c16_018():
    # P(X = 0) = e^(-m), m = 1.5.
    prob = poisson_p(0, 1.5)
    return result(
        prob,
        {"A": "0.2231", "B": "0.7769", "C": "0.3347", "D": "0.1116"},
    )


def q_f3c16_019():
    # m = 3, x = 2.
    prob = poisson_p(2, 3)
    return result(
        prob,
        {"A": "0.1494", "B": "0.2240", "C": "0.2510", "D": "0.0498"},
    )


def q_f3c16_021():
    # Mean m = 2, find P(X = 2) = 2 e^(-2).
    prob = poisson_p(2, 2)
    return result(
        prob,
        {"A": "0.1353", "B": "0.2707", "C": "0.1804", "D": "0.5413"},
    )


def q_f3c16_022():
    # P(at least one) = 1 - e^(-m), m = 1.
    prob = 1 - poisson_p(0, 1)
    return result(
        prob,
        {"A": "0.3679", "B": "0.6321", "C": "0.7358", "D": "0.2642"},
    )


def q_f3c16_023():
    # Additive property: m = m1 + m2 = 1.5 + 2.5 = 4; P(X = 0) = e^(-4).
    m = 1.5 + 2.5
    assert m == 4
    prob = poisson_p(0, m)
    return result(
        prob,
        {"A": "0.0183", "B": "0.0821", "C": "0.1353", "D": "0.0916"},
    )


def q_f3c16_024():
    # Mode of a Poisson with non-integer m is the integer part; m = 2.6 -> 2.
    m = 2.6
    mode = math.floor(m)
    assert mode == 2
    return result(
        mode,
        {"A": "3", "B": "2", "C": "2.6", "D": "1.6"},
    )


def q_f3c16_025():
    # P(X = 1) = P(X = 2) forces m: e^-m m = e^-m m^2/2 -> m = 2.
    # Recover m from the recurrence P(x+1) = P(x) m/(x+1) with x = 1 and ratio 1.
    # ratio P(2)/P(1) = m/2 = 1 -> m = 2.
    m = 2 * 1  # m/2 = 1
    assert abs(poisson_p(1, m) - poisson_p(2, m)) < 1e-9
    return result(
        m,
        {"A": "1", "B": "2", "C": "4", "D": "0.5"},
    )


def q_f3c16_026():
    # Fitting: expected frequency = N x P(X = 1), N = 200, m = 1.
    N, m = 200, 1
    freq = N * poisson_p(1, m)
    return result(
        freq,
        {"A": "73.58", "B": "36.79", "C": "200", "D": "27.07"},
    )


def q_f3c16_027():
    # SD of a Poisson = sqrt(m); m = 9 -> 3.
    m = 9
    sd = math.sqrt(m)
    return result(
        sd,
        {"A": "9", "B": "81", "C": "3", "D": "4.5"},
    )


def q_f3c16_028():
    # Fit m from data: m = total occurrences / number of intervals = 300/200.
    m = Fraction(300, 200)
    assert m == Fraction(3, 2)
    return result(
        m,
        {"A": "1.5", "B": "2", "C": "0.667", "D": "3"},
    )


# ================================================================ §8-§10 normal


def q_f3c16_031():
    # z = (x - mu)/sigma = (68 - 50)/10.
    z = (68 - 50) / 10
    return result(
        z,
        {"A": "1.8", "B": "0.56", "C": "2.3", "D": "0.18"},
    )


def q_f3c16_032():
    # Raw value from z: x = mu + z sigma = 100 + 2 x 15.
    x = 100 + 2 * 15
    return result(
        x,
        {"A": "70", "B": "130", "C": "102", "D": "115"},
    )


def q_f3c16_033():
    # Within one SD: 2 x area(0 to 1), as a percentage.
    pct = 2 * AREA_0_TO["1"] * 100
    return result(
        pct,
        {"A": "34.13", "B": "68.26", "C": "95.44", "D": "50"},
    )


def q_f3c16_034():
    # Within two SD: 2 x area(0 to 2), as a percentage.
    pct = 2 * AREA_0_TO["2"] * 100
    return result(
        pct,
        {"A": "47.72", "B": "68.26", "C": "95.44", "D": "99.73"},
    )


def q_f3c16_035():
    # P(Z > 1) = 0.5 - area(0 to 1).
    prob = 0.5 - AREA_0_TO["1"]
    return result(
        prob,
        {"A": "0.3413", "B": "0.1587", "C": "0.8413", "D": "0.6587"},
    )


def q_f3c16_036():
    # P(Z < 2) = 0.5 + area(0 to 2).
    prob = 0.5 + AREA_0_TO["2"]
    return result(
        prob,
        {"A": "0.4772", "B": "0.9772", "C": "0.0228", "D": "0.5228"},
    )


def q_f3c16_037():
    # P(-1 < Z < 2) = area(0 to 1) + area(0 to 2), opposite sides add.
    prob = AREA_0_TO["1"] + AREA_0_TO["2"]
    return result(
        prob,
        {"A": "0.8185", "B": "0.1359", "C": "0.9545", "D": "0.6826"},
    )


def q_f3c16_038():
    # Percentage beyond mu + 1.96 sigma in the upper tail = 0.5 - area(0 to 1.96).
    pct = (0.5 - AREA_0_TO["1.96"]) * 100
    return result(
        pct,
        {"A": "2.5", "B": "5", "C": "1.25", "D": "97.5"},
    )


def q_f3c16_039():
    # Upper limit of the central 99% = mu + 2.58 sigma = 200 + 2.58 x 20.
    upper = 200 + 2.58 * 20
    return result(
        upper,
        {"A": "148.4", "B": "251.6", "C": "240", "D": "258"},
    )


def q_f3c16_041():
    # SD = sqrt(variance); variance = 64 -> 8.
    sd = math.isqrt(64)
    return result(
        sd,
        {"A": "8", "B": "64", "C": "32", "D": "4096"},
    )


def q_f3c16_042():
    # Upper limit of the central 95% = mu + 1.96 sigma = 500 + 1.96 x 100.
    upper = 500 + 1.96 * 100
    return result(
        upper,
        {"A": "696", "B": "304", "C": "500", "D": "600"},
    )


def q_f3c16_043():
    # Count within one SD = N x (2 x area(0 to 1)) = 10000 x 0.6826.
    count = 10000 * (2 * AREA_0_TO["1"])
    return result(
        count,
        {"A": "3413", "B": "6826", "C": "9544", "D": "5000"},
    )


# ================================================================ extras


def q_f3c16_046():
    # P(X <= 1) = P(0) + P(1), binomial n = 5, p = 1/2. Exact 6/32.
    n, p = 5, Fraction(1, 2)
    prob = binom_p(n, 0, p) + binom_p(n, 1, p)
    assert prob == Fraction(6, 32)
    return result(
        prob,
        {"A": "0.1875", "B": "0.0313", "C": "0.1563", "D": "0.8125"},
    )


def q_f3c16_047():
    # P(X >= 2) = 1 - P(0) - P(1), Poisson m = 2.
    m = 2
    prob = 1 - poisson_p(0, m) - poisson_p(1, m)
    return result(
        prob,
        {"A": "0.4060", "B": "0.5940", "C": "0.7293", "D": "0.3233"},
    )


def q_f3c16_048():
    # P(Z > 2) = 0.5 - area(0 to 2).
    prob = 0.5 - AREA_0_TO["2"]
    return result(
        prob,
        {"A": "0.4772", "B": "0.0228", "C": "0.9772", "D": "0.5228"},
    )


def q_f3c16_049():
    # Six dice, exactly two sixes: n = 6, p = 1/6, r = 2. Exact 9375/46656.
    prob = binom_p(6, 2, Fraction(1, 6))
    assert prob == Fraction(9375, 46656)
    return result(
        prob,
        {"A": "0.2009", "B": "0.0335", "C": "0.4019", "D": "0.1339"},
    )


def q_f3c16_050():
    # Percentage in the upper tail beyond mu + 2.58 sigma = 0.5 - area(0 to 2.58),
    # as a percentage.
    pct = (0.5 - AREA_0_TO["2.58"]) * 100
    return result(
        pct,
        {"A": "0.5", "B": "1", "C": "0.05", "D": "99.5"},
    )
