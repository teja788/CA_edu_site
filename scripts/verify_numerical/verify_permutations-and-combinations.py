"""Verifier for foundation/quantitative-aptitude/permutations-and-combinations.json (P3 Ch 5).

Every function recomputes its answer from the stem's own parameters. Nothing is
copied from the answer key: each computed value is mapped to an option key
through a dict of the four option values, so a wrong key in the bank surfaces as
a KeyError or as a mismatch the runner reports.

Method policy for this chapter (stated per function in a comment):

  * BRUTE FORCE wherever the numbers allow it. A counting formula and the stem
    can be wrong in the same way — re-applying the formula the stem used proves
    nothing. Building the actual arrangements or selections with `itertools` and
    counting them is an independent check, and it is the only check that really
    tests a RESTRICTION (together, never together, no two adjacent, at least,
    collinear, unlabelled groups). 49 of the 56 numerical questions are verified
    this way.
  * FORMULA (`math.factorial`, `math.perm`, `math.comb`) in 6 functions only,
    where enumeration is infeasible — the service-tag case runs into millions of
    tags — or where the question is itself about a factorial identity
    (q-f3c5-007, q-f3c5-008). Those functions say so.
  * HYBRID in 1 function, q-f3c5-028: 10! rows is too many to lay out, so the
    restriction is brute forced over seat positions and the people are then
    placed by the plain arrangement counts.
  * Circular arrangements are enumerated and then CANONICALISED: an arrangement
    is reduced to its lexicographically smallest rotation (and, for a necklace or
    garland, the smallest of the rotations of the sequence and of its reverse).
    Counting canonical forms reproduces (n - 1)! and (n - 1)!/2 from first
    principles rather than assuming them.
"""

from __future__ import annotations

import math
from itertools import combinations, permutations, product

# ------------------------------------------------------------ shared helpers


def rot_canonical(seq):
    """Smallest rotation of seq — one representative per circular arrangement."""
    n = len(seq)
    return min(tuple(seq[i:] + seq[:i]) for i in range(n))


def flip_canonical(seq):
    """Smallest rotation of seq or of its reverse — one per necklace/garland."""
    rev = tuple(reversed(seq))
    return min(rot_canonical(tuple(seq)), rot_canonical(rev))


def circularly_adjacent(seq, a, b):
    """True if a and b sit next to each other around the closed loop seq."""
    n = len(seq)
    i, j = seq.index(a), seq.index(b)
    return (i - j) % n == 1 or (j - i) % n == 1


def multiset_words(letters):
    """Every distinct arrangement of a multiset of letters, built by choosing
    positions for each letter in turn. Returns a set of strings, so the
    distinctness is proved by construction rather than assumed."""
    counts = {}
    for ch in letters:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(letters)
    words = set()

    def place(free, remaining, slots):
        if not remaining:
            words.add("".join(slots))
            return
        ch, k = remaining[0]
        for spots in combinations(free, k):
            nxt = list(slots)
            for s in spots:
                nxt[s] = ch
            place([f for f in free if f not in spots], remaining[1:], nxt)

    place(list(range(n)), sorted(counts.items()), [""] * n)
    return words


# ------------------------------------------- SS 1-2 the two rules of counting


