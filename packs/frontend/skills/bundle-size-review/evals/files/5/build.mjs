import * as esbuild from 'esbuild';
import { writeFileSync } from 'node:fs';

const result = await esbuild.build({
  entryPoints: ['src/main.jsx'],
  bundle: true,
  splitting: true,
  format: 'esm',
  minify: true,
  sourcemap: true,
  target: ['chrome110', 'edge110'],
  outdir: 'dist/assets',
  entryNames: '[name]-[hash]',
  chunkNames: '[name]-[hash]',
  metafile: true,
});

writeFileSync('build/meta.json', JSON.stringify(result.metafile, null, 2));
