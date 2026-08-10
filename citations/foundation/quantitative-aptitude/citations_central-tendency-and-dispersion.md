# Citations — Foundation P3 Ch 14 · Measures of Central Tendency and Dispersion

Generated 11 Aug 2026 in the same session as the chapter content. This chapter
rests on the **ICAI Foundation Study Material, Paper 3, Statistics — Measures of
Central Tendency and Measures of Dispersion**, read for scope and for the formula
set it teaches, and on the standard statements of those formulas as they appear in
any elementary statistics text. The Study Material is ICAI-copyrighted, so it is
used `reference_only`: every position below is **paraphrased and cited by subject
only, never reproduced**, no ICAI question text or worked answer is copied, and all
numbers, names and scenarios in the notes and in the bank are fresh.

**No bare Act exists for this chapter.** Nothing here states a legal position: the
content is arithmetic, and it is true whatever the law says. That is why the notes
frontmatter carries `applicable_attempts` but deliberately **omits
`law_as_on_date`** — there is no legal cut-off to pin, and an empty or invented date
would be worse than no date. The bank's questions likewise carry `applicableAttempts`
and `lastVerified` but no `lawAsOnDate`.

What a reviewer must check here is therefore different from a law chapter. The
formulas are not in doubt; the **conventions** are — above all the population-vs-sample
standard-deviation choice. Sections A to K record each formula as it is conventionally
stated and where it is used. The **Reviewer's checklist of conventions** at the end
records every choice made in this chapter, because a single different choice silently
changes answer keys.

---

## A. Central tendency and the choice of average

- **Position relied on (paraphrase):** central tendency is the tendency of data to
  cluster around a central value. The arithmetic mean uses the value of every item and
  is therefore the average most affected by an extreme value; the median depends only
  on the middle position and is unaffected by the size of the extremes; the mode is the
  most frequent value.
- **Source:** ICAI Foundation SM Paper 3, Statistics — Measures of Central Tendency,
  May 2026 edition — reference_only; standard elementary statements of the same
  definitions.
- **Used in:** notes §1; q-f3c14-001.
- **Spot-checked by:** _(blank until a human checks)_

## B. Arithmetic mean — simple, weighted and combined

- **Position relied on (paraphrase):** the arithmetic mean is the total divided by the
  count; the weighted mean weights each item by its own weight; the combined mean of
  groups pools their totals and weights each group mean by its size.
- **Formulas as conventionally stated:** `x̄ = Σx ÷ n`; `x̄w = Σ(w x) ÷ Σw`;
  `x̄₁₂ = (n₁x̄₁ + n₂x̄₂) ÷ (n₁ + n₂)`; and the grouped forms
  `x̄ = Σ(f x) ÷ N` (direct) and `x̄ = A + (Σ f d ÷ N) × h` with `d = (x − A) ÷ h`
  (step-deviation).
- **Used in:** notes §2, §3; q-f3c14-002 to q-f3c14-008, q-f3c14-049, q-f3c14-050;
  worked examples 1 and 2.
- **Spot-checked by:** _(blank until a human checks)_

## C. Properties of the arithmetic mean

- **Position relied on (paraphrase):** the algebraic sum of deviations about the mean
  is zero, `Σ(x − x̄) = 0`; and under a linear transformation `y = k x + c` the mean
  becomes `ȳ = k x̄ + c`. The step-deviation method is exactly this change of origin (A)
  and scale (h) read backwards.
- **Used in:** notes §4; q-f3c14-009, q-f3c14-010.
- **Spot-checked by:** _(blank until a human checks)_

## D. Median

- **Position relied on (paraphrase):** the median is the middle value of the ordered
  data. For individual and discrete series the position is the `(n + 1) ÷ 2` th item
  (for even individual n, the average of the two middle items); for a continuous series
  the median class is located by `N ÷ 2` and the value found by interpolation
  `Median = L + [(N ÷ 2 − cf) ÷ f] × h`.
- **Convention note for the reviewer:** the continuous-series median uses `N ÷ 2`,
  **not** `(N + 1) ÷ 2`. Confirm the SM locates the median class the same way; the two
  give the same class here but the distinction is tested (q-f3c14-014 option D).
- **Used in:** notes §5; q-f3c14-011 to q-f3c14-015; worked example 3.
- **Spot-checked by:** _(blank until a human checks)_

## E. Mode

