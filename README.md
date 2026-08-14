# CazzPatent

<p align="center"><i>A DeepSeek Harness skill that turns technical proposals into submission-ready patent disclosures — with verified technical diagrams, LaTeX→OMML math rendering, a self-improving memory, and Markdown / Word / PDF export.</i></p>

---

## What is this?

CazzPatent is a **DeepSeek Harness skill** (`cazz-patent`) that acts as an AI patent agent. It walks a raw technical idea through an 8-stage pipeline — environment check, material parsing, patent-point mining, prior-art search, drafting + diagram generation, review & iteration, reflection & learning, and multi-format export — producing a disclosure ready for firm review.

> - **Markdown** → LaTeX formulas, CJK typography, embedded diagrams
> - **Word (.docx)** → OMML native equations, table formatting, professional layout
> - **PDF** → Word COM / LibreOffice / weasyprint triple-engine fallback
> - **Diagrams** → Mermaid logic verification → HTML+SVG → high-res PNG (3× DPI)

## Installation

The skill is a directory bundle at `cazz-patent/`. Install it through any DeepSeek Harness skill root:

**1. User-level** — available to every project:

```sh
git clone https://github.com/<you>/CazzPatent ~/.dsh/skills/cazz-patent
```

**2. Project-level** — one project only: copy `cazz-patent/` into `<project>/.dsh/skills/`.

**3. Custom root** — clone anywhere and point `customSkillDirs` at the repo root in your `cordis.yml`:

```yaml
customSkillDirs:
  - /absolute/path/to/CazzPatent
```

## Python environment

The skill's tooling is Python 3.10+:

```sh
pip install -r requirements.txt
playwright install chromium

# Windows DOCX → PDF (highest fidelity, optional)
pip install pywin32
```

## Usage

In a DeepSeek Harness session, either:

- invoke the skill directly: `/skill:cazz-patent 请基于以下技术方案撰写专利交底书…`, or
- let the model auto-load it through the `skill` tool when it detects a patent-writing task.

The skill drives the 8-stage workflow, pausing for confirmation between stages. Personalize the identity placeholder first (see [Configuration](#configuration)).

## Configuration

The skill is identity-neutral. One placeholder is resolved from your input material at run time:

- `{提案人}` — the proposer's name, taken from the **基本信息** table's `提案人` field (or your material's file-name prefix); the model asks when it is missing.

Output directories (`专利输出/`, `需求输出/`) are created under your working directory and are never part of the skill.

## Pipeline

| Stage | What it does | Output |
|:-----:|-------------|--------|
| **0. 环境预检** | Checks Python, Playwright/Chromium, python-docx, pywin32 | Environment readiness report |
| **1. 素材解析** | Reads proposal, exemplars, company template; learns style & terminology | Material analysis report |
| **2. 专利点挖掘** | Extracts patentable points; scores novelty / inventiveness / practicality | Patent point checklist |
| **3. 查新检索** | Web search for closest prior art; flags high-risk matches | Prior-art comparison |
| **4. 交底书撰写** | Drafts all chapters + diagrams (Phase A→D) | `交底书_v1.md` + figures |
| **5. 审核迭代** | Template compliance + content review; multi-round iteration | `迭代记录/v{N}-to-v{N+1}.md` |
| **5.5. 反思沉淀** | Extracts reusable rules, deduplicates, dual-scoring, regenerates injections | Updated `memory/` |
| **6. 文档导出** | MD → DOCX (OMML) → PDF (triple-engine) + post-export verification | `.md` + `.docx` + `.pdf` |

## Capabilities

### LaTeX → OMML equation engine

The DOCX engine (`scripts/md_to_docx.py`) converts LaTeX directly into **Word-native OMML equations** — no MathML, no images. Every formula renders as an editable, high-fidelity Word equation: Greek & variants, large operators, fractions/radicals, relations, sets & logic, arrows, accents, `\mathbb`/`\mathbf`/`\mathcal`, 6 matrix delimiters, `\underbrace`/`\overbrace`, and text operators — **170+ symbols**.

### Diagram pipeline

Every figure passes a **verified 4-phase process** before entering the disclosure:

```
Phase A   Mermaid DSL        ── logic sketch, fast iteration
Phase B   6-point checklist  ── completeness / flow / numbering / scoping / alignment
Phase C   HTML + SVG         ── polished vector art, patent spec
Phase D   3× DPI PNG         ── Playwright render, print-ready
```

Batch mode (`scripts/batch_diagrams.py`) automates Phase C+D from Mermaid `.md` for proposals with many structurally similar diagrams.

### Self-improving memory

Every proposal's review iteration yields rules that auto-inject into future proposals — fix once, never repeat. Dual-scoring (`confirm_count` + `effectiveness`), four-layer injection governance, and a shipped seed corpus of 9 rules distilled from 15 real proposals.

## Directory layout

```
CazzPatent/
├── cazz-patent/                 # the DSH skill bundle
│   ├── SKILL.md                 # entry point (8 stages, DSH frontmatter)
│   ├── prompts/                 # mine / search / draft / diagram / review / reflect
│   ├── scripts/                 # md_to_docx / docx_to_pdf / html_to_png / batch_diagrams / html_to_pdf / template_loader
│   ├── templates/               # disclosure_template.md + patent_diagram_template.html
│   └── memory/                  # ledger.json + corrections/ + injections/ + patterns/
├── tests/                       # smoke tests for the Python tooling
├── README.md / README_zh.md
├── requirements.txt
├── LICENSE
└── .gitignore
```

## Requirements

| Dependency | Purpose | Required? |
|-----------|---------|:---------:|
| **python-docx** | MD → DOCX (OMML equations, CJK, tables) | Yes |
| **Playwright + Chromium** | HTML/SVG → high-res PNG rendering | Yes |
| **pywin32** | DOCX → PDF via Word COM (Windows) | Recommended* |
| **LibreOffice** | DOCX → PDF (cross-platform fallback) | Optional |
| **weasyprint** | DOCX → PDF (pure Python fallback) | Optional |

<sub>*Windows: Word COM produces the highest PDF fidelity.</sub>

## Tests

```sh
pip install pytest
python -m pytest tests/
```

## License

MIT — see [LICENSE](LICENSE).
