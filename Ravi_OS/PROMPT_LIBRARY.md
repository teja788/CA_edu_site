# Future-me prompt library

50 reusable prompts for the tasks I ask AI to do again and again — 5 per category.
Each has **Use when** / **Fill in** (`{{PLACEHOLDER}}` slots) and a paste-ready prompt
below the divider, with an accuracy contract baked in (cite-or-UNVERIFIED, no invented
studies/filings/quotes, facts separated from interpretation).

Canonical copy lives in the Ravi OS Prompt Library (tag `custom:future-me`);
this file is the committable export.

## Stock analysis

### 1. Stocks · Catalyst deep-dive with thesis & invalidation

**Use when:** A stock hits my radar and I need a full catalyst workup before it goes on the watchlist.
**Fill in:** `{{TICKER}}`, `{{EXCHANGE}}` (NSE/BSE/NYSE/NASDAQ), `{{CATALYST_HINT}}` — what drew my attention

---

Act as a buy-side catalyst analyst. Work up {{TICKER}} ({{EXCHANGE}}) around this trigger: {{CATALYST_HINT}}.

Deliver, in order:
1. **Business snapshot** — what the company actually sells, to whom, revenue mix (cite the specific filing/annual report and period each number comes from).
2. **The catalyst** — what exactly is expected to happen, the evidence it's real (filings, exchange announcements, credible reports — named and dated), and the expected timeline.
3. **Base rates** — how situations like this have historically resolved for comparable companies. If you don't have solid base-rate data, say so plainly instead of hand-waving.
4. **Thesis in 3 sentences** — the bet, the mechanism, the payoff window.
5. **Invalidation** — the specific price level AND the specific event/datapoint that would prove the thesis wrong. A thesis without invalidation is rejected.
6. **Monitoring plan** — the 3–5 things to watch each quarter, and where to watch them (which filing, which disclosure).
7. **Bear case steelman** — the strongest honest argument against, not a strawman.

Educational analysis only, not investment advice — I make the final call and size my own positions.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 2. Stocks · Quarterly results vs my thesis

**Use when:** Results are out for a stock I hold or track and I need a disciplined thesis check, not a news summary.
**Fill in:** `{{TICKER}}`, `{{MY_THESIS}}` — thesis + invalidation as I recorded it, `{{RESULTS}}` — pasted results/press release or filing reference

---

My recorded thesis for {{TICKER}}: {{MY_THESIS}}

Latest results: {{RESULTS}}

Do a thesis audit, not a news recap:
1. Extract the thesis's load-bearing assumptions as a numbered list (growth, margins, order book, market share — whatever it actually depends on).
2. For each assumption: what did this quarter's numbers say? Quote the exact figure and where it appears. Mark each assumption CONFIRMED / WEAKENED / BROKEN / NOT TESTED THIS QUARTER.
3. Separate one-off noise (exceptional items, deferrals, base effects) from trend — show your reasoning.
4. Check management commentary against last quarter's commentary: what changed, what quietly disappeared?
5. Verdict: THESIS INTACT / WEAKENED / BROKEN, with the single strongest piece of evidence for that verdict.
6. Update the invalidation level and monitoring list if warranted.

Resist narrative drift: judge against what I originally believed, not a new story that fits the print. Educational analysis only, not investment advice — I make the final call and size my own positions.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 3. Stocks · Red-flag forensic scan

**Use when:** Before any position gets serious money — or when something smells off about a holding.
**Fill in:** `{{TICKER}}`, `{{MARKET}}` (India/US), `{{DOCS}}` — filings/reports available, or note what to pull

---

Run a forensic red-flag scan on {{TICKER}} ({{MARKET}}). Check each item and report EVIDENCE FOUND / CLEAN / COULD NOT VERIFY — never guess:

**Governance:** promoter pledging trend (India) or insider selling pattern (US); board independence; auditor changes or resignations and stated reasons; frequent CFO/CS exits; regulator actions (SEBI/SEC — cite the order if any).
**Accounting:** receivables growing faster than revenue; cash flow from operations persistently below profit; contingent liabilities vs net worth; related-party transactions (list counterparties from the actual disclosure); frequent exceptional items; capitalization of costs peers expense.
**Capital behavior:** serial dilution, aggressive M&A with goodwill write-offs later, dividend/buyback funded by debt.
**Narrative:** guidance repeatedly missed then re-explained; sudden pivots into fashionable sectors.

For every flag raised: quote the source document and period, rate severity (disqualifying / serious / monitor), and say what additional document would confirm or clear it. End with an overall verdict: INVESTABLE WITH MONITORING / NEEDS DEEPER WORK / AVOID — and the one flag that most drives that verdict.

Educational analysis only, not investment advice — I make the final call and size my own positions.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 4. Stocks · Filing & event interpreter

**Use when:** A specific disclosure drops — 13D/13G, Form 4 cluster, block deal, big order win, buyback, pledge release — and I want to know what it actually means.
**Fill in:** `{{TICKER}}`, `{{EVENT}}` — paste the disclosure or describe it precisely, `{{MY_POSITION}}` — holding / watching / none

---

Interpret this event for {{TICKER}}: {{EVENT}}. My status: {{MY_POSITION}}.

1. **What it literally says** — strip the interpretation, state the disclosed facts (who, how much, at what price, what obligations follow).
2. **What this event type typically signals** — base rates and mechanism, honest about how noisy the signal is. Distinguish "studies/data show" (cite) from "market folklore says" (label it as folklore).
3. **Bull read and bear read** — the strongest version of each, and what each side has to believe.
4. **Discriminating evidence** — what should show up within 1–2 quarters if the bull read is right, and where it would show up (which filing, which metric).
5. **Action framework** — the conditions under which this event alone justifies action versus just a monitoring note. Do not tell me to buy or sell; give me the decision structure.

Educational analysis only, not investment advice — I make the final call and size my own positions.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 5. Stocks · Peer comparison with sourced numbers

**Use when:** I need to know whether a company is actually differentiated or just tells a better story than its peers.
**Fill in:** `{{TICKER}}`, `{{PEERS}}` — 3–5 comparables, `{{METRICS}}` — default: growth, margins, ROCE/ROIC, debt, valuation, working capital

---

Build a peer comparison: {{TICKER}} vs {{PEERS}} on {{METRICS}}.

Rules of construction:
- Every number in the table carries its source: which filing/report, which fiscal period. Mixed periods must be flagged, not silently blended.
- Flag non-comparability before comparing: different fiscal years, accounting choices (revenue recognition, capitalization), segment mixes that make a ratio misleading. A footnoted honest table beats a clean misleading one.
- If you cannot source a number, leave the cell as UNVERIFIED — do not fill from memory.

Then the analysis:
1. Where the target genuinely leads or lags peers, metric by metric.
2. Which gaps are structural (moat, mix, geography) vs cyclical vs accounting artifacts.
3. What premium/discount the market assigns and whether the sourced fundamentals justify it.
4. The one metric that most deserves a deeper look before believing the story.

Educational analysis only, not investment advice — I make the final call and size my own positions.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

## Coding projects

### 6. Coding · Idea → spec-first build brief

**Use when:** A raw project idea needs to become a proper written brief before any code — my standard starting artifact.
**Fill in:** `{{RAW_IDEA}}` — the idea in my words, `{{CONSTRAINTS}}` — stack/time/privacy constraints if any

---

Turn this raw idea into a complete build brief (my initial_prompt.md convention): {{RAW_IDEA}}. Constraints: {{CONSTRAINTS}}.

Produce a single markdown brief with:
1. **Vision paragraph** — what exists when this is done and who is measurably better off.
2. **Users & jobs** — who uses it and for what recurring job. If it's just me, say so and design for that honestly.
3. **Non-goals** — explicit list; this section prevents scope rot.
4. **Design principles** — default to local-first, private by default, no LLM calls inside code paths (agent reasoning happens at the file seam), zero-cost hosting where possible.
5. **Architecture sketch** — components, data flow, storage, one recommended stack with a one-line justification each.
6. **Milestone plan** — 3–5 milestones, each independently shippable and testable; explicitly note "build milestone-by-milestone, don't one-shot."
7. **Validation gates** — what must pass before each milestone counts as done.
8. **Risks & open questions** — ranked; mark which ones block milestone 1 vs which can wait.

Ask me at most 3 clarifying questions ONLY if genuinely blocking; otherwise state your assumptions inline and proceed.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 7. Coding · CLAUDE.md contract writer

**Use when:** A repo needs its agent contract — conventions plus hard rules plus validation gates — written or overhauled.
**Fill in:** `{{REPO}}` — what the project is/does, `{{HARD_RULES}}` — non-negotiables (privacy, billing, data), `{{GATES}}` — existing tests/checks

---

Write a CLAUDE.md for this repo: {{REPO}}. Non-negotiables: {{HARD_RULES}}. Existing checks: {{GATES}}.

Structure it as a working contract, not documentation:
1. **One-paragraph orientation** — what this project is and where to start reading.
2. **How to run and test** — exact commands, expected output, common failure and its fix.
3. **Hard rules** — the never-do list (e.g., never commit data/ or secrets, never add LLM/API calls to code paths, never weaken .gitignore, commit only on explicit ask). Each rule gets a one-line WHY so a future agent doesn't "helpfully" remove it.
4. **Conventions** — naming, structure, error handling, comment policy — only conventions that are real in this codebase, not aspirational ones.
5. **Validation gates** — the checks that must pass before any change counts as done, in run order, with the command for each.
6. **Known traps** — the 3–5 mistakes an agent is most likely to make in this specific repo.

Keep it under 120 lines: every line an agent must obey, nothing an agent can ignore. Note at the end that AGENTS.md should mirror it for other tools.

### 8. Coding · Diff review — correctness first

