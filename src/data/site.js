/**
 * Canonical data for the CA Intermediate launch (plan §6.2).
 * Attempt-tagging (`applicableAttempts`, `lawAsOnDate`) is mandatory on
 * everything volatile — tax/law content without it must not merge.
 *
 * All ICAI resources are LINKS to official sources, never re-hosted copies.
 */

// Full attempt records (next three attempts, with verification TODOs) live in
// intermediate.js `attempts`; this is the site-wide current-attempt pointer.
// NOTE: the Income-tax Act 2025 / Finance Act 2026 applies only from the
// May 2027 exams (ICAI announcement 08-12-2025); Sept 2026 stays on the
// 1961 Act as amended by the Finance Act 2025.
export const attempt = {
  id: 'sept-2026',
  name: 'Sept 2026',
  beginsOn: '2026-09-08',
  beginsLabel: '8 Sept 2026',
  applicableFinanceAct: 'Finance Act 2025 (Income-tax Act, 1961 · AY 2026-27)',
};

export const level = {
  id: 'intermediate',
  name: 'CA Intermediate',
  groups: [
    { id: 1, name: 'Group I' },
    { id: 2, name: 'Group II' },
  ],
};

export const papers = [
  {
    id: 'p1',
    slug: 'advanced-accounting',
    group: 1,
    number: 1,
    name: 'Advanced Accounting',
    shortName: 'Adv. Accounting',
    marks: 100,
    pattern: { mcqPct: 30, descriptivePct: 70, negativeMarking: false },
    chapters: 15,
    topics: 96,
    status: 'live',
  },
  {
    id: 'p2',
    slug: 'corporate-and-other-laws',
    group: 1,
    number: 2,
    name: 'Corporate & Other Laws',
    shortName: 'Corporate Laws',
    marks: 100,
    pattern: { mcqPct: 30, descriptivePct: 70, negativeMarking: false },
    chapters: 15,
    topics: 74,
    status: 'coming-soon',
  },
  {
    id: 'p3',
    slug: 'taxation',
    group: 1,
    number: 3,
    name: 'Taxation (Income Tax + GST)',
    shortName: 'Taxation',
    marks: 100,
    pattern: { mcqPct: 30, descriptivePct: 70, negativeMarking: false },
    chapters: 24,
    topics: 110,
    status: 'coming-soon',
  },
  {
    id: 'p4',
    slug: 'cost-and-management-accounting',
    group: 2,
    number: 4,
    name: 'Cost & Management Accounting',
    shortName: 'Cost Mgmt',
    marks: 100,
    pattern: { mcqPct: 30, descriptivePct: 70, negativeMarking: false },
    chapters: 15,
    topics: 88,
    status: 'coming-soon',
  },
  {
    id: 'p5',
    slug: 'auditing-and-ethics',
    group: 2,
    number: 5,
    name: 'Auditing & Ethics',
    shortName: 'Auditing',
    marks: 100,
    pattern: { mcqPct: 30, descriptivePct: 70, negativeMarking: false },
    chapters: 11,
    topics: 68,
    status: 'coming-soon',
  },
  {
    id: 'p6',
    slug: 'fm-and-sm',
    group: 2,
    number: 6,
    name: 'Financial Management & Strategic Management',
    shortName: 'FM & SM',
    marks: 100,
    pattern: { mcqPct: 30, descriptivePct: 70, negativeMarking: false },
    chapters: 14,
    topics: 90,
    status: 'coming-soon',
  },
];

/**
 * Paper 1 chapter map (seed — sectioned as in the hub template).
 * Only Ch 4 "Partnership accounts" carries live topics/notes so far.
 */
