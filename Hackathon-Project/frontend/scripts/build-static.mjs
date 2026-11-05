// Fallback production build that only needs `esbuild` (already a dependency of Vite).
// Usage: node scripts/build-static.mjs   (writes ../backend/static, same layout Vite produces)
import { build } from 'esbuild';
import { createHash } from 'node:crypto';
import { cpSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const out = resolve(root, '../backend/static');
const assets = join(out, 'assets');

rmSync(out, { recursive: true, force: true });
mkdirSync(assets, { recursive: true });

const result = await build({
  entryPoints: { index: join(root, 'src/main.jsx') },
  outdir: assets,
  bundle: true,
  splitting: true,
  format: 'esm',
  target: 'es2022',
  jsx: 'automatic',
  minify: !process.env.NO_MIN,
  sourcemap: false,
  entryNames: '[name]-[hash]',
  chunkNames: 'chunk-[hash]',
  define: { 'process.env.NODE_ENV': '"production"' },
  metafile: true,
  logLevel: 'info',
});

const files = readdirSync(assets);
const js = files.find((f) => f.startsWith('index-') && f.endsWith('.js'));
const css = files.find((f) => f.startsWith('index-') && f.endsWith('.css'));
let html = readFileSync(join(root, 'index.html'), 'utf8');
html = html.replace('<script type="module" src="/src/main.jsx"></script>',
  `${css ? `<link rel="stylesheet" href="./static/assets/${css}" />\n    ` : ''}<script type="module" src="./static/assets/${js}"></script>`);
writeFileSync(join(out, 'index.html'), html);
console.log(`built ${js}${css ? ` + ${css}` : ''} -> ${out}`, createHash('md5').update(html).digest('hex').slice(0, 8));
