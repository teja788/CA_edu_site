# Citations — law/tax/audit traceability

Every law, tax, or audit chapter ships a citations file here, generated in the
same session as the content:

    citations/<level>/<paper-slug>/citations_<chapter-slug>.md

One entry per section/AS/SA/notification cited anywhere in that chapter's
notes, questions, or flashcards:

```markdown
## s.6, Indian Contract Act 1872
- **Bare-act line relied on:** "A proposal is revoked — (1) by the communication
  of notice of revocation by the proposer to the other party; …"
- **Source:** India Code, consolidated Contract Act 1872
- **Used in:** q-offer-004 (options b, d), notes §2.3, flashcard f-offer-11
- **Spot-checked by:** _(reviewer initials + date — blank until a human checks)_
```

Rules:

- The "bare-act line relied on" is quoted from the primary source (India Code /
  incometaxindia.gov.in / mca.gov.in / cbic.gov.in) — statutory text is
  reproducible under Copyright Act s.52(1)(q). ICAI-copyrighted text (SM, SA,
  Guidance Notes) is never quoted here or anywhere; paraphrase and cite the
  number instead.
- A law MCQ whose answer cannot be traced to an entry in this file does not
  merge — this file is what makes the human spot-check fast.
- Tax entries additionally record notification number + date and the
  "as amended by the Finance Act <year>" position.

Reviewer workflow: open the chapter's citations file, verify each quoted line
against the primary source, initial the entry, then remove the page's
"Community draft" badge in the same PR.
