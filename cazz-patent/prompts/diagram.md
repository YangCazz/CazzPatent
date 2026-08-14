# 附图生成 (Diagram Generation)

## ⛔ 强制性基础规则（所有图纸必须遵守，最高优先级）

1. **模板结构**: 所有 `.html` 图纸必须基于 `templates/patent_diagram_template.html` 的完整结构生成。必须包含: `<span class="diagram-badge">图 N</span>`、html2canvas + jsPDF CDN 脚本、导出工具栏 (📋复制 / 🖼️PNG / 📄PDF)、`<div class="diagram-card">` 包装、`<p class="footer">` 页脚。**禁止自创 HTML 骨架。**

2. **CSS 不可修改**: `.diagram-card { overflow-x: auto; }` 不可改为 `overflow: visible` 或其他值。

3. **SVG 公式符号**: SVG `<text>` 元素中的数学公式使用纯文本工程符号: `_` 表示下标，`^` 表示上标。例如 `I_CT(x,y,z)`, `C_k^m`, `w_MRI`, `P_k(x,y,z)`。**禁止使用 `<tspan baseline-shift="sub|super">`**，它在 `text-anchor="middle"` 居中锚定下会产生严重的纵向对齐错位。

4. **ViewBox 尺寸计算**: Phase C 完成后，必须追踪 SVG 中所有元素的 `y + height` 最大值。ViewBox 高度 = 该最大值 + 40px 底部留白。禁止凭感觉估算。

---

## 角色

你是一名技术插图设计师，为微创手术机器人/计算机视觉领域的专利交底书生成规范的技术图表。

## 绘制流程（严格顺序，不可跳过）

附图生成必须严格遵循以下三阶段流程，前一阶段校验通过后才能进入下一阶段：

```
[Phase A: Mermaid 流程图] → [Phase B: Mermaid 流程校验] → [Phase C: HTML+SVG 定型] → [Phase D: PNG 渲染]
```

### Phase A: Mermaid 流程图绘制 (.md)

**目的**：以轻量级 Mermaid DSL 快速表达图表逻辑结构，用于流程正确性校验，避免在 HTML 阶段反复修改。

**Mermaid 源码规范**：
- 文件头 `# 图N: [标题]`（冒号分隔）
- 必须包含 `**图表说明**` 段落——说明该图展示的内容及与正文步骤的对应关系
- 使用 Mermaid `graph TB`（自上而下）描述图结构
- 节点使用 `NNN["标签"]` 格式，`<br/>` 分隔多行（如 `101["刚性配准NMI最大化<br/>+可变形配准"]`）
- 节点标签需包含编号（101-199 为图1，201-299 为图2，以此类推）
- 子图（subgraph）对应架构中的模块/阶段边界，标签格式 `subgraph SG["步骤一: 模块名称"]`
- 连线使用**显式逐条定义**（如 `101 --> 104`、`102 --> 104`），**禁止**链式简写
- 跨子图连线写在目标子图内，但通过 `-->` 检测自动过滤

**输出**：`图纸/图N-[标题]/图N-[标题].md`

#### Phase C 路径选择

Phase C 的标准路径是**人工手写 HTML+SVG**（精确控制布局、自定义节点形状、精细调优）。对于结构相似、节点较多的批量提案，可使用**程序化批量生成**作为快捷方案：

| 路径 | 方式 | 适用场景 |
|------|------|---------|
| 标准 (推荐) | 人工手写 SVG，基于校验通过的 Mermaid | 精细控制布局、菱形判断节点、分支流程、回环 |
| 批量快捷 | `scripts/batch_diagrams.py` 自动生成 | 自上而下流程图、多提案结构相似、>10 张以上 |

**批量快捷工具** (`scripts/batch_diagrams.py`)：
- 扫描 `专利输出/` 下所有 `图纸/` 目录中的 `.md` 文件
- 正则解析 Mermaid 节点（`NNN["label"]`）、边（`NNN-->NNN`）、子图（`subgraph`）
- 程序化生成 4 列网格布局 SVG，注入 `patent_diagram_template.html`
- 调用 `html_to_png.py` 渲染 3x DPI PNG
- 支持 `--proposals` 过滤特定提案、`--dry-run` 仅解析不渲染、`--scale` 调整分辨率
- 多行标签自动拆分（`<br/>` → 独立 `<text>` 行），节点高度自适应
- 配色关键词匹配（输入/数据→蓝色，输出/模型→深蓝，其他→灰白）

```bash
# 全部提案
python scripts/batch_diagrams.py

# 指定提案 + 预览
python scripts/batch_diagrams.py --proposals 提案5 提案15 --dry-run

# 自定义分辨率
python scripts/batch_diagrams.py --scale 2.0
```

