/**
 * Canonical data for the CA Intermediate launch (plan §6.2).
 * Attempt-tagging (`applicableAttempts`, `lawAsOnDate`) is mandatory on
 * everything volatile — tax/law content without it must not merge.
 *
 * All ICAI resources are LINKS to official sources, never re-hosted copies.
 */

export const attempt = {
  id: 'sept-2026',
  name: 'Sept 2026',
  beginsOn: '2026-09-08',
  beginsLabel: '8 Sept 2026',
  applicableFinanceAct: 'Finance Act 2026',
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
    chapters: 14,
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
    chapters: 12,
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
    chapters: 18,
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
    chapters: 16,
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
          { slug: 'goodwill-nature-valuation', name: 'Goodwill: nature & valuation', hasNotes: false },
          { slug: 'admission-of-a-partner', name: 'Admission of a partner', hasNotes: true },
          { slug: 'retirement-of-a-partner', name: 'Retirement of a partner', hasNotes: false },
        ],
      },
      { number: 5, slug: 'branch-accounting', name: 'Branch accounting', draft: true },
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
    title: 'Study Material — Paper 1 (2025 edition)',
    url: 'https://www.icai.org/post/study-material-intermediate',
    host: 'icai.org',
    requiresLogin: false,
    lastChecked: '28 Jun 2026',
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
