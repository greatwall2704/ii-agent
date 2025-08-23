import json
import os
import shutil
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Any, Optional

from ii_agent.llm.message_history import MessageHistory
from ii_agent.tools.base import LLMTool, ToolImplOutput
from ii_agent.utils.workspace_manager import WorkspaceManager


class SlideInitializeTool(LLMTool):
    name = "slide_initialize"
    description = (
        "Initializes a presentation project structure. Creates directories, a project "
        "configuration file, and blank HTML files for each slide based on a provided "
        "outline and style instructions. This tool sets up the project, but does not "
        "fill content into slides."
    )

    input_schema = {
        "type": "object",
        "properties": {
            "main_title": {
                "type": "string",
                "description": "The main title of the presentation.",
            },
            "project_dir": {
                "type": "string",
                "description": "The root directory path for the presentation project.",
            },
            "outline": {
                "type": "array",
                "description": "An array of objects, each describing a slide.",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Unique identifier for the slide, used as the HTML filename (e.g., 'intro').",
                        },
                        "page_title": {
                            "type": "string",
                            "description": "The title to be displayed on the slide.",
                        },
                        "summary": {
                            "type": "string",
                            "description": "A brief summary of the slide's content.",
                        },
                        "content_outline": {
                            "type": "array",
                            "description": "Detailed outline/bullet points for the slide content.",
                            "items": {
                                "type": "string",
                                "description": "A bullet point or content item for the slide.",
                            },
                        },
                    },
                    "required": ["id", "page_title", "summary", "content_outline"],
                },
            },
            "style_instruction": {
                "type": "object",
                "description": "Detailed instructions for the visual style of the presentation.",
                "properties": {
                    "theme": {
                        "type": "string",
                        "description": "A descriptive name for the overall theme (e.g., 'professional_corporate', 'playful_creative').",
                    },
                    "color_palette": {
                        "type": "object",
                        "description": "Defines the key colors for the presentation.",
                        "properties": {
                            "primary": {"type": "string"},
                            "secondary": {"type": "string"},
                            "background": {"type": "string"},
                            "text_color": {"type": "string"},
                            "header_color": {"type": "string"},
                        },
                        "required": ["primary", "background", "text_color", "header_color"],
                    },
                    "typography": {
                        "type": "object",
                        "description": "Defines the fonts for the presentation.",
                        "properties": {
                            "header_font": {"type": "string"},
                            "body_font": {"type": "string"},
                        },
                        "required": ["header_font", "body_font"],
                    },
                    "layout_description": {
                        "type": "string",
                        "description": "A text description of the desired layout (e.g., 'Use two-column layouts for slides with text and images.').",
                    },
                },
                "required": ["theme", "color_palette", "typography", "layout_description"],
            },
        },
        "required": ["main_title", "project_dir", "outline", "style_instruction"],
    }

    def __init__(self, workspace_manager: WorkspaceManager = None):
        self.workspace_manager = workspace_manager

    async def run_impl(self, tool_input: dict[str, Any], message_history: Optional[MessageHistory] = None) -> ToolImplOutput:
        return self.execute(
            tool_input["main_title"],
            tool_input["project_dir"], 
            tool_input["outline"],
            tool_input["style_instruction"]
        )

    def _get_base_html_template(self, title: str, css_path: str) -> str:
        # Basic HTML template for each slide
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1"></script>
    <link rel="stylesheet" href="{css_path}">
</head>
<body>
    <div class="slide-container">
        <!-- All components for the slide will be added here by the AI -->
    </div>
