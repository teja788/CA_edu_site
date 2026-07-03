/**
 * Flashcard decks (plan Phase 1): accounting standards, law sections,
 * formulas — quick-recall facts that spaced repetition holds best.
 * All original phrasing; attempt-tagged like everything else.
 */
export const decks = [
  {
    id: 'as-numbers',
    name: 'Accounting Standards — quick recall',
    paper: 'P1 · Adv. Accounting',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    cards: [
      { id: 'as-1', front: 'AS 1 covers…', back: 'Disclosure of Accounting Policies — fundamental assumptions: going concern, consistency, accrual.' },
      { id: 'as-2', front: 'AS 2 covers… and its core rule is…', back: 'Valuation of Inventories — value at the LOWER of cost and net realisable value.' },
      { id: 'as-3', front: 'AS 3 covers… with which three activity heads?', back: 'Cash Flow Statements — operating, investing and financing activities.' },
      { id: 'as-10', front: 'AS 10 covers…', back: 'Property, Plant and Equipment — recognition at cost; subsequent cost model or revaluation model.' },
      { id: 'as-26', front: 'AS 26 covers… and its rule on self-generated goodwill is…', back: 'Intangible Assets — self-generated goodwill is NEVER recognised; record goodwill only when consideration is paid.' },
    ],
  },
  {
    id: 'partnership-formulas',
    name: 'Partnership — formulas & rules',
    paper: 'P1 · Ch 4',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    cards: [
      { id: 'pf-1', front: 'Sacrificing ratio =', back: 'Old ratio − New ratio. Equals the old ratio ONLY when the question is silent on how the new share is acquired.' },
      { id: 'pf-2', front: 'Gaining ratio =', back: 'New ratio − Old ratio (used on retirement — continuing partners compensate the outgoing partner in this ratio).' },
      { id: 'pf-3', front: 'Revaluation profit on admission goes to…', back: 'Old partners in the OLD ratio — the value change happened during their tenure.' },
      { id: 'pf-4', front: 'Goodwill premium brought by the new partner is shared by…', back: 'Old partners in the SACRIFICING ratio.' },
      { id: 'pf-5', front: 'Hidden goodwill on admission =', back: "(New partner's capital ÷ new partner's share) − total capital of the new firm including the new partner's capital." },
    ],
  },
];

export const allCards = decks.flatMap((d) => d.cards.map((c) => ({ ...c, deckId: d.id, deckName: d.name })));
