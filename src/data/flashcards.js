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
  {
    id: 'foundation-depreciation',
    name: 'Depreciation & Amortisation — formulas & rules',
    paper: 'Foundation P1 · Ch 5',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    cards: [
      { id: 'fdep-1', front: 'Depreciable amount =', back: 'Cost − Residual value. This is what gets spread over the useful life — the expected recovery at the end is never depreciated.' },
      { id: 'fdep-2', front: 'SLM yearly charge =', back: '(Cost − Residual value) ÷ Useful life. Same amount every year; book value lands exactly on residual value at the end.' },
      { id: 'fdep-3', front: 'WDV yearly charge is computed on…', back: 'The OPENING carrying amount (book value), not on cost. The charge shrinks every year and the value never reaches zero.' },
      { id: 'fdep-4', front: 'WDV rate needed to reach a residual value in n years =', back: '1 − (Residual ÷ Cost)^(1/n).' },
      { id: 'fdep-5', front: 'Units-of-production charge =', back: '(Cost − Residual) × units produced this year ÷ total expected lifetime units. Use when wear follows OUTPUT, not time.' },
      { id: 'fdep-6', front: 'Profit or loss on sale of an asset is measured against…', back: 'The written-down value on the date of sale — never against original cost. Sold below cost but above WDV = still a profit.' },
      { id: 'fdep-7', front: 'Depreciation is a process of ______, not ______.', back: 'Allocation, not valuation. It spreads cost; it does not track market value.' },
      { id: 'fdep-8', front: 'Is depreciation charged in a loss year? On an idle machine?', back: 'Yes and yes. It does not depend on profits or usage — time and obsolescence run regardless.' },
      { id: 'fdep-9', front: 'The three causes of depreciation are…', back: 'Wear and tear · passage of time (rights expiring) · obsolescence (new technology makes the asset uneconomic).' },
      { id: 'fdep-10', front: 'Revision of useful life or residual value: which years change?', back: 'Only FUTURE years (prospective). Spread (carrying amount − revised residual) over the remaining revised life. Past years are never reopened.' },
      { id: 'fdep-11', front: 'Change of depreciation method (WDV → SLM) is treated as…', back: 'A change in accounting ESTIMATE under AS 10 — applied prospectively from the current carrying amount. (Retrospective recomputation is the old AS 6 treatment.)' },
      { id: 'fdep-12', front: 'Depreciation starts from which date?', back: 'The date the asset is READY/available for use — not the delivery date, and not the day production actually starts.' },
      { id: 'fdep-13', front: 'Which asset is never depreciated, and why?', back: 'Freehold land — unlimited useful life, nothing to spread. (Leasehold land IS amortised over the lease term.)' },
      { id: 'fdep-14', front: 'Depreciation ÷ amortisation ÷ depletion apply respectively to…', back: 'Tangible assets · intangible assets (AS 26) · natural resources (mines, quarries).' },
      { id: 'fdep-15', front: 'Under the Provision for Depreciation method, the asset account shows…', back: 'Original COST, unchanged. Accumulated depreciation sits in the separate provision account; WDV appears only as the net figure in the balance sheet.' },
      { id: 'fdep-16', front: 'Direct-method yearly journal entry for depreciation:', back: 'Depreciation A/c Dr → To Asset A/c; then P&L A/c Dr → To Depreciation A/c. No cash moves — ever.' },
      { id: 'fdep-17', front: 'Which purchase-time costs are capitalised into an asset’s cost?', back: 'Everything to bring it to location and working condition: freight, installation, pre-use overhaul, first registration — LESS trade discount. Running costs (fuel, salaries, annual maintenance) are revenue expenses.' },
      { id: 'fdep-18', front: 'For companies, indicative useful lives come from…', back: 'Schedule II of the Companies Act 2013 ("Useful Lives to Compute Depreciation", see s.123). Schedule III is the financial-statement FORMAT — a classic swap in MCQs.' },
    ],
  },
];

export const allCards = decks.flatMap((d) => d.cards.map((c) => ({ ...c, deckId: d.id, deckName: d.name })));
