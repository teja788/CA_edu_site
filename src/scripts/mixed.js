/**
 * Mixed cumulative sets — sampling one session across a whole paper.
 *
 * Chapter-at-a-time practice teaches you to answer a question you already
 * know the chapter of. The exam never tells you. Interleaving — mixing
 * chapters inside a single session — is the retrieval-practice finding this
 * module exists to implement: it feels harder and measures better, because
 * choosing WHICH rule applies is the skill being tested.
 *
 * Everything here is pure. The quiz page supplies the deck, the per-chapter
 * mastery/mistake stats it reads from localStorage, and a random source; this
 * module decides only how many questions come from where, and in what order.
 * That keeps it testable under plain node with no DOM and no storage.
 */

/** Session size for a mixed set — long enough to spread, short enough to sit. */
export const MIXED_SET_SIZE = 20;

/**
 * Group a deck into atomic units. A case-scenario set's linked MCQs must be
 * served together and in order, so each set travels as ONE unit and is
 * counted by its length. A plain MCQ is a unit of one.
 */
export function toUnits(questions) {
  const units = [];
  for (const q of questions) {
    const last = units[units.length - 1];
    if (q.case && last && last[0].case && last[0].case.id === q.case.id) last.push(q);
    else units.push([q]);
  }
  return units;
}

/**
 * How much of the session a chapter deserves.
 *
 * Two signals, both pointing the same way — toward what is not yet secure:
 *   · mistakes due for review in that chapter (capped, so one bad day cannot
 *     swallow the whole set)
 *   · mastery, inverted — an untouched chapter (0) weighs three times a
 *     proficient one (2+).
 * The floor is 1, so a chapter you have mastered still shows up occasionally.
 * That is deliberate: mastery decays, and a mixed set is where you find out.
 */
export function chapterWeight({ mastery = 0, due = 0 } = {}) {
  const m = Math.min(Math.max(mastery, 0), 2);
  const dueFactor = 1 + Math.min(Math.max(due, 0), 5);
  return dueFactor * (3 - m);
}

/** Fisher–Yates, on a copy, with an injectable random source. */
function shuffled(list, random) {
  const out = [...list];
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

/** Pick an index from `weights` proportionally. Returns -1 if all are zero. */
function weightedPick(weights, random) {
  const total = weights.reduce((a, b) => a + b, 0);
  if (total <= 0) return -1;
  let r = random() * total;
  for (let i = 0; i < weights.length; i++) {
    r -= weights[i];
    if (r < 0) return i;
  }
  return weights.length - 1;
}

/**
 * Order chosen units so that consecutive units come from different chapters
 * wherever that is possible — round-robin over the chapters, largest pile
 * first. Interleaving the ORDER matters as much as the mix: two questions
 * from the same chapter back to back let you answer the second from the
 * first's context instead of from memory.
 */
export function interleave(unitsByChapter) {
  const piles = [...unitsByChapter.entries()]
    .map(([slug, units]) => ({ slug, units: [...units] }))
    .filter((p) => p.units.length > 0);
  const out = [];
  let lastSlug = null;
  while (piles.length > 0) {
    piles.sort((a, b) => b.units.length - a.units.length);
    // Prefer the biggest pile that is not the one we just drew from.
    let pick = piles.find((p) => p.slug !== lastSlug) ?? piles[0];
    out.push(pick.units.shift());
    lastSlug = pick.slug;
    for (let i = piles.length - 1; i >= 0; i--) {
      if (piles[i].units.length === 0) piles.splice(i, 1);
    }
  }
  return out;
}

/**
 * Sample a mixed cumulative set.
 *
 * @param {Array} questions  the deck, already scoped to one paper.
 * @param {object} opts
 *   size      target number of QUESTIONS (case sets may overshoot by design —
 *             a set is never cut in half).
 *   statsFor  (chapterSlug) => { mastery, due } — from localStorage.
 *   restrictTo optional array of chapter slugs; when given, only these are
 *             eligible (the confusable-regime preset).
 *   requireStarted  when true (the default), chapters the student has not
 *             started are excluded — UNLESS that would empty the pool, in
 *             which case every chapter is eligible. A student who has read
 *             nothing yet still gets a working set.
 *   random    injectable for tests.
 *
 * @returns {{ questions: Array, chapters: string[], startedOnly: boolean }}
 */
export function sampleMixedSet(questions, opts = {}) {
  const {
    size = MIXED_SET_SIZE,
    statsFor = () => ({}),
    restrictTo = null,
    requireStarted = true,
    random = Math.random,
  } = opts;

  const allow = restrictTo ? new Set(restrictTo) : null;

  // Bucket the deck by chapter.
  const byChapter = new Map();
  for (const unit of toUnits(questions)) {
    const slug = (unit[0].meta && unit[0].meta.chapterSlug) || '_unchaptered';
    if (allow && !allow.has(slug)) continue;
    if (!byChapter.has(slug)) byChapter.set(slug, []);
    byChapter.get(slug).push(unit);
  }
  if (byChapter.size === 0) return { questions: [], chapters: [], startedOnly: false };

  // Eligible chapters: started ones, or all of them when nothing is started.
  const all = [...byChapter.keys()];
  const started = all.filter((slug) => (statsFor(slug).mastery ?? 0) >= 1);
  const startedOnly = requireStarted && started.length > 0;
  const eligible = startedOnly ? started : all;

  // Weight, and pre-shuffle each chapter's units so "take the next" is a
  // random draw without re-sorting on every pick.
  const pools = eligible.map((slug) => ({
    slug,
    weight: chapterWeight(statsFor(slug)),
    units: shuffled(byChapter.get(slug), random),
  }));
  pools.sort((a, b) => b.weight - a.weight);

  const taken = new Map(eligible.map((slug) => [slug, []]));
  let count = 0;

  // A linked case set is never cut in half, so a unit is only taken when it
  // FITS the remaining budget. Units are pre-shuffled, so taking the first
  // fitting one is still a random draw. Returns null when nothing fits —
  // the set then ends at or below `size`, never over it.
  const takeFitting = (pool, remaining) => {
    const at = pool.units.findIndex((u) => u.length <= remaining);
    if (at < 0) return null;
    const [unit] = pool.units.splice(at, 1);
    taken.get(pool.slug).push(unit);
    count += unit.length;
    return unit;
  };

  // Pass 1 — one unit from every eligible chapter, heaviest first, while the
  // budget allows. This is what guarantees the set actually spans the paper
  // rather than collapsing onto the two chapters with the worst mistakes.
  for (const pool of pools) {
    if (count >= size) break;
    takeFitting(pool, size - count);
  }

  // Pass 2 — fill the remainder proportionally to weight.
  while (count < size) {
    const remaining = size - count;
    const live = pools.filter((p) => p.units.some((u) => u.length <= remaining));
    if (live.length === 0) break;
    const idx = weightedPick(live.map((p) => p.weight), random);
    if (idx < 0) break;
    takeFitting(live[idx], remaining);
  }

  // Drop chapters that contributed nothing, then interleave.
  for (const [slug, units] of [...taken.entries()]) {
    if (units.length === 0) taken.delete(slug);
  }
  const ordered = interleave(taken);

  return {
    questions: ordered.flat(),
    chapters: [...taken.keys()],
    startedOnly,
  };
}
