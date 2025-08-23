#!/usr/bin/env python
"""
Convert multiple HTML slide files in a folder into a single PDF using pdfkit/wkhtmltopdf.

Highlights:
- Faithful rendering of original HTML/CSS (better than text-only extraction).
- Excludes presentation.html automatically.
- Respects explicit slide order if defined in presentation.html (const slides=[...]/loadSlide(...)).

Usage:
    python scripts/html_slides_to_pptx.py --src-dir <folder> --out <output.pdf>

Dependencies:
    pip install pdfkit beautifulsoup4 lxml
    System binary required: wkhtmltopdf (install via apt/yum or from https://wkhtmltopdf.org/)
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup
import pdfkit


def parse_slide_order_from_presentation(presentation_html: Path, src_dir: Path) -> List[Path]:
    """Try to detect slide order from presentation.html.

    Supports either a JS array `const slides = ['a.html', ...]` or calls like `loadSlide('a.html')`.
    Returns an ordered list of existing Paths under src_dir, excluding presentation.html itself.
    """
    if not presentation_html.exists():
        return []

    text = presentation_html.read_text(encoding="utf-8", errors="ignore")
    files: List[str] = []

    # Try to find a JS array definition
    m = re.search(r"const\s+slides\s*=\s*\[(?P<body>.*?)\];", text, re.S)
    if m:
        body = m.group("body")
        files = re.findall(r"['\"]([^'\"]+?\.html)['\"]", body)
    else:
        # Fallback: look for loadSlide('file.html') calls
        files = re.findall(r"loadSlide\(['\"]([^'\"]+?\.html)['\"]", text)

    ordered: List[Path] = []
    for f in files:
        p = (src_dir / f).resolve()
        if p.name.lower() == "presentation.html":
            continue
        if p.exists():
            ordered.append(p)
    return ordered


def collect_html_slides(src_dir: Path) -> List[Path]:
    """Collect all *.html in src_dir except presentation.html, sorted alphabetically."""
    return sorted([p for p in src_dir.glob("*.html") if p.name.lower() != "presentation.html"])


def _has_single_index_html(files: List[Path]) -> bool:
    """If folder has only index.html, convert just that file (common in SPA slides)."""
    htmls = [p for p in files if p.suffix.lower() == ".html"]
    return len(htmls) == 1 and htmls[0].name.lower() == "index.html"


def build_pdf_with_pdfkit(src_dir: Path, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    presentation_html = src_dir / "presentation.html"
    ordered = parse_slide_order_from_presentation(presentation_html, src_dir)
    if not ordered:
        ordered = collect_html_slides(src_dir)

    if not ordered:
        raise SystemExit(f"No HTML files found under {src_dir}")

    # If only index.html exists, pass that single file (common in single-page slides)
    if _has_single_index_html(ordered):
        files = [str(ordered[0])]
    else:
        files = [str(p) for p in ordered]

    # wkhtmltopdf options
    options = {
        "enable-local-file-access": None,  # allow local CSS/images
        "encoding": "utf-8",
        "quiet": None,
        "page-size": "A4",
        "orientation": "Landscape",
        # Margins suitable for slides
        "margin-top": "10mm",
        "margin-bottom": "10mm",
        "margin-left": "10mm",
        "margin-right": "10mm",
        # Improve rendering for high-DPI content
        "dpi": 200,
        # "zoom": 1.0,  # uncomment to tweak scaling if needed
    }

    # Try default configuration; if wkhtmltopdf is missing, give a helpful error
    try:
        pdfkit.from_file(files, str(out_path), options=options)
    except OSError as e:
        raise SystemExit(
            "wkhtmltopdf not found or failed to run. Please install it (e.g., 'sudo apt-get install -y wkhtmltopdf') "
            "or provide the path via pdfkit.configuration(wkhtmltopdf=...).\n"
            f"Original error: {e}"
        )
    print(f"Saved PDF: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert multiple HTML slides to a single PDF using wkhtmltopdf.")
    parser.add_argument("--src-dir", required=True, help="Directory containing slide HTML files.")
    parser.add_argument("--out", required=False, help="Output PDF path.")
    args = parser.parse_args()

    src_dir = Path(args.src_dir).resolve()
    if not src_dir.exists():
        raise SystemExit(f"Source dir not found: {src_dir}")

    out_path = Path(args.out).resolve() if args.out else (src_dir / "slides.pdf").resolve()

    build_pdf_with_pdfkit(src_dir, out_path)


if __name__ == "__main__":
    main()
