"""Verifier for foundation/quantitative-aptitude/sequence-and-series.json (P3 Ch 6).

Every function recomputes its answer from the stem's own parameters. Nothing is
copied from the answer key: each computed value is mapped to an option key
through a dict of the four option values, so a wrong key in the bank surfaces as
a KeyError or as a mismatch the runner reports.

METHOD NOTE — why most functions build the sequence instead of using a formula.
The single most common error in this chapter is an off-by-one in the count of
terms (n where n - 1 belongs, a sum taken over one term too many, the last term
of a range mis-identified). Re-running the same closed form the stem used would
reproduce that error silently. So wherever the number of terms is small enough,
these verifiers GENERATE the actual terms one at a time and read or add them:

  * `ap_terms(a, d, n)` and `gp_terms(a, r, n)` build term lists by repeated
    addition and repeated multiplication respectively — never by a power or an
    (n - 1) index — so the term count is proved by construction.
  * A closed form is used only where generation is impossible or meaningless:
    the sum of an INFINITE GP, a recurring decimal, and the arithmetic and
    geometric mean of a pair. Each such function says so in its own comment.
  * Where a stem gives two terms of a progression, the function derives a and d
    (or a and r), rebuilds the whole progression, and ASSERTS that the rebuilt
    progression reproduces both given terms before reading off the answer.

`fractions.Fraction` is used throughout so ratios, percentage growth factors and
sums stay exact; no float ever reaches an option comparison.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

# ------------------------------------------------------------ shared helpers


def ap_terms(a, d, n):
    """The first n terms of an AP, built by repeated addition of d."""
    a, d = F(a), F(d)
    out, cur = [], a
    for _ in range(n):
        out.append(cur)
        cur = cur + d
    return out


def gp_terms(a, r, n):
    """The first n terms of a GP, built by repeated multiplication by r."""
    a, r = F(a), F(r)
    out, cur = [], a
    for _ in range(n):
        out.append(cur)
        cur = cur * r
    return out


def ap_to_last(a, d, last):
    """Every term of an AP from a up to and including `last`, built term by term."""
    a, d, last = F(a), F(d), F(last)
    out, cur = [], a
    while (cur <= last) if d > 0 else (cur >= last):
        out.append(cur)
        cur = cur + d
    assert out[-1] == last, "the stated last term is not a term of this AP"
    return out


def gp_to_last(a, r, last):
    """Every term of a GP from a up to and including `last`, built term by term."""
    a, r, last = F(a), F(r), F(last)
    out, cur = [], a
    while abs(cur) <= abs(last):
        out.append(cur)
        cur = cur * r
    assert out[-1] == last, "the stated last term is not a term of this GP"
    return out


def d_from_two_terms(p, tp, q, tq):
    """Common difference from the pth and qth terms, then verified by rebuilding."""
    d = F(tq - tp, q - p)
    a = F(tp) - (p - 1) * d
    terms = ap_terms(a, d, max(p, q))
    assert terms[p - 1] == tp and terms[q - 1] == tq, "rebuilt AP misses a given term"
    return a, d


def r_from_two_terms(p, tp, q, tq):
    """Positive common ratio from the pth and qth terms, verified by rebuilding."""
    power = q - p
    ratio = F(tq, tp)
    root = round(float(ratio) ** (1.0 / power))
    r = F(root)
    assert r ** power == ratio, "the ratio is not a rational power here"
    a = F(tp) / r ** (p - 1)
    terms = gp_terms(a, r, max(p, q))
    assert terms[p - 1] == tp and terms[q - 1] == tq, "rebuilt GP misses a given term"
    return a, r


def pick(value, mapping):
    """Map a computed value to the option key that carries it."""
    return mapping[value]


# ------------------------------------------------- sequences, series, the general term


def q_f3c6_002():
    # GENERATED: the ten terms of a_n = 4n + 5 are written out and the last is read,
    # so the position is proved by the length of the list rather than by an index.
    terms = [4 * n + 5 for n in range(1, 11)]
    assert len(terms) == 10
    value = F(terms[-1])
    return {"answer": pick(value, {F(41): "A", F(45): "B", F(49): "C", F(270): "D"}),
            "computed": str(value)}


def q_f3c6_003():
    # GENERATED: the six terms of a_n = 3n - 1 are built and added one at a time.
    terms = [3 * n - 1 for n in range(1, 7)]
    total = F(sum(terms))
    return {"answer": pick(total, {F(57): "A", F(17): "B", F(40): "C", F(66): "D"}),
            "computed": "%s from %s" % (total, terms)}


def q_f3c6_004():
    # GENERATED: each option's successive ratios are computed; a GP is the option
    # whose ratios are all equal. Two pairs at least are checked, never one.
    lists = {"A": [3, 6, 9, 12], "B": [2, 6, 18, 54], "C": [5, 10, 16, 23], "D": [1, 4, 9, 16]}
    gps = [k for k, xs in lists.items()
           if len({F(xs[i + 1], xs[i]) for i in range(len(xs) - 1)}) == 1]
    assert len(gps) == 1, "exactly one option should be a GP"
    return {"answer": gps[0], "computed": "constant-ratio option %s" % gps[0]}


# ------------------------------------------------------------ AP: the nth term


def q_f3c6_005():
    # GENERATED: 24 terms of 8, 15, 22, ... are built by repeated addition.
    terms = ap_terms(8, 15 - 8, 24)
    value = terms[-1]
    return {"answer": pick(value, {F(176): "A", F(162): "B", F(169): "C", F(2124): "D"}),
            "computed": str(value)}


def q_f3c6_006():
    # GENERATED: 30 terms with a negative d, built by repeated addition.
    terms = ap_terms(250, -7, 30)
    value = terms[-1]
    return {"answer": pick(value, {F(40): "A", F(54): "B", F(4455): "C", F(47): "D"}),
            "computed": str(value)}


def q_f3c6_007():
    # GENERATED + CHECKED: d and a are derived, then the AP is rebuilt and both
    # given terms are asserted before the first term is read off.
    a, d = d_from_two_terms(5, 41, 12, 90)
    return {"answer": pick(a, {F(13): "A", F(6): "B", F(20): "C", F(7): "D"}),
            "computed": "a=%s, d=%s" % (a, d)}


def q_f3c6_008():
    # GENERATED + CHECKED: rebuild the AP to 25 terms and read the last one.
    a, d = d_from_two_terms(10, 52, 16, 82)
    terms = ap_terms(a, d, 25)
    value = terms[-1]
    return {"answer": pick(value, {F(127): "A", F(132): "B", F(122): "C", F(142): "D"}),
            "computed": str(value)}


def q_f3c6_009():
    # GENERATED from the sum formula the stem gives: every term is rebuilt as the
    # difference of two consecutive sums, so the 8th term is the 8th entry of a
    # list rather than the value of a re-derived closed form.
    def S(n):
        return F(3 * n * n + 5 * n)

    terms = [S(n) - S(n - 1) for n in range(1, 10)]
    assert sum(terms[:8]) == S(8), "the rebuilt terms must add back to S8"
    value = terms[7]
    return {"answer": pick(value, {F(232): "A", F(50): "B", F(44): "C", F(56): "D"}),
            "computed": str(value)}


def q_f3c6_010():
    # GENERATED: terms of 5, 11, 17, ... are produced until 251 appears, and the
    # answer is the length of the list — the count itself, with no "+ 1" to forget.
    terms, cur = [], F(5)
    while cur <= 251:
        terms.append(cur)
        cur += 6
    assert terms[-1] == 251
    position = F(len(terms))
    return {"answer": pick(position, {F(41): "A", F(42): "B", F(43): "C", F(40): "D"}),
            "computed": "position %s" % position}


# --------------------------------------------------------- AP: the sum of n terms


def q_f3c6_011():
    # GENERATED: 20 terms of 7, 12, 17, ... are built and added.
    terms = ap_terms(7, 5, 20)
    total = sum(terms)
    return {"answer": pick(total, {F(102): "A", F(1140): "B", F(1090): "C", F(988): "D"}),
            "computed": str(total)}


def q_f3c6_012():
    # GENERATED: d is recovered from the 15 terms spanning 12 to 96, the AP is
    # rebuilt, its last term is asserted to be 96, and the terms are then added.
    n, a, last = 15, 12, 96
    d = F(last - a, n - 1)
    terms = ap_terms(a, d, n)
    assert terms[-1] == last
    total = sum(terms)
    return {"answer": pick(total, {F(756): "A", F(1620): "B", F(108): "C", F(810): "D"}),
            "computed": str(total)}


def q_f3c6_013():
    # GENERATED: every multiple of 6 strictly between 50 and 300 is listed, then added.
    terms = [F(k) for k in range(51, 300) if k % 6 == 0]
    total = sum(terms)
    return {"answer": pick(total, {F(6960): "A", F(7308): "B", F(7134): "C", F(41): "D"}),
            "computed": "%s over %d terms" % (total, len(terms))}


def q_f3c6_014():
    # GENERATED: terms of 3, 7, 11, ... are accumulated until the running total
    # reaches 300; the answer is how many terms that took.
    total, count, cur = F(0), 0, F(3)
    while total < 300:
        total += cur
        count += 1
        cur += 4
    assert total == 300, "the running total must land exactly on 300"
    value = F(count)
    return {"answer": pick(value, {F(12): "A", F(11): "B", F(13): "C", F(-25, 2): "D"}),
            "computed": "%s terms" % value}


def q_f3c6_015():
    # GENERATED: 25 terms of a falling AP are built and added; the negative terms
    # are kept in the list, which is exactly what the formula would also do.
    terms = ap_terms(90, -4, 25)
    total = sum(terms)
    return {"answer": pick(total, {F(1000): "A", F(-6): "B", F(1040): "C", F(1050): "D"}),
            "computed": "%s, last term %s" % (total, terms[-1])}


def q_f3c6_016():
    # GENERATED + CHECKED: a and d come from the two given terms, the AP is rebuilt
    # to 20 terms with both given terms asserted, and the 20 terms are added.
    a, d = d_from_two_terms(5, 26, 12, 61)
    terms = ap_terms(a, d, 20)
    total = sum(terms)
    return {"answer": pick(total, {F(1120): "A", F(1070): "B", F(101): "C", F(969): "D"}),
            "computed": str(total)}


# ------------------------------------------------ AP: counting from the end and in a range


def q_f3c6_017():
    # GENERATED: the whole AP up to 201 is written out and the 7th entry from the
    # end is read with a negative index, so no "n - 1" is ever computed by hand.
    terms = ap_to_last(6, 5, 201)
    value = terms[-7]
    return {"answer": pick(value, {F(166): "A", F(176): "B", F(171): "C", F(34): "D"}),
            "computed": "%s (%d terms in all)" % (value, len(terms))}


def q_f3c6_018():
    # GENERATED: same method — build the full AP, index from the end.
    terms = ap_to_last(7, 6, 205)
    value = terms[-4]
    return {"answer": pick(value, {F(181): "A", F(193): "B", F(34): "C", F(187): "D"}),
            "computed": "%s (%d terms in all)" % (value, len(terms))}


def q_f3c6_019():
    # GENERATED: the twelve products k(k + 1) are built and added directly, which
    # tests the closed form Sk^2 + Sk rather than repeating it.
    terms = [F(k * (k + 1)) for k in range(1, 13)]
    total = sum(terms)
    return {"answer": pick(total, {F(728): "A", F(650): "B", F(78): "C", F(156): "D"}),
            "computed": str(total)}


def q_f3c6_020():
    # GENERATED: terms of 12, 19, 26, ... are produced while they stay under 500,
    # and those strictly above 100 are counted. Generation removes the "+ 1" risk.
    terms, cur = [], F(12)
    while cur < 500:
        terms.append(cur)
        cur += 7
    inside = [t for t in terms if t > 100]
    value = F(len(inside))
    return {"answer": pick(value, {F(56): "A", F(70): "B", F(57): "C", F(58): "D"}),
            "computed": "%s terms, from %s to %s" % (value, inside[0], inside[-1])}


def q_f3c6_021():
    # GENERATED: the fifteen cubes are built and added, which is an independent
    # test of the identity Sn^3 = (Sn)^2 rather than an application of it.
    total = sum(F(k) ** 3 for k in range(1, 16))
    return {"answer": pick(total, {F(1240): "A", F(14400): "B", F(120): "C", F(3375): "D"}),
            "computed": str(total)}


def q_f3c6_022():
    # GENERATED: weekly output is produced week by week until it reaches 150; the
    # answer is the number of weeks generated, so no rounding rule is applied.
    week, output = 1, F(45)
    while output < 150:
        week += 1
        output += 6
    value = F(week)
    return {"answer": pick(value, {F(18): "A", F(17): "B", F(26): "C", F(19): "D"}),
            "computed": "week %s at %s units" % (value, output)}


# --------------------------------------------- AP: equidistant terms and arithmetic means


def q_f3c6_023():
    # GENERATED over several progressions: the stem fixes only T5 + T20 = 96, so
    # the function builds three different 24-term APs that satisfy it and checks
    # that all three give the same total. That proves the equidistant property
    # instead of assuming it.
    totals = set()
    for d in (F(2), F(5), F(-3)):
        a = (F(96) - 23 * d) / 2
        terms = ap_terms(a, d, 24)
        assert terms[4] + terms[19] == 96
        totals.add(sum(terms))
    assert len(totals) == 1, "the sum must not depend on which AP was chosen"
    total = totals.pop()
    return {"answer": pick(total, {F(1152): "A", F(2304): "B", F(96): "C", F(1248): "D"}),
            "computed": str(total)}


def q_f3c6_024():
    # GENERATED over several progressions: only the 8th of 15 terms is fixed at 34.
    totals = set()
    for d in (F(3), F(7), F(-2)):
        a = F(34) - 7 * d
        terms = ap_terms(a, d, 15)
        assert terms[7] == 34
        totals.add(sum(terms))
    assert len(totals) == 1
    total = totals.pop()
    return {"answer": pick(total, {F(255): "A", F(68): "B", F(510): "C", F(1020): "D"}),
            "computed": str(total)}


def q_f3c6_025():
    # FORMULA (nothing to generate): a single arithmetic mean is a definition,
    # A = (a + b) / 2, solved for the unknown member of the pair.
    other = 2 * F(46) - 19
    assert (F(19) + other) / 2 == 46
    return {"answer": pick(other, {F(27): "A", F(73): "B", F(65): "C", F(65, 2): "D"}),
            "computed": str(other)}


def q_f3c6_026():
    # GENERATED: the whole AP of 6 + 2 = 8 terms is built with d recovered from the
    # endpoints, the endpoint 44 is asserted, and the third INSERTED term is read
    # at index 3 — the endpoints are excluded by construction, not by arithmetic.
    a, b, n_means = F(9), F(44), 6
    d = (b - a) / (n_means + 1)
    terms = ap_terms(a, d, n_means + 2)
    assert terms[-1] == b
    means = terms[1:-1]
    assert len(means) == n_means
    value = means[2]
    return {"answer": pick(value, {F(53, 2): "A", F(19): "B", F(29): "C", F(24): "D"}),
            "computed": "%s from means %s" % (value, [str(m) for m in means])}


def q_f3c6_027():
    # GENERATED by search: for each candidate n the AP is built, the inserted means
    # are summed, and the n whose means total 675 is returned. No formula for the
    # sum of the means is used, so the formula in the notes is independently tested.
    hits = []
    for n in range(1, 61):
        d = (F(85) - F(5)) / (n + 1)
        terms = ap_terms(F(5), d, n + 2)
        assert terms[-1] == 85
        if sum(terms[1:-1]) == 675:
            hits.append(n)
    assert len(hits) == 1, "exactly one count of means should fit"
    value = F(hits[0])
    return {"answer": pick(value, {F(15): "A", F(13): "B", F(17): "C", F(30): "D"}),
            "computed": "%s means" % value}


# ------------------------------------------------------------ GP: the nth term


def q_f3c6_028():
    # GENERATED: 7 terms of 3, 12, 48, ... built by repeated multiplication.
    terms = gp_terms(3, F(12, 3), 7)
    value = terms[-1]
    return {"answer": pick(value, {F(49152): "A", F(3072): "B", F(12288): "C", F(16383): "D"}),
            "computed": str(value)}


def q_f3c6_029():
    # GENERATED: 9 terms of 1024, 512, 256, ... built by repeated halving.
    terms = gp_terms(1024, F(512, 1024), 9)
    value = terms[-1]
    return {"answer": pick(value, {F(2): "A", F(8): "B", F(2044): "C", F(4): "D"}),
            "computed": str(value)}


def q_f3c6_030():
    # GENERATED: five yearly figures are built by multiplying by 1 + 20/100 each
    # time, so the number of growth periods equals the number of steps taken.
    r = 1 + F(20, 100)
    terms = gp_terms(12500, r, 5)
    value = terms[-1]
    return {"answer": pick(value, {F(31104): "A", F(25920): "B", F(21600): "C", F(93020): "D"}),
            "computed": "%s from %s" % (value, [str(t) for t in terms])}


def q_f3c6_031():
    # GENERATED + CHECKED: a and r are derived from the 3rd and 6th terms, the GP is
    # rebuilt to 8 terms with both given terms asserted, and the last is read.
    a, r = r_from_two_terms(3, 45, 6, 1215)
    terms = gp_terms(a, r, 8)
    value = terms[-1]
    return {"answer": pick(value, {F(10935): "A", F(32805): "B", F(3645): "C", F(3): "D"}),
            "computed": "%s (a=%s, r=%s)" % (value, a, r)}


def q_f3c6_032():
    # GENERATED: 5 terms built by multiplying by the RATIO 18/6, which is what
    # makes this an independent check on the ratio-versus-difference confusion.
    terms = gp_terms(6, F(18, 6), 5)
    value = terms[-1]
    return {"answer": pick(value, {F(54): "A", F(1458): "B", F(486): "C", F(162): "D"}),
            "computed": str(value)}


def q_f3c6_033():
    # GENERATED + CHECKED: a and r come from the 5th and 8th terms; the rebuilt GP
    # must reproduce both before the first term is reported.
    a, r = r_from_two_terms(5, 80, 8, 640)
    return {"answer": pick(a, {F(2): "A", F(10): "B", F(5, 2): "C", F(5): "D"}),
            "computed": "a=%s, r=%s" % (a, r)}


# --------------------------------------------------------- GP: the sum of n terms


def q_f3c6_034():
    # GENERATED: 8 terms of 2, 6, 18, ... are built and added, which is a stronger
    # check than re-running a(r^n - 1) / (r - 1) with the same n.
    terms = gp_terms(2, 3, 8)
    total = sum(terms)
    return {"answer": pick(total, {F(4374): "A", F(6560): "B", F(19682): "C", F(2186): "D"}),
            "computed": str(total)}


def q_f3c6_035():
    # GENERATED: 7 terms of 128, 64, 32, ... built and added exactly as Fractions.
    terms = gp_terms(128, F(1, 2), 7)
    total = sum(terms)
    return {"answer": pick(total, {F(254): "A", F(2): "B", F(255): "C", F(252): "D"}),
            "computed": str(total)}


def q_f3c6_036():
    # GENERATED: with r = 1 the nine terms are simply nine copies of 15, and adding
    # them avoids the zero denominator the two standard forms would produce.
    terms = gp_terms(15, 1, 9)
    assert len(set(terms)) == 1
    total = sum(terms)
    return {"answer": pick(total, {F(15): "B", F(135): "C", F(120): "D"}),
            "computed": "%s over %d equal terms" % (total, len(terms))}


def q_f3c6_037():
    # GENERATED: terms are produced from 5 by repeated multiplication until 1215 is
    # reached, the last term is asserted, and the list is added.
    terms = gp_to_last(5, 3, 1215)
    total = sum(terms)
    return {"answer": pick(total, {F(1215): "A", F(605): "B", F(3640): "C", F(1820): "D"}),
            "computed": "%s over %d terms" % (total, len(terms))}


# ---------------------------------------------------------------- infinite GPs


def q_f3c6_038():
    # FORMULA, necessarily: an infinite sum cannot be generated. The closed form is
    # used only after |r| < 1 is asserted, and the partial sums are then checked to
    # be climbing towards the computed limit without passing it.
    a, r = F(45), F(15, 45)
    assert abs(r) < 1
    limit = a / (1 - r)
    partials = gp_terms(a, r, 20)
    running = F(0)
    for t in partials:
        running += t
        assert running < limit
    return {"answer": pick(limit, {F(135): "A", F(135, 2): "B", F(30): "C", F(45, 2): "D"}),
            "computed": str(limit)}


def q_f3c6_039():
    # CONDITION TEST: each option's ratio is computed from its own first two terms
    # and |r| < 1 is applied; exactly one option should pass.
    ratios = {"A": F(10, 5), "B": F(-6, 3), "C": F(-4, 12), "D": F(7, 7)}
    convergent = [k for k, r in ratios.items() if abs(r) < 1]
    assert len(convergent) == 1
    return {"answer": convergent[0],
            "computed": "ratios %s" % {k: str(v) for k, v in ratios.items()}}


def q_f3c6_040():
    # FORMULA run backwards, then GENERATED as a check: r is solved from
    # S = a / (1 - r), and the first 40 terms of the resulting GP are added to
    # confirm the running total is approaching 60.
    a, s_inf = F(15), F(60)
    r = 1 - a / s_inf
    assert abs(r) < 1
    running = sum(gp_terms(a, r, 40))
    assert running < s_inf and s_inf - running < F(1, 100)
    return {"answer": pick(r, {F(3, 4): "A", F(1, 4): "B", F(4): "C", F(-3): "D"}),
            "computed": str(r)}


def q_f3c6_041():
    # FORMULA, necessarily (an endless decimal cannot be generated), but the result
    # is checked back against the decimal expansion of the fraction.
    a, r = F(36, 100), F(1, 100)
    value = a / (1 - r)
    digits = ""
    num, den = value.numerator, value.denominator
    for _ in range(8):
        num *= 10
        digits += str(num // den)
        num %= den
    assert digits == "36363636", "the fraction must expand back to 0.363636..."
    return {"answer": pick(value, {F(9, 25): "A", F(2, 5): "B", F(4, 9): "C", F(4, 11): "D"}),
            "computed": "%s = 0.%s..." % (value, digits)}


def q_f3c6_042():
    # CONDITION TEST: the ratio is computed and |r| < 1 is applied. The options are
    # described by what each CLAIMS, so the key follows from the truth of the claim
    # rather than from any stored answer.
    r = F(8, 4)
    claims = {"A": "finite", "B": "none", "C": "finite", "D": "finite"}
    verdict = "finite" if abs(r) < 1 else "none"
    keys = [k for k, c in claims.items() if c == verdict]
    assert len(keys) == 1
    return {"answer": keys[0], "computed": "r=%s, |r|>=1 so no sum" % r}


def q_f3c6_043():
    # GENERATED: the whole GP up to 2,560 is written out and indexed from the end.
    terms = gp_to_last(5, 2, 2560)
    value = terms[-3]
    return {"answer": pick(value, {F(320): "A", F(1280): "B", F(640): "C", F(20): "D"}),
            "computed": "%s (%d terms in all)" % (value, len(terms))}


# ------------------------------------------------- geometric means and the AM-GM relation


def q_f3c6_044():
    # FORMULA (a mean of two numbers has nothing to generate), with the result
    # checked by confirming that 8, G, 32 really do have a constant ratio.
    a, b = 8, 32
    g = F(math.isqrt(a * b))
    assert g * g == a * b
    assert F(g, a) == F(b, g)
    return {"answer": pick(g, {F(16): "A", F(20): "B", F(256): "C", F(40): "D"}),
            "computed": str(g)}


def q_f3c6_045():
    # GENERATED: the GP of 3 + 2 = 5 terms is built with r found from the endpoints,
    # the endpoint 1,250 is asserted, and the FIRST inserted term is read at index 1.
    a, b, n_means = F(2), F(1250), 3
    r = F(round((b / a) ** (1.0 / (n_means + 1))))
    assert a * r ** (n_means + 1) == b
    terms = gp_terms(a, r, n_means + 2)
    assert terms[-1] == b
    means = terms[1:-1]
    assert len(means) == n_means
    value = means[0]
    return {"answer": pick(value, {F(50): "A", F(626): "C", F(10): "D"}),
            "computed": "%s from means %s" % (value, [str(m) for m in means])}


def q_f3c6_046():
    # OPTION TEST: each offered pair is checked against BOTH conditions, AM = 15 and
    # GM = 12. Exactly one pair should satisfy them, and the quadratic is not needed.
    pairs = {"A": (20, 10), "B": (24, 6), "C": (18, 12), "D": (27, 3)}
    fits = [k for k, (x, y) in pairs.items() if F(x + y, 2) == 15 and x * y == 144]
    assert len(fits) == 1
    x, y = pairs[fits[0]]
    return {"answer": fits[0], "computed": "%d and %d, AM=%s, GM=%s" % (x, y, F(x + y, 2), math.isqrt(x * y))}


# --------------------------------------- symmetrical forms and the special series


def q_f3c6_048():
    # GENERATED by search: every candidate triple a - d, a, a + d with 3a = 45 is
    # built and both stated conditions are checked on the actual terms.
    a = F(45, 3)
    fits = []
    for d in range(0, 60):
        terms = [a - d, a, a + d]
        if sum(terms) == 45 and terms[0] * terms[1] * terms[2] == 3000:
            fits.append(terms)
    assert len(fits) == 1, "one non-negative spacing should fit"
    largest = max(fits[0])
    return {"answer": pick(largest, {F(20): "A", F(15): "B", F(10): "C", F(40): "D"}),
            "computed": "%s from %s" % (largest, [str(t) for t in fits[0]])}


def q_f3c6_049():
    # GENERATED by search: candidate ratios p/q are tried, the triple a/r, a, ar is
    # built with a from the product, and both stated conditions are checked.
    a = F(round(216 ** (1.0 / 3)))
    assert a ** 3 == 216
    found = None
    for p in range(1, 13):
        for q in range(1, 13):
            r = F(p, q)
            terms = [a / r, a, a * r]
            if terms[0] * terms[1] * terms[2] == 216 and sum(terms) == 26:
                cand = sorted(terms)
                if found is None:
                    found = cand
                assert found == cand, "all fitting ratios must give the same triple"
    assert found is not None
    smallest = found[0]
    return {"answer": pick(smallest, {F(6): "A", F(18): "B", F(3): "C", F(2): "D"}),
            "computed": "%s from %s" % (smallest, [str(t) for t in found])}


def q_f3c6_050():
    # GENERATED: the twenty-five squares are built and added, an independent test of
    # n(n + 1)(2n + 1) / 6 rather than a repeat of it.
    total = sum(F(k) ** 2 for k in range(1, 26))
    return {"answer": pick(total, {F(325): "A", F(105625): "B", F(5525): "C", F(6201): "D"}),
            "computed": str(total)}


# --------------------------------------------------- case set 01: production build-up

CS01_A, CS01_D, CS01_N = 3400, 260, 24


def q_f3c6_cs01_terms(n):
    return ap_terms(CS01_A, CS01_D, n)


def cs_f3c6_01_a():
    # GENERATED: 18 monthly figures built by repeated addition; the last is read.
    value = q_f3c6_cs01_terms(18)[-1]
    return {"answer": pick(value, {F(7820): "A", F(8080): "B", F(7560): "C", F(100980): "D"}),
            "computed": str(value)}


def cs_f3c6_01_b():
    # GENERATED: the same 18 figures are added one at a time.
    total = sum(q_f3c6_cs01_terms(18))
    return {"answer": pick(total, {F(7820): "A", F(103320): "B", F(93160): "C", F(100980): "D"}),
            "computed": str(total)}


def cs_f3c6_01_c():
    # GENERATED: months are produced until output reaches 9,000, and the answer is
    # how many months were generated — no rounding rule is applied by hand.
    month, output = 1, F(CS01_A)
    while output < 9000:
        month += 1
        output += CS01_D
    value = F(month)
    return {"answer": pick(value, {F(23): "A", F(22): "B", F(21): "C", F(35): "D"}),
            "computed": "month %s at %s pieces" % (value, output)}


def cs_f3c6_01_d():
    # GENERATED: all 24 monthly figures are built and months 7 and 18 are added
    # directly, which tests the equidistant property instead of relying on it.
    terms = q_f3c6_cs01_terms(CS01_N)
    value = terms[6] + terms[17]
    assert value == terms[0] + terms[-1], "positions 7 and 18 must be equidistant"
    return {"answer": pick(value, {F(15640): "A", F(6800): "B", F(12780): "C", F(17200): "D"}),
            "computed": "%s (%s + %s)" % (value, terms[6], terms[17])}


# ------------------------------------------- case set 02: growth and managed decline

CS02_A, CS02_R = 25000, 1 + F(40, 100)


def cs_f3c6_02_a():
    # GENERATED: five year-end counts built by repeated multiplication by 1.4.
    terms = gp_terms(CS02_A, CS02_R, 5)
    value = terms[-1]
    return {"answer": pick(value, {F(134456): "A", F(96040): "B", F(68600): "C", F(273640): "D"}),
            "computed": "%s from %s" % (value, [str(t) for t in terms])}


def cs_f3c6_02_b():
    # GENERATED: the same five counts are added one at a time.
    total = sum(gp_terms(CS02_A, CS02_R, 5))
    return {"answer": pick(total, {F(96040): "A", F(177600): "B", F(408096): "C", F(273640): "D"}),
            "computed": str(total)}


def cs_f3c6_02_c():
    # FORMULA, necessarily: an endless decline cannot be generated. |r| < 1 is
    # asserted first, and the partial sums are checked to approach the limit.
    a, r = F(9600000), F(3, 4)
    assert abs(r) < 1
    limit = a / (1 - r)
    running = sum(gp_terms(a, r, 120))
    assert running < limit and limit - running < 1
    return {"answer": pick(limit, {F(38400000): "A", F(12800000): "B",
                                   F(7200000): "C", F(28800000): "D"}),
            "computed": str(limit)}


# ----------------------------------------------- case set 03: seating layouts

CS03_A, CS03_D, CS03_ROWS = 26, 5, 28


def cs_f3c6_03_a():
    # GENERATED: 28 row counts built by repeated addition; the last is read.
    value = ap_terms(CS03_A, CS03_D, CS03_ROWS)[-1]
    return {"answer": pick(value, {F(166): "A", F(156): "B", F(161): "C", F(2618): "D"}),
            "computed": str(value)}


def cs_f3c6_03_b():
    # GENERATED: the same 28 row counts are added one at a time.
    total = sum(ap_terms(CS03_A, CS03_D, CS03_ROWS))
    return {"answer": pick(total, {F(161): "A", F(2618): "B", F(2688): "C", F(2457): "D"}),
            "computed": str(total)}


def cs_f3c6_03_c():
    # FORMULA plus a GENERATED check: the geometric mean is computed as the root of
    # the product, and the three row counts are then confirmed to be a real GP.
    a, b = 18, 50
    g = F(math.isqrt(a * b))
    assert g * g == a * b
    assert F(g, a) == F(b, g)
    return {"answer": pick(g, {F(34): "A", F(900): "B", F(32): "C", F(30): "D"}),
            "computed": str(g)}
