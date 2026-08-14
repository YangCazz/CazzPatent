# -*- coding: utf-8 -*-
"""冒烟测试：Mermaid 批量图生成器。"""
import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "cazz-patent" / "scripts"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


batch = _load("batch_diagrams", SCRIPTS / "batch_diagrams.py")

MERMAID = """# 图1: 系统架构图

graph TB
    subgraph 输入模块[输入模块]
        001[读取图像数据]
    end
    001 --> 002[特征提取]
    002 --> 003[输出结果]

**图表说明**：测试图。
"""


def test_parse_md_extracts_nodes_and_edges(tmp_path):
    md = tmp_path / "图1.md"
    md.write_text(MERMAID, encoding="utf-8")
    nodes, edges, sg_labels, sg_nids, sg_order = batch.parse_md(md)
    nids = [n[0] for n in nodes]
    assert "001" in nids and "002" in nids and "003" in nids
    assert ("001", "002") in edges
    assert ("002", "003") in edges
    assert "输入模块" in sg_labels


def test_gen_svg_produces_svg(tmp_path):
    md = tmp_path / "图1.md"
    md.write_text(MERMAID, encoding="utf-8")
    nodes, edges, sg_labels, sg_nids, sg_order = batch.parse_md(md)
    svg = batch.gen_svg(nodes, edges, sg_labels, sg_nids, sg_order, "系统架构图")
    assert "<svg" in svg
    assert "</svg>" in svg