**Use when:** A diff or PR needs review before merge; bugs first, cleanups second, no style noise.
**Fill in:** `{{DIFF}}` — the diff/PR or branch reference, `{{CONTEXT}}` — what the change is supposed to do

---

Review this change. Intent: {{CONTEXT}}. Diff: {{DIFF}}

Pass 1 — **Correctness (the only pass that can block):** For each candidate bug, give file:line, a concrete failure scenario (specific input/state → specific wrong outcome), and the minimal fix. A finding without a concrete failure scenario doesn't count — drop it. Check especially: boundary conditions, error paths, concurrency/ordering assumptions, unhandled empty/null states, behavior changes to untested code paths, security (injection, path traversal, secrets in code).

Pass 2 — **Simplification:** dead code introduced, duplicated logic that existing code already provides, abstractions with a single caller, complexity not required by the actual requirements.

Pass 3 — **Tests:** which of the Pass-1 scenarios lack a test; propose the smallest test that would have caught each.

Rank all findings by severity. No style/formatting comments unless they hide a bug. For each finding state your confidence (certain / likely / worth checking) — and if you're pattern-matching rather than reasoning from this code's actual behavior, say so.

### 9. Coding · Debugging protocol

**Use when:** Something is broken and I want a disciplined root-cause hunt, not guess-and-patch.
**Fill in:** `{{BUG}}` — symptoms, error text, when it started, `{{STACK}}` — language/framework/environment, `{{REPRO}}` — steps if known

---

Debug this with me: {{BUG}}. Stack: {{STACK}}. Repro: {{REPRO}}.

Follow the protocol strictly:
1. **Reproduce first.** Define the minimal reliable reproduction. If we can't reproduce, that's step zero — design the logging/instrumentation to catch it in the act, and stop there until data exists.
2. **State the delta.** What changed between working and broken (code, data, dependency, environment)? If "nothing changed," something changed — list the usual invisible suspects for this stack.
3. **Ranked hypotheses.** 3–5, each with: mechanism (how it produces exactly these symptoms — not just similar ones), prior probability, and the cheapest discriminating test. Order tests by information-per-minute, not by which hypothesis is most likely.
4. **Run the splits.** After each test result I give you, prune the hypothesis list explicitly — say what got eliminated and why.
5. **Fix the root cause,** not the symptom. If the fix is at a different layer than the symptom, explain the causal chain end to end.
6. **Regression test** that fails before the fix and passes after.
7. **Three-line postmortem:** cause, why it wasn't caught, what makes this class of bug impossible or loud next time.

Never propose a fix before a hypothesis survives a discriminating test. "Try this and see" is banned.

### 10. Coding · Refactor / migration plan

**Use when:** A codebase needs restructuring or a dependency/platform migration, and I want it shippable at every step.
**Fill in:** `{{CURRENT}}` — current state and pain, `{{TARGET}}` — desired end state, `{{CONSTRAINTS}}` — downtime tolerance, test coverage reality

---

Plan this migration: {{CURRENT}} → {{TARGET}}. Constraints: {{CONSTRAINTS}}.

1. **Blast radius inventory** — everything that touches the code being changed: callers, configs, scripts, docs, CI. State how you'd verify the inventory is complete (grep patterns, dependency graphs), not just that it feels complete.
2. **Safety net first** — what tests/characterization coverage must exist BEFORE step one. If coverage is thin, writing pin-down tests for current behavior is step one, not optional.
3. **Strangler-fig steps** — a sequence where each step: is independently shippable, keeps the system fully working, is reversible, and has an explicit verification command. No step may depend on "and then we quickly also fix X."
4. **Rollback per step** — the concrete undo for each step, and the point of no return if one exists (call it out loudly).
5. **Effort estimates** — per step, with a confidence label; flag the step most likely to blow up and why.
6. **Kill criteria** — the signal that says stop and reassess rather than push through.

If the honest answer is "rewrite is cheaper than refactor" or vice versa, argue it with evidence from the codebase, not doctrine.

## Website building

### 11. Web · Niche site validation & content plan

**Use when:** Before committing weekends to a new content site — validate the niche and plan the launch content.
**Fill in:** `{{NICHE}}` — topic/angle, `{{MONETIZATION_GOAL}}` — AdSense/affiliate/product, `{{MY_EDGE}}` — why me for this niche

---

Validate this niche and plan the site: {{NICHE}}. Monetization intent: {{MONETIZATION_GOAL}}. My edge: {{MY_EDGE}}.

1. **Demand** — estimate search demand and the query landscape. Label every volume figure as an estimate with its basis; if you can't ground it, give the query list and tell me to pull real volumes from a keyword tool.
2. **Competition** — who ranks now, their content depth, domain strength, and the gap I could occupy. Name real sites only; UNVERIFIED if unsure a site exists.
3. **Monetization fit** — realistic revenue math for {{MONETIZATION_GOAL}} in this niche: RPM/commission ranges labeled as rough benchmarks with their source and date, never as promises. Include the traffic level needed for ₹X/month at those benchmarks.
4. **YMYL/policy risk** — is this niche held to higher E-E-A-T standards or AdSense-policy risk? What that demands of the content.
5. **Launch content plan** — 20 articles: mix of head/long-tail, informational/commercial intent, each with target query, angle, and internal-link role. Order by (low competition × monetization value).
6. **Verdict** — GO / GO WITH CHANGES / SKIP, with the single decisive reason, and the standard launch kit reminder (sitemap, robots, GSC, IndexNow, OG cards, analytics).

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 12. Web · SEO article brief + sourced draft

**Use when:** One target keyword needs a brief and a draft that can survive both Google and a fact-checker.
**Fill in:** `{{KEYWORD}}`, `{{SITE}}` — site and its audience, `{{ANGLE}}` — my experience/edge for E-E-A-T, `{{WORDS}}` — target length

---

Write a brief, then a draft, for {{KEYWORD}} on {{SITE}}. My angle: {{ANGLE}}. Length: {{WORDS}}.

**Brief:** search intent (what the searcher is actually trying to do); what top results cover and where they're thin (name the gap precisely); the E-E-A-T claim this article can honestly make given my angle; outline with H2/H3s; 3–5 internal-link opportunities; meta title (≤60 chars) and description (≤155) with the keyword natural, not stuffed.

**Draft rules:**
- Every statistic, price, date, and study reference carries a named source. No source available → rewrite the sentence to not need the claim, or mark UNVERIFIED for me to resolve. Never invent a study, survey, or expert quote.
- Anything time-sensitive (prices, versions, regulations) gets an as-of framing so the article ages gracefully, plus a list at the end of what I should re-verify before publishing and on each review.
- Write for the reader first: answer the intent in the first 150 words, then earn the depth. No filler intros, no "in today's fast-paced world."
- First-hand experience beats paraphrased consensus — where my angle provides it, use it and mark where I should add specifics only I know.

Deliver: brief, draft, pre-publish verification checklist, and a suggested lastReviewed date convention.

### 13. Web · Traffic-drop diagnosis

**Use when:** A site's search traffic dropped and I need an ordered differential diagnosis, not panic.
**Fill in:** `{{SITE}}`, `{{SYMPTOM}}` — what dropped, when, how much, which pages, `{{GSC_DATA}}` — what Search Console shows

---

Diagnose this traffic drop: {{SITE}}, symptom: {{SYMPTOM}}, GSC evidence: {{GSC_DATA}}.

Work the differential in likelihood order, and for each cause state the specific evidence that would confirm or exclude it:
1. **Algorithm update** — did the drop date match a known/confirmed update? You must verify update dates against current web sources, not memory — list what to check.
2. **Technical/indexing** — coverage errors, accidental noindex/robots changes, canonical issues, sitemap staleness, CWV regressions, hosting incidents. Which GSC report and which crawl check answers each.
3. **SERP shift** — did the query still send traffic but to a new feature (AI overview, featured snippet, shopping)? Impressions-vs-clicks pattern that indicates this.
4. **Cannibalization / content decay** — own pages competing, or freshness-sensitive queries where competitors updated and I didn't.
5. **Seasonality/demand** — is the query itself down? How to check trends before blaming the site.
6. **Manual action / policy** — the GSC panel to check, and content types at risk.

Then: the 3 highest-information checks to run first, the likely diagnosis once I report results, and a fix plan with expected recovery timeline honestly framed (including "some ranking losses don't come back until the next update").
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 14. Web · Content quality QC gate

**Use when:** Before publishing a batch of content — especially agent-assisted content — run it through a quality gate.
**Fill in:** `{{PAGES}}` — the content or list of drafts, `{{SITE_STANDARD}}` — the site's niche and quality bar

---

QC this content batch against publish standards: {{PAGES}} for {{SITE_STANDARD}}.

Run every page through the gate; output a table: page → PASS / FIX (with the specific fix) / REJECT (with the reason).

1. **Factual spot-check** — extract each page's 5 most load-bearing factual claims; for each: sourced in the text / plausible but unsourced (add source) / suspicious (verify before publish) / wrong. Never let a confident-sounding fabricated fact through — that's the failure mode this gate exists for.
2. **Search-value test** — does this page do something the top results don't (more specific, more current, first-hand, better structured)? "Same info, rephrased" = FIX or REJECT.
3. **Helpful-content self-assessment** — would a reader who lands here feel they got what they came for without pogo-sticking back? Is expertise demonstrated or claimed?
4. **Thin/duplicate detection** — pages saying the same thing as each other (cannibalization risk) or padding to hit word counts.
5. **Hygiene** — title/meta present and honest, headings match content, internal links present and relevant, images have alt text, lastReviewed date set.

End with: batch pass rate, the systemic weakness across the batch (fix the generator, not just the output), and the 3 pages closest to great with the one change each needs.

### 15. Web · Pre-launch checklist executor

