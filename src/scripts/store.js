/**
 * Local-first user state (plan §6.3): no accounts, no server.
 * Everything lives in localStorage under the `adh-` prefix.
 */

const KEY = 'adh-progress';
const MOCKS_KEY = 'adh-mocks';

/**
 * Schema version. 1 = the original shape (no `version` field). 2 adds:
 * `attempt` (chosen exam attempt + its date), `masteryDays` (distinct-day
 * evidence for successive relearning) and per-mistake `due` / `sure` / `reps`
 * so the notebook is a real due queue.
 */
export const SCHEMA_VERSION = 2;

const DAY = 86400000;

/** v1 → v2, in place. Fills new fields with defaults; loses nothing. */
function migrate(state) {
  if (state.version === SCHEMA_VERSION) return state;

  // Existing mistakes are all immediately eligible — nobody should have to
  // wait for a notebook they already filled.
  const now = Date.now();
  state.mistakes = (state.mistakes ?? []).map((m) => ({ reps: 0, due: now, ...m }));

  // masteryAt held ONE date per topic; masteryDays holds the distinct days.
  state.masteryDays = state.masteryDays ?? {};
  for (const [topicId, day] of Object.entries(state.masteryAt ?? {})) {
    if (!Array.isArray(state.masteryDays[topicId]) && day) state.masteryDays[topicId] = [day];
  }
  // Topics already at 3 keep level 3 — levels never go down.

  state.attempt = state.attempt ?? null;
  state.version = SCHEMA_VERSION;
  return state;
}

function read() {
  let raw;
  try {
    raw = JSON.parse(localStorage.getItem(KEY)) ?? {};
  } catch {
    return { version: SCHEMA_VERSION };
  }
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return { version: SCHEMA_VERSION };
  if (raw.version === SCHEMA_VERSION) return raw;
  const hadData = Object.keys(raw).length > 0;
  const migrated = migrate(raw);
  // Persist the migration once, but never create a state file for a brand-new
  // visitor who has only ever read.
  if (hadData) write(migrated);
  return migrated;
}

function write(state) {
  // Safari private mode / full quota throws — losing one update is fine,
  // crashing mid-quiz is not.
  try {
    state.version = SCHEMA_VERSION;
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* storage unavailable */
  }
}

/** Mastery: 0 not started · 1 familiar · 2 proficient · 3 mastered */
export function getMastery(topicId) {
  return read().mastery?.[topicId] ?? 0;
}

/**
 * Successive relearning: level 3 is not three corrects in one sitting, it is
 * proficiency shown on three DIFFERENT days. `masteryDays[topicId]` collects
 * the distinct days that carried level-≥2 evidence (last 5 kept).
 * Levels never go down.
 */
export function bumpMastery(topicId, level) {
  const state = read();
  state.mastery = state.mastery ?? {};
  state.masteryAt = state.masteryAt ?? {};
  state.masteryDays = state.masteryDays ?? {};
  const prev = state.mastery[topicId] ?? 0;
  let next = Math.max(prev, level);
  const today = new Date().toDateString();

  if (level >= 2) {
    const days = Array.isArray(state.masteryDays[topicId]) ? state.masteryDays[topicId] : [];
    if (!days.includes(today)) days.push(today);
    state.masteryDays[topicId] = days.slice(-5);
    if (state.masteryDays[topicId].length >= 3) next = Math.max(next, 3);
    state.masteryAt[topicId] = today;
  }

  state.mastery[topicId] = Math.max(prev, next);
  write(state);
}

/** Distinct days of level-≥2 evidence for a topic — 3 of them means mastered. */
export function getMasteryDays(topicId) {
  const days = read().masteryDays?.[topicId];
  return Array.isArray(days) ? days.length : 0;
}

/**
 * Paper progress: topics at Proficient or above, over the paper's tracked
 * topics. `prefixes` — one or more mastery-key prefixes belonging to the
 * paper (e.g. ['i1-', 'p1-ch4-'] for Inter P1 chapters + the partnership
 * refresher topics).
 */
