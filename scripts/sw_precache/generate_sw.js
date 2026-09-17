/**
 * Build-time service-worker generator (site audit deferral #7).
 *
 * `astro build` copies public/sw.js to dist/ verbatim, with two placeholders
 * left in it. This script rewrites dist/sw.js with a real precache manifest so
 * the app shell works on a cold, offline first load — not just on pages the
 * student has already visited.
 *
 * What goes in the manifest (deliberately small — the audience is on patchy
 * mobile data): the hashed, immutable CSS/JS in dist/_astro/ plus a handful of
 * shell HTML routes. Chapter pages, the Pagefind index and the question-bank
 * JSON stay with the existing runtime cache.
 *
 * The cache version is a hash of the *contents* of every precached file, so a
 * rebuild that changes anything busts the old precache, and a rebuild that
 * changes nothing rewrites byte-identical output (safe to run twice).
 *
 * Usage: node scripts/sw_precache/generate_sw.js [distDir]
 */

import { createHash } from 'node:crypto';
import { readFileSync, readdirSync, writeFileSync, existsSync, statSync } from 'node:fs';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const DIST = resolve(process.argv[2] || join(ROOT, 'dist'));
const TEMPLATE = join(ROOT, 'public', 'sw.js');

// Hard per-file budget. The install-time download is paid by every first-time
// visitor on mobile data, so nothing large may slip into it silently — the
// mock pages, for instance, still inline their banks and build to ~2 MB each.
// Anything over the budget is skipped (and logged) and left to runtime cache.
const MAX_FILE_BYTES = 150 * 1024;

// Shell routes only. Anything with per-chapter content is left to runtime cache.
// A third element marks a file as exempt from the budget — used once, with a
// reason, never as a convenience.
const SHELL_ROUTES = [
  ['/', 'index.html'],
  ['/dashboard/', join('dashboard', 'index.html')],
  ['/practice/', join('practice', 'index.html')],
  ['/practice/quiz/', join('practice', 'quiz', 'index.html')],
  ['/practice/flashcards/', join('practice', 'flashcards', 'index.html')],
  // The quiz page is a 10 KB shell that is useless without its deck manifest:
  // without this, an offline visitor gets the page and then an error. It is
  // over budget at ~280 KB raw, but compresses to ~50 KB on the wire and is
  // what makes offline practice work at all, so it is exempt deliberately.
  ['/practice/banks/manifest.json', join('practice', 'banks', 'manifest.json'), true],
  ['/404.html', '404.html'], // offline fallback for never-visited URLs
  ['/manifest.webmanifest', 'manifest.webmanifest'],
];

function hashedAssets() {
  const dir = join(DIST, '_astro');
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith('.css') || f.endsWith('.js'))
    .sort()
    .map((f) => ['/_astro/' + f, join('_astro', f)]);
}

const candidates = [...SHELL_ROUTES, ...hashedAssets()]
  .filter(([, file]) => existsSync(join(DIST, file)))
  .map(([url, file, exempt = false]) => {
    const bytes = readFileSync(join(DIST, file));
    return {
      url,
      file,
      exempt,
      bytes: bytes.length,
      hash: createHash('sha256').update(bytes).digest('hex'),
    };
  });

const skipped = candidates.filter((e) => !e.exempt && e.bytes > MAX_FILE_BYTES);
const entries = candidates.filter((e) => e.exempt || e.bytes <= MAX_FILE_BYTES);

if (!entries.length) {
  console.error('generate_sw: nothing found to precache — did `astro build` run? (dist: ' + DIST + ')');
  process.exit(1);
}

// Version derives from every precached file's content, so identical input =>
// identical output (idempotent), and any content change => a new cache name.
const version = createHash('sha256')
  .update(entries.map((e) => e.url + ':' + e.hash).join('\n'))
  .digest('hex')
  .slice(0, 12);

const template = readFileSync(TEMPLATE, 'utf8');
if (!template.includes('__PRECACHE_VERSION__') || !template.includes('__PRECACHE_MANIFEST__')) {
  console.error('generate_sw: public/sw.js is missing the __PRECACHE_VERSION__ / __PRECACHE_MANIFEST__ placeholders.');
  process.exit(1);
}

const manifest = entries.map((e) => "  '" + e.url + "',").join('\n');
const out = template
  .replace('__PRECACHE_VERSION__', version)
  .replace('/* __PRECACHE_MANIFEST__ */', '\n' + manifest + '\n');

const target = join(DIST, 'sw.js');
const unchanged = existsSync(target) && readFileSync(target, 'utf8') === out;
writeFileSync(target, out);

const totalKb = (entries.reduce((n, e) => n + e.bytes, 0) / 1024).toFixed(1);
for (const e of skipped) {
  console.log(
    'generate_sw: skipped ' + e.url + ' (' + (e.bytes / 1024).toFixed(0) +
    ' KB > ' + MAX_FILE_BYTES / 1024 + ' KB budget) — left to runtime cache'
  );
}
console.log(
  'generate_sw: ' + entries.length + ' files, ' + totalKb + ' KB precached, version ' + version +
  (unchanged ? ' (unchanged)' : '')
);
