# Citations — CA Intermediate P2 Ch 12 · The Limited Liability Partnership Act, 2008

Generated 27 August 2026 in the same session as the chapter content. Law stated
**as on 28 February 2026**, for the **Sept 2026 and Jan 2027** attempts, with the
**Limited Liability Partnership (Amendment) Act 2021** read in. The **LLP Act
2008** is a Central Act, so its bare-act text is reproducible (Copyright Act
s. 52(1)(q)) and the operative positions relied on are set out below. The **ICAI
Study Material** is ICAI-copyrighted: it is paraphrased and cited by paper and
chapter only, never quoted. The comparison tables, worked scenarios and the
First Schedule digest are written in this chapter's own words; no Study Material
paragraph has been copied.

> **Provenance warning for the reviewer — read before initialling anything.**
> Every statutory position below was **transcribed from the LLP Act 2008 and the
> LLP Rules 2009 from memory in this session; nothing was re-fetched from India
> Code or the MCA site**. This chapter sits on **three separate layers**, each
> needing its own check:
>
> 1. **Act-level text and sub-section numbering.** The **LLP (Amendment) Act
>    2021** touched a great deal of this chapter: it inserted **s. 2(1)(ta)**
>    (small LLP), substituted the **Explanation to s. 7** (residence), rewrote
>    **s. 17** (rectification of name), inserted **s. 34A** (accounting and
>    auditing standards), **ss. 67A to 67C** (Special Courts) and **s. 68A**
>    (adjudication of penalties), substituted **s. 39** (compounding), and
>    **omitted s. 64(c)** (inability to pay debts). Please diff each row below
>    against the notified text of Act 6 of 2009 as amended, and initial it.
> 2. **Rules-level detail.** The **Form 8 / Form 11 mechanics**, the **audit
>    thresholds**, the **eight-year preservation of books**, the **FiLLiP**
>    filing wrapper and the **strike-off** procedure all sit in the **LLP Rules
>    2009** and change by notification. Each is flagged in the rows below and in
>    an AMENDMENT-CHECK callout in the notes.
> 3. **Penalty amounts.** Recast wholesale by the 2021 Amendment, which
>    converted most defaults from *fine* to *penalty* adjudicated by the
>    Registrar. **No rupee penalty figure is examined anywhere in this chapter's
>    bank**, deliberately; only s. 11(3) (imprisonment up to two years, fine
>    ₹10,000 to ₹5,00,000) is stated in the notes, because it was **not**
>    decriminalised.
>
> Cross-check the whole chapter against **ICAI SM Paper 2, Chapter 12 (May 2026
> edition)** and the ICAI supplementary/amendment material notified for the
> attempt before this chapter leaves `unreviewed`.

> **Scope note.** A Foundation-level page on the LLP Act exists separately at
> `src/pages/foundation/business-laws/llp-act-2008.mdx`. This chapter is the
> deeper Intermediate treatment and was written independently; the Foundation
> page was not edited and is not a source for anything below.
>
> **Shared verifier module — note for the reviewer.** Both banks carry the
> `chapterSlug` **`llp-act-2008`**, and `scripts/verify_numerical/run.py`
> resolves the verify module from the slug alone, so the two chapters
> necessarily share **one** file: `scripts/verify_numerical/verify_llp-act-2008.py`.
> The Foundation functions (`q_f2c5_*`, `cs_f2c5_*`) were left untouched; the
> Intermediate functions (`q_i2c12_*`, `cs_i2c12_*`) were appended in a marked
> block at the end and reuse the existing `_add_days`, `_add_months`, `_pick`
> helpers and the `AUDIT_TURNOVER_LIMIT` / `AUDIT_CONTRIBUTION_LIMIT`
> constants. **Both banks were re-run after the merge and both pass with zero
> failures.** If either chapter's thresholds are revised, remember that the
> constants at the top of that module now serve both.

## Sections 3 and 4, LLP Act 2008 — nature of an LLP

- **Position relied on (paraphrase):** an LLP is a **body corporate** formed and
  incorporated under the Act and is a **legal entity separate from its
  partners** (s. 3(1)); it has **perpetual succession** (s. 3(2)); and **any
  change in the partners does not affect its existence, rights or liabilities**
  (s. 3(3)). **Section 4** provides that the **Indian Partnership Act 1932 does
  not apply** to an LLP, save as otherwise provided.
- **Source:** LLP Act 2008, ss. 3 and 4 — transcribed 27 Aug 2026, not
  re-fetched.
- **Used in:** q-i2c12-001, q-i2c12-002, q-i2c12-005, q-i2c12-006 (contrast),
  d-i2c12-01 (points 1–3), notes §1 and §2, one-page revision summary.
