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
                "required": ["theme", "color_palette", "typography"],
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
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="{css_path}">
    <!-- Additional JS/CSS libraries can be added here -->
</head>
<body>
    <div class="slide-container">
        <!-- Slide content will be filled here by SlideContentTool -->
    </div>
</body>
</html>"""

    def _get_main_css_content(self, style_instruction: dict) -> str:
        # Generate main CSS content based on style_instruction
        # This is where you convert style_instruction to actual CSS
        # Simple example:
        primary_color = style_instruction['color_palette']['primary']
        background_color = style_instruction['color_palette']['background']
        text_color = style_instruction['color_palette']['text_color']
        header_color = style_instruction['color_palette']['header_color']
        header_font = style_instruction['typography']['header_font']
        body_font = style_instruction['typography']['body_font']
        
        # Get secondary color if available
        secondary_color = style_instruction['color_palette'].get('secondary', primary_color)

        return f"""/* main.css - Generated Slide Styles */
:root {{
    --primary-color: {primary_color};
    --secondary-color: {secondary_color};
    --background-color: {background_color};
    --text-color: {text_color};
    --header-color: {header_color};
    --header-font: '{header_font}', sans-serif;
    --body-font: '{body_font}', sans-serif;
}}

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    padding: 0;
    font-family: var(--body-font);
    overflow: hidden;
}}

.slide-container {{
    width: 1280px;
    min-height: 720px;
    margin: 0 auto;
    background: var(--background-color);
    color: var(--text-color);
    font-family: var(--body-font);
    padding: 40px;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    position: relative;
}}

.slide-title {{
    font-size: 36px;
    font-weight: bold;
    color: var(--header-color);
    font-family: var(--header-font);
    margin-bottom: 30px;
    text-align: center;
}}

/* Layout utilities */
.content-container {{
    display: flex;
    gap: 30px;
    flex: 1;
}}

.column {{
    flex: 1;
    display: flex;
    flex-direction: column;
}}

.text-content {{
    flex: 1;
}}

.media-content {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
    font-family: var(--header-font);
    color: var(--header-color);
}}

p {{
    line-height: 1.6;
    margin-bottom: 16px;
}}

/* Lists */
ul, ol {{
    line-height: 1.6;
    margin-bottom: 16px;
}}

li {{
    margin-bottom: 8px;
}}

/* Images */
img {{
    max-width: 100%;
    height: auto;
    border-radius: 8px;
}}

/* Buttons and interactive elements */
.btn {{
    background: var(--primary-color);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
}}

.btn:hover {{
    background: var(--secondary-color);
    transform: translateY(-2px);
}}

/* Cards and boxes */
.info-box {{
    background: rgba(255, 255, 255, 0.9);
    border-left: 4px solid var(--primary-color);
    padding: 20px;
    margin: 20px 0;
    border-radius: 4px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}}

.highlight-box {{
    background: var(--primary-color);
    color: white;
    padding: 20px;
    border-radius: 8px;
    margin: 20px 0;
}}

