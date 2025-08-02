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
    <div class="slide-frame" id="slide-frame">
        <div class="slide-container" id="slide-container">
            <h1 id="slide-title">{title}</h1>
            <div id="slide-content" class="slide-content">
                <!-- Content for this slide will be added here -->
            </div>
            
            <!-- Split slide navigation -->
            <div class="split-nav hidden" id="split-nav">
                <button class="split-prev" id="split-prev">
                    <i class="fas fa-chevron-left"></i>
                </button>
                <div class="split-indicator" id="split-indicator">
                    Part 1 of 1
                </div>
                <button class="split-next" id="split-next">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        </div>
    </div>
    
    <script>
        // Split content management
        let currentPart = 0;
        let totalParts = 1;
        const contentParts = [];
        
        // Initialize the slide
        function initSlide() {{
            const contentElement = document.getElementById('slide-content');
            contentParts[0] = contentElement.innerHTML;
            checkContentLength();
        }}
        
        // Check if content needs splitting
        function checkContentLength() {{
            const container = document.getElementById('slide-container');
            const content = document.getElementById('slide-content');
            const frame = document.getElementById('slide-frame');
            const nav = document.getElementById('split-nav');
            const indicator = document.getElementById('split-indicator');
            
            // Reset scroll position
            frame.scrollTop = 0;
            
            // Check if content overflows
            const isOverflowing = content.scrollHeight > frame.clientHeight;
            
            if (isOverflowing) {{
                // Split the content
                splitContent();
            }} else {{
                // Hide navigation if not needed
                nav.classList.add('hidden');
                totalParts = 1;
                currentPart = 0;
                indicator.textContent = `Part ${{currentPart+1}} of ${{totalParts}}`;
            }}
        }}
        
        // Split content into multiple parts
        function splitContent() {{
            const content = document.getElementById('slide-content');
            const originalContent = content.innerHTML;
            const frameHeight = document.getElementById('slide-frame').clientHeight;
            const titleHeight = document.getElementById('slide-title').offsetHeight;
            const navHeight = document.getElementById('split-nav').offsetHeight;
            
            // Calculate available space for content
            const availableHeight = frameHeight - titleHeight - navHeight - 40; // 40px padding
            
            // Reset parts
            contentParts.length = 0;
            currentPart = 0;
            
            // Create a temporary element for measuring
            const tempDiv = document.createElement('div');
            tempDiv.style.visibility = 'hidden';
            tempDiv.style.position = 'absolute';
            tempDiv.style.width = '100%';
            document.body.appendChild(tempDiv);
            
            // Clone the content for splitting
            tempDiv.innerHTML = originalContent;
            
            // Split logic
            let currentPartContent = '';
            let currentHeight = 0;
            let partCount = 1;
            
            // Process child nodes
            const nodes = Array.from(tempDiv.childNodes);
            for (let i = 0; i < nodes.length; i++) {{
                const node = nodes[i];
                const nodeClone = node.cloneNode(true);
                
                // Measure node height
                tempDiv.innerHTML = '';
                tempDiv.appendChild(nodeClone);
                const nodeHeight = tempDiv.offsetHeight;
                
                // Check if node fits or needs to be split
                if (currentHeight + nodeHeight <= availableHeight) {{
                    currentPartContent += node.outerHTML || node.textContent;
                    currentHeight += nodeHeight;
                }} else {{
                    // Save current part
                    if (currentPartContent) {{
                        contentParts.push(currentPartContent);
                        partCount++;
                    }}
                    
                    // Start new part
                    currentPartContent = node.outerHTML || node.textContent;
                    currentHeight = nodeHeight;
                }}
            }}
            
            // Add last part
            if (currentPartContent) {{
                contentParts.push(currentPartContent);
            }}
            
            // Clean up
            document.body.removeChild(tempDiv);
            
            // Update navigation
            totalParts = contentParts.length;
            showPart(currentPart);
            
            // Show navigation if needed
            const nav = document.getElementById('split-nav');
            if (totalParts > 1) {{
                nav.classList.remove('hidden');
            }}
        }}
        
        // Show specific part
        function showPart(partIndex) {{
            if (partIndex >= 0 && partIndex < totalParts) {{
                currentPart = partIndex;
                document.getElementById('slide-content').innerHTML = contentParts[partIndex];
                document.getElementById('split-indicator').textContent = `Part ${{currentPart+1}} of ${{totalParts}}`;
                
                // Update button states
                document.getElementById('split-prev').disabled = (currentPart === 0);
                document.getElementById('split-next').disabled = (currentPart === totalParts - 1);
            }}
        }}
        
        // Event listeners
        document.getElementById('split-prev').addEventListener('click', () => {{
            if (currentPart > 0) {{
                showPart(currentPart - 1);
            }}
        }});
        
        document.getElementById('split-next').addEventListener('click', () => {{
            if (currentPart < totalParts - 1) {{
                showPart(currentPart + 1);
            }}
        }});
        
        // Initialize on load
        window.addEventListener('load', () => {{
            initSlide();
            
            // Re-check on resize
            window.addEventListener('resize', () => {{
                setTimeout(checkContentLength, 100);
            }});
        }});
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
    margin: 0;
    padding: 0;
}}

body, html {{
    width: 100%;
    height: 100%;
    font-family: var(--body-font);
    background: #f0f2f5;
    overflow: hidden;
}}

/* Slide frame - khung chứa slide ở giữa màn hình */
.slide-frame {{
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100vw;
    height: 100vh;
    padding: 20px;
    overflow: hidden;
    background: #f0f2f5;
}}

