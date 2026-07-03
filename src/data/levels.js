/**
 * Canonical taxonomy for all three levels (plan §2.2) under the
 * New Scheme of Education and Training (effective July 2023).
 *
 * ⚠ Every regulatory fact here must be re-verified against icai.org
 * before content production for a new attempt (plan §2, first line).
 */
import { papers as intermediatePapers } from './site.js';

const commonResources = (levelName) => [
  {
    kind: 'SM',
    title: `Study Material — ${levelName} (BoS Knowledge Portal)`,
    url: 'https://www.icai.org/post/bos-knowledge-portal',
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
    title: 'MTP Series I & II — Sept 2026',
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
    title: 'ICAI CA Tube — free live/recorded classes',
    url: 'https://www.youtube.com/@icaicatube',
    host: 'youtube.com · public',
    requiresLogin: false,
    lastChecked: '28 Jun 2026',
  },
  {
    kind: 'Exam',
    title: 'Exam portal — forms, dates, admit cards, results',
    url: 'https://icai.nic.in/',
    host: 'icai.nic.in',
    requiresLogin: false,
    lastChecked: '28 Jun 2026',
  },
];

export const levels = [
  {
    id: 'foundation',
    name: 'CA Foundation',
    shortName: 'Foundation',
    overline: '4 papers · no groups · 3 attempts a year (Jan, May/June, Sept)',
    intro:
      'The entry test. Papers 1–2 are descriptive; Papers 3–4 are objective with 0.25 negative marking per wrong answer — the only negative marking in the whole CA course.',
    passing: [
      'Per paper: minimum 40 of 100.',
      'Aggregate: minimum 50% across all four papers together.',
      'Papers 3 and 4 are objective with 0.25 negative marking — accuracy matters more than attempts here.',
      'No groups and no paper-wise exemptions at Foundation.',
    ],
    groups: [
      {
        name: 'All papers',
        papers: [
          { number: 1, slug: 'accounting', name: 'Accounting', shortName: 'Accounting', marks: 100, pattern: { style: 'Descriptive', negativeMarking: false } },
          { number: 2, slug: 'business-laws', name: 'Business Laws', shortName: 'Business Laws', marks: 100, pattern: { style: 'Descriptive', negativeMarking: false } },
          { number: 3, slug: 'quantitative-aptitude', name: 'Quantitative Aptitude (Maths, LR, Stats)', shortName: 'Quant. Aptitude', marks: 100, pattern: { style: 'Objective', negativeMarking: true } },
          { number: 4, slug: 'business-economics', name: 'Business Economics', shortName: 'Business Economics', marks: 100, pattern: { style: 'Objective', negativeMarking: true } },
        ],
      },
    ],
    resources: commonResources('Foundation'),
  },
  {
    id: 'intermediate',
    name: 'CA Intermediate',
    shortName: 'Intermediate',
    overline: '6 papers · 2 groups · 3 attempts a year',
    intro:
      'Each paper is 100 marks: 30% case-scenario MCQs + 70% descriptive, no negative marking. To pass a group you need 40% in every paper and 50% aggregate. Papers scoring 60+ earn a permanent exemption.',
    passing: [
      'Per paper: minimum 40 of 100.',
      "Per group: minimum 50% aggregate across the group's three papers.",
      'Exemption: score 60+ in a paper and fail the group — that paper is exempt in future attempts; remaining papers then need 50% each. Exemptions can be surrendered.',
      'No negative marking in any Intermediate paper — attempt every MCQ.',
    ],
    groups: [
      {
        name: 'Group I',
        papers: intermediatePapers
          .filter((p) => p.group === 1)
          .map((p) => ({ number: p.number, slug: p.slug, name: p.name, shortName: p.shortName, marks: p.marks, pattern: { style: '30% MCQ + 70% descriptive', negativeMarking: false }, status: p.status })),
      },
      {
        name: 'Group II',
        papers: intermediatePapers
          .filter((p) => p.group === 2)
          .map((p) => ({ number: p.number, slug: p.slug, name: p.name, shortName: p.shortName, marks: p.marks, pattern: { style: '30% MCQ + 70% descriptive', negativeMarking: false }, status: p.status })),
      },
    ],
    resources: commonResources('Intermediate'),
  },
  {
    id: 'final',
    name: 'CA Final',
    shortName: 'Final',
    overline: '6 papers · 2 groups · 3 attempts a year (from 2025)',
    intro:
      'The last examination stage. Same 30/70 MCQ-descriptive split and passing rules as Intermediate. Paper 6 (Integrated Business Solutions) is an open-book multidisciplinary case study drawing on all subjects. SPOM modules must be qualified before appearing.',
    passing: [
      'Per paper: minimum 40 of 100.',
      "Per group: minimum 50% aggregate across the group's three papers.",
      'Exemption: 60+ in a paper with a failed group exempts that paper in future attempts (verify current wording on icai.org).',
      'Paper 6 (Integrated Business Solutions) is open-book — but open-book means find-fast, not read-there. Index your material.',
      'All four SPOM sets must be qualified before CA Final (see the SPOM guide).',
    ],
    groups: [
      {
        name: 'Group I',
        papers: [
          { number: 1, slug: 'financial-reporting', name: 'Financial Reporting', shortName: 'Fin. Reporting', marks: 100, pattern: { style: '30% MCQ + 70% descriptive', negativeMarking: false } },
          { number: 2, slug: 'advanced-financial-management', name: 'Advanced Financial Management', shortName: 'AFM', marks: 100, pattern: { style: '30% MCQ + 70% descriptive', negativeMarking: false } },
          { number: 3, slug: 'advanced-auditing', name: 'Advanced Auditing, Assurance & Professional Ethics', shortName: 'Adv. Auditing', marks: 100, pattern: { style: '30% MCQ + 70% descriptive', negativeMarking: false } },
        ],
      },
      {
        name: 'Group II',
        papers: [
          { number: 4, slug: 'direct-tax', name: 'Direct Tax Laws & International Taxation', shortName: 'Direct Tax', marks: 100, pattern: { style: '30% MCQ + 70% descriptive', negativeMarking: false } },
          { number: 5, slug: 'indirect-tax', name: 'Indirect Tax Laws', shortName: 'Indirect Tax', marks: 100, pattern: { style: '30% MCQ + 70% descriptive', negativeMarking: false } },
          { number: 6, slug: 'integrated-business-solutions', name: 'Integrated Business Solutions', shortName: 'IBS (open book)', marks: 100, pattern: { style: 'Open-book multidisciplinary case study', negativeMarking: false }, openBook: true },
        ],
      },
    ],
    resources: commonResources('Final'),
  },
];

export function getLevel(id) {
  return levels.find((l) => l.id === id);
}

export function allPaperPaths() {
  const paths = [];
  for (const level of levels) {
    for (const group of level.groups) {
      for (const paper of group.papers) {
        paths.push({ level, group, paper });
      }
    }
  }
  return paths;
}