/* Animations */
@keyframes fadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(30px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

.fade-in-up {{
    animation: fadeInUp 0.6s ease-out;
}}

/* Responsive design */
@media (max-width: 1280px) {{
    .slide-container {{
        width: 100vw;
        height: 100vh;
        padding: 30px;
    }}
}}
"""

    def execute(self, main_title: str, project_dir: str, outline: list, style_instruction: dict) -> ToolImplOutput:
        project_path = Path(project_dir)
        slides_path = project_path / "slides"
        assets_path = project_path / "assets"
        css_path = project_path / "css"

        # 1. Create directory structure
        os.makedirs(slides_path, exist_ok=True)
        os.makedirs(assets_path, exist_ok=True)
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
        .nav-button {{
            background: #4B72B0;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        .nav-button:disabled {{
            background: #cccccc;
            cursor: not-allowed;
        }}
        .slide-indicator {{
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
        <button id="prevBtn" class="nav-button">Previous</button>
        <span id="slideIndicator" class="slide-indicator">1 / {len(slide_ids)}</span>
        <button id="nextBtn" class="nav-button">Next</button>
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


class SlideContentTool(LLMTool):
    name = "slide_content"
    description = (
        "Fills content into a specific slide HTML file based on a chosen template type. "
        "This tool takes the raw content and integrates it into the pre-defined slide structure."
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
                "description": "The unique identifier of the slide to update (e.g., 'intro').",
            },
            "template_type": {
                "type": "string",
                "description": "The type of content template to use (e.g., 'basic_content', 'chart_data', 'front_page').",
                "enum": ["front_page", "basic_content", "comparison", "chart_data", "thank_you", "custom"], # Add templates provided
            },
            "content_data": {
                "type": "object",
                "description": "A dictionary containing data to populate the template (e.g., text, image paths, chart data).",
            },
        },
        "required": ["project_dir", "slide_id", "template_type", "content_data"],
    }

    def __init__(self, workspace_manager: WorkspaceManager = None):
        self.workspace_manager = workspace_manager

    async def run_impl(self, tool_input: dict[str, Any], message_history: Optional[MessageHistory] = None) -> ToolImplOutput:
        return self.execute(
            tool_input["project_dir"],
            tool_input["slide_id"], 
            tool_input["template_type"],
            tool_input["content_data"]
        )

    def _get_front_page_template(self) -> str:
        return """<div class="slide-container front-page">
    <div class="content-overlay">
        <h1 class="main-title">{main_title}</h1>
        <h2 class="subtitle">{subtitle}</h2>
        <p class="author-date">{author} - {date}</p>
    </div>
</div>

<style>
.front-page {{
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}}

.content-overlay {{
    background: rgba(255, 255, 255, 0.9);
    padding: 60px;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}}

.main-title {{
    font-size: 48px;
    margin-bottom: 20px;
    color: var(--header-color);
}}

.subtitle {{
    font-size: 24px;
    margin-bottom: 30px;
    color: var(--text-color);
    font-weight: normal;
}}

.author-date {{
    font-size: 18px;
    color: var(--text-color);
    opacity: 0.8;
}}
</style>"""

    def _get_basic_content_template(self) -> str:
        return """<div class="slide-container basic-content">
    <h1 class="slide-title">{title}</h1>
    <div class="content-area">
        <div class="text-content">
            {content}
        </div>
        <div class="media-content">
            {media}
        </div>
    </div>
</div>

<style>
.basic-content {{
    padding: 40px;
}}

.content-area {{
    display: flex;
    gap: 40px;
    height: calc(100% - 100px);
}}

.text-content {{
    flex: 1;
    display: flex;
    flex-direction: column;
}}

.media-content {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
}}

.text-content p {{
    font-size: 18px;
    line-height: 1.6;
    margin-bottom: 20px;
}}

.text-content ul, .text-content ol {{
    font-size: 18px;
    line-height: 1.8;
}}

.media-content img {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 10px;
}}
</style>"""

    def _get_comparison_template(self) -> str:
        return """<div class="slide-container comparison">
    <h1 class="slide-title">{title}</h1>
    <div class="comparison-grid">
        <div class="comparison-item">
            <h3>{left_title}</h3>
            <div class="comparison-content">
                {left_content}
            </div>
        </div>
        <div class="vs-divider">VS</div>
        <div class="comparison-item">
            <h3>{right_title}</h3>
            <div class="comparison-content">
                {right_content}
            </div>
        </div>
    </div>
</div>

<style>
.comparison {{
    padding: 40px;
}}

.comparison-grid {{
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 30px;
    height: calc(100% - 100px);
    align-items: center;
}}

.comparison-item {{
    background: var(--background-color);
    border: 2px solid var(--primary-color);
    border-radius: 15px;
    padding: 30px;
    height: 100%;
    display: flex;
    flex-direction: column;
}}

.comparison-item h3 {{
    color: var(--header-color);
    font-size: 24px;
    margin-bottom: 20px;
    text-align: center;
}}

.comparison-content {{
    flex: 1;
    font-size: 16px;
    line-height: 1.6;
}}

.vs-divider {{
    background: var(--primary-color);
    color: white;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 18px;
}}
</style>"""

    def _get_chart_data_template(self) -> str:
        return """<div class="slide-container chart-data">
    <h1 class="slide-title">{title}</h1>
    <div class="chart-container">
        <div class="chart-area">
            {chart_html}
        </div>
        <div class="chart-description">
            {description}
        </div>
    </div>
</div>

<style>
.chart-data {{
    padding: 40px;
}}

.chart-container {{
    display: flex;
    gap: 40px;
    height: calc(100% - 100px);
}}

