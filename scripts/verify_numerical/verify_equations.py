"""Verifier for foundation/quantitative-aptitude/equations.json (P3 Ch 2).

Every function recomputes its answer from the stem's own parameters. Nothing is
copied from the answer key: each computed value is mapped to an option key
through a dict of the four option values, so a wrong key in the bank surfaces as
a KeyError or as a mismatch the runner reports.

Conventions used below:
  * `Fraction` is used wherever an exact rational answer is wanted (roots,
    sums and products of roots, blends, prices). Floating point appears only
    where the stem itself asks for a rounded whole number, and every such
    rounding is done explicitly with a comment saying so.
  * `quad_roots(a, b, c)` returns the two roots of ax^2 + bx + c = 0 as exact
    Fractions when the discriminant is a perfect square, and as floats
    otherwise; `TOL` is the tolerance used for any surd comparison.
  * A quadratic's roots are always returned as a sorted pair, so option
    matching never depends on which root was found first.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

TOL = 1e-9


# ------------------------------------------------------------ shared helpers


def disc(a, b, c):
    """The discriminant b^2 - 4ac."""
    return b * b - 4 * a * c


def is_perfect_square(n):
    return n >= 0 and math.isqrt(int(n)) ** 2 == int(n)


def quad_roots(a, b, c):
    """Roots of ax^2 + bx + c = 0, exact when the discriminant is a square."""
    d = disc(a, b, c)
    if d < 0:
        return None
    if is_perfect_square(d):
        r = math.isqrt(int(d))
        return tuple(sorted((F(-b - r, 2 * a), F(-b + r, 2 * a))))
    r = math.sqrt(d)
    return tuple(sorted(((-b - r) / (2 * a), (-b + r) / (2 * a))))


def nature(a, b, c):
    """Classify the roots exactly as the chapter's table does."""
    d = disc(a, b, c)
    if d < 0:
        return "not real"
    if d == 0:
        return "real and equal"
    if is_perfect_square(d):
        return "real distinct rational"
    return "real distinct irrational"


def solve_linear_pair(a1, b1, c1, a2, b2, c2):
    """Exact solution of a1 x + b1 y = c1 and a2 x + b2 y = c2."""
    den = a1 * b2 - a2 * b1
    assert den != 0, "the pair has no unique solution"
    x = F(c1 * b2 - c2 * b1, den)
    y = F(a1 * c2 - a2 * c1, den)
    return x, y


def solve_linear_triple(rows):
    """Exact solution of three equations, rows = [(a, b, c, rhs), ...]."""
    m = [[F(v) for v in row] for row in rows]
    n = 3
    for col in range(n):
        piv = next(r for r in range(col, n) if m[r][col] != 0)
        m[col], m[piv] = m[piv], m[col]
        pv = m[col][col]
        m[col] = [v / pv for v in m[col]]
        for r in range(n):
            if r != col and m[r][col] != 0:
                f = m[r][col]
                m[r] = [vr - f * vc for vr, vc in zip(m[r], m[col])]
    return m[0][3], m[1][3], m[2][3]


# ------------------------------------------------------ SS 1-3 linear equations


def q_f3c2_002():
    # 5(x - 4) = 5x - 20 -> compare the two sides coefficient by coefficient.
    left = (5, 5 * -4)  # (coefficient of x, constant)
    right = (5, -20)
    a = left[0] - right[0]
    c = left[1] - right[1]
    if a == 0 and c == 0:
        verdict = "identity"
    elif a == 0:
        verdict = "no solution"
    else:
        verdict = "one root"
    key = {"one root": "A", "identity": "B", "no solution": "C", "two roots": "D"}[verdict]
    return {"answer": key, "computed": verdict}


def q_f3c2_003():
    # 2x^4 - 5x^3 + x - 7 = 0: the degree is the highest power present.
    coeffs = {4: 2, 3: -5, 1: 1, 0: -7}
    degree = max(p for p, c in coeffs.items() if c != 0)
    key = {1: "A", 2: "B", 4: "C", 3: "D"}[degree]
    return {"answer": key, "computed": degree}


def q_f3c2_004():
    # (3x - 1)/5 - (x + 2)/3 = 2/15, cleared by the LCM 15.
    # 3(3x - 1) - 5(x + 2) = 2  ->  4x - 13 = 2
    a = 3 * 3 - 5 * 1
    const = 3 * (-1) - 5 * 2
    x = F(2 - const, a)
    key = {F(-5, 4): "A", F(-11, 4): "B", F(4, 15): "C", F(15, 4): "D"}[x]
    return {"answer": key, "computed": str(x)}