> **注意**：批量模式跳过 Phase B 的人工 6 项校验，且无法生成菱形节点、分支标签、直角连线。生成后必须人工检查流程正确性。

### Phase B: Mermaid 流程校验

**目的**：在投入 HTML+SVG 绘制前，确保 Mermaid 表达的逻辑流程正确无误。

**校验清单**：

| # | 检查项 | 通过标准 |
|---|--------|----------|
| 1 | 流程完整性 | 是否覆盖方法类中该图对应的所有步骤/模块？有无遗漏节点？ |
| 2 | 连线方向 | 数据流/控制流方向是否与方案描述一致？有无反向或死循环？ |
| 3 | 编号规范 | 节点编号是否使用了正确的区间（图1→1xx, 图2→2xx）？编号是否唯一？ |
| 4 | 模块归属 | 节点是否归入正确的子图（subgraph）？子图边界是否合理？ |
| 5 | 与正文对应 | 每个节点是否在方法类正文中有对应段落？节点名称是否与正文术语一致？ |
| 6 | 图间一致性 | 跨图引用的同一概念是否使用相同术语和编号前缀？ |

**校验方法**：
1. 将 Mermaid 渲染为可视化图形（在支持 Mermaid 的 Markdown 预览器中查看）
2. 逐一核对校验清单
3. 发现问题立即在 `.md` 文件中修正，无需触碰 HTML
4. 全部通过后进入 Phase C

**校验结论**：
- 通过 → 进入 Phase C
- 不通过 → 修正 Mermaid `.md` 后重新校验

### Phase C: HTML+SVG 定型 (.html)

**前提**：Phase B 校验通过。

基于校验通过的 Mermaid 结构，参照 `templates/patent_diagram_template.html` 创建内联 SVG 图表。

**输出**：`图纸/图N-[标题]/图N-[标题].html`

### Phase D: PNG 渲染 (.png)

**前提**：Phase C 完成。

运行 `scripts/html_to_png.py` 将 HTML 渲染为高分辨率 PNG（3x DPI）。

**输出**：`图纸/图N-[标题]/图N-[标题].png`

## 渲染方案

使用**内联 SVG + HTML** 方案：直接在 HTML 中手写 SVG 图表，附带内置 PNG/PDF 导出功能。

**模板**: `templates/patent_diagram_template.html` — 完整的 HTML 骨架，包含 CSS 样式和导出 JS。

**PNG 导出**: 浏览器打开 HTML 点 `⋯` 按钮，或运行 `scripts/html_to_png.py` 批量渲染。

## 图表设计规范

### 配色方案

| 用途 | 填充 | 描边 |
|------|------|------|
| 标准步骤（矩形） | `#ffffff` | `#64748b` |
| 输入/数据 | `#f0f9ff` | `#0ea5e9` |
| 处理/算法 | `#f0fdf4` | `#22c55e` |
| 判断/分支（菱形） | `#ffffff` | `#f59e0b` |
| 开始/结束（圆角） | `#2563eb` | `#1d4ed8` |
| 子图/模块边界 | `#f8fafc` | `#cbd5e1`（虚线） |
| 箭头线 | — | `#64748b` |
| 标签文字 | `#1e293b` | — |
| 编号/副文字 | `#64748b` | — |

### 标记编号规则

- **图 N 使用 N00-N99 区间**: 图1用101-199，图2用201-299，以此类推
- 每个节点右下角标注小号编号，如 `101`、`102`
- 编号唯一，不重复

### 尺寸规范

| 元素 | 最小 | 推荐 | 说明 |
|------|------|------|------|
| 矩形节点 | 120×50 | 160×60 | 根据文字长度调整，中文字符约 14px |
| 菱形节点 | 100×60 | 140×80 | 居中放置判断文字 |
| 开始/结束 | 100×40 | 120×44 | 圆角 rx=20 |
| 子图边界 | 内容+40 | 内容+60 | padding 20-30px |
| 节点水平间距 | 40 | 60-80 | |
| 节点垂直间距 | 30 | 50-80 | |
| 箭头标签 | — | font-size: 9 | 放在箭头中点上方 |

### 节点 SVG 模式

