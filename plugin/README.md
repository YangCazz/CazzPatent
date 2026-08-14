# dsh-cazz-patent (plugin)

A DeepSeek Harness **Cordis plugin** that exposes the CazzPatent Python toolchain as five deterministic, schema-validated tools. Pair it with the `cazz-patent` skill (the instruction brain) for the full experience, or use the tools on their own.

## Tools

| Tool | Wraps | Purpose |
|------|-------|---------|
| `patent_md_to_docx` | `md_to_docx.py` | Markdown → Word (.docx), LaTeX→OMML + CJK + tables |
| `patent_docx_to_pdf` | `docx_to_pdf.py` | Word → PDF (Word COM / LibreOffice / weasyprint) |
| `patent_render_diagram` | `html_to_png.py` | HTML/SVG → high-res PNG (3× DPI) |
| `patent_batch_diagrams` | `batch_diagrams.py` | Batch Mermaid → HTML+SVG+PNG |
| `patent_html_to_pdf` | `html_to_pdf.py` | Markdown/HTML → PDF (weasyprint / Playwright) |

Every tool returns a uniform canonical value: `{ exitCode, timedOut, aborted, stdout, stderr }`.

## Configuration

| Field | Default | Meaning |
|-------|---------|---------|
| `pythonPath` | `python` | Python interpreter used to invoke the scripts. |
| `scriptsDir` | bundled `scripts/` | Directory containing the Python scripts. |
| `defaultTimeoutMs` | `300000` | Foreground timeout for every run. |

Override in a profile's `cordis.patch.yml` (or edit this bundle's `cordis.patch.yml`):

```yaml
- insert:
    - id: cazz-patent-tools
      name: dsh-cazz-patent
      config:
        pythonPath: D:/miniforge3/envs/patent/python.exe
        scriptsDir: /absolute/path/to/CazzPatent/cazz-patent/scripts
```

## Installation

The plugin ships as an npm **bundle** (its `package.json` declares `dsh.bundle`). Install from a git host:

```sh
dsh plugin --profile demo add github:you/CazzPatent#<sha>
# pnpm will ask you to allow the build (the prepare script compiles src/ -> lib/):
#   copy the printed package key into the profile's pnpm-workspace.yaml allowBuilds, then re-run.
# Then boot:
dsh --profile demo
```

Or from a local checkout during development:

```sh
dsh plugin --profile demo add ./plugin
```

## Python environment

The wrapped scripts need Python 3.10+ and the CazzPatent dependencies. Install them into the interpreter referenced by `pythonPath`:

```sh
pip install -r ../requirements.txt
playwright install chromium
# Windows DOCX → PDF (highest fidelity)
pip install pywin32
```

## Build

```sh
pnpm install
pnpm run build   # tsdown transpiles src/ -> lib/
```

The `prepare` script runs the same build automatically after a git install, so the bundle is self-contained without relying on a sibling monorepo checkout.