</body>
</html>"""

    def _get_main_css_content(self, style_instruction: dict) -> str:
        # --- 1. Extract and Sanitize Variables ---
        
        # Color Palette
        primary_color = style_instruction.get('color_palette', {}).get('primary', '#1E88E5')
        background_color = style_instruction.get('color_palette', {}).get('background', '#FFFFFF')
        text_color = style_instruction.get('color_palette', {}).get('text_color', '#333333')
        header_color = style_instruction.get('color_palette', {}).get('header_color', primary_color)
        secondary_color = style_instruction.get('color_palette', {}).get('secondary', '#0D47A1')
        accent_color = style_instruction.get('color_palette', {}).get('accent', '#FFC107')
        primary_light = style_instruction.get('color_palette', {}).get('primary_light', '#64B5F6')
        primary_dark = style_instruction.get('color_palette', {}).get('primary_dark', '#0D47A1')
        light_gray = style_instruction.get('color_palette', {}).get('light_gray', '#F5F9FF')
        
        # Functional Colors
        success_color = style_instruction.get('color_palette', {}).get('success', '#4CAF50')
        warning_color = style_instruction.get('color_palette', {}).get('warning', '#FF9800')
        danger_color = style_instruction.get('color_palette', {}).get('danger', '#F44336')
        info_color = style_instruction.get('color_palette', {}).get('info', '#2196F3')

        # Typography
        header_font = style_instruction.get('typography', {}).get('header_font', 'Roboto')
        body_font = style_instruction.get('typography', {}).get('body_font', 'Open Sans')
        header_size = style_instruction.get('typography', {}).get('header_size', '36px')
        subheader_size = style_instruction.get('typography', {}).get('subheader_size', '24px')
        body_size = style_instruction.get('typography', {}).get('body_size', '18px')

        # Helper to ensure colors have a '#' prefix
        def ensure_hex_prefix(color):
            return f"#{color.lstrip('#')}"

        # Apply prefix to all colors
        primary_color = ensure_hex_prefix(primary_color)
        secondary_color = ensure_hex_prefix(secondary_color)
        background_color = ensure_hex_prefix(background_color)
        text_color = ensure_hex_prefix(text_color)
        header_color = ensure_hex_prefix(header_color)
        accent_color = ensure_hex_prefix(accent_color)
        primary_light = ensure_hex_prefix(primary_light)
        primary_dark = ensure_hex_prefix(primary_dark)
        light_gray = ensure_hex_prefix(light_gray)
        success_color = ensure_hex_prefix(success_color)
        warning_color = ensure_hex_prefix(warning_color)
        danger_color = ensure_hex_prefix(danger_color)
        info_color = ensure_hex_prefix(info_color)

        # --- 2. Generate CSS String ---
        return f"""/*
* =========================================
* main.css - Custom Slide Deck Stylesheet
* =========================================
*/

/* -----------------------------------------
 * 1. CSS Variables & Base Setup
 * ----------------------------------------- */
:root {{
  /* Color Palette */
  --primary-color: {primary_color};
  --primary-dark: {primary_dark};
  --primary-light: {primary_light};
  --secondary-color: {secondary_color};
  --accent-color: {accent_color};
  
  /* Background & Text Colors */
  --background-color: {background_color};
  --text-color: {text_color};
  --header-color: {header_color};
  --light-gray: {light_gray};
  
  /* Functional Colors */
  --success-color: {success_color};
  --warning-color: {warning_color};
  --danger-color: {danger_color};
  --info-color: {info_color};
  
  /* Typography */
  --header-font: '{header_font}', 'Roboto', sans-serif;
  --body-font: '{body_font}', 'Open Sans', sans-serif;
  
  /* Font Sizes */
  --header-size: {header_size};
  --subheader-size: {subheader_size};
  --body-size: {body_size};
}}

* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

html, body {{
  width: 100%;
  height: 100%;
  overflow: hidden;
}}

body {{
  font-family: var(--body-font);
  background-color: #e0e0e0; /* Light gray background outside the slide */
  color: var(--text-color);
  line-height: 1.6;
  display: flex;
  justify-content: center;
  align-items: center;
}}

/* -----------------------------------------
 * 2. Core Slide Structure
 * ----------------------------------------- */
.slide-container {{
  width: 1280px;
  min-height: 720px;
  background: var(--background-color);
  margin: 0 auto;
  padding: 40px;
  display: flex;
  flex-direction: column;
  position: relative;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden; /* Crucial for border-radius and absolute children */
}}

