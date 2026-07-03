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
  localStorage.setItem(KEY, JSON.stringify(state));
}

/** Mastery: 0 not started · 1 familiar · 2 proficient · 3 mastered */
export function getMastery(topicId) {
  return read().mastery?.[topicId] ?? 0;
}

export function bumpMastery(topicId, level) {
  const state = read();
  state.mastery = state.mastery ?? {};
  state.mastery[topicId] = Math.max(state.mastery[topicId] ?? 0, level);
  write(state);
}

export function getPaperProgress(paperId, totalTopics) {
  const mastery = read().mastery ?? {};
  const done = Object.entries(mastery).filter(([k, v]) => k.startsWith(paperId) && v >= 2).length;
  return { done, total: totalTopics, pct: Math.round((done / totalTopics) * 100) };
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

export function getWeekStats() {
  const weekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
  const recent = (read().history ?? []).filter((h) => h.at >= weekAgo);
  return {
    attempted: recent.length,
    correct: recent.filter((h) => h.correct).length,
  };
}