- **Spot-checked by:** _(blank until a human checks)_

## Section 2(1)(ta), LLP Act 2008 — small LLP

- **Position relied on (paraphrase):** a small LLP is one in respect of which the
  **contribution of the partners does not exceed ₹25 lakh** (or such higher
  amount as may be prescribed, **not exceeding ₹5 crore**) **and** the
  **turnover as per the Statement of Account and Solvency for the immediately
  preceding financial year does not exceed ₹40 lakh** (or such higher amount as
  may be prescribed, **not exceeding ₹50 crore**). Both limbs must be satisfied.
- **Source:** LLP Act 2008, s. 2(1)(ta), inserted by the LLP (Amendment) Act 2021
  — transcribed 27 Aug 2026, not re-fetched.
- **AMENDMENT-SENSITIVE — flag for the reviewer:** the operative ceilings of
  **₹25 lakh and ₹40 lakh** are **notification-level** and may be raised without
  amending the Act, up to the statutory outer limits stated above.
  **q-i2c12-004 is a verified numerical that turns directly on both figures and
  on the AND conjunction**; if either ceiling has moved, the question, the
  option set and `CONTRIBUTION_CEILING` / `TURNOVER_CEILING` in
  `scripts/verify_numerical/verify_llp-act-2008.py` must be reworked together.
  Confirm also that the turnover limb is still tested on the **immediately
  preceding** financial year.
- **Used in:** q-i2c12-003, q-i2c12-004 (**numerical**), d-i2c12-01 (point 4),
  notes §1 (table, working note and AMENDMENT-CHECK callout), §11 (contrast with
  the audit test), one-page revision summary.
- **Spot-checked by:** _(blank)_

## Sections 5, 6 and 22, LLP Act 2008 — partners

- **Position relied on (paraphrase):** on incorporation the **subscribers to the
  incorporation document** become the partners, and any other person becomes a
  partner **in accordance with the LLP agreement** (s. 22). Any **individual or
  body corporate** may be a partner, but an **individual** is not capable of
  becoming one if he has been **found of unsound mind by a court of competent
  jurisdiction and the finding is in force**, is an **undischarged insolvent**,
  or has **applied to be adjudicated an insolvent and his application is
  pending** (s. 5). Every LLP shall have **at least two partners**, with **no
  maximum** (s. 6(1)); and where the number is **reduced below two** and the LLP
  **carries on business for more than six months** while so reduced, the person
  who is **the only partner** during that continued period **and has knowledge**
  of the fact is **personally liable for the obligations of the LLP incurred
  during that period** (s. 6(2)).
- **Source:** LLP Act 2008, ss. 5, 6 and 22 — transcribed 27 Aug 2026, not
  re-fetched. **Reviewer note:** the analytical points the notes draw from
  s. 6(2) — the LLP is not dissolved; the clock starts only after six months;
  knowledge is an element; liability is confined to obligations of that period —
  are the Study Material's standard analysis restated in our own words. Confirm
  they match the current SM, and confirm that the parallel drawn with s. 3A of
  the Companies Act 2013 is one the SM also draws.
- **Used in:** q-i2c12-008, q-i2c12-009 (**numerical** — six-month expiry),
  q-i2c12-010, d-i2c12-01 (point 3), notes §3 and Scenario 1, one-page revision
  summary.
- **Spot-checked by:** _(blank)_

## Sections 7 to 10, LLP Act 2008 — designated partners

- **Position relied on (paraphrase):** every LLP shall have **at least two
  designated partners who are individuals**, at least one of whom shall be a
  **resident in India**; where all the partners are bodies corporate, or where
  they are a mixture of individuals and bodies corporate, **at least two
  individuals who are partners or nominees of those bodies corporate** shall act
  as designated partners (s. 7(1) and proviso). **Prior consent** to act in the
  prescribed form (s. 7(4)); **particulars filed with the Registrar within 30
  days of appointment** (s. 7(5)); **DPIN** obtained from the Central Government,
  with **ss. 153 to 159 of the Companies Act 2013 applying mutatis mutandis**
  (s. 7(6)). A designated partner is **responsible for all acts required for
  compliance with the Act, including every filing**, and **liable to all
  penalties imposed on the LLP** for contravention of those provisions (s. 8). A
  vacancy may be filled **within 30 days**, and if none is appointed or there is
  only one designated partner, **each partner is deemed to be a designated
  partner** (s. 9 and proviso). Contravention of ss. 7, 8 or 9 attracts a
  **penalty** on the LLP and its partners or designated partners (s. 10).
