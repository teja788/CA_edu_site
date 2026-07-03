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
    status: 'coming-soon',
    sections: [
      {
        name: 'Module 1',
        chapters: [
          { number: 1, slug: 'theoretical-framework', name: 'Theoretical Framework' },
          { number: 2, slug: 'accounting-process', name: 'Accounting Process (Journal, Ledger, Trial Balance, Rectification)' },
          { number: 3, slug: 'bank-reconciliation-statement', name: 'Bank Reconciliation Statement' },
          { number: 4, slug: 'inventories', name: 'Inventories' },
          { number: 5, slug: 'depreciation-and-amortisation', name: 'Depreciation and Amortisation' },
          { number: 6, slug: 'bills-of-exchange-and-promissory-notes', name: 'Bills of Exchange and Promissory Notes' },
          { number: 7, slug: 'final-accounts-of-sole-proprietors', name: 'Preparation of Final Accounts of Sole Proprietors' },
        ],
      },
      {
        name: 'Module 2',
        chapters: [
          { number: 8, slug: 'financial-statements-of-not-for-profit-organisations', name: 'Financial Statements of Not-for-Profit Organisations' },
          { number: 9, slug: 'accounts-from-incomplete-records', name: 'Accounts from Incomplete Records' },
          { number: 10, slug: 'partnership-and-llp-accounts', name: 'Partnership and LLP Accounts' },
          { number: 11, slug: 'company-accounts', name: 'Company Accounts' },
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
    status: 'coming-soon',
    sections: [
      {
        name: 'All chapters',
        chapters: [
          { number: 1, slug: 'indian-regulatory-framework', name: 'Indian Regulatory Framework' },
          { number: 2, slug: 'indian-contract-act-1872', name: 'The Indian Contract Act, 1872' },
          { number: 3, slug: 'sale-of-goods-act-1930', name: 'The Sale of Goods Act, 1930' },
          { number: 4, slug: 'indian-partnership-act-1932', name: 'The Indian Partnership Act, 1932' },
          { number: 5, slug: 'llp-act-2008', name: 'The Limited Liability Partnership Act, 2008' },
          { number: 6, slug: 'companies-act-2013', name: 'The Companies Act, 2013' },
          { number: 7, slug: 'negotiable-instruments-act-1881', name: 'The Negotiable Instruments Act, 1881' },
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
    status: 'coming-soon',
    sections: [
      {
        name: 'Part A · Business Mathematics (40 marks)',
        chapters: [
          { number: 1, slug: 'ratio-proportion-indices-logarithms', name: 'Ratio and Proportion, Indices, Logarithms' },
          { number: 2, slug: 'equations', name: 'Equations' },
          { number: 3, slug: 'linear-inequalities', name: 'Linear Inequalities' },
          { number: 4, slug: 'mathematics-of-finance', name: 'Mathematics of Finance (Time Value of Money)' },
          { number: 5, slug: 'permutations-and-combinations', name: 'Basic Concepts of Permutations and Combinations' },
          { number: 6, slug: 'sequence-and-series', name: 'Sequence and Series — Arithmetic and Geometric Progressions' },
          { number: 7, slug: 'sets-relations-functions', name: 'Sets, Relations and Functions; Basics of Limits and Continuity' },
          { number: 8, slug: 'differential-and-integral-calculus', name: 'Basic Applications of Differential and Integral Calculus' },
        ],
      },
      {
        name: 'Part B · Logical Reasoning (20 marks)',
        chapters: [
          { number: 9, slug: 'number-series-coding-decoding', name: 'Number Series, Coding and Decoding and Odd Man Out' },
          { number: 10, slug: 'direction-sense-test', name: 'Direction Sense Test' },
          { number: 11, slug: 'seating-arrangements', name: 'Seating Arrangements' },
          { number: 12, slug: 'blood-relations', name: 'Blood Relations' },
        ],
      },
      {
        name: 'Part C · Statistics (40 marks)',
        chapters: [
          { number: 13, slug: 'statistical-description-of-data', name: 'Statistical Description of Data and Sampling' },
          { number: 14, slug: 'central-tendency-and-dispersion', name: 'Measures of Central Tendency and Dispersion' },
          { number: 15, slug: 'probability', name: 'Probability' },
          { number: 16, slug: 'theoretical-distributions', name: 'Theoretical Distributions' },
          { number: 17, slug: 'correlation-and-regression', name: 'Correlation and Regression' },
          { number: 18, slug: 'index-numbers', name: 'Index Numbers' },
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
    status: 'coming-soon',
    sections: [
      {
        name: 'All chapters',
        chapters: [
          { number: 1, slug: 'nature-and-scope-of-business-economics', name: 'Nature and Scope of Business Economics' },
          { number: 2, slug: 'theory-of-demand-and-supply', name: 'Theory of Demand and Supply' },
          { number: 3, slug: 'theory-of-production-and-cost', name: 'Theory of Production and Cost' },
          { number: 4, slug: 'price-determination-in-different-markets', name: 'Price Determination in Different Markets' },
          { number: 5, slug: 'business-cycles', name: 'Business Cycles' },
          { number: 6, slug: 'determination-of-national-income', name: 'Determination of National Income' },
          { number: 7, slug: 'public-finance', name: 'Public Finance' },
          { number: 8, slug: 'money-market', name: 'Money Market' },
          { number: 9, slug: 'international-trade', name: 'International Trade' },
          { number: 10, slug: 'indian-economy', name: 'Indian Economy' },
        ],
      },
    ],
    resources: paperResources(4, 'Business Economics'),
  },
];

export function getFoundationPaper(slug) {
  return foundationPapers.find((p) => p.slug === slug);
}
