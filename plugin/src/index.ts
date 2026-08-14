/**
 * CazzPatent tool plugin: deterministic wrappers around the patent Python scripts.
 *
 * Each tool validates its arguments, builds a quoted command, and runs the
 * corresponding script in cazz-patent/scripts through the harness shell
 * service. This gives the patent workflow typed, validated, configurable
 * tool entry points instead of raw shell commands.
 *
 * @module dsh-cazz-patent
 */
import type { Context } from '@deepseek-ai/cordis'
import z from '@deepseek-ai/schemastery'
import { defineTool } from '@deepseek-ai/dsh-tools'
import type { ShellRunResult } from '@deepseek-ai/dsh-shell'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

/** Cordis plugin name used by loader diagnostics. */
export const name = 'cazz-patent-tools'

/** This plugin runs Python scripts through the shell capability. */
export const inject = ['tools', 'shell']

/** Plugin configuration (set from cordis.yml). */
export interface Config {
  /** Python interpreter to invoke the scripts with. Defaults to 'python' (resolved from PATH). */
  pythonPath?: string
  /** Directory containing the Python scripts. Defaults to the bundled 'scripts/' next to this plugin. */
  scriptsDir?: string
  /** Foreground timeout applied to every run. Defaults to 300000 (5 min). */
  defaultTimeoutMs?: number
}

/** Schemastery validation for {@link Config}. */
export const Config: z<Config> = z.object({
  pythonPath: z.string().default('python'),
  scriptsDir: z.string(),
  defaultTimeoutMs: z.number().default(300_000),
})

/** Canonical value returned by every tool in this plugin. */
interface ScriptResult {
  exitCode: number | null
  timedOut: boolean
  aborted: boolean
  stdout: string
  stderr: string
}

