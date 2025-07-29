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
    <div class="slide-container">
        <h1>{title}</h1>
        <div id="slide-content-placeholder">
            <!-- Content for this slide will be added here -->
        </div>
    </div>
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

body, html {{
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #f0f0f0;
}}

.slide-container {{
    max-width: 1280px;
    max-height: 720px;
    height: auto;
    background-color: var(--background-color);
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
    padding: 3rem 4rem;
    display: flex;
    flex-direction: column;
    text-align: left;
    box-sizing: border-box;
}}

h1, h2, h3 {{
    font-size: 36px;
    font-family: var(--header-font);
    color: var(--header-color);
    font-weight: bold;
}}

.slide-container p, .slide-container li, .slide-container span {{
    font-size: 24px;
    font-family: var(--body-font);
    color: var(--text-color);
    line-height: 1.6;
}}

.slide-container img {{
    max-width: 100%;
    max-height: 100%;
    object-fit: cover;
    border-radius: 15px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}}

.slide-container a {{
    color: var(--primary-color);
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
        body, html {{
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
            font-family: sans-serif;
            background-color: #f0f0f0;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        #slide-wrapper {{
            width: 1280px;
            height: 720px;
            background: #000;
            box-shadow: 0 0 30px rgba(0,0,0,0.5);
            position: relative;
            overflow: hidden;
        }}
        .slide-iframe {{
            display: none;
            width: 100%;
            height: 100%;
            border: none;
        }}
        .slide-iframe.active {{
            display: block;
        }}
        #navigation-controls {{
            position: absolute;
            bottom: 20px;
            right: 30px;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        #navigation-controls button {{
            font-size: 18px;
            padding: 5px 10px;
            cursor: pointer;
            background-color: rgba(0, 0, 0, 0.4);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.5);
            border-radius: 5px;
            transition: background-color 0.3s;
        }}
        #navigation-controls button:hover:not(:disabled) {{
            background-color: rgba(0, 0, 0, 0.7);
        }}
        #navigation-controls button:disabled {{
            cursor: not-allowed;
            opacity: 0.3;
        }}
        #slide-counter {{
            font-size: 16px;
            color: white;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.7);
        }}
    </style>
</head>
<body>
    <div id="slide-wrapper">
        {slide_iframes_html}
        <div id="navigation-controls">
            <button id="prev-btn">Previous</button>
            <span id="slide-counter">1 / {slide_count}</span>
            <button id="next-btn">Next</button>
        </div>
    </div>

    <script>
        const slides = document.querySelectorAll('.slide-iframe');
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const slideCounter = document.getElementById('slide-counter');
        let currentSlide = 0;

        function showSlide(index) {{
            slides.forEach((slide, i) => {{
                slide.classList.toggle('active', i === index);
            }});
            currentSlide = index;
            slideCounter.textContent = (currentSlide + 1) + ' / ' + slides.length;
            prevBtn.disabled = currentSlide === 0;
            nextBtn.disabled = currentSlide === slides.length - 1;
        }}

        nextBtn.addEventListener('click', () => {{
            if (currentSlide < slides.length - 1) {{
                showSlide(currentSlide + 1);
            }}
        }});

        prevBtn.addEventListener('click', () => {{
            if (currentSlide > 0) {{
                showSlide(currentSlide - 1);
            }}
        }});
        
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowRight') {{
                nextBtn.click();
            }} else if (e.key === 'ArrowLeft') {{
                prevBtn.click();
            }}
        }});

        // Show the first slide initially
        showSlide(0);
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
                iframe_html_parts.append(f'<iframe id="slide-{slide_id}" class="slide-iframe {active_class}" src="slides/{slide_id}.html" scrolling="no"></iframe>')
            
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
