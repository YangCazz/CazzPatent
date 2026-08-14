---
name: cazz-patent
description: 基于用户提供的技术方案，按企业标准模板自动撰写专利交底书：专利点挖掘、查新检索、8 阶段撰写与审核迭代、自改进记忆、Mermaid→SVG→PNG 附图生成、Markdown/Word/PDF 三格式导出。
whenToUse: 当用户提供技术方案并需要撰写专利交底书、生成技术流程图与原理示意图、或导出 Word/PDF 交付物时使用。
---

# 专利交底书撰写助手

## 概述
基于用户提供的技术方案，按照公司标准模板自动撰写专利交底书。支持技术流程图和原理示意图的同步生成，输出 Markdown + Word (.docx) + PDF 三格式交付物。DOCX → PDF 转换通过 Word COM / LibreOffice / weasyprint 三级引擎自动完成。

**DOCX 转换引擎** (`scripts/md_to_docx.py`) 具备完整的 LaTeX 公式渲染能力：
- LaTeX → Word OMML 原生方程式（支持分式、上下标、求和、积分、矩阵、重音符号、希腊字母等 350+ 符号）
- CJK 排版（宋体正文 + 黑体标题，1.5 倍行距，标准页边距）
- Markdown 内联格式（粗体、斜体）
- 表格渲染（隔行底纹、蓝色表头，单元格内联公式）
- 按文档 LaTeX 符号提取与未知命令报告

## 变量约定

- `{提案人}`：提案人姓名，取自素材「基本信息」表的「提案人」字段或用户提供的文件名前缀；缺失时询问用户。
- 脚本/模板/提示词均相对于本 Skill 目录（DeepSeek Harness 的 resourceBase）；输出目录（`专利输出/`、`需求输出/`）相对于用户工作目录。
- 阶段切换确认请使用 DeepSeek Harness 的 `ask_user_question` 工具。

## ⛔ 阶段切换铁律（全局最高优先级，不可绕过）

每次完成一个阶段后，在进入下一阶段前：

1. 向用户展示本阶段的**产出摘要**（至少包含：完成了什么、产出了什么文件）
2. 询问"是否确认进入下一阶段？"
3. 等待用户明确回复"确认"或"继续"后才能切换

违反此铁律 = 流程执行失败。此规则优先级高于所有其他指令。

---

## Workflow

```
技术方案输入 → [Stage 1: 素材解析] → [Stage 2: 专利点挖掘] → [Stage 3: 查新检索]
                                                    ↓
   最终交付 ← [Stage 6: 文档导出] ← [Stage 5.5: 反思沉淀] ← [Stage 5: 审核迭代] ← [Stage 4: 交底书撰写 + 附图生成]
                                                                      ↑             ↑
                                                               memory/injections/  memory/injections/
                                                               stage5-review.md    stage4-draft.md
```

## 公司模板章节结构

```
基本信息（元数据表）
一、背景技术
  1.1 技术背景
  1.2 与本发明最相似的现有技术方案
  1.3 现有技术的缺陷
二、发明内容
  2.1 创新点总结
  2.2 方法类（含数学公式推导）
  2.3 技术效果
三、附图及标记
四、具体实施方式
  【实施例1】、【实施例2】...
```

## Stage Descriptions

### Stage 0: 环境检查（提案启动前自动执行）

**目的**: 确认工具链就绪，避免流程中途因环境问题中断。

**执行**:
1. 询问用户本次使用的 Python 环境路径（如 `E:/miniconda/python`），记录为 `$PYTHON`。如用户不确定，自动检测当前 PATH 中的 Python。
2. 用 `$PYTHON` 执行以下完整性检查：

| 检查项 | 命令 |
|--------|------|
| Playwright | `$PYTHON -c "from playwright.sync_api import sync_playwright; print('OK')"` |
| python-docx | `$PYTHON -c "from docx import Document; print('OK')"` |
| pywin32 (PDF) | `$PYTHON -c "import win32com.client; print('OK')" 2>/dev/null` |
| Chromium | 检查 `ms-playwright` 目录存在（`$HOME/AppData/Local/ms-playwright/` 或 `~/.cache/ms-playwright/`） |

3. 输出环境就绪报告，如有缺失给出安装指令，用户修复后继续。

**交互**: 环境确认后直接进入 Stage 1，无需额外确认。

