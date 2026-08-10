# Citations — Foundation P3 Ch 2 · Equations

Generated 10 Aug 2026 in the same session as the chapter content.

**There is no bare Act behind this chapter.** Mathematics has no statutory
source, so nothing here can be checked against India Code the way a Business
Laws chapter can. What this file records instead is (i) the **ICAI Study
Material scope** the chapter was written to, (ii) every **standard algebraic
result** relied on, stated in its conventional form so a reviewer can check the
statement rather than hunt for a source, and (iii) the **editorial conventions**
chosen at points where textbook practice genuinely varies. Section (iii) is the
reviewer's real checklist: those are the calls a human must confirm.

**Note on `law_as_on_date`.** The chapter's frontmatter deliberately **omits**
`law_as_on_date`. That field pins content to a cut-off date for a legal or
fiscal position, and this chapter states none — an equation's roots do not
change with a Finance Act. `applicable_attempts` is present, because the SM
edition and the examinable scope can change between attempts.

The ICAI Study Material was used `reference_only` — read to confirm that the
scope and the level of treatment match, and cited by chapter number only. No SM
prose, no SM worked example and no SM question wording was reproduced. Every
number, scenario and name in the chapter and the bank is original.

A reviewer spot-checking this file should confirm each entry against **ICAI
Foundation SM Paper 3, Ch 2 (Equations), May 2026 edition** and initial the
"Spot-checked by" line.

## Scope relied on

- **Position relied on (paraphrase, not quoted):** the chapter covers simple
  (linear) equations in one unknown; simultaneous linear equations in two
  unknowns by elimination, substitution and cross-multiplication, together with
  the conditions for a unique solution, no solution and infinitely many
  solutions; simultaneous linear equations in three unknowns; quadratic
  equations solved by factorisation, by completing the square and by the
  formula; the discriminant and the nature of the roots; the relations between
  roots and coefficients, the formation of an equation from given roots, and
  symmetric functions of the roots at an elementary level; equations reducible
  to quadratic form; cubic equations solved by locating one rational root; and
  applications to business situations.
- **Source:** ICAI Foundation SM Paper 3, Ch 2 (Equations), May 2026 edition —
  reference_only.
- **Used in:** the whole chapter; the section numbering of the notes follows
  this scope order.
- **Spot-checked by:** _(blank until a human checks)_

## Equation and identity

- **Result relied on:** an equation is a statement of equality that holds only
  for particular values of the variable; an identity is a statement of equality
  that holds for every value of the variable. When solving, an equation reduces
  to a value; an identity reduces every term away and leaves a true statement
  with no variable in it (0 = 0), while an inconsistent equation leaves a false
  statement (for example 9 = −3).
- **Source:** elementary algebra, standard; SM Ch 2 introductory treatment —
  reference_only.
- **Used in:** q-f3c2-001, q-f3c2-002, q-f3c2-006; notes §1 and the §3 paragraph
  on a letter that cancels.
- **Spot-checked by:** _(blank until a human checks)_

## Degree and the number of roots

- **Result relied on:** a polynomial equation of degree n has exactly n roots,
  counted with multiplicity. Degree 1 is linear, degree 2 quadratic, degree 3
  cubic, degree 4 biquadratic.
- **Source:** the fundamental theorem of algebra, in the elementary form in
  which Foundation states it; SM Ch 2 — reference_only.
- **Used in:** q-f3c2-003, q-f3c2-037, q-f3c2-039; notes §2 (the degree table),
  §15 and §16.
- **Spot-checked by:** _(blank until a human checks)_

## Linear equations and the transposition rule

- **Result relied on:** ax + b = 0 with a ≠ 0 has the single root x = −b/a. An
  equation is solved by clearing fractions with the LCM of the denominators,
  removing brackets, transposing (a term changes sign when it crosses the
  equality) and dividing by the coefficient of the unknown. Where the unknown
  appears in a denominator, any root that makes an original denominator zero is
  rejected, because the equation is undefined at that value.
- **Source:** elementary algebra, standard; SM Ch 2 — reference_only.
- **Used in:** q-f3c2-004, q-f3c2-005, q-f3c2-006; notes §3 including both
  working notes and the "mistake" callout on transposition.
- **Spot-checked by:** _(blank until a human checks)_

## The cross-multiplication rule

