/**
 * Amendment changelog (plan §6.4 rule 4 — the amendment calendar's output).
 * One entry per sourced change: notification/Finance Act ref → what changed →
 * affected content IDs. Rendered per paper at /intermediate/<paper>/amendments/
 * and site-wide at /updates/.
 *
 * RULES:
 *  - Every entry cites its official source URL. No source, no entry.
 *  - `todo: true` = the source document exists but a human hasn't transcribed
 *    the substance yet; the tracker shows it as "pending transcription" rather
 *    than inventing details.
 *  - `affected` lists content IDs/notes touched — empty until content ships.
 *
 * (Two earlier seeded entries from the design build were removed 3 Jul 2026:
 * a "stamp duty via Finance Act 2026" note — stamp duty is a State List
 * subject, not a Finance Act matter — and a mis-dated P3 syllabus claim.)
 */

export const amendments = [
  {
    id: 'amd-p1-sebi-buyback',
    paperSlug: 'advanced-accounting',
    paperLabel: 'P1 · Advanced Accounting',
    appliesFrom: 'Sept 2026',
    title: 'SEBI (Buy-back of Securities) Regulations — listed-company procedure watch item',
    old: 'Ch 12 notes summarise only the stable Companies Act layer (ss. 68–70)',
    now: 'Pending human decision — SEBI has amended the 2018 buyback regulations repeatedly (incl. phasing down the open-market route). Confirm per attempt whether the Inter P1 syllabus expects SEBI-layer detail, and update Ch 12 notes §3 if so (AMENDMENT-CHECK marker in the notes; also in review_queue.md)',
    source: 'SEBI regulations page',
    sourceUrl: 'https://www.sebi.gov.in/legal/regulations',
    affected: [{ label: 'Ch 12 Buyback — §3', href: '/intermediate/advanced-accounting/buyback-of-securities/#3-after-the-cheque-extinguishment-and-the-quiet-period' }],
    todo: true,
  },
  {
    id: 'amd-p3-itact2025',
    paperSlug: 'taxation',
    paperLabel: 'P3 · Taxation',
    appliesFrom: 'May 2027',
    title: 'Income-tax Act, 2025 replaces the Income-tax Act, 1961 in the syllabus',
    old: 'Income-tax Act, 1961 as amended by the Finance Act, 2025 (through the Jan 2027 attempt)',
    now: 'Income-tax Act, 2025 as amended by the Finance Act, 2026 — ICAI has published a 1961→2025 section-mapping booklet; every Sec A section citation must migrate',
    source: 'ICAI BoS announcement, 8 Dec 2025',
    sourceUrl: 'https://boslive.icai.org/announcement_details.php?id=552',
    affected: [],
  },
  {
    id: 'amd-p2-sept2026',
    paperSlug: 'corporate-and-other-laws',
    paperLabel: 'P2 · Corporate & Other Laws',
    appliesFrom: 'Sept 2026',
    title: 'ICAI "Amendments for September 2026 Examinations" (Company Law)',
    old: 'May 2026 SM edition text',
    now: 'Pending transcription — the ICAI amendment document is published; a human must transcribe each change here with its notification reference before P2 content ships',
    source: 'ICAI BoS Amendments/Developments — Intermediate',
    sourceUrl: 'https://boslive.icai.org/education_content_AmendmentsDevelopments.php?p=Amendments%2FDevelopments&c=intermediate',
    affected: [],
    todo: true,
  },
  {
    id: 'amd-p3-gst-sept2026',
    paperSlug: 'taxation',
    paperLabel: 'P3 · Taxation (GST)',
    appliesFrom: 'Sept 2026',
    title: 'GST statutory update for September 2026 examinations',
    old: 'May 2026 SM edition (Sec B GST) positions',
    now: 'Pending transcription — ICAI has published the Sept 2026 GST statutory update; transcribe notification-by-notification (number + date) before any GST content ships',
    source: 'ICAI BoS Amendments/Developments — Intermediate',
    sourceUrl: 'https://boslive.icai.org/education_content_AmendmentsDevelopments.php?p=Amendments%2FDevelopments&c=intermediate',
    affected: [],
    todo: true,
  },
];

export function amendmentsForPaper(slug) {
  return amendments.filter((a) => a.paperSlug === slug);
}
