# Citations — Foundation P3 Ch 13 · Statistical Description of Data and Sampling

Generated 11 Aug 2026 in the same session as the chapter content. This chapter
rests on the **ICAI Foundation Study Material, Paper 3, Chapter 13 (Statistical
Description of Data)**, read for scope and for the definitions and conventions it
teaches, and on the standard statements of those definitions as they appear in
any elementary statistics text. The Study Material is ICAI-copyrighted, so it is
used `reference_only`: every position below is **paraphrased and cited by chapter
subject only, never reproduced**, no ICAI question text or worked answer is
copied, and all numbers, names and scenarios in the notes and in the bank are
fresh.

**No bare Act exists for this chapter.** Nothing here states a legal position:
the content is definitional and arithmetical, and it is true whatever the law
says. That is why the notes frontmatter carries `applicable_attempts` but
deliberately **omits `law_as_on_date`** — there is no legal cut-off to pin, and
an empty or invented date would be worse than no date. The bank's questions
likewise carry `applicableAttempts` and `lastVerified` but no `lawAsOnDate`.

What a reviewer must actually check here is therefore different from a law
chapter. The definitions are not in doubt; the **conventions** are — the
class-boundary adjustment, the rounding of Sturges' rule, and the ogive-median
method each rest on a choice that silently sets answer keys. Sections A to K
record each definition and formula as it is conventionally stated and where it is
used. The **Reviewer's checklist of conventions** at the end records every
convention choice made in this chapter.

---

## A. The meaning of statistics, variables and attributes

- **Position relied on (paraphrase):** in the singular, statistics is the science
  of collecting, organising, presenting, analysing and interpreting numerical
  data; in the plural, the numerical facts themselves. Statistics deals with
  aggregates, not single items. A **variable** is a measurable characteristic,
  **discrete** if it takes only separate countable values and **continuous** if it
  may take any value in a range; an **attribute** is a non-numerical characteristic
  that is counted, not measured.
- **Source:** ICAI Foundation SM Paper 3, Ch 13 (Statistical Description of Data),
  May 2026 edition — reference_only; standard elementary statistics definitions.
- **Used in:** notes §1; q-f3c13-001, q-f3c13-002.
- **Spot-checked by:** _(blank until a human checks)_

## B. Primary and secondary data

- **Position relied on (paraphrase):** primary data are collected first-hand by
  the investigator for the enquiry in hand; secondary data are data already
  collected by someone else for another purpose and reused. The single test is the
  collector's relation to the enquiry, so the same figures are primary to the body
  that first collected them and secondary to a later user.
- **Used in:** notes §2; q-f3c13-003; worked example (none — definitional).
- **Spot-checked by:** _(blank until a human checks)_

## C. The four scales of measurement

- **Position relied on (paraphrase):** measurement scales climb through four
  levels — **nominal** (labels only), **ordinal** (rank but unequal gaps),
  **interval** (equal, meaningful gaps but no true zero) and **ratio** (equal gaps
  and a true, absolute zero) — each level permitting one more arithmetic
  operation than the one below. Ratios are meaningful only on a ratio scale.
- **Standard convention relied on:** temperature in degrees Celsius is the
  textbook example of an **interval** scale, because its zero is a convention and
  not an absence of heat, so 40 °C is not twice 20 °C. Temperature in Kelvin,
  whose zero is absolute, is a ratio scale.
- **Used in:** notes §3; q-f3c13-004 to q-f3c13-008; worked example 1.
- **Spot-checked by:** _(blank until a human checks)_

## D. Census, sample and the sampling frame

- **Position relied on (paraphrase):** a **census** examines every unit of the
  population and carries no sampling error but is costly, slow and impossible where
  testing is destructive; a **sample survey** examines a representative part and
  infers the whole, being cheaper, faster and often more accurate in practice.
  Good sampling is random, so that every unit has a known non-zero chance of
  selection and the reliability of the result can be measured.
- **Used in:** notes §4; q-f3c13-009, q-f3c13-010.
- **Spot-checked by:** _(blank until a human checks)_

## E. Methods of random sampling

- **Position relied on (paraphrase):** the examinable random methods are
  **simple random** (every unit an equal chance), **systematic** (a random start
  then every k-th unit, with interval `k = N ÷ n`), **stratified** (sample within
  internally-similar strata; under proportional allocation, units from a stratum =
  `(stratum size ÷ N) × sample size`), **cluster** (choose some internally-varied
  clusters and study each completely) and **multistage** (sampling in successive
  nested stages).
- **Formulas:** systematic interval `k = N ÷ n`; proportional allocation
  `n_h = (N_h ÷ N) × n`.
- **Reviewer note:** stratified and cluster sampling are the pair most often
  confused; the notes and q-f3c13-013 turn on the distinction (sample *every*
  group versus fully study *some* groups).
