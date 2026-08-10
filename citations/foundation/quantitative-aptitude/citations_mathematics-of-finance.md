# Citations — Foundation P3 Ch 4 · Mathematics of Finance (Time Value of Money)

Generated 10 Aug 2026 in the same session as the chapter content. This chapter
rests on the **ICAI Foundation Study Material, Paper 3, Chapter 4 (Time Value of
Money)**, read for scope and for the formula set it teaches, and on the standard
statements of those formulas as they appear in any elementary finance text. The
Study Material is ICAI-copyrighted, so it is used `reference_only`: every
position below is **paraphrased and cited by chapter subject only, never
reproduced**, no ICAI question text or worked answer is copied, and all numbers,
names and scenarios in the notes and in the bank are fresh.

**No bare Act exists for this chapter.** Nothing here states a legal position:
the content is arithmetic, and it is true whatever the law says. That is why the
notes frontmatter carries `applicable_attempts` but deliberately **omits
`law_as_on_date`** — there is no legal cut-off to pin, and an empty or invented
date would be worse than no date. The bank's questions likewise carry
`applicableAttempts` and `lastVerified` but no `lawAsOnDate`.

What a reviewer must actually check here is therefore different from a law
chapter. The formulas are not in doubt; the **conventions** are. Sections A to N
record each formula as it is conventionally stated and where it is used. The
**Reviewer's checklist of conventions** at the end records every rounding and
convention choice made in this chapter, because a single different choice
silently changes answer keys.

---

## A. The time value of money and the two interest bases

- **Position relied on (paraphrase):** a sum available today is worth more than
  the same sum available later, because it can be invested and earn. Interest is
  the price paid for the use of money for a period. Under **simple interest** the
  charge is computed on the original principal for every period; under **compound
  interest** the interest earned at the end of a period is added to the principal
  and itself earns in later periods. The two agree over one conversion period and
  diverge thereafter, compound interest always being the larger.
- **Formulas as conventionally stated:** `I = P i t`; `A = P(1 + i t)`;
  `A = P(1 + i)^n`; `CI = P[(1 + i)^n − 1]`.
- **Source:** ICAI Foundation SM Paper 3, Ch 4 (Time Value of Money), May 2026
  edition — reference_only; standard elementary statements of the same formulas.
- **Used in:** notes §1, §2, §3; q-f3c4-001 to q-f3c4-014, worked example 1.
- **Spot-checked by:** _(blank until a human checks)_

## B. Difference between compound and simple interest over 2 and 3 periods

- **Position relied on (paraphrase):** expanding `(1 + i)^n` gives the standard
  shortcuts for the excess of compound over simple interest — `P i²` for two
  periods and `P i²(3 + i)` for three. They are algebraic identities, not
  approximations.
- **Used in:** notes §3 (pointer callout); q-f3c4-012, q-f3c4-013, q-f3c4-014;
  worked example 1 working note 3. The verifier computes the difference the long
  way (compound less simple) and asserts the shortcut reproduces it, so the two
  routes check each other.
- **Spot-checked by:** _(blank until a human checks)_

## C. Growth and decay at a constant rate

- **Position relied on (paraphrase):** a quantity falling by a constant
  proportion of its own current value is the compound formula with a negative
  rate, `Value = P(1 − d)^n`. This chapter treats it purely as the mathematics of
  constant-rate decline.
- **Deliberate scope boundary:** the reducing-balance method of **depreciation**
  is taught as an accounting treatment in Foundation Paper 1
  (`depreciation-and-amortisation`). This chapter does not repeat that treatment,
  does not discuss the choice of method, the entries or the disclosure, and asks
  only for the arithmetic of the written-down value.
- **Used in:** notes §3; q-f3c4-015.
- **Spot-checked by:** _(blank until a human checks)_

## D. Conversion periods

- **Position relied on (paraphrase):** where interest is converted more than once
  a year, the rate per conversion period is the annual nominal rate divided by
  the number of conversions, and the number of periods is the number of years
  multiplied by the same number. Both adjustments are made together.
