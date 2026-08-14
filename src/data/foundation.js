/**
 * CA Foundation taxonomy (plan §2.2, §6.2) — New Scheme of Education and Training.
 *
 * Chapter lists verified against the ICAI BoS Knowledge Portal study-material
 * index, edition "Applicable for May 2026 Exam Onwards", on 3 Jul 2026:
 *   P1 https://www.icai.org/post/sm-foundation-p1-may2026
 *   P2 https://www.icai.org/post/sm-foundation-p2-may2026
 *   P3 https://www.icai.org/post/sm-foundation-p3-may2026
 *   P4 https://www.icai.org/post/sm-foundation-p4-may2026
 * Re-verify against these URLs whenever ICAI announces a new SM edition.
 *
 * Papers 3 & 4 are objective with 0.25 negative marking — the only negative
 * marking in the CA course. The quiz engine reads `foundationScoring` for it.
 */

export const foundationScoring = {
  correct: 1,
  wrong: -0.25,
  skipped: 0,
  /** Paper slugs the negative-marking mode applies to. */
  appliesTo: ['quantitative-aptitude', 'business-economics'],
};

const LAST_CHECKED = '3 Jul 2026';

/** Deep links to official free sources only — never re-hosted (plan §3.1). */
function paperResources(paperNumber, paperShortName) {
  return [
    {
      kind: 'SM',
      title: `Study Material — Paper ${paperNumber} ${paperShortName} (May 2026 onwards edition)`,
      url: `https://www.icai.org/post/sm-foundation-p${paperNumber}-may2026`,
      host: 'icai.org',
      requiresLogin: false,
      lastChecked: LAST_CHECKED,
    },
    {
      kind: 'RTP',
      title: 'RTP — Sept 2026 (Foundation)',
      url: 'https://boslive.icai.org/',
      host: 'boslive.icai.org',
      requiresLogin: true,
      lastChecked: LAST_CHECKED,
    },
    {
      kind: 'MTP',
      title: 'MTP Series I & II — Sept 2026 (Foundation)',
      url: 'https://boslive.icai.org/',
      host: 'boslive.icai.org',
      requiresLogin: true,
      lastChecked: LAST_CHECKED,
    },
    {
      kind: 'PastPaper',
      title: 'Past question papers + suggested answers',
      url: 'https://www.icai.org/post/question-papers-suggested-answers',
      host: 'icai.org',
      requiresLogin: false,
      lastChecked: LAST_CHECKED,
    },
    {
      kind: 'LVC',
      title: 'ICAI free Live Virtual Classes (BoS Live)',
      url: 'https://boslive.icai.org/',
      host: 'boslive.icai.org',
      requiresLogin: true,
      lastChecked: LAST_CHECKED,
    },
    {
      kind: 'LVC',
      title: 'ICAI CA Tube — free recorded classes (public)',
      url: 'https://www.youtube.com/@icaicatube',
      host: 'youtube.com · public',
      requiresLogin: false,
      lastChecked: LAST_CHECKED,
    },
  ];
}

