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

## branches-including-foreign — VERIFY 2026-07-04

- [ ] **Transit-adjustment convention** — notes §5, q-014 and cs-003 state
  that goods/cash-in-transit entries are passed in HEAD OFFICE books. That is
  the SM Ch 15 convention, but some texts have the branch record goods in
  transit; the blind pass flagged the same question as its one mildly
  uncertain answer. Confirm the SM's presentation and initial the citations
  row (SM Ch 15 §7.1).
- [ ] **AS 11 reclassification wording** — q-028 / d-009 state that on a
  non-integral → integral change the change-date translated amounts of
  non-monetary items become their historical costs and the FCTR stays until
  disposal. Verify against the AS 11 text (paras on change in classification)
  and initial the citations row.

## financial-statements-of-companies — VERIFY 2026-07-04

- [ ] **Overdraft/cash credit under AS 3** — q-028, cs-004-d, notes §6 and
  fs-15 present overdraft/cash credit movements as FINANCING flows. The blind
  pass agreed but noted AS 3's text can be read to admit on-demand overdrafts
  nearer the cash pool. Confirm the SM Ch 11 U2 presentation and initial the
  citations row.
- [ ] **Month-12 instalment boundary** — cs-001-c counts an instalment due
  exactly twelve months after the reporting date as a current maturity
  (₹4,00,000, not ₹2,00,000). The blind pass reached the same answer but
  flagged the boundary. Confirm the SM/Schedule III convention ("due to be
  settled within twelve months") and initial.
- [ ] **Statutory quotations kept on purpose** — the notes quote three
  Schedule III phrases verbatim (share-number reconciliation wording, the
  nature-wise P&L line-item names, the rounding bands). They survive the
  shingle check by design and are marked ※ in the citations file.

## introduction-to-accounting-standards — VERIFY 2026-07-04

- [ ] **Roadmap dates/thresholds** — the chapter leans on the SM §14
  snapshot: voluntary 2015-16; Phase I 1-4-2016 ≥₹500cr; Phase II 1-4-2017
  all-listed-except-SME + ₹250-500cr; NBFCs 2018/2019. Spot-check each
  against the SM and the MCA notifications, and initial the citations rows —
  these are the highest-yield memorised facts in the bank.
- [ ] **Stale 2006-Rules reference in the SM** — the SM's roadmap bullet
  says uncovered companies continue with the 2006 Rules; the content states
  the 2021 Rules (per SM §3). Confirm the notes/bank never repeat the stale
  reference.
- [ ] **NFRA vs NACAS wording in s.133** — content says CG notifies "in
  consultation with NFRA". Confirm the current s.133 text and the SM edition
  agree (older editions referenced NACAS).
