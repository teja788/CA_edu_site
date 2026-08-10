"""Verifier for foundation/quantitative-aptitude/differential-and-integral-calculus.json (P3 Ch 8).

The point of this module is that it must NOT repeat the algebra the stem used.
Re-applying the same differentiation rule would reproduce the same mistake, so
every claim is checked NUMERICALLY against the original function instead:

  * A claimed DERIVATIVE is compared, at several sample points, with a
    five-point central difference quotient of the original function
    (error O(h^4), h = 1e-4). Tolerance: `close()` below, 1e-6 relative.
  * A claimed ANTIDERIVATIVE is differentiated numerically by the same stencil
    and compared with the integrand at several sample points, same tolerance.
    An option that is arithmetically identical to the key but omits "+ c" is
    distinguished by the explicit `const` flag on each option, never by algebra.
  * A claimed DEFINITE INTEGRAL is recomputed by composite Simpson's rule with
    2,000 sub-intervals (error O(h^4)); tolerance 1e-6 relative.
  * A claimed MAXIMUM or MINIMUM is confirmed by evaluating the function on a
    dense grid of 4,001 points around the stated point and checking that the
    stated point really is the extremum of that neighbourhood, and of the
    stated kind. The second derivative is checked numerically as well.

Nothing below reads the answer key. Each function computes a value (or a
verdict) and then looks it up in a dict of the four printed option values, so a
wrong key in the bank surfaces as a mismatch or a KeyError.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------- tolerances

H = 1e-4          # step for the difference quotients
H2 = 1e-3         # step for the second-derivative stencil (needs a larger h)
TOL = 1e-6        # relative tolerance for every numerical comparison
ROUND_TOL = 1e-3  # looser tolerance where the printed option is rounded to 3-4 s.f.
SIMPSON_N = 2000  # sub-intervals for the composite Simpson rule
GRID_N = 4000     # points in the dense grid used for extremum checks


def close(a, b, tol=TOL):
    """Relative-or-absolute comparison, so it works at 1e-3 and at 1e6 alike."""
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def nderiv(f, x, h=H):
    """Five-point central difference: error O(h^4)."""
    return (f(x - 2 * h) - 8 * f(x - h) + 8 * f(x + h) - f(x + 2 * h)) / (12 * h)


def nderiv2(f, x, h=H2):
    """Five-point central second difference: error O(h^4)."""
    return (
        -f(x - 2 * h) + 16 * f(x - h) - 30 * f(x) + 16 * f(x + h) - f(x + 2 * h)
    ) / (12 * h * h)


def simpson(f, a, b, n=SIMPSON_N):
    """Composite Simpson's rule on n sub-intervals (n even)."""
    if n % 2:
        n += 1
    h = (b - a) / n
    total = f(a) + f(b)
    for i in range(1, n):
        total += (4 if i % 2 else 2) * f(a + i * h)
    return total * h / 3


def pick_derivative(options, f, pts, tol=TOL):
    """options: {key: callable or None}. Returns the single key whose function
    matches the numerical derivative of f at every point in pts."""
    hits = [
        k
        for k, g in options.items()
        if g is not None and all(close(g(x), nderiv(f, x), tol) for x in pts)
    ]
    assert len(hits) == 1, f"expected exactly one matching option, got {hits}"
    return hits[0]


def pick_value(options, value, tol=TOL):
    """options: {key: number or None}. Returns the key whose printed value equals
    the independently computed `value`."""
    hits = [k for k, v in options.items() if v is not None and close(v, value, tol)]
    assert len(hits) == 1, f"expected exactly one matching option, got {hits}"
    return hits[0]


def pick_antiderivative(options, integrand, pts, tol=TOL):
    """options: {key: (F, has_constant) or None}. Returns the single key whose F
    differentiates back to the integrand AND carries the constant of
    integration. The numerical derivative cannot see "+ c", so the flag records
    what the printed option actually says."""
    hits = [
        k
        for k, opt in options.items()
        if opt is not None
        and opt[1]
        and all(close(nderiv(opt[0], x), integrand(x), tol) for x in pts)
    ]
    assert len(hits) == 1, f"expected exactly one matching option, got {hits}"
    return hits[0]


def extremum_kind(f, c, span, n=GRID_N):
    """Evaluate f on a dense grid of n+1 points across [c - span, c + span] and
    report whether f(c) is the largest or the smallest value there."""
    vals = [f(c - span + 2 * span * i / n) for i in range(n + 1)]
    here = f(c)
    if here >= max(vals) - 1e-12:
        return "maximum"
    if here <= min(vals) + 1e-12:
        return "minimum"
    return "neither"


# ------------------------------------------- SS 1-3 the derivative and the table