export const foundationPapers = [
  {
    id: 'f1',
    slug: 'accounting',
    number: 1,
    name: 'Accounting',
    shortName: 'Accounting',
    marks: 100,
    pattern: { style: 'Descriptive', mcqPct: 0, descriptivePct: 100, negativeMarking: false },
    status: 'live',
    sections: [
      {
        name: 'Module 1',
        chapters: [
          { number: 1, slug: 'theoretical-framework', name: 'Theoretical Framework', hasNotes: true },
          { number: 2, slug: 'accounting-process', name: 'Accounting Process (Journal, Ledger, Trial Balance, Rectification)', hasNotes: true },
          { number: 3, slug: 'bank-reconciliation-statement', name: 'Bank Reconciliation Statement', hasNotes: true },
          { number: 4, slug: 'inventories', name: 'Inventories', hasNotes: true },
          { number: 5, slug: 'depreciation-and-amortisation', name: 'Depreciation and Amortisation', hasNotes: true },
          { number: 6, slug: 'bills-of-exchange-and-promissory-notes', name: 'Bills of Exchange and Promissory Notes', hasNotes: true },
          { number: 7, slug: 'final-accounts-of-sole-proprietors', name: 'Preparation of Final Accounts of Sole Proprietors', hasNotes: true },
        ],
      },
      {
        name: 'Module 2',
        chapters: [
          { number: 8, slug: 'financial-statements-of-not-for-profit-organisations', name: 'Financial Statements of Not-for-Profit Organisations', hasNotes: true },
          { number: 9, slug: 'accounts-from-incomplete-records', name: 'Accounts from Incomplete Records', hasNotes: true },
          { number: 10, slug: 'partnership-and-llp-accounts', name: 'Partnership and LLP Accounts', hasNotes: true },
          { number: 11, slug: 'company-accounts', name: 'Company Accounts', hasNotes: true },
        ],
      },
    ],
    resources: paperResources(1, 'Accounting'),
  },
  {
    id: 'f2',
    slug: 'business-laws',
    number: 2,
    name: 'Business Laws',
    shortName: 'Business Laws',
    marks: 100,
    pattern: { style: 'Descriptive', mcqPct: 0, descriptivePct: 100, negativeMarking: false },
    status: 'live',
    sections: [
      {
        name: 'All chapters',
        chapters: [
          { number: 1, slug: 'indian-regulatory-framework', name: 'Indian Regulatory Framework', hasNotes: true },
          { number: 2, slug: 'indian-contract-act-1872', name: 'The Indian Contract Act, 1872', hasNotes: true },
          { number: 3, slug: 'sale-of-goods-act-1930', name: 'The Sale of Goods Act, 1930', hasNotes: true },
          { number: 4, slug: 'indian-partnership-act-1932', name: 'The Indian Partnership Act, 1932', hasNotes: true },
          { number: 5, slug: 'llp-act-2008', name: 'The Limited Liability Partnership Act, 2008', hasNotes: true },
          { number: 6, slug: 'companies-act-2013', name: 'The Companies Act, 2013', hasNotes: true },
          { number: 7, slug: 'negotiable-instruments-act-1881', name: 'The Negotiable Instruments Act, 1881', hasNotes: true },
        ],
      },
    ],
    resources: paperResources(2, 'Business Laws'),
  },
  {
    id: 'f3',
    slug: 'quantitative-aptitude',
    number: 3,
    name: 'Quantitative Aptitude',
    shortName: 'Quant. Aptitude',
    marks: 100,
    pattern: { style: 'Objective (MCQ)', mcqPct: 100, descriptivePct: 0, negativeMarking: true },
    status: 'live',
    sections: [
      {
        name: 'Part A · Business Mathematics (40 marks)',
        chapters: [
          { number: 1, slug: 'ratio-proportion-indices-logarithms', name: 'Ratio and Proportion, Indices, Logarithms', hasNotes: true },
          { number: 2, slug: 'equations', name: 'Equations', hasNotes: true },
          { number: 3, slug: 'linear-inequalities', name: 'Linear Inequalities', hasNotes: true },
          { number: 4, slug: 'mathematics-of-finance', name: 'Mathematics of Finance (Time Value of Money)', hasNotes: true },
          { number: 5, slug: 'permutations-and-combinations', name: 'Basic Concepts of Permutations and Combinations', hasNotes: true },
          { number: 6, slug: 'sequence-and-series', name: 'Sequence and Series — Arithmetic and Geometric Progressions', hasNotes: true },
          { number: 7, slug: 'sets-relations-functions', name: 'Sets, Relations and Functions; Basics of Limits and Continuity', hasNotes: true },
          { number: 8, slug: 'differential-and-integral-calculus', name: 'Basic Applications of Differential and Integral Calculus', hasNotes: true },
        ],
      },
      {
        name: 'Part B · Logical Reasoning (20 marks)',
        chapters: [
          { number: 9, slug: 'number-series-coding-decoding', name: 'Number Series, Coding and Decoding and Odd Man Out', hasNotes: true },
          { number: 10, slug: 'direction-sense-test', name: 'Direction Sense Test', hasNotes: true },
          { number: 11, slug: 'seating-arrangements', name: 'Seating Arrangements', hasNotes: true },
          { number: 12, slug: 'blood-relations', name: 'Blood Relations', hasNotes: true },
        ],
      },
      {
        name: 'Part C · Statistics (40 marks)',
        chapters: [
          { number: 13, slug: 'statistical-description-of-data', name: 'Statistical Description of Data and Sampling', hasNotes: true },
          { number: 14, slug: 'central-tendency-and-dispersion', name: 'Measures of Central Tendency and Dispersion', hasNotes: true },
          { number: 15, slug: 'probability', name: 'Probability', hasNotes: true },
          { number: 16, slug: 'theoretical-distributions', name: 'Theoretical Distributions', hasNotes: true },
          { number: 17, slug: 'correlation-and-regression', name: 'Correlation and Regression', hasNotes: true },
          { number: 18, slug: 'index-numbers', name: 'Index Numbers', hasNotes: true },
        ],
      },
    ],
    resources: paperResources(3, 'Quantitative Aptitude'),
  },
  {
    id: 'f4',
    slug: 'business-economics',
    number: 4,
    name: 'Business Economics',
    shortName: 'Business Economics',
    marks: 100,
    pattern: { style: 'Objective (MCQ)', mcqPct: 100, descriptivePct: 0, negativeMarking: true },
    status: 'live',
    sections: [
      {
        name: 'All chapters',
        chapters: [
          { number: 1, slug: 'nature-and-scope-of-business-economics', name: 'Nature and Scope of Business Economics', hasNotes: true },
          { number: 2, slug: 'theory-of-demand-and-supply', name: 'Theory of Demand and Supply', hasNotes: true },
          { number: 3, slug: 'theory-of-production-and-cost', name: 'Theory of Production and Cost', hasNotes: true },
          { number: 4, slug: 'price-determination-in-different-markets', name: 'Price Determination in Different Markets', hasNotes: true },
          { number: 5, slug: 'business-cycles', name: 'Business Cycles', hasNotes: true },
          { number: 6, slug: 'determination-of-national-income', name: 'Determination of National Income', hasNotes: true },
          { number: 7, slug: 'public-finance', name: 'Public Finance', hasNotes: true },
          { number: 8, slug: 'money-market', name: 'Money Market', hasNotes: true },
          { number: 9, slug: 'international-trade', name: 'International Trade', hasNotes: true },
          { number: 10, slug: 'indian-economy', name: 'Indian Economy', hasNotes: true },
        ],
      },
    ],
    resources: paperResources(4, 'Business Economics'),
  },
];