- **Formula:** `i = r ÷ m`, `n = years × m`.
- **Used in:** notes §4 and the conversion table; q-f3c4-003, q-f3c4-018 to
  q-f3c4-021, q-f3c4-033, q-f3c4-035, q-f3c4-044, cs-f3c4-01 (all four
  sub-questions); worked examples 5 and 11.
- **Spot-checked by:** _(blank until a human checks)_

## E. Solving for the rate and for the time

- **Position relied on (paraphrase):** the compound formula is solved for the
  rate by taking the n-th root of the growth ratio, `i = (A ÷ P)^(1/n) − 1`, and
  for the time by logarithms, `n = [log A − log P] ÷ log(1 + i)`, any consistent
  base serving. The principal cancels in every "doubling / tripling" question, so
  only the ratio matters.
- **Assumed prior learning:** logarithms are taught in **Paper 3 Chapter 1**, and
  this chapter uses them without re-teaching them. Where a question needs a log
  value it is supplied in the stem to four decimal places.
- **Used in:** notes §5; q-f3c4-007 (the simple-interest analogue), q-f3c4-022 to
  q-f3c4-025, q-f3c4-049; worked example 3.
- **Spot-checked by:** _(blank until a human checks)_

## F. Nominal rate, effective rate and continuous compounding

- **Position relied on (paraphrase):** the effective annual rate is the single
  yearly rate that produces the same amount in one year as the stated nominal
  rate compounded m times, `E = (1 + r ÷ m)^m − 1`, and it is the only proper
  basis for comparing offers quoted on different conversion periods. It equals
  the nominal rate only for yearly conversion and rises, at a decreasing pace,
  with the frequency of conversion. The limit of that process is **continuous
  compounding**, `A = P e^(r t)` with `E = e^r − 1`.
- **Reverse conversion:** `r = m[(1 + E)^(1/m) − 1]`.
- **Scope note for the reviewer:** the Study Material's treatment of continuous
  compounding is brief. This chapter keeps it to the two formulas above, one
  worked amount and the position of continuous compounding as the ceiling of the
  effective-rate table. If the May 2026 edition drops continuous compounding
  altogether, q-f3c4-029 and q-f3c4-030 and the last row of the §6 table should
  come out; nothing else depends on them.
- **Used in:** notes §6; q-f3c4-020, q-f3c4-026 to q-f3c4-030; worked example 2.
- **Spot-checked by:** _(blank until a human checks)_

## G. Present value and future value of a single sum

- **Position relied on (paraphrase):** discounting is compounding solved for the
  principal, `PV = FV(1 + i)^(−n)`. The discount factor is the reciprocal of the
  matching compound factor, is always below 1, and falls as either the rate or
  the time rises. Unequal cash flows are discounted one by one and added; no
  annuity shortcut applies to them.
- **Used in:** notes §7; q-f3c4-017, q-f3c4-031, q-f3c4-032, q-f3c4-033; worked
  example 4.
- **Spot-checked by:** _(blank until a human checks)_

## H. Annuities — ordinary, due, and the vocabulary

- **Position relied on (paraphrase):** an annuity is a series of equal payments
  at equal intervals. In an **ordinary annuity** (annuity regular / immediate)
  the payment falls at the **end** of each period; in an **annuity due** it falls
  at the **beginning**. The four standard results are
  `FV = R[(1 + i)^n − 1] ÷ i`, `PV = R[1 − (1 + i)^(−n)] ÷ i`, and the same two
  multiplied by `(1 + i)` for an annuity due. The present value factor is always
  below n and the future value factor always above n, and the two are linked by
  `P(n, i) × (1 + i)^n = A(n, i)`.
- **Used in:** notes §8 to §11; q-f3c4-034 to q-f3c4-040, cs-f3c4-03; worked
  examples 5, 6 and 10.
- **Spot-checked by:** _(blank until a human checks)_

## I. Perpetuity and growing perpetuity

- **Position relied on (paraphrase):** letting n tend to infinity in the present
  value annuity formula gives `PV = R ÷ i` for a level perpetuity. Where the
  payment grows at a constant rate g per period, `PV = R ÷ (i − g)`, valid only
  while `g < i`, and R is the payment **one period from now**.
