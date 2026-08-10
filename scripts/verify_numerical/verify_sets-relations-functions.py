"""Verifier for foundation/quantitative-aptitude/sets-relations-functions.json (P3 Ch 7).

Every function recomputes its answer from the stem's own parameters and maps the
computed value onto an option key through a dict of the four option values, so a
wrong key in the bank surfaces as a KeyError or as a mismatch the runner reports.

Method used, and why, is stated in a comment on every function. The house style
for this chapter is deliberate:

  * ENUMERATION FIRST. Wherever the universe is small enough, the answer is
    obtained by building real Python `set` objects, or by walking every
    candidate with `itertools`, and counting what actually comes out — never by
    re-applying the same formula the stem used. Counting subsets, relations,
    functions, one-one functions and bijections is done by generating them.
    Venn-region questions build an explicit population of labelled members and
    count the region with set operations, so the inclusion-exclusion formula is
    tested rather than repeated.
  * LIMITS ARE DONE TWICE. The exact value comes from an algebraic
    simplification carried in `fractions.Fraction` (synthetic division for a
    cancelled factor, the conjugate for a surd). It is then confirmed
    numerically by approaching the point from both sides and checking the two
    approach values agree with the exact answer to within `NUM_TOL`.
  * Constructed populations are self-checked: `build_three_sets` asserts that
    the sets it returns really do reproduce every cardinality the stem gave.
"""

from __future__ import annotations

import itertools
from fractions import Fraction as F

NUM_TOL = 1e-4  # tolerance for the two-sided numerical confirmation of a limit


# ------------------------------------------------------------ shared helpers


def subsets(items):
    """Generate every subset of `items` as a frozenset. Pure enumeration."""
    items = list(items)
    for r in range(len(items) + 1):
        for combo in itertools.combinations(items, r):
            yield frozenset(combo)


def count_subsets(n):
    """Count the subsets of an n-element set BY GENERATING THEM."""
    return sum(1 for _ in subsets(range(n)))


def build_two_sets(n_u, n_a, n_b, n_ab):
    """Return (universe, A, B) as real sets reproducing the given counts.

    Members are plain integers. The construction lays out the four Venn regions
    as disjoint blocks; it asserts the result matches every figure supplied, so
    an impossible data set fails loudly instead of returning a plausible number.
    """
    only_a = n_a - n_ab
    only_b = n_b - n_ab
    assert only_a >= 0 and only_b >= 0, "an overlap cannot exceed either set"
    both = list(range(0, n_ab))
    a_only = list(range(n_ab, n_ab + only_a))
    b_only = list(range(n_ab + only_a, n_ab + only_a + only_b))
    used = n_ab + only_a + only_b
    assert used <= n_u, "the sets do not fit inside the universe"
    outside = list(range(used, n_u))
    a = set(both) | set(a_only)
    b = set(both) | set(b_only)
    u = set(both) | set(a_only) | set(b_only) | set(outside)
    assert len(u) == n_u and len(a) == n_a and len(b) == n_b and len(a & b) == n_ab
    return u, a, b