export function getFoundationPaper(slug) {
  return foundationPapers.find((p) => p.slug === slug);
}

/* ═══════════════════════════════════════════════════════════════════════
 * Exam-facts data layer (Phase 1) — attempts, paper structure, weightage.
 * Every figure below is ICAI-sourced; the source URL and the date it was
 * read sit in the doc comment directly above each export.
 * ═══════════════════════════════════════════════════════════════════════ */

const EXAM_FACTS_CHECKED = '14 Aug 2026';

/**
 * Foundation attempt calendar.
 *
 * Foundation has been held thrice yearly (January / May / September) since
 * June 2024. The 2026 dates below are from the ICAI examination
 * notifications, read 14 Aug 2026:
 *   https://icai.nic.in/  ·  https://www.icai.org/
 * Registration cut-offs (ICAI BoS registration rule): register by 1 January
 * for the May attempt, 1 May for September, and 1 September of the previous
 * year for January. Foundation registration is valid four years and there is
 * NO revalidation at this level.
 *
 * Jan 2027 and May 2027 dates are `null` — ICAI had not notified them as of
 * 14 Aug 2026. Same `verified` / `verify` contract as intermediate.js
 * `attempts`: a human must confirm before content is tagged to that attempt.
 *
 * DATES are notified by ICAI. The paper→date MAPPING follows ICAI's
 * invariable Foundation sequence (Paper 1 → 2 → 3 → 4) and is inferred, not
 * quoted — hence the verify entry on every attempt.
 */
