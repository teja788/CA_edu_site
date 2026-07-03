/**
 * CA Intermediate taxonomy (plan §2.2, §6.2) — New Scheme of Education and Training.
 *
 * Chapter lists verified against the ICAI BoS Knowledge Portal study-material
 * indexes, edition "Applicable for May 2026 Exam" (P3 label: "May 2026/
 * September 2026/ January 2027 Exams"), on 3 Jul 2026:
 *   P1  https://www.icai.org/post/bos-int-p1-may2026-exam
 *   P2  https://www.icai.org/post/sm-inter-p2-may2026
 *   P3A https://www.icai.org/post/sm-intermediate-paper3-seca
 *   P3B https://www.icai.org/post/sm-intermediate-paper3-secb-may26
 *   P4  https://www.icai.org/post/sm-inter-p4-may2026
 *   P5  https://www.icai.org/post/sm-inter-p5-may2026
 *   P6A https://www.icai.org/post/sm-inter-p6a-may2026
 *   P6B https://www.icai.org/post/sm-inter-p6b-may2026
 * Re-verify against these URLs whenever ICAI announces a new SM edition.
 *
 * Every Intermediate paper: 100 marks, 30% case-scenario MCQs + 70%
 * descriptive, NO negative marking (contrast foundationScoring).
 */

const LAST_CHECKED = '3 Jul 2026';

/** Intermediate scoring profile — no negative marking anywhere. */
export const interScoring = {
  correct: 1,
  wrong: 0,
  skipped: 0,
  negativeMarking: false,
};

/**
 * Attempt records (plan §6.2 Attempt schema) — the amendment machinery keys
 * off these. `verified: false` + `verify` list = facts I could not confirm
 * against a fetchable ICAI page; a human must check before content tagged to
 * that attempt ships. The Income-tax Act 2025 boundary IS confirmed:
 * ICAI announcement 08-12-2025 — the 2025 Act applies from May 2027 CA exams
 * onwards; earlier attempts stay on the Income-tax Act 1961.
 *   https://boslive.icai.org/announcement_details.php?id=552
 */
export const attempts = [
  {
    id: 'sept-2026',
    name: 'Sept 2026',
    examDates: { begins: '2026-09-08', label: '8 Sept 2026' },
    incomeTaxLaw: 'Income-tax Act, 1961 as amended by the Finance Act, 2025',
    applicableFinanceAct: 'Finance Act 2025',
    assessmentYear: 'AY 2026-27',
    // ICAI convention: amendments up to ~6 months before the exam apply.
    amendmentCutoff: { date: '2026-02-28', basis: '6-month convention — verify against the Sept 2026 statutory update' },
    verified: false,
    verify: [
      'Finance Act 2025 / AY 2026-27 mapping — open the "Statutory Update for September 2026 Examination" PDF linked from https://www.icai.org/post/sm-intermediate-paper3-seca',
      'GST notification cut-off date — same PDF (Section B) or https://boslive.icai.org/education_content_AmendmentsDevelopments.php?p=Amendments%2FDevelopments&c=intermediate',
      'Exam start date 8 Sept 2026 — https://icai.nic.in/',
    ],
  },
  {
    id: 'jan-2027',
    name: 'Jan 2027',
    examDates: { begins: null, label: 'Jan 2027 (dates TBA — TODO verify)' },
    // The P3 SM edition label covers "May 2026/ September 2026/ January 2027
    // Exams" — same base law as Sept 2026, updated by its own statutory update.
    incomeTaxLaw: 'Income-tax Act, 1961 as amended by the Finance Act, 2025',
    applicableFinanceAct: 'Finance Act 2025',
    assessmentYear: 'AY 2026-27',
    amendmentCutoff: { date: '2026-06-30', basis: '6-month convention — verify against the Jan 2027 statutory update when released' },
    verified: false,
    verify: [
      'Exam dates — ICAI notification, https://icai.nic.in/',
      'Finance Act / AY and GST cut-off — Jan 2027 statutory update (not yet released as of 3 Jul 2026); watch https://boslive.icai.org/education_content_AmendmentsDevelopments.php?p=Amendments%2FDevelopments&c=intermediate',
    ],
  },
  {
    id: 'may-2027',
    name: 'May 2027',
    examDates: { begins: null, label: 'May 2027 (dates TBA — TODO verify)' },
    // CONFIRMED boundary: first attempt under the Income-tax Act, 2025
    // (ICAI announcement 08-12-2025). ICAI has published the 2025 Act as
    // amended by the Finance Act, 2026 with a 1961→2025 section mapping.
    incomeTaxLaw: 'Income-tax Act, 2025 as amended by the Finance Act, 2026',
    applicableFinanceAct: 'Finance Act 2026',
    assessmentYear: 'Tax year 2026-27 (the 2025 Act replaces "assessment year" — verify ICAI terminology)',
    amendmentCutoff: { date: '2026-10-31', basis: '6-month convention — verify against the May 2027 statutory update when released' },
    verified: false,
    verify: [
      'Exam dates — https://icai.nic.in/',
      'Confirm the 2025-Act applicability announcement text — https://boslive.icai.org/announcement_details.php?id=552',
      'New SM edition for May 2027 (the 1961-Act SM edition ends at Jan 2027) — re-run the taxonomy check for P3 Section A against the new index',
    ],
  },
];

