# Citations — Foundation P3 Ch 15 · Probability

Generated 11 Aug 2026 in the same session as the chapter content. This chapter
rests on the **ICAI Foundation Study Material, Paper 3, Chapter 15
(Probability)**, read for scope and for the definitions and theorems it teaches,
and on the standard statements of those results as they appear in any elementary
text on probability. The Study Material is ICAI-copyrighted, so it is used
`reference_only`: every position below is **paraphrased and cited by chapter
subject only, never reproduced**, no ICAI question text or worked answer is
copied, and all numbers, names and scenarios in the notes and in the bank are
fresh.

**No bare Act exists for this chapter.** Nothing here states a legal position:
the content is mathematics, and it is true whatever the law says. That is why the
notes frontmatter carries `applicable_attempts` but deliberately **omits
`law_as_on_date`** — there is no legal cut-off to pin, and an empty or invented
date would be worse than no date. The bank's questions likewise carry
`applicableAttempts` and `lastVerified` but no `lawAsOnDate`.

What a reviewer must actually check here is therefore different from a law
chapter. The theorems are not in doubt; the **conventions and set-up counts**
are. Sections A to I record each definition and theorem as it is conventionally
stated and where it is used. The **Reviewer's checklist of conventions** at the
end records every counting and convention choice made in this chapter, because a
single different choice silently changes answer keys.

---

## A. Random experiment, sample space and events

- **Position relied on (paraphrase):** a random experiment has outcomes that
  cannot be predicted individually but are all known in advance; the **sample
  space** S is the set of all outcomes; an **event** is any subset of S; an event
  occurs when the actual outcome lies inside it. The **sure** event is S and the
  **impossible** event is the empty set. Set operations carry the meanings
  A ∪ B = "A or B", A ∩ B = "A and B", A' = "not A".
- **Source:** ICAI Foundation SM Paper 3, Ch 15 (Probability), May 2026 edition —
  reference_only; standard elementary statements of the same definitions.
- **Used in:** notes §1; q-f3c15-001.
- **Spot-checked by:** _(blank until a human checks)_

## B. The three definitions and the axioms of probability

- **Position relied on (paraphrase):** the **classical (a priori)** definition
  `P(E) = n(E) / n(S)` applies when outcomes are finite and equally likely; the
  **relative-frequency (empirical)** definition is the limiting proportion of
  trials in which the event occurs; the **axiomatic** definition builds
  probability from `P(A) ≥ 0`, `P(S) = 1` and `P(A ∪ B) = P(A) + P(B)` for
  mutually exclusive A and B. From the axioms follow `0 ≤ P(A) ≤ 1`,
  `P(impossible) = 0` and the **complement rule** `P(A') = 1 − P(A)`.
- **Axioms relied on:** the three Kolmogorov axioms above, at the elementary level
  the Foundation SM treats them.
- **Used in:** notes §2; q-f3c15-002, q-f3c15-003, q-f3c15-004, q-f3c15-009,
  q-f3c15-032; worked examples 1 and 5.
- **Spot-checked by:** _(blank until a human checks)_

## C. Types of events

- **Position relied on (paraphrase):** events are **equally likely** when none is
  preferred to another; **mutually exclusive (disjoint)** when they share no
  outcome, so `P(A ∩ B) = 0`; **exhaustive** when their union is the whole sample
  space; **independent** when the occurrence of one does not change the
  probability of the other. Two events of non-zero probability cannot be both
  mutually exclusive and independent.
- **Used in:** notes §3; q-f3c15-015, q-f3c15-048.
- **Spot-checked by:** _(blank until a human checks)_

## D. The addition theorem

- **Position relied on (paraphrase):** for any two events,
  `P(A ∪ B) = P(A) + P(B) − P(A ∩ B)`, reducing to `P(A) + P(B)` when the events
  are mutually exclusive. The three-event form adds the singles, subtracts the
  pairs and adds back the triple.
- **Theorem relied on:** the addition theorem of probability (general and
  mutually-exclusive forms).