- **Result relied on, in the conventional statement:** for
  a₁x + b₁y + c₁ = 0 and a₂x + b₂y + c₂ = 0,

  > x ÷ (b₁c₂ − b₂c₁) = y ÷ (c₁a₂ − c₂a₁) = 1 ÷ (a₁b₂ − a₂b₁),

  valid whenever a₁b₂ − a₂b₁ ≠ 0. The rule requires both equations written with
  every term on the left and zero on the right; c₁ and c₂ therefore carry the
  sign they have **after** transposition.
- **Source:** standard algebraic result; SM Ch 2 presents the same three-fraction
  form — reference_only.
- **Used in:** q-f3c2-010; notes §5 (both `formula` lines, the worked note and
  the "mistake" callout on the sign of c) and worked example 2, working note 3.
- **Spot-checked by:** _(blank until a human checks)_ — **confirm the SM writes
  the rule in this order of subscripts.** Some texts present the second
  denominator as (a₁c₂ − a₂c₁) with the fraction read as −y; the answers are
  identical but the printed form differs, and students match forms literally.

## Consistency of a pair of linear equations

- **Result relied on:** for a₁x + b₁y = c₁ and a₂x + b₂y = c₂ —
  a₁/a₂ ≠ b₁/b₂ gives a unique solution (consistent and independent);
  a₁/a₂ = b₁/b₂ ≠ c₁/c₂ gives no solution (inconsistent, parallel lines);
  a₁/a₂ = b₁/b₂ = c₁/c₂ gives infinitely many solutions (consistent and
  dependent, coincident lines). The unique-solution condition is equivalent to
  a₁b₂ − a₂b₁ ≠ 0.
- **Source:** standard; SM Ch 2 — reference_only.
- **Used in:** q-f3c2-011, q-f3c2-012, cs-f3c2-03-c; notes §6 (the condition
  table, the paragraph on the geometry and the pointer callout) and worked
  example 3.
- **Spot-checked by:** _(blank until a human checks)_

## Quadratic equations: factorisation, completing the square, and the formula

- **Results relied on, in their conventional statements:** for ax² + bx + c = 0
  with a ≠ 0 —
  1. **Factorisation** — split b into two parts whose sum is b and whose product
     is a × c, then factorise by grouping and set each factor to zero.
  2. **Completing the square** — divide by a, move the constant across, add
     (b/2a)² to both sides, and take **both** square roots.
  3. **The quadratic formula** — x = [ −b ± √(b² − 4ac) ] ÷ 2a.
  A quadratic with no constant term, ax² + bx = 0, always has one root equal to
  zero; a pure quadratic ax² + c = 0 has roots equal in magnitude and opposite
  in sign.
- **Source:** standard algebraic results, the formula being the general solution
  of completing the square; SM Ch 2 — reference_only.
- **Used in:** q-f3c2-015 to q-f3c2-020, cs-f3c2-02-a; notes §8, §9 and §10
  including the derivation note and all three "mistake" callouts, and worked
  examples 5 and 8.
- **Spot-checked by:** _(blank until a human checks)_

## The discriminant and the nature of the roots

- **Result relied on:** with D = b² − 4ac and a, b, c rational —
  D > 0 and a perfect square → roots real, distinct and **rational**;
  D > 0 and not a perfect square → roots real, distinct and **irrational**,
  occurring as a conjugate pair p ± √q;
  D = 0 → roots **real and equal**, both equal to −b/2a;
  D < 0 → roots **not real**, occurring as a conjugate pair of imaginary
  numbers. The "real roots" condition is therefore D ≥ 0.
- **Source:** standard; SM Ch 2 — reference_only.
- **Used in:** q-f3c2-021 to q-f3c2-025; notes §11 (the D table, the worked note
  on k, the −b/2a `formula` line and the pointer callout) and the summary.
- **Spot-checked by:** _(blank until a human checks)_ — see the two convention
  entries at the foot of this file on **complex roots** and on **"real and
  equal" counting as two roots**.

## Relations between roots and coefficients (Vieta's relations)

- **Results relied on, in their conventional statements:**
  - **Quadratic** ax² + bx + c = 0 with roots α and β: **α + β = −b/a** and
    **αβ = c/a**.
  - **Cubic** ax³ + bx² + cx + d = 0 with roots α, β, γ: **α + β + γ = −b/a**,
    **αβ + βγ + γα = c/a**, **αβγ = −d/a** — the signs alternating minus, plus,
    minus.
  - **Forming an equation** from given roots: x² − (sum)x + (product) = 0,
    scaled by any convenient factor to clear fractions.
  - **Derived-root equations:** roots kα and kβ give sum ks and product k²p;
    roots α + k and β + k give sum s + 2k and product p + ks + k²; roots 1/α and
    1/β give the equation cx² + bx + a = 0, that is the coefficients reversed;
    roots −α and −β give ax² − bx + c = 0.
