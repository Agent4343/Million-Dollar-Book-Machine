"""
Image Generation Module using Google Gemini/Imagen API

Generates book covers and chapter illustrations using AI.
Analyzes book content to create context-aware, accurate prompts.
"""

import os
import base64
import io
from typing import Optional, Dict, Any, List

# Lazy import to avoid issues if not installed
_genai = None
_PIL_Image = None


def get_genai():
    """Lazy load google.generativeai"""
    global _genai
    if _genai is None:
        try:
            import google.generativeai as genai
            api_key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
            _genai = genai
        except ImportError:
            return None
    return _genai


def get_pil():
    """Lazy load PIL"""
    global _PIL_Image
    if _PIL_Image is None:
        try:
            from PIL import Image
            _PIL_Image = Image
        except ImportError:
            return None
    return _PIL_Image


def check_image_gen_status() -> Dict[str, Any]:
    """Check if image generation is available."""
    genai = get_genai()
    api_key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if genai is None:
        return {
            "available": False,
            "reason": "google-generativeai not installed",
            "has_api_key": bool(api_key)
        }

    if not api_key:
        return {
            "available": False,
            "reason": "No GOOGLE_AI_API_KEY or GEMINI_API_KEY environment variable set",
            "has_api_key": False
        }

    return {
        "available": True,
        "reason": "Image generation ready",
        "has_api_key": True
    }


# =============================================================================
# Book Analysis Functions - Extract visual elements from story data
# =============================================================================

def analyze_book_for_visuals(project) -> Dict[str, Any]:
    """
    Analyze a book project and extract key visual elements for image generation.
    Pulls from all completed pipeline agents to build rich context.
    """
    visual_data = {
        "title": project.title,
        "genre": project.user_constraints.get("genre", "fiction"),
        "themes": project.user_constraints.get("themes", []),
        "description": project.user_constraints.get("description", ""),
        "tone": project.user_constraints.get("tone", ""),
        "target_audience": project.user_constraints.get("target_audience", ""),

        # Extracted from pipeline
        "protagonist": None,
        "antagonist": None,
        "setting": None,
        "time_period": None,
        "mood": None,
        "key_symbols": [],
        "color_palette_hints": [],
        "central_conflict": None,
        "story_hook": None,
    }

    # Extract data from completed agents
    for layer in project.layers.values():
        for agent_id, agent_state in layer.agents.items():
            if agent_state.current_output and agent_state.current_output.content:
                content = agent_state.current_output.content
                _extract_agent_visuals(agent_id, content, visual_data)

    return visual_data


def _extract_agent_visuals(agent_id: str, content: Dict, visual_data: Dict):
    """Extract visual elements from a specific agent's output."""

    if agent_id == "character_architecture":
        # Extract protagonist details
        if content.get("protagonist_profile"):
            pp = content["protagonist_profile"]
            visual_data["protagonist"] = {
                "name": pp.get("name", ""),
                "traits": pp.get("traits", []),
                "appearance": pp.get("physical_description", ""),
                "age": pp.get("age", ""),
                "occupation": pp.get("occupation", ""),
            }

        # Extract antagonist details
        if content.get("antagonist_profile"):
            ap = content["antagonist_profile"]
            visual_data["antagonist"] = {
                "name": ap.get("name", ""),
                "type": ap.get("type", ""),
                "worldview": ap.get("worldview", ""),
            }

    elif agent_id == "world_architecture":
        # Extract setting details
        if content.get("primary_setting"):
            ps = content["primary_setting"]
            visual_data["setting"] = {
                "location": ps.get("location", ""),
                "environment": ps.get("environment", ""),
                "atmosphere": ps.get("atmosphere", ""),
            }
        visual_data["time_period"] = content.get("time_period", "")

    elif agent_id == "thematic_architecture":
        # Extract mood and symbols
        if content.get("primary_theme"):
            visual_data["mood"] = content["primary_theme"].get("mood", "")
        if content.get("symbols"):
            visual_data["key_symbols"] = content["symbols"][:5]  # Top 5 symbols

    elif agent_id == "concept_definition":
        # Extract hook and core concept
        visual_data["story_hook"] = content.get("one_line_hook", "")
        if content.get("core_promise"):
            visual_data["central_conflict"] = content["core_promise"].get("transformation", "")

    elif agent_id == "voice_specification":
        # Extract tone/mood hints
        if content.get("narrative_voice"):
            nv = content["narrative_voice"]
            visual_data["mood"] = nv.get("tone", visual_data.get("mood", ""))

    elif agent_id == "market_intelligence":
        # Extract visual style hints from market positioning
        if content.get("positioning_angle"):
            pa = content["positioning_angle"]
            visual_data["color_palette_hints"] = pa.get("visual_style_notes", [])


