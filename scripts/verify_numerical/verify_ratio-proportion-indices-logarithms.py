"""Verifier for foundation/quantitative-aptitude/ratio-proportion-indices-logarithms.json
(P3 Ch 1 — Ratio and Proportion, Indices, Logarithms).

Every function recomputes its answer from the stem's own parameters. Ratio and
proportion arithmetic is done with `fractions.Fraction` so that nothing is lost
to floating point; logarithms use `math.log`/`math.log10`. Where a question is
set with four-figure table values (log 2 = 0.3010 and the like), the function
computes from those SAME stated values and then rounds explicitly to four
decimal places, because the option list is quoted to four decimals — the
comment on each such function says so.

Conventions:
  * a ratio is carried as a reduced (antecedent, consequent) pair, so that
    "4 : 6" and "2 : 3" stay distinguishable where a question asks for lowest
    terms;
  * `pick` maps a computed value onto the option that holds it and fails loudly
    if no option, or more than one option, matches — a wrong key in the bank
    therefore surfaces as an assertion, not as a silent pass.
"""

from __future__ import annotations

import math
from fractions import Fraction


# ------------------------------------------------------------ shared helpers


def ratio(a, b):
    """Reduce a : b to a lowest-terms (antecedent, consequent) pair."""
    f = Fraction(a, b)
    return (f.numerator, f.denominator)


