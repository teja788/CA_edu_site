# Citations — Foundation P3 Ch 10 · Direction Sense Test

Generated 11 Aug 2026 in the same session as the chapter content.

**There is no bare Act behind this chapter.** Direction sense is a Logical
Reasoning topic built on the conventions of the compass and elementary plane
geometry; it has no statutory source, so nothing here can be checked against
India Code the way a Business Laws chapter can. What this file records instead
is (i) the **ICAI Study Material scope** the chapter was written to, (ii) every
**standard convention and geometric result** relied on, stated in its usual
form so a reviewer can check the statement rather than hunt for a source, and
(iii) the **editorial conventions** chosen at points where practice genuinely
varies. Section (iii) is the reviewer's real checklist: those are the calls a
human must confirm.

**Note on `law_as_on_date`.** The chapter's frontmatter deliberately **omits**
`law_as_on_date`. That field pins content to a cut-off date for a legal or
fiscal position, and this chapter states none — the compass rose and the
Pythagoras theorem do not change with a Finance Act. `applicable_attempts` is
present, because the SM edition and the examinable scope can change between
attempts.

The ICAI Study Material was used `reference_only` — read to confirm that the
scope and the level of treatment match, and cited by topic only. No SM prose, no
SM worked example and no SM question wording was reproduced. Every scenario,
name and set of numbers in the chapter and the bank is original.

A reviewer spot-checking this file should confirm each entry against **ICAI
Foundation SM Paper 3, Part B (Logical Reasoning), Direction Sense Test, May
2026 edition** and initial the "Spot-checked by" line.

## Scope relied on

- **Position relied on (paraphrase, not quoted):** the chapter covers the
  eight-point compass (four cardinal and four ordinal directions); the reading
  of a described walk as a drawn path; the distinction between the total
  distance walked and the net displacement (shortest distance from the start);
  the computation of that shortest distance by the Pythagoras theorem; turns
  measured as left or right, and as clockwise or anticlockwise, relative to the
  walker's current facing; the effect of turns given in degrees; the position of
  the sun through the day and the direction of shadows; relative-direction
  clues, opposite-direction movement, and mirror reflection; and the negative
  marking pattern of Paper 3.
- **Source:** ICAI Foundation SM Paper 3, Part B Logical Reasoning, Direction
  Sense Test, May 2026 edition — reference_only.
- **Used in:** the whole chapter; the section numbering of the notes follows
  this scope order.
- **Spot-checked by:** _(blank until a human checks)_

## The compass and the eight directions

- **Convention relied on:** the four cardinal directions are North, East, South
  and West, adjacent cardinals being 90° apart around a 360° circle; the four
  ordinal (intercardinal) directions — North-East, South-East, South-West,
  North-West — lie exactly midway between their neighbours, 45° from each. The
  opposite of any direction is 180° away and is found by reversing both letters
  (NE ↔ SW, NW ↔ SE). When a person faces a given direction, the right hand
  points 90° clockwise from the facing and the left hand 90° anticlockwise.
- **Source:** standard eight-point compass rose; SM Ch on Direction Sense —
  reference_only.
- **Used in:** q-f3c10-001, q-f3c10-002, q-f3c10-003, q-f3c10-004; notes §1.
- **Spot-checked by:** _(blank until a human checks)_

## Drawing the path and the coordinate convention

- **Convention relied on:** a described walk is drawn with North up the page,
  East to the right, South down and West to the left; equivalently, on a grid
  with the start at the origin, East increases the x-coordinate and West
  decreases it, while North increases the y-coordinate and South decreases it.
  Moves along the same line (two North–South moves, or two East–West moves)
  combine by addition and subtraction before any triangle is formed.
- **Source:** standard map/graph orientation; SM Direction Sense treatment —
  reference_only.
- **Used in:** q-f3c10-013, q-f3c10-025, q-f3c10-026; notes §2 and the verifier's
  `Walk` grid (`scripts/verify_numerical/verify_direction-sense-test.py`).
