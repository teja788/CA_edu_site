# Citations — Foundation P3 Ch 5 · Basic Concepts of Permutations and Combinations

Generated 10 Aug 2026 in the same session as the chapter content.

**There is no bare Act behind this chapter.** Mathematics has no statutory
source, so nothing here can be checked against India Code the way a Business
Laws chapter can. What this file records instead is (i) the **ICAI Study
Material scope** the chapter was written to, (ii) every **standard counting
result** relied on, stated in its conventional form so a reviewer can check the
statement rather than hunt for a source, and (iii) the **editorial conventions**
chosen at points where textbook practice genuinely varies. Section (iii) is the
reviewer's real checklist: each of those calls silently changes an answer key.

**Note on `law_as_on_date`.** The chapter's frontmatter deliberately **omits**
`law_as_on_date`. That field pins content to a cut-off date for a legal or
fiscal position, and this chapter states none — the number of ways of seating
eight people at a round table does not move with a Finance Act.
`applicable_attempts` is present, because the SM edition and the examinable
scope can change between attempts.

The ICAI Study Material was used `reference_only` — read to confirm that the
scope and the level of treatment match, and cited by chapter number only. No SM
prose, no SM worked example and no SM question wording was reproduced. Every
number, scenario and name in the chapter and the bank is original.

A reviewer spot-checking this file should confirm each entry against **ICAI
Foundation SM Paper 3, Ch 5 (Basic Concepts of Permutations and Combinations),
May 2026 edition** and initial the "Spot-checked by" line.

## Scope relied on

- **Position relied on (paraphrase, not quoted):** the chapter covers the
  fundamental principle of counting in its multiplication and addition forms;
  factorial notation and its elementary properties, including the value of 0!;
  permutations, the derivation of nPr, permutations of n distinct objects taken
  all at a time, permutations with repetition allowed, permutations of objects
  that are not all distinct, and permutations under the standard restrictions
  (particular objects together, never together, or in fixed places); circular
  permutations, including the necklace and garland case; combinations, the
  derivation of nCr, the relation nPr = nCr × r!, and the properties
  nC0 = nCn = 1, nCr = nC(n − r) and nCr + nC(r − 1) = (n + 1)Cr; combinations
  under restrictions; the number of ways of selecting one or more items from a
  group; the division of objects into groups of equal and of unequal size; and
  applications to committee formation, seating, word formation, handshakes and
  the diagonals of a polygon.
- **Source:** ICAI Foundation SM Paper 3, Ch 5, May 2026 edition —
  reference_only.
- **Used in:** the whole chapter; the section numbering of the notes follows
  this scope order.
- **Spot-checked by:** _(blank until a human checks)_

## The fundamental principle of counting

- **Result relied on, in its conventional statement:** if one operation can be
  performed in m ways and, after it has been performed, a second operation can
  be performed in n ways, then the two operations in succession can be performed
  in m × n ways (the multiplication rule). If an operation can be performed in
  m ways or, alternatively, in n ways, and the two sets of ways have no member
  in common, then the operation can be performed in m + n ways (the addition
  rule). The addition rule requires the alternatives to be mutually exclusive;
  where they overlap, the overlap is subtracted once.
- **Source:** standard elementary combinatorics; SM Ch 5 introductory treatment
  — reference_only.
- **Used in:** q-f3c5-001 to q-f3c5-005; notes §1 and §2, including the
  AND/OR decision table and the worked note on three-digit numbers.
- **Spot-checked by:** _(blank until a human checks)_ — **confirm the SM states
  the addition rule with the mutual-exclusion condition attached.** Some
  presentations state it without the condition and handle overlaps only later.
  q-f3c5-004 depends on the condition being taught.

## Factorial notation and the value of 0!

- **Result relied on:** for a whole number n ≥ 1, n! = n × (n − 1) × … × 2 × 1;
  n! = n × (n − 1)!; and 0! = 1. The last is fixed by the recursion at n = 1,
  which gives 1! = 1 × 0!. Factorials are defined for whole numbers n ≥ 0 only,
  and do not distribute over addition or multiplication.
- **Source:** standard; SM Ch 5 — reference_only.
- **Used in:** q-f3c5-006 to q-f3c5-010; notes §3 and the §5 note that nPn = n!
  requires 0! = 1.
- **Spot-checked by:** _(blank until a human checks)_

## Permutations and the formula nPr

- **Result relied on, in the conventional statement:** the number of
  permutations of n distinct objects taken r at a time, no object being used
  more than once, is

  > nPr = n × (n − 1) × (n − 2) × … × (n − r + 1), a product of exactly r
  > factors, which equals n! ÷ (n − r)! for 0 ≤ r ≤ n.

  Special cases: nPn = n!, nP1 = n, nP0 = 1. The derivation used in the notes is
  the multiplication rule applied to r positions in succession.