def build_three_sets(n_u, n_a, n_b, n_c, n_ab, n_bc, n_ac, n_abc):
    """Return (universe, A, B, C) as real sets reproducing the given counts.

    The seven inside regions are laid out as disjoint integer blocks. Only the
    definitions of the regions are used to size them (a pairs-only block is the
    pairwise count less the triple count; an only block is the set less the two
    pairwise counts it sits inside, with the triple restored once because it was
    removed twice). The union is then measured with `|`, never computed.
    """
    ab_only = n_ab - n_abc
    bc_only = n_bc - n_abc
    ac_only = n_ac - n_abc
    a_only = n_a - n_ab - n_ac + n_abc
    b_only = n_b - n_ab - n_bc + n_abc
    c_only = n_c - n_ac - n_bc + n_abc
    sizes = [n_abc, ab_only, bc_only, ac_only, a_only, b_only, c_only]
    assert all(s >= 0 for s in sizes), f"a Venn region came out negative: {sizes}"
    blocks, start = [], 0
    for size in sizes:
        blocks.append(list(range(start, start + size)))
        start += size
    abc, ab, bc, ac, a_o, b_o, c_o = blocks
    assert start <= n_u, "the three sets do not fit inside the universe"
    outside = list(range(start, n_u))
    a = set(abc) | set(ab) | set(ac) | set(a_o)
    b = set(abc) | set(ab) | set(bc) | set(b_o)
    c = set(abc) | set(bc) | set(ac) | set(c_o)
    u = a | b | c | set(outside)
    assert len(u) == n_u and len(a) == n_a and len(b) == n_b and len(c) == n_c
    assert len(a & b) == n_ab and len(b & c) == n_bc and len(a & c) == n_ac
    assert len(a & b & c) == n_abc
    return u, a, b, c


def exactly_n_of_three(a, b, c, universe, how_many):
    """Count members of `universe` lying in exactly `how_many` of the three sets.

    Membership is tested member by member — no band formula is used.
    """
    return sum(
        1
        for x in universe
        if (x in a) + (x in b) + (x in c) == how_many
    )


def synthetic_divide(coeffs, root):
    """Divide a polynomial (highest power first) by (x - root); return quotient.

    Used to cancel the factor that creates a 0/0 form, exactly, in integers or
    Fractions. Asserts the remainder is zero, so a stem that is not actually of
    the 0/0 form fails rather than returning a quietly wrong quotient.
    """
    out = [coeffs[0]]
    for c in coeffs[1:]:
        out.append(c + out[-1] * root)
    remainder = out.pop()
    assert remainder == 0, f"(x - {root}) is not a factor; remainder {remainder}"
    return out


def poly_at(coeffs, x):
    """Evaluate a polynomial (highest power first) at x."""
    total = 0
    for c in coeffs:
        total = total * x + c
    return total


def two_sided_check(f, a, expected, tol=NUM_TOL):
    """Confirm a limit numerically by approaching `a` from both sides.

    Returns True when both approach values sit within `tol` of `expected`.
    """
    for h in (1e-6, 1e-7):
        left = f(a - h)
        right = f(a + h)
        if abs(left - float(expected)) > tol or abs(right - float(expected)) > tol:
            return False
    return True


# --------------------------------------------- SS 1-2 notation and set types


def q_f3c7_001():
    # ENUMERATION: build the actual set of characters of the word and measure it.
    word = "ASSESSMENT"
    letters = set(word)
    n = len(letters)
    key = {9: "A", 7: "B", 6: "C", 10: "D"}[n]
    return {"answer": key, "computed": n}


def q_f3c7_003():
    # ENUMERATION: test every natural number up to 36 for divisibility, and
    # collect the successes in a real set, so repeated factors cannot be
    # double-counted.
    factors = {n for n in range(1, 37) if 36 % n == 0}
    key = {9: "A", 8: "B", 10: "C", 5: "D"}[len(factors)]
    return {"answer": key, "computed": sorted(factors)}


def q_f3c7_005():
    # ENUMERATION: build the whole numbers 0..6 explicitly. W starts at 0, and
    # the condition is x <= 6, so the member 6 is included.
    s = {x for x in range(0, 100) if x <= 6}
    key = {6: "A", 8: "B", 5: "C", 7: "D"}[len(s)]
    return {"answer": key, "computed": sorted(s)}


# ---------------------------------------- SS 3 subsets and the power set


def q_f3c7_006():
    # ENUMERATION: generate every subset of a 7-element set and count them,
    # rather than evaluating 2**7.
    n = count_subsets(7)
    key = {128: "A", 14: "B", 127: "C", 49: "D"}[n]
    return {"answer": key, "computed": n}