- **Used in:** notes §4; q-f3c15-014, q-f3c15-021, q-f3c15-022, q-f3c15-023,
  q-f3c15-024, q-f3c15-025, q-f3c15-026, q-f3c15-027; worked examples 3 and 6. The
  verifier counts the union directly over the sample space where possible, so the
  theorem and the raw count check each other.
- **Spot-checked by:** _(blank until a human checks)_

## E. Conditional probability and the multiplication theorem

- **Position relied on (paraphrase):** `P(A | B) = P(A ∩ B) / P(B)` for
  `P(B) > 0`; rearranged, the **multiplication theorem** is
  `P(A ∩ B) = P(B)P(A | B) = P(A)P(B | A)`. Drawing without replacement makes the
  second draw conditional on the first (the denominator falls by one each draw).
- **Theorems relied on:** the definition of conditional probability and the
  multiplication (compound-probability) theorem.
- **Used in:** notes §5; q-f3c15-029, q-f3c15-030, q-f3c15-031, q-f3c15-033,
  q-f3c15-034, q-f3c15-035, q-f3c15-036, q-f3c15-037; worked examples 4 and 5.
- **Spot-checked by:** _(blank until a human checks)_

## F. Independence

- **Position relied on (paraphrase):** A and B are **independent** if and only if
  `P(A ∩ B) = P(A)P(B)`, equivalently `P(A | B) = P(A)`. The probability that all
  of several independent events occur is the product of their probabilities, and
  "at least one" is handled by the complement, `1 − P(none)`.
- **Theorem relied on:** the multiplication theorem for independent events.
- **Used in:** notes §6; q-f3c15-038, q-f3c15-039, q-f3c15-040, q-f3c15-041,
  q-f3c15-042; worked examples 6 and 7.
- **Spot-checked by:** _(blank until a human checks)_

## G. Bayes' theorem and total probability

- **Position relied on (paraphrase):** where causes B1, B2, ... are mutually
  exclusive and exhaustive and an event A is observed, the **theorem of total
  probability** gives `P(A) = Σ P(Bi)P(A | Bi)` and **Bayes' theorem** gives
  `P(Bk | A) = P(Bk)P(A | Bk) / P(A)`. At Foundation level it is asked with two or
  three causes and simple fractions.
- **Theorems relied on:** the theorem of total probability and Bayes' theorem, in
  their elementary (finite, discrete) form.
- **Scope note for the reviewer:** Bayes' theorem sits at the harder edge of the
  Foundation syllabus. This chapter keeps it to a single two-urn illustration and
  two questions (q-f3c15-043, q-f3c15-044). If the May 2026 edition treats Bayes
  only in outline, those two questions and worked example 8 can be trimmed;
  nothing else depends on them.
- **Used in:** notes §7; q-f3c15-043, q-f3c15-044; worked example 8.
- **Spot-checked by:** _(blank until a human checks)_

## H. Random variables: expectation, variance and mean

- **Position relied on (paraphrase):** for a discrete random variable X with a
  probability distribution summing to 1, the **expectation (mean)** is
  `E(X) = Σ x·P(x)`, the **variance** is `Var(X) = E(X²) − [E(X)]²` with
  `E(X²) = Σ x²·P(x)`, and the **standard deviation** is its square root. The mean
  and the expectation are the same number. A game is **fair** when its expected
  gain is zero.
- **Definitions relied on:** the expectation and variance of a discrete random
  variable.
- **Used in:** notes §8; q-f3c15-045, q-f3c15-046, q-f3c15-047; worked examples 9
  and 10.
- **Spot-checked by:** _(blank until a human checks)_

## I. Odds in favour and against

- **Position relied on (paraphrase):** for a favourable outcomes and b
  unfavourable, **odds in favour** are `a : b` and **odds against** are `b : a`.
  Odds in favour `a : b` give `P = a / (a + b)`; a probability p gives odds in
  favour `p : (1 − p)` and odds against `(1 − p) : p`.
- **Used in:** notes §9; q-f3c15-049, q-f3c15-050; worked example 10.
- **Spot-checked by:** _(blank until a human checks)_

---

# Reviewer's checklist of conventions

**These matter more here than the theorems.** Every item below is a choice, not a
fact. A different choice does not merely change the wording — it moves a computed
figure and therefore **changes answer keys**. Please confirm each against the
ICAI SM (May 2026 ed.) and initial it.