def q_f3c2_005():
    # 3/(x - 1) = 5/(x + 3) -> 3(x + 3) = 5(x - 1)
    x = F(5 * 1 + 3 * 3, 5 - 3)
    assert x != 1 and x != -3, "a root that kills a denominator must be rejected"
    key = {F(7): "A", F(-9): "B", F(2): "C", F(1): "D"}[x]
    return {"answer": key, "computed": str(x)}


def q_f3c2_006():
    # 1/(x-3) + 6/(x^2-9) = 1/(x+3), multiplied by (x-3)(x+3):
    # (x + 3) + 6 = (x - 3)
    a = 1 - 1  # coefficient of x after moving everything left
    const = (3 + 6) - (-3)
    if a == 0 and const != 0:
        verdict = "no solution"
    elif a == 0:
        verdict = "identity"
    else:
        verdict = "one root"
    key = {"x = 3": "A", "no solution": "B", "x = -3": "C", "identity": "D"}[verdict]
    return {"answer": key, "computed": verdict}


# --------------------------------------------- SS 4-7 simultaneous equations


def q_f3c2_007():
    # 4x + 3y = 34 and 5x - 2y = 8; the question asks for y.
    x, y = solve_linear_pair(4, 3, 34, 5, -2, 8)
    key = {F(4): "A", F(10): "B", F(6): "C", F(-6): "D"}[y]
    return {"answer": key, "computed": "x=%s, y=%s" % (x, y)}


def q_f3c2_008():
    # 7x + 5y = 46 and 3x + 5y = 34; the question asks for x.
    x, y = solve_linear_pair(7, 5, 46, 3, 5, 34)
    key = {F(-3): "A", F(8): "B", F(5): "C", F(3): "D"}[x]
    return {"answer": key, "computed": "x=%s, y=%s" % (x, y)}


def q_f3c2_009():
    # x = 2y - 3 and 3x + 4y = 11, i.e. x - 2y = -3 and 3x + 4y = 11.
    x, y = solve_linear_pair(1, -2, -3, 3, 4, 11)
    key = {F(1): "A", F(2): "B", F(-1): "C", F(7): "D"}[x]
    return {"answer": key, "computed": "x=%s, y=%s" % (x, y)}


def q_f3c2_010():
    # Cross-multiplication on 2x + 3y - 13 = 0 and 3x - y - 3 = 0.
    a1, b1, c1 = 2, 3, -13
    a2, b2, c2 = 3, -1, -3
    den = a1 * b2 - a2 * b1
    x = F(b1 * c2 - b2 * c1, den)
    y = F(c1 * a2 - c2 * a1, den)
    # Confirm against the ordinary elimination route (constants on the right).
    assert (x, y) == solve_linear_pair(a1, b1, -c1, a2, b2, -c2)
    key = {(F(3), F(2)): "A", (F(2), F(3)): "B", (F(-2), F(-3)): "C", (F(2), F(-3)): "D"}[(x, y)]
    return {"answer": key, "computed": "x=%s, y=%s" % (x, y)}


def q_f3c2_011():
    # 2x + 3y = 7 and 6x + ky = 21: infinitely many needs all three ratios equal.
    a1, b1, c1 = 2, 3, 7
    a2, c2 = 6, 21
    assert F(a1, a2) == F(c1, c2), "the a and c ratios must already agree"
    k = F(b1 * a2, a1)  # b1/k = a1/a2  ->  k = b1 * a2 / a1
    key = {F(1): "A", F(3): "B", F(9): "C", "none": "D"}[k]
    return {"answer": key, "computed": str(k)}


def q_f3c2_012():
    # px + 4y = 10 and 3x + 2y = 8: no solution needs a1/a2 = b1/b2 != c1/c2.
    b1, b2, c1, c2, a2 = 4, 2, 10, 8, 3
    p = F(b1 * a2, b2)  # p/a2 = b1/b2
    assert F(c1, c2) != F(b1, b2), "the c ratio must differ, or it is dependent"
    key = {F(3, 2): "A", F(2): "B", "none": "C", F(6): "D"}[p]
    return {"answer": key, "computed": str(p)}