- **Source:** standard; SM Ch 5 derives the same result the same way —
  reference_only.
- **Used in:** q-f3c5-011 to q-f3c5-014, cs-f3c5-01-b, cs-f3c5-01-d; notes §4
  and §5 including the derivation and both `formula` lines.
- **Spot-checked by:** _(blank until a human checks)_

## Permutations when repetition is allowed

- **Result relied on:** the number of arrangements of r positions filled from n
  objects, each object being usable any number of times, is n<sup>r</sup>. The
  exponent is the number of positions to be filled; the base is the number of
  objects available. Where an object must be assigned to exactly one of several
  containers, the objects supply the exponent and the containers the base.
- **Source:** standard; SM Ch 5 — reference_only.
- **Used in:** q-f3c5-016 to q-f3c5-019, cs-f3c5-01-a, cs-f3c5-01-c; notes §6.
- **Spot-checked by:** _(blank until a human checks)_ — confirm the SM treats
  the "letters into pillar boxes" family, which is the only place the base and
  the exponent are easy to swap. q-f3c5-017 rests on it.

## Permutations of objects that are not all distinct

- **Result relied on, in the conventional statement:** if n objects consist of p
  alike of one kind, q alike of a second kind, r alike of a third kind and the
  rest all different, the number of distinct arrangements of all n is

  > n! ÷ (p! × q! × r!).

  A block of identical objects tied together contributes no internal factor,
  because permuting identical objects within the block gives the same block.
- **Source:** standard; SM Ch 5 — reference_only.
- **Used in:** q-f3c5-020 to q-f3c5-023; notes §7, including the derivation by
  division of the over-count and the "mistake" callout on internal factors.
- **Spot-checked by:** _(blank until a human checks)_

## Permutations under restrictions

- **Results relied on:** for n distinct objects in a row —
  (i) r particular objects always together: tie them into one block, giving
  (n − r + 1)! × r! arrangements;
  (ii) those r objects never all together: total − together, that is
  n! − (n − r + 1)! × r!;
  (iii) no two of a set of k objects adjacent: arrange the other n − k objects
  first in (n − k)! ways, creating n − k + 1 gaps, and place the k restricted
  objects into k of those gaps in (n − k + 1)Pk ways;
  (iv) a particular object in a stated position: fix it and arrange the rest.
- **Source:** standard; SM Ch 5 — reference_only.
- **Used in:** q-f3c5-024 to q-f3c5-028, q-f3c5-034; notes §8 and worked
  examples 3 and 9.
- **Spot-checked by:** _(blank until a human checks)_ — **confirm the SM's
  reading of "never together" for three or more objects.** See checklist item 5.

## Circular permutations

- **Result relied on:** the number of circular arrangements of n distinct
  objects is (n − 1)!, because a rotation of the whole circle leaves the
  arrangement unchanged and each arrangement is therefore counted n times among
  the n! linear orders. The number of circular arrangements of r objects chosen
  from n distinct objects is nPr ÷ r. Restrictions are handled by the same block
  and gap devices as in a row, applied to the reduced object count, and n objects
  seated in a circle create exactly n gaps.
- **Source:** standard; SM Ch 5 — reference_only.
- **Used in:** q-f3c5-029 to q-f3c5-031, q-f3c5-034; notes §9 and worked
  examples 3, 4 and 10.
- **Spot-checked by:** _(blank until a human checks)_

## Necklaces and garlands

- **Result relied on:** where the circular arrangement can be turned over, so
  that the clockwise and anticlockwise readings describe the same physical
  object, the circular count is halved: the number of distinct necklaces or
  garlands from n distinct beads or flowers is (n − 1)! ÷ 2.
- **Source:** standard; SM Ch 5 — reference_only.
- **Used in:** q-f3c5-032, q-f3c5-033; notes §10 including the table of which
  situations halve, and worked example 4.
- **Spot-checked by:** _(blank until a human checks)_ — see checklist item 1,
  which is the single most consequential convention in this chapter.

## Combinations and the formula nCr

- **Result relied on, in the conventional statement:** the number of
  combinations of n distinct objects taken r at a time, order being
  disregarded, is

  > nCr = nPr ÷ r! = n! ÷ [ r! × (n − r)! ], for 0 ≤ r ≤ n.

  The derivation used in the notes is that each selection of r objects can be
  arranged in r! ways, so the nPr arrangements fall into groups of r!, one group
  per selection.
- **Source:** standard; SM Ch 5 derives it the same way — reference_only.
- **Used in:** q-f3c5-015, q-f3c5-035, q-f3c5-036, q-f3c5-040, cs-f3c5-02-a;
  notes §11 and §12, and worked examples 5 and 10.
- **Spot-checked by:** _(blank until a human checks)_

## Properties of nCr

