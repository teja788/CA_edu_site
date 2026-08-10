# Citations — Foundation P3 Ch 8 · Basic Applications of Differential and Integral Calculus

Generated 10 Aug 2026. The chapter content and the question bank were authored
in one session; this citations file was completed separately in the same
session after that run was cut short, and the verifier functions for
`q-f3c8-041` to `q-f3c8-050` and all twelve case-set sub-questions were written
at the same time. That split is recorded here because it is the kind of thing a
reviewer should know: the notes and the bank were written by one pass, and the
last 22 verifier functions were written by a second pass that read the finished
bank rather than the reasoning behind it. Every one of those 22 recomputed the
bank's answer independently and agreed with it — see the note under
**Verification status** below.

**There is no bare Act behind this chapter.** Mathematics has no statutory
source, so nothing here can be checked against India Code the way a Business
Laws chapter can. What this file records instead is (i) the **ICAI Study
Material scope** the chapter was written to, (ii) every **standard result of
elementary calculus** relied on, stated in its conventional form so a reviewer
can check the statement rather than hunt for a source, and (iii) the
**editorial conventions** chosen at points where textbook practice genuinely
varies. Section (iii) is the reviewer's real checklist: those are the calls a
human must confirm, and several of them move answer keys.

**Note on `law_as_on_date`.** The chapter's frontmatter deliberately **omits**
`law_as_on_date`. That field pins content to a cut-off date for a legal or
fiscal position, and this chapter states none — a derivative does not change
with a Finance Act. `applicable_attempts` is present, because the SM edition
and the examinable scope can change between attempts.

The ICAI Study Material was used `reference_only` — read to confirm that the
scope and the level of treatment match, and cited by chapter number only. No SM
prose, no SM worked example and no SM question wording was reproduced. Every
number, scenario and name in the chapter and the bank is original: the pump
maker at Coimbatore, the machined-part supplier and the spares depot are
inventions, and their figures were chosen to give clean optima.

A reviewer spot-checking this file should confirm each entry against **ICAI
Foundation SM Paper 3, Ch 8 (Basic Applications of Differential and Integral
Calculus), May 2026 edition** and initial the "Spot-checked by" line.

## Verification status

All **61 numerical questions** in this bank are machine-verified by
`scripts/verify_numerical/verify_differential-and-integral-calculus.py`, which
does **not** re-apply the algebra the stem used. A claimed derivative is
compared with a five-point central difference quotient of the original
function; a claimed antiderivative is differentiated numerically and compared
with the integrand; a claimed definite integral is recomputed by composite
Simpson's rule on 2,000 sub-intervals; a claimed maximum or minimum is
confirmed on a dense grid of 4,001 points and by ternary search that uses no
calculus at all. The reviewer therefore does **not** need to re-check any
arithmetic in this chapter. What is left for a human is exactly the conventions
listed at the end of this file, and the question of whether the scope matches
the SM.

Two consequences worth stating plainly. First, the constant of integration
cannot be seen by a numerical derivative, so each option carries an explicit
flag recording whether "+ c" is actually printed; the verifier reads that flag,
never the algebra. Second, the EOQ case set is verified by minimising the
annual cost function written straight from the scenario's own words, **not** by
the √(2DCo/Ch) formula — so those four keys test the model, not a memorised
square root.

## Scope relied on

- **Position relied on (paraphrase, not quoted):** the chapter covers the
  derivative as a rate of change and as the slope of a tangent; the derivative
  from first principles; the standard derivatives of a constant, of xⁿ, of eˣ,
  of aˣ and of log x; the sum, difference, constant-multiple, product, quotient
  and chain rules; logarithmic differentiation; implicit and parametric
  differentiation; higher-order derivatives; marginal cost, marginal revenue
  and average cost as derivatives; maxima and minima by the first- and
  second-derivative tests, applied to business optimisation; integration as the
  reverse of differentiation and the constant of integration; the standard
  integrals; integration by substitution, by parts and by partial fractions;
  the definite integral and its evaluation; and business applications of the
  definite integral, chiefly recovering totals from marginals.
