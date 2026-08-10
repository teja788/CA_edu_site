# Citations — Foundation P3 Ch 7 · Sets, Relations and Functions; Basics of Limits and Continuity

Generated 10 Aug 2026 in the same session as the chapter content.

**There is no bare Act behind this chapter.** Mathematics has no statutory
source, so nothing here can be checked against India Code the way a Business
Laws chapter can. What this file records instead is (i) the **ICAI Study
Material scope** the chapter was written to, (ii) every **standard result** of
set theory and elementary analysis relied on, stated in its conventional form so
a reviewer can check the statement rather than hunt for a source, and (iii) the
**editorial conventions** chosen at points where textbook practice genuinely
varies. Section (iii) is the reviewer's real checklist, and several of those
calls silently change answer keys.

**Note on `law_as_on_date`.** The chapter's frontmatter deliberately **omits**
`law_as_on_date`. That field pins content to a cut-off date for a legal or
fiscal position, and this chapter states none — the cardinality of a power set
does not change with a Finance Act. `applicable_attempts` is present, because
the SM edition and the examinable scope can change between attempts.

The ICAI Study Material was used `reference_only` — read to confirm that the
scope and the level of treatment match, and cited by chapter number only. No SM
prose, no SM worked example and no SM question wording was reproduced. Every
number, scenario and name in the chapter and the bank is original.

A reviewer spot-checking this file should confirm each entry against **ICAI
Foundation SM Paper 3, Ch 7 (Sets, Relations and Functions; Basics of Limits and
Continuity), May 2026 edition** and initial the "Spot-checked by" line.

## Scope relied on

- **Position relied on (paraphrase, not quoted):** the chapter covers sets in
  roster and set-builder form; the empty, singleton, finite, infinite, equal,
  equivalent and universal sets; subsets, proper subsets and the power set with
  their counts; union, intersection, difference, symmetric difference and
  complement together with the laws of set algebra including De Morgan; Venn
  diagrams and the cardinality results for two and three sets, including the
  exactly-one, exactly-two and at-least variants; ordered pairs and the
  Cartesian product; relations with their domain, range and codomain, the count
  of relations on a finite set, the reflexive, symmetric, transitive,
  anti-symmetric and equivalence properties, and the inverse relation; functions,
  their domain, codomain and range, one-one, onto and bijective functions and
  their counts, composite and inverse functions, and even and odd functions;
  limits, one-sided limits and the condition for a limit to exist, evaluation by
  substitution, factorisation and rationalisation, the standard limits and the
  indeterminate form 0/0; and continuity at a point tested by the three-part
  definition, including piecewise functions and solving for a constant.
- **Source:** ICAI Foundation SM Paper 3, Ch 7, May 2026 edition —
  reference_only.
- **Used in:** the whole chapter; the section numbering of the notes follows
  this scope order.
- **Spot-checked by:** _(blank until a human checks)_

## Sets, notation and types

- **Results relied on:** a set is a well-defined collection of distinct objects.
  Roster form lists members inside braces, ignoring order and repetition;
  set-builder form states a defining property. n(A) denotes the cardinal number.
  The empty set has no members and is unique; a singleton has exactly one; equal
  sets have identical members; equivalent sets have equal cardinal numbers;
  disjoint sets have empty intersection; the universal set is fixed by the
  question. Equality implies equivalence and not conversely.
- **Source:** elementary set theory, standard; SM Ch 7 introductory treatment —
  reference_only.
- **Used in:** q-f3c7-001 to q-f3c7-005; notes §1 and §2.
- **Spot-checked by:** _(blank until a human checks)_ — see convention 1 below
  on whether 0 belongs to N.

## Subsets, proper subsets and the power set

- **Results relied on, in their conventional statements:** A ⊆ B when every
  element of A is an element of B; A ⊂ B (proper) when A ⊆ B and A ≠ B. Every
  set is a subset of itself and the empty set is a subset of every set. For
  n(A) = n: the number of subsets is 2ⁿ, the number of proper subsets is 2ⁿ − 1,
  and the number of non-empty proper subsets is 2ⁿ − 2. The power set P(A) is
  the set of all subsets of A and n(P(A)) = 2ⁿ; its elements are sets, so
  {x} ∈ P(A) while x ∉ P(A).