def q_f3c7_007():
    # ENUMERATION: generate every subset of a 6-element set and drop the one
    # that equals the set itself. The empty set is retained, because it is a
    # proper subset of any non-empty set.
    whole = frozenset(range(6))
    proper = [s for s in subsets(range(6)) if s != whole]
    key = {64: "A", 62: "B", 63: "C", 12: "D"}[len(proper)]
    return {"answer": key, "computed": len(proper)}


def q_f3c7_008():
    # SEARCH: increase n until the generated power set has 1,024 members. The
    # relation n(P(A)) = 2**n is confirmed by construction, not assumed.
    target = 1024
    n = next(k for k in range(1, 20) if count_subsets(k) == target)
    key = {512: "A", 10: "B", 32: "C", 11: "D"}[n]
    return {"answer": key, "computed": n}


def q_f3c7_009():
    # ENUMERATION: generate every subset of the 5-element set and drop both the
    # empty set and the set itself.
    items = ["a", "b", "c", "d", "e"]
    whole = frozenset(items)
    kept = [s for s in subsets(items) if s and s != whole]
    key = {32: "A", 31: "B", 10: "C", 30: "D"}[len(kept)]
    return {"answer": key, "computed": len(kept)}


# ------------------------------------ SS 4-5 set operations and set algebra


def q_f3c7_011():
    # ENUMERATION: the three sets are given in roster form, so build them and
    # let Python's own symmetric_difference do the work.
    a = {1, 2, 3, 4, 5, 6}
    b = {4, 5, 6, 7, 8}
    delta = a ^ b
    key = {3: "A", 5: "B", 8: "C", 11: "D"}[len(delta)]
    return {"answer": key, "computed": sorted(delta)}


def q_f3c7_012():
    # ENUMERATION: build concrete sets with the stated cardinalities and take the
    # real difference A - B, instead of applying n(A) - n(A and B).
    _u, a, b = build_two_sets(n_u=200, n_a=48, n_b=35, n_ab=14)
    key = {13: "A", 21: "B", 34: "C", 69: "D"}[len(a - b)]
    return {"answer": key, "computed": len(a - b)}


# --------------------------------------------- SS 6-7 counting with two sets


def q_f3c7_015():
    # ENUMERATION: construct the 240 depositors as labelled members and count the
    # ones lying outside both product sets.
    u, r, f_ = build_two_sets(n_u=240, n_a=145, n_b=96, n_ab=61)
    neither = len(u - (r | f_))
    key = {180: "A", 60: "B", 95: "C", 61: "D"}[neither]
    return {"answer": key, "computed": neither}


def q_f3c7_016():
    # SEARCH: try every possible overlap until the constructed pair really has a
    # union of 620 members. The union is measured, not computed by formula.
    def union_size(k):
        _u, a, b = build_two_sets(n_u=1000, n_a=420, n_b=380, n_ab=k)
        return len(a | b)

    n_ab = next(k for k in range(0, 381) if union_size(k) == 620)
    key = {800: "A", 40: "B", 180: "C", 200: "D"}[n_ab]
    return {"answer": key, "computed": n_ab}


def q_f3c7_017():
    # ENUMERATION: build the 300 employees and count those in exactly one of the
    # two language sets by testing each member.
    u, h, m = build_two_sets(n_u=300, n_a=175, n_b=140, n_ab=60)
    exactly_one = sum(1 for x in u if (x in h) + (x in m) == 1)
    key = {195: "A", 255: "B", 115: "C", 80: "D"}[exactly_one]
    return {"answer": key, "computed": exactly_one}


def q_f3c7_018():
    # ENUMERATION: build the 500 policyholders and count the motor-only region as
    # a real set difference.
    _u, motor, health = build_two_sets(n_u=500, n_a=290, n_b=245, n_ab=118)
    only_motor = len(motor - health)
    key = {45: "A", 127: "B", 417: "C", 172: "D"}[only_motor]
    return {"answer": key, "computed": only_motor}


