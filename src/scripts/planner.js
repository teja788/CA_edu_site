/**
 * Foundation study planner (plan §7) — pure, deterministic, dependency-free.
 *
 * No DOM, no localStorage, no Date.now(), no Math.random(). Everything the
 * planner needs arrives in `input`, so the same input always produces the
 * same JSON. plan.astro owns persistence; dashboard.astro owns the day view.
 *
 * The shape follows the research skeleton:
 *   · three phases over the available study days — learn 50%, practice 30%,
 *     pure revision 20%
 *   · exactly three revision cycles of shrinking depth: chapter-level,
 *     group-level, then paper-level one-pagers in the final fortnight
 *   · about a fifth of the days held back as buffer, sprinkled weekly
 *   · five to seven full mocks in the final three to five weeks, two of them
 *     anchored to the usual ICAI MTP windows
 *   · every study day pairs one practical paper (P1/P3) with one theory
 *     paper (P2/P4); the sequence opens with Accounting
 *   · weak papers draw more slots (P3 is pre-checked weak by the page)
 *   · the day after a mock is a "minimum effective dose" day
 *
 * Warnings are emitted, never blocks. A plan that is too short to work is
 * still generated, with the reason said plainly.
 */

/* ── constants ────────────────────────────────────────────────────────── */

/** Weekly-hour envelopes by situation. Below or above → a warning, not a stop. */
export const MODE_ENVELOPES = {
  class12: { lo: 14, hi: 27, label: 'School and CA Foundation together' },
  postboards: { lo: 35, hi: 60, label: 'After the board exams, Foundation full-time' },
  bcom: { lo: 20, hi: 40, label: 'Alongside B.Com or other college' },
};

/** Learn → practice → pure revision, as fractions of the working days. */
export const PHASE_SPLIT = { learn: 0.5, practice: 0.3, revision: 0.2 };

/** A paper marked weak draws this much more study time per chapter. */
export const WEAK_MULTIPLIER = 1.35;

/** Runways shorter than this cannot hold a learn phase — revision only. */
export const COMPRESSED_RUNWAY_DAYS = 21;

/** Cycle 3 (paper-level one-pagers) never starts earlier than this. */
export const CYCLE3_WINDOW_DAYS = 14;

/** Mocks live in this window before the first paper. */
export const MOCK_WINDOW = { from: 35, to: 4 };

/** Practical papers are paired with theory papers, one of each per day. */
export const PRACTICAL_PAPERS = ['accounting', 'quantitative-aptitude'];
export const THEORY_PAPERS = ['business-laws', 'business-economics'];

const DAY_MS = 86400000;

/* ── dates: ISO strings in, ISO strings out, UTC midnight in between ──── */

export function parseISO(iso) {
  if (typeof iso !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(iso)) return null;
  const d = new Date(`${iso}T00:00:00Z`);
  return Number.isFinite(d.getTime()) ? d : null;
}

export function toISO(date) {
  return date.toISOString().slice(0, 10);
}

export function addDays(iso, n) {
  const d = parseISO(iso);
  if (!d) return null;
  return toISO(new Date(d.getTime() + n * DAY_MS));
}

/** Whole days from `a` to `b` (positive when b is later). */
export function diffDays(a, b) {
  const x = parseISO(a);
  const y = parseISO(b);
  if (!x || !y) return null;
  return Math.round((y.getTime() - x.getTime()) / DAY_MS);
}

/** 0 = Monday … 6 = Sunday. */
export function weekday(iso) {
  const d = parseISO(iso);
  return d ? (d.getUTCDay() + 6) % 7 : null;
}

/** The Monday on or before `iso` — weeks in the output start there. */
export function mondayOf(iso) {
  return addDays(iso, -weekday(iso));
}

/** Inclusive list of ISO dates. Empty when `to` precedes `from`. */
export function dateRange(from, to) {
  const n = diffDays(from, to);
  if (n === null || n < 0) return [];
  const out = [];
  for (let i = 0; i <= n; i += 1) out.push(addDays(from, i));
  return out;
}

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'];

/** "2026-09-02" → "2 Sept 2026". Labels are built here so the plan JSON
 *  reads on its own, without the page having to reformat every string. */
export function humanDate(iso) {
  const d = parseISO(iso);
  if (!d) return '';
  const month = MONTHS[d.getUTCMonth()];
  const short = month === 'September' ? 'Sept' : month.length > 4 ? month.slice(0, 3) : month;
  return `${d.getUTCDate()} ${short} ${d.getUTCFullYear()}`;
}