export const paper1Sections = [
  {
    name: 'Section A · Accounting standards',
    chapters: [
      { number: 1, slug: 'intro-accounting-standards', name: 'Introduction to Accounting Standards', draft: false },
      { number: 2, slug: 'framework-fs', name: 'Framework for preparation of FS', draft: false },
      { number: 3, slug: 'as-1-2-3', name: 'AS 1, 2, 3 — Disclosure, Inventories, Cash flow', draft: false },
    ],
  },
  {
    name: 'Section B · Special transactions',
    chapters: [
      {
        number: 4,
        slug: 'partnership-accounts',
        name: 'Partnership accounts',
        draft: false,
        topics: [
          { slug: 'goodwill-nature-valuation', name: 'Goodwill: nature & valuation', hasNotes: true },
          { slug: 'admission-of-a-partner', name: 'Admission of a partner', hasNotes: true },
          { slug: 'retirement-of-a-partner', name: 'Retirement of a partner', hasNotes: true },
        ],
      },
      { number: 5, slug: 'branch-accounting', name: 'Branch accounting', draft: true },
    ],
  },
  {
    name: 'Section C · Company accounts (ICAI Module 3)',
    chapters: [
      {
        number: 1,
        slug: 'introduction-to-accounting-standards',
        name: 'Introduction to Accounting Standards',
        draft: true,
        notesHref: '/intermediate/advanced-accounting/introduction-to-accounting-standards/',
      },
      {
        number: 2,
        slug: 'framework-for-preparation-and-presentation-of-fs',
        name: 'Framework for Preparation & Presentation of Financial Statements',
        draft: true,
        notesHref: '/intermediate/advanced-accounting/framework-for-preparation-and-presentation-of-fs/',
      },
      {
        number: 3,
        slug: 'applicability-of-accounting-standards',
        name: 'Applicability of Accounting Standards',
        draft: true,
        notesHref: '/intermediate/advanced-accounting/applicability-of-accounting-standards/',
      },
      {
        number: 11,
        slug: 'financial-statements-of-companies',
        name: 'Financial Statements of Companies',
        draft: true,
        notesHref: '/intermediate/advanced-accounting/financial-statements-of-companies/',
      },
      {
        number: 12,
        slug: 'buyback-of-securities',
        name: 'Buyback of Securities',
        draft: true,
        notesHref: '/intermediate/advanced-accounting/buyback-of-securities/',
      },
      {
        number: 13,
        slug: 'amalgamation-of-companies',
        name: 'Amalgamation of Companies',
        draft: true,
        notesHref: '/intermediate/advanced-accounting/amalgamation-of-companies/',
      },
      {
        number: 14,
        slug: 'internal-reconstruction',
        name: 'Internal Reconstruction',
        draft: true,
        notesHref: '/intermediate/advanced-accounting/internal-reconstruction/',
      },
      {
        number: 15,
        slug: 'branches-including-foreign',
        name: 'Accounting for Branches including Foreign Branches',
        draft: true,
        notesHref: '/intermediate/advanced-accounting/branches-including-foreign/',
      },
    ],
  },
];

/**
 * ResourceLink — deep links to official free sources only.
 * `requiresLogin`: free ICAI student login (registration no. + DOB).
 */
export const paper1Resources = [
  {
    kind: 'SM',
    // Old /post/study-material-intermediate URL now 404s — ICAI reshuffle.
    title: 'Study Material — Paper 1 Advanced Accounting (May 2026 onwards)',
    url: 'https://www.icai.org/post/bos-int-p1-may2026-exam',
    host: 'icai.org',
    requiresLogin: false,
    lastChecked: '3 Jul 2026',
  },
  {
    kind: 'RTP',
    title: 'RTP — Sept 2026',
    url: 'https://boslive.icai.org/',
    host: 'boslive.icai.org',
    requiresLogin: true,
    lastChecked: '28 Jun 2026',
  },
  {
    kind: 'MTP',
    title: 'MTP Series I — Sept 2026',
    url: 'https://boslive.icai.org/',
    host: 'boslive.icai.org',
    requiresLogin: true,
    lastChecked: '21 Jun 2026',
  },
  {
    kind: 'PastPaper',
    title: 'Past question papers + suggested answers',
    url: 'https://www.icai.org/post/question-papers-suggested-answers',
    host: 'icai.org',
    requiresLogin: false,
    lastChecked: '28 Jun 2026',
  },
  {
    kind: 'LVC',
    title: 'ICAI CA Tube — free live/recorded classes (Paper 1 playlist)',
    url: 'https://www.youtube.com/@icaicatube',
    host: 'youtube.com · public',
    requiresLogin: false,
    lastChecked: '28 Jun 2026',
  },
];

/**
 * Question bank — 100% original questions (plan §3.2).
 * Every option carries an explanation of WHY it is right/wrong,
 * and the correct option links back to the exact note section.
 */
