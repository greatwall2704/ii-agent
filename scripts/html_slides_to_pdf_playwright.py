#!/usr/bin/env python
"""
Advanced HTML slides to PDF converter using Playwright.

This implementation provides better performance and reliability compared to Selenium,
with built-in PDF generation capabilities and better JavaScript execution handling.

Features:
- Uses Playwright for superior rendering performance
- Built-in PDF generation without external dependencies
- Better handling of dynamic content and animations
- Supports custom CSS for print media
- Automatic detection of slide completion
- Optimized for presentation slides

Usage:
    python scripts/html_slides_to_pdf_playwright.py --src-dir <folder> --out <output.pdf>

Dependencies:
    pip install playwright PyPDF2
    playwright install chromium
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from playwright.async_api import async_playwright, Browser, Page
from PyPDF2 import PdfMerger

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PlaywrightPDFConverter:
    """Advanced HTML to PDF converter using Playwright."""
    
    def __init__(self, 
                 page_format: str = "A4",
                 orientation: str = "landscape",
                 margin: Dict[str, str] = None,
                 wait_timeout: int = 30000,
                 load_delay: float = 2.0,
                 scale: float = 1.0):
        """
        Initialize converter.
        
        Args:
            page_format: PDF page format (A4, Letter, etc.)
            orientation: Page orientation (landscape/portrait)  
            margin: Page margins dict with top, right, bottom, left
            wait_timeout: Maximum wait time for page load (milliseconds)
            load_delay: Additional delay after page load (seconds)
            scale: Page scale factor for rendering
        """
        self.page_format = page_format
        self.orientation = orientation
        self.margin = margin or {"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"}
        self.wait_timeout = wait_timeout
        self.load_delay = load_delay
        self.scale = scale
        self.browser: Optional[Browser] = None
        
    async def _setup_browser(self):
        """Initialize Playwright browser with optimized settings."""
        playwright = await async_playwright().start()
        
        # Launch browser with optimized settings for PDF generation
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--allow-running-insecure-content',
                '--disable-features=VizDisplayCompositor',
                '--force-device-scale-factor=1',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--allow-file-access-from-files',
            ]
        )
        
        return self.browser
    
    async def _wait_for_slide_ready(self, page: Page) -> None:
        """Wait for slide to be fully loaded and rendered."""
        try:
            # Wait for document ready state
            await page.wait_for_load_state('domcontentloaded', timeout=self.wait_timeout)
            await page.wait_for_load_state('networkidle', timeout=self.wait_timeout)
            
            # Wait for common JavaScript frameworks
            await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        // Wait for jQuery if present
                        if (typeof window.jQuery !== 'undefined') {
                            window.jQuery(document).ready(() => {
                                setTimeout(resolve, 500);
                            });
                            return;
                        }
                        
                        // Wait for Chart.js if present
                        if (typeof window.Chart !== 'undefined') {
                            setTimeout(resolve, 1500);
                            return;
                        }
                        
                        // Wait for reveal.js if present
                        if (typeof window.Reveal !== 'undefined') {
                            if (window.Reveal.isReady && window.Reveal.isReady()) {
                                setTimeout(resolve, 500);
                            } else {
                                window.Reveal.addEventListener('ready', () => {
                                    setTimeout(resolve, 500);
                                });
                            }
                            return;
                        }
                        
                        // Default wait for other dynamic content
                        setTimeout(resolve, 500);
                    });
                }
            """)
            
            # Additional delay for animations and dynamic content
            await asyncio.sleep(self.load_delay)
            
        except Exception as e:
            logger.warning(f"Page ready check failed: {e}")
    
    async def _inject_print_styles(self, page: Page) -> None:
        """Inject CSS optimized for PDF printing."""
        await page.add_style_tag(content="""
            @media print {
                * {
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                    color-adjust: exact !important;
                }
                
                body {
                    margin: 0 !important;
                    padding: 0 !important;
                }
                
                /* Hide elements that shouldn't appear in PDF */
                .no-print,
                .slide-number,
                .progress,
                .controls,
                nav,
                .navigation {
                    display: none !important;
                }
                
                /* Ensure slides fill the page */
                .slide,
                .reveal .slides section,
                .remark-slide-container {
                    width: 100% !important;
                    height: 100vh !important;
                    page-break-after: always !important;
                    box-sizing: border-box !important;
                }
                
                /* Prevent content from breaking across pages */
                .slide-content,
                .slide > div {
                    page-break-inside: avoid !important;
                }
                
                /* Ensure images are properly sized */
                img {
                    max-width: 100% !important;
                    height: auto !important;
                }
                
                /* Chart.js canvas elements */
                canvas {
                    page-break-inside: avoid !important;
                }
            }
        """)
    
    async def _render_slide_to_pdf(self, html_path: Path, output_path: Path) -> bool:
        """
        Render a single HTML slide to PDF.
        
        Args:
            html_path: Path to HTML slide file
            output_path: Path to save PDF
            
        Returns:
            True if successful, False otherwise
        """
        try:
            page = await self.browser.new_page()
            
            # Set viewport for consistent rendering
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Load the HTML file
            file_url = f"file://{html_path.resolve()}"
            logger.info(f"Loading slide: {html_path.name}")
            
            await page.goto(file_url, wait_until='domcontentloaded', timeout=self.wait_timeout)
            
            # Inject print-optimized styles
            await self._inject_print_styles(page)
            
            # Wait for slide to be fully rendered
            await self._wait_for_slide_ready(page)
            
            # Configure PDF options
            pdf_options = {
                "path": str(output_path),
                "format": self.page_format,
                "landscape": self.orientation.lower() == "landscape",
                "margin": self.margin,
                "print_background": True,
                "scale": self.scale,
                "prefer_css_page_size": True,
            }
            
            # Generate PDF
            await page.pdf(**pdf_options)
            
            await page.close()
            
            logger.info(f"Successfully rendered: {html_path.name} -> {output_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to render {html_path.name}: {e}")
            try:
                await page.close()
            except:
                pass
            return False
    
    def _parse_slide_order_from_presentation(self, presentation_html: Path, src_dir: Path) -> List[Path]:
        """Extract slide order from presentation.html if available."""
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
    
    def _collect_html_slides(self, src_dir: Path) -> List[Path]:
        """Collect all HTML slides in directory, excluding presentation.html."""
        slides = []
        
        # First try to get order from presentation.html
        presentation_html = src_dir / "presentation.html"
        ordered = self._parse_slide_order_from_presentation(presentation_html, src_dir)
        
        if ordered:
            slides = ordered
        else:
            # Fallback to alphabetical order
            slides = sorted([p for p in src_dir.glob("*.html") 
                           if p.name.lower() != "presentation.html"])
        
        # Special case: if only index.html exists, use it
        if len(slides) == 0:
            index_html = src_dir / "index.html"
            if index_html.exists():
                slides = [index_html]
        
        return slides
    
    def _merge_pdfs(self, pdf_paths: List[Path], output_path: Path) -> None:
        """Merge multiple PDF files into a single PDF."""
        logger.info(f"Merging {len(pdf_paths)} PDF files...")
        
        merger = PdfMerger()
        try:
            for pdf_path in pdf_paths:
                if pdf_path.exists():
                    merger.append(str(pdf_path))
                else:
                    logger.warning(f"PDF file not found: {pdf_path}")
            
            with open(output_path, 'wb') as output_file:
                merger.write(output_file)
            
            logger.info(f"Successfully merged PDFs to: {output_path}")
            
        finally:
            merger.close()
    
    async def convert_slides_to_pdf(self, src_dir: Path, output_path: Path) -> None:
        """
        Convert all HTML slides in directory to a single PDF.
        
        Args:
            src_dir: Directory containing HTML slide files
            output_path: Path for output PDF file
        """
        if not src_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {src_dir}")
        
        # Collect HTML slides
        slide_files = self._collect_html_slides(src_dir)
        if not slide_files:
            raise ValueError(f"No HTML slides found in: {src_dir}")
        
        logger.info(f"Found {len(slide_files)} slides to convert")
        
        # Create output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize browser
        await self._setup_browser()
        
        try:
            # Create temporary directory for individual PDF files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                pdf_files = []
                
                # Render each slide to individual PDF
                for i, slide_file in enumerate(slide_files):
                    pdf_file = temp_path / f"slide_{i:03d}.pdf"
                    
                    if await self._render_slide_to_pdf(slide_file, pdf_file):
                        pdf_files.append(pdf_file)
                    else:
                        logger.warning(f"Skipping failed slide: {slide_file.name}")
                
                if not pdf_files:
                    raise RuntimeError("No slides were successfully rendered")
                
                # Merge all PDFs into final output
                self._merge_pdfs(pdf_files, output_path)
                
        finally:
            # Clean up browser
            if self.browser:
                await self.browser.close()
    
    async def __aenter__(self):
        await self._setup_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()


