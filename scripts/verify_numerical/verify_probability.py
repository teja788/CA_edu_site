"""Verifier for foundation/quantitative-aptitude/probability.json (P3 Ch 15).

Every function recomputes its answer from the stem's own parameters, using
``fractions.Fraction`` so that each probability, expectation or odds ratio is an
EXACT rational number. Favourable and total counts are built from first
principles (list the sample space, count the favourable outcomes, or apply the
stated theorem), and the computed Fraction is mapped to an option key through a
dict of the four option VALUES — never through the bank's answer key. A wrong key
in the bank therefore shows up as a mismatch, and a wrong option value shows up as
an assertion.

Conventions applied throughout (they match the chapter's notes, and a reviewer
should confirm them against the study material):

  * Outcomes are equally likely unless the stem says otherwise, so the classical
    definition P(E) = n(E) / n(S) applies.
  * Two dice are distinguishable: the sample space is the 36 ordered pairs.
  * n coins (or one coin n times) give 2^n equally likely outcomes.
  * A pack has 52 cards: 26 red, 13 per suit, 4 of each rank, 12 face cards.
  * "Drawn together" or "at random" from a bag means WITHOUT replacement; the
    word "with replacement" makes successive draws independent.
  * Odds are stored as the Fraction favourable/unfavourable (or its reciprocal
    for "against"), and a ratio option "a : b" is the Fraction a/b.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from math import comb


def F(x) -> Fraction:
    """Fraction from an int, a 'a/b' string, a decimal string, or a 'a : b' ratio."""
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    s = str(x).strip()
    if ":" in s:  # an odds ratio "a : b"
        a, b = s.split(":")
        return Fraction(int(a.strip()), int(b.strip()))
    if "/" in s:
        return Fraction(s)
    return Fraction(s)  # Fraction parses decimal strings like "0.88" exactly


def pick(computed, options) -> str:
    """Map a computed Fraction to exactly one option key.

    `options` is {option key: option value as printed in the bank}. Exactly one
    option must equal the computed value, otherwise the verifier raises — which
    the runner reports as a failure. The key is NEVER read from the bank.
    """
    computed = F(computed)
    hits = [k for k, v in options.items() if F(v) == computed]
    if len(hits) != 1:
        raise AssertionError(f"computed {computed} matched {hits} in {options}")
    return hits[0]


def result(computed, options):
    return {"answer": pick(computed, options), "computed": str(F(computed))}


# ------------------------------------------------------------ dice helpers

DICE = list(product(range(1, 7), repeat=2))  # 36 ordered pairs
PRIMES = {2, 3, 5, 7, 11, 13}


def two_dice(predicate) -> Fraction:
    favourable = sum(1 for a, b in DICE if predicate(a, b))
    return Fraction(favourable, len(DICE))


# ------------------------------------------------------------ coin helpers


def coins(n, predicate) -> Fraction:
    space = list(product("HT", repeat=n))
    favourable = sum(1 for outcome in space if predicate(outcome))
    return Fraction(favourable, len(space))


# =============================================================== §2 classical


def q_f3c15_002():
    # A die: even faces {2, 4, 6}.
    favourable = sum(1 for face in range(1, 7) if face % 2 == 0)
    return result(Fraction(favourable, 6), {"A": "1/2", "B": "1/3", "C": "1/6", "D": "2/3"})


def q_f3c15_003():
    # A die: faces greater than 4, i.e. 5 and 6.
    favourable = sum(1 for face in range(1, 7) if face > 4)
    return result(Fraction(favourable, 6), {"A": "1/3", "B": "1/2", "C": "1/6", "D": "2/3"})


# =============================================================== §10 coins


def q_f3c15_005():
    # Two tosses, exactly one head.
    p = coins(2, lambda o: o.count("H") == 1)
    return result(p, {"A": "1/2", "B": "1/4", "C": "1/3", "D": "3/4"})


def q_f3c15_006():
    # Two tosses, at least one head = 1 - P(no head).
    p = coins(2, lambda o: o.count("H") >= 1)
    assert p == 1 - coins(2, lambda o: o.count("H") == 0)
    return result(p, {"A": "3/4", "B": "1/2", "C": "1/4", "D": "1/3"})


def q_f3c15_007():
    # Three tosses, exactly two heads.
    p = coins(3, lambda o: o.count("H") == 2)
    assert p == Fraction(comb(3, 2), 2 ** 3)
    return result(p, {"A": "3/8", "B": "1/8", "C": "1/4", "D": "1/2"})


def q_f3c15_008():
    # Three tosses, at least one head.
    p = coins(3, lambda o: o.count("H") >= 1)
    assert p == 1 - Fraction(1, 8)
    return result(p, {"A": "7/8", "B": "1/8", "C": "1/2", "D": "3/8"})


# =============================================================== §10 cards


def q_f3c15_010():
    # A king: 4 of 52.
    return result(Fraction(4, 52), {"A": "1/13", "B": "1/52", "C": "1/4", "D": "4/13"})


def q_f3c15_011():
    # A red card: 26 of 52.
    return result(Fraction(26, 52), {"A": "1/2", "B": "1/26", "C": "1/13", "D": "2/13"})


def q_f3c15_012():
    # Face cards: 3 per suit x 4 suits = 12 of 52.
    return result(Fraction(3 * 4, 52), {"A": "3/13", "B": "1/13", "C": "4/13", "D": "3/52"})


def q_f3c15_013():
    # A spade: 13 of 52.
    return result(Fraction(13, 52), {"A": "1/4", "B": "1/13", "C": "1/2", "D": "1/26"})


# =============================================================== §4 addition


def q_f3c15_014():
    # Ace or king, mutually exclusive: 4/52 + 4/52.
    p = Fraction(4, 52) + Fraction(4, 52)
    return result(p, {"A": "2/13", "B": "1/13", "C": "4/13", "D": "8/13"})


def q_f3c15_022():
    # Mutually exclusive union.
    p = F("0.3") + F("0.4")
    return result(p, {"A": "0.7", "B": "0.12", "C": "0.1", "D": "0.58"})


def q_f3c15_023():
    # General addition theorem.
    p = Fraction(1, 2) + Fraction(1, 3) - Fraction(1, 6)
    return result(p, {"A": "2/3", "B": "5/6", "C": "1/6", "D": "1/2"})


def q_f3c15_024():
    # King or heart: P(king) + P(heart) - P(king of hearts).
    p = Fraction(4, 52) + Fraction(13, 52) - Fraction(1, 52)
    return result(p, {"A": "4/13", "B": "17/52", "C": "1/4", "D": "1/52"})


def q_f3c15_025():
    # One die: even OR greater than 3, counted over the union.
    p = sum(1 for f in range(1, 7) if f % 2 == 0 or f > 3)
    return result(Fraction(p, 6), {"A": "2/3", "B": "1/2", "C": "5/6", "D": "1"})


def q_f3c15_026():
    # Two dice: sum is 7 or 11 (mutually exclusive).
    p = two_dice(lambda a, b: a + b in (7, 11))
    return result(p, {"A": "2/9", "B": "1/6", "C": "1/3", "D": "1/4"})


def q_f3c15_027():
    # Solve the addition theorem for the overlap.
    p = F("0.5") + F("0.6") - F("0.8")
    return result(p, {"A": "0.3", "B": "1.1", "C": "0.11", "D": "0.2"})


# =============================================================== §10 dice


def q_f3c15_016():
    return result(two_dice(lambda a, b: a + b == 7), {"A": "1/6", "B": "5/36", "C": "1/9", "D": "1/12"})


def q_f3c15_017():
    return result(two_dice(lambda a, b: a + b == 8), {"A": "5/36", "B": "1/6", "C": "1/9", "D": "1/12"})


def q_f3c15_018():
    return result(two_dice(lambda a, b: a == b), {"A": "1/6", "B": "1/12", "C": "1/36", "D": "5/36"})


def q_f3c15_019():
    return result(two_dice(lambda a, b: a + b >= 10), {"A": "1/6", "B": "1/12", "C": "5/36", "D": "1/9"})


def q_f3c15_020():
    return result(two_dice(lambda a, b: (a + b) in PRIMES), {"A": "5/12", "B": "1/3", "C": "7/18", "D": "1/2"})


# =============================================================== §5/§10 urns


def q_f3c15_028():
    # Single draw: 5 red of 8.
    return result(Fraction(5, 5 + 3), {"A": "5/8", "B": "3/8", "C": "5/3", "D": "1/2"})


def q_f3c15_029():
    # Both red, without replacement: 4C2 / 10C2.
    p = Fraction(comb(4, 2), comb(10, 2))
    return result(p, {"A": "2/15", "B": "4/25", "C": "2/5", "D": "1/3"})


def q_f3c15_030():
    # Both black: 6C2 / 10C2.
    p = Fraction(comb(6, 2), comb(10, 2))
    return result(p, {"A": "1/3", "B": "9/25", "C": "3/5", "D": "2/15"})


def q_f3c15_031():
    # One of each: 4C1 * 6C1 / 10C2.
    p = Fraction(comb(4, 1) * comb(6, 1), comb(10, 2))
    # the three colour cases must partition the sample space
    assert Fraction(comb(4, 2), comb(10, 2)) + Fraction(comb(6, 2), comb(10, 2)) + p == 1
    return result(p, {"A": "8/15", "B": "12/25", "C": "1/2", "D": "2/15"})


def q_f3c15_032():
    # Not black = 1 - P(black); 5 black of 10.
    p = 1 - Fraction(5, 10)
    return result(p, {"A": "1/2", "B": "1/5", "C": "3/10", "D": "2/5"})


# =============================================================== §5 conditional


def q_f3c15_034():
    # P(A|B) = P(A and B) / P(B).
    p = F("0.2") / F("0.5")
    return result(p, {"A": "0.4", "B": "0.1", "C": "0.7", "D": "2.5"})


def q_f3c15_035():
    # Both kings without replacement: 4/52 * 3/51.
    p = Fraction(4, 52) * Fraction(3, 51)
    return result(p, {"A": "1/221", "B": "1/169", "C": "1/13", "D": "1/16"})


def q_f3c15_036():
    # P(6 | even): shrink the space to {2,4,6}.
    even = [f for f in range(1, 7) if f % 2 == 0]
    p = Fraction(sum(1 for f in even if f == 6), len(even))
    return result(p, {"A": "1/3", "B": "1/6", "C": "1/2", "D": "1/9"})


def q_f3c15_037():
    # Sum 8 given first die is 3: only the second die matters.
    favourable = sum(1 for b in range(1, 7) if 3 + b == 8)
    p = Fraction(favourable, 6)
    return result(p, {"A": "1/6", "B": "5/36", "C": "1/36", "D": "1/5"})


# =============================================================== §6 independence


def q_f3c15_038():
    # Both aces WITH replacement: independent draws, (4/52)^2.
    p = Fraction(4, 52) * Fraction(4, 52)
    return result(p, {"A": "1/169", "B": "1/221", "C": "2/13", "D": "1/26"})


def q_f3c15_040():
    # Independent joint probability.
    p = F("0.3") * F("0.5")
    return result(p, {"A": "0.15", "B": "0.8", "C": "0.65", "D": "0.35"})


def q_f3c15_041():
    # Independent union: P(A)+P(B)-P(A)P(B).
    a, b = F("0.4"), F("0.7")
    p = a + b - a * b
    return result(p, {"A": "0.82", "B": "1.1", "C": "0.28", "D": "0.9"})


def q_f3c15_042():
    # At least one hit = 1 - P(both miss), independent.
    p = 1 - (1 - F("0.6")) * (1 - F("0.7"))
    return result(p, {"A": "0.88", "B": "0.42", "C": "1.3", "D": "0.12"})


# =============================================================== §7 Bayes


def q_f3c15_043():
    # Posterior P(Urn I | white) by Bayes.
    prior_i, prior_ii = Fraction(1, 2), Fraction(1, 2)
    w_given_i, w_given_ii = Fraction(3, 5), Fraction(2, 5)
    total = prior_i * w_given_i + prior_ii * w_given_ii
    posterior = (prior_i * w_given_i) / total
    return result(posterior, {"A": "3/5", "B": "1/2", "C": "2/5", "D": "3/10"})


def q_f3c15_044():
    # Total probability of white.
    total = Fraction(1, 2) * Fraction(3, 5) + Fraction(1, 2) * Fraction(2, 5)
    return result(total, {"A": "1/2", "B": "1/5", "C": "3/5", "D": "2/5"})


# =============================================================== §8 random variable


def q_f3c15_045():
    # E(X) for a fair die.
    e = sum(Fraction(x, 6) for x in range(1, 7))
    assert e == Fraction(7, 2)
    return result(e, {"A": "3.5", "B": "3", "C": "21", "D": "6"})


def q_f3c15_046():
    # Mean of a discrete distribution.
    dist = [(0, "0.2"), (1, "0.5"), (2, "0.3")]
    assert sum(F(p) for _, p in dist) == 1
    e = sum(x * F(p) for x, p in dist)
    return result(e, {"A": "1.1", "B": "1", "C": "1.5", "D": "0.9"})


def q_f3c15_047():
    # Var(X) = E(X^2) - [E(X)]^2.
    dist = [(0, "0.2"), (1, "0.5"), (2, "0.3")]
    e = sum(x * F(p) for x, p in dist)
    e2 = sum(x * x * F(p) for x, p in dist)
    var = e2 - e * e
    return result(var, {"A": "0.49", "B": "1.7", "C": "1.21", "D": "0.7"})


# =============================================================== §9 odds


def q_f3c15_049():
    # Odds in favour 3:2 -> probability a/(a+b).
    a, b = 3, 2
    p = Fraction(a, a + b)
    return result(p, {"A": "3/5", "B": "3/2", "C": "2/5", "D": "2/3"})


def q_f3c15_050():
    # Probability 2/7 -> odds against = (1-p):p, stored as the Fraction (1-p)/p.
    p = Fraction(2, 7)
    odds_against = (1 - p) / p
    return result(odds_against, {"A": "5 : 2", "B": "2 : 5", "C": "2 : 7", "D": "5 : 7"})
