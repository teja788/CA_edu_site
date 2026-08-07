# Citations — Foundation P1 Ch 6 · Bills of Exchange and Promissory Notes

Generated 7 Aug 2026 in the same session as the chapter content. This chapter is
half law, half accounting. The **Negotiable Instruments Act 1881** is a Central
Act, so its bare-act text is reproducible (Copyright Act s. 52(1)(q)) and the
operative lines are quoted below with an India Code source. The **ICAI Study
Material** is ICAI-copyrighted: it is paraphrased and cited by chapter only,
never quoted; the doctrinal and accounting positions were fact-checked against
the current SM chapter (reference_only — read to check, nothing copied).

> **Provenance warning for the reviewer.** The bare-act lines below were
> transcribed from the Negotiable Instruments Act 1881 rather than re-fetched
> from India Code in this session. Before this chapter leaves `unreviewed`,
> please diff every quoted line against the India Code text of Act 26 of 1881
> (indiacode.nic.in) and initial each row. Section numbers, not just wording,
> should be checked — several sections of the Act have been amended.

## Section 4, NI Act 1881 — "Promissory note"

- **Bare-act line relied on:** "A 'promissory note' is an instrument in writing
  (not being a bank-note or a currency-note) containing an unconditional
  undertaking, signed by the maker, to pay a certain sum of money only to, or to
  the order of, a certain person, or to the bearer of the instrument."
- **Source:** India Code, Negotiable Instruments Act 1881 (Act 26 of 1881),
  s. 4 — transcribed 7 Aug 2026, not re-fetched (see warning above).
- **Used in:** q-f1c6-001 (definition, all four options), q-f1c6-004
  (unconditional promise), q-f1c6-005 (essentials), d-f1c6-01 skeleton point 1,
  notes §1.
- **Spot-checked by:** _(blank until a human checks)_

## Section 5, NI Act 1881 — "Bill of exchange"

- **Bare-act line relied on:** "A 'bill of exchange' is an instrument in writing
  containing an unconditional order, signed by the maker, directing a certain
  person to pay a certain sum of money only to, or to the order of, a certain
  person or to the bearer of the instrument."
- **Note on the word "maker":** s. 5 uses "signed by the maker" for the person
  who draws the bill; the Act's own definition clause then names that person the
  **drawer** and the person directed to pay the **drawee** (s. 7). The notes use
  drawer/drawee/acceptor throughout, which is the SM's usage — the reviewer
  should confirm the notes' §2 table does not read as though it were quoting
  s. 5's "maker".
- **Source:** India Code, Act 26 of 1881, s. 5 — transcribed 7 Aug 2026.
- **Used in:** q-f1c6-001 (distractor A), q-f1c6-002 (order vs promise),
  q-f1c6-003 (acceptance), q-f1c6-006 (parties), d-f1c6-01 skeleton points 1–2,
  notes §1–§2.
- **Spot-checked by:** _(blank)_

## Section 7, NI Act 1881 — drawer, drawee, acceptor, payee

- **Position relied on (paraphrase of the definitions clause):** the maker of a
  bill is called the **drawer**; the person directed to pay is the **drawee**;
  after the drawee has signed his assent on the instrument he is the
  **acceptor**; and the person named in the instrument to whom the money is
  directed to be paid is the **payee**.
- **Source:** India Code, Act 26 of 1881, s. 7.
- **Used in:** q-f1c6-006, q-f1c6-007, q-f1c6-008, d-f1c6-01 skeleton point 3,
  notes §2.
- **Spot-checked by:** _(blank)_

## Section 22, NI Act 1881 — "Maturity" and the three days of grace

- **Bare-act line relied on:** "The maturity of a promissory note or bill of
  exchange is the date at which it falls due. Every promissory note or bill of
  exchange which is not expressed to be payable on demand, at sight or on
  presentment is at maturity on the third day after the day on which it is
  expressed to be payable."
- **How it is applied:** the notes and the verifier add exactly three days to
  the day the instrument is *expressed* to be payable, and add none at all to an
  instrument payable on demand, at sight or on presentment.
- **Source:** India Code, Act 26 of 1881, s. 22 — transcribed 7 Aug 2026.
- **Used in:** q-f1c6-010 (grace on time instruments only), q-f1c6-011 to
  q-f1c6-019 (every due-date question adds grace), q-f1c6-020 (demand
  instrument, no grace), d-f1c6-01 point 5, d-f1c6-02 point 3, notes §4,
  verifier `add_grace()` and `GRACE_DAYS = 3`.
- **Spot-checked by:** _(blank)_

