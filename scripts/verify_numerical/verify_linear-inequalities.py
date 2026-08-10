"""Verifier for foundation/quantitative-aptitude/linear-inequalities.json (P3 Ch 3).

Every function recomputes its answer from the stem's own parameters. One-variable
inequalities are reduced to `a*x SENSE b` and then solved by `solve_1v`, which
applies the sign reversal itself, so a verifier that forgot the flip would
disagree with the bank rather than agree with it. Two-variable questions are
answered from the geometry: `corner_points` intersects EVERY pair of boundary
lines (the axes included) and filters the results by feasibility, so a vertex is
never asserted, and `is_bounded` computes the recession cone rather than reading
the constraint signs off a pattern.

All coordinate arithmetic uses `fractions.Fraction`, so a vertex such as
(16/3, 20/3) is exact and compares equal to the option text rather than to a
rounded neighbour.

Conventions used below:
  * a two-variable constraint is the 4-tuple (a, b, sense, c) meaning
    `a*x + b*y SENSE c`, with sense in {"<=", ">=", "<", ">", "=="};
  * a one-variable solution set is ("lt"|"le"|"gt"|"ge", bound), or the string
    "all" / "none" when the variable cancels;
  * an interval is the 4-tuple (lo, lo_included, hi, hi_included), with None for
    an unbounded end.
"""

from __future__ import annotations

from fractions import Fraction as F
from itertools import combinations

# ------------------------------------------------------------ shared helpers

FLIP = {"<": ">", ">": "<", "<=": ">=", ">=": "<="}
NAME = {"<": "lt", "<=": "le", ">": "gt", ">=": "ge"}


def solve_1v(a, b, sense):
    """Solve `a*x SENSE b` for x. Returns (name, bound), or "all" / "none"."""
    a, b = F(a), F(b)
    if a == 0:
        holds = {
            "<": b > 0,
            "<=": b >= 0,
            ">": b < 0,
            ">=": b <= 0,
        }[sense]
        return "all" if holds else "none"
    if a < 0:
        sense = FLIP[sense]
    return NAME[sense], b / a


def reduce_1v(lhs, rhs, sense):
    """`lhs` and `rhs` are (coefficient, constant) pairs. Returns the solution
    of `lhs SENSE rhs` after collecting x on the left and constants on the
    right — the transposition step, which never changes the direction."""
    a = F(lhs[0]) - F(rhs[0])
    b = F(rhs[1]) - F(lhs[1])
    return solve_1v(a, b, sense)


def double_1v(lo, hi, coef, const, lo_strict=False, hi_strict=False):
    """Solve `lo SENSE coef*x + const SENSE hi` for x, returning an interval
    (low, low_included, high, high_included). Both ends are divided by `coef`
    together, so a negative coefficient reverses and swaps them."""
    coef = F(coef)
    left = (F(lo) - F(const)) / coef
    right = (F(hi) - F(const)) / coef
    left_incl, right_incl = not lo_strict, not hi_strict
    if coef < 0:
        left, right = right, left
        left_incl, right_incl = right_incl, left_incl
    return (left, left_incl, right, right_incl)


def is_empty(interval):
    lo, lo_in, hi, hi_in = interval
    if lo is None or hi is None:
        return False
    if lo > hi:
        return True
    return lo == hi and not (lo_in and hi_in)


def integers_in(interval):
    """Every integer inside the interval, computed from the exact bounds."""
    lo, lo_in, hi, hi_in = interval
    import math

    start = math.ceil(lo) if lo_in else math.floor(lo) + 1
    stop = math.floor(hi) if hi_in else math.ceil(hi) - 1
    return list(range(start, stop + 1))


def intersect_1v(*sets):
    """Intersect one-variable solution sets given as (name, bound) pairs into an
    interval. The stricter condition wins at a shared endpoint."""
    lo, lo_in, hi, hi_in = None, True, None, True
    for name, bound in sets:
        if name in ("gt", "ge"):
            incl = name == "ge"
            if lo is None or bound > lo:
                lo, lo_in = bound, incl
            elif bound == lo:
                lo_in = lo_in and incl
        else:
            incl = name == "le"
            if hi is None or bound < hi:
                hi, hi_in = bound, incl
            elif bound == hi:
                hi_in = hi_in and incl
    return (lo, lo_in, hi, hi_in)


