"""Verifier for foundation/quantitative-aptitude/number-series-coding-decoding.json
(P3 Part B, Ch 9 — Number Series, Coding and Decoding and Odd Man Out).

Every function recomputes its answer from the stem's own parameters. Nothing is
copied from the answer key: each computed value (a number, or a coded string) is
mapped to an option key through a dict of the four option values, so a wrong key
in the bank surfaces as a KeyError or as a mismatch the runner reports.

Only questions flagged `"numerical": true` in the bank have a function here. The
pure-judgement items (odd-man-out reasoning, "which rule/statement fits",
substitution languages) carry `"numerical": false` and are checked by the
consistency pass, not by this module.

Conventions:
  * `pos(ch)` is the 1-based place value of a letter, A = 1 ... Z = 26.
  * `letter(n)` inverts it, wrapping into 1..26 first, so a shift past either end
    of the alphabet is handled the same way every time.
  * `shift(word, k)` shifts every letter of `word` forward by k places (k may be
    negative), with wrap-around; it is used for both the forward and backward
    letter-shift codes.
  * Series answers are derived from the given terms (differences, ratios or the
    stated two-step rule), never hard-coded, so a mistyped stem would surface.
"""

from __future__ import annotations

# ---------------------------------------------------------------- letter helpers


def pos(ch):
    """Place value of a single letter, A = 1 ... Z = 26."""
    return ord(ch.upper()) - ord("A") + 1


def letter(n):
    """Inverse of pos(), wrapping n into 1..26 first."""
    return chr((n - 1) % 26 + ord("A"))


def shift(word, k):
    """Shift each letter of `word` by k places along the alphabet, with wrap."""
    return "".join(letter(pos(c) + k) for c in word)


def reverse(word):
    return word[::-1]


def position_code(word, sep="-"):
    """Each letter written as its place value, joined by `sep`."""
    return sep.join(str(pos(c)) for c in word)


def reverse_position_code(word, sep="-"):
    """Each letter written as (27 - place value): A = 26 ... Z = 1."""
    return sep.join(str(27 - pos(c)) for c in word)


def value_sum(word):
    """Sum of the letters' place values."""
    return sum(pos(c) for c in word)


def next_by_constant_diff(seq):
    """Next term of an arithmetic series, verifying the difference is constant."""
    diffs = [b - a for a, b in zip(seq, seq[1:])]
    assert len(set(diffs)) == 1, "the difference is not constant"
    return seq[-1] + diffs[0]


def next_by_diff_series(seq, step):
    """Next term when the difference row is itself arithmetic with the given step."""
    diffs = [b - a for a, b in zip(seq, seq[1:])]
    inner = [b - a for a, b in zip(diffs, diffs[1:])]
    assert set(inner) == {step}, "the difference row does not rise by the given step"
    return seq[-1] + diffs[-1] + step


def next_by_ratio(seq, ratio):
    """Next term of a geometric series, verifying the ratio."""
    for a, b in zip(seq, seq[1:]):
        assert b == a * ratio, "the ratio is not constant"
    return seq[-1] * ratio


# --------------------------------------------------------------- number series