export function getPaperProgress(prefixes, totalTopics) {
  const list = Array.isArray(prefixes) ? prefixes : [prefixes];
  const mastery = read().mastery ?? {};
  const done = Object.entries(mastery).filter(
    ([k, v]) => list.some((p) => k.startsWith(p)) && v >= 2
  ).length;
  const total = totalTopics || 0;
  return { done, total, pct: total ? Math.min(100, Math.round((done / total) * 100)) : 0 };
}

/* ── Exam attempt ─────────────────────────────────────────────────────── */

/** End of the exam day, IST — a card due that morning still counts. */
function examMs(isoDate) {
  if (!isoDate) return null;
  const t = new Date(`${isoDate}T23:59:59+05:30`).getTime();
  return Number.isFinite(t) ? t : null;
}

/**
 * Remember which attempt the student is sitting. `examDate` is resolved by
 * the caller at set time (from foundationAttempts, or a date the student
 * typed in for an attempt ICAI has not notified yet) and stored as an ISO
 * date so the scheduler never has to look it up again.
 */
export function setAttempt(attemptId, examDate) {
  const state = read();
  state.attempt = attemptId
    ? { id: attemptId, examDate: examDate ?? null, setAt: Date.now() }
    : null;
  write(state);
  return state.attempt;
}

export function getAttempt() {
  return read().attempt ?? null;
}

/** Whole days from now to the exam, or null if no dated attempt is set. */
export function getDaysToExam() {
  const at = read().attempt;
  const ms = examMs(at?.examDate);
  if (!ms) return null;
  return Math.ceil((ms - Date.now()) / DAY);
}

/**
 * Longest interval (days) a card may be scheduled for. With a dated attempt
 * set, nothing may land after the exam; inside the last 30 days every card
 * cycles at least once more (quarter of the time remaining).
 */
function intervalCap(attempt) {
  const ms = examMs(attempt?.examDate);
  if (!ms) return 365;
  const daysLeft = (ms - Date.now()) / DAY;
  if (daysLeft <= 0) return 365; // attempt already sat — back to normal spacing
  let cap = Math.min(365, daysLeft);
  if (daysLeft <= 30) cap = Math.min(cap, Math.max(2, daysLeft / 4));
  return cap;
}

/* ── Mistake notebook — a due queue, not a graveyard ──────────────────── */

/** 3–7 days out: far enough to be a real retrieval, near enough to matter. */
function mistakeDue() {
  return Date.now() + (3 + Math.random() * 4) * DAY;
}

/**
 * Wrong answers auto-collected, tagged by topic. `sure` records whether the
 * student had said they were confident — optional, older callers omit it.
 */
export function addMistake({ questionId, topic, sure }) {
  const state = read();
  state.mistakes = state.mistakes ?? [];
  const existing = state.mistakes.find((m) => m.questionId === questionId);
  if (existing) {
    if (typeof sure === 'boolean') existing.sure = sure;
  } else {
    state.mistakes.unshift({
      questionId,
      topic,
      at: Date.now(),
      due: mistakeDue(),
      sure: typeof sure === 'boolean' ? sure : undefined,
      reps: 0,
    });
    state.mistakes = state.mistakes.slice(0, 200);
  }
  write(state);
}

export function clearMistake(questionId) {
  const state = read();
  state.mistakes = (state.mistakes ?? []).filter((m) => m.questionId !== questionId);
  write(state);
}

export function getMistakes() {
  return read().mistakes ?? [];
}

/**
 * Mistakes ready for a re-test. Confident-but-wrong first — those are the
 * beliefs that will cost marks in the hall — then oldest first.
 */
export function getDueMistakes() {
  const now = Date.now();
  return (read().mistakes ?? [])
    .filter((m) => (m.due ?? m.at ?? 0) <= now)
    .sort((a, b) => {
      const sureGap = (b.sure === true ? 1 : 0) - (a.sure === true ? 1 : 0);
      if (sureGap !== 0) return sureGap;
      return (a.at ?? a.due ?? 0) - (b.at ?? b.due ?? 0);
    });
}

