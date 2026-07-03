# Manual verification checklist — Intermediate preparation (3 Jul 2026)

Everything commit `fe05f90` could not verify against a fetchable official
source. Work through the boxes before the first Intermediate law/tax content
ships; strike items through with the date + your initials as you go.
(Machine-checkable facts are NOT here — CI covers those.)

## Blocking for any Inter content

- [ ] **Inter P1 partnership content is off-syllabus.** The ICAI May-2026 SM
  index for Paper 1 (15 chapters) has **no partnership chapter** — partnership
  accounts now sit in Foundation. The live notes trio under
  `src/pages/intermediate/advanced-accounting/partnership-accounts/` and the
  12 launch MCQs in `src/data/site.js` predate this. Decide:
  re-home to Foundation P1, or archive. Until then they render on a live page.
  - Check: https://www.icai.org/post/bos-int-p1-may2026-exam

## Blocking for tax/law content (P2, P3, P5)

- [ ] **Finance Act 2025 / AY 2026-27 for the Sept 2026 attempt.** Stated per
  ICAI convention + the SM edition label ("May 2026/September 2026/January
  2027 Exams"); the confirming statement is inside a PDF I could not parse.
  Open the "Statutory Update for September 2026 Examination" and confirm both
  the Finance Act and the assessment year, then set `verified: true` on the
  `sept-2026` record in `src/data/intermediate.js`.
  - Check: https://www.icai.org/post/sm-intermediate-paper3-seca
- [ ] **GST notification cut-off dates.** All three attempts carry dates
  computed from the 6-month convention (Sept 2026 → 28 Feb 2026 ·
  Jan 2027 → 30 Jun 2026 · May 2027 → 31 Oct 2026), flagged as such in
  `intermediate.js`. Confirm each against the attempt's statutory update.
  - Check: https://boslive.icai.org/education_content_AmendmentsDevelopments.php?p=Amendments%2FDevelopments&c=intermediate
- [ ] **Income-tax Act 2025 boundary (May 2027 onwards).** The announcement
  headline is confirmed ("Applicability of the Income-tax Act, 2025 from
  May 2027 CA Exams Onwards", 08-12-2025) but read the full text for
  transition details (terminology, section mapping booklet, whether RTP/MTP
  for May 2027 follow the new Act).
  - Check: https://boslive.icai.org/announcement_details.php?id=552
- [ ] **Transcribe the two "pending transcription" amendment entries** in
  `src/data/amendments.js`: the P2 "Amendments for September 2026
  Examinations" document and the P3 GST statutory update for Sept 2026.
  Each change needs its notification number + date, entered as its own
  changelog entry.
  - Source: https://boslive.icai.org/education_content_AmendmentsDevelopments.php?p=Amendments%2FDevelopments&c=intermediate
- [ ] **MCA notification for the Companies (Accounting Standards) Rules,
  2021.** `sources.yaml` cites G.S.R. 432(E) dated 23-06-2021 from memory —
  verify number and date on mca.gov.in / eGazette before the first AS citation
  references it.

## Exam-calendar facts (non-blocking, needed for attempt pages)

- [ ] **Sept 2026 Inter exams begin 8 Sept 2026** (`site.js`/`intermediate.js`).
  Confirm against the ICAI exam notification: https://icai.nic.in/
- [ ] **Jan 2027 exam dates** — TBA; fill `examDates` on the `jan-2027` record
  when announced.
- [ ] **May 2027 exam dates** — TBA; same. Also re-run the P3 Sec A taxonomy
  check when the new (2025-Act) SM edition for May 2027 is published — the
  chapter list in `intermediate.js` reflects the 1961-Act edition.
- [ ] **MTP Series I from 25 Jul 2026 / Series II from 8 Aug 2026** (shown on
  Inter paper pages) — sourced from a secondary report of the BoS
  announcement; confirm on https://boslive.icai.org/

## Judgement calls to ratify (already live, revisit if you disagree)

- [ ] **Mock composer marks assumption:** MCQs count 2 marks each
  (15 × 2 = 30). Verify against an actual Inter question paper's Part I
  before publicising the first composed mock. (`src/pages/practice/mock.astro`,
  `MCQ_MARKS`.)
- [ ] **Removed fabricated demo amendments** — the "stamp duty via Finance Act
  2026" tracker entry + its inline callout in the admission-of-a-partner note
  (stamp duty is a State List subject), and a mis-dated "P3 syllabus revision
  from Jan 2027" entry. Skim the `fe05f90` diff to confirm you agree.
- [ ] **Volatile-paper notes must be MDX** (attempt_lint flags `.astro` note
  pages under P2/P3/P5 because their frontmatter can't be linted;
  `index`/`amendments`/`weightage` are exempt). Confirm this convention works
  for the Prompt 5 chapter loop.