def get_genre_visual_style(genre: str) -> Dict[str, str]:
    """Get visual style recommendations based on genre."""

    genre_styles = {
        "thriller": {
            "colors": "dark, high contrast, shadows, noir palette",
            "mood": "tense, suspenseful, mysterious",
            "elements": "shadows, silhouettes, urban landscapes, rain",
            "typography_hint": "bold, stark, modern sans-serif"
        },
        "romance": {
            "colors": "warm, soft, romantic pastels or rich jewel tones",
            "mood": "emotional, intimate, passionate",
            "elements": "couples in silhouette, flowers, sunset/sunrise, intertwined elements",
            "typography_hint": "elegant script, flowing"
        },
        "sci_fi": {
            "colors": "cool blues, neon accents, metallic",
            "mood": "futuristic, vast, technological",
            "elements": "space, technology, geometric shapes, cityscapes",
            "typography_hint": "sleek, futuristic, geometric"
        },
        "fantasy": {
            "colors": "rich, magical, ethereal glows",
            "mood": "epic, mystical, otherworldly",
            "elements": "magical creatures, castles, forests, mystical symbols",
            "typography_hint": "ornate, medieval-inspired"
        },
        "horror": {
            "colors": "black, red, desaturated, shadows",
            "mood": "dread, fear, unsettling",
            "elements": "darkness, decay, isolated settings, ominous shapes",
            "typography_hint": "distressed, eerie"
        },
        "mystery": {
            "colors": "muted, foggy, sepia undertones",
            "mood": "intriguing, secretive, atmospheric",
            "elements": "magnifying glass, shadows, clues, fog",
            "typography_hint": "classic, sophisticated"
        },
        "literary_fiction": {
            "colors": "sophisticated, muted, artistic",
            "mood": "contemplative, emotional, meaningful",
            "elements": "symbolic imagery, artistic composition, metaphorical",
            "typography_hint": "elegant, classic serif"
        },
        "memoir": {
            "colors": "warm, nostalgic, personal",
            "mood": "reflective, authentic, intimate",
            "elements": "personal objects, photographs, meaningful locations",
            "typography_hint": "personal, handwritten feel"
        },
    }

    # Normalize genre name
    genre_lower = genre.lower().replace(" ", "_").replace("-", "_")

    return genre_styles.get(genre_lower, {
        "colors": "appropriate to story mood",
        "mood": "engaging, professional",
        "elements": "symbolic of story themes",
        "typography_hint": "genre-appropriate"
    })


# =============================================================================
# Prompt Building Functions
# =============================================================================

def build_intelligent_cover_prompt(
    visual_data: Dict[str, Any],
    cover_type: str = "front",
    style: str = "professional cinematic"
) -> str:
    """Build a detailed, story-aware prompt for cover generation."""

    genre_style = get_genre_visual_style(visual_data.get("genre", "fiction"))

    # Build protagonist description if available
    protagonist_desc = ""
    if visual_data.get("protagonist"):
        p = visual_data["protagonist"]
        parts = []
        if p.get("appearance"):
            parts.append(p["appearance"])
        if p.get("age"):
            parts.append(f"age {p['age']}")
        if p.get("traits"):
            parts.append(f"with {', '.join(p['traits'][:3])} demeanor")
        if parts:
            protagonist_desc = f"Protagonist: {' '.join(parts)}"

    # Build setting description
    setting_desc = ""
    if visual_data.get("setting"):
        s = visual_data["setting"]
        parts = [s.get("location", ""), s.get("environment", ""), s.get("atmosphere", "")]
        setting_desc = f"Setting: {', '.join(p for p in parts if p)}"

    # Build symbols/motifs
    symbols = ""
    if visual_data.get("key_symbols"):
        symbols = f"Key visual symbols: {', '.join(visual_data['key_symbols'][:3])}"

    if cover_type == "front":
        prompt = f"""Create a professional, publishable FRONT BOOK COVER for:

TITLE: "{visual_data['title']}"
GENRE: {visual_data['genre']}
STORY HOOK: {visual_data.get('story_hook', visual_data.get('description', ''))}

VISUAL DIRECTION:
- Color palette: {genre_style['colors']}
- Mood: {genre_style['mood']}, {visual_data.get('mood', '')}
- Key visual elements: {genre_style['elements']}

STORY ELEMENTS TO INCORPORATE:
{protagonist_desc}
{setting_desc}
{symbols}
Themes: {', '.join(visual_data.get('themes', []))}

STYLE: {style}

CRITICAL REQUIREMENTS:
- NO text, letters, or words in the image - ONLY visual artwork
- Leave clear space at TOP for title text overlay
- Leave clear space at BOTTOM for author name
- Vertical/portrait orientation (book cover ratio)
- High resolution, professional quality
- Evocative of the story's mood and themes
- Would look compelling on a bookstore shelf
"""

    elif cover_type == "back":
        prompt = f"""Create a professional BACK BOOK COVER design for:

TITLE: "{visual_data['title']}"
GENRE: {visual_data['genre']}

VISUAL DIRECTION:
- Color palette: {genre_style['colors']} (slightly muted)
- Mood: {genre_style['mood']} but subtle
- Should complement front cover aesthetic

DESIGN REQUIREMENTS:
- Subtle, textured background design
- NOT compete with text (synopsis will overlay)
- Large clear area in CENTER for text
- Small design elements at edges/corners
- Vertical/portrait orientation
- NO text, letters, or words
- Professional, publishable quality
"""

    else:  # spine
        prompt = f"""Create a narrow BOOK SPINE design for:

TITLE: "{visual_data['title']}"
GENRE: {visual_data['genre']}

REQUIREMENTS:
- Very narrow vertical strip
- Complementary to cover colors: {genre_style['colors']}
- Simple, elegant design elements only
- NO text or letters
- Would connect front and back cover seamlessly
"""

    return prompt


