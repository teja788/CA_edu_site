/**
 * Question-bank assembly — BUILD TIME ONLY.
 *
 * This module reads every chapter bank under src/data/questions/ and flattens
 * it into the shape the practice quiz consumes. It is imported by the static
 * endpoints under src/pages/practice/banks/ and must never reach the browser:
 * `import.meta.glob` is a build-time construct, and the whole point of the
 * split is that a visitor downloads one chapter, not all forty-six.
 *
 * Two artefacts come out of here:
 *
 *   · one JSON file per bank — the full questions, stems and options, fetched
 *     only when a question from that chapter is actually about to be shown;
 *   · a manifest — id, topic and chapter metadata for EVERY question, which is
 *     what the deck is built and filtered from. It has to be complete, because
 *     ?mode=mistakes, ?topic= and an unscoped ?mode=mixed all legitimately
 *     range over the whole course.
 *
 * Splitting along that line is what keeps /practice/quiz/ small: the manifest
 * carries the ~60 bytes per question the filters need, and leaves behind the
 * ~2.7 KB per question of stem, options and explanations that they do not.
 */

import { questions as legacyMcqs } from '../data/site.js';

const bankModules = import.meta.glob('../data/questions/**/*.json', { eager: true });

/** URL-safe bank slug from the source path: <level>--<paper>--<chapter>. */
function slugFromPath(path) {
  const parts = path.split('/').slice(-3);
  return parts.join('--').replace(/\.json$/, '');
}

/**
 * Flatten one bank's questions.
 *
 * Descriptive questions (model-answer skeletons) live in /practice/descriptive/,
 * not here — only MCQs enter the deck. Case-scenario sets (the Inter 30% MCQ
 * pattern) flatten into linked MCQs that stay together and score as a unit.
 */
function flatten(bank) {
  return bank.questions.flatMap((q) => {
    if (q.type === 'case_mcq_set' && Array.isArray(q.questions)) {
      return q.questions.map((sub, i) => ({
        topic: q.topic,
        applicableAttempts: q.applicableAttempts,
        lawAsOnDate: q.lawAsOnDate,
        ...sub,
        type: 'mcq',
        case: { id: q.id, text: q.case, pos: i + 1, size: q.questions.length },
      }));
    }
    return q.type === 'mcq' ? [q] : [];
  });
}

/**
 * Every bank, in a stable order, each with its shared metadata and its
 * flattened questions.
 *
 * @returns {Array<{slug: string, meta: object, questions: Array}>}
 */
export function buildBanks() {
  const banks = Object.entries(bankModules)
    .sort(([a], [b]) => a.localeCompare(b))
    .flatMap(([path, mod]) => {
      const bank = mod.default ?? mod;
      if (!Array.isArray(bank.questions)) return [];
      const paperNum = Number((bank.paper ?? '').match(/Paper\s*(\d)/i)?.[1] ?? 0);
      const chapterNum = Number((bank.chapter ?? '').match(/Ch\s*(\d+)/i)?.[1] ?? 0);
      return [
        {
          slug: slugFromPath(path),
          meta: {
            level: bank.level,
            paper: bank.paper,
            // Canonical route slug carried by the bank; slugifying the display
            // string loses "&" → "and" and breaks ?paper= filters.
            paperSlug: bank.paperSlug ?? null,
            chapterSlug: bank.chapterSlug,
            // Foundation Papers 3 & 4 are the only negatively marked papers.
            negative: bank.level === 'foundation' && [3, 4].includes(paperNum),
            masteryId:
              paperNum && chapterNum
                ? `${bank.level === 'foundation' ? 'f' : 'i'}${paperNum}-ch${chapterNum}`
                : null,
          },
          questions: flatten(bank),
        },
      ];
    });

  // The launch questions in site.js are Inter P1 and predate the chapter banks.
  // They ride in a bank of their own so the client has one uniform shape to
  // fetch, rather than a special case inlined into the page.
  banks.unshift({
    slug: 'legacy--advanced-accounting--launch',
    meta: {
      level: 'intermediate',
      paper: 'Paper 1 — Advanced Accounting',
      paperSlug: 'advanced-accounting',
      chapterSlug: null,
      negative: false,
      masteryId: null,
    },
    questions: legacyMcqs.map((q) => ({ ...q })),
  });

  return banks;
}

/**
 * The deck-building manifest: enough to filter, sample and order every
 * question in the course, and nothing more.
 *
 * Questions are tuples rather than objects — at ~2,400 entries the repeated
 * key names cost more than the values do.
 *   [bankIndex, id, topic, caseId, casePos, caseSize]
 * The last three are omitted entirely for a plain MCQ.
 *
 * Per-question `masteryId` on the legacy launch questions is the one field
 * that varies WITHIN a bank, so it rides as a seventh slot when present.
 */
export function buildManifest(banks) {
  const questions = [];
  banks.forEach((bank, bankIndex) => {
    for (const q of bank.questions) {
      const row = [bankIndex, q.id, q.topic];
      if (q.case) row.push(q.case.id, q.case.pos, q.case.size);
      else if (q.masteryId) row.push(null, null, null);
      if (q.masteryId) row.push(q.masteryId);
      questions.push(row);
    }
  });
  return {
    banks: banks.map((b) => ({ slug: b.slug, ...b.meta })),
    questions,
  };
}