- **Used in:** notes §4; q-f3c13-011 to q-f3c13-014; worked example 2. The verifier
  computes the systematic interval and the proportional allocation from the stem's
  own figures and asserts the strata add back to the whole sample.
- **Spot-checked by:** _(blank until a human checks)_

## F. Sampling and non-sampling error

- **Position relied on (paraphrase):** **sampling error** arises because only a
  part of the population is studied; it is present only in sample surveys, falls as
  the sample grows and can be estimated from the sample. **Non-sampling error**
  arises from faults in measurement and processing; it is present in both censuses
  and samples and can be larger in a census because of its scale. A census
  therefore has no sampling error but is not free of all error.
- **Used in:** notes §5; q-f3c13-015, q-f3c13-016.
- **Spot-checked by:** _(blank until a human checks)_

## G. Classification and tabulation

- **Position relied on (paraphrase):** classification is the sorting of data into
  homogeneous groups on a chronological, geographical, qualitative or quantitative
  basis; tabulation is the orderly presentation of classified data in rows and
  columns with a title, stub, caption, body and, where needed, notes.
  Classification precedes tabulation, and a quantitative classification presented
  as a table is a frequency distribution.
- **Used in:** notes §6.
- **Spot-checked by:** _(blank until a human checks)_

## H. Frequency distributions and the number of classes (Sturges' rule)

- **Position relied on (paraphrase):** a frequency distribution pairs the values
  (discrete) or class intervals (continuous) of a variable with their frequencies.
  The number of classes for a grouped distribution is guided by **Sturges' rule**,
  `k = 1 + 3.322 log₁₀ N`, the result being **rounded to a whole number**; the
  class width then follows as `Range ÷ number of classes`, with `Range = largest −
  smallest`.
- **Standard convention relied on:** Sturges' rule is a guide, and the width is
  computed from the **rounded** number of classes and usually rounded up to a
  convenient figure. For N = 100, `k = 1 + 3.322 × 2 = 7.644`, taken as 8 classes.
- **Used in:** notes §7; q-f3c13-021, q-f3c13-022, q-f3c13-023, q-f3c13-046;
  worked example 4. The verifier rounds Sturges' `k` half-up to a whole number and
  divides the range by that rounded `k`.
- **Spot-checked by:** _(blank until a human checks)_

## I. Class limits, class boundaries, width and mid-value

- **Position relied on (paraphrase):** an **inclusive** (discontinuous)
  distribution states limits both of which belong to the class (20–29); its true
  **class boundaries** close the gap to the next class by half of it, so
  `lower boundary = lower limit − ½(gap)` and `upper boundary = upper limit +
  ½(gap)`. An **exclusive** distribution's boundaries equal its limits. The
  **class width** is `upper boundary − lower boundary` (equivalently the difference
  between successive lower limits), and the **mid-value** is `(lower limit + upper
  limit) ÷ 2`, so successive mid-values differ by the class width. An **open-end**
  class states only one limit.
- **Standard convention relied on:** the half-unit boundary adjustment for a
  one-unit gap (0.5), so the inclusive class 20–29 is 10 units wide, not 9.
- **Used in:** notes §8; q-f3c13-017 to q-f3c13-020, q-f3c13-024, q-f3c13-031,
  q-f3c13-032, q-f3c13-045; worked example 3.
- **Spot-checked by:** _(blank until a human checks)_

## J. Cumulative and relative frequency

- **Position relied on (paraphrase):** a **less-than** cumulative frequency
  against an upper boundary counts observations below that value (rising to N); a
  **more-than** cumulative frequency against a lower boundary counts observations
  at or above it (falling to 0); a single class frequency is the difference of two
  neighbouring cumulative figures. **Relative frequency** is `f ÷ N`, the relative
  frequencies summing to exactly 1, and **percentage frequency** is that times 100;
  the total is recovered as `N = f ÷ relative frequency`.
- **Used in:** notes §9; q-f3c13-025 to q-f3c13-030, q-f3c13-042, q-f3c13-044,
  q-f3c13-047, q-f3c13-048; worked examples 5 and 9. The verifier carries the exact
  relative frequencies in `fractions.Fraction` and asserts the missing relative
  frequency completes the sum to 1.
- **Spot-checked by:** _(blank until a human checks)_

## K. Diagrams and graphs — bar, pie, histogram, polygon and ogive

