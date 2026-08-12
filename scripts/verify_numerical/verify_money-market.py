"""Verifier for foundation/business-economics/money-market.json (P4 Ch 8).

Every function recomputes its answer from the stem's own parameters. Nothing is
copied from the answer key: each computed value is mapped to an option key
through a dict of the four option values, so a wrong key in the bank surfaces as
a KeyError or as a mismatch the runner reports.

Conventions used below:
  * `Fraction` (F) keeps every ratio exact — reserve ratios, multipliers and
    prices are clean rationals, so no rounding is ever needed. Option texts that
    quote a decimal (for example "0.2" or "12.5") map to the exact fraction they
    stand for.
  * The credit (deposit) multiplier is 1 / r, where r is the required reserve
    ratio written as a fraction. The money multiplier is money supply / high-
    powered money (MS / H). The two are distinct objects and are computed
    separately here.
  * Total deposits (credit) created from a fresh deposit = initial deposit / r,
    which INCLUDES the original primary deposit; derivative deposits = total −
    initial deposit (the newly created money only).
  * M1 = currency with the public + demand deposits + other deposits with the
    RBI; M3 = M1 + time deposits (broad money).
  * Fisher's equation of exchange MV = PT gives the price level P = MV / T.
"""

from __future__ import annotations

from fractions import Fraction as F


# ------------------------------------------------------------ shared helpers


def credit_multiplier(r):
    """Credit / deposit multiplier = 1 / r for a reserve ratio r (a Fraction)."""
    return 1 / r


def total_credit(initial, r):
    """Total deposits created = initial deposit / r (includes the original)."""
    return initial / r


def money_multiplier(ms, h):
    """Money multiplier = money supply / high-powered money."""
    return F(ms, h)


# ------------------------------------------------- money demand: quantity theory


def q_f4c8_011():
    # Fisher: MV = PT -> P = MV / T, with M = 2000, V = 5, T = 500.
    p = F(2000 * 5, 500)
    key = {F(200): "A", F(20): "B", F(5): "C", F(50): "D"}[p]
    return {"answer": key, "computed": str(p)}


# -------------------------------------------------------- money supply: aggregates


def q_f4c8_016():
    # M1 = currency 500 + demand deposits 300 + other deposits with RBI 20.
    m1 = 500 + 300 + 20
    key = {800: "A", 520: "B", 820: "C", 320: "D"}[m1]
    return {"answer": key, "computed": m1}


def q_f4c8_017():
    # M3 = M1 (820) + time deposits (680).
    m3 = 820 + 680
    key = {1500: "A", 820: "B", 680: "C", 140: "D"}[m3]
    return {"answer": key, "computed": m3}


# --------------------------------------------- high-powered money and multiplier


def q_f4c8_021():
    # Money multiplier = MS / H = 4000 / 800.
    m = money_multiplier(4000, 800)
    key = {F(4): "A", F(1, 5): "B", F(5): "C", F(16, 5): "D"}[m]
    return {"answer": key, "computed": str(m)}


def q_f4c8_022():
    # MS = m * H = 4 * 1500.
    ms = 4 * 1500
    key = {6000: "A", 375: "B", 1500: "C", 4000: "D"}[ms]
    return {"answer": key, "computed": ms}


def q_f4c8_023():
    # H = MS / m = 6000 / 4.
    h = F(6000, 4)
    key = {F(24000): "A", F(1500): "B", F(2000): "C", F(1000): "D"}[h]
    return {"answer": key, "computed": str(h)}


def q_f4c8_032():
    # Credit multiplier = 1 / r, r = 12.5% = 1/8.
    m = credit_multiplier(F(1, 8))
    key = {F(8): "A", F(25, 2): "B", F(5, 4): "C", F(1, 8): "D"}[m]
    return {"answer": key, "computed": str(m)}


def q_f4c8_033():
    # Deposit multiplier = 1 / r, r = 4% = 1/25.
    m = credit_multiplier(F(1, 25))
    key = {F(4): "A", F(5, 2): "B", F(25): "C", F(20): "D"}[m]
    return {"answer": key, "computed": str(m)}


# ----------------------------------------------------------- credit creation


def q_f4c8_027():
    # Credit multiplier = 1 / r, r = 25% = 1/4.
    m = credit_multiplier(F(1, 4))
    key = {F(4): "A", F(5, 2): "B", F(5): "C", F(1, 4): "D"}[m]
    return {"answer": key, "computed": str(m)}


def q_f4c8_028():
    # Total credit = initial deposit / r = 10000 / (1/5).
    total = total_credit(10000, F(1, 5))
    key = {F(40000): "A", F(12500): "B", F(50000): "C", F(2000): "D"}[total]
    return {"answer": key, "computed": str(total)}


def q_f4c8_029():
    # Derivative deposits = total (50000) - initial deposit (10000).
    total = total_credit(10000, F(1, 5))
    derivative = total - 10000
    key = {F(50000): "A", F(40000): "B", F(10000): "C", F(60000): "D"}[derivative]
    return {"answer": key, "computed": str(derivative)}


def q_f4c8_030():
    # Required reserves = deposits * r = 20000 * 5%.
    reserves = 20000 * F(5, 100)
    key = {F(4000): "A", F(19000): "B", F(100): "C", F(1000): "D"}[reserves]
    return {"answer": key, "computed": str(reserves)}


def q_f4c8_031():
    # Total credit = initial deposit / r = 5000 / (1/10).
    total = total_credit(5000, F(1, 10))
    key = {F(5000): "A", F(500): "B", F(45000): "C", F(50000): "D"}[total]
    return {"answer": key, "computed": str(total)}


def q_f4c8_034():
    # Total credit = initial deposit / r = 2000 / (1/4).
    total = total_credit(2000, F(1, 4))
    key = {F(6000): "A", F(500): "B", F(10000): "C", F(8000): "D"}[total]
    return {"answer": key, "computed": str(total)}