# --------------------------------------------------- two-variable geometry


def holds(constraint, point):
    """Does `point` satisfy `a*x + b*y SENSE c`?"""
    a, b, sense, c = constraint
    lhs = F(a) * point[0] + F(b) * point[1]
    c = F(c)
    return {
        "<=": lhs <= c,
        ">=": lhs >= c,
        "<": lhs < c,
        ">": lhs > c,
        "==": lhs == c,
    }[sense]


def feasible(point, constraints):
    return all(holds(k, point) for k in constraints)


def intersect_lines(k1, k2):
    """Solve the two boundary EQUATIONS exactly. None if they are parallel."""
    a1, b1, _, c1 = k1
    a2, b2, _, c2 = k2
    det = F(a1) * F(b2) - F(a2) * F(b1)
    if det == 0:
        return None
    x = (F(c1) * F(b2) - F(c2) * F(b1)) / det
    y = (F(a1) * F(c2) - F(a2) * F(c1)) / det
    return (x, y)


NONNEG = [(1, 0, ">=", 0), (0, 1, ">=", 0)]


def corner_points(constraints):
    """Intersect EVERY pair of boundary lines and keep only the intersections
    that satisfy every constraint. The answer is never asserted."""
    kept = []
    for k1, k2 in combinations(constraints, 2):
        pt = intersect_lines(k1, k2)
        if pt is None:
            continue
        if feasible(pt, constraints) and pt not in kept:
            kept.append(pt)
    return sorted(kept)


def is_bounded(constraints):
    """Bounded iff the recession cone contains no non-zero direction. In two
    variables the candidate extreme rays are the two axes and, for each
    constraint row, the direction along that row's boundary line."""
    rays = [(F(1), F(0)), (F(0), F(1))]
    for a, b, _, _ in constraints:
        for d in ((F(b), F(-a)), (F(-b), F(a))):
            if d != (0, 0) and d not in rays:
                rays.append(d)
    for d in rays:
        if d[0] < 0 or d[1] < 0:
            continue  # non-negativity forbids it as a direction of travel
        ok = True
        for a, b, sense, _ in constraints:
            v = F(a) * d[0] + F(b) * d[1]
            if sense in ("<=", "<") and v > 0:
                ok = False
            if sense in (">=", ">") and v < 0:
                ok = False
            if sense == "==" and v != 0:
                ok = False
        if ok and d != (0, 0):
            return False
    return True


def same_region(k1, k2, lo=-6, hi=12, step=1):
    """Do two two-variable constraints admit exactly the same points? Tested
    over a lattice, which is enough to separate the option set of any question
    in this bank because every distractor differs on a lattice point."""
    rng = [F(v, 2) for v in range(2 * lo, 2 * hi + 1, step)]
    for x in rng:
        for y in rng:
            if holds(k1, (x, y)) != holds(k2, (x, y)):
                return False
    return True


def match_region(truth, options, lo=-6, hi=12):
    """Return the single option key whose constraint is the same region."""
    hits = [k for k, v in options.items() if same_region(truth, v, lo, hi)]
    assert len(hits) == 1, f"expected one equivalent option, got {hits}"
    return hits[0]


# ------------------------------------- §1 to §5: one variable, sign reversal


def q_f3c3_002():
    # 4x - 12 = 0 pins x; 4x - 12 < 0 fences it.
    root = F(12, 4)
    ineq = solve_1v(4, 12, "<")
    key = {(F(3), ("lt", F(3))): "C"}[(root, ineq)]
    return {"answer": key, "computed": f"root {root}; inequality x {ineq}"}


