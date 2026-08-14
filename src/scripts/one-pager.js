/**
 * One-pager extraction — pull a printable revision sheet out of a chapter's
 * raw MDX at build time.
 *
 * The notes are the source of truth. Nothing here is authored twice: a print
 * sheet is the chapter's own "One-page revision summary" section, re-rendered
 * for paper. That means a correction to the notes reaches the print sheet on
 * the next build, and a chapter can never drift from its own summary.
 *
 * This runs at BUILD time over raw file text, so it is deliberately a small
 * subset of Markdown rather than a dependency: the summaries use bold, italic,
 * bullets, pipe tables, and the site's own `<div class="formula">` box, and
 * nothing else (asserted by the build check in the print route). If a chapter
 * grows a construct this does not know, it degrades to a paragraph — it never
 * throws, because a broken print page is worse than a plain one.
 */

/** The heading every Foundation chapter ends with. Matched case-insensitively. */
export const SUMMARY_HEADING = /^##\s+One-page revision summary\s*$/i;

/** A slightly wider net, for chapters that word the heading differently. */
const SUMMARY_HEADING_LOOSE = /^##\s+.*(one[- ]page|revision summary|at a glance|quick recap)/i;

/** Split YAML frontmatter off the top of an MDX file. */
export function stripFrontmatter(raw) {
  const text = String(raw).replace(/^﻿/, '');
  if (!text.startsWith('---')) return { frontmatter: '', body: text };
  const end = text.indexOf('\n---', 3);
  if (end === -1) return { frontmatter: '', body: text };
  const nl = text.indexOf('\n', end + 1);
  return {
    frontmatter: text.slice(4, end),
    body: nl === -1 ? '' : text.slice(nl + 1),
  };
}

/**
 * Read a scalar out of the frontmatter block. Only the flat `key: value`
 * shape is supported — that is all the print sheet needs, and a real YAML
 * parser would be a dependency for four fields.
 */
