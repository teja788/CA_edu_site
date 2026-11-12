/**
 * ACTUAL chapter-wise marks in past CA Foundation papers 1 and 2 — tallied
 * question by question from the ICAI question papers of every New Scheme
 * attempt (June 2024 – September 2026), downloaded from
 * https://www.icai.org/post/question-papers-foundation-course on 12 Nov 2026.
 *
 * Method: marks OFFERED per chapter. Where the paper gives an internal
 * choice (OR), BOTH alternatives are counted, so an attempt's chapter marks
 * sum to `offeredTotal` (125 for P1, 126 for P2), not to the 100-mark paper.
 *
 * Papers 3 and 4 are fully objective and ICAI does not publish their
 * question papers, so no actuals exist for them — only the official
 * weightage ranges in `foundationWeightage`.
 *
 * Evidence (question → chapter → marks, per attempt, spot-checkable against
 * each PDF): citations/foundation/weightage/weightage_p1_evidence.md and
 * weightage_p2_evidence.md in the repository.
 *
 * Judgement calls made while mapping borderline sub-parts to chapters are
 * recorded per attempt in `notes`.
 */

export const weightageActuals = {
  lastChecked: '12 Nov 2026',
  papers: {
    accounting: {
      offeredTotal: 125,
      structureNote:
        'Every paper so far: Q1 compulsory (20 marks), then any 4 of Q2–Q6 at 20 marks each; Q5 carries one 5-mark either/or — 125 marks offered per 100-mark paper.',
      attempts: [
    { name: "June 2024", sourceUrl: "https://resource.cdn.icai.org/80830bos65028.pdf", paperTotal: 100, offeredTotal: 125, chapters: {"theoretical-framework": 6, "accounting-process": 25, "bank-reconciliation-statement": 5, "inventories": 5, "depreciation-and-amortisation": 8, "bills-of-exchange-and-promissory-notes": 2, "final-accounts-of-sole-proprietors": 7, "financial-statements-of-not-for-profit-organisations": 12, "accounts-from-incomplete-records": 8, "partnership-and-llp-accounts": 22, "company-accounts": 25}, notes: ["Structure: Q1 compulsory (20) + answer any 4 of Q2-Q6 (20 each) = 100. offeredTotal counts all five optional questions plus both alternatives of the Q5 'either (i) or (ii)' OR-pair, hence 125.", "1(a)(i) closing stock in TB is about final-accounts presentation; mapped to final-accounts-of-sole-proprietors."] },
    { name: "September 2024", sourceUrl: "https://resource.cdn.icai.org/82221bos66272-p1.pdf", paperTotal: 100, offeredTotal: 125, chapters: {"theoretical-framework": 8, "accounting-process": 6, "bank-reconciliation-statement": 10, "inventories": 10, "depreciation-and-amortisation": 5, "bills-of-exchange-and-promissory-notes": 12, "final-accounts-of-sole-proprietors": 10, "financial-statements-of-not-for-profit-organisations": 12, "accounts-from-incomplete-records": 5, "partnership-and-llp-accounts": 22, "company-accounts": 25}, notes: ["Structure: Q1 compulsory (20) + answer any 4 of Q2-Q6 (20 each) = 100. offeredTotal counts all five optional questions plus both alternatives of the Q5 'either (i) or (ii)' OR-pair, hence 125.", "1(a)(ii) capital vs revenue expenditure sits in ICAI Ch 1 (Theoretical Framework).", "1(a)(iii) inventory valuation vs conservatism: tested as an accounting concept, mapped to theoretical-framework (alt: inventories)."] },
    { name: "January 2025", sourceUrl: "https://resource.cdn.icai.org/84047bos130125.pdf", paperTotal: 100, offeredTotal: 125, chapters: {"theoretical-framework": 10, "accounting-process": 11, "bank-reconciliation-statement": 10, "inventories": 7, "depreciation-and-amortisation": 10, "bills-of-exchange-and-promissory-notes": 5, "final-accounts-of-sole-proprietors": 15, "financial-statements-of-not-for-profit-organisations": 10, "accounts-from-incomplete-records": 5, "partnership-and-llp-accounts": 20, "company-accounts": 22}, notes: ["Structure: Q1 compulsory (20) + answer any 4 of Q2-Q6 (20 each) = 100. offeredTotal counts all five optional questions plus both alternatives of the Q5 'either (i) or (ii)' OR-pair, hence 125.", "6(b) double-entry advantages mapped to accounting-process (ICAI Ch 2 opens with double entry; alt: theoretical-framework)."] },
    { name: "May 2025", sourceUrl: "https://resource.cdn.icai.org/85933bos-aps655-fnd-acc-p1.pdf", paperTotal: 100, offeredTotal: 125, chapters: {"theoretical-framework": 11, "accounting-process": 17, "bank-reconciliation-statement": 10, "inventories": 4, "depreciation-and-amortisation": 5, "bills-of-exchange-and-promissory-notes": 5, "final-accounts-of-sole-proprietors": 10, "financial-statements-of-not-for-profit-organisations": 16, "accounts-from-incomplete-records": 0, "partnership-and-llp-accounts": 22, "company-accounts": 25}, notes: ["Structure: Q1 compulsory (20) + answer any 4 of Q2-Q6 (20 each) = 100. offeredTotal counts all five optional questions plus both alternatives of the Q5 'either (i) or (ii)' OR-pair, hence 125.", "4(b) (prepare closing BS of a sole trader from opening BS, net profit and omitted adjustments) mapped to final-accounts-of-sole-proprietors; arguably accounts-from-incomplete-records."] },
    { name: "September 2025", sourceUrl: "https://resource.cdn.icai.org/88313bos-aps2395-fnd-sep2025-p1.pdf", paperTotal: 100, offeredTotal: 125, chapters: {"theoretical-framework": 8, "accounting-process": 16, "bank-reconciliation-statement": 5, "inventories": 5, "depreciation-and-amortisation": 10, "bills-of-exchange-and-promissory-notes": 5, "final-accounts-of-sole-proprietors": 5, "financial-statements-of-not-for-profit-organisations": 10, "accounts-from-incomplete-records": 12, "partnership-and-llp-accounts": 22, "company-accounts": 27}, notes: ["Structure: Q1 compulsory (20) + answer any 4 of Q2-Q6 (20 each) = 100. offeredTotal counts all five optional questions plus both alternatives of the Q5 'either (i) or (ii)' OR-pair, hence 125.", "PDF page 12 is a misaligned scan (overlaid with page 11); Q5(b) read from the visible half: sugar manufacturing, 5 marks, manufacturing account inferred. Marks check (Q5 = 5+5+5+10 = 25) holds."] },
    { name: "January 2026", sourceUrl: "https://resource.cdn.icai.org/90640bos-aps4047-fnd-jan2026-p1.pdf", paperTotal: 100, offeredTotal: 125, chapters: {"theoretical-framework": 8, "accounting-process": 23, "bank-reconciliation-statement": 5, "inventories": 0, "depreciation-and-amortisation": 8, "bills-of-exchange-and-promissory-notes": 5, "final-accounts-of-sole-proprietors": 10, "financial-statements-of-not-for-profit-organisations": 10, "accounts-from-incomplete-records": 7, "partnership-and-llp-accounts": 22, "company-accounts": 27}, notes: ["Structure: Q1 compulsory (20) + answer any 4 of Q2-Q6 (20 each) = 100. offeredTotal counts all five optional questions plus both alternatives of the Q5 'either (i) or (ii)' OR-pair, hence 125.", "1(a)(iv) 'nominal accounts kept under single entry' mapped to accounts-from-incomplete-records (alt: accounting-process)."] },
    { name: "May 2026", sourceUrl: "https://resource.cdn.icai.org/92236bos-aps5106-p1.pdf", paperTotal: 100, offeredTotal: 125, chapters: {"theoretical-framework": 6, "accounting-process": 21, "bank-reconciliation-statement": 5, "inventories": 7, "depreciation-and-amortisation": 10, "bills-of-exchange-and-promissory-notes": 0, "final-accounts-of-sole-proprietors": 10, "financial-statements-of-not-for-profit-organisations": 7, "accounts-from-incomplete-records": 10, "partnership-and-llp-accounts": 22, "company-accounts": 27}, notes: ["Structure: Q1 compulsory (20) + answer any 4 of Q2-Q6 (20 each) = 100. offeredTotal counts all five optional questions plus both alternatives of the Q5 'either (i) or (ii)' OR-pair, hence 125.", "5(a)(i) asks inventory value and adjusted net profit; mapped to inventories (alt: final-accounts-of-sole-proprietors)."] },
    { name: "September 2026", sourceUrl: "https://resource.cdn.icai.org/94143bos-aps6246-fnd-sep2026-p1.pdf", paperTotal: 100, offeredTotal: 125, chapters: {"theoretical-framework": 6, "accounting-process": 23, "bank-reconciliation-statement": 5, "inventories": 5, "depreciation-and-amortisation": 10, "bills-of-exchange-and-promissory-notes": 0, "final-accounts-of-sole-proprietors": 10, "financial-statements-of-not-for-profit-organisations": 7, "accounts-from-incomplete-records": 10, "partnership-and-llp-accounts": 20, "company-accounts": 29}, notes: ["Structure: Q1 compulsory (20) + answer any 4 of Q2-Q6 (20 each) = 100. offeredTotal counts all five optional questions plus both alternatives of the Q5 'either (i) or (ii)' OR-pair, hence 125.", "1(a)(i) FIFO/WA as accounting policy mapped to theoretical-framework (alt: inventories).", "6(b) double-entry advantages mapped to accounting-process (alt: theoretical-framework)."] },
      ],
    },
    'business-laws': {
      offeredTotal: 126,
      structureNote:
        'Every paper so far: Q1 compulsory, then any 4 of Q2–Q6 at 20 marks each; Q6(b) carries a 6-mark either/or — 126 marks offered per 100-mark paper.',
      attempts: [
    { name: "June 2024", sourceUrl: "https://resource.cdn.icai.org/80839bos65047.pdf", paperTotal: 100, offeredTotal: 126, chapters: {"indian-regulatory-framework": 6, "indian-contract-act-1872": 38, "sale-of-goods-act-1930": 21, "indian-partnership-act-1932": 20, "llp-act-2008": 6, "companies-act-2013": 21, "negotiable-instruments-act-1881": 14}, notes: ["2(a) does not name the Act; SoGA (price fixed by third party) is the fit."] },
    { name: "September 2024", sourceUrl: "https://resource.cdn.icai.org/82222bos66272-p2.pdf", paperTotal: 100, offeredTotal: 126, chapters: {"indian-regulatory-framework": 6, "indian-contract-act-1872": 38, "sale-of-goods-act-1930": 21, "indian-partnership-act-1932": 20, "llp-act-2008": 6, "companies-act-2013": 21, "negotiable-instruments-act-1881": 14}, notes: [] },
    { name: "January 2025", sourceUrl: "https://resource.cdn.icai.org/84098bos67816.pdf", paperTotal: 100, offeredTotal: 126, chapters: {"indian-regulatory-framework": 6, "indian-contract-act-1872": 38, "sale-of-goods-act-1930": 21, "indian-partnership-act-1932": 20, "llp-act-2008": 6, "companies-act-2013": 21, "negotiable-instruments-act-1881": 14}, notes: [] },
    { name: "May 2025", sourceUrl: "https://resource.cdn.icai.org/85949bos-aps655-fnd-bl-p1.pdf", paperTotal: 100, offeredTotal: 126, chapters: {"indian-regulatory-framework": 6, "indian-contract-act-1872": 38, "sale-of-goods-act-1930": 21, "indian-partnership-act-1932": 20, "llp-act-2008": 6, "companies-act-2013": 21, "negotiable-instruments-act-1881": 14}, notes: [] },
    { name: "September 2025", sourceUrl: "https://resource.cdn.icai.org/88339bos-aps2395-fnd-sep2025-p2.pdf", paperTotal: 100, offeredTotal: 126, chapters: {"indian-regulatory-framework": 6, "indian-contract-act-1872": 38, "sale-of-goods-act-1930": 21, "indian-partnership-act-1932": 20, "llp-act-2008": 6, "companies-act-2013": 21, "negotiable-instruments-act-1881": 14}, notes: ["1(a)(ii) mixing of goods is explicitly asked under the Contract Act (bailment); counted there.", "5(a)(ii) pledge-then-sale is explicitly framed under SoGA; counted there."] },
    { name: "January 2026", sourceUrl: "https://resource.cdn.icai.org/90641bos-aps4047-fnd-jan2026-p2.pdf", paperTotal: 100, offeredTotal: 126, chapters: {"indian-regulatory-framework": 6, "indian-contract-act-1872": 32, "sale-of-goods-act-1930": 27, "indian-partnership-act-1932": 20, "llp-act-2008": 6, "companies-act-2013": 21, "negotiable-instruments-act-1881": 14}, notes: ["2(a)(iii) (hypothecated car, loan from friend) reads like a pledge/contract fact pattern but sits under the 2(a) SoGA condition/warranty stem; counted SoGA.", "Q3(c) is SoGA in this attempt (Contract Act in every other attempt), hence SoGA 27 / Contract 32."] },
    { name: "May 2026", sourceUrl: "https://resource.cdn.icai.org/92284bos-aps5106-p2.pdf", paperTotal: 100, offeredTotal: 126, chapters: {"indian-regulatory-framework": 6, "indian-contract-act-1872": 38, "sale-of-goods-act-1930": 21, "indian-partnership-act-1932": 20, "llp-act-2008": 6, "companies-act-2013": 21, "negotiable-instruments-act-1881": 14}, notes: [] },
    { name: "September 2026", sourceUrl: "https://resource.cdn.icai.org/94162bos-aps6246-fnd-sep2026-p2.pdf", paperTotal: 100, offeredTotal: 126, chapters: {"indian-regulatory-framework": 6, "indian-contract-act-1872": 38, "sale-of-goods-act-1930": 21, "indian-partnership-act-1932": 20, "llp-act-2008": 6, "companies-act-2013": 21, "negotiable-instruments-act-1881": 14}, notes: ["Published PDF is English-only (18 pp; cover says 40 printed pages incl. Hindi).", "3(a) also asks about revoking a continuing guarantee (Contract Act s.131) but is framed under the Partnership Act; counted Partnership."] },
      ],
    },
  },
};