def q_f3c2_013():
    # x + y + z = 9, 2x - y + z = 8, x + 2y - z = 3; the question asks for z.
    x, y, z = solve_linear_triple([(1, 1, 1, 9), (2, -1, 1, 8), (1, 2, -1, 3)])
    key = {F(4): "A", F(3): "B", F(2): "C", F(9): "D"}[z]
    return {"answer": key, "computed": "x=%s, y=%s, z=%s" % (x, y, z)}


def q_f3c2_014():
    # x + y = 7, y + z = 12, z + x = 13; the question asks for x + y + z.
    x, y, z = solve_linear_triple([(1, 1, 0, 7), (0, 1, 1, 12), (1, 0, 1, 13)])
    total = x + y + z
    key = {F(32): "A", F(16): "B", F(8): "C", F(9): "D"}[total]
    return {"answer": key, "computed": str(total)}


# --------------------------------------------------- SS 8-10 quadratics solved


def q_f3c2_015():
    roots = quad_roots(6, 1, -15)
    key = {
        (F(-3, 2), F(5, 3)): "A",
        (F(-5), F(3)): "B",
        (F(-5, 3), F(3, 2)): "C",
        (F(3, 2), F(5, 3)): "D",
    }[roots]
    return {"answer": key, "computed": "%s, %s" % roots}


def q_f3c2_016():
    # 4x^2 = 12x  ->  4x^2 - 12x = 0; the missing constant forces a zero root.
    roots = quad_roots(4, -12, 0)
    key = {
        (F(3),): "A",
        (F(0),): "B",
        (F(-3), F(3)): "C",
        (F(0), F(3)): "D",
    }[roots]
    return {"answer": key, "computed": "%s, %s" % roots}


def q_f3c2_017():
    # x^2 - 6x - 16 = 0 by completing the square: (x - 3)^2 = 25.
    a, b, c = 1, -6, -16
    half = F(b, 2 * a)
    rhs = half * half - F(c, a)
    r = math.isqrt(int(rhs))
    assert r * r == rhs
    roots = tuple(sorted((-half - r, -half + r)))
    assert roots == quad_roots(a, b, c)
    key = {
        (F(-2), F(8)): "A",
        (F(8),): "B",
        (F(-8), F(2)): "C",
        (F(3), F(5)): "D",
    }[roots]
    return {"answer": key, "computed": "%s, %s" % roots}


def q_f3c2_018():
    # 2x^2 + 12x - 7 = 0, divided by a first: the constant added is (b/2a)^2.
    a, b = 2, 12
    added = F(b, 2 * a) ** 2
    key = {F(36): "A", F(9): "B", F(3): "C", F(6): "D"}[added]
    return {"answer": key, "computed": str(added)}


def q_f3c2_019():
    roots = quad_roots(3, -5, -2)
    key = {
        (F(-2), F(1, 3)): "A",
        (F(1, 3), F(2)): "B",
        (F(-1, 3), F(2)): "C",
        (F(-3), F(1, 2)): "D",
    }[roots]
    return {"answer": key, "computed": "%s, %s" % roots}


def q_f3c2_020():
    # 2x^2 = 7x - 3 rearranged to 2x^2 - 7x + 3 = 0.
    roots = quad_roots(2, -7, 3)
    key = {
        (F(2), F(3)): "A",
        (F(-3), F(-1, 2)): "B",
        (F(-13, 4), F(27, 4)): "C",
        (F(1, 2), F(3)): "D",
    }[roots]
    return {"answer": key, "computed": "%s, %s" % roots}


# ------------------------------------------------ SS 11 discriminant questions


def q_f3c2_021():
    n = nature(4, -12, 9)
    key = {
        "real and equal": "A",
        "real distinct rational": "B",
        "real distinct irrational": "C",
        "not real": "D",
    }[n]
    return {"answer": key, "computed": "D=%d, %s" % (disc(4, -12, 9), n)}


def q_f3c2_022():
    n = nature(2, -3, 5)
    key = {
        "real and equal": "A",
        "not real": "B",
        "real distinct rational": "C",
        "real distinct irrational": "D",
    }[n]
    return {"answer": key, "computed": "D=%d, %s" % (disc(2, -3, 5), n)}