- **Source:** LLP Act 2008, ss. 7 to 10 — transcribed 27 Aug 2026, not
  re-fetched.
- **AMENDMENT-SENSITIVE — the single most likely stale point in this chapter:**
  the **Explanation to s. 7** defining "**resident in India**" was
  **substituted by the LLP (Amendment) Act 2021**. It formerly read "**not less
  than 182 days during the immediately preceding one year**"; it now reads
  "**not less than 120 days during the financial year**". **Both halves changed**
  — the number of days and the reference period. **q-i2c12-012 and
  cs-i2c12-02-a are verified numericals that turn entirely on the 120-day
  figure**, with 182 days named as the pre-amendment distractor, and
  `RESIDENCE_DAYS` in the verifier carries the same constant. Older Study
  Material states the 182-day position. **Verify before initialling.** Note also
  that the notes deliberately contrast this with the **182-day** resident-director
  test in s. 149(3) of the Companies Act 2013 — confirm that section too.
- **Also amendment-sensitive (NOT examined):** the **rupee penalties in s. 10**
  were recast in 2021 and are stated only qualitatively in the notes, inside an
  AMENDMENT-CHECK callout.
- **Used in:** q-i2c12-011, q-i2c12-012 (**numerical**), q-i2c12-013,
  q-i2c12-014, q-i2c12-015 (**numerical** — 30-day vacancy), q-i2c12-016,
  cs-i2c12-02 (sub a, **numerical**), d-i2c12-02 (all points), notes §4 and
  Scenario 2, one-page revision summary.
- **Spot-checked by:** _(blank)_

## Sections 11, 12 and 14, LLP Act 2008 — incorporation

- **Position relied on (paraphrase):** **two or more persons associated for
  carrying on a lawful business with a view to profit** subscribe to an
  **incorporation document**, filed with the **Registrar of the State in which
  the registered office is to be situated**, together with a **statement of
  compliance** made by an **advocate, Chartered Accountant, Cost Accountant or
  Company Secretary engaged in the formation** of the LLP **and** by **anyone
  who subscribed** his name to the incorporation document (s. 11(1)). The
  document states the **name, proposed business, registered-office address, and
  the names and addresses of the persons who are to be partners and designated
  partners** (s. 11(2)). A statement made **knowing it to be false, or not
  believing it to be true**, is punishable with **imprisonment up to two years
  and fine of not less than ₹10,000 and up to ₹5,00,000** (s. 11(3)). The
  Registrar **registers** the incorporation document and issues a certificate,
  may **accept the statement of compliance as sufficient evidence**, and the
  certificate is **conclusive evidence** that the LLP is incorporated by the name
  specified (s. 12). On registration the LLP is capable of **suing and being
  sued**, **acquiring, owning, holding and developing or disposing of property**,
  **having a common seal if it decides to have one**, and doing such other things
  as bodies corporate may lawfully do (s. 14).
- **Source:** LLP Act 2008, ss. 11, 12 and 14 — transcribed 27 Aug 2026, not
  re-fetched.
- **Rules-level and NOT examined:** the **FiLLiP** filing wrapper and the
  integrated DPIN / PAN / TAN services. Form names change by notification; the
  notes mention FiLLiP only as the vehicle and no question names a form for
  incorporation.
- **Reviewer note:** s. 11(3) is one of the **few surviving imprisonment
  offences** in the Act after the 2021 decriminalisation. Please confirm that it
  was not touched, since the notes and d-i2c12-03 state the figures.
- **Used in:** q-i2c12-017, q-i2c12-018, q-i2c12-019, d-i2c12-03 (points 1–4),
  notes §5, one-page revision summary.
- **Spot-checked by:** _(blank)_

## Sections 13, 15, 16 and 17, LLP Act 2008 — registered office and name

- **Position relied on (paraphrase):** every LLP shall have a **registered
  office** to which communications may be addressed and where they shall be
  received; documents may be served by **post under a certificate of posting,
  registered post or any other prescribed manner** at the registered office and
  at any other declared address; a **change of the registered office takes effect
  only on filing** the notice with the Registrar; contravention attracts a
  **daily penalty** subject to a maximum (s. 13). Every LLP's name must end with
  "**limited liability partnership**" or "**LLP**" (s. 15(1)); and no LLP may be
  registered by a name that in the **Central Government's** opinion is
  **undesirable**, or **identical with or too nearly resembling** the name of any
  **other partnership firm, LLP or body corporate**, or a **registered trade
  mark**, or a trade mark that is the **subject matter of a pending
  application** under the Trade Marks Act 1999 (s. 15(2)). A name may be
  **reserved for three months from the date of intimation by the Registrar**
  (s. 16). Under **s. 17**, where an LLP is registered with a name identical with
  or too nearly resembling that of **another LLP or a company**, or a
  **registered trade mark** likely to be mistaken for it, the **Central
  Government may direct a change within three months of the direction** on the
  application of that LLP or the proprietor, the proprietor's application being
  maintainable **within three years** of incorporation, registration or change of
  name; **notice of the change to the Registrar within 15 days**, and the **LLP
  agreement changed within 30 days** of the change in the certificate (s. 17(2));
  and on **default the Central Government allots a new name**, the Registrar
  entering it and issuing a **fresh certificate of incorporation** (s. 17(3)).
