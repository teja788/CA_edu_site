# Build Plan: A Free, Organized, Evidence-Based CA Prep Platform

**Purpose of this document:** A complete specification and strategy document for building a free website that helps Indian CA students prepare for ICAI exams (Foundation, Intermediate, Final) without depending on expensive coaching. Written to be handed to Claude Code as the project brief.

**Working thesis:** ICAI already gives away nearly everything a student needs — study material, revision papers, mock tests, past papers with suggested answers, and even free live classes. What students lack is *organization, navigation, a practice engine, and a study method*. This site's moat is structure + pedagogy + accuracy, not content volume. Do not compete on hoarding PDFs; compete on making the free official ecosystem actually usable.

**Locked decisions (July 2026):**
- **Launch level: CA Intermediate.** Largest cohort (~1.6–1.7 lakh candidates/attempt), lowest pass rates (Group 1 ~9–15%), highest coaching dependence. Consequence: the amendment/attempt-tagging machinery (§6.2, §6.4) is a day-one requirement, not a later phase.
- **Phase 1 priority: question bank + practice engine** (Inter papers are 30% case-scenario MCQs, so the engine mirrors the exam itself). Study plans + attempt dashboard ship as thin static slices within Phase 0. Original notes follow in Phase 2.

---

## 1. The Problem (why this site should exist)

- Coaching for the full CA journey costs roughly ₹2–4 lakh, while ICAI's own fees (registration + exams) total only about ₹70,000. Coaching is the single largest avoidable cost for a middle-class family.
- Pass rates remain very low despite this spend. Recent cycles: Foundation ~15%, Intermediate Group I as low as ~9–15%, Final both-groups ~16–19%. Passive lecture consumption is not producing results for the majority.
- ICAI's free ecosystem (BoS Knowledge Portal, free Live Virtual Classes, ICAI CA Tube on YouTube, BoS mobile app) is comprehensive but poorly organized, hard to discover, and offers no interactive practice, progress tracking, or study methodology.
- Existing "free resources" websites are largely SEO blogs whose business model is upselling paid test series and lectures. Telegram piracy channels exist but are illegal, unreliable, and often outdated — dangerous in a course where law/tax content changes every attempt.
- The learning-science literature is unambiguous: practice testing (retrieval practice) and distributed/spaced practice are the two highest-utility study techniques (Dunlosky et al. 2013; replicated by Hattie & Donoghue 2021 across 242 studies). Almost nothing in the CA prep ecosystem is built around them.

**Mission statement (suggested):** "Every resource you need to become a CA is already free. We organize it, keep it current, and give you the practice system coaching never did."

---

## 2. Ground Truth: The Exam (verify against icai.org before publishing anything)

Everything below reflects the New Scheme of Education and Training (effective July 2023, first exams mid-2024). **All facts on the live site must link to the ICAI source they came from and carry a "last verified" date.** ICAI announced further pattern refinements for Sept/Nov 2026 attempts — re-verify every table below against current ICAI notifications during content production.

### 2.1 Structure overview

| Level | Papers | Grouping | Frequency |
|---|---|---|---|
| Foundation | 4 papers × 100 marks | No groups | 3×/year (Jan, May/June, Sept) |
| Intermediate | 6 papers × 100 marks | 2 groups × 3 papers | 3×/year |
| Final | 6 papers × 100 marks | 2 groups × 3 papers | 3×/year (from 2025) |

- **Passing:** 40% per paper AND 50% aggregate per group.
- **Exemption rule (updated policy):** papers scoring 60+ are treated as permanently exempt under ICAI's revised norms; remaining papers then require 50% each. Students may also surrender exemptions. (Verify current wording — this changed in 2025 and trips students up constantly. A plain-language explainer of exemption rules is a high-value page.)
- **Foundation:** Papers 1–2 (Accounting; Business Laws) are descriptive. Papers 3–4 (Quantitative Aptitude; Business Economics) are objective **with 0.25 negative marking**.
- **Inter & Final:** each paper is 30% case-scenario MCQs + 70% descriptive, **no negative marking**.
- **Articleship:** 2 years under the new scheme (down from 3). Total course duration ≈ 3.5–4.5 years post-12th.
- **Final Paper 6 (Integrated Business Solutions):** multidisciplinary case study, **open-book**, draws on all subjects.