export const questions = [
  {
    id: 'q-adm-001',
    topic: 'Ch 4 · Partnership · Admission of a partner',
    type: 'mcq',
    stem: 'A and B share profits in the ratio 3:2. C is admitted for a 1/5th share, which he acquires equally from A and B. What is the new profit-sharing ratio?',
    options: [
      { key: 'A', text: '3 : 2 : 1', explanation: 'This keeps the old ratio and bolts C on — but A and B each gave up 1/10, so their shares must shrink.' },
      { key: 'B', text: '5 : 3 : 2', explanation: 'C takes 1/10 from each: A = 3/5 − 1/10 = 5/10, B = 2/5 − 1/10 = 3/10, C = 2/10 → 5:3:2.' },
      { key: 'C', text: '12 : 8 : 5', explanation: 'This comes from taking C’s 1/5 out of the combined firm first (old ratio × 4/5). That method applies only when the question doesn’t say whom C acquires from — here it says “equally from A and B”.' },
      { key: 'D', text: '2 : 2 : 1', explanation: 'Equal-ish shares look plausible but have no basis in the working — always compute, never eyeball.' },
    ],
    correct: 'B',
    readLink: { label: 'Read: Sacrificing ratio, §1 →', href: '/intermediate/advanced-accounting/partnership-accounts/admission-of-a-partner/#s1' },
    difficulty: 'medium',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '14 Jun 2026',
  },
  {
    id: 'q-adm-002',
    topic: 'Ch 4 · Partnership · Admission of a partner',
    type: 'mcq',
    stem: 'Revaluation profit arising on admission of a partner is shared by:',
    options: [
      { key: 'A', text: 'Old partners, in the old ratio', explanation: 'The value change happened during their tenure, so it belongs to the old partners in the old ratio.' },
      { key: 'B', text: 'All partners, in the new ratio', explanation: 'The new partner wasn’t there when values changed — no claim.' },
      { key: 'C', text: 'Old partners, in the sacrificing ratio', explanation: 'Sacrificing ratio is for goodwill premium — a different adjustment.' },
      { key: 'D', text: 'The new partner alone', explanation: 'The incoming partner never bears pre-admission gains or losses.' },
    ],
    correct: 'A',
    readLink: { label: 'Read: Revaluation, §3 →', href: '/intermediate/advanced-accounting/partnership-accounts/admission-of-a-partner/#s3' },
    difficulty: 'easy',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '14 Jun 2026',
  },
  {
    id: 'q-adm-003',
    topic: 'Ch 4 · Partnership · Admission of a partner',
    type: 'mcq',
    stem: 'X and Y share profits 7:3. Z is admitted and the new ratio is agreed as 5:3:2. The sacrificing ratio of X and Y is:',
    options: [
      { key: 'A', text: '7 : 3', explanation: 'That is the old ratio. Sacrifice equals old ratio only when the question is silent on how the new share is acquired — here the new ratio is given, so compute the difference.' },
      { key: 'B', text: '2 : 0 (X alone sacrifices)', explanation: 'X: 7/10 − 5/10 = 2/10. Y: 3/10 − 3/10 = 0. Only X sacrifices, so the whole goodwill premium goes to X.' },
      { key: 'C', text: '1 : 1', explanation: 'Equal sacrifice happens only when the question says the share is acquired equally — not here.' },
      { key: 'D', text: '5 : 3', explanation: 'That is the new inter-se ratio of X and Y, not what they gave up.' },
    ],
    correct: 'B',
    readLink: { label: 'Read: Sacrificing ratio, §1 →', href: '/intermediate/advanced-accounting/partnership-accounts/admission-of-a-partner/#s1' },
    difficulty: 'medium',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '14 Jun 2026',
  },
  {
    id: 'q-as2-001',
    topic: 'Ch 3 · AS 2 · Inventories',
    type: 'mcq',
    stem: 'Raw material was bought at ₹100/kg; its replacement cost has fallen to ₹80/kg. The finished goods made from it still sell above their total cost. Under AS 2, the raw material is valued at:',
    options: [
      { key: 'A', text: '₹80 — always write down to NRV', explanation: 'AS 2 does NOT write down raw materials when the finished goods they go into will sell at or above cost.' },
      { key: 'B', text: '₹100 — no write-down here', explanation: 'Correct. Raw materials are written down below cost only when the finished products will sell below cost; here they don’t, so cost stands.' },
      { key: 'C', text: '₹90 — average of the two', explanation: 'Averaging has no basis in AS 2 — the standard chooses between cost and NRV, never blends them.' },
      { key: 'D', text: 'Whichever the auditor prefers', explanation: 'Valuation follows the standard, not preference.' },
    ],
    correct: 'B',
    difficulty: 'medium',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '14 Jun 2026',
  },
  {
    id: 'q-as3-001',
    topic: 'Ch 3 · AS 3 · Cash flow statements',
    type: 'mcq',
    stem: 'For a finance company, interest paid on borrowings is classified in the cash flow statement as:',
    options: [
      { key: 'A', text: 'Operating activity', explanation: 'Correct. For a finance company, borrowing and lending IS the business — interest paid is operating. For other companies it is financing.' },
      { key: 'B', text: 'Financing activity', explanation: 'That is the rule for non-finance companies. The classification flips with the nature of the business.' },
      { key: 'C', text: 'Investing activity', explanation: 'Investing covers acquisition/disposal of long-term assets — interest paid never sits here.' },
      { key: 'D', text: 'Excluded from the statement', explanation: 'All interest paid in cash appears in the statement; only non-cash items are excluded.' },
    ],
    correct: 'A',
    difficulty: 'medium',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '14 Jun 2026',
  },
  {
    id: 'q-as1-001',
    topic: 'Ch 3 · AS 1 · Disclosure of accounting policies',
    type: 'mcq',
    stem: 'Which of these is NOT a fundamental accounting assumption under AS 1?',
    options: [
      { key: 'A', text: 'Going concern', explanation: 'One of the three fundamental assumptions — presumed unless stated otherwise.' },
      { key: 'B', text: 'Consistency', explanation: 'Also fundamental — policies are presumed consistent period to period.' },
      { key: 'C', text: 'Accrual', explanation: 'The third fundamental assumption.' },
      { key: 'D', text: 'Prudence', explanation: 'Correct — prudence is a consideration in SELECTING policies, not a fundamental assumption. The exam loves this distinction.' },
    ],
    correct: 'D',
    difficulty: 'easy',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '14 Jun 2026',
  },
  {
    id: 'q-ret-001',
    topic: 'Ch 4 · Partnership · Retirement of a partner',
    type: 'mcq',
    stem: 'On retirement of a partner, the continuing partners compensate the outgoing partner for goodwill in the:',
    options: [
      { key: 'A', text: 'Gaining ratio (New − Old)', explanation: 'Correct. Whoever gains share pays for it — the mirror image of the sacrificing ratio on admission.' },
      { key: 'B', text: 'Old profit-sharing ratio', explanation: 'The old ratio measures what everyone had, not who gained from the retirement.' },
      { key: 'C', text: 'New profit-sharing ratio', explanation: 'Close but wrong — two partners can have the same new ratio while gaining very differently.' },
      { key: 'D', text: 'Equal shares', explanation: 'Equality has no basis unless the gaining ratio happens to be equal.' },
    ],
    correct: 'A',
    readLink: { label: 'Read: Gaining ratio, §1 →', href: '/intermediate/advanced-accounting/partnership-accounts/retirement-of-a-partner/#s1' },
    difficulty: 'easy',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '14 Jun 2026',
  },
  {
    id: 'q-s37-001',
    topic: 'Ch 4 · Partnership · Retirement of a partner',
    type: 'mcq',
    stem: 'A partner retires and the firm delays paying the amount due, with the partnership deed silent on the point. Under Section 37 of the Indian Partnership Act 1932, the outgoing partner may claim:',
    options: [
      { key: 'A', text: 'Interest at 12% p.a. on the unpaid amount', explanation: '12% appears in other statutes; Section 37 prescribes 6%.' },
      { key: 'B', text: 'Interest at 6% p.a., OR the profits attributable to the use of his money — at his option', explanation: 'Correct. Section 37 gives the OUTGOING partner the choice between 6% p.a. interest and the share of profits earned with his money.' },
      { key: 'C', text: 'Only his capital, with no further entitlement', explanation: 'The firm keeps using his money — Section 37 exists precisely to compensate that.' },
      { key: 'D', text: 'Whatever the continuing partners decide', explanation: 'The statute grants the option to the outgoing partner, not the firm.' },
    ],
    correct: 'B',
    readLink: { label: 'Read: Settlement, §3 →', href: '/intermediate/advanced-accounting/partnership-accounts/retirement-of-a-partner/#s3' },
    difficulty: 'medium',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '30 Jun 2026',
  },
  {
    id: 'q-gw-001',
    topic: 'Ch 4 · Partnership · Goodwill: nature & valuation',
    type: 'mcq',
    stem: 'Average profit ₹95,000; capital employed ₹5,00,000; normal rate of return 10%. Goodwill by capitalisation of super profits is:',
    options: [
      { key: 'A', text: '₹1,35,000', explanation: 'That is 3 years’ PURCHASE of super profits — a different method with the same inputs.' },
      { key: 'B', text: '₹4,50,000', explanation: 'Correct. Super profit = 95,000 − 50,000 = ₹45,000; capitalised at 10% → 45,000 ÷ 0.10 = ₹4,50,000.' },
      { key: 'C', text: '₹9,50,000', explanation: 'This capitalises the AVERAGE profit (95,000 ÷ 10%) — that gives the firm’s implied value, from which capital employed must still be deducted.' },
      { key: 'D', text: '₹45,000', explanation: 'That is the super profit itself, before capitalisation.' },
    ],
    correct: 'B',
    readLink: { label: 'Read: Capitalisation methods, §4 →', href: '/intermediate/advanced-accounting/partnership-accounts/goodwill-nature-valuation/#s4' },
    difficulty: 'medium',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '30 Jun 2026',
  },
  {
    id: 'q-adm-005',
    topic: 'Ch 4 · Partnership · Admission of a partner',
    type: 'mcq',
    stem: 'C is admitted for a 1/4th share and brings ₹3,00,000 as capital (no goodwill premium). The adjusted capitals of A and B total ₹6,00,000. The hidden goodwill of the firm is:',
    options: [
      { key: 'A', text: '₹3,00,000', explanation: 'Correct. Implied firm value = 3,00,000 ÷ 1/4 = ₹12,00,000; actual capital = 6,00,000 + 3,00,000 = ₹9,00,000; the ₹3,00,000 gap is hidden goodwill.' },
      { key: 'B', text: '₹6,00,000', explanation: 'This subtracts only A and B’s capitals from the implied value — C’s own capital must be included in the actual total.' },
      { key: 'C', text: '₹12,00,000', explanation: 'That is the implied value of the whole firm, not the goodwill.' },
      { key: 'D', text: 'Nil — no premium was brought', explanation: 'Hidden goodwill exists precisely when no premium is brought but the capital contribution implies a higher firm value.' },
    ],
    correct: 'A',
    difficulty: 'hard',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '14 Jun 2026',
  },
  {
    id: 'q-as10-001',
    topic: 'Ch 3 · AS 10 · Property, plant & equipment',
    type: 'mcq',
    stem: 'Which cost is NOT capitalised into the cost of a machine under AS 10?',
    options: [
      { key: 'A', text: 'Trial-run costs before commercial production', explanation: 'Trial runs are directly attributable to bringing the asset to working condition — capitalised.' },
      { key: 'B', text: 'Site preparation and installation', explanation: 'Directly attributable — capitalised.' },
      { key: 'C', text: 'General administrative overheads', explanation: 'Correct — general admin and other indirect overheads are expensed, never capitalised into PPE.' },
      { key: 'D', text: 'Non-refundable import duties', explanation: 'Part of purchase cost — capitalised.' },
    ],
    correct: 'C',
    difficulty: 'medium',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '14 Jun 2026',
  },
  {
    id: 'q-adm-004',
    topic: 'Ch 4 · Partnership · Admission of a partner',
    type: 'mcq',
    stem: 'Under AS 26, goodwill of the firm is recorded in the books at the time of admission:',
    options: [
      { key: 'A', text: 'Always, at its full computed value', explanation: 'Self-generated goodwill cannot be recorded — AS 26 permits recognition only when consideration is paid.' },
      { key: 'B', text: 'Only when consideration in money or money’s worth is paid for it', explanation: 'AS 26 bars self-generated goodwill; the premium brought by the new partner is shared by old partners in the sacrificing ratio.' },
      { key: 'C', text: 'Never, under any circumstance', explanation: 'Too strong — purchased goodwill (consideration paid) is recognised.' },
      { key: 'D', text: 'Only if all partners agree in writing', explanation: 'Partner consent doesn’t override the accounting standard.' },
    ],
    correct: 'B',
    readLink: { label: 'Read: Treatment of goodwill, §2 →', href: '/intermediate/advanced-accounting/partnership-accounts/admission-of-a-partner/#s2' },
    difficulty: 'easy',
    source: 'original',
    applicableAttempts: ['Sept 2026', 'Jan 2027'],
    lastVerified: '14 Jun 2026',
  },
];