.slide-header {{
  margin-bottom: 30px;
  flex-shrink: 0; /* Prevent header from shrinking */
}}

.slide-title {{
  font-size: var(--header-size);
  color: var(--header-color);
  font-weight: bold;
  text-align: center;
  font-family: var(--header-font);
}}

.slide-content {{
  display: flex;
  flex: 1; /* Allow content to fill remaining space */
  gap: 40px;
  min-height: 0; /* Fix for flexbox overflow issues */
}}

/* -----------------------------------------
 * 3. Special Slide Types
 * ----------------------------------------- */

/* --- A. Opening / Title Slide --- */
.slide-container.title-slide {{
  padding: 0;
  justify-content: center;
  align-items: center;
  color: white; /* Default text color for this slide */
}}  

.title-slide .slide-background-image {{
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: brightness(0.6) saturate(1.1);
  z-index: 1;
}}

.title-slide .content-overlay {{
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px;
  text-align: center;
  width: 100%;
  height: 100%;
}}

.title-slide .main-title {{
  color: white;
  font-size: 52px;
  text-shadow: 2px 2px 8px rgba(0, 0, 0, 0.7);
}}

.title-slide .subtitle {{
  color: #e0e0e0;
  font-size: 30px;
  max-width: 80%;
  text-shadow: 1px 1px 4px rgba(0, 0, 0, 0.7);
  margin-top: 1rem;
}}

.title-slide .presenter-info {{
  margin-top: 40px;
  color: #d0d0d0;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  padding-top: 20px;
}}

/* --- B. Thank You Slide --- */
.thank-you-slide-content {{
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  height: 100%;
}}
.thank-you-title {{
  font-size: calc(var(--header-size) * 1.5);
  color: var(--primary-color);
  margin-bottom: 20px;
}}
.thank-you-subtitle {{
  font-size: var(--header-size);
  color: var(--secondary-color);
  margin-bottom: 40px;
}}
.contact-info {{
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 40px;
}}
.contact-item {{
  display: flex;
  align-items: center;
  gap: 10px;
}}
.contact-item i {{
  color: var(--primary-color);
}}

/* --- C. Quote Slide --- */
.quote-slide-content {{
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  height: 100%;
  padding: 0 80px;
}}
.quote-icon {{
  font-size: 48px;
  color: var(--primary-light);
  margin-bottom: 20px;
}}
.quote-text {{
  font-size: calc(var(--body-size) * 1.5);
  font-style: italic;
  line-height: 1.6;
  margin-bottom: 30px;
}}
.quote-attribution {{
  margin-top: 20px;
}}
.quote-author {{
  font-size: calc(var(--body-size) * 1.2);
  font-weight: bold;
  color: var(--primary-color);
}}
.quote-source {{
  font-size: var(--body-size);
}}

/* -----------------------------------------
 * 4. Content Components
 * ----------------------------------------- */

/* --- A. Text & Lists --- */
.slide-text {{
  flex: 1;
  display: flex;
  flex-direction: column;
}}
.section-title {{
  font-size: var(--subheader-size);
  color: var(--primary-dark);
  margin-bottom: 15px;
  font-weight: 600;
  font-family: var(--header-font);
}}
.section-content {{
  font-size: var(--body-size);
  line-height: 1.5;
}}
.highlighted-section {{
  background-color: var(--light-gray);
  border-left: 4px solid var(--primary-color);
  padding: 20px;
  border-radius: 0 10px 10px 0;
  margin: 20px 0;
}}
.slide-list {{ list-style-type: none; padding: 0; }}
.slide-list li {{ margin-bottom: 1rem; padding-left: 1.5rem; position: relative; }}
.slide-list li:before {{
  content: ""; position: absolute; left: 0; top: 0.5rem;
  width: 0.5rem; height: 0.5rem; background-color: var(--primary-light); border-radius: 50%;
}}