- **Source:** LLP Act 2008, ss. 13, 15, 16 and 17 — transcribed 27 Aug 2026, not
  re-fetched.
- **AMENDMENT-SENSITIVE — flag for the reviewer:** **s. 17 was wholly
  substituted by the LLP (Amendment) Act 2021.** The pre-amendment section gave
  the aggrieved entity or proprietor **24 months** to apply and imposed a
  **fine** for default; the substituted section adds the **three-year** limit for
  a trade-mark proprietor and replaces the fine with **allotment of a name by
  the Central Government**. **q-i2c12-021 (verified numerical) and q-i2c12-022
  turn on these two changes.** Separately, the notes state that the Central
  Government's power under s. 17 stands **delegated in practice to the Regional
  Director**, and that an appeal against a penalty adjudicated under s. 68A lies
  to the **Regional Director within 60 days** — **please confirm the delegation
  notification**, since no bank question is allowed to turn on the delegation and
  none does. The **prescribed format of the allotted name** is **rules-level**
  and is deliberately neither stated nor examined. The s. 13(4) penalty figures
  were also recast in 2021 and are stated only qualitatively.
- **Used in:** q-i2c12-020, q-i2c12-021 (**numerical**), q-i2c12-022,
  d-i2c12-03 (points 5–6), notes §6, one-page revision summary.
- **Spot-checked by:** _(blank)_

## Section 23 and the First Schedule, LLP Act 2008 — the LLP agreement

- **Position relied on (paraphrase):** the **mutual rights and duties** of the
  partners, and of the LLP and its partners, are governed by the **LLP
  agreement** (s. 23(1)), which and any changes in which are **filed with the
  Registrar** (s. 23(2)). An agreement made **before incorporation** between the
  subscribers may impose obligations on the LLP **provided it is ratified by all
  the partners after incorporation** (s. 23(3)). **In the absence of agreement as
  to any matter**, the provisions **relating to that matter** in the **First
  Schedule** apply (s. 23(4)).
- **First Schedule default rules relied on:** equal sharing of **capital, profits
  and losses**; **indemnity by the LLP** for payments made and personal
  liabilities incurred in the ordinary and proper conduct of the business or in
  anything necessarily done to preserve the business or property; **indemnity by
  a partner** for loss caused by his **fraud**; **every partner may take part in
  the management**; **no partner is entitled to remuneration**; **no person may
  be introduced as a partner without the consent of all existing partners**;
  ordinary matters decided by a **resolution passed by a majority in number**,
  each partner having **one vote**, with **no change in the nature of the
  business without the consent of all**; decisions **recorded in the minutes
  within 30 days** and kept at the registered office; **true accounts and full
  information** rendered to any partner or his legal representatives; accounting
  for profits of a **competing business** carried on without consent; accounting
  for any **benefit derived without consent** from a transaction concerning the
  LLP or from use of its **property, name or business connection**; **no
  expulsion by a majority** without express agreement; and reference of disputes
  to **arbitration** under the Arbitration and Conciliation Act 1996.
- **Source:** LLP Act 2008, s. 23 and the First Schedule — transcribed 27 Aug
  2026, not re-fetched. **Reviewer note:** the First Schedule paragraphs are
  **digested into a table** in the notes and are paraphrased throughout; please
  confirm the list is complete for the SM's purposes and that no paragraph has
  been misattributed. The **matter-by-matter** reading of s. 23(4) (the Schedule
  fills gaps rather than displacing an agreement wholesale) is load-bearing for
  q-i2c12-024, q-i2c12-025 and cs-i2c12-02-b; confirm the SM states it in these
  terms.
- **Used in:** q-i2c12-023, q-i2c12-024, q-i2c12-025, cs-i2c12-02 (sub b,
  distractor D), notes §7, one-page revision summary.
- **Spot-checked by:** _(blank)_

## Sections 24 and 25, LLP Act 2008 — cessation and registration of changes

