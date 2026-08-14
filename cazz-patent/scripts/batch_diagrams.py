"""
Batch diagram generator: Mermaid .md → HTML+SVG → high-res PNG.
Automates Phase C+D of the diagram pipeline for Mermaid flowcharts
that share a consistent node/edge/subgraph structure.

Usage:
    # Process all Mermaid .md files under 专利输出/
    python batch_diagrams.py

    # Process specific proposals only
    python batch_diagrams.py --proposals 提案5 提案15

    # Custom output base directory
    python batch_diagrams.py --base 专利输出

    # Dry run (parse only, skip rendering)
    python batch_diagrams.py --dry-run

Design:
    This script automates the mechanical Phase C (SVG generation) and
    Phase D (PNG rendering) for Mermaid source files that follow the
    standard format (NNN["label"] nodes, subgraph[...] groups, NNN-->NNN edges).
    It does NOT replace the full Phase A→B→C→D pipeline — use the manual
    flow for diagrams that need custom layouts, diamond decision nodes,
    branch logic, or hand-tuned positioning.

    See prompts/diagram.md for the Mermaid format specification.
"""

import argparse
import os
import re
import subprocess
import struct
import sys
from collections import OrderedDict
from pathlib import Path


# ── Resolve tool paths relative to this script ──
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent  # .claude/skills/patent-disclosure/
TEMPLATE_PATH = SKILL_DIR / "templates" / "patent_diagram_template.html"
HTML2PNG_PATH = SCRIPT_DIR / "html_to_png.py"


