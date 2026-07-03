import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// TODO: replace with the real production domain before launch.
export default defineConfig({
  site: 'https://adhyayan.example',
  output: 'static',
  integrations: [sitemap()],
});