def q_f3c7_019():
    # SEARCH: try every candidate size for the Paper 2 group and keep the one for
    # which the constructed population really leaves 40 candidates outside both
    # papers, with 360 in all.
    def works(nb):
        try:
            u, p1, p2 = build_two_sets(n_u=360, n_a=210, n_b=nb, n_ab=85)
        except AssertionError:
            return False
        return len(u - (p1 | p2)) == 40

    nb = next(k for k in range(85, 361) if works(k))
    key = {110: "A", 320: "B", 195: "C", 150: "D"}[nb]
    return {"answer": key, "computed": nb}


# ----------------------------------------- SS 8-9 counting with three sets

# The seven-question block q-f3c7-020 to q-f3c7-025 all share one data set. It is
# built once, as a real population of labelled members, and every band is then
# counted by walking that population.
_S3 = dict(n_u=1000, n_a=180, n_b=150, n_c=120, n_ab=70, n_bc=55, n_ac=60, n_abc=30)


def q_f3c7_020():
    # ENUMERATION: measure the union of the three constructed sets with `|`.
    _u, a, b, c = build_three_sets(**_S3)
    union = len(a | b | c)
    key = {450: "A", 295: "B", 235: "C", 265: "D"}[union]
    return {"answer": key, "computed": union}


def q_f3c7_021():
    # ENUMERATION: count members lying in exactly one of the three sets by
    # testing membership member by member.
    u, a, b, c = build_three_sets(**_S3)
    n = exactly_n_of_three(a, b, c, u, 1)
    key = {170: "A", 110: "B", 95: "C", 295: "D"}[n]
    return {"answer": key, "computed": n}


def q_f3c7_022():
    # ENUMERATION: same population, count of members in exactly two sets.
    u, a, b, c = build_three_sets(**_S3)
    n = exactly_n_of_three(a, b, c, u, 2)
    key = {185: "A", 155: "B", 125: "C", 95: "D"}[n]
    return {"answer": key, "computed": n}


def q_f3c7_023():
    # ENUMERATION: members in two OR three sets, counted directly, then
    # cross-checked against the exactly-two plus exactly-three split.
    u, a, b, c = build_three_sets(**_S3)
    n = sum(1 for x in u if (x in a) + (x in b) + (x in c) >= 2)
    assert n == exactly_n_of_three(a, b, c, u, 2) + exactly_n_of_three(a, b, c, u, 3)
    key = {95: "A", 125: "B", 185: "C", 155: "D"}[n]
    return {"answer": key, "computed": n}


def q_f3c7_024():
    # SEARCH: try every candidate triple overlap and keep the one for which the
    # constructed population really leaves 45 firms outside all three sets.
    def works(t):
        try:
            u, x, y, z = build_three_sets(
                n_u=400, n_a=220, n_b=190, n_c=160, n_ab=90, n_bc=75, n_ac=80, n_abc=t
            )
        except AssertionError:
            return False
        return len(u - (x | y | z)) == 45

    t = next(k for k in range(0, 161) if works(k))
    key = {75: "A", 45: "B", 30: "C", 120: "D"}[t]
    return {"answer": key, "computed": t}


def q_f3c7_025():
    # ENUMERATION: the C-only region measured as a real set difference.
    _u, a, b, c = build_three_sets(**_S3)
    only_c = len(c - a - b)
    key = {35: "A", 5: "B", 65: "C", 120: "D"}[only_c]
    return {"answer": key, "computed": only_c}


# ----------------------------- SS 10-12 Cartesian products and relations


def q_f3c7_026():
    # ENUMERATION: generate the ordered pairs with itertools.product and count
    # them, rather than multiplying the two cardinal numbers.
    a = range(7)
    b = "abcde"
    pairs = list(itertools.product(a, b))
    key = {12: "A", 2: "B", 128: "C", 35: "D"}[len(pairs)]
    return {"answer": key, "computed": len(pairs)}