def q_f3c5_001():
    # BRUTE FORCE: build every (dish, bread) pair and count them.
    meals = set(product(range(6), range(4)))
    total = len(meals)
    key = {10: "A", 24: "B", 360: "C", 1296: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_002():
    # BRUTE FORCE: the two fleets are one pool of distinct vehicles; build the
    # union and count it, which is what "either ... or" means.
    vans = [("van", i) for i in range(5)]
    bikes = [("bike", i) for i in range(3)]
    choices = set(vans) | set(bikes)
    total = len(choices)
    key = {15: "A", 5: "B", 8: "C", 2: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_003():
    # BRUTE FORCE: enumerate every ordered triple of distinct digits and keep
    # the ones that are genuine three-digit numbers.
    total = sum(1 for t in permutations(range(10), 3) if t[0] != 0)
    key = {720: "A", 504: "B", 900: "C", 648: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_004():
    # BRUTE FORCE: test every number in the stated range, so the overlap
    # between the two lists is handled by the set, not by a rule.
    hits = [n for n in range(1, 100) if n % 3 == 0 or n % 5 == 0]
    total = len(hits)
    key = {46: "A", 52: "B", 40: "C", 33: "D"}[total]
    return {"answer": key, "computed": total}


# ------------------------------------------------- SS 3 factorials


def q_f3c5_007():
    # FORMULA: the question is itself about cancelling factorials, so the check
    # is the definition of n! rather than an enumeration.
    value = math.factorial(10) // math.factorial(8)
    key = {1.25: "A", 2: "B", 720: "C", 90: "D"}[value]
    return {"answer": key, "computed": value}


def q_f3c5_008():
    # FORMULA: same reason as q-f3c5-007. Computed straight from the definition
    # of each factorial, not from any cancellation shortcut.
    value = math.factorial(12) // (math.factorial(9) * math.factorial(3))
    key = {220: "A", 1320: "B", 440: "C", 1: "D"}[value]
    return {"answer": key, "computed": value}


def q_f3c5_009():
    # BRUTE FORCE search: test every candidate n against the stated equation
    # instead of rearranging it, so no algebra can go unnoticed.
    hits = [n for n in range(2, 60) if math.factorial(n) // math.factorial(n - 2) == 72]
    assert len(hits) == 1, hits
    n = hits[0]
    key = {-8: "A", 9: "B", 8: "C", 74: "D"}[n]
    return {"answer": key, "computed": n}


# --------------------------------------------------- SS 4-5 permutations nPr


def q_f3c5_011():
    # BRUTE FORCE: build every ordered triple of distinct assistants and count.
    total = sum(1 for _ in permutations(range(9), 3))
    key = {504: "A", 84: "B", 729: "C", 362880: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_012():
    # BRUTE FORCE: 7P3 by enumeration of the ordered triples themselves.
    total = sum(1 for _ in permutations(range(7), 3))
    key = {35: "A", 343: "B", 210: "C", 5040: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_013():
    # BRUTE FORCE search over r: enumerate 10Pr for each r and keep the r whose
    # enumerated count is 720.
    hits = [r for r in range(0, 11) if sum(1 for _ in permutations(range(10), r)) == 720]
    assert len(hits) == 1, hits
    r = hits[0]
    key = {6: "A", 4: "B", 720: "C", 3: "D"}[r]
    return {"answer": key, "computed": r}


def q_f3c5_014():
    # BRUTE FORCE search over n: enumerate nP2 for each n and keep the match.
    hits = [n for n in range(2, 40) if sum(1 for _ in permutations(range(n), 2)) == 56]
    assert len(hits) == 1, hits
    n = hits[0]
    key = {8: "A", 7: "B", -7: "C", 28: "D"}[n]
    return {"answer": key, "computed": n}


# --------------------------------------------- SS 6 repetition allowed


def q_f3c5_016():
    # BRUTE FORCE: generate every 4-digit string over the 10 digits.
    total = sum(1 for _ in product(range(10), repeat=4))
    key = {5040: "A", 10000: "B", 210: "C", 1048576: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_017():
    # BRUTE FORCE: each of the 5 letters chooses a box, so enumerate the
    # functions from letters to boxes. This settles which side is the exponent
    # by construction rather than by rule.
    total = sum(1 for _ in product(range(3), repeat=5))
    key = {243: "A", 125: "B", 120: "C", 60: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_018():
    # BRUTE FORCE: every 4-digit string over the six digits, keeping only the
    # ones that do not begin with 0.
    total = sum(1 for t in product(range(6), repeat=4) if t[0] != 0)
    key = {1296: "A", 360: "B", 1080: "C", 300: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_019():
    # BRUTE FORCE: each prize picks a winner, so enumerate the functions from
    # the 3 prizes to the 8 students.
    total = sum(1 for _ in product(range(8), repeat=3))
    key = {336: "A", 512: "B", 56: "C", 6561: "D"}[total]
    return {"answer": key, "computed": total}


# ----------------------------------- SS 7 objects that are not all distinct


def q_f3c5_020():
    # BRUTE FORCE: build the distinct words of BALLOON as strings and count
    # them. Identical letters collapse in the set, so no division is assumed.
    total = len(multiset_words("BALLOON"))
    key = {5040: "A", 2520: "B", 630: "C", 1260: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_021():
    # BRUTE FORCE: same construction for ACCOUNTANT. 2,26,800 strings is large
    # but well within reach, and it proves the four repeated pairs collapse.
    total = len(multiset_words("ACCOUNTANT"))
    key = {3628800: "A", 907200: "B", 226800: "C", 151200: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_022():
    # BRUTE FORCE: the flags are 3 R, 2 B and 4 G; build every distinct signal.
    total = len(multiset_words("RRRBBGGGG"))
    key = {362880: "A", 30240: "B", 15120: "C", 1260: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_023():
    # BRUTE FORCE on the restriction: filter the distinct words of BALLOON for
    # the ones that actually contain the substring OO. Re-applying the block
    # formula would not test the restriction at all.
    total = sum(1 for w in multiset_words("BALLOON") if "OO" in w)
    key = {720: "A", 360: "B", 1260: "C", 900: "D"}[total]
    return {"answer": key, "computed": total}


# ------------------------------------------- SS 8 restrictions in a row


def _directors_together(row, directors=(0, 1, 2)):
    """True when the named people occupy consecutive positions of the row."""
    spots = sorted(row.index(d) for d in directors)
    return spots[-1] - spots[0] == len(directors) - 1


def q_f3c5_024():
    # BRUTE FORCE on the restriction: lay out all 7! rows and keep the ones in
    # which the three directors really do stand in consecutive places.
    total = sum(1 for row in permutations(range(7)) if _directors_together(row))
    key = {720: "A", 120: "B", 5040: "C", 4320: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_025():
    # BRUTE FORCE on the restriction: the same enumeration, keeping the rows in
    # which the three are NOT all consecutive. Computed independently of
    # q-f3c5-024 rather than by subtracting from it.
    total = sum(1 for row in permutations(range(7)) if not _directors_together(row))
    key = {720: "A", 4320: "B", 5040: "C", 1440: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_026():
    # BRUTE FORCE on the restriction: adults are 0-3 and children 4-6. Keep the
    # rows in which no two children occupy neighbouring positions. This tests
    # the gap method instead of repeating it.
    children = (4, 5, 6)

    def separated(row):
        spots = sorted(row.index(c) for c in children)
        return all(b - a > 1 for a, b in zip(spots, spots[1:]))

    total = sum(1 for row in permutations(range(7)) if separated(row))
    key = {1440: "A", 576: "B", 5040: "C", 720: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_027():
    # BRUTE FORCE on the restriction: all distinct words of ORANGE, kept when
    # the first letter is one of the word's own vowels.
    vowels = set("AEIOU")
    total = sum(1 for w in multiset_words("ORANGE") if w[0] in vowels)
    key = {120: "A", 720: "B", 2160: "C", 360: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_028():
    # HYBRID: 10! rows is too many to lay out, so the RESTRICTION is brute
    # forced — every set of 4 seats the girls could take is enumerated and only
    # the consecutive ones are kept — and the people are then placed into those
    # seats by the plain arrangement counts for distinct objects.
    blocks = [c for c in combinations(range(10), 4) if c[-1] - c[0] == 3]
    total = len(blocks) * math.factorial(6) * math.factorial(4)
    key = {5040: "A", 3628800: "B", 120960: "C", 17280: "D"}[total]
    return {"answer": key, "computed": "%d blocks -> %d" % (len(blocks), total)}


# --------------------------------------- SS 9-10 circles, necklaces, garlands


def q_f3c5_029():
    # BRUTE FORCE: lay out all 6! seatings, reduce each to its smallest
    # rotation, and count the distinct representatives. This derives (n - 1)!
    # from the meaning of a circle rather than assuming the formula.
    total = len({rot_canonical(p) for p in permutations(range(6))})
    key = {720: "A", 60: "B", 24: "C", 120: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_030():
    # BRUTE FORCE: all distinct circular seatings of 8, kept when directors 0
    # and 1 are neighbours around the closed table.
    seatings = {rot_canonical(p) for p in permutations(range(8))}
    total = sum(1 for s in seatings if circularly_adjacent(s, 0, 1))
    key = {5040: "A", 720: "B", 1440: "C", 10080: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_031():
    # BRUTE FORCE: the same enumeration, keeping the seatings in which the two
    # are NOT neighbours. Computed independently of q-f3c5-030.
    seatings = {rot_canonical(p) for p in permutations(range(8))}
    total = sum(1 for s in seatings if not circularly_adjacent(s, 0, 1))
    key = {3600: "A", 1440: "B", 5040: "C", 38880: "D"}[total]
    return {"answer": key, "computed": total}


def _circular_forms(n):
    """Every distinct circular arrangement of 0..n-1, one tuple each.

    Because a permutation of 0..n-1 has its smallest rotation starting at 0,
    the tuples (0,) + p over all p enumerate the rotation classes exactly.
    """
    return {(0,) + p for p in permutations(range(1, n))}


def q_f3c5_032():
    # BRUTE FORCE: lay out all 7! strings of beads, reduce each to the smallest
    # of the rotations of the string AND of its reverse, and count the distinct
    # forms. Both the rotation and the flip are derived, not assumed.
    total = len({flip_canonical(p) for p in permutations(range(7))})
    key = {720: "A", 360: "B", 5040: "C", 2520: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_033():
    # BRUTE FORCE: 9! strings is more than needed, so start from the 8! distinct
    # circular arrangements and merge each with its mirror image. The reflection
    # is computed by actually reversing the loop, not by dividing by 2.
    total = len({flip_canonical(s) for s in _circular_forms(9)})
    key = {20160: "A", 40320: "B", 362880: "C", 181440: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_034():
    # BRUTE FORCE on the restriction: all distinct circular seatings of 9, kept
    # when no two of the three women (6, 7, 8) are neighbours around the loop.
    women = (6, 7, 8)

    def separated(seat):
        return not any(
            circularly_adjacent(seat, a, b) for a, b in combinations(women, 2)
        )

    total = sum(1 for s in _circular_forms(9) if separated(s))
    key = {40320: "A", 14400: "B", 2400: "C", 7200: "D"}[total]
    return {"answer": key, "computed": total}


# ----------------------------------- SS 11-13 combinations and their properties


def q_f3c5_035():
    # BRUTE FORCE: build every unordered team of 3 from the 9 assistants.
    total = sum(1 for _ in combinations(range(9), 3))
    key = {504: "A", 729: "B", 168: "C", 84: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_036():
    # BRUTE FORCE: enumerate the 4-subsets themselves.
    total = sum(1 for _ in combinations(range(12), 4))
    key = {11880: "A", 20736: "B", 495: "C", 2970: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_037():
    # BRUTE FORCE: enumerate the 17-subsets of a 20-set directly, so the
    # symmetry nCr = nC(n - r) is a result of the count and not an input to it.
    total = sum(1 for _ in combinations(range(20), 17))
    key = {6840: "A", 3: "B", 1140: "C", 190: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_038():
    # BRUTE FORCE search: count the r-subsets of a 15-set for every r and keep
    # the r values whose count equals that of r = 4.
    target = sum(1 for _ in combinations(range(15), 4))
    hits = tuple(
        x for x in range(16) if sum(1 for _ in combinations(range(15), x)) == target
    )
    key = {(4, 11): "A", (4,): "B", (11,): "C", (4, 19): "D"}[hits]
    return {"answer": key, "computed": "%s (each giving %d)" % (str(hits), target)}


def q_f3c5_039():
    # BRUTE FORCE: enumerate both families of subsets and add their sizes; then
    # confirm independently that the sum equals the number of 3-subsets of 8.
    total = sum(1 for _ in combinations(range(7), 3)) + sum(
        1 for _ in combinations(range(7), 2)
    )
    assert total == sum(1 for _ in combinations(range(8), 3)), "Pascal's rule failed"
    key = {21: "A", 56: "B", 35: "C", 70: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_040():
    # BRUTE FORCE search over n: enumerate the 2-subsets of each n-set.
    hits = [n for n in range(2, 40) if sum(1 for _ in combinations(range(n), 2)) == 45]
    assert len(hits) == 1, hits
    n = hits[0]
    key = {9: "A", 90: "B", -9: "C", 10: "D"}[n]
    return {"answer": key, "computed": n}


# --------------------------------- SS 14-15 restricted and "one or more"


def q_f3c5_041():
    # BRUTE FORCE on the restriction: chartered accountants are 0-5 and cost
    # accountants 6-9. Build every committee of 5 and keep those with at least
    # 3 chartered accountants. Enumeration cannot double-count, which is exactly
    # the failure the reserved-core distractor commits.
    cas = set(range(6))
    total = sum(
        1 for c in combinations(range(10), 5) if len(set(c) & cas) >= 3
    )
    key = {420: "A", 186: "B", 120: "C", 252: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_042():
    # BRUTE FORCE on the restriction: build every team of 11 from 15 and keep
    # the ones that actually contain player 0, the captain.
    total = sum(1 for c in combinations(range(15), 11) if 0 in c)
    key = {1365: "A", 364: "B", 1001: "C", 3003: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_043():
    # BRUTE FORCE on the restriction: every sub-committee of 4 from 10, kept
    # when director 0 (the interested one) is absent.
    total = sum(1 for c in combinations(range(10), 4) if 0 not in c)
    key = {210: "A", 84: "B", 70: "C", 126: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_044():
    # BRUTE FORCE: enumerate the in-or-out decision for each magazine and drop
    # the single empty basket, rather than quoting 2**n - 1.
    baskets = [b for b in product((0, 1), repeat=6) if any(b)]
    total = len(baskets)
    key = {63: "A", 64: "B", 21: "C", 720: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_045():
    # BRUTE FORCE: a pack is (number of identical pens, number of identical
    # diaries, which of the two distinct books). Enumerate all of them and drop
    # the empty pack. Identical items contribute a quantity, distinct items an
    # in-or-out decision, and the enumeration makes that difference explicit.
    packs = [
        (p, d, b)
        for p in range(5)
        for d in range(4)
        for b in product((0, 1), repeat=2)
        if p or d or any(b)
    ]
    total = len(packs)
    key = {80: "A", 511: "B", 39: "C", 79: "D"}[total]
    return {"answer": key, "computed": total}


# --------------------------------------------- SS 16 division into groups


def q_f3c5_046():
    # BRUTE FORCE: enumerate every 5-subset of the 10 trainees and identify a
    # split with the UNORDERED pair of its two halves. Equal unlabelled groups
    # then merge by construction, with no division by 2! assumed.
    splits = set()
    everyone = set(range(10))
    for c in combinations(range(10), 5):
        splits.add(frozenset({frozenset(c), frozenset(everyone - set(c))}))
    total = len(splits)
    key = {252: "A", 126: "B", 42: "C", 30240: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_047():
    # BRUTE FORCE: a posting is a function from the 9 students to the 3 named
    # branches. Enumerate all 3**9 of them and keep those sending exactly 3
    # students to each branch. Because the branches are named, no merging is
    # done — which is the whole point of the question.
    postings = [
        p
        for p in product(range(3), repeat=9)
        if all(p.count(b) == 3 for b in range(3))
    ]
    total = len(postings)
    key = {1680: "A", 280: "B", 84: "C", 60480: "D"}[total]
    return {"answer": key, "computed": total}


# ----------------------------------------------- SS 17 standard applications


def q_f3c5_048():
    # BRUTE FORCE: a handshake is an unordered pair of delegates; enumerate them.
    total = sum(1 for _ in combinations(range(12), 2))
    key = {132: "A", 144: "B", 66: "C", 220: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_049():
    # BRUTE FORCE: label the vertices 0-9 around the polygon, enumerate every
    # pair, and keep the pairs that are not neighbours — those are the
    # diagonals. The sides are identified by adjacency, not subtracted by rule.
    n = 10
    total = sum(
        1
        for a, b in combinations(range(n), 2)
        if (b - a) % n != 1 and (a - b) % n != 1
    )
    key = {35: "A", 45: "B", 90: "C", 70: "D"}[total]
    return {"answer": key, "computed": total}


def q_f3c5_050():
    # BRUTE FORCE on the restriction: points 0-3 are the collinear four.
    # Enumerate every triple of points and keep the ones that are not wholly
    # inside the collinear set, since those form no triangle.
    line = set(range(4))
    total = sum(
        1 for t in combinations(range(10), 3) if not set(t).issubset(line)
    )
    key = {120: "A", 114: "B", 40: "C", 116: "D"}[total]
    return {"answer": key, "computed": total}


# ------------------------------------------- case set 1: the service tag
#
# FORMULA throughout this case. The tag counts run into millions, so the tags
# cannot be laid out one by one; instead each function multiplies the SIZE of
# the choice set available at each position, and those sizes are derived from
# the alphabet and the digit set rather than written in.

ALPHABET = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
DIGITS = list(range(10))
VOWELS = [c for c in ALPHABET if c in "AEIOU"]


def cs_f3c5_01_a():
    # FORMULA: three free letter positions and two free digit positions.
    total = len(ALPHABET) ** 3 * len(DIGITS) ** 2
    key = {1404000: "A", 6760: "B", 1757600: "C", 17576: "D"}[total]
    return {"answer": key, "computed": total}


def cs_f3c5_01_b():
    # FORMULA: nPr inside each pool, because a letter and a digit cannot clash.
    total = math.perm(len(ALPHABET), 3) * math.perm(len(DIGITS), 2)
    key = {1757600: "A", 1404000: "B", 15600: "C", 1560000: "D"}[total]
    return {"answer": key, "computed": total}


def cs_f3c5_01_c():
    # FORMULA: the restricted first position takes the vowel count, derived
    # from the alphabet, and the remaining positions stay free.
    total = len(VOWELS) * len(ALPHABET) ** 2 * len(DIGITS) ** 2
    key = {1757600: "A", 13000: "B", 67600: "C", 338000: "D"}[total]
    return {"answer": key, "computed": total}


def cs_f3c5_01_d():
    # FORMULA: four letter positions, no repetition, no digits.
    total = math.perm(len(ALPHABET), 4)
    key = {358800: "A", 456976: "B", 14950: "C", 15600: "D"}[total]
    return {"answer": key, "computed": total}


# ------------------------------------------- case set 2: the CSR committee
#
# BRUTE FORCE throughout. Independent directors are 0-6 and executive
# directors 7-11, so every committee is built explicitly and filtered on its
# actual composition.

INDEPENDENT = set(range(7))


def cs_f3c5_02_a():
    # BRUTE FORCE: every unordered committee of 5 from the 12 directors.
    total = sum(1 for _ in combinations(range(12), 5))
    key = {95040: "A", 792: "B", 248832: "C", 462: "D"}[total]
    return {"answer": key, "computed": total}


def cs_f3c5_02_b():
    # BRUTE FORCE on the restriction: keep the committees whose independent
    # membership is exactly 3.
    total = sum(
        1 for c in combinations(range(12), 5) if len(set(c) & INDEPENDENT) == 3
    )
    key = {546: "A", 1260: "B", 350: "C", 210: "D"}[total]
    return {"answer": key, "computed": total}


def cs_f3c5_02_c():
    # BRUTE FORCE on the restriction: keep the committees with 3 or more
    # independent directors. Computed independently of cs-f3c5-02-b.
    total = sum(
        1 for c in combinations(range(12), 5) if len(set(c) & INDEPENDENT) >= 3
    )
    key = {546: "A", 350: "B", 792: "C", 1260: "D"}[total]
    return {"answer": key, "computed": total}


# ------------------------------------------- case set 3: splitting a batch
#
# BRUTE FORCE throughout. The whole case turns on labelled versus unlabelled
# groups, and enumeration settles that by identifying a split with the object
# the question describes — an unordered pair of halves, or a named assignment.


def cs_f3c5_03_a():
    # BRUTE FORCE: identify a split by the UNORDERED pair of its two halves, so
    # the two unnamed groups merge by construction.
    everyone = set(range(8))
    splits = {
        frozenset({frozenset(c), frozenset(everyone - set(c))})
        for c in combinations(range(8), 4)
    }
    total = len(splits)
    key = {70: "A", 1680: "B", 140: "C", 35: "D"}[total]
    return {"answer": key, "computed": total}


def cs_f3c5_03_b():
    # BRUTE FORCE: identify a split by WHICH half is the audit team, so the two
    # named teams stay distinct. Each 4-subset is one audit team.
    splits = {frozenset(c) for c in combinations(range(8), 4)}
    total = len(splits)
    key = {70: "A", 35: "B", 1680: "C", 140: "D"}[total]
    return {"answer": key, "computed": total}


def cs_f3c5_03_c():
    # BRUTE FORCE: a posting is a function from the 8 trainees to the 3 named
    # clients. Enumerate all 3**8 and keep those with group sizes 2, 3 and 3.
    sizes = (2, 3, 3)
    postings = [
        p
        for p in product(range(3), repeat=8)
        if all(p.count(g) == sizes[g] for g in range(3))
    ]
    total = len(postings)
    key = {280: "A", 3360: "B", 560: "C", 1120: "D"}[total]
    return {"answer": key, "computed": total}
