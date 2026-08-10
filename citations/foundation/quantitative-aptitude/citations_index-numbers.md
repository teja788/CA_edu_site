# Citations — Foundation P3 Ch 18 · Index Numbers

Generated 11 Aug 2026 in the same session as the chapter content. This chapter
rests on the **ICAI Foundation Study Material, Paper 3, Chapter 18 (Index
Numbers)**, read for scope and for the formula set it teaches, and on the
standard statements of those formulas as they appear in any elementary
statistics text. The Study Material is ICAI-copyrighted, so it is used
`reference_only`: every position below is **paraphrased and cited by chapter
subject only, never reproduced**, no ICAI question text or worked answer is
copied, and all numbers, names and scenarios in the notes and in the bank are
fresh.

**No bare Act exists for this chapter.** Nothing here states a legal position:
the content is arithmetic, and it is true whatever the law says. That is why the
notes frontmatter carries `applicable_attempts` but deliberately **omits
`law_as_on_date`** — there is no legal cut-off to pin, and an empty or invented
date would be worse than no date. The bank's questions likewise carry
`applicableAttempts` and `lastVerified` but no `lawAsOnDate`.

What a reviewer must actually check here is therefore different from a law
chapter. The formulas are not in doubt; the **conventions** are — which sum sits
on top, whether the reversal tests strip the ×100, how many decimals an index
carries. Sections A to K record each formula as it is conventionally stated and
where it is used. The **Reviewer's checklist of conventions** at the end records
every rounding and convention choice made in this chapter, because a single
different choice silently changes answer keys.

---

## A. Definition, uses and the base period

- **Position relied on (paraphrase):** an index number is a ratio, expressed as a
  percentage, that measures the relative change in a variable or a group of
  variables between a current period (subscript 1) and a base period (subscript
  0), the base being fixed at 100. It is a pure number, free of units, and it
  summarises the net change in a group. Index numbers act as economic barometers
  and are used for the cost of living / consumer price index, the wholesale price
  index, deflating money figures and the index of industrial production. A
  fixed-base series compares every year with one base year; a chain-base series
  compares each year with the preceding one.
- **Source:** ICAI Foundation SM Paper 3, Ch 18 (Index Numbers), May 2026
  edition — reference_only; standard elementary statements of the same
  definitions.
- **Used in:** notes §1; q-f3c18-001, q-f3c18-002, q-f3c18-049, q-f3c18-050.
- **Spot-checked by:** _(blank until a human checks)_

## B. Price relatives

- **Position relied on (paraphrase):** a price relative measures the change in a
  single commodity's price as the current price expressed as a percentage of the
  base price, `(p₁ ÷ p₀) × 100`. Quantity and value relatives are defined the
  same way for quantities and for total money values.
- **Formula:** `Price relative = (p₁ ÷ p₀) × 100`.
- **Used in:** notes §2; q-f3c18-003, q-f3c18-004, q-f3c18-044.
- **Spot-checked by:** _(blank until a human checks)_

## C. Unweighted aggregate indices

- **Position relied on (paraphrase):** the simple aggregate price index is
  `(Σp₁ ÷ Σp₀) × 100`; it is distorted by the units in which prices are quoted
  and gives every commodity equal importance. The simple average of price
  relatives, `Σ(p₁ ÷ p₀ × 100) ÷ N`, cures the units defect but not the weighting
  defect.
- **Formulas:** `Simple aggregate = (Σp₁ ÷ Σp₀) × 100`;
  `Simple average of relatives = Σ(p₁ ÷ p₀ × 100) ÷ N`.
- **Used in:** notes §3, §4; q-f3c18-005, q-f3c18-006, q-f3c18-007, q-f3c18-042,
  q-f3c18-043; worked example 1.
- **Spot-checked by:** _(blank until a human checks)_

## D. Laspeyres and Paasche price indices

