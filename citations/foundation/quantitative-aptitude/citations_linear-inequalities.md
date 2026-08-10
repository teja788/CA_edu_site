# Citations — Foundation P3 Ch 3 · Linear Inequalities

Generated 10 Aug 2026 in the same session as the chapter content. This chapter
rests on the ICAI Foundation Study Material's Paper 3, Ch 3 treatment of linear
inequalities, read together with the standard results of elementary algebra
(the order properties of the real numbers and the half-plane test). **No bare
Act exists for mathematics**, so this file cannot follow the usual pattern of
quoting a statutory line. What it records instead is: the SM scope relied on,
each standard result used and its conventional statement, and — most
importantly for a reviewer — every place where classroom practice varies and a
convention had to be chosen.

The Study Material is ICAI-copyrighted and was used `reference_only`: read to
confirm the scope and the depth expected at Foundation, never copied. Every
scenario, every number and every question in this chapter is original. Where
the SM's own worked patterns and the standard algebraic result agree (as they
do throughout), the position is recorded once, below.

**Frontmatter note.** The chapter frontmatter carries
`applicable_attempts: ['Sept 2026','Jan 2027']` but deliberately **omits**
`law_as_on_date`. Mathematics states no legal position, so there is no cut-off
date for a Finance Act or notification to be pinned to; the attempt tags remain
because the SM edition and the syllabus weighting can change between attempts.
`scripts/attempt_lint/` requires `law_as_on_date` only for the volatile
law/tax/audit papers, so its omission here is correct and not an oversight.

A reviewer spot-checking this file should confirm each row against ICAI SM
Paper 3, Ch 3 (May 2026 ed.), settle the four convention questions flagged at
the end, and initial the "Spot-checked by" lines.

## Scope of the chapter as taught

- **Position relied on (paraphrase, not quoted):** the Foundation treatment of
  linear inequalities covers the meaning of an inequality and how it differs
  from an equation; the rules of operation, including the reversal of the sign
  on multiplication or division by a negative quantity; the solution of a
  linear inequality in one variable and its presentation as a set, on a number
  line and in interval notation; double inequalities; systems of linear
  inequalities in one variable; the graph of a linear inequality in two
  variables, with the boundary line drawn solid or dashed and the correct
  half-plane shaded; systems of such inequalities and the resulting common or
  feasible region; bounded and unbounded regions; corner points; the
  non-negativity conditions; and the formulation of business constraints as
  inequalities. Optimisation over the feasible region — the objective function,
  the corner-point theorem and the simplex method — is **outside** the chapter
  and is not taught here.
- **Source:** ICAI Foundation SM Paper 3, Ch 3 (Linear Inequalities), May 2026
  edition — reference_only.
- **Used in:** notes §1 to §18 (the whole chapter's scope decision, including
  the decision to stop at the corner points and not evaluate an objective
  function).
- **Spot-checked by:** _(blank until a human checks)_

## Order properties: the four rules of operation

- **Position relied on (paraphrase):** for real numbers, (i) if `a < b` then
  `a + c < b + c` for every real *c*, so adding or subtracting the same
  quantity on both sides leaves the direction unchanged; (ii) if `a < b` and
  `c > 0` then `ac < bc`, so multiplying or dividing by a positive quantity
  leaves the direction unchanged; (iii) if `a < b` and `c < 0` then `ac > bc`,
  so multiplying or dividing by a negative quantity **reverses** the direction;
  (iv) if `a < b` and `c < d` then `a + c < b + d`, so two inequalities of the
  same direction may be added. Subtracting two inequalities of the same
  direction, and multiplying two inequalities whose terms are not known to be
  positive, are **not** valid operations. Taking reciprocals of both sides
  reverses the direction when both sides carry the same sign.
- **Source:** standard order axioms of the ordered field of real numbers, as
  presented for Foundation in SM Ch 3 — reference_only.
- **Used in:** q-f3c3-005, q-f3c3-006, q-f3c3-007, q-f3c3-008, q-f3c3-009,
  q-f3c3-010, q-f3c3-011, q-f3c3-012; notes §3 (all four rules and the
  operations table) and §4 in full.
- **Spot-checked by:** _(blank until a human checks)_

## Strict and non-strict signs, and the words that produce them

- **Position relied on (paraphrase):** `<` and `>` are strict and exclude the
  boundary value; `≤` and `≥` are non-strict and include it. In the standard
  business vocabulary, "at most", "not more than", "maximum of", "up to",
  "cannot exceed" and a stated availability of a resource all give `≤`; "at
  least", "not less than", "minimum of" and a stated requirement give `≥`;
  "less than", "below" and "under" give `<`; "more than", "exceeds" and "above"
  give `>`. A double inequality such as `a ≤ x < b` is the conjunction of its
  two halves, never a disjunction.
- **Source:** SM Ch 3, May 2026 ed., and the ordinary usage of the terms in
  ICAI-style formulation problems — reference_only.
