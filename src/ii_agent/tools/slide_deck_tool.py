import json
import os
from pathlib import Path
from typing import Any, Optional

from ii_agent.llm.message_history import MessageHistory
from ii_agent.tools.base import LLMTool, ToolImplOutput
from ii_agent.utils.workspace_manager import WorkspaceManager


class SlideInitializeTool(LLMTool):
    name = "slide_initialize"
    description = (
        "Initializes a presentation project structure. Creates directories, a project "
        "configuration file, a main CSS file, and blank HTML templates for each slide "
        "based on a provided outline and style instructions."
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
                    },
                    "required": ["id", "page_title", "summary"],
                },
            },
            "style_instruction": {
                "type": "object",
                "description": "Detailed instructions for the visual style of the presentation.",
                "properties": {
                    "theme": {
                        "type": "string",
                        "description": "A descriptive name for the overall theme (e.g., 'professional_corporate', 'playful_creative', 'dark_mode_tech', 'minimalist_elegant').",
                        "enum": [
                            "professional_corporate",
                            "playful_creative",
                            "dark_mode_tech",
                            "minimalist_elegant",
                            "custom",
                        ],
                    },
                    "color_palette": {
                        "type": "object",
                        "description": "Defines the key colors for the presentation.",
                        "properties": {
                            "primary": {
                                "type": "string",
                                "description": "Primary/accent color (e.g., '#4A90E2').",
                            },
                            "secondary": {
                                "type": "string",
                                "description": "Secondary color (e.g., '#F5A623').",
                            },
                            "background": {
                                "type": "string",
                                "description": "Background color (e.g., '#FFFFFF').",
                            },
                            "text_color": {
                                "type": "string",
                                "description": "Main text color (e.g., '#333333').",
                            },
                            "header_color": {
                                "type": "string",
                                "description": "Color for slide titles (e.g., '#000000').",
                            },
                        },
                        "required": [
                            "primary",
                            "background",
                            "text_color",
                            "header_color",
                        ],
                    },
                    "typography": {
                        "type": "object",
                        "description": "Defines the fonts for the presentation.",
                        "properties": {
                            "header_font": {
                                "type": "string",
                                "description": "Font for titles (e.g., 'Montserrat').",
                            },
                            "body_font": {
                                "type": "string",
                                "description": "Font for body text (e.g., 'Lato').",
                            },
                        },
                        "required": ["header_font", "body_font"],
                    },
                    "layout_description": {
                        "type": "string",
                        "description": "A text description of the desired layout (e.g., 'Use two-column layouts for slides with text and images. Keep it clean and spacious.').",
                    },
                },
                "required": ["theme", "color_palette", "typography"],
            },
        },
        "required": ["main_title", "project_dir", "outline", "style_instruction"],
    }

    def __init__(self, workspace_manager: WorkspaceManager):
        super().__init__()
        self.workspace_manager = workspace_manager

    def _get_html_template(self, title: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link rel="stylesheet" href="../style.css">
</head>
<body>
    <div class="slide-container" id="slide-container">
        <h1 id="slide-title">{title}</h1>
        <div id="slide-content-placeholder" class="slide-content">
            <!-- Content for this slide will be added here -->
            <!-- Use class "two-column" for two-column layout -->
            <!-- Use class "three-column" for three-column layout -->
            <!-- Wrap images in "image-container" div -->
            <!-- Wrap charts in "chart-container" div -->
            <!-- Use "info-box" class for content boxes -->
        </div>
    </div>
    
    <script>
        let layoutMode = 'normal'; // normal, compact, ultra-compact
        let isOverflowing = false;
        
        // Kiểm tra và điều chỉnh layout để tránh overflow
        function checkAndAdjustLayout() {{
            const container = document.getElementById('slide-container');
            const content = document.getElementById('slide-content-placeholder');
            const warning = document.getElementById('overflow-warning');
            const indicator = document.querySelector('.layout-indicator') || createLayoutIndicator();
            
            // Reset classes
            container.className = 'slide-container';
            if (warning) warning.classList.add('hidden');
            
            // Kiểm tra overflow
            const isContentOverflowing = container.scrollHeight > container.clientHeight;
            
            if (isContentOverflowing) {{
                // Áp dụng compact layout trước
                if (layoutMode === 'normal') {{
                    layoutMode = 'compact';
                    container.classList.add('compact-layout');
                    indicator.textContent = 'Compact Layout';
                    
                    // Kiểm tra lại sau khi áp dụng compact
                    setTimeout(() => {{
                        if (container.scrollHeight > container.clientHeight) {{
                            layoutMode = 'ultra-compact';
                            container.classList.remove('compact-layout');
                            container.classList.add('ultra-compact-layout');
                            indicator.textContent = 'Ultra-Compact Layout';
                            
                            // Nếu vẫn overflow, hiển thị cảnh báo
                            setTimeout(() => {{
                                if (container.scrollHeight > container.clientHeight) {{
                                    showContentWarning();
                                    indicator.textContent = 'Content Too Long - Consider Splitting';
                                }}
                            }}, 100);
                        }}
                    }}, 100);
                }}
            }} else {{
                indicator.textContent = 'Normal Layout';
                hideContentWarning();
            }}
        }}
        
        function createLayoutIndicator() {{
            const indicator = document.createElement('div');
            indicator.className = 'layout-indicator';
            indicator.textContent = 'Normal Layout';
            document.getElementById('slide-container').appendChild(indicator);
            return indicator;
        }}
        
        function showContentWarning() {{
            let warning = document.getElementById('content-warning');
            if (!warning) {{
                warning = document.createElement('div');
                warning.id = 'content-warning';
                warning.className = 'content-warning';
                warning.innerHTML = '⚠️ Nội dung quá dài<br>Cân nhắc chia thành nhiều slide';
                document.getElementById('slide-container').appendChild(warning);
            }}
            warning.classList.remove('hidden');
        }}
        
        function hideContentWarning() {{
            const warning = document.getElementById('content-warning');
            if (warning) {{
                warning.classList.add('hidden');
            }}
        }}
        
        // Tối ưu hóa hình ảnh để tránh overflow
        function optimizeImages() {{
            const images = document.querySelectorAll('#slide-content-placeholder img');
            images.forEach(img => {{
                if (!img.closest('.image-container')) {{
                    const container = document.createElement('div');
                    container.className = 'image-container';
                    img.parentNode.insertBefore(container, img);
                    container.appendChild(img);
                }}
            }});
        }}
        
        // Tối ưu hóa bảng và biểu đồ
        function optimizeChartsAndTables() {{
            const charts = document.querySelectorAll('#slide-content-placeholder canvas');
            charts.forEach(chart => {{
                if (!chart.closest('.chart-container')) {{
                    const container = document.createElement('div');
                    container.className = 'chart-container';
                    chart.parentNode.insertBefore(container, chart);
                    container.appendChild(chart);
                }}
            }});
        }}
        
        // Xử lý responsive
        function handleResponsive() {{
            const container = document.getElementById('slide-container');
            const screenWidth = window.innerWidth;
            
            // Remove all responsive classes first
            container.classList.remove('mobile-layout', 'tablet-layout', 'desktop-layout');
            
            if (screenWidth <= 768) {{
                container.classList.add('mobile-layout');
            }} else if (screenWidth <= 1024) {{
                container.classList.add('tablet-layout');
            }} else {{
                container.classList.add('desktop-layout');
            }}
        }}
        
        // Event listeners
        window.addEventListener('load', () => {{
            handleResponsive();
            optimizeImages();
            optimizeChartsAndTables();
            setTimeout(checkAndAdjustLayout, 100);
        }});
        
        window.addEventListener('resize', () => {{
            handleResponsive();
            setTimeout(checkAndAdjustLayout, 200);
        }});
        
        // Observer để theo dõi thay đổi nội dung
        const observer = new MutationObserver(() => {{
            optimizeImages();
            optimizeChartsAndTables();
            setTimeout(checkAndAdjustLayout, 100);
        }});
        
        observer.observe(document.getElementById('slide-content-placeholder'), {{
            childList: true,
            subtree: true,
            characterData: true,
            attributes: true
        }});
        
        // Debug function để test layout
        window.testLayout = function() {{
            console.log('Container height:', document.getElementById('slide-container').clientHeight);
            console.log('Content height:', document.getElementById('slide-container').scrollHeight);
            console.log('Layout mode:', layoutMode);
            console.log('Is overflowing:', document.getElementById('slide-container').scrollHeight > document.getElementById('slide-container').clientHeight);
        }};
    </script>
</body>
</html>
"""

    def _get_main_css_template(self, style_instruction: dict) -> str:
        palette = style_instruction.get("color_palette", {})
        typography = style_instruction.get("typography", {})

        primary_color = palette.get("primary", "#4A90E2")
        secondary_color = palette.get("secondary", "#F5A623")
        background_color = palette.get("background", "#FFFFFF")
        text_color = palette.get("text_color", "#333333")
        header_color = palette.get("header_color", "#000000")

        header_font = typography.get("header_font", "Arial, sans-serif")
        body_font = typography.get("body_font", "Arial, sans-serif")

        return f"""
:root {{
    --primary-color: {primary_color};
    --secondary-color: {secondary_color};
    --background-color: {background_color};
    --text-color: {text_color};
    --header-color: {header_color};
    --header-font: '{header_font}';
    --body-font: '{body_font}';
}}

/* Reset và thiết lập cơ bản */
* {{
    box-sizing: border-box;
}}

body, html {{
    margin: 0;
    padding: 0;
    width: 100vw;
    height: 100vh;
    overflow: auto;
    font-family: var(--body-font);
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 20px;
}}

/* Container cố định với kích thước chuẩn */
.slide-container {{
    width: 1280px;
    min-height: 720px;
    max-width: 100vw;
    padding: 40px;
    display: flex;
    flex-direction: column;
    background-color: var(--background-color);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    border-radius: 12px;
    position: relative;
    overflow: visible;
}}

/* Typography cơ bản với kích thước cố định */
.slide-container h1 {{
    font-size: 36px;
    font-family: var(--header-font);
    color: var(--header-color);
    font-weight: bold;
    margin: 0 0 30px 0;
    line-height: 1.2;
    flex-shrink: 0;
}}

.slide-container h2 {{
    font-size: 28px;
    font-family: var(--header-font);
    color: var(--header-color);
    font-weight: bold;
    margin: 25px 0 15px 0;
    line-height: 1.3;
}}

.slide-container h3 {{
    font-size: 24px;
    font-family: var(--header-font);
    color: var(--header-color);
    font-weight: bold;
    margin: 20px 0 10px 0;
    line-height: 1.3;
}}

.slide-container p, .slide-container li, .slide-container span {{
    font-size: 18px;
    font-family: var(--body-font);
    color: var(--text-color);
    line-height: 1.6;
    margin: 12px 0;
}}

.slide-container ul, .slide-container ol {{
    padding-left: 30px;
    margin: 15px 0;
}}

.slide-container li {{
    margin: 8px 0;
}}

/* Nội dung slide với flexbox layout */
.slide-content {{
    flex: 1;
    overflow: visible;
    display: flex;
    flex-direction: column;
    gap: 20px;
    min-height: 0;
}}

/* Content container với flexbox */
.content-container {{
    flex: 1;
    display: flex;
    gap: 30px;
    align-items: stretch;
}}

/* Info box với kích thước được kiểm soát */
.info-box {{
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 20px;
    background: rgba(0, 0, 0, 0.02);
    border-radius: 8px;
    border-left: 4px solid var(--primary-color);
}}

/* Image container với kích thước cố định */
.image-container {{
    height: 250px;
    overflow: hidden;
    border-radius: 8px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    margin: 15px 0;
}}

/* Hình ảnh với kích thước được kiểm soát */
.slide-container img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 8px;
    display: block;
}}