/** Quote one argv token for the PowerShell/bash shell. */
function quote(arg: string): string {
  return '"' + arg.replace(/"/g, '""') + '"'
}

/** Render a script result as model-facing text. */
function renderResult(r: ScriptResult): string {
  const parts: string[] = []
  const out = r.stdout.trim()
  const err = r.stderr.trim()
  if (out) parts.push(out)
  if (err) parts.push('[stderr]\n' + err)
  if (r.timedOut) parts.push('[timed out]')
  if (r.aborted) parts.push('[aborted]')
  parts.push('[exit code: ' + String(r.exitCode) + ']')
  return parts.join('\n')
}

/** Shared output schema + renderer for every tool. */
const SCRIPT_OUTPUT = {
  schema: {
    type: 'object',
    additionalProperties: false,
    properties: {
      exitCode: { required: true, oneOf: [{ type: 'integer' }, { type: 'null' }] },
      timedOut: { type: 'boolean', required: true },
      aborted: { type: 'boolean', required: true },
      stdout: { type: 'string', required: true },
      stderr: { type: 'string', required: true },
    },
  },
  render: (_args: unknown, value: ScriptResult) => [{ type: 'text', text: renderResult(value) }],
}

export function apply(ctx: Context, config: Config): void {
  const python = config.pythonPath || 'python'
  const scriptsDir = config.scriptsDir || join(dirname(fileURLToPath(import.meta.url)), '..', 'scripts')
  const timeoutMs = config.defaultTimeoutMs ?? 300_000

  /** Run one Python script and normalize the shell outcome into a canonical value. */
  async function runScript(
    script: string,
    rawArgs: readonly string[],
    opts: { workdir?: string; signal?: AbortSignal },
  ): Promise<ScriptResult> {
    const argv = [quote(python), quote(join(scriptsDir, script)), ...rawArgs.map(quote)]
    const command = argv.join(' ')
    const result: ShellRunResult = await ctx.shell.run(ctx.shell.resolve({
      command,
      ...opts.workdir ? { workdir: opts.workdir } : {},
      timeoutMs,
      ...opts.signal ? { signal: opts.signal } : {},
    }))
    return {
      exitCode: result.exitCode,
      timedOut: result.timedOut,
      aborted: result.aborted,
      stdout: result.stdout.text,
      stderr: result.stderr.text,
    }
  }

  ctx.tools.register(defineTool({
    name: 'patent_md_to_docx',
    description: 'Convert a patent disclosure Markdown file to Word (.docx): LaTeX to OMML native equations, CJK typography, tables and image embedding.',
    parameters: {
      input: { type: 'string', required: true, description: 'Path to the input Markdown file.' },
      output: { type: 'string', description: 'Output .docx path (default: disclosure.docx).' },
      workdir: { type: 'string', description: 'Working directory (default: session workspace).' },
    },
    output: SCRIPT_OUTPUT,
    async execute(args, exec) {
      const argv: string[] = [args.input]
      if (args.output) argv.push('-o', args.output)
      return runScript('md_to_docx.py', argv, { workdir: args.workdir, signal: exec.signal })
    },
  }))

  ctx.tools.register(defineTool({
    name: 'patent_docx_to_pdf',
    description: 'Convert a patent disclosure Word (.docx) to PDF via the Word COM / LibreOffice / weasyprint fallback chain.',
    parameters: {
      input: { type: 'string', required: true, description: 'Path to the input .docx file.' },
      output: { type: 'string', description: 'Output .pdf path (default: same directory as input).' },
      workdir: { type: 'string', description: 'Working directory (default: session workspace).' },
    },
    output: SCRIPT_OUTPUT,
    async execute(args, exec) {
      const argv: string[] = [args.input]
      if (args.output) argv.push('-o', args.output)
      return runScript('docx_to_pdf.py', argv, { workdir: args.workdir, signal: exec.signal })
    },
  }))

  ctx.tools.register(defineTool({
    name: 'patent_render_diagram',
    description: 'Render a patent diagram HTML/SVG file to a high-resolution PNG (3x DPI print quality).',
    parameters: {
      input: { type: 'string', required: true, description: 'Path to the diagram HTML file.' },
      output: { type: 'string', description: 'Output PNG path (default: diagram.png).' },
      scale: { type: 'number', description: 'Output scale factor (default: 3.0).' },
      workdir: { type: 'string', description: 'Working directory (default: session workspace).' },
    },
    output: SCRIPT_OUTPUT,
    async execute(args, exec) {
      const argv: string[] = [args.input]
      if (args.output) argv.push('-o', args.output)
      if (args.scale !== undefined) argv.push('--scale', String(args.scale))
      return runScript('html_to_png.py', argv, { workdir: args.workdir, signal: exec.signal })
    },
  }))

  ctx.tools.register(defineTool({
    name: 'patent_batch_diagrams',
    description: 'Batch-generate patent diagrams: Mermaid .md to HTML+SVG+PNG across proposal output folders.',
    parameters: {
      base: { type: 'string', description: 'Base directory containing proposal output folders (default: 专利输出).' },
      proposals: { type: 'array', items: { type: 'string' }, description: 'Filter to specific proposal names (default: all).' },
      dryRun: { type: 'boolean', description: 'Parse Mermaid files and report stats without rendering.' },
      scale: { type: 'number', description: 'PNG output scale factor (default: 3.0).' },
      workdir: { type: 'string', description: 'Working directory (default: session workspace).' },
    },
    output: SCRIPT_OUTPUT,
    async execute(args, exec) {
      const argv: string[] = []
      if (args.base) argv.push('--base', args.base)
      if (args.proposals && args.proposals.length > 0) argv.push('--proposals', ...args.proposals)
      if (args.dryRun) argv.push('--dry-run')
      if (args.scale !== undefined) argv.push('--scale', String(args.scale))
      return runScript('batch_diagrams.py', argv, { workdir: args.workdir, signal: exec.signal })
    },
  }))

  ctx.tools.register(defineTool({
    name: 'patent_html_to_pdf',
    description: 'Convert a patent disclosure Markdown or HTML file to a print-ready PDF (weasyprint / Playwright).',
    parameters: {
      input: { type: 'string', required: true, description: 'Path to the .md or .html file.' },
      output: { type: 'string', description: 'Output .pdf path (default: disclosure.pdf).' },
      workdir: { type: 'string', description: 'Working directory (default: session workspace).' },
    },
    output: SCRIPT_OUTPUT,
    async execute(args, exec) {
      const argv: string[] = [args.input]
      if (args.output) argv.push('-o', args.output)
      return runScript('html_to_pdf.py', argv, { workdir: args.workdir, signal: exec.signal })
    },
  }))
}