def q_f3c9_001():
    nxt = next_by_constant_diff([4, 11, 18, 25])
    key = {30: "A", 31: "B", 32: "C", 33: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_002():
    nxt = next_by_diff_series([3, 5, 9, 15, 23], 2)
    key = {31: "A", 32: "B", 33: "C", 35: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_003():
    nxt = next_by_diff_series([2, 6, 12, 20, 30], 2)
    key = {40: "A", 42: "B", 44: "C", 38: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_004():
    nxt = next_by_diff_series([100, 92, 85, 79, 74], 1)
    key = {69: "A", 70: "B", 71: "C", 68: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_005():
    nxt = next_by_ratio([2, 6, 18, 54], 3)
    key = {108: "A", 162: "B", 150: "C", 216: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_006():
    seq = [96, 48, 24, 12]
    for a, b in zip(seq, seq[1:]):
        assert a == b * 2, "each term is not twice the next"
    nxt = seq[-1] // 2
    key = {6: "A", 8: "B", 4: "C", 10: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_007():
    # multipliers 2, 3, 4, 5 -> next is 6
    seq = [1, 2, 6, 24, 120]
    mults = [b // a for a, b in zip(seq, seq[1:])]
    assert mults == [2, 3, 4, 5], "the multiplier does not climb 2,3,4,5"
    nxt = seq[-1] * (mults[-1] + 1)
    key = {600: "A", 720: "B", 840: "C", 620: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_008():
    # rule: multiply by 2 and add 1
    seq = [3, 7, 15, 31]
    for a, b in zip(seq, seq[1:]):
        assert b == a * 2 + 1, "the rule x2+1 does not hold"
    nxt = seq[-1] * 2 + 1
    key = {47: "A", 62: "B", 63: "C", 61: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_009():
    # rule: multiply by 3 and subtract 2
    seq = [5, 13, 37, 109]
    for a, b in zip(seq, seq[1:]):
        assert b == a * 3 - 2, "the rule x3-2 does not hold"
    nxt = seq[-1] * 3 - 2
    key = {321: "A", 327: "B", 325: "C", 323: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_010():
    # terms are the squares 1..5, next is 6^2
    seq = [1, 4, 9, 16, 25]
    assert seq == [n * n for n in range(1, 6)]
    nxt = 6 * 6
    key = {30: "A", 35: "B", 36: "C", 49: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_012():
    # terms are the cubes 1..4, next is 5^3
    seq = [1, 8, 27, 64]
    assert seq == [n ** 3 for n in range(1, 5)]
    nxt = 5 ** 3
    key = {100: "A", 125: "B", 121: "C", 216: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_014():
    # terms are n^2 - 1 for n = 1..5, next is 6^2 - 1
    seq = [0, 3, 8, 15, 24]
    assert seq == [n * n - 1 for n in range(1, 6)]
    nxt = 6 * 6 - 1
    key = {33: "A", 34: "B", 35: "C", 48: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_015():
    # 1, 5, 2, 10, 3, 15, ?  -> odd positions 1,2,3 ; even positions 5,10,15
    odd = [1, 2, 3]      # 1st, 3rd, 5th terms
    # the 7th term is the 4th odd-position term, continuing 1,2,3 by +1
    nxt = odd[-1] + 1
    key = {4: "A", 20: "B", 18: "C", 6: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_016():
    # operations cycle +1, +4 ; six terms means five gaps used, next gap index 5
    start = 5
    ops = [1, 4]
    terms = [start]
    for i in range(5):
        terms.append(terms[-1] + ops[i % 2])
    assert terms == [5, 6, 10, 11, 15, 16]
    nxt = terms[-1] + ops[5 % 2]
    key = {17: "A", 20: "B", 21: "C", 19: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_017():
    # Fibonacci-type: each term the sum of the two before
    seq = [2, 3, 5, 8, 13]
    for a, b, c in zip(seq, seq[1:], seq[2:]):
        assert c == a + b, "the sum rule does not hold"
    nxt = seq[-2] + seq[-1]
    key = {18: "A", 20: "B", 21: "C", 26: "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_019():
    # 7, 14, ?, 28, 35 ; constant difference from the known terms
    known = [7, 14, 28, 35]
    d = 14 - 7
    assert 35 - 28 == d, "the outer differences disagree"
    missing = 14 + d
    assert 28 - d == missing, "the two sides of the gap disagree"
    key = {20: "A", 21: "B", 22: "C", 19: "D"}[missing]
    return {"answer": key, "computed": missing}


# ----------------------------------------------------------------- coding


def q_f3c9_023():
    # CAT -> DBU is a forward shift of 1
    assert shift("CAT", 1) == "DBU"
    code = shift("DOG", 1)
    key = {"EPH": "A", "EPI": "B", "FPH": "C", "EOH": "D"}[code]
    return {"answer": key, "computed": code}


def q_f3c9_024():
    # BAT -> DCV is a forward shift of 2
    assert shift("BAT", 2) == "DCV"
    code = shift("BIRD", 2)
    key = {"DKTF": "A", "CJSE": "B", "DKTE": "C", "DLTF": "D"}[code]
    return {"answer": key, "computed": code}


def q_f3c9_025():
    # MANGO -> LZMFN is a backward shift of 1 (with wrap: A -> Z)
    assert shift("MANGO", -1) == "LZMFN"
    code = shift("APPLE", -1)
    key = {"ZOOKD": "A", "BQQMF": "B", "ZOODK": "C", "YNNJC": "D"}[code]
    return {"answer": key, "computed": code}


def q_f3c9_026():
    # DELHI -> IHLED is the reversal
    assert reverse("DELHI") == "IHLED"
    code = reverse("PATNA")
    key = {"ANTAP": "A", "ANATP": "B", "APTNA": "C", "ATNAP": "D"}[code]
    return {"answer": key, "computed": code}


def q_f3c9_027():
    # SUN -> VXQ is a forward shift of 3
    assert shift("SUN", 3) == "VXQ"
    code = shift("MOON", 3)
    key = {"PRRQ": "A", "PRRP": "B", "ORRQ": "C", "PQRQ": "D"}[code]
    return {"answer": key, "computed": code}


def q_f3c9_030():
    total = value_sum("FACE")
    key = {15: "A", 14: "B", 16: "C", 13: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c9_031():
    # EAT -> 5-1-20 confirms the plain position code
    assert position_code("EAT") == "5-1-20"
    code = position_code("BIG")
    key = {"2-9-7": "A", "2-8-7": "B", "3-9-7": "C", "2-9-6": "D"}[code]
    return {"answer": key, "computed": code}


def q_f3c9_032():
    # reverse position code: A = 26 ... Z = 1
    assert reverse_position_code("AZ") == "26-1"
    code = reverse_position_code("BAD")
    key = {"25-26-23": "A", "2-1-4": "B", "25-25-23": "C", "24-26-23": "D"}[code]
    return {"answer": key, "computed": code}


def q_f3c9_033():
    # CAT -> 24 confirms the sum code
    assert value_sum("CAT") == 24
    total = value_sum("DOG")
    key = {26: "A", 24: "B", 25: "C", 27: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c9_037():
    # TEACHER -> UFBDIFS is a forward shift of 1
    assert shift("TEACHER", 1) == "UFBDIFS"
    code = shift("STUDENT", 1)
    key = {"TUVEFOU": "A", "TUVEFPU": "B", "RUVEFOU": "C", "TUWEFOU": "D"}[code]
    return {"answer": key, "computed": code}


# ------------------------------------------------------------- letter series


def q_f3c9_047():
    # B, D, G, K -> place values 2,4,7,11 ; gaps 2,3,4 ; next gap 5
    vals = [pos(c) for c in "BDGK"]
    gaps = [b - a for a, b in zip(vals, vals[1:])]
    assert gaps == [2, 3, 4], "the gaps do not rise 2,3,4"
    nxt = letter(vals[-1] + gaps[-1] + 1)
    key = {"O": "A", "P": "B", "N": "C", "Q": "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_048():
    # Z, X, V, T -> place values 26,24,22,20 stepping back by 2
    vals = [pos(c) for c in "ZXVT"]
    gaps = [b - a for a, b in zip(vals, vals[1:])]
    assert set(gaps) == {-2}, "the step is not a constant -2"
    nxt = letter(vals[-1] - 2)
    key = {"S": "A", "R": "B", "Q": "C", "P": "D"}[nxt]
    return {"answer": key, "computed": nxt}


def q_f3c9_049():
    # A, Z, B, Y, C, X, ? -> odd positions A,B,C forward ; the 7th is the 4th odd term
    odd_vals = [pos("A"), pos("B"), pos("C")]  # 1,2,3
    assert [b - a for a, b in zip(odd_vals, odd_vals[1:])] == [1, 1]
    nxt = letter(odd_vals[-1] + 1)
    key = {"W": "A", "D": "B", "E": "C", "V": "D"}[nxt]
    return {"answer": key, "computed": nxt}