**Use when:** A site is built and 'ready' — run the launch kit so it actually goes live properly indexed and measurable.
**Fill in:** `{{SITE}}` — stack and hosting, `{{STATUS}}` — what's already done vs pending

---

Execute the pre-launch kit for {{SITE}}. Current status: {{STATUS}}.

Walk the standard kit as a live checklist — for each item give the exact command/steps, the verification that proves it worked, and mark DONE / BLOCKED (with the unblocking step):

1. Production build clean — no errors, no dev artifacts, env vars set.
2. Lighthouse pass — performance/SEO/accessibility scores with the top fix for each if below ~90.
3. sitemap.xml — generated, valid, referenced in robots.txt; verification: fetch it and check entries.
4. robots.txt — allows crawling, blocks only what should be blocked (a staging-era Disallow:/ in production is the classic launch-killer — check for it explicitly).
5. Google Search Console — property verified, sitemap submitted, indexing requested for key pages.
6. IndexNow — key configured, postbuild ping wired in.
7. Canonical URLs, OG/social cards, favicon, 404 page — verify by fetching, not by assuming.
8. Analytics — installed, receiving events, filtered for own traffic.
9. Monetization readiness — AdSense/affiliate requirements met (content volume, policy pages: privacy, about, contact) before applying.
10. Legal pages — privacy policy (accurate to actual data practices), terms if needed.

End with: the single blocking item, the launch decision (ship now / ship after fixes), and — because my pattern is docs-complete-launch-pending — a named date to press publish.

## Sanskrit / Hindu thought

### 16. Sanskrit · Concept explainer with primary sources

**Use when:** I want a rigorous explanation of a concept (dharma, māyā, puruṣārtha…) grounded in actual texts, not internet summaries.
**Fill in:** `{{CONCEPT}}`, `{{DEPTH}}` — overview / serious study, `{{FOCUS}}` — school or text to center, if any

---

Explain {{CONCEPT}} at {{DEPTH}} level, centered on {{FOCUS}}.

Structure:
1. **Working definition** — one paragraph, noting where translation flattens the Sanskrit term's range.
2. **Primary passages** — 3–5 key passages where the concept is actually developed. For each: text name, chapter.verse (only if you can verify the reference — a wrong verse number is worse than none; mark UNVERIFIED if unsure), Devanagari + IAST, and a translation with the TRANSLATOR NAMED. Quote translations verbatim or not at all — never compose a quote and attribute it.
3. **How the schools differ** — where Advaita, Viśiṣṭādvaita, Dvaita, Sāṅkhya-Yoga, or Mīmāṃsā genuinely diverge on this concept vs where they use different vocabulary for compatible ideas. Attribute positions to named ācāryas/texts conservatively — "Śaṅkara argues in his bhāṣya on X" only if he actually does.
4. **Common misreadings** — the 2–3 most frequent modern distortions of this concept and what the sources actually support.
5. **Living relevance** — how the concept functions in practice/ethics today, clearly marked as interpretation, without forcing sources into modern self-help shapes.

Distinguish throughout: what the texts say / what traditions hold / what scholars debate / what you're inferring.

### 17. Sanskrit · Verse deep-study (pada-by-pada)

**Use when:** One verse deserves full treatment — grammar, commentaries, translations, memorization.
**Fill in:** `{{TEXT}}` — e.g. Bhagavad Gītā, `{{VERSE}}` — chapter.verse, `{{MY_LEVEL}}` — Sanskrit ability

---

Deep-study {{TEXT}} {{VERSE}} with me (my Sanskrit level: {{MY_LEVEL}}).

1. **The verse** — Devanagari and IAST. Reproduce it only if you're confident of the exact wording; otherwise give your best text marked UNVERIFIED and tell me which critical edition to check.
2. **Pada-by-pada gloss** — each word: form (case/number/gender or verb form), root/derivation, meaning in this context. Show sandhi splits and any samāsa analysis explicitly.
3. **Syntax** — how the sentence actually constructs; the natural prose order (anvaya).
4. **Commentaries** — what the major classical commentators say on THIS verse, named individually — but only commentators who actually wrote on this text; if unsure whether a bhāṣya covers this verse, say so rather than synthesizing one. Note where they disagree and what turns on it.
5. **Translation comparison** — 2–3 published translations (translator named, quoted verbatim or closely paraphrased with attribution), highlighting where they diverge and which choice each made on the contested words.
6. **Memorization aid** — meter identification (chandas), natural pause points, a recall hook connecting sound to meaning.

End with one question this verse should make me sit with.

### 18. Sanskrit · School comparison on a question

**Use when:** A philosophical question where I want the darśanas' actual positions compared, steelmanned, without forced harmony.
**Fill in:** `{{QUESTION}}` — e.g. the ontological status of the world, jīva–Brahman relation, `{{SCHOOLS}}` — default: Advaita, Viśiṣṭādvaita, Dvaita

---

Compare {{SCHOOLS}} on: {{QUESTION}}.

For each school:
1. **The position** — stated in its own terms, then in plain language.
2. **The textual basis** — the actual sources the school builds on (sūtra-s, bhāṣya-s, key verses cited conservatively — text and location only when verifiable, UNVERIFIED otherwise). Which śruti passages the school treats as primary and which it must interpret away.
3. **The strongest argument** — steelmanned as its ācāryas would make it, including the standard objection to rival schools and how rivals answer back. Represent each school as its adherents would recognize.

Then the synthesis section, with discipline:
- Where the disagreement is REAL (incompatible claims) vs TERMINOLOGICAL (different vocabulary, compatible claims) vs PERSPECTIVAL (different questions being answered).
- No false harmony: "all paths say the same thing" is banned unless the texts actually support it on this specific question — and where they don't, say so plainly.
- What each school would say the others get importantly wrong.
- Which historical debates (named, dated if known) shaped these positions.

Close: what remains genuinely unresolved, and one primary text per school to read next on this question.

### 19. Sanskrit · Essay/talk builder from primary passages

**Use when:** Turning a theme into an essay, thread, or talk that stays anchored to sources while speaking to a modern audience.
**Fill in:** `{{THEME}}`, `{{AUDIENCE}}` — who it's for, `{{FORM}}` — essay/thread/talk, `{{LENGTH}}`

---

Build a {{FORM}} on {{THEME}} for {{AUDIENCE}}, length {{LENGTH}}.

1. **Thesis** — one sentence the whole piece defends; sharp enough that someone could disagree.
2. **Passage selection** — 3–6 primary passages that carry the argument. Same citation discipline as always: verified references, named translators, verbatim quotes or honest paraphrase clearly marked. The piece's authority comes from the sources being real.
3. **Architecture** — opening hook from lived modern experience (not "since ancient times"); build the argument passage by passage, each doing one job; a turn where the theme complicates or deepens; an ending that lands on practice, not platitude.
4. **The modern bridge** — connect to contemporary life without distortion: no retrofitting sources into productivity advice or nationalism, no claims that ancient texts "predicted" modern science. Where a bridge is interpretive, mark it as your reading.
5. **Hostile-expert pass** — what would a trained scholar attack: weakest citation, biggest interpretive leap, missing counter-voice from within the tradition. Fix what's fixable; acknowledge what's honest to acknowledge.
6. **Draft it** — full draft in the register {{AUDIENCE}} actually reads, Sanskrit terms introduced with light glosses, not italicized walls.

Deliver: thesis, outline, draft, citation list with verification status per citation.

### 20. Sanskrit · Guided reading practice session

**Use when:** A working session to actually read Sanskrit — vocabulary, grammar, comprehension — at my level, from real texts.
**Fill in:** `{{TEXT}}` — what I'm reading, `{{MY_LEVEL}}` — honest current ability, `{{SESSION_MINUTES}}`

---

Run a {{SESSION_MINUTES}}-minute guided reading session on {{TEXT}} at my level ({{MY_LEVEL}}).

