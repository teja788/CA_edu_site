"""Verifier for foundation/quantitative-aptitude/correlation-and-regression.json (P3 Ch 17).

Every function recomputes its answer from the stem's OWN data — the paired
(x, y) lists, the five raw sums, the given regression coefficients, or the given
ranks — never from the bank's answer key. Exact rationals come from
``fractions.Fraction`` wherever the arithmetic is rational (sums, covariances,
regression coefficients, rank correlation); ``math.sqrt`` with a tolerance is
used only where a square root is unavoidable (the correlation coefficient r and
r = ±sqrt(b_yx * b_xy)). Each computed value is mapped to an option key through a
dict of the four printed option VALUES, so a wrong key shows up as a mismatch and
a wrong option value shows up as a failure to match exactly one option.

Conventions (they match the chapter notes; a reviewer should confirm them against
the study material):

  * r = [n*Sxy - Sx*Sy] / sqrt([n*Sx2 - Sx^2] * [n*Sy2 - Sy^2]).
  * Covariance is the mean of the deviation products,
    Cov = Sxy/n - xbar*ybar = (n*Sxy_raw - Sx*Sy) / n^2.
  * Regression coefficients share the numerator of r; b_yx divides by the x
    spread, b_xy by the y spread. b_yx = r*(sy/sx), b_xy = r*(sx/sy).
  * Rank correlation R = 1 - 6*Sd2 / [n(n^2 - 1)]; tied ranks use average ranks
    and the correction Sum (m^3 - m)/12 added to Sd2.
  * Probable error PE = 0.6745*(1 - r^2)/sqrt(n).
  * Percentages/coefficients are matched to the printed rounding via a tolerance.
"""

from __future__ import annotations

import math
from collections import Counter
from fractions import Fraction as Fr


# --------------------------------------------------------------- shared helpers


def sums(x, y):
    """Return the exact five raw sums (and n) as Fractions."""
    n = len(x)
    assert len(y) == n
    Sx = sum(Fr(v) for v in x)
    Sy = sum(Fr(v) for v in y)
    Sxy = sum(Fr(a) * Fr(b) for a, b in zip(x, y))
    Sx2 = sum(Fr(v) * Fr(v) for v in x)
    Sy2 = sum(Fr(v) * Fr(v) for v in y)
    return n, Sx, Sy, Sxy, Sx2, Sy2


def num_and_brackets(n, Sx, Sy, Sxy, Sx2, Sy2):
    """The shared numerator and the two spread brackets, all exact."""
    numerator = n * Sxy - Sx * Sy
    bx = n * Sx2 - Sx * Sx
    by = n * Sy2 - Sy * Sy
    return numerator, bx, by


def pearson_from_sums(n, Sx, Sy, Sxy, Sx2, Sy2):
    numerator, bx, by = num_and_brackets(n, Sx, Sy, Sxy, Sx2, Sy2)
    denom = math.sqrt(float(bx) * float(by))
    return float(numerator) / denom


def pearson(x, y):
    return pearson_from_sums(*sums(x, y))


def b_yx(x, y):
    n, Sx, Sy, Sxy, Sx2, Sy2 = sums(x, y)
    numerator, bx, _ = num_and_brackets(n, Sx, Sy, Sxy, Sx2, Sy2)
    return numerator / bx  # exact Fraction


def b_xy(x, y):
    n, Sx, Sy, Sxy, Sx2, Sy2 = sums(x, y)
    numerator, _, by = num_and_brackets(n, Sx, Sy, Sxy, Sx2, Sy2)
    return numerator / by  # exact Fraction


def covariance(x, y):
    """Cov = mean of deviation products = (n*Sxy - Sx*Sy) / n^2, exact."""
    n, Sx, Sy, Sxy, Sx2, Sy2 = sums(x, y)
    numerator, _, _ = num_and_brackets(n, Sx, Sy, Sxy, Sx2, Sy2)
    return numerator / (n * n)


def r_from_bs(byx, bxy):
    """r = ±sqrt(byx*bxy); the sign is the common sign of the two coefficients."""
    byx, bxy = float(byx), float(bxy)
    prod = byx * bxy
    r = math.sqrt(abs(prod))
    if byx < 0 and bxy < 0:
        r = -r
    return r