/** Retested: right → it leaves the notebook · wrong → back in 3–7 days. */
export function rescheduleMistake(questionId, correctOnRetest) {
  if (correctOnRetest) {
    clearMistake(questionId);
    return null;
  }
  const state = read();
  const m = (state.mistakes ?? []).find((x) => x.questionId === questionId);
  if (!m) return null;
  m.due = mistakeDue();
  m.reps = (m.reps ?? 0) + 1;
  write(state);
  return m;
}

/* ── History ─────────────────────────────────────────────────────────── */

/** Quiz history for the "This week" facts. `sure` is optional. */
export function recordAnswer({ questionId, correct, sure }) {
  const state = read();
  state.history = state.history ?? [];
  const entry = { questionId, correct, at: Date.now() };
  if (typeof sure === 'boolean') entry.sure = sure;
  state.history.push(entry);
  state.history = state.history.slice(-1000);
  write(state);
}

/**
 * Confidence calibration: accuracy when the student said "Sure" against
 * accuracy when they said "Not sure". Only answers that carry the tag count.
 */
export function getCalibration() {
  const tagged = (read().history ?? []).filter((h) => typeof h.sure === 'boolean');
  const tally = (list) => {
    const correct = list.filter((h) => h.correct).length;
    return { n: list.length, correct, pct: list.length ? Math.round((correct / list.length) * 100) : 0 };
  };
  const sure = tally(tagged.filter((h) => h.sure));
  const unsure = tally(tagged.filter((h) => !h.sure));
  const gap = sure.pct - unsure.pct;
  let verdict = 'calibrated';
  if (sure.n > 0 && unsure.n > 0) {
    if (unsure.pct >= 70 && gap < 15) verdict = 'underconfident';
    else if (sure.pct < 75 || gap < 15) verdict = 'overconfident';
  }
  return { tagged: tagged.length, sure, unsure, gap, verdict };
}

/** Timestamp of the last recorded answer, or null. */
export function getLastActivity() {
  const history = read().history ?? [];
  return history.length ? history[history.length - 1].at : null;
}

/**
 * Spaced-repetition scheduler for flashcards — a lightweight
 * SM-2/FSRS-style algorithm (plan §6.3 suggests ts-fsrs; this keeps v1
 * dependency-free with the same behaviour class: expanding intervals,
 * ease adjusted by rating). State: { due, ivl (days), ease, reps }.
 */
export function getCardState(cardId) {
  return read().fsrs?.[cardId] ?? null;
}

export function rateCard(cardId, rating) {
  // rating: 'again' | 'hard' | 'good' | 'easy'
  const state = read();
  state.fsrs = state.fsrs ?? {};
  const prev = state.fsrs[cardId] ?? { ivl: 0, ease: 2.5, reps: 0 };
  let { ivl, ease } = prev;

  if (rating === 'again') {
    ease = Math.max(1.3, ease - 0.2);
    ivl = 0; // due again in 10 minutes
  } else if (rating === 'hard') {
    ease = Math.max(1.3, ease - 0.15);
    ivl = Math.max(1, ivl * 1.2);
  } else if (rating === 'good') {
    ivl = ivl === 0 ? 1 : ivl * ease;
  } else {
    ease = ease + 0.15;
    ivl = ivl === 0 ? 4 : ivl * ease * 1.3;
  }
  // No attempt set → the plain 365-day ceiling. With one, nothing is ever
  // scheduled past the exam.
  ivl = Math.min(ivl, intervalCap(state.attempt));

  const dueMs = rating === 'again' ? 10 * 60 * 1000 : ivl * DAY;
  state.fsrs[cardId] = { ivl, ease, reps: prev.reps + 1, due: Date.now() + dueMs };
  write(state);
  return state.fsrs[cardId];
}

/** Cards due now: never-seen cards are always due. */
export function getDueCards(allCards) {
  const fsrs = read().fsrs ?? {};
  const now = Date.now();
  return allCards.filter((c) => {
    const s = fsrs[c.id];
    return !s || s.due <= now;
  });
}