export const foundationAttempts = [
  {
    id: 'sept-2026',
    name: 'Sept 2026',
    // Notified dates: 2, 5, 7 and 9 September 2026.
    examDates: { begins: '2026-09-02', ends: '2026-09-09', label: '2–9 Sept 2026' },
    papers: [
      { paperSlug: 'accounting', date: '2026-09-02', label: '2 Sept 2026' },
      { paperSlug: 'business-laws', date: '2026-09-05', label: '5 Sept 2026' },
      { paperSlug: 'quantitative-aptitude', date: '2026-09-07', label: '7 Sept 2026' },
      { paperSlug: 'business-economics', date: '2026-09-09', label: '9 Sept 2026' },
    ],
    registration: {
      cutoff: '2026-05-01',
      label: '1 May 2026',
      rule: 'Register with the ICAI Board of Studies by 1 May to be eligible for the September attempt.',
      passed: true,
    },
    session: { startsAt: '14:00', label: 'Afternoon session — papers begin at 2:00 PM' },
    dayPattern: 'Four papers spread over about a week, with one or two gap days between papers.',
    verified: false,
    verify: [
      'Exam dates 2 / 5 / 7 / 9 Sept 2026 and which paper falls on which date — ICAI examination notification, https://icai.nic.in/',
      'Exam-form opening and closing dates for this attempt — https://icai.nic.in/',
    ],
  },
  {
    id: 'jan-2027',
    name: 'Jan 2027',
    examDates: { begins: null, ends: null, label: 'Jan 2027 (dates not yet notified)' },
    papers: [
      { paperSlug: 'accounting', date: null, label: 'TBA' },
      { paperSlug: 'business-laws', date: null, label: 'TBA' },
      { paperSlug: 'quantitative-aptitude', date: null, label: 'TBA' },
      { paperSlug: 'business-economics', date: null, label: 'TBA' },
    ],
    registration: {
      cutoff: '2026-09-01',
      label: '1 Sept 2026',
      rule: 'Register by 1 September 2026 — the cut-off for a January attempt falls in the previous calendar year.',
      passed: false,
    },
    session: { startsAt: '14:00', label: 'Afternoon session — papers begin at 2:00 PM' },
    dayPattern: 'Four papers spread over about a week, with one or two gap days between papers.',
    verified: false,
    verify: [
      'Exam dates — not notified as of ' + EXAM_FACTS_CHECKED + '; watch https://icai.nic.in/',
      'Registration cut-off 1 Sept 2026 — confirm against the BoS registration announcement on https://www.icai.org/',
    ],
  },
  {
    id: 'may-2027',
    name: 'May 2027',
    examDates: { begins: null, ends: null, label: 'May 2027 (dates not yet notified)' },
    papers: [
      { paperSlug: 'accounting', date: null, label: 'TBA' },
      { paperSlug: 'business-laws', date: null, label: 'TBA' },
      { paperSlug: 'quantitative-aptitude', date: null, label: 'TBA' },
      { paperSlug: 'business-economics', date: null, label: 'TBA' },
    ],
    registration: {
      cutoff: '2027-01-01',
      label: '1 Jan 2027',
      rule: 'Register by 1 January 2027 for the May attempt.',
      passed: false,
    },
    session: { startsAt: '14:00', label: 'Afternoon session — papers begin at 2:00 PM' },
    dayPattern: 'Four papers spread over about a week, with one or two gap days between papers.',
    verified: false,
    verify: [
      'Exam dates — not notified as of ' + EXAM_FACTS_CHECKED + '; watch https://icai.nic.in/',
      'Registration cut-off 1 Jan 2027 — confirm against the BoS registration announcement on https://www.icai.org/',
    ],
  },
];

/**
 * Per-paper structure — mode, duration, question pattern, negative marking.
 *
 * Source: ICAI Foundation syllabus / scheme of examination,
 *   https://resource.cdn.icai.org/76829bos61899-foundation.pdf
 * plus the ICAI Foundation examination FAQ, both read 14 Aug 2026.
 *
 * Papers 1 & 2 are subjective, 3 hours: six questions of 20 marks each,
 * Question 1 compulsory, any four of the remaining five to be attempted.
 * Papers 3 & 4 are objective, 2 hours: 100 MCQs of 1 mark each on an OMR
 * sheet, with 15 minutes of reading time before the exam starts.
 *
 * The negative-marking NUMBER is not repeated here — `scoring` points at
 * `foundationScoring` so the quiz/mock engines and this table can never
 * drift apart.
 */
