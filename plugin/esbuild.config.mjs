import { build } from 'esbuild'

// Self-contained build: transpile src/index.ts -> lib/index.js without type-checking.
// @deepseek-ai/* are peer dependencies resolved from the dsh installation at runtime,
// so they are marked external rather than bundled.
await build({
  entryPoints: ['src/index.ts'],
  outfile: 'lib/index.js',
  bundle: true,
  format: 'esm',
  platform: 'node',
  target: 'es2022',
  sourcemap: false,
  external: ['@deepseek-ai/*'],
})
