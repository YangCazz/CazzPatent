"""
Load and manage patent disclosure templates.

Usage:
    python template_loader.py --list              # List available templates
    python template_loader.py --load company.docx  # Load and inspect a template
"""

import argparse
import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def list_templates() -> list[Path]:
    """List all template files in the templates directory."""
    if not TEMPLATES_DIR.exists():
        return []
    return sorted(TEMPLATES_DIR.glob("*"))


def load_template(name: str) -> dict:
    """Load a template and return its metadata and content."""
    template_path = TEMPLATES_DIR / name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    result = {
        "name": template_path.name,
        "path": str(template_path),
        "size_bytes": template_path.stat().st_size,
        "suffix": template_path.suffix,
    }

    if template_path.suffix in (".md", ".txt"):
        content = template_path.read_text(encoding="utf-8")
        result["content"] = content
        result["sections"] = _extract_sections(content)
    else:
        result["content"] = f"<binary file: {template_path.suffix}>"

    return result


def _extract_sections(content: str) -> list[str]:
    """Extract section headings from markdown content."""
    import re

    headings = re.findall(r"^#{1,4}\s+(.+)$", content, re.MULTILINE)
    return headings


def main():
    parser = argparse.ArgumentParser(description="Patent template loader")
    parser.add_argument("--list", action="store_true", help="List available templates")
    parser.add_argument("--load", help="Load a specific template by filename")
    args = parser.parse_args()

    if args.list:
        templates = list_templates()
        if not templates:
            print("No templates found in:", TEMPLATES_DIR)
        else:
            print("Available templates:")
            for t in templates:
                info = load_template(t.name)
                sections = info.get("sections", [])
                section_preview = ", ".join(sections[:3])
                if len(sections) > 3:
                    section_preview += f", ... (+{len(sections) - 3} more)"
                print(f"  {t.name} ({info['size_bytes']} bytes)")
                if section_preview:
                    print(f"    Sections: {section_preview}")
    elif args.load:
        try:
            info = load_template(args.load)
            print(json.dumps(info, ensure_ascii=False, indent=2))
        except FileNotFoundError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