- **Results relied on:** nC0 = nCn = 1; nC1 = n; the symmetry
  nCr = nC(n − r); Pascal's rule nCr + nC(r − 1) = (n + 1)Cr; the row total
  nC0 + nC1 + … + nCn = 2ⁿ; and the equality rule, that nCx = nCy implies
  x = y or x + y = n. The notes justify the symmetry by the equivalence of
  choosing what to take and choosing what to leave, and Pascal's rule by a case
  split on whether one particular object is in the selection.
- **Source:** standard; SM Ch 5 — reference_only.
- **Used in:** q-f3c5-037 to q-f3c5-039, q-f3c5-044; notes §13 and the
  one-page summary.
- **Spot-checked by:** _(blank until a human checks)_ — **confirm the SM states
  the equality rule with both branches.** q-f3c5-038's key (4 or 11) depends on
  the second branch being examinable; if the SM gives only x = y, the question
  should be reworded rather than re-keyed.

## Combinations under restrictions

- **Results relied on:** selections of r from n that always include a particular
  object number (n − 1)C(r − 1); those that always exclude it number
  (n − 1)Cr; and the two add to nCr, which is Pascal's rule. Where a selection
  must draw a stated number from each of two groups, the within-group counts
  multiply. A requirement of the form "at least k" is resolved by splitting into
  mutually exclusive cases and adding, or equivalently by subtracting the
  complementary cases from the unrestricted total. Reserving a fixed core and
  filling the balance from the combined pool is **not** valid, because it counts
  the same selection once for each way of nominating the core.
- **Source:** standard; SM Ch 5 — reference_only.
- **Used in:** q-f3c5-041 to q-f3c5-043, cs-f3c5-02-b, cs-f3c5-02-c; notes §14,
  the "mistake" callout on the reserved core, and worked examples 5 and 10.
- **Spot-checked by:** _(blank until a human checks)_

## Selecting one or more items

- **Results relied on:** the number of ways of selecting one or more items from
  n distinct items is 2ⁿ − 1, since each item is independently in or out and the
  single empty selection is excluded. Where the group contains p alike of one
  kind, q alike of another and r distinct items, the number of ways of selecting
  one or more is (p + 1) × (q + 1) × 2ʳ − 1, because an identical set offers
  only a quantity decision with p + 1 outcomes. From n identical items alone the
  count is n.
- **Source:** standard; SM Ch 5 — reference_only.
- **Used in:** q-f3c5-044, q-f3c5-045; notes §15 and worked example 7.
- **Spot-checked by:** _(blank until a human checks)_ — see checklist item 2.

## Division of objects into groups

- **Results relied on:** m + n distinct objects can be divided into two groups
  of m and n, with m ≠ n, in (m + n)! ÷ (m! × n!) ways. 2n distinct objects can
  be divided into two groups of n each, the groups being unlabelled, in
  (2n)! ÷ (n! × n! × 2!) ways. In general, kn distinct objects divided into k
  unlabelled groups of n each give (kn)! ÷ [ (n!)ᵏ × k! ], and if the groups are
  labelled — sent to named places, or given different work — the divisor k! is
  omitted, which is the same as multiplying the unlabelled count by k!. Groups
  of unequal size are self-identifying and take no such divisor.
- **Source:** standard; SM Ch 5 — reference_only.
- **Used in:** q-f3c5-046, q-f3c5-047, cs-f3c5-03-a to cs-f3c5-03-c; notes §16
  and worked example 6.
- **Spot-checked by:** _(blank until a human checks)_ — see checklist item 4.
  This is the family in which a single word in the stem moves the key.

## Applications: handshakes, points, diagonals and word formation

- **Results relied on:** the number of handshakes when each of n people shakes
  hands with every other exactly once is nC2 = n(n − 1) ÷ 2, because a handshake
  is an unordered pair; an exchange that is directional, such as a greeting card
  or a one-way journey, is nP2 instead. From n points in a plane with no three
  collinear, the number of straight lines is nC2 and the number of triangles is
  nC3; if k of the points are collinear, the line count becomes
  nC2 − kC2 + 1 and the triangle count becomes nC3 − kC3. A convex polygon of n
  sides has nC2 − n = n(n − 3) ÷ 2 diagonals. In word-formation questions,
  "word" means any arrangement of the letters whether or not it is meaningful,
  unless the question says otherwise.
- **Source:** standard; SM Ch 5 applications — reference_only.
- **Used in:** q-f3c5-048 to q-f3c5-050; notes §17 and worked examples 2, 8
  and 9.
- **Spot-checked by:** _(blank until a human checks)_ — **confirm the collinear
  correction for LINES is stated as "− kC2 + 1".** Some presentations state only
  the triangle correction. q-f3c5-050 uses the line count 40 as a distractor and
  worked example 8 states the rule, so the reviewer should confirm the SM
  teaches it before a student meets it as a wrong option.

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

