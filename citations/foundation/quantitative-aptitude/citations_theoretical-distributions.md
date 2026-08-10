# Citations — Foundation P3 Ch 16 · Theoretical Distributions

Generated 11 Aug 2026 in the same session as the chapter content. This chapter
rests on the **ICAI Foundation Study Material, Paper 3, Chapter 16 (Theoretical
Distributions)**, read for scope and for the formula set it teaches, and on the
standard statements of the binomial, Poisson and normal distributions as they
appear in any elementary statistics text. The Study Material is ICAI-copyrighted,
so it is used `reference_only`: every position below is **paraphrased and cited by
chapter subject only, never reproduced**, no ICAI question text or worked answer
is copied, and all numbers, names and scenarios in the notes and in the bank are
fresh.

**No bare Act exists for this chapter.** Nothing here states a legal position: the
content is mathematics, and it is true whatever the law says. That is why the
notes frontmatter carries `applicable_attempts` but deliberately **omits
`law_as_on_date`** — there is no legal cut-off to pin, and an empty or invented
date would be worse than no date. The bank's questions likewise carry
`applicableAttempts` and `lastVerified` but no `lawAsOnDate`.

What a reviewer must actually check here is therefore different from a law
chapter. The formulas are not in doubt; the **conventions** are — in particular
the value of e used, the standard z-areas relied on, and the 68-95-99.7
convention. Sections A to G record each formula as it is conventionally stated and
where it is used. The **Reviewer's checklist of conventions** at the end records
every rounding and convention choice made, because a single different choice
silently changes answer keys.

---

## A. Probability distributions — the framework

- **Position relied on (paraphrase):** a random variable attaches a number to each
  outcome, and a probability distribution lists each value with its probability. A
  distribution is **theoretical** when its probabilities come from a mathematical
  law fixed by parameters, and **observed** when they come from counting data.
  Every distribution satisfies `0 ≤ P ≤ 1` and `Σ P = 1`. Discrete distributions
  (binomial, Poisson) attach probability to whole-number values; continuous
  distributions (normal) spread it over an interval.
- **Source:** ICAI Foundation SM Paper 3, Ch 16 (Theoretical Distributions), May
  2026 edition — reference_only; standard elementary statements.
- **Used in:** notes §1; q-f3c16-001, q-f3c16-002.
- **Spot-checked by:** _(blank until a human checks)_

## B. The binomial distribution — law, mean, variance, mode

- **Position relied on (paraphrase):** for n independent Bernoulli trials with
  constant success probability p (and q = 1 − p), the number of successes X has
  `P(X = r) = nCr p^r q^(n−r)`, r = 0 … n. Its **mean is n p**, its **variance is
  n p q** (always below the mean because q < 1), and its **standard deviation is
  √(n p q)**. The **mode** is the integer part of (n + 1)p, with two modes at
  (n + 1)p and (n + 1)p − 1 when (n + 1)p is a whole number. `P(at least one) =
  1 − q^n`. The n + 1 terms are those of the expansion of (q + p)^n, so they sum
  to 1.
- **Formulas as conventionally stated:** `P(X = r) = nCr p^r q^(n−r)`;
  `Mean = n p`; `Variance = n p q`; `SD = √(n p q)`; `Mode = integer part of
  (n + 1)p`; parameter recovery `q = variance ÷ mean`, `p = 1 − q`, `n = mean ÷ p`.
- **Used in:** notes §2, §3; q-f3c16-003 to q-f3c16-013, q-f3c16-015, q-f3c16-044,
  q-f3c16-046, q-f3c16-049; worked examples 1, 2, 3. The verifier computes every
  binomial probability EXACTLY with `math.comb` and `fractions.Fraction`, so the
  four-decimal option is checked against an exact rational.
- **Spot-checked by:** _(blank until a human checks)_

## C. Fitting a binomial distribution

- **Position relied on (paraphrase):** to fit a binomial, take n as the largest
  possible count and estimate p from the data mean (p = mean ÷ n); the expected
  frequency of r successes over N repetitions is `N × nCr p^r q^(n−r)`, and the
  expected frequencies sum to N.
- **Used in:** notes §4; q-f3c16-014; worked example 4.
- **Spot-checked by:** _(blank until a human checks)_

## D. The Poisson distribution — law, mean, variance, additive property

- **Position relied on (paraphrase):** the Poisson is the limit of the binomial as
  n → ∞ and p → 0 with n p = m finite. Its law is `P(X = x) = e^(−m) m^x ÷ x!`,
  x = 0, 1, 2, …, with a single parameter m. Its **mean and variance are both m**,
  so its **standard deviation is √m**. `P(X = 0) = e^(−m)` and `P(at least one) =
  1 − e^(−m)`. The **additive property**: the sum of independent Poisson variables
  is Poisson with mean the sum of the means. The **mode** follows the same
  integer-part rule as the binomial with m in place of (n + 1)p, and the
  **recurrence** is `P(x + 1) = P(x) × m ÷ (x + 1)`.