- **Scope note for the reviewer:** the **growing** perpetuity is the one item in
  this chapter most likely to sit outside the Foundation syllabus. It is taught
  in notes §12 and tested by q-f3c4-042 and worked example 10 part (b). If the
  May 2026 SM does not carry it, drop that question and that half of the worked
  example; the level perpetuity (q-f3c4-041) stands on its own.
- **Used in:** notes §12; q-f3c4-041, q-f3c4-042; worked example 10.
- **Spot-checked by:** _(blank until a human checks)_

## J. Sinking funds

- **Position relied on (paraphrase):** a sinking fund accumulates a known sum by
  the target date through equal periodic deposits that earn interest, so the
  deposit is the future-value annuity formula solved for R,
  `R = S i ÷ [(1 + i)^n − 1]`. The total deposited is always less than the sum
  required, the balance being the fund's own interest.
- **Used in:** notes §13; q-f3c4-036, q-f3c4-043; worked example 7.
- **Spot-checked by:** _(blank until a human checks)_

## K. Loan amortisation and the equated instalment

- **Position relied on (paraphrase):** a loan repaid by equal instalments equals
  the present value of those instalments on the date of the loan, so
  `R = Loan × i ÷ [1 − (1 + i)^(−n)]`. Each instalment is split: interest for the
  period is the **opening balance** times the periodic rate, and the remainder
  reduces the principal, so the interest slice shrinks and the principal slice
  grows over the life of the loan. The balance outstanding after k instalments is
  the present value of those still to come, `R × P(n − k, i)`.
- **Used in:** notes §14 and the worked schedule; q-f3c4-044, q-f3c4-045,
  cs-f3c4-01 (all four sub-questions); worked example 8.
- **Spot-checked by:** _(blank until a human checks)_

## L. Net present value and the accept-reject rule

- **Position relied on (paraphrase):** NPV is the present value of a proposal's
  cash inflows less the present value of its outflows, discounted at the rate of
  return the business requires. A positive NPV means acceptance, a negative NPV
  rejection, and a zero NPV means the proposal earns exactly the required rate.
  An outlay incurred today is not discounted. Where two proposals are mutually
  exclusive, the higher NPV decides.
- **Used in:** notes §15, §16; q-f3c4-046, q-f3c4-047, cs-f3c4-02; worked
  example 9.
- **Spot-checked by:** _(blank until a human checks)_

## M. Profitability index

- **Position relied on (paraphrase):** the profitability index (benefit-cost
  ratio, desirability factor) is the present value of the inflows divided by the
  present value of the outlay. A single proposal is accepted when the index
  exceeds 1, which is exactly when its NPV is positive, so the two tests never
  disagree on one project. Rankings of different projects can diverge when the
  outlays differ, and the index is the more useful ranking only when capital is
  rationed.
- **Scope note for the reviewer:** capital rationing is mentioned in notes §16 in
  two sentences and is not tested. Confirm the Foundation SM goes this far; if it
  does not, the two sentences and the small comparison table can be cut without
  touching any question.
- **Used in:** notes §16; q-f3c4-048, cs-f3c4-02-c; worked example 9.
- **Spot-checked by:** _(blank until a human checks)_

## N. Compound annual growth rate and simple bond valuation

- **Position relied on (paraphrase):** CAGR is the constant yearly compounding
  rate that carries a beginning value to an ending value,
  `(Ending ÷ Beginning)^(1/n) − 1`, where n is the number of **years between**
  the two figures. It ignores what happened in between, and it is not the
  arithmetic mean of the yearly growth rates. A bond's value is the present value
  of its coupons (an ordinary annuity at the yield) plus the present value of its
  redemption amount, so `Value = Coupon × P(n, y) + Redemption × (1 + y)^(−n)`.
  The **coupon rate** applies to the face value to fix the rupee coupon; the
  **yield** does the discounting. A bond sells at a discount when the yield
  exceeds the coupon rate, at par when they are equal, and at a premium when the
  yield is lower.
- **Used in:** notes §17, §18; q-f3c4-049, q-f3c4-050; worked examples 10 and 11.
- **Spot-checked by:** _(blank until a human checks)_

---

# Reviewer's checklist of conventions

**These matter more here than anywhere else in the paper.** Every item below is a
choice, not a fact. A different choice does not merely change the wording — it
moves a computed figure and therefore **changes answer keys**. Please confirm
each against the ICAI SM (May 2026 ed.) and initial it.