export const paperStructure = {
  accounting: {
    paperSlug: 'accounting',
    mode: 'subjective',
    modeLabel: 'Subjective (descriptive)',
    durationMinutes: 180,
    durationLabel: '3 hours',
    readingTimeMinutes: 0,
    marks: 100,
    negativeMarking: false,
    scoring: null, // no negative marking on P1/P2
    questionPattern: {
      kind: 'descriptive',
      totalQuestions: 6,
      marksPerQuestion: 20,
      compulsory: 1,
      chooseFromRemaining: { attempt: 4, outOf: 5 },
      answerMedium: 'Answer booklet',
      summary: 'Six questions of 20 marks. Question 1 is compulsory; attempt any four of the remaining five.',
    },
  },
  'business-laws': {
    paperSlug: 'business-laws',
    mode: 'subjective',
    modeLabel: 'Subjective (descriptive)',
    durationMinutes: 180,
    durationLabel: '3 hours',
    readingTimeMinutes: 0,
    marks: 100,
    negativeMarking: false,
    scoring: null,
    questionPattern: {
      kind: 'descriptive',
      totalQuestions: 6,
      marksPerQuestion: 20,
      compulsory: 1,
      chooseFromRemaining: { attempt: 4, outOf: 5 },
      answerMedium: 'Answer booklet',
      summary: 'Six questions of 20 marks. Question 1 is compulsory; attempt any four of the remaining five.',
    },
  },
  'quantitative-aptitude': {
    paperSlug: 'quantitative-aptitude',
    mode: 'objective',
    modeLabel: 'Objective (MCQ, OMR)',
    durationMinutes: 120,
    durationLabel: '2 hours',
    readingTimeMinutes: 15,
    marks: 100,
    negativeMarking: true,
    /** Single source of truth for +1 / −0.25 / 0 — see `foundationScoring`. */
    scoring: foundationScoring,
    questionPattern: {
      kind: 'mcq',
      totalQuestions: 100,
      marksPerQuestion: 1,
      answerMedium: 'OMR sheet',
      summary: '100 multiple-choice questions of 1 mark each, answered on an OMR sheet.',
    },
  },
  'business-economics': {
    paperSlug: 'business-economics',
    mode: 'objective',
    modeLabel: 'Objective (MCQ, OMR)',
    durationMinutes: 120,
    durationLabel: '2 hours',
    readingTimeMinutes: 15,
    marks: 100,
    negativeMarking: true,
    scoring: foundationScoring,
    questionPattern: {
      kind: 'mcq',
      totalQuestions: 100,
      marksPerQuestion: 1,
      answerMedium: 'OMR sheet',
      summary: '100 multiple-choice questions of 1 mark each, answered on an OMR sheet.',
    },
  },
};

export function getPaperStructure(slug) {
  return paperStructure[slug];
}

/**
 * The Foundation passing rule.
 *
 * Source: ICAI Foundation scheme of examination,
 *   https://resource.cdn.icai.org/76829bos61899-foundation.pdf (read 14 Aug 2026).
 * A candidate passes Foundation on securing a minimum of 40% in EACH paper
 * AND 50% of the aggregate (200 of 400) in the SAME sitting. Foundation has
 * no exemption / set-off machinery — a shortfall in one paper means writing
 * all four again.
 */
export const passRule = {
  perPaperPct: 40,
  aggregatePct: 50,
  oneSitting: true,
  setOff: false,
  papers: 4,
  totalMarks: 400,
  aggregateMarks: 200,
  source: {
    label: 'ICAI Foundation syllabus & scheme of examination',
    url: 'https://resource.cdn.icai.org/76829bos61899-foundation.pdf',
    lastChecked: EXAM_FACTS_CHECKED,
  },
};

/**
 * OFFICIAL section-wise weightage, announced by ICAI on 26 October 2023 and
 * published with the Foundation syllabus:
 *   https://resource.cdn.icai.org/76829bos61899-foundation.pdf (read 14 Aug 2026)
 *
 * ICAI states that a deviation of ±5% is permitted in the actual question
 * paper, so treat every range as indicative rather than a contract.
 *
 * `basis` records what the percentage is a percentage OF. For Papers 1, 2
 * and 4 it is the whole 100-mark paper. For Paper 3 the published ranges are
 * of the PART (Part A Business Mathematics = 40 marks, Part C Statistics =
 * 40 marks); Part B Logical Reasoning carries 20 marks of the paper with no
 * published sub-split, so its group holds `weightage: null`.
 *
 * Group→chapter mapping: ICAI publishes weightage against syllabus SECTIONS,
 * not against study-material chapters. Each group below lists the chapter
 * slugs that section covers. Every chapter slug in `foundationPapers`
 * appears in exactly one group of its paper (asserted by the build check).
 *
 * Paper 4's figures are published as single values, not ranges, so lo === hi
 * for every P4 group. They sum to 100.
 */