- **Position relied on (paraphrase):** the Laspeyres price index weights current
  prices by base-year quantities, `(Σp₁q₀ ÷ Σp₀q₀) × 100`, and tends to overstate
  the rise in the cost of living. The Paasche price index weights by current-year
  quantities, `(Σp₁q₁ ÷ Σp₀q₁) × 100`, and tends to understate it. In both the
  price is current over base; only the quantity weight changes.
- **Formulas:** `Laspeyres = (Σp₁q₀ ÷ Σp₀q₀) × 100`;
  `Paasche = (Σp₁q₁ ÷ Σp₀q₁) × 100`.
- **Used in:** notes §6, §7; q-f3c18-008, q-f3c18-009, q-f3c18-011, q-f3c18-012,
  q-f3c18-016, q-f3c18-017; worked example 2.
- **Spot-checked by:** _(blank until a human checks)_

## E. Fisher's ideal index

- **Position relied on (paraphrase):** Fisher's ideal index is the geometric mean
  of the Laspeyres and Paasche indices, `square root of (Laspeyres × Paasche)`.
  It lies between the two, balancing the upward Laspeyres bias against the
  downward Paasche bias, and it is the only one of the standard weighted indices
  to satisfy both the time-reversal and factor-reversal tests — hence "ideal". It
  is the geometric mean, not the arithmetic mean.
- **Formula:** `Fisher = square root of [(Σp₁q₀ ÷ Σp₀q₀) × (Σp₁q₁ ÷ Σp₀q₁)] × 100`.
- **Verifier note:** Fisher is irrational in general, so the verifier computes it
  with `math.sqrt` on the exact Laspeyres and Paasche fractions and matches the
  option within a tolerance, while every rational index is carried as an exact
  `fractions.Fraction`.
- **Used in:** notes §8; q-f3c18-010, q-f3c18-015, q-f3c18-018, q-f3c18-037;
  worked example 2.
- **Spot-checked by:** _(blank until a human checks)_

## F. Marshall-Edgeworth and Dorbish-Bowley indices

- **Position relied on (paraphrase):** the Marshall-Edgeworth index weights each
  price by the sum of the base and current quantities,
  `[(Σp₁q₀ + Σp₁q₁) ÷ (Σp₀q₀ + Σp₀q₁)] × 100`, and closely approximates Fisher.
  The Dorbish-Bowley index (also written Drobish-Bowley) is the arithmetic mean
  of Laspeyres and Paasche, `(Laspeyres + Paasche) ÷ 2`. Both use base and
  current weights, and both sit between Laspeyres and Paasche alongside Fisher.
- **Formulas:** `Marshall-Edgeworth = [(Σp₁q₀ + Σp₁q₁) ÷ (Σp₀q₀ + Σp₀q₁)] × 100`;
  `Dorbish-Bowley = (Laspeyres + Paasche) ÷ 2`.
- **Used in:** notes §9; q-f3c18-013, q-f3c18-014, q-f3c18-045, q-f3c18-046;
  worked example 3.
- **Spot-checked by:** _(blank until a human checks)_

## G. The time-reversal and factor-reversal tests

- **Position relied on (paraphrase):** the **time-reversal test** requires that
  reversing the two periods inverts the index, so `P₀₁ × P₁₀ = 1` with the
  indices taken as ratios (the ×100 stripped). The **factor-reversal test**
  requires that the price index times the matching quantity index equals the
  value ratio, `P₀₁ × Q₀₁ = Σp₁q₁ ÷ Σp₀q₀`, again as ratios. Laspeyres and Paasche
  fail both; **Fisher passes both**, which is exactly why it is the ideal index.
  The **circular test** (`P₀₁ × P₁₂ × P₂₀ = 1`) is passed by the simple aggregate
  and by fixed-weight indices but not by Fisher.
- **Formulas relied on:** `Time-reversal: P₀₁ × P₁₀ = 1`;
  `Factor-reversal: P₀₁ × Q₀₁ = Σp₁q₁ ÷ Σp₀q₀`.