Session protocol:
1. **Select the passage** — 2–6 verses/lines sized to my level: hard enough to teach, easy enough to finish. Reproduce the text carefully (flag any wording you're unsure of rather than silently normalizing).
2. **Pre-teach** — the 5–8 vocabulary items and 1–2 grammar patterns I'll need, BEFORE reading. For grammar, show the pattern with one example from elsewhere, then let me find it in the passage.
3. **Guided reading** — I attempt each unit first; you then correct with explanation, not just the answer. Show sandhi resolution step by step where I stumble. Never let a wrong parse slide to be encouraging.
4. **Comprehension check** — 3 questions: one literal (what happened/was said), one grammatical (why is this word in this case), one interpretive (what is the line doing in context).
5. **Close the loop** — list every new form/word from today formatted for spaced review (word — form — meaning — the line it came from), and tell me what the next session should target based on where I actually struggled.

Keep the register warm but rigorous — this is abhyāsa, and consistency beats intensity.

## Health & supplement evidence

### 21. Health · Supplement evidence review

**Use when:** Before adding anything to the stack: what does human evidence actually show for this supplement and this goal?
**Fill in:** `{{SUPPLEMENT}}`, `{{GOAL}}` — the outcome I care about, `{{MY_CONTEXT}}` — age/training/diet/meds relevant to it

---

Review the evidence: {{SUPPLEMENT}} for {{GOAL}}. My context: {{MY_CONTEXT}}.

1. **Evidence base** — human RCTs and meta-analyses first; mechanistic/animal data only as supporting context, clearly labeled as such. For each key study: first author, year, journal, n, population, dose, duration, and the actual effect size (not just "significant"). NEVER invent or half-remember a study — a fabricated citation here is the worst possible failure; write UNVERIFIED and tell me what to search instead.
2. **Evidence grade** — STRONG / MODERATE / WEAK / INSUFFICIENT for this specific goal, with the biggest limitation of the evidence (small samples, unrepresentative populations, industry funding, publication bias).
3. **Effective protocol** — dose, form (which salt/ester/standardization the trials actually used), timing, duration to expected effect; where the commercial products diverge from studied forms.
4. **Safety** — side effects with frequency, interactions with common drugs and MY listed context, contraindications, quality/adulteration concerns for this supplement category (relevant for the Indian market — note testing/certification to look for).
5. **Verdict** — TAKE (protocol as above) / SKIP (reason) / INSUFFICIENT EVIDENCE (what trial would change the answer), plus the cheaper/better-evidenced alternative if one exists.

This is research support, not medical advice — decisions get confirmed with a doctor.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 22. Health · Stack interaction & redundancy audit

**Use when:** The current supplement stack needs an audit — interactions, redundancy, timing, and what to cut.
**Fill in:** `{{STACK}}` — everything with doses and timing, `{{MEDS}}` — prescription drugs if any, `{{GOALS}}` — what the stack is for

---

Audit this stack: {{STACK}}. Medications: {{MEDS}}. Goals: {{GOALS}}.

1. **Interaction matrix** — supplement↔supplement and supplement↔drug interactions: mechanism, severity (avoid / separate timing / monitor / theoretical only), and the evidence level behind each claimed interaction. Distinguish documented interactions from mechanistic speculation — both matter, but differently.
2. **Redundancy** — overlapping ingredients across products (multis quietly duplicating standalone doses), and cumulative totals vs tolerable upper limits for anything fat-soluble or accumulating (A, D, E, K, iron, zinc, copper, selenium, B6). Show the arithmetic per nutrient.
3. **Absorption & timing conflicts** — competing minerals, fat-soluble items away from fat, fiber/binders near everything else, stimulant load and its timing vs sleep.
4. **Goal alignment** — for each stack item: which goal it serves and its evidence grade for that goal. Items serving no goal or duplicating a stronger item go on the cut list.
5. **The verdict** — KEEP / CUT / REPLACE / RETIME for every item with one-line reasoning, the money saved by the cuts, and the single highest-risk thing in the current stack.

This is research support, not medical advice — decisions get confirmed with a doctor.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 23. Health · Protocol design for a goal

**Use when:** Design an evidence-ranked protocol for a specific health goal — training, sleep, energy, biomarker — with tracking and falsification built in.
**Fill in:** `{{GOAL}}` — specific and measurable, `{{CONSTRAINTS}}` — time, equipment, diet pattern, budget, `{{BASELINE}}` — current state/numbers

---

Design a protocol: {{GOAL}}. Constraints: {{CONSTRAINTS}}. Baseline: {{BASELINE}}.

1. **Intervention ranking** — every credible intervention for this goal ranked by (evidence strength × effect size × effort/cost). Behavior and training interventions compete with supplements on the same table — usually they win; show that honestly. Cite the key evidence per intervention (real studies only; UNVERIFIED where memory is shaky).
2. **The protocol** — the top 2–4 interventions composed into a weekly schedule that fits my constraints. Doses, sets/reps, timings — whatever the interventions need, specified concretely enough to execute without further decisions.
3. **Tracking plan** — the primary outcome measure and how often to measure it; 1–2 process metrics (adherence); the measurement's noise level so I don't react to random variation week to week.
4. **Checkpoints** — 30-day: what should be visible, and the adherence threshold below which the protocol wasn't actually tested; 90-day: the success criterion in numbers.
5. **Falsification** — what result at 90 days means "this protocol doesn't work for me, change it" — decided now, not after motivated reasoning sets in. Plus the most likely failure mode and its pre-planned countermeasure.

This is research support, not medical advice — decisions get confirmed with a doctor.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 24. Health · Claim tracer (debunk or confirm)

**Use when:** A health claim from a video, article, or influencer needs tracing to primary literature before it changes my behavior.
**Fill in:** `{{CLAIM}}` — stated precisely, `{{SOURCE}}` — who made it and where, `{{STAKES}}` — what I'd change if true

---

Trace this claim to ground truth: "{{CLAIM}}" — made by {{SOURCE}}. If true I would: {{STAKES}}.

1. **Sharpen the claim** — restate it as a testable proposition with population, dose/exposure, outcome, and magnitude. Vague claims get sharpened before judging; note if the sharpening is doing charitable work the claimant didn't.
2. **Find the actual evidence** — what primary studies exist on the sharpened claim: design, n, population, effect size, and how directly they test the claim vs something adjacent. Cite only studies you're confident exist (author, year, journal); otherwise describe what to search and where (PubMed terms). The claim's cited source, if any, gets read for what it ACTUALLY found vs what was claimed from it.
3. **The gap analysis** — where claim and evidence diverge: extrapolation from animals/in-vitro, healthy-user confounding, relative-vs-absolute risk inflation, single-study cherry-picking against a contrary literature, mechanism presented as outcome.
4. **Verdict** — SUPPORTED / PARTIALLY (the supported core vs the overreach) / UNSUPPORTED / UNKNOWN — with the strength of that verdict and what evidence would flip it.
5. **Decision relevance** — given {{STAKES}}: act, ignore, or cheap-test-on-myself with defined tracking.

This is research support, not medical advice — decisions get confirmed with a doctor.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 25. Health · Doctor-visit prep

**Use when:** Turn symptoms, history, and lab results into an organized brief and question list before an appointment.
**Fill in:** `{{ISSUE}}` — symptoms/results and timeline, `{{HISTORY}}` — relevant history, meds, supplements, `{{VISIT_TYPE}}` — GP/specialist/follow-up

---

Prepare me for this appointment ({{VISIT_TYPE}}): {{ISSUE}}. History: {{HISTORY}}.

This is preparation to communicate well with a doctor — explicitly NOT diagnosis.

1. **Organized timeline** — my scattered account restructured chronologically: onset, progression, triggers/relievers, what's been tried. The one-page version a rushed doctor can absorb in 60 seconds.
2. **Lab context** — for any results: the reference range and its source, which values are flagged vs borderline vs trending (trend matters more than single values — show the trend if I gave history), and which findings commonly matter vs commonly benign — framed as "worth asking about," never as interpretation.
3. **Question list, ranked** — the questions worth the limited minutes, ordered by decision-impact: differential possibilities to ask about, tests that would discriminate, red flags that should trigger urgent follow-up, treatment trade-offs.
4. **Honest disclosure list** — supplements, self-experiments, adherence gaps the doctor needs to know; note interactions worth flagging from my listed meds/stack.
5. **After-visit checklist** — what to record before leaving: diagnosis wording, test names, follow-up triggers, "call if X."

This is research support, not medical advice — decisions get confirmed with a doctor. If anything in {{ISSUE}} pattern-matches to urgent red flags, say so at the very top and keep it proportionate — flag, don't alarm.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

## Animal welfare research

### 26. Animals · Intervention effectiveness review

**Use when:** Evaluate a welfare intervention — does the evidence show it actually helps animals, and at what cost-effectiveness?
**Fill in:** `{{INTERVENTION}}` — e.g. street-dog ABC programs, cage-free campaigns, feed fortification, `{{REGION}}` — default India

---

Review the effectiveness of: {{INTERVENTION}} in {{REGION}}.

1. **Theory of change** — the causal chain from intervention to welfare improvement, with each link's strength assessed separately (interventions usually fail at their weakest link, not their headline).
2. **Evidence** — what studies and org evaluations exist: distinguish RCT/quasi-experimental evidence from monitoring data from advocacy claims. Cite real, named sources (papers, charity evaluator reports) — a fabricated evaluation would poison the whole analysis; UNVERIFIED where unsure, with where to look.
3. **Scale–neglectedness–tractability** — animals affected (orders of magnitude with stated assumptions), how crowded the space is in {{REGION}}, and what share of the problem is realistically moveable.
4. **Cost-effectiveness** — best available estimate per animal helped or per welfare-adjusted unit, with the uncertainty range honestly wide where it is, and the 2 assumptions the estimate is most sensitive to.
5. **Failure modes** — where this intervention has underperformed or backfired (displacement effects, compliance decay, welfare-washing), with examples if documented.
6. **Verdict** — STRONG BET / PROMISING BUT THIN EVIDENCE / WEAK — versus a named benchmark intervention, and what evidence would upgrade it.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 27. Animals · Landscape map — who works on what

**Use when:** Map the organizations and gaps around a specific animal-welfare problem before starting or funding anything.
**Fill in:** `{{PROBLEM}}` — the specific problem, `{{REGION}}` — default India/Bangalore

---

Map the landscape for {{PROBLEM}} in {{REGION}}.

1. **The actors** — organizations actually working on this: name, approach, scale, funding model, geography. ONLY organizations you're confident exist — an invented NGO is worse than a gap in the map; mark uncertain entries UNVERIFIED with how to confirm (site, registration, recent activity). Include government programs and laws in force, cited to the actual act/rule.
2. **The approaches** — cluster the work: direct care, sterilization/vaccination, policy/enforcement, corporate campaigns, alternatives development, public attitude change. Which approaches are crowded, which are empty, and whether empty means overlooked or means tried-and-failed (very different implications).
3. **The gaps** — underserved geographies, species (farmed animals vs companion animals attention gap), and functions (most spaces lack data/measurement more than they lack passion — flag where a data scientist specifically is scarce).
4. **The dynamics** — funding flows, key people, coordination or turf issues, recent momentum or setbacks (dated).
5. **Entry points** — for a skilled individual: the 3 highest-leverage places to plug in, each with the specific org/person to approach and the concrete first offer to make.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 28. Animals · Personal action plan (time & money)

**Use when:** Convert my available time and money into the highest-impact set of animal-welfare actions, honestly counterfactual.
**Fill in:** `{{CAUSE}}` — focus area or 'open', `{{HOURS_MONTH}}`, `{{BUDGET_MONTH}}` — ₹, `{{SKILLS}}` — default: data science, ML, web development, writing

---

Build my action plan: cause {{CAUSE}}, {{HOURS_MONTH}} hours/month, ₹{{BUDGET_MONTH}}/month, skills: {{SKILLS}}. Based in Bangalore.

1. **The option set** — concrete options across four channels: DONATE (to whom — real, verifiable orgs with a note on evaluation quality), VOLUNTEER (where my presence adds value vs displaces others), BUILD (tools/data projects only I would build — my highest-leverage channel if the project is right), ADVOCATE (where a marginal voice moves anything).
2. **Counterfactual discipline** — for each option: what happens if I don't do it? Work that would happen anyway scores low however good it feels. Money is usually more counterfactual than unskilled time; skilled time (data/ML for orgs that can't hire it) can beat both — test each option against this honestly.
3. **The portfolio** — allocate my actual hours and rupees across 2–3 options max (focus beats scatter), with expected impact reasoning per allocation, not vibes. Include one "learning bet" — an option kept small until its impact evidence improves.
4. **This month's first step** — for each chosen option: the concrete step, sized under 2 hours, with the specific contact/link/task.
5. **Review trigger** — what I should see within 90 days to continue, double down, or reallocate.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 29. Animals · Impact estimation (Fermi with sensitivity)

