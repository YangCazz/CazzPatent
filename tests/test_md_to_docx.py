# -*- coding: utf-8 -*-
"""冒烟测试：Markdown → DOCX 引擎（LaTeX → OMML）。"""
import importlib.util
import sys
from pathlib import Path

import pytest

pytest.importorskip("docx", reason="需要安装 python-docx 才能运行")

SCRIPTS = Path(__file__).resolve().parent.parent / "cazz-patent" / "scripts"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


md_to_docx = _load("md_to_docx", SCRIPTS / "md_to_docx.py")


def test_symbol_map_has_core_symbols():
    keys = [
        "alpha", "beta", "gamma", "omega",
        "sum", "int", "frac",
        "leq", "geq", "neq", "approx", "times", "cdot", "pm",
        "nabla", "partial", "in", "forall", "exists", "rightarrow", "infty",
        "dots", "cdots", "mathbb", "mathbf", "hat", "bar", "tilde",
    ]
    for key in keys:
        assert key in md_to_docx._SYMBOLS or key in md_to_docx._SKIP_COMMANDS, (
            f"缺少符号/命令: {key}"
        )


def test_extract_latex_commands():
    cmds = md_to_docx._extract_latex_commands(r"$$\alpha = \frac{1}{2}\sum_{i=1}^{N} x_i$$")
    assert "alpha" in cmds
    assert "frac" in cmds
    assert "sum" in cmds


def test_build_symbol_map_reports_unknown():
    sym_map, unknown = md_to_docx._build_symbol_map(r"$$\alpha + \totallyunknowncmd $$")
    assert sym_map["alpha"] == "α"
    assert "totallyunknowncmd" in unknown


def test_markdown_to_docx_roundtrip(tmp_path):
    md = tmp_path / "test.md"
    md.write_text(
        """# 测试

## 一、背景技术

这是正文，含公式 $E = mc^2$。

| 列A | 列B |
|---|---|
| 1 | 2 |
""",
        encoding="utf-8",
    )
    out = tmp_path / "test.docx"
    md_to_docx.markdown_to_docx(md, out)
    assert out.exists()
    assert out.stat().st_size > 1000