/* Chart container với kích thước cố định */
.chart-container {{
    height: 250px;
    overflow: hidden;
    border-radius: 8px;
    margin: 15px 0;
    background: #f8f9fa;
    display: flex;
    align-items: center;
    justify-content: center;
}}

/* Links */
.slide-container a {{
    color: var(--primary-color);
    text-decoration: none;
}}

.slide-container a:hover {{
    text-decoration: underline;
}}

/* Two column layout với gap kiểm soát */
.two-column {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    height: auto;
    align-items: start;
}}

/* Three column layout */
.three-column {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    height: auto;
    align-items: start;
}}

/* Compact layout cho nội dung dài */
.compact-layout {{
    padding: 30px;
}}

.compact-layout h1 {{
    font-size: 32px;
    margin: 0 0 25px 0;
}}

.compact-layout h2 {{
    font-size: 24px;
    margin: 20px 0 12px 0;
}}

.compact-layout h3 {{
    font-size: 20px;
    margin: 15px 0 8px 0;
}}

.compact-layout p, 
.compact-layout li {{
    font-size: 16px;
    line-height: 1.5;
    margin: 10px 0;
}}

.compact-layout .image-container {{
    height: 200px;
}}

.compact-layout .chart-container {{
    height: 200px;
}}

/* Ultra-compact layout cho nội dung rất dài */
.ultra-compact-layout {{
    padding: 25px;
}}