**Use when:** Put honest numbers on an animal-welfare idea before investing in it — scale, welfare delta, probability, counterfactual.
**Fill in:** `{{IDEA}}` — the intervention/project, `{{COMPARISON}}` — a benchmark to compare against, or 'pick one'

---

Estimate the impact of: {{IDEA}}. Benchmark: {{COMPARISON}}.

1. **The model** — expected impact = animals reached × welfare improvement per animal × probability of success × counterfactual share. Build each factor explicitly:
   - **Animals reached**: population data where it exists (cited), stated assumptions where it doesn't — show the arithmetic, order of magnitude is the goal.
   - **Welfare delta**: how much better off per animal, on a stated scale; duration of the improvement matters (a lifetime improvement ≠ a one-day one) — annualize honestly.
   - **P(success)**: base rates for this kind of project if known, else a stated prior with reasoning.
   - **Counterfactual share**: how much happens only because of this project.
2. **The range** — pessimistic / central / optimistic for the composite, not just the central estimate. If the range spans 3+ orders of magnitude, say so — that itself is the finding.
3. **Sensitivity** — the 2 assumptions that move the result most; what cheap research would tighten each.
4. **Benchmark comparison** — same model applied to {{COMPARISON}}; the honest ratio between them and what would change it.
5. **Verdict** — pursue / pursue after tightening assumption X / the benchmark is better — and the kill criterion if pursued.

Label every number: SOURCED (cite) / ESTIMATED (show basis) / GUESS (say so). ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 30. Animals · Tech-for-animals project scout

**Use when:** Find where software and data skills actually bottleneck animal-welfare work — join or build, ranked by fit and impact.
**Fill in:** `{{SKILLS}}` — default: Python, ML, data pipelines, web apps, `{{HOURS_WEEK}}` — sustainable commitment, `{{PREFERENCE}}` — join existing vs build new

---

Scout tech-for-animals opportunities for me: skills {{SKILLS}}, {{HOURS_WEEK}} hrs/week, preference: {{PREFERENCE}}.

1. **Where tech actually bottlenecks welfare work** — be concrete and skeptical: most orgs need operations and money more than apps. Find the genuine tech bottlenecks: population/welfare data that nobody collects or cleans, monitoring that's manual, matching/logistics problems (rescue-transport-adoption), evidence synthesis nobody has automated, enforcement data scattered across PDFs. For each: who has this problem and how it's known (real examples, cited or marked UNVERIFIED).
2. **Existing projects to join** — open-source or org-run projects in this space that are alive (recent activity — note what to check) and accept contributors. Joining usually beats building: the adoption problem is pre-solved.
3. **Gaps worth building** — only where step 1 shows a real user with a real problem and step 2 shows nobody serving it. For each: the user, the wedge (smallest useful version), why it survives the graveyard of abandoned do-gooder apps (distribution plan, not just code).
4. **Ranking** — all options scored on: welfare impact if it works × probability someone uses it × fit to my skills × fit to my hours. Show the table.
5. **The pick and the probe** — top option, plus a <5-hour validation step that tests the riskiest assumption BEFORE real building starts.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

## Career / resume / interview prep

### 31. Career · JD → tailored resume + gap plan

**Use when:** A specific job posting is worth applying to — tailor the resume honestly and plan the prep for the gaps.
**Fill in:** `{{JD}}` — full job description, `{{RESUME}}` — my current resume, `{{CONTEXT}}` — anything the resume doesn't show

---

Tailor my application for this role. JD: {{JD}}. Resume: {{RESUME}}. Extra context: {{CONTEXT}}.

1. **Requirement map** — every requirement/preference in the JD → STRONG MATCH (where in my experience) / PARTIAL (the nearest real thing) / GAP (no honest match). No stretch-matching: a partial labeled as strong fails in the interview, which is worse than failing at screening.
2. **Bullet rewrites** — resume bullets reworked toward this JD's language and priorities: action verb, specific technology, quantified outcome. HARD RULE: never fabricate or inflate a metric, title, or scope — where a bullet needs a number I haven't given you, insert [MY REAL NUMBER: what to measure] for me to fill. Truthful and specific beats impressive and vague.
3. **Ordering & cuts** — what moves up, what shrinks, what leaves entirely for this application; keep it to the length this seniority expects.
4. **ATS pass** — exact keyword forms from the JD present naturally (spelled-out + acronym), standard section headers, no formatting that parsers mangle.
5. **Gap plan** — for each GAP: closeable-before-interview (the 10–20 hour version: a small project, a refresher, a credible talking point from adjacent experience — honestly framed as adjacent) vs not closeable (the honest answer if asked, delivered with a growth frame).
6. **The narrative** — the 3-sentence "why me for this role" that the whole application should whisper, consistent with every bullet.

### 32. Career · ML system design mock interview

**Use when:** A realistic ML/GenAI system design interview with a demanding interviewer, rubric scoring, and a model answer afterward.
**Fill in:** `{{TOPIC}}` — e.g. recommendation system, RAG pipeline, fraud detection, or 'surprise me', `{{LEVEL}}` — senior/staff, `{{MINUTES}}` — default 45

---

Run a mock ML system design interview: {{TOPIC}}, {{LEVEL}} bar, {{MINUTES}} minutes.

**Format:** You are the interviewer. Present a realistic, slightly underspecified prompt (like real interviews). Then let ME drive — do not lecture. Interject only as a real interviewer would: answer my clarifying questions (have consistent hidden requirements ready: scale, latency, label availability, budget), push when I hand-wave ("how exactly would you get labels for that?"), redirect when I rabbit-hole, and drop one mid-interview twist (requirement change or constraint reveal).

**Cover-pressure:** if I haven't touched a critical area by its natural point, probe it: problem framing & metrics (business metric vs model metric vs proxy), data & labels (the usual make-or-break), baseline-first modeling, training/serving architecture, evaluation (offline/online, slices), deployment (latency/cost/fallbacks), monitoring (drift, feedback loops, retraining), and the failure modes specific to {{TOPIC}}.

**Afterward:**
1. Score me on a {{LEVEL}} rubric — problem framing / data strategy / modeling judgment / systems thinking / evaluation & monitoring / communication — each 1–5 with the specific moment that earned the score.
2. The 2 worst moments, replayed: what I said → what a strong candidate says.
3. A model answer outline for this exact prompt, at the depth {{LEVEL}} requires.
4. One drill for my weakest dimension before the next mock.

### 33. Career · Behavioral story bank (STAR)

**Use when:** Turn my real experiences into a tight, reusable bank of STAR stories mapped to the questions interviews actually ask.
**Fill in:** `{{EXPERIENCES}}` — raw dump: projects, conflicts, wins, failures, messy situations, `{{TARGET_ROLES}}` — what I'm interviewing for

---

Build my behavioral story bank from this raw material: {{EXPERIENCES}}. Target roles: {{TARGET_ROLES}}.