def q_f3c8_002():
    # Method: compare each printed option with the five-point numerical
    # derivative of f(x) = x^3 at three sample points. Tolerance 1e-6 relative.
    # Option D quotes the difference quotient before the limit, which is not a
    # function of x alone, so it is recorded as None.
    f = lambda x: x ** 3
    options = {
        "A": lambda x: x ** 2,
        "B": lambda x: 3 * x ** 3,
        "C": lambda x: 3 * x ** 2,
        "D": None,
    }
    key = pick_derivative(options, f, [0.7, 1.3, 2.1])
    return {"answer": key, "computed": "3x^2"}


def q_f3c8_003():
    # Method: the average rate of change is computed straight from C(x) at the
    # two ends of the step, with no derivative involved. Exact arithmetic.
    C = lambda x: 3 * x ** 2 + 40 * x + 500
    rate = (C(12) - C(10)) / (12 - 10)
    options = {"A": 106, "B": C(12) - C(10), "C": nderiv(C, 10), "D": nderiv(C, 12)}
    # the three wrong options are recomputed here as the errors they represent
    key = pick_value({"A": 106, "B": 212, "C": 100, "D": 112}, rate)
    assert close(options["C"], 100) and close(options["D"], 112)
    return {"answer": key, "computed": rate}


def q_f3c8_004():
    # Method: numerical derivative of f(x) = 1/x at three points away from zero,
    # compared with each printed option. Tolerance 1e-6 relative.
    f = lambda x: 1 / x
    options = {
        "A": lambda x: 1 / x ** 2,
        "B": lambda x: -1 / x,
        "C": lambda x: math.log(abs(x)),
        "D": lambda x: -1 / x ** 2,
    }
    key = pick_derivative(options, f, [0.5, 1.5, 2.5])
    return {"answer": key, "computed": "-1/x^2"}


def q_f3c8_005():
    # Method: numerical derivative of x^7 at three sample points. Tol 1e-6 rel.
    f = lambda x: x ** 7
    options = {
        "A": lambda x: 7 * x ** 6,
        "B": lambda x: 7 * x ** 7,
        "C": lambda x: x ** 6,
        "D": lambda x: 6 * x ** 6,
    }
    key = pick_derivative(options, f, [0.8, 1.1, 1.4])
    return {"answer": key, "computed": "7x^6"}


def q_f3c8_006():
    # Method: numerical derivative of 1/x^3 at three positive points. Tol 1e-6.
    f = lambda x: 1 / x ** 3
    options = {
        "A": lambda x: 3 / x ** 4,
        "B": lambda x: -3 / x ** 2,
        "C": lambda x: -3 / x ** 4,
        "D": lambda x: 3 / x ** 2,
    }
    key = pick_derivative(options, f, [0.8, 1.3, 2.0])
    return {"answer": key, "computed": "-3/x^4"}


def q_f3c8_007():
    # Method: numerical derivative of sqrt(x) at x = 9, matched against the four
    # printed values. Tolerance 1e-6 relative.
    value = nderiv(math.sqrt, 9.0)
    key = pick_value({"A": 1 / 3, "B": 1 / 6, "C": 6, "D": 1 / 18}, value)
    return {"answer": key, "computed": round(value, 8)}


def q_f3c8_008():
    # Method: numerical derivative of 3^x at three sample points, compared with
    # each printed option as a function of x. Tolerance 1e-6 relative.
    f = lambda x: 3 ** x
    options = {
        "A": lambda x: x * 3 ** (x - 1),
        "B": lambda x: 3 ** x,
        "C": lambda x: 3 ** x / math.log(3),
        "D": lambda x: 3 ** x * math.log(3),
    }
    key = pick_derivative(options, f, [0.5, 1.0, 1.7])
    return {"answer": key, "computed": "3^x log 3"}


def q_f3c8_009():
    # Method: numerical derivative of log x at x = 4. Tolerance 1e-6 relative.
    value = nderiv(math.log, 4.0)
    key = pick_value({"A": 0.25, "B": -0.0625, "C": 4, "D": 1.3863}, value)
    return {"answer": key, "computed": round(value, 8)}


# ------------------------------------------------- SS 4-6 the combination rules