.chart-area {{
    flex: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    background: white;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}}

.chart-description {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}}

.chart-description h3 {{
    color: var(--header-color);
    font-size: 22px;
    margin-bottom: 20px;
}}

.chart-description p {{
    font-size: 16px;
    line-height: 1.6;
    margin-bottom: 15px;
}}

.chart-description ul {{
    font-size: 16px;
    line-height: 1.6;
}}
</style>"""

    def _get_thank_you_template(self) -> str:
        return """<div class="slide-container thank-you">
    <div class="thank-you-content">
        <h1 class="thank-you-title">{title}</h1>
        <p class="thank-you-message">{message}</p>
        <div class="contact-info">
            {contact_info}
        </div>
    </div>
</div>

<style>
.thank-you {{
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}}

.thank-you-content {{
    background: rgba(255, 255, 255, 0.9);
    padding: 60px;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}}

.thank-you-title {{
    font-size: 48px;
    color: var(--header-color);
    margin-bottom: 30px;
}}

.thank-you-message {{
    font-size: 24px;
    color: var(--text-color);
    margin-bottom: 40px;
}}

.contact-info {{
    font-size: 18px;
    color: var(--text-color);
    opacity: 0.8;
}}

.contact-info a {{
    color: var(--primary-color);
    text-decoration: none;
}}
</style>"""

    def execute(self, project_dir: str, slide_id: str, template_type: str, content_data: dict) -> ToolImplOutput:
        project_path = Path(project_dir)
        config_path = project_path / "config.json"
        slides_path = project_path / "slides"
        slide_file_path = slides_path / f"{slide_id}.html"

        # Check if project exists
        if not config_path.exists():
            return ToolImplOutput(
                tool_output=f"Error: Configuration file not found at '{config_path}'. Please initialize project first.",
                tool_result_message="Configuration file not found"
            )

        # Check if slide file exists
        if not slide_file_path.exists():
            return ToolImplOutput(
                tool_output=f"Error: Slide file '{slide_id}.html' not found. Please check slide_id.",
                tool_result_message="Slide file not found"
            )

        # Read configuration to get style information
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # MANDATORY: Truncate content to fit slide dimensions
        truncated_content_data = self._truncate_content_for_template(template_type, content_data)

        # MANDATORY: Validate that essential content exists
        if not truncated_content_data:
            return ToolImplOutput(
                tool_output=f"Error: No content data provided for slide '{slide_id}'.",
                tool_result_message="No content data provided"
            )

        # MANDATORY: Ensure content is not empty after truncation
        required_fields = self._get_required_fields_for_template(template_type)
        for field in required_fields:
            if field not in truncated_content_data or not str(truncated_content_data[field]).strip():
                return ToolImplOutput(
                    tool_output=f"Error: Required field '{field}' is missing or empty for template '{template_type}'.",
                    tool_result_message=f"Required field '{field}' is missing or empty"
                )

        # Create CSS variables from style instruction
        style_vars = self._create_css_variables(config.get("style_instruction", {}))

        # Get template content
        if template_type == "front_page":
            template_content = self._get_front_page_template()
        elif template_type == "basic_content":
            template_content = self._get_basic_content_template()
        elif template_type == "comparison":
            template_content = self._get_comparison_template()
        elif template_type == "chart_data":
            template_content = self._get_chart_data_template()
        elif template_type == "thank_you":
            template_content = self._get_thank_you_template()
        elif template_type == "custom":
            template_content = content_data.get("custom_html", "<!-- Custom content -->")
        else:
            return ToolImplOutput(
                tool_output=f"Error: Template type '{template_type}' is not supported.",
                tool_result_message=f"Template type '{template_type}' is not supported"
            )

        # Fill data into template
        try:
            filled_content = template_content.format(**truncated_content_data)
        except KeyError as e:
            return ToolImplOutput(
                tool_output=f"Error: Missing required data for template: {e}",
                tool_result_message=f"Missing required data for template: {e}"
            )

        # Read current HTML file
        with open(slide_file_path, "r", encoding="utf-8") as f:
            current_html = f.read()

        # Replace content in slide container
        if "<!-- Slide content will be filled here by SlideContentTool -->" in current_html:
            new_html = current_html.replace(
                "<!-- Slide content will be filled here by SlideContentTool -->",
                filled_content
            )
        else:
            # Find and replace content in slide-container
            import re
            pattern = r'<div class="slide-container"[^>]*>.*?</div>'
            if re.search(pattern, current_html, re.DOTALL):
                new_html = re.sub(pattern, filled_content, current_html, flags=re.DOTALL)
            else:
                # If not found, add to body
                new_html = current_html.replace(
                    '<div class="slide-container">',
                    filled_content
                )

        # Add CSS variables to beginning of file
        if style_vars and "<style>" not in new_html:
            head_close_pos = new_html.find("</head>")
            if head_close_pos != -1:
                new_html = (
                    new_html[:head_close_pos] +
                    f"<style>\n:root {{\n{style_vars}\n}}\n</style>\n" +
                    new_html[head_close_pos:]
                )

        # Write new file
        with open(slide_file_path, "w", encoding="utf-8") as f:
            f.write(new_html)

        return ToolImplOutput(
            tool_output=f"✓ CONTENT FILLED: Updated slide '{slide_id}' with template '{template_type}'. Content successfully truncated and fitted to slide dimensions (1280x720px).",
            tool_result_message=f"Successfully updated slide {slide_id} with content"
        )

    def _create_css_variables(self, style_instruction: dict) -> str:
        """Create CSS variables from style instruction"""
        if not style_instruction:
            return ""
        
        css_vars = []
        
        # Color palette
        color_palette = style_instruction.get("color_palette", {})
        if color_palette:
            for key, value in color_palette.items():
                css_var_name = key.replace("_", "-")
                css_vars.append(f"  --{css_var_name}: {value};")
        
        # Typography
        typography = style_instruction.get("typography", {})
        if typography:
            for key, value in typography.items():
                css_var_name = key.replace("_", "-")
                css_vars.append(f"  --{css_var_name}: '{value}', sans-serif;")
        
        return "\n".join(css_vars)

    def _truncate_content_for_template(self, template_type: str, content_data: dict) -> dict:
        """Intelligently truncate content to fit slide dimensions"""
        truncated_data = content_data.copy()
        
        if template_type == "front_page":
            # Front page content limits
            if "main_title" in truncated_data:
                truncated_data["main_title"] = self._truncate_text(truncated_data["main_title"], 60)
            if "subtitle" in truncated_data:
                truncated_data["subtitle"] = self._truncate_text(truncated_data["subtitle"], 100)
                
        elif template_type == "basic_content":
            # Basic content limits
            if "title" in truncated_data:
                truncated_data["title"] = self._truncate_text(truncated_data["title"], 60)
            if "content" in truncated_data:
                truncated_data["content"] = self._truncate_text(truncated_data["content"], 500, preserve_paragraphs=True)
                
        elif template_type == "comparison":
            # Comparison content limits
            if "title" in truncated_data:
                truncated_data["title"] = self._truncate_text(truncated_data["title"], 60)
            if "left_content" in truncated_data:
                truncated_data["left_content"] = self._truncate_text(truncated_data["left_content"], 250)
            if "right_content" in truncated_data:
                truncated_data["right_content"] = self._truncate_text(truncated_data["right_content"], 250)
                
        elif template_type == "chart_data":
            # Chart data content limits
            if "title" in truncated_data:
                truncated_data["title"] = self._truncate_text(truncated_data["title"], 60)
            if "description" in truncated_data:
                truncated_data["description"] = self._truncate_text(truncated_data["description"], 300)
                
        elif template_type == "thank_you":
            # Thank you content limits
            if "title" in truncated_data:
                truncated_data["title"] = self._truncate_text(truncated_data["title"], 40)
            if "message" in truncated_data:
                truncated_data["message"] = self._truncate_text(truncated_data["message"], 150)
        
        return truncated_data
    
    def _truncate_text(self, text: str, max_chars: int, preserve_paragraphs: bool = False) -> str:
        """Truncate text while preserving readability"""
        if len(text) <= max_chars:
            return text
            
        if preserve_paragraphs and '\n\n' in text:
            # For paragraph content, truncate by paragraphs
            paragraphs = text.split('\n\n')
            result = ""
            for para in paragraphs:
                if len(result + para) + 4 <= max_chars:  # +4 for \n\n
                    result += para + '\n\n'
                else:
                    break
            return result.rstrip('\n')
        else:
            # For regular text, truncate at word boundary
            if text[max_chars].isspace():
                return text[:max_chars].rstrip()
            else:
                # Find last space before max_chars
                last_space = text.rfind(' ', 0, max_chars)
                if last_space > max_chars * 0.8:  # If we can keep at least 80% of desired length
                    return text[:last_space] + "..."
                else:
                    return text[:max_chars-3] + "..."

    def _get_required_fields_for_template(self, template_type: str) -> list:
        """Get required fields for each template type"""
        template_fields = {
            "front_page": ["main_title", "subtitle", "author", "date"],
            "basic_content": ["title", "content", "media"],
            "comparison": ["title", "left_title", "left_content", "right_title", "right_content"],
            "chart_data": ["title", "chart_html", "description"],
            "thank_you": ["title", "message", "contact_info"],
            "custom": ["custom_html"]
        }
        return template_fields.get(template_type, [])


class SlideDeckManager:
    """Utility class to manage the entire slide deck creation process"""
    
    def __init__(self, workspace_manager: WorkspaceManager = None):
        self.workspace_manager = workspace_manager
        self.initialize_tool = SlideInitializeTool(workspace_manager)
        self.content_tool = SlideContentTool(workspace_manager)
        self.present_tool = SlidePresentTool(workspace_manager)
    
    def create_presentation(self, main_title: str, project_dir: str, outline: list, 
                          style_instruction: dict, slides_content: list = None) -> dict:
        """
        Create a complete presentation from start to finish
        
        Args:
            main_title: Main title of the presentation
            project_dir: Project directory
            outline: List of slides with id, title, summary
            style_instruction: Style guidelines
            slides_content: Detailed content for each slide (optional)
        
        Returns:
            dict: Result with project information and presentation URL
        """
        # Step 1: Initialize project
        init_result = self.initialize_tool.execute(
            main_title=main_title,
            project_dir=project_dir,
            outline=outline,
            style_instruction=style_instruction
        )
        
        if init_result.error:
            return {"error": init_result.error}
        
        results = {"initialization": init_result.tool_output}
        
        # Step 2: Fill content for slides (if provided)
        if slides_content:
            content_results = []
            for slide_content in slides_content:
                slide_id = slide_content.get("slide_id")
                template_type = slide_content.get("template_type", "basic_content")
                content_data = slide_content.get("content_data", {})
                
                content_result = self.content_tool.execute(
                    project_dir=project_dir,
                    slide_id=slide_id,
                    template_type=template_type,
                    content_data=content_data
                )
                
                content_results.append({
                    "slide_id": slide_id,
                    "result": content_result.tool_output if not content_result.error else content_result.error
                })
            
            results["content_update"] = content_results
        
        # Step 3: Create presentation
        slide_ids = [s['id'] for s in outline]
        present_result = self.present_tool.execute(
            project_dir=project_dir,
            slide_ids=slide_ids
        )
        
        if present_result.error:
            results["presentation_error"] = present_result.error
        else:
            results["presentation"] = {
                "message": present_result.tool_output,
                "url": getattr(present_result, 'auxiliary_data', {}).get('url', None)
            }
        
        return results
    
    def get_available_templates(self) -> dict:
        """Return list of available templates and their descriptions"""
        return {
            "front_page": {
                "name": "Cover Page",
                "description": "Template for opening slide with main title, subtitle and author info",
                "required_fields": ["main_title", "subtitle", "author", "date"]
            },
            "basic_content": {
                "name": "Basic Content",
                "description": "Template for slide with text content and media",
                "required_fields": ["title", "content", "media"]
            },
            "comparison": {
                "name": "Comparison",
                "description": "Template for comparing two contents side by side",
                "required_fields": ["title", "left_title", "left_content", "right_title", "right_content"]
            },
            "chart_data": {
                "name": "Chart Data",
                "description": "Template for slide displaying charts and explanations",
                "required_fields": ["title", "chart_html", "description"]
            },
            "thank_you": {
                "name": "Thank You",
                "description": "Template for closing slide",
                "required_fields": ["title", "message", "contact_info"]
            },
            "custom": {
                "name": "Custom",
                "description": "Custom template with custom HTML",
                "required_fields": ["custom_html"]
            }
        }


# Export main classes
__all__ = ['SlideInitializeTool', 'SlideContentTool', 'SlidePresentTool', 'SlideDeckManager']