def q_f3c2_023():
    n = nature(1, -6, 7)
    key = {
        "real and equal": "A",
        "real distinct rational": "B",
        "real distinct irrational": "C",
        "not real": "D",
    }[n]
    return {"answer": key, "computed": "D=%d, %s" % (disc(1, -6, 7), n)}


def q_f3c2_024():
    # x^2 - mx + 16 = 0 has equal roots: D = m^2 - 64 = 0.
    ms = sorted(m for m in range(-100, 101) if disc(1, -m, 16) == 0)
    key = {(8,): "A", (4,): "B", (16,): "C", (-8, 8): "D"}[tuple(ms)]
    return {"answer": key, "computed": str(ms)}


def q_f3c2_025():
    # x^2 + (k-3)x + 9 = 0 has equal roots: (k-3)^2 - 36 = 0; take k > 0.
    ks = sorted(k for k in range(-100, 101) if disc(1, k - 3, 9) == 0)
    positive = [k for k in ks if k > 0]
    assert len(positive) == 1
    key = {9: "A", -3: "B", 3: "C", 6: "D"}[positive[0]]
    return {"answer": key, "computed": "all k: %s" % ks}


# --------------------------------------- SS 12-14 roots and their coefficients


def root_sum(a, b, c):
    return F(-b, a)


def root_product(a, b, c):
    return F(c, a)


def q_f3c2_026():
    s = root_sum(7, -21, 14)
    assert sum(quad_roots(7, -21, 14)) == s  # the relation matches the roots
    key = {F(-3): "A", F(3): "B", F(2): "C", F(-2): "D"}[s]
    return {"answer": key, "computed": str(s)}


def q_f3c2_027():
    p = root_product(5, 12, -9)
    r1, r2 = quad_roots(5, 12, -9)
    assert r1 * r2 == p
    key = {F(9, 5): "A", F(-12, 5): "B", F(-9, 5): "C", F(12, 5): "D"}[p]
    return {"answer": key, "computed": str(p)}


def q_f3c2_028():
    a, b, c = 3, -7, 2
    s, p = root_sum(a, b, c), root_product(a, b, c)
    value = s / p
    r1, r2 = quad_roots(a, b, c)
    assert 1 / r1 + 1 / r2 == value
    key = {F(2, 7): "A", F(3, 7): "B", F(7, 3): "C", F(7, 2): "D"}[value]
    return {"answer": key, "computed": str(value)}


def q_f3c2_029():
    r1, r2 = F(5), F(-2)
    # x^2 - (sum)x + (product) = 0, quoted as the coefficient triple.
    eq = (1, -(r1 + r2), r1 * r2)
    key = {
        (1, F(-3), F(-10)): "A",
        (1, F(3), F(-10)): "B",
        (1, F(-3), F(10)): "C",
        (1, F(3), F(10)): "D",
    }[eq]
    return {"answer": key, "computed": "x^2 + (%s)x + (%s) = 0" % (eq[1], eq[2])}


def q_f3c2_030():
    r1, r2 = F(2, 3), F(-1, 4)
    s, p = r1 + r2, r1 * r2
    scale = 12  # the LCM that clears both denominators
    eq = (scale, -s * scale, p * scale)
    assert all(v.denominator == 1 for v in eq[1:])
    key = {
        (12, F(5), F(-2)): "A",
        (12, F(-5), F(-2)): "B",
        (12, F(-5), F(2)): "C",
        (12, F(5), F(2)): "D",
    }[eq]
    return {"answer": key, "computed": "(%s)x^2 + (%s)x + (%s) = 0" % eq}


def q_f3c2_031():
    # One root 3 - sqrt(5); rational coefficients force the conjugate 3 + sqrt(5).
    rational_part, surd = 3, 5
    s = 2 * rational_part
    p = rational_part * rational_part - surd  # difference of two squares
    eq = (1, -s, p)
    # Cross-check numerically against the surd itself.
    r = rational_part - math.sqrt(surd)
    assert abs(eq[0] * r * r + eq[1] * r + eq[2]) < TOL
    key = {(1, -6, -4): "A", (1, 6, 4): "B", (1, -6, 4): "C", "irrational": "D"}[eq]
    return {"answer": key, "computed": "x^2 + (%s)x + (%s) = 0" % (eq[1], eq[2])}