async def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Convert HTML slides to PDF using Playwright browser rendering"
    )
    parser.add_argument(
        "--src-dir", 
        required=True, 
        help="Directory containing HTML slide files"
    )
    parser.add_argument(
        "--out", 
        help="Output PDF path (default: slides.pdf in source directory)"
    )
    parser.add_argument(
        "--page-format", 
        default="A4",
        help="PDF page format (default: A4)"
    )
    parser.add_argument(
        "--orientation", 
        default="landscape",
        choices=["landscape", "portrait"],
        help="Page orientation (default: landscape)"
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=30000,
        help="Page load timeout in milliseconds (default: 30000)"
    )
    parser.add_argument(
        "--load-delay",
        type=float,
        default=2.0,
        help="Additional delay for JS execution in seconds (default: 2.0)"
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Page scale factor (default: 1.0)"
    )
    
    args = parser.parse_args()
    
    # Validate paths
    src_dir = Path(args.src_dir).resolve()
    if not src_dir.exists():
        raise SystemExit(f"Source directory not found: {src_dir}")
    
    output_path = Path(args.out).resolve() if args.out else (src_dir / "slides.pdf")
    
    # Convert slides
    try:
        converter = PlaywrightPDFConverter(
            page_format=args.page_format,
            orientation=args.orientation,
            wait_timeout=args.wait_timeout,
            load_delay=args.load_delay,
            scale=args.scale
        )
        
        await converter.convert_slides_to_pdf(src_dir, output_path)
        
        print(f"✅ Successfully converted slides to: {output_path}")
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