### 2.2 Papers by level (site's canonical taxonomy)

**Foundation:** 1. Accounting · 2. Business Laws · 3. Quantitative Aptitude (Maths, LR, Stats) · 4. Business Economics

**Intermediate — Group 1:** 1. Advanced Accounting · 2. Corporate & Other Laws · 3. Taxation (Income Tax + GST)
**Intermediate — Group 2:** 4. Cost & Management Accounting · 5. Auditing & Ethics · 6. Financial Management & Strategic Management

**Final — Group 1:** 1. Financial Reporting · 2. Advanced Financial Management · 3. Advanced Auditing, Assurance & Professional Ethics
**Final — Group 2:** 4. Direct Tax Laws & International Taxation · 5. Indirect Tax Laws · 6. Integrated Business Solutions (open-book case study)

### 2.3 Self-Paced Online Modules (SPOM) — must-cover topic, badly explained everywhere

Mandatory online modules qualified before CA Final; done via ICAI's LMS (lms.icai.org):
- **SET A:** Corporate & Economic Laws (mandatory, expert knowledge expected)
- **SET B:** Strategic Cost & Performance Management (mandatory, expert knowledge)
- **SET C:** one elective from ~10 subjects (working knowledge)
- **SET D:** one multidisciplinary elective from ~4 subjects (working knowledge)
- 50% to pass each set, unlimited attempts, no negative marking, no extra fee; prescribed learning hours must be completed first; webcam/face-detection requirements apply. Marks don't aggregate with Final marks.
- The site should have a definitive SPOM guide: what it is, exemptions, how to book the test, hardware requirements, common failure points.

### 2.4 The attempt calendar problem (a core product feature, not just content)

Exams run 3×/year with registration cut-offs ~4 months prior, RTPs released per attempt, and law/tax amendments applicable per attempt. Students constantly confuse *which* material/amendments apply to *their* attempt. Every content item on the site must be tagged with applicable attempts (e.g., "applicable: May 2026, Sept 2026"), and the site needs an always-current "Your attempt" dashboard: dates, forms, fees, applicable RTP/MTP links, applicable Finance Act, cut-off dates.

---

## 3. Licensing & Content Strategy (the non-negotiable constraints)

### 3.1 What you must NOT do
- **Never re-host, mirror, or bundle ICAI PDFs** (study material, RTPs, MTPs, suggested answers, sample papers). ICAI asserts copyright over all of it; commentary sites explicitly note ICAI materials cannot be reused without written consent. Re-hosting is what the piracy Telegram channels do — it's both illegal and strategically weak (stale copies spread misinformation).
- Never reproduce ICAI question text or suggested-answer text verbatim in your question bank.
- Never use ICAI's name/logo in the domain or branding in a way that implies affiliation. Prominent disclaimer on every page: independent, not affiliated with or endorsed by ICAI.
- Never scrape-and-republish paid publishers' books or coaching notes.

### 3.2 What you CAN build freely
1. **A deep-link directory** to official sources. Linking is not copying. The single most valuable v1 artifact is a perfectly organized, always-current index of every official free resource, per paper, per attempt.
2. **Original explanatory content** written from scratch: chapter notes, concept explainers, worked examples with different numbers, summaries, mnemonics, flowcharts, comparison tables. Base them on the syllabus and primary law, in your own words.
3. **Original practice questions**: write new MCQs and descriptive questions testing the same concepts. Concepts and facts aren't copyrightable; specific expression is.
4. **Statutory text**: Acts of Parliament and government notifications occupy a special place — Section 52(1)(q) of the Indian Copyright Act permits reproduction of Acts (with any authorized commentary excluded). Primary sources: India Code (indiacode.nic.in), incometaxindia.gov.in, cbic.gov.in / GST Council, mca.gov.in (Companies Act, notified Ind AS), sebi.gov.in, rbi.org.in. Still add a one-time legal review of your reproduction approach before launch; keep official-gazette sourcing documented.
5. **Metadata and analysis**: past-paper topic weightage analysis, trend analysis, amendment trackers, study plans, exam-writing guides — all original work.

### 3.3 License your own content openly
Publish your original notes and question bank under **CC BY-SA 4.0** and the code under **MIT/AGPL** on GitHub. This (a) signals trustworthiness, (b) invites contributors, (c) ensures the project outlives you — key for the mission of helping as many students as possible.