- **Position relied on (paraphrase):** the mode is the most frequent value. In a
  discrete series it is read by inspection (the value with the highest frequency); in a
  continuous series the modal class is the class with the highest frequency and the mode
  is `L + [(f₁ − f₀) ÷ (2f₁ − f₀ − f₂)] × h`, where f₀ is the class before the modal
  class and f₂ the class after it.
- **Used in:** notes §6; q-f3c14-016, q-f3c14-017; worked example 3.
- **Spot-checked by:** _(blank until a human checks)_

## F. The empirical relation between mean, median and mode

- **Position relied on (paraphrase):** for a moderately skewed distribution
  `Mean − Mode = 3 (Mean − Median)`, equivalently `Mode = 3 Median − 2 Mean`, an
  approximate relation in which the median lies one-third of the way from the mean to the
  mode. In a symmetrical distribution the three coincide: mean = median = mode.
- **Used in:** notes §7; q-f3c14-018, q-f3c14-019, q-f3c14-048; worked example 4.
- **Spot-checked by:** _(blank until a human checks)_

## G. Geometric mean and harmonic mean

- **Position relied on (paraphrase):** the geometric mean is the n-th root of the
  product, `GM = (x₁x₂…xₙ)^(1/n)`, and is the correct average for growth rates, ratios
  and index numbers (for two numbers `GM = √(ab)`). The harmonic mean is the reciprocal
  of the mean of the reciprocals, `HM = n ÷ Σ(1 ÷ x)`, and is the correct average for
  rates over equal distances (average speed). For positive unequal values `AM > GM > HM`,
  with equality only when all values are equal, and `GM² = AM × HM` for two numbers.
- **Used in:** notes §8, §9; q-f3c14-020 to q-f3c14-024; worked example 5.
- **Spot-checked by:** _(blank until a human checks)_

## H. Quartiles, deciles and percentiles

- **Position relied on (paraphrase):** partition values divide the ordered data into
  equal parts and are found like the median. For a continuous series the k-th quartile,
  decile and percentile use positions `kN ÷ 4`, `kN ÷ 10` and `kN ÷ 100` and the same
  interpolation formula; for individual and discrete series the positional rules use
  `(n + 1)`, interpolating between neighbouring items when the position is fractional.
- **Used in:** notes §10; q-f3c14-025 to q-f3c14-028; worked example 6.
- **Spot-checked by:** _(blank until a human checks)_

## I. Range, quartile deviation and mean deviation

- **Position relied on (paraphrase):** the range is `largest − smallest` with
  coefficient `(L − S) ÷ (L + S)`; the quartile deviation is `(Q₃ − Q₁) ÷ 2` with
  coefficient `(Q₃ − Q₁) ÷ (Q₃ + Q₁)`; the mean deviation is the average of the
  **absolute** deviations from a centre, `Σ f |x − A| ÷ N`, and is smallest when taken
  about the median. Each absolute measure has a relative (coefficient) form.
- **Used in:** notes §12, §13, §14; q-f3c14-029 to q-f3c14-034; worked example 6.
- **Spot-checked by:** _(blank until a human checks)_

## J. Standard deviation, variance and combined standard deviation

- **Position relied on (paraphrase):** the variance is the mean of the squared
  deviations and the standard deviation is its square root,
  `σ = √[Σ(x − x̄)² ÷ n]`, with the short-cut `σ² = Σx² ÷ n − x̄²` and the grouped coded
  form `σ = √[Σ f d² ÷ N − (Σ f d ÷ N)²] × h`. Two groups combine to
  `σ₁₂ = √{[n₁(σ₁² + d₁²) + n₂(σ₂² + d₂²)] ÷ (n₁ + n₂)}`, where `dᵢ = x̄ᵢ − x̄₁₂` measures
  each group mean's distance from the combined mean.
- **Population-vs-sample choice (the key convention):** this chapter divides by **n**
  (the population standard deviation), matching the Foundation SM and its worked
  examples. Every SD and variance figure in the notes and the bank uses divisor n, not
  (n − 1). Several distractors are built precisely from the (n − 1) divisor
  (q-f3c14-035 option C, q-f3c14-036 option D), so if the SM uses (n − 1) those keys
  move.
- **Used in:** notes §15, §16, §17; q-f3c14-035 to q-f3c14-039, q-f3c14-044; worked
  examples 7 and 8.
- **Spot-checked by:** _(blank until a human checks)_

## K. Coefficient of variation and change of origin and scale

