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

## framework-for-preparation-and-presentation-of-fs — VERIFY 2026-07-04

- [ ] **Asset/liability definitions quoted on purpose** — the Framework's
  definitions of asset and liability are kept near-verbatim in notes §4, the
  bank (q-014/q-015 correct options) and flashcards fw-9/fw-10, because exam
  answers require the definitional wording. All surviving shingles sit inside
  these two definitions (marked ※ in the citations file). Confirm the
  wording matches the current Framework text exactly — a paraphrased
  "definition" is worse than none.
- [ ] **Capital-maintenance case arithmetic basis** — cs-003 asserts CPP
  profit = sales − restated opening capital, with retained profit measured
  after drawings. Confirm this matches the SM's Example 8/9 presentation
  (the SM works the same way, but the reviewer should sight it).

## applicability-of-accounting-standards — VERIFY 2026-07-04

- [ ] **Five-gate definitional wording kept on purpose** — the SMC (AS Rules
  2021) and MSME (revised ICAI announcement) gates are quoted near-verbatim
  in notes/bank/flashcards (※ in citations). Confirm each threshold against
  the MCA notification and the ICAI announcement: ₹250cr turnover excl.
  other income; ₹50cr borrowings AT ANY TIME in the preceding year (SMC
  wording "including public deposits" — sight it); ₹50cr/₹10cr AS 18-28
  sub-class; end-of-period test date.
- [ ] **Blind-pass primer caveat** — the revised Aug-2024 MSME/Large scheme
  post-dates general knowledge, so the blind solver was given the regime
  RULES (not answers) before solving. Weaker independence than other
  chapters; a human spot-check of 5 random questions would restore it.
- [ ] **Legacy Level I-IV references** — the site must nowhere else imply
  the four-level non-company scheme still operates (superseded for periods
  from 1 Apr 2024).

## presentation-and-disclosures-based-as — VERIFY 2026-07-04

- [ ] **Stale "Level I" applicability wording inside the SM units** — SM Ch 4
  U2 (AS 3) and U3 (AS 17) intros still say the standards bind "Level I"
  non-corporate entities, but Ch 3 of the SAME SM edition teaches the revised
  Aug-2024 MSME/Large scheme (Level I–IV superseded for periods from
  1-4-2024). The site's Ch 4 content states applicability per the REVISED
  scheme (MSMEs skip AS 3/17/20/24; SMCs skip AS 17 and diluted EPS but keep
  AS 3). Confirm the revised scheme is what the Sept 2026 exam expects and
  initial — this is an internal inconsistency in the SM itself.
- [ ] **Definitional quotations kept on purpose** — five clusters survive the
  shingle check by design (※ in the citations file): AS 24's
  discontinuing-operation definition, AS 18's related-party families and
  relative definition, AS 17's business-segment definition, AS 20's basic-EPS
  formula phrase and face-of-P&L requirement, AS 18's aggregation sentence.
  Confirm each matches the current AS text exactly.
- [ ] **Overdraft convention continuity** — Ch 4 notes §2 repeat the site's
  Ch 11 convention (bank overdraft / cash credit movements = financing).
  The SM Ch 4 U2 item list places overdraft and cash credit alongside
  financing borrowings; sight it and initial (same open item as Ch 11).
- [ ] **AS 25 final-interim-period rule** — q-039 asserts nature and amount
  of a material estimate change in the final interim period (no separate
  report published) go to the annual FS notes. Sight the SM/AS 25 paragraph
  and initial.
- [ ] **Partly paid shares in EPS** — notes §5 states partly paid shares
  count as a fraction to the extent of dividend entitlement, and the SM note
  treats no-dividend partly-paid shares as potential equity shares for
  diluted EPS. Sight the SM Unit 5 note and initial.

## assets-based-as — VERIFY 2026-07-04

- [ ] **Definitional quotations kept on purpose** — the ※ clusters in the
  citations file (AS 2 inventory definition, AS 10/26 held-for-use tail and
  intangible definition, AS 13 current-investment definition and LT→current
  rule, AS 16 qualifying-asset core and exchange-difference clause, AS 19
  lease/finance-lease definitions, lower-of initial measurement,
  straight-line rule and S&LB deferral rule, AS 10 retired-assets rule,
  AS 28 discount-rate wording and goodwill-reversal condition). Confirm each
  against the current AS text.
- [ ] **AS 28 goodwill-reversal wording** — the extracted SM Unit 7 text did
  not surface the "specific external event of an exceptional nature" sentence
  verbatim (PDF extraction may have mangled it). The notes/bank state the
  AS 28 rule; sight the SM/AS 28 paragraph on reversal of goodwill impairment
  and initial.
- [ ] **AS 16 "ordinarily twelve months"** — the notes gloss "substantial
  period" with the customary twelve-month yardstick. The SM discusses the
  12-month norm in its explanation; confirm the SM wording supports
  "ordinarily" and initial.
- [ ] **AS 13 cum-right exception** — q/notes state the narrow case where
  sale proceeds of unsubscribed rights reduce carrying cost (cum-right
  purchase + ex-right value below cost). Sight the SM Unit 3 paragraph.
- [ ] **AS 10 testing proceeds** — q-008 nets sale proceeds of test output
  against testing costs per AS 10 (Revised). Confirm the SM presents net
  testing cost the same way.