- **Source:** standard (Vieta's relations); SM Ch 2 — reference_only.
- **Used in:** q-f3c2-026 to q-f3c2-032, q-f3c2-042, q-f3c2-043, cs-f3c2-02-b;
  notes §12, §13 (including the four-row derived-root table and the reciprocal
  result) and §16, and worked examples 6 and 8.
- **Spot-checked by:** _(blank until a human checks)_ — the **derived-root
  table in §13 goes slightly beyond the minimum** some editions teach. Confirm
  the SM covers the reciprocal and shifted cases at Foundation depth; if not,
  the table can be trimmed without affecting any bank question except
  q-f3c2-032, which uses only the scaled-roots row.

## Symmetric functions of the roots

- **Results relied on**, with s = α + β and p = αβ:
  α² + β² = s² − 2p; (α − β)² = s² − 4p; α³ + β³ = s³ − 3ps;
  1/α + 1/β = s/p; 1/α² + 1/β² = (s² − 2p)/p²; α/β + β/α = (s² − 2p)/p;
  α⁴ + β⁴ = (s² − 2p)² − 2p². Note that (α − β)² = s² − 4p equals D/a², so a
  question about the **difference** of the roots is a discriminant question.
- **Source:** standard algebraic identities; SM Ch 2 — reference_only.
- **Used in:** q-f3c2-028, q-f3c2-033 to q-f3c2-036, cs-f3c2-02-c; notes §14
  (all six `formula` lines, the D/a² observation and the worked note) and worked
  example 6.
- **Spot-checked by:** _(blank until a human checks)_

## Equations reducible to quadratic form, and extraneous roots

- **Results relied on:** ax⁴ + bx² + c = 0 reduces under y = x², each positive
  value of y yielding two values of x and each negative value yielding none that
  are real. An equation in which a single expression repeats reduces under a
  substitution for that expression. An equation of the form
  a(x + 1/x)² + b(x + 1/x) + c = 0 reduces under y = x + 1/x, and solving
  x + 1/x = y means solving x² − yx + 1 = 0, whose roots are always reciprocals.
  **Squaring both sides of an equation is not reversible:** it can introduce
  roots that satisfy the squared equation but not the original, and every
  candidate must therefore be tested in the **original** equation, the failures
  being discarded as **extraneous roots**.
- **Source:** standard; SM Ch 2 — reference_only.
- **Used in:** q-f3c2-037, q-f3c2-038, q-f3c2-039, q-f3c2-040; notes §15 (all
  four families, both worked notes and the "mistake" callout) and worked
  example 7.
- **Spot-checked by:** _(blank until a human checks)_ — see the convention entry
  on **how an extraneous root is reported** at the foot of this file.

## Cubic equations solved by locating one rational root

- **Result relied on:** any rational root p/q of a polynomial equation with
  integer coefficients has p a factor of the constant term and q a factor of the
  leading coefficient (the rational root theorem, used at Foundation level only
  as a rule for choosing trial values). Once a root r is found, (x − r) is a
  factor; dividing it out leaves a quadratic, which is then solved by the
  ordinary methods.
- **Source:** standard; SM Ch 2 — reference_only.
- **Used in:** q-f3c2-041, q-f3c2-042, q-f3c2-043; notes §16 (the three-step
  method, the division note, the cubic relations and the pointer callout) and
  worked example 8.
- **Spot-checked by:** _(blank until a human checks)_ — confirm the SM expects
  students to divide by **long division** rather than by matching coefficients;
  §16 teaches coefficient-matching as the quicker route and mentions long
  division only in passing.

## Business applications

- **Results relied on:** with a fixed cost F, a variable cost v per unit and a
  selling price p per unit — total cost = F + vx, total revenue = px, profit =
  (p − v)x − F, contribution per unit = p − v, break-even quantity =
  F ÷ (p − v), and the quantity for a target profit T = (F + T) ÷ (p − v). Two
  cost structures are compared by setting their total-cost expressions equal
  (the indifference or cost-equivalence output). **Market equilibrium** is the
  price at which quantity demanded equals quantity supplied. A **blend** of two
  grades is solved by one quantity equation and one value equation. **Work
  rates add:** 1/a + 1/b = 1/t. A **two-digit number** with tens digit t and
  units digit u is 10t + u, its reversal is 10u + t and the difference is
  9(t − u). In an **age** problem the same number of years is added to or
  subtracted from every person's age.
- **Source:** standard business-mathematics formulations; SM Ch 2 applications —
  reference_only. The cost-volume-profit relations are also the ones taught in
  Costing, and are used here in exactly that form.
- **Used in:** q-f3c2-044 to q-f3c2-050, cs-f3c2-01-a to cs-f3c2-01-d,
  cs-f3c2-02-a, cs-f3c2-03-a, cs-f3c2-03-b; notes §17 (all six application
  families and both `formula` blocks) and worked examples 1, 9 and 10.
- **Spot-checked by:** _(blank until a human checks)_

## Negative marking

- **Position relied on:** Paper 3 is wholly objective and carries negative
  marking of **0.25 mark for each wrong answer**, with 1 mark for a correct
  answer and 0 for an unattempted one. The expected-value arithmetic in §18
  follows directly from those numbers.
- **Source:** `foundationScoring` in `src/data/foundation.js`, which the quiz
  engine also reads; ICAI's stated pattern for Papers 3 and 4.
- **Used in:** notes §18 and the last line of the one-page summary.
- **Spot-checked by:** _(blank until a human checks)_ — confirm the 0.25
  deduction is still the announced pattern for the Sept 2026 and Jan 2027
  attempts before the draft badge comes off.

---

# Reviewer's checklist — conventions chosen where practice varies

These are editorial calls, not sourced positions. Each one changes what a
student is taught, and each needs a human to confirm it against the SM.

1. **Are complex roots examinable at Foundation?** The chapter says that when
   D < 0 the roots are "not real" and are "a conjugate pair of imaginary
   numbers", and it stops there — no arithmetic with i, no modulus, no
   conjugate-pair manipulation. q-f3c2-022 tests only the classification. If
   the SM's Ch 2 develops complex roots further, the §11 table and the summary
   should say so; if the SM avoids the word "imaginary" entirely, the phrase
   should be trimmed back to "no real roots". Nothing in the bank depends on
   which way this goes.

2. **Does "roots are real and equal" count as one root or two?** The chapter
   treats D = 0 as **two roots that happen to be equal**, consistent with the
   degree-n-means-n-roots statement in §2. The §2 "mistake" callout and
   q-f3c2-021 both rest on it, and q-f3c2-024's answer (m = 8 **or** −8) rests
   on the related point that the equal-roots *condition* can itself have two
   solutions. If the SM says a D = 0 equation "has one root", §2, §11 and the
   q-f3c2-021 explanations all need rewording — though the keys do not change.

3. **How is an extraneous root reported?** In q-f3c2-038 and worked example 7
   the chapter states the surviving root only, and names the discarded value an
   "extraneous root" produced by the squaring. The alternative convention —
   listing both and marking one "rejected" — would change the wording of the
   q-f3c2-038 options but not the key. Confirm which the SM uses, since students
   match option wording literally.

4. **Is a negative root rejected by default?** The chapter rejects a negative
   root only when the situation forbids it (a count of boxes in worked example
   5, an age, a digit), and §17's "mistake" callout warns expressly against
   reflexive rejection. q-f3c2-015, q-f3c2-019 and q-f3c2-027 all have a
   legitimate negative root among their answers. Confirm the SM does not teach
   a blanket "reject the negative root" rule for business questions.

5. **Rounding of break-even quantities.** Worked example 1(c) computes
   2,666.67 exactly and then rounds **up** to 2,667, on the reasoning that
   2,666 units still leave a loss. Every bank question is built so the exact
   answer is a whole number, so no key depends on this; but the rounding
   *direction* taught in the notes should match the SM's own worked patterns.
   The verifier's `break_even()` returns an exact `Fraction` and never rounds.

6. **Section count and length.** The notes run to 18 numbered sections and about
   1,180 lines, with 10 worked examples. §13's derived-root table and §14's
   α⁴ + β⁴ identity are the two places most likely to exceed the SM's depth;
   both can be cut without touching a bank question.

7. **The cross-multiplication print form.** See the note under that heading
   above — confirm the subscript order matches the SM's printed rule.

