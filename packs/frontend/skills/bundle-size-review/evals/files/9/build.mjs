import { build } from 'esbuild';
import { writeFileSync } from 'node:fs';

const result = await build({
  entryPoints: ['src/widget.ts'],
  bundle: true,
  splitting: true,
  format: 'esm',
  minify: true,
  target: ['es2020'],
  outdir: 'dist',
  jsxFactory: 'h',
  jsxFragment: 'Fragment',
  metafile: true,
});

writeFileSync(process.env.META_OUT ?? 'meta.json', JSON.stringify(result.metafile, null, 2));