export function getWeekStats() {
  const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
  const recent = (read().history ?? []).filter((h) => h.at >= weekAgo);
  return {
    attempted: recent.length,
    correct: recent.filter((h) => h.correct).length,
  };
}

/* ── Backup: export / import ─────────────────────────────────────────── */

/** Everything this browser holds, as a plain object ready for JSON. */
export function exportProgress() {
  const progress = read();
  let mocks = null;
  try {
    const raw = localStorage.getItem(MOCKS_KEY);
    if (raw) mocks = JSON.parse(raw);
  } catch {
    /* unreadable — the rest of the backup is still worth having */
  }
  const out = {
    app: 'adhyayan',
    version: progress.version ?? SCHEMA_VERSION,
    exportedAt: new Date().toISOString(),
    progress,
  };
  if (mocks !== null) out.mocks = mocks;
  return out;
}

const KNOWN_KEYS = ['mastery', 'masteryDays', 'masteryAt', 'mistakes', 'history', 'fsrs', 'attempt'];

/** A file is a backup if it carries a version and at least one known key. */
export function validateBackup(data) {
  if (!data || typeof data !== 'object') return null;
  const progress = data.progress && typeof data.progress === 'object' ? data.progress : data;
  const version = data.version ?? progress.version;
  if (!version) return null;
  if (!KNOWN_KEYS.some((k) => progress[k] != null)) return null;
  return { progress, mocks: data.mocks ?? null };
}

function unionBy(local, imported, keyOf) {
  const out = new Map();
  for (const item of Array.isArray(local) ? local : []) out.set(keyOf(item), item);
  // Imported wins on conflict: a restore is a deliberate act.
  for (const item of Array.isArray(imported) ? imported : []) out.set(keyOf(item), item);
  return [...out.values()];
}

/**
 * Conservative merge — a restore never deletes what this browser already
 * knows. Mastery takes the higher level; lists union by id/timestamp.
 */
export function importProgress(data) {
  const parsed = validateBackup(data);
  if (!parsed) return null;
  const incoming = migrate({ ...parsed.progress });
  const state = read();

  state.mastery = state.mastery ?? {};
  for (const [k, v] of Object.entries(incoming.mastery ?? {})) {
    state.mastery[k] = Math.max(state.mastery[k] ?? 0, v ?? 0);
  }

  state.masteryDays = state.masteryDays ?? {};
  for (const [k, days] of Object.entries(incoming.masteryDays ?? {})) {
    const merged = [...new Set([...(state.masteryDays[k] ?? []), ...(Array.isArray(days) ? days : [])])];
    state.masteryDays[k] = merged.slice(-5);
  }
  state.masteryAt = { ...(state.masteryAt ?? {}), ...(incoming.masteryAt ?? {}) };

  state.mistakes = unionBy(state.mistakes, incoming.mistakes, (m) => m.questionId).slice(0, 200);
  state.history = unionBy(state.history, incoming.history, (h) => `${h.questionId}|${h.at}`)
    .sort((a, b) => (a.at ?? 0) - (b.at ?? 0))
    .slice(-1000);
  state.fsrs = { ...(state.fsrs ?? {}), ...(incoming.fsrs ?? {}) };
  if (incoming.attempt) state.attempt = incoming.attempt;

  write(state);

  if (parsed.mocks != null) {
    try {
      const localRaw = localStorage.getItem(MOCKS_KEY);
      const local = localRaw ? JSON.parse(localRaw) : null;
      let merged = parsed.mocks;
      if (Array.isArray(local) && Array.isArray(parsed.mocks)) {
        merged = unionBy(local, parsed.mocks, (m) => m?.id ?? JSON.stringify(m));
      } else if (local && typeof local === 'object' && parsed.mocks && typeof parsed.mocks === 'object') {
        merged = { ...local, ...parsed.mocks };
      }
      localStorage.setItem(MOCKS_KEY, JSON.stringify(merged));
    } catch {
      /* mocks are a bonus — never fail the restore over them */
    }
  }
  return state;
}