- **Formulas as conventionally stated:** `P(X = x) = e^(−m) m^x ÷ x!`;
  `Mean = Variance = m`; `SD = √m`; additive `Poisson(m₁) + Poisson(m₂) =
  Poisson(m₁ + m₂)`; recurrence `P(x + 1) = P(x) m ÷ (x + 1)`.
- **Used in:** notes §5, §6; q-f3c16-016 to q-f3c16-025, q-f3c16-027, q-f3c16-045,
  q-f3c16-047; worked examples 5, 6, 10. The verifier uses `math.exp` with a
  tolerance and cross-checks the P(1) = P(2) recurrence question.
- **Spot-checked by:** _(blank until a human checks)_

## E. Fitting a Poisson distribution

- **Position relied on (paraphrase):** estimate m as the data mean,
  `m = (Σ f x) ÷ (Σ f)`; the expected frequency of x occurrences over N
  repetitions is `N × e^(−m) m^x ÷ x!`, and the recurrence builds the table from
  the x = 0 figure.
- **Used in:** notes §7; q-f3c16-026, q-f3c16-028; worked example 7.
- **Spot-checked by:** _(blank until a human checks)_

## F. The normal distribution — properties and the standard normal variable

- **Position relied on (paraphrase):** the normal is the continuous, symmetric,
  bell-shaped curve with parameters μ and σ and probability density
  `f(x) = 1 ÷ (σ √(2π)) × e^(−(x − μ)² ÷ (2σ²))`. Its **mean, median and mode
  coincide** at μ; its **total area is 1** with 0.5 on each side; it is asymptotic
  to the axis; its **points of inflexion are at μ ± σ**; its skewness is 0 and
  kurtosis 3. The **mean deviation is ≈ 0.7979σ**, the **quartile deviation is
  ≈ 0.6745σ**, and QD : MD : SD ≈ 10 : 12 : 15. The **standard normal variable**
  is `z = (x − μ) ÷ σ`, with mean 0 and standard deviation 1, and the raw value is
  recovered by `x = μ + z σ`.
- **Used in:** notes §8, §9; q-f3c16-029 to q-f3c16-032, q-f3c16-040, q-f3c16-041;
  worked example 8. The verifier computes every z-score and raw value exactly from
  the stem.
- **Spot-checked by:** _(blank until a human checks)_

## G. Areas under the normal curve — the standard z-values and the empirical rule

- **Position relied on (paraphrase):** area under the normal curve is probability.
  The chapter relies on a fixed, small set of standard areas measured from the
  mean (z = 0) out to z, and no other table value is used:

  | z | area(0 to z) |
  |---|---|
  | 1.00 | 0.3413 |
  | 1.96 | 0.4750 |
  | 2.00 | 0.4772 |
  | 2.58 | 0.4950 |
  | 3.00 | 0.4987 |

  One-sided and two-sided areas follow by adding or subtracting, using total area
  1 and half-area 0.5. The **empirical (68-95-99.7) rule** states that about
  **68.27%** of values lie within μ ± 1σ (2 × 0.3413 = 0.6826), about **95.45%**
  within μ ± 2σ (2 × 0.4772 = 0.9544), and about **99.73%** within μ ± 3σ
  (2 × 0.4987 = 0.9974). The **central 95%** is μ ± 1.96σ (each tail 2.5%) and the
  **central 99%** is μ ± 2.58σ (each tail 0.5%).
- **Reproducibility note for the reviewer:** every normal-area question in the bank
  either states the area value it needs inside the stem or uses only the standard
  z-values above, so the verifier reproduces each figure **without consulting an
  external z-table**. `AREA_0_TO` in the verifier holds exactly the five values
  tabulated here.
- **Used in:** notes §10; q-f3c16-033 to q-f3c16-039, q-f3c16-042, q-f3c16-043,
  q-f3c16-048, q-f3c16-050; worked examples 8, 9.
- **Spot-checked by:** _(blank until a human checks)_

## H. Choosing between the three distributions and their limiting links

- **Position relied on (paraphrase):** the binomial fits a fixed number of
  independent trials with constant p; the Poisson fits rare events over an interval
  with only a mean rate; the normal fits a continuous measurement clustering around
  a mean. The **Poisson is the limit of the binomial** for large n and small p
  (m = n p), and the **normal is the limit of the binomial** for large n and
  moderate p (μ = n p, σ = √(n p q)).
