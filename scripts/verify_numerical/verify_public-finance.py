"""Verifier for foundation/business-economics/public-finance.json (P4 Ch 7).

Every function recomputes its answer from the stem's own numbers. Nothing is
copied from the answer key: each computed value is mapped to an option key
through a dict of the four option values, so a wrong key in the bank surfaces as
a KeyError or as a mismatch the runner reports.

Conventions used below:
  * `Fraction` (F) gives exact rational tax rates; no rounding is needed,
    because every stem is built so the exact answer is a clean value. An option
    that quotes a percentage (for example "7.5%") maps to the exact fraction
    (3/40) it stands for.
  * The three deficits follow their standard definitions:
      revenue deficit  = revenue expenditure - revenue receipts
      fiscal deficit   = total expenditure - total receipts EXCLUDING borrowings
      primary deficit  = fiscal deficit - interest payments
    and the fiscal deficit equals the government's borrowing for the year.
  * A progressive slab tax charges each rate only on the income that falls
    within its band. Rates and amounts in the stems are illustrative, not a
    statement of any current Indian tax schedule.
  * Money figures are in ₹ crore (or ₹) exactly as the stem states; the
    verifier works in the same units and maps the integer result to a key.
"""

from __future__ import annotations

from fractions import Fraction as F


# ------------------------------------------------------------ shared helpers


def revenue_deficit(rev_exp, rev_rec):
    """Revenue deficit = revenue expenditure - revenue receipts."""
    return rev_exp - rev_rec


def fiscal_deficit(total_exp, non_borrow_receipts):
    """Fiscal deficit = total expenditure - total receipts excluding borrowings."""
    return total_exp - non_borrow_receipts


def primary_deficit(fisc_def, interest):
    """Primary deficit = fiscal deficit - interest payments."""
    return fisc_def - interest


# ---------------------------------------------------------------- tax rates


def q_f4c7_030():
    # Average tax rate = tax / income = 60,000 / 8,00,000 = 7.5%.
    rate = F(60000, 800000)
    key = {F(6, 100): "A", F(12, 100): "B", F(75, 1000): "C", F(8, 100): "D"}[rate]
    return {"answer": key, "computed": "%s = %.1f%%" % (rate, float(rate) * 100)}


def q_f4c7_031():
    # Slab tax on 6,00,000: nil up to 2,50,000; 5% on next 2,50,000; 20% above.
    income = 600000
    tax = 0
    tax += F(5, 100) * (500000 - 250000)          # 5% band, fully used
    tax += F(20, 100) * (income - 500000)          # 20% band, part used
    assert tax.denominator == 1
    tax = int(tax)
    key = {20000: "A", 12500: "B", 120000: "C", 32500: "D"}[tax]
    return {"answer": key, "computed": tax}


def q_f4c7_032():
    # Proportional 10%: B pays on 9,00,000, A pays on 3,00,000; find B - A.
    rate = F(10, 100)
    diff = int(rate * 900000 - rate * 300000)
    key = {60000: "A", 30000: "B", 90000: "C", 120000: "D"}[diff]
    return {"answer": key, "computed": diff}


# ---------------------------------------------------------- budget deficits


def q_f4c7_033():
    # Revenue deficit = 1,800 - 1,600.
    rd = revenue_deficit(1800, 1600)
    key = {400: "A", 200: "B", 3400: "C", 100: "D"}[rd]
    return {"answer": key, "computed": rd}


def q_f4c7_034():
    # Fiscal deficit: total exp = 2,300 + 700; receipts excl borrowings = 2,000 + 200.
    total_exp = 2300 + 700
    non_borrow = 2000 + 200
    fd = fiscal_deficit(total_exp, non_borrow)
    key = {600: "A", 1000: "B", 800: "C", 400: "D"}[fd]
    return {"answer": key, "computed": fd}


def q_f4c7_035():
    # Primary deficit = fiscal deficit 800 - interest 400.
    pd = primary_deficit(800, 400)
    key = {1200: "A", 800: "B", 200: "C", 400: "D"}[pd]
    return {"answer": key, "computed": pd}


def q_f4c7_036():
    # Fiscal deficit: total exp 2,200; receipts excl borrowings = 1,600 + 100.
    fd = fiscal_deficit(2200, 1600 + 100)
    key = {500: "A", 600: "B", 700: "C", 2100: "D"}[fd]
    return {"answer": key, "computed": fd}


def q_f4c7_037():
    # Primary deficit = fiscal deficit 500 - interest 300.
    pd = primary_deficit(500, 300)
    key = {800: "A", 200: "B", 500: "C", 300: "D"}[pd]
    return {"answer": key, "computed": pd}


def q_f4c7_038():
    # Borrowing = fiscal deficit = total exp 2,000 - non-borrowed receipts 1,650.
    fd = fiscal_deficit(2000, 1650)
    key = {1650: "A", 2000: "B", 350: "C", 3650: "D"}[fd]
    return {"answer": key, "computed": fd}


def q_f4c7_039():
    # Fiscal deficit: total exp 45,000; receipts excl borrowings = 32,000 + 3,000.
    fd = fiscal_deficit(45000, 32000 + 3000)
    key = {13000: "A", 3000: "B", 35000: "C", 10000: "D"}[fd]
    return {"answer": key, "computed": fd}


def q_f4c7_040():
    # Revenue deficit = 2,900 - 2,500.
    rd = revenue_deficit(2900, 2500)
    key = {400: "A", 600: "B", 200: "C", 5400: "D"}[rd]
    return {"answer": key, "computed": rd}


def q_f4c7_041():
    # Primary deficit = fiscal deficit 5,60,000 - interest 2,10,000.
    pd = primary_deficit(560000, 210000)
    key = {770000: "A", 350000: "B", 210000: "C", 560000: "D"}[pd]
    return {"answer": key, "computed": pd}
