/**
 * Local-first user state (plan §6.3): no accounts, no server.
 * Everything lives in localStorage under the `adh-` prefix.
 */

const KEY = 'adh-progress';

function read() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) ?? {};
  } catch {
    return {};
  }
}

function write(state) {
  // Safari private mode / full quota throws — losing one update is fine,
  // crashing mid-quiz is not.
  try {
    localStorage.setItem(KEY, JSON.stringify(state));
  } catch {
    /* storage unavailable */
  }
}

/** Mastery: 0 not started · 1 familiar · 2 proficient · 3 mastered */
export function getMastery(topicId) {
  return read().mastery?.[topicId] ?? 0;
}

export function bumpMastery(topicId, level) {
  const state = read();
  state.mastery = state.mastery ?? {};
  state.masteryAt = state.masteryAt ?? {};
  const prev = state.mastery[topicId] ?? 0;
  let next = Math.max(prev, level);
  // Mastered (3) needs spaced evidence: proficiency demonstrated again on a
  // later day, not three quick corrects in one sitting.
  const today = new Date().toDateString();
  if (prev >= 2 && level >= 2 && state.masteryAt[topicId] && state.masteryAt[topicId] !== today) {
    next = 3;
  }
  if (level >= 2) state.masteryAt[topicId] = today;
  state.mastery[topicId] = next;
  write(state);
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

/** Mistake notebook: wrong answers auto-collected, tagged by topic. */
export function addMistake({ questionId, topic }) {
  const state = read();
  state.mistakes = state.mistakes ?? [];
  if (!state.mistakes.some((m) => m.questionId === questionId)) {
    state.mistakes.unshift({ questionId, topic, at: Date.now() });
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

/** Quiz history for the "This week" facts. */
export function recordAnswer({ questionId, correct }) {
  const state = read();
  state.history = state.history ?? [];
  state.history.push({ questionId, correct, at: Date.now() });
  state.history = state.history.slice(-1000);
  write(state);
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
  ivl = Math.min(ivl, 365);

  const dueMs = rating === 'again' ? 10 * 60 * 1000 : ivl * 86400000;
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