### 3.4 Optional: write to ICAI
ICAI has a public-interest mandate (set up by an Act of Parliament) and already gives materials away. A polite request for permission to embed/re-host specific items, or an offer to collaborate, costs nothing. Don't block on it; design assuming link-only.

---

## 4. The Source-of-Truth Directory (what the site links to)

### 4.1 ICAI official (free)
| Resource | What it is | Where |
|---|---|---|
| BoS Knowledge Portal | Study material (all papers, PDF), syllabus, sample MCQs | icai.org → Students → BoS Knowledge Portal |
| RTPs (Revision Test Papers) | Per-attempt revision Q&A + statutory amendments not in the SM | boslive.icai.org (RTP section) |
| MTPs (Mock Test Papers) | Exam-pattern mocks with answers, per attempt (2 series typical) | BoS portal |
| Past question papers + Suggested Answers | Actual exam papers with ICAI's model answers | BoS portal / ICAI exam site |
| Free Live Virtual Classes (LVC/LVRC) | Full-syllabus + revisionary live classes, Zoom + recorded, notes/assignments/MCQs | boslive.icai.org; ICAI BoS app; **ICAI CA Tube** (YouTube) |
| ICAI BoS Mobile App | All of the above on Android/iOS | Play Store / App Store |
| SPOM / Digital Learning Campus | Mandatory Final-level modules | lms.icai.org; spmt.icai.org (test booking) |
| Exam portal | Forms, dates, admit cards, results | icai.nic.in / eservices.icai.org (SSP) |
| CDS portal | Physical books ordering (printing cost only) | cds.icai.org |
| Students' Journal, announcements | Amendments, applicability notifications | icai.org |

**Important nuance to surface to users:** some BoS-portal content (live class recordings, notes) sits behind a free student login (registration no. + DOB), and the portal is course-scoped (Foundation students see Foundation content). The site should say which links need login and which are public (ICAI CA Tube is public).

### 4.2 Government primary sources (free, reproducible with care)
- **India Code** — every central Act, consolidated and current.
- **incometaxindia.gov.in** — Income-tax Act, Rules, circulars, notifications, Finance Acts.
- **cbic.gov.in / gstcouncil.gov.in** — CGST/IGST Acts, rules, rate notifications, circulars.
- **mca.gov.in** — Companies Act 2013, rules, notified Ind AS.
- **sebi.gov.in, rbi.org.in** — regulations relevant to law/AFM/audit papers.
- **egazette.gov.in** — the authoritative version of any notification.

### 4.3 Quality third-party free material (curate, attribute, never copy)
- ICAI CA Tube + regional ICAI branch channels (official lectures).
- Reputable educator channels offering genuinely free full lectures (e.g., large freemium platforms and individual CA educators). Curate by paper with timestamps/playlists; review quality and syllabus-version before listing. Rule: only list content the owner published freely themselves — never "leaked" lectures.
- NPTEL/SWAYAM for foundational accounting/economics/statistics background.
- Khan Academy for Foundation-level maths/statistics/economics fundamentals.

---

## 5. Pedagogy: How the Site Teaches (the actual differentiator)

Design principle: **the site is a practice-first learning system, not a content library.** Every feature maps to an evidence-based technique.