- **Position relied on (paraphrase):** a person may cease to be a partner **in
  accordance with an agreement with the other partners** or, in the absence of
  such agreement, by giving **notice in writing of not less than 30 days to the
  other partners** (s. 24(1)); and **shall cease** on his **death or the
  dissolution of the LLP**, on being **declared of unsound mind** by a competent
  court, or on **applying to be adjudged, or being declared, insolvent**
  (s. 24(2)). A **former partner** is still regarded, in relation to a person
  dealing with the LLP, as a partner **unless that person has notice of the
  cessation or notice has been delivered to the Registrar** (s. 24(3)).
  Cessation **does not by itself discharge** obligations incurred while a partner
  (s. 24(4)). Unless the agreement provides otherwise, the former partner, or the
  person entitled to his share on his death or insolvency, receives an amount
  **equal to the capital contribution actually made** and his **share in
  accumulated profits after deducting accumulated losses**, determined **as at
  the date of cessation** (s. 24(5)), with **no right to interfere in
  management** (s. 24(6)). A **partner** must inform the LLP of a change in his
  **name or address within 15 days** (s. 25(1)); the **LLP** must file notice
  with the Registrar **within 30 days** where a person **becomes or ceases** to
  be a partner, and within 30 days of a change in a partner's name or address
  (s. 25(2)); the notice is **signed by a designated partner** and, for an
  incoming partner, carries his **statement of consent** (s. 25(3)); default
  attracts **penalties** on the LLP and every designated partner (s. 25(4)) and
  on the defaulting partner (s. 25(5)); and a **former partner may file the
  notice himself** where he has reasonable cause to believe the LLP will not
  (s. 25(6)).
- **Source:** LLP Act 2008, ss. 24 and 25 — transcribed 27 Aug 2026, not
  re-fetched.
- **AMENDMENT-SENSITIVE (NOT examined):** the **penalty figures in s. 25(4) and
  (5)** were substituted in 2021, replacing the earlier fine. The notes state
  them qualitatively and no question turns on an amount.
- **Used in:** q-i2c12-026 (**numerical** — the 30-day resignation notice),
  q-i2c12-027, q-i2c12-028 (**numerical** — the 30-day filing), notes §8 and
  Scenario 3, one-page revision summary.
- **Spot-checked by:** _(blank)_

## Sections 26 to 31, LLP Act 2008 — extent of liability

- **Position relied on (paraphrase):** every partner is, for the purpose of the
  business of the LLP, the **agent of the LLP but not of the other partners**
  (s. 26). The LLP is **not bound** by anything done by a partner in dealing with
  a person **if** the partner **in fact has no authority** to act **and** that
  person **knows he has no authority, or does not know or believe him to be a
  partner** (s. 27(1)) — **both limbs cumulative**. The LLP **is liable** where a
  partner is liable as a result of a **wrongful act or omission in the course of
  the business of the LLP or with its authority** (s. 27(2)); an obligation of
  the LLP, in contract or otherwise, is **solely the obligation of the LLP**
  (s. 27(3)), met out of **the property of the LLP** (s. 27(4)). A partner is
  **not personally liable** for such an obligation **solely by reason of being a
  partner** (s. 28(1)), but remains liable for **his own** wrongful act or
  omission and is **not** liable for that of **any other partner** (s. 28(2)).
  **Holding out** — a person who represents himself, or knowingly permits himself
  to be represented, to be a partner is liable to anyone who on the faith of that
  representation gives credit to the LLP, and where the LLP receives credit as a
  result **the LLP is liable to the extent of the credit received or the
  financial benefit derived**, without prejudice to his liability; continued use
  of a **deceased partner's name** does not of itself make his legal
  representative or estate liable for acts after his death (s. 29). **Unlimited
  liability for fraud** — where an act is carried out by the LLP or any partner
  **with intent to defraud creditors** or for any fraudulent purpose, the
  liability of the **LLP and of the partners who so acted is unlimited**, and
  where the act is a partner's the **LLP is liable to the same extent unless it
  establishes that the act was without its knowledge or authority**; criminal
  liability for those knowingly party, and **compensation** for loss caused by
  affairs conducted fraudulently (s. 30). **Whistle-blowing** — reduction or
  waiver of penalty for useful information, and protection from discharge,
  demotion or discrimination (s. 31).