def q_f3c2_032():
    a, b, c = 1, -5, 6
    k = 3
    s, p = root_sum(a, b, c), root_product(a, b, c)
    new = (1, -(k * s), k * k * p)
    r1, r2 = quad_roots(a, b, c)
    assert k * r1 + k * r2 == k * s and (k * r1) * (k * r2) == k * k * p
    key = {
        (1, F(-15), F(18)): "A",
        (1, F(-5), F(54)): "B",
        (1, F(-15), F(6)): "C",
        (1, F(-15), F(54)): "D",
    }[new]
    return {"answer": key, "computed": "x^2 + (%s)x + (%s) = 0" % (new[1], new[2])}


def q_f3c2_033():
    a, b, c = 1, -8, 5
    s, p = root_sum(a, b, c), root_product(a, b, c)
    value = s * s - 2 * p
    key = {F(54): "A", F(64): "B", F(74): "C", F(59): "D"}[value]
    return {"answer": key, "computed": str(value)}


def q_f3c2_034():
    a, b, c = 1, -7, 12
    s, p = root_sum(a, b, c), root_product(a, b, c)
    value = s ** 3 - 3 * p * s
    r1, r2 = quad_roots(a, b, c)
    assert r1 ** 3 + r2 ** 3 == value
    key = {F(343): "A", F(91): "B", F(595): "C", F(307): "D"}[value]
    return {"answer": key, "computed": str(value)}


def q_f3c2_035():
    a, b, c = 2, -9, 4
    s, p = root_sum(a, b, c), root_product(a, b, c)
    sq = s * s - 4 * p
    num = math.isqrt(sq.numerator)
    den = math.isqrt(sq.denominator)
    assert num * num == sq.numerator and den * den == sq.denominator
    value = F(num, den)
    r1, r2 = quad_roots(a, b, c)
    assert abs(r2 - r1) == value
    key = {F(65, 4): "A", F(7, 4): "B", F(7, 2): "C", F(49, 4): "D"}[value]
    return {"answer": key, "computed": str(value)}


def q_f3c2_036():
    a, b, c = 1, -6, 4
    s, p = root_sum(a, b, c), root_product(a, b, c)
    value = (s * s - 2 * p) / p
    key = {F(9): "A", F(28): "B", F(2): "C", F(7): "D"}[value]
    return {"answer": key, "computed": str(value)}


# ------------------------------------- SS 15-16 reducible forms and the cubic


def q_f3c2_037():
    # x^4 - 10x^2 + 9 = 0 under y = x^2.
    ys = quad_roots(1, -10, 9)
    xs = []
    for y in ys:
        if y > 0:
            r = math.isqrt(int(y))
            assert r * r == y
            xs.extend([F(-r), F(r)])
        elif y == 0:
            xs.append(F(0))
    xs = tuple(sorted(set(xs)))
    key = {
        (F(-3), F(-1), F(1), F(3)): "A",
        (F(1), F(9)): "B",
        (F(1), F(3)): "C",
        (F(-3), F(3)): "D",
    }[xs]
    return {"answer": key, "computed": str([str(v) for v in xs])}


def q_f3c2_038():
    # sqrt(x + 12) = x; square, then test every candidate in the ORIGINAL.
    candidates = quad_roots(1, -1, -12)
    genuine = tuple(
        c for c in candidates if c + 12 >= 0 and abs(math.sqrt(float(c) + 12) - float(c)) < TOL
    )
    key = {
        (F(-3), F(4)): "A",
        (F(4),): "B",
        (F(-3),): "C",
        (): "D",
    }[genuine]
    return {"answer": key, "computed": "candidates %s, genuine %s" % (
        [str(v) for v in candidates], [str(v) for v in genuine])}


def q_f3c2_039():
    # (x^2 - 3x)^2 - 2(x^2 - 3x) - 8 = 0; substitute y = x^2 - 3x.
    ys = quad_roots(1, -2, -8)
    xs = []
    for y in ys:
        r = quad_roots(1, -3, -y)  # x^2 - 3x - y = 0
        if r:
            xs.extend(r)
    xs = sorted(set(xs))
    total = sum(xs)
    key = {F(2): "A", F(3): "B", F(6): "C", F(8): "D"}[total]
    return {"answer": key, "computed": "roots %s, sum %s" % ([str(v) for v in xs], total)}


