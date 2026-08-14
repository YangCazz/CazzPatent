# assets/ — 品牌图片

本目录存放仓库的品牌图片。当前是 **占位图**，请用 AI 生成的正式图替换同名文件（保持文件名与尺寸不变）。

| 文件 | 尺寸 | 用途 | 状态 |
|------|------|------|------|
| logo.png | 1024 × 1024（1:1） | README 头部图标 + GitHub 社交预览头像 | 占位 |
| banner.png | 1500 × 500（3:1） | README 顶部横幅 | 占位 |
| social-preview.png | 1280 × 640（2:1） | 链接分享预览图（GitHub Settings → Social preview） | 占位 |

---

## Gemini 提示词（可直接复制）

### 1. logo.png（图标）

> Minimal flat vector logo icon for "CazzPatent", an AI-powered patent drafting assistant.
> Concept: a quill pen whose nib merges into a glowing circuit trace that outlines an abstract patent document (a scroll with a wax seal), symbolizing "AI writing patents".
> Style: clean flat design, geometric, modern tech aesthetic, smooth gradient from deep blue #2563eb to violet #8b5cf6, one cyan #22d3ee accent, white or transparent background, icon only (no text), centered, simple enough to stay legible at 32px.
> Aspect ratio: 1:1, high resolution.

### 2. banner.png（横幅）

> Wide horizontal hero banner (aspect ratio about 3:1) for "CazzPatent", an AI patent disclosure drafting plugin for DeepSeek Harness.
> Concept: left side shows a stylized patent document with floating mathematical formulas (fractions, Greek letters, summation) and a small technical flow diagram; a glowing data stream flows to the right side, transforming into an AI neural network / circuit motif with connected glowing nodes.
> Style: flat modern illustration, deep blue #1e3a8a to violet #8b5cf6 gradient palette with cyan #22d3ee accents, clean, professional, subtle depth, no text.
> Aspect ratio: 3:1, high resolution.

### 3. social-preview.png（社交预览图，可选）

> Social preview image 1280x640 for the GitHub repository "CazzPatent", an AI patent drafting plugin.
> Concept: centered minimalist composition — a patent document with a glowing AI circuit quill above it, subtle mathematical formula symbols floating in the background.
> Style: flat modern, deep blue to violet gradient, cyan accents, clean, professional, no text.
> Aspect ratio: 2:1 (1280x640).

---

## 替换后

把生成图覆盖同名文件后，README 顶部的图片会自动更新（无需改代码）。

生成小提示：

- logo 尽量要 **透明背景**（PNG 透明）或纯白底
- 负向提示词（如 Gemini 支持）：no text, no watermark, no letters
- 分辨率拉满（1024 或 2K），缩放后更清晰
