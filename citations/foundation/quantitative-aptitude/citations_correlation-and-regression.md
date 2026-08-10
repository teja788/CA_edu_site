# Citations — Foundation P3 Ch 17 · Correlation and Regression

Generated 11 Aug 2026 in the same session as the chapter content. This chapter
rests on the **ICAI Foundation Study Material, Paper 3, Part C (Statistics),
Correlation and Regression**, read for scope and for the formula set it teaches,
and on the standard statements of those formulas as they appear in any elementary
statistics text. The Study Material is ICAI-copyrighted, so it is used
`reference_only`: every position below is **paraphrased and cited by chapter
subject only, never reproduced**, no ICAI question text or worked answer is
copied, and all numbers, names and scenarios in the notes and in the bank are
fresh.

**No bare Act exists for this chapter.** Nothing here states a legal position:
the content is arithmetic and statistical method, true whatever the law says.
That is why the notes frontmatter carries `applicable_attempts` but deliberately
**omits `law_as_on_date`** — there is no legal cut-off to pin, and an empty or
invented date would be worse than no date. The bank's questions likewise carry
`applicableAttempts` and `lastVerified` but no `lawAsOnDate`.

What a reviewer must check here is therefore different from a law chapter. The
formulas are not in doubt; the **conventions** are (which rank goes to a tie, how
covariance is scaled, how many decimals an option needs). Sections A to H record
each formula as it is conventionally stated and where it is used. The
**Reviewer's checklist of conventions** at the end records every convention
choice made in this chapter, because a single different choice silently changes
answer keys.

---

## A. Meaning, types and scatter diagrams of correlation

- **Position relied on (paraphrase):** two variables are correlated when they
  tend to change together. The direction is the sign — positive when they move
  the same way, negative when they move oppositely, zero when there is no linear
  tendency — and the strength is how tightly the points cluster about a straight
  line. A scatter diagram plots each pair (x, y) as a dot; the tilt of the cloud
  is the sign and the tightness is the size of r. Correlation measures a
  **linear** tendency only and does not imply causation.
- **Source:** ICAI Foundation SM Paper 3, Statistics — Correlation and Regression
  — reference_only; standard elementary statements of the same ideas.
- **Used in:** notes §1, §2; q-f3c17-001 to q-f3c17-003.
- **Spot-checked by:** _(blank until a human checks)_

## B. Karl Pearson's product-moment coefficient r

- **Position relied on (paraphrase):** the product-moment coefficient is the
  covariance divided by the product of the standard deviations, and equivalently
  is computed from the five raw sums.
- **Formulas as conventionally stated:**
  `r = Cov(x, y) / (sx sy)`;
  `Cov(x, y) = Sum (x - xbar)(y - ybar) / n`;
  `r = [n Sxy - Sx Sy] / sqrt([n Sx2 - (Sx)^2] [n Sy2 - (Sy)^2])`.
- **Used in:** notes §3; q-f3c17-006, q-f3c17-007, q-f3c17-008, q-f3c17-026,
  q-f3c17-031, q-f3c17-034, q-f3c17-043; worked examples 1, 2, 7. The verifier
  computes r from the stem's own (x, y) list or its five sums, using exact
  Fractions for the rational parts and `math.sqrt` with a tolerance for the root.
- **Spot-checked by:** _(blank until a human checks)_

## C. Properties of the correlation coefficient

- **Position relied on (paraphrase):** r satisfies −1 ≤ r ≤ 1; it is a pure
  number, free of units; it is unaffected by a change of origin and by a change
  of scale, except that a **negative** scale factor reverses its sign; it is
  symmetric in x and y; and it is the geometric mean of the two regression
  coefficients. These are the standard properties of the product-moment
  coefficient.
- **Used in:** notes §4; q-f3c17-004, q-f3c17-005; worked examples 2 and 3.
- **Spot-checked by:** _(blank until a human checks)_

## D. Spearman's rank correlation, with and without ties

