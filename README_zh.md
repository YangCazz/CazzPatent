# CazzPatent

<p align="center"><i>一个 DeepSeek Harness 技能，把技术方案转化为可直接提交的专利交底书——含经校验的技术流程图、LaTeX→OMML 公式渲染、自改进记忆，以及 Markdown / Word / PDF 三格式导出。</i></p>

---

## 这是什么？

CazzPatent 是一个 **DeepSeek Harness 技能**（`cazz-patent`），扮演 AI 专利代理人的角色。它把原始技术方案送进 8 阶段管线——环境预检、素材解析、专利点挖掘、查新检索、撰写+附图、审核迭代、反思沉淀、多格式导出——产出可直接提交代理机构审查的交底书。

> - **Markdown** → LaTeX 公式、CJK 排版、内嵌图表
> - **Word (.docx)** → OMML 原生方程式、表格格式化、专业排版
> - **PDF** → Word COM / LibreOffice / weasyprint 三级引擎降级
> - **附图** → Mermaid 逻辑校验 → HTML+SVG → 高清 PNG（3× DPI）

## 安装

技能是一个目录包，位于 `cazz-patent/`。可通过任意 DeepSeek Harness 技能根目录安装：

**1. 用户级**——对所有项目可用：

```sh
git clone https://github.com/<you>/CazzPatent ~/.dsh/skills/cazz-patent
```

**2. 项目级**——仅单个项目：把 `cazz-patent/` 复制到 `<project>/.dsh/skills/`。

**3. 自定义根目录**——克隆到任意位置，在 `cordis.yml` 里把 `customSkillDirs` 指向仓库根目录：

```yaml
customSkillDirs:
  - /absolute/path/to/CazzPatent
```

## 插件（Cordis 工具）

Phase 2 新增一个 Cordis 插件，把 Python 脚本包装成五个确定性工具（`patent_md_to_docx`、`patent_docx_to_pdf`、`patent_render_diagram`、`patent_batch_diagrams`、`patent_html_to_pdf`）。作为 bundle 安装：

```sh
dsh plugin --profile demo add github:you/CazzPatent#<sha>
```

工具清单、配置与构建详见 [plugin/README.md](plugin/README.md)。

## Python 环境

技能工具链为 Python 3.10+：

```sh
pip install -r requirements.txt
playwright install chromium

# Windows DOCX → PDF（最高保真度，可选）
pip install pywin32
```

## 使用方式

在 DeepSeek Harness 会话中，任选其一：

- 直接调用技能：`/skill:cazz-patent 请基于以下技术方案撰写专利交底书…`；
- 或让模型在识别到专利撰写任务时通过 `skill` 工具自动加载。

技能随后驱动 8 阶段工作流，并在阶段之间暂停确认。运行前请先个性化身份占位符（见[配置](#配置)）。

## 配置

技能本身与身份无关。一个占位符在运行时从你的素材中解析：

- `{提案人}` —— 提案人姓名，取自「基本信息」表的「提案人」字段（或素材文件名前缀）；缺失时模型会询问。

输出目录（`专利输出/`、`需求输出/`）创建在你的工作目录下，永远不属于技能本身。

## 工作流

| 阶段 | 说明 | 产出 |
|:---:|------|------|
| **0. 环境预检** | 检查 Python、Playwright/Chromium、python-docx、pywin32 | 环境就绪报告 |
| **1. 素材解析** | 读取技术方案、范例、公司模板；学习风格与术语 | 素材分析报告 |
| **2. 专利点挖掘** | 提取可专利点；评估新颖性/创造性/实用性 | 专利点清单 |
| **3. 查新检索** | 联网检索最接近的现有技术；预警高风险对比文件 | 对比分析报告 |
| **4. 交底书撰写** | 撰写全部章节 + 附图（Phase A→D） | `交底书_v1.md` + 附图 |
| **5. 审核迭代** | 模板合规 + 内容质量审核；多轮迭代 | `迭代记录/v{N}-to-v{N+1}.md` |
| **5.5. 反思沉淀** | 提取可复用规则、去重、双重评分、重生成注入片段 | 更新后的 `memory/` |
| **6. 文档导出** | MD → DOCX（OMML）→ PDF（三级引擎）+ 导出后验证 | `.md` + `.docx` + `.pdf` |

## 核心能力

### LaTeX → OMML 公式引擎

DOCX 引擎（`scripts/md_to_docx.py`）把 LaTeX 直接转换为 **Word 原生 OMML 方程**——不用 MathML、不嵌图片。每个公式渲染为可编辑的高保真 Word 方程：希腊字母及变体、大型运算符、分式/根式、关系符、集合与逻辑、箭头、重音、`\mathbb`/`\mathbf`/`\mathcal`、6 种矩阵定界符、`\underbrace`/`\overbrace`、文本运算符——**350+ 符号**。

### 附图管线

每张图纸在进入交底书前都经过**四阶段严格校验**：

```
Phase A   Mermaid 源码        ── 逻辑草图，快速迭代
Phase B   6 项校验清单        ── 完整性 / 流向 / 编号 / 归属 / 对齐
Phase C   HTML + SVG          ── 精修矢量图，专利规格
Phase D   3× DPI PNG          ── Playwright 渲染，印刷级
```

批量模式（`scripts/batch_diagrams.py`）可从 Mermaid `.md` 自动完成 Phase C+D，适用于大量结构相似的流程图。

### 自改进记忆系统

每次提案的审核迭代经验都会沉淀为规则，自动注入到后续提案——纠正一次，永不重复。双重评分（`confirm_count` + `effectiveness`）、四层注入治理，并随包附带由 15 个真实提案提炼的 9 条种子规则。

## 目录结构

```
CazzPatent/
├── cazz-patent/                 # DSH 技能包
│   ├── SKILL.md                 # 调度入口（8 阶段，DSH frontmatter）
│   ├── prompts/                 # mine / search / draft / diagram / review / reflect
│   ├── scripts/                 # md_to_docx / docx_to_pdf / html_to_png / batch_diagrams / html_to_pdf / template_loader
│   ├── templates/               # disclosure_template.md + patent_diagram_template.html
│   └── memory/                  # ledger.json + corrections/ + injections/ + patterns/
├── tests/                       # Python 工具层冒烟测试
├── README.md / README_zh.md
├── requirements.txt
├── LICENSE
└── .gitignore
```

## 环境要求

| 依赖 | 用途 | 是否必需 |
|------|------|:------:|
| **python-docx** | MD → DOCX（OMML 公式、CJK、表格） | 是 |
| **Playwright + Chromium** | HTML/SVG → 高清 PNG 渲染 | 是 |
| **pywin32** | DOCX → PDF（Windows Word COM） | 推荐* |
| **LibreOffice** | DOCX → PDF（跨平台备选） | 可选 |
| **weasyprint** | DOCX → PDF（纯 Python 兜底） | 可选 |

<sub>*Windows 用户：Word COM 生成的 PDF 保真度最高。</sub>

## 测试

```sh
pip install pytest
python -m pytest tests/
```

## 开源许可

MIT — 详见 [LICENSE](LICENSE)。