- **Spot-checked by:** _(blank until a human checks)_ — confirm the SM draws the
  same orientation (North up); a minority of texts orient differently, and every
  relative-direction answer depends on this choice.

## Net displacement and the Pythagoras theorem

- **Result relied on:** for a walk whose net East–West gap is x and whose net
  North–South gap is y, the shortest straight-line distance from the start is
  √(x² + y²), because x and y are the two perpendicular sides of a right
  triangle and the shortest distance is its hypotenuse. The **distance walked**
  (the sum of the leg lengths) is a different quantity and coincides with the
  displacement only when the walk does not turn.
- **Source:** the Pythagoras theorem, standard plane geometry; SM Direction
  Sense treatment — reference_only.
- **Used in:** q-f3c10-006 to q-f3c10-024, q-f3c10-033, q-f3c10-034,
  q-f3c10-042, q-f3c10-048, q-f3c10-049, q-f3c10-050; notes §3, the triples
  table, and worked examples 1, 2, 3, 4, 7 and 9.
- **Spot-checked by:** _(blank until a human checks)_

## Pythagorean triples used

- **Result relied on:** the integer right-triangle triples 3-4-5, 6-8-10,
  5-12-13, 9-12-15, 8-15-17, 7-24-25, 20-21-29 and 12-35-37 give a whole-number
  hypotenuse for the stated pairs of legs. Each numerical distance question in
  the bank is built so the net East–West and North–South gaps form one of these
  pairs, so the answer is an exact integer.
- **Source:** standard; the verifier recomputes each distance as
  √(x² + y²) via `math.isqrt` and confirms it is a perfect square, so the triple
  is checked rather than assumed.
- **Used in:** every numerical distance id listed above; notes §3 table.
- **Spot-checked by:** _(blank until a human checks)_

## Turns: left, right, clockwise and anticlockwise

- **Convention relied on:** a right turn is 90° clockwise and a left turn is 90°
  anticlockwise, each measured from the walker's **current** heading, not from
  North. The clockwise chain is N → E → S → W → N and the anticlockwise chain is
  N → W → S → E → N. A turn changes the heading only and adds no distance.
  Turns given in degrees are read on the same clock face (90° a quarter, 180° an
  about-turn, 270° one way equal to 90° the other, 360° a full circle), and
  successive turns may be added, taking right as +90° and left as −90° and
  reducing modulo 360°.
- **Source:** standard rotation convention; SM Direction Sense treatment —
  reference_only.
- **Used in:** q-f3c10-005, q-f3c10-027 to q-f3c10-034, q-f3c10-049; notes §4 and
  worked examples 3, 5 and 9. The verifier rotates a heading vector by
  (dx, dy) → (−dy, dx) for left and (dx, dy) → (dy, −dx) for right.
- **Spot-checked by:** _(blank until a human checks)_ — confirm the SM equates
  "turn right" with clockwise; the wording is near-universal but worth a glance.

## Shadows and the position of the sun

- **Result relied on:** the sun rises in the East and sets in the West, so a
  shadow, falling on the side away from the sun, points **West in the morning**
  and **East in the evening**. Around noon the sun is nearly overhead, shadows
  are very short, and no reliable direction can be read from them. From a stated
  shadow direction and time of day, the sun is fixed, the shadow placed opposite
  it, and the person's facing recovered from which hand the shadow falls on.
- **Source:** standard solar-direction convention used in reasoning questions;
  SM Direction Sense treatment — reference_only.
- **Used in:** q-f3c10-035 to q-f3c10-041; notes §5 and worked example 6.
- **Spot-checked by:** _(blank until a human checks)_ — see the convention entry
  on **midday shadows** at the foot of this file. The "rises exactly East"
  statement is the idealisation these questions assume; it is exact only near
  the equinoxes, but every bank question uses it in that idealised form.

## Relative direction, opposite movement and mirror reflection

- **Results relied on:** a stated relation reverses cleanly — if A is East of B
  then B is West of A — and a chain of such clues is resolved by placing the
  points on a grid and reading the required direction off the sketch. Two people
  moving in **opposite** directions from one point are separated by the **sum**
  of their distances, and each lies in the opposite direction from the other. A
  plane mirror reverses the single direction that crosses its plane while leaving
  the perpendicular directions unchanged, so a movement towards a facing mirror
  appears reversed in the reflection.