/** "2026-09" — the key the month-by-month overview groups on. */
export function monthKey(iso) {
  return iso.slice(0, 7);
}

export function monthLabel(iso) {
  const d = parseISO(iso);
  return d ? `${MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}` : '';
}

/* ── papers, chapters, weightage ──────────────────────────────────────── */

/**
 * Chapters of a paper, in study-material order. Accepts either the full
 * `foundationPapers` record (sections → chapters) or the slimmed shape a
 * page may hand over (a flat `chapters` array), so the module stays
 * data-agnostic.
 */
export function chaptersOf(paper) {
  const flat = Array.isArray(paper.chapters)
    ? paper.chapters
    : (paper.sections ?? []).flatMap((s) => s.chapters ?? []);
  return flat.map((c) => ({
    paperSlug: paper.slug,
    slug: c.slug,
    number: c.number,
    name: c.name,
  }));
}

/** Marks a weightage group is a percentage OF: the Part for P3, else the paper. */
function groupBasisMarks(group, paper) {
  if ((paper.weightageBasis ?? 'paper') !== 'section') return paper.marks ?? 100;
  const found = /\((\d+)\s*marks?\)/i.exec(group.section ?? '');
  return found ? Number(found[1]) : paper.marks ?? 100;
}

/**
 * Each chapter's share of its paper, in marks, from the ICAI weightage
 * groups. A group's marks are split evenly across the chapters it covers —
 * ICAI publishes no finer split, so neither do we. Groups with no published
 * range (P3 Part B) use their `marks` figure. A chapter in no group at all
 * falls back to the paper's average so it can never score zero and vanish.
 */
export function chapterWeights(paper) {
  const chapters = chaptersOf(paper);
  const weights = new Map(chapters.map((c) => [c.slug, 0]));
  for (const group of paper.weightageGroups ?? []) {
    const slugs = group.chapterSlugs ?? [];
    if (slugs.length === 0) continue;
    let marks;
    if (group.weightage) {
      const mid = (group.weightage.lo + group.weightage.hi) / 2;
      marks = (mid / 100) * groupBasisMarks(group, paper);
    } else {
      marks = typeof group.marks === 'number' ? group.marks : 0;
    }
    for (const slug of slugs) {
      if (weights.has(slug)) weights.set(slug, weights.get(slug) + marks / slugs.length);
    }
  }
  const scored = [...weights.values()].filter((v) => v > 0);
  const average = scored.length ? scored.reduce((a, b) => a + b, 0) / scored.length : 1;
  for (const [slug, value] of weights) if (value <= 0) weights.set(slug, average);
  return weights;
}

/* ── allocation ───────────────────────────────────────────────────────── */

/**
 * Split `total` slots across `weights` by largest remainder, giving every
 * entry at least one. When there are fewer slots than entries everyone still
 * gets one — the day packer then puts two chapters on some days rather than
 * letting a chapter fall off the plan entirely.
 */
export function allocate(weights, total) {
  const n = weights.length;
  if (n === 0) return [];
  if (total <= n) return weights.map(() => 1);
  const spare = total - n;
  const sum = weights.reduce((a, b) => a + b, 0) || n;
  const exact = weights.map((w) => (w / sum) * spare);
  const counts = exact.map((e) => Math.floor(e));
  let left = spare - counts.reduce((a, b) => a + b, 0);
  // Largest fractional remainder first; ties break on index, so this is
  // stable for a given input.
  const order = exact
    .map((e, i) => ({ i, frac: e - Math.floor(e) }))
    .sort((a, b) => (b.frac - a.frac) || (a.i - b.i));
  for (let k = 0; k < order.length && left > 0; k += 1, left -= 1) counts[order[k].i] += 1;
  return counts.map((c) => c + 1);
}

/**
 * Interleave two ordered streams in proportion to their lengths, always
 * opening with the first stream — that is what makes day 1 Accounting.
 */
export function mergeStreams(a, b) {
  const out = [];
  let i = 0;
  let j = 0;
  while (i < a.length || j < b.length) {
    if (j >= b.length) out.push(a[i++]);
    else if (i >= a.length) out.push(b[j++]);
    else if (i / a.length <= j / b.length) out.push(a[i++]);
    else out.push(b[j++]);
  }
  return out;
}