/* --- B. Image Blocks --- */
.slide-image {{
  flex: 0 0 45%;
  display: flex;
  justify-content: center;
  align-items: center;
  max-height: 500px;
  overflow: hidden;
}}
.image-wrapper {{
  display: flex; flex-direction: column; align-items: center;
  width: 100%; height: 100%;
}}
.slide-image img {{
  max-width: 100%; max-height: calc(100% - 30px);
  width: auto; height: auto; object-fit: contain;
  border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}}
.image-caption {{
  margin-top: 10px; padding: 0 10px; font-size: 14px;
  color: #666; text-align: center; font-style: italic;
  width: 100%; flex-shrink: 0;
}}

/* --- C. Code Blocks (Scalable) --- */
.code-scaler {{
  width: 100%;
  overflow: hidden;
  margin-top: 10px;
  margin-bottom: 15px;
}}
.code-block {{
  background-color: #2d3748;
  color: #e2e8f0;
  padding-top: 15px;
  padding-left: 15px;
  padding-right: 15px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  font-family: 'Fira Code', 'JetBrains Mono', 'Courier New', monospace;
  font-size: 16px;
  white-space: pre;
  display: inline-block;
  min-width: 100%;
  transform-origin: left top;
  transition: transform 0.2s ease-in-out;
}}

/* --- D. Charts & Tables --- */
.chart-container {{
  flex: 1; /* Cho phép co giãn trong layout flex */
  display: flex;
  flex-direction: column; /* Xếp canvas và tiêu đề theo chiều dọc */
  justify-content: center; /* Căn giữa theo chiều dọc */
  align-items: center;   /* Căn giữa theo chiều ngang */
  
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  background: rgba(255, 255, 255, 0.8); /* Nền bán trong suốt để nổi bật */
  min-height: 300px; /* Đảm bảo biểu đồ không quá nhỏ */
  margin-bottom: 20px; /* Khoảng cách nếu có nhiều biểu đồ xếp chồng */
}}

/* Lớp bọc cho canvas để kiểm soát kích thước và co giãn */
.canvas-wrapper {{
    width: 100%;
    flex-grow: 1; /* Cho phép canvas chiếm không gian dọc còn lại */
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 0; /* Sửa lỗi co giãn của flexbox */
}}

/* Canvas của Chart.js */
.chart-container canvas {{
  max-width: 100%;
  max-height: 100%;
}}

/* Tiêu đề của biểu đồ, nằm dưới canvas */
.chart-title {{
  /* Đây là một khối văn bản bình thường, không dùng position: absolute */
  margin-top: 15px; /* Khoảng cách với biểu đồ ở trên */
  font-size: 18px;
  font-weight: 600;
  font-family: var(--header-font);
  color: var(--primary-dark);
  text-align: center;
  width: 100%;
  flex-shrink: 0; /* Ngăn tiêu đề bị co lại */
}}

/* Modifiers cho các kích thước biểu đồ khác nhau */
.chart-container.full-width {{
  flex-basis: 100%;
  height: 500px;
}}
.chart-container.small {{
  flex-basis: 300px;
  height: 250px;
}}