- **Source:** standard; SM Direction Sense treatment — reference_only.
- **Used in:** q-f3c10-042 to q-f3c10-046; notes §6 and worked examples 7 and 8.
- **Spot-checked by:** _(blank until a human checks)_ — see the convention entry
  on **mirror reflection** at the foot of this file; the workable rule adopted
  here is deliberately limited to the direction crossing the mirror plane.

## Negative marking

- **Position relied on:** Paper 3 is wholly objective and carries negative
  marking of **0.25 mark for each wrong answer**, with 1 mark for a correct
  answer and 0 for an unattempted one. The expected-value arithmetic in §7
  follows directly from those numbers.
- **Source:** `foundationScoring` in `src/data/foundation.js`, which the quiz
  engine also reads; ICAI's stated pattern for Papers 3 and 4.
- **Used in:** q-f3c10-047; notes §7 and the last line of the one-page summary.
- **Spot-checked by:** _(blank until a human checks)_ — confirm the 0.25
  deduction is still the announced pattern for the Sept 2026 and Jan 2027
  attempts before the draft badge comes off.

---

# Reviewer's checklist — conventions chosen where practice varies

These are editorial calls, not sourced positions. Each one changes what a
student is taught, and each needs a human to confirm it against the SM.

1. **Map orientation.** The chapter fixes North up and East right, both on paper
   and on the coordinate grid the verifier uses. Every relative-direction and
   left/right answer depends on this. If the SM draws the compass differently,
   the §2 convention and the affected explanations should be reworded — though
   the numerical distance keys, which depend only on perpendicular gaps, do not
   change.

2. **Idealised sunrise due East.** §5 and q-f3c10-035, q-f3c10-036, q-f3c10-040
   assume the sun rises exactly in the East and sets exactly in the West. This
   is the idealisation these questions universally adopt; it is precisely true
   only near the equinoxes. If the SM qualifies it, §5 should carry the same
   qualification. No key changes either way, because each question turns only on
   "sun East in the morning, West in the evening".

3. **Midday shadows.** q-f3c10-039 takes the correct answer to be that a noon
   shadow is too short to give a reliable direction, and §5 says the same. Some
   question sets instead expect "shadow points North (or South)" from the small
   midday shadow at Indian latitudes. Confirm which the SM teaches; if it expects
   a definite midday direction, q-f3c10-039 must be reworded and re-keyed.

4. **Mirror reflection rule.** §6 and q-f3c10-045 adopt the limited rule that a
   plane mirror reverses only the direction crossing its plane and leaves the
   perpendicular directions unchanged. Mirror-direction puzzles vary in how much
   they develop (left–right swap versus front–back swap), so confirm the SM's
   treatment matches this limited rule before the badge comes off; only
   q-f3c10-045 depends on it.

5. **"Turn" adds no distance.** The chapter treats every turn as a change of
   heading only, never as a unit of movement, and the turn-and-walk questions
   (q-f3c10-006, q-f3c10-007, q-f3c10-033, q-f3c10-034, q-f3c10-049) rely on
   this. This is the standard reading and is very unlikely to differ, but it is
   the assumption a reviewer should keep in mind when checking those stems.

6. **Whole-number answers by design.** Every numerical distance question is
   built on a Pythagorean triple so the answer is an exact integer, and the
   verifier confirms each is a perfect square rather than rounding. Worked
   example 4 deliberately breaks this pattern (net gaps 8 and 12, distance
   4√13 ≈ 14.42 m) to teach that not every walk lands on a triple; it is a notes
   example only and has no bank question, so no key depends on the surd.

7. **Section count and length.** The notes run to 7 numbered sections and about
   9 worked examples. §6 (mirror reflection) is the part most likely to exceed
   or differ from the SM's depth; it can be trimmed to the opposite-direction and
   relative-direction material without touching any distance question.