- **Source:** ICAI Foundation SM Paper 3, Ch 8, May 2026 edition —
  reference_only.
- **Used in:** the whole chapter; the section numbering of the notes follows
  this scope order.
- **Spot-checked by:** _(blank until a human checks)_

## The derivative as the limit of a difference quotient

- **Result relied on (conventional statement):** f′(x) = lim(h → 0)
  [f(x + h) − f(x)] / h, when that limit exists; geometrically the slope of the
  tangent at x, and physically the instantaneous rate of change of f at x.
- **Used in:** §1, §2 and `q-f3c8-002`.
- **Note for the reviewer:** the chapter derives two results from first
  principles and then stops, on the view that the Foundation paper tests the
  table rather than the derivation. Confirm the SM does not require more.
- **Spot-checked by:** _(blank)_

## The standard derivatives

- **Results relied on (conventional statements):** d/dx (k) = 0;
  d/dx (xⁿ) = n·xⁿ⁻¹ for every real n; d/dx (eˣ) = eˣ;
  d/dx (aˣ) = aˣ·log a; d/dx (log x) = 1/x for x > 0.
- **Used in:** §3, the derivative table, and roughly a third of the bank.
- **Note for the reviewer:** the power rule is stated for **every real n**,
  including negative and fractional exponents, because the bank tests 1/x and
  √x through it. Confirm the SM states it that generally.
- **Spot-checked by:** _(blank)_

## The rules of combination

- **Results relied on (conventional statements):** the sum, difference and
  constant-multiple rules; the product rule (uv)′ = u′v + uv′; the quotient
  rule (u/v)′ = (u′v − uv′) / v²; and the chain rule, dy/dx = (dy/du)(du/dx).
- **Used in:** §4 to §7, and the largest single group of questions in the bank.
- **Note for the reviewer:** the quotient rule's numerator order (u′v − uv′,
  not uv′ − u′v) is the one place where a printed slip would silently invert
  several keys. The verifier catches it numerically, but the notes' statement
  should still be read carefully.
- **Spot-checked by:** _(blank)_

## Logarithmic differentiation

- **Result relied on (conventional statement):** where y is a product, quotient
  or power that is awkward to differentiate directly, take logs of both sides
  and differentiate implicitly: (1/y)(dy/dx) = d/dx [log y], so
  dy/dx = y · d/dx [log y], with y written back in its original form in x.
- **Used in:** §8 and the questions on xˣ-type forms.
- **Note for the reviewer:** the chapter is explicit that the bracket must be
  multiplied back by y, and that leaving the answer in terms of the letter y is
  the trap the distractors are built on. Confirm the SM presents it the same way.
- **Spot-checked by:** _(blank)_

## Implicit and parametric differentiation

- **Results relied on (conventional statements):** for an implicit relation,
  differentiate every term with respect to x, treating y as a function of x and
  attaching dy/dx by the chain rule, then solve for dy/dx. For a parametric
  form x = f(t), y = g(t), dy/dx = (dy/dt) ÷ (dx/dt), provided dx/dt ≠ 0.
- **Used in:** §9.
- **Note for the reviewer — SCOPE CALL.** Whether implicit and parametric
  differentiation are examinable at Foundation varies between presentations.
  The chapter includes them as a full section. If the SM omits them, §9 can be
  removed without disturbing any other section. Check the bank before cutting:
  any question keyed to a §9 anchor would need removing with it.
- **Spot-checked by:** _(blank)_

## Higher-order derivatives

- **Result relied on (conventional statement):** the second derivative f″(x) is
  the derivative of f′(x), written d²y/dx²; it measures the rate at which the
  rate of change is itself changing, and it is what the second-derivative test
  reads.
