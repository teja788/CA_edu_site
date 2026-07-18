# Site audit — 17 Jul 2026 (RESOLVED 19 Jul 2026)

Full-code audit of everything except `Ravi_OS/`, run by five parallel review agents
(infrastructure, pages/app logic, question bank, chapter content, scripts/CI),
followed by a fix pass that resolved every finding except the deliberate deferrals
listed at the bottom.

Verification at close: build green (63 pages incl. new 404), `verify_numerical`
234/234, all three tooling selftests pass, all data JS parses, link-check URL
extraction yields 20 clean URLs, lastChecked stamper covers all four data files.

## What was found and fixed

**Infrastructure / PWA**
- Service worker: no longer serves homepage HTML for failed asset requests
  (navigate-only fallback); only caches `response.ok` non-206 responses; cache
  bumped to `adhyayan-v2`.
- Added `src/pages/404.astro`; `robots.txt` is now generated from the Astro
  config (`src/pages/robots.txt.ts`) so the sitemap URL can't diverge.
- Real PNG icon set generated (192/512 maskable, apple-touch-icon, 1200×630
  og-image) + manifest and `<head>` wired (`summary_large_image`).
- Base.astro: skip-to-content link, `aria-pressed` on toggles, storage access
  wrapped in try/catch. global.css: badge border token, quiz-bar dark-theme vars.
  Callout falls back to 'note' on unknown kind. store.js `write()` guarded.

**Progress tracking (was decorative, now real)**
- One mastery scheme: `i1-chN`/`f1-chN` (chapters, written by the quiz from bank
  metadata + MDX frontmatter) plus `p1-ch4-*` (partnership refresher topics).
  The 12 legacy site.js questions carry explicit `masteryId`s.
- `getPaperProgress(prefixes, total)` counts real keys; dashboard + hub use
  `['i1-ch', 'p1-ch4-']` over 18 tracked topics (15 chapters + 3 refresher).
- Mastery streaks are per topic (3 corrects on THAT topic → proficient);
  level 3 requires proficiency re-demonstrated on a later day (store.js).
- Mastery hydration lives once in Mastery.astro (5 page copies removed).

**P1 hub / data model**
- Hub rebuilt from the verified ICAI taxonomy in `intermediate.js` — all 13
  published chapters linked (5 were orphaned), Ch 7 & 10 shown as "Notes soon",
  duplicate legacy sections removed, `paper1Sections` deleted from site.js.
- Partnership demoted to a labelled "Refresher (pre-Inter foundations)" section —
  it is not a chapter of new-scheme Inter P1. Legacy question topic labels
  re-mapped to new-scheme chapters.

**Practice engines**
- Banks carry a canonical `paperSlug`; quiz/descriptive/mock filter on it
  exactly (the old slugified-name `.includes` broke 4 of 6 future papers).
- Quiz: honest empty states for mistakes/topic modes (no silent full-deck
  fallback); options shuffled with positional letters (authored keys skewed
  A/B); all question rendering XSS-safe (textContent/createElement); timed-quiz
  interval cleared at finish; negative-marking chip guarded on empty decks.
- Mock composer: pools shuffled per compose (was deterministic); slug map
  deduplicated; `(${2} marks)` literal fixed.
- Flashcards: progress bar can't exceed 100% ("Again" re-queues counted).
- Dashboard/attempt: countdown reads `attempt.beginsOn` from site.js (no
  hardcoded dates); mistake list safely rendered; fake personalization removed;
  "change attempt" → /attempt/. Study plan collapses to a revision sprint under
  4 weeks (phases can no longer exceed available weeks). Practice index shows
  the real merged deck count. `[level]/[paper]` Practice tab is a real link.

**Question bank + content data**
- All 13 banks: `paperSlug` added; 129 missing `"numerical"` keys added; zero
  wrong answers found in the full audit (234 numericals recomputed + ~100
  conceptual spot-checks). Flashcard `ir-2` fixed (s.61(1)(b) proviso: NCLT
  needed for consolidation/division changing voting %). Broken amendment anchor
  fixed.

**Chapter content (MDX) — no critical factual errors found; all ~30 worked
examples recompute correctly**
- New `citations_revenue-based-as.md` + review-queue VERIFY section (was the
  only chapter without them).
- s.66(1)(b)(i)/(ii) lettering un-swapped in internal-reconstruction citations.
- AS 15: sub-50-employee SMC "other rational method" carve-out added
  (applicability + liabilities chapters and their citations).
- AS count restated frame-proof (32 issued / AS 6, 8, 30–32 withdrawn / 27 in
  force = the notified set).
- AS 7 WE1 labour-escalation stem disambiguated; WE2 cost-to-complete
  clarified; depreciation WE1 "transit insurance"; "Other Equity" → "Reserves
  and Surplus"; foundation frontmatter schema normalised.
- sources.yaml: ICAI MSME/Large classification (1 Apr 2024) and the ICAI
  Framework registered under reference_only.

**Tooling / CI**
- `update_last_checked.py`: matches `LAST_CHECKED = '...'` constants (was
  silently skipping foundation.js/intermediate.js); `--root` respected;
  `--date` validated + applied to YAML; fails loudly on format drift.
- `link-check.yml`: URL grep no longer captures `${...}` template literals
  (guaranteed false weekly failures); auto-issue gated on the lychee step
  specifically.
- `attempt_lint.py`: vacuous-pass guard (volatile paper with content but 0
  checked files → exit 1), argparse, empty-value frontmatter fails.
- `consistency_check.py`: answer normalization (strip/upper), repo-anchored
  default queue path. All selftests updated and still adversarial.

## Deliberately deferred (decisions or content work, not bugs)

1. **Real domain** — `astro.config.mjs` still has the placeholder
   `https://adhyayan.example` (robots.txt/sitemap/canonicals derive from it).
   One-line change once a domain is chosen. BLOCKING for publish.
2. **Content coverage** — Inter P1 Ch 7 (AS 4/5/11/22) and Ch 10 (AS 21/23/27)
   notes + banks; more Foundation chapters; question banks for the other 5
   Inter papers.
3. **Human review pass** — the ※ rows in citations files and the VERIFY
   sections in review_queue.md still need a CA's initials (by design).
4. **Analytics** — none present; decide (Plausible/GoatCounter fit the
   positioning) before/at launch.
5. **Ads** — AdSlot is a visual placeholder; no network integration, no
   ads.txt. Fine to launch ad-free.
6. **`CA Intermediate UI System.zip`** at repo root — design-asset archive,
   kept (extraction dir is gitignored); remove if unwanted.
7. **SW precache** — offline works for visited pages; precaching hashed assets
   would need a build-time-generated SW (nice-to-have).