def q_f3c7_027():
    # SEARCH: grow A until the generated product really contains 42 pairs.
    b = range(6)
    n_a = next(
        k for k in range(1, 100) if len(list(itertools.product(range(k), b))) == 42
    )
    key = {36: "A", 7: "B", 48: "C", 252: "D"}[n_a]
    return {"answer": key, "computed": n_a}


def q_f3c7_029():
    # ENUMERATION: a relation from A to B is a subset of A x B, so generate every
    # subset of the 12 pairs and count them. 4,096 objects is small enough to
    # build outright, which is stronger evidence than evaluating 2**12.
    pairs = list(itertools.product(range(4), range(3)))
    n = sum(1 for _ in subsets(pairs))
    key = {4096: "A", 12: "B", 128: "C", 81: "D"}[n]
    return {"answer": key, "computed": n}


def q_f3c7_030():
    # ENUMERATION: generate every subset of the 9 pairs in A x A.
    pairs = list(itertools.product(range(3), repeat=2))
    n = sum(1 for _ in subsets(pairs))
    key = {8: "A", 64: "B", 9: "C", 512: "D"}[n]
    return {"answer": key, "computed": n}


def q_f3c7_031():
    # ENUMERATION: walk all 2**16 on/off patterns over the 16 cells of the grid
    # and keep the ones whose four diagonal cells are switched on. The reflexive
    # relations are counted by being generated, not by a formula.
    cells = list(itertools.product(range(4), repeat=2))
    diagonal = {(i, i) for i in range(4)}
    count = 0
    for pattern in itertools.product((0, 1), repeat=len(cells)):
        relation = {cell for cell, on in zip(cells, pattern) if on}
        if diagonal <= relation:
            count += 1
    key = {65536: "A", 1024: "B", 4096: "C", 16: "D"}[count]
    return {"answer": key, "computed": count}


# ---------------------------------------------- SS 13-15 functions


def q_f3c7_035():
    # ENUMERATION: a function from a 5-set to a 3-set is one choice of image per
    # input, so generate every such tuple with itertools.product and count.
    fns = list(itertools.product(range(3), repeat=5))
    key = {125: "A", 243: "B", 15: "C", 32768: "D"}[len(fns)]
    return {"answer": key, "computed": len(fns)}


def q_f3c7_036():
    # ENUMERATION: generate every function from the 3-set to the 6-set and keep
    # those whose three images are distinct.
    one_one = [
        f_ for f_ in itertools.product(range(6), repeat=3) if len(set(f_)) == 3
    ]
    key = {216: "A", 720: "B", 120: "C", 18: "D"}[len(one_one)]
    return {"answer": key, "computed": len(one_one)}


def q_f3c7_037():
    # ENUMERATION: generate every function from the 5-set to the 3-set and keep
    # those with five distinct images. The count comes out empty on its own.
    one_one = [
        f_ for f_ in itertools.product(range(3), repeat=5) if len(set(f_)) == 5
    ]
    key = {60: "A", 6: "B", 243: "C", 0: "D"}[len(one_one)]
    return {"answer": key, "computed": len(one_one)}


def q_f3c7_039():
    # ENUMERATION: a bijection of a 6-set onto itself is a permutation of it, so
    # generate the permutations and count them.
    perms = list(itertools.permutations(range(6)))
    key = {46656: "A", 720: "B", 64: "C", 36: "D"}[len(perms)]
    return {"answer": key, "computed": len(perms)}


def q_f3c7_040():
    # EXACT ARITHMETIC: apply f first, then g, keeping the values as Fractions so
    # no rounding can hide a slip. The wrong-order value is computed too and
    # asserted to differ, which is the point the distractor tests.
    def f(x):
        return 2 * x + 5

    def g(x):
        return x * x - 1

    value = g(f(F(3)))
    other = f(g(F(3)))
    assert value != other, "the two composites should differ at x = 3"
    key = {F(21): "A", F(122): "B", F(120): "C", F(88): "D"}[value]
    return {"answer": key, "computed": str(value)}