/**
 * Per-chapter summary across attempts: average/min/max marks offered and in
 * how many papers the chapter appeared. Sorted by average, descending.
 */
export function actualsSummary(paperSlug) {
  const paper = weightageActuals.papers[paperSlug];
  if (!paper) return null;
  const perChapter = new Map();
  for (const a of paper.attempts) {
    for (const [slug, marks] of Object.entries(a.chapters)) {
      if (!perChapter.has(slug)) perChapter.set(slug, []);
      perChapter.get(slug).push(marks);
    }
    // Integrity: the tally of every attempt must sum to the offered total.
    const sum = Object.values(a.chapters).reduce((x, y) => x + y, 0);
    if (sum !== a.offeredTotal) throw new Error(`weightageActuals: ${a.name} sums to ${sum}, expected ${a.offeredTotal}`);
  }
  const n = paper.attempts.length;
  return [...perChapter.entries()]
    .map(([slug, marks]) => {
      while (marks.length < n) marks.push(0);
      const total = marks.reduce((x, y) => x + y, 0);
      return {
        slug,
        avg: total / n,
        min: Math.min(...marks),
        max: Math.max(...marks),
        appearances: marks.filter((m) => m > 0).length,
        attempts: n,
      };
    })
    .sort((x, y) => y.avg - x.avg);
}