- **Source:** standard; SM Ch 7 — reference_only.
- **Used in:** q-f3c7-006 to q-f3c7-010; notes §3 and the one-page summary.
- **Spot-checked by:** _(blank until a human checks)_ — see convention 2 below
  on what a proper subset excludes.

## Set operations and the laws of set algebra

- **Results relied on:** A ∪ B is the set of elements in A or in B or in both;
  A ∩ B those in both; A − B = A ∩ B′ those in A but not in B; A Δ B =
  (A − B) ∪ (B − A) = (A ∪ B) − (A ∩ B) those in exactly one; A′ = U − A. The
  laws are commutative, associative, distributive **in both directions**,
  identity (A ∪ ∅ = A, A ∩ U = A), domination, idempotent, complement,
  absorption, and De Morgan in the form (A ∪ B)′ = A′ ∩ B′ and
  (A ∩ B)′ = A′ ∪ B′. Counting corollaries: n(A − B) = n(A) − n(A ∩ B),
  n(A Δ B) = n(A) + n(B) − 2n(A ∩ B), n(A′) = n(U) − n(A).
- **Source:** standard results of Boolean set algebra; SM Ch 7 —
  reference_only.
- **Used in:** q-f3c7-011 to q-f3c7-014; notes §4, §5 (the law table and the
  De Morgan verification working note) and worked example 4.
- **Spot-checked by:** _(blank until a human checks)_

## Venn diagrams and the inclusion-exclusion principle

- **Results relied on, in their conventional statements:**
  - Two sets: n(A ∪ B) = n(A) + n(B) − n(A ∩ B); the four regions (A only, both,
    B only, neither) partition U and add to n(U).
  - Three sets: n(A ∪ B ∪ C) = n(A) + n(B) + n(C) − n(A ∩ B) − n(B ∩ C) −
    n(A ∩ C) + n(A ∩ B ∩ C); the eight regions partition U.
  - With s = the sum of the three single counts, p = the sum of the three
    pairwise counts and t = the triple count: **at least one = s − p + t**,
    **exactly one = s − 2p + 3t**, **exactly two = p − 3t**, **exactly three =
    t**, **at least two = p − 2t**, and none = n(U) − (s − p + t). The identity
    (exactly one) + (exactly two) + (exactly three) = the union is the standing
    arithmetic check.
- **Source:** the inclusion-exclusion principle in its elementary two-set and
  three-set forms; SM Ch 7 — reference_only.
- **Used in:** q-f3c7-015 to q-f3c7-025, cs-f3c7-01-a to cs-f3c7-01-d; notes §6
  (both region tables), §7, §8, §9 (the band table) and worked examples 2, 3
  and 11.
- **Spot-checked by:** _(blank until a human checks)_ — the **band formulas in
  §9 go slightly beyond the minimum** some editions print. Every one of them is
  reproduced by the region table in §6, so if the SM states only the union
  formula, §9 can be presented as a derived shortcut without any key changing.
  The verifier does not use the band formulas at all: it builds the actual
  population and counts, so the formulas in the notes are checked against
  enumeration rather than assumed.

## Ordered pairs and the Cartesian product

- **Results relied on:** (a, b) = (c, d) if and only if a = c and b = d;
  A × B = {(a, b) : a ∈ A, b ∈ B}; n(A × B) = n(A) × n(B); A × B ≠ B × A unless
  A = B or one of them is empty, though n(A × B) = n(B × A) always; A × ∅ = ∅;
  and the product distributes over ∪, ∩ and − in the second factor.
- **Source:** standard; SM Ch 7 — reference_only.
- **Used in:** q-f3c7-026 to q-f3c7-028; notes §10 and worked example 5.
- **Spot-checked by:** _(blank until a human checks)_

## Relations, their properties, and the counts