/* Chú thích (legend) tùy chỉnh nếu cần */
.chart-legend {{
  margin-top: 15px;
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 15px;
}}
.chart-legend-item {{
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
}}
.chart-legend-color {{
  width: 12px;
  height: 12px;
  border-radius: 2px;
}}
/* Container cho bảng so sánh */
.comparison-table-container {{
  width: 100%;
  overflow-x: auto;
  margin: 20px 0;
  border-radius: 10px;
  border: 1px solid var(--light-gray, #E0E0E0);
  overflow: hidden;
}}

/* Bảng so sánh */
.comparison-table {{
  width: 100%;
  border-collapse: collapse;
}}
.comparison-table th, .comparison-table td {{
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid var(--light-gray, #E0E0E0);
}}
.comparison-table th {{
  background-color: var(--primary-color);
  color: white;
  font-weight: bold;
}}
.comparison-table tr:nth-child(even) {{
  background-color: var(--light-gray);
}}
.comparison-table tr:last-child td {{
  border-bottom: none;
}}
/* -----------------------------------------
 * 5. Layout Systems
 * ----------------------------------------- */

/* --- A. Code Layout --- */
.slide-content.code-layout {{
  display: flex;
  gap: 40px;
  align-items: flex-start; /* Align columns to the top */
}}
.code-layout .slide-text {{
  flex: 0 0 40%;
  padding-right: 20px;
}}
.code-layout .slide-code {{
  flex: 1;
  display: flex;
  flex-direction: column;
  max-height: 600px; /* Set a max height for the code column */
  overflow-y: auto;  /* Add vertical scroll if code column is too long */
}}
.code-title {{
  font-size: 18px;
  font-family: var(--header-font);
  color: var(--primary-dark);
  margin-top: 15px;
  margin-bottom: 5px;
  font-weight: 600;
}}
.code-layout .slide-code .code-title:first-child {{
    margin-top: 0;
}}

/* --- B. Standard Layouts --- */
.slide-content.two-column {{ align-items: stretch; }}
.two-column .slide-text {{ padding-right: 20px; }}
.two-column .slide-image, .two-column .chart-container {{ flex: 0 0 45%; }}

.slide-content.three-column {{ display: flex; gap: 30px; align-items: stretch; }}
.three-column .slide-text {{ flex: 0 0 35%; }}
.three-column .slide-image, .three-column .chart-container {{ flex: 0 0 30%; }}

.slide-content.vertical {{ flex-direction: column; }}

.slide-content.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }}

.slide-content.image-only, .slide-content.chart-only {{ justify-content: center; align-items: center; }}
.image-only .slide-image, .chart-only .chart-container {{ flex: none; width: 90%; height: 80%; }}
.slide-content.gallery {{
  display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px; padding: 20px 0;
}}

.gallery .slide-image {{ height: 150px; }}
.slide-content.text-wrap {{ display: block; }}
.text-wrap .slide-image {{
  float: right; margin: 0 0 20px 20px;
  max-width: 40%; max-height: 300px;
}}
.text-wrap .slide-text {{ text-align: justify; }}
/* -----------------------------------------
 * 6. Responsive Design
 * ----------------------------------------- */
