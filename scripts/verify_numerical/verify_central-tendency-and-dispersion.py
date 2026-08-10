"""Verifier for foundation/quantitative-aptitude/central-tendency-and-dispersion.json (P3 Ch 14).

Every function recomputes its answer from the stem's own data list or frequency
table. The computed value is then matched, BY VALUE, against the printed option
figures of the same question, and the key of the matching option is returned. The
option figures are read straight from the bank and parsed to numbers, so the
verifier never restates — and never trusts — the bank's ``correct`` key: if the
key pointed at an option whose printed value did not equal the computed value, the
verifier would return a different key and the runner would flag the mismatch.

Conventions applied throughout (they match the chapter's notes, and a reviewer
should confirm them against the study material):

  * Exact quantities (arithmetic, weighted and combined mean, median and quartiles
    by linear interpolation, variance, mean deviation) are carried as
    ``fractions.Fraction`` so no rounding creeps in.
  * The STANDARD DEVIATION and VARIANCE divide by n (POPULATION standard
    deviation), the convention the Foundation study material uses. Where the SD is
    irrational it is compared with a tolerance and matched to the option that
    rounds to the stated figure.
  * Median and quartiles use the (n + 1) positional rules for individual and
    discrete series, and N ÷ 2, kN ÷ 4, kN ÷ 100 to locate classes in a
    continuous series.
"""

from __future__ import annotations

import json
import math
import re
from fractions import Fraction as F
from pathlib import Path

# ------------------------------------------------------------ bank option values

_BANK = (
    Path(__file__).resolve().parents[2]
    / "src" / "data" / "questions" / "foundation" / "quantitative-aptitude"
    / "central-tendency-and-dispersion.json"
)
_NUM = re.compile(r"-?\d+(?:\.\d+)?")


def _to_number(text):
    """First numeric figure printed in an option, ₹/%/commas stripped, else None."""
    cleaned = text.replace(",", "").replace("₹", "").replace("%", "")
    m = _NUM.search(cleaned)
    return float(m.group()) if m else None


def _load_options():
    data = json.loads(_BANK.read_text(encoding="utf-8"))
    table = {}
    for q in data["questions"]:
        table[q["id"]] = {
            o["key"]: _to_number(o["text"])
            for o in q["options"]
            if _to_number(o["text"]) is not None
        }
    return table


_OPTIONS = _load_options()


def opts(qid):
    """The {key: printed value} map for one question, numeric options only."""
    return _OPTIONS[qid]


def pick(computed, options, tol="0"):
    """Map a computed value to exactly one option key by its printed value."""
    c = float(computed)
    t = float(tol)
    hits = [k for k, v in options.items() if abs(v - c) <= t]
    if len(hits) != 1:
        raise AssertionError(f"computed {c} matched {hits} in {options}")
    return hits[0]


def result(qid, computed, tol="0"):
    return {"answer": pick(computed, opts(qid), tol), "computed": str(computed)}


# ------------------------------------------------------------ shared helpers


def mean(values):
    """Exact arithmetic mean of a list of numbers."""
    return F(sum(F(v) for v in values), len(values))


def grouped_mean(pairs):
    """Exact mean from (value_or_midpoint, frequency) pairs."""
    n = sum(f for _, f in pairs)
    return F(sum(F(x) * f for x, f in pairs), n)


def pop_variance(values):
    """Population variance Σ(x - x̄)² / n, exact."""
    m = mean(values)
    return F(sum((F(v) - m) ** 2 for v in values), len(values))


def grouped_pop_variance(pairs):
    """Population variance from (value, frequency) pairs, exact."""
    m = grouped_mean(pairs)
    n = sum(f for _, f in pairs)
    return F(sum(f * (F(x) - m) ** 2 for x, f in pairs), n)


def partition_continuous(freqs, lowers, h, pos):
    """L + [(pos - cf) / f] * h for the class holding the given position."""
    cum = 0
    for lo, f in zip(lowers, freqs):
        if cum + f >= pos:
            return F(lo) + (F(pos) - F(cum)) / F(f) * F(h)
        cum += f
    raise AssertionError("position beyond data")


# ------------------------------------------------------------ §2 arithmetic mean


def q_f3c14_002():
    return result("q-f3c14-002", mean([45, 52, 48, 60, 55]))


def q_f3c14_003():
    known = [35, 42, 38, 45, 50]
    return result("q-f3c14-003", 6 * 40 - sum(known))


def q_f3c14_004():
    pairs = [(80, 4), (70, 3), (60, 2), (90, 1)]
    wm = F(sum(x * w for x, w in pairs), sum(w for _, w in pairs))
    return result("q-f3c14-004", wm)


def q_f3c14_005():
    return result("q-f3c14-005", F(40 * 60 + 60 * 70, 40 + 60))


def q_f3c14_006():
    # (30*64 + 20*x) / 50 = 68  ->  x
    return result("q-f3c14-006", F(68 * 50 - 30 * 64, 20))


def q_f3c14_049():
    remaining = F(25 * 18000 - 10 * 30000, 15)
    return result("q-f3c14-049", remaining)


