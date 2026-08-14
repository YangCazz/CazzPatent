"""
Render a patent diagram HTML file to high-resolution PNG via Playwright.

Usage:
    python html_to_png.py diagram.html -o diagram.png
    python html_to_png.py diagram.html -o diagram.png --scale 3.0
"""

import argparse
import glob
import os
import sys
from pathlib import Path


def _find_chromium_exe() -> str:
    """Find an available Chromium installation for Playwright."""
    base = os.environ.get(
        "PLAYWRIGHT_BROWSERS_PATH",
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "ms-playwright"),
    )
    chromium_dirs = sorted(glob.glob(os.path.join(base, "chromium-*")))
    for d in reversed(chromium_dirs):
        chrome_exe = os.path.join(d, "chrome-win64", "chrome.exe")
        if os.path.exists(chrome_exe):
            return chrome_exe
    sys.exit(
        "No Chromium installation found. Run:\n"
        "  playwright install chromium"
    )


def html_to_png(html_path: Path, output_path: Path, scale: float = 3.0) -> None:
    """Render a patent diagram HTML to high-res PNG using Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit(
            "playwright not installed. Run:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        )

    abs_url = html_path.resolve().as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=_find_chromium_exe(),
        )
        page = browser.new_page(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=scale,
        )
        page.goto(abs_url, wait_until="domcontentloaded", timeout=60000)
        # Poll for CDN scripts to load (html2canvas may need extra time)
        for _ in range(20):
            page.wait_for_timeout(500)
            ready = page.evaluate("() => typeof html2canvas !== 'undefined' && typeof captureCanvas === 'function'")
            if ready:
                break

        # Try HTML built-in captureCanvas (html2canvas, template-native)
        has_capture = page.evaluate("() => typeof html2canvas !== 'undefined' && typeof captureCanvas === 'function'")
        if has_capture:
            import base64
            data_url = page.evaluate('''async () => {
                const canvas = await captureCanvas(3);
                return canvas.toDataURL('image/png');
            }''')
            png_data = base64.b64decode(data_url.split(',')[1])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(png_data)
            # Read dimensions from PNG header
            w = int.from_bytes(png_data[16:20], 'big')
            h = int.from_bytes(png_data[20:24], 'big')
        else:
            # Fallback: bounding_box clip for HTML without captureCanvas
            root = page.locator("#diagram-root")
            box = root.bounding_box()
            if box is None:
                browser.close()
                sys.exit("Error: could not locate #diagram-root element.")
            margin = 20
            clip = {
                "x": max(0, box["x"] - margin),
                "y": max(0, box["y"] - margin),
                "width": box["width"] + 2 * margin,
                "height": box["height"] + 2 * margin,
            }
            output_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output_path), clip=clip, scale="device")
            w = int(clip["width"] * scale)
            h = int(clip["height"] * scale)
        browser.close()

    file_size = output_path.stat().st_size
    print(f"Saved: {output_path} ({file_size:,} bytes, {w}x{h}px)")


def main():
    parser = argparse.ArgumentParser(
        description="Render patent diagram HTML to high-res PNG"
    )
    parser.add_argument("input", help="Path to diagram HTML file")
    parser.add_argument("-o", "--output", default="diagram.png", help="Output PNG path")
    parser.add_argument(
        "--scale", type=float, default=3.0,
        help="Output scale factor (default: 3.0, for ~3x DPI print quality)"
    )
    args = parser.parse_args()

    html_to_png(Path(args.input), Path(args.output), args.scale)


if __name__ == "__main__":
    main()