def q_f3c3_007():
    truth = (-1, 3, "<=", 6)
    options = {
        "A": (1, -3, ">=", -6),
        "B": (1, -3, "<=", -6),
        "C": (1, -3, ">=", 6),
        "D": (-1, 3, ">=", 6),
    }
    key = match_region(truth, options)
    return {"answer": key, "computed": "x - 3y >= -6"}


def q_f3c3_008():
    sol = solve_1v(-5, 20, ">")
    key = {("gt", F(-4)): "A", ("gt", F(4)): "B", ("lt", F(-4)): "C", ("lt", F(4)): "D"}[sol]
    return {"answer": key, "computed": f"x {sol}"}


def q_f3c3_009():
    # 7 - 3x > 1  ->  -3x > -6
    sol = reduce_1v((-3, 7), (0, 1), ">")
    key = {("gt", F(2)): "A", ("lt", F(-2)): "B", ("gt", F(-2)): "C", ("lt", F(2)): "D"}[sol]
    return {"answer": key, "computed": f"x {sol}"}


def q_f3c3_011():
    iv = double_1v(-4, 10, coef=-2, const=0)
    key = {(F(-2), F(5)): "A", (F(2), F(-5)): "B", (F(-5), F(2)): "C"}[(iv[0], iv[2])]
    return {"answer": key, "computed": f"{iv[0]} <= x <= {iv[2]}"}


def q_f3c3_013():
    # (2x - 3)/4 + 9  >=  3 + 4x/3
    lhs = (F(2, 4), F(-3, 4) + 9)
    rhs = (F(4, 3), F(3))
    sol = reduce_1v(lhs, rhs, ">=")
    key = {
        ("ge", F(63, 10)): "A",
        ("le", F(-3, 10)): "B",
        ("le", F(63, 10)): "C",
        ("ge", F(-3, 10)): "D",
    }[sol]
    return {"answer": key, "computed": f"x {sol}"}


def q_f3c3_014():
    sol = reduce_1v((5, 7), (5, 12), "<")
    key = {("lt", F(5)): "A", "all": "B", "none": "C", ("gt", F(0)): "D"}[sol]
    return {"answer": key, "computed": sol}


def q_f3c3_015():
    # 3(x - 2) + 4 <= 5x + 10
    sol = reduce_1v((3, -6 + 4), (5, 10), "<=")
    key = {("le", F(-6)): "A", ("ge", F(6)): "B", ("le", F(6)): "C", ("ge", F(-6)): "D"}[sol]
    return {"answer": key, "computed": f"x {sol}"}


def q_f3c3_016():
    sol = reduce_1v((F(1, 3), -2), (F(1, 5), F(4, 5)), "<")
    key = {("lt", F(21)): "A", ("lt", F(7)): "B", ("gt", F(21)): "C", ("lt", F(6)): "D"}[sol]
    return {"answer": key, "computed": f"x {sol}"}


def q_f3c3_017():
    sol = reduce_1v((4, 4), (4, 9), ">")
    key = {"none": "A", "all": "B", ("gt", F(5, 4)): "C", ("gt", F(0)): "D"}[sol]
    return {"answer": key, "computed": sol}


def least_integer(sol):
    """The least integer in a solution set of the form x > b or x >= b."""
    import math

    name, bound = sol
    assert name in ("gt", "ge")
    return math.floor(bound) + 1 if name == "gt" else math.ceil(bound)


def q_f3c3_018():
    contribution, fixed_cost = 45, 27_000
    sol = solve_1v(contribution, fixed_cost, ">")  # 'exceed' is strict
    units = least_integer(sol)
    key = {600: "A", 599: "B", 27_045: "C", 601: "D"}[units]
    return {"answer": key, "computed": units}


def q_f3c3_019():
    scored, target, papers = [62, 71], 70, 3
    sol = solve_1v(1, target * papers - sum(scored), ">=")  # 'at least' is non-strict
    mark = least_integer(sol)
    key = {70: "A", 77: "B", 76: "C", 210: "D"}[mark]
    return {"answer": key, "computed": mark}


# ------------------------- §6 to §8: intervals, double and joint inequalities