- **Used in:** q-f3c3-003, q-f3c3-004, q-f3c3-018, q-f3c3-019, q-f3c3-029,
  q-f3c3-031, q-f3c3-035, q-f3c3-039, q-f3c3-040; notes §2 (the symbol table)
  and §9 (the translation table).
- **Spot-checked by:** _(blank until a human checks)_

## Presentation of a one-variable solution set

- **Position relied on (paraphrase):** a solution set may be written in
  set-builder form with its universe stated, drawn on a number line with an
  open circle at an excluded endpoint and a solid circle at an included one, or
  written in interval notation with a round bracket for an excluded endpoint
  and a square bracket for an included one. Infinity always takes a round
  bracket. The universe matters: over the natural numbers, the whole numbers,
  the integers and the reals the same inequality has four different solution
  sets, and the stem must state which universe applies.
- **Source:** SM Ch 3, May 2026 ed. — reference_only.
- **Used in:** q-f3c3-020, q-f3c3-021, q-f3c3-022, q-f3c3-023, q-f3c3-024,
  q-f3c3-028, q-f3c3-033; notes §6 (all three forms, the conversion table and
  the paragraph on the universe).
- **Spot-checked by:** _(blank until a human checks)_

## Systems in one variable: intersection, not union

- **Position relied on (paraphrase):** a system of linear inequalities in one
  variable is solved by solving each inequality separately and taking the
  intersection of the solution sets. Where the same endpoint is reached by a
  strict and a non-strict condition, the strict condition governs, because a
  value must satisfy every inequality of the system. Where one range lies
  wholly inside another, the tighter range is the answer and the other
  condition is redundant. Where the ranges do not meet, the solution set is
  empty.
- **Source:** SM Ch 3, May 2026 ed. — reference_only.
- **Used in:** q-f3c3-030, q-f3c3-031, q-f3c3-032, q-f3c3-033, q-f3c3-034;
  notes §8 (the overlap table and the three outcomes).
- **Spot-checked by:** _(blank until a human checks)_

## The half-plane and the test-point method

- **Position relied on (paraphrase):** a linear inequality in two variables is
  graphed by replacing the sign with `=`, plotting the boundary line (most
  quickly by its two intercepts), drawing that line **solid** if the sign is
  `≤` or `≥` and **dashed** if it is `<` or `>`, and then shading the half-plane
  that contains a test point which satisfies the inequality. `(0, 0)` is the
  standard test point and may be used whenever the boundary does not pass
  through the origin; where it does, any other point off the line serves. If
  the substitution is true, the region containing the test point is shaded; if
  false, the other region is.
- **Source:** SM Ch 3, May 2026 ed.; standard result that a line divides the
  plane into two half-planes on which a linear expression keeps a constant sign
  — reference_only.
- **Used in:** q-f3c3-040, q-f3c3-041, q-f3c3-042, q-f3c3-043, q-f3c3-044,
  cs-f3c3-03-a; notes §10 and §11 (the construction tables, the solid/dashed
  rule and the two test-point failures).
- **Spot-checked by:** _(blank until a human checks)_

## Feasible region, corner points, boundedness

- **Position relied on (paraphrase):** the feasible (common) region of a system
  of linear inequalities in two variables is the intersection of the
  half-planes, that is the set of points satisfying every inequality at once. A
  corner point (vertex, extreme point) is the intersection of two boundary
  lines of the region **which also satisfies every constraint**; intersections
  that fail any constraint are discarded, so an intercept is not automatically
  a corner. The region is bounded if it can be enclosed within a circle of
  finite radius and unbounded otherwise; an unbounded region is not an empty
  one, and a region is empty only when the half-planes do not overlap at all.
- **Source:** SM Ch 3, May 2026 ed. — reference_only.
- **Used in:** q-f3c3-045, q-f3c3-046, q-f3c3-048, q-f3c3-049, q-f3c3-050,
  q-f3c3-051, q-f3c3-052, cs-f3c3-01-b, cs-f3c3-01-d, cs-f3c3-02-a,
  cs-f3c3-02-b, cs-f3c3-02-c, cs-f3c3-03-b, cs-f3c3-03-c; notes §12, §14, §15
  and §16 (including the pair-and-filter tables and the direction-walk test for
  boundedness).
- **Spot-checked by:** _(blank until a human checks)_

## Non-negativity, and the constraint families

- **Position relied on (paraphrase):** business formulations carry `x ≥ 0` and
  `y ≥ 0` because the variables count physical or monetary quantities that
  cannot be negative; the two conditions confine the region to the first
  quadrant and frequently supply corner points where a resource line meets an
  axis. The recurring constraint families are machine or labour hours, raw
  material or component stock, budget or investment ceilings, blending, diet or
  quality minimums, and transport or storage capacity; the first, third and
  fifth are `≤` families, the fourth is a `≥` family, and market or contract
  limits on a single product give a vertical or horizontal line. A constraint
  comparing two variables passes through the origin and needs a test point
  elsewhere.
- **Source:** SM Ch 3, May 2026 ed., and the standard formulation vocabulary of
  ICAI-style application problems — reference_only.
