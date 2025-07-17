from typing import Any, Optional
from ii_agent.llm.message_history import MessageHistory
from ii_agent.sandbox.config import SandboxSettings
from ii_agent.tools.base import LLMTool, ToolImplOutput
from ii_agent.tools.clients.str_replace_client import StrReplaceClient
from ii_agent.tools.clients.terminal_client import TerminalClient
from ii_agent.utils.workspace_manager import WorkspaceManager


class SlideInitializeTool(LLMTool):
    name = "slide_initialize"
    description = "This tool initializes a presentation structure by creating empty HTML templates for each slide based on the provided outline. It sets up the foundation, style, and structure without detailed content."
    input_schema = {
        "type": "object",
        "properties": {
            "main_title": {
                "type": "string",
                "description": "The main title of the entire presentation that appears prominently on the cover page",
            },
            "project_dir": {
                "type": "string",
                "description": "The directory path where all presentation files will be stored (e.g., /home/ubuntu/deep_learning_slides)",
            },
            "outline": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "description": "Unique identifier for the slide (e.g., trang_bia, gioi_thieu_deep_learning)"},
                        "page_title": {"type": "string", "description": "Title that will appear on this specific slide"},
                        "summary": {"type": "string", "description": "Brief summary of what you want to present in this slide"}
                    },
                    "required": ["id", "page_title", "summary"]
                },
                "description": "List of slides to create with their basic structure",
                "minItems": 1
            },
            "style_instruction": {
                "type": "object",
                "properties": {
                    "color_palette": {"type": "string", "description": "Primary color codes (e.g., Google blue, red, yellow, green)"},
                    "typography": {"type": "string", "description": "Font type and sizes for different text types"},
                    "layout": {"type": "string", "description": "Layout arrangement of elements on slides"},
                    "content_style_description": {"type": "string", "description": "Overall style description (e.g., youthful and vibrant or professional and minimalist)"}
                },
                "description": "Style customization for the presentation appearance and feel"
            }
        },
        "required": ["main_title", "project_dir", "outline"],
    }

    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        str_replace_client: StrReplaceClient,
    ) -> None:
        super().__init__()
        self.workspace_manager = workspace_manager
        self.str_replace_client = str_replace_client

    async def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        try:
            main_title = tool_input["main_title"]
            project_dir = tool_input["project_dir"]
            outline = tool_input["outline"]
            style_instruction = tool_input.get("style_instruction", {})
            
            # Create the project directory
            import os
            os.makedirs(project_dir, exist_ok=True)
            
            # Create empty HTML templates for each slide
            slide_files = []
            for slide_info in outline:
                slide_filename = f"{slide_info['id']}.html"
                slide_path = f"{project_dir}/{slide_filename}"
                slide_files.append(slide_filename)
                
                # Generate empty template with structure and style
                slide_content = self._generate_slide_template(
                    slide_info["page_title"], 
                    slide_info["summary"],
                    slide_info["id"],
                    main_title,
                    style_instruction
                )
                self.str_replace_client.write_file(slide_path, slide_content)

            # Create project metadata file
            self._create_project_metadata(project_dir, main_title, outline, style_instruction)

            return ToolImplOutput(
                f"Successfully initialized presentation '{main_title}' with {len(outline)} slide templates in `{project_dir}`. Created slide templates: {', '.join(slide_files)}",
                "Successfully initialized presentation structure",
                auxiliary_data={
                    "success": True,
                    "main_title": main_title,
                    "project_dir": project_dir,
                    "slide_files": slide_files,
                    "slide_ids": [slide["id"] for slide in outline]
                },
            )

        except Exception as e:
            return ToolImplOutput(
                f"Error initializing presentation: {str(e)}",
                "Error initializing presentation",
                auxiliary_data={"success": False, "error": str(e)},
            )

    def _generate_slide_template(self, page_title: str, summary: str, slide_id: str, main_title: str, style_instruction: dict) -> str:
        """Generate HTML template for a slide with structure and style but without detailed content"""
        
        # Extract style preferences
        color_palette = style_instruction.get("color_palette", "modern blue gradient")
        typography = style_instruction.get("typography", "Inter font family")
        layout = style_instruction.get("layout", "centered with title and content areas")
        content_style = style_instruction.get("content_style_description", "professional and clean")
        
        # Generate background style based on color palette
        if "blue" in color_palette.lower():
            background_style = "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
        elif "green" in color_palette.lower():
            background_style = "background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);"
        elif "orange" in color_palette.lower() or "warm" in color_palette.lower():
            background_style = "background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);"
        else:
            background_style = "background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title} - {main_title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #2563eb;
            --secondary-color: #f1f5f9;
            --text-primary: #1e293b;
            --text-secondary: #64748b;
            --border-color: #e2e8f0;
            --shadow-light: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
            --shadow-medium: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-large: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            height: 100vh;
            overflow: hidden;
            {background_style}
            font-feature-settings: 'liga' 1, 'kern' 1;
            text-rendering: optimizeLegibility;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        
        .slide-container {{
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 3rem;
            position: relative;
        }}
        
        .slide-content {{
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 4rem;
            box-shadow: var(--shadow-large);
            max-width: 900px;
            width: 100%;
            max-height: 80vh;
            overflow-y: auto;
            animation: slideIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        .slide-header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            position: relative;
        }}
        
        .slide-header::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color), #8b5cf6);
            border-radius: 2px;
        }}
        
        .slide-title {{
            font-size: 3rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 1rem;
            line-height: 1.2;
            letter-spacing: -0.025em;
        }}
        
        .slide-summary {{
            font-size: 1.2rem;
            color: var(--text-secondary);
            line-height: 1.6;
            font-weight: 400;
            font-style: italic;
            opacity: 0.8;
        }}
        
        .content-area {{
            min-height: 300px;
            padding: 2rem;
            border: 2px dashed var(--border-color);
            border-radius: 12px;
            background: rgba(248, 250, 252, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }}
        
        .content-placeholder {{
            color: var(--text-secondary);
            font-size: 1.1rem;
            line-height: 1.6;
        }}
        
        .template-info {{
            position: fixed;
            top: 2rem;
            right: 2rem;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            border: none;
            padding: 0.8rem 1.2rem;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-secondary);
            box-shadow: var(--shadow-medium);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        /* Animations */
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(40px) scale(0.95);
            }}
            to {{
                opacity: 1;
                transform: translateY(0) scale(1);
            }}
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .slide-container {{
                padding: 1.5rem;
            }}
            
            .slide-content {{
                padding: 2.5rem 2rem;
                border-radius: 20px;
                max-height: 85vh;
            }}
            
            .slide-title {{
                font-size: 2.2rem;
                margin-bottom: 1rem;
            }}
            
            .slide-summary {{
                font-size: 1.1rem;
            }}
            
            .content-area {{
                min-height: 200px;
                padding: 1.5rem;
            }}
            
            .template-info {{
                top: 1rem;
                right: 1rem;
                padding: 0.6rem 1rem;
                font-size: 0.8rem;
            }}
        }}
        
        @media (max-width: 480px) {{
            .slide-content {{
                padding: 2rem 1.5rem;
            }}
            
            .slide-title {{
                font-size: 1.8rem;
            }}
        }}
        
        /* Custom scrollbar */
        .slide-content::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .slide-content::-webkit-scrollbar-track {{
            background: transparent;
        }}
        
        .slide-content::-webkit-scrollbar-thumb {{
            background: rgba(0, 0, 0, 0.2);
            border-radius: 3px;
        }}
        
        .slide-content::-webkit-scrollbar-thumb:hover {{
            background: rgba(0, 0, 0, 0.3);
        }}
    </style>