1. **Decimal places in a factor.** Every compound, discount and annuity factor is
   quoted in the notes to **four decimal places**, and the full unrounded value
   is carried into the arithmetic. If the SM works to three decimals, several
   answers move by a few rupees; the option gaps in this bank are wide enough to
   survive that, but the *displayed* working notes would no longer match.

2. **When money is rounded.** Money is rounded **once, at the final step**, to
   the nearest paisa, half-up. Interest is **not** rounded at the end of each
   period. If the SM rounds period by period (as some bank statements do), long
   amortisation and sinking-fund answers drift by several rupees.

3. **Days in a year for simple interest.** A year is **365 days**
   (q-f3c4-006 turns on it: 146 days gives ₹ 7,200 on 365 days and ₹ 7,300 on
   360). If the SM uses a 360-day commercial year by default, that key flips to
   option A and the option explanations must swap.

4. **Months.** Months are treated as **exact twelfths** of a year — 8 months is
   8/12, and 3 years 6 months is 3.5 years (q-f3c4-005, q-f3c4-009). No
   day-counting inside a month is used anywhere.

5. **The ordinary annuity is the default.** Where a question does not say when
   the payment falls, it is treated as falling at the **end** of the period. An
   annuity due is used **only** where the stem says "at the beginning", "in
   advance" or "the first payment today" (q-f3c4-039, q-f3c4-040, cs-f3c4-03-c
   and worked examples 5, 6). Confirm the SM does not make the annuity due the
   default anywhere — for instance in recurring-deposit or lease illustrations,
   where commercial practice often pays in advance.

6. **Cash flows fall at period ends in NPV work.** "In the third year" is read as
   the **end** of year 3; the initial outlay is spent **today** and carries a
   factor of 1 (q-f3c4-046, q-f3c4-047, cs-f3c4-02). Mid-year conventions are not
   used at this level.

7. **Amortisation schedules use the unrounded instalment.** The schedules in
   notes §14, worked example 8 and cs-f3c4-01 are built row by row from the
   unrounded instalment, so the closing balance falls to exactly zero. A bank
   that rounds the instalment to the nearest rupee leaves a small residue that
   the final instalment absorbs. If the SM rounds the EMI first, the last row of
   every schedule changes and cs-f3c4-01-d moves by a few rupees.

8. **Counting years for a CAGR.** The number of years is the number of
   **intervals** between the two figures, so 2019-20 to 2025-26 is 6 years and
   2021-22 to 2025-26 is 4 (q-f3c4-049, worked example 10). Confirm the SM counts
   the same way; counting the labels instead would give 7 and 5 and change both
   keys.

9. **Logarithm values supplied in stems.** Where an answer needs a logarithm, the
   stem supplies it to four decimals (q-f3c4-023, q-f3c4-024). The verifier
   recomputes with full-precision natural logarithms and asserts the two agree to
   within 0.01 of a year, so the printed logs and the exact answer cannot drift
   apart unnoticed.

10. **The value of e.** Continuous compounding uses e = 2.71828 in the notes and
    full precision in the verifier (q-f3c4-029, q-f3c4-030).

11. **Rates as decimals.** Every formula takes the rate as a decimal (8% = 0.08).
    Several distractors are built from the failure to convert, which is a real
    student error, not a manufactured one.

12. **Percentage answers are quoted to four decimals** where the question is
    about a rate (12.5509%), and to two decimals where it is about an
    approximate rate (8.89%). Confirm this matches the precision the SM's own
    options use, since a rate rounded to one decimal can make two options
    indistinguishable.

**Machine verification already done (do not repeat it).** All **57** numerical
questions in this bank are recomputed from their stems by
`scripts/verify_numerical/verify_mathematics-of-finance.py`, which uses
`decimal.Decimal` under an explicit context, builds the amortisation and
drawdown schedules row by row rather than asserting their end points, and maps
each computed value to an option by value. The runner reports 0 failures. Your
time is better spent on the twelve conventions above and on the three scope
calls flagged in sections F, I and M.

**Spot-checked by:** _(blank until a human checks)_