- **Used in:** §10, and every maxima-and-minima question.
- **Spot-checked by:** _(blank)_

## Marginal cost, marginal revenue and average cost

- **Results relied on (conventional statements):** marginal cost is the
  derivative of total cost, MC = dC/dx; marginal revenue is the derivative of
  total revenue, MR = dR/dx; average cost is AC = C(x)/x, and average cost is
  stationary where MC = AC.
- **Used in:** §11, §13, `cs-f3c8-01` and `cs-f3c8-02`.
- **Note for the reviewer:** the chapter treats output as a **continuous**
  variable throughout, so "the marginal cost at 20 units" means the derivative
  at x = 20, not the cost of the 21st unit. Both readings appear in teaching
  material and they give different numbers. Every case-set scenario says
  "treat x as a continuous variable" for exactly this reason, but if the SM
  defines marginal cost as the incremental cost of one more unit, the wording
  of §11 should change even though the keys would not.
- **Spot-checked by:** _(blank)_

## Maxima and minima: the two tests

- **Results relied on (conventional statements):** critical points solve
  f′(x) = 0. Under the **second-derivative test**, f″(c) < 0 gives a maximum,
  f″(c) > 0 gives a minimum, and f″(c) = 0 is inconclusive. Under the
  **first-derivative test**, a sign change of f′ from positive to negative
  gives a maximum, negative to positive gives a minimum, and no sign change
  gives a point of inflexion.
- **Used in:** §12, §13, and all three case sets.
- **Note for the reviewer — CONVENTION.** The chapter makes the
  **second-derivative test its default**, on the stated ground that an
  objective paper rewards speed, and falls back on sign-testing only when the
  second derivative vanishes. If the SM leads with the first-derivative test,
  §12's ordering should be swapped. No key moves either way: the verifier
  confirms every extremum on a dense grid, independent of which test the notes
  recommend.
- **Spot-checked by:** _(blank)_

## Integration as the reverse of differentiation

- **Result relied on (conventional statement):** F is an antiderivative of f
  when F′ = f; because any constant differentiates to zero, the indefinite
  integral is the whole family F(x) + c, and the constant of integration is
  part of the answer, not an optional flourish.
- **Used in:** §14, and `q-f3c8-041` and `q-f3c8-042` directly.
- **Note for the reviewer — CONVENTION THAT CARRIES KEYS.** In both
  `q-f3c8-041` and `q-f3c8-042` the distractor is the correct function with
  "+ c" removed. Those two keys rest on the position that an indefinite
  integral written without its constant is **wrong**, not merely untidy. If the
  SM accepts an answer without the constant, both keys become ambiguous and
  those two questions must be rewritten rather than re-keyed. This is the
  single highest-value check in this file.
- **Spot-checked by:** _(blank)_

## The standard integrals

- **Results relied on (conventional statements):** ∫xⁿ dx = xⁿ⁺¹/(n + 1) + c
  for n ≠ −1; ∫(1/x) dx = log |x| + c; ∫eˣ dx = eˣ + c;
  ∫aˣ dx = aˣ/log a + c. Where the inside of a bracket is linear in x,
  integrate as usual and divide by the coefficient of x:
  ∫(ax + b)ⁿ dx = (ax + b)ⁿ⁺¹ / [a(n + 1)] + c.
- **Used in:** §15, and `q-f3c8-041` to `q-f3c8-045`.
- **Note for the reviewer:** the n = −1 gap in the power rule is presented as
  the reason the logarithm exists in the table at all, and the **modulus sign
  is retained** in every logarithmic integral, on the stated ground that 1/x is
  defined for negative x where log x is not. Some presentations drop the
  modulus. No key moves — the verifier differentiates numerically at positive
  sample points either way — but the printed answers should match the SM.
- **Spot-checked by:** _(blank)_

## What "log" means in this chapter