| Evidence-based principle | Evidence (cite on an "Our method" page) | Site feature |
|---|---|---|
| Retrieval practice / practice testing | One of two "high-utility" techniques (Dunlosky et al. 2013; Hattie & Donoghue 2021 meta-analysis, 242 studies) | MCQ engine after every topic; daily quiz; past-paper drills; "test-first" chapter openers |
| Spaced repetition | The other high-utility technique; spacing beats massed study for retention | FSRS-scheduled flashcard decks (sections, AS/Ind AS numbers, formulas, case law, audit SAs); review queue on the dashboard |
| Interleaving | Mixing problem types improves discrimination and transfer | Mixed-topic quiz mode; cumulative weekly tests that blend chapters |
| Mastery learning | Khan Academy model: don't advance until prerequisite mastery; addresses Bloom's classic finding that mastery + feedback approaches tutoring-level gains | Per-topic mastery states (Not started → Familiar → Proficient → Mastered) gated by quiz performance, not videos watched |
| Worked examples → faded practice | Cognitive load theory: novices learn faster from worked examples, then gradually removed scaffolding | Numerical chapters: fully worked example → partially worked → independent problem, in that order |
| Immediate elaborated feedback | Feedback with explanation beats right/wrong marking | Every MCQ option has an explanation of *why* it's wrong; link back to the exact note section |
| Deliberate exam-writing practice | CA descriptive papers reward presentation: working notes, section citations, prescribed formats | "Answer like a topper" guides per paper; model-answer anatomy breakdowns; self-grading rubrics derived from suggested answers (described, not copied); timed writing drills |
| Error logging / metacognition | Reviewing errors is where marks are recovered | Built-in mistake notebook: wrong quiz answers auto-collected, tagged by topic, resurfaced via spaced review |
| Planning & goal-setting | Structure is what coaching actually sells | Attempt-based study-plan generator: input attempt + hours/day + working-or-not → week-by-week plan with revision cycles (learn → revise-1 in 48h → revise-2 in 1 week → pre-exam) |

