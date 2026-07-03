# Contributing to Adhyayan

Thank you — reader-contributors are how a free project reaches paid-quality accuracy.
CA finalists and newly-qualified CAs especially: an hour of your review protects
thousands of study-hours downstream.

## Ways to help

- **Report an error** — open an issue with the page, what's wrong, and the ICAI
  source or Act section showing the correct position. Confirmed errors are fixed
  within 7 days, publicly.
- **Review a community draft** — pages badged "✎ Community draft" need a qualified
  reviewer before the badge comes off.
- **Write content** — notes, questions, flashcards for papers not yet covered.
  Start an issue first so work isn't duplicated.
- **Check links** — official URLs move often; dead links destroy trust fastest.

## The accuracy machine (every PR is checked against this)

1. **Traceability** — every factual claim in notes carries a source reference:
   ICAI SM module/unit, Act section, notification number. No source, no merge.
2. **Two-person rule** — content merges need an author and a reviewer (ideally a
   qualified CA or Final-level student). Until reviewed, pages ship with the
   visible "Community draft" badge — never silently.
3. **Attempt gating** — `applicableAttempts` and `lastVerified` are mandatory
   frontmatter/fields. Tax questions additionally require `lawAsOnDate`.
   Rule: **no tax/law content merges without attempt tags.**
4. **Original words only** — never copy ICAI question text, suggested answers, or
   study-material prose. Concepts aren't copyrightable; expression is. Write fresh
   questions testing the same concept with different numbers/facts.
5. **Link-only for ICAI material** — never commit or re-host ICAI PDFs.

## Content style

- Calm, factual, never judgmental. No countdown pressure, no streak guilt.
- Semantic color always pairs with a glyph + word (✓ Correct, ✕ Incorrect, ! warning).
- Numbers use tabular figures and Indian grouping (₹ 2,40,000).
- Every MCQ option gets an explanation of *why* it's right or wrong; the correct
  option links to the exact note section.
- Worked examples before independent problems; common-mistake callouts wherever
  students actually go wrong.

## Dev setup

```sh
npm install && npm run dev
```

Content lives in `src/data/` (questions, flashcards, resources, taxonomy) and
`src/pages/` (notes). The design system is documented in the design handoff bundle
(`CA Intermediate UI System.zip`) — recreate its patterns, don't invent new ones.

## The verification pipeline (how a reviewer audits fast)

Every chapter of content moves through the same machine-checked pipeline
before a human ever spends time on it. Reviewers: you are auditing the
residue the machines can't judge, not re-checking arithmetic.

1. **Numerical answers are computed, never trusted.** Each chapter bank
   (`src/data/questions/<level>/<paper>/<chapter>.json`) flags computable
   questions `"numerical": true` and ships
   `scripts/verify_numerical/verify_<chapter>.py`, which recomputes every
   answer from the stem's parameters. CI
   (`.github/workflows/verify-content.yml`) fails the PR on any mismatch or
   missing verifier — a fluent explanation defending a wrong key cannot merge.
   The toolkit's own self-test contains a planted wrong key to prove the
   runner catches exactly that.
2. **Non-computable MCQs get an independent pass.** `scripts/consistency_check/`
   strips a bank to a blind file, a fresh session re-answers it without the
   key, and disagreements are quarantined in `review_queue.md` (root) with
   both answers shown — quarantined questions never merge until a human
   resolves them from the primary source.
3. **Law/tax/audit claims are traceable.** Every cited section/AS/SA/
   notification has an entry in `citations/<level>/<paper>/citations_<chapter>.md`
   quoting the exact bare-act line it relies on. Spot-check the quotes against
   India Code / incometaxindia.gov.in / mca.gov.in / cbic.gov.in, initial the
   entries, and remove the draft badge in the same PR.
4. **Unreviewed pages say so, loudly.** Content whose frontmatter/props carry
   `review_status: "unreviewed"` (the `draft` flag on `TrustRow`) renders the
   amber "✎ Community draft — cross-check with ICAI study material" badge with
   a report link. Every report link pre-fills a GitHub issue with the page ID
   via `/report-error/?page=…`. The badge comes off only via item 3.
5. **Links are machine-checked weekly.** `scripts/linkcheck/` + the Monday
   workflow ping every official URL, open an issue on failure, and stamp
   `lastChecked` dates after a green sweep.

The fastest useful review: open `review_queue.md`, resolve a quarantined
question against the bare Act, and open a PR with the fix — 15 minutes,
permanent value.

## Licensing of contributions

By contributing you agree your code is MIT-licensed and your content is
CC BY-SA 4.0 — this keeps the project forkable and alive beyond any one maintainer.