@media (max-width: 1280px) {{
  .slide-container {{
    width: 100%;
    height: auto;
    min-height: 0;
    padding: 20px;
  }}
  .slide-content, .slide-content.two-column, .slide-content.three-column, .slide-content.code-layout {{
    flex-direction: column;
    gap: 20px;
  }}
  .slide-image, .chart-container {{
    flex: none !important;
    max-height: 300px;
  }}
}}
@media (max-width: 768px) {{
  :root {{
    --header-size: calc({header_size} * 0.8);
    --subheader-size: calc({subheader_size} * 0.8);
    --body-size: calc({body_size} * 0.9);
  }}
  .slide-container {{ padding: 15px; }}
  .chart-container {{ height: 250px; padding: 10px; }}
  .slide-image {{ max-height: 200px; }}
  .title-slide .main-title {{ font-size: 36px; }}
  .title-slide .subtitle {{ font-size: 22px; }}
}}
"""


    def execute(self, main_title: str, project_dir: str, outline: list, style_instruction: dict) -> ToolImplOutput:
        project_path = Path(project_dir)
        slides_path = project_path / "slides"
        css_path = project_path / "css"

        # 1. Create directory structure (NO assets directory as per system prompt)
        os.makedirs(slides_path, exist_ok=True)
        os.makedirs(css_path, exist_ok=True)

        # 2. Save project configuration
        config = {
            "main_title": main_title,
            "project_dir": str(project_path),
            "outline": outline,
            "style_instruction": style_instruction,
            "slides_order": [s['id'] for s in outline]
        }
        with open(project_path / "config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # 3. Create main CSS file
        main_css_content = self._get_main_css_content(style_instruction)
        with open(css_path / "main.css", "w", encoding="utf-8") as f:
            f.write(main_css_content)

        # 4. Create empty HTML files for each slide
        for slide_info in outline:
            slide_id = slide_info['id']
            page_title = slide_info['page_title']
            slide_html_path = slides_path / f"{slide_id}.html"
            
            # Relative path from slide HTML to main.css
            relative_css_path = os.path.relpath(css_path / "main.css", slides_path)
            
            base_html = self._get_base_html_template(page_title, relative_css_path)
            with open(slide_html_path, "w", encoding="utf-8") as f:
                f.write(base_html)
        
        # Return success message
        return ToolImplOutput(
            tool_output=f"Presentation project '{main_title}' has been initialized at '{project_dir}'.",
            tool_result_message=f"Successfully initialized presentation project at {project_dir}"
        )


class SlidePresentTool(LLMTool):
    name = "slide_present"
    description = (
        "Presents a presentation project. This tool reads the project configuration "
        "and generates a main presentation HTML file that links to or embeds "
        "individual slide HTML files, providing a viewable presentation URL."
    )

    input_schema = {
        "type": "object",
        "properties": {
            "project_dir": {
                "type": "string",
                "description": "Absolute path of the presentation project directory.",
            },
            "slide_ids": {
                "type": "array",
                "description": "A list of unique slide identifiers to be presented, in the desired presentation order.",
                "items": {"type": "string"},
            },
        },
        "required": ["project_dir", "slide_ids"],
    }

    def __init__(self, workspace_manager: WorkspaceManager = None):
        self.workspace_manager = workspace_manager

    async def run_impl(self, tool_input: dict[str, Any], message_history: Optional[MessageHistory] = None) -> ToolImplOutput:
        return self.execute(tool_input["project_dir"], tool_input["slide_ids"])

    def execute(self, project_dir: str, slide_ids: list) -> ToolImplOutput:
        project_path = Path(project_dir)
        config_path = project_path / "config.json"
        slides_path = project_path / "slides"

        if not config_path.exists():
            return ToolImplOutput(
                tool_output=f"Error: Configuration file not found at '{config_path}'. Please initialize project first.",
                tool_result_message="Configuration file not found"
            )

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        main_title = config.get("main_title", "Presentation")
        all_slides_info = {s['id']: s for s in config['outline']}

        # Create HTML for main presentation page
        presentation_html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{main_title}</title>
    <style>
        body {{ margin: 0; overflow: hidden; font-family: sans-serif; }}
        iframe {{ border: none; width: 100vw; height: 100vh; }}
        .navigation-controls {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7);
            padding: 10px 20px;
            border-radius: 10px;
            display: flex;
            gap: 10px;
            z-index: 1000;
        }}
        .navigation-controls button {{
            background: var(--primary-color, #4B72B0);
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        .navigation-controls button:disabled {{
            background: #cccccc;
            cursor: not-allowed;
        }}
        .navigation-controls span {{
            color: white;
            font-size: 18px;
            display: flex;
            align-items: center;
        }}
    </style>
</head>
<body>
    <iframe id="slideFrame" src="" allowfullscreen></iframe>

    <div class="navigation-controls">
        <button id="prevBtn">Previous</button>
        <span id="slideIndicator">1 / {len(slide_ids)}</span>
        <button id="nextBtn">Next</button>
    </div>

    <script>
        const slideIds = {json.dumps(slide_ids)};
        let currentSlideIndex = 0;
        const slideFrame = document.getElementById('slideFrame');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const slideIndicator = document.getElementById('slideIndicator');

        function updateSlide() {{
            const slideId = slideIds[currentSlideIndex];
            slideFrame.src = `slides/${{slideId}}.html`;
            slideIndicator.textContent = `${{currentSlideIndex + 1}} / ${{slideIds.length}}`;
            prevBtn.disabled = currentSlideIndex === 0;
            nextBtn.disabled = currentSlideIndex === slideIds.length - 1;
        }}

        function nextSlide() {{
            if (currentSlideIndex < slideIds.length - 1) {{
                currentSlideIndex++;
                updateSlide();
            }}
        }}

        function prevSlide() {{
            if (currentSlideIndex > 0) {{
                currentSlideIndex--;
                updateSlide();
            }}
        }}

        prevBtn.addEventListener('click', prevSlide);
        nextBtn.addEventListener('click', nextSlide);

        // Navigation with arrow keys
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight') {{
                nextSlide();
            }} else if (e.key === 'ArrowLeft') {{
                prevSlide();
            }}
        }});

        updateSlide(); // Load first slide when page loads
    </script>
</body>
</html>"""

        presentation_file_path = project_path / "presentation.html"
        with open(presentation_file_path, "w", encoding="utf-8") as f:
            f.write(presentation_html_content)

        # Assume system has mechanism to create access URL for this file
        # This part needs integration with actual system
        presentation_url = f"slides://{project_path.name}/presentation.html"

        return ToolImplOutput(
            tool_output=f"Presentation is ready: {presentation_url}",
            tool_result_message="Presentation generated successfully",
            auxiliary_data={"url": presentation_url}
        )