def average_ranks(values):
    """Average ranks, highest value = rank 1 (descending)."""
    order = sorted(values, reverse=True)
    # positions occupied by each value (1-based) in the descending order
    pos = {}
    start = 1
    for val in order:
        pos.setdefault(val, [])
    # assign positions in order, grouping equal values
    positions = {}
    for idx, val in enumerate(order, start=1):
        positions.setdefault(val, []).append(idx)
    avg = {val: Fr(sum(ps), len(ps)) for val, ps in positions.items()}
    return [avg[v] for v in values]


def rank_correlation(x, y):
    """Spearman R with average ranks and the tie correction, exact Fraction."""
    n = len(x)
    rx = average_ranks(x)
    ry = average_ranks(y)
    Sd2 = sum((a - b) * (a - b) for a, b in zip(rx, ry))
    tie = Fr(0)
    for series in (x, y):
        for m in Counter(series).values():
            if m > 1:
                tie += Fr(m ** 3 - m, 12)
    Sd2c = Sd2 + tie
    return 1 - Fr(6) * Sd2c / (n * (n * n - 1))


def rank_correlation_from_sd2(Sd2, n):
    return 1 - Fr(6) * Fr(Sd2) / (n * (n * n - 1))


def probable_error(r, n):
    return 0.6745 * (1 - r * r) / math.sqrt(n)


def pick(computed, options, tol=Fr(1, 100)):
    """Map one computed value to exactly one option key by VALUE."""
    c = float(computed)
    t = float(tol)
    hits = [k for k, v in options.items() if abs(float(Fr(v)) - c) <= t]
    if len(hits) != 1:
        raise AssertionError(f"computed {c} matched {hits} in {options}")
    return hits[0]


def result(computed, options, tol=Fr(1, 100)):
    return {"answer": pick(computed, options, tol), "computed": str(computed)}


# datasets reused across questions
DS_A = ([1, 2, 3, 4, 5], [3, 2, 5, 6, 4])
DS_G = ([6, 2, 10, 4, 8], [9, 11, 5, 8, 7])


# --------------------------------------------------------------- §3 Pearson r


def q_f3c17_006():
    r = pearson(*DS_A)
    return result(r, {"A": "1.0", "B": "0.36", "C": "0.6", "D": "0.3"}, tol="0.01")


def q_f3c17_007():
    cov = covariance(*DS_A)  # exact 6/5
    return result(cov, {"A": "6", "B": "1.2", "C": "0.6", "D": "30"}, tol="0.001")


def q_f3c17_008():
    # given sums for 5 pairs; recompute r from them
    n, Sx, Sy, Sxy, Sx2, Sy2 = 5, Fr(30), Fr(38), Fr(264), Fr(220), Fr(330)
    r = pearson_from_sums(n, Sx, Sy, Sxy, Sx2, Sy2)
    return result(r, {"A": "1.00", "B": "0.90", "C": "0.79", "D": "0.89"}, tol="0.01")


def q_f3c17_026():
    r = pearson(*DS_G)
    return result(r, {"A": "-1.3", "B": "0.92", "C": "-0.65", "D": "-0.92"}, tol="0.01")


def q_f3c17_043():
    n, Sx, Sy, Sxy, Sx2, Sy2 = 8, Fr(56), Fr(40), Fr(364), Fr(524), Fr(256)
    r = pearson_from_sums(n, Sx, Sy, Sxy, Sx2, Sy2)
    return result(r, {"A": "1.5", "B": "0.95", "C": "0.98", "D": "0.64"}, tol="0.01")


# ------------------------------------------------------------ regression b's


def q_f3c17_009():
    n, Sx, Sy, Sxy, Sx2, Sy2 = 5, Fr(30), Fr(38), Fr(264), Fr(220), Fr(330)
    numerator, bx, _ = num_and_brackets(n, Sx, Sy, Sxy, Sx2, Sy2)
    byx = numerator / bx
    return result(byx, {"A": "0.87", "B": "0.6", "C": "1.11", "D": "0.9"}, tol="0.01")


def q_f3c17_010():
    bxy = b_xy(*DS_G)  # exact -13/10
    return result(bxy, {"A": "-0.92", "B": "-0.65", "C": "1.3", "D": "-1.3"}, tol="0.01")


def q_f3c17_027():
    byx = b_yx(*DS_A)  # exact 3/5
    return result(byx, {"A": "0.6", "B": "1.2", "C": "0.36", "D": "1.67"}, tol="0.01")