- **Convention relied on:** **log means the natural logarithm**, to the base e,
  what a calculator calls ln — everywhere in this chapter, in the derivative
  table and the integral table alike. The chapter states this explicitly in a
  callout in §3 and attributes the usage to ICAI's own material.
- **Used in:** the whole of §3, §15 to §18, and every logarithmic option in the
  bank.
- **Note for the reviewer — HIGH VALUE.** This differs from Ch 1 (Ratio,
  Indices, Logarithms), where an unmarked `log` means base 10. The two chapters
  therefore use the same symbol for different things, which is defensible only
  because each says so where a student will see it. Confirm both statements
  survive editing, and confirm that ICAI does use "log" for the natural log in
  its calculus chapter — the whole convention rests on that claim.
- **Spot-checked by:** _(blank)_

## Integration by substitution

- **Results relied on (conventional statements):** where the integrand contains
  a function and its own derivative, put u equal to the inner function and
  convert the differential as well as the function; in particular
  ∫ g′(x)/g(x) dx = log |g(x)| + c.
- **Used in:** §16, `q-f3c8-045` and `q-f3c8-046`.
- **Note for the reviewer:** the un-converted differential — forgetting that
  x dx = du/2 when u = x² — is the error the distractors in `q-f3c8-045` are
  built from. That is the intended teaching point of the question.
- **Spot-checked by:** _(blank)_

## Integration by parts, and ILATE

- **Result relied on (conventional statement):** ∫u·v dx = u∫v dx −
  ∫[u′·∫v dx] dx, choosing as u the function that comes earlier in **ILATE**
  (Inverse, Logarithmic, Algebraic, Trigonometric, Exponential). The standard
  consequence ∫log x dx = x log x − x + c is obtained by taking v = 1.
- **Used in:** §17, `q-f3c8-047` and `q-f3c8-048`.
- **Note for the reviewer — SCOPE.** Trigonometric functions appear in the
  ILATE mnemonic for completeness only; the chapter states in the same
  paragraph that the CA Foundation syllabus does not examine them, and no
  question anywhere in the bank uses one. If the SM omits the T from the
  mnemonic, the letter can be dropped without touching a key.
- **Spot-checked by:** _(blank)_

## Integration by partial fractions

- **Result relied on (conventional statement):** a proper fraction with
  distinct linear factors splits as A/(x − a) + B/(x − b); A and B are found by
  substituting the values that kill one bracket at a time; each piece then
  integrates to a logarithm.
- **Used in:** §18 and `q-f3c8-049`.
- **Note for the reviewer — SCOPE CALL.** The chapter covers **distinct linear
  factors only**. Repeated factors and irreducible quadratic factors are
  deliberately omitted as beyond Foundation depth. Confirm against the SM; if
  repeated factors are examinable, §18 is short one case.
- **Spot-checked by:** _(blank)_

## The definite integral

- **Results relied on (conventional statements):** ∫ from a to b of f(x) dx =
  F(b) − F(a), where F is any antiderivative of f; the constant of integration
  cancels in the subtraction, which is why a definite integral carries no + c.
- **Used in:** §19, `q-f3c8-050`, and `cs-f3c8-02-c`.
- **Note for the reviewer:** the order F(upper) − F(lower) is stated
  explicitly, and the reversed subtraction is carried as a distractor in
  `q-f3c8-050` (−34 against the correct 34). A presentation that is casual
  about the order would make that distractor defensible, which it must not be.
- **Spot-checked by:** _(blank)_

## Business applications of the definite integral

- **Results relied on (conventional statements):** total cost is recovered from
  marginal cost by integration, with the **fixed cost supplying the constant**;
  total revenue is recovered from marginal revenue with **no constant**,
  because revenue is zero at zero output; and the change in a total between two
  output levels is the definite integral of the marginal between them, in which
  the constant and the fixed cost both cancel.