## Section 23, NI Act 1881 — months after date or after sight

- **Bare-act lines relied on:** "In calculating the date at which a promissory
  note or bill of exchange, made payable a stated number of months after date or
  after sight, or after a certain event, is at maturity, the period stated shall
  be held to terminate on the day of the month which corresponds with the day on
  which the instrument is dated, or presented for acceptance or sight … If the
  month in which the period would terminate has no corresponding day, the period
  shall be held to terminate on the last day of such month."
- **Elision:** the ellipsis omits the clauses on noting or protest for
  non-acceptance, the happening of an event, and acceptance for honour — none of
  which is in the Foundation scope. The reviewer should confirm the elision does
  not change the sense of the two propositions actually used.
- **Source:** India Code, Act 26 of 1881, s. 23 — transcribed 7 Aug 2026.
- **Used in:** q-f1c6-009 (after sight runs from acceptance), q-f1c6-011,
  q-f1c6-012 (no corresponding day → last day of the month), q-f1c6-014
  (after-sight), q-f1c6-015 to q-f1c6-018, d-f1c6-02 points 1–2 and 5, notes §3
  and §4, verifier `add_months()` and `expressed_day()`.
- **Spot-checked by:** _(blank)_

## Section 24, NI Act 1881 — days after date or after sight

- **Bare-act line relied on:** "In calculating the date at which a promissory
  note or bill of exchange made payable a certain number of days after date or
  after sight or after a certain event is at maturity, the day of the date, or
  of presentment for acceptance or sight, or of protest for non-acceptance, or
  on which the event happens, shall be excluded."
- **How it is applied:** the verifier counts days with `start + timedelta(days=n)`,
  which excludes the day of the date exactly as s. 24 requires.
- **Source:** India Code, Act 26 of 1881, s. 24 — transcribed 7 Aug 2026.
- **Used in:** q-f1c6-013 (60 days after date, and distractor D which wrongly
  includes the day of the date), d-f1c6-02 point 2, notes §4, verifier
  `expressed_day(days=…)`.
- **Spot-checked by:** _(blank)_

## Section 25, NI Act 1881 — maturity falling on a public holiday

- **Bare-act line relied on:** "When the day on which a promissory note or bill
  of exchange is at maturity is a public holiday, the instrument shall be deemed
  to be due on the next preceding business day."
- **Explanation relied on:** "The expression 'public holiday' includes Sundays
  and any other day declared by the Central Government, by notification in the
  Official Gazette, to be a public holiday."
- **How it is applied, and the assumptions the reviewer must confirm:**
  1. the holiday test is applied to the date **after** the three days of grace
     have been added, never before;
  2. the days treated as notified public holidays across the chapter are
     **26 January, 15 August and 2 October** (stated in the stems and in
     notes §5), which are the SM's standard illustrations rather than a current
     Gazette list;
  3. **Saturdays are treated as ordinary business days.** The notes say so
     expressly, and q-f1c6-017's answer (3 October 2026, a Saturday) depends on
     it. If the reviewer prefers the alternative convention, that question and
     the verifier's `is_public_holiday()` both need changing.
- **Source:** India Code, Act 26 of 1881, s. 25 — transcribed 7 Aug 2026.
- **Used in:** q-f1c6-015 (15 August), q-f1c6-016 (2 October), q-f1c6-017
  (Sunday), q-f1c6-018 (26 January), d-f1c6-02 point 4, notes §5, verifier
  `is_public_holiday()` and `apply_holiday()`.
- **Spot-checked by:** _(blank)_

## Emergency holidays — convention, NOT a quoted provision

- **Position relied on (paraphrase; no bare-act line quoted):** where the day of
  maturity is declared a holiday only after the instrument was drawn — an
  emergency holiday — the instrument falls due on the **next succeeding**
  business day, rather than the preceding one under s. 25. This is the treatment
  applied in the ICAI Study Material and in standard commercial practice; it is
  stated here as a convention because no line of the NI Act was found that says
  it in those words.
- **Reviewer action:** please either supply the statutory or notified authority
  for this rule, or confirm that stating it as an SM/practice convention is
  acceptable for Foundation. The notes' §5 callout and q-f1c6-019 both rest on
  it, and d-f1c6-02 point 4 states it alongside s. 25.
- **Used in:** q-f1c6-019, q-f1c6-015 (distractor C), q-f1c6-016 (distractor C),
  q-f1c6-017 (distractor C), q-f1c6-018 (distractor B), d-f1c6-02 point 4,
  notes §5, verifier `apply_holiday(emergency=…)`.