export function frontmatterValue(frontmatter, key) {
  const m = new RegExp(`^${key}\\s*:\\s*(.+)$`, 'm').exec(frontmatter);
  if (!m) return null;
  return m[1].trim().replace(/^['"]|['"]$/g, '') || null;
}

/** Every `##` heading in the body, in document order, as plain text. */
export function extractHeadings(body) {
  const out = [];
  for (const line of body.split('\n')) {
    const m = /^##\s+(.+?)\s*$/.exec(line);
    if (m && !/^#/.test(m[1])) out.push(stripInlineMarkup(m[1]));
  }
  return out;
}

/** Drop markdown emphasis and stray tags — for headings and plain-text use. */
export function stripInlineMarkup(s) {
  return String(s)
    .replace(/<[^>]+>/g, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .trim();
}

/**
 * The chapter's summary section body, or null.
 *
 * Tries the canonical heading first, then the looser pattern, so a chapter
 * that words its heading differently is still caught rather than silently
 * falling back. Returns everything up to the next `##` (in practice the
 * summary is the last section, but that is not assumed).
 */
export function extractSummary(body) {
  const lines = body.split('\n');
  const findFrom = (pattern) => {
    const start = lines.findIndex((l) => pattern.test(l));
    if (start === -1) return null;
    let end = lines.length;
    for (let i = start + 1; i < lines.length; i++) {
      if (/^##\s/.test(lines[i])) { end = i; break; }
    }
    const section = lines.slice(start + 1, end).join('\n').trim();
    return section.length > 0 ? section : null;
  };
  return findFrom(SUMMARY_HEADING) ?? findFrom(SUMMARY_HEADING_LOOSE);
}

/* ── rendering ─────────────────────────────────────────────────────────── */

function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * Inline formatting. Everything is escaped first, then the small set of tags
 * the notes legitimately use is restored — so chapter text can never inject
 * markup, while `<sup>`, `<sub>` and `<br />` keep working.
 */
export function inlineHtml(s) {
  let out = escapeHtml(s);
  out = out.replace(/&lt;(\/?)(sup|sub|strong|em|code)&gt;/g, '<$1$2>');
  out = out.replace(/&lt;br\s*\/?&gt;/g, '<br />');
  out = out.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  out = out.replace(/(^|[^*\w])\*([^*\n]+)\*/g, '$1<em>$2</em>');
  out = out.replace(/`([^`]+)`/g, '<code>$1</code>');
  return out;
}

const isFormulaOpen = (l) => /^\s*<div class="formula">/.test(l);
const isTableRow = (l) => /^\s*\|/.test(l);
const isBullet = (l) => /^\s*(?:[-+]|\*(?!\*))\s+\S/.test(l);
const bulletText = (l) => l.replace(/^\s*(?:[-+]|\*)\s+/, '');

function renderTable(rows) {
  // A pipe table: header, an alignment row, then body rows. The alignment row
  // is dropped; anything else is data.
  const cells = (row) =>
    row.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map((c) => c.trim());
  const body = rows.filter((r) => !/^\s*\|[\s:|-]+\|?\s*$/.test(r));
  if (body.length === 0) return '';
  const [head, ...rest] = body;
  const th = cells(head).map((c) => `<th>${inlineHtml(c)}</th>`).join('');
  const trs = rest
    .map((r) => `<tr>${cells(r).map((c) => `<td>${inlineHtml(c)}</td>`).join('')}</tr>`)
    .join('');
  return `<table><thead><tr>${th}</tr></thead><tbody>${trs}</tbody></table>`;
}

/**
 * Render a summary section to print-ready HTML.
 *
 * Blocks recognised: the `formula` box, pipe tables, bullet lists (with
 * hanging indented continuation lines), and paragraphs. Anything else lands
 * in a paragraph rather than being dropped.
 */
export function renderSummaryHtml(md) {
  const lines = String(md).split('\n');
  const out = [];
  let i = 0;

  const flushParagraph = (buf) => {
    const text = buf.join(' ').trim();
    if (text) out.push(`<p>${inlineHtml(text)}</p>`);
  };

  while (i < lines.length) {
    const line = lines[i];

    if (!line.trim()) { i++; continue; }

    // Formula box — one line, or opened and closed across several.
    if (isFormulaOpen(line)) {
      const chunk = [];
      let l = line;
      let closed = false;
      while (i < lines.length) {
        chunk.push(lines[i]);
        if (/<\/div>/.test(lines[i])) { closed = true; i++; break; }
        i++;
      }
      const inner = chunk
        .join(' ')
        .replace(/^\s*<div class="formula">/, '')
        .replace(/<\/div>\s*$/, '')
        .trim();
      out.push(`<div class="formula">${inlineHtml(inner)}</div>`);
      if (!closed) { /* unclosed div — treated as ending at EOF, never thrown */ }
      continue;
    }

    // Pipe table.
    if (isTableRow(line)) {
      const rows = [];
      while (i < lines.length && isTableRow(lines[i])) rows.push(lines[i++]);
      out.push(renderTable(rows));
      continue;
    }

    // Bullet list. A line indented under a bullet continues that bullet.
    if (isBullet(line)) {
      const items = [];
      while (i < lines.length) {
        const l = lines[i];
        if (isBullet(l)) { items.push([bulletText(l)]); i++; continue; }
        if (l.trim() && /^\s+\S/.test(l) && items.length > 0) {
          items[items.length - 1].push(l.trim());
          i++;
          continue;
        }
        break;
      }
      const lis = items.map((parts) => `<li>${inlineHtml(parts.join(' '))}</li>`).join('');
      out.push(`<ul>${lis}</ul>`);
      continue;
    }

    // Paragraph — runs to a blank line or the start of another block.
    const buf = [];
    while (i < lines.length) {
      const l = lines[i];
      if (!l.trim() || isFormulaOpen(l) || isTableRow(l) || isBullet(l)) break;
      buf.push(l.trim());
      i++;
    }
    flushParagraph(buf);
  }

  return out.join('\n');
}

/**
 * Parse one chapter's raw MDX into everything a print sheet needs.
 *
 * `mode` reports which path produced the sheet:
 *   'summary'  — the chapter's own one-page summary was found and rendered.
 *   'fallback' — no parseable summary; the caller renders the section
 *                headings as a checklist instead. Never a broken page.
 */
export function parseOnePager(raw) {
  const { frontmatter, body } = stripFrontmatter(raw);
  const headings = extractHeadings(body);
  const summary = extractSummary(body);
  const html = summary ? renderSummaryHtml(summary) : '';
  return {
    mode: html.trim() ? 'summary' : 'fallback',
    html,
    headings,
    lastVerified: frontmatterValue(frontmatter, 'last_verified'),
    sourceLabel: frontmatterValue(frontmatter, 'sourceLabel'),
    readTime: frontmatterValue(frontmatter, 'readTime'),
  };
}