- **Results relied on, in their conventional statements:** a relation from A to
  B is any subset of A × B; its domain is the set of first co-ordinates actually
  appearing, its range the set of second co-ordinates actually appearing, and
  its codomain the whole of B as declared. R⁻¹ = {(b, a) : (a, b) ∈ R} always
  exists, and the domain of R⁻¹ is the range of R.
  - **Counts:** relations from an m-set to an n-set = 2^(mn); relations on an
    n-set = 2^(n²); reflexive relations = 2^(n² − n); symmetric relations =
    2^(n(n + 1)/2); reflexive and symmetric together = 2^(n(n − 1)/2).
  - **Properties**, for R on A: reflexive when (a, a) ∈ R for every a ∈ A;
    symmetric when (a, b) ∈ R implies (b, a) ∈ R; transitive when (a, b) ∈ R and
    (b, c) ∈ R imply (a, c) ∈ R; anti-symmetric when (a, b) ∈ R and (b, a) ∈ R
    imply a = b; and an **equivalence relation** when reflexive, symmetric and
    transitive together.
- **Source:** standard; SM Ch 7 — reference_only. The counting results follow
  from the subset count applied to the grid of n² cells.
- **Used in:** q-f3c7-029 to q-f3c7-033, cs-f3c7-02-a, cs-f3c7-02-d; notes §11,
  §12 (the property definitions, the counting table and the empty-relation
  paragraph) and worked example 6.
- **Spot-checked by:** _(blank until a human checks)_ — see convention 3 below
  on the empty relation, which is the single most answer-changing call in this
  chapter. Confirm also that the SM asks for **reflexive and symmetric counts**
  at Foundation depth; if it does not, the §12 counting table can be trimmed to
  its first two rows without touching a key other than q-f3c7-031.

## Functions, their types and the counts

- **Results relied on, in their conventional statements:** f : A → B is a
  relation in which every element of A has exactly one image, so every function
  is a relation and not conversely. Domain = A; codomain = B; range = f(A) ⊆ B.
  f is **one-one (injective)** when f(x₁) = f(x₂) forces x₁ = x₂; **onto
  (surjective)** when the range equals the codomain; **bijective** when both.
  - **Counts** for n(A) = m and n(B) = n: all functions = n^m; one-one functions
    = n(n − 1)…(n − m + 1), which is ⁿPₘ and is 0 when m > n; bijections when
    m = n = n!.
  - Structural conditions: a one-one function needs n(B) ≥ n(A); an onto
    function needs n(B) ≤ n(A); a bijection between finite sets needs
    n(A) = n(B).
  - **Natural domain of a formula:** every real value at which the formula is
    defined — a denominator may not vanish and the quantity under an even root
    may not be negative.
- **Source:** standard; SM Ch 7 — reference_only.
- **Used in:** q-f3c7-034 to q-f3c7-039, cs-f3c7-02-b, cs-f3c7-02-c; notes §13,
  §14 and worked examples 5 and 7.
- **Spot-checked by:** _(blank until a human checks)_ — see convention 4 below
  on whether "onto" is tested against the codomain or against the range as
  stated. The chapter does **not** teach a formula for the number of onto
  functions in the general case; every onto question in the bank is either the
  m = n case (n! bijections) or the impossible case (0). Confirm the SM does not
  expect the general surjection count at Foundation level.

## Limits