- **Source:** LLP Act 2008, ss. 26 to 31 — transcribed 27 Aug 2026, not
  re-fetched. The contrast drawn with **ss. 18 and 25 of the Indian Partnership
  Act 1932** is stated in our own words. **Reviewer note:** the three-way split
  the notes apply — a partner's own wrong (partner and LLP both liable), another
  partner's wrong (LLP only), and a contractual obligation (LLP only) — is the
  Study Material's standard analysis restated; confirm it, since cs-i2c12-02 and
  d-i2c12-04 award marks on it. Confirm too that the **rupee fine range in
  s. 30(2)** was not altered; the notes state it only qualitatively and no
  question turns on it.
- **Used in:** q-i2c12-029, q-i2c12-030, q-i2c12-031, q-i2c12-032, cs-i2c12-02
  (subs b, c and d), d-i2c12-04 (all points), notes §9 and Scenario 4, one-page
  revision summary.
- **Spot-checked by:** _(blank)_

## Sections 32 and 33, LLP Act 2008 — contributions

- **Position relied on (paraphrase):** a contribution may consist of **tangible,
  movable or immovable, or intangible property or other benefit** to the LLP,
  **including money, promissory notes, other agreements to contribute cash or
  property, and contracts for services performed or to be performed** (s. 32(1));
  the **monetary value** of each partner's contribution is **accounted for and
  disclosed in the accounts** in the prescribed manner (s. 32(2)). A partner's
  obligation to contribute is **as per the LLP agreement** (s. 33(1)); and a
  **creditor who extends credit or acts in reliance on an obligation described in
  the LLP agreement, without notice of any compromise between the partners, may
  enforce the original obligation** against that partner (s. 33(2)).
- **Source:** LLP Act 2008, ss. 32 and 33 — transcribed 27 Aug 2026, not
  re-fetched.
- **Used in:** q-i2c12-033, notes §10, one-page revision summary.
- **Spot-checked by:** _(blank)_

## Sections 34, 34A, 35, 36, 37 and 38, LLP Act 2008 with Rule 24 — accounts, audit and filings

- **Position relied on (paraphrase):** every LLP shall maintain **proper books of
  account** for each year of its existence, **on a cash basis or an accrual
  basis** and according to the **double entry system**, at its **registered
  office**, for the prescribed period (s. 34(1)). It shall, **within six months
  from the end of each financial year**, prepare a **Statement of Account and
  Solvency** as at the last day of that year, **signed by the designated
  partners** (s. 34(2)), and **file it with the Registrar** within the prescribed
  time (s. 34(3)). Accounts are to be **audited in accordance with the prescribed
  rules**, the Central Government having power to **exempt any class or classes**
  (s. 34(4)). The Central Government may, **in consultation with the National
  Financial Reporting Authority**, prescribe **standards of accounting and of
  auditing as recommended by the Institute of Chartered Accountants of India**
  for a class or classes of LLPs (s. 34A). Every LLP shall file an **annual
  return**, duly authenticated, **within 60 days of the closure of its financial
  year** (s. 35(1)), default attracting a **daily penalty** on the LLP and its
  designated partners subject to a maximum (s. 35(2)). The **incorporation
  document, the names of partners and changes in them, the Statement of Account
  and Solvency and the annual return** are open to **public inspection** on
  payment of the prescribed fee (s. 36). **False statements** are punishable
  (s. 37), and the **Registrar may require information or explanation** from any
  present or former partner or designated partner (s. 38).
- **Rules-level positions relied on (LLP Rules 2009, Rule 24):** the Statement of
  Account and Solvency is filed in **Form 8 within 30 days from the end of six
  months of the financial year** to which it relates (**30 October** where the
  financial year ends 31 March); the annual return is filed in **Form 11**
  (**30 May** on the same assumption); **books are preserved for eight years**
  from the date on which they are made; and an LLP whose **turnover does not
  exceed ₹40 lakh in any financial year and whose contribution does not exceed
  ₹25 lakh** is **exempt from audit**, so that audit becomes compulsory where
  **turnover exceeds ₹40 lakh OR contribution exceeds ₹25 lakh**.
- **Source:** LLP Act 2008, ss. 34, 34A, 35, 36, 37 and 38, and Rule 24 of the
  LLP Rules 2009 — transcribed 27 Aug 2026, not re-fetched.