def q_f3c3_020():
    iv = intersect_1v(("gt", F(-2)), ("le", F(4)))
    key = {
        (F(-2), True, F(4), True): "A",
        (F(-2), False, F(4), False): "B",
        (F(-2), False, F(4), True): "C",
        (F(-2), True, F(4), False): "D",
    }[iv]
    return {"answer": key, "computed": f"({iv[0]}, {iv[2]}] with brackets {iv[1]}/{iv[3]}"}


def q_f3c3_022():
    sol = solve_1v(2, 9, "<")
    naturals = tuple(n for n in range(1, 20) if F(n) < sol[1])
    key = {(1, 2, 3, 4): "A", (0, 1, 2, 3, 4): "B", (1, 2, 3, 4, 5): "C"}[naturals]
    return {"answer": key, "computed": naturals}


def q_f3c3_024():
    sol = reduce_1v((3, -4), (0, 11), "<")
    wholes = [n for n in range(0, 30) if F(n) < sol[1]]
    key = {4: "A", 6: "B", 5: "D"}[len(wholes)]
    return {"answer": key, "computed": f"{wholes} -> {len(wholes)}"}


def q_f3c3_025():
    iv = double_1v(-5, 19, coef=3, const=4, lo_strict=False, hi_strict=True)
    key = {
        (F(-3), False, F(5), True): "A",
        (F(-3), True, F(5), True): "B",
        (F(-5, 3), True, F(5), False): "C",
        (F(-3), True, F(5), False): "D",
    }[iv]
    return {"answer": key, "computed": iv}


def q_f3c3_026():
    iv = double_1v(7, 13, coef=-2, const=5)
    key = {(F(1), F(4)): "A", (F(-1), F(-4)): "B", (F(-4), F(-1)): "C"}[(iv[0], iv[2])]
    return {"answer": key, "computed": f"{iv[0]} <= x <= {iv[2]}"}


def q_f3c3_027():
    iv = double_1v(9, 5, coef=2, const=1, lo_strict=True, hi_strict=True)
    key = "A" if is_empty(iv) else {(F(2), F(4)): "B"}[(iv[0], iv[2])]
    return {"answer": key, "computed": f"{iv[0]} < x < {iv[2]} -> empty={is_empty(iv)}"}


def DOUBLE_028():
    return double_1v(-8, 13, coef=-3, const=5, lo_strict=False, hi_strict=True)


def q_f3c3_028():
    ints = integers_in(DOUBLE_028())
    key = {6: "A", 7: "B", 8: "C", 4: "D"}[len(ints)]
    return {"answer": key, "computed": f"{ints} -> {len(ints)}"}


def q_f3c3_029():
    lo, lo_in, hi, hi_in = DOUBLE_028()
    included = tuple(v for v, inc in ((lo, lo_in), (hi, hi_in)) if inc)
    key = {
        (F(-8, 3), F(13, 3)): "A",
        (F(-8, 3),): "B",
        (F(13, 3),): "C",
        (): "D",
    }[included]
    return {"answer": key, "computed": included}


def q_f3c3_030():
    iv = intersect_1v(reduce_1v((3, -5), (0, 7), "<="), reduce_1v((2, 3), (0, 5), ">"))
    key = {
        (F(1), True, F(4), False): "A",
        (F(1), False, F(4), True): "B",
    }[iv]
    return {"answer": key, "computed": iv}


def q_f3c3_031():
    iv = intersect_1v(("le", F(4)), ("lt", F(4)))
    key = {(F(4), True): "A", (F(4), False): "D"}[(iv[2], iv[3])]
    return {"answer": key, "computed": f"x < {iv[2]} (included: {iv[3]})"}


def q_f3c3_032():
    iv = intersect_1v(reduce_1v((1, 2), (0, 8), ">"), solve_1v(3, 6, "<"))
    key = "A" if is_empty(iv) else {(F(2), F(6)): "B"}[(iv[0], iv[2])]
    return {"answer": key, "computed": f"{iv[0]} < x < {iv[2]} -> empty={is_empty(iv)}"}