1. **Equally likely by default.** Every coin, die, card and ball problem assumes
   the outcomes are equally likely (fair coin, fair die, well-shuffled pack,
   random draw), so the classical definition applies. No question in this bank
   uses a biased device.

2. **Two dice are distinguishable.** The sample space for two dice is the **36
   ordered pairs**, so (2,5) and (5,2) are counted separately (q-f3c15-016 to
   q-f3c15-020, q-f3c15-026, q-f3c15-037). Treating the dice as identical would
   give 21 unordered outcomes and change every dice key.

3. **Coins give 2^n outcomes.** n coins (or one coin n times) give 2^n equally
   likely outcomes, and "exactly r heads" is counted as nCr of them (q-f3c15-005
   to q-f3c15-008). "At least one head" is computed as 1 − P(none).

4. **Standard 52-card pack.** 26 red and 26 black, 13 per suit, 4 of each rank, 3
   face cards per suit (jack, queen, king) so 12 face cards in all, and the ace is
   **not** counted as a face card (q-f3c15-010 to q-f3c15-014, q-f3c15-024,
   q-f3c15-035, q-f3c15-038). If the SM counts the ace as a face card, q-f3c15-012
   changes.

5. **"Drawn together" means without replacement.** Two balls or cards drawn
   together, or "at random" with no further word, are drawn **without
   replacement**, so batch draws use combinations and successive draws use a
   falling denominator (q-f3c15-029 to q-f3c15-031, q-f3c15-035). The phrase
   **"with replacement"** is stated explicitly wherever the draws are meant to be
   independent (q-f3c15-038). Confirm the SM uses the same default.

6. **The complement route for "at least one".** "At least one" is computed as
   1 − P(none) rather than by adding overlapping probabilities (q-f3c15-006,
   q-f3c15-008, q-f3c15-042). This avoids double-counting and is the SM's own
   preferred method; confirm it.

7. **Independence is tested, not assumed.** Where a question calls events
   independent it says so, and the joint probability is then the product
   (q-f3c15-039 to q-f3c15-042). Worked example 6 shows independence being
   **checked** by comparing P(A ∩ B) with P(A)P(B) rather than assumed from words.

8. **Bayes uses equal priors here.** The two-urn Bayes questions choose the urn
   "at random", i.e. with equal prior probabilities 1/2 each (q-f3c15-043,
   q-f3c15-044). If a future variant makes the urns unequally likely, the priors
   in the verifier must change with the stem.

9. **Distributions are checked to sum to 1.** Every random-variable question is
   given a valid distribution, and the verifier asserts the probabilities total 1
   before computing E(X) or Var(X) (q-f3c15-046, q-f3c15-047).

10. **Variance by the shortcut form.** Var(X) is computed as E(X²) − [E(X)]², and
    the standard deviation is offered as a distractor (q-f3c15-047 option D). If
    the SM asks for the **sample** variance with an (n − 1) divisor anywhere, that
    is a different quantity and is not used here.

11. **Odds versus probability.** Odds in favour a : b give a probability
    a / (a + b), **not** a / b; the standard student error (writing 3/2 for
    "odds 3 : 2") is a deliberate distractor (q-f3c15-049 option B). Odds
    "against" reverse the ratio (q-f3c15-050). Confirm the SM's wording of "in
    favour" and "against" matches.

12. **Exact rationals throughout.** Every numerical answer is an exact fraction or
    a terminating decimal, and the verifier carries it as `fractions.Fraction`, so
    there is no rounding to argue about. Decimal-valued options (e.g. 0.88) are
    exact rationals (22/25) and are compared as such.

**Machine verification already done (do not repeat it).** All **42** numerical
questions in this bank are recomputed from their stems by
`scripts/verify_numerical/verify_probability.py`, which uses
`fractions.Fraction`, builds each sample space or count from first principles (or
applies the stated theorem), and maps each computed value to an option by value —
never by the bank's key. The runner reports 0 failures. Your time is better spent
on the twelve conventions above and on the scope call flagged in section G.

**Spot-checked by:** _(blank until a human checks)_