- **Results relied on, in their conventional statements:** lim (x → a) f(x) = L
  means f(x) approaches L as x approaches a, with x never equal to a; the value
  f(a) is irrelevant to the limit and may not even exist. The limit exists if
  and only if the left-hand and right-hand limits are equal and finite. Limits
  add, subtract, multiply and scale term by term, and divide provided the
  denominator's limit is non-zero.
  - **Methods:** direct substitution where the function is defined and behaves;
    factorisation and cancellation for a 0/0 form; rationalisation by the
    conjugate where a surd produces the 0/0; and the standard limits below.
  - **Standard limits taken as known WITHOUT PROOF:**
    lim (x → a) (xⁿ − aⁿ) ÷ (x − a) = n·aⁿ⁻¹;
    lim (x → 0) (eˣ − 1) ÷ x = 1; lim (x → 0) (aˣ − 1) ÷ x = logₑ a;
    lim (x → 0) logₑ(1 + x) ÷ x = 1;
    lim (x → 0) (1 + x)^(1/x) = e and lim (x → ∞) (1 + 1/x)ˣ = e.
  - **Rational functions as x → ∞:** lower degree on top gives 0; equal degrees
    give the ratio of the leading coefficients; higher degree on top gives no
    finite limit.
  - **0/0 is indeterminate** — a signal that the substitution has told you
    nothing, not a value.
- **Source:** standard results of elementary analysis; SM Ch 7 —
  reference_only. The standard limits are quoted, not derived, at this level.
- **Used in:** q-f3c7-044 to q-f3c7-048, cs-f3c7-03-a; notes §16, §17 and worked
  examples 9 and 11.
- **Spot-checked by:** _(blank until a human checks)_ — see convention 5 below
  on which standard limits are examinable and on the deliberate omission of the
  trigonometric limit.

## Continuity

- **Result relied on, in its conventional statement:** f is continuous at x = a
  when all three hold — (i) f(a) is defined, (ii) lim (x → a) f(x) exists, that
  is the two one-sided limits agree, and (iii) that limit equals f(a). A
  function is continuous on an interval when it is continuous at every point of
  it. Every polynomial is continuous everywhere; a rational function is
  continuous wherever its denominator is non-zero; sums, differences, products
  and (with a non-zero denominator) quotients of continuous functions are
  continuous. For a piecewise function only the junctions can fail, and a
  constant that makes the function continuous is found by setting
  LHL = RHL = f(a).
- **Source:** standard; SM Ch 7 — reference_only.
- **Used in:** q-f3c7-049, q-f3c7-050, cs-f3c7-03-b, cs-f3c7-03-c; notes §18 and
  worked example 10.
- **Spot-checked by:** _(blank until a human checks)_ — see convention 6 below
  on which branch owns a junction, which decides two keys.

## Negative marking

- **Position relied on:** Paper 3 is wholly objective and carries negative
  marking of **0.25 mark for each wrong answer**, with 1 mark for a correct
  answer and 0 for an unattempted one. The expected-value arithmetic in §19
  follows directly from those numbers.
- **Source:** `foundationScoring` in `src/data/foundation.js`, which the quiz
  engine also reads; ICAI's stated pattern for Papers 3 and 4.
- **Used in:** notes §19 and the last line of the one-page summary.
- **Spot-checked by:** _(blank until a human checks)_ — confirm the 0.25
  deduction is still the announced pattern for the Sept 2026 and Jan 2027
  attempts before the draft badge comes off.

---

# Reviewer's checklist — conventions chosen where practice varies

These are editorial calls, not sourced positions. Each one changes what a
student is taught, and the first four change answer keys outright if the SM
takes the other view.

1. **Is 0 a natural number?** The chapter says **no**: N = {1, 2, 3, …} and
   W = N ∪ {0}. §2 states this in a "mistake" callout, and **q-f3c7-005 turns on
   it** — the set is written over W precisely so the key does not depend on the
   convention, but its distractor A (6 instead of 7) is built from reading W as
   N. If the SM treats 0 as natural, the §2 table and that callout need
   rewording; no key moves, because no bank question quantifies over N near
   zero. Confirm before the badge comes off.

2. **What does a proper subset exclude — the set itself only, or the empty set
   too?** The chapter takes the standard position: **A ⊂ B means A ⊆ B and
   A ≠ B**, so the empty set IS a proper subset of every non-empty set and the
   count is **2ⁿ − 1**. This decides **q-f3c7-007 (key 63, not 62)**, and 62 is
   deliberately offered as the distractor for the other convention. Some Indian
   textbooks teach 2ⁿ − 2 as "the number of proper subsets", meaning non-empty
   proper subsets. If the SM does that, q-f3c7-007's key flips to B and §3 must
   be rewritten. **This is the single most important entry on this list.**