/** Deep links to official free sources only — never re-hosted (plan §3.1). */
function smLink(title, url) {
  return { kind: 'SM', title, url, host: 'icai.org', requiresLogin: false, lastChecked: LAST_CHECKED };
}

const commonInterResources = [
  {
    kind: 'RTP',
    title: 'RTP — Sept 2026 (Intermediate)',
    url: 'https://boslive.icai.org/',
    host: 'boslive.icai.org',
    requiresLogin: true,
    lastChecked: LAST_CHECKED,
  },
  {
    kind: 'MTP',
    title: 'MTP Series I (from 25 Jul) & II (from 8 Aug) — Sept 2026',
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
    kind: 'Amendments',
    title: 'BoS amendments & statutory updates (per attempt)',
    url: 'https://boslive.icai.org/education_content_AmendmentsDevelopments.php?p=Amendments%2FDevelopments&c=intermediate',
    host: 'boslive.icai.org',
    requiresLogin: false,
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

/**
 * The six papers, chapter-aligned to the ICAI SM index above.
 * `volatile: true` ⇒ law/tax paper: every question and note MUST carry
 * `applicableAttempts` + `lawAsOnDate` (frontmatter: `applicable_attempts`,
 * `law_as_on_date`) — enforced by scripts/attempt_lint in CI.
 */
export const intermediatePapers = [
  {
    id: 'p1',
    slug: 'advanced-accounting',
    group: 1,
    number: 1,
    name: 'Advanced Accounting',
    shortName: 'Adv. Accounting',
    marks: 100,
    volatile: false,
    edition: 'Applicable for May 2026 Exam onwards',
    resources: [smLink('Study Material — Paper 1 Advanced Accounting (May 2026 onwards)', 'https://www.icai.org/post/bos-int-p1-may2026-exam'), ...commonInterResources],
    sections: [
      {
        name: 'Module 1',
        chapters: [
          { number: 1, slug: 'introduction-to-accounting-standards', name: 'Introduction to Accounting Standards' },
          { number: 2, slug: 'framework-for-preparation-and-presentation-of-fs', name: 'Framework for Preparation and Presentation of Financial Statements' },
          { number: 3, slug: 'applicability-of-accounting-standards', name: 'Applicability of Accounting Standards' },
          {
            number: 4,
            slug: 'presentation-and-disclosures-based-as',
            name: 'Presentation & Disclosures Based Accounting Standards',
            units: ['AS 1 Disclosure of Accounting Policies', 'AS 3 Cash Flow Statement', 'AS 17 Segment Reporting', 'AS 18 Related Party Disclosures', 'AS 20 Earnings Per Share', 'AS 24 Discontinuing Operations', 'AS 25 Interim Financial Reporting'],
          },
        ],
      },
      {
        name: 'Module 2',
        chapters: [
          { number: 5, slug: 'assets-based-as', name: 'Assets Based Accounting Standards', units: ['AS 2 Inventories', 'AS 10 PPE', 'AS 13 Investments', 'AS 16 Borrowing Costs', 'AS 19 Leases', 'AS 26 Intangible Assets', 'AS 28 Impairment of Assets'] },
          { number: 6, slug: 'liabilities-based-as', name: 'Liabilities Based Accounting Standards', units: ['AS 15 Employee Benefits', 'AS 29 Provisions, Contingent Liabilities & Contingent Assets'] },
          { number: 7, slug: 'as-items-impacting-fs', name: 'Accounting Standards Based on Items Impacting Financial Statements', units: ['AS 4 Events after Balance Sheet Date', 'AS 5 Net Profit/Loss, Prior Period Items & Changes in Policies', 'AS 11 Effects of Changes in Foreign Exchange Rates', 'AS 22 Taxes on Income'] },
          { number: 8, slug: 'revenue-based-as', name: 'Revenue Based Accounting Standards', units: ['AS 7 Construction Contracts', 'AS 9 Revenue Recognition'] },
          { number: 9, slug: 'other-accounting-standards', name: 'Other Accounting Standards', units: ['AS 12 Government Grants', 'AS 14 Accounting for Amalgamations'] },
          { number: 10, slug: 'as-consolidated-fs', name: 'Accounting Standards for Consolidated Financial Statements', units: ['AS 21 Consolidated FS', 'AS 23 Investments in Associates', 'AS 27 Joint Ventures'] },
        ],
      },
      {
        name: 'Module 3',
        chapters: [
          { number: 11, slug: 'financial-statements-of-companies', name: 'Financial Statements of Companies (Schedule III)' },
          { number: 12, slug: 'buyback-of-securities', name: 'Buyback of Securities' },
          { number: 13, slug: 'amalgamation-of-companies', name: 'Amalgamation of Companies' },
          { number: 14, slug: 'internal-reconstruction', name: 'Internal Reconstruction' },
          { number: 15, slug: 'branches-including-foreign', name: 'Accounting for Branches including Foreign Branches' },
        ],
      },
    ],
  },
  {
    id: 'p2',
    slug: 'corporate-and-other-laws',
    group: 1,
    number: 2,
    name: 'Corporate & Other Laws',
    shortName: 'Corporate Laws',
    marks: 100,
    volatile: true,
    edition: 'Applicable for May 2026 Exam onwards',
    resources: [smLink('Study Material — Paper 2 Corporate & Other Laws (May 2026 onwards)', 'https://www.icai.org/post/sm-inter-p2-may2026'), ...commonInterResources],
    sections: [
      {
        name: 'Part I · Company Law & LLP Law — Module 1',
        chapters: [
          { number: 1, slug: 'preliminary', name: 'Preliminary' },
          { number: 2, slug: 'incorporation-of-company', name: 'Incorporation of Company and Matters Incidental Thereto' },
          { number: 3, slug: 'prospectus-and-allotment', name: 'Prospectus and Allotment of Securities' },
          { number: 4, slug: 'share-capital-and-debentures', name: 'Share Capital and Debentures' },
          { number: 5, slug: 'acceptance-of-deposits', name: 'Acceptance of Deposits by Companies' },
          { number: 6, slug: 'registration-of-charges', name: 'Registration of Charges' },
        ],
      },
      {
        name: 'Part I · Company Law & LLP Law — Module 2',
        chapters: [
          { number: 7, slug: 'management-and-administration', name: 'Management & Administration' },
          { number: 8, slug: 'declaration-and-payment-of-dividend', name: 'Declaration and Payment of Dividend' },
          { number: 9, slug: 'accounts-of-companies', name: 'Accounts of Companies' },
          { number: 10, slug: 'audit-and-auditors', name: 'Audit and Auditors' },
          { number: 11, slug: 'companies-incorporated-outside-india', name: 'Companies Incorporated Outside India' },
        ],
      },
      {
        name: 'Part I · Company Law & LLP Law — Module 3',
        chapters: [{ number: 12, slug: 'llp-act-2008', name: 'The Limited Liability Partnership Act, 2008' }],
      },
      {
        name: 'Part II · Other Laws',
        chapters: [
          { number: 13, slug: 'general-clauses-act', name: 'The General Clauses Act, 1897', smNumber: 'Part II Ch 1' },
          { number: 14, slug: 'interpretation-of-statutes', name: 'Interpretation of Statutes', smNumber: 'Part II Ch 2' },
          { number: 15, slug: 'fema-1999', name: 'The Foreign Exchange Management Act, 1999', smNumber: 'Part II Ch 3' },
        ],
      },
    ],
  },
  {
    id: 'p3',
    slug: 'taxation',
    group: 1,
    number: 3,
    name: 'Taxation (Income Tax + GST)',
    shortName: 'Taxation',
    marks: 100,
    volatile: true,
    // Built LAST (plan §7 Phase 1 order) — Finance Act churn every attempt,
    // and the Income-tax Act 2025 replaces the entire Sec A base from May 2027.
    buildLast: true,
    edition: 'Applicable for May 2026 / September 2026 / January 2027 Exams (Income-tax Act 1961 base; NEW edition expected for May 2027 under the Income-tax Act 2025)',
    resources: [
      smLink('Study Material — Paper 3 Sec A Income-tax Law', 'https://www.icai.org/post/sm-intermediate-paper3-seca'),
      smLink('Study Material — Paper 3 Sec B Goods & Services Tax (May 2026 onwards)', 'https://www.icai.org/post/sm-intermediate-paper3-secb-may26'),
      ...commonInterResources,
    ],
    sections: [
      {
        name: 'Section A · Income-tax Law',
        chapters: [
          { number: 1, slug: 'basic-concepts', name: 'Basic Concepts' },
          { number: 2, slug: 'residence-and-scope-of-total-income', name: 'Residence and Scope of Total Income' },
          { number: 3, slug: 'heads-of-income', name: 'Heads of Income', units: ['Salaries', 'Income from House Property', 'Profits and Gains of Business or Profession', 'Capital Gains', 'Income from Other Sources'] },
          { number: 4, slug: 'clubbing-of-income', name: "Income of Other Persons included in Assessee's Total Income" },
          { number: 5, slug: 'set-off-and-carry-forward', name: 'Aggregation of Income, Set-Off and Carry Forward of Losses' },
          { number: 6, slug: 'deductions-from-gross-total-income', name: 'Deductions from Gross Total Income' },
          { number: 7, slug: 'advance-tax-tds-tcs', name: 'Advance Tax, Tax Deduction at Source and Tax Collection at Source' },
          { number: 8, slug: 'return-filing-and-self-assessment', name: 'Provisions for filing Return of Income and Self Assessment' },
          { number: 9, slug: 'total-income-computation', name: 'Income Tax Liability — Computation and Optimisation' },
        ],
      },
      {
        name: 'Section B · Goods and Services Tax',
        chapters: [
          { number: 1, slug: 'gst-in-india-introduction', name: 'GST in India — An Introduction', smNumber: 'Sec B Ch 1' },
          { number: 2, slug: 'supply-under-gst', name: 'Supply under GST', smNumber: 'Sec B Ch 2' },
          { number: 3, slug: 'charge-of-gst', name: 'Charge of GST', smNumber: 'Sec B Ch 3' },
          { number: 4, slug: 'place-of-supply', name: 'Place of Supply', smNumber: 'Sec B Ch 4' },
          { number: 5, slug: 'exemptions-from-gst', name: 'Exemptions from GST', smNumber: 'Sec B Ch 5' },
          { number: 6, slug: 'time-of-supply', name: 'Time of Supply', smNumber: 'Sec B Ch 6' },
          { number: 7, slug: 'value-of-supply', name: 'Value of Supply', smNumber: 'Sec B Ch 7' },
          { number: 8, slug: 'input-tax-credit', name: 'Input Tax Credit', smNumber: 'Sec B Ch 8' },
          { number: 9, slug: 'registration', name: 'Registration', smNumber: 'Sec B Ch 9' },
          { number: 10, slug: 'tax-invoice-credit-debit-notes', name: 'Tax Invoice; Credit and Debit Notes', smNumber: 'Sec B Ch 10' },
          { number: 11, slug: 'accounts-and-records', name: 'Accounts and Records', smNumber: 'Sec B Ch 11' },
          { number: 12, slug: 'e-way-bill', name: 'E-Way Bill', smNumber: 'Sec B Ch 12' },
          { number: 13, slug: 'payment-of-tax', name: 'Payment of Tax', smNumber: 'Sec B Ch 13' },
          { number: 14, slug: 'gst-tds-tcs', name: 'Tax Deduction at Source and Collection of Tax at Source', smNumber: 'Sec B Ch 14' },
          { number: 15, slug: 'returns', name: 'Returns', smNumber: 'Sec B Ch 15' },
        ],
      },
    ],
  },
  {
    id: 'p4',
    slug: 'cost-and-management-accounting',
    group: 2,
    number: 4,
    name: 'Cost & Management Accounting',
    shortName: 'Cost Mgmt',
    marks: 100,
    volatile: false,
    edition: 'Applicable for May 2026 Exam onwards',
    resources: [smLink('Study Material — Paper 4 Cost & Management Accounting (May 2026 onwards)', 'https://www.icai.org/post/sm-inter-p4-may2026'), ...commonInterResources],
    sections: [
      {
        name: 'Module 1',
        chapters: [
          { number: 1, slug: 'introduction-to-cost-and-management-accounting', name: 'Introduction to Cost and Management Accounting' },
          { number: 2, slug: 'material-cost', name: 'Material Cost' },
          { number: 3, slug: 'employee-cost-and-direct-expenses', name: 'Employee Cost and Direct Expenses' },
          { number: 4, slug: 'overheads-absorption-costing', name: 'Overheads — Absorption Costing Method' },
          { number: 5, slug: 'activity-based-costing', name: 'Activity Based Costing' },
          { number: 6, slug: 'cost-sheet', name: 'Cost Sheet' },
          { number: 7, slug: 'cost-accounting-systems', name: 'Cost Accounting Systems' },
        ],
      },
      {
        name: 'Module 2',
        chapters: [
          { number: 8, slug: 'unit-and-batch-costing', name: 'Unit & Batch Costing' },
          { number: 9, slug: 'job-costing', name: 'Job Costing' },
          { number: 10, slug: 'process-and-operation-costing', name: 'Process & Operation Costing' },
          { number: 11, slug: 'joint-products-and-by-products', name: 'Joint Products and By Products' },
          { number: 12, slug: 'service-costing', name: 'Service Costing' },
          { number: 13, slug: 'standard-costing', name: 'Standard Costing' },
          { number: 14, slug: 'marginal-costing', name: 'Marginal Costing' },
          { number: 15, slug: 'budgets-and-budgetary-control', name: 'Budgets and Budgetary Control' },
        ],
      },
    ],
  },
  {
    id: 'p5',
    slug: 'auditing-and-ethics',
    group: 2,
    number: 5,
    name: 'Auditing & Ethics',
    shortName: 'Auditing',
    marks: 100,
    volatile: true,
    edition: 'Applicable for May 2026 Exam onwards',
    resources: [smLink('Study Material — Paper 5 Auditing & Ethics (May 2026 onwards)', 'https://www.icai.org/post/sm-inter-p5-may2026'), ...commonInterResources],
    sections: [
      {
        name: 'Module 1',
        chapters: [
          { number: 1, slug: 'nature-objective-and-scope-of-audit', name: 'Nature, Objective and Scope of Audit' },
          { number: 2, slug: 'audit-strategy-planning-and-programme', name: 'Audit Strategy, Audit Planning and Audit Programme' },
          { number: 3, slug: 'risk-assessment-and-internal-control', name: 'Risk Assessment and Internal Control' },
          { number: 4, slug: 'audit-evidence', name: 'Audit Evidence' },
          { number: 5, slug: 'audit-of-items-of-financial-statements', name: 'Audit of Items of Financial Statements' },
        ],
      },
      {
        name: 'Module 2',
        chapters: [
          { number: 6, slug: 'audit-documentation', name: 'Audit Documentation' },
          { number: 7, slug: 'completion-and-review', name: 'Completion and Review' },
          { number: 8, slug: 'audit-report', name: 'Audit Report' },
          { number: 9, slug: 'audit-of-different-types-of-entities', name: 'Special Features of Audit of Different Type of Entities' },
          { number: 10, slug: 'audit-of-banks', name: 'Audit of Banks' },
          { number: 11, slug: 'ethics-and-terms-of-audit-engagements', name: 'Ethics and Terms of Audit Engagements' },
        ],
      },
    ],
  },
  {
    id: 'p6',
    slug: 'fm-and-sm',
    group: 2,
    number: 6,
    name: 'Financial Management & Strategic Management',
    shortName: 'FM & SM',
    marks: 100,
    volatile: false,
    edition: 'Applicable for May 2026 Exam onwards',
    resources: [
      smLink('Study Material — Paper 6 Sec A Financial Management (May 2026 onwards)', 'https://www.icai.org/post/sm-inter-p6a-may2026'),
      smLink('Study Material — Paper 6 Sec B Strategic Management (May 2026 onwards)', 'https://www.icai.org/post/sm-inter-p6b-may2026'),
      ...commonInterResources,
    ],
    sections: [
      {
        name: 'Section A · Financial Management — Module 1',
        chapters: [
          { number: 1, slug: 'scope-and-objectives-of-fm', name: 'Scope and Objectives of Financial Management' },
          { number: 2, slug: 'types-of-financing', name: 'Types of Financing' },
          { number: 3, slug: 'ratio-analysis', name: 'Financial Analysis and Planning — Ratio Analysis' },
          { number: 4, slug: 'cost-of-capital', name: 'Cost of Capital' },
          { number: 5, slug: 'capital-structure', name: 'Financing Decisions — Capital Structure' },
          { number: 6, slug: 'leverages', name: 'Financing Decisions — Leverages' },
        ],
      },
      {
        name: 'Section A · Financial Management — Module 2',
        chapters: [
          { number: 7, slug: 'investment-decisions', name: 'Investment Decisions (Capital Budgeting)' },
          { number: 8, slug: 'dividend-decision', name: 'Dividend Decision' },
          { number: 9, slug: 'management-of-working-capital', name: 'Management of Working Capital', units: ['Introduction to Working Capital Management', 'Treasury and Cash Management', 'Management of Inventory', 'Management of Receivables', 'Management of Payables (Creditors)', 'Financing of Working Capital'] },
        ],
      },
      {
        name: 'Section B · Strategic Management',
        chapters: [
          { number: 1, slug: 'introduction-to-strategic-management', name: 'Introduction to Strategic Management', smNumber: 'Sec B Ch 1' },
          { number: 2, slug: 'strategic-analysis-external-environment', name: 'Strategic Analysis: External Environment', smNumber: 'Sec B Ch 2' },
          { number: 3, slug: 'strategic-analysis-internal-environment', name: 'Strategic Analysis: Internal Environment', smNumber: 'Sec B Ch 3' },
          { number: 4, slug: 'strategic-choices', name: 'Strategic Choices', smNumber: 'Sec B Ch 4' },
          { number: 5, slug: 'strategy-implementation-and-evaluation', name: 'Strategy Implementation and Evaluation', smNumber: 'Sec B Ch 5' },
        ],
      },
    ],
  },
];

export function getInterPaper(slug) {
  return intermediatePapers.find((p) => p.slug === slug);
}

/** Paper slugs whose content must carry law_as_on_date + applicable_attempts. */
export const volatilePaperSlugs = intermediatePapers.filter((p) => p.volatile).map((p) => p.slug);
