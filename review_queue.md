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