class SlideContentWriterTool(LLMTool):
    name = "slide_content_writer"
    description = (
         "Injects HTML content into a specific slide file that has already been created by 'slide_initialize'. "
        "This tool safely modifies the existing file to prevent HTML nesting errors."
        )

    input_schema = {
        "type": "object",
        "properties": {
            "project_dir": {
                "type": "string",
                "description": "Absolute path of the presentation project directory.",
            },
            "slide_id": {
                "type": "string",
                "description": "The unique identifier of the slide to write content to (e.g., 'intro').",
            },
            "slide_content": {
                "type": "string",
                "description": "The inner HTML content to be placed inside the slide's main container.",
            },
        },
        "required": ["project_dir", "slide_id", "slide_content"],
    }

    def __init__(self, workspace_manager: WorkspaceManager = None):
        self.workspace_manager = workspace_manager

    async def run_impl(self, tool_input: dict[str, Any], message_history: Optional[MessageHistory] = None) -> ToolImplOutput:
        return self.execute(
            tool_input["project_dir"],
            tool_input["slide_id"], 
            tool_input["slide_content"]
        )

    def execute(self, project_dir: str, slide_id: str, slide_content: str) -> ToolImplOutput:
        project_path = Path(project_dir)
        slides_path = project_path / "slides"
        slide_file_path = slides_path / f"{slide_id}.html"

        # Check if project exists
        if not slide_file_path.exists():
            return ToolImplOutput(
                tool_output=f"Error: Slide file not found at '{slide_file_path}'. Please ensure the project is initialized correctly before writing content.",
                tool_result_message="Slide file not found"
            )

        # Validate slide_content
        if not slide_content.strip():
            return ToolImplOutput(
                tool_output=f"Error: slide_content cannot be empty for slide '{slide_id}'.",
                tool_result_message="Empty slide content"
            )

        try:
            with open(slide_file_path, "r", encoding="utf-8") as f:
                existing_html = f.read()

            soup = BeautifulSoup(existing_html, 'lxml')

            container = soup.find('div', class_='slide-container')

            if not container:
                return ToolImplOutput(
                    tool_output=f"Error: Could not find the '<div class=\"slide-container\">' in '{slide_file_path}'. The slide template might be corrupted.",
                    tool_result_message="Slide container not found"
                )

            container.clear()
            container.append(BeautifulSoup(slide_content, 'html.parser'))

            with open(slide_file_path, "w", encoding="utf-8") as f:
                f.write(soup.prettify(formatter="html5"))

            return ToolImplOutput(
                tool_output=f"✓ Successfully wrote content to slide '{slide_id}'. File updated at: {slide_file_path}",
                tool_result_message=f"Content for slide {slide_id} written successfully."
            )

        except Exception as e:
            return ToolImplOutput(
                tool_output=f"An unexpected error occurred while writing to slide '{slide_id}': {e}",
                tool_result_message="An unexpected error occurred"
            )

# Export main classes
__all__ = ['SlideInitializeTool', 'SlidePresentTool', 'SlideContentWriterTool']