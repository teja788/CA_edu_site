# Adhyayan — free, organized, evidence-based CA prep

> Every resource you need to become a CA is already free. We organize it, keep it
> current, and give you the practice system coaching never did.

**Independent — not affiliated with, or endorsed by, ICAI.**

ICAI gives away nearly everything a student needs: study material, RTPs, MTPs, past
papers with suggested answers, and free live classes. What students lack is
*organization, navigation, a practice engine, and a study method*. Adhyayan is that
missing layer — launched for **CA Intermediate**, built to expand.

## What's here

- **The map** — every official free resource per paper per attempt, with login flags
  and last-checked dates. Deep links only; **ICAI material is never re-hosted**.
- **The engine** — original MCQs where every option explains itself, a mistake
  notebook, spaced-repetition flashcards, mastery tracking. All local-first
  (no accounts, no trackers).
- **The method** — level guides, exemption/SPOM/articleship explainers, a
  study-plan generator, and answer-writing training. Built on retrieval practice
  and spaced repetition (Dunlosky et al. 2013).

## Stack

[Astro](https://astro.build) static site · system fonts only · no client framework —
interactive islands are small vanilla-JS scripts · state in `localStorage` ·
PWA with offline cache · deployable to any static host (Cloudflare Pages recommended).

```sh
npm install
npm run dev      # local dev at :4321
npm run build    # static build to dist/
```

## Repository layout

```
src/data/       levels, papers, questions, flashcards, resource links (the content DB)
src/pages/      routes — dynamic [level]/[paper] pages + rich per-topic notes
src/components/ badges, callouts, mastery, trust rows, ad slots
src/scripts/    local-first progress store + spaced-repetition scheduler
```

## Content rules (non-negotiable)

1. **Never re-host ICAI PDFs or reproduce ICAI question/answer text.** Link only.
2. **Original words only** for notes and questions, written from the syllabus and primary law.
3. **Attempt-tag everything volatile** — `applicableAttempts` and `lastVerified` are mandatory on tax/law content.
4. Every factual claim carries a source ref; unreviewed pages carry a **Community draft** badge.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full accuracy workflow.

## License

Code: [MIT](LICENSE). Original content (notes, questions, flashcards): **CC BY-SA 4.0**.