- **AMENDMENT-SENSITIVE — flag for the reviewer, three separate items:**
  1. **Rule 24 audit thresholds.** The ₹40 lakh turnover and ₹25 lakh
     contribution figures, and the fact that the **exemption** is conjunctive so
     that the **audit trigger is disjunctive (OR)**, drive **cs-i2c12-03-c**
     (verified numerical) and the mistake callout in notes §11. They are
     **rules-level** and move by notification. If they change, the question and
     the verifier constants must move together.
  2. **Form 8 / Form 11 mechanics.** The **form numbers** and the **30 days
     after six months** are rules-level; only the **60 days** in s. 35(1) is
     Act-level. **q-i2c12-035, cs-i2c12-03-a and cs-i2c12-03-b** are verified
     numericals on these clocks. The Ministry has repeatedly **extended** filing
     dates for particular years by circular; the notes warn that an extension is
     never the law and no question uses one.
  3. **s. 34A and the penalties.** Section 34A was **inserted in 2021**; the
     penalties in ss. 34(5) and 35(2) were **recast in 2021** into penalties
     adjudicated by the Registrar under s. 68A, with a **reduced penalty for a
     small LLP or start-up LLP**. **No rupee figure is examined.**
- **Used in:** q-i2c12-034, q-i2c12-035 (**numerical**), cs-i2c12-03 (subs a, b
  and c — all three **numerical** — and sub d), d-i2c12-06 (all points), notes
  §11 (table, working note, two mistake callouts and an AMENDMENT-CHECK) and
  Scenario 5, one-page revision summary.
- **Spot-checked by:** _(blank)_

## Sections 39, 42 and 43, LLP Act 2008 — compounding, assignment and investigation

- **Position relied on (paraphrase):** the **Regional Director**, or an officer
  **not below that rank** authorised by the Central Government, may **compound
  any offence punishable with fine only**, collecting a sum **not exceeding the
  maximum and not less than the minimum fine**, with a bar where a **like
  offence was compounded within the preceding three years** (s. 39). A partner's
  rights to a **share of profits and losses and to receive distributions** are
  **transferable wholly or in part** (s. 42(1)); the transfer does **not by
  itself cause disassociation of the partner or dissolution and winding up**
  (s. 42(2)); and it does **not by itself entitle the transferee to participate
  in management or conduct of the activities, or to access information**
  (s. 42(3)). The **Central Government appoints inspectors** to investigate the
  affairs of an LLP where the **Tribunal so declares by order**, where the **LLP
  itself applies**, or where the Central Government is of the requisite
  **opinion** (fraud, unlawful purpose, oppression of partners, misconduct in
  formation or management, or partners not given the information they might
  reasonably expect); **not less than one-fifth of the total number of partners**
  may apply (s. 43).
- **Source:** LLP Act 2008, ss. 39, 42 and 43 — transcribed 27 Aug 2026, not
  re-fetched.
- **AMENDMENT-SENSITIVE:** **s. 39 was substituted by the 2021 Amendment**,
  which moved compounding from the **Central Government** to the **Regional
  Director** and confined it to offences **punishable with fine only**. The notes
  state the amended position and the pointer callout separating the four
  decision-makers depends on it; **no bank question turns on s. 39**, but
  d-i2c12-02 and the revision summary mention the adjudication chain.
- **Used in:** q-i2c12-036, notes §12, one-page revision summary.
- **Spot-checked by:** _(blank)_

## Sections 55 to 58 and the Second, Third and Fourth Schedules — conversion into an LLP

- **Position relied on (paraphrase):** a **firm** may convert into an LLP in
  accordance with the **Second Schedule** (s. 55); a **private company** in
  accordance with the **Third Schedule** (s. 56); and an **unlisted public
  company** in accordance with the **Fourth Schedule** (s. 57). The **Second
  Schedule** permits conversion only if the partners of the LLP comprise **all
  the partners of the firm and no one else**. The **Third and Fourth Schedules**
  add that there must be **no security interest in the company's assets
  subsisting or in force at the time of the application**, and that the partners
  of the LLP must comprise **all the shareholders of the company and no one
  else**. On registration the Registrar issues a **certificate of
  registration**; the LLP must **inform the Registrar of Firms or the Registrar
  of Companies within 15 days** of the date of registration; and on and from that
  date there is an **LLP by the name specified**, all **property, assets,
  interests, rights, privileges, liabilities, obligations and the whole
  undertaking vest in the LLP without further assurance, act or deed**, and the
  firm or company is **deemed dissolved** and removed from the relevant register
  (s. 58). The Schedules carry the continuity provisions — **pending
  proceedings**, **convictions, rulings, orders and judgments**, **existing
  agreements, contracts and deeds**, **contracts of employment**, and
  **approvals, permits and licences transferred subject to the provisions of the
  Act under which they were issued** — and require every **official
  correspondence** to bear a **conversion statement and the former entity's name
  and registration number for twelve months commencing not later than fourteen
  days after registration**.
- **Source:** LLP Act 2008, ss. 55 to 58 and the Second, Third and Fourth
  Schedules — transcribed 27 Aug 2026, not re-fetched. **Reviewer note:** the
  Schedules also carry conditions about **up-to-date filings, consent of
  secured creditors and objections**, which the notes summarise rather than
  enumerate; please confirm the Study Material's list before initialling, and
  confirm that a **listed** public company remains outside ss. 55 to 57.
