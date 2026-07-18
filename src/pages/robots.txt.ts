import type { APIRoute } from 'astro';

/**
 * robots.txt is generated from the site config so the Sitemap URL can
 * never diverge from `site` in astro.config.mjs.
 */
export const GET: APIRoute = ({ site }) => {
  const sitemapURL = new URL('sitemap-index.xml', site);
  const body = `User-agent: *
Allow: /

Sitemap: ${sitemapURL.href}
`;
  return new Response(body, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
};