- **Position relied on (paraphrase):** for ranked data the rank correlation
  coefficient is `R = 1 - 6 Sum d^2 / [n(n^2 - 1)]`, where d is the difference of
  the two ranks of a pair. When values tie, each tied item takes the **average**
  of the rank positions it occupies, and a correction `Sum (m^3 - m)/12` (one
  term per tied group, m the size of the group) is added to Sum d^2 before
  substitution.
- **Used in:** notes §5; q-f3c17-020, q-f3c17-021, q-f3c17-022, q-f3c17-039;
  worked examples 4 and 5. The verifier assigns average ranks in descending order
  and adds the tie correction exactly (as a Fraction), so both the no-tie and the
  tied cases are recomputed from the stem's own scores or rank differences.
- **Spot-checked by:** _(blank until a human checks)_

## E. Probable error and the significance of r

- **Position relied on (paraphrase):** the probable error of the coefficient is
  `PE = 0.6745 (1 - r^2) / sqrt(n)`. The true correlation is expected within
  r ± PE; as a rough test, correlation is treated as **not significant** when r is
  below PE and as **significant** when r exceeds 6 × PE. The constant 0.6745 is
  the standard one.
- **Used in:** notes §6; q-f3c17-023, q-f3c17-024, q-f3c17-040, q-f3c17-048;
  worked example 6.
- **Spot-checked by:** _(blank until a human checks)_

## F. The two lines of regression

- **Position relied on (paraphrase):** by least squares there are two regression
  lines. The line of y on x, `y - ybar = b_yx (x - xbar)`, minimises squared
  errors in y; the line of x on y, `x - xbar = b_xy (y - ybar)`, minimises squared
  errors in x. Both lines pass through the point of means (xbar, ybar); they
  coincide only when r = ±1 and are perpendicular when r = 0. To estimate y use
  the line of y on x, and to estimate x use the line of x on y.
- **Used in:** notes §7, §10; q-f3c17-016, q-f3c17-017, q-f3c17-018, q-f3c17-019,
  q-f3c17-032, q-f3c17-036, q-f3c17-037, q-f3c17-038, q-f3c17-045, q-f3c17-046,
  q-f3c17-050; worked examples 8 and 9. Where a question gives the two line
  equations, the verifier solves them exactly for the means.
- **Spot-checked by:** _(blank until a human checks)_

## G. The regression coefficients and their link with r

- **Position relied on (paraphrase):** the regression coefficients share the
  numerator of r and differ only in the denominator —
  `b_yx = [n Sxy - Sx Sy] / [n Sx2 - (Sx)^2]` and
  `b_xy = [n Sxy - Sx Sy] / [n Sy2 - (Sy)^2]` — and equivalently
  `b_yx = r (sy / sx)`, `b_xy = r (sx / sy)`, so
  `b_yx = Cov / sx^2` and `b_xy = Cov / sy^2`. Both coefficients carry the sign of
  r; their product is r², so `r = ±sqrt(b_yx b_xy)` with the common sign of the
  two coefficients; because r² ≤ 1 the product of the two coefficients cannot
  exceed 1, and their arithmetic mean is at least r.
- **Used in:** notes §8, §9; q-f3c17-009 to q-f3c17-015, q-f3c17-027 to
  q-f3c17-030, q-f3c17-033, q-f3c17-035, q-f3c17-041, q-f3c17-042, q-f3c17-044,
  q-f3c17-047, q-f3c17-049; worked examples 7 and 9. The verifier takes the two
  b's straight from the stem for r = ±sqrt(b_yx b_xy), fixing the sign from the
  coefficients rather than from the answer key.
- **Spot-checked by:** _(blank until a human checks)_

## H. Correlation versus regression

- **Position relied on (paraphrase):** correlation gives one pure, symmetric
  number for the strength and direction of a linear relationship; regression gives
  two lines, in units, to estimate one variable from the other. They share the
  same five sums but answer different questions. r and the two regression
  coefficients always share one sign, r is the geometric mean of the two
  coefficients, and the two lines cross at the means. r never exceeds 1 in size,
  while a regression coefficient may.