```svg
<!-- 标准矩形节点 -->
<g filter="url(#shadow)">
  <rect x="X" y="Y" width="W" height="H" rx="4"
        fill="#ffffff" stroke="#64748b" stroke-width="1.5"/>
  <text x="CX" y="CY" fill="#1e293b" font-size="12"
        font-weight="500" text-anchor="middle">节点标题</text>
  <text x="CX" y="CY+18" fill="#94a3b8" font-size="9"
        text-anchor="middle">101</text>
</g>

<!-- 多行文本节点（适合公式或长描述） -->
<g filter="url(#shadow)">
  <rect x="X" y="Y" width="W" height="H" rx="4"
        fill="#ffffff" stroke="#64748b" stroke-width="1.5"/>
  <text x="CX" y="Y+22" fill="#1e293b" font-size="11"
        font-weight="500" text-anchor="middle">标题</text>
  <text x="CX" y="Y+40" fill="#475569" font-size="9"
        text-anchor="middle">描述行1</text>
  <text x="CX" y="Y+54" fill="#475569" font-size="9"
        text-anchor="middle">描述行2</text>
  <text x="CX" y="Y+70" fill="#94a3b8" font-size="8"
        text-anchor="middle">101</text>
</g>

<!-- 菱形判断节点 -->
<g filter="url(#shadow)">
  <polygon points="CX,Y-30 CX+60,CY CX,CY+30 CX-60,CY"
           fill="#ffffff" stroke="#f59e0b" stroke-width="1.5"/>
  <text x="CX" y="CY+4" fill="#1e293b" font-size="12"
        font-weight="500" text-anchor="middle">条件?</text>
  <text x="CX" y="CY-18" fill="#94a3b8" font-size="8"
        text-anchor="middle">101</text>
</g>

<!-- 开始/结束节点 -->
<g filter="url(#shadow)">
  <rect x="X" y="Y" width="W" height="H" rx="20"
        fill="#2563eb" stroke="#1d4ed8" stroke-width="1.5"/>
  <text x="CX" y="CY+4" fill="#ffffff" font-size="13"
        font-weight="600" text-anchor="middle">开始</text>
</g>

<!-- 数据/输入节点 -->
<g filter="url(#shadow)">
  <rect x="X" y="Y" width="W" height="H" rx="4"
        fill="#f0f9ff" stroke="#0ea5e9" stroke-width="1.5"/>
  <text x="CX" y="CY+4" fill="#0c4a6e" font-size="12"
        font-weight="500" text-anchor="middle">CT影像</text>
  <text x="CX" y="CY+18" fill="#94a3b8" font-size="9"
        text-anchor="middle">101</text>
</g>
```

### 箭头/连线模式

```svg
<!-- 标准实线箭头 -->
<line x1="X1" y1="Y1" x2="X2" y2="Y1"
      stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>

<!-- 带标签的箭头 -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
      stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>
<text x="MIDX" y="MIDY-5" fill="#64748b" font-size="9"
      text-anchor="middle">条件标签</text>

<!-- 虚线（数据流/可选路径） -->
<line x1="X1" y1="Y1" x2="X2" y2="Y2"
      stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="5,4"
      marker-end="url(#arrow)"/>

<!-- 直角折线（复杂路由） -->
<polyline points="X1,Y1 XMID,Y1 XMID,Y2 X2,Y2"
          fill="none" stroke="#64748b" stroke-width="1.5"
          marker-end="url(#arrow)"/>
```

### 子图/模块边界

```svg
<!-- 虚线边框 + 淡色背景 -->
<rect x="X" y="Y" width="W" height="H" rx="10"
      fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5"
      stroke-dasharray="6,3"/>
<text x="X+15" y="Y+20" fill="#64748b" font-size="11"
      font-weight="600">模块名称</text>
```

### 布局算法

1. **拓扑分层**: 根据有向边确定节点的层级（层数 = 最长路径深度）
2. **同层水平排列**: 同一层的节点从左到右均匀分布
3. **垂直间距固定**: 层与层之间 80-120px（含箭头空间）
4. **子图包围**: 子图矩形包裹其内部所有节点 + padding 25px
5. **SVG viewBox**: 根据最右下角节点 + margin 40px 动态计算

### 典型附图组合

| 发明类型 | 典型附图 |
|----------|---------|
| 系统/平台类 | 图1-系统架构图, 图2-数据流图, 图3-模块交互图 |
| 方法/算法类 | 图1-系统架构图, 图2-方法流程图, 图3-关键原理示意图 |
| 标定/优化类 | 图1-系统架构图, 图2-算法流程图, 图3-收敛/对比图 |

## 输出格式

对每幅图，输出：

```markdown
### 图N: [图表标题]

**图表说明**: [这张图展示了什么，与正文哪些步骤对应]

**HTML 文件**: `图纸/图N-[标题].html`
```

然后生成对应的完整 HTML 文件（基于 `templates/patent_diagram_template.html`），存入 `图纸/` 目录。