3. **Is the empty relation called symmetric and transitive on vacuous grounds?**
   The chapter says **yes**: on a non-empty set, R = ∅ is symmetric and
   transitive because both conditions are of the form "whenever a pair is
   present…", and no pair is present, so neither can be violated; it is not
   reflexive, because reflexivity requires pairs to be present. This decides
   **q-f3c7-032 (key B)** and underpins the §12 "mistake" callout and worked
   example 6, working note 4. Vacuous truth is standard mathematics but is
   sometimes ducked at Foundation level. If the SM avoids it or takes the other
   line, q-f3c7-032 must be rewritten or removed. The same convention makes the
   relation {(1, 2), (3, 4)} transitive, which §12 states expressly.

4. **Is "onto" tested against the codomain or against the range?** The chapter
   tests against the **codomain the question declares**: f is onto when
   range = codomain. This decides **q-f3c7-038 (key A: x² on R → R is neither
   one-one nor onto)**, and the explanation of option C names the error of
   judging onto against the values the function happens to produce, which would
   make every function onto and empty the word of content. Worked example 7(b)
   makes the same point by changing only the codomain. Confirm the SM states the
   codomain explicitly in its own onto questions; where a stem leaves the
   codomain unstated, the question is ambiguous and should not be set.

5. **Which standard limits are taken as known without proof, and is the
   trigonometric limit examinable?** §17 quotes five results without proof: the
   power limit n·aⁿ⁻¹, the two exponential limits, the logarithmic limit, and
   the two forms of the limit defining e. It **deliberately omits**
   lim (x → 0) (sin x) ÷ x = 1 and every other trigonometric limit, on the view
   that Foundation Paper 3 treats limits algebraically. No bank question needs a
   trigonometric limit. If the SM's Ch 7 does carry them, §17 should gain a row
   and the bank a question; nothing already written changes.

6. **Which branch of a piecewise definition owns the junction?** The chapter
   reads the inequality signs literally: in "f(x) = 2x + k for x ≤ 3", the point
   x = 3 belongs to the **first** branch, so that branch supplies both the
   left-hand limit and f(3). **q-f3c7-049 (k = 7)** and the whole of
   **cs-f3c7-03** depend on reading the signs this way, and cs-f3c7-03 is
   written with "x ≥ 8" on the upper branch so that the upper branch owns the
   junction there. This is not really a convention — it is what the inequality
   says — but students and some question papers are careless about it, so the
   §18 pointer callout states it expressly. Confirm the stems read
   unambiguously.

7. **How the Venn work is presented.** The chapter draws no diagrams. Regions
   are set out as tables of (region, description, count) in §6 and reasoned from
   there, which is deliberate: it is more reliable under exam conditions and it
   renders identically on any device. A reviewer who expects a drawn Venn
   diagram should note that this is a presentation choice, not an omission of
   scope — every result the diagram would carry is in the two tables.

8. **Verification method.** 49 of the 61 MCQs are flagged numerical and are
   proved by `scripts/verify_numerical/verify_sets-relations-functions.py`. 39
   of those are settled by **brute-force enumeration or search over constructed
   objects** — real Python sets built as an explicit population of labelled
   members for every Venn question, generated subsets for every subset, power
   set and relation count, and generated tuples for every function and one-one
   count. The remaining 10 are limit and composition questions, settled exactly
   with `fractions.Fraction` (synthetic division for a cancelled factor, the
   conjugate for a surd) and then confirmed numerically from both sides to a
   tolerance of 1e-4. No verifier re-applies the formula the stem is testing.

9. **Section count and length.** The notes run to 19 numbered sections plus a
   worked-examples block, a common-mistakes list and a one-page summary, about
   1,770 lines with 11 worked examples. The two places most likely to exceed the
   SM's depth are the §12 counting table for reflexive and symmetric relations
   and the §9 band formulas; both can be cut without touching a bank question
   other than q-f3c7-031.