</head>
<body>
    <div class="template-info">Template: {slide_id}</div>
    
    <div class="slide-container">
        <div class="slide-content">
            <div class="slide-header">
                <h1 class="slide-title">{page_title}</h1>
                <p class="slide-summary">{summary}</p>
            </div>
            
            <div class="content-area">
                <div class="content-placeholder">
                    <p><strong>Content will be added here</strong></p>
                    <p>This is a template slide for: <em>{page_title}</em></p>
                    <p>Summary: {summary}</p>
                    <br>
                    <p>Style: {content_style}</p>
                    <p>Color Palette: {color_palette}</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Template identification
        console.log('Slide Template ID: {slide_id}');
        console.log('Main Title: {main_title}');
        console.log('Page Title: {page_title}');
        console.log('Summary: {summary}');
        
        // Page load animation
        window.addEventListener('load', function() {{
            document.body.style.transition = 'opacity 0.3s ease';
            document.body.style.opacity = '1';
        }});
        
        document.body.style.opacity = '0';
    </script>
</body>
</html>"""

    def _create_project_metadata(self, project_dir: str, main_title: str, outline: list, style_instruction: dict) -> None:
        """Create a metadata file for the project with all necessary information"""
        metadata_path = f"{project_dir}/project_metadata.json"
        
        import json
        metadata = {
            "main_title": main_title,
            "project_dir": project_dir,
            "outline": outline,
            "style_instruction": style_instruction,
            "slide_ids": [slide["id"] for slide in outline],
            "created_at": "2025-07-16",
            "version": "1.0"
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)


class SlidePresentTool(LLMTool):
    name = "slide_present"
    description = "This tool presents an initialized slide deck by combining the slides in the specified order and creating a navigable presentation interface."
    input_schema = {
        "type": "object",
        "properties": {
            "project_dir": {
                "type": "string",
                "description": "The directory path where the presentation files are stored (same as used in slide_initialize)",
            },
            "slide_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of slide IDs in the order they should be presented (e.g., ['trang_bia', 'gioi_thieu'])",
                "minItems": 1
            }
        },
        "required": ["project_dir", "slide_ids"],
    }

    def __init__(
        self, workspace_manager: WorkspaceManager, str_replace_client: StrReplaceClient
    ) -> None:
        super().__init__()
        self.workspace_manager = workspace_manager
        self.str_replace_client = str_replace_client

    async def run_impl(
        self,
        tool_input: dict[str, Any],
        message_history: Optional[MessageHistory] = None,
    ) -> ToolImplOutput:
        try:
            project_dir = tool_input["project_dir"]
            slide_ids = tool_input["slide_ids"]
            
            # Check if project directory exists
            import os
            import json
            
            if not os.path.exists(project_dir):
                return ToolImplOutput(
                    f"Error: Project directory '{project_dir}' not found. Please initialize the presentation first using slide_initialize tool.",
                    "Project directory not found",
                    auxiliary_data={"success": False, "error": "Project not initialized"},
                )
            
            # Load project metadata
            metadata_path = f"{project_dir}/project_metadata.json"
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                main_title = metadata.get("main_title", "Presentation")
                outline = metadata.get("outline", [])
                style_instruction = metadata.get("style_instruction", {})
            except:
                return ToolImplOutput(
                    f"Error: Could not load project metadata from '{metadata_path}'. Project may be corrupted.",
                    "Project metadata not found",
                    auxiliary_data={"success": False, "error": "Metadata missing"},
                )
            
            # Validate slide IDs exist
            available_ids = [slide["id"] for slide in outline]
            missing_ids = [sid for sid in slide_ids if sid not in available_ids]
            
            if missing_ids:
                return ToolImplOutput(
                    f"Error: The following slide IDs were not found in the project: {', '.join(missing_ids)}. Available IDs: {', '.join(available_ids)}",
                    "Invalid slide IDs",
                    auxiliary_data={"success": False, "error": "Invalid slide IDs", "missing_ids": missing_ids, "available_ids": available_ids},
                )
            
            # Check if slide files exist
            missing_files = []
            for slide_id in slide_ids:
                slide_file = f"{project_dir}/{slide_id}.html"
                if not os.path.exists(slide_file):
                    missing_files.append(f"{slide_id}.html")
            
            if missing_files:
                return ToolImplOutput(
                    f"Error: The following slide files were not found: {', '.join(missing_files)}",
                    "Slide files missing",
                    auxiliary_data={"success": False, "error": "Slide files missing", "missing_files": missing_files},
                )
            
            # Create presentation with navigation
            presentation_url = self._create_presentation_interface(project_dir, main_title, slide_ids, outline, style_instruction)
            
            return ToolImplOutput(
                f"Successfully created presentation interface for '{main_title}' with {len(slide_ids)} slides in order: {', '.join(slide_ids)}. Access your presentation at: {presentation_url}",
                "Successfully created presentation interface",
                auxiliary_data={
                    "success": True,
                    "main_title": main_title,
                    "project_dir": project_dir,
                    "slide_ids": slide_ids,
                    "presentation_url": presentation_url,
                    "total_slides": len(slide_ids)
                },
            )

        except Exception as e:
            return ToolImplOutput(
                f"Error creating presentation: {str(e)}",
                "Error creating presentation",
                auxiliary_data={"success": False, "error": str(e)},
            )

    def _create_presentation_interface(self, project_dir: str, main_title: str, slide_ids: list[str], outline: list[dict], style_instruction: dict) -> str:
        """Create presentation interface that combines slides in specified order."""
        import os
        import json
        
        # Read individual slide files and extract content
        slide_contents = []
        for slide_id in slide_ids:
            slide_file = f"{project_dir}/{slide_id}.html"
            try:
                with open(slide_file, 'r', encoding='utf-8') as f:
                    slide_html = f.read()
                
                # Extract slide content (everything within slide-content div)
                import re
                content_match = re.search(r'<div class="slide-content">(.*?)</div>', slide_html, re.DOTALL)
                if content_match:
                    slide_contents.append(content_match.group(1).strip())
                else:
                    slide_contents.append(f"<h2>Slide {slide_id}</h2><p>Content not found</p>")
            except Exception:
                slide_contents.append(f"<h2>Error loading slide {slide_id}</h2><p>Could not load slide content</p>")
        
        # Get slide metadata for titles
        slide_metadata = {slide["id"]: slide for slide in outline}
        
        # Generate presentation HTML
        presentation_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{main_title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary-color: {style_instruction.get('primary_color', '#2563eb')};
            --secondary-color: {style_instruction.get('secondary_color', '#1e40af')};
            --accent-color: {style_instruction.get('accent_color', '#3b82f6')};
            --background-color: {style_instruction.get('background_color', '#0f172a')};
            --text-color: {style_instruction.get('text_color', '#f8fafc')};
            --slide-background: {style_instruction.get('slide_background', 'rgba(255, 255, 255, 0.05)')};
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, var(--background-color), #1e293b);
            color: var(--text-color);
            overflow: hidden;
            min-height: 100vh;
        }}

        .presentation-container {{
            position: relative;
            width: 100vw;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .slide {{
            position: absolute;
            width: 90%;
            max-width: 1200px;
            height: 85%;
            background: var(--slide-background);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 60px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            opacity: 0;
            transform: translateX(100px) scale(0.9);
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
        }}

        .slide.active {{
            opacity: 1;
            transform: translateX(0) scale(1);
        }}

        .slide.prev {{
            transform: translateX(-100px) scale(0.9);
        }}

        .slide h1, .slide h2, .slide h3 {{
            margin-bottom: 30px;
            line-height: 1.2;
        }}

        .slide h1 {{
            font-size: 3.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .slide h2 {{
            font-size: 2.5rem;
            font-weight: 600;
            color: var(--text-color);
        }}

        .slide h3 {{
            font-size: 2rem;
            font-weight: 500;
            color: var(--accent-color);
        }}

        .slide p {{
            font-size: 1.2rem;
            line-height: 1.6;
            margin-bottom: 20px;
            max-width: 800px;
        }}

        .slide ul, .slide ol {{
            text-align: left;
            max-width: 600px;
            margin: 20px 0;
        }}

        .slide li {{
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 10px;
            padding-left: 10px;
        }}

        .navigation {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 15px;
            z-index: 1000;
        }}

        .nav-btn {{
            padding: 12px 20px;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            color: var(--text-color);
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Inter', sans-serif;
            font-weight: 500;
        }}

        .nav-btn:hover {{
            background: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }}

        .nav-btn:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}

        .slide-counter {{
            position: fixed;
            top: 30px;
            right: 30px;
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 500;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .slide-title {{
            position: fixed;
            top: 30px;
            left: 30px;
            background: rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 500;
            border: 1px solid rgba(255, 255, 255, 0.1);
            max-width: 300px;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }}

        @media (max-width: 768px) {{
            .slide {{
                padding: 30px;
                width: 95%;
                height: 80%;
            }}

            .slide h1 {{
                font-size: 2.5rem;
            }}

            .slide h2 {{
                font-size: 2rem;
            }}

            .slide h3 {{
                font-size: 1.5rem;
            }}

            .slide p {{
                font-size: 1.1rem;
            }}

            .nav-btn {{
                padding: 10px 15px;
                font-size: 0.9rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="presentation-container">
        <div class="slide-title" id="slideTitle">{main_title}</div>
        <div class="slide-counter">
            <span id="currentSlide">1</span> / <span id="totalSlides">{len(slide_ids)}</span>
        </div>

"""

        # Add individual slides
        for i, (slide_id, content) in enumerate(zip(slide_ids, slide_contents)):
            slide_title = slide_metadata.get(slide_id, {}).get("title", f"Slide {slide_id}")
            active_class = "active" if i == 0 else ""
            
            presentation_html += f"""
        <div class="slide {active_class}" data-slide="{i}" data-title="{slide_title}">
            {content}
        </div>
"""

        # Add navigation and script
        presentation_html += """
        <div class="navigation">
            <button class="nav-btn" id="prevBtn" onclick="previousSlide()">← Previous</button>
            <button class="nav-btn" id="nextBtn" onclick="nextSlide()">Next →</button>
        </div>
    </div>

    <script>
        let currentSlideIndex = 0;
        const slides = document.querySelectorAll('.slide');
        const totalSlides = slides.length;

        function updateSlideDisplay() {
            slides.forEach((slide, index) => {
                slide.classList.remove('active', 'prev');
                if (index === currentSlideIndex) {
                    slide.classList.add('active');
                } else if (index < currentSlideIndex) {
                    slide.classList.add('prev');
                }
            });

            // Update counter
            document.getElementById('currentSlide').textContent = currentSlideIndex + 1;

            // Update title
            const currentSlide = slides[currentSlideIndex];
            const slideTitle = currentSlide.getAttribute('data-title');
            document.getElementById('slideTitle').textContent = slideTitle;

            // Update navigation buttons
            document.getElementById('prevBtn').disabled = currentSlideIndex === 0;
            document.getElementById('nextBtn').disabled = currentSlideIndex === totalSlides - 1;
        }

        function nextSlide() {
            if (currentSlideIndex < totalSlides - 1) {
                currentSlideIndex++;
                updateSlideDisplay();
            }
        }

        function previousSlide() {
            if (currentSlideIndex > 0) {
                currentSlideIndex--;
                updateSlideDisplay();
            }
        }

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === ' ') {
                e.preventDefault();
                nextSlide();
            } else if (e.key === 'ArrowLeft') {
                e.preventDefault();
                previousSlide();
            } else if (e.key === 'Home') {
                e.preventDefault();
                currentSlideIndex = 0;
                updateSlideDisplay();
            } else if (e.key === 'End') {
                e.preventDefault();
                currentSlideIndex = totalSlides - 1;
                updateSlideDisplay();
            }
        });

        // Touch navigation for mobile
        let touchStartX = 0;
        let touchEndX = 0;

        document.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });

        document.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        });

        function handleSwipe() {
            const swipeThreshold = 50;
            const diff = touchStartX - touchEndX;

            if (Math.abs(diff) > swipeThreshold) {
                if (diff > 0) {
                    nextSlide(); // Swipe left - next slide
                } else {
                    previousSlide(); // Swipe right - previous slide
                }
            }
        }

        // Initialize
        updateSlideDisplay();
    </script>
</body>
</html>
"""

        # Save presentation file
        presentation_path = f"{project_dir}/presentation.html"
        with open(presentation_path, 'w', encoding='utf-8') as f:
            f.write(presentation_html)
        
        return f"file://{os.path.abspath(presentation_path)}"