/**
 * Deal `items` across `dayCount` days, order preserved and load even. Days
 * that would come out empty (more days than items) carry the item before
 * them again — a second pass at the same chapter, never a blank day.
 */
export function dealAcrossDays(items, dayCount) {
  const out = Array.from({ length: Math.max(0, dayCount) }, () => []);
  if (out.length === 0 || items.length === 0) return out;
  let last = null;
  for (let d = 0; d < out.length; d += 1) {
    const from = Math.floor((d * items.length) / out.length);
    const to = Math.floor(((d + 1) * items.length) / out.length);
    for (let k = from; k < to; k += 1) {
      out[d].push({ item: items[k], repeat: false });
      last = items[k];
    }
    if (out[d].length === 0) {
      // More days than items: a second pass at the last thing covered,
      // never a blank day.
      out[d].push(last === null ? { item: items[0], repeat: false } : { item: last, repeat: true });
      if (last === null) last = items[0];
    }
  }
  return out;
}

/* ── the calendar scaffold ────────────────────────────────────────────── */

/**
 * Buffer days, sprinkled about weekly: every Saturday, plus the Wednesday of
 * every third week. That lands near a fifth of the runway without ever
 * putting two rest days back to back, and it leaves Sunday free — Sunday is
 * where the full mocks go.
 */
function isBufferDay(iso, startDate) {
  const wd = weekday(iso);
  if (wd === 5) return true;
  const week = Math.floor(diffDays(startDate, iso) / 7);
  return wd === 2 && week % 3 === 2;
}

/**
 * Split the working days into phases. A runway too short to hold a learning
 * phase becomes three revision cycles and nothing else — said plainly in the
 * warnings rather than dressed up as a full plan.
 */
function splitPhases(work, compressed, examStart) {
  const W = work.length;
  if (W === 0) return { phase1: [], cycle1: [], cycle2: [], cycle3: [] };

  if (compressed) {
    const c1 = Math.max(1, Math.round(W * PHASE_SPLIT.learn));
    const c2 = Math.max(W - c1 > 1 ? 1 : 0, Math.round(W * PHASE_SPLIT.practice));
    const c3 = Math.max(0, W - c1 - c2);
    return {
      phase1: [],
      cycle1: work.slice(0, c1),
      cycle2: work.slice(c1, c1 + c2),
      cycle3: work.slice(c1 + c2, c1 + c2 + c3),
    };
  }

  const n1 = Math.round(W * PHASE_SPLIT.learn);
  const n3 = Math.round(W * PHASE_SPLIT.revision);
  const n2 = Math.max(0, W - n1 - n3);
  const phase1 = work.slice(0, n1);
  const cycle1 = work.slice(n1, n1 + n2);
  const phase3 = work.slice(n1 + n2);

  // Cycle 3 — the paper-level one-pagers — belongs in the last fortnight.
  // Whichever is later, the start of phase 3 or fourteen days out, wins.
  const gate = addDays(examStart, -CYCLE3_WINDOW_DAYS);
  let cut = phase3.findIndex((d) => d >= gate);
  if (cut < 0) cut = Math.max(0, phase3.length - 2);
  // Cycle 2 keeps at least one day, cycle 3 at least two, where there is room.
  if (phase3.length >= 3) cut = Math.min(Math.max(cut, 1), phase3.length - 2);
  return { phase1, cycle1, cycle2: phase3.slice(0, cut), cycle3: phase3.slice(cut) };
}

/**
 * Five to seven full mocks in the last three to five weeks. Sundays first —
 * a full paper needs an unbroken afternoon — then the two dates that track
 * ICAI's usual MTP Series I and II windows, then whatever is left, spread.
 */
function pickMocks(work, examStart, protectedDays) {
  const from = addDays(examStart, -MOCK_WINDOW.from);
  const to = addDays(examStart, -MOCK_WINDOW.to);
  const pool = work.filter((d) => d >= from && d <= to && !protectedDays.has(d));
  const n = pool.length;
  let target = n >= 20 ? 6 : n >= 14 ? 5 : n >= 8 ? 3 : n >= 4 ? 2 : n >= 1 ? 1 : 0;
  // On a short runway the mocks would eat the revision cycles they are meant
  // to test. A fifth of the working days is the most they may take.
  target = Math.min(target, Math.max(1, Math.floor(work.length / 5)));
  const chosen = [];
  const take = (d) => {
    if (d && pool.includes(d) && !chosen.includes(d) && chosen.length < target) chosen.push(d);
  };
  for (const d of pool) if (weekday(d) === 6) take(d);
  take(addDays(examStart, -22)); // ICAI MTP Series I window
  take(addDays(examStart, -8)); //  ICAI MTP Series II window
  for (let k = 0; k < n && chosen.length < target; k += 1) {
    take(pool[Math.floor(((k + 1) * n) / (target + 1)) % n]);
  }
  for (const d of pool) take(d);
  return chosen.sort();
}

