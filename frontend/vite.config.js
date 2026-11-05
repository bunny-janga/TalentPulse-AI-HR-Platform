import { defineConfig } from 'vite';

// Backend route prefixes that the dev server forwards to FastAPI.
const API_PREFIXES = [
  'auth', 'employees', 'departments', 'org', 'leave', 'reviews', 'chat',
  'policies', 'surveys', 'onboarding', 'attrition', 'ai', 'admin', 'notifications',
];

/**
 * FastAPI serves index.html at /ui and mounts backend/static at /static.
 * Relative URLs in index.html therefore resolve from "/" (not "/ui/"), so the
 * hashed bundle must be addressed as ./static/assets/... for the browser to
 * find it. Lazy chunks are fetched relative to their importer and need no help.
 */
const staticPrefix = () => ({
  name: 'talentpulse-static-prefix',
  apply: 'build',
  transformIndexHtml: {
    order: 'post',
    handler: (html) => html.replaceAll('"./assets/', '"./static/assets/'),
  },
});

export default defineConfig({
  base: './',
  // Vite's built-in esbuild handles JSX, so no React plugin dependency is needed.
  esbuild: { jsx: 'automatic' },
  plugins: [staticPrefix()],
  build: {
    outDir: '../backend/static',
    emptyOutDir: true,
    assetsDir: 'assets',
    target: 'es2022',
    sourcemap: false,
  },
  server: {
    port: 5173,
    proxy: {
      [`^/(${API_PREFIXES.join('|')})(/|$)`]: {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
});