1. **Mine the material** — extract 8–12 distinct stories. Work ONLY from what I gave you: never invent details, outcomes, or numbers. Where a story is thin at a critical point (especially Results), insert [NEED: the specific detail to recall] — a placeholder beats a fabrication that collapses under follow-up questions.
2. **STAR-structure each** — Situation (2 sentences, minimum context that makes the stakes clear), Task (my responsibility specifically — watch the we/I ratio), Action (the decisions and the why, 3–5 concrete moves), Result (quantified where my material allows, plus what I learned where it doesn't).
3. **Map to the question bank** — coverage matrix against the standards: conflict with colleague/manager, failure & what changed after, leadership without authority, ambiguity, tight deadline & prioritization, influencing a decision, technical disagreement, initiative beyond scope. Every question needs a primary and backup story; one story may serve 2–3 questions with different emphasis — show which facet serves which question. Flag uncovered questions: tell me what kind of experience to dig for.
4. **Tighten for delivery** — each story in a 90-second telling (the default) and a 30-second version (for "briefly tell me about…"). Kill throat-clearing; lead with stakes.
5. **Follow-up armor** — for each story, the 2 follow-ups an interviewer will ask ("what would you do differently?", "what did X think?") and honest answer sketches.

### 34. Career · DSA pattern coach

**Use when:** Focused coding-interview practice on one pattern — taught by invariant, drilled easy→hard, reviewed like a real interview.
**Fill in:** `{{PATTERN}}` — e.g. sliding window, monotonic stack, binary search on answer, DP on intervals — or 'diagnose me from my recent misses: {{MISSES}}', `{{MINUTES}}`

---

Coach me on {{PATTERN}} for {{MINUTES}} minutes.

1. **The invariant, first** — teach the pattern as its core invariant (what stays true while the algorithm runs) and the RECOGNITION signals: what in a problem statement whispers this pattern, and the classic disguises. One worked example, narrated the way I should narrate in an interview: restate → constraints → brute force → why it's slow → the insight → complexity.
2. **Drill ladder** — 3 problems, easy → medium → hard-medium, each a genuine instance of the pattern (use well-known problems; describe them fully so we don't depend on my looking anything up). For each: I attempt first — full approach + code before you reveal ANYTHING. If I'm stuck, hints in strict order: (a) restate the invariant for this problem, (b) point at the decision I'm mis-making, (c) one line of the approach. Never jump to solution while a hint is unplayed.
3. **Review like an interviewer** — my solution checked for: correctness (walk my code against an edge case I didn't consider — make me trace it), complexity (make me state it and justify it), code quality under time pressure, and communication (did I narrate decisions or go silent?).
4. **Close the session** — my error pattern across the drills (the fixable habit, not just the missed problems), the spaced-repetition schedule for this pattern (what to re-attempt in 3 days and 2 weeks), and the next pattern to train based on what today exposed.

### 35. Career · Offer evaluation & negotiation prep

**Use when:** An offer (or competing offers) needs clear-eyed evaluation and a concrete negotiation plan with scripts.
**Fill in:** `{{OFFER}}` — full details: base, bonus, equity, joining bonus, level, location/remote, `{{ALTERNATIVES}}` — other offers/current situation/BATNA, `{{PRIORITIES}}` — what actually matters to me now

---

Evaluate and prep negotiation for: {{OFFER}}. My alternatives: {{ALTERNATIVES}}. Priorities: {{PRIORITIES}}.

1. **Total-comp decomposition** — year-1 and 4-year value: base, bonus (target vs realistic), equity (vesting schedule, and for private companies the honest discount for illiquidity and dilution — show the math at conservative/expected valuations), joining bonus with clawbacks, benefits worth actual money. One table, assumptions explicit.
2. **Market position** — where this sits for the role/level/location. Compensation data goes stale fast: label every benchmark with its source and date, mark memory-based figures UNVERIFIED, and tell me exactly what to check on live sources (levels.fyi-type data, recent postings with disclosed bands) before I anchor on anything.
3. **Non-comp evaluation** — against my stated priorities: growth trajectory of the role, manager/team signals from my interviews, stability signals (funding/layoff history — verify current), learning density, optionality it creates in 2 years.
4. **Negotiation plan** — levers ranked by typical flexibility (joining bonus and equity usually move before base; level sometimes beats all); my leverage assessment given {{ALTERNATIVES}}, honestly — and the ask: specific numbers with the reasoning I'd say out loud.
5. **Scripts** — the exact words for: the counter (anchored, warm, non-ultimatum), the response to "that's our best offer," buying time, and accepting gracefully. Plus my walk-away line, decided now.
ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

## Travel planning

### 36. Travel · Spiritual circuit planner

**Use when:** Plan a pilgrimage/temple circuit properly — route, logistics, season, and the actual significance of each site.
**Fill in:** `{{CIRCUIT}}` — region, deity, or tradition (e.g. Kashi–Prayag–Ayodhya, Pancharanga kshetras, Jyotirlingas subset), `{{DAYS}}`, `{{BUDGET}}`, `{{PARTY}}` — who's traveling

---

Plan this circuit: {{CIRCUIT}}, {{DAYS}} days, budget ₹{{BUDGET}}, party: {{PARTY}}.

1. **The route** — sites ordered by geography and transport reality (rail/road/flight legs with realistic durations — mark all schedules VERIFY-CURRENT; never present a remembered train as bookable). Nights per place justified by what's actually there, with buffer built in — pilgrimage travel runs late.
2. **Each site** — significance with its basis: scriptural references (text and location, verified-or-UNVERIFIED, same discipline as always), historical record vs living tradition vs local legend — all three are valuable but LABEL which is which; don't present sthala-purāṇa as archaeology or vice versa. What to actually do at each site beyond darshan.
3. **Darshan logistics** — timings, queue/ticket systems, dress codes, restrictions: flag EVERY one of these as verify-before-travel with the official source to check (temple trust sites change rules often). Note season-specific factors for my dates: festivals that transform crowds (dates verified against the actual panchang year, or marked approximate), closures, weather.
4. **Budget breakdown** — transport / stay / food / offerings-donations / buffer, with estimates labeled by confidence and as-of date. Where staying near the temple beats staying cheap, say so.
5. **Preparation** — bookings in lead-time order (special darshan tickets often gate everything — book first), what to carry, and one text/chapter worth reading per major site before standing in front of it.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 37. Travel · Trip plan with budget breakdown

**Use when:** A standard end-to-end trip plan — itinerary, costs, bookings — for any destination.
**Fill in:** `{{DESTINATION}}`, `{{DATES}}` — or month if flexible, `{{BUDGET}}` — total ₹, `{{PARTY}}` — travelers, `{{STYLE}}` — pace and interests

---

Plan: {{DESTINATION}}, {{DATES}}, ₹{{BUDGET}} total, {{PARTY}}, style: {{STYLE}}.

1. **Fit check first** — is this destination right for these dates (season, weather actuals for that month, crowds, closures)? If the dates fight the destination, say so before planning around it.
2. **Day-wise itinerary** — realistic pacing (transit time between sights included, one anchor per day + flexible orbit, not a checklist sprint), matched to {{STYLE}}. Mark which items need advance booking and their lead times.
3. **Budget breakdown** — flights/trains, stay per night, local transport, food, entries/activities, shopping/buffer — as a table summing against ₹{{BUDGET}}. Every estimate labeled with its confidence and as-of date; prices drift — list which line items to verify live and where. If the budget doesn't close, show the 2–3 cuts that close it with least experience lost.
4. **Booking checklist** — in lead-time order with a book-by date each: the thing that sells out first tops the list.
5. **Contingencies** — the most likely disruption for this destination/season (monsoon washout, strike, altitude issues) and the pre-decided plan B; plus a half-day slack policy.
6. **The 3 non-negotiables** — the experiences that justify this trip; protect them in the schedule, let everything else flex.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 38. Travel · Destination dossier — worth it?

**Use when:** Before committing to a destination: an honest dossier on whether it's worth it for my month and interests.
**Fill in:** `{{PLACE}}`, `{{MONTH}}`, `{{INTERESTS}}` — what I travel for, `{{COMING_FROM}}` — default Bangalore

---

Dossier: is {{PLACE}} worth it in {{MONTH}}, for someone who travels for {{INTERESTS}}, from {{COMING_FROM}}?

1. **The month question** — weather actuals for {{MONTH}} (temperature, rain, humidity — sourced, not vibes), what's open/closed/transformed (seasonal closures, festival crowds, peak-pricing), and the honest verdict: is this the right month, a workable month, or the wrong month — and which month is better if wrong.
2. **The real highlights** — what's genuinely worth the trip, separated by evidence: CONSENSUS (travelers consistently rate it), CONTESTED (loved or shrugged at — say who loves it), OVERRATED (famous but routinely disappoints — and why it stays famous). Match against {{INTERESTS}} specifically, not a generic tourist profile.
3. **The frictions** — getting there from {{COMING_FROM}} (options, duration, realistic cost range — dated), getting around locally, scams/hassles specific to this place, safety notes proportionate to actual risk.
4. **Cost picture** — daily budget range at my likely travel style, and the big-ticket items; all figures labeled with as-of dates and marked for live verification.
5. **Verdict** — GO / GO IN A DIFFERENT MONTH / SKIP FOR NOW, with the single decisive reason — plus 3 alternatives that serve the same {{INTERESTS}} better if the verdict isn't GO, one line each on why.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 39. Travel · Multi-city route optimizer

**Use when:** Several places, limited days — find the ordering and allocation that wastes the least life in transit.
**Fill in:** `{{CITIES}}` — the wishlist, `{{DAYS}}` — total including travel days, `{{FIXED}}` — locked constraints (entry/exit points, event dates), `{{MODE_PREFS}}` — train/flight/road preferences

---

Optimize this route: {{CITIES}} in {{DAYS}} days. Fixed: {{FIXED}}. Mode preferences: {{MODE_PREFS}}.

1. **The geometry** — lay out the cities spatially and identify the natural line/loop through them. Show the transit matrix for adjacent candidates: mode, realistic door-to-door duration (not just flight time — airports add 3–4 hours), and rough cost. All schedules and durations marked VERIFY-CURRENT with where to check; never present a remembered connection as fact.
2. **The allocation** — nights per city justified by what each offers (from my list's intent, not generic must-sees), with the arithmetic shown: {{DAYS}} minus transit-days = experience-days, allocated. Half-day arrivals count as half.
3. **The honest cut** — if the wishlist doesn't fit (it usually doesn't): which city to drop, and why dropping it beats shaving a day off everything (2 rushed cities usually lose to 1 proper one). Show the with/without versions side by side.
4. **Ordering logic** — why this sequence: overnight-transit tricks that save days, weekend/closure timing per city, intensity pacing (don't stack the two exhausting cities back-to-back), and arrival/departure city economics.
5. **The route card** — final sequence: city, nights, arrival/departure mode and rough timing, book-by priority. Plus the one leg most likely to fail and its fallback.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 40. Travel · Prep & packing executor

**Use when:** The trip is booked — now execute the countdown: documents, health, bookings, packing, home prep.
**Fill in:** `{{TRIP}}` — destination(s), dates, activities planned, `{{PARTY}}` — who's going, `{{BOOKED}}` — what's already done

---

Run trip prep for: {{TRIP}}, party: {{PARTY}}. Already booked: {{BOOKED}}.

1. **T-minus checklist** — everything remaining, ordered by deadline, grouped T-30/T-14/T-7/T-2/departure-day:
   - **Documents**: visa/permit requirements for this destination and nationality — cite the official source (embassy/government site) and mark VERIFY-CURRENT; rules change and a stale answer here ruins trips. Passport validity window, photocopies/cloud backups, permits for restricted areas if any.
   - **Health**: recommended vaccinations/prophylaxis per official travel-health guidance (named source, verify-current), prescriptions + generics list, travel insurance that actually covers the planned activities.
   - **Money & connectivity**: cards that work there, cash strategy, SIM/eSIM options, offline maps downloaded.
   - **Bookings gap-check**: from {{BOOKED}}, what's missing — with book-by dates.
2. **Packing list** — generated from destination climate for the actual dates + planned activities, not a generic list: clothing by expected temperature range (sourced), activity gear, meds, electronics/adapters (plug type for this country), documents pouch. Flag airline baggage limits to verify.
3. **Home prep** — the leaving-house list: payments due during the trip, plants/pets/deliveries, security basics.
4. **Day-zero card** — departure-day timeline from wake-up to seat, with the checked-thrice items (passport, cards, tickets, meds).

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

## Learning deeply

### 41. Learning · Skill roadmap with capstone

**Use when:** Commit to learning a skill properly — one primary resource, a proving capstone, a weekly rhythm, and honest checkpoints.
**Fill in:** `{{SKILL}}`, `{{WHY}}` — the real reason (job, project, curiosity), `{{HOURS_WEEK}}` — sustainable, not aspirational, `{{CURRENT}}` — honest starting point

---

Build my learning roadmap: {{SKILL}}. Why: {{WHY}}. Budget: {{HOURS_WEEK}} hrs/week from {{CURRENT}}.

1. **Define 'learned'** — what I can DO when done, stated as capabilities ("build/derive/diagnose X unaided"), not topics covered. Sized honestly for {{HOURS_WEEK}} hrs/week — tell me the realistic timeline, not the motivating one.
2. **One primary resource** — pick ONE spine (course/book/docs) and justify the choice against 2 named alternatives (and why they lost: outdated, wrong level, poor exercises). Resource-hopping is the #1 self-learner failure; everything else is supplementary and consulted only on demand. Verify the resource is current for {{SKILL}} — flag if the field moves fast enough that edition/version matters.
3. **The capstone** — a project that PROVES the skill and connects to {{WHY}}: specific, demoable, slightly beyond comfortable. Define its done-criteria now. Learning without a capstone is entertainment.
4. **Weekly rhythm** — the {{HOURS_WEEK}} hours allocated: consume (smallest share), practice/build (largest share), retrieve/review (the share everyone skips — spaced recall of prior weeks). Concrete session plan for week 1.
5. **30-day checkpoint** — the observable that says on-track (a specific thing built/solved, not "feeling progress"), the adherence threshold below which the plan wasn't tested, and the pre-decided adjustment for each failure mode: too hard → what to change; boring → check if {{WHY}} was real; no time → what {{HOURS_WEEK}} should actually be.
6. **Failure-mode inoculation** — the top 3 ways self-learners fail at {{SKILL}} specifically, and this plan's defense against each.

### 42. Learning · Deep-read protocol (paper/book/chapter)

**Use when:** Read something dense so it actually sticks — structured notes, claim verification, connections to what I know and build.
**Fill in:** `{{MATERIAL}}` — the paper/chapter/book (paste, link, or name), `{{PURPOSE}}` — why I'm reading it, `{{PRIOR}}` — what I already know about this area

---

Guide a deep read of: {{MATERIAL}}. Purpose: {{PURPOSE}}. My prior knowledge: {{PRIOR}}.

1. **Pre-read frame** — before content: what QUESTION is this work answering, what would I predict the answer is given {{PRIOR}}, and 3 things to watch for given {{PURPOSE}}. (Prediction-first makes disagreement memorable.)
2. **Structured pass** — work through section by section, keeping three ledgers strictly separate:
   - **CLAIMS**: what the work asserts, with the strength each claim is made at (proven / argued / assumed / speculated — authors mix these and hope you don't notice).
   - **EVIDENCE**: what actually supports each major claim, and its quality (experiment, data, citation-to-someone-else, intuition pump).
   - **MY QUESTIONS**: confusions to resolve, objections, "wait, does that follow?"
3. **Verification shortlist** — the 3 claims most worth independently checking: the load-bearing ones, the surprising ones, and any that smell like the author's motivated conclusion. For each: how to check (a source, a derivation to redo, a quick experiment).
4. **Connection pass** — link to what I know and build: what this changes in my current projects/beliefs, what it contradicts from my prior reading (name the tension precisely), and one place I could apply it within a month.
5. **The synthesis test** — I write the one-paragraph summary from memory; you grade it against the ledgers: what I got wrong, what load-bearing thing I omitted. Then the 5 retrieval questions to re-answer in a week.

### 43. Learning · Feynman examiner

**Use when:** I claim to understand something — probe until my hand-waving is exposed, then map the gaps to study actions.
**Fill in:** `{{TOPIC}}` — what I claim to understand, `{{CLAIMED_LEVEL}}` — how well I think I know it, `{{STAKES}}` — interview / teaching / building with it

---

Examine my understanding of {{TOPIC}} (I claim: {{CLAIMED_LEVEL}}; it matters because: {{STAKES}}).

Protocol:
1. **I explain first** — prompt me to explain {{TOPIC}} as if to a smart newcomer. Do not interrupt the first pass.
2. **Probe in escalating order** — then dig, one question at a time, waiting for my answer before the next:
   - **Mechanism**: "walk me through WHY that happens, step by step" — wherever I used a term as a black box, open it.
   - **Edges**: "when does this break / not apply / give the wrong answer?" — understanding lives at the boundaries.
   - **Quantities**: "roughly how big/fast/many?" — hand-wavers can't estimate.
   - **Counterfactual**: "what would be different if X weren't true?"
   - **Transfer**: a novel scenario I haven't seen — make me apply, not recall.
3. **Call the hand-waves mercilessly** — every time I retreat to jargon, analogy-without-mechanism, or "it just does," name it in the moment: "that was a hand-wave — you used the word but couldn't open it." No credit for confident delivery. If my answer is wrong but plausible-sounding, that's the most important catch of all.
4. **The gap map** — afterward: SOLID (survived probing) / SHAKY (right but couldn't defend) / HOLLOW (couldn't open the box) / WRONG (confidently incorrect — flag these loudest, given {{STAKES}}). For each non-solid item: the specific study action (what to read/derive/build) and the re-test question you'll ask me next time.

### 44. Learning · Flashcard deck from notes

**Use when:** Convert my notes into a clean spaced-repetition deck — atomic, verified, Anki-ready.
**Fill in:** `{{NOTES}}` — the notes/highlights to convert, `{{SUBJECT}}` — what this is for (exam, interview, retention), `{{DECK_SIZE}}` — max cards, or 'as many as the material honestly supports'

---

Convert these notes into a flashcard deck for {{SUBJECT}} (max {{DECK_SIZE}} cards): {{NOTES}}.

Card construction rules:
1. **Atomic** — one fact/distinction/step per card. A note claiming three things becomes three cards, not one card with a list answer (lists get "recognized," not recalled).
2. **Retrieval-shaped** — front asks something my future self must produce, not recognize: "What is X?" is weak; "Why does X happen?" / "X vs Y — the key difference?" / "When would X fail?" are strong. Use cloze deletion where the note is a crisp statement with one keystone term.
3. **Verified-or-flagged** — encode ONLY what the notes actually say or what you can verify. If something in my notes looks wrong or outdated, DO NOT encode it — list it in a "check before trusting" section with why it smells off. A spaced-repetition system is a machine for making memories permanent; feeding it errors is self-sabotage.
4. **Context-carrying** — each card understandable standing alone in 6 months: no "this method" / "the above case" references back to notes I won't have open.
5. **Tagged** — by subtopic for selective review.

Deliver:
- The deck as CSV (front,back,tags) ready for Anki import.
- The "check before trusting" list (suspect items from my notes).
- The 5 cards most likely to leech (ambiguous/interference-prone) with suggested rewrites.
- What the notes COVER thinly: concepts referenced but never explained — candidate gaps in the source material itself.

### 45. Learning · Learn-by-building syllabus

**Use when:** Learn a skill by building a real project — a milestone ladder where each rung forces the next concept.
**Fill in:** `{{SKILL}}` — what to learn, `{{PROJECT}}` — what to build (or 'propose one that fits'), `{{WEEKS}}`, `{{HOURS_WEEK}}`

---

Design a learn-by-building syllabus: learn {{SKILL}} by building {{PROJECT}} in {{WEEKS}} weeks at {{HOURS_WEEK}} hrs/week.

1. **Project fit check** — does {{PROJECT}} actually exercise {{SKILL}}'s core, or just its easy 20%? If the project lets me dodge the hard parts (the parts I'd hire someone else for), reshape it or propose a better one — and say which {{SKILL}} concepts this project CANNOT teach, so I don't mistake finishing for mastery.
2. **The milestone ladder** — {{WEEKS}} milestones (or fewer, multi-week), each: (a) ships something demonstrable, (b) is IMPOSSIBLE without the next concept — the project pulls the learning, not the reverse, (c) has a done-criterion I can't argue with. Show the ladder as: milestone → what it forces me to learn → done when.
3. **Just-in-time theory** — per milestone: the minimum reading/reference for THAT milestone's concept (specific chapters/docs, not "read the book"), consumed when blocked, not in advance. Front-loading theory is the failure mode this format exists to prevent.
4. **The anti-shortcut clause** — for each milestone: the specific way to fake it (copy-paste, framework magic, an LLM writing it) and the self-check that catches the fake ("close the reference and re-implement X," "explain why line Y is needed," "predict what breaks if Z is removed"). Using AI to explain is learning; using it to skip is the shortcut — mark which is which per milestone.
5. **Weekly rhythm & recovery** — session structure for {{HOURS_WEEK}} hrs, what to do when a milestone overruns (shrink scope, never skip the concept), and the {{WEEKS}}/2 checkpoint: on-pace test and the honest descope plan if behind.

## App & site monetization

### 46. Monetize · Asset monetization audit

**Use when:** An existing site/app/tool — find the realistic monetization paths and pick one with a 90-day plan.
**Fill in:** `{{ASSET}}` — what it is and does, `{{STATS}}` — traffic/users/engagement, honest numbers, `{{EFFORT_BUDGET}}` — hrs/week I'll actually invest

---

Audit monetization for: {{ASSET}}. Current numbers: {{STATS}}. My effort budget: {{EFFORT_BUDGET}} hrs/week.

1. **The option table** — every applicable model: display ads, affiliate, sponsorship, digital product (course/ebook/template), SaaS/pro tier, API access, services/consulting spun from it, donations. For each: fit to THIS asset's audience and intent (ads need volume; affiliate needs purchase intent; products need trust — score honestly against {{STATS}}), effort to implement, and realistic revenue range AT MY CURRENT NUMBERS — benchmarks labeled with source and date, marked as rough (RPMs and conversion rates vary wildly; never present a benchmark as a promise). If current numbers are below viability for a model, state the threshold it needs.
2. **The math check** — for the top 3 options: revenue = my actual traffic/users × realistic rate — shown as pessimistic/central/optimistic. If every option yields pocket change at current scale, say so plainly: the answer might be "grow first, monetize later" and that's a valid audit outcome.
3. **The pick** — one primary option (maybe one passive secondary), chosen by expected value per hour of my {{EFFORT_BUDGET}} — not by ceiling.
4. **90-day plan** — for the pick: week-by-week to first rupee, instrumented so I can see what's working (what to measure weekly), with the decision gate at day 45: the number that says continue vs switch to option #2.
5. **The risk** — what monetizing this way could damage (user trust, SEO, policy standing) and the guardrail.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 47. Monetize · Launch executor — kill the launch gap

**Use when:** The thing is built, docs are done, listing drafted — and it's still not live. Force the launch across the line.
**Fill in:** `{{PROJECT}}` — what's launch-ready, `{{PENDING}}` — what I believe is left, `{{FEAR}}` — honest answer: what's actually stopping me, if I know

---

Get this launched: {{PROJECT}}. Supposedly remaining: {{PENDING}}. The honest blocker: {{FEAR}}.

Context you should know: my pattern, verified across my own repos, is launch docs complete, launches pending. The building is done and the publishing is dodged. Your job is to be the countermeasure, not another planning session.

1. **Audit the 'remaining' list** — sort {{PENDING}} into: GENUINELY BLOCKING (app store will reject without it / site breaks without it), COSMETIC (perfection-seeking wearing a checklist costume — name each one bluntly), and POST-LAUNCH (real, but doable after going live — most things are). Be aggressive: the burden of proof is on an item to justify blocking.
2. **The true critical path** — only the GENUINELY BLOCKING items, ordered, with time estimates. If this sums to more than a weekend, challenge your own list again — it's usually hiding cosmetics.
3. **Define 'launched'** — the measurable event: listing live / site indexed / first stranger can use it without me. Not "ready to launch." Launched.
4. **The scheduled push** — critical path mapped onto the next 7 days with a named launch date and time. Include the point-of-no-return step early (submit the listing, flip the DNS, post the link) — commitment devices beat motivation.
5. **Pre-mortem the fear** — take {{FEAR}} seriously for one paragraph: what's the realistic worst case of launching as-is (usually: silence, a bug report, a bad review — all survivable and all fixable post-launch), versus the certain cost of another month unlaunched. Then the day-1-after-launch checklist: where feedback arrives, what to monitor, the first fix window.

End with the one sentence I should read when I hesitate at the publish button.

### 48. Monetize · AdSense / SEO revenue tune-up

**Use when:** A live content site earns something — find the levers that raise revenue without wrecking UX or rankings.
**Fill in:** `{{SITE}}` — the site and niche, `{{DATA}}` — GSC + analytics + AdSense numbers: traffic, top pages, RPM, CTR, geo mix, `{{CONSTRAINT}}` — what I won't do (e.g. intrusive formats)

---

Tune up revenue for {{SITE}}. Data: {{DATA}}. Off-limits: {{CONSTRAINT}}.

1. **Decompose the revenue** — revenue = pageviews × RPM; RPM = fill × CTR × CPC, shaped by geo mix, page type, ad placement, and seasonality. Locate MY bottleneck in that chain from {{DATA}} — a traffic problem and an RPM problem have opposite fix lists; diagnose before prescribing.
2. **RPM levers** (if RPM is the gap) — placement/density review against both UX and policy (what's under-monetized vs what risks a violation — cite the actual policy area, current rules to be verified), format mix, page-type analysis (which content types earn vs merely rank — informational often ranks big and earns small), geo reality (my traffic's country mix caps CPC; which content would shift the mix, honestly assessed).
3. **Content ROI pass** (if traffic is the gap) — from {{DATA}}: pages to EXPAND (ranking 5–15 with earning potential — the compound-interest fix), UPDATE (decaying winners), PRUNE/MERGE (thin pages diluting the site), and the gap topics adjacent to what already works. Ranked by expected revenue impact per hour of work.
4. **The uplift estimate** — for the top 3 moves: realistic uplift RANGE with the reasoning shown, labeled as estimates — never promise percentages. Sequenced into a 60-day plan with weekly measurables.
5. **The do-not list** — the tempting moves that backfire for this site specifically (ad density that tanks CWV and rankings, policy-gray formats, MFA drift that erodes trust). Revenue that costs the site's standing isn't revenue.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 49. Monetize · Pricing & packaging design

**Use when:** A product/tool needs its free-paid boundary, tiers, and price points designed — grounded in real comparables.
**Fill in:** `{{PRODUCT}}` — what it does and for whom, `{{VALUE_STORY}}` — the outcome users pay for, `{{MARKET}}` — India-first / global / both, `{{COMPARABLES}}` — competitors I know of, if any

---

Design pricing for: {{PRODUCT}}. Value: {{VALUE_STORY}}. Market: {{MARKET}}. Known comparables: {{COMPARABLES}}.

1. **Value metric first** — what unit should price scale with (seats, usage, projects, features)? The right metric grows with the user's value received and is hard to game; test 2–3 candidates against those criteria before any numbers.
2. **The free-paid boundary** — free tier's job is distribution (habit-forming, shareable) while the paid trigger is a moment of obvious value (hitting a real limit at a moment of need — name that moment for {{PRODUCT}} specifically). What must NEVER be free (the core value the whole model monetizes), and the boundary's abuse-resistance.
3. **Tier architecture** — 2–3 tiers max, each mapped to a distinct user situation (not a feature grab-bag): who it's for → what they get → what pushes them up. A clear middle-tier default. Naming that says who-it's-for.
4. **Price points** — anchored in comparables: real products with their ACTUAL current pricing — every price labeled with as-of date and marked VERIFY-CURRENT (pricing pages change constantly; a stale comparable misprices the whole design; if unsure a comparable's price, say UNVERIFIED, never guess a number). For {{MARKET}}: PPP reality — India-market pricing vs global pricing, and whether regional pricing (or an India-specific tier) beats one global price for this product.
5. **The test plan** — pricing is a hypothesis: what to test first (the boundary? the middle price?), the cheapest honest test (landing-page split, manual concierge tier), the metric that decides, and the 90-day revisit trigger.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.

### 50. Monetize · Distribution channel plan

**Use when:** The product exists; users don't know it does. Find where they actually are and plan 30 focused days of distribution.
**Fill in:** `{{PRODUCT}}`, `{{ICP}}` — the specific person it's for, `{{HOURS_WEEK}}` — sustainable distribution time, `{{DONE_SO_FAR}}` — channels already tried and what happened

---

Plan distribution for: {{PRODUCT}}. Ideal user: {{ICP}}. Budget: {{HOURS_WEEK}} hrs/week. Already tried: {{DONE_SO_FAR}}.

1. **Where {{ICP}} actually congregates** — channel inventory: communities (subreddits, Discords, forums — REAL, named ones whose existence you're confident of; UNVERIFIED otherwise, with how to check activity levels), search (what they'd query at the moment of need — the SEO wedge), directories/marketplaces for this product type, social platforms where this ICP consumes (not where founders post), and offline/dark channels if relevant (WhatsApp groups, meetups). For each: how to verify it's alive and receptive BEFORE investing (posting rules, self-promo tolerance — channels burn cold-promoters).
2. **Channel economics** — score each: effort per week, expected reach honestly (small-N reality: most channels yield trickles, and that's fine early), time-to-signal (SEO pays in months; community pays in days), and compounding (does effort accumulate or evaporate?). Show the table.
3. **Fit to my patterns** — I build well and publish reluctantly; favor channels where the unit of work is shippable content or product presence over channels demanding daily social performance. Note which channels my existing assets (published sites, GitHub, dashboards) can feed.
4. **The 30-day focus** — TWO channels max (from the table, with the why). Week-by-week actions sized to {{HOURS_WEEK}}, each week ending in something published/posted/submitted — with the numbers to record weekly.
5. **Kill/scale criteria** — per channel, decided now: the day-30 signal that means double down vs the signal that means switch to channel #3. Distribution dies from unfocused dabbling; this plan exists to prevent it.

ACCURACY CONTRACT: Cite a checkable source (name + date) for every factual claim. Never invent quotes, numbers, studies, filings, URLs, prices, or organizations — write UNVERIFIED instead and tell me how to verify. State the as-of date for anything time-sensitive and list what needs re-checking on the live web. Keep FACT, INTERPRETATION, and SPECULATION visibly separate. End with your overall confidence and the 3 claims most worth double-checking.
