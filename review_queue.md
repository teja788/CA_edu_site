# Review queue

Quarantine for content that failed an automated check and must NOT go live
until a human resolves it. Entries are appended by
`scripts/consistency_check/consistency_check.py diff` (key vs fresh-pass
mismatches) and by chapter sessions logging AMENDMENT-CHECK markers or
low-confidence items.

Triage rules:

1. A mismatch means the key is wrong, the stem is ambiguous, or the fresh pass
   erred — decide which by recomputing/re-reading the primary source, never by
   picking the more confident-sounding explanation.
2. Resolution = fix the key, fix the stem, or delete the question; then rerun
   both the numerical verifier and the consistency check before merging.
3. Tick the checkbox and note the resolution inline. Resolved sections may be
   pruned once the fix is committed — git history is the log.

---

## buyback-of-securities — AMENDMENT-CHECK 2026-07-03

- [ ] **Notes §3 (SEBI route for listed companies)** — the notes deliberately do
  NOT summarise the SEBI (Buy-back of Securities) Regulations 2018 (open-market
  route phase-down, escrow, tender mechanics) because SEBI amends them
  frequently. A human must decide, per attempt, whether the Inter P1 syllabus
  expects any SEBI-layer detail beyond "listed companies follow SEBI
  regulations", and update notes §3 + the P1 amendment tracker accordingly.
  Source to check: https://www.sebi.gov.in/legal/regulations (Buy-back of
  Securities Regulations, as amended).
- [ ] **s.68 Explanation numbering** — content relies on the Explanation to
  s.68 including securities premium in free reserves for buyback. The
  substance is standard ICAI-solution doctrine, but verify the exact clause
  label/wording in the current consolidated Act (India Code) and initial the
  citations row.

## amalgamation-of-companies — VERIFY 2026-07-04

- [ ] **AS 14 paragraph numbering** — notes/bank/citations cite para 3(e) and
  3(g) precisely (safe: definitions), but the pooling-method, purchase-method,
  goodwill-amortisation and statutory-reserve positions are cited generically
  ("AS 14 — purchase method" etc.). A human should insert the exact para
  numbers from the notified standard (Companies (Accounting Standards) Rules
  2021 text) into citations_amalgamation-of-companies.md and initial the rows.
- [ ] **MCA 2016 rename** — notes §5 and flashcard am-10 state the
  "Amalgamation Adjustment Account → Reserve" rename came from the MCA's 2016
  amendment (believed Companies (Accounting Standards) Amendment Rules, 2016,
  notified 30-03-2016). Confirm the instrument + date before anyone cites it
  verbatim in an answer.
- [ ] **Quoted standard text** — one 10-word shingle vs the SM survives by
  design: the AS 14 amortisation formula ("five years unless a somewhat longer
  period can be justified"), retained as a marked quotation in notes §4 and
  q-009/q-021/d-005. Confirm we are comfortable quoting notified-standard
  wording at this length (precedent: statutory text, Copyright Act s.52(1)(q)).
- [ ] **Fixed while here: buyback readLink anchors** — the Ch 12 bank's
  readLink hrefs pointed at #s2/#s5/#s6, which never existed on the built page
  (Astro auto-slugs headings). Re-pointed to the real heading ids this
  session; spot-click two of them after the next deploy.

## internal-reconstruction — VERIFY 2026-07-04

- [ ] **Five-year disclosure anchor** — notes §6 and q-016 state that amounts
  written off fixed assets under a scheme are shown for five years. The SM
  Ch 14 asserts this; its statutory anchor today (the rule descends from an
  old Schedule VI note) should be confirmed against current Schedule III /
  NCLT practice, and the citations row initialled. The blind pass flagged the
  same question as its one medium-confidence answer — same reason.
- [ ] **s.66 clause labels** — content cites s.66(1)(a) / s.66(1)(b)(i)-(ii)
  for the three reduction modes. Verify the exact clause lettering in the
  current consolidated Act (India Code) and initial the citations rows.