def q_f3c17_028():
    n, Sx, Sy, Sxy, Sx2, Sy2 = 5, Fr(30), Fr(38), Fr(264), Fr(220), Fr(330)
    numerator, _, by = num_and_brackets(n, Sx, Sy, Sxy, Sx2, Sy2)
    bxy = numerator / by
    return result(bxy, {"A": "0.87", "B": "0.9", "C": "1.14", "D": "0.79"}, tol="0.01")


def q_f3c17_041():
    n, Sx, Sy, Sxy, Sx2, Sy2 = 8, Fr(56), Fr(40), Fr(364), Fr(524), Fr(256)
    numerator, bx, _ = num_and_brackets(n, Sx, Sy, Sxy, Sx2, Sy2)
    byx = numerator / bx
    return result(byx, {"A": "1.57", "B": "1.5", "C": "0.98", "D": "0.64"}, tol="0.01")


def q_f3c17_042():
    n, Sx, Sy, Sxy, Sx2, Sy2 = 8, Fr(56), Fr(40), Fr(364), Fr(524), Fr(256)
    numerator, _, by = num_and_brackets(n, Sx, Sy, Sxy, Sx2, Sy2)
    bxy = numerator / by
    return result(bxy, {"A": "0.64", "B": "0.67", "C": "0.98", "D": "1.5"}, tol="0.01")


# ------------------------------------------------------- b from r and SDs


def q_f3c17_014():
    r, sx, sy = Fr(8, 10), Fr(4), Fr(6)
    byx = r * sy / sx  # exact 6/5
    return result(byx, {"A": "0.53", "B": "1.2", "C": "4.8", "D": "0.8"}, tol="0.01")


def q_f3c17_015():
    r, sx, sy = Fr(7, 10), Fr(5), Fr(10)
    bxy = r * sx / sy  # exact 7/20
    return result(bxy, {"A": "1.4", "B": "0.7", "C": "0.35", "D": "3.5"}, tol="0.01")


def q_f3c17_035():
    cov, var_x = Fr(12), Fr(16)
    byx = cov / var_x  # 3/4
    return result(byx, {"A": "0.75", "B": "1.33", "C": "0.6", "D": "192"}, tol="0.01")


def q_f3c17_034():
    cov, sx, sy = Fr(12), Fr(4), Fr(5)
    r = cov / (sx * sy)  # 3/5
    return result(r, {"A": "0.6", "B": "0.48", "C": "2.4", "D": "0.75"}, tol="0.01")


def q_f3c17_033():
    # b_yx / b_xy = sy^2 / sx^2, so sy = sx * sqrt(byx/bxy)
    byx, bxy, sx = Fr(16, 10), Fr(4, 10), Fr(3)
    ratio = byx / bxy  # 4
    sy = float(sx) * math.sqrt(float(ratio))
    return result(sy, {"A": "12", "B": "1.5", "C": "6", "D": "4.8"}, tol="0.01")


# ------------------------------------------------------- r from the two b's


def q_f3c17_011():
    r = r_from_bs(Fr(8, 10), Fr(45, 100))
    return result(r, {"A": "0.625", "B": "0.36", "C": "0.6", "D": "1.2"}, tol="0.01")


def q_f3c17_012():
    r = r_from_bs(Fr(-6, 10), Fr(-6, 10))
    return result(r, {"A": "0.6", "B": "-0.6", "C": "-0.36", "D": "0"}, tol="0.01")


def q_f3c17_029():
    r = r_from_bs(Fr(15, 10), Fr(6, 10))
    return result(r, {"A": "0.95", "B": "0.9", "C": "1.05", "D": "2.1"}, tol="0.01")


def q_f3c17_030():
    r = r_from_bs(Fr(-9, 10), Fr(-4, 10))
    return result(r, {"A": "-0.36", "B": "0.6", "C": "-0.6", "D": "-0.65"}, tol="0.01")


def q_f3c17_044():
    r = r_from_bs(Fr(6364, 10000), Fr(15, 10))
    return result(r, {"A": "0.98", "B": "0.95", "C": "1.07", "D": "2.14"}, tol="0.01")


def q_f3c17_047():
    r = r_from_bs(Fr(2, 10), Fr(18, 10))
    return result(r, {"A": "0.36", "B": "0.6", "C": "1.0", "D": "2.0"}, tol="0.01")


# ------------------------------------------------------- covariance from sums