def q_f3c3_033():
    iv = intersect_1v(
        reduce_1v((5, -3), (3, 11), "<="),
        reduce_1v((6, -2), (4, 6), ">"),
    )
    ints = integers_in(iv)
    key = {3: "A", 4: "B", 2: "C", 8: "D"}[len(ints)]
    return {"answer": key, "computed": f"{ints} -> {len(ints)}"}


def q_f3c3_034():
    iv = intersect_1v(solve_1v(2, 8, "<="), ("le", F(9)))
    key = {(F(9), True): "A", (F(4), True): "B", (F(13), True): "D"}[(iv[2], iv[3])]
    return {"answer": key, "computed": f"x <= {iv[2]}"}


# ------------------------------------------- §9 and §17: translation to a system


def match_predicate(pred, options, lo=0, hi=12):
    """Like match_region, but the truth is the sentence itself, written as a
    predicate, so no simplified form is assumed before the comparison."""
    grid = [F(v, 2) for v in range(2 * lo, 2 * hi + 1)]
    hits = []
    for k, v in options.items():
        if all(pred(x, y) == holds(v, (x, y)) for x in grid for y in grid):
            hits.append(k)
    assert len(hits) == 1, f"expected one equivalent option, got {hits}"
    return hits[0]


def q_f3c3_035():
    truth = (15_000, 20_000, "<=", 2_40_000)
    options = {
        "A": (15_000, 20_000, ">=", 2_40_000),
        "B": (15_000, 20_000, "==", 2_40_000),
        "C": (15_000, 20_000, "<=", 2_40_000),
        "D": (15_000, 20_000, "<", 2_40_000),
    }
    key = match_region(truth, options)
    return {"answer": key, "computed": "3x + 4y <= 48 after dividing by 5,000"}


def q_f3c3_036():
    # 'At least one third of the total output must be product A', written as it
    # stands, with nothing simplified in advance.
    def sentence(x, y):
        return x >= (x + y) / 3

    options = {
        "A": (1, F(-1, 3), ">=", 0),
        "B": (1, -2, "<=", 0),
        "C": (3, -1, ">=", 0),
        "D": (2, -1, ">=", 0),
    }
    key = match_predicate(sentence, options)
    return {"answer": key, "computed": "2x - y >= 0"}


def q_f3c3_037():
    minutes_available = 60 * 60  # 60 hours converted before the coefficient
    truth = (40, 0, "<=", minutes_available)
    options = {
        "A": (40, 0, "<=", 60),
        "B": (40, 0, ">=", minutes_available),
        "C": (60, 0, "<=", 40),
        "D": (40, 0, "<=", minutes_available),
    }
    key = match_region(truth, options, lo=0, hi=120)
    return {"answer": key, "computed": f"40x <= {minutes_available}, so x <= 90"}


def q_f3c3_038():
    truth = (F(1, 2), F(4, 5), "<=", 6)
    options = {
        "A": (5, 8, "<=", 6),
        "B": (F(1, 2), F(4, 5), ">=", 6),
        "C": (5, 8, "<=", 60),
        "D": (1, 1, "<=", 6),
    }
    key = match_region(truth, options, lo=0, hi=14)
    return {"answer": key, "computed": "5x + 8y <= 60"}


def q_f3c3_039():
    truth = (12, 8, ">=", 90)
    options = {
        "A": (12, 8, "<=", 90),
        "B": (12, 8, ">=", 90),
        "C": (12, 8, "==", 90),
        "D": (20, 20, ">=", 90),
    }
    key = match_region(truth, options, lo=0, hi=12)
    return {"answer": key, "computed": "12x + 8y >= 90"}


# --------------------------------- §10 to §16: half-planes, regions, vertices


def q_f3c3_041():
    a, b, c = 5, 3, 45
    x_int, y_int = F(c, a), F(c, b)
    key = {(F(15), F(9)): "A", (F(9), F(15)): "B", (F(5), F(3)): "C", (F(45), F(45)): "D"}[
        (x_int, y_int)
    ]
    return {"answer": key, "computed": f"({x_int}, 0) and (0, {y_int})"}