These are editorial calls, not sourced positions. Each one changes an answer
key or the wording a student matches against, and each needs a human to confirm
it against the SM.

1. **Is a garland treated as identical under reflection?** The chapter says yes:
   a necklace, garland, bangle or key ring can be turned over, so the clockwise
   and anticlockwise readings are one object and the count is (n − 1)! ÷ 2. A
   round table, a meeting and a fixed circle of seats are **not** halved. Two
   keys depend on it — q-f3c5-032 (necklace of 7 beads, 360) and q-f3c5-033
   (garland of 9 flowers, 20,160) — and in both the unhalved value is offered as
   a distractor, so if the SM does not halve garlands the keys move to those
   options. q-f3c5-029 (round table, 120) offers the halved value 60 as its
   distractor, so the same convention is being tested in both directions. The
   §10 table is the place to edit if the SM differs.

2. **Does an "at least one" answer include the empty selection?** The chapter
   says no: "one or more", "at least one" and "some" all exclude taking nothing,
   so 1 is subtracted. q-f3c5-044 (63, not 64) and q-f3c5-045 (79, not 80) both
   rest on it, and in both the un-subtracted value is the distractor. The §15
   "mistake" callout also states the converse — that wording such as "any
   number, including none" does **not** subtract — which is an editorial
   addition and should be checked against how the SM phrases such questions.

3. **Are repeated letters assumed distinct unless stated?** The chapter says the
   opposite: identical letters and identical objects are treated as
   indistinguishable by default, so BALLOON gives 1,260 and not 5,040, and 5
   identical notebooks offer 6 quantity choices and not 2⁵. This is the standard
   convention, but it is worth confirming, because it decides q-f3c5-020,
   q-f3c5-021, q-f3c5-022, q-f3c5-023 and q-f3c5-045 together. The related call
   inside the block method — that a tied block of **identical** objects is not
   multiplied back by its internal factorial, while a block of **distinct**
   objects is — is stated in §7 and tested by q-f3c5-023 against q-f3c5-024.

4. **Are groups of equal size labelled or unlabelled?** The chapter treats a
   group as **unlabelled**, and therefore divides by k!, only when the question
   gives the equal-sized groups no name, destination or distinct work. Named
   branches, named teams and named clients are labelled and take no division.
   Four keys turn on this: q-f3c5-046 (two unnamed groups of 5, 126),
   q-f3c5-047 (three named branches, 1,680), cs-f3c5-03-a (two unnamed groups
   of 4, 35) and cs-f3c5-03-b (the same 8 trainees into two **named** teams,
   70). The last pair is deliberately the same numbers with one word changed, so
   if the SM's convention differs the two keys swap. Confirm also that unequal
   groups take no divisor, which cs-f3c5-03-c (sizes 2, 3, 3 to named clients,
   560) relies on.

5. **What does "never together" mean for three or more objects?** The chapter
   reads "never all together" as the complement of the single block — total
   minus the block count — and reserves the gap method for the stronger "no two
   adjacent". q-f3c5-025 (4,320) offers 1,440, the no-two-adjacent figure, as
   its distractor, and q-f3c5-026 (1,440) offers 720, the all-together figure,
   as its distractor. If the SM reads "never together" as "no two adjacent", the
   two keys change places. This is the most likely single point of disagreement
   between presentations.

6. **The line count when some points are collinear.** §17 and worked example 8
   state that k collinear points among n reduce the line count to
   nC2 − kC2 + 1, adding back the one line they actually make, while the
   triangle count is simply nC3 − kC3. Only the triangle rule carries a key
   (q-f3c5-050, 116); the line rule appears as that question's distractor and in
   the worked example. If the SM does not develop the line case, the worked
   example can be trimmed without touching a key.

7. **Section count and length.** The notes run to 19 numbered sections and about
   1,360 lines, with 10 worked examples. §16's three-or-more-groups formula and
   §17's collinear-point corrections are the two places most likely to exceed
   the SM's depth; both can be cut without touching a bank question.

8. **Verifier method.** `scripts/verify_numerical/verify_permutations-and-combinations.py`
   verifies 49 of the 56 numerical questions by **brute-force enumeration** with
   `itertools` — building the arrangements, selections, circular canonical forms
   and group assignments and counting them — rather than by re-applying the
   formula the stem used. Six use a formula and say why in a comment: the
   service-tag case (cs-f3c5-01-a to -d) runs to millions of tags, and
   q-f3c5-007 and q-f3c5-008 are themselves about factorial identities. One,
   q-f3c5-028, is a hybrid — the restriction is enumerated, the placements are
   counted by formula. A reviewer who changes a convention above should expect
   the verifier to fail, not to agree; that is the intended behaviour.