def ratio3(a, b, c):
    """Reduce a three-term continued ratio to lowest terms."""
    g = math.gcd(math.gcd(int(a), int(b)), int(c))
    return (int(a) // g, int(b) // g, int(c) // g)


def pick(computed, options):
    """Return the single option key whose value equals `computed`."""
    hits = [k for k, v in options.items() if v == computed]
    assert len(hits) == 1, f"computed {computed!r} matched {hits} in {options!r}"
    return hits[0]


def pick_close(computed, options, tol=1e-6):
    """Same, for values that can only be compared as floats (surds, logs)."""
    hits = [k for k, v in options.items() if abs(float(v) - float(computed)) < tol]
    assert len(hits) == 1, f"computed {computed!r} matched {hits} in {options!r}"
    return hits[0]


def share(total, parts, index):
    """The `index`-th share when `total` is divided in the ratio `parts`."""
    return Fraction(total) * Fraction(parts[index], sum(parts))


# Four-figure table values quoted in the stems that use them.
LOG2 = 0.3010
LOG3 = 0.4771


# --------------------------------------------------------- §1–§2 ratio basics


def q_f3c1_001():
    # 750 g against 3 kg: convert to a common unit BEFORE forming the ratio.
    first_g = 750
    second_g = 3 * 1000
    r = ratio(first_g, second_g)
    key = pick(r, {"A": (1, 4), "B": (250, 1), "C": (4, 1), "D": (1, 400)})
    return {"answer": key, "computed": f"{r[0]}:{r[1]}"}


def q_f3c1_003():
    # Cross multiplication: 5 x 11 = 55 against 8 x 7 = 56.
    left, right = Fraction(5, 8), Fraction(7, 11)
    if left > right:
        key = "A"
    elif left == right:
        key = "B"
    else:
        key = "C"  # 7 : 11 is the greater ratio
    return {"answer": key, "computed": f"{float(left):.4f} vs {float(right):.4f}"}


def q_f3c1_004():
    # Lowest terms: divide both terms by the HCF, not by any common factor.
    a, b = 84, 126
    r = ratio(a, b)
    assert math.gcd(a, b) == 42
    key = pick(r, {"A": (4, 6), "B": (3, 2), "C": (2, 1), "D": (2, 3)})
    return {"answer": key, "computed": f"{r[0]}:{r[1]}"}


# ------------------------------------------------------------ §3 named ratios


def q_f3c1_005():
    # Duplicate ratio of a : b is a squared : b squared.
    a, b = 4, 9
    r = ratio(a ** 2, b ** 2)
    key = pick(r, {"A": (16, 81), "B": (8, 18), "C": (2, 3), "D": (64, 729)})
    return {"answer": key, "computed": f"{r[0]}:{r[1]}"}


def q_f3c1_006():
    # Sub-triplicate ratio of a : b is the ratio of the cube roots.
    a, b = 27, 64
    ra, rb = round(a ** (1 / 3)), round(b ** (1 / 3))
    assert ra ** 3 == a and rb ** 3 == b
    r = ratio(ra, rb)
    key = pick(r, {"A": (9, 16), "B": (3, 4), "C": (19683, 262144), "D": (4, 3)})
    return {"answer": key, "computed": f"{r[0]}:{r[1]}"}


def q_f3c1_007():
    # Compound ratio: antecedents together, consequents together.
    r = ratio(3 * 8, 4 * 15)
    key = pick(r, {"A": (45, 32), "B": (11, 19), "C": (2, 5), "D": (5, 2)})
    return {"answer": key, "computed": f"{r[0]}:{r[1]}"}


def q_f3c1_008():
    # Form each named ratio first, then compound all three.
    dup = (2 ** 2, 3 ** 2)          # duplicate of 2 : 3
    tri = (3 ** 3, 4 ** 3)          # triplicate of 3 : 4
    sub = (round(16 ** 0.5), round(25 ** 0.5))  # sub-duplicate of 16 : 25
    r = ratio(dup[0] * tri[0] * sub[0], dup[1] * tri[1] * sub[1])
    key = pick(r, {"A": (3, 25), "B": (2, 5), "C": (4, 15), "D": (3, 20)})
    return {"answer": key, "computed": f"{r[0]}:{r[1]}"}


# -------------------------------------------- §4–§5 continued ratio, division


def continued(ab, bc):
    """A : B = ab and B : C = bc, joined into a reduced three-term ratio."""
    (a, b), (c, d) = ab, bc
    return ratio3(a * c, b * c, b * d)


def q_f3c1_009():
    r = continued((2, 3), (4, 5))
    key = pick(r, {"A": (8, 12, 15), "B": (2, 3, 5), "C": (2, 4, 5), "D": (15, 12, 8)})
    return {"answer": key, "computed": ":".join(str(x) for x in r)}


def q_f3c1_010():
    # Build X : Y : Z, then divide the total capital in it and read off Z.
    parts = continued((5, 6), (8, 9))
    total = 497_000
    z = share(total, parts, 2)
    assert z.denominator == 1
    key = pick(int(z), {"A": 168_000, "B": 189_000, "C": 223_650, "D": 140_000})
    return {"answer": key, "computed": int(z)}


def q_f3c1_011():
    parts = (5, 4, 3)
    largest = share(684_000, parts, 0)
    key = pick(int(largest), {"A": 228_000, "B": 171_000, "C": 285_000, "D": 342_000})
    return {"answer": key, "computed": int(largest)}


def q_f3c1_012():
    # The given amount is a DIFFERENCE, so it measures (7 - 4) = 3 parts.
    parts = (7, 4)
    one_part = Fraction(66_000, parts[0] - parts[1])
    total = one_part * sum(parts)
    key = pick(int(total), {"A": 726_000, "B": 154_000, "C": 88_000, "D": 242_000})
    return {"answer": key, "computed": int(total)}


def q_f3c1_013():
    # The given amount is the MIDDLE share, so it measures 5 parts.
    parts = (6, 5, 4)
    one_part = Fraction(115_000, parts[1])
    total = one_part * sum(parts)
    key = pick(int(total), {"A": 345_000, "B": 1_725_000, "C": 287_500, "D": 431_250})
    return {"answer": key, "computed": int(total)}


def q_f3c1_014():
    # (a1 x + add) / (a2 x + add) = m / n  ->  solve the linear equation for x.
    a1, a2, add, m, n = 4, 7, 6, 2, 3
    x = Fraction(add * (m - n), a1 * n - a2 * m)
    smaller, larger = a1 * x, a2 * x
    assert Fraction(smaller + add, larger + add) == Fraction(m, n)
    key = pick(int(larger), {"A": 12, "B": 21, "C": 27, "D": 18})
    return {"answer": key, "computed": int(larger)}


# ------------------------------------------------- §6–§7 proportion and rules


def fourth_proportional(a, b, c):
    return Fraction(b * c, a)


def third_proportional(a, b):
    return Fraction(b * b, a)


def mean_proportional(a, c):
    root = math.isqrt(a * c)
    assert root * root == a * c, "the mean proportional is not a whole number"
    return root


def q_f3c1_015():
    d = fourth_proportional(5, 10, 15)
    assert Fraction(5, 10) == Fraction(15, int(d))
    key = pick(d, {"A": Fraction(20), "B": Fraction(15, 2), "C": Fraction(30), "D": Fraction(10, 3)})
    return {"answer": key, "computed": float(d)}


def q_f3c1_016():
    b = mean_proportional(8, 32)
    assert b * b == 8 * 32
    key = pick(b, {"A": 20, "B": 128, "C": 4, "D": 16})
    return {"answer": key, "computed": b}


def q_f3c1_017():
    c = third_proportional(9, 12)
    assert Fraction(9, 12) == Fraction(12, int(c))
    key = pick(c, {"A": Fraction(16), "B": Fraction(27, 4), "C": Fraction(1039, 100), "D": Fraction(15)})
    return {"answer": key, "computed": float(c)}


def q_f3c1_018():
    # 4, x, 25 in continued proportion means x squared = 4 x 25.
    x = mean_proportional(4, 25)
    key = pick(x, {"A": 14.5, "B": 10, "C": 100, "D": 6.25})
    return {"answer": key, "computed": x}


def q_f3c1_020():
    # Componendo et dividendo in reverse: (5x)/(3y) = (7 + 3)/(7 - 3).
    m, n = 7, 3
    five_x_over_three_y = Fraction(m + n, m - n)
    x_over_y = five_x_over_three_y * Fraction(3, 5)
    r = ratio(x_over_y.numerator, x_over_y.denominator)
    # sanity check with the smallest whole numbers in that ratio
    x, y = r
    assert Fraction(5 * x + 3 * y, 5 * x - 3 * y) == Fraction(m, n)
    key = pick(r, {"A": (5, 2), "B": (2, 5), "C": (6, 25), "D": (3, 2)})
    return {"answer": key, "computed": f"{r[0]}:{r[1]}"}


# ------------------------------------------------------------- §8 variation


def q_f3c1_021():
    # Inverse variation: machine-hours are constant.
    machines_1, hours_1, machines_2 = 18, 10, 12
    constant = machines_1 * hours_1
    hours_2 = Fraction(constant, machines_2)
    key = pick(hours_2, {"A": Fraction(15), "B": Fraction(20, 3), "C": Fraction(40, 3), "D": Fraction(180)})
    return {"answer": key, "computed": float(hours_2)}


def q_f3c1_022():
    # y = k x / z**2 ; find k from the first reading, then substitute the second.
    y1, x1, z1 = 12, 6, 2
    k = Fraction(y1 * z1 ** 2, x1)
    x2, z2 = 15, 5
    y2 = k * Fraction(x2, z2 ** 2)
    key = pick(y2, {"A": Fraction(12), "B": Fraction(24, 5), "C": Fraction(30), "D": Fraction(48, 25)})
    return {"answer": key, "computed": float(y2)}


def q_f3c1_023():
    # Cost = a + b x, solved from two observations.
    (x1, c1), (x2, c2) = (5_000, 300_000), (8_000, 420_000)
    b = Fraction(c2 - c1, x2 - x1)
    a = c1 - b * x1
    cost = a + b * 12_000
    key = pick(int(cost), {"A": 720_000, "B": 630_000, "C": 580_000, "D": 480_000})
    return {"answer": key, "computed": int(cost)}


# ---------------------------------------------------------------- §9 indices


def q_f3c1_024():
    value = 3 ** 4 * 3 ** 2
    assert value == 3 ** (4 + 2)
    key = pick(value, {"A": 6_561, "B": 531_441, "C": 81, "D": 729})
    return {"answer": key, "computed": value}


def q_f3c1_025():
    # (x**3)**4 / x**5 -> the resulting index only.
    index = 3 * 4 - 5
    key = pick(Fraction(index), {"A": Fraction(7), "B": Fraction(2), "C": Fraction(17), "D": Fraction(12, 5)})
    return {"answer": key, "computed": f"x^{index}"}


# ------------------------------------------ §10 zero, negative and fractional


def q_f3c1_027():
    value = 7 ** 0 + (-5) ** 0 + Fraction(1, 3) ** 0
    key = pick(value, {"A": 0, "B": 2, "C": 3, "D": 1})
    return {"answer": key, "computed": int(value)}


def q_f3c1_028():
    value = Fraction(1, 2 ** 3)
    key = pick(value, {"A": -8, "B": -6, "C": 8, "D": Fraction(1, 8)})
    return {"answer": key, "computed": str(value)}


def q_f3c1_029():
    # 32**(3/5): take the fifth root first, then cube it.
    root = round(32 ** (1 / 5))
    assert root ** 5 == 32
    value = root ** 3
    key = pick(value, {"A": 8, "B": 19.2, "C": 2, "D": 4})
    return {"answer": key, "computed": value}


def q_f3c1_030():
    # (27/64)**(-2/3): flip, take the cube root, then square.
    num_root, den_root = round(64 ** (1 / 3)), round(27 ** (1 / 3))
    assert num_root ** 3 == 64 and den_root ** 3 == 27
    value = Fraction(num_root, den_root) ** 2
    key = pick(value, {"A": Fraction(9, 16), "B": Fraction(16, 9), "C": Fraction(4, 3), "D": Fraction(3, 4)})
    return {"answer": key, "computed": str(value)}


def q_f3c1_031():
    first = round(16 ** (1 / 4)) ** 3            # 16**(3/4)
    second = math.isqrt(25)                      # 25**(1/2)
    third = round(81 ** (1 / 4))                 # (1/81)**(-1/4) = 81**(1/4)
    value = Fraction(first - second + third)
    key = pick(value, {"A": Fraction(10, 3), "B": Fraction(10), "C": Fraction(6), "D": Fraction(0)})
    return {"answer": key, "computed": float(value)}


# ------------------------------------------------------------------ §11 surds


def q_f3c1_032():
    # 1 / (root 7 - root 5), compared with each option evaluated numerically.
    value = 1 / (math.sqrt(7) - math.sqrt(5))
    options = {
        "A": (math.sqrt(7) - math.sqrt(5)) / 2,
        "B": (math.sqrt(7) + math.sqrt(5)) / 12,
        "C": (math.sqrt(7) + math.sqrt(5)) / math.sqrt(2),
        "D": (math.sqrt(7) + math.sqrt(5)) / 2,
    }
    key = pick_close(value, options, tol=1e-9)
    return {"answer": key, "computed": round(value, 4)}


def q_f3c1_033():
    # Raise both to the LCM of the orders (6): 3**2 = 9 against 2**3 = 8.
    left, right = 3 ** 2, 2 ** 3
    if left > right:
        key = "A"          # cube root of 3 is the greater surd
    elif left == right:
        key = "C"
    else:
        key = "B"
    return {"answer": key, "computed": f"{3 ** (1/3):.4f} vs {2 ** 0.5:.4f}"}


def q_f3c1_034():
    # 3 root 2 + root 8 + root 18, every surd reduced to a multiple of root 2.
    value = 3 * math.sqrt(2) + math.sqrt(8) + math.sqrt(18)
    options = {
        "A": 2 * math.sqrt(11),
        "B": 8 * math.sqrt(2),
        "C": 5 * math.sqrt(2),
        "D": 8 * math.sqrt(6),
    }
    key = pick_close(value, options, tol=1e-9)
    return {"answer": key, "computed": round(value, 4)}


# -------------------------------------------------- §12 exponential equations


def q_f3c1_035():
    # 3**(2x - 1) = 81 = 3**4, so 2x - 1 = 4.
    rhs_index = round(math.log(81, 3))
    assert 3 ** rhs_index == 81
    x = Fraction(rhs_index + 1, 2)
    key = pick(x, {"A": Fraction(2), "B": Fraction(5), "C": Fraction(5, 2), "D": Fraction(14)})
    return {"answer": key, "computed": float(x)}


def q_f3c1_036():
    # 2**(x + 3) = 8**(x - 1); 8 = 2**3, so x + 3 = 3(x - 1).
    p = round(math.log(8, 2))
    assert 2 ** p == 8
    # x + 3 = p*x - p  ->  x (1 - p) = -p - 3
    x = Fraction(-p - 3, 1 - p)
    assert x.denominator == 1 and 2 ** (int(x) + 3) == 8 ** (int(x) - 1)
    key = pick(x, {"A": Fraction(2), "B": Fraction(7, 3), "C": None, "D": Fraction(3)})
    return {"answer": key, "computed": float(x)}


def q_f3c1_037():
    # y = 2**x turns 4**x - 5(2**x) + 4 = 0 into y**2 - 5y + 4 = 0.
    b, c = -5, 4
    disc = b * b - 4 * c
    roots = [(-b + math.isqrt(disc)) // 2, (-b - math.isqrt(disc)) // 2]
    xs = sorted(round(math.log(y, 2)) for y in roots if y > 0)
    assert all(4 ** x - 5 * 2 ** x + 4 == 0 for x in xs)
    key = pick(tuple(xs), {"A": (0, 2), "B": (2,), "C": (1, 4), "D": ()})
    return {"answer": key, "computed": xs}


# ------------------------------------------------------------ §13–§14 logs


def q_f3c1_038():
    value = math.log(Fraction(1, 32), 2)
    value = round(value)
    assert 2 ** value == Fraction(1, 32)
    key = pick(value, {"A": 5, "B": -5, "C": 0.2, "D": None})
    return {"answer": key, "computed": value}


def q_f3c1_040():
    # log to base 5 of x = 3 is the same statement as 5**3 = x.
    x = 5 ** 3
    key = pick(x, {"A": 15, "B": 8, "C": 243, "D": 125})
    return {"answer": key, "computed": x}


def q_f3c1_041():
    # 12 = 2**2 x 3. Computed from the stated four-figure values, then rounded
    # explicitly to the four decimals the options are quoted to.
    value = round(2 * LOG2 + LOG3, 4)
    key = pick(value, {"A": 1.0791, "B": 0.7781, "C": 1.3010, "D": 0.2872})
    return {"answer": key, "computed": value}


def q_f3c1_042():
    # log 2 + 2 log 3 - log 6, with log 6 itself built from log 2 and log 3.
    log6 = LOG2 + LOG3
    value = round(LOG2 + 2 * LOG3 - log6, 4)
    assert value == round(LOG3, 4)      # the expression collapses to log 3
    key = pick(value, {"A": 0.0, "B": 0.4771, "C": 2.0333, "D": 0.9542})
    return {"answer": key, "computed": value}


# ------------------------------------------------ §15–§16 base, characteristic


def q_f3c1_045():
    # Change of base to 2: log2(32) / log2(8).
    value = Fraction(round(math.log(32, 2)), round(math.log(8, 2)))
    assert abs(8 ** float(value) - 32) < 1e-9
    key = pick(value, {"A": Fraction(5, 3), "B": Fraction(4), "C": Fraction(3, 5), "D": Fraction(5)})
    return {"answer": key, "computed": str(value)}


def q_f3c1_046():
    # ln N = ln 10 x log N, with ln 10 = 2.3026 as the stem states; rounded to
    # the four decimals the options carry.
    value = round(2.3026 * 0.6000, 4)
    key = pick(value, {"A": 0.2606, "B": 1.3816, "C": 0.6000, "D": 3.8377})
    return {"answer": key, "computed": value}


def q_f3c1_047():
    # Characteristic = floor(log10 N); for 0.00427 that is -3.
    characteristic = math.floor(math.log10(0.00427))
    key = pick(characteristic, {"A": -2, "B": -4, "C": -3, "D": 3})
    return {"answer": key, "computed": characteristic}


def q_f3c1_049():
    # log of 2**30 from the stated log 2, then digits = characteristic + 1.
    log_value = 30 * LOG2
    digits = math.floor(log_value) + 1
    assert digits == len(str(2 ** 30))
    key = pick(digits, {"A": 10, "B": 9, "C": 30, "D": 11})
    return {"answer": key, "computed": digits}


def q_f3c1_050():
    # log2(x) + log2(x-2) = 3  ->  x(x-2) = 8, then reject non-positive args.
    target = 2 ** 3
    disc = 4 + 4 * target
    roots = [(2 + math.isqrt(disc)) // 2, (2 - math.isqrt(disc)) // 2]
    valid = tuple(sorted(r for r in roots if r > 0 and r - 2 > 0))
    assert all(r * (r - 2) == target for r in roots)
    key = pick(valid, {"A": (-2, 4), "B": (4,), "C": (-2,), "D": (3,)})
    return {"answer": key, "computed": list(valid)}


# ------------------------------------------- cs-f3c1-01: three partners' case

KONKAN_TOTAL_CAPITAL = 2_450_000
KONKAN_PROFIT = 560_000
KONKAN_WITHDRAWAL = 140_000


def _konkan_parts():
    """Anil : Bhavana = 3 : 4 and Bhavana : Chirag = 6 : 7, joined."""
    return continued((3, 4), (6, 7))


def _konkan_capitals():
    parts = _konkan_parts()
    return [int(share(KONKAN_TOTAL_CAPITAL, parts, i)) for i in range(3)]


def cs_f3c1_01_a():
    r = _konkan_parts()
    key = pick(r, {"A": (3, 4, 7), "B": (3, 6, 7), "C": (9, 12, 14), "D": (14, 12, 9)})
    return {"answer": key, "computed": ":".join(str(x) for x in r)}


def cs_f3c1_01_b():
    capitals = _konkan_capitals()
    assert sum(capitals) == KONKAN_TOTAL_CAPITAL
    key = pick(capitals[2], {"A": 630_000, "B": 840_000, "C": 1_225_000, "D": 980_000})
    return {"answer": key, "computed": capitals[2]}


def cs_f3c1_01_c():
    parts = _konkan_parts()
    bhavana = share(KONKAN_PROFIT, parts, 1)
    key = pick(int(bhavana), {"A": 192_000, "B": 144_000, "C": 224_000, "D": 186_667})
    return {"answer": key, "computed": int(bhavana)}


def cs_f3c1_01_d():
    anil, _, chirag = _konkan_capitals()
    r = ratio(anil - KONKAN_WITHDRAWAL, chirag - KONKAN_WITHDRAWAL)
    key = pick(r, {"A": (9, 14), "B": (7, 12), "C": (3, 4), "D": (1, 2)})
    return {"answer": key, "computed": f"{r[0]}:{r[1]}"}


# ------------------------------------------------ cs-f3c1-02: three machines

MACHINES = {"P": 2 ** 12, "Q": 8 ** 5, "R": 4 ** 7}


def cs_f3c1_02_a():
    best = max(MACHINES, key=MACHINES.get)
    key = pick(best, {"A": "P", "B": "R", "C": "Q", "D": None})
    return {"answer": key, "computed": f"{best} = {MACHINES[best]}"}


def cs_f3c1_02_b():
    r = ratio(max(MACHINES.values()), min(MACHINES.values()))
    key = pick(r, {"A": (3, 1), "B": (5, 4), "C": (2, 1), "D": (8, 1)})
    return {"answer": key, "computed": f"{r[0]}:{r[1]}"}


def cs_f3c1_02_c():
    value = Fraction(2 ** 12 * 4 ** 7, 8 ** 5)
    assert value.denominator == 1 and int(value) == 2 ** 11
    key = pick(int(value), {"A": 2_048, "B": 16_384, "C": 4_096, "D": 32_768})
    return {"answer": key, "computed": int(value)}


# ----------------------------------------------- cs-f3c1-03: the growth rate

VIDARBHA_OLD, VIDARBHA_NEW, VIDARBHA_YEARS = 2_500_000, 20_000_000, 6


def cs_f3c1_03_a():
    # The factor is 8 = 2**3, so its log is 3 x log 2, rounded to four decimals.
    factor = Fraction(VIDARBHA_NEW, VIDARBHA_OLD)
    assert factor == 8
    index = round(math.log(int(factor), 2))
    value = round(index * LOG2, 4)
    key = pick(value, {"A": 2.4080, "B": 0.6020, "C": 0.9030, "D": 1.2040})
    return {"answer": key, "computed": value}


def cs_f3c1_03_b():
    # log(1 + r) = log(factor) / years, then antilog; reported as a percentage
    # rounded to two decimals, which is how the options are quoted.
    factor = VIDARBHA_NEW / VIDARBHA_OLD
    log_1_plus_r = math.log10(factor) / VIDARBHA_YEARS
    rate = round((10 ** log_1_plus_r - 1) * 100, 2)
    key = pick(rate, {"A": 116.67, "B": 133.33, "C": 700.0, "D": 41.42})
    return {"answer": key, "computed": rate}


def cs_f3c1_03_c():
    characteristic = math.floor(math.log10(VIDARBHA_NEW))
    assert characteristic == len(str(VIDARBHA_NEW)) - 1
    key = pick(characteristic, {"A": 8, "B": 7, "C": 6, "D": 0.3010})
    return {"answer": key, "computed": characteristic}