def q_f3c7_041():
    # EXACT ARITHMETIC: solve f(x) = 5 for x with Fractions, then confirm by
    # substituting the answer back into f.
    # f(x) = (4x - 3) / 2, so 4x - 3 = 10 and x = 13/4.
    y = F(5)
    x = (2 * y + 3) / F(4)
    assert (4 * x - 3) / 2 == y, "the inverse value must satisfy f(x) = 5"
    key = {F(17, 2): "A", F(2, 17): "B", F(7, 4): "C", F(13, 4): "D"}[x]
    return {"answer": key, "computed": str(x)}


def q_f3c7_043():
    # EXACT ARITHMETIC: substitute x = -3 directly, and separately confirm the
    # oddness property f(-x) = -f(x) at several points by evaluation.
    def f(x):
        return 5 * x ** 3 - 2 * x

    assert f(F(3)) == 129, "the stem's stated value of f(3) must hold"
    assert all(f(F(-t)) == -f(F(t)) for t in (1, 2, 3, 7)), "f should be odd"
    value = f(F(-3))
    key = {F(129): "A", F(-129): "B", F(-141): "C", F(-135): "D"}[value]
    return {"answer": key, "computed": str(value)}


# ------------------------------------------ SS 16-18 limits and continuity


def q_f3c7_044():
    # EXACT then NUMERICAL. Exact: cancel the factor (x - 5) out of x^2 - 25 by
    # synthetic division and evaluate the quotient at 5, all in Fractions.
    # Numerical: approach 5 from both sides and confirm to within NUM_TOL.
    numerator = [1, 0, -25]  # x^2 + 0x - 25
    quotient = synthetic_divide(numerator, 5)  # -> x + 5
    exact = F(poly_at(quotient, F(5)))
    assert two_sided_check(lambda t: (t * t - 25) / (t - 5), 5.0, exact)
    key = {F(0): "A", F(5): "B", F(10): "C"}[exact]  # option D is 'does not exist'
    return {"answer": key, "computed": str(exact)}


def q_f3c7_045():
    # EXACT then NUMERICAL. Exact: multiply by the conjugate, which turns the
    # expression into 1 / (sqrt(x + 16) + 4); at x = 0 that is 1 / 8 exactly.
    # Numerical: approach 0 from both sides on the ORIGINAL expression.
    exact = F(1, 4 + 4)
    assert two_sided_check(lambda t: ((t + 16) ** 0.5 - 4) / t, 0.0, exact)
    key = {F(1, 8): "A", F(0): "B", F(1, 4): "C", F(8): "D"}[exact]
    return {"answer": key, "computed": str(exact)}


def q_f3c7_046():
    # EXACT then NUMERICAL, by two independent exact routes. Route 1: synthetic
    # division of x^5 - 243 by (x - 3), then evaluate the quotient at 3.
    # Route 2: the standard limit n * a**(n - 1). The two must agree.
    quotient = synthetic_divide([1, 0, 0, 0, 0, -243], 3)
    exact = F(poly_at(quotient, F(3)))
    assert exact == 5 * F(3) ** 4, "the two exact routes must agree"
    assert two_sided_check(lambda t: (t ** 5 - 243) / (t - 3), 3.0, exact, tol=1e-2)
    key = {F(243): "A", F(81): "B", F(15): "C", F(405): "D"}[exact]
    return {"answer": key, "computed": str(exact)}