def q_f3c14_050():
    cm = F(20 * 15 + 30 * 20 + 50 * 25, 20 + 30 + 50)
    return result("q-f3c14-050", cm, tol="0.001")


# ------------------------------------------------------ §3 grouped mean


def q_f3c14_007():
    m = grouped_mean(list(zip([5, 15, 25, 35, 45], [6, 8, 12, 10, 4])))
    return result("q-f3c14-007", m, tol="0.001")


def q_f3c14_008():
    mids, freq = [10, 30, 50, 70, 90], [5, 8, 15, 7, 5]
    A, h, N = 50, 20, sum(freq)
    d = [F(x - A, h) for x in mids]
    sfd = sum(di * fi for di, fi in zip(d, freq))
    return result("q-f3c14-008", A + F(sfd, N) * h, tol="0.001")


# --------------------------------------------------- §4 properties of the mean


def q_f3c14_010():
    return result("q-f3c14-010", 2 * 45 + 5)  # y = k x + c


# ------------------------------------------------------------ §5 median


def q_f3c14_011():
    data = sorted([12, 18, 15, 22, 10, 25, 20])
    return result("q-f3c14-011", data[(len(data) + 1) // 2 - 1], tol="0.001")


def q_f3c14_012():
    data = sorted([34, 28, 45, 52, 30, 40])
    n = len(data)
    return result("q-f3c14-012", F(data[n // 2 - 1] + data[n // 2], 2), tol="0.001")


def q_f3c14_013():
    xs, fs = [10, 20, 30, 40, 50], [4, 6, 10, 8, 2]
    N, cum = sum(fs), 0
    for x, f in zip(xs, fs):
        cum += f
        if cum >= F(N, 2):
            return result("q-f3c14-013", x, tol="0.001")
    raise AssertionError


def q_f3c14_014():
    med = partition_continuous([10, 20, 40, 30], [0, 10, 20, 30], 10, F(100, 2))
    return result("q-f3c14-014", med, tol="0.001")


def q_f3c14_015():
    fs = [5, 8, 15, 7, 5]
    med = partition_continuous(fs, [0, 10, 20, 30, 40], 10, F(sum(fs), 2))
    return result("q-f3c14-015", med, tol="0.01")


# ------------------------------------------------------------ §6 mode


def q_f3c14_016():
    xs, fs = [5, 10, 15, 20, 25], [3, 7, 12, 8, 2]
    return result("q-f3c14-016", xs[fs.index(max(fs))], tol="0.001")


def q_f3c14_017():
    fs, lowers = [5, 8, 20, 10, 7], [0, 10, 20, 30, 40]
    idx = fs.index(max(fs))
    L, h = lowers[idx], 10
    f1, f0, f2 = fs[idx], fs[idx - 1], fs[idx + 1]
    mode = F(L) + F(f1 - f0, 2 * f1 - f0 - f2) * h
    return result("q-f3c14-017", mode, tol="0.01")


# ------------------------------------------- §7 empirical relation


def q_f3c14_018():
    mode = 3 * F("44.4") - 2 * F("45.6")
    return result("q-f3c14-018", mode, tol="0.001")


def q_f3c14_019():
    median_ = (F(30) + 2 * F(36)) / 3
    return result("q-f3c14-019", median_, tol="0.001")


# ------------------------------------------------------------ §8 geometric mean


def q_f3c14_020():
    vals = [3, 9, 27]
    return result("q-f3c14-020", math.prod(vals) ** (1 / len(vals)), tol="0.001")


def q_f3c14_021():
    return result("q-f3c14-021", math.sqrt(5 * 20), tol="0.001")


# ------------------------------------------------------------ §9 harmonic mean


def q_f3c14_022():
    vals = [2, 3, 6]
    hm = F(len(vals), 1) / sum(F(1, v) for v in vals)
    return result("q-f3c14-022", hm, tol="0.01")


def q_f3c14_023():
    speeds = [40, 60]
    hm = F(len(speeds), 1) / sum(F(1, s) for s in speeds)
    return result("q-f3c14-023", hm, tol="0.001")


# ------------------------------------------- §10 quartiles / percentiles


def q_f3c14_025():
    fs = [5, 8, 15, 7, 5]
    q1 = partition_continuous(fs, [0, 10, 20, 30, 40], 10, F(sum(fs), 4))
    return result("q-f3c14-025", q1, tol="0.005")


def q_f3c14_026():
    fs = [5, 8, 15, 7, 5]
    q3 = partition_continuous(fs, [0, 10, 20, 30, 40], 10, F(3 * sum(fs), 4))
    return result("q-f3c14-026", q3, tol="0.01")


def q_f3c14_027():
    fs = [5, 8, 15, 7, 5]
    p90 = partition_continuous(fs, [0, 10, 20, 30, 40], 10, F(90 * sum(fs), 100))
    return result("q-f3c14-027", p90, tol="0.005")


def q_f3c14_028():
    data = [12, 15, 18, 22, 25, 28, 30, 35]
    pos = F(len(data) + 1, 4)  # 2.25
    lo = int(pos)
    q1 = F(data[lo - 1]) + (pos - lo) * (data[lo] - data[lo - 1])
    return result("q-f3c14-028", q1, tol="0.001")


# ------------------------------------------------------------ §12 range


def q_f3c14_029():
    data = [25, 40, 15, 60, 35]
    return result("q-f3c14-029", max(data) - min(data), tol="0.001")


# ------------------------------------------------------ §13 quartile deviation


def q_f3c14_030():
    q1, q3 = 25, 45
    return result("q-f3c14-030", F(q3 - q1, 2), tol="0.001")


def q_f3c14_031():
    q1, q3 = 15, 25
    return result("q-f3c14-031", F(q3 - q1, q3 + q1), tol="0.001")


# ------------------------------------------------------------ §14 mean deviation


def q_f3c14_032():
    data = [4, 6, 8, 10, 12]
    m = mean(data)
    md = F(sum(abs(F(x) - m) for x in data), len(data))
    return result("q-f3c14-032", md, tol="0.001")


def q_f3c14_033():
    data = [3, 6, 9, 12, 15]
    median_ = data[len(data) // 2]
    md = F(sum(abs(F(x) - median_) for x in data), len(data))
    return result("q-f3c14-033", md / median_, tol="0.001")


def q_f3c14_034():
    xs, fs = [10, 20, 30, 40, 50], [2, 3, 5, 3, 2]
    m = grouped_mean(list(zip(xs, fs)))
    md = F(sum(f * abs(F(x) - m) for x, f in zip(xs, fs)), sum(fs))
    return result("q-f3c14-034", md, tol="0.01")


# ------------------------------------------- §15 standard deviation & variance


def q_f3c14_035():
    sd = math.sqrt(float(pop_variance([2, 4, 6, 8, 10])))
    return result("q-f3c14-035", sd, tol="0.01")


def q_f3c14_036():
    return result("q-f3c14-036", pop_variance([5, 10, 15, 20, 25]), tol="0.01")


def q_f3c14_044():
    n, sx, sx2 = 10, 100, 1090
    var = F(sx2, n) - F(sx, n) ** 2
    return result("q-f3c14-044", math.sqrt(float(var)), tol="0.01")


# --------------------------------------------- §16 SD of grouped data


def q_f3c14_037():
    sd = math.sqrt(float(grouped_pop_variance(list(zip([2, 4, 6, 8], [1, 3, 3, 1])))))
    return result("q-f3c14-037", sd, tol="0.01")


def q_f3c14_038():
    mids, fs = [5, 15, 25, 35, 45], [5, 8, 15, 7, 5]
    A, h, N = 25, 10, sum(fs)
    d = [F(x - A, h) for x in mids]
    sfd = sum(di * fi for di, fi in zip(d, fs))
    sfd2 = sum(di * di * fi for di, fi in zip(d, fs))
    var_coded = F(sfd2, N) - F(sfd, N) ** 2
    sd = math.sqrt(float(var_coded)) * h
    return result("q-f3c14-038", sd, tol="0.02")


# --------------------------------------------- §17 combined SD


def q_f3c14_039():
    n1, m1, s1 = 100, 50, 5
    n2, m2, s2 = 150, 60, 7
    cm = F(n1 * m1 + n2 * m2, n1 + n2)
    d1, d2 = m1 - cm, m2 - cm
    comb_var = F(n1 * (s1 ** 2 + d1 ** 2) + n2 * (s2 ** 2 + d2 ** 2), n1 + n2)
    return result("q-f3c14-039", math.sqrt(float(comb_var)), tol="0.01")


# --------------------------------------------- §18 coefficient of variation


def q_f3c14_040():
    return result("q-f3c14-040", F(8, 40) * 100, tol="0.001")


def q_f3c14_041():
    # A decision question: compute both coefficients of variation and name the
    # steadier (lower-CV) series. Only one option pairs "Series B" with "lower
    # coefficient of variation"; the verifier finds the winning series, and the
    # bank's key must point at the option that names it for the right reason.
    cv_a = F(10, 50) * 100
    cv_b = F(12, 80) * 100
    lower = "B" if cv_b < cv_a else "A"
    data = json.loads(_BANK.read_text(encoding="utf-8"))
    q = next(x for x in data["questions"] if x["id"] == "q-f3c14-041")
    want = f"Series {lower}"
    hits = [
        o["key"] for o in q["options"]
        if want in o["text"] and "coefficient of variation" in o["text"].lower()
    ]
    assert len(hits) == 1, f"expected one option naming {want} for its CV, got {hits}"
    return {"answer": hits[0], "computed": f"CV_A={float(cv_a)} CV_B={float(cv_b)} -> {lower}"}


def q_f3c14_045():
    cv, sd = 25, 5
    return result("q-f3c14-045", F(sd, 1) / F(cv, 100))


def q_f3c14_046():
    m, var = 50, 100
    return result("q-f3c14-046", math.sqrt(var) / m * 100, tol="0.001")


# --------------------------------------------- §19 change of origin and scale


def q_f3c14_042():
    return result("q-f3c14-042", abs(3) * 5)  # scale multiplies the SD


def q_f3c14_043():
    return result("q-f3c14-043", 7)  # change of origin leaves the SD unchanged