- **Spot-checked by:** _(blank)_

## Section 99, NI Act 1881 — noting, and the notary's charges

- **Bare-act line relied on:** "When a promissory note or bill of exchange has
  been dishonoured by non-acceptance or non-payment, the holder may cause such
  dishonour to be noted by a notary public upon the instrument, or upon a paper
  attached thereto, or partly upon each. Such note must be made within a
  reasonable time after dishonour, and must specify the date of dishonour, the
  reason, if any, assigned for such dishonour, or, if the instrument has not
  been expressly dishonoured, the reason why the holder treats it as
  dishonoured, and the notary's charges."
- **What the chapter takes from it:** that noting is an act of the **holder**
  (hence he pays the notary), and that the notary's charges are a recognised
  head of cost on the instrument.
- **Source:** India Code, Act 26 of 1881, s. 99 — transcribed 7 Aug 2026.
- **Used in:** q-f1c6-038, d-f1c6-04 points 1–2, notes §9.
- **Spot-checked by:** _(blank)_

## Recovery of noting charges from the party liable — paraphrase, section to be confirmed

- **Position relied on (paraphrase):** the party entitled to compensation on a
  dishonoured instrument may recover the expenses of noting and protest from the
  party liable to compensate him, so the charges travel down the chain of
  endorsers and come to rest on the defaulting acceptor. The accounting
  consequence, which is what the questions test, is that noting charges are
  **paid by the holder but debited to the acceptor**, and are never an expense
  of the drawer in an ordinary trade dishonour.
- **Reviewer action:** the compensation rules sit in **s. 117** of the Act, but
  the exact clause was not verified in this session and is therefore not quoted.
  Please confirm the clause reference (and whether the SM cites it at all)
  before this row is signed off. The accounting position itself is uncontested
  in the SM.
- **Used in:** q-f1c6-028 (₹60,500 = face + noting recovered from the acceptor),
  q-f1c6-030 (dividend computed on ₹25,300 including noting charges),
  q-f1c6-037, q-f1c6-038, q-f1c6-039, d-f1c6-04 points 2–4, notes §9 and §12.
- **Spot-checked by:** _(blank)_

## Section 21, NI Act 1881 — "at sight", "on presentment"

- **Bare-act line relied on:** "In a promissory note or bill of exchange the
  expressions 'at sight' and 'on presentment' mean on demand."
- **Used in:** q-f1c6-010 (grace excluded for demand/sight instruments),
  q-f1c6-020 (a demand note matures on presentment), notes §3 and §4.
- **Source:** India Code, Act 26 of 1881, s. 21 — transcribed 7 Aug 2026.
- **Spot-checked by:** _(blank)_

## ICAI SM Ch 6 — accounting conventions (paraphrase only, nothing quoted)

- **Positions relied on (all paraphrased from the current SM chapter, May 2026
  onwards edition, checked 7 Aug 2026):**
  - the four courses open to a holder — retain, discount, endorse, send for
    collection — and the entries in the drawer's and acceptor's books, including
    that discounting, endorsement and sending for collection produce **no entry
    in the acceptor's books**;
  - on dishonour of a **discounted** bill the credit goes to **Bank**, and of an
    **endorsed** bill to the **endorsee**, because Bills Receivable was cleared
    when the bill left the holder's books;
  - renewal = cancel the old bill, charge interest for the extension on the
    amount actually carried forward, then draw the new bill;
  - retirement under rebate = payment before maturity at face value less a
    rebate computed for the unexpired period, the rebate being an **expense of
    the holder** and an **income of the acceptor**;
  - insolvency of the acceptor amounts to dishonour without presentment; the
    dividend in paise in the rupee is computed on the **whole amount owing**
    (including noting charges) and the shortfall is a bad debt;
  - accommodation bills: **net proceeds** are shared in the agreed ratio at the
    start, the **discount** is shared in the same ratio, and the **face value**
    is shared at maturity;
  - Bills Receivable and Bills Payable Books: periodic totals to the impersonal
    accounts, individual names to the personal accounts.
- **Used in:** q-f1c6-021 to q-f1c6-045 (accounting questions), d-f1c6-03,
  d-f1c6-04, d-f1c6-05, d-f1c6-06, notes §6 to §14.
- **Reviewer action:** the **direction of the rebate** (holder debits, acceptor
  credits) is the single position most worth re-reading in the SM, because it is
  asserted in q-f1c6-041, in d-f1c6-05 point 5 and in the notes' §11 callout,
  and reversing it would flip a whole cluster of answers.
- **Spot-checked by:** _(blank)_