def q_f3c3_044():
    system = [(3, 4, "<=", 24)] + NONNEG
    points = {"A": (F(4), F(4)), "B": (F(-1), F(5)), "C": (F(2), F(3)), "D": (F(0), F(7))}
    hits = [k for k, p in points.items() if feasible(p, system)]
    assert len(hits) == 1, hits
    return {"answer": hits[0], "computed": f"feasible: {hits}"}


def region_is_empty(constraints, span=60):
    """No vertex and no lattice point anywhere in a wide first-quadrant scan."""
    if corner_points(constraints):
        return False
    grid = [F(v) for v in range(0, span + 1)]
    return not any(feasible((x, y), constraints) for x in grid for y in grid)


def q_f3c3_046():
    system = [(1, 1, "<=", 10), (1, 1, ">=", 25)] + NONNEG
    empty = region_is_empty(system)
    key = {True: "A"}[empty]
    return {"answer": key, "computed": f"corners {corner_points(system)}, empty={empty}"}


def q_f3c3_048():
    system = [(1, 2, ">=", 20), (3, 1, ">=", 15)] + NONNEG
    pts, bounded = corner_points(system), is_bounded(system)
    key = {(3, False): "B", (4, True): "C", (3, True): "D"}[(len(pts), bounded)]
    return {"answer": key, "computed": f"{pts}, bounded={bounded}"}


def q_f3c3_049():
    system = [(1, 1, ">=", 8), (1, 2, "<=", 20)] + NONNEG
    pts, bounded = corner_points(system), is_bounded(system)
    key = {(4, True): "A", (4, False): "B", (0, True): "C"}[(len(pts), bounded)]
    return {"answer": key, "computed": f"{pts}, bounded={bounded}"}


def q_f3c3_050():
    carpentry, polishing = (2, 3, "<=", 120), (2, 1, "<=", 80)
    pt = intersect_lines(carpentry, polishing)
    assert feasible(pt, [carpentry, polishing] + NONNEG)
    key = {(F(20), F(30)): "A", (F(30), F(20)): "B", (F(40), F(40)): "C", (F(60), F(80)): "D"}[pt]
    return {"answer": key, "computed": pt}


def q_f3c3_051():
    system = [(1, 1, "<=", 12), (1, 4, "<=", 32)] + NONNEG
    pts = corner_points(system)
    candidates = {
        "A": (F(12), F(0)),
        "B": (F(0), F(8)),
        "C": (F(0), F(12)),
        "D": (F(16, 3), F(20, 3)),
    }
    misses = [k for k, p in candidates.items() if p not in pts]
    assert len(misses) == 1, misses
    return {"answer": misses[0], "computed": f"corners {pts}"}


def q_f3c3_052():
    system = [(3, 2, "<=", 60), (1, 2, "<=", 40), (1, 0, "<=", 16)] + NONNEG
    pts = set(corner_points(system))
    options = {
        "A": {(0, 0), (20, 0), (10, 15), (0, 20)},
        "B": {(0, 0), (16, 0), (16, 12), (0, 30)},
        "C": {(0, 0), (16, 0), (10, 15), (0, 20)},
        "D": {(0, 0), (16, 0), (16, 6), (10, 15), (0, 20)},
    }
    hits = [k for k, v in options.items() if {(F(a), F(b)) for a, b in v} == pts]
    assert len(hits) == 1, hits
    return {"answer": hits[0], "computed": sorted(pts)}


# ------------------------------------------------------------- case sets

# cs-01: Sahyadri Packaging — board 4x + 5y <= 200, machine 2x + 5y <= 150.
PACK_BOARD = (4, 5, "<=", 200)
PACK_MACHINE = (2, 5, "<=", 150)
PACK = [PACK_BOARD, PACK_MACHINE] + NONNEG


