#!/usr/bin/env python
"""
Convert HTML slide files to PDF using headless browser rendering.

This script implements the approach described:
1. Initialize render environment (headless browser)
2. Render each slide to PDF page
3. Merge PDF pages
4. Optimize and save

Features:
- Faithful rendering using headless Chrome/Chromium
- Supports JavaScript-generated content (charts, animations)
- Proper page breaks between slides
- Waits for dynamic content to load
- Maintains original layout, colors, fonts

Usage:
    python scripts/html_slides_to_pdf.py --src-dir <folder> --out <output.pdf>

Dependencies:
    pip install selenium PyPDF2 pillow webdriver-manager
    Chrome/Chromium browser required
"""

from __future__ import annotations

import argparse
import base64
import json
import time
from pathlib import Path
from typing import List, Optional
import tempfile
import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PyPDF2 import PdfMerger
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HTMLToPDFConverter:
    """Convert HTML slides to PDF using headless browser rendering."""
    
    def __init__(self, page_size: str = "A4", orientation: str = "landscape", 
                 wait_timeout: int = 10, load_delay: float = 2.0):
        """
        Initialize converter.
        
        Args:
            page_size: PDF page size (A4, Letter, etc.)
            orientation: Page orientation (landscape/portrait)
            wait_timeout: Maximum wait time for page load (seconds)
            load_delay: Additional delay after page load for JS execution (seconds)
        """
        self.page_size = page_size
        self.orientation = orientation
        self.wait_timeout = wait_timeout
        self.load_delay = load_delay
        self.driver: Optional[webdriver.Chrome] = None
        
    def _setup_browser(self) -> webdriver.Chrome:
        """Initialize headless Chrome browser with optimized settings."""
        chrome_options = Options()
        
        # Headless mode
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Set window size for consistent rendering (can be adjusted based on slide dimensions)
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Optimize for slide rendering
        chrome_options.add_argument('--force-device-scale-factor=1')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        
        # Enable local file access
        chrome_options.add_argument('--allow-file-access-from-files')
        chrome_options.add_argument('--disable-web-security')
        
        # PDF printing preferences
        prefs = {
            'printing.print_preview_sticky_settings.appState': json.dumps({
                'recentDestinations': [{
                    'id': 'Save as PDF',
                    'origin': 'local',
                    'account': '',
                }],
                'selectedDestinationId': 'Save as PDF',
                'version': 2,
                'isHeaderFooterEnabled': False,
                'isLandscapeEnabled': self.orientation.lower() == 'landscape',
                'isCssBackgroundEnabled': True,
                'isCollateEnabled': True,
                'isColorEnabled': True,
                'isDuplexEnabled': False,
                'isHeaderFooterEnabled': False,
                'isSelectionOnly': False,
                'marginsType': 0,  # Default margins
                'pageSize': self.page_size,
                'scalingType': 0,  # Fit to page
                'scaling': '100',
            })
        }
        chrome_options.add_experimental_option('prefs', prefs)
        
        # Use webdriver manager to automatically handle ChromeDriver
        service = Service(ChromeDriverManager().install())
        
        return webdriver.Chrome(service=service, options=chrome_options)
    
    def _wait_for_page_ready(self, driver: webdriver.Chrome) -> None:
        """Wait for page to be fully loaded including JavaScript execution."""
        try:
            # Wait for document ready state
            WebDriverWait(driver, self.wait_timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for potential JavaScript frameworks to initialize
            try:
                # Check for common frameworks and wait for them
                driver.execute_script("""
                    return new Promise((resolve) => {
                        if (typeof jQuery !== 'undefined') {
                            jQuery(document).ready(() => resolve());
                        } else if (typeof Chart !== 'undefined') {
                            // Wait for Chart.js if present
                            setTimeout(() => resolve(), 1000);
                        } else {
                            resolve();
                        }
                    });
                """)
            except Exception:
                pass
            
            # Additional delay for dynamic content
            time.sleep(self.load_delay)
            
        except Exception as e:
            logger.warning(f"Page ready check failed: {e}")
    
    def _render_slide_to_pdf(self, html_path: Path, output_path: Path) -> bool:
        """
        Render a single HTML slide to PDF.
        
        Args:
            html_path: Path to HTML slide file
            output_path: Path to save PDF
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load the HTML file
            file_url = f"file://{html_path.resolve()}"
            logger.info(f"Loading slide: {html_path.name}")
            
            self.driver.get(file_url)
            
            # Wait for page to be fully rendered
            self._wait_for_page_ready(self.driver)
            
            # Generate PDF using Chrome's printing capabilities
            pdf_options = {
                'landscape': self.orientation.lower() == 'landscape',
                'format': self.page_size,
                'printBackground': True,
                'marginTop': 0,
                'marginBottom': 0,
                'marginLeft': 0,
                'marginRight': 0,
                'preferCSSPageSize': True,
            }
            
            # Execute print command and get PDF data
            pdf_data = self.driver.execute_cdp_cmd('Page.printToPDF', pdf_options)
            
            # Decode and save PDF
            with open(output_path, 'wb') as file:
                file.write(base64.b64decode(pdf_data['data']))
            
            logger.info(f"Successfully rendered: {html_path.name} -> {output_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to render {html_path.name}: {e}")
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
    
    def convert_slides_to_pdf(self, src_dir: Path, output_path: Path) -> None:
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
        self.driver = self._setup_browser()
        
        try:
            # Create temporary directory for individual PDF files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                pdf_files = []
                
                # Render each slide to individual PDF
                for i, slide_file in enumerate(slide_files):
                    pdf_file = temp_path / f"slide_{i:03d}.pdf"
                    
                    if self._render_slide_to_pdf(slide_file, pdf_file):
                        pdf_files.append(pdf_file)
                    else:
                        logger.warning(f"Skipping failed slide: {slide_file.name}")
                
                if not pdf_files:
                    raise RuntimeError("No slides were successfully rendered")
                
                # Merge all PDFs into final output
                self._merge_pdfs(pdf_files, output_path)
                
        finally:
            # Clean up browser
            if self.driver:
                self.driver.quit()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Convert HTML slides to PDF using headless browser rendering"
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
        "--page-size", 
        default="A4",
        help="PDF page size (default: A4)"
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
        default=10,
        help="Page load timeout in seconds (default: 10)"
    )
    parser.add_argument(
        "--load-delay",
        type=float,
        default=2.0,
        help="Additional delay for JS execution in seconds (default: 2.0)"
    )
    
    args = parser.parse_args()
    
    # Validate paths
    src_dir = Path(args.src_dir).resolve()
    if not src_dir.exists():
        raise SystemExit(f"Source directory not found: {src_dir}")
    
    output_path = Path(args.out).resolve() if args.out else (src_dir / "slides.pdf")
    
    # Convert slides
    try:
        with HTMLToPDFConverter(
            page_size=args.page_size,
            orientation=args.orientation,
            wait_timeout=args.wait_timeout,
            load_delay=args.load_delay
        ) as converter:
            converter.convert_slides_to_pdf(src_dir, output_path)
        
        print(f"✅ Successfully converted slides to: {output_path}")
        
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
