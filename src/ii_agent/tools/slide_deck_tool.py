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
                "description": "The type of content template to use with various visual styles.",
                "enum": [
                    "front_page", "basic_content", "comparison", "chart_data", "thank_you", "custom",
                    "hero_banner", "feature_showcase", "timeline", "process_flow", "team_grid", 
                    "stats_highlight", "quote_slide", "image_gallery", "split_content", 
                    "full_image", "minimal_text", "bullet_points", "icon_grid", "video_embed"
                ],
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
    background: linear-gradient(135deg, var(--background-color) 0%, rgba(255,255,255,0.95) 100%);
}}

.content-area {{
    display: flex;
    gap: 40px;
    height: calc(100% - 100px);
    align-items: center;
}}

.text-content {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}}

.media-content {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255,255,255,0.8);
    border-radius: 15px;
    padding: 20px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
}}

.text-content p {{
    font-size: 20px;
    line-height: 1.7;
    margin-bottom: 20px;
    text-align: justify;
}}

.text-content ul, .text-content ol {{
    font-size: 18px;
    line-height: 1.8;
    padding-left: 20px;
}}

.text-content li {{
    margin-bottom: 12px;
    position: relative;
}}

.text-content ul li::before {{
    content: "▶";
    color: var(--primary-color);
    font-weight: bold;
    position: absolute;
    left: -20px;
}}

.media-content img {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 10px;
    transition: transform 0.3s ease;
}}