def q_f3c2_040():
    # x + 1/x = 10/3  ->  3x^2 - 10x + 3 = 0.
    y = F(10, 3)
    a, b, c = y.denominator, -y.numerator, y.denominator
    roots = quad_roots(a, b, c)
    assert roots[0] * roots[1] == 1  # the reciprocal pattern always gives this
    key = {
        (F(3),): "A",
        (F(1), F(10, 3)): "B",
        (F(-1, 3), F(3)): "C",
        (F(1, 3), F(3)): "D",
    }[roots]
    return {"answer": key, "computed": "%s, %s" % roots}


def cubic_roots(a, b, c, d):
    """Find one rational root by trial over factors of d/a, then factorise."""
    def value(x):
        return a * x ** 3 + b * x ** 2 + c * x + d

    da = [n for n in range(1, abs(a) + 1) if a % n == 0]
    dd = [n for n in range(1, abs(d) + 1) if d % n == 0]
    cands = sorted({F(s * p, q) for p in dd for q in da for s in (1, -1)})
    first = next(x for x in cands if value(x) == 0)
    # Divide out (x - first): a x^2 + (b + a*first) x + (c + first*(b + a*first))
    b2 = b + a * first
    c2 = c + first * b2
    assert d + first * c2 == 0, "the division must leave no remainder"
    rest = quad_roots(a, b2, c2)
    roots = [first] + (list(rest) if rest else [])
    return sorted(roots)


def q_f3c2_041():
    roots = tuple(cubic_roots(1, -4, 1, 6))
    key = {
        (F(-1), F(2), F(3)): "A",
        (F(1), F(2), F(3)): "B",
        (F(-3), F(-2), F(-1)): "C",
        (F(-3), F(-2), F(1)): "D",
    }[roots]
    return {"answer": key, "computed": str([str(v) for v in roots])}


def q_f3c2_042():
    a, b, c, d = 2, -5, -4, 3
    s = F(-b, a)
    key = {F(-5, 2): "A", F(5, 2): "B", F(-3, 2): "C", F(-2): "D"}[s]
    return {"answer": key, "computed": str(s)}


def q_f3c2_043():
    a, b, c, d = 1, -6, 11, -6
    product = F(-d, a)
    assert math.prod(cubic_roots(a, b, c, d)) == product
    key = {F(-6): "A", F(11): "B", F(6): "C", F(1): "D"}[product]
    return {"answer": key, "computed": str(product)}


# ---------------------------------------------- S 17 business applications


def break_even(fixed, price, variable):
    """Exact break-even quantity: fixed cost over contribution per unit."""
    return F(fixed, price - variable)


def q_f3c2_044():
    q = break_even(480_000, 420, 260)
    key = {F(1143): "A", F(1846): "B", F(706): "C", F(3000): "D"}[q]
    return {"answer": key, "computed": str(q)}


def q_f3c2_045():
    fixed, price, variable, target = 480_000, 420, 260, 240_000
    q = F(fixed + target, price - variable)
    key = {F(4500): "A", F(1500): "B", F(3000): "C", F(1714): "D"}[q]
    return {"answer": key, "computed": str(q)}


def q_f3c2_046():
    # demand q = 640 - 8p, supply q = 12p - 160.
    p = F(640 + 160, 8 + 12)
    q_demand = 640 - 8 * p
    q_supply = 12 * p - 160
    assert q_demand == q_supply
    key = {F(40): "A", F(320): "B", F(448): "C", F(800): "D"}[q_demand]
    return {"answer": key, "computed": "p=%s, q=%s" % (p, q_demand)}


def q_f3c2_047():
    # x + y = 60 and 320x + 440y = 400 * 60.
    total, r1, r2, blend = 60, 320, 440, 400
    x, y = solve_linear_pair(1, 1, total, r1, r2, blend * total)
    assert r1 * x + r2 * y == blend * total
    key = {F(40): "A", F(30): "B", F(20): "C", F(25): "D"}[x]
    return {"answer": key, "computed": "cheap=%s, dear=%s" % (x, y)}


def q_f3c2_048():
    a, b = 15, 10
    t = 1 / (F(1, a) + F(1, b))
    key = {F(25): "A", F(25, 2): "B", F(5): "C", F(6): "D"}[t]
    return {"answer": key, "computed": str(t)}


def q_f3c2_049():
    # 10t + u = 4(t + u) and (10u + t) - (10t + u) = 27.
    hits = [
        10 * t + u
        for t in range(1, 10)
        for u in range(0, 10)
        if 10 * t + u == 4 * (t + u) and (10 * u + t) - (10 * t + u) == 27
    ]
    assert len(hits) == 1
    key = {36: "A", 63: "B", 24: "C", 48: "D"}[hits[0]]
    return {"answer": key, "computed": hits[0]}