**What the site deliberately does NOT do:** long passive video content (link to ICAI's instead), motivational fluff, "importance of chapter" filler, and anything that increases time-on-site without increasing marks. Respect the student's time ruthlessly.

**Lessons from successful platforms to encode:**
- *Khan Academy:* mastery map + free forever + progress visibility.
- *UWorld (medical):* the question bank with world-class explanations IS the product; explanations teach more than notes.
- *Anki/FSRS community:* scheduling beats willpower; make review queues the daily habit loop.
- *freeCodeCamp:* open-source + community contribution + certification-shaped curriculum keeps a free project alive for a decade.
- *Physics Wallah's rise:* Indian students flock to genuinely free, high-quality, Hinglish-friendly material — demand is proven; language accessibility matters (plan Hindi/Hinglish explanations in Phase 3).

---

## 6. Product Specification

### 6.1 Information architecture
```
Home
├── Start Here (how to use the site; self-study roadmap; "is self-study viable?" honest guide)
├── Foundation / Intermediate / Final
│   ├── Level guide (structure, passing rules, exemptions, registration walkthrough)
│   └── Paper (e.g., Inter P3 Taxation)
│       ├── Syllabus map + past-attempt weightage analysis
│       ├── Official resources for THIS paper & THIS attempt (deep links: SM, RTP, MTP, past papers, LVC playlist)
│       ├── Chapters → Topics
│       │   ├── Original notes (concept → worked examples → common mistakes → exam pointers)
│       │   ├── Practice (MCQs, descriptive Qs with model-answer skeletons)
│       │   └── Flashcard deck
│       └── Revision (chapter summaries, formula/section sheets, 30/60/90-day plans)
├── Practice Hub (quiz engine, mock timer mode, mistake notebook, review queue)
├── Attempt Dashboard (dates, deadlines, applicable amendments/Finance Act, countdown, RTP links)
├── Amendment Tracker (what changed since the SM edition, per paper, per attempt, sourced)
├── SPOM Guide · Articleship Guide · Exemption Rules Explained
└── About / Method / Contribute / Disclaimer
```

### 6.2 Core data models (for Claude Code)
```
Level { id, name }
Paper { id, level_id, group, number, name, pattern: {mcq_pct, descriptive_pct, negative_marking}, open_book: bool }
Chapter { id, paper_id, order, name, syllabus_ref }
Topic { id, chapter_id, name, note_slug, mastery_thresholds }
Question {
  id, topic_ids[], type: mcq|descriptive|case_mcq_set,
  stem, options[], correct, explanation_per_option,
  difficulty, source: "original", author, reviewer,
  applicable_attempts[], last_verified_date, law_as_on_date
}
Flashcard { id, topic_id, front, back, deck, applicable_attempts[] }
ResourceLink {
  id, paper_id, attempt, kind: SM|RTP|MTP|PastPaper|SuggestedAnswers|LVC|Act|Notification,
  title, url, requires_icai_login: bool, last_checked_date, status: live|moved|dead
}
Attempt { id, name: "May 2026", exam_dates, form_window, applicable_finance_act, amendment_cutoff_date }
UserProgress (local-first) { topic_mastery{}, quiz_history[], mistakes[], fsrs_state{}, plan{} }
```
Attempt-tagging (`applicable_attempts`, `law_as_on_date`) is the most important field in the schema. Tax/law content without it is a liability.

### 6.3 Tech stack recommendation
- **Framework:** Astro (content-heavy, MD/MDX-native, islands for interactive widgets) or Next.js SSG. Astro preferred: faster on cheap Android phones, which is the real user device.
- **Content:** MDX files in the Git repo. Frontmatter carries paper/chapter/topic/attempt tags, author, reviewer, last_verified. Content = code = reviewable via PRs.
- **Question bank:** JSON/YAML in repo (or SQLite built at compile time); quiz engine is a client-side island. No backend needed for v1.
- **Spaced repetition:** ts-fsrs (open-source FSRS scheduler). State in localStorage/IndexedDB with export/import; optional sync later.
- **Search:** Pagefind (static, free, works offline-ish).
- **Progress/accounts:** local-first v1 (no login, no privacy burden — many users are minors). Phase 3: optional sync via Supabase/Cloudflare D1 free tier.
- **Hosting:** Cloudflare Pages (free, fast in India) + domain (~₹800/yr). Total running cost ≈ domain only.
- **PWA:** installable, offline-cached notes and question bank — many students have unreliable data. High effort-to-value; schedule Phase 2.
- **Analytics:** privacy-friendly (Cloudflare Web Analytics / Plausible self-host later). No ad trackers ever.
- **Link health:** scheduled GitHub Action that pings every ResourceLink weekly and opens an issue on 404/redirect (ICAI reshuffles URLs often — dead links destroy trust fastest).
- **Repo:** public GitHub from day one. CONTRIBUTING.md with the accuracy workflow below.

### 6.4 The accuracy machine (quality is a process, not an intention)
1. **Traceability rule:** every factual claim in notes carries a source ref (ICAI SM module §, Act section, notification no.). Enforced in review.
2. **Two-person rule for content:** author + reviewer (ideally a qualified CA or Final-level student) before merge. Until you have reviewers, mark unreviewed pages with a visible "community draft" badge.
3. **Attempt gating:** content shows a banner: "Verified for May 2026 attempt. Checking for Sept 2026." Nothing silently rots.
4. **Amendment calendar:** recurring workflow keyed to the ecosystem's rhythm — Finance Act (Feb–Apr), GST notifications (rolling), ICAI SM edition updates, RTP releases (~2 months pre-exam), applicability announcements. Each triggers a review sweep of tagged pages.
5. **Error reporting:** one-click "report an error" on every page/question → GitHub issue. Publicly visible fix log. Turning readers into proofreaders is how free projects reach paid-quality accuracy.
6. **Honesty page:** what the site is, isn't, and how errors are handled. Never claim ICAI affiliation; always tell students the ICAI material is the primary source and the exam-setter's voice.

### 6.5 What NOT to build (scope discipline)
- No video hosting/production (link to ICAI's and curated free lectures instead).
- No forum in v1 (moderation burden; point to a Telegram/Discord you moderate lightly).
- No accounts/login in v1.
- No AI-generated notes published without human expert review — in tax/law, hallucinated section numbers are worse than nothing.
- No test-series evaluation service in v1 (labor-intensive; the paid market does this).

---

## 7. Phased Roadmap

### Phase 0 — "The Map" (weeks 1–4) → launchable
- Site skeleton, taxonomy for all 3 levels, 16 paper pages.
- The definitive **resource directory**: every official free link per paper per current attempt, login-required flags, last-checked dates.
- Level guides: structure, passing/exemption rules in plain language, registration walkthroughs, SPOM guide, attempt calendar/dashboard.
- Study-plan generator v1 (static templates per attempt distance: 6-month, 3-month, 60-day revision).
- "Self-study playbook": how to run your prep on ICAI material + free classes, built on retrieval + spacing.
- *Success bar:* a confused 12th-pass student can go from "what is CA?" to a complete, zero-cost prep setup in one sitting.

### Phase 1 — "The Engine" (months 2–4) → the differentiator
- Quiz engine (client-side): topic quizzes, mixed mode, timed mode, per-option explanations.
- Original MCQ + case-scenario question bank for **CA Intermediate** (decided). Build papers in order of content stability so the system matures before the volatile content arrives:
  1. Advanced Accounting (standards-based, stable) — prove the engine here
  2. Cost & Management Accounting, then FM-SM (stable)
  3. Auditing & Ethics, Corporate & Other Laws (moderate churn — SA revisions, Companies Act amendments)
  4. Taxation LAST (Finance Act churn every attempt) — only once attempt-tagging and the amendment tracker are battle-tested. Rule: no tax question merges without `law_as_on_date` and `applicable_attempts` populated.
- Mistake notebook + FSRS review queue + flashcard decks (accounting standards, law sections, formulas, QA shortcuts).
- Mastery tracking per topic; paper progress maps.
- Past-paper weightage analysis pages (original analysis of publicly listed papers).

### Phase 2 — depth + resilience (months 4–8)
- Original chapter notes for the chosen level (worked-example-first format), then expand level by level.
- Descriptive-answer training: model-answer anatomy, self-grading rubrics, timed drills.
- PWA/offline; Hindi/Hinglish variants of high-traffic explainers.
- Amendment tracker automation (sourced changelog per paper).

### Phase 3 — community + scale (months 8+)
- Contributor pipeline (recruit CA finalists/newly-qualifieds — many want to teach/give back; contribution = portfolio).
- Optional account sync; Inter → Final content expansion; mentor AMAs; partnerships with free-content educators.

---

## 8. Distribution (a great site nobody finds helps nobody)
- **SEO:** attempt-specific evergreen pages ("CA Inter May 2027 — dates, applicable amendments, free resources") are what students search; keep them genuinely current and they compound. Structured data + fast pages beat blog farms on quality signals.
- **Communities:** answer questions (genuinely, not spammily) where students already are — r/CharteredAccountants, Quora, student Telegram/WhatsApp groups. Free + no-upsell is itself the viral hook.
- **Launch moments:** result days and registration-deadline weeks are traffic spikes; have shareable one-page guides ready.
- **Ethos as marketing:** "no ads, no paid tier, no lead-gen, open source" — say it loudly; it's the exact opposite of every competitor and students notice.

## 9. Risks & honest assessment
| Risk | Severity | Mitigation |
|---|---|---|
| Content staleness (law/tax changes every attempt) | **Highest** | Attempt-tagging in schema, amendment calendar, verified-for badges, link checker; prefer linking over rewriting volatile content |
| Copyright misstep with ICAI material | High | Link-only policy, original-words rule, review checklist, disclaimer; optionally seek ICAI permission |
| Accuracy errors in original content | High | Two-person review, source-traceability rule, public error reporting, "draft" badges |
| Solo-maintainer burnout | High | Open source from day one, narrow Phase 1 scope (one level), automate link/amendment checks, recruit reviewers early |
| Being mistaken for/attacked as ICAI-affiliated | Medium | Clear branding distance, disclaimers, no ICAI marks |
| Nobody finds it | Medium | Distribution plan above; attempt-page SEO; community presence |

**Is it possible?** Yes — and it's more tractable than it looks, precisely because content acquisition (the expensive part) is already solved by ICAI. The genuinely hard parts are (1) keeping tax/law content current per attempt and (2) writing a large original question bank with excellent explanations. Both are solvable with process + community, and both are exactly what no free competitor does well. The realistic promise is not "replace coaching for everyone" but "make coaching optional for disciplined students and dramatically cheaper prep for everyone else" — that alone is transformative at CA's scale (~3.5+ lakh exam candidates per cycle).

## 10. Success metrics
- Weekly active students; % returning 4+ weeks (habit = the pedagogy is working).
- Questions attempted per user per week (practice volume is the leading indicator of marks).
- Resource-directory click-throughs to ICAI (proof the map works).
- Error reports resolved < 7 days; zero dead official links at any time.
- Qualitative: "cleared without coaching" testimonials; contributor count.

---
*Prepared July 2026. Exam-structure facts summarized from ICAI announcements and current prep-ecosystem coverage; re-verify every regulatory detail against icai.org before publishing. Learning-science references: Dunlosky et al. (2013), Psychological Science in the Public Interest; Hattie & Donoghue meta-analysis (2021); Roediger & Karpicke (2006) on the testing effect; Bloom (1984) two-sigma problem; FSRS open-source scheduler.*
