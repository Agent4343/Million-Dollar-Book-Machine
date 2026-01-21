"""
Image Generation Module using Google Gemini/Imagen API

Generates book covers and chapter illustrations using AI.
"""

import os
import base64
import io
from typing import Optional, Dict, Any

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


def build_cover_prompt(
    title: str,
    genre: str,
    description: str,
    themes: list,
    cover_type: str = "front",
    style: str = "professional book cover"
) -> str:
    """Build a detailed prompt for cover generation."""

    theme_str = ", ".join(themes) if themes else "universal themes"

    if cover_type == "front":
        prompt = f"""Create a professional front book cover design for:

Title: "{title}"
Genre: {genre}
Description: {description}
Themes: {theme_str}

Style requirements:
- {style}
- High-quality, publishable book cover
- Visually striking and genre-appropriate
- Leave space at top for title text
- Leave space at bottom for author name
- Rich colors and professional composition
- NO text or letters in the image - just the visual artwork
- Vertical orientation (portrait) suitable for a book cover
"""
    elif cover_type == "back":
        prompt = f"""Create a professional back book cover design for:

Title: "{title}"
Genre: {genre}
Themes: {theme_str}

Style requirements:
- Complementary to front cover aesthetic
- Subtle, muted design that won't compete with text
- Professional book back cover look
- Space for synopsis text in center
- Vertical orientation (portrait)
- NO text or letters - just background artwork/texture
"""
    else:  # spine
        prompt = f"""Create a book spine design for:

Title: "{title}"
Genre: {genre}

Style requirements:
- Very narrow vertical design
- Simple, elegant
- Complementary colors to the cover
- NO text - just visual design elements
"""

    return prompt


def build_chapter_illustration_prompt(
    chapter_number: int,
    chapter_title: str,
    chapter_summary: str,
    genre: str,
    style: str = "artistic illustration"
) -> str:
    """Build a prompt for chapter illustration."""

    prompt = f"""Create an artistic chapter illustration for:

Chapter {chapter_number}: "{chapter_title}"
Scene/Summary: {chapter_summary}
Book Genre: {genre}

Style requirements:
- {style}
- Evocative and atmospheric
- Captures the mood and key elements of the chapter
- Suitable as a chapter header illustration
- Horizontal orientation (landscape)
- NO text or letters in the image
- Professional quality illustration
"""
    return prompt


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
        # Note: Model name may need to be updated based on availability
        imagen = genai.ImageGenerationModel("imagen-3.0-generate-002")

        result = imagen.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="9:16" if height > width else "16:9" if width > height else "1:1",
            safety_filter_level="block_only_high",
            person_generation="allow_adult"
        )

        if result.images:
            # Get the first image
            image = result.images[0]

            # Convert to base64
            image_bytes = image._pil_image
            buffered = io.BytesIO()
            image_bytes.save(buffered, format="PNG")
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

        # Check for common errors
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            # Try fallback to Gemini with image generation
            return await generate_image_gemini_fallback(prompt)

        return {
            "success": False,
            "error": f"Image generation failed: {error_msg}"
        }


async def generate_image_gemini_fallback(prompt: str) -> Dict[str, Any]:
    """
    Fallback: Use Gemini model if Imagen is not available.
    Note: This generates a description, not an actual image.
    For actual image generation, Imagen access is required.
    """
    genai = get_genai()

    if genai is None:
        return {
            "success": False,
            "error": "Google AI SDK not available"
        }

    try:
        # Try using Gemini 2.0 Flash with image generation
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

        # Check if image was generated
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


async def generate_book_cover(
    title: str,
    genre: str,
    description: str,
    themes: list,
    cover_type: str = "front",
    style: str = "professional cinematic book cover"
) -> Dict[str, Any]:
    """Generate a book cover image."""

    prompt = build_cover_prompt(
        title=title,
        genre=genre,
        description=description,
        themes=themes,
        cover_type=cover_type,
        style=style
    )

    # Front covers are portrait, wider aspect ratio
    if cover_type == "front":
        width, height = 768, 1024
    elif cover_type == "back":
        width, height = 768, 1024
    else:  # spine
        width, height = 256, 1024

    result = await generate_image(prompt, width=width, height=height)
    result["prompt_used"] = prompt
    result["cover_type"] = cover_type

    return result


async def generate_chapter_illustration(
    chapter_number: int,
    chapter_title: str,
    chapter_summary: str,
    genre: str,
    style: str = "moody atmospheric illustration"
) -> Dict[str, Any]:
    """Generate a chapter illustration."""

    prompt = build_chapter_illustration_prompt(
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        chapter_summary=chapter_summary,
        genre=genre,
        style=style
    )

    # Chapter illustrations are landscape
    result = await generate_image(prompt, width=1024, height=576)
    result["prompt_used"] = prompt
    result["chapter_number"] = chapter_number

    return result
