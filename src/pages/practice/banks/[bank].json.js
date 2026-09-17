/**
 * One JSON file per chapter bank, at /practice/banks/<slug>.json.
 *
 * The quiz page fetches these lazily — only the banks holding questions it is
 * about to show. Same-origin and not under /_astro/, so the service worker's
 * network-first-with-cache-fallback branch stores them on first use and serves
 * them offline afterwards, which is what keeps offline practice working.
 */
import { buildBanks } from '../../../scripts/banks.js';

export function getStaticPaths() {
  return buildBanks().map((bank) => ({
    params: { bank: bank.slug },
    props: { questions: bank.questions },
  }));
}

export function GET({ props }) {
  return new Response(JSON.stringify(props.questions), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}