def q_f3c7_047():
    # EXACT then NUMERICAL. Exact: with equal degrees the limit is the ratio of
    # the leading coefficients, taken as a Fraction. Numerical: evaluate the
    # ratio at increasingly large x and confirm it settles on that value.
    num = [7, 0, 2, 0]  # 7x^3 + 0x^2 + 2x + 0
    den = [3, -1, 0, 5]  # 3x^3 - x^2 + 0x + 5
    assert len(num) == len(den), "the degrees must match for this rule"
    exact = F(num[0], den[0])
    for big in (1e5, 1e6, 1e7):
        ratio = poly_at([float(c) for c in num], big) / poly_at([float(c) for c in den], big)
        assert abs(ratio - float(exact)) < NUM_TOL, ratio
    key = {F(0): "A", F(7, 3): "B", F(3, 7): "D"}[exact]  # option C is 'no finite limit'
    return {"answer": key, "computed": str(exact)}


def q_f3c7_048():
    # NUMERICAL from both sides, using the branch that actually applies at each
    # sample point, so the piecewise definition itself decides the answer.
    def f(x):
        return 3 * x + 2 if x < 4 else x * x - 6

    lhl = round(f(4 - 1e-9), 6)
    rhl = round(f(4 + 1e-9), 6)
    pair = (round(lhl), round(rhl))
    assert abs(lhl - pair[0]) < NUM_TOL and abs(rhl - pair[1]) < NUM_TOL
    key = {(14, 14): "A", (10, 10): "B", (14, 10): "C", (10, 14): "D"}[pair]
    return {"answer": key, "computed": pair}


def q_f3c7_049():
    # SEARCH over exact rationals: try candidate values of k in sixteenths and
    # keep the one for which the left branch value, the right-hand limit and
    # f(3) all coincide. Nothing is solved algebraically.
    def continuous(k):
        left = 2 * F(3) + k          # LHL, and also f(3): the junction is x <= 3
        right = F(3) ** 2 + 4        # RHL from the branch valid above 3
        return left == right

    k = next(F(n, 16) for n in range(-400, 401) if continuous(F(n, 16)))
    key = {F(-7): "A", F(19): "B", F(6): "C", F(7): "D"}[k]
    return {"answer": key, "computed": str(k)}


# ------------------------------- case set 1: three service lines at a CA firm

# One population of 640 labelled clients, built once and counted four ways.
_CS1 = dict(n_u=640, n_a=385, n_b=300, n_c=245, n_ab=165, n_bc=120, n_ac=140, n_abc=75)


def cs_f3c7_01_a():
    # ENUMERATION: measure the union of the three constructed client sets.
    _u, g, t, r = build_three_sets(**_CS1)
    union = len(g | t | r)
    key = {930: "A", 580: "B", 505: "C", 640: "D"}[union]
    return {"answer": key, "computed": union}


def cs_f3c7_01_b():
    # ENUMERATION: count clients lying in exactly one of the three service sets.
    u, g, t, r = build_three_sets(**_CS1)
    n = exactly_n_of_three(g, t, r, u, 1)
    key = {580: "A", 200: "B", 305: "C", 155: "D"}[n]
    return {"answer": key, "computed": n}


def cs_f3c7_01_c():
    # ENUMERATION: count clients lying in exactly two of the three service sets.
    u, g, t, r = build_three_sets(**_CS1)
    n = exactly_n_of_three(g, t, r, u, 2)
    key = {200: "A", 425: "B", 350: "C", 275: "D"}[n]
    return {"answer": key, "computed": n}


def cs_f3c7_01_d():
    # ENUMERATION: the clients outside all three sets, taken as a set difference,
    # then cross-checked against the four bands adding back to 640.
    u, g, t, r = build_three_sets(**_CS1)
    none = len(u - (g | t | r))
    bands = [exactly_n_of_three(g, t, r, u, k) for k in (1, 2, 3)]
    assert sum(bands) + none == 640, "the bands must exhaust the register"
    key = {75: "A", 135: "B", 155: "C", 60: "D"}[none]
    return {"answer": key, "computed": none}


# ---------------------------- case set 2: assigning three zones to four hubs

_ZONES = [1, 2, 3]
_HUBS = ["w", "x", "y", "z"]