def q_f3c2_050():
    # mother = 4 * daughter, and mother + 12 = 2 * (daughter + 12).
    # 4d + 12 = 2d + 24  ->  2d = 12
    d = F(2 * 12 - 12, 4 - 2)
    mother = 4 * d
    assert mother + 12 == 2 * (d + 12)
    key = {F(6): "A", F(24): "B", F(48): "C", F(36): "D"}[mother]
    return {"answer": key, "computed": "daughter=%s, mother=%s" % (d, mother)}


# ------------------------------------------------------------- case scenarios

# cs-01: Suvarna Ceramics, per quarter.
OLD_FIXED, OLD_VAR, PRICE = 720_000, 340, 580
NEW_FIXED, NEW_VAR = 1_152_000, 220


def cs_f3c2_01_a():
    q = break_even(OLD_FIXED, PRICE, OLD_VAR)
    key = {F(3000): "A", F(2118): "B", F(1241): "C", F(783): "D"}[q]
    return {"answer": key, "computed": str(q)}


def cs_f3c2_01_b():
    q = F(OLD_FIXED + 360_000, PRICE - OLD_VAR)
    key = {F(1500): "A", F(4500): "B", F(3000): "C", F(1862): "D"}[q]
    return {"answer": key, "computed": str(q)}


def cs_f3c2_01_c():
    q = break_even(NEW_FIXED, PRICE, NEW_VAR)
    key = {F(2000): "A", F(5236): "B", F(3200): "C", F(4800): "D"}[q]
    return {"answer": key, "computed": str(q)}


def cs_f3c2_01_d():
    # OLD_FIXED + OLD_VAR*x = NEW_FIXED + NEW_VAR*x
    x = F(NEW_FIXED - OLD_FIXED, OLD_VAR - NEW_VAR)
    assert OLD_FIXED + OLD_VAR * x == NEW_FIXED + NEW_VAR * x
    key = {F(3200): "A", F(3000): "B", F(771): "C", F(3600): "D"}[x]
    return {"answer": key, "computed": str(x)}


def cs_f3c2_02_a():
    # P = -x^2 + 24x - 108 = 0  ->  x^2 - 24x + 108 = 0
    roots = quad_roots(1, -24, 108)
    key = {
        (F(6), F(12)): "A",
        (F(-18), F(-6)): "B",
        (F(6), F(18)): "C",
        (F(12), F(18)): "D",
    }[roots]
    return {"answer": key, "computed": "%s, %s" % roots}


def cs_f3c2_02_b():
    a, b, c = 1, -24, 108
    pair = (root_sum(a, b, c), root_product(a, b, c))
    key = {
        (F(-24), F(108)): "A",
        (F(24), F(-108)): "B",
        (F(108), F(24)): "C",
        (F(24), F(108)): "D",
    }[pair]
    return {"answer": key, "computed": "sum=%s, product=%s" % pair}


def cs_f3c2_02_c():
    a, b, c = 1, -24, 108
    s, p = root_sum(a, b, c), root_product(a, b, c)
    value = s * s - 2 * p
    key = {F(576): "A", F(360): "B", F(792): "C", F(468): "D"}[value]
    return {"answer": key, "computed": str(value)}


# cs-03: the three canteen bills, as (idli, dosa, coffee, total).
CANTEEN = [(4, 2, 3, 310), (2, 5, 1, 380), (3, 1, 4, 255)]


def cs_f3c2_03_a():
    idli, dosa, coffee = solve_linear_triple(CANTEEN)
    for a, b, c, total in CANTEEN:
        assert a * idli + b * dosa + c * coffee == total
    key = {F(60): "A", F(25): "B", F(30): "C", F(115): "D"}[dosa]
    return {"answer": key, "computed": "idli=%s, dosa=%s, coffee=%s" % (idli, dosa, coffee)}


def cs_f3c2_03_b():
    idli, dosa, coffee = solve_linear_triple(CANTEEN)
    bill = 3 * idli + 2 * dosa + 1 * coffee
    key = {F(235): "A", F(260): "B", F(225): "C", F(115): "D"}[bill]
    return {"answer": key, "computed": str(bill)}
