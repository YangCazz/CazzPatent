"""
Convert patent disclosure Word (.docx) to print-ready PDF.

Three engines, tried in order:
  1. Word COM automation (Windows) — preserves OMML equations, CJK fonts, tables
  2. LibreOffice headless (cross-platform) — good formatting fidelity
  3. python-docx → weasyprint (pure Python) — limited equation support, no COM/app needed

Usage:
    python docx_to_pdf.py disclosure.docx -o disclosure.pdf
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _render_word_com(docx_path: Path, output_path: Path) -> bool:
    """Convert via Microsoft Word COM automation (Windows only)."""
    if sys.platform != "win32":
        return False

    try:
        import win32com.client
    except ImportError:
        return False

    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(str(docx_path))
        doc.SaveAs(str(output_path), FileFormat=17)  # 17 = wdFormatPDF
        doc.Close()
        word.Quit()
        return True
    except Exception as e:
        print(f"  Word COM failed: {e}")
        return False


def _render_libreoffice(docx_path: Path, output_path: Path) -> bool:
    """Convert via LibreOffice headless (cross-platform)."""
    candidates = []
    if sys.platform == "win32":
        for base in [r"C:\Program Files\LibreOffice\program",
                     r"C:\Program Files (x86)\LibreOffice\program"]:
            exe = os.path.join(base, "soffice.exe")
            if os.path.exists(exe):
                candidates.append(exe)
    else:
        for exe in ["libreoffice", "soffice"]:
            if shutil.which(exe):
                candidates.append(exe)

    if not candidates:
        return False

    soffice = candidates[0]
    out_dir = str(output_path.parent)

    try:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf",
             "--outdir", out_dir, str(docx_path)],
            check=True, timeout=120,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        # LibreOffice names the output after the input stem, rename if needed
        expected = output_path.parent / (docx_path.stem + ".pdf")
        if expected != output_path and expected.exists():
            expected.replace(output_path)
        return output_path.exists()
    except Exception as e:
        print(f"  LibreOffice failed: {e}")
        return False


def _render_python(docx_path: Path, output_path: Path) -> bool:
    """Pure-Python fallback: docx → HTML → PDF via weasyprint."""
    try:
        from docx import Document
    except ImportError:
        return False

    try:
        from weasyprint import HTML
    except ImportError:
        print("  weasyprint not available for Python fallback")
        return False

    doc = Document(str(docx_path))

    html_parts = [
        '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">',
        '<style>',
        '@page { size: A4; margin: 2.54cm 3.18cm; }',
        'body { font-family: "SimSun", "Times New Roman", serif; font-size: 12pt; line-height: 2; }',
        'h1 { font-family: "SimHei", sans-serif; font-size: 16pt; text-align: center; }',
        'h2 { font-family: "SimHei", sans-serif; font-size: 14pt; }',
        'h3 { font-family: "SimHei", sans-serif; font-size: 12pt; }',
        'table { border-collapse: collapse; width: 100%; margin: 12pt 0; }',
        'td, th { border: 1px solid #333; padding: 4pt 8pt; font-size: 10.5pt; }',
        'p { margin: 6pt 0; text-indent: 2em; }',
        '</style></head><body>',
    ]

    for para in doc.paragraphs:
        style = para.style.name.lower() if para.style else ""
        text = para.text.strip()
        if not text:
            html_parts.append("<p>&nbsp;</p>")
            continue

        if "heading 1" in style or "title" in style:
            html_parts.append(f"<h1>{text}</h1>")
        elif "heading 2" in style:
            html_parts.append(f"<h2>{text}</h2>")
        elif "heading 3" in style:
            html_parts.append(f"<h3>{text}</h3>")
        else:
            html_parts.append(f"<p>{text}</p>")

    html_parts.append("</body></html>")
    html = "\n".join(html_parts)

    try:
        HTML(string=html).write_pdf(str(output_path))
        return True
    except Exception as e:
        print(f"  weasyprint error: {e}")
        return False


def docx_to_pdf(docx_path: Path, output_path: Path) -> None:
    """Convert DOCX to PDF, trying engines in priority order."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for name, engine in [
        ("Word COM", _render_word_com),
        ("LibreOffice", _render_libreoffice),
        ("python-docx + weasyprint", _render_python),
    ]:
        print(f"  Trying {name}...")
        if engine(docx_path, output_path):
            print(f"Saved (via {name}): {output_path}")
            return

    print("No PDF engine available. Install one of:")
    print("  - Windows: Microsoft Word + pywin32")
    print("  - Cross-platform: LibreOffice")
    print("  - Pure Python: pip install weasyprint")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convert patent disclosure Word (.docx) to PDF"
    )
    parser.add_argument("input", help="Path to input .docx file")
    parser.add_argument("-o", "--output", default=None,
                        help="Output PDF path (default: same directory as input)")
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        # Auto-derive: place PDF alongside the DOCX
        output_path = input_path.parent / (input_path.stem + ".pdf")

    docx_to_pdf(input_path, output_path)


if __name__ == "__main__":
    main()