- **Used in:** notes §11; q-f3c17-025; and drawn on throughout the regression
  questions.
- **Spot-checked by:** _(blank until a human checks)_

---

# Reviewer's checklist of conventions

**These matter here more than the formulas do.** Every item below is a choice,
not a fact. A different choice does not merely change the wording — it moves a
computed figure and therefore **changes answer keys**. Please confirm each
against the ICAI SM and initial it.

1. **The computing form of r.** r is built from the five raw sums as
   `[n Sxy - Sx Sy] / sqrt([n Sx2 - (Sx)^2] [n Sy2 - (Sy)^2])`. The notes and the
   verifier both use this form; the deviation form gives the same value.

2. **How covariance is scaled.** Covariance is the **mean** of the deviation
   products, `Cov = Sum (x - xbar)(y - ybar) / n = (n Sxy - Sx Sy) / n^2`
   (q-f3c17-007, q-f3c17-031). If the SM defines a "sum of products" without
   dividing by n, q-f3c17-007's key moves from 1.2 to 6 and its distractors swap.

3. **Ranking direction and ties.** Ranks are assigned with the **highest value as
   rank 1**, and tied items take the **average** of the positions they occupy
   (q-f3c17-022, worked example 5). Ranking the lowest value as rank 1 does not
   change R when done consistently in both series, but the illustrated ranks in
   the notes assume highest = 1. Confirm the SM's convention.

4. **The tie correction.** One `(m^3 - m)/12` term is added to Sum d^2 for **each**
   tied group in **either** series (q-f3c17-022). Some texts omit the correction
   at Foundation level; if the SM does, that key moves from 0.675 to 0.75.

5. **The probable-error constant.** PE uses **0.6745** (q-f3c17-023, q-f3c17-040,
   q-f3c17-048). Confirm the SM uses 0.6745 and not a rounded 0.674 or 0.675; the
   option gaps in this bank are wide enough to survive that, but the displayed
   working would differ.

6. **The significance rule of thumb.** Correlation is called significant when
   r > 6 × PE and not significant when r < PE (q-f3c17-024). Confirm the SM states
   the six-times rule; some texts phrase significance differently.

7. **Which line predicts which variable.** To estimate y, the line of **y on x**
   is used; to estimate x, the line of **x on y** (q-f3c17-016, q-f3c17-017,
   q-f3c17-032, q-f3c17-045, q-f3c17-050). This is the standard convention and the
   distractors are built from using the wrong line.

8. **Sign of r from the two coefficients.** r takes the **common sign** of the two
   regression coefficients, positive root when both are positive and negative root
   when both are negative (q-f3c17-012, q-f3c17-030). A pair of coefficients with
   opposite signs is impossible and is used only as an eliminable distractor.

9. **Decimal places in an option.** Correlation coefficients and regression
   coefficients are quoted to two decimals where that separates the options and to
   more where needed (rank correlation and probable error to the precision the
   distractors require). Confirm this matches the precision the SM's own options
   use, since a value rounded too far can make two options indistinguishable.

10. **Rounding of r under the root.** r is computed from the unrounded root and
    rounded only at the end; the verifier carries the rational parts exactly and
    takes a single `math.sqrt` at the last step (q-f3c17-008, q-f3c17-026,
    q-f3c17-043). Rounding the brackets first can move the second decimal.

**Machine verification already done (do not repeat it).** All **36** numerical
questions in this bank are recomputed from their stems by
`scripts/verify_numerical/verify_correlation-and-regression.py`, which uses
`fractions.Fraction` for the exact rational arithmetic (sums, covariances,
regression coefficients, rank correlation) and `math.sqrt` with a tolerance for
r and for `r = ±sqrt(b_yx b_xy)`, and maps each computed value to an option by
value rather than by the answer key. The runner reports 0 failures. Your time is
better spent on the ten conventions above.

**Spot-checked by:** _(blank until a human checks)_