def cs_f3c3_01_a():
    options = {
        "A": (5, 2, "<=", 150),
        "B": (2, 5, "<=", 150),
        "C": (2, 5, ">=", 150),
        "D": (2, 5, "==", 150),
    }
    key = match_region(PACK_MACHINE, options, lo=0, hi=40)
    return {"answer": key, "computed": "2x + 5y <= 150"}


def cs_f3c3_01_b():
    pt = intersect_lines(PACK_BOARD, PACK_MACHINE)
    assert feasible(pt, PACK)
    key = {(F(25), F(20)): "A", (F(20), F(25)): "B", (F(50), F(30)): "C", (F(50), F(0)): "D"}[pt]
    return {"answer": key, "computed": pt}


def cs_f3c3_01_c():
    plan = (F(30), F(15))
    board = 4 * plan[0] + 5 * plan[1]
    machine = 2 * plan[0] + 5 * plan[1]
    key = {True: "D", False: "A"}[feasible(plan, PACK)]
    return {"answer": key, "computed": f"board {board}/200, machine {machine}/150"}


def cs_f3c3_01_d():
    pts, bounded = corner_points(PACK), is_bounded(PACK)
    key = {(3, False): "A", (5, True): "B", (4, True): "C", (2, True): "D"}[(len(pts), bounded)]
    return {"answer": key, "computed": f"{pts}, bounded={bounded}"}


# cs-02: Kaveri Feeds — energy 2x + y >= 30, fibre x + 3y >= 30.
FEED_ENERGY = (2, 1, ">=", 30)
FEED_FIBRE = (1, 3, ">=", 30)
FEED = [FEED_ENERGY, FEED_FIBRE] + NONNEG


def cs_f3c3_02_a():
    pts, bounded = corner_points(FEED), is_bounded(FEED)
    if region_is_empty(FEED):
        return {"answer": "C", "computed": "empty"}
    key = {(4, True): "A", (3, False): "B", (3, True): "D"}[(len(pts), bounded)]
    return {"answer": key, "computed": f"{pts}, bounded={bounded}"}


def cs_f3c3_02_b():
    pt = intersect_lines(FEED_ENERGY, FEED_FIBRE)
    assert feasible(pt, FEED)
    key = {(F(6), F(12)): "A", (F(10), F(10)): "B", (F(12), F(6)): "C", (F(15), F(0)): "D"}[pt]
    return {"answer": key, "computed": pt}


def cs_f3c3_02_c():
    pts = corner_points(FEED)
    candidates = {
        "A": (F(0), F(30)),
        "B": (F(0), F(10)),
        "C": (F(5), F(0)),
        "D": (F(0), F(0)),
    }
    hits = [k for k, p in candidates.items() if p in pts]
    assert len(hits) == 1, hits
    return {"answer": hits[0], "computed": f"corners {pts}"}


# cs-03: the trust — funds x + y <= 800, equity ceiling y <= 300, policy x >= y.
TRUST_FUNDS = (1, 1, "<=", 800)
TRUST_CEILING = (0, 1, "<=", 300)
TRUST_POLICY = (1, -1, ">=", 0)
TRUST = [TRUST_FUNDS, TRUST_CEILING, TRUST_POLICY] + NONNEG


def cs_f3c3_03_b():
    pt = intersect_lines(TRUST_CEILING, TRUST_FUNDS)
    assert feasible(pt, TRUST)
    key = {
        (F(500), F(300)): "A",
        (F(300), F(500)): "B",
        (F(400), F(400)): "C",
        (F(800), F(300)): "D",
    }[pt]
    return {"answer": key, "computed": pt}


def cs_f3c3_03_c():
    pts = set(corner_points(TRUST))
    options = {
        "A": {(0, 0), (800, 0), (400, 400)},
        "B": {(0, 0), (800, 0), (500, 300), (300, 300)},
        "C": {(0, 0), (800, 0), (500, 300), (0, 300)},
        "D": {(500, 300), (300, 300)},
    }
    hits = [k for k, v in options.items() if {(F(a), F(b)) for a, b in v} == pts]
    assert len(hits) == 1, hits
    return {"answer": hits[0], "computed": sorted(pts)}