.media-content img:hover {{
    transform: scale(1.02);
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

    def _get_hero_banner_template(self) -> str:
        return """<div class="slide-container hero-banner">
    <div class="hero-background" style="background-image: url('{background_image}');">
        <div class="hero-overlay">
            <div class="hero-content">
                <h1 class="hero-title">{title}</h1>
                <h2 class="hero-subtitle">{subtitle}</h2>
                <p class="hero-description">{description}</p>
                <div class="hero-cta">
                    {call_to_action}
                </div>
            </div>
        </div>
    </div>
</div>

<style>
.hero-banner {{
    padding: 0;
    position: relative;
    overflow: hidden;
}}

.hero-background {{
    width: 100%;
    height: 100%;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    position: relative;
    background-color: var(--primary-color);
}}

.hero-overlay {{
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.3) 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
}}

.hero-content {{
    color: white;
    max-width: 800px;
    padding: 40px;
}}

.hero-title {{
    font-size: 56px;
    font-weight: bold;
    margin-bottom: 20px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
}}

.hero-subtitle {{
    font-size: 32px;
    margin-bottom: 30px;
    opacity: 0.9;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
}}

.hero-description {{
    font-size: 20px;
    line-height: 1.6;
    margin-bottom: 40px;
    opacity: 0.9;
}}

.hero-cta {{
    font-size: 18px;
    font-weight: bold;
}}
</style>"""

    def _get_feature_showcase_template(self) -> str:
        return """<div class="slide-container feature-showcase">
    <h1 class="slide-title">{title}</h1>
    <div class="features-grid">
        <div class="feature-item">
            <div class="feature-icon">{icon1}</div>
            <h3 class="feature-title">{feature1_title}</h3>
            <p class="feature-description">{feature1_description}</p>
        </div>
        <div class="feature-item">
            <div class="feature-icon">{icon2}</div>
            <h3 class="feature-title">{feature2_title}</h3>
            <p class="feature-description">{feature2_description}</p>
        </div>
        <div class="feature-item">
            <div class="feature-icon">{icon3}</div>
            <h3 class="feature-title">{feature3_title}</h3>
            <p class="feature-description">{feature3_description}</p>
        </div>
    </div>
</div>

<style>
.feature-showcase {{
    padding: 40px;
    background: linear-gradient(135deg, var(--background-color) 0%, rgba(240,245,255,1) 100%);
}}

.features-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 40px;
    height: calc(100% - 100px);
    align-items: stretch;
}}

.feature-item {{
    background: white;
    border-radius: 20px;
    padding: 40px 30px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    transition: all 0.3s ease;
    border: 2px solid transparent;
}}

.feature-item:hover {{
    transform: translateY(-10px);
    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    border-color: var(--primary-color);
}}

.feature-icon {{
    font-size: 48px;
    margin-bottom: 20px;
    color: var(--primary-color);
}}

.feature-title {{
    font-size: 24px;
    color: var(--header-color);
    margin-bottom: 15px;
    font-weight: bold;
}}

.feature-description {{
    font-size: 16px;
    line-height: 1.6;
    color: var(--text-color);
    opacity: 0.8;
}}
</style>"""

    def _get_timeline_template(self) -> str:
        return """<div class="slide-container timeline">
    <h1 class="slide-title">{title}</h1>
    <div class="timeline-container">
        <div class="timeline-item">
            <div class="timeline-marker"></div>
            <div class="timeline-content">
                <h3>{step1_title}</h3>
                <p>{step1_description}</p>
            </div>
        </div>
        <div class="timeline-item">
            <div class="timeline-marker"></div>
            <div class="timeline-content">
                <h3>{step2_title}</h3>
                <p>{step2_description}</p>
            </div>
        </div>
        <div class="timeline-item">
            <div class="timeline-marker"></div>
            <div class="timeline-content">
                <h3>{step3_title}</h3>
                <p>{step3_description}</p>
            </div>
        </div>
        <div class="timeline-item">
            <div class="timeline-marker"></div>
            <div class="timeline-content">
                <h3>{step4_title}</h3>
                <p>{step4_description}</p>
            </div>
        </div>
    </div>
</div>

<style>
.timeline {{
    padding: 40px;
    background: linear-gradient(135deg, var(--background-color) 0%, rgba(248,250,252,1) 100%);
}}

.timeline-container {{
    position: relative;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px 0;
}}

.timeline-container::before {{
    content: '';
    position: absolute;
    left: 50%;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(to bottom, var(--primary-color), var(--secondary-color));
    border-radius: 2px;
}}

.timeline-item {{
    position: relative;
    margin-bottom: 40px;
    display: flex;
    align-items: center;
}}

.timeline-item:nth-child(odd) {{
    flex-direction: row;
}}

.timeline-item:nth-child(even) {{
    flex-direction: row-reverse;
}}

.timeline-marker {{
    width: 20px;
    height: 20px;
    background: var(--primary-color);
    border-radius: 50%;
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    z-index: 2;
    border: 4px solid white;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}}

.timeline-content {{
    background: white;
    padding: 25px 30px;
    border-radius: 15px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    width: 40%;
    margin: 0 60px;
    position: relative;
}}

.timeline-item:nth-child(odd) .timeline-content {{
    margin-right: 60px;
    margin-left: 0;
}}

.timeline-item:nth-child(even) .timeline-content {{
    margin-left: 60px;
    margin-right: 0;
}}

.timeline-content h3 {{
    color: var(--header-color);
    font-size: 20px;
    margin-bottom: 10px;
    font-weight: bold;
}}

.timeline-content p {{
    color: var(--text-color);
    font-size: 16px;
    line-height: 1.6;
    margin: 0;
}}
</style>"""

    def _get_stats_highlight_template(self) -> str:
        return """<div class="slide-container stats-highlight">
    <h1 class="slide-title">{title}</h1>
    <div class="stats-grid">
        <div class="stat-item">
            <div class="stat-number">{stat1_number}</div>
            <div class="stat-label">{stat1_label}</div>
            <div class="stat-description">{stat1_description}</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{stat2_number}</div>
            <div class="stat-label">{stat2_label}</div>
            <div class="stat-description">{stat2_description}</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{stat3_number}</div>
            <div class="stat-label">{stat3_label}</div>
            <div class="stat-description">{stat3_description}</div>
        </div>
    </div>
</div>

<style>
.stats-highlight {{
    padding: 40px;
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    color: white;
}}

.slide-title {{
    color: white !important;
    text-align: center;
    margin-bottom: 60px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}}

.stats-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 50px;
    height: calc(100% - 150px);
    align-items: center;
}}

.stat-item {{
    text-align: center;
    background: rgba(255,255,255,0.15);
    padding: 40px 20px;
    border-radius: 20px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255,255,255,0.2);
    transition: all 0.3s ease;
}}

.stat-item:hover {{
    transform: translateY(-10px);
    background: rgba(255,255,255,0.2);
}}

.stat-number {{
    font-size: 56px;
    font-weight: bold;
    margin-bottom: 15px;
    color: white;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}}

.stat-label {{
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 10px;
    color: rgba(255,255,255,0.95);
}}

.stat-description {{
    font-size: 16px;
    line-height: 1.5;
    color: rgba(255,255,255,0.85);
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
        elif template_type == "hero_banner":
            template_content = self._get_hero_banner_template()
        elif template_type == "feature_showcase":
            template_content = self._get_feature_showcase_template()
        elif template_type == "timeline":
            template_content = self._get_timeline_template()
        elif template_type == "stats_highlight":
            template_content = self._get_stats_highlight_template()
        elif template_type == "split_content":
            template_content = self._get_split_content_template()
        elif template_type == "quote_slide":
            template_content = self._get_quote_slide_template()
        elif template_type == "bullet_points":
            template_content = self._get_bullet_points_template()
        elif template_type == "full_image":
            template_content = self._get_full_image_template()
        elif template_type == "minimal_text":
            template_content = self._get_minimal_text_template()
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
        """Return enhanced list of available templates and their descriptions"""
        return {
            "front_page": {
                "name": "Cover Page",
                "description": "Enhanced opening slide with gradient backgrounds and modern typography",
                "required_fields": ["main_title", "subtitle", "author", "date"],
                "style_features": ["Gradient overlay", "Glass effect", "Modern typography", "Smooth animations"]
            },
            "basic_content": {
                "name": "Enhanced Basic Content",
                "description": "Improved two-column layout with better visual hierarchy and animations",
                "required_fields": ["title", "content", "media"],
                "style_features": ["Enhanced animations", "Better spacing", "Gradient backgrounds", "Interactive elements"]
            },
            "comparison": {
                "name": "Modern Comparison",
                "description": "Side-by-side comparison with enhanced visual design",
                "required_fields": ["title", "left_title", "left_content", "right_title", "right_content"],
                "style_features": ["Card-based design", "Border animations", "Color coding", "Hover effects"]
            },
            "chart_data": {
                "name": "Data Visualization",
                "description": "Enhanced charts with modern styling and descriptions",
                "required_fields": ["title", "chart_html", "description"],
                "style_features": ["Clean backgrounds", "Shadow effects", "Responsive design", "Typography hierarchy"]
            },
            "thank_you": {
                "name": "Thank You Slide",
                "description": "Beautiful closing slide with enhanced styling",
                "required_fields": ["title", "message", "contact_info"],
                "style_features": ["Gradient background", "Glass morphism", "Elegant typography", "Subtle animations"]
            },
            "hero_banner": {
                "name": "Hero Banner",
                "description": "Full-screen impact slide with background image support",
                "required_fields": ["title", "subtitle", "description", "background_image", "call_to_action"],
                "style_features": ["Full-screen background", "Dramatic typography", "Text shadows", "Overlay effects"]
            },
            "feature_showcase": {
                "name": "Feature Showcase",
                "description": "Three-column grid with icons and feature descriptions",
                "required_fields": ["title", "icon1", "feature1_title", "feature1_description", "icon2", "feature2_title", "feature2_description", "icon3", "feature3_title", "feature3_description"],
                "style_features": ["Card hover effects", "Icon styling", "Grid layout", "Transform animations"]
            },
            "timeline": {
                "name": "Timeline",
                "description": "Vertical timeline for processes or historical events",
                "required_fields": ["title", "step1_title", "step1_description", "step2_title", "step2_description", "step3_title", "step3_description", "step4_title", "step4_description"],
                "style_features": ["Alternating layout", "Connection lines", "Marker animations", "Progressive disclosure"]
            },
            "stats_highlight": {
                "name": "Statistics Highlight",
                "description": "Eye-catching numbers and metrics display",
                "required_fields": ["title", "stat1_number", "stat1_label", "stat1_description", "stat2_number", "stat2_label", "stat2_description", "stat3_number", "stat3_label", "stat3_description"],
                "style_features": ["Glass morphism", "Large typography", "Animated backgrounds", "Gradient effects"]
            },
            "quote_slide": {
                "name": "Quote Slide",
                "description": "Elegant quote presentation with author attribution",
                "required_fields": ["quote_text", "author_name", "author_title"],
                "style_features": ["Centered design", "Large quotation marks", "Elegant typography", "Gradient backgrounds"]
            },
            "split_content": {
                "name": "Split Content",
                "description": "Two-section layout with contrasting backgrounds",
                "required_fields": ["left_title", "left_content", "right_title", "right_content"],
                "style_features": ["50/50 split", "Contrasting colors", "Independent animations", "Visual separation"]
            },
            "bullet_points": {
                "name": "Enhanced Bullet Points",
                "description": "Structured bullet points with icons and visual content",
                "required_fields": ["title", "icon1", "point1_title", "point1_description", "icon2", "point2_title", "point2_description", "icon3", "point3_title", "point3_description", "icon4", "point4_title", "point4_description", "visual_content"],
                "style_features": ["Icon integration", "Card design", "Hover animations", "Side-by-side layout"]
            },
            "full_image": {
                "name": "Full Image Slide",
                "description": "Image-focused slide with minimal text overlay",
                "required_fields": ["image_url", "title", "subtitle"],
                "style_features": ["Full-screen image", "Text overlay", "Image filters", "Responsive scaling"]
            },
            "minimal_text": {
                "name": "Minimal Text",
                "description": "Clean, typography-focused design for important messages",
                "required_fields": ["title", "content", "accent_text"],
                "style_features": ["Clean design", "Typography focus", "Subtle gradients", "Whitespace usage"]
            },
            "custom": {
                "name": "Custom HTML",
                "description": "Fully customizable template with your own HTML/CSS",
                "required_fields": ["custom_html"],
                "style_features": ["Complete freedom", "Custom styling", "Advanced layouts", "Personal branding"]
            }
        }


# Export main classes
__all__ = ['SlideInitializeTool', 'SlideContentTool', 'SlidePresentTool', 'SlideDeckManager']
