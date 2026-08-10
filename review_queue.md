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
- [x] **s.66 clause labels** — content cites s.66(1)(a) / s.66(1)(b)(i)-(ii)
  for the three reduction modes. Verify the exact clause lettering in the
  current consolidated Act (India Code) and initial the citations rows.
  **Resolved 2026-07-19** — the citations file had the (b) sub-clauses
  swapped: the Act reads s.66(1)(b)(i) = cancel paid-up capital which is lost
  or unrepresented by available assets, s.66(1)(b)(ii) = pay off paid-up
  capital in excess of the wants of the company. Ref labels fixed in
  citations_internal-reconstruction.md (notes/bank describe the modes without
  sub-clause letters, so no other content was affected).

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
- [ ] **AS count restated frame-proof (added 2026-07-19)** — notes §3, the
  pointer callout and §7 now say: 32 standards issued by the ICAI over time;
  AS 6, AS 8 and AS 30–32 withdrawn; 27 in force — exactly the set the 2021
  Rules notify — with the SM's "29 issued, minus two, equals 27" preserved as
  the notified-series frame. Sight the current SM Ch 1 §3 wording and confirm
  the exam still expects 29/27 in count questions (the bank's q-007–q-009/
  q-026 answer keys should be re-read against the new framing).

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
- [ ] **AS 15 sub-50-employee SMC carve-out (added 2026-07-19)** — the 2026-07
  audit softened Ch 3 §1 (AS 15 bullet + summary) and the Ch 6 intro, which
  had stated flatly that every SMC must use the Projected Unit Credit Method
  for defined benefit plans: an SMC with an average of fewer than 50 employees
  may instead use another rational method for the accrued liability. A human
  should sight the AS 15 text annexed to the Companies (AS) Rules 2021 for the
  exact carve-out wording (average-employee test, "accrued liability" scope)
  and initial the corresponding rows in citations_applicability-of-accounting-
  standards.md and citations_liabilities-based-as.md.

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

## liabilities-based-as — VERIFY 2026-07-05