export const foundationWeightage = {
  accounting: {
    basis: 'paper',
    basisLabel: 'of the 100-mark paper',
    groups: [
      {
        id: 'f1-w1',
        label: 'Theoretical Framework',
        weightage: { lo: 5, hi: 10 },
        chapterSlugs: ['theoretical-framework'],
      },
      {
        id: 'f1-w2',
        label: 'Accounting Process · Bank Reconciliation · Inventories · Depreciation · Bills of Exchange',
        weightage: { lo: 30, hi: 35 },
        chapterSlugs: [
          'accounting-process',
          'bank-reconciliation-statement',
          'inventories',
          'depreciation-and-amortisation',
          'bills-of-exchange-and-promissory-notes',
        ],
      },
      {
        id: 'f1-w3',
        label: 'Final Accounts of Sole Proprietors · Not-for-Profit Organisations · Incomplete Records',
        weightage: { lo: 20, hi: 25 },
        chapterSlugs: [
          'final-accounts-of-sole-proprietors',
          'financial-statements-of-not-for-profit-organisations',
          'accounts-from-incomplete-records',
        ],
      },
      {
        id: 'f1-w4',
        label: 'Partnership and LLP Accounts',
        weightage: { lo: 15, hi: 20 },
        chapterSlugs: ['partnership-and-llp-accounts'],
      },
      {
        id: 'f1-w5',
        label: 'Company Accounts',
        weightage: { lo: 15, hi: 25 },
        chapterSlugs: ['company-accounts'],
      },
    ],
  },
  'business-laws': {
    basis: 'paper',
    basisLabel: 'of the 100-mark paper',
    groups: [
      { id: 'f2-w1', label: 'Indian Regulatory Framework', weightage: { lo: 0, hi: 5 }, chapterSlugs: ['indian-regulatory-framework'] },
      { id: 'f2-w2', label: 'The Indian Contract Act, 1872', weightage: { lo: 20, hi: 30 }, chapterSlugs: ['indian-contract-act-1872'] },
      { id: 'f2-w3', label: 'The Sale of Goods Act, 1930', weightage: { lo: 15, hi: 20 }, chapterSlugs: ['sale-of-goods-act-1930'] },
      { id: 'f2-w4', label: 'The Indian Partnership Act, 1932', weightage: { lo: 15, hi: 20 }, chapterSlugs: ['indian-partnership-act-1932'] },
      { id: 'f2-w5', label: 'The Limited Liability Partnership Act, 2008', weightage: { lo: 5, hi: 10 }, chapterSlugs: ['llp-act-2008'] },
      { id: 'f2-w6', label: 'The Companies Act, 2013', weightage: { lo: 15, hi: 20 }, chapterSlugs: ['companies-act-2013'] },
      { id: 'f2-w7', label: 'The Negotiable Instruments Act, 1881', weightage: { lo: 10, hi: 15 }, chapterSlugs: ['negotiable-instruments-act-1881'] },
    ],
  },
  'quantitative-aptitude': {
    basis: 'section',
    basisLabel: 'of its own Part, not of the whole paper',
    groups: [
      {
        id: 'f3-w1',
        section: 'Part A · Business Mathematics (40 marks)',
        label: 'Ratio and Proportion, Indices, Logarithms · Equations · Linear Inequalities',
        weightage: { lo: 20, hi: 30 },
        chapterSlugs: ['ratio-proportion-indices-logarithms', 'equations', 'linear-inequalities'],
      },
      {
        id: 'f3-w2',
        section: 'Part A · Business Mathematics (40 marks)',
        label: 'Mathematics of Finance',
        weightage: { lo: 30, hi: 40 },
        chapterSlugs: ['mathematics-of-finance'],
      },
      {
        id: 'f3-w3',
        section: 'Part A · Business Mathematics (40 marks)',
        label: 'Permutations and Combinations · Sequence and Series · Sets, Relations and Functions · Calculus',
        weightage: { lo: 30, hi: 50 },
        chapterSlugs: [
          'permutations-and-combinations',
          'sequence-and-series',
          'sets-relations-functions',
          'differential-and-integral-calculus',
        ],
      },
      {
        id: 'f3-w4',
        section: 'Part B · Logical Reasoning (20 marks)',
        label: 'Logical Reasoning — the whole Part',
        // ICAI publishes no sub-split inside Part B; it is 20 marks of the paper.
        weightage: null,
        marks: 20,
        note: 'ICAI publishes no sub-split within Part B — it carries 20 marks of the paper.',
        chapterSlugs: ['number-series-coding-decoding', 'direction-sense-test', 'seating-arrangements', 'blood-relations'],
      },
      {
        id: 'f3-w5',
        section: 'Part C · Statistics (40 marks)',
        label: 'Statistical Description of Data · Measures of Central Tendency and Dispersion',
        weightage: { lo: 45, hi: 50 },
        chapterSlugs: ['statistical-description-of-data', 'central-tendency-and-dispersion'],
      },
      {
        id: 'f3-w6',
        section: 'Part C · Statistics (40 marks)',
        label: 'Probability · Theoretical Distributions',
        weightage: { lo: 25, hi: 30 },
        chapterSlugs: ['probability', 'theoretical-distributions'],
      },
      {
        id: 'f3-w7',
        section: 'Part C · Statistics (40 marks)',
        label: 'Correlation and Regression',
        weightage: { lo: 10, hi: 15 },
        chapterSlugs: ['correlation-and-regression'],
      },
      {
        id: 'f3-w8',
        section: 'Part C · Statistics (40 marks)',
        label: 'Index Numbers',
        weightage: { lo: 10, hi: 15 },
        chapterSlugs: ['index-numbers'],
      },
    ],
  },
  'business-economics': {
    basis: 'paper',
    basisLabel: 'of the 100-mark paper',
    groups: [
      { id: 'f4-w1', label: 'Nature and Scope of Business Economics', weightage: { lo: 5, hi: 5 }, chapterSlugs: ['nature-and-scope-of-business-economics'] },
      { id: 'f4-w2', label: 'Theory of Demand and Supply', weightage: { lo: 10, hi: 10 }, chapterSlugs: ['theory-of-demand-and-supply'] },
      { id: 'f4-w3', label: 'Theory of Production and Cost', weightage: { lo: 10, hi: 10 }, chapterSlugs: ['theory-of-production-and-cost'] },
      { id: 'f4-w4', label: 'Price Determination in Different Markets', weightage: { lo: 15, hi: 15 }, chapterSlugs: ['price-determination-in-different-markets'] },
      { id: 'f4-w5', label: 'Business Cycles', weightage: { lo: 5, hi: 5 }, chapterSlugs: ['business-cycles'] },
      { id: 'f4-w6', label: 'Determination of National Income', weightage: { lo: 15, hi: 15 }, chapterSlugs: ['determination-of-national-income'] },
      { id: 'f4-w7', label: 'Public Finance', weightage: { lo: 10, hi: 10 }, chapterSlugs: ['public-finance'] },
      { id: 'f4-w8', label: 'Money Market', weightage: { lo: 10, hi: 10 }, chapterSlugs: ['money-market'] },
      { id: 'f4-w9', label: 'International Trade', weightage: { lo: 10, hi: 10 }, chapterSlugs: ['international-trade'] },
      { id: 'f4-w10', label: 'Indian Economy', weightage: { lo: 10, hi: 10 }, chapterSlugs: ['indian-economy'] },
    ],
  },
};

