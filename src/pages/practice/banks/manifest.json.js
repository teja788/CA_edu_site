/**
 * The deck manifest, at /practice/banks/manifest.json.
 *
 * Every question in the course, reduced to what the filters and samplers
 * need — id, topic, chapter metadata, case grouping. The quiz page fetches
 * this once, builds the whole deck from it, and only then goes after the
 * bodies of the questions it will actually display.
 */
import { buildBanks, buildManifest } from '../../../scripts/banks.js';

export function GET() {
  return new Response(JSON.stringify(buildManifest(buildBanks())), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}