- [ ] **Definitional quotations kept on purpose** — the ※ clusters in the
  citations file: the AS 15 short-term-benefit definition ("fall due wholly
  within twelve months after the end of the period in which the service is
  rendered"), the AS 29 definitions block (provision, liability, the
  contingent-liability/contingent-asset "confirmed only by the occurrence or
  non-occurrence…" limbs), AS 29's best-estimate measurement sentence, and
  AS 29's discount-rate wording ("current market assessments of the time
  value of money and the risks specific to the liability"). Confirm each
  matches the notified AS text exactly.
- [ ] **Stale Level-based applicability in SM Ch 6 U1 §1.2** — the SM still
  says AS 15 "applies from April 1, 2006 in its entirety for all Level 1
  enterprises" with a 50-employee relaxation, and the non-vesting-absences
  exception names "Levels IV, III and II non-corporate entities". The site
  states the revised Aug-2024 MSME/Large scheme instead (per Ch 3): SMC/MSME
  exemption for non-vesting accumulating short-term absences; SMC keeps PUC
  actuarial for DB with disclosure relief; non-company MSME may use any
  rational method. Sight the ICAI announcement/Rules and initial the mapping.
- [ ] **AS 15 paragraph numbers quoted via the SM** — para 7.2 (falls due),
  para 8(b) (expected to occur), para 49 (schemes with estimation
  difficulty), para 59(b) (asset ceiling), para 61 (P&L components),
  para 129 (other long-term benefits). Confirm the numbering against the
  notified standard before anyone cites it in an answer.
- [ ] **AS 29 discounting exception** — notes/bank state that
  decommissioning/restoration-type liabilities recognised as part of PPE
  cost are discounted (pre-tax market rate; unwinding to P&L) while all
  other provisions stay undiscounted. This wording entered AS 29 by
  amendment; sight the current notified text (2021 Rules print) and initial.
- [ ] **Contingent-asset disclosure route** — q-029/notes assert a
  contingent asset is not disclosed in the financial statements at all and
  appears only in the report of the approving authority when inflow is
  probable. That is AS 29's Indian position (contrast IAS 37); sight the
  paragraph and initial.
- [ ] **cs-i1c06-002 drafting note** — "she will receive 4 yearly
  increments" over a 4-year term mirrors the SM's own Illustration 9
  convention (final salary = current × 1.1⁴). The blind solver flagged the
  timeline drafting as slightly unusual though internally corroborated;
  reviewer may want to re-read the stem once.

## other-accounting-standards — VERIFY 2026-07-05

- [ ] **Definitional quotations kept on purpose** — the ※ clusters in the
  citations file: the AS 12 grant-definition head ("assistance by government
  in cash or kind"), the Method II release rule ("systematic and rational
  basis over the useful life"), the nominal-value trigger ("whole, or
  virtually the whole"), AS 14's acquisition-scope sentence, the five-year
  goodwill rule, the key-personnel goodwill factor, and the AS 14
  disclosure-list items (names/general nature; percentage of equity shares
  exchanged). Confirm each against the notified AS texts.
- [ ] **AS 12 paragraph numbers quoted via the SM** — para 10 (promoters'
  contribution → capital reserve), para 14 (deferred grant released in
  depreciation proportions), para 21 (refund mechanics). Confirm numbering
  against the notified standard.
- [ ] **Refund as extraordinary item** — AS 12 read with AS 5. The site's
  Ch 7 (AS 5) is not yet written; when it is, keep the extraordinary-items
  treatment consistent with what Ch 9 states here.
- [ ] **AS 14 disclosure paragraphs** — the three disclosure lists are
  stated per SM Ch 9 U2 (which cites paras 43–46). Sight the notified AS 14
  text and initial.
- [ ] **AS 14 not applicable to MSMEs** — the intro repeats Ch 3's position
  that AS 14 is treated as not applicable to MSMEs because such
  transactions rarely occur (applies if one does). Sight the revised-scheme
  announcement wording and initial.
- [ ] **Division of labour with Ch 13** — Ch 9's AS 14 content deliberately
  covers only standard-text angles (scope/acquisitions, post-balance-sheet
  date, contingent consideration, goodwill factors, P&L balance,
  disclosures); all computation mechanics remain in Ch 13. Reviewer should
  confirm no contradiction between the two chapters' statements.

## revenue-based-as — VERIFY 2026-07-19

- [ ] **Citations file created retroactively** — the chapter's notes shipped
  without a citations file; citations_revenue-based-as.md was written during
  the 2026-07 content audit from the notes as they stand. No shingle/overlap
  pass was run for this chapter, and there is no question bank, flashcard set
  or numerical verify script yet. A reviewer should spot-check the rows
  against SM Ch 8 Units 1–2 and the notified AS 7/AS 9 texts, and the overlap
  check must be run when the bank is built.
- [ ] **Definitional quotations kept on purpose** — the ※ clusters in the
  citations file: the AS 7 construction-contract definitional tail ("closely
  interrelated or interdependent in terms of their design, technology and
  function or their ultimate purpose or use"), the cost-plus definition
  ("allowable or otherwise defined costs, plus a percentage of these costs or
  a fixed fee"), the AS 9 revenue definition ("gross inflow of cash,
  receivables or other consideration…"), and the sale-of-goods recognition
  heads. Confirm each matches the notified AS text exactly.
- [ ] **Reliable-estimate condition counts** — notes §1 states FOUR conditions
  for a fixed price contract's outcome and TWO for cost-plus. Sight the AS 7
  paragraphs (SM Ch 8 U1) and confirm the four/two split and the
  "compared with prior estimates" tail.
- [ ] **WE 1 escalation stem reworded (2026-07-19)** — the labour clause now
  reads "passes on labour cost increases in full provided the rise in minimum
  wages does not exceed 30%", so the solution's full ₹30 lakh pass-through is
  unambiguous (numbers and answer unchanged, ₹9,75,00,000). Re-read the stem
  once against SM-style escalation problems and confirm the intended reading.
- [ ] **WE 2 cost-to-complete clause (2026-07-19)** — the stem now states the
  further ₹600 lakh includes consuming the ₹20 lakh of materials at site, so
  total cost is unambiguously ₹1,000 lakh (numbers unchanged). Confirm this
  matches the SM's convention for materials-at-site adjustments.

## as-items-impacting-fs — VERIFY 2026-07-19

- [ ] **New chapter (Ch 7, AS 4/5/11/22) authored 19 Jul 2026** — notes, bank
  (38 MCQs · 8 descriptives · 4 case sets, 22 machine-verified numericals) and
  citations file shipped together. A reviewer should spot-check the citations
  rows against SM Ch 7 (May 2026 ed.) and the notified AS texts.
- [ ] **MAT one-liner (AS 22)** — stated per ASI-6: MAT amount is the current
  tax; deferred tax still measured at regular enacted rates. Sight the May
  2026 SM to confirm it still carries this position.
- [ ] **Para 46A** — presented as a live irrevocable election for long-term
  foreign-currency monetary items without its 2011 insertion history; confirm
  the SM's current framing.
- [ ] **AS 4 disclosure split** — strict line taken: non-adjusting events →
  report of the approving authority; proposed dividends → notes. Verify the
  SM does not soften this.

## as-consolidated-fs — VERIFY 2026-07-19

- [ ] **New chapter (Ch 10, AS 21/23/27) authored 19 Jul 2026** — notes, bank
  (38 MCQs · 8 descriptives · 4 case sets, 24 machine-verified numericals) and
  citations file shipped together. Spot-check citations rows against SM Ch 10
  (May 2026 ed.) and the notified AS texts.
- [ ] **"Near future" ≈ 12 months** for the AS 21/23 temporary-holding
  exclusion — per the ICAI explanation; confirm SM wording.
- [ ] **Reporting-date gap** — 6-month cap asserted only for AS 21; confirm
  whether the SM extends it to AS 23 associates.
- [ ] **AS 23 unrealised-profit elimination** to the extent of the investor's
  interest (both directions) — follows the ASI-derived explanation; confirm
  against current SM text.
## theoretical-framework — VERIFY 2026-08-07

- [ ] **New chapter (Ch 1, Theoretical Framework) authored 7 Aug 2026** — notes
  (473-line MDX), bank (53 questions: 45 MCQs · 6 descriptives · 2 case items,
  9 machine-verified numericals) and citations file shipped together. Reviewer
  should spot-check the citations rows against SM Ch 1 (May 2026 ed.).
- [ ] **AS 1 three-assumptions rule** — bank and notes state exactly three
  fundamental assumptions (going concern, consistency, accrual) with the
  disclose-only-if-departed rule. Sight the AS 1 text/SM wording.
- [ ] **Policy vs estimate line** — depreciation METHOD treated as an accounting
  policy while useful life is an estimate (prospective revision). Confirm the SM
  Ch 1 framing matches (this interacts with the AS 10 position used in Ch 5).
- [ ] **Qualitative characteristics set** — four principal characteristics
  (understandability, relevance, reliability, comparability) with materiality as
  a threshold of relevance, per the ICAI Framework as summarised for Foundation.
  Confirm the SM presents the same four-way split at Foundation level.
- [ ] **Capital vs revenue classification battery** — the classification calls in
  the MCQs follow SM conventions (e.g. carriage on new machinery capitalised,
  heavy advertising as deferred revenue expenditure treatment). Re-check any row
  the reviewer finds arguable against the SM's own classification examples.
- [ ] **AICPA definition fragment** — used as a short attributed fragment (as the
  SM itself does). Confirm the attribution stays and no longer quote crept in.
## accounting-process — VERIFY 2026-08-07

- [ ] **New chapter (Ch 2, Accounting Process) authored 7 Aug 2026** — notes (530-line MDX), bank (51 questions, 22 machine-verified numericals), citations; reviewer should spot-check citations rows against SM Ch 2 (May 2026 ed.).
- [ ] **Answer-key distribution is badly skewed** — 34 of the 45 MCQs key to option **A**, 7 to B, 4 to C and **none to D**; among the 22 numericals it is 21 A / 1 B. Nothing is factually wrong (all 22 numericals recompute correctly), but a student who guesses "A" scores ~75% on this chapter. Recommend reshuffling option order across roughly half the bank and re-running `scripts/verify_numerical/run.py` afterwards, since the verifier maps computed values to option keys.
- [ ] **q-f1c2-002 — Outstanding Salaries A/c classified as a *representative personal* account.** This is the ICAI SM line and the notes §2 line, but some textbooks treat outstanding-expense accounts as liability/nominal under the modern map. Confirm the SM Ch 2 wording still supports the representative-personal answer, and that option B's explanation (salary expense = nominal, outstanding amount = personal) reads as the SM does.
- [ ] **q-f1c2-039 and q-f1c2-041 — the "zero effect on net profit" treatment of stationery wrongly debited to Purchases A/c.** Both questions assume the stationery is a revenue expense of the *same* year, so removing it from Purchases and charging it to Stationery leaves net profit untouched (gross profit alone moves). Confirm a CA is comfortable with this being asserted as an exact zero, and with q-f1c2-039's direction on error (i) — capitalised **repairs** *reduce* corrected profit, the mirror image of q-f1c2-040's capitalisable installation wages, which *raise* it. This capital/revenue direction pair is the highest-risk judgment call in the chapter.
- [ ] **q-f1c2-036 and q-f1c2-042 — the one-sided/two-sided calls on subsidiary-book casting errors.** Both treat "the purchases book was overcast/undercast" as a purely **one-sided** error (only the periodic total posted to Purchases A/c is wrong; the individual suppliers' accounts, posted entry by entry, are unaffected), so the correction must run through Suspense. Confirm this is how the SM frames it, since q-f1c2-042's whole answer ("Suspense closes to nil") depends on it, as does q-f1c2-036's claim that a book overcast IS caught by the trial balance.
- [ ] **q-f1c2-030 — "a credit balance in the cash column is impossible" stated as an absolute.** Notes §6 says the same. Confirm the reviewer is happy with the unqualified phrasing (the usual textbook justification is that you cannot pay out more physical cash than you hold).
- [ ] **q-f1c2-015 / q-f1c2-017 — the "goods vs assets" filter applied to a specific trade.** Both turn on the firm being a *cloth merchant*, so a computer / office furniture bought on credit goes to the journal proper rather than the purchases book. Confirm the stems make the firm's line of business unambiguous enough for an examiner-grade question, and that q-f1c2-015's distractor D (which adds the computer) is framed as an error of principle consistently with notes §5's callout.
- [ ] **No bank corrections were needed** — all 22 numerical questions recomputed to the bank's existing keys on the first verifier run (`22 numerical question(s) verified, 0 failure(s)`), and descriptive question d-f1c2-06's stem is internally consistent (debit column short ₹2,700 = ₹3,500 sales overcast − ₹800 short credit to Hari). No key or explanation was edited.
## bank-reconciliation-statement — VERIFY 2026-08-07

- [ ] **New chapter (Ch 3, Bank Reconciliation Statement) authored 7 Aug 2026** — notes (403-line MDX), bank (51 questions, 26 machine-verified numericals), citations; reviewer should spot-check citations rows against SM Ch 3 (May 2026 ed.).
- [ ] **Signed plus/minus convention replaces the SM's Add/Less case tables.** Notes §5–§6 and every numerical write favourable balances positive and overdrafts negative, then run ONE formula for all four starting points (reverse walk = flip every sign), instead of the four separate "add if favourable / less if overdraft" grids many texts print. Confirm this is presentationally acceptable for ICAI answer-writing and arithmetically equivalent in every case the SM tabulates — especially the overdraft-start cases (q-f1c3-004 to q-f1c3-006, q-f1c3-010 to q-f1c3-012, q-f1c3-016, q-f1c3-025, d-f1c3-05), where the answer is reported by reading the sign of the result ("−23,500 → overdraft ₹23,500").
- [ ] **Amended-cash-book item split.** The convention used (notes §7, q-f1c3-013/014/016/037/040/045, d-f1c3-04): bank-first items the trader did not know about (charges, interest charged and allowed, standing instructions, direct deposits, collections, dishonours) AND the trader's own errors go INTO the cash book; cheques issued-not-presented, deposits not credited, and the BANK's errors stay BRS-only. Confirm ICAI treats the trader's own errors as amended-cash-book items (rather than BRS lines) under this heading.
- [ ] **Own-error correction inside an amended cash book from an overdraft — q-f1c3-016.** A deposit of ₹3,500 duly collected but never entered in the cash book is treated as the trader's OWN omission and added into the amended cash book (answer: overdraft ₹3,340). A reader could instead classify it as a timing/bank item and leave it in the BRS, giving a different amended balance. Confirm the omission reading is the intended one on the stem's wording ("deposited and duly collected was never entered in the cash book").
- [ ] **Bank's own error kept out of the trader's books — q-f1c3-021, q-f1c3-038, d-f1c3-05(f).** Position taken: pass NO cash book entry; the bank's wrong debit/credit stays a BRS reconciling item until the bank reverses its ledger, and its effect is single-sized (not doubled). Confirm ICAI does not expect a memorandum correction in the trader's books.
- [ ] **Error-sizing rules (the doubling boundary) — notes §4, q-f1c3-017/018/019/020/022/032, d-f1c3-05.** Wrong SIDE = twice the amount; transposition/wrong amount = the difference only; omission, wrong COLUMN (bank entry parked in the cash column) and casting over/undercast = the amount ONCE. The wrong-column case (q-f1c3-019: ₹2,750 payment entered in the cash column, treated as −2,750, single-sized) is the one most often mis-taught as a doubled error — confirm the single-sized treatment.
- [ ] **Dishonour treated as cheque amount PLUS the bank's dishonour charges as two separate reconciling amounts** — q-f1c3-003 (₹3,200 + ₹200), q-f1c3-025 (₹5,000 + ₹100), q-f1c3-014, notes §3 and Common mistakes. Confirm both components are expected, and that on the reverse (pass book → cash book) walk they are added back rather than deducted.
- [ ] **Requirement-line dependency — q-f1c3-045, notes §7 pointer.** Position taken: "prepare a BRS WITHOUT adjusting the cash book" sends every given item (charges, standing instructions, errors and all) straight into the statement, producing a different presentation from the amended-cash-book route on identical facts. Confirm this is how ICAI marks the two wordings.

_No factual corrections were needed to the MDX or the bank during this citations pass; `scripts/verify_numerical/run.py` re-run on 7 Aug 2026 reports 26 numericals verified, 0 failures._
## final-accounts-of-sole-proprietors — VERIFY 2026-08-07

- [ ] **New chapter (Ch 7, Final Accounts of Sole Proprietors) authored 7 Aug 2026** — notes (502-line MDX), bank (51 questions: 45 MCQs of which 25 are `numerical: true`, plus 6 descriptives; answer keys A 11 / B 11 / C 12 / D 11), citations (16 sections). All 25 numerical questions are recomputed independently by `scripts/verify_numerical/verify_final-accounts-of-sole-proprietors.py` (0 failures) and all 45 `readLink` anchors resolve to real MDX headings. Reviewer should spot-check the citations rows against SM Ch 7 (May 2026 ed.) and initial each "Spot-checked by" line.
- [ ] **Wages-and-salaries placement convention (q-f1c7-006, notes §3 pointer callout).** The bank treats a combined trial-balance line "Wages and salaries" as a **Trading Account** debit and "Salaries and wages" as a **P&L** debit, on the basis that the leading word signals the dominant element. This is a presentation convention, not a rule — please confirm the May 2026 SM still states it in these terms, and confirm we are comfortable examining on it as a single-best-answer MCQ rather than flagging it as a convention only.
- [ ] **Ordering of the provision for discount on debtors (q-f1c7-026, q-f1c7-030, q-f1c7-031, q-f1c7-032, notes §7).** Every one of these questions assumes the discount provision is computed on *good debtors* = debtors − further bad debts − doubtful-debts provision, i.e. strictly **after** the doubtful-debts provision. q-f1c7-030 additionally nets the new discount provision against an old discount provision already in the trial balance (charge = new − old, the same treatment as the doubtful-debts chain). Please confirm both the ordering and the netting against the SM's own illustration; if the SM's illustration nets differently, q-f1c7-030 is the question to re-check first.
- [ ] **Two-way-readable adjustment stems.** Three stems could in principle be read either way and were deliberately worded to close the ambiguity — please confirm the wording holds: (a) **q-f1c7-011** — "closing stock ₹84,000 (appearing inside the trial balance)" alongside adjusted purchases, which is what makes the stock a balance-sheet-only item; (b) **q-f1c7-019** — "'Outstanding wages ₹7,000' already appears as a credit balance inside the trial balance", the once-not-twice trap; (c) **q-f1c7-044** — "net profit … before charging interest on capital and before crediting interest on drawings", without which the ₹2,30,000 could be read as already net of both.
- [ ] **Abnormal-loss presentation (q-f1c7-037, q-f1c7-039, notes §9).** The bank credits the Trading Account with the **full cost** of stock lost and treats the admitted claim as an asset, with only the uninsured balance in the P&L. The notes acknowledge that some solutions instead **deduct the loss from purchases** (identical effect on gross profit). Confirm that the Trading-credit presentation is the one we want to mark as correct, since q-f1c7-039's distractors are built around it.
- [ ] **Manager's commission in the full-battery question (q-f1c7-045).** Adjustment (vi) gives 10% of net profit *after* charging such commission, applied to a profit of ₹88,000 that itself depends on five earlier adjustments (including the provision chain). A CA should re-walk the whole solution once end-to-end — Trading ₹1,94,000 gross profit → ₹88,000 pre-commission → ₹8,000 commission → ₹80,000 net profit — and confirm the debtors block (further bad debts ₹5,000 + new provision ₹8,000 − old provision ₹6,000 = ₹7,000) is presented the way the SM would present it.
- [ ] **No MDX corrections were made.** All five worked examples in the notes were re-checked arithmetically (gross profit ₹2,25,000; net profit ₹77,000; provision charge ₹10,000 with the ₹2,000 write-back variant; commission ₹22,000 / ₹20,000; and the balance sheet tallying at ₹3,94,000) and every figure holds, so the notes were left untouched.
## financial-statements-of-not-for-profit-organisations — VERIFY 2026-08-07

- [ ] **New chapter (Ch 8, Financial Statements of Not-for-Profit Organisations) authored 7 Aug 2026** — notes (438-line MDX), bank (45 MCQs of which 23 numerical + 6 descriptives; keys A 11 / B 11 / C 11 / D 12), citations; reviewer should spot-check citations rows against SM Ch 8 (May 2026 ed.).
- [ ] **Entrance fees convention — sight the SM line.** The notes (§7 table row, §7 pointer callout, revision summary) and the bank treat entrance/admission fees as **income unless the question directs capitalisation**. Many textbooks capitalise them instead. q-f1c8-021 tests this convention head-on and q-f1c8-039 and q-f1c8-044 depend on it; if the May 2026 SM states the opposite, q-f1c8-021's key flips and the two capital-fund questions need re-stemming.
- [ ] **General legacy / general donation convention — sight the SM line.** The notes capitalise legacies (specific legacy → its own fund) but record that a **small general legacy may be treated as income**, and treat a general donation as income of the year. q-f1c8-023 and q-f1c8-024 rest on this. Confirm both the main rule and the small-general-legacy qualification appear in the May 2026 SM in these terms; if the qualification has been dropped, remove it from the §7 callout, the revision summary and the explanation to q-f1c8-024 option C.
- [ ] **MDX factual fix made 7 Aug 2026 (§3, R&P bullet 1).** The notes read "A closing balance on the payments side means a bank overdraft." That is the normal FAVOURABLE case — the closing cash/bank balance is carried down on the payments (credit) side, and an overdraft at the year end appears on the RECEIPTS side. Minimally corrected to: "A favourable closing balance is carried down on the payments side; a closing balance appearing on the **receipts** side is a **bank overdraft**." Reviewer to confirm the wording. q-f1c8-045 relies on the corrected position.
- [ ] **Life membership fees — full capitalisation, no split.** The notes and bank capitalise the whole receipt. q-f1c8-022 option B offers the "one year's ordinary subscription to income, balance capitalised" split found in some books and marks it wrong. Confirm the SM does not use that split.
- [ ] **Sale of old sports material credited in full.** q-f1c8-026, q-f1c8-029 and q-f1c8-044 credit the full proceeds of old sports material to I&E on the ground that the material was already expensed when consumed, while an asset sale yields only profit/loss. Where a question instead states that sports material is carried as stock and sold out of stock, the treatment would differ — confirm the SM states the full-proceeds rule for consumable scrap without that qualification.
- [ ] **q-f1c8-017 assumes every member is liable for the full year.** Accrued income is taken as 500 members × ₹600 with no allowance for members joining mid-year or for irrecoverable arrears. Confirm this is the standard SM/exam framing for the "members × rate" pattern before the question is treated as settled.
## inventories — VERIFY 2026-08-07

- [ ] **New chapter (Ch 4, Inventories) authored 7 Aug 2026** — notes, bank
  (counts), citations; reviewer should spot-check citations rows against SM Ch 4
  (May 2026 ed.). Shipped together: a 474-line MDX, a 51-question bank
  (45 MCQs · 6 descriptives, 25 machine-verified numericals, answer keys
  A 12 / B 11 / C 11 / D 11) and `citations/foundation/accounting/citations_inventories.md`.
- [ ] **Cash discount NOT deducted from the cost of inventories** — the chapter
  states this flatly (notes §4 pointer callout, worked example 3 working note 2,
  q-f1c4-015 option D, q-f1c4-017, d-f1c4-02 skeleton point 5). AS 2 names trade
  discounts, rebates and duty drawbacks as deductions and is silent on cash
  discount; the treatment taken here follows the Ch 2 financing-item position.
  Confirm the SM Ch 4 worked examples treat it the same way, since a full mark
  in an exam answer can turn on it.
- [ ] **Normal-wastage arithmetic in q-f1c4-021** — the ₹6,00,000 pool is spread
  over the 9,600 surviving kg (₹62.50/kg) so that the normal 400 kg carries no
  cost of its own, and the abnormal 600 kg is expensed at that rate. Confirm SM
  Ch 4 uses the same "normal loss absorbed by good units" convention rather than
  simply expensing the abnormal quantity at the gross rate of ₹60/kg (the B
  distractor).
- [ ] **Fixed-overhead allocation on normal capacity** (notes §4, q-f1c4-019,
  d-f1c4-02 skeleton point 3) — this is an AS 2 conversion-cost position but sits
  at the edge of Foundation depth. Confirm the SM Ch 4 states it at this level of
  detail; if it does not, the question can be softened to a pure inclusion test.
- [ ] **Cut-off: "sold and invoiced, awaiting collection" is EXCLUDED**
  (notes §10 table, q-f1c4-043 item (iv), d-f1c4-06 point (e)). This assumes
  title passed on invoicing rather than on delivery. Confirm the SM frames it the
  same way — a stem that turned on a retention-of-title clause would flip the
  answer.
- [ ] **AS 2 cited by subject, not by paragraph number** — the citations file
  deliberately names paragraphs by subject ("cost-of-purchase paragraph") rather
  than by number, to avoid asserting numbering the drafter could not verify
  against the current text. If the reviewer wants paragraph numbers in the
  citations file, they must be added from the ICAI text by hand.
- [ ] **MDX length** — 474 lines against a 320–380 brief. The overrun is content
  (10 numbered sections plus 5 worked examples), not padding; trim §1's scope
  callout or §8 if the house style is strict on length.
## bills-of-exchange-and-promissory-notes — VERIFY 2026-08-07

- [ ] **New chapter (Ch 6, Bills of Exchange and Promissory Notes) authored 7 Aug 2026** — notes (570-line MDX, 14 sections, 5 worked examples), bank (51 questions: 45 MCQs + 6 descriptives, 22 machine-verified numericals, key split A 12 / B 12 / C 11 / D 10), citations; reviewer should spot-check citations rows against SM Ch 6 (May 2026 ed.) and the NI Act text. **Every bare-act line in the citations file was transcribed rather than re-fetched from India Code in this session** — it must be diffed against Act 26 of 1881 on indiacode.nic.in before the chapter leaves `unreviewed`.

- [ ] **The rebate income/expense direction is asserted, and a whole cluster of answers depends on it.** Notes §11 and q-f1c6-041 state that a rebate allowed on retirement is an **expense in the holder's books** (Rebate on Bills / Discount Allowed A/c debited) and an **income in the acceptor's books** (Rebate A/c credited), on the reasoning that whoever grants the concession takes the debit. The same direction is stated in d-f1c6-05 skeleton point 5, and it is deliberately contrasted with renewal interest, which runs the other way (cost to the acceptor, income to the drawer, q-f1c6-040). Some texts label the holder's side "Rebate on Bills Discounted", which in a bank's books is a *liability* for unearned discount — a different animal entirely. Please confirm the SM's account names and direction for a non-bank trader, since reversing it would flip q-f1c6-041, d-f1c6-05 and the §11 callout together.

- [ ] **The exact holiday dates assumed, and the Saturday convention.** Every holiday question assumes **26 January, 15 August and 2 October** are notified public holidays (stated in the stems), plus Sundays under the s. 25 Explanation. It also assumes **Saturdays are ordinary business days** — notes §5 says so expressly, and q-f1c6-017's answer of **3 October 2026 (a Saturday)** depends entirely on it: 1 June + 4 months + 3 days grace = 4 October 2026, a Sunday, so s. 25 pulls it back one day to the Saturday. If the reviewer prefers the alternative convention, q-f1c6-017 and the verifier's `is_public_holiday()` must change together. Also confirm the ordering rule the whole set rests on: **grace is added first, and the holiday test is applied to the post-grace date** — q-f1c6-012 relies on this (28 February 2027 is itself a Sunday, but the answer is 3 March 2027 because only the post-grace date is tested).

- [ ] **The emergency-holiday rule has no quoted statutory authority.** q-f1c6-019 answers 7 August 2026 (next *succeeding* business day) for a maturity of 6 August 2026 declared an emergency holiday, and the same convention supplies the "moved forward" distractor in q-f1c6-015 to q-f1c6-018. Notes §5 presents it as settled commercial practice and the SM's treatment; the citations file flags it as a convention rather than a quoted provision because no line of the NI Act was found stating it in those words. Please either supply the authority or confirm that stating it as an SM/practice convention is acceptable at Foundation level.

- [ ] **The noting-charge recovery chain in endorsement and discounting cases.** The chapter asserts throughout that noting charges are **paid by the holder but borne by the party ultimately liable**, so they are added to the amount debited to the acceptor and are never the drawer's expense (q-f1c6-038, d-f1c6-04). Two consequences are asserted as absolutes and should be checked: (a) on dishonour of a **discounted** bill the credit is to **Bank** for face value *plus* noting charges, with Bills Receivable untouched (q-f1c6-028 answers ₹60,500, q-f1c6-037); (b) on dishonour of an **endorsed** bill the credit is to the **endorsee** for the same combined figure (notes §9 table, d-f1c6-04 point 4). The citations file records that the statutory recovery rule sits in **s. 117** but the exact clause was not verified — that reference needs confirming or dropping.

- [ ] **q-f1c6-030 computes the insolvency dividend on the amount owing INCLUDING noting charges.** Amount owing ₹25,000 + ₹300 = ₹25,300; dividend at 40 paise = ₹10,120; bad debts ₹15,180. The distractor at ₹15,000 is the version that works on face value alone. Notes §12 states the "whole amount owing" base explicitly. Confirm the SM computes the dividend on the same base, since a reviewer following the face-value convention would mark the keyed answer wrong.

- [ ] **Accommodation bills: proceeds shared at the start, FACE VALUE shared at maturity.** q-f1c6-024 (₹29,100, not ₹30,000), q-f1c6-031 (₹28,500) and q-f1c6-025 (₹900) all rest on splitting the **net proceeds** and the **discount** in the agreed ratio, while q-f1c6-044 and Worked example 5 switch to splitting the **face value** on the due date. The reconciliation check built into both (the accommodating party's net outgo ends up equal to exactly his own share of the discount) is the strongest evidence the pair of conventions is internally consistent, but a CA should confirm the SM presents both steps the same way.

- [ ] **No bank corrections were needed** — all 22 numerical questions recomputed to the bank's existing keys on the first verifier run (`22 numerical question(s) verified, 0 failure(s)`), including all 10 due-date questions, which the verifier derives with `datetime.date` arithmetic implementing ss. 22–25 rather than by lookup. Anchor self-check: `all 45 anchors ok against 17 headings`. No key or explanation was edited except a cosmetic reword of q-f1c6-012 option A, whose explanation had begun with the word "Correct" although it is a wrong option.

- [ ] **Notes length overruns the house target.** The MDX is 570 lines against the ~320–380 the brief asked for. The overrun is content, not padding: the mandated scope for this chapter is 14 distinct topics plus 5 worked examples, against the 9 sections and 4 examples in the Ch 5 exemplar. If a trim is wanted, the cheapest cuts without losing scope are the §7 four-fates table (duplicated in condensed form in the revision summary) and Worked example 1, which carries six sub-cases where four would teach the same rules.
## accounts-from-incomplete-records — VERIFY 2026-08-07

- [ ] **New chapter (Ch 9, Accounts from Incomplete Records) authored 7 Aug 2026** — notes (506-line MDX, 11 numbered sections plus 5 worked examples), bank (51 questions: 45 MCQs of which 26 are `numerical: true`, plus 6 descriptives; answer keys A 12 / B 11 / C 11 / D 11), citations (15 sections). All 26 numerical questions are recomputed independently by `scripts/verify_numerical/verify_accounts-from-incomplete-records.py` (0 failures) and all 45 `readLink` anchors resolve to real MDX headings. Reviewer should spot-check the citations rows against SM Ch 9 (May 2026 ed.) and initial each "Spot-checked by" line.
- [ ] **Bills-dishonour routing through the debtors and creditors accounts (q-f1c9-023, q-f1c9-027, q-f1c9-028, notes §9, worked examples 2 and 3).** Every one of these treats a dishonoured **bill receivable** as a DEBIT in the Total Debtors Account (so it *reduces* the credit sales that fall out as the balancing figure) and a dishonoured **bill payable** as a CREDIT in the Total Creditors Account (reducing the computed credit purchases). q-f1c9-028 goes one step further and asserts that a bill *previously discounted with the bank* and then dishonoured is still charged back to the customer through the Total Debtors Account, the bank not being the debtor. Please confirm both the routing and that the SM's own illustration nets the dishonour the same way; if the SM instead shows dishonoured discounted bills only through a separate Bank/B-R-discounted working, q-f1c9-028 is the question to re-check first. Noting charges were deliberately left out of every stem to avoid a second convention.
- [ ] **Mark-up vs margin stem wordings (q-f1c9-033, q-f1c9-034, q-f1c9-036, q-f1c9-037, q-f1c9-038, notes §11).** These stems turn entirely on two words. The wording used is "gross profit of 25% **on sales**" for a margin and "a mark-up of 25% **on cost**" for a mark-up, and in each numerical the *other* reading is deliberately planted as a distractor (₹1,30,000 in q-033, ₹11,16,000 in q-034, ₹8,00,000 in q-036, ₹12,70,000 in q-038). Please confirm (a) that this phrasing matches how the SM and recent ICAI papers word the two bases, and (b) that we are comfortable examining the distinction this hard when a careless reader loses the mark on a single preposition. q-f1c9-037 is the conceptual anchor for the pair and is flagged `numerical: false` even though it states percentages — confirm that classification is right for the practice engine.
- [ ] **Set-off between the two ledgers (q-f1c9-043, notes §7 and §8, worked example 2).** The bank puts the transfer on the **credit** of the Total Debtors Account and the **debit** of the Total Creditors Account, and worked example 2 folds a ₹9,000 set-off into the credit-sales computation. Confirm the SM presents set-off in the total accounts rather than only as a ledger-transfer journal entry, since q-f1c9-043's three distractors are all built on that placement.
- [ ] **Adjusted net-worth profit: which items move closing capital (q-f1c9-011, notes §4).** The stem pushes four adjustments through the *closing capital* — depreciation not provided (−), further bad debts (−), outstanding loan interest (−) and a bill receivable omitted from the assets (+) — and only then applies the formula. The omitted-asset item is the judgment call: it is added back, and the "₹2,08,000" distractor is the reader who deducts it with the other three. Confirm the SM works adjustments on closing capital rather than on the profit figure, and that interest on capital / interest on drawings being left to *after* the profit (notes §4) is how the SM sequences them.
- [ ] **q-f1c9-041, the omitted OPENING liability.** The bank marks the profit as *understated* by ₹20,000 (a dropped liability inflates opening capital, and a higher opening capital gives a lower profit). The stem says "omitted from the OPENING Statement of Affairs only" precisely so that the errors cannot cancel — please confirm the wording is tight enough that a reader cannot take the omission as running through both statements, since that reading makes option B defensible.
- [ ] **No arithmetic corrections were made to the MDX.** All five worked examples were re-checked by hand against the same conventions the verifier encodes (WE1 profit ₹1,12,000; WE2 credit sales ₹12,82,000 and total sales ₹14,37,000; WE3 acceptances ₹2,43,000 and credit purchases ₹11,17,000; WE4 stock at the fire ₹6,50,000 and loss ₹5,40,000; WE5 gross profit ₹4,05,000, net profit ₹1,33,000 and the closing capital tying to ₹4,13,000 from both directions) and every figure holds. Note for the reviewer: the notes run to 506 lines against a ~400-line drafting guide — in line with the sibling Ch 7 chapter, but trim §1/§4/§6 first if a length cap is being enforced.
## partnership-and-llp-accounts — VERIFY 2026-08-07

- [ ] **New chapter (Ch 10, Partnership and LLP Accounts) authored 7 Aug 2026** — notes (748-line MDX, 5 worked examples), bank (54 questions: 48 MCQs of which 28 are `numerical: true`, plus 6 descriptives; answer keys A 12 / B 12 / C 12 / D 12), citations (17 sections). All 28 numerical questions are recomputed independently by `scripts/verify_numerical/verify_partnership-and-llp-accounts.py` (0 failures) and all 48 `readLink` anchors resolve to real MDX headings. Reviewer should spot-check the citations rows against SM Ch 10 (May 2026 ed., all units) and initial each "Spot-checked by" line. **Note on length:** the brief asked for 420–480 lines; the file is 748 because the chapter carries six SM units plus five graded worked examples. Nothing was padded — if the length is a problem, the sub-sections to cut first are §10 "Annuity method" and the Memorandum Revaluation Account paragraph in §11.

- [ ] **Joint Life Policy was deliberately left OUT, of the notes and of the bank.** I could not establish with confidence whether the May 2026 edition of the Foundation SM still covers JLP under the "Death of a partner" unit (older editions did; the New Scheme SM appears to have dropped it, and it is squarely covered in Inter P1). Following the brief's instruction to omit when unsure, §13 covers only the executor's account and the profit to the date of death, and no question mentions JLP or a joint life policy reserve. **If the May 2026 SM does cover it, this chapter has a genuine scope gap** and needs a JLP sub-section in §13 plus two or three questions. Please confirm either way. The same doubt attaches, more weakly, to **dissolution of a firm**, which I have treated as outside Ch 10 entirely.

- [ ] **Charge-vs-appropriation classifications used throughout (notes §3 table, q-f1c10-006/007/008/009, d-f1c10-02).** The chapter treats as **charges**: interest on a partner's loan or advance, rent payable to a partner for his property, and a manager's salary/commission. It treats as **appropriations**: interest on capital, a partner's salary/commission, transfer to reserve, and the partners' shares of profit. q-f1c10-007 turns on both the rent and the loan interest being charges simultaneously, so if the SM classifies rent to a partner differently that one question breaks. Please confirm the table against the SM's own list.

- [ ] **The s.13(d) 6% position, and how far it has been extended.** The Act's 6% on a partner's advance is applied in three places: (i) interest on a partner's loan when the deed is silent (q-f1c10-004, q-f1c10-007, worked example 1 — where it is also the pivot of the "no deed" twist); (ii) a retiring partner's Loan Account (q-f1c10-040, notes §12); and (iii) a deceased partner's Executor's Account (notes §13). Extension (i) is straight statute. Extensions (ii) and (iii) are the standard SM/textbook position but rest on treating the outgoing partner's balance as money left with the firm rather than on the literal words of s.13(d). q-f1c10-040 examines (ii) as a single-best-answer MCQ — please confirm we are comfortable examining on it in that form. The chapter also states, as a consequence of the entitlement being independent of profits, that the interest is a **charge** and not an appropriation; that inference should be checked against the SM's own presentation of the Appropriation Account.

- [ ] **Scope boundary against the Intermediate P1 partnership refresher.** This Foundation chapter is written as the syllabus home of the topic and stands entirely alone: it does not link to, and copied nothing from, `src/pages/intermediate/advanced-accounting/partnership-accounts/goodwill-nature-valuation.astro`, `admission-of-a-partner.astro` or `retirement-of-a-partner.astro`. There is therefore deliberate doctrinal overlap (AS 26, sacrificing/gaining ratios, the four goodwill methods) between the two levels. Please confirm that is the intended editorial position rather than something to be de-duplicated, and check that the two treatments do not contradict each other — in particular the AS 26 "never raise goodwill" wording, which both pages assert.

- [ ] **Two computational conventions that decide MCQ keys and are worth a second pair of eyes.** (a) **Insufficient profit for appropriations** (q-f1c10-010, notes §4): the available profit is distributed *in the ratio of the amounts claimed*, so A receives ₹45,000 of the ₹75,000 available against a ₹60,000 entitlement. Some texts instead treat interest on capital as a charge when the deed so provides, which would give a different answer; the stem explicitly says "as an appropriation of profit" to close that door — confirm the wording is tight enough. (b) **Drawings with no dates** (q-f1c10-016, notes §6): the chapter takes 6 months as the convention, and distinguishes it from the 6.5-month beginning-of-month case. Confirm the SM states the 6-month default in those terms.

- [ ] **One draft error was caught and fixed by the verifier, not by review — worth knowing.** q-f1c10-024 (weighted-average goodwill) was originally drafted with a weighted average of ₹2,50,000 and goodwill of ₹7,50,000; recomputation showed the products total ₹26,00,000, not ₹25,00,000, so the correct figures are ₹2,60,000 and **₹7,80,000**. The question and its explanation were corrected. No other numerical mismatch arose. The five MDX worked examples were re-checked by hand (divisible profit ₹2,72,000 and the ₹2,44,000-each no-deed variant; goodwill ₹1,80,000 / ₹5,00,000 / ₹5,00,000; new ratio 12:8:5 with capitals ₹5,47,000 / ₹3,98,000 / ₹3,00,000; gaining ratio 1:2 with the ₹3,00,000 hidden-goodwill cross-check; executor's amount ₹3,60,000) and all figures hold, so the notes were left as drafted.
## company-accounts — VERIFY 2026-08-07

- [ ] **New chapter (Ch 11, Company Accounts) authored 7 Aug 2026** — notes (619-line MDX, 15 numbered sections, 5 worked examples), bank (54 questions: 48 MCQs of which 27 are `numerical: true`, plus 6 descriptives; answer keys A 12 / B 12 / C 12 / D 12), citations (21 sections). All 27 numerical questions are recomputed independently by `scripts/verify_numerical/verify_company-accounts.py` (0 failures) and all 54 `readLink` anchors resolve to real MDX headings. Reviewer should spot-check the citations rows against SM Ch 11 (May 2026 ed., Units 1–3) and initial each "Spot-checked by" line.
- [ ] **Bare-act lines were TRANSCRIBED, not fetched.** Sections 43, 52, 53, 39, 2(30) and Table F were written from memory in this session, not pulled from India Code, and the citations file carries a prominent provenance warning saying so. Please diff every quoted line against Act 18 of 2013 on indiacode.nic.in before the chapter leaves `unreviewed`. Two amendment traps in particular: the s. 52(2) proviso (omitted by the Companies (Amendment) Act 2017) and s. 53(2A) (the statutory debt-conversion exception inserted in 2017), both of which the notes rely on. The s. 53(3) penalty is deliberately not used anywhere.
- [ ] **Premium-on-forfeiture convention (q-f1c11-034, q-f1c11-035, q-f1c11-036, notes §10, worked example 3).** The whole chapter turns on one rule: premium **already received** is never written back (Securities Premium is left alone), while premium **called but not received** is debited back to Securities Premium alongside Share Capital. q-f1c11-034 marks ₹1,600 correct precisely because the ₹3,200 of premium received on application stays put, and q-f1c11-035 marks ₹600 (the unreceived ₹1 per share) rather than the whole ₹1,800. Please confirm the SM states the rule in these terms and that the ₹4,800 / ₹1,800 distractors are the ones a student would actually reach for.
- [ ] **Discount-on-reissue cap and the capital-reserve arithmetic (q-f1c11-038, q-f1c11-039, q-f1c11-040, q-f1c11-041, notes §11).** The bank treats the maximum discount on reissue as the amount forfeited **on those very shares** (so 1,500 shares with ₹3 per share forfeited may go no lower than ₹7 — q-f1c11-040), apportions the forfeited amount **per share** when only part of the holding is reissued (q-f1c11-039: ₹7,200 to capital reserve, ₹6,000 left in Share Forfeiture), and treats a reissue **above** face value as a fresh credit to Securities Premium that neither enlarges nor reduces the capital reserve (q-f1c11-041: ₹7,000, not ₹9,000 or ₹5,000). The verifier asserts the cap rather than assuming it. Confirm all three against the SM's own illustrations.
- [ ] **Table F rates presented as MAXIMUMS, not flat rates (q-f1c11-027, q-f1c11-028, notes §8, worked example 4).** Table F allows interest "not exceeding" 10% p.a. on calls in arrears and "not exceeding" 12% p.a. on calls in advance. Both stems therefore say "at the maximum rate Table F allows" so that the question has a single defensible answer. If the SM presents these as flat rates, the stems could be simplified — but if the reviewer prefers, the safer edit is to state the rate in the stem outright. Also confirm the related Table F points repeated in notes §5 (call ≤ 25% of nominal value, one month apart, 14 days' notice).
- [ ] **Kept deliberately out of scope, and said so in notes §15.** Redemption of preference shares, redemption of debentures (Debenture Redemption Reserve / sinking fund), and bonus and rights issues are treated as Intermediate topics and are excluded. Redeemable preference shares and redeemable debentures are still *mentioned* (notes §3, §12, §13) because Units 1 and 3 require it, and securities premium is described as usable for the premium payable on redemption (s. 52(d)). Please confirm this is where the Foundation boundary actually falls in the May 2026 SM — if the SM's Unit 3 does carry basic redemption entries, this chapter is short by a section.
- [ ] **Small-company rupee limits (notes §1 table).** The notes state the prescribed limits as "currently ₹4 crore and ₹40 crore" (Companies (Specification of Definitions Details) Rules, as amended 2022). These live in the Rules and move; no question turns on them — q-f1c11-002 examines the **exclusion list** only (public / holding / subsidiary / s. 8 / special-Act companies). Confirm the figures, or drop them to "the prescribed limits" if the reviewer would rather the notes carried no rules-level numbers at all.
- [ ] **Debenture-interest TDS mention (notes §14, q-f1c11-047).** The notes state that debenture interest is paid net of tax deducted at source, with the entry Debenture Interest A/c Dr … To Debentureholders A/c … To TDS Payable A/c. q-f1c11-047 tests only the ₹54,000 gross interest on face value and does **not** examine the TDS rate. Confirm the SM carries the TDS point at Foundation level; if it does not, the sentence can be deleted without touching any question.
- [ ] **No MDX corrections were made after drafting.** All five worked examples were re-checked arithmetically and hold: WE1 share capital ₹5,00,000 / securities premium ₹2,00,000 on ₹7,00,000 received; WE2 ratio 2:3, excess ₹90,000, allotment cash ₹2,07,200, Xavier unpaid ₹2,800; WE3 forfeiture entry balancing at ₹6,000 with capital reserve ₹300 and ₹600 left in Share Forfeiture; WE4 interest ₹200 and ₹360; WE5 loss on issue ₹36,000, issue entry balancing at ₹4,20,000, interest ₹48,000. The notes run 619 lines against a 380–450 line brief — the chapter covers three SM units and 15 numbered sections, so the overrun is content, not padding; trim §1, §4 or §12 first if a shorter page is wanted.
## revenue-based-as bank — VERIFY 2026-08-07

- [ ] **Question bank authored 7 Aug 2026** (38 MCQs · 8 descriptives · 4 case sets, 25 machine-verified numericals) — closes the 'no question bank yet' line in the 2026-07-19 revenue-based-as section; the 10-word shingle/overlap check against SM Ch 8 still needs a reviewer with SM access.
- [ ] **Escalation ceiling read as a gate, not a cap** (q-i1c8-009, and by implication worked example 1 in the notes). The stem says the whole labour increase passes "provided the rise in minimum wages does not exceed 25%", and the answer treats a 20% rise as passing the full ₹16 lakh. Confirm the ICAI convention that breaching the ceiling disqualifies the labour pass-through entirely rather than capping it at the ceiling percentage — the bank never tests the breach case precisely because that reading is unsettled.
- [ ] **Materials-at-site exclusion phrasing** (q-i1c8-018, cs-i1c8-02-a/b). Both stems say the cost-to-complete estimate "already allows for consuming" the unused site materials, so the materials are stripped from the numerator and are NOT added back to the estimated total cost. Confirm this is the intended reading of the SM illustrations, and that a reviewer is happy the stems make it unambiguous.
- [ ] **Gross amount due to customers on a loss contract** (cs-i1c8-02-d). The computation uses costs incurred *for work performed* (₹600 lakh, excluding the ₹40 lakh of steel at site), deducts the full ₹100 lakh recognised loss, and deducts progress billings gross of the ₹70 lakh retention while leaving the ₹90 lakh of advances out of the formula. Confirm each of those four choices against the SM presentation format; the sub-stem flags the first one expressly.
- [ ] **Provision vs loss recognised** (q-i1c8-017 option C, cs-i1c8-02-c). The bank distinguishes the loss *recognised* for the year (the full expected loss) from the *provision* to be created (expected loss less the loss the period's own revenue-less-cost figures already carry). Confirm the wording does not mislead students into providing the whole loss twice.
- [ ] **Completed-service vs proportionate boundary** (q-i1c8-036, and the installation-fee limb of q-i1c8-032). A one-machine installation is treated as a single act on the completed service contract method, while a four-visit AMC goes to proportionate completion. Confirm a CA is comfortable with the AMC being multi-act on these facts (the SM examples are less specific about visit-based contracts).
- [ ] **Agent's revenue out of a gross collection** (q-i1c8-026). The platform's revenue is only its ₹1,80,000 delivery charge, with GST excluded as a liability to government. Confirm the food-delivery fact pattern (which mirrors the notes' example with different figures) is still the position a CA would defend post-GST for an entity that does not take inventory risk.
- [ ] **AS 9 postponement disclosure** (d-i1c8-08, final skeleton point, 0.5 marks). This is the one position the bank cites that the notes do not state — the requirement to disclose the circumstances in which revenue recognition has been postponed. Confirm it against AS 9 and consider adding a sentence to the notes so the bank and the notes stay in step.
## preliminary — VERIFY 2026-08-07

- [ ] **New chapter (Inter P2 Ch 1, Preliminary) authored 7 Aug 2026 — FIRST chapter of Paper 2** — notes, bank (38 standalone MCQs + 6 descriptives + 3 case_mcq_sets with 10 subs; 11 questions flagged `numerical`), citations; reviewer should spot-check against SM P2 Ch 1 (May 2026 ed.) and the notified s.2 text. Because this is the first P2 chapter, also confirm that the paper-level conventions set here (frontmatter `paper: 'Paper 2 · Corporate &amp; Other Laws'`, `paperSlug: corporate-and-other-laws`, `masteryId: i2-ch1`, bank `paper: "Paper 2 — Corporate & Other Laws"`, question-id prefixes `q-i2c1-`/`d-i2c1-`/`cs-i2c1-`) are the ones the paper should carry, since Ch 2 onwards will copy them. Shared files (`src/data/intermediate.js`, `review_queue.md`, `site.js`) were deliberately NOT touched — the chapter still needs wiring into the paper index and the amendment-tracker page.

- [ ] **AMENDMENT-SENSITIVE · small-company thresholds (₹4 crore paid-up capital / ₹40 crore turnover, s.2(85) read with the Companies (Specification of Definitions Details) Rules).** These are **Rules-level** and have already been raised twice since 2013; they can change by notification without any amendment to the Act. Unlike the Foundation company-accounts chapter, **this chapter examines them directly**: q-i2c1-023, q-i2c1-025 and cs-i2c1-03-a are numerical questions decided by the figures, and notes §7 (with Vignette 3) and the one-page summary state them. The verifier holds them in the named constants `SMALL_CAPITAL_LIMIT` and `SMALL_TURNOVER_LIMIT` in `scripts/verify_numerical/verify_preliminary.py` so a change is a one-line edit — but the three stems/options, notes §7 and the summary row must move with it. Confirm the figures in force on the exam cut-off date, and confirm the Act-level ceilings (₹10 crore / ₹100 crore) quoted in notes §7 and d-i2c1-02.

- [ ] **AMENDMENT-SENSITIVE · s.2(87)(ii) reads "more than one-half of the TOTAL VOTING POWER", not total share capital.** The substitution was made by the Companies (Amendment) Act 2017. The whole of notes §9, Vignette 5, q-i2c1-032, q-i2c1-033 (numerical), cs-i2c1-01-c (numerical), the `_classify`/`_voting_pct` helpers in the verifier, common mistake 3 and the one-page summary depend on it, and several wrong options are deliberately built from the discarded share-capital reading. **Confirm the current wording and the notification date of the substitution.** While there, confirm the identical 2017 switch in the s.2(6) Explanation ("at least twenty per cent of total voting power"), on which q-i2c1-037 (numerical, the exactly-20.00% boundary) turns, and the s.47(2) position that non-voting preference shares are outside the general voting base — the chapter strips preference capital out of the "total voting power" denominator in two numerical questions on that footing.

- [ ] **AMENDMENT-SENSITIVE · s.2(41) financial-year alignment — current position stated is the CENTRAL GOVERNMENT.** The chapter states that the application under the proviso lies to the **Central Government** (jurisdiction having been shifted from the Tribunal/NCLT, with a transitional saving for pending applications), and that the applicants are a **holding, subsidiary OR associate** company of a company incorporated outside India. q-i2c1-038 is decided entirely by the granting authority, and its wrong-option explanation tells the student that "Tribunal" was the *earlier* position — so a wrong transcription breaks both the key and the teaching. d-i2c1-06 (point 4), notes §10 and its amendment callout, and the one-page summary carry the same statement. **Confirm the amending Act, its notification date, and whether "associate company" is in the notified proviso.**

- [ ] **BARE-ACT TRANSCRIPTION WARNING — every quoted line in `citations/intermediate/corporate-and-other-laws/citations_preliminary.md` was transcribed from memory in this session and NOT re-fetched from India Code.** Please diff each row against the notified text of Act 18 of 2013 on indiacode.nic.in and initial it. Rows carrying quoted bare-act text: **s.1 (extent + the s.1(4) application list — confirm the sub-section NUMBERING as well as the content), s.2(6), s.2(11), s.2(20), s.2(41), s.2(42), s.2(45), s.2(46) (confirm the "includes any body corporate" Explanation exists and is attached to 2(46), since q-i2c1-031 depends on it), s.2(52) (main limb + the 2020 proviso), s.2(62), s.2(68) (both provisos — diff word by word; this clause carries more marks than any other here), s.2(71) (definition + deeming proviso), s.2(85), s.2(87) (clause + proviso + Explanation (a)–(d))**. Also confirm the 2015 omissions of the ₹1 lakh / ₹5 lakh minimum capital figures (q-i2c1-012 turns on there being no minimum today).

- [ ] **RULES-LEVEL, summarised not quoted — confirm before the attempt.** (a) **Rule 2A, Companies (Specification of Definitions Details) Rules 2014** — the classes not to be considered "listed companies"; q-i2c1-030 and cs-i2c1-02-b turn on the private-company / privately-placed-NCD carve-out, and notes §8 carries an amendment callout. (b) **Companies (Restriction on Number of Layers) Rules 2017** — the two-layer ceiling and its carve-outs (wholly-owned-subsidiary layer not counted; foreign acquisition; banking/NBFC/insurance/Government exemptions); q-i2c1-036 states all of it in one option. (c) **Companies (Incorporation) Rules 2014, OPC provisions** — the 2021 relaxations (residency 120 days, NRIs permitted, conversion triggers omitted) are mentioned only in an amendment callout in notes §6; **no question turns on any OPC figure** — q-i2c1-021 uses the old ₹50 lakh figure solely as a wrong option whose explanation says the Rule was omitted. Confirm that framing is still safe.

- [ ] **Case law — names, years and propositions.** The veil-lifting table in notes §11, q-i2c1-007, q-i2c1-010 and d-i2c1-04 cite Salomon, Lee, Daimler, Gilford, Jones v Lipman, Dinshaw Maneckjee Petit, Workmen of Associated Rubber and LIC v Escorts **by name and proposition only**; all facts are restated in original words and **nothing is quoted from any judgment or textbook**. Check the propositions against the SM's own list — the SM's selection of veil authorities has varied between editions, and a mis-attributed proposition costs marks even where the underlying principle is right. Also confirm the statutory-lifting section numbers named (ss.34–35, 7(7), 339, 216/219) — they are named for orientation and no question turns on their content.

- [ ] **Numerical verifier is green but the LAW behind it needs a human.** `python3 scripts/verify_numerical/run.py --bank src/data/questions/intermediate/corporate-and-other-laws/preliminary.json` reports **11 numerical question(s) verified, 0 failure(s)**, and the anchor check passes (41 anchors against 18 headings). The verifier only proves the arithmetic is internally consistent with the stated legal rule — it cannot prove the rule. The three rules encoded are: member count = individuals + one per joint holding + post-employment purchasers (employees and continuing ex-employee members excluded, debenture-holders never counted); small company = not public AND capital ≤ limit AND preceding-FY turnover ≤ limit AND no exclusion, with "does not exceed" treated as inclusive (q-i2c1-025 tests only that); subsidiary/associate = voting power > 50% then ≥ 20%, tested step by step down a chain and never multiplied. Confirm each against the SM's worked treatment.
## incorporation-of-company — VERIFY 2026-08-07

- [ ] **New chapter (Inter P2 Ch 2, Incorporation) authored 7 Aug 2026** — notes, bank (38 standalone MCQs + 3 case_mcq_sets with 11 sub-MCQs + 6 descriptives; 9 numerical, all verifier-proven), citations; reviewer should spot-check against SM P2 Ch 2 (May 2026 ed.) and notified text.

- [ ] **Every statutory line in this chapter was transcribed from the Companies Act 2013 from memory — nothing was re-fetched from India Code or the MCA site in the authoring session.** The citations file (`citations/intermediate/corporate-and-other-laws/citations_incorporation-of-company.md`) carries a provenance warning and a per-section `Spot-checked by:` row, all blank. Diff each section's text, sub-section numbering AND amendment status before the chapter leaves `unreviewed`. Sections most likely to have moved: 3A, 4(5), 7(7), 9 (common seal), 10A, 12(1)/(2)/(4)/(9), 13(8), 14 (approver), 16(1)/(3).

- [ ] **Rules-level numbers flagged as amendment-sensitive — confirm none has moved.** (a) **Name-reservation validity: 20 days from the date of APPROVAL for a proposed new company, 60 days from approval for an existing company changing its name** (s. 4(5)(i) as amended — the section originally read 60 days from the date of APPLICATION). `q-i2c2-018` and `q-i2c2-019` are verified numericals that turn on both the period and the clock-start, so any change means reworking both questions and `verify_incorporation-of-company.py`. (b) The **fee-based extensions** of the reserved period and the prescribed list of words needing prior CG approval sit in the Companies (Incorporation) Rules and are deliberately NOT examined. (c) **OPC eligibility (Rule 3) and the 2021 omission of the mandatory-conversion thresholds of ₹50 lakh paid-up capital / ₹2 crore turnover (Rule 6)** are stated in an AMENDMENT-CHECK callout and are not examined. (d) **SPICe+ form names and the linked-services bundle** are described generically with no form number anywhere in the bank. (e) The **format of a name allotted by the CG under s. 16(3)** is rules-level and is not stated.

- [ ] **The s. 10A consequences chain — verify all three links and the trigger.** As stated: applies only to a company incorporated after the 2018 amendment AND having a share capital; declaration by a director **within 180 days of the date of incorporation** that every subscriber has paid, PLUS s. 12(2) verification, before commencing business or exercising borrowing powers; default → **₹50,000 penalty on the company**, **₹1,000 per day on each officer in default capped at ₹1,00,000**, and **strike-off exposure under Chapter XVIII** where nothing is filed inside the 180 days and the Registrar has reasonable cause to believe there are no operations. Examined in `q-i2c2-029` (verified numerical, 180-day date), `q-i2c2-030` (the chain, with "transactions become void" as the correct NOT-a-consequence answer) and Scenario 2 in the notes. Also confirm **s. 11 remains omitted** — `q-i2c2-031` and a mistake callout both treat it as dead law.

- [ ] **Pre-incorporation contract position as stated.** The notes and `d-i2c2-02` / `q-i2c2-009` / `q-i2c2-010` state: not binding on the company; **cannot be ratified** (no principal in existence); promoters personally liable; company bound only by a fresh contract (novation); and adoption possible under **Specific Relief Act ss. 15(h) and 19(e)** where the contract is warranted by the terms of the incorporation and the company has accepted it and communicated the acceptance. Confirm the SM still frames it this way and that the clause letters are as cited.

- [ ] **s. 14 approver — the highest-risk single point in the chapter.** `q-i2c2-035` answers that a **public → private conversion needs an order of the Central Government (power delegated to the Regional Director)**, with "an order of the Tribunal" as the named pre-amendment distractor. If the position has reverted or moved, that question inverts. Also confirm the three-way separation stated in the notes and the common-mistakes list: **NCLT** = s. 7(7) fraudulent incorporation; **RD** = s. 14 conversion and the intra-State inter-Registrar shift under s. 12; **CG** = s. 13(2) name change and s. 13(4) State-to-State shift.

- [ ] **s. 16 periods.** Three months (formerly six) to change the name after a CG direction, by **ordinary** resolution; three years for a trade-mark proprietor's application; fifteen days to notify the Registrar of the change; and on default the **CG allots a name** (the pre-2019 text imposed a fine instead). `q-i2c2-036`, `cs-i2c2-03-b` (verified numerical) and `cs-i2c2-01-c` (verified numerical, the parallel s. 4(5)(ii) three-month period) all depend on these.

- [ ] **Penalty figures deliberately excluded from the bank.** The s. 8(11) fine range and the fund named in s. 8(9) are stated only qualitatively in the notes because both have been recast by amendment; the s. 12(8), s. 15(2) and s. 17(2) figures appear in the notes but in no question. If a reviewer wants them examined, verify the current amounts first.

- [ ] **Frontmatter deviation to confirm.** `paper` is written as `'Paper 2 · Corporate & Other Laws'` with a raw ampersand, matching `src/data/intermediate.js` (`name: 'Corporate & Other Laws'`). The brief specified `&amp;`; YAML frontmatter is rendered as escaped text by NotesLayout, so `&amp;` would display literally. Ampersands inside the MDX **body** are escaped as `&amp;` per house style.
## indian-regulatory-framework — VERIFY 2026-08-07

- [ ] **New chapter (Foundation P2 Ch 1, Indian Regulatory Framework) authored 7 Aug 2026 — FIRST chapter of Paper 2** — notes (`src/pages/foundation/business-laws/indian-regulatory-framework.mdx`, 587 lines, 14 numbered sections + 3 vignettes), bank (`src/data/questions/foundation/business-laws/indian-regulatory-framework.json` — 40 standalone MCQs, 6 descriptives, 2 case_mcq_sets of 3 subs each = 46 keyed MCQs; key split A 12 / B 12 / C 11 / D 11), verifier (`scripts/verify_numerical/verify_indian-regulatory-framework.py`, 3 numerical questions, runner reports 0 failures), citations (`citations/foundation/business-laws/citations_indian-regulatory-framework.md`). Reviewer should spot-check the whole chapter against **ICAI SM Paper 2 Ch 1 (May 2026 ed.)**, which was **not read** while drafting — the section list follows the well-known scope of the chapter, not a verified table of contents.

- [ ] **Every constitutional and statutory line was transcribed from memory — nothing was fetched.** No India Code or official Constitution text was consulted in this session. The citations file carries a prominent provenance warning and marks five rows **CHECK CLOSELY**: Art. 13 (the notes blend the 13(1) "inconsistency" and 13(2) "contravention" formulas into one sentence); the Seventh Schedule List entries (given by subject name only, with **no entry numbers**, because they were not verified); the Art. 136(2) carve-out (rendered as "other than a court martial", which is a simplification of the Armed Forces wording); s. 469 of the Companies Act 2013 as the Companies (Incorporation) Rules' parent section; and the 1 July 2024 commencement of the three new criminal codes.

- [ ] **Judgment call — the chapter uses the new criminal codes (BNS / BNSS / BSA), not IPC / CrPC / Evidence Act.** As on 28 Feb 2026 that is the correct law, and §11, the amendment callout and d-f2c1-05 are drafted on it. **But the May 2026 SM edition may still print the old names.** If it does, decide whether to (a) keep the new names with the existing amendment callout that flags the change, which is what has been done, or (b) mirror the SM. No MCQ key turns on the *name* of the code — q-f2c1-032 and q-f2c1-033 examine standard of proof and the party/document/outcome vocabulary — so a change here is a prose edit only.

- [ ] **Judgment call — pecuniary-jurisdiction figures are hypothetical and stated inside each stem.** Real pecuniary limits are fixed State by State, so asserting any would date the chapter and be wrong for most students. Every routing stem (q-f2c1-030, cs-f2c1-01) therefore supplies its own limits, and `verify_indian-regulatory-framework.py` takes those limits as **parameters** rather than hard-coding a State's figures. Related call: these three questions were flagged `"numerical": true` and given verifier functions even though the answer is a court name rather than a rupee figure, because the routing genuinely turns on arithmetic (₹15,00,000 + ₹1,80,000 vs a ₹15,00,000 ceiling). If house convention would treat threshold-routing as non-numerical, unflag them and delete the verifier module — the keys are unaffected.

- [ ] **Judgment call — conciliator "may propose terms" vs mediator "facilitates only" is the pivot of q-f2c1-035 and of the ADR pointer callout.** The distinction is standard (Arbitration and Conciliation Act 1996 Part III vs the Mediation Act 2023), but SM treatments vary in how sharply they draw it, and the Mediation Act 2023 is recent enough that older material describes mediation and conciliation as interchangeable. Confirm the SM's line before the question goes live; if the SM does not draw the distinction, q-f2c1-035 option A/C should be rewritten around a different contrast.

- [ ] **Judgment call — length.** The brief asked for ~260–330 lines; the file is 587 (≈5,500 words), close to the Inter P2 Ch 1 exemplar's 590. The mandated scope covers 12 distinct topics plus 3 vignettes, traps and a revision summary, and cutting to 330 lines would reduce most topics to two sentences. Trim if the house standard for a Foundation intro chapter is firm — the most compressible parts are §14 (statutes/regulators table) and the one-page revision summary.

- [ ] **Two institutional numbers are stated in prose and will age:** the Supreme Court's sanctioned strength (**34**) and the number of High Courts (**25**). Both are stated with hedging in §9 and repeated in the revision summary, and **no question in the bank turns on either** — deliberately. Confirm both, or drop them to "a Chief Justice and other judges" / "one for each State, some serving more than one".

- [ ] **All illustrative statutory provisions in §6, §13, vignettes 1 and 3, and cs-f2c1-02 are FICTIONAL** ("section 12", "section 14", "sections 30 and 41") and are labelled as such in the text. Check that every occurrence still reads as invented, so that no student cites them as real law. This was chosen over using a real section because the bare-act-reading skill needs a provision with a proviso, an explanation and an illustration all visible at once.
## indian-contract-act-1872 — VERIFY 2026-08-07

- [ ] **New chapter (Foundation P2 Ch 2, The Indian Contract Act 1872) authored
  7 Aug 2026** — notes (six SM units mapped to 24 numbered sections, 6 worked
  scenarios), bank (48 standalone MCQs, 4 case_mcq_sets with 15 sub-MCQs,
  8 descriptives; 10 numericals, all verifier-proven; answer keys A16/B16/C16/D15),
  citations (`citations/foundation/business-laws/citations_indian-contract-act-1872.md`).
  Reviewer should spot-check the whole chapter against **ICAI SM Paper 2 Ch 2
  (May 2026 ed.)** and the notified text of Act 9 of 1872 on India Code. This is
  the heaviest chapter in the paper (roughly 30–40% of marks), so nothing here
  should go live unreviewed.

- [ ] **Postal-rule statements as examined (ss. 4 and 5)** — three numericals and
  one case set turn on the exact deadlines. Confirm all four propositions as the
  SM states them: (i) an acceptance is complete against the PROPOSER when posted;
  (ii) it is complete against the ACCEPTOR when it reaches the proposer; (iii) the
  proposer may revoke *before or at the moment* the acceptance is posted, and his
  revocation binds the offeree only when it REACHES him; (iv) the acceptor may
  revoke *before or at the moment* the acceptance reaches the proposer. The
  verifier treats deadlines (iii) and (iv) as **inclusive** of the posting and
  delivery dates. Affected: q-f2c2-009, q-f2c2-010, q-f2c2-011, cs-f2c2-01-c,
  cs-f2c2-01-d, notes §5 and worked scenario 1. If the SM phrases any deadline
  differently, question, option set and `verify_indian-contract-act-1872.py` must
  move together — never edit the key alone.

- [ ] **The s. 74 Indian-position phrasing** — the notes say: no distinction
  between liquidated damages and a penalty; the court awards *reasonable
  compensation not exceeding* the sum named; the named sum is a **ceiling, never
  an automatic entitlement**; and the words "whether or not actual damage or loss
  is proved" relieve a claimant whose loss is hard to quantify but do not hand
  the named sum to a claimant with no loss at all. **That last sentence is the
  most contestable proposition in the chapter** and SM editions summarise it
  differently. Affected: q-f2c2-043 (numerical, capped award ₹8,00,000),
  cs-f2c2-04-d, notes §21, d-f2c2-07 points 5–6. Also confirm the Exception
  (bail bonds and bonds under a Government direction recover the whole sum) and
  the Explanation on increased interest as a penalty.

- [ ] **Minor and necessaries nuances (ss. 11, 68 and the Majority Act)** — four
  points to verify against the SM, each of which a question depends on: (i) the
  age of majority is stated as **18 for everyone**, with a note that the 21-year
  limb for court-appointed guardianship was removed by the Indian Majority
  (Amendment) Act 1999 — **several SM editions still print 21**, so decide which
  the notes should lead with (no question turns on the figure, by design);
  (ii) s. 68 gives a claim **against the incapable person's property only, never a
  personal decree** (q-f2c2-020, worked scenario 2 point 4); (iii) **no estoppel**
  against a minor who misrepresents his age, but equity may order restoration of
  what is **still traceable** in his hands and nothing more (q-f2c2-021 option B,
  worked scenario 2 point 3 — the ₹50,000 spent on the holiday is stated as
  irrecoverable); (iv) **no ratification** after majority without fresh
  consideration (q-f2c2-019).

- [ ] **Every transcription warning in the citations file** — all bare-act lines
  and all nine quoted illustrations were transcribed from the Act, **not
  re-fetched from India Code in this session**. Diff each quoted row against
  indiacode.nic.in (Act 9 of 1872) and initial the "Spot-checked by" line. Give
  particular attention to: the illustration **letters** (the chapter avoids
  letters everywhere except in the citations commentary, deliberately); the
  **₹500 horse-race threshold** in s. 30; the **one-year floor** in Exception 3 to
  s. 28 (inserted 2013); and the **s. 15 / Indian Penal Code** reference now read
  as the Bharatiya Nyaya Sanhita 2023 (in force 1 July 2024) — the notes carry an
  amendment callout in §11, and **no question turns on the name of the penal
  statute**.

- [ ] **Unit-scope doubts against the SM** — five judgment calls where the SM's
  own arrangement should decide: (i) the **presumption table** of relationships
  under s. 16(2) in notes §11 is the SM's list, not the Act's — confirm the
  entries, especially "creditor and debtor in urgent need: yes" and "husband and
  wife: no" (q-f2c2-025 examines only the husband-and-wife negative);
  (ii) *Chikham Amiraju* (threat of suicide = coercion) is mentioned in notes §11
  as a case anchor but **deliberately not examined**, because it rests on the
  pre-2024 penal law — check whether the notified SM still carries it;
  (iii) the **wagers are void but not illegal** point and the **Gujarat and
  Maharashtra** carve-out in notes §15 rest on State legislation, not this Act —
  confirm the SM covers it and that no question depends on it (none does);
  (iv) the **finder of goods** detail in notes §24 (lien, reward, power of sale,
  two-thirds-of-value threshold) actually comes from **ss. 168–169** in the
  bailment chapter — decide whether it belongs here or should be trimmed to
  "same responsibility as a bailee"; (v) the **anticipatory-breach election** in
  q-f2c2-041 (contract stays alive for both parties, so intervening frustration
  saves the guilty party, and damages then run from the performance date) is case
  law rather than statute — confirm the SM states it in those terms.

- [ ] **Length and readTime** — the notes run ~1,650 lines / ~18,000 words, well
  beyond the ~700–800 lines the chapter brief estimated, because the six SM units
  span ss. 2 to 75. `readTime` is set to "About 65 min read". A human should
  decide whether to keep it as one long chapter, split it into two pages (Units
  1–3 and Units 4–6), or trim §§16–18 (performance detail), which is the densest
  and least heavily examined stretch.
## sale-of-goods-act-1930 — VERIFY 2026-08-07

- [ ] **New chapter (Foundation P2 Ch 3, The Sale of Goods Act 1930) authored
  7 Aug 2026** — notes (18 numbered sections plus mistakes list and one-page
  summary, 5 application vignettes with working notes), bank (44 standalone
  MCQs, 3 case_mcq_sets with 11 sub-MCQs, 7 descriptives; 7 numericals, all
  verifier-proven; answer keys A14/B14/C13/D14 over 55 MCQs), citations
  (`citations/foundation/business-laws/citations_sale-of-goods-act-1930.md`).
  Reviewer should spot-check the whole chapter against **ICAI SM Paper 2 Ch 3
  (May 2026 ed.)** and the notified text of Act 3 of 1930 on India Code. The
  bare-act lines were transcribed, not re-fetched, so the sub-section lettering
  of ss. 16, 17, 24, 25, 30, 37, 47, 49, 51 and 64, and the whole of the s. 2
  definition numbering, need a line-by-line diff.

- [ ] **Day-counting on a fixed sale-or-return period (s. 24(b)).** Two answers
  depend on it: q-f2c3-031 (20 days from delivery on 6 March 2026 → property
  passes 26 March 2026) and step 1 of vignette 4 (15 days from 2 March 2026 →
  17 March 2026). The chapter counts a period expressed in days **from and
  excluding** the trigger date, matching the convention used for offer-lapse in
  the Contract Act chapter. The Act itself says only "on the expiration of such
  time", so if the SM or a past ICAI answer counts inclusively, both dates move
  back one day and the verifier's `_add_days` must change with them.

- [ ] **s. 54(2) — who takes the profit, and whether expenses ride along.**
  q-f2c3-042 (notice given, seller keeps the ₹75,000 surplus), q-f2c3-043 (no
  notice, buyer takes the ₹54,000 profit) and cs-f2c3-03-b (notice given,
  seller recovers a ₹60,000 deficiency) all rest on reading the second half of
  s. 54(2) as a genuine forfeiture rule rather than as a mere evidential
  presumption. cs-f2c3-03-b additionally **excludes the ₹22,000 redelivery cost
  of the stoppage** from the recoverable deficiency, on the strength of s. 52(2)
  putting those expenses on the seller; the wrong option is exactly ₹82,000.
  If the SM treats redelivery costs as recoverable damages under s. 54(2)
  instead, that key flips.

- [ ] **Insolvency without adjudication (s. 2(8)) as the trigger for stoppage.**
  Vignette 3 and cs-f2c3-03-a both hold that bounced cheques and stopped
  payments are enough, with no petition filed. That follows the statutory
  definition, but the facts are deliberately thin (three cheques, supplier
  payments stopped) and a reviewer may want the vignette to state a clearer
  cessation of payment before students are taught to stop goods on that much.

- [ ] **The hire-purchase / s. 30(2) proposition.** q-f2c3-036, cs-f2c3-01-d and
  the §3 comparison table all turn on a hirer having an **option** to buy and so
  not being a person who has "agreed to buy". Settled law, but it is stated from
  the case law as the SM presents it, not from statutory words, and it is the
  single point on which an innocent third party loses everything. Confirm the SM
  still teaches it this way and that the Hire Purchase Act 1972 is the reference
  the May 2026 edition uses.

- [ ] **Scope calls made without the SM in front of me.** (i) The chapter treats
  **s. 64A** (change in duty or tax) at the level of principle only, because its
  post-GST wording needs checking — confirm whether the SM examines it at all.
  (ii) **s. 53** (sub-sale or pledge by the buyer, with the document-of-title
  provisos) is stated in full in §16 although it is often skipped at Foundation
  level; drop it if the SM does. (iii) The **nine** exceptions to s. 27 include
  the finder (Contract Act s. 169), the pawnee (s. 176) and sales under statute
  or court order, which some presentations leave out; d-f2c3-05 marks them at
  only 0.5 of 6 so the skeleton survives either way. (iv) The notes are
  **1,402 lines**, roughly double the 600–750 the brief suggested — the scope
  list (every s. 27 exception, ss. 31–44 and ss. 45–56 in full, five vignettes)
  did not compress further without dropping content, but a trim pass is
  available if length is a hard constraint.
## indian-partnership-act-1932 — VERIFY 2026-08-07

- [ ] **New chapter (Foundation P2 Ch 4, The Indian Partnership Act 1932)
  authored 7 Aug 2026** — notes (22 numbered sections plus mistakes list and
  one-page summary, 5 application vignettes with working notes, 1,424 lines),
  bank (44 standalone MCQs, 3 case_mcq_sets with 12 sub-MCQs, 7 descriptives;
  7 numericals, all verifier-proven; answer keys A14/B14/C14/D14 over 56 MCQs),
  citations (`citations/foundation/business-laws/citations_indian-partnership-act-1932.md`).
  Reviewer should spot-check the whole chapter against **ICAI SM Paper 2 Ch 4
  (May 2026 ed.)** and the notified text of Act 9 of 1932 on India Code. The
  bare-act lines were transcribed, not re-fetched, so the sub-section numbering
  of ss. 19, 30, 32, 44, 48 and 69 needs a line-by-line diff.

- [ ] **The eight exclusions in s. 19(2), as transcribed.** §13.1 lists them in
  order and letters them (a) arbitration, (b) banking account in his own name,
  (c) compromise or relinquish a claim, (d) withdraw a suit, (e) admit liability,
  (f) acquire immovable property, (g) transfer immovable property, (h) enter into
  partnership. Four questions (q-f2c4-024, q-f2c4-025, q-f2c4-027 and d-f2c4-03,
  which carries 3.5 of its 7 marks on the list) depend on both the membership and
  the lettering. If the notified text orders the clauses differently, the
  citations in the skeleton and in the option explanations must move with it.
  Also confirm that the chapter is right to treat **engaging a lawyer to defend a
  suit against the firm** as inside implied authority (the correct answer to
  q-f2c4-024) — the list bars withdrawing, compromising and admitting, not
  defending, but the SM may state this differently.

- [ ] **The s. 69 exception list in §18.3.** Eight exceptions are given: third
  party suing the firm; dissolution; accounts of a dissolved firm; realisation of
  the property of a dissolved firm; powers of an Official Assignee, Receiver or
  Court; claims not exceeding **₹100**; notified areas under s. 56; and claims
  arising otherwise than out of a contract. Two of those need care. The **₹100
  figure** is the only rupee amount in the chapter taken from the Act and is the
  likeliest to have drifted or to be presented by the SM with the Presidency
  Small Cause Court qualification spelt out. And the **non-contractual claim**
  exception is stated as a general proposition rather than from a sub-clause; if
  the SM does not teach it, drop the eighth bullet — no question depends on it
  alone, though d-f2c4-04 gives it 0.5 of 8 marks. Separately, the chapter states
  flatly that **registration after institution does not cure the defect**
  (q-f2c4-034 option D, cs-f2c4-03-a option D); that is settled law but is stated
  from principle, not from statutory words.

- [ ] **The s. 48(b) order and the rateable abatement.** Three questions and one
  vignette turn on it. q-f2c4-041 pays Deepa ₹17,00,000 on the full waterfall,
  and q-f2c4-042 abates capital **rateably** where ₹9,00,000 is available against
  capitals of ₹12,00,000, giving Q ₹3,00,000 rather than his full ₹4,00,000.
  The rateable reading comes from the words "rateably" in s. 48(b)(ii) and (iii);
  if the SM instead teaches the *Garner v Murray* style treatment for a capital
  deficiency at Foundation level, q-f2c4-042 needs rewriting. Note that this
  chapter deliberately keeps the accounting treatment out: the realisation
  account, capital-account adjustments and Garner v Murray belong to **Foundation
  P1 Ch 10 (Partnership and LLP Accounts)** and are not repeated or linked here.

- [ ] **The boundary against the P1 accounting chapter.** Only the headings of
  `src/pages/foundation/accounting/partnership-and-llp-accounts.mdx` were read,
  to avoid duplication. Three topics sit close to the seam and are treated here
  as **law only**: interest on capital and on advances (§11 gives the s. 13(c)
  and 13(d) rules and one arithmetic example, but no P&amp;L appropriation
  account), goodwill (§20 gives s. 55 only, no valuation methods), and the
  outgoing partner (§17 gives the s. 37 option, not the retirement entries).
  Confirm that this is the split the site wants, and that nothing in P1 now
  contradicts the 6% figures used here.

- [ ] **Two propositions stated from drafting or principle rather than from
  quoted words.** (i) That **ss. 9 and 10 are absolute** while ss. 12 and 13 are
  "subject to contract" — this chapter infers it from the opening words of the
  sections and from s. 23 of the Contract Act, and q-f2c4-029 (an option in the
  bank) and the §10 pointer both rest on it. (ii) That a **firm cannot be a
  partner in another firm** while a company can (q-f2c4-004 was dropped from the
  final bank but the proposition survives in §2 and in the one-page summary).
  Both are standard, neither is quoted.

- [ ] **Length.** The notes run to **1,424 lines** against the 600–800 the brief
  suggested. The scope list (ss. 4 to 55 plus registration, four comparison
  tables, the full s. 19(2) and s. 44 lists, five vignettes, a 20-item mistakes
  list and a one-page summary) did not compress further without dropping
  examinable content, but a trim pass on §4 (the four comparison tables) and §20
  (ss. 49 to 53, which some presentations skip at Foundation level) is available
  if length is a hard constraint.

## llp-act-2008 — VERIFY 2026-08-10

- [ ] **New chapter (Foundation P2 Ch 5, The Limited Liability Partnership Act
  2008) authored 10 Aug 2026** — notes (18 numbered sections plus mistakes list
  and one-page summary, 5 application vignettes with working notes), bank
  (44 standalone MCQs, 3 case_mcq_sets with 11 sub-MCQs, 7 descriptives;
  8 numericals, all verifier-proven; answer keys A14/B14/C14/D13 over 55 MCQs),
  citations (`citations/foundation/business-laws/citations_llp-act-2008.md`).
  Reviewer should spot-check the whole chapter against **ICAI SM Paper 2 Ch 5
  (May 2026 ed.)** and the notified text of Act 6 of 2009 **as amended by the
  LLP (Amendment) Act 2021 (Act 31 of 2021)** on India Code. The bare-act lines
  were transcribed, not re-fetched, so the whole of the s. 2(1) definition
  lettering (the clauses are alphabetical and (ta) was inserted into the
  sequence in 2021) and every penalty quantum need a line-by-line diff.

- [ ] **Every penalty figure is a 2021-amendment figure and none was
  re-fetched.** The chapter states s. 10 (₹10,000 / ₹5,000 plus ₹100 a day,
  capped at ₹1,00,000 and ₹50,000 for the LLP, ₹50,000 and ₹25,000 for a
  partner), s. 13(4) (₹500 a day capped at ₹50,000), s. 25(4) and 25(5)
  (₹10,000), s. 69 (₹100 a day), s. 74 (₹5,000 to ₹5,00,000 plus ₹50 a day),
  s. 76A (half penalty, capped at ₹1,00,000 / ₹50,000), s. 20, s. 30(2) and
  s. 37 (fine bands). Two of them carry answer keys — **q-f2c5-009** (₹50,000,
  the s. 13(4) cap applied to 132 × ₹500 = ₹66,000, which is the distractor)
  and **q-f2c5-032** (₹3,700 on a 37-day delay at the s. 69 rate). Both rates
  and the cap live as named constants at the top of
  `scripts/verify_numerical/verify_llp-act-2008.py`, so a correction is a
  one-line change. The chapter deliberately **omits** the s. 34(5) and s. 35(2)
  quanta because the pre- and post-2021 texts differ; add them if the SM states
  them.

- [ ] **The audit threshold, read as a disjunction.** Rule 24 of the LLP Rules
  2009 words the exemption with "or" between two negative limbs, which read
  literally would exempt an LLP satisfying either limb. The chapter follows the
  settled reading — **audit required if turnover exceeds ₹40,00,000 OR
  contribution exceeds ₹25,00,000**, exemption only where both are below — and
  states it in a formula box in §15, in vignette 3 and in the mistakes list.
  **q-f2c5-030** is written on it (turnover ₹42,60,000, contribution
  ₹18,00,000 → audit required). If the SM takes the literal disjunctive
  reading, that key flips to "no audit". Related and deliberately contrasted:
  the **small LLP** definition in s. 2(1)(ta) is treated as **cumulative** (both
  limbs), which carries **q-f2c5-006**. Please confirm both conjunctions.

- [ ] **Day-counting and month-counting conventions.** The chapter counts a
  period expressed in DAYS **from and excluding** the trigger date (matching the
  Sale of Goods s. 24 convention), and adds MONTHS by calendar with clamping to
  the month end, so six months from 31 March is 30 September. Four answers rest
  on it: **q-f2c5-031** (60 days from 31 March 2027 → 30 May 2027),
  **q-f2c5-032** (Form 8 due 30 October 2027, 37 days late), **cs-f2c5-03-b**
  (15 days from 20 August 2026 → 4 September 2026, with the inclusive count,
  3 September, as a distractor) and **cs-f2c5-02-c** (six months from
  14 April 2026 → 14 October 2026). Vignettes 3, 4 and 5 use the same
  conventions in prose. If the SM counts inclusively, every one of those dates
  moves back a day and `_add_days` / `_add_months` in the verifier must change
  with them.

- [ ] **s. 6(2) — which obligations reach the sole partner.** **cs-f2c5-02-c**
  computes ₹23,80,000 on the footing that only obligations incurred **after**
  the six months have run reach the sole partner personally, the ₹11,50,000
  incurred inside the six months staying with the LLP under s. 27(3). That
  reading comes from "for more than six months" and "incurred during that
  period". Vignette 5 teaches the same split. If the SM reads the liability as
  attaching to everything from the date the number fell below two, the key
  becomes ₹35,30,000, which is option A.

- [ ] **s. 64 — the omitted "unable to pay its debts" ground.** **q-f2c5-043**
  makes that a wrong option, on the footing that clause (c) was omitted by
  Act 31 of 2021 because LLP insolvency moved to the IBC 2016. This is the
  single proposition in the chapter most likely to be out of step with an older
  study material or an older question bank, and it should be confirmed against
  the amended s. 64 and its commencement notification before the draft badge
  comes off.

- [ ] **The 120-day residence test for a designated partner.** §9,
  **q-f2c5-018** and d-f2c5-06 all use 120 days (Explanation to s. 7(1), as
  substituted in 2021), and q-f2c5-018 is written so that the older 182-day
  answer is an explicit distractor. Confirm the substitution is in force for the
  Sept 2026 and Jan 2027 attempts.

- [ ] **Two negative propositions taught as headline traps.** (i) The chapter
  asserts that the **First Schedule contains no provision for interest** on
  contribution or on advances, and the mistakes list teaches students not to
  import the six per cent from s. 13(d) of the 1932 Act. A negative proposition
  cannot be verified from memory — please read the Schedule through. (ii) The
  chapter asserts that there is **no provision corresponding to s. 30 of the
  1932 Act**, so a minor cannot be admitted even to the benefits of an LLP.
  Both appear in §3, §8, §10 and the one-page summary. The chapter also states
  the First Schedule has **thirteen** clauses; confirm the count.

- [ ] **Rule-level and practice-level detail stated without a statutory
  anchor.** (i) The **RUN-LLP / FiLLiP / Form 3 / Form 4 / Form 8 / Form 11**
  table in §6 and the compliance calendar in §15 are MCA practice, and the claim
  that **FiLLiP allows DPIN to be applied for by at most two** proposed
  designated partners changes with the form. (ii) The **50-person ceiling** on a
  general partnership (s. 464 of the Companies Act 2013 with r. 10 of the
  Companies (Miscellaneous) Rules 2014) appears in §2 and the §3 table. (iii)
  **s. 18** is stated in §7 without a limitation period, on purpose, because the
  2021 amendment altered it — supply the period if the SM gives one. (iv)
  **s. 75** striking-off uses a **two-year** inactivity period from the rules,
  not the section. No answer key depends on (ii), (iii) or (iv); (i) supports
  q-f2c5-032 only through the Form 8 due date.

- [ ] **Scope calls made without the SM in front of me.** (i) **s. 31 (whistle
  blowing)** and **s. 42 (transferable interest)** are treated at full section
  depth with a question each (q-f2c5-036, q-f2c5-039); both are sometimes
  skipped at Foundation level — drop them if the SM does. (ii) **s. 39
  compounding**, **s. 74 general penalty** and **s. 76A half penalties** are
  compressed into §18 alongside winding up; only q-f2c5-044 tests them, and it
  turns solely on "fine only" and on the sum lying between the minimum and the
  maximum fine, so it survives a change in the compounding authority or period.
  (iii) The chapter treats **conversion** at Schedule-condition depth including
  the twelve-month correspondence statement and the preservation of partners'
  pre-conversion liability (vignette 4, cs-f2c5-03-c); trim if the SM gives
  conversion only an outline. (iv) The notes are **1,592 lines**, above the
  1,200–1,500 the brief suggested — the scope list (LLP against both a firm and
  a company in full tables, the whole First Schedule, ss. 26 to 31 in full, five
  vignettes) did not compress further without dropping content, but a trim pass
  is available if length is a hard constraint.

## companies-act-2013 — VERIFY 2026-08-10

- [ ] **New chapter (Foundation P2 Ch 6, The Companies Act 2013) authored
  10 Aug 2026** — notes (18 numbered sections plus mistakes list and one-page
  summary, 5 application vignettes with working notes, 1,223 lines), bank
  (44 standalone MCQs, 3 case_mcq_sets with 12 sub-MCQs, 7 descriptives;
  8 numericals, all verifier-proven; answer keys A14/B14/C14/D14 over 56 MCQs),
  citations (`citations/foundation/business-laws/citations_companies-act-2013.md`).
  Reviewer should spot-check the whole chapter against **ICAI SM Paper 2 Ch 6
  (May 2026 ed.)** and the notified text of Act 18 of 2013 on India Code. The
  bare-act lines were transcribed, not re-fetched, so the whole of the s. 2
  definition numbering used here — 2(6), 2(11), 2(20), 2(21), 2(22), 2(42),
  2(45), 2(46), 2(52), 2(62), 2(68), 2(69), 2(71), 2(85), 2(87), 2(92) — needs a
  line-by-line diff.

- [ ] **HIGHEST DRIFT RISK — the small-company thresholds are set by RULES, not
  by the Act.** ₹ 4,00,00,000 paid-up capital and ₹ 40,00,00,000 turnover are
  prescribed by the Companies (Specification of Definitions Details) Rules 2014
  as amended, and have already moved twice (₹ 50 lakh / ₹ 2 crore as enacted,
  then ₹ 2 crore / ₹ 20 crore, then the present figures). They can be raised
  again by notification with no amendment to the Act. Two verified numericals
  depend on them: **q-f2c6-024** (₹ 3.20 crore capital, ₹ 44 crore turnover →
  NOT small, built with a comfortable margin) and **cs-f2c6-02-c** (₹ 3.90 crore
  and ₹ 38 crore → small, which sits close to the line and is the fragile one).
  If the Rules change, update both stems **and** the two constants
  `SMALL_COMPANY_CAPITAL_LIMIT` / `SMALL_COMPANY_TURNOVER_LIMIT` at the top of
  `scripts/verify_numerical/verify_companies-act-2013.py`. Also confirm the
  statutory ceilings of ₹ 10 crore and ₹ 100 crore quoted in §10.

- [ ] **s. 2(87)(ii) — "total voting power" versus "total share capital".**
  q-f2c6-027 exists only because the Companies (Amendment) Act 2017 substituted
  "total voting power"; its 67 per cent paid-up-capital distractor is the whole
  point, and if the older wording were in force the key would flip from B to A.
  The same amendment is what makes vignette 3(a) work. Confirm the substitution
  is notified and in force as on 28 Feb 2026.

- [ ] **s. 2(87)(ii) — "either at its own or together with one or more of its
  subsidiary companies".** cs-f2c6-02-b adds Suvarna's own 34 per cent to its
  subsidiary Bhagirathi's 19 per cent to reach 53 per cent and a subsidiary
  relationship. The whole question rests on those words being in the notified
  clause; without them the answer is 34 per cent and an associate relationship
  (option B). Please check the exact phrase.

- [ ] **The 20.00 per cent boundary in s. 2(6).** q-f2c6-029 is decided at
  exactly 20.00 per cent (3,00,000 of 15,00,000 votes) on the reading that
  "significant influence" means control of **at least** twenty per cent, so the
  boundary is inclusive. If the notified Explanation reads "more than twenty per
  cent", the key moves from A to C. The deliberate contrast with the exclusive
  "more than one-half" comparator in s. 2(87)(ii) also carries q-f2c6-031,
  vignette 3(c) and one row of the mistakes list.

- [ ] **s. 3A day-counting in cs-f2c6-01-d.** The membership of a private company
  falls to one on **1 March 2026**; the chapter treats the six-month grace as
  expiring on **1 September 2026**, so a loan taken on 20 November 2026 is caught
  and the cognisant member is severally liable for the whole ₹ 12,00,000.
  q-f2c6-009 uses the same convention (5 January 2026 → 5 July 2026). The
  section says only "carries on business for more than six months while the
  number is so reduced"; if the SM counts differently the conclusion survives on
  these facts (both loans fall well after any plausible expiry) but the stated
  dates should be re-worded.

- [ ] **Pre-incorporation contracts — the Specific Relief Act qualification is
  deliberately omitted.** q-f2c6-042 and cs-f2c6-03-a both state flatly that the
  company can become bound only by a **fresh contract** after incorporation. The
  Intermediate chapter additionally cites **ss. 15(h) and 19(e) of the Specific
  Relief Act 1963**, under which such a contract may be specifically enforced by
  or against the company where it is warranted by the terms of the incorporation
  and the company has accepted it and communicated the acceptance. That
  qualification was left out as Intermediate-level detail. If the Foundation SM
  teaches it, both questions and the §16 note need softening.

- [ ] **Producer companies — Chapter XXIA scope call.** §14 and q-f2c6-038 state
  that a producer company may be formed by **ten or more individual producers or
  two or more producer institutions**, that it is treated as a **private
  company**, and that the **two-hundred-member cap does not apply** to it. The
  last proposition is drawn from the producer-company chapter read with
  s. 2(68), not from a single quotable line. Confirm it, and confirm the section
  range 378A–378ZU (Chapter XXIA was inserted by the Companies (Amendment) Act
  2020).

- [ ] **Scope boundaries against the Intermediate paper.** The chapter is pitched
  at Foundation depth and says so in several places, but four calls were made
  without the SM in front of me. (i) **ss. 4 and 5 are outline only** — the
  alteration provisions (ss. 13, 14), entrenchment, name reservation and
  rectification, and the s. 12 registered-office machinery are left to
  Intermediate; §16 mentions only the thirty-day rule in s. 12. (ii) **s. 2(52)
  listed company** is answered on the main clause only, the Rule 2A carve-outs
  being flagged as Intermediate detail (q-f2c6-034 says so in its explanation).
  (iii) **The layers restriction under s. 2(87)** is mentioned in one line with
  no Rules detail and no question on it. (iv) **s. 8(11) penalties and the
  s. 8(9) fund carry no rupee figures**, deliberately, because both have been
  amended. Drop or expand each if the SM differs.

- [ ] **Deliberate non-duplication with the Intermediate bank.** Every numerical
  in this chapter was written to avoid the framings already used in
  `src/data/questions/intermediate/corporate-and-other-laws/preliminary.json`
  (Tara Weaves, Vyoma Ceramics, Neelkanth Alloys, Sahyadri Infra, Panna/Rewa,
  Ambika/Bhadra/Chitra/Damodar, Godavari/Halcyon). Names, numbers and the shape
  of the trap differ in each case, and cs-f2c6-02-b (aggregation with a
  subsidiary's holding) and cs-f2c6-02-c (an associate is **not** a s. 2(85)
  exclusion) are framings the Intermediate bank does not test at all. A reviewer
  cross-reading the two banks should confirm nothing has converged.

## negotiable-instruments-act-1881 — VERIFY 2026-08-10

- [ ] **New chapter (Foundation P2 Ch 7, The Negotiable Instruments Act 1881)
  authored 10 Aug 2026** — notes (18 numbered sections plus mistakes list and
  one-page summary, 5 application vignettes with working notes, 1,793 lines),
  bank (46 standalone MCQs, 3 case_mcq_sets with 9 sub-MCQs, 7 descriptives;
  9 numericals, all verifier-proven; answer keys A14/B14/C14/D13 over 55 MCQs),
  citations (`citations/foundation/business-laws/citations_negotiable-instruments-act-1881.md`),
  verifier (`scripts/verify_numerical/verify_negotiable-instruments-act-1881.py`).
  Reviewer should spot-check the whole chapter against **ICAI SM Paper 2 Ch 7
  (May 2026 ed.)** and the notified text of Act 26 of 1881 on India Code. The
  bare-act lines were transcribed, not re-fetched, so the sub-section and clause
  lettering of ss. 6, 13, 16, 20, 45A, 82, 85, 118, 131, 138, 141 and 142 needs
  a line-by-line diff.

- [ ] **ss. 138 to 148 are the high-drift block.** The group was inserted in
  1988 and amended in 2002, 2015 and 2018. Three figures carry questions and
  must be confirmed against the current notified text: the **two-year /
  twice-the-cheque-amount** punishment (d-f2c7-07, vignette 4), the **30-day**
  demand-notice window (cs-f2c7-03-b, a verified numerical) and the **15-day**
  payment window feeding the **one-month** complaint limit in s. 142(1)(b)
  (cs-f2c7-03-c, a verified numerical). Separately, **s. 143A** (interim
  compensation up to 20%) and **s. 148** (deposit of at least 20% on appeal),
  both from the 2018 amendment, are mentioned in §18 and in one sentence of
  vignette 4 but **no question depends on either** — delete both if the May 2026
  SM does not examine them at Foundation level.

- [ ] **The presentment window in proviso (a) to s. 138.** §17 now states the
  statutory formula ("six months from the date drawn, or the period of its
  validity, whichever is earlier") and then says the operative limit is
  **three months** because of the RBI direction that shortened cheque validity.
  The three-month figure is **not in the Act**. Confirm which form the SM
  prints. Nothing turns on it arithmetically — the cheque in cs-f2c7-03 is dated
  12 May 2026 and presented 24 June 2026, inside either limit — but the wording
  should match the SM.

- [ ] **Day-counting and the order of operations on maturity (ss. 22 to 25).**
  Four verified numericals depend on the chapter's stated convention:
  q-f2c7-037 (30 Nov 2026 + 3 months → 28 Feb 2027 → due **3 Mar 2027**),
  q-f2c7-038 (3 Aug 2026 + 100 days → 11 Nov 2026 → due **14 Nov 2026**),
  q-f2c7-039 (accepted 10 Jan 2026, 2 months after sight → due **13 Mar 2026**)
  and q-f2c7-040 (29 Jun 2026 + 3 months + grace → 2 Oct 2026, a notified
  holiday → due **1 Oct 2026**). The convention, stated in a pointer in §11 and
  in the verifier's docstring, is: a period in **days** is counted **from and
  excluding** the trigger date (s. 24 says exactly this, and it matches the
  offer-lapse and sale-or-return conventions used in the sibling chapters); a
  period in **months** ends on the **corresponding date**, else on the last day
  of that month (s. 23); and the **three days of grace are added BEFORE the
  s. 25 holiday test**, which then moves the date BACK. If the SM applies s. 25
  before grace, or counts days inclusively, all four keys move and
  `_add_days`, `_add_months` and `_grace` in the verifier must move with them.
  The same convention is applied **by analogy** to the s. 138 periods, which the
  Act does not spell out — see the next item.

- [ ] **The s. 138 clock, applied by analogy.** cs-f2c7-03-b counts 30 days from
  and excluding 27 June 2026 (the day the payee received the dishonour memo) to
  **27 July 2026**. cs-f2c7-03-c counts 15 days from and excluding 6 July 2026
  (the day the drawer received the notice) to 21 July 2026, treats the cause of
  action as arising on **22 July 2026**, and then takes "one month" to the
  corresponding date, **22 August 2026**. The one-month step follows the General
  Clauses Act s. 9 convention rather than any words in s. 142. A reviewer who
  prefers a different count should say so, because both keys move together.

- [ ] **"Account payee" is not in the Act.** q-f2c7-035 and step 4 of vignette 5
  both rest on the proposition that an account-payee crossing is banking
  practice which bites through the **negligence** limb of s. 131, so a
  collecting banker who ignores it loses its statutory shield. Settled
  commercial law, but stated from principle, not from statutory words, and it is
  the point on which the collecting banker in cs-f2c7-01-c loses. Confirm the SM
  presents it this way.

- [ ] **Section 20 applied to a cheque (vignette 1 and q-f2c7-017).** Vignette 1
  runs s. 20 on a **blank cheque** and reasons that, a cheque requiring no
  stamp, the "amount covered by the stamp" ceiling does not operate — which is
  what makes the ₹ 6,50,000 answer work against a ₹ 1,20,000 private authority.
  If the SM confines s. 20 to stamped notes and bills, both the vignette and
  q-f2c7-017 need rewriting. The same vignette also chains s. 20 into **s. 53**
  so that Bharani, who knew of the fraud, still recovers; that chain is the
  single most counter-intuitive proposition in the chapter and is worth a
  reviewer's eye.

- [ ] **Two list-based questions that move if the notified list moves.**
  q-f2c7-004 is built by offering "due presentment" as the item **not** in the
  s. 118 presumptions; if the notified text carries a limb this chapter missed,
  the key changes. q-f2c7-043 and d-f2c7-06 depend on the membership of the
  **eight** cases in s. 98 where notice of dishonour is unnecessary; d-f2c7-06
  puts 1.5 of its 6 marks on that list. Likewise the **materiality list** in §16
  (date, sum, time of payment, place of payment, rate of interest, new party,
  unauthorised crossing) comes from the case law and the SM, not from s. 87,
  and q-f2c7-045 is built by asking which item is not on it.

- [ ] **The drawee in case of need (q-f2c7-012).** The chapter holds that a bill
  is **not treated as dishonoured until the drawee in case of need has also
  refused**. That is standard, but it is stated from the scheme of the Act and
  the SM's treatment rather than from a single quoted sub-section; confirm which
  section the SM attributes it to.

- [ ] **s. 11 read disjunctively (q-f2c7-021).** The key turns on reading the
  two limbs of s. 11 as alternatives, so that a bill drawn in India on an Indian
  resident is **inland** even though payable in Dubai. Check the punctuation of
  the notified text; a conjunctive reading flips the key.

- [ ] **The boundary against the P1 accounting chapter.** Only the headings and
  the first 180 lines of
  `src/pages/foundation/accounting/bills-of-exchange-and-promissory-notes.mdx`
  were read, to avoid duplication. This chapter is **law only**: no journal
  entries, no discounting, renewal, rebate on retirement, insolvency or
  accommodation-bill accounting. It links to the P1 chapter twice (the opening
  pointer and §14 on noting charges). The **due-date method must agree in both
  chapters** — expressed day, plus three days of grace, then the s. 25 test
  moving back — so a reviewer who changes one must change the other in the same
  PR.

- [ ] **Length.** The notes run to **1,793 lines** against the 1,200–1,500 the
  brief suggested. The scope list (ss. 4 to 148, five vignettes, six comparison
  tables, the full ss. 98 and 118 lists, a 24-item mistakes list and a one-page
  summary) did not compress further without dropping examinable content. A trim
  pass is available on §12 (ss. 61 to 76, the presentment detail) and §15
  (ss. 26 to 45A), which are the least heavily examined stretches, if length is
  a hard constraint.

- [ ] **Verifier output on 10 Aug 2026:**
  `python scripts/verify_numerical/run.py --bank src/data/questions/foundation/business-laws/negotiable-instruments-act-1881.json`
  → 9 numerical questions verified, 0 failures. All 56 `readLink` anchors were
  checked against the headings of the MDX and all resolve.

## equations — VERIFY 2026-08-10

- [ ] **New chapter (Foundation P3 Ch 2, Equations) authored 10 Aug 2026** —
  notes (18 numbered sections plus a common-mistakes list and a one-page
  summary, 10 fully worked examples with working notes, 1,176 lines), bank
  (50 standalone MCQs plus 3 case_mcq_sets carrying 10 sub-MCQs = **60 MCQs, no
  descriptives**, Paper 3 being wholly objective; **58 numericals, all
  verifier-proven**; answer keys A15/B15/C15/D15), citations
  (`citations/foundation/quantitative-aptitude/citations_equations.md`),
  verifier (`scripts/verify_numerical/verify_equations.py`, 744 lines, one
  function per numerical id). Reviewer should spot-check the whole chapter
  against **ICAI SM Paper 3 Ch 2 (May 2026 ed.)**. There is no bare Act to
  check against, so the citations file records the SM scope, each standard
  result in its conventional statement, and the editorial conventions instead —
  items 1 to 7 of its "Reviewer's checklist" are the real work.

- [ ] **`law_as_on_date` is deliberately omitted from the frontmatter.** This
  chapter states no legal or fiscal position, so there is no cut-off date to
  pin it to; `applicable_attempts` (Sept 2026, Jan 2027) is present. If the
  attempt-lint rules are later extended to Paper 3, confirm that a mathematics
  chapter is exempt from `law_as_on_date` rather than failing CI.

- [ ] **Are complex roots examinable at Foundation?** The chapter stops at
  "D < 0 → the roots are not real, a conjugate pair of imaginary numbers" and
  does no arithmetic with i. q-f3c2-022 tests only the classification. If the SM
  develops complex roots further, §11 and the summary need extending; if the SM
  avoids "imaginary" altogether, the phrase should be cut back to "no real
  roots". No answer key moves either way.

- [ ] **Does D = 0 give "one root" or "two equal roots"?** The chapter treats it
  as **two roots that are equal**, consistent with the degree-n-means-n-roots
  statement in §2. The §2 "mistake" callout, q-f3c2-021 and the reasoning behind
  q-f3c2-024's two answers (m = 8 *or* −8) all rest on it. If the SM says "one
  root", §2, §11 and several explanations need rewording, though no key changes.

- [ ] **How an extraneous root is reported.** q-f3c2-038 and worked example 7
  state the surviving root only and name the discarded value an extraneous root
  created by squaring. The alternative house style — list both, mark one
  "rejected" — would change option wording but not the key. Students match
  option wording literally, so confirm which form the SM prints.

- [ ] **Rejecting negative roots.** The chapter rejects a negative root only
  when the situation forbids it (a count of boxes, an age, a digit) and warns
  in §17 against reflexive rejection; q-f3c2-015, q-f3c2-019 and q-f3c2-027 all
  have a legitimate negative root. Confirm the SM teaches no blanket rule.

- [ ] **Break-even rounding.** Worked example 1(c) computes 2,666.67 and rounds
  **up** to 2,667 because 2,666 units still leave a loss. Every bank question is
  built so the exact answer is a whole number and the verifier's `break_even()`
  returns an exact `Fraction` without rounding, so no key depends on this — but
  the rounding direction taught should match the SM's worked patterns.

- [ ] **Two places that may exceed SM depth.** (i) The four-row derived-root
  table in §13 (roots kα, α + k, 1/α, −α, including the "reverse the
  coefficients" reciprocal result); only q-f3c2-032 uses it, and only the
  scaled-roots row. (ii) The α⁴ + β⁴ identity in §14, which no bank question
  uses. Both can be cut without touching a question. Also confirm the printed
  subscript order of the cross-multiplication rule in §5 matches the SM's, since
  some texts print the middle denominator as (a₁c₂ − a₂c₁) against −y.

- [ ] **Negative-marking paragraph (§18).** The expected-value arithmetic —
  blind guessing among four options being close to neutral, elimination of one
  option making an attempt clearly worthwhile — follows from 1 / −0.25 / 0 as
  recorded in `foundationScoring`. Confirm the 0.25 deduction is still ICAI's
  announced pattern for both attempts before the draft badge comes off.

## ratio-proportion-indices-logarithms — VERIFY 2026-08-10

- [ ] **New chapter (Foundation P3 Ch 1, Ratio and Proportion, Indices,
  Logarithms) authored 10 Aug 2026** — notes (18 numbered sections plus
  mistakes list and one-page summary, 11 worked examples with working notes,
  1,208 lines), bank (50 standalone MCQs, 3 case_mcq_sets with 10 sub-MCQs, and
  **no descriptives** — Paper 3 is 100% objective; 53 numericals, all
  verifier-proven; answer keys A15/B15/C15/D15 over 60 MCQs), citations
  (`citations/foundation/quantitative-aptitude/citations_ratio-proportion-indices-logarithms.md`).
  This is the first Paper 3 chapter and sets the pattern for the rest: no
  descriptives, numerical density far above the accounting chapters, and every
  distractor built from a named error. Reviewer should spot-check scope and
  depth against **ICAI SM Paper 3, Ch 1 (May 2026 ed.)**. There is no bare Act
  here, so the citations file records conventional statements of each standard
  result instead of quoted source lines.

- [ ] **`law_as_on_date` is deliberately omitted from the frontmatter.** The
  chapter carries `applicable_attempts: ['Sept 2026','Jan 2027']` but states no
  legal position at any date, and a law-as-on date on a mathematics chapter
  would tell a reviewer that a statutory cut-off had been checked when none
  exists. Confirm that `scripts/attempt_lint/` does not require
  `law_as_on_date` for Foundation P3 (it is specified for the volatile
  Intermediate law/tax papers), and that the notes page renders without it.

- [ ] **`log` with no base is taken as base 10 throughout.** §15 states this
  explicitly and distinguishes `ln` (base e), with ln N = 2.3026 log N. No
  answer key turns on it, because every stem that matters names its base, but
  if the SM uses `log` for the natural logarithm anywhere in Ch 1, §15 and
  q-f3c1-046 need re-reading.

- [ ] **Sign convention on the characteristic, and the bar notation.** §16
  teaches 3̄.6304 as −3 + 0.6304 = −0.3696, with the **mantissa always
  positive**. q-f3c1-047 (characteristic of log 0.00427 = −3) and q-f3c1-048
  (mantissa positive and digit-dependent) both rest on it. The keys stand under
  either presentation, but if the SM teaches the single-negative-decimal form,
  the §16 table and mistake callout should be re-worded to match.

- [ ] **Four-figure tables, and values supplied in the stem.** §16 walks through
  a four-figure lookup with a mean-difference column and states plainly that
  antilog 0.8572 gives 719.7 against a true 720, the gap being rounding rather
  than error. No question in the bank requires a table: every logarithm question
  supplies the values it needs (log 2 = 0.3010, log 3 = 0.4771, ln 10 = 2.3026,
  antilog 0.1505 = 1.4142). Confirm the SM examines at four-figure precision and
  that supplying values in the stem matches how the paper is actually set.

- [ ] **The mean proportional is taken as the positive root only.** q-f3c1-016
  (between 8 and 32, answer 16) reports one value; q-f3c1-018 says "x is
  positive" in the stem. If the SM admits the negative root as a second answer,
  q-f3c1-016 needs the same qualifier added.

- [ ] **Extraneous roots are rejected rather than listed.** q-f3c1-050 and
  worked example 11 hold that log₂ x + log₂ (x − 2) = 3 has the single answer
  x = 4, the quadratic's other root x = −2 making an argument negative. The
  trap option "x = 4 or x = −2" is the answer to the quadratic, not to the
  equation. Standard position, but confirm the SM states the domain check
  explicitly; if it does not, the notes carry more weight on this point than the
  SM does.

- [ ] **The partly-constant, partly-varying cost form (y = a + bx) sits in §8**,
  next to variation, and q-f3c1-023 tests it. Some presentations place it under
  simultaneous equations (Ch 2). Nothing in the key depends on where it sits;
  if the SM keeps it out of Ch 1, the §8 closing block and q-f3c1-023 can move
  without disturbing anything else.

- [ ] **Negative-marking guidance is stated numerically in §18 and repeated in
  the one-page summary.** With four options and −0.25, a random answer has an
  expected value of +0.0625; eliminating one option raises it to about +0.17 and
  two to +0.375. The section then makes the point that guesses in this chapter
  are not random, because every distractor is a prepared error. Tone is factual
  and carries no pressure language, but a reviewer should confirm the arithmetic
  and the framing before it is copied into the other seven Paper 3 chapters.

## linear-inequalities — VERIFY 2026-08-10

- [ ] **New chapter (Foundation P3 Ch 3, Linear Inequalities) authored
  10 Aug 2026** — notes (18 numbered sections plus mistakes list and one-page
  summary, 8 worked examples with working notes), bank (52 standalone MCQs,
  3 case_mcq_sets with 10 sub-MCQs, no descriptives — Paper 3 is 100%
  objective; 47 numericals, all verifier-proven; answer keys A16/B16/C15/D15
  over 62 MCQs), citations
  (`citations/foundation/quantitative-aptitude/citations_linear-inequalities.md`).
  Reviewer should spot-check the scope and depth against **ICAI SM Paper 3 Ch 3
  (May 2026 ed.)**. There is no bare Act for mathematics, so the citations file
  records standard results and chosen conventions instead of quoted lines, and
  the frontmatter deliberately omits `law_as_on_date` while keeping
  `applicable_attempts`.

- [ ] **Does the feasible region include its boundary?** Every corner-point key
  in the bank assumes yes for non-strict constraints: q-f3c3-050 (30, 20),
  q-f3c3-051, q-f3c3-052, cs-f3c3-01-b (25, 20), cs-f3c3-02-b (12, 6) and
  cs-f3c3-03-b (500, 300) all sit exactly on two boundary lines. This is the
  universal convention, but §10 and q-f3c3-040 option D state the consequence
  for a STRICT system — that its vertices are not attainable and a "maximum
  production" reading has no exact answer — and that phrasing should be checked
  against the SM's own words.

- [ ] **Are integer-only solutions required in production problems?** Corner
  points are reported as exact rationals, so q-f3c3-051 option D and worked
  example 6 give `(16/3, 20/3)` and the notes forbid rounding it to
  `(5.33, 6.67)`. Worked example 4 flags that machines come in whole numbers and
  calls the practical answers the lattice points of the region. Where a whole
  number IS wanted the stem says so (q-f3c3-018, -019, -022, -024, -028, -033).
  If the SM expects production vertices to be rounded to feasible integer plans,
  the wording of q-f3c3-051 option D and worked example 6 needs revising, though
  no key moves.

- [ ] **Is an unbounded region ever described as having "no solution"?** This
  chapter says never: q-f3c3-048, q-f3c3-049 and cs-f3c3-02-a each offer
  "empty" and "unbounded" as competing options and key the unbounded one, and
  the §14 callout states that the two are opposite conditions. Because the
  chapter stops before optimisation, no question asks for a maximum over an
  unbounded region, where "no finite optimum" would be the right phrase. Confirm
  the SM's own vocabulary for the unbounded case.

- [ ] **May a stated fund or budget be left partly unused?** cs-f3c3-03 and
  worked example 8 read "has ₹ 8,00,000 available... need not place the whole
  sum" as `x + y ≤ 800`, which keeps `(0, 0)` and `(800, 0)` as corner points;
  q-f3c3-035 makes the same `≤` choice for a sanctioned budget and offers the
  equality as a named distractor. Worked example 8, a separate ₹ 6,00,000 trust
  with `x ≥ 2y` and `y ≥ 100`, sets out what changes under an equality — its
  region collapses to the segment joining `(500, 100)` and `(400, 200)` and the
  vertex `(200, 100)` disappears. If the SM's investment problems use `=`, the
  corner-point sets in cs-f3c3-03-c and worked example 8 both change.

- [ ] **Scope boundary: the chapter stops at the corner points.** No objective
  function is evaluated anywhere in the notes or the bank, and no question asks
  which vertex is best. That was a deliberate reading of the Foundation
  syllabus, which places linear-programming optimisation outside Ch 3. If the
  SM's Ch 3 in fact carries a corner-point-theorem treatment, this chapter is
  short by one section rather than wrong, and §15 is the natural place to add it.

- [ ] **Non-numerical MCQs need the blind second pass.** Fifteen of the 62 MCQs
  are conceptual rather than computable (q-f3c3-001, -003, -004, -005, -006,
  -010, -012, -021, -023, -040, -042, -043, -045, -047 and cs-f3c3-03-a) and so
  carry no verifier. They should go through `scripts/consistency_check/` before
  the draft badge comes off.

## mathematics-of-finance — VERIFY 2026-08-10

- [ ] **New chapter (Foundation P3 Ch 4, Mathematics of Finance / Time Value of
  Money) authored 10 Aug 2026** — notes (20 numbered sections plus a common-
  mistakes list and a one-page formula summary, 11 fully worked examples with
  line-by-line working notes, 1,226 lines), bank (50 standalone MCQs plus 3
  case_mcq_sets carrying 10 sub-MCQs = 60 MCQs, no descriptives, because Paper 3
  is fully objective; **57 numericals, all verifier-proven**; answer keys
  A15/B15/C15/D15 over 60 MCQs), verifier
  (`scripts/verify_numerical/verify_mathematics-of-finance.py`, 57 functions,
  `decimal.Decimal` under an explicit context), citations
  (`citations/foundation/quantitative-aptitude/citations_mathematics-of-finance.md`).
  Reviewer should spot-check the whole chapter against **ICAI SM Paper 3 Ch 4
  (May 2026 ed.)**. There is no bare Act here and nothing states a legal
  position, so the notes frontmatter deliberately **omits `law_as_on_date`** and
  the bank carries no `lawAsOnDate`. `python scripts/verify_numerical/run.py`
  reports 0 failures across the whole tree (825 numericals).

- [ ] **Rounding and day-count conventions are the real review surface here.**
  The citations file ends with a twelve-item **Reviewer's checklist of
  conventions**; please work through it rather than re-checking arithmetic. The
  four that change answer keys outright: (i) a year is **365 days** for simple
  interest — q-f3c4-006 gives ₹ 7,200 on 365 days and ₹ 7,300 (option A) on 360;
  (ii) money is rounded **once at the end**, to the nearest paisa, and interest
  is never rounded period by period; (iii) amortisation schedules are built from
  the **unrounded** instalment so the closing balance falls to zero — if the SM
  rounds the EMI first, cs-f3c4-01-d moves; (iv) CAGR counts the **intervals**
  between the two years, so 2019-20 to 2025-26 is 6 years (q-f3c4-049) and
  2021-22 to 2025-26 is 4 (worked example 10). Counting the labels instead flips
  both to the D distractor.

- [ ] **The ordinary annuity is this chapter's default where a stem is silent.**
  An annuity due is used only where the stem says "at the beginning", "in
  advance" or "the first payment today" (q-f3c4-039, q-f3c4-040, cs-f3c4-03-c,
  worked examples 5 and 6). Confirm the SM does not make payment-in-advance the
  default in any of its own illustrations — recurring deposits and lease rentals
  are the places where commercial practice differs from the textbook default,
  and a silent switch would flip several keys by a factor of (1 + i).

- [ ] **Three scope calls made without the SM in front of me.** (i) **Continuous
  compounding** is taught at the level of two formulas (`A = P e^(r t)` and
  `E = e^r − 1`), one worked amount and the last row of the §6 effective-rate
  table; if the May 2026 edition omits it, drop q-f3c4-029 and q-f3c4-030 and
  that table row — nothing else depends on them. (ii) The **growing perpetuity**
  (`R ÷ (i − g)`) is the single item most likely to sit outside the Foundation
  syllabus; it is notes §12, q-f3c4-042 and half of worked example 10, all of
  which lift out cleanly, leaving the level perpetuity intact. (iii) **Capital
  rationing** gets two sentences and a small table in §16 and is never tested;
  cut it if the SM does not go that far.

- [ ] **Overlap boundary with Paper 1 was drawn deliberately.** Notes §3 treats
  the constant-rate decline formula `P(1 − d)^n` as pure arithmetic and says in
  terms that the accounting treatment of reducing-balance depreciation belongs to
  `foundation/accounting/depreciation-and-amortisation`. Confirm the split reads
  correctly to a student who has done Paper 1 first, and that q-f3c4-015 cannot
  be mistaken for an accounting question.

- [ ] **The negative-marking paragraph (notes §20) states expected values.** With
  0.25 deducted per wrong answer, a blind guess among four options is worth
  +0.0625 marks, one elimination +0.1667 and two eliminations +0.375. The
  arithmetic is right, but a reviewer should confirm the framing is acceptable
  house style — it tells students a blind guess is very nearly worthless rather
  than telling them never to guess, and it names three chapter-specific sanity
  checks (a PV annuity factor above n, a compound amount below the simple-
  interest amount, a present value above the future sum) as the cheap way to
  eliminate options.

- [ ] **Interest tables are never assumed.** Notes §19 shows how to build any
  factor by repeated squaring and how to derive the other three factors from one,
  and every worked example states the factor it uses to four decimal places.
  Confirm this is enough for a student sitting the paper without printed tables,
  and that no question in the bank silently requires a table lookup.

## sequence-and-series — VERIFY 2026-08-10

- [ ] **New chapter (Foundation P3 Ch 6, Sequence and Series — Arithmetic and
  Geometric Progressions) authored 10 Aug 2026** — notes (18 numbered sections
  plus a common-mistakes list and a one-page summary, 12 fully worked examples
  with line-by-line working notes, 1,245 lines), bank (50 standalone MCQs,
  3 case_mcq_sets with 10 sub-MCQs, no descriptives because Paper 3 is wholly
  objective; 58 of the 60 MCQs numerical and all 58 verifier-proven; answer keys
  A15/B15/C15/D15 over 60 MCQs), citations
  (`citations/foundation/quantitative-aptitude/citations_sequence-and-series.md`),
  verifier (`scripts/verify_numerical/verify_sequence-and-series.py`).
  Reviewer should spot-check the whole chapter against **ICAI SM Paper 3 Ch 6
  (May 2026 ed.)**. There is no bare Act behind a mathematics chapter, so the
  citations file records the standard results in their conventional statements
  instead; what needs a human is the convention list reproduced below.
  `law_as_on_date` is deliberately omitted from the frontmatter and that
  omission is noted in the citations file.

- [ ] **Scope boundary with Ch 4 (Mathematics of Finance).** Compound interest,
  annuities, sinking funds, present value and instalment problems are GP
  applications but are **not** worked here — they belong to Ch 4. This chapter
  teaches the GP machinery and mentions the finance chapter once, in the
  one-page summary, with no link. If the SM's Ch 6 does work an interest
  example, confirm that leaving it out does not create a gap for students who
  read the chapters in order.

- [ ] **Is the geometric mean of two positive numbers the positive root only?**
  The chapter takes G = √(ab) as the positive root throughout. q-f3c6-044
  (GM of 8 and 32 = 16) and cs-f3c6-03-c (GM of 18 and 50 = 30) both depend on
  it, as does q-f3c6-045, which takes r = 5 and not −5 when inserting geometric
  means. Strictly G² = ab has two roots. This is the usual Foundation
  convention; confirm the SM states it explicitly rather than leaving it
  implied.

- [ ] **Does "insert n means" count the endpoints?** The chapter says it does
  not: n means between a and b give a progression of n + 2 terms and n + 1 gaps,
  so d = (b − a) ÷ (n + 1) and r = (b ÷ a)^[1 ÷ (n + 1)]. q-f3c6-026,
  q-f3c6-027 and q-f3c6-045 all rest on this, and their distractors are built
  from the n-versus-n+1 divisor error. Standard, but it is the commonest source
  of a one-place shift in a student's answer, so the SM's phrasing should be
  matched word for word.

- [ ] **An infinite GP with r = 1 — "divergent", or "no sum exists"?** The
  chapter says the sum to infinity does not exist and gives the reason (partial
  sums are na), avoiding "convergent" and "divergent" as later-syllabus words.
  q-f3c6-039 option D and the whole of q-f3c6-042 use the "no sum exists"
  phrasing. If the SM uses "divergent", q-f3c6-042's correct option should adopt
  that word so students recognise it. The r = −1 case is listed separately in
  §11's table (partial sums oscillate between a and 0); trim that row if the SM
  folds it into |r| ≥ 1 without comment.

- [ ] **Whether a single number or a two-term list counts as a progression.**
  The chapter never asks a student to classify a one- or two-term list, and no
  key turns on it. Some texts say any two-term sequence is trivially both an AP
  and a GP. If the SM states a position, §1 should be aligned with it.

- [ ] **Endpoints of a stated range, and rounding when a target is crossed.**
  §6 reads "between 100 and 500" as exclusive and "from 100 to 500" as
  inclusive. The ambiguity is designed out of the bank rather than relied on:
  q-f3c6-013 is worded "greater than 50 and less than 300" because 300 is itself
  a multiple of 6, and in q-f3c6-020 neither endpoint is a term. Separately,
  q-f3c6-022 and cs-f3c6-01-c round the period count **up** when asking when a
  target is first reached; confirm the SM's worked examples do the same rather
  than naming the last period below the target.

- [ ] **Notation and presentation calls.** The notes use Tₙ for the nth term,
  Sₙ for the sum of n terms and l for the last term, but use aₙ for the general
  term of a plain sequence in §1–§2 before switching to Tₙ inside the
  progressions. §10 presents both arrangements of the finite GP sum and states
  they are the same formula; if the SM leads with only one, follow its order,
  because students match printed forms literally. Finally, the notes run to
  1,245 lines — §7 (equidistant terms) and §15 (symmetrical forms) compress
  most easily if a shorter page is wanted.

## permutations-and-combinations — VERIFY 2026-08-10

- [ ] **New chapter (Foundation P3 Ch 5, Basic Concepts of Permutations and
  Combinations) authored 10 Aug 2026** — notes (19 numbered sections plus a
  common-mistakes list and a one-page summary, 10 fully worked examples with
  line-by-line working notes, 1,359 lines), bank (50 standalone MCQs, 3
  case_mcq_sets with 10 sub-MCQs, no descriptives — Paper 3 is wholly
  objective; 56 of the 60 MCQs numerical and all verifier-proven; answer keys
  A16/B14/C15/D15 over 60 MCQs), citations
  (`citations/foundation/quantitative-aptitude/citations_permutations-and-combinations.md`).
  Reviewer should spot-check the whole chapter against **ICAI SM Paper 3 Ch 5
  (May 2026 ed.)**. There is no statutory source, so the audit is a scope and
  convention check, not a bare-act diff. Frontmatter carries
  `applicable_attempts` and deliberately omits `law_as_on_date` — an
  arrangement count does not move with a Finance Act.

- [ ] **Is a garland identical under reflection?** The chapter halves the
  circular count for anything that can be turned over — necklace, garland,
  bangle, key ring — and does not halve a table or a fixed circle of seats.
  q-f3c5-032 (necklace of 7 beads → 360) and q-f3c5-033 (garland of 9 flowers
  → 20,160) both depend on it, and in both the unhalved value sits there as a
  distractor, so if the SM does not halve garlands the keys move to those
  options. q-f3c5-029 (round table of 6 → 120) tests the same convention in the
  opposite direction, offering the halved 60. The §10 table is the single place
  to edit.

- [ ] **Does "at least one" include the empty selection?** The chapter excludes
  it, so q-f3c5-044 is 63 and not 64, and q-f3c5-045 is 79 and not 80. Both
  un-subtracted values are the distractors. §15 additionally states the converse
  — that wording such as "any number, including none" does not subtract — which
  is an editorial addition and should be checked against the SM's phrasing.

- [ ] **Are repeated letters indistinguishable by default?** The chapter assumes
  yes, which decides q-f3c5-020 (BALLOON → 1,260), q-f3c5-021 (ACCOUNTANT →
  2,26,800), q-f3c5-022 (identical flags → 1,260), q-f3c5-023 and q-f3c5-045
  together. The related call is inside the block method: a tied block of
  **identical** objects is not multiplied back by its internal factorial, while
  a block of **distinct** objects is. q-f3c5-023 (360) and q-f3c5-024 (720) are
  set side by side to test exactly that difference.

- [ ] **Equal-size groups: labelled or unlabelled?** The chapter divides by k!
  only when equal-sized groups carry no name, destination or distinct work.
  Four keys turn on it: q-f3c5-046 (two unnamed groups of 5 → 126), q-f3c5-047
  (three named branches of 3 → 1,680), cs-f3c5-03-a (two unnamed groups of 4 →
  35) and cs-f3c5-03-b (**the same 8 trainees**, two named teams of 4 → 70).
  The last pair is the same numbers with one word changed, so a different
  convention swaps the two keys. cs-f3c5-03-c (sizes 2, 3, 3 to named clients →
  560) additionally relies on unequal or labelled groups taking no divisor.

- [ ] **"Never together" versus "no two adjacent" for three or more objects.**
  The chapter reads "never all together" as the complement of the single block
  and reserves the gap method for "no two adjacent". q-f3c5-025 (4,320) carries
  1,440 — the no-two-adjacent figure — as its distractor, and q-f3c5-026
  (1,440) carries 720 as its. If the SM reads "never together" as "no two
  adjacent", the two keys change places. This is the most likely single point of
  disagreement between presentations.

- [ ] **Two smaller scope calls made without the SM in front of me.** (i) §17
  and worked example 8 state the collinear-point correction for **lines** as
  nC2 − kC2 + 1 alongside the triangle correction nC3 − kC3; only the triangle
  rule carries a key (q-f3c5-050 → 116), so the line rule can be trimmed if the
  SM omits it. (ii) §13 states the equality rule with both branches, so
  q-f3c5-038's key is "4 or 11"; if the SM teaches only x = y, reword the
  question rather than re-key it. (iii) The notes run to 1,359 lines with 19
  sections; §16's three-or-more-groups formula is the most likely item to
  exceed SM depth and can go without touching a bank question.

- [ ] **Verifier method, for information.**
  `scripts/verify_numerical/verify_permutations-and-combinations.py` proves 49
  of the 56 numerical answers by **brute-force enumeration** with `itertools`,
  building the arrangements, selections, circular canonical forms and group
  assignments and counting them, rather than re-applying the stem's formula.
  Circular counts are derived by reducing each arrangement to its smallest
  rotation, and necklace counts by the smallest rotation of the sequence or its
  reverse, so (n − 1)! and (n − 1)! ÷ 2 are results and not assumptions. Six
  functions use a formula (the service-tag case, which runs to millions of tags,
  and the two factorial-identity questions) and one is a hybrid; each says so in
  a comment. If a reviewer changes any convention above, the verifier is
  expected to fail rather than to agree.

## sets-relations-functions — VERIFY 2026-08-10

- [ ] **New chapter (Foundation P3 Ch 7, Sets, Relations and Functions; Basics
  of Limits and Continuity) authored 10 Aug 2026** — notes (19 numbered sections
  plus a common-mistakes list and a one-page summary, 11 worked examples with
  line-by-line working notes, 1,773 lines), bank (50 standalone MCQs plus 3
  case_mcq_sets carrying 11 sub-MCQs = 61 MCQs, no descriptives, as Paper 3 is
  wholly objective; 49 numerical, all verifier-proven; answer keys
  A15/B15/C16/D15), citations
  (`citations/foundation/quantitative-aptitude/citations_sets-relations-functions.md`).
  `python scripts/verify_numerical/run.py --bank
  src/data/questions/foundation/quantitative-aptitude/sets-relations-functions.json`
  prints 49 verified, 0 failures. All 53 readLink anchors were checked against
  the built heading slugs of the finished MDX. Reviewer should spot-check the
  whole chapter against **ICAI SM Paper 3 Ch 7 (May 2026 ed.)** for scope and
  depth; there is no statutory source to diff against.

- [ ] **Proper subsets: 2ⁿ − 1 or 2ⁿ − 2?** The chapter takes the standard
  position that ∅ is a proper subset of every non-empty set, so a 6-element set
  has **63** proper subsets. **q-f3c7-007's key (C, 63) depends on it**, and 62
  is offered as the distractor for the other convention. Several Indian
  textbooks teach "proper subsets = 2ⁿ − 2", meaning non-empty proper subsets.
  If the SM does that, the key flips to B and notes §3 plus the summary need
  rewriting. This is the highest-value check on this chapter.

- [ ] **The empty relation, and vacuous truth generally.** The chapter holds
  that R = ∅ on a non-empty set is symmetric and transitive (nothing can violate
  a condition that never fires) but not reflexive, and states expressly that
  {(1, 2), (3, 4)} is transitive for the same reason. **q-f3c7-032 (key B) and
  worked example 6 working note 4 rest entirely on this.** Vacuous truth is
  standard mathematics but is sometimes avoided at Foundation level. If the SM
  ducks it, q-f3c7-032 must be rewritten or dropped, and the §12 "mistake"
  callout with it.

- [ ] **"Onto" judged against the codomain, not the range.** q-f3c7-038 (key A:
  f(x) = x² on R → R is neither one-one nor onto) and worked example 7(b) both
  turn on testing surjectivity against the codomain the question declares.
  Confirm the SM's own onto questions always state a codomain; a stem that does
  not is ambiguous and its key is not defensible either way.

- [ ] **Is 0 a natural number?** The chapter follows N = {1, 2, 3, …} and
  W = N ∪ {0}, and says so in a §2 callout. q-f3c7-005 is deliberately written
  over W so no key depends on the convention, but the §2 table and that callout
  need rewording if the SM says otherwise.

- [ ] **Standard limits quoted without proof, and the omitted trigonometric
  limit.** §17 quotes five results — the power limit n·aⁿ⁻¹, (eˣ − 1)/x → 1,
  (aˣ − 1)/x → logₑ a, logₑ(1 + x)/x → 1, and both forms of the limit defining
  e — and **deliberately omits lim (x → 0) (sin x)/x = 1** and every other
  trigonometric limit, on the view that Foundation Paper 3 handles limits
  algebraically. No bank question needs one. If the SM carries them, §17 gains a
  row and the bank should gain a question; nothing already written changes.

- [ ] **Which branch owns a junction in a piecewise function.** q-f3c7-049
  (k = 7) and the whole of cs-f3c7-03 read the inequality signs literally, so
  "x ≤ 3" gives f(3) from the first branch and "x ≥ 8" gives H(8) from the
  second. Confirm the stems read unambiguously to a student; two keys move if a
  reader takes the junction the other way.

- [ ] **No Venn diagrams are drawn.** §6 sets the regions out as two tables
  (four regions for two sets, eight for three) and every counting question
  reasons from the table. This is a presentation choice, not a scope omission —
  but a reviewer expecting a drawn diagram should confirm it is acceptable for
  the page, and that the eight-region table's "+ t" restoration in each only
  region reads clearly.

- [ ] **Scope calls made without the SM in front of me.** (i) The §12 table
  giving the counts of reflexive and symmetric relations (2^(n²−n) and
  2^(n(n+1)/2)) may exceed Foundation depth; only q-f3c7-031 uses it. (ii) The
  §9 band formulas (exactly one = s − 2p + 3t and the rest) may be presented in
  the SM only as region arithmetic; every one of them is reproduced by the §6
  table, so they can be demoted to a shortcut without any key changing. (iii) No
  general formula for the number of onto functions is taught — every onto
  question in the bank is either the m = n case or the impossible case. Confirm
  the SM does not want the general surjection count.

## differential-and-integral-calculus — VERIFY 2026-08-10

- [ ] **New chapter (Foundation P3 Ch 8, Basic Applications of Differential and
  Integral Calculus) authored 10 Aug 2026** — notes (21 numbered sections plus
  12 fully worked examples, a common-mistakes list and a one-page summary;
  1,566 lines), bank (50 standalone MCQs + 3 case_mcq_sets carrying 12
  sub-MCQs = 62 MCQs, no descriptives because Paper 3 is wholly objective;
  answer keys A16/B17/C14/D15), citations
  (`citations/foundation/quantitative-aptitude/citations_differential-and-integral-calculus.md`).
  **All 61 numerical questions are verifier-proven, 0 failures.** Reviewer
  should spot-check the scope against **ICAI SM Paper 3 Ch 8 (May 2026 ed.)**;
  the arithmetic does not need re-checking (see the next item for why).

- [ ] **Split authorship — read this before reviewing.** The notes, the bank,
  and verifier functions `q_f3c8_002` to `q_f3c8_040` were written in one
  session pass. That pass was cut short by a session usage limit before it
  finished, and the remaining **22 verifier functions** (`q-f3c8-041` to
  `q-f3c8-050` and all twelve `cs-f3c8-*` sub-questions) plus this citations
  file were written by a **second pass that read the finished bank without the
  reasoning behind it**. Every one of those 22 recomputed the answer
  independently and agreed with the key already in the bank. That agreement is
  meaningful precisely because the second pass did not know the first pass's
  working — but a reviewer should know the two halves of the module were
  written hours apart, and may want to read the last 22 functions with fresh
  eyes. Nothing else in the chapter was touched by the second pass.

- [ ] **The verifier deliberately never repeats the stem's algebra.** A claimed
  derivative is compared with a five-point central difference quotient of the
  original function; a claimed antiderivative is differentiated numerically and
  compared with the integrand; a definite integral is recomputed by composite
  Simpson's rule on 2,000 sub-intervals; an extremum is confirmed on a dense
  grid of 4,001 points and located by ternary search using no calculus at all.
  Re-applying the same differentiation rule the stem used would reproduce the
  same mistake, which is the failure this design exists to prevent. The module
  imports only `math` — no third-party package — because CI runs a bare
  Python 3 with no pip install step.

- [ ] **"+ c" is compulsory, and two keys rest on it.** In `q-f3c8-041`
  (∫x⁵ dx) and `q-f3c8-042` (∫(1/x) dx) the distractor is the correct function
  with the constant of integration removed. A numerical derivative cannot see
  an additive constant, so each option carries an explicit flag recording
  whether "+ c" is actually printed, and the verifier reads that flag rather
  than the algebra. **If the SM accepts an indefinite integral written without
  its constant, both questions must be rewritten — not re-keyed.** This is the
  highest-value check in the chapter.

- [ ] **`log` means the natural logarithm throughout this chapter**, while an
  unmarked `log` means base 10 in Ch 1 (Ratio, Proportion, Indices,
  Logarithms). Both chapters state their convention explicitly where a student
  will see it, which is the only thing that makes the clash defensible.
  Confirm that ICAI's own calculus chapter uses "log" for the natural log —
  every logarithmic option in this bank depends on that claim — and confirm
  both statements survive any later editing pass.

- [ ] **Marginal cost is treated as the derivative, not the cost of one more
  unit.** Every case-set scenario says to treat output as a continuous
  variable, so "the marginal cost at 20 pumps" means C′(20) = ₹ 90, not the
  cost of the 21st pump. Both readings appear in teaching material and give
  different numbers. If the SM defines marginal cost incrementally, §11 needs
  rewording, though no key would move.

- [ ] **The EOQ case set is derived, not quoted (`cs-f3c8-03`).** The scenario
  states the cost structure in words — ₹ 400 per order, ₹ 10 to carry one
  bearing for a year, average stock is half the order size, 18,000 bearings a
  year — and the verifier builds that annual cost function and minimises it by
  ternary search. It never uses √(2·D·Co/Ch). So those four keys are proof the
  model is right, not that a remembered square root was typed correctly.
  `cs-f3c8-03-d` additionally tests that quadrupling the holding cost **halves**
  the optimum (600), with the "divide by four" answer (300) sitting beside it.

- [ ] **Scope calls made without the SM to hand.** Three sections may be out of
  Foundation scope and are each removable as a block: **§9 implicit and
  parametric differentiation** (check the bank for anchors into §9 before
  cutting); **partial fractions restricted to distinct linear factors** — if
  repeated or irreducible quadratic factors are examinable, §18 is short a
  case; and **trigonometric functions excluded**, appearing only as the T in
  the ILATE mnemonic with an explicit note that they are not examined, and used
  by no question anywhere in the bank.

- [ ] **The second-derivative test is the chapter's default**, with the
  first-derivative test given as the fallback when f″(c) = 0. If the SM leads
  with sign-testing, §12's ordering should be swapped. No key moves either way:
  every extremum is confirmed on a dense grid independently of which test the
  notes recommend.

- [ ] **Definite integrals are evaluated as F(upper) − F(lower)**, and the
  reversed subtraction is carried as a distractor in `q-f3c8-050` (−34 against
  the correct 34). A presentation casual about the order would make that
  distractor defensible, which it must not be.