- **Verifier note:** for the two reversal-test questions the verifier builds
  Fisher's price and quantity indices from the stem's own sums, multiplies the
  reversed pair, and asserts the identity holds to within 1e-9 before mapping the
  value ratio to an option — so the "Fisher passes" claim is machine-proved from
  the data, not assumed.
- **Used in:** notes §10; q-f3c18-019, q-f3c18-020, q-f3c18-021, q-f3c18-022,
  q-f3c18-023; worked examples 4 and 5.
- **Spot-checked by:** _(blank until a human checks)_

## H. Quantity and value index numbers

- **Position relied on (paraphrase):** a quantity index swaps the roles of price
  and quantity, so the Laspeyres quantity index is `(Σq₁p₀ ÷ Σq₀p₀) × 100` and the
  Fisher quantity index is the geometric mean of the Laspeyres and Paasche
  quantity indices. A value index needs no weights, being
  `(Σp₁q₁ ÷ Σp₀q₀) × 100`, and equals the product of the Fisher price and Fisher
  quantity indices as ratios (the factor-reversal test read forwards).
- **Formulas:** `Laspeyres quantity = (Σq₁p₀ ÷ Σq₀p₀) × 100`;
  `Fisher quantity = square root of (Laspeyres q × Paasche q)`;
  `Value index = (Σp₁q₁ ÷ Σp₀q₀) × 100`.
- **Used in:** notes §11; q-f3c18-024, q-f3c18-025, q-f3c18-038, q-f3c18-039,
  q-f3c18-047.
- **Spot-checked by:** _(blank until a human checks)_

## I. Cost of living / consumer price index

- **Position relied on (paraphrase):** the cost of living index measures the
  change in the cost of a fixed basket bought by a defined group of consumers,
  computed by either the **aggregate expenditure method**,
  `(Σp₁q₀ ÷ Σp₀q₀) × 100` (identical to Laspeyres), or the **family budget
  method**, `Σ(RW) ÷ ΣW`, where `R = (p₁ ÷ p₀) × 100` is the price relative and
  `W = p₀q₀` is the value weight. The two methods are algebraically identical,
  because `R × W = 100 × p₁q₀`, so they always give the same answer.
- **Formulas:** `Aggregate expenditure = (Σp₁q₀ ÷ Σp₀q₀) × 100`;
  `Family budget = Σ(RW) ÷ ΣW`.
- **Used in:** notes §12; q-f3c18-026, q-f3c18-027, q-f3c18-028, q-f3c18-048;
  worked examples 6 and 7.
- **Spot-checked by:** _(blank until a human checks)_

## J. Deflating, real wage and purchasing power

- **Position relied on (paraphrase):** deflating removes the price effect from a
  money figure, so the real wage is `(Money wage ÷ cost of living index) × 100`,
  always below the money wage once the index exceeds 100. The purchasing power of
  the rupee is the reciprocal of the index restored to a rupee,
  `100 ÷ cost of living index`.
- **Formulas:** `Real wage = (Money wage ÷ CLI) × 100`;
  `Purchasing power of the rupee = 100 ÷ CLI`.
- **Used in:** notes §13; q-f3c18-029, q-f3c18-030, q-f3c18-031, q-f3c18-032,
  q-f3c18-040, q-f3c18-041; worked example 8.
- **Spot-checked by:** _(blank until a human checks)_

## K. Base shifting and splicing

- **Position relied on (paraphrase):** base shifting re-expresses a single series
  on a new, more recent base without collecting new data, dividing every figure
  by the old index of the chosen new base year and multiplying by 100. Splicing
  joins two overlapping series computed on different bases into one continuous
  series by rescaling the new series through the overlap-year value of the old
  series.
- **Formulas:** `Base shifting: new index = (old index of the year ÷ old index of
  the new base year) × 100`; `Splicing: new index × (old overlap value ÷ 100)`.
- **Used in:** notes §14, §15; q-f3c18-033, q-f3c18-034, q-f3c18-035,
  q-f3c18-036; worked example 9.
- **Spot-checked by:** _(blank until a human checks)_