def cs_f3c7_02_a():
    # ENUMERATION: generate every subset of the 12 zone-hub pairs and count them.
    pairs = list(itertools.product(_ZONES, _HUBS))
    n = sum(1 for _ in subsets(pairs))
    key = {12: "A", 64: "B", 4096: "C", 128: "D"}[n]
    return {"answer": key, "computed": n}


def cs_f3c7_02_b():
    # ENUMERATION: generate every assignment of one hub to each zone.
    plans = list(itertools.product(_HUBS, repeat=len(_ZONES)))
    key = {81: "A", 64: "B", 12: "C", 24: "D"}[len(plans)]
    return {"answer": key, "computed": len(plans)}


def cs_f3c7_02_c():
    # ENUMERATION: filter the generated plans down to those with no repeated hub.
    plans = [p for p in itertools.product(_HUBS, repeat=len(_ZONES)) if len(set(p)) == 3]
    key = {64: "A", 6: "B", 12: "C", 24: "D"}[len(plans)]
    return {"answer": key, "computed": len(plans)}


def cs_f3c7_02_d():
    # ENUMERATION: test the three properties by walking every element, every pair
    # and every chain of the relation, so no property is asserted on sight.
    s = {(1, 1), (2, 2), (3, 3), (1, 2), (2, 1), (1, 3), (3, 1)}
    reflexive = all((x, x) in s for x in _ZONES)
    symmetric = all((b, a) in s for (a, b) in s)
    transitive = all(
        (a, d) in s for (a, b) in s for (c, d) in s if b == c
    )
    profile = (reflexive, symmetric, transitive)
    key = {
        (True, True, False): "A",
        (True, True, True): "B",
        (False, True, True): "C",
        (True, False, True): "D",
    }[profile]
    return {"answer": key, "computed": profile}


# ------------------------------ case set 3: a two-slab warehouse tariff

_LOWER = lambda x: 250 * x + 1500          # applies for x < 8
_UPPER = lambda x, c: 400 * x + c          # applies for x >= 8
_JUNCTION = 8


def cs_f3c7_03_a():
    # NUMERICAL from the left, using the branch that actually applies below the
    # junction, then rounded to the nearest rupee and confirmed exactly.
    approach = [_LOWER(_JUNCTION - h) for h in (1e-6, 1e-7, 1e-8)]
    lhl = round(approach[-1])
    assert all(abs(v - lhl) < 1e-2 for v in approach), approach
    assert lhl == _LOWER(F(_JUNCTION)), "the exact branch value must agree"
    key = {3200: "A", 1500: "B", 3500: "C", 2000: "D"}[lhl]
    return {"answer": key, "computed": lhl}


def cs_f3c7_03_b():
    # SEARCH over exact rationals: try candidate values of c and keep the one for
    # which the upper branch at the junction equals the lower branch's limit.
    target = _LOWER(F(_JUNCTION))
    c = next(
        F(n, 4)
        for n in range(-40000, 40001)
        if _UPPER(F(_JUNCTION), F(n, 4)) == target
    )
    key = {F(-300): "A", F(300): "B", F(6700): "C", F(1500): "D"}[c]
    return {"answer": key, "computed": str(c)}


def cs_f3c7_03_c():
    # NUMERICAL both sides plus the value at the junction, tested against the
    # three-part definition rather than assumed from part (b).
    c = F(300)

    def h(x):
        return _LOWER(x) if x < _JUNCTION else _UPPER(x, float(c))

    lhl = h(_JUNCTION - 1e-7)
    rhl = h(_JUNCTION + 1e-7)
    value = h(float(_JUNCTION))
    limit_exists = abs(lhl - rhl) < 1e-2
    continuous = limit_exists and abs(value - lhl) < 1e-2
    result = (continuous, round(lhl))
    key = {
        (False, 3500): "A",
        (True, 3200): "B",
        (True, 3500): "C",
    }[result]  # option D claims a limit with a discontinuity, which cannot arise here
    return {"answer": key, "computed": result}