def q_f3c17_031():
    n, Sx, Sy, Sxy = 5, Fr(30), Fr(38), Fr(264)
    cov = Sxy / n - (Sx / n) * (Sy / n)  # 7.2
    return result(cov, {"A": "0.9", "B": "52.8", "C": "180", "D": "7.2"}, tol="0.01")


# ------------------------------------------------------- prediction


def q_f3c17_016():
    # line y = 0.6x + 2.2 at x = 10
    y = Fr(6, 10) * 10 + Fr(22, 10)
    return result(y, {"A": "6.0", "B": "8.2", "C": "2.8", "D": "16.3"}, tol="0.01")


def q_f3c17_017():
    # line x = 0.6y + 0.6 at y = 9
    xv = Fr(6, 10) * 9 + Fr(6, 10)
    return result(xv, {"A": "5.4", "B": "9.0", "C": "6.0", "D": "15.0"}, tol="0.01")


def q_f3c17_032():
    # y - ybar = byx (x - xbar); xbar=6, ybar=7.6, byx=0.9, x=12
    xbar, ybar, byx, x = Fr(6), Fr(76, 10), Fr(9, 10), Fr(12)
    y = ybar + byx * (x - xbar)
    return result(y, {"A": "13.0", "B": "10.8", "C": "7.6", "D": "15.4"}, tol="0.01")


def q_f3c17_045():
    y = Fr(2) * 5 + Fr(3)
    return result(y, {"A": "10", "B": "13", "C": "5", "D": "25"}, tol="0.01")


# ------------------------------------------------------- means from two lines


def _solve2(a1, b1, c1, a2, b2, c2):
    """Solve a1*x + b1*y = c1 and a2*x + b2*y = c2 exactly."""
    a1, b1, c1, a2, b2, c2 = map(Fr, (a1, b1, c1, a2, b2, c2))
    det = a1 * b2 - a2 * b1
    x = (c1 * b2 - c2 * b1) / det
    y = (a1 * c2 - a2 * c1) / det
    return x, y


def q_f3c17_018():
    # 3x + 2y = 26 ; 6x + y = 31 -> xbar
    x, y = _solve2(3, 2, 26, 6, 1, 31)
    return result(x, {"A": "5", "B": "7", "C": "4", "D": "13"}, tol="0.001")


def q_f3c17_038():
    # 8x - 10y = -66 ; 40x - 18y = 214 -> ybar
    x, y = _solve2(8, -10, -66, 40, -18, 214)
    return result(y, {"A": "13", "B": "17", "C": "7", "D": "6.6"}, tol="0.001")


# ------------------------------------------------------- rank correlation


def q_f3c17_020():
    d = [-1, 1, -1, 1, -1, 1]
    Sd2 = sum(v * v for v in d)
    R = rank_correlation_from_sd2(Sd2, 6)
    return result(R, {"A": "0.60", "B": "0.17", "C": "-0.83", "D": "0.83"}, tol="0.01")


def q_f3c17_021():
    d = [-2, 1, -1, 2, -1, 1, 0]
    Sd2 = sum(v * v for v in d)
    R = rank_correlation_from_sd2(Sd2, 7)
    return result(R, {"A": "0.79", "B": "0.21", "C": "0.86", "D": "0.64"}, tol="0.01")


def q_f3c17_022():
    X = [50, 70, 60, 60, 80]
    Y = [55, 60, 40, 55, 60]
    R = rank_correlation(X, Y)  # 0.675 exact
    return result(R, {"A": "0.75", "B": "0.60", "C": "0.325", "D": "0.675"}, tol="0.005")


def q_f3c17_039():
    R = rank_correlation_from_sd2(44, 10)
    return result(R, {"A": "0.44", "B": "0.27", "C": "0.56", "D": "0.73"}, tol="0.01")


# ------------------------------------------------------- probable error


def q_f3c17_023():
    pe = probable_error(0.6, 64)
    return result(pe, {"A": "0.054", "B": "0.076", "C": "0.43", "D": "0.34"}, tol="0.001")


def q_f3c17_040():
    pe = probable_error(0.8, 25)
    return result(pe, {"A": "0.0486", "B": "0.027", "C": "0.243", "D": "0.29"}, tol="0.001")


def q_f3c17_048():
    pe = probable_error(0.9, 100)
    return result(pe, {"A": "0.077", "B": "0.0067", "C": "0.128", "D": "0.0128"}, tol="0.0005")