- **Position relied on (paraphrase):** the coefficient of variation is the standard
  deviation as a percentage of the mean, `CV = (σ ÷ x̄) × 100`, the relative measure of
  dispersion; the lower the CV, the more consistent the data, so consistency is judged by
  the CV and never by the raw SD alone. Under `y = k x + c` the standard deviation is
  independent of the origin and depends on the scale, `σy = |k| σx`, and the variance is
  `σy² = k² σx²`.
- **Used in:** notes §18, §19; q-f3c14-040 to q-f3c14-043, q-f3c14-045 to q-f3c14-047;
  worked example 9.
- **Spot-checked by:** _(blank until a human checks)_

---

# Reviewer's checklist of conventions

**These matter more here than the formulas themselves.** Every item below is a choice,
not a fact. A different choice does not merely change the wording — it moves a computed
figure and therefore **changes answer keys**. Please confirm each against the ICAI SM
(May 2026 ed.) and initial it.

1. **Population standard deviation (divisor n).** Every standard deviation and variance
   in this chapter divides by **n**, not (n − 1). This is the single most important
   convention here. If the SM teaches the sample SD at Foundation level, q-f3c14-035 to
   q-f3c14-039 and q-f3c14-044 all move, and the (n − 1) distractors become the keys.

2. **Rounding.** Intermediate figures are carried unrounded (exact fractions in the
   verifier) and only the final answer is rounded — to **two decimal places** for
   irrational standard deviations, quartiles and modes, and exactly otherwise. Option
   gaps are wide enough that a third decimal never decides a key.

3. **Median of a continuous series uses N ÷ 2**, not (N + 1) ÷ 2; the (n + 1) rule is
   reserved for individual and discrete series (q-f3c14-011 to q-f3c14-015).

4. **Quartiles, deciles and percentiles of a continuous series use kN ÷ 4, kN ÷ 10 and
   kN ÷ 100** to locate the class, then the median-style interpolation (q-f3c14-025 to
   q-f3c14-027). For an individual series the positional rule is (n + 1) with
   interpolation (q-f3c14-028). Confirm the SM does not use the (n + 1) rule inside
   continuous series or kN with a +1 adjustment.

5. **Mode formula orientation.** f₀ is the frequency of the class **before** the modal
   class and f₂ the class **after** it (q-f3c14-017). Swapping them is a built distractor.

6. **Empirical relation direction.** `Mode = 3 Median − 2 Mean` (equivalently
   `Median = (Mode + 2 Mean) ÷ 3`). The reversed form `3 Mean − 2 Median` is a distractor
   (q-f3c14-018, q-f3c14-019).

7. **Which average for which data.** The geometric mean is used for growth rates and
   ratios and the harmonic mean for rates over equal distances (q-f3c14-023, worked
   example 5). Confirm the SM makes the same recommendation.

8. **Mean deviation uses absolute deviations** and is taken about the mean unless the
   question says "about the median" (q-f3c14-032 to q-f3c14-034). The coefficient of mean
   deviation divides by the centre used (q-f3c14-033 divides by the median).

9. **Combined SD includes the separation terms** d₁², d₂² (q-f3c14-039). A plain weighted
   average of the two group SDs is a distractor and is always too small.

10. **Consistency is judged by the coefficient of variation, not the raw SD**
    (q-f3c14-041). The steadier series can have the larger absolute SD.

11. **Change of origin and scale.** SD independent of origin, multiplied by |k| under
    scale; variance multiplied by k²; mean changes with both (q-f3c14-042, q-f3c14-043,
    q-f3c14-047). Confirm the SM states these standard results.

12. **Rates as decimals and percentages.** The coefficient of variation is quoted as a
    percentage (q-f3c14-040, q-f3c14-046); coefficients of range and quartile deviation
    are pure numbers (q-f3c14-031).

**Machine verification already done (do not repeat it).** All **45** numerical questions
in this bank are recomputed from their stems by
`scripts/verify_numerical/verify_central-tendency-and-dispersion.py`, which uses exact
`fractions.Fraction` arithmetic for the rational measures, `math.sqrt` with a tolerance
for the irrational standard deviations, and maps each computed value to an option by
reading the printed option figures from the bank — never by trusting the answer key. The
runner reports 0 failures. Your time is better spent on the twelve conventions above,
above all the population-vs-sample standard-deviation choice in item 1.

**Spot-checked by:** _(blank until a human checks)_