/* ── assignments ──────────────────────────────────────────────────────── */

function shortOf(paper) {
  return paper.shortName ?? paper.name ?? paper.slug;
}

function assignment(paper, chapter, activity, label, extra) {
  return {
    paperSlug: paper ? paper.slug : null,
    paperName: paper ? shortOf(paper) : null,
    chapterSlug: chapter ? chapter.slug : null,
    chapterName: chapter ? chapter.name : null,
    activity,
    label,
    ...(extra ?? {}),
  };
}

/** Total weighted mass of a paper — its marks, tilted if it is a weak paper. */
function paperMass(paper, weak) {
  const weights = chapterWeights(paper);
  const sum = [...weights.values()].reduce((a, b) => a + b, 0);
  return sum * (weak.has(paper.slug) ? WEAK_MULTIPLIER : 1);
}

/**
 * One study stream (practical or theory): chapters expanded into as many
 * visits as their weightage earns, the two papers interleaved in proportion,
 * the higher-numbered paper never crowding out the opener.
 */
function studyStream(pairPapers, slots, weak) {
  const live = pairPapers.filter(Boolean);
  if (live.length === 0 || slots <= 0) return [];
  const masses = live.map((p) => paperMass(p, weak));
  const perPaper = allocate(masses, slots);
  const streams = live.map((paper, i) => {
    const chapters = chaptersOf(paper);
    const weights = chapterWeights(paper);
    const counts = allocate(chapters.map((c) => weights.get(c.slug) ?? 1), perPaper[i]);
    const visits = [];
    chapters.forEach((chapter, ci) => {
      for (let k = 0; k < counts[ci]; k += 1) {
        visits.push({ paper, chapter, first: k === 0 });
      }
    });
    return visits;
  });
  return streams.length === 1 ? streams[0] : mergeStreams(streams[0], streams[1]);
}

/** Every chapter of a pair of papers, once, interleaved — a cycle-1 pass. */
function revisionStream(pairPapers) {
  const streams = pairPapers
    .filter(Boolean)
    .map((paper) => chaptersOf(paper).map((chapter) => ({ paper, chapter })));
  if (streams.length === 0) return [];
  return streams.length === 1 ? streams[0] : mergeStreams(streams[0], streams[1]);
}

/** Lay a practical stream and a theory stream over the same days, one each. */
function layPair(days, practical, theory, toAssignment) {
  const left = dealAcrossDays(practical, days.length);
  const right = dealAcrossDays(theory, days.length);
  const out = new Map();
  days.forEach((date, i) => {
    const list = [];
    for (const entry of left[i]) list.push(toAssignment(entry));
    for (const entry of right[i]) list.push(toAssignment(entry));
    out.set(date, list);
  });
  return out;
}

/* ── the plan ─────────────────────────────────────────────────────────── */

function dayRecord(date, kind, assignments, note) {
  const rec = { date, weekday: weekday(date), kind, assignments: assignments ?? [] };
  if (note) rec.note = note;
  return rec;
}

/**
 * Build a Foundation study plan.
 *
 * input = {
 *   attemptId, examDate (ISO), startDate (ISO),
 *   mode: 'class12' | 'postboards' | 'bcom',
 *   hoursPerWeek, weakPapers: [paperSlug],
 *   papers: the Foundation paper records,
 *   paperDates?: [{ paperSlug, date }]   — per-paper exam dates, when notified
 *   registrationCutoff?: ISO, registrationLabel?: string,
 *   attemptName?: string, sessionLabel?: string
 * }
 */