/** The ±5% caveat, in ICAI's own terms — render this next to any range. */
export const WEIGHTAGE_NOTE = 'ICAI section-wise weightage, ±5% deviation permitted';

export const WEIGHTAGE_SOURCE = {
  label: 'ICAI section-wise weightage, announced 26 Oct 2023',
  url: 'https://resource.cdn.icai.org/76829bos61899-foundation.pdf',
  lastChecked: EXAM_FACTS_CHECKED,
};

// Attach the weightage groups to each paper so hub pages can read
// `paper.weightageGroups` without a second lookup. Chapters are NEVER
// reordered by this — the groups only annotate the existing lists.
for (const paper of foundationPapers) {
  const w = foundationWeightage[paper.slug];
  paper.weightageGroups = w ? w.groups : [];
  paper.weightageBasis = w ? w.basis : null;
  paper.weightageBasisLabel = w ? w.basisLabel : null;
}

/** Format a weightage range for display: {lo:30,hi:35} → "30–35%". */
export function formatWeightage(weightage) {
  if (!weightage) return null;
  return weightage.lo === weightage.hi ? `${weightage.lo}%` : `${weightage.lo}–${weightage.hi}%`;
}

/** The weightage group a chapter slug belongs to, or undefined. */
export function getWeightageGroupForChapter(paperSlug, chapterSlug) {
  const w = foundationWeightage[paperSlug];
  return w && w.groups.find((g) => g.chapterSlugs.includes(chapterSlug));
}

/**
 * Attempt-wise Foundation pass percentages, as announced by ICAI with each
 * result. Read from the ICAI result announcements / press releases,
 * 14 Aug 2026: https://www.icai.org/  ·  https://icai.nic.in/
 *
 * The scheme changed with the June 2024 attempt, so figures before and after
 * that line are not directly comparable — `scheme` records which is which.
 * ICAI does not publish per-paper pass statistics at Foundation level.
 * Candidate counts are given only where ICAI announced them.
 */