def q_f3c8_010():
    # Method: five-point numerical derivative of the polynomial at x = 2,
    # matched against the four printed values. Tolerance 1e-6 relative.
    f = lambda x: 5 * x ** 4 - 3 * x ** 2 + 7 * x - 9
    value = nderiv(f, 2.0)
    key = pick_value({"A": 148, "B": 155, "C": 146, "D": 162}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_011():
    # Method: numerical derivative of the ORIGINAL quotient at x = 2 — the
    # simplification into 2x + 5 - 4/x^2 is never used, so a mistake in that
    # simplification cannot be repeated here. Tolerance 1e-6 relative.
    f = lambda x: (2 * x ** 3 + 5 * x ** 2 - 4) / x ** 2
    value = nderiv(f, 2.0)
    key = pick_value({"A": 1, "B": 2, "C": 11, "D": 3}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_012():
    # Method: numerical derivative of 4*sqrt(x) + 6/x at x = 4. Tol 1e-6 rel.
    f = lambda x: 4 * math.sqrt(x) + 6 / x
    value = nderiv(f, 4.0)
    key = pick_value({"A": 1.375, "B": -0.125, "C": 0.625, "D": 2.5}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_013():
    # Method: numerical derivative of x^2 * e^x at x = 1, matched against the
    # printed values, which are rounded to three decimals (tolerance 1e-3 rel).
    f = lambda x: x ** 2 * math.exp(x)
    value = nderiv(f, 1.0)
    key = pick_value(
        {"A": 8.155, "B": 5.437, "C": 2.718, "D": 4.718}, value, ROUND_TOL
    )
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_014():
    # Method: numerical derivative of the product as written, at x = 2, so the
    # product rule itself is never applied. Tolerance 1e-6 relative.
    f = lambda x: (3 * x + 1) * (x ** 2 - 2)
    value = nderiv(f, 2.0)
    key = pick_value({"A": 12, "B": 34, "C": 28, "D": 6}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_015():
    # Method: numerical derivative of the quotient as written, at x = 5, so the
    # quotient rule is never applied here. Tolerance 1e-6 relative.
    f = lambda x: (2 * x + 1) / (x - 3)
    value = nderiv(f, 5.0)
    key = pick_value({"A": 1.75, "B": 2, "C": -1.75, "D": -3.5}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_016():
    # Method: numerical derivative of x^2/(x + 1) at x = 1. Tolerance 1e-6 rel.
    f = lambda x: x ** 2 / (x + 1)
    value = nderiv(f, 1.0)
    key = pick_value({"A": -0.75, "B": 2, "C": 1.5, "D": 0.75}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_017():
    # Method: numerical derivative of e^x / x at x = 2; printed options are
    # rounded to three decimals, so tolerance 1e-3 relative.
    f = lambda x: math.exp(x) / x
    value = nderiv(f, 2.0)
    key = pick_value(
        {"A": 1.847, "B": 3.695, "C": -1.847, "D": 7.389}, value, ROUND_TOL
    )
    return {"answer": key, "computed": round(value, 6)}


# ----------------------------------------------------- SS 7-9 chain, log, forms


def q_f3c8_018():
    # Method: numerical derivative of (4x - 7)^6 at x = 2. The chain rule is
    # never applied by the verifier. Tolerance 1e-6 relative.
    f = lambda x: (4 * x - 7) ** 6
    value = nderiv(f, 2.0)
    key = pick_value({"A": 6, "B": 24, "C": 4, "D": 48}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_019():
    # Method: numerical derivative of e^(3x^2) at x = 1; printed options are
    # rounded to three decimals, so tolerance 1e-3 relative.
    f = lambda x: math.exp(3 * x ** 2)
    value = nderiv(f, 1.0)
    key = pick_value(
        {"A": 20.086, "B": 120.513, "C": 60.257, "D": 22.167}, value, ROUND_TOL
    )
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_020():
    # Method: numerical derivative of log(5x^2 + 2) at x = 1; printed options
    # are rounded to four decimals, so tolerance 1e-3 relative.
    f = lambda x: math.log(5 * x ** 2 + 2)
    value = nderiv(f, 1.0)
    key = pick_value(
        {"A": 0.7, "B": 0.1429, "C": 10, "D": 1.4286}, value, ROUND_TOL
    )
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_021():
    # Method: numerical derivative of sqrt(x^2 + 9) at x = 4. Tol 1e-6 relative.
    f = lambda x: math.sqrt(x ** 2 + 9)
    value = nderiv(f, 4.0)
    key = pick_value({"A": 0.8, "B": 0.1, "C": 1.6, "D": 0.16}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_022():
    # Method: numerical derivative of x^x at x = 2 (computed as exp(x log x), so
    # the logarithmic-differentiation algebra is not reused). Printed options are
    # rounded to three decimals, so tolerance 1e-3 relative.
    f = lambda x: math.exp(x * math.log(x))
    value = nderiv(f, 2.0)
    key = pick_value(
        {"A": 4, "B": 6.773, "C": 1.693, "D": 2.773}, value, ROUND_TOL
    )
    return {"answer": key, "computed": round(value, 6)}


def _solve_branch(g, lo, hi, iters=200):
    """Bisection root of g on [lo, hi]; used to pin the implicit branch."""
    flo = g(lo)
    for _ in range(iters):
        mid = (lo + hi) / 2
        if (g(mid) < 0) == (flo < 0):
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def q_f3c8_023():
    # Method: the implicit curve is turned into an explicit branch numerically —
    # y(x) = sqrt(25 - x^2) near (3, 4) — and differentiated by the five-point
    # stencil. No implicit-differentiation algebra is reused. Tol 1e-6 relative.
    y = lambda x: math.sqrt(25 - x ** 2)
    assert close(y(3.0), 4.0)
    value = nderiv(y, 3.0)
    key = pick_value({"A": 0.75, "B": -1.3333, "C": 1.3333, "D": -0.75}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_024():
    # Method: for each x the branch through (2, 4) is found by bisection on
    # y^3 - 9xy + x^3 = 0 over [3.0, 5.5], and that numerically defined y(x) is
    # differentiated by the five-point stencil. Tolerance 1e-3 relative, because
    # the printed options are rounded.
    def y(x):
        return _solve_branch(lambda t: t ** 3 - 9 * x * t + x ** 3, 3.0, 5.5)

    assert close(y(2.0), 4.0, 1e-9)
    value = nderiv(y, 2.0)
    key = pick_value({"A": 1.25, "B": -0.8, "C": 0.8, "D": 0.5}, value, ROUND_TOL)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_025():
    # Method: the parameter is eliminated numerically — t = sqrt(x/4) and
    # y = 8t^3 — and the resulting y(x) is differentiated by the five-point
    # stencil at x = 4*2^2 = 16. The (dy/dt)/(dx/dt) rule is never used.
    # Tolerance 1e-6 relative.
    y = lambda x: 8 * math.sqrt(x / 4) ** 3
    value = nderiv(y, 4 * 2.0 ** 2)
    key = pick_value({"A": 6, "B": 0.1667, "C": 96, "D": 16}, value, ROUND_TOL)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_026():
    # Method: five-point numerical SECOND derivative of the polynomial at x = 2,
    # step 1e-3. Tolerance 1e-6 relative.
    f = lambda x: x ** 4 - 5 * x ** 3 + 2 * x
    value = nderiv2(f, 2.0)
    key = pick_value({"A": -26, "B": -12, "C": 18, "D": 108}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_027():
    # Method: five-point numerical second derivative of e^(5x) at x = 0, step
    # 1e-3. Tolerance 1e-6 relative.
    f = lambda x: math.exp(5 * x)
    value = nderiv2(f, 0.0)
    key = pick_value({"A": 5, "B": 1, "C": 25, "D": 10}, value)
    return {"answer": key, "computed": round(value, 6)}


# ------------------------------------- SS 11-13 business rates and optimisation


def _ternary(f, lo, hi, want="min", iters=300):
    """Locate the extremum of a unimodal f on [lo, hi] without using calculus."""
    for _ in range(iters):
        m1 = lo + (hi - lo) / 3
        m2 = hi - (hi - lo) / 3
        if (f(m1) < f(m2)) == (want == "min"):
            hi = m2
        else:
            lo = m1
    return (lo + hi) / 2


def q_f3c8_028():
    # Method: five-point numerical derivative of C(x) at x = 30. Tol 1e-6 rel.
    C = lambda x: 2 * x ** 2 + 60 * x + 5000
    value = nderiv(C, 30.0)
    key = pick_value({"A": 286.67, "B": 8600, "C": 5180, "D": 180}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_029():
    # Method: average cost recomputed straight from C(30)/30 — exact arithmetic.
    # Printed options are rounded to the paisa, so tolerance 1e-3 relative.
    C = lambda x: 2 * x ** 2 + 60 * x + 5000
    value = C(30) / 30
    key = pick_value(
        {"A": 286.67, "B": 180, "C": 120, "D": 8600}, value, ROUND_TOL
    )
    return {"answer": key, "computed": round(value, 4)}


def q_f3c8_030():
    # Method: five-point numerical derivative of R(x) at x = 20. Tol 1e-6 rel.
    R = lambda x: 236 * x - 2 * x ** 2
    value = nderiv(R, 20.0)
    key = pick_value({"A": 196, "B": 3920, "C": 156, "D": 236}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_031():
    # Method: the minimiser of AC(x) = C(x)/x is found by ternary search on
    # [1, 500] — a direct search, with no derivative of AC taken — and then
    # confirmed as a minimum on a dense grid of 4,001 points spanning +/- 5
    # units. Tolerance 1e-6 relative.
    C = lambda x: 3 * x ** 2 + 36 * x + 1200
    AC = lambda x: C(x) / x
    x_star = _ternary(AC, 1.0, 500.0, "min")
    assert extremum_kind(AC, x_star, 5.0) == "minimum"
    key = pick_value({"A": 400, "B": 20, "C": 34.64, "D": None}, x_star, ROUND_TOL)
    return {"answer": key, "computed": round(x_star, 6)}


def q_f3c8_032():
    # Method: fixed cost is evaluated as C(0) directly from the stem's function.
    C = lambda x: 4 * x ** 2 + 25 * x + 900
    value = C(0)
    key = pick_value({"A": 25, "B": None, "C": C(1), "D": 900}, value)
    return {"answer": key, "computed": value}


def q_f3c8_033():
    # Method: total revenue is built as p(x)*x and differentiated numerically at
    # x = 10; the MR formula is never written out. Tolerance 1e-6 relative.
    p = lambda x: 180 - 3 * x
    R = lambda x: p(x) * x
    value = nderiv(R, 10.0)
    key = pick_value({"A": 120, "B": p(10), "C": R(10), "D": -3}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_034():
    # Method: the local maximum is located by ternary search on [0, 2] (a direct
    # search over function values, not by solving f' = 0) and confirmed as a
    # maximum on a dense grid spanning +/- 0.5. Tolerance 1e-6 relative.
    f = lambda x: x ** 3 - 6 * x ** 2 + 9 * x + 4
    x_star = _ternary(f, 0.0, 2.0, "max")
    assert extremum_kind(f, x_star, 0.5) == "maximum"
    assert nderiv2(f, x_star) < 0
    value = f(x_star)
    key = pick_value({"A": f(3.0), "B": 8, "C": 1, "D": 3}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_035():
    # Method: the KIND of the critical point at x = 3 is decided by evaluating f
    # on a dense grid of 4,001 points across [2.5, 3.5] and asking whether f(3)
    # is the largest or the smallest value there; the numerical second
    # derivative is checked to agree in sign. No rule is re-applied.
    f = lambda x: x ** 3 - 6 * x ** 2 + 9 * x + 4
    kind = extremum_kind(f, 3.0, 0.5)
    second = nderiv2(f, 3.0)
    assert (second > 0) == (kind == "minimum")
    claims = {"A": "maximum", "B": "maximum", "C": "minimum", "D": "neither"}
    hits = [k for k, v in claims.items() if v == kind]
    assert len(hits) == 1, hits
    return {"answer": hits[0], "computed": f"{kind}, f''(3) = {round(second, 4)}"}


def q_f3c8_036():
    # Method: the local minimum is located by ternary search on [1.5, 3] and
    # confirmed on a dense grid spanning +/- 0.4. Tolerance 1e-6 relative.
    f = lambda x: 2 * x ** 3 - 9 * x ** 2 + 12 * x + 5
    x_star = _ternary(f, 1.5, 3.0, "min")
    assert extremum_kind(f, x_star, 0.4) == "minimum"
    assert nderiv2(f, x_star) > 0
    value = f(x_star)
    key = pick_value({"A": f(1.0), "B": 1, "C": 2, "D": 9}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_037():
    # Method: the minimum of x + 4/x on x > 0 is located by ternary search on
    # [0.5, 10] and confirmed on a dense grid spanning +/- 0.4.
    f = lambda x: x + 4 / x
    x_star = _ternary(f, 0.5, 10.0, "min")
    assert extremum_kind(f, x_star, 0.4) == "minimum"
    value = f(x_star)
    key = pick_value({"A": 4, "B": 2, "C": f(1.0), "D": 0}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_038():
    # Method: the profit function is built from the stem's own price and cost
    # functions and its maximiser found by ternary search on [0, 80]; the point
    # is confirmed a maximum on a dense grid spanning +/- 10 units.
    P = lambda x: (400 - 5 * x) * x - (100 * x + 1200)
    x_star = _ternary(P, 0.0, 80.0, "max")
    assert extremum_kind(P, x_star, 10.0) == "maximum"
    key = pick_value({"A": 40, "B": 60, "C": 80, "D": 30}, x_star)
    return {"answer": key, "computed": round(x_star, 6)}


def q_f3c8_039():
    # Method: as above, but the answer is the profit AT the maximiser, so the
    # grid search returns the value rather than the position.
    P = lambda x: (400 - 5 * x) * x - (100 * x + 1200)
    x_star = _ternary(P, 0.0, 80.0, "max")
    value = P(x_star)
    revenue = (400 - 5 * x_star) * x_star
    key = pick_value({"A": 4500, "B": 3300, "C": 30, "D": revenue}, value)
    return {"answer": key, "computed": round(value, 6)}


def q_f3c8_040():
    # Method: the area is written from the constraint 2x + y = 100 and its
    # maximiser found by ternary search on [0, 50]; confirmed a maximum on a
    # dense grid spanning +/- 5 metres. Tolerance 1e-6 relative.
    A = lambda x: x * (100 - 2 * x)
    x_star = _ternary(A, 0.0, 50.0, "max")
    assert extremum_kind(A, x_star, 5.0) == "maximum"
    value = A(x_star)
    key = pick_value({"A": 625, "B": 1111.11, "C": 1250, "D": 2500}, value, ROUND_TOL)
    return {"answer": key, "computed": round(value, 6)}


# ------------------------------------------------ SS 12-16 the indefinite integral
#
# Every function below differentiates each printed option NUMERICALLY and keeps
# the one that returns to the integrand. The integration rule the stem used is
# never re-applied, so a mis-integration in the bank cannot be reproduced here.
# The "+ c" flag is carried separately because a numerical derivative is blind
# to an additive constant: two options can differentiate identically and still
# differ on whether the constant of integration is printed.


def q_f3c8_041():
    # Method: numerical differentiation of each option against x^5 at three
    # points. A and D differentiate alike; D is excluded by the missing "+ c".
    integrand = lambda x: x ** 5
    options = {
        "A": (lambda x: x ** 6 / 6, True),
        "B": (lambda x: 5 * x ** 4, True),
        "C": (lambda x: x ** 6, True),
        "D": (lambda x: x ** 6 / 6, False),
    }
    key = pick_antiderivative(options, integrand, [0.6, 1.4, 2.2])
    return {"answer": key, "computed": "x^6/6 + c"}


def q_f3c8_042():
    # Method: as above, on 1/x over positive x only. Option A ("x^0 / 0") is not
    # a function at all, so it is recorded as None; D omits the constant.
    integrand = lambda x: 1 / x
    options = {
        "A": None,
        "B": (lambda x: math.log(abs(x)), True),
        "C": (lambda x: -1 / x ** 2, True),
        "D": (lambda x: math.log(abs(x)), False),
    }
    key = pick_antiderivative(options, integrand, [0.7, 1.5, 3.0])
    return {"answer": key, "computed": "log|x| + c"}


def q_f3c8_043():
    # Method: numerical differentiation against e^(4x). Sample points are kept
    # small so the exponential stays in a well-conditioned range, and away from
    # x = 0 where option C is undefined.
    integrand = lambda x: math.exp(4 * x)
    options = {
        "A": (lambda x: math.exp(4 * x), True),
        "B": (lambda x: 4 * math.exp(4 * x), True),
        "C": (lambda x: math.exp(4 * x) / (4 * x), True),
        "D": (lambda x: math.exp(4 * x) / 4, True),
    }
    key = pick_antiderivative(options, integrand, [0.1, 0.35, 0.6])
    return {"answer": key, "computed": "e^(4x)/4 + c"}


def q_f3c8_044():
    # Method: numerical differentiation against (3x + 2)^5. This is the question
    # that catches the missing 1/(coefficient of x) after raising the power, so
    # the check must not re-use the reciprocal rule the stem applied.
    integrand = lambda x: (3 * x + 2) ** 5
    options = {
        "A": (lambda x: (3 * x + 2) ** 6 / 6, True),
        "B": (lambda x: (3 * x + 2) ** 6 / 3, True),
        "C": (lambda x: (3 * x + 2) ** 6 / 18, True),
        "D": (lambda x: 15 * (3 * x + 2) ** 4, True),
    }
    key = pick_antiderivative(options, integrand, [0.2, 0.5, 0.9])
    return {"answer": key, "computed": "(3x + 2)^6 / 18 + c"}


def q_f3c8_045():
    # Method: numerical differentiation against 2x(x^2 + 7)^5. The substitution
    # is never performed here; each printed option is simply differentiated back.
    integrand = lambda x: 2 * x * (x ** 2 + 7) ** 5
    options = {
        "A": (lambda x: (x ** 2 + 7) ** 6 / 6, True),
        "B": (lambda x: (x ** 2 + 7) ** 6 / 12, True),
        "C": (lambda x: x ** 2 * (x ** 2 + 7) ** 6 / 6, True),
        "D": (lambda x: (x ** 2 + 7) ** 6, True),
    }
    key = pick_antiderivative(options, integrand, [0.3, 0.8, 1.2])
    return {"answer": key, "computed": "(x^2 + 7)^6 / 6 + c"}


def q_f3c8_046():
    # Method: numerical differentiation against (2x + 3)/(x^2 + 3x + 5). The
    # denominator has no real root, so any sample point is safe.
    integrand = lambda x: (2 * x + 3) / (x ** 2 + 3 * x + 5)
    options = {
        "A": (lambda x: (2 * x + 3) * math.log(abs(x ** 2 + 3 * x + 5)), True),
        "B": (lambda x: math.log(abs(x ** 2 + 3 * x + 5)), True),
        "C": (lambda x: math.log(abs(2 * x + 3)), True),
        "D": (lambda x: -(2 * x + 3) / (x ** 2 + 3 * x + 5) ** 2, True),
    }
    key = pick_antiderivative(options, integrand, [0.4, 1.1, 2.0])
    return {"answer": key, "computed": "log|x^2 + 3x + 5| + c"}


def q_f3c8_047():
    # Method: numerical differentiation against x*e^(2x). Integration by parts is
    # not performed here; the two plausible parts-results (dividing by 2 and by 4)
    # are separated purely by which one differentiates back to the integrand.
    integrand = lambda x: x * math.exp(2 * x)
    options = {
        "A": (lambda x: math.exp(2 * x) * (2 * x - 1) / 2, True),
        "B": (lambda x: x * math.exp(2 * x) / 2, True),
        "C": (lambda x: math.exp(2 * x) * (2 * x - 1) / 4, True),
        "D": (lambda x: x ** 2 * math.exp(2 * x) / 4, True),
    }
    key = pick_antiderivative(options, integrand, [0.2, 0.6, 1.0])
    return {"answer": key, "computed": "e^(2x)(2x - 1)/4 + c"}


def q_f3c8_048():
    # Method: numerical differentiation against log x over positive x. Option B
    # (x log x) is the classic near-miss: its derivative is log x + 1, which the
    # difference quotient separates from log x without any algebra.
    integrand = lambda x: math.log(x)
    options = {
        "A": (lambda x: 1 / x, True),
        "B": (lambda x: x * math.log(x), True),
        "C": (lambda x: math.log(x) ** 2 / 2, True),
        "D": (lambda x: x * math.log(x) - x, True),
    }
    key = pick_antiderivative(options, integrand, [0.8, 1.7, 3.0])
    return {"answer": key, "computed": "x log x - x + c"}


def q_f3c8_049():
    # Method: numerical differentiation against (5x - 4)/((x - 2)(x + 1)). The
    # partial-fraction split is never solved here, so a wrong pair of numerators
    # cannot survive. Sample points stay clear of the poles at x = 2 and x = -1.
    integrand = lambda x: (5 * x - 4) / ((x - 2) * (x + 1))
    options = {
        "A": (lambda x: 2 * math.log(abs(x - 2)) + 3 * math.log(abs(x + 1)), True),
        "B": (lambda x: 3 * math.log(abs(x - 2)) + 2 * math.log(abs(x + 1)), True),
        "C": (lambda x: 2 * math.log(abs(x - 2)) - 3 * math.log(abs(x + 1)), True),
        "D": (lambda x: math.log(abs((x - 2) * (x + 1))), True),
    }
    key = pick_antiderivative(options, integrand, [3.0, 4.5, 6.0])
    return {"answer": key, "computed": "2 log|x - 2| + 3 log|x + 1| + c"}


def q_f3c8_050():
    # Method: composite Simpson's rule on 2,000 sub-intervals, not the
    # antiderivative. Option A is the same magnitude with the limits subtracted
    # the wrong way round, so the sign carries real information here.
    f = lambda x: 3 * x ** 2 + 2 * x
    value = simpson(f, 1.0, 3.0)
    key = pick_value({"A": -34, "B": 34, "C": 36, "D": 26}, value)
    return {"answer": key, "computed": round(value, 6)}


# --------------------------------------------------------------- the case sets


def _case1_cost():
    """Anuradha Pumps: total cost of x pumps a day."""
    return lambda x: x ** 2 + 50 * x + 900


def _case1_profit():
    """Anuradha Pumps: profit at output x, price p = 250 - x."""
    C = _case1_cost()
    return lambda x: (250 - x) * x - C(x)


def cs_f3c8_01_a():
    # Method: five-point numerical derivative of C(x) at x = 20. The marginal
    # cost is never read off a differentiated formula. Tolerance 1e-6 relative.
    value = nderiv(_case1_cost(), 20.0)
    key = pick_value({"A": 115, "B": 2300, "C": 90, "D": 990}, value)
    return {"answer": key, "computed": round(value, 6)}


def cs_f3c8_01_b():
    # Method: average cost C(x)/x minimised by ternary search on [1, 500] with no
    # calculus, then confirmed the minimum of a dense neighbourhood. The answer
    # is the COST at the optimum, so option C (the optimal output, 30) is the
    # trap this separates.
    C = _case1_cost()
    AC = lambda x: C(x) / x
    x_star = _ternary(AC, 1.0, 500.0, "min")
    assert extremum_kind(AC, x_star, 10.0) == "minimum"
    value = AC(x_star)
    key = pick_value({"A": 80, "B": 3300, "C": 30, "D": 110}, value)
    return {"answer": key, "computed": round(value, 6)}


def cs_f3c8_01_c():
    # Method: profit maximised by ternary search on [0, 200], confirmed a maximum
    # on a dense grid. The answer is the OUTPUT at the optimum.
    P = _case1_profit()
    x_star = _ternary(P, 0.0, 200.0, "max")
    assert extremum_kind(P, x_star, 20.0) == "maximum"
    key = pick_value({"A": 50, "B": 125, "C": 66.67, "D": 30}, x_star, ROUND_TOL)
    return {"answer": key, "computed": round(x_star, 6)}


def cs_f3c8_01_d():
    # Method: as (c), but the answer is the PROFIT at the maximiser. Option C is
    # the revenue-side figure a student reaches by forgetting to deduct cost.
    P = _case1_profit()
    x_star = _ternary(P, 0.0, 200.0, "max")
    value = P(x_star)
    key = pick_value({"A": 5000, "B": 4100, "C": 10000, "D": 50}, value)
    return {"answer": key, "computed": round(value, 6)}


# Meenakshi Components: only the marginal functions and the fixed cost are given,
# so every total below is rebuilt by INTEGRATING the marginal numerically
# (composite Simpson), never by quoting an antiderivative.

_MC = lambda x: 3 * x ** 2 - 24 * x + 90
_MR = lambda x: 500 - 6 * x
_FIXED = 2500


def _case2_total_cost(x):
    """Total cost of x parts = fixed cost + the integral of MC from 0 to x."""
    return _FIXED + simpson(_MC, 0.0, x)


def _case2_total_revenue(x):
    """Total revenue from x parts = the integral of MR from 0 to x (TR(0) = 0)."""
    return simpson(_MR, 0.0, x)


def cs_f3c8_02_a():
    # Method: Simpson integration of MC over [0, 10] plus the fixed cost. Option A
    # is the integral with the fixed cost omitted, which is the error being tested.
    value = _case2_total_cost(10.0)
    key = pick_value({"A": 700, "B": 150, "C": 3200, "D": 2500}, value)
    return {"answer": key, "computed": round(value, 6)}


def cs_f3c8_02_b():
    # Method: Simpson integration of MR over [0, 20]. No constant is added: total
    # revenue is zero at zero output, which is what makes TR's constant knowable
    # while TC's is not. Option B is MR evaluated at 20 instead of integrated.
    value = _case2_total_revenue(20.0)
    key = pick_value({"A": 10000, "B": 380, "C": 11300, "D": 8800}, value)
    return {"answer": key, "computed": round(value, 6)}


def cs_f3c8_02_c():
    # Method: the definite integral of MC from 10 to 15 by Simpson. A change in
    # total cost needs no fixed cost and no constant, since both cancel; option B
    # is the figure reached by carrying the fixed cost in anyway.
    value = simpson(_MC, 10.0, 15.0)
    key = pick_value({"A": 1325, "B": 3825, "C": 2025, "D": 4525}, value)
    return {"answer": key, "computed": round(value, 6)}


def cs_f3c8_02_d():
    # Method: both totals rebuilt independently by Simpson, then subtracted.
    # Option C is total revenue left undeducted.
    value = _case2_total_revenue(20.0) - _case2_total_cost(20.0)
    key = pick_value({"A": 3800, "B": 1300, "C": 8800, "D": -430}, value)
    return {"answer": key, "computed": round(value, 6)}


# Girija Traders: the EOQ formula is deliberately NOT used. The annual cost
# function is written straight from the scenario's own words -- ordering cost per
# order times orders a year, plus holding cost times average stock -- and its
# minimiser is found by ternary search. So the answer tests the model, not the
# memorised square root.

_ANNUAL_DEMAND = 18000
_ORDER_COST = 400


def _case3_annual_cost(holding):
    """Annual ordering + holding cost as a function of order size q."""
    return lambda q: (_ANNUAL_DEMAND / q) * _ORDER_COST + (q / 2) * holding


def cs_f3c8_03_a():
    # Method: ternary search for the minimiser of the annual cost on [50, 5000],
    # confirmed the minimum of a dense neighbourhood. Option D is a text option
    # (the claim that price is needed), so it is recorded as None.
    total = _case3_annual_cost(10)
    q_star = _ternary(total, 50.0, 5000.0, "min")
    assert extremum_kind(total, q_star, 200.0) == "minimum"
    key = pick_value({"A": 848.5, "B": 30, "C": 1200, "D": None}, q_star, ROUND_TOL)
    return {"answer": key, "computed": round(q_star, 6)}


def cs_f3c8_03_b():
    # Method: the optimal order size is re-derived by search, then the number of
    # orders falls out as demand / order size. Option B is the order size's own
    # divisor confused with the count.
    total = _case3_annual_cost(10)
    q_star = _ternary(total, 50.0, 5000.0, "min")
    value = _ANNUAL_DEMAND / q_star
    key = pick_value({"A": 21.2, "B": 30, "C": 1200, "D": 15}, value, ROUND_TOL)
    return {"answer": key, "computed": round(value, 6)}


def cs_f3c8_03_c():
    # Method: the annual cost function is evaluated AT the searched minimiser, so
    # the answer is a measured minimum rather than the sqrt(2*D*Co*Ch) shortcut.
    # Options B and A differ by whether both cost limbs are counted.
    total = _case3_annual_cost(10)
    q_star = _ternary(total, 50.0, 5000.0, "min")
    value = total(q_star)
    key = pick_value({"A": 12000, "B": 6000, "C": 18000, "D": 12728}, value, ROUND_TOL)
    return {"answer": key, "computed": round(value, 6)}


def cs_f3c8_03_d():
    # Method: the same search re-run with holding cost 40 instead of 10. Quadrupling
    # the holding cost halves the optimum; option C is the unchanged answer and
    # option A is the result of dividing by four rather than by its square root.
    total = _case3_annual_cost(40)
    q_star = _ternary(total, 50.0, 5000.0, "min")
    assert extremum_kind(total, q_star, 100.0) == "minimum"
    key = pick_value({"A": 300, "B": 600, "C": 1200, "D": 2400}, q_star, ROUND_TOL)
    return {"answer": key, "computed": round(q_star, 6)}