- **Used in:** notes §11; q-f3c16-044, q-f3c16-045; worked example 10.
- **Spot-checked by:** _(blank until a human checks)_

---

# Reviewer's checklist of conventions

**These matter more here than the formulas.** Every item below is a choice, not a
fact. A different choice does not merely change the wording — it moves a computed
figure and therefore **changes answer keys**. Please confirm each against the ICAI
SM (May 2026 ed.) and initial it.

1. **The value of e.** The notes use e = 2.71828 with e^(−1) = 0.3679,
   e^(−2) = 0.1353, e^(−3) = 0.0498, e^(−1.5) = 0.2231, e^(−4) = 0.0183,
   e^(−5) = 0.006738, e^(−0.5) = 0.6065. Each Poisson question that needs an
   exponential **states the value in the stem**, and the verifier recomputes with
   full-precision `math.exp` under a tolerance, so the printed value and the exact
   answer cannot drift apart unnoticed.

2. **Standard z-areas.** Only the five areas in section G are used
   (0.3413, 0.4750, 0.4772, 0.4950, 0.4987). Every normal question either quotes
   the area it needs in the stem or restricts itself to z = 1, 1.96, 2, 2.58 or 3.
   If the SM's table rounds differently (some quote 0.4750 as 0.4750 but 2.58 as
   2.575), confirm the values; the option gaps in this bank are wide enough to
   survive a last-digit change, but the displayed working would differ.

3. **The 68-95-99.7 convention.** Within-band percentages are taken as
   2 × the one-sided area: μ ± 1σ = 68.26% (2 × 0.3413), μ ± 2σ = 95.44%
   (2 × 0.4772), μ ± 3σ = 99.74% (2 × 0.4987). These are quoted in the notes as the
   familiar 68.27 / 95.45 / 99.73; the tiny last-digit differences come from
   rounding the half-areas and never affect an answer key, because the numerical
   questions (q-f3c16-033, q-f3c16-034, q-f3c16-043) use the doubled table value,
   which is stated in the stem.

4. **Central 95% and 99% markers.** z = 1.96 gives the central 95% (2.5% per tail)
   and z = 2.58 gives the central 99% (0.5% per tail). Both are used as exact
   markers (q-f3c16-038, q-f3c16-039, q-f3c16-042, q-f3c16-050). If the SM uses
   z = 2.576 or 2.575 for 99%, the limit in q-f3c16-039 shifts by a few tenths;
   the option gap (251.6 versus 258) absorbs it, but confirm the value.

5. **z-score denominator.** Every z-score divides by the **standard deviation**,
   never the variance (q-f3c16-031, q-f3c16-041). Where a question gives a
   variance, its square root is taken first. Several distractors are built from the
   failure to do so, which is a real student error.

6. **Mode of a discrete distribution.** The mode is the **integer part** of
   (n + 1)p for the binomial and of m for the Poisson when that quantity is not a
   whole number; when it is a whole number there are two modes (q-f3c16-012,
   q-f3c16-024). Confirm the SM does not instead round to nearest.

7. **Binomial variance is below the mean; Poisson mean equals variance.** These two
   contrasts are load-bearing (q-f3c16-015, q-f3c16-020) and are used as free
   eliminations in the negative-marking section. They follow from the formulas and
   are not conventions, but a reviewer should still confirm the SM states them.

8. **Rounding of the displayed answer.** Probabilities are quoted to **four decimal
   places** and percentages to **two**. Expected frequencies (q-f3c16-026) are left
   unrounded to two decimals (73.58) rather than rounded to a whole number of
   observations, matching the way fitted frequencies are usually shown before the
   final tidy-up.

9. **Scaling the Poisson mean to the interval.** Where a rate is per unit interval,
   m must be scaled to the interval the question asks about. No bank question hides
   a scaling step, but the notes flag it because it is a common examiner trap.

10. **The growing/continuous cases are out of scope.** This chapter keeps to the
    binomial, Poisson and normal only. No negative binomial, geometric,
    hypergeometric, exponential or other distribution is introduced or tested.
    Confirm the Foundation SM's Ch 16 goes no further.

**Machine verification already done (do not repeat it).** All **39** numerical
questions in this bank are recomputed from their stems by
`scripts/verify_numerical/verify_theoretical-distributions.py`, which computes
binomial probabilities exactly with `math.comb` and `fractions.Fraction`, Poisson
probabilities with `math.exp` under a tolerance, z-scores and raw values exactly,
and normal areas only from the five standard values it holds in `AREA_0_TO`
(each also stated in the relevant stem). Every computed value is mapped to an
option **by value, never by the key**. The runner reports 0 failures. Your time is
better spent on the ten conventions above.

**Spot-checked by:** _(blank until a human checks)_