- **Position relied on (paraphrase):** a **bar chart** shows category sizes by bar
  length with gaps between bars; a **pie chart** cuts a circle into sectors whose
  angles are proportional to the components, `angle = (component ÷ total) × 360°`,
  so 1% of the total is 3.6°. A **histogram** is a set of adjacent rectangles on
  the class boundaries in which **area** represents frequency; where class widths
  differ, the height plotted is the **frequency density**, `frequency ÷ class
  width`. A **frequency polygon** joins the `(mid-value, frequency)` points. An
  **ogive** plots cumulative frequency against class boundaries — the less-than
  ogive rising to N, the more-than ogive falling — and the **median** is read at
  the cumulative position `N ÷ 2`, interpolated inside the median class as
  `Median = L + [(N ÷ 2 − cf) ÷ f] × h`.
- **Standard convention relied on:** the ogive-median method uses `N ÷ 2` (not
  `(N + 1) ÷ 2`) as the median position for grouped continuous data, and the two
  ogives cross at the median.
- **Used in:** notes §10, §11; q-f3c13-033 to q-f3c13-041, q-f3c13-043,
  q-f3c13-049; worked examples 6, 7 and 8. The verifier computes each pie angle and
  share as an exact fraction of 360° (asserting the 1% = 3.6° bridge) and locates
  the median class from the cumulative frequencies before interpolating.
- **Spot-checked by:** _(blank until a human checks)_

---

# Reviewer's checklist of conventions

**These matter more here than the definitions themselves.** Every item below is a
choice, not a fact. A different choice does not merely change the wording — it
moves a computed figure and therefore **changes answer keys**. Please confirm each
against the ICAI SM (May 2026 ed.) and initial it.

1. **Class-boundary adjustment.** For inclusive classes with a one-unit gap, each
   boundary is shifted by **0.5** (half the gap), so 20–29 has boundaries 19.5 to
   29.5 and a true width of 10, not 9 (q-f3c13-019, q-f3c13-020, q-f3c13-031). If
   the SM works with a different gap convention, these keys move.

2. **Sturges' rule is rounded to a whole number.** `k = 1 + 3.322 log₁₀ N` is
   rounded half-up to a whole number of classes, and the class width is
   `range ÷ (rounded k)`, not `range ÷ (raw k)` (q-f3c13-021, q-f3c13-022). For
   N = 100 this gives 8 classes and, on a range of 80, a width of 10. If the SM
   rounds up rather than to nearest, N-values near a half-integer could change `k`.

3. **Range definition.** `Range = largest − smallest` (q-f3c13-046), with no
   +1 adjustment. Confirm the SM does not add one unit for inclusive data.

4. **Relative frequencies sum to exactly 1.** The missing relative frequency is
   found by subtraction and N is recovered as `f ÷ relative frequency`
   (q-f3c13-030, q-f3c13-044). This is an identity, not a rounding choice.

5. **Cumulative frequency directions.** "Less than" cumulates upward to N against
   the upper boundary; "more than" cumulates downward against the lower boundary
   (q-f3c13-027, q-f3c13-028, q-f3c13-042). A single class frequency is the
   difference of two neighbouring cumulative figures (q-f3c13-029, q-f3c13-047).

6. **Pie-chart conversions.** `angle = (component ÷ total) × 360°`, `1% = 3.6°`,
   and the sector angles sum to 360° (q-f3c13-033 to q-f3c13-035, q-f3c13-043,
   q-f3c13-049). Amounts are exact fractions of the total; no rounding is applied.

7. **Frequency density for unequal classes.** A histogram with unequal widths
   plots `frequency ÷ class width` so that area carries the frequency
   (q-f3c13-037). Confirm the SM draws unequal-width histograms this way rather
   than by raw frequency.

8. **Ogive-median position.** The median is read at `N ÷ 2` on the cumulative
   axis and interpolated as `L + [(N ÷ 2 − cf) ÷ f] × h` (q-f3c13-039,
   q-f3c13-040). This chapter uses `N ÷ 2`, the standard grouped-data convention,
   not `(N + 1) ÷ 2`. If the SM's ogive illustrations use a different position,
   q-f3c13-039 and q-f3c13-040 move.

9. **Scale of Celsius temperature.** Treated as an **interval** scale because its
   zero is a convention (q-f3c13-006). Confirm the SM classifies it the same way;
   it is the single most-tested scale example.

10. **Exam-technique arithmetic.** The expected value of a blind guess under 0.25
    negative marking is `(1/4)(+1) + (3/4)(−0.25) = 0.0625` (q-f3c13-050). This is
    a property of the marking scheme, stated in the SM's exam guidance, not a
    statistical convention.

**Machine verification already done (do not repeat it).** All **32** numerical
questions in this bank are recomputed from their stems by
`scripts/verify_numerical/verify_statistical-description-of-data.py`, which carries
exact rationals in `fractions.Fraction`, rounds Sturges' `k` half-up, locates the
median class from the cumulative frequencies before interpolating, and maps each
computed value to an option **by value** (never by the bank's key). The runner
reports 0 failures. Your time is better spent on the ten conventions above.

**Spot-checked by:** _(blank until a human checks)_
