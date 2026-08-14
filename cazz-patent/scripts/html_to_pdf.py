"""
Convert patent disclosure Markdown or HTML to a print-ready PDF.

Two rendering engines:
  1. weasyprint (recommended) — pip install weasyprint
  2. Playwright (fallback)    — already installed, renders as print PDF

Usage:
    # From Markdown: wraps content in a clean HTML template first
    python html_to_pdf.py disclosure.md -o disclosure.pdf

    # From HTML (e.g. a generated diagram page):
    python html_to_pdf.py diagram.html -o diagram.pdf
"""

import argparse
import re
import sys
from pathlib import Path

PDF_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: A4;
    margin: 2.54cm 3.18cm 2.54cm 3.18cm;
    @bottom-center {{
      content: counter(page);
      font-family: 'Microsoft YaHei', 'SimSun', sans-serif;
      font-size: 9pt;
      color: #999;
    }}
  }}
  body {{
    font-family: 'SimSun', 'Microsoft YaHei', 'Times New Roman', serif;
    font-size: 12pt;
    line-height: 2;
    color: #000;
  }}
  h1 {{
    font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
    font-size: 16pt;
    font-weight: bold;
    text-align: center;
    margin-bottom: 24pt;
    page-break-before: avoid;
  }}
  h2 {{
    font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
    font-size: 14pt;
    font-weight: bold;
    margin-top: 18pt;
    margin-bottom: 12pt;
    page-break-after: avoid;
  }}
  h3 {{
    font-family: 'SimHei', 'Microsoft YaHei', sans-serif;
    font-size: 12pt;
    font-weight: bold;
    margin-top: 12pt;
    margin-bottom: 6pt;
  }}
  p {{ margin: 6pt 0; text-indent: 2em; }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 12pt 0;
  }}
  td, th {{
    border: 1px solid #333;
    padding: 4pt 8pt;
    font-size: 10.5pt;
  }}
  img {{ max-width: 100%; margin: 12pt auto; display: block; }}
  .caption {{ text-align: center; font-size: 9pt; color: #666; text-indent: 0; }}
  code {{ font-family: 'Consolas', monospace; font-size: 10pt; }}
  .math {{ font-style: italic; }}
  .page-break {{ page-break-before: always; }}
</style>
</head>
<body>
{content}
</body>
</html>"""


def _md_to_html(md_text: str) -> str:
    """Basic Markdown → HTML conversion for PDF rendering."""
    # Headings
    md_text = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', md_text, flags=re.MULTILINE)
    md_text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', md_text, flags=re.MULTILINE)
    md_text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', md_text, flags=re.MULTILINE)
    md_text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', md_text, flags=re.MULTILINE)

    # Bold and italic
    md_text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md_text)
    md_text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', md_text)

    # Inline LaTeX: keep as-is for readability in PDF
    md_text = re.sub(r'\$\$(.+?)\$\$', r'<div class="math">\1</div>', md_text, flags=re.DOTALL)
    md_text = re.sub(r'\$(.+?)\$', r'<span class="math">\1</span>', md_text)

    # Images: convert ![alt](path) → <img>
    md_text = re.sub(
        r'!\[(.*?)\]\((.*?)\)',
        r'<div><img src="\2" alt="\1"><p class="caption">\1</p></div>',
        md_text
    )

    # Paragraphs: blank lines → </p><p>
    paragraphs = md_text.split('\n\n')
    html_paragraphs = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if p.startswith('<h') or p.startswith('<div') or p.startswith('<table'):
            html_paragraphs.append(p)
        else:
            # Inline line breaks
            p = p.replace('\n', '<br>')
            html_paragraphs.append(f'<p>{p}</p>')

    return '\n'.join(html_paragraphs)


def _render_weasyprint(html: str, output_path: Path) -> bool:
    """Try weasyprint rendering. Returns True on success."""
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(str(output_path))
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"weasyprint error: {e}")
        return False


def _render_playwright(html: str, output_path: Path) -> bool:
    """Fallback: use Playwright to print to PDF."""
    import glob, os
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False

    playwright_base = os.path.join(
        os.path.expanduser("~"), "AppData", "Local", "ms-playwright"
    )
    chromium_dirs = sorted(glob.glob(os.path.join(playwright_base, "chromium-*")))
    chrome_exe = None
    for d in reversed(chromium_dirs):
        exe = os.path.join(d, "chrome-win64", "chrome.exe")
        if os.path.exists(exe):
            chrome_exe = exe
            break

    if not chrome_exe:
        return False

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chrome_exe)
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(500)
        page.pdf(
            path=str(output_path),
            format="A4",
            margin={"top": "2.54cm", "bottom": "2.54cm",
                    "left": "3.18cm", "right": "3.18cm"},
            print_background=True,
        )
        browser.close()
    return True


def md_to_pdf(md_path: Path, output_path: Path) -> None:
    """Convert Markdown to PDF via HTML template."""
    md_text = md_path.read_text(encoding="utf-8")
    body_html = _md_to_html(md_text)
    full_html = PDF_HTML_TEMPLATE.format(content=body_html)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if _render_weasyprint(full_html, output_path):
        print(f"Saved (weasyprint): {output_path}")
    elif _render_playwright(full_html, output_path):
        print(f"Saved (Playwright): {output_path}")
    else:
        # Save the HTML for manual conversion
        html_path = output_path.with_suffix(".html")
        html_path.write_text(full_html, encoding="utf-8")
        print(
            f"Could not render PDF (install weasyprint: pip install weasyprint).\n"
            f"HTML saved to: {html_path}\n"
            f"Open in browser and Print → Save as PDF."
        )


def html_to_pdf(html_path: Path, output_path: Path) -> None:
    """Convert an existing HTML file to PDF."""
    html_text = html_path.read_text(encoding="utf-8")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if _render_weasyprint(html_text, output_path):
        print(f"Saved (weasyprint): {output_path}")
    elif _render_playwright(html_text, output_path):
        print(f"Saved (Playwright): {output_path}")
    else:
        print("Install weasyprint for PDF support: pip install weasyprint")


def main():
    parser = argparse.ArgumentParser(
        description="Convert patent disclosure to print-ready PDF"
    )
    parser.add_argument("input", help="Path to .md or .html file")
    parser.add_argument("-o", "--output", default="disclosure.pdf",
                        help="Output PDF path")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.suffix.lower() == ".md":
        md_to_pdf(input_path, output_path)
    else:
        html_to_pdf(input_path, output_path)


if __name__ == "__main__":
    main()