def build_intelligent_chapter_prompt(
    chapter_number: int,
    chapter_title: str,
    chapter_content: str,
    visual_data: Dict[str, Any],
    style: str = "atmospheric illustration"
) -> str:
    """Build a story-aware prompt for chapter illustration."""

    genre_style = get_genre_visual_style(visual_data.get("genre", "fiction"))

    # Analyze chapter content for key visual moments
    # Take key sentences that might describe scenes
    content_excerpt = chapter_content[:1000] if chapter_content else ""

    prompt = f"""Create an evocative CHAPTER ILLUSTRATION for:

BOOK: "{visual_data['title']}" ({visual_data['genre']})
CHAPTER {chapter_number}: "{chapter_title}"

SCENE CONTENT:
{content_excerpt}...

VISUAL DIRECTION:
- Color palette: {genre_style['colors']}
- Mood: {genre_style['mood']}
- Style: {style}

STORY CONTEXT:
- Themes: {', '.join(visual_data.get('themes', [])[:3])}
- Overall mood: {visual_data.get('mood', 'dramatic')}

REQUIREMENTS:
- Capture the emotional essence of this chapter
- Horizontal/landscape orientation (chapter header)
- Atmospheric and evocative, not literal
- NO text, letters, or words
- Professional illustration quality
- Would work as a chapter opener image
"""

    return prompt


def extract_chapter_visual_moments(chapter_text: str) -> List[str]:
    """Extract key visual moments from chapter text for illustration."""

    # Look for descriptive passages
    visual_keywords = [
        "looked", "saw", "watched", "gazed", "stood", "walked",
        "dark", "light", "shadow", "sun", "moon", "rain",
        "room", "house", "street", "forest", "city", "ocean"
    ]

    sentences = chapter_text.split('.')
    visual_sentences = []

    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in visual_keywords):
            if len(sentence.strip()) > 20:  # Skip very short sentences
                visual_sentences.append(sentence.strip())

    # Return top 3 most visual sentences
    return visual_sentences[:3]


# =============================================================================
# Image Generation Functions
# =============================================================================

async def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    style: str = "vivid"
) -> Optional[Dict[str, Any]]:
    """
    Generate an image using Google's Imagen model.

    Returns dict with:
    - success: bool
    - image_base64: base64 encoded image (if success)
    - error: error message (if failed)
    """
    genai = get_genai()

    if genai is None:
        return {
            "success": False,
            "error": "Google AI SDK not available"
        }

    api_key = os.environ.get("GOOGLE_AI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "success": False,
            "error": "No API key configured"
        }

    try:
        # Use Imagen 3 model for image generation
        imagen = genai.ImageGenerationModel("imagen-3.0-generate-002")

        # Determine aspect ratio
        if height > width * 1.2:
            aspect = "9:16"  # Portrait (book cover)
        elif width > height * 1.2:
            aspect = "16:9"  # Landscape (chapter illustration)
        else:
            aspect = "1:1"

        result = imagen.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio=aspect,
            safety_filter_level="block_only_high",
            person_generation="allow_adult"
        )

        if result.images:
            image = result.images[0]
            buffered = io.BytesIO()
            image._pil_image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            return {
                "success": True,
                "image_base64": img_base64,
                "format": "png"
            }
        else:
            return {
                "success": False,
                "error": "No image generated"
            }

    except Exception as e:
        error_msg = str(e)

        # Try fallback
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            return await generate_image_gemini_fallback(prompt)

        return {
            "success": False,
            "error": f"Image generation failed: {error_msg}"
        }