export function generatePlan(input) {
  const warnings = [];
  const papers = Array.isArray(input?.papers) ? input.papers.filter(Boolean) : [];
  const bySlug = new Map(papers.map((p) => [p.slug, p]));
  const weak = new Set(Array.isArray(input?.weakPapers) ? input.weakPapers : []);
  const mode = MODE_ENVELOPES[input?.mode] ? input.mode : 'bcom';
  const envelope = MODE_ENVELOPES[mode];
  const hours = Number(input?.hoursPerWeek);
  const attemptName = input?.attemptName ?? input?.attemptId ?? 'your attempt';

  /* Exam window: per-paper dates when ICAI has notified them, else the one
     date the student is working to. */
  const paperDates = (Array.isArray(input?.paperDates) ? input.paperDates : [])
    .filter((p) => p && p.date && bySlug.has(p.paperSlug))
    .slice()
    .sort((a, b) => a.date.localeCompare(b.date));
  const examStart = paperDates.length ? paperDates[0].date : input?.examDate ?? null;
  const examEnd = paperDates.length ? paperDates[paperDates.length - 1].date : examStart;
  const startDate = input?.startDate ?? null;

  const examWindow = {
    first: examStart,
    last: examEnd,
    papers: paperDates.map((p) => ({
      paperSlug: p.paperSlug,
      paperName: shortOf(bySlug.get(p.paperSlug)),
      date: p.date,
      label: p.label ?? humanDate(p.date),
    })),
  };
  const empty = (why) => {
    warnings.unshift(why);
    return { input: null, phases: [], weeks: [], mocks: [], warnings, examWindow, summary: null };
  };

  if (!parseISO(startDate)) return empty('No start date — pick the day you want to begin and the plan will build from there.');
  if (!parseISO(examStart)) {
    return empty(
      `ICAI has not notified dates for ${attemptName}. Put in the date you are working towards and the plan will shape itself around it — nothing here is a prediction of the real timetable.`
    );
  }
  if (papers.length === 0) return empty('No paper data reached the planner.');

  const runway = dateRange(startDate, addDays(examStart, -1));
  if (runway.length === 0) {
    return empty(
      `Your start date is on or after the first paper (${humanDate(examStart)}). Nothing left to schedule — set an earlier start, or pick the next attempt.`
    );
  }

  /* Weekly hours against the envelope for this situation — a warning, never
     a block. The student knows their life better than the planner does. */
  if (!Number.isFinite(hours) || hours <= 0) {
    warnings.push('No weekly hours set, so the plan assumes you will fill each day as it comes.');
  } else if (hours < envelope.lo) {
    warnings.push(
      `${hours} hours a week sits under the ${envelope.lo}–${envelope.hi} that usually carries "${envelope.label}". The plan below still covers the syllabus, but each day is asked to do more than the hours allow — expect to lean on buffer days. One extra hour a day changes more than any schedule can.`
    );
  } else if (hours > envelope.hi) {
    warnings.push(
      `${hours} hours a week is above the ${envelope.lo}–${envelope.hi} band for "${envelope.label}". Plans built on hours nobody sustains break around week three. Treat the top of that band as the honest ceiling and keep the buffer days.`
    );
  }

  /* Registration cut-off — factual, and only when it actually bites. */
  const cutoff = input?.registrationCutoff ?? null;
  const cutoffLabel = input?.registrationLabel ?? (cutoff ? humanDate(cutoff) : null);
  if (cutoff && parseISO(cutoff)) {
    if (startDate > cutoff) {
      warnings.push(
        `Registration for ${attemptName} closed on ${cutoffLabel}. If you are not already registered with the ICAI Board of Studies, this plan belongs to the following attempt — the study sequence is the same either way.`
      );
    } else if (diffDays(startDate, cutoff) <= 30) {
      warnings.push(
        `Registration for ${attemptName} closes on ${cutoffLabel} — inside a month of your start date. Confirm your BoS registration before you sink weeks into this timetable.`
      );
    }
  }

  const compressed = runway.length < COMPRESSED_RUNWAY_DAYS;
  if (compressed) {
    warnings.push(
      `${runway.length} day${runway.length === 1 ? '' : 's'} to the first paper is revision territory, not first-study territory. The plan below drops the learning phase and runs three shrinking revision passes instead. If the syllabus is not already covered, the honest move is the next attempt — this plan will still hold the ground you have.`
    );
  }

  /* Exam eve is never a buffer and never a mock — it is the last quiet
     evening before the first paper. */
  const examEve = runway[runway.length - 1];
  const bufferDays = runway.filter((d) => d !== examEve && isBufferDay(d, startDate));
  const bufferSet = new Set(bufferDays);
  const work = runway.filter((d) => d !== examEve && !bufferSet.has(d));

  const { phase1, cycle1, cycle2, cycle3 } = splitPhases(work, compressed, examStart);

  /* Mocks may not land on the last two days of cycle 3 — those belong to the
     one-pagers, and a mock that late teaches nothing you can still fix. */
  const protectedDays = new Set(cycle3.slice(-2));
  const mockDates = pickMocks(work, examStart, protectedDays);
  const mockSet = new Set(mockDates);

  /* The day after a mock is the minimum effective dose: the mock has already
     taken the day's energy, and its mistakes are the best thing to touch. */
  const minimumSet = new Set();
  if (work.length >= 30) {
    for (const d of mockDates) {
      const next = addDays(d, 1);
      if (next !== examEve && work.includes(next) && !mockSet.has(next)) minimumSet.add(next);
    }
  }

  const teaching = (list) => list.filter((d) => !mockSet.has(d) && !minimumSet.has(d));

  /* Practical papers (P1, P3) pair with theory papers (P2, P4) — one of each
     on a study day, so no day is all ledgers or all sections. */
  const practicalPapers = PRACTICAL_PAPERS.map((s) => bySlug.get(s)).filter(Boolean);
  const theoryPapers = THEORY_PAPERS.map((s) => bySlug.get(s)).filter(Boolean);
  const paired = new Set([...PRACTICAL_PAPERS, ...THEORY_PAPERS]);
  for (const p of papers) if (!paired.has(p.slug)) theoryPapers.push(p);

  const dayAssignments = new Map();
  const put = (map) => { for (const [d, a] of map) dayAssignments.set(d, a); };

  /* Phase 1 — learning. Slots follow weightage midpoints times the weak-paper
     multiplier; every chapter earns at least one slot, so nothing is dropped. */
  const studyDays = teaching(phase1);
  if (studyDays.length > 0) {
    put(layPair(
      studyDays,
      studyStream(practicalPapers, studyDays.length, weak),
      studyStream(theoryPapers, studyDays.length, weak),
      ({ item, repeat }) => {
        const opening = item.first && !repeat;
        return assignment(item.paper, item.chapter, opening ? 'notes' : 'practice',
          `${shortOf(item.paper)} · Ch ${item.chapter.number} ${item.chapter.name} — ${opening ? 'first pass through the notes' : 'work the practice set'}`,
          { cycle: 0 });
      }
    ));
  }

  /* Revision cycle 1 — chapter level, every chapter of every paper. */
  const cycle1Days = teaching(cycle1);
  if (cycle1Days.length > 0) {
    put(layPair(
      cycle1Days,
      revisionStream(practicalPapers),
      revisionStream(theoryPapers),
      ({ item }) => assignment(item.paper, item.chapter, 'mixed',
        `${shortOf(item.paper)} · Ch ${item.chapter.number} ${item.chapter.name} — revise it, then work ten questions on it`,
        { cycle: 1 })
    ));
  }

  /* Revision cycle 2 — group level: ICAI's own weightage blocks, not chapters. */
  const groupStream = (list) => {
    const streams = list.map((paper) => (paper.weightageGroups ?? []).map((group) => ({ paper, group })));
    if (streams.length === 0) return [];
    return streams.length === 1 ? streams[0] : mergeStreams(streams[0], streams[1]);
  };
  const cycle2Days = teaching(cycle2);
  if (cycle2Days.length > 0) {
    put(layPair(
      cycle2Days,
      groupStream(practicalPapers),
      groupStream(theoryPapers),
      ({ item }) => assignment(item.paper, null, 'revision',
        `${shortOf(item.paper)} · ${item.group.label} — group-level pass: the shape of the block, not every line`,
        { cycle: 2, groupId: item.group.id, chapterSlugs: item.group.chapterSlugs ?? [] })
    ));
  }

  /* Revision cycle 3 — paper level, one-pagers only, in the last fortnight. */
  const cycle3Days = teaching(cycle3);
  if (cycle3Days.length > 0) {
    const ordered = [...papers].sort((a, b) => (a.number ?? 99) - (b.number ?? 99));
    const items = [];
    for (let k = 0; k < cycle3Days.length * 2; k += 1) items.push(ordered[k % ordered.length]);
    dealAcrossDays(items, cycle3Days.length).forEach((entries, i) => {
      dayAssignments.set(cycle3Days[i], entries.map(({ item: paper }) => assignment(
        paper, null, 'revision',
        `${shortOf(paper)} — one-pager pass: formats, formulas and section names, nothing new`,
        { cycle: 3, chapterSlugs: chaptersOf(paper).map((c) => c.slug) }
      )));
    });
  }

  /* Density, said out loud. The plan never silently thins a cycle to fit —
     if the days cannot hold the syllabus, that is the warning's job. */
  const chapterCount = papers.reduce((n, p) => n + chaptersOf(p).length, 0);
  if (studyDays.length > 0 && studyDays.length * 2 < chapterCount) {
    warnings.push(
      `The learning phase has ${studyDays.length} teaching days for ${chapterCount} chapters, so some days carry more than one new chapter. Chapters with the heaviest ICAI weightage keep their slots first; the light ones are the ones doubling up.`
    );
  }
  if (cycle1Days.length > 0 && chapterCount / cycle1Days.length > 6) {
    warnings.push(
      `Revision cycle 1 has ${cycle1Days.length} day${cycle1Days.length === 1 ? '' : 's'} for ${chapterCount} chapters — around ${Math.round(chapterCount / cycle1Days.length)} a day. At that rate it is a skim of your own notes, not a revision. Treat cycle 2 and the one-pagers as the real passes.`
    );
  }

  /* Mocks. Single-paper sittings first — weak papers before the rest — and
     the last two as full four-paper dress rehearsals. */
  const rotation = [...papers].sort((a, b) => (a.number ?? 99) - (b.number ?? 99));
  const weakFirst = [...rotation.filter((p) => weak.has(p.slug)), ...rotation.filter((p) => !weak.has(p.slug))];
  const mtpI = addDays(examStart, -22);
  const mtpII = addDays(examStart, -8);
  const mocks = mockDates.map((date, i) => {
    const full = mockDates.length >= 3 && i >= mockDates.length - 2;
    const paper = full ? null : weakFirst[i % weakFirst.length];
    const label = full
      ? 'Full dress rehearsal — all four papers to the clock, in the 2 PM slot if you can'
      : `${shortOf(paper)} — one full paper, timed, no notes`;
    const entry = { date, paperSlug: full ? 'full' : paper.slug, label };
    if (date === mtpI) entry.note = 'Lands in the usual ICAI MTP Series I window — sit the real MTP here if it is out.';
    if (date === mtpII) entry.note = 'Lands in the usual ICAI MTP Series II window — sit the real MTP here if it is out.';
    return entry;
  });
  const mockByDate = new Map(mocks.map((m) => [m.date, m]));

  /* Every day of the runway, then the exam window itself. */
  const kindOf = new Map();
  for (const d of phase1) kindOf.set(d, 'study');
  for (const d of cycle1) kindOf.set(d, 'revision1');
  for (const d of cycle2) kindOf.set(d, 'revision2');
  for (const d of cycle3) kindOf.set(d, 'revision3');

  const firstPaper = paperDates.length ? bySlug.get(paperDates[0].paperSlug) : null;
  const sessionLabel = input?.sessionLabel ?? 'papers begin at 2:00 PM';
  const planDays = [];

  for (const date of runway) {
    if (date === examEve) {
      planDays.push(dayRecord(date, 'gap', firstPaper
        ? [assignment(firstPaper, null, 'revision',
            `${shortOf(firstPaper)} one-pagers and your mistake notebook — nothing new`,
            { cycle: 3, chapterSlugs: chaptersOf(firstPaper).map((c) => c.slug) })]
        : [], 'The evening before the first paper. Finish while it is still light and sleep — the last hour of cramming has never bought a mark.'));
    } else if (bufferSet.has(date)) {
      planDays.push(dayRecord(date, 'buffer', [], 'Buffer day — catch up on anything that slipped, or rest. Both are the plan working.'));
    } else if (mockByDate.has(date)) {
      const mock = mockByDate.get(date);
      const paper = mock.paperSlug === 'full' ? null : bySlug.get(mock.paperSlug);
      planDays.push(dayRecord(date, 'mock',
        [assignment(paper, null, 'mock', mock.label, { scope: mock.paperSlug })], mock.note));
    } else if (minimumSet.has(date)) {
      planDays.push(dayRecord(date, 'minimum', [
        assignment(null, null, 'flashcards', 'Due flashcards — whatever the queue offers'),
        assignment(null, null, 'practice', 'Ten questions from yesterday’s mock mistakes'),
      ], 'The day after a mock is deliberately light: mark the paper, log what went wrong, stop there.'));
    } else {
      planDays.push(dayRecord(date, kindOf.get(date) ?? 'buffer', dayAssignments.get(date) ?? []));
    }
  }

  /* The exam window: paper days, and the gap days between them. */
  if (paperDates.length > 0) {
    for (const date of dateRange(examStart, examEnd)) {
      const today = paperDates.find((p) => p.date === date);
      if (today) {
        const paper = bySlug.get(today.paperSlug);
        planDays.push(dayRecord(date, 'exam', [assignment(paper, null, 'revision',
          `${shortOf(paper)} — the paper is today, ${sessionLabel}`,
          { chapterSlugs: chaptersOf(paper).map((c) => c.slug) })],
          'Morning: your one-pager for this paper only. Nothing new goes in on an exam day.'));
        continue;
      }
      const next = paperDates.find((p) => p.date > date);
      const paper = next ? bySlug.get(next.paperSlug) : null;
      planDays.push(dayRecord(date, 'gap', paper
        ? [assignment(paper, null, 'revision',
            `Gap day before ${shortOf(paper)} on ${humanDate(next.date)} — its one-pagers and its mistakes, nothing else`,
            { chapterSlugs: chaptersOf(paper).map((c) => c.slug) })]
        : [], paper
          ? 'One paper is behind you. It is finished, and reading about it changes nothing — the next one is the only one that can still move.'
          : null));
    }
  } else {
    planDays.push(dayRecord(examStart, 'exam', [], `First paper — ${sessionLabel}.`));
  }

  /* Weeks, Monday-anchored. */
  const weeks = [];
  let current = null;
  for (const day of planDays) {
    const monday = mondayOf(day.date);
    if (!current || current.startDate !== monday) {
      current = { startDate: monday, endDate: addDays(monday, 6), days: [] };
      weeks.push(current);
    }
    current.days.push(day);
  }

  const span = (list, name, key) => (list.length === 0 ? null : {
    name,
    key,
    startDate: list[0],
    endDate: list[list.length - 1],
    days: diffDays(list[0], list[list.length - 1]) + 1,
    workDays: list.length,
  });

  const phases = (compressed
    ? [
        span(cycle1, 'Cycle 1 · Chapter-level pass', 'revision1'),
        span(cycle2, 'Cycle 2 · Group-level pass', 'revision2'),
        span(cycle3, 'Cycle 3 · Paper one-pagers', 'revision3'),
      ]
    : [
        span(phase1, 'Phase 1 · Learning the syllabus', 'study'),
        span(cycle1, 'Phase 2 · Practice and revision cycle 1', 'practice'),
        span([...cycle2, ...cycle3], 'Phase 3 · Revision cycles 2 and 3', 'revision'),
      ]
  ).filter(Boolean);

  const summary = {
    startDate,
    examStart,
    examEnd,
    runwayDays: runway.length,
    workDays: work.length,
    bufferDays: bufferDays.length,
    bufferPct: runway.length ? Math.round((bufferDays.length / runway.length) * 100) : 0,
    studyDays: phase1.length,
    cycleDays: { one: cycle1.length, two: cycle2.length, three: cycle3.length },
    mockCount: mocks.length,
    compressed,
    mode,
    hoursPerWeek: Number.isFinite(hours) && hours > 0 ? hours : null,
    weakPapers: [...weak],
    chapterCount: papers.reduce((n, p) => n + chaptersOf(p).length, 0),
  };

  return {
    generatedFor: {
      attemptId: input?.attemptId ?? null,
      attemptName,
      examDate: examStart,
      startDate,
      mode,
      hoursPerWeek: summary.hoursPerWeek,
      weakPapers: [...weak],
    },
    phases,
    weeks,
    mocks,
    warnings,
    examWindow,
    summary,
  };
}

/** The plan's record for one ISO date, or null. Used by the dashboard. */
export function dayFor(plan, iso) {
  for (const week of plan?.weeks ?? []) {
    for (const day of week.days) if (day.date === iso) return day;
  }
  return null;
}

/** The minimum effective dose — the fallback any day can shrink to. */
export const MINIMUM_DOSE = {
  label: 'Due flashcards, then ten MCQs',
  minutes: '30 to 60 minutes',
  why: 'Short and done beats long and skipped. A day at the minimum keeps the spacing alive, which is the part that actually compounds.',
};