- **Used in:** §20 and the whole of `cs-f3c8-02`.
- **Note for the reviewer:** the asymmetry between the two constants — fixed
  cost known, revenue constant necessarily zero — is the point of that case
  set, and `cs-f3c8-02-a` carries the fixed-cost-omitted figure as its
  distractor while `cs-f3c8-02-c` carries the fixed-cost-wrongly-included
  figure. Both rest on the statements above.
- **Spot-checked by:** _(blank)_

## The economic order quantity, and why it is derived rather than quoted

- **Result relied on (conventional statement):** where demand is steady,
  ordering cost is a fixed amount per order and stock is drawn down evenly, the
  annual total of ordering and holding cost is (D/q)·Co + (q/2)·Ch, which is
  least at q = √(2·D·Co / Ch), and the minimum total is √(2·D·Co·Ch).
- **Used in:** §13 and the whole of `cs-f3c8-03`.
- **Note for the reviewer — DELIBERATE CHOICE.** The scenario states the cost
  structure in words (cost per order, cost of carrying one unit for a year,
  average stock is half the order size) and asks the student to build and
  minimise the function. The EOQ formula is given in the notes, but the
  **verifier does not use it** — it minimises the cost function by ternary
  search. So `cs-f3c8-03-a` to `-d` are proof that the model is right, not that
  a remembered square root was typed correctly. `-d` additionally tests that
  quadrupling the holding cost **halves** the optimum, with the "divide by
  four" answer (300) sitting next to the correct 600.
- **Spot-checked by:** _(blank)_

## Negative marking

- **Position relied on:** Paper 3 carries 0.25 negative marking per wrong
  answer, and no penalty for a question left blank — the values in
  `foundationScoring` in `src/data/foundation.js`.
- **Used in:** §21.
- **Note for the reviewer:** §21 states the arithmetic factually and makes the
  same point the sibling Paper 3 chapters make — that a guess between two
  remaining options is not a random guess, because every distractor in this
  bank is a prepared error rather than a filler. Confirm the tone stays
  descriptive; the house style forbids pressure language.
- **Spot-checked by:** _(blank)_

## The reviewer's checklist — conventions that could move keys

Ranked by how much damage a disagreement would do. Everything above this line
is arithmetic the machine has already proven; this is the part that needs a
human.

1. **"+ c" is compulsory in an indefinite integral.** `q-f3c8-041` and
   `q-f3c8-042` are keyed on it, with the constant-less version as the
   distractor in each. If the SM accepts an answer without the constant, both
   questions must be rewritten, not re-keyed. **Highest value.**
2. **`log` means natural log throughout this chapter**, while it means base 10
   in Ch 1. Both chapters say so explicitly. Confirm ICAI's calculus chapter
   really does use "log" for the natural log, because every logarithmic option
   in the bank depends on that reading.
3. **Marginal cost is the derivative, not the cost of one more unit.** Every
   case-set scenario says to treat output as continuous. If the SM defines it
   incrementally, §11's wording needs changing even though no key moves.
4. **The second-derivative test is the chapter's default.** Swap the ordering
   in §12 if the SM leads with sign-testing. No key moves.
5. **Partial fractions cover distinct linear factors only.** Repeated and
   irreducible quadratic factors are omitted as beyond Foundation.
6. **Implicit and parametric differentiation are in scope** (§9). Removable as
   a block if the SM omits them — but check the bank for anchors into §9 first.
7. **The modulus is kept inside every logarithmic integral.** Cosmetic; no key
   moves, but the printed answers should match the SM's habit.
8. **Trigonometric functions are excluded**, appearing only as the T in ILATE
   with an explicit note that they are not examined. No question uses one.

## Spot-check record

| Row | Checked against | By | Date |
|---|---|---|---|
| _(all rows above)_ | ICAI SM P3 Ch 8, May 2026 ed. | _(blank)_ | _(blank)_ |

Until this table is completed and the frontmatter's `review_status` changes from
`unreviewed`, the chapter renders the amber "✎ Community draft" badge, as
required by CONTRIBUTING.md item 4.