.ultra-compact-layout h1 {{
    font-size: 28px;
    margin: 0 0 20px 0;
}}

.ultra-compact-layout h2 {{
    font-size: 22px;
    margin: 15px 0 10px 0;
}}

.ultra-compact-layout h3 {{
    font-size: 18px;
    margin: 12px 0 6px 0;
}}

.ultra-compact-layout p, 
.ultra-compact-layout li {{
    font-size: 14px;
    line-height: 1.4;
    margin: 8px 0;
}}

.ultra-compact-layout .image-container {{
    height: 180px;
}}

.ultra-compact-layout .chart-container {{
    height: 180px;
}}

/* Text overflow handling */
.text-ellipsis {{
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}}

.text-clamp-2 {{
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}

.text-clamp-3 {{
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}

/* Cảnh báo content overflow - ít invasive hơn */
.content-warning {{
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(255, 193, 7, 0.9);
    color: #212529;
    padding: 8px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    z-index: 1000;
    animation: fadeIn 0.3s ease-in-out;
    max-width: 200px;
}}

.content-warning.hidden {{
    display: none;
}}

@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(-10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

/* Layout adjustment indicators */
.layout-indicator {{
    position: absolute;
    bottom: 10px;
    left: 10px;
    background: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 4px 8px;
    border-radius: 10px;
    font-size: 10px;
    font-weight: 500;
    z-index: 999;
}}

/* Responsive breakpoints để giữ tỷ lệ */
@media (max-width: 1400px) {{
    .slide-container {{
        width: 90vw;
        min-height: 540px; /* Giữ tỷ lệ 16:9 */
        padding: 30px;
    }}
    
    .slide-container h1 {{ font-size: 32px; }}
    .slide-container h2 {{ font-size: 26px; }}
    .slide-container h3 {{ font-size: 22px; }}
    .slide-container p, .slide-container li {{ font-size: 16px; }}
}}

@media (max-width: 1024px) {{
    .slide-container {{
        width: 95vw;
        min-height: 480px;
        padding: 25px;
    }}
    
    .slide-container h1 {{ font-size: 28px; }}
    .slide-container h2 {{ font-size: 24px; }}
    .slide-container h3 {{ font-size: 20px; }}
    .slide-container p, .slide-container li {{ font-size: 14px; }}
    
    .two-column {{
        grid-template-columns: 1fr;
        gap: 20px;
    }}
    
    .three-column {{
        grid-template-columns: 1fr 1fr;
        gap: 15px;
    }}
    
    .image-container, .chart-container {{
        height: 200px;
    }}
}}
@media (max-width: 768px) {{
    .slide-container {{
        width: 100vw;
        min-height: 400px;
        padding: 20px;
        border-radius: 0;
    }}
    
    .slide-container h1 {{ font-size: 24px; }}
    .slide-container h2 {{ font-size: 20px; }}
    .slide-container h3 {{ font-size: 18px; }}
    .slide-container p, .slide-container li {{ font-size: 14px; }}
    
    .two-column, .three-column {{
        grid-template-columns: 1fr;
        gap: 15px;
    }}
    
    .image-container, .chart-container {{
        height: 150px;
    }}
}}

@media (max-width: 480px) {{
    .slide-container {{
        padding: 15px;
        min-height: 320px;
    }}
    
    .slide-container h1 {{ font-size: 20px; margin-bottom: 15px; }}
    .slide-container h2 {{ font-size: 18px; margin: 15px 0 10px 0; }}
    .slide-container h3 {{ font-size: 16px; margin: 12px 0 8px 0; }}
    .slide-container p, .slide-container li {{ font-size: 12px; margin: 8px 0; }}
    
    .image-container, .chart-container {{
        height: 120px;
    }}
    
    .info-box {{
        padding: 15px;
    }}
}}

/* Print styles */
@media print {{
    body {{
        padding: 0;
        background: none;
    }}
    
    .slide-container {{
        width: 100%;
        min-height: auto;
        padding: 2cm;
        box-shadow: none;
        border-radius: 0;
        page-break-inside: avoid;
    }}
    
    .slide-content {{
        overflow: visible;
    }}
    
    .content-warning, .layout-indicator {{
        display: none;
    }}
}}
    
    .overflow-warning {{
        display: none;
    }}
}}
"""

    async def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        try:
            project_dir = self.workspace_manager.get_path(tool_input["project_dir"])
            outline = tool_input["outline"]
            style_instruction = tool_input["style_instruction"]

            # 1. Create directory structure
            slides_dir = project_dir / "slides"
            assets_dir = project_dir / "assets"

            for d in [
                project_dir,
                slides_dir,
                assets_dir,
            ]:
                d.mkdir(parents=True, exist_ok=True)

            # 2. Store project configuration in the root
            config_data = {
                "main_title": tool_input["main_title"],
                "outline": outline,
                "style_instruction": style_instruction,
            }
            config_file_path = project_dir / "config.json"
            with open(config_file_path, "w") as f:
                json.dump(config_data, f, indent=4)

            # 3. Create main CSS file in the root
            css_content = self._get_main_css_template(style_instruction)
            css_file_path = project_dir / "style.css"
            with open(css_file_path, "w") as f:
                f.write(css_content)

            # 4. Create blank HTML files for each slide
            for slide_info in outline:
                slide_id = slide_info["id"]
                page_title = slide_info["page_title"]
                file_path = slides_dir / f"{slide_id}.html"
                html_content = self._get_html_template(page_title)
                with open(file_path, "w") as f:
                    f.write(html_content)

            return ToolImplOutput(
                f"Successfully initialized presentation project at '{tool_input['project_dir']}'.",
                "Project initialized successfully.",
                auxiliary_data={"success": True, "project_dir": str(project_dir)},
            )

        except Exception as e:
            return ToolImplOutput(
                f"Error initializing slide project: {str(e)}",
                "Error initializing project.",
                auxiliary_data={"success": False, "error": str(e)},
            )


class SlidePresentTool(LLMTool):
    name = "slide_present"
    description = "Aggregates individual slide HTML files into a final, interactive presentation file with navigation controls."

    input_schema = {
        "type": "object",
        "properties": {
            "project_dir": {
                "type": "string",
                "description": "Path to the slide project directory.",
            },
            "slide_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Ordered list of slide IDs to be presented.",
            },
        },
        "required": ["project_dir", "slide_ids"],
    }

    def __init__(self, workspace_manager: WorkspaceManager):
        super().__init__()
        self.workspace_manager = workspace_manager

    def _get_presentation_html_template(self, title: str, slide_iframes_html: str, slide_count: int) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        
        body, html {{
            margin: 0;
            padding: 0;
            height: 100vh;
            width: 100vw;
            overflow: auto;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        #slide-wrapper {{
            width: 100vw;
            height: 100vh;
            position: relative;
            overflow: auto;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        
        .slide-iframe {{
            display: none;
            width: 100%;
            height: 100%;
            border: none;
            background: transparent;
        }}
        
        .slide-iframe.active {{
            display: block;
        }}
        
        #navigation-controls {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 15px;
            background: rgba(0, 0, 0, 0.8);
            padding: 12px 20px;
            border-radius: 30px;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: opacity 0.3s ease, transform 0.3s ease;
        }}
        
        #navigation-controls:hover {{
            transform: translateX(-50%) translateY(-5px);
            background: rgba(0, 0, 0, 0.9);
        }}
        
        #navigation-controls button {{
            font-size: 14px;
            padding: 10px 16px;
            cursor: pointer;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            transition: all 0.3s ease;
            font-weight: 500;
            min-width: 80px;
        }}
        
        #navigation-controls button:hover:not(:disabled) {{
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }}
        
        #navigation-controls button:disabled {{
            cursor: not-allowed;
            opacity: 0.4;
            transform: none;
        }}
        
        #slide-counter {{
            font-size: 14px;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
            padding: 0 15px;
            min-width: 80px;
            text-align: center;
        }}
        
        /* Fullscreen và controls phụ */
        #top-controls {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1001;
            display: flex;
            gap: 10px;
        }}
        
        .control-btn {{
            background: rgba(0, 0, 0, 0.7);
            color: white;
            border: none;
            padding: 12px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 16px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            width: 45px;
            height: 45px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .control-btn:hover {{
            background: rgba(0, 0, 0, 0.9);
            transform: scale(1.1);
        }}
        
        /* Progress bar */
        #progress-bar {{
            position: fixed;
            bottom: 0;
            left: 0;
            height: 4px;
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 1000;
            box-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
        }}
        
        /* Loading animation */
        #loading-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            opacity: 1;
            transition: opacity 0.5s ease;
        }}
        
        #loading-overlay.hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        
        .loading-spinner {{
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-top: 3px solid white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        /* Slide transition effects */
        .slide-iframe {{
            transition: opacity 0.3s ease;
        }}
        
        .slide-iframe.entering {{
            opacity: 0;
            animation: slideIn 0.5s ease forwards;
        }}
        
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateX(50px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        /* Responsive controls */
        @media (max-width: 768px) {{
            #navigation-controls {{
                bottom: 20px;
                padding: 10px 15px;
                gap: 10px;
            }}
            
            #navigation-controls button {{
                padding: 8px 12px;
                font-size: 12px;
                min-width: 60px;
            }}
            
            #slide-counter {{
                font-size: 12px;
                min-width: 60px;
            }}
            
            #top-controls {{
                top: 15px;
                right: 15px;
            }}
            
            .control-btn {{
                width: 40px;
                height: 40px;
                font-size: 14px;
            }}
        }}
        
        /* Auto-hide controls */
        .controls-hidden #navigation-controls,
        .controls-hidden #top-controls {{
            opacity: 0;
            pointer-events: none;
        }}
        
        /* Slide overview mode */
        .overview-mode {{
            background: #1a1a1a;
        }}
        
        .overview-grid {{
            display: none;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            padding: 40px;
            max-height: 100vh;
            overflow-y: auto;
        }}
        
        .overview-grid.active {{
            display: grid;
        }}
        
        .overview-slide {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            cursor: pointer;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            position: relative;
            aspect-ratio: 16/9; /* Giữ tỷ lệ chuẩn */
        }}
        
        .overview-slide:hover {{
            transform: scale(1.05);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        }}
        
        .overview-slide iframe {{
            width: 100%;
            height: 100%;
            border: none;
            pointer-events: none;
            transform: scale(0.8); /* Scale down để xem overview */
            transform-origin: top left;
        }}
        
        .overview-slide-number {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div id="loading-overlay">
        <div class="loading-spinner"></div>
    </div>
    
    <div id="slide-wrapper">
        {slide_iframes_html}
        
        <div id="top-controls">
            <button class="control-btn" id="overview-btn" title="Slide Overview">⚏</button>
            <button class="control-btn" id="fullscreen-btn" title="Fullscreen">⛶</button>
        </div>
        
        <div id="progress-bar"></div>
        
        <div id="navigation-controls">
            <button id="prev-btn">← Previous</button>
            <span id="slide-counter">1 / {slide_count}</span>
            <button id="next-btn">Next →</button>
        </div>
    </div>
    
    <!-- Overview mode -->
    <div id="overview-grid" class="overview-grid">
        <!-- Overview slides will be generated here -->
    </div>

    <script>
        const slides = document.querySelectorAll('.slide-iframe');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const slideCounter = document.getElementById('slide-counter');
        const progressBar = document.getElementById('progress-bar');
        const loadingOverlay = document.getElementById('loading-overlay');
        const slideWrapper = document.getElementById('slide-wrapper');
        const overviewGrid = document.getElementById('overview-grid');
        const overviewBtn = document.getElementById('overview-btn');
        
        let currentSlide = 0;
        let isOverviewMode = false;
        let controlsVisible = true;
        let hideControlsTimeout;

        // Khởi tạo presentation
        function initPresentation() {{
            // Ẩn loading sau khi tải xong
            setTimeout(() => {{
                loadingOverlay.classList.add('hidden');
            }}, 1000);
            
            // Tạo overview grid
            createOverviewGrid();
            
            // Hiển thị slide đầu tiên
            showSlide(0);
            
            // Setup auto-hide controls
            setupAutoHideControls();
        }}
        
        function createOverviewGrid() {{
            slides.forEach((slide, index) => {{
                const overviewSlide = document.createElement('div');
                overviewSlide.className = 'overview-slide';
                overviewSlide.innerHTML = `
                    <iframe src="${{slide.src}}"></iframe>
                    <div class="overview-slide-number">${{index + 1}}</div>
                `;
                overviewSlide.addEventListener('click', () => {{
                    toggleOverview();
                    showSlide(index);
                }});
                overviewGrid.appendChild(overviewSlide);
            }});
        }}

        function showSlide(index) {{
            if (index < 0 || index >= slides.length) return;
            
            slides.forEach((slide, i) => {{
                if (i === index) {{
                    slide.classList.add('active', 'entering');
                    setTimeout(() => slide.classList.remove('entering'), 500);
                }} else {{
                    slide.classList.remove('active', 'entering');
                }}
            }});
            
            currentSlide = index;
            updateUI();
        }}
        
        function updateUI() {{
            slideCounter.textContent = `${{currentSlide + 1}} / ${{slides.length}}`;
            prevBtn.disabled = currentSlide === 0;
            nextBtn.disabled = currentSlide === slides.length - 1;
            
            // Update progress bar
            const progress = ((currentSlide + 1) / slides.length) * 100;
            progressBar.style.width = progress + '%';
        }}

        function nextSlide() {{
            if (currentSlide < slides.length - 1) {{
                showSlide(currentSlide + 1);
            }}
        }}
        
        function prevSlide() {{
            if (currentSlide > 0) {{
                showSlide(currentSlide - 1);
            }}
        }}
        
        function toggleOverview() {{
            isOverviewMode = !isOverviewMode;
            if (isOverviewMode) {{
                slideWrapper.style.display = 'none';
                overviewGrid.classList.add('active');
                document.body.classList.add('overview-mode');
            }} else {{
                slideWrapper.style.display = 'flex';
                overviewGrid.classList.remove('active');
                document.body.classList.remove('overview-mode');
            }}
        }}
        
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                document.exitFullscreen();
            }}
        }}
        
        function setupAutoHideControls() {{
            function showControls() {{
                document.body.classList.remove('controls-hidden');
                controlsVisible = true;
                clearTimeout(hideControlsTimeout);
                
                if (document.fullscreenElement) {{
                    hideControlsTimeout = setTimeout(() => {{
                        document.body.classList.add('controls-hidden');
                        controlsVisible = false;
                    }}, 3000);
                }}
            }}
            
            function hideControls() {{
                if (document.fullscreenElement) {{
                    document.body.classList.add('controls-hidden');
                    controlsVisible = false;
                }}
            }}
            
            document.addEventListener('mousemove', showControls);
            document.addEventListener('touchstart', showControls);
            document.addEventListener('keydown', showControls);
            
            // Hide controls initially in fullscreen
            document.addEventListener('fullscreenchange', () => {{
                if (document.fullscreenElement) {{
                    hideControlsTimeout = setTimeout(hideControls, 3000);
                }} else {{
                    showControls();
                    clearTimeout(hideControlsTimeout);
                }}
            }});
        }}

        // Event listeners
        nextBtn.addEventListener('click', nextSlide);
        prevBtn.addEventListener('click', prevSlide);
        overviewBtn.addEventListener('click', toggleOverview);
        document.getElementById('fullscreen-btn').addEventListener('click', toggleFullscreen);
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (isOverviewMode) {{
                if (e.key === 'Escape') {{
                    toggleOverview();
                }}
                return;
            }}
            
            switch(e.key) {{
                case 'ArrowRight':
                case ' ':
                case 'PageDown':
                    e.preventDefault();
                    nextSlide();
                    break;
                case 'ArrowLeft':
                case 'PageUp':
                    e.preventDefault();
                    prevSlide();
                    break;
                case 'Escape':
                    if (document.fullscreenElement) {{
                        document.exitFullscreen();
                    }}
                    break;
                case 'f':
                case 'F11':
                    e.preventDefault();
                    toggleFullscreen();
                    break;
                case 'o':
                case 'O':
                    e.preventDefault();
                    toggleOverview();
                    break;
                case 'Home':
                    e.preventDefault();
                    showSlide(0);
                    break;
                case 'End':
                    e.preventDefault();
                    showSlide(slides.length - 1);
                    break;
            }}
        }});
        
        // Touch/swipe support
        let touchStartX = 0;
        let touchEndX = 0;
        let touchStartY = 0;
        let touchEndY = 0;
        
        document.addEventListener('touchstart', e => {{
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
        }});
        
        document.addEventListener('touchend', e => {{
            touchEndX = e.changedTouches[0].screenX;
            touchEndY = e.changedTouches[0].screenY;
            handleSwipe();
        }});
        
        function handleSwipe() {{
            const swipeThreshold = 50;
            const diffX = touchStartX - touchEndX;
            const diffY = Math.abs(touchStartY - touchEndY);
            
            // Only process horizontal swipes
            if (Math.abs(diffX) > swipeThreshold && diffY < swipeThreshold) {{
                if (diffX > 0) {{
                    nextSlide(); // Swipe left - next slide
                }} else {{
                    prevSlide(); // Swipe right - previous slide
                }}
            }}
        }}

        // Initialize presentation when page loads
        window.addEventListener('load', initPresentation);
    </script>
</body>
</html>
"""

    async def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        try:
            project_dir = self.workspace_manager.get_path(tool_input["project_dir"])
            slide_ids = tool_input["slide_ids"]
            slides_dir = project_dir / "slides"
            
            # 1. Read project config from the root
            config_file_path = project_dir / "config.json"
            if not config_file_path.exists():
                return ToolImplOutput(f"Configuration file 'config.json' not found at '{config_file_path}'. Please run slide_initialize first.", "Configuration not found.", auxiliary_data={"success": False})

            with open(config_file_path, 'r') as f:
                config_data = json.load(f)
            main_title = config_data.get("main_title", "Presentation")

            # 2. Verify all slide files exist
            for slide_id in slide_ids:
                slide_path = slides_dir / f"{slide_id}.html"
                if not slide_path.exists():
                    return ToolImplOutput(
                        f"Slide file '{slide_id}.html' not found in '{slides_dir}'.",
                        "Missing slide file.",
                        auxiliary_data={"success": False, "missing_file": str(slide_path)},
                    )
            
            # 3. Create the main presentation HTML
            iframe_html_parts = []
            for i, slide_id in enumerate(slide_ids):
                active_class = "active" if i == 0 else ""
                iframe_html_parts.append(f'<iframe id="slide-{slide_id}" class="slide-iframe {active_class}" src="slides/{slide_id}.html"></iframe>')
            
            presentation_content = self._get_presentation_html_template(
                title=main_title,
                slide_iframes_html="\\n".join(iframe_html_parts),
                slide_count=len(slide_ids)
            )

            presentation_file_path = project_dir / "presentation.html"
            with open(presentation_file_path, 'w') as f:
                f.write(presentation_content)
            
            message = f"Successfully generated presentation file at '{presentation_file_path}'. You can now open this file to view the presentation."

            return ToolImplOutput(
                message,
                message,
                auxiliary_data={"success": True, "presentation_path": str(presentation_file_path)},
            )
        except Exception as e:
            return ToolImplOutput(
                f"Error presenting slides: {str(e)}",
                "Error during presentation.",
                auxiliary_data={"success": False, "error": str(e)},
            )