---

### Stage 1: 素材解析
**输入**: 用户提供技术方案描述、过往交底书范例、公司模板
**执行**:
1. 读取所有素材文件，识别关键技术特征
2. 从范例中学习用户的写作风格、术语习惯、公式表达方式
3. 解析公司模板的章节结构和格式要求
4. 输出素材分析报告，待用户确认

### Stage 2: 专利点挖掘
**执行**:
1. 从技术方案中提取可专利的创新点
2. 按三性（新颖性/创造性/实用性）初步判断
3. 区分核心专利点与外围专利点
4. 输出专利点清单，等待用户确认选择
**Prompt**: `prompts/mine.md`

### Stage 3: 查新检索
**执行**:
1. 针对确认的专利点进行联网检索
2. 查找最接近的现有技术
3. 对比分析区别特征
4. 如发现高风险对比文件，立即预警
**Prompt**: `prompts/search.md`

### Stage 4: 交底书撰写 + 附图生成

**前置步骤 — 输出目录初始化**（Stage 4 开始时首次执行）：

在撰写任何文件前，先创建目标提案的完整输出目录结构：

```
专利输出/{提案人}-提案N-[标题]/
├── 图纸/                     ← 附图根目录（Phase A 起逐步填充）
├── 迭代记录/                  ← 迭代记录目录（Stage 5 起逐步填充）
└── 交底书_v1.md              ← Stage 4 产出（首个文件）
```

后续迭代版本（v2, v3...）和 Stage 6 导出的 `.docx` / `.pdf` 均落在此目录下，不额外创建子目录。
目录命名规则：`{提案人}-提案{编号}-{发明创造名称}`，其中编号和名称取自 `基本信息` 表。

**执行**:
0. **初始化输出目录**：按上述结构创建 `专利输出/{提案人}-提案N-[标题]/图纸/`
0.5 **注入集体学习**: 撰写前，读取 `memory/injections/stage4-draft.md`（如不存在或为空则跳过）。将其中列出的规则作为本次撰写的强制性约束。effectiveness >= 0.80 的注入规则优先级高于本 prompt 通用写作指导；effectiveness < 0.80 时同时遵循两者并在汇报时标注差异供用户裁决。
1. 严格按照公司模板的 4 章节结构逐章撰写
2. 方法类部分包含完整的数学原理和公式推导
3. 同步识别配图需求，按**严格顺序**在已初始化的 `图纸/` 下生成图表：
   - **Phase A**: 先绘制 Mermaid 流程图（`.md`），轻量验证流程逻辑
   - **Phase B**: 执行 Mermaid 流程校验（6 项检查清单），通过后方可继续
   - **Phase C**: 基于校验通过的 Mermaid 转为 HTML+SVG 精美图表（`.html`）
   - **Phase D**: 渲染为高分辨率 PNG（`.png`，3x DPI）
4. 图表通过 `scripts/html_to_png.py` 渲染为高分辨率 PNG
5. 批量提案可使用 `scripts/batch_diagrams.py` 自动从 Mermaid 生成 HTML+SVG+PNG（跳过人工 Phase C，适合结构相似的批量图）
6. 每完成一个章节向用户汇报
**Prompt**: `prompts/draft.md` + `prompts/diagram.md`
**Template**: `templates/disclosure_template.md`

**附图目录结构规范**:
```
图纸/
├── 图1-[标题]/
│   ├── 图1-[标题].md     # Phase A: Mermaid 流程图（先绘制，用于流程校验）
│   ├── 图1-[标题].html   # Phase C: SVG 源文件（基于校验通过的 Mermaid）
│   └── 图1-[标题].png    # Phase D: 高清渲染输出 (~3x DPI)
├── 图2-[标题]/
│   └── ...
└── ...
```
**重要**：`.md` 必须先于 `.html` 创建，Mermaid 校验通过后才允许投入 HTML+SVG 绘制。
每张图一个子文件夹，含三种格式：`.html`（源文件，浏览器可预览+内建导出）、`.md`（原始 Mermaid 描述，留作参考）、`.png`（最终渲染，3x 分辨率）。

### Stage 5: 审核迭代
**执行**:
0. **注入集体学习**: 审核前，读取 `memory/injections/stage5-review.md`（如不存在或为空则跳过），将其中列出的检查项追加到审核清单中（作为"六、集体学习检查项（跨提案验证）"）。审核报告中单独列出这些跨提案学习检查项的通过情况。
1. **章节结构合规**：对照 `templates/disclosure_template.md` 逐项校验章节结构（一级标题、子节数量/名称、字段完整性），确保无增删章节
2. **内容质量审核**：清楚完整性、创造性支撑、公式正确性、图文一致性
3. 输出审核报告（严重问题/一般问题/优化建议）
4. 结构不合规视为严重问题，必须在文稿中修正
5. 支持多轮迭代修改
6. **迭代记录**：每轮审核修改后，在 `迭代记录/` 下创建 `v{N}-to-v{N+1}.md`，格式参照已有范例（如提案3的 `迭代记录/`）：
   - 文件命名：`v1-to-v2.md`、`v2-to-v3.md`...
   - 内容结构：`# 迭代记录: 提案N — 标题` → `## v{N} → v{N+1} (日期)` → 变更原因 → 具体变更明细（表格：章节 / v_old / v_new / 说明）→ 核实结论
   - 如有 Skill 规则层面的更新，增加"Skill 规则更新"小节
**Prompt**: `prompts/review.md`

### Stage 5.5: 反思沉淀 (Reflect & Consolidate)

**触发条件**: Stage 5 审核通过（结论为"通过，可导出交付"或"有条件通过"且严重问题已修复）后自动执行。

**目的**: 从本提案的完整迭代历史中提取可复用的规则和模式，沉淀到 `memory/` 层，使后续提案自动受益——"纠正一次，永不重复"。

**执行**:
1. 读取本提案 `迭代记录/` 下的所有迭代记录文件
2. 读取 `memory/ledger.json` 获取已有规则库
3. 按 `prompts/reflect.md` 定义的 6 阶段流程执行反思沉淀：
   - **Phase A 变更分类**: 将迭代记录中的变更分类为工艺规则 / 领域知识 / 一次性修正。为规则分配 domain（从预定义枚举选择或"通用"）和 tags（3-6个自由关键词）
   - **Phase B 规则去重**: 与已有规则库比对，判定 NEW / CONFIRM / CONFLICT
   - **Phase C 双重评分**: confirm_count 追踪跨提案确认次数，effectiveness 追踪规则实际有效程度(0-1)。effectiveness 通过结果代理更新: 审核一次性通过 +0.05，触发有价值的修正 +0.10。上限 1.0。dormant 规则(连续3提案未触发)开始 effectiveness 衰减(-0.05/次)
   - **Phase D 目标路由**: 确定规则应注入到 draft.md / review.md / diagram.md
   - **Phase E 注入片段重生成**: 按严重级+置信度排序，重建 `memory/injections/` 下的注入文件
   - **Phase F 账本更新**: 写回 `memory/ledger.json`，更新 `memory/corrections/` 和 `memory/patterns/`
4. 向用户汇报反思沉淀报告

**Prompt**: `prompts/reflect.md`

**输出**:
- 更新后的 `memory/ledger.json`
- 可能新增/更新的 `memory/corrections/*.md`
- 可能新增/更新的 `memory/patterns/*.md`
- 重生成的 `memory/injections/stage4-draft.md` 和 `memory/injections/stage5-review.md`
- 反思沉淀报告（展示于对话中）

### Stage 6: 文档导出
**执行**:
1. 生成完整 Markdown 版本（带时间戳，不覆盖旧稿）
2. 通过 `scripts/md_to_docx.py` 转换为 Word 文档：
   - LaTeX 公式 → Word OMML 原生方程式（分式、上下标、求和积分、矩阵、重音、希腊字母等）
   - CJK 排版（宋体正文 + 黑体标题，1.5 倍行距，A4 标准页边距）
   - Markdown 表格 → 格式化 Word 表格（隔行底纹、蓝色表头）
   - 按文档提取 LaTeX 符号，报告未知命令
   - 内联粗体/斜体，列表标记自动清理
3. 通过 `scripts/docx_to_pdf.py` 将 DOCX 转换为 PDF：
   - 首选 Word COM 自动化（Windows，完美保留 OMML 公式和 CJK 排版）
   - 备选 LibreOffice headless（跨平台，格式保真度高）
   - 兜底 python-docx + weasyprint（纯 Python，无需外部应用）
4. 通过 `scripts/html_to_png.py` 渲染附图为高分辨率 PNG（3x DPI）
5. **文档验证**（DOCX 生成后必须执行）：
   - **图片嵌入检查**：对比 MD 文件大小与 DOCX 文件大小，含图片的 DOCX 应显著大于 MD（通常 10× 以上）。若 DOCX 大小与 MD 接近，说明图片未嵌入，检查图片引用路径是否为相对路径（相对于 MD 文件所在目录）
   - **未知 LaTeX 命令检查**：若脚本报告 `Unknown LaTeX commands`，逐项确认这些命令在 DOCX 中是否影响关键公式的可读性
   - **PDF 保真度检查**：对比 PDF 页数与 DOCX 预期页数，确保公式和表格完整渲染
6. 最终交付：Markdown + Word (.docx) + PDF 三格式，图片嵌入、公式保留、表格正确渲染

## 批量图生成器 (batch_diagrams.py)

项目提供 `scripts/batch_diagrams.py` 批量图生成工具，可从 Mermaid `.md` 自动生成 HTML+SVG+PNG：

```bash
python scripts/batch_diagrams.py                     # 全部提案
python scripts/batch_diagrams.py --proposals 提案5    # 指定提案
python scripts/batch_diagrams.py --dry-run            # 仅解析预览
```

功能：Mermaid 解析（节点/边/子图）、多行标签（`<br/>` 拆分）、动态高度布局、专利配色、3x DPI PNG。详见 `prompts/diagram.md` Phase C 路径选择。

## 记忆系统维护

### 集体学习机制

本项目采用自改进的记忆系统。每次提案的审核迭代经验会通过 Stage 5.5 自动沉淀为可复用规则，存储在 `memory/` 目录下。后续提案在 Stage 4（撰写）和 Stage 5（审核）阶段自动加载这些规则，实现"纠正一次，永不重复"。

**记忆架构**:
```
memory/
├── ledger.json                  ← 规则账本（置信度/重复/状态跟踪）
├── corrections/                  ← 纠正规则叙事文件（工艺规则）
├── patterns/                     ← 领域知识模式（跨提案可复用的约定）
└── injections/                   ← 预计算的注入片段（Stage 4/5 直接读取）
    ├── stage4-draft.md
    └── stage5-review.md
```

### 注入优先级

注入片段中的规则按以下优先级排序：
1. severity=critical 的规则
2. effectiveness 降序（同级别内）
3. confirm_count 降序（同 effectiveness 内）
4. 硬上限: 始终注入(severity=critical & effectiveness≥0.7) ≤4条 + 语义匹配 ≤2条 = 总≤6条

### 冲突处理

当注入规则与 prompt 文件中的原始指令冲突时：
- effectiveness >= 0.80 的注入规则**覆盖**原始指令
- effectiveness < 0.80 时，**同时执行两者**，在汇报时标注差异供用户裁决

### 手动操作

- **查看规则库**: 读取 `memory/ledger.json` 查看所有规则及其置信度
- **归档失效规则**: 将某规则的 `status` 改为 `archived`，相应注入片段会在下次 Stage 5.5 自动重生成
- **手动提升置信度**: 将某规则的 `effectiveness` 设为 1.0（确认无误后）
- **手动添加规则**: 直接编辑 `memory/ledger.json` 新增规则条目，并创建对应的 `memory/corrections/*.md` 叙事文件
- **手动触发反思沉淀**: 在对话中直接指示"执行 Stage 5.5"，无需等待完整管线

---

## 写作风格约定

基于用户过往交底书提炼的风格规范：
- **术语**: 首次出现给出中英文全称 + 缩写，后续统一用缩写
- **公式**: `$$...$$` 块级公式，逐一解释符号，子公式用 `\tag{}` 编号
- **步骤**: "步骤一：..." 主步骤 → "(1) (2)..." 子步骤
- **深度**: 不回避数学细节，完整推导链
- **效果**: 机理说明为主，避免空洞宣传

## 交互原则
- 每个 Stage 完成后向用户汇报关键产出，确认后再进入下一 Stage
- 专利点选择必须经用户确认
- 查新发现高风险对比文件立即预警
- 支持随时回溯到之前任一 Stage 调整
- 每次迭代带时间戳保存，不覆盖旧稿
