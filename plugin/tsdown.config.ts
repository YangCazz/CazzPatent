import { defineConfig } from 'tsdown'

/** Self-contained build: transpile src/ to lib/ with no project references. */
export default defineConfig({
  entry: ['src/index.ts'],
  outDir: 'lib',
  format: ['esm'],
  platform: 'node',
  target: 'es2024',
  dts: true,
  clean: true,
})