- **Used in:** q-f3c3-035, q-f3c3-036, q-f3c3-037, q-f3c3-038, q-f3c3-039,
  q-f3c3-047, cs-f3c3-01-a, cs-f3c3-03-a; notes §9, §13 and §17.
- **Spot-checked by:** _(blank until a human checks)_

## Negative marking on Paper 3

- **Position relied on (paraphrase):** Paper 3 is wholly objective, a correct
  answer carries 1 mark and a wrong answer attracts a deduction of 0.25 marks,
  while an unattempted question carries nothing. The expected-value arithmetic
  in §18 (0.25 marks per blind four-way guess, about 0.33 with one option
  eliminated, 0.5 with two) is elementary probability computed from those two
  figures, not a position taken from any ICAI text.
- **Source:** `foundationScoring` in `src/data/foundation.js` (correct 1, wrong
  −0.25, skipped 0, applied to `quantitative-aptitude` and
  `business-economics`); ICAI Foundation exam pattern for Papers 3 and 4.
- **Used in:** notes §18 and the last line of the one-page summary.
- **Spot-checked by:** _(blank until a human checks)_

## Conventions chosen where practice varies — THE REVIEWER'S CHECKLIST

These four are the residue a machine cannot settle. Each is a defensible
choice, each affects answer keys, and each should be confirmed against the SM
before the draft badge comes off.

1. **The feasible region INCLUDES its boundary when the constraints are
   non-strict.** Throughout this chapter, `≤` and `≥` constraints are drawn
   solid and their boundary points, including the corner points sitting on
   them, are treated as feasible. Every corner-point answer in the bank depends
   on this — q-f3c3-050 (30, 20), q-f3c3-051, q-f3c3-052, cs-f3c3-01-b (25, 20),
   cs-f3c3-02-b (12, 6) and cs-f3c3-03-b (500, 300) all lie exactly on two
   boundary lines. This is the universal convention and no variation is
   expected, but §10's remark that a strict system's vertices are *not*
   attainable, and q-f3c3-040 option D, are the two places where the chapter
   states the consequence explicitly. Confirm the SM says the same.

2. **Integer-only solutions are NOT imposed unless the question asks for a
   whole number.** Corner points are reported as exact rationals, so
   q-f3c3-051 and worked example 6 give `(16/3, 20/3)` and the notes insist it
   is not rounded to `(5.33, 6.67)`. Worked example 4 raises the point that
   machines come in whole numbers and calls the practical answers the lattice
   points of the region, and §15 and the common-mistakes list both flag it, but
   no question is keyed to an integer-rounded vertex. Where a whole-number
   answer IS required the stem says so in terms — q-f3c3-018 ("least whole
   number of units"), q-f3c3-019, q-f3c3-022, q-f3c3-024, q-f3c3-028 and
   q-f3c3-033. If the SM instead expects a production problem's corner points
   to be rounded to feasible integer plans, q-f3c3-051 option D and worked
   example 6 need rewording, although the keys themselves would not move.

3. **An unbounded feasible region is described as UNBOUNDED, never as "no
   solution".** q-f3c3-048, q-f3c3-049 and cs-f3c3-02-a all turn on the
   distinction between an unbounded region (infinitely many feasible points, no
   outer edge) and an empty one (no feasible point at all), and each offers the
   confusion as a named distractor. Because this chapter stops short of
   optimisation, no question asks for a maximum over an unbounded region, where
   "no finite optimum exists" would be the correct phrasing. If the SM's own
   wording for an unbounded case differs, the option text in those three
   questions should follow it.

4. **A stated fund or resource may be left partly unused unless the wording
   compels its full use.** cs-f3c3-03 and worked example 8 read "has ₹ 8,00,000
   available... need not place the whole sum" as `x + y ≤ 800`, which keeps
   `(0, 0)` and `(800, 0)` as corner points; q-f3c3-035 makes the same choice
   for a budget sanction and offers the equality as a named distractor.
   Worked example 8 spells out what changes if the whole sum must be placed:
   the region collapses to a segment and one vertex disappears. A reviewer
   should confirm that the SM's investment problems are set up as `≤` rather
   than `=`, because if they use an equality the corner-point sets in
   cs-f3c3-03-c and worked example 8 both change.

- **Spot-checked by:** _(blank until a human checks)_

## Machine verification already performed

All 47 numerical questions in this bank are recomputed from their stems by
`scripts/verify_numerical/verify_linear-inequalities.py` and pass. The verifier
does not hard-code any key: one-variable inequalities are reduced to
`a·x SENSE b` and solved by a routine that applies the sign reversal itself;
corner points are found by intersecting **every** pair of boundary lines and
filtering the results by feasibility; boundedness is decided from the recession
cone rather than from the pattern of constraint signs; and translation
questions are checked by testing candidate constraints against the sentence
itself over a lattice. All coordinate arithmetic uses `fractions.Fraction`, so
`(16/3, 20/3)` is exact. A reviewer therefore need not re-check arithmetic —
only the four conventions above and the wording of the non-numerical questions.