def strip_quotes(s: str) -> str:
    """Strip surrounding double/single quotes and whitespace."""
    s = s.strip()
    if len(s) >= 2:
        if (s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'"):
            s = s[1:-1]
    return s


def parse_md(md_path: Path):
    """Parse a Mermaid .md file into nodes, edges, and subgraph groups."""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract all NNN["label"] node definitions
    nodes = re.findall(r"(\d{3})\[(.+?)\]", content)
    nodes = [(nid, strip_quotes(lbl)) for nid, lbl in nodes]

    # Extract all NNN --> NNN edge definitions
    edges = re.findall(r"(\d{3})\s*-->\s*(\d{3})", content)

    # Extract subgraph structure
    sg_labels = {}
    sg_nids = OrderedDict()
    sg_order = []
    cur = None
    for ln in content.split("\n"):
        m = re.match(r"\s*subgraph\s+(\w+)\s*\[(.+?)\]", ln)
        me = re.match(r"\s*end\s*$", ln)
        if m:
            cur = m.group(1)
            sg_labels[cur] = strip_quotes(m.group(2))
            sg_nids[cur] = []
            sg_order.append(cur)
            continue
        elif me:
            cur = None
            continue
        elif cur and "-->" not in ln:
            for n in re.findall(r"(\d{3})", ln):
                sg_nids[cur].append(n)
    return nodes, edges, sg_labels, sg_nids, sg_order


def gen_svg(nodes, edges, sg_labels, sg_nids, sg_order, title: str):
    """Generate inline SVG from parsed Mermaid structure."""
    nl = dict(nodes)
    SVG_W = 1100
    NODE_W = 175
    BASE_H = 42
    LINE_H = 14
    Y_BETWEEN = 62
    SG_PAD_TOP = 26
    SG_PAD_SIDE = 18
    SG_PAD_BOT = 14
    SG_GAP = 22
    NODE_GAP = 18

    # ── Parse multi-line labels and compute node heights ──
    node_lines = {}
    node_heights = {}
    for nid, label in nl.items():
        if "<br/>" in label or "<br>" in label:
            lines = [l.strip() for l in re.split(r"<br\s*/?>", label)]
        else:
            lines = [label]
        node_lines[nid] = lines
        node_heights[nid] = BASE_H + max(0, (len(lines) - 1) * LINE_H)

    # ── Layout with dynamic heights ──
    node_map = {}
    sg_boxes = []
    curr_y = 55
    for sg_name in sg_order:
        nids = sg_nids.get(sg_name, [])
        if not nids:
            continue
        n = len(nids)
        max_c = min(4, n)
        rows = (n + max_c - 1) // max_c

        # Compute per-row max heights
        row_max_h = []
        for row in range(rows):
            row_nids = nids[row * max_c : (row + 1) * max_c]
            row_max_h.append(max(node_heights.get(nid, BASE_H) for nid in row_nids))

        # Position rows
        row_ys = [curr_y + SG_PAD_TOP + row_max_h[0] // 2]
        for row in range(1, rows):
            prev_center = row_ys[-1]
            prev_h = row_max_h[row - 1]
            this_h = row_max_h[row]
            row_ys.append(prev_center + prev_h // 2 + NODE_GAP + this_h // 2)

        # Place each node
        for i, nid in enumerate(nids):
            col = i % max_c
            row = i // max_c
            ac = min(max_c, n - row * max_c)
            off = (max_c - ac) * (SVG_W - 80) // max_c // 2
            xs = (SVG_W - 80) // max_c
            x = 40 + off + col * xs + xs // 2
            y = row_ys[row]
            node_map[nid] = (x, y)

        # Subgraph bounding box
        xs2 = [node_map[n][0] for n in nids]
        ytops = []
        ybots = []
        for n in nids:
            h = node_heights.get(n, BASE_H)
            ytops.append(node_map[n][1] - h // 2)
            ybots.append(node_map[n][1] + h // 2)
        bx = min(xs2) - NODE_W // 2 - SG_PAD_SIDE
        bw = max(xs2) - min(xs2) + NODE_W + 2 * SG_PAD_SIDE
        bh = (max(ybots) - curr_y) + SG_PAD_BOT
        sg_boxes.append((sg_labels.get(sg_name, sg_name), bx, curr_y, bw, bh))
        curr_y = max(ybots) + SG_PAD_BOT + SG_GAP

    svg_h = curr_y + 120

    # ── Build SVG ──
    parts = [
        f'<text x="{SVG_W//2}" y="30" text-anchor="middle" font-size="17" font-weight="700" fill="#1e293b">{title}</text>'
    ]

    # Subgraph boundary boxes
    for label, bx, by, bw, bh in sg_boxes:
        parts.append(
            f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="6,3"/>'
        )
        parts.append(
            f'<text x="{bx+12}" y="{by+SG_PAD_TOP-10}" fill="#64748b" font-size="10" font-weight="600">{label}</text>'
        )

    # Edges
    for s, d in edges:
        if s not in node_map or d not in node_map:
            continue
        sx, sy = node_map[s]
        dx, dy = node_map[d]
        sh = node_heights.get(s, BASE_H)
        dh = node_heights.get(d, BASE_H)
        if abs(sy - dy) < Y_BETWEEN * 0.3:
            parts.append(
                f'<line x1="{sx+NODE_W//2}" y1="{sy}" x2="{dx-NODE_W//2}" y2="{dy}" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>'
            )
        else:
            my = (sy + sh // 2 + dy - dh // 2) / 2
            parts.append(
                f'<path d="M{sx},{sy+sh//2} C{sx},{my} {dx},{my} {dx},{dy-dh//2}" fill="none" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow)"/>'
            )

    # Nodes with multi-line text
    for nid, (x, y) in node_map.items():
        label = nl.get(nid, nid)
        lines = node_lines.get(nid, [label])
        h = node_heights.get(nid, BASE_H)
        n_lines = len(lines)

        # Color by keyword
        ll = label.lower()
        if any(k in ll for k in ["输出", "掩码", "模型", "报告", "方案", "最终"]):
            fill, stroke, tc = ("#2563eb", "#1d4ed8", "#fff")
        elif any(k in ll for k in ["输入", "影像", "数据", "标注"]):
            fill, stroke, tc = ("#f0f9ff", "#0ea5e9", "#0c4a6e")
        else:
            fill, stroke, tc = ("#fff", "#64748b", "#1e293b")

        fs = 9 if n_lines > 2 else (10 if n_lines == 2 else 11)
        start_y = y - (n_lines - 1) * LINE_H // 2 - 1

        parts.append(
            f'<g filter="url(#shadow)"><rect x="{x-NODE_W//2}" y="{y-h//2}" width="{NODE_W}" height="{h}" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        )
        for li, line in enumerate(lines):
            display = line[:46] if len(line) > 46 else line
            parts.append(
                f'<text x="{x}" y="{start_y+li*LINE_H}" text-anchor="middle" font-size="{fs}" fill="{tc}">{display}</text>'
            )
        parts.append(
            f'<text x="{x}" y="{y+h//2-5}" text-anchor="middle" font-size="8" fill="#94a3b8">{nid}</text></g>'
        )

    # Legend
    ly = svg_h - 105
    lx = SVG_W - 250
    parts.append(
        f'<rect x="{lx}" y="{ly}" width="230" height="80" rx="6" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1"/><text x="{lx+15}" y="{ly+18}" font-size="10" font-weight="600" fill="#64748b">图例</text>'
    )
    for ii, (fs, st, tx) in enumerate(
        [
            ("#f0f9ff", "#0ea5e9", "数据/输入"),
            ("#fff", "#64748b", "处理步骤"),
            ("#2563eb", "#1d4ed8", "最终输出"),
        ]
    ):
        yo = ly + 24 + ii * 16
        parts.append(
            f'<rect x="{lx+15}" y="{yo}" width="14" height="10" rx="2" fill="{fs}" stroke="{st}" stroke-width="1"/><text x="{lx+35}" y="{yo+9}" font-size="9" fill="#64748b">{tx}</text>'
        )
    return "\n".join(parts), SVG_W, svg_h + 20


# ────────────────────────────────────────────────────────
def process_diagrams(
    base_dir: str,
    proposals: set = None,
    dry_run: bool = False,
    scale: float = 3.0,
) -> int:
    """Walk 图纸/ directories, parse Mermaid .md, generate HTML+PNG."""
    if not TEMPLATE_PATH.exists():
        print(f"Error: template not found at {TEMPLATE_PATH}")
        return 0
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    python_exe = sys.executable
    count = 0

    for root, dirs, files in os.walk(base_dir):
        if "图纸" not in root:
            continue
        # Derive proposal name from path: .../专利输出/提案N-名称/图纸/图N-标题/
        pp = root.replace("\\", "/").split("/")
        pd = pp[-3] if len(pp) >= 3 else ""

        if proposals and not any(p in pd for p in proposals):
            continue

        for f in files:
            if not f.endswith(".md"):
                continue
            mp = os.path.join(root, f)
            hp = os.path.join(root, f.replace(".md", ".html"))
            pp2 = os.path.join(root, f.replace(".md", ".png"))

            # Use directory name as title & badge
            dn = os.path.basename(root)
            badge = dn[:3] if dn.startswith("图") else "图 N"
            title = dn[3:].lstrip("-") if dn.startswith("图") else dn

            try:
                nodes, edges, sg_labels, sg_nids, sg_order = parse_md(mp)
                if not nodes:
                    print(f"  SKIP {f} (no nodes found)")
                    continue

                svg, vw, vh = gen_svg(
                    nodes, edges, sg_labels, sg_nids, sg_order, title
                )

                if dry_run:
                    print(
                        f"  PARSE {f} → {len(nodes)} nodes, {len(edges)} edges, "
                        f"{len(sg_order)} subgraphs, viewBox={vw}x{vh}"
                    )
                    count += 1
                    continue

                # Fill template placeholders
                html = template
                html = html.replace(
                    '<span class="diagram-badge">图 N</span>',
                    f'<span class="diagram-badge">{badge}</span>',
                )
                html = html.replace(
                    "<h1>[图表标题]</h1>", f"<h1>{title}</h1>"
                )
                html = html.replace(
                    "[一句话说明这张图展示的内容]",
                    f"提案{pd[:4]} — {title}",
                )
                html = html.replace(
                    "专利附图 · [提案名称]",
                    f"专利附图 · {pd}",
                )
                svg_repl = f'viewBox="0 0 {vw} {vh}"'
                html = html.replace(
                    'viewBox="0 0 [WIDTH] [HEIGHT]"', svg_repl
                )
                html = re.sub(
                    r'viewBox="0 0 \d+ \d+"', svg_repl, html
                )
                html = re.sub(
                    r'(<svg class="diagram" [^>]+>.*?<defs>.*?</defs>)\s*.*?(?=</svg>)',
                    r"\1\n" + svg + "\n",
                    html,
                    flags=re.DOTALL,
                )

                with open(hp, "w", encoding="utf-8") as wf:
                    wf.write(html)

                # Render PNG (Phase D)
                r = subprocess.run(
                    [
                        python_exe,
                        str(HTML2PNG_PATH),
                        hp,
                        "-o",
                        pp2,
                        "--scale",
                        str(scale),
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=60,
                    env={
                        **os.environ,
                        "PYTHONIOENCODING": "utf-8",
                    },
                )
                if r.returncode == 0 and os.path.exists(pp2):
                    kb = os.path.getsize(pp2) // 1024
                    with open(pp2, "rb") as pf:
                        pf.read(16)
                        w = int.from_bytes(pf.read(4), "big")
                        h = int.from_bytes(pf.read(4), "big")
                    print(f"  OK {f} {kb}KB {w}x{h}")
                    count += 1
                else:
                    print(f"  ERR {f}: render failed")
                    if r.stderr:
                        print(f"    {r.stderr.strip()[:200]}")

            except Exception as e:
                import traceback

                print(f"  ERR {f}: {e}")
                traceback.print_exc()

    return count


def main():
    parser = argparse.ArgumentParser(
        description="Batch Mermaid .md → HTML+SVG → PNG diagram generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_diagrams.py
  python batch_diagrams.py --base 专利输出 --proposals 提案5 提案15
  python batch_diagrams.py --dry-run
  python batch_diagrams.py --scale 2.0
        """,
    )
    parser.add_argument(
        "--base",
        default="专利输出",
        help="Base directory containing proposal output folders (default: 专利输出)",
    )
    parser.add_argument(
        "--proposals",
        nargs="*",
        default=None,
        help="Filter to specific proposal names (e.g. 提案5 提案15). Processes all if omitted.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse Mermaid files and report stats without rendering",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=3.0,
        help="PNG output scale factor (default: 3.0 for ~3x DPI)",
    )
    args = parser.parse_args()

    proposals = set(args.proposals) if args.proposals else None

    if not os.path.isdir(args.base):
        print(f"Error: base directory '{args.base}' not found")
        sys.exit(1)
    if not TEMPLATE_PATH.exists():
        print(f"Error: HTML template not found at {TEMPLATE_PATH}")
        sys.exit(1)

    print(f"Base:   {os.path.abspath(args.base)}")
    if proposals:
        print(f"Filter: {proposals}")
    if args.dry_run:
        print("Mode:   DRY RUN (parse only)")
    print()

    count = process_diagrams(
        base_dir=args.base,
        proposals=proposals,
        dry_run=args.dry_run,
        scale=args.scale,
    )
    print(f"\nDone: {count} diagrams")


if __name__ == "__main__":
    main()