async def generate_image_gemini_fallback(prompt: str) -> Dict[str, Any]:
    """Fallback using Gemini model if Imagen unavailable."""
    genai = get_genai()

    if genai is None:
        return {
            "success": False,
            "error": "Google AI SDK not available"
        }

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')

        enhanced_prompt = f"""Generate an image based on this description:

{prompt}

Create a high-quality, detailed image that matches this description exactly."""

        response = model.generate_content(
            enhanced_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="image/png"
            )
        )

        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_data = part.inline_data.data
                    img_base64 = base64.b64encode(img_data).decode()
                    return {
                        "success": True,
                        "image_base64": img_base64,
                        "format": "png"
                    }

        return {
            "success": False,
            "error": "Gemini image generation not available. Please ensure you have access to Imagen API.",
            "fallback_description": response.text if hasattr(response, 'text') else None
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Fallback generation failed: {str(e)}"
        }


# =============================================================================
# Main Generation Functions (called from API)
# =============================================================================

async def generate_book_cover(
    project,
    cover_type: str = "front",
    style: str = "professional cinematic book cover"
) -> Dict[str, Any]:
    """Generate a book cover using intelligent story analysis."""

    # Analyze the book for visual elements
    visual_data = analyze_book_for_visuals(project)

    # Build intelligent prompt
    prompt = build_intelligent_cover_prompt(
        visual_data=visual_data,
        cover_type=cover_type,
        style=style
    )

    # Generate image
    if cover_type in ["front", "back"]:
        width, height = 768, 1024  # Portrait for covers
    else:
        width, height = 256, 1024  # Narrow for spine

    result = await generate_image(prompt, width=width, height=height)
    result["prompt_used"] = prompt
    result["cover_type"] = cover_type
    result["visual_analysis"] = {
        "genre": visual_data.get("genre"),
        "themes": visual_data.get("themes"),
        "mood": visual_data.get("mood"),
        "has_protagonist": bool(visual_data.get("protagonist")),
        "has_setting": bool(visual_data.get("setting")),
    }

    return result


async def generate_chapter_illustration(
    project,
    chapter_number: int,
    chapter_title: str,
    chapter_content: str,
    style: str = "moody atmospheric illustration"
) -> Dict[str, Any]:
    """Generate a chapter illustration using story analysis."""

    # Analyze the book for visual elements
    visual_data = analyze_book_for_visuals(project)

    # Build intelligent prompt
    prompt = build_intelligent_chapter_prompt(
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        chapter_content=chapter_content,
        visual_data=visual_data,
        style=style
    )

    # Generate landscape image for chapter header
    result = await generate_image(prompt, width=1024, height=576)
    result["prompt_used"] = prompt
    result["chapter_number"] = chapter_number

    return result


# =============================================================================
# Legacy compatibility functions (simple interface)
# =============================================================================

async def generate_book_cover_simple(
    title: str,
    genre: str,
    description: str,
    themes: list,
    cover_type: str = "front",
    style: str = "professional cinematic book cover"
) -> Dict[str, Any]:
    """Simple cover generation without full project analysis (legacy support)."""

    visual_data = {
        "title": title,
        "genre": genre,
        "themes": themes,
        "description": description,
        "story_hook": description,
        "mood": "",
        "protagonist": None,
        "setting": None,
        "key_symbols": [],
    }

    prompt = build_intelligent_cover_prompt(
        visual_data=visual_data,
        cover_type=cover_type,
        style=style
    )

    if cover_type in ["front", "back"]:
        width, height = 768, 1024
    else:
        width, height = 256, 1024

    result = await generate_image(prompt, width=width, height=height)
    result["prompt_used"] = prompt
    result["cover_type"] = cover_type

    return result


async def generate_chapter_illustration_simple(
    chapter_number: int,
    chapter_title: str,
    chapter_summary: str,
    genre: str,
    style: str = "moody atmospheric illustration"
) -> Dict[str, Any]:
    """Simple chapter illustration without full project analysis (legacy support)."""

    visual_data = {
        "title": "",
        "genre": genre,
        "themes": [],
        "mood": "",
    }

    prompt = build_intelligent_chapter_prompt(
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        chapter_content=chapter_summary,
        visual_data=visual_data,
        style=style
    )

    result = await generate_image(prompt, width=1024, height=576)
    result["prompt_used"] = prompt
    result["chapter_number"] = chapter_number

    return result
