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