export const foundationPassPercentages = [
  { attempt: 'June 2023', pct: 24.98, scheme: 'old', appeared: null, passed: null },
  { attempt: 'Dec 2023', pct: 29.99, scheme: 'old', appeared: null, passed: null },
  { attempt: 'June 2024', pct: 14.96, scheme: 'new', appeared: null, passed: null },
  { attempt: 'Sept 2024', pct: 19.67, scheme: 'new', appeared: null, passed: null },
  { attempt: 'Jan 2025', pct: 21.52, scheme: 'new', appeared: null, passed: null },
  { attempt: 'May 2025', pct: 15.09, scheme: 'new', appeared: null, passed: null },
  { attempt: 'Sept 2025', pct: 14.78, scheme: 'new', appeared: null, passed: null },
  { attempt: 'Jan 2026', pct: 19.23, scheme: 'new', appeared: 109694, passed: null },
  { attempt: 'May 2026', pct: 20.09, scheme: 'new', appeared: 90217, passed: 18124 },
];

/** Plain-language range for the new scheme, derived from the table above. */
export const foundationPassRange = { lo: 14.78, hi: 21.52, scheme: 'new' };

export const PASS_PERCENTAGE_SOURCE = {
  label: 'Pass percentages as announced by ICAI with each result',
  url: 'https://www.icai.org/',
  lastChecked: EXAM_FACTS_CHECKED,
};

/**
 * ICAI's free official practice corpus and when each piece lands relative to
 * an attempt. Everything here is free on the BoS Knowledge Portal
 * (https://boslive.icai.org/) with the student login; nothing is re-hosted.
 * Timings read from the ICAI BoS announcements, 14 Aug 2026 — the Sept 2025
 * MTP dates (Series I from 11 Aug 2025, Series II from 25 Aug 2025) are the
 * worked example of the pattern, not a promise for future attempts.
 */
export const foundationOfficialCorpus = [
  {
    kind: 'RTP',
    name: 'Revision Test Paper (RTP)',
    timing: 'Released about one to two months before the exam',
    what: 'One booklet per paper per attempt: a syllabus-wide question set plus the amendments and updates applicable to that specific attempt.',
    useIt: 'Read the amendment section the day it lands. Work the questions during your second revision cycle, once the syllabus is covered.',
    url: 'https://boslive.icai.org/',
    requiresLogin: true,
  },
  {
    kind: 'MTP',
    name: 'Mock Test Paper (MTP) — Series I and Series II',
    timing: 'Two series per attempt, typically a few weeks apart in the month or two before the exam (for Sept 2025: Series I from 11 Aug 2025, Series II from 25 Aug 2025)',
    what: 'Full-length papers in the real exam pattern, released with answer keys and suggested answers.',
    useIt: 'Sit each series to the clock, in the real 2 PM slot if you can. These are the closest thing to exam-day conditions ICAI publishes.',
    url: 'https://boslive.icai.org/',
    requiresLogin: true,
  },
  {
    kind: 'PastPaper',
    name: 'Past question papers with suggested answers',
    timing: 'Published after each attempt, once results are declared',
    what: 'The actual question paper of a past attempt with ICAI’s own model answers — the clearest picture of what depth and presentation earn marks.',
    useIt: 'Use the last three attempts. Attempt first, compare after — reading suggested answers without writing teaches very little.',
    url: 'https://www.icai.org/post/question-papers-suggested-answers',
    requiresLogin: false,
  },
  {
    kind: 'ModelPaper',
    name: 'Model test papers / sample papers',
    timing: 'Published with each new study-material edition',
    what: 'Pattern-illustrating papers issued alongside the study material, showing how the syllabus is examined under the current scheme.',
    useIt: 'Useful early — they show the shape of the paper before you have enough syllabus covered to sit a full mock.',
    url: 'https://boslive.icai.org/',
    requiresLogin: true,
  },
];

/**
 * Paper 3 "safe path to 40" — the highest-yield route to the 40-mark pass
 * bar for a student weak in Quantitative Aptitude. Every mark figure comes
 * from the official weightage above; the strategy of prioritising them is
 * ours, and the page says so.
 */
export const p3SafePathTo40 = [
  {
    label: 'Logical Reasoning',
    detail: '20 marks of the paper, and the part that needs no formula sheet — only practice.',
    chapterSlugs: ['number-series-coding-decoding', 'direction-sense-test', 'seating-arrangements', 'blood-relations'],
  },
  {
    label: 'Measures of Central Tendency and Dispersion',
    detail: 'With Statistical Description of Data, 45–50% of the 40-mark Statistics part — the single densest block in the paper.',
    chapterSlugs: ['statistical-description-of-data', 'central-tendency-and-dispersion'],
  },
  {
    label: 'Mathematics of Finance',
    detail: '30–40% of the 40-mark Business Mathematics part, from a small and stable set of formulas.',
    chapterSlugs: ['mathematics-of-finance'],
  },
];