---

# Reviewer's checklist of conventions

**These matter more here than anywhere else in the paper.** Every item below is a
choice, not a fact. A different choice does not merely change the wording — it
moves a computed figure and therefore **changes answer keys**. Please confirm
each against the ICAI SM (May 2026 ed.) and initial it.

1. **Which sum sits on top.** Every price index has current prices over base
   prices; only the quantity weight changes — q₀ for Laspeyres, q₁ for Paasche,
   (q₀ + q₁) for Marshall-Edgeworth. Confirm the SM writes the ratios the same
   way; swapping numerator and denominator inverts every key.

2. **Fisher is the geometric mean.** Fisher = square root of (Laspeyres ×
   Paasche), never the arithmetic mean (that is Dorbish-Bowley). The two land
   very close in these datasets, so the distractors deliberately keep the
   arithmetic mean off the Fisher questions and vice versa.

3. **The reversal tests strip the ×100.** Time-reversal (P₀₁ × P₁₀ = 1) and
   factor-reversal (P₀₁ × Q₀₁ = value ratio) use the indices as ratios, so 132.99
   enters as 1.3299. If the SM keeps the hundreds, the printed test values change
   though the pass/fail conclusion does not.

4. **Decimal places in an index.** Every index is quoted to **two decimal
   places**, rounded half-up at the final step. Exact (rational) indices are
   carried as fractions and rounded once; Fisher and the reversal-test products
   are matched within a small tolerance. If the SM rounds to whole numbers or one
   decimal, several close options (e.g. Fisher 149.04 against Dorbish-Bowley
   149.05) would need re-spacing.

5. **The two cost-of-living methods agree.** The aggregate expenditure method is
   the Laspeyres formula and the family budget method is Σ(RW) ÷ ΣW with W = p₀q₀;
   they are identical because R × W = 100 × p₁q₀. Confirm the SM uses value
   weights (p₀q₀), not quantity weights, in the family budget method — worked
   example 6 turns on this identity.

6. **Family budget weights are values, relatives are percentages.** In q-f3c18-027
   and q-f3c18-048 the group "index" R is a price relative (a percentage) and W is
   its weight; the answer is Σ(RW) ÷ ΣW. Where the weights total 100 the divisor
   is 100. Confirm the SM's family-budget illustrations weight relatives by value,
   not prices by quantity.

7. **Deflating divides by the index.** Real wage = money wage ÷ index × 100, and
   the purchasing power of the rupee is 100 ÷ index. The real wage is always below
   the money wage once the index exceeds 100 — a free elimination the distractors
   exploit.

8. **Base shifting divides by the new base year's old figure.** The whole series
   is divided by the old index of the year chosen to read 100, not by the first
   year of the series (q-f3c18-033). Splicing multiplies the new series by the old
   overlap value ÷ 100 to carry it onto the old base (q-f3c18-034); the reverse
   direction uses the reciprocal.

9. **Spelling of Dorbish-Bowley.** The index is written **Dorbish-Bowley** here,
   and is also seen as Drobish-Bowley. Confirm the SM's spelling so the option and
   note text match the paper the students will sit.

10. **A Fisher index lies between Laspeyres and Paasche.** Every Fisher answer in
    this bank has been checked to sit strictly between the matching Laspeyres and
    Paasche figures. If a reviewer finds one that does not, a column-sum is wrong.

**Machine verification already done (do not repeat it).** All **37** numerical
questions in this bank are recomputed from their stems by
`scripts/verify_numerical/verify_index-numbers.py`, which carries the four
building-block sums (Σp₀q₀, Σp₁q₀, Σp₀q₁, Σp₁q₁) as exact `fractions.Fraction`,
computes Fisher and the reversal tests with `math.sqrt`, proves the
factor-reversal identity to within 1e-9 from the data, and maps each computed
value to an option by value rather than by the bank's key. The runner reports 0
failures. Your time is better spent on the ten conventions above.

**Spot-checked by:** _(blank until a human checks)_