- **Used in:** q-i2c12-037, cs-i2c12-01 (subs a, b, c (**numerical** — the
  15-day intimation) and d), d-i2c12-05 (all points), notes §13 and Scenario 6,
  one-page revision summary.
- **Spot-checked by:** _(blank)_

## Sections 59 to 68A and 75, LLP Act 2008 — foreign LLPs, compromise, winding up, Special Courts and strike off

- **Position relied on (paraphrase):** the **Central Government may make rules**
  for the establishment of a place of business in India by **foreign LLPs** —
  defined in **s. 2(1)(m)** as an LLP formed, incorporated or registered outside
  India that establishes a place of business within India — by applying or
  incorporating, with appropriate modifications, the provisions of the Companies
  Act or such other regulatory mechanism as may be prescribed (s. 59). A
  **compromise or arrangement** between an LLP and its **creditors** or its
  **partners** may be ordered to be put to a **meeting** by the **Tribunal**,
  and if a majority representing **three-fourths in value** of those present and
  voting agrees and the Tribunal **sanctions** it, it is **binding on all** of
  them and on the LLP (ss. 60 to 62). An LLP may be wound up **voluntarily or by
  the Tribunal** (s. 63), the Tribunal's grounds being the **LLP's own
  decision**, the number of partners **reduced below two for more than six
  months**, **inability to pay debts**, acts **against the sovereignty and
  integrity of India, the security of the State or public order**, **default in
  filing the Statement of Account and Solvency or the annual return for five
  consecutive financial years**, and the **just and equitable** ground (s. 64).
  **Sections 67A to 67C** provide for **Special Courts**, an offence punishable
  with **imprisonment of three years or more** being triable by the Special Court
  and every other offence by a **Metropolitan Magistrate or Judicial Magistrate
  of the first class**. **Section 68A** empowers the Central Government to
  appoint **adjudicating officers** to **adjudge penalties**, with an **appeal to
  the Regional Director within 60 days**. Under **s. 75** with **Rule 37**, the
  Registrar may **strike the name of an LLP off the register** where he has
  reasonable cause to believe it is not carrying on business or operation, after
  a hearing, and an LLP may apply for strike off itself.
- **Source:** LLP Act 2008, ss. 59 to 68A and 75, and Rule 37 of the LLP Rules
  2009 — transcribed 27 Aug 2026, not re-fetched.
- **AMENDMENT-SENSITIVE — flag for the reviewer:** **clause (c) of s. 64
  (inability to pay debts) was omitted by the LLP (Amendment) Act 2021**,
  insolvency of LLPs being routed to the **Insolvency and Bankruptcy Code 2016**
  as and when the relevant provisions are notified. Study Material editions
  **differ** on whether the ground is still listed. The notes therefore state the
  clause **with an explicit AMENDMENT-CHECK qualification**, and
  **q-i2c12-038 deliberately turns on clause (e) (five consecutive financial
  years) and clause (b) (below two partners for more than six months), never on
  clause (c)**. **Sections 67A to 67C and 68A were inserted in 2021** — confirm
  the numbering. The **strike-off procedure in Rule 37** is rules-level and is
  described only in outline.
- **Used in:** q-i2c12-038, d-i2c12-06 (point 6, the s. 64(e) link), notes §14
  (with an AMENDMENT-CHECK callout), one-page revision summary.
- **Spot-checked by:** _(blank)_

## Scope boundary recorded for the reviewer

- **Position relied on:** the chapter covers the **LLP Act 2008 as amended to
  2021**, in the scope set by ICAI SM Paper 2 Chapter 12. Sections 44 to 54
  (inspectors' powers, reports and consequences of investigation) are described
  only in outline; **ss. 65 and 67** are mentioned as enabling powers; the
  detailed winding-up and dissolution rules are outside this chapter. Company
  law topics — incorporation, prospectus, share capital, deposits, charges,
  management and administration — are separate chapters of Paper 2. Where the
  notes cross-refer to the **Companies Act 2013** (s. 3A on members below the
  minimum, s. 128(1) on the accrual basis, s. 149(3) on the 182-day resident
  director, ss. 153 to 159 on DIN), the reference is comparative and is flagged
  as such; **please verify those cross-references too**, since q-i2c12-034 and
  the residence callouts rely on the contrast.
- **Used in:** notes §3, §4, §9, §11, common-mistakes list items 1, 2 and 12.
- **Spot-checked by:** _(blank)_
