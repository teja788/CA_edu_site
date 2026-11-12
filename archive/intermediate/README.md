# Archived Intermediate content (unpublished 12 Nov 2026)

Everything here was moved out of `src/pages/` to finish the Foundation-only
pivot (commit 4501976 rewrote the homepage/nav; these routes stayed live).
Nothing is deleted — this is the staging ground for the eventual Intermediate
launch.

What's here:

- `pages/` — the whole `/intermediate/` route tree (advanced-accounting notes,
  the off-syllabus partnership trio, per-paper amendment trackers).
- `level-paper-route/` — the old `src/pages/[level]/[paper]/` dynamic hubs
  (served Intermediate/Final papers only; Foundation hubs live under
  `src/pages/foundation/[paper]/`).
- `mock.astro` — the Intermediate 30:70 mock composer (`/practice/mock/`).
- `attempt.astro` — the Intermediate attempt dashboard (`/attempt/`).

Before any of it ships again, resolve the blocking items in
`manual_verification_checklist.md` and `review_queue.md` — in particular:
partnership content is now Foundation syllabus (Foundation P1 Ch 10 covers it;
decide whether these deeper topic pages re-home there), and the Inter law/tax
attempt-tagging items are unverified.

Related data still in `src/data/` (intermediate.js, amendments.js, the
`src/data/questions/intermediate/` banks, the Inter flashcard decks and the
launch MCQs in site.js) is retained but no longer reachable from any page;
`src/scripts/banks.js` and the flashcards page filter to Foundation.
