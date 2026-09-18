import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';

/**
 * `site` drives canonicals, og:url, og:image, the sitemap and robots.txt, so a
 * wrong value is worse than an obviously fake one — it points every crawler and
 * every shared link at a domain that is not the site.
 *
 * Resolution order:
 *   SITE_URL                        — set this once a real domain exists
 *   VERCEL_PROJECT_PRODUCTION_URL   — set by Vercel; the PRODUCTION domain, so
 *                                     preview deploys keep production canonicals
 *                                     instead of each claiming their own
 *   the placeholder                 — local builds, and a loud signal if neither
 *                                     of the above is set in a real deploy
 */
const site =
  process.env.SITE_URL ||
  (process.env.VERCEL_PROJECT_PRODUCTION_URL
    ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
    : 'https://adhyayan.example');

export default defineConfig({
  site,
  output: 'static',
  integrations: [mdx(), sitemap()],
});