/* Slide container - khung nội dung chính */
.slide-container {{
    width: 100%;
    max-width: 1200px;
    height: 100%;
    max-height: 90vh;
    padding: 40px;
    display: flex;
    flex-direction: column;
    background-color: var(--background-color);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
    border-radius: 12px;
    position: relative;
    overflow: hidden;
}}

.slide-content {{
    flex: 1;
    overflow-y: auto;
    padding: 10px 5px;
    scrollbar-width: thin;
    scrollbar-color: var(--primary-color) rgba(0, 0, 0, 0.1);
}}

.slide-content::-webkit-scrollbar {{
    width: 6px;
}}

.slide-content::-webkit-scrollbar-track {{
    background: rgba(0, 0, 0, 0.05);
}}

.slide-content::-webkit-scrollbar-thumb {{
    background-color: var(--primary-color);
    border-radius: 3px;
}}

/* Tiêu đề slide */
#slide-title {{
    font-size: 36px;
    font-family: var(--header-font);
    color: var(--header-color);
    font-weight: bold;
    margin: 0 0 30px 0;
    line-height: 1.2;
    flex-shrink: 0;
    padding-bottom: 15px;
    border-bottom: 2px solid var(--primary-color);
}}

/* Thanh điều hướng chia slide */
.split-nav {{
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 20px;
    padding: 10px;
    background: rgba(0, 0, 0, 0.03);
    border-radius: 8px;
    border-top: 1px solid rgba(0, 0, 0, 0.1);
}}

.split-prev, .split-next {{
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: 50%;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
}}

.split-prev:hover, .split-next:hover {{
    background: {primary_color}CC;
    transform: scale(1.05);
}}

.split-prev:disabled, .split-next:disabled {{
    background: #cccccc;
    cursor: not-allowed;
    transform: none;
}}

.split-indicator {{
    margin: 0 15px;
    font-size: 14px;
    color: var(--text-color);
    font-weight: 500;
}}

/* Styling cho nội dung */
.slide-content h2 {{
    font-size: 28px;
    font-family: var(--header-font);
    color: var(--header-color);
    margin: 20px 0 15px 0;
}}

.slide-content h3 {{
    font-size: 24px;
    font-family: var(--header-font);
    color: var(--header-color);
    margin: 15px 0 10px 0;
}}

.slide-content p {{
    font-size: 18px;
    line-height: 1.6;
    margin-bottom: 15px;
    color: var(--text-color);
}}

.slide-content ul, .slide-content ol {{
    padding-left: 30px;
    margin-bottom: 20px;
}}

.slide-content li {{
    margin-bottom: 8px;
    line-height: 1.6;
}}

.slide-content img {{
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 15px 0;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}}

.slide-content table {{
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}}

.slide-content th {{
    background-color: var(--primary-color);
    color: white;
    padding: 12px;
    text-align: left;
}}

.slide-content td {{
    padding: 10px;
    border-bottom: 1px solid #ddd;
}}

.slide-content tr:nth-child(even) {{
    background-color: #f9f9f9;
}}

.slide-content blockquote {{
    border-left: 4px solid var(--primary-color);
    padding: 10px 20px;
    margin: 20px 0;
    background-color: #f9f9f9;
    font-style: italic;
}}

.slide-content code {{
    font-family: monospace;
    background-color: #f5f5f5;
    padding: 2px 6px;
    border-radius: 4px;
}}

.slide-content pre {{
    background-color: #2d2d2d;
    color: #f8f8f2;
    padding: 15px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 20px 0;
}}

.slide-content pre code {{
    background: none;
    padding: 0;
}}

/* Layouts */
.two-column {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 30px;
    margin: 20px 0;
}}

.three-column {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    margin: 20px 0;
}}

.image-container {{
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    margin: 15px 0;
}}

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

.info-box {{
    padding: 20px;
    background: rgba(0, 0, 0, 0.02);
    border-radius: 8px;
    border-left: 4px solid var(--primary-color);
    margin: 15px 0;
}}

/* Responsive design */
@media (max-width: 1200px) {{
    .slide-container {{
        max-width: 95vw;
        max-height: 95vh;
        padding: 30px;
    }}
    
    #slide-title {{
        font-size: 32px;
    }}
}}

@media (max-width: 992px) {{
    .two-column {{
        grid-template-columns: 1fr;
    }}
    
    .three-column {{
        grid-template-columns: 1fr 1fr;
    }}
}}

@media (max-width: 768px) {{
    .slide-frame {{
        padding: 10px;
    }}
    
    .slide-container {{
        padding: 25px;
        max-height: 100vh;
        border-radius: 0;
    }}
    
    #slide-title {{
        font-size: 28px;
        margin-bottom: 20px;
    }}
    
    .slide-content h2 {{
        font-size: 24px;
    }}
    
    .slide-content h3 {{
        font-size: 20px;
    }}
    
    .slide-content p {{
        font-size: 16px;
    }}
    
    .three-column {{
        grid-template-columns: 1fr;
    }}
}}

@media (max-width: 480px) {{
    .slide-container {{
        padding: 20px;
    }}
    
    #slide-title {{
        font-size: 24px;
    }}
    
    .slide-content h2 {{
        font-size: 20px;
    }}
    
    .slide-content p {{
        font-size: 14px;
    }}
    
    .split-nav {{
        padding: 8px;
    }}
    
    .split-indicator {{
        font-size: 12px;
    }}
}}

/* Hiệu ứng chuyển phần */
@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}

.slide-content {{
    animation: fadeIn 0.3s ease-out;
}}

/* Trạng thái ẩn cho thanh điều hướng chia slide */
.hidden {{
    display: none !important;
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
