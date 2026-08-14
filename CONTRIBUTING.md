# 贡献指南 / Contributing

感谢你对 CazzPatent 的关注！欢迎提交 Issue、Pull Request 或改进建议。

## 环境准备

```sh
# Python（Skill 工具链 + 测试）
pip install -r requirements.txt
pip install python-docx pytest
playwright install chromium

# Node（插件构建，可选）
# cd plugin && npm install && npm run build
```

## 运行测试

```sh
python -m pytest tests -q
```

## 目录结构

- `cazz-patent/` — DSH Skill（指令大脑）：`SKILL.md` + prompts + scripts + templates + memory
- `plugin/` — Cordis 插件（确定性工具）：`src/index.ts` + esbuild 构建 + cordis.patch.yml
- `tests/` — pytest 测试套件

## 修改脚本后

`cazz-patent/scripts/` 与 `plugin/scripts/` 是两份同步副本。修改任一脚本后，请同步另一份：

```sh
cp cazz-patent/scripts/<script>.py plugin/scripts/<script>.py
```

## 提交规范

- 每个提交聚焦单一改动，提交信息用祈使句（如 `Fix LaTeX relation aliases`）。
- 改动符号库、脚本、插件时同步更新 `tests/` 下的回归测试。
- 中文与英文文档（README.md / README_zh.md）保持同步。

## 许可

本项目采用 [MIT](LICENSE) 许可。贡献即表示你同意在该许可下分发你的代码。
