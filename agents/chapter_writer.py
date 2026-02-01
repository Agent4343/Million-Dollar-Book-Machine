"""
Chapter Writer Agent

Dedicated agent for writing individual chapters with full context
from the book development pipeline.
"""

from typing import Dict, Any, Optional
from core.orchestrator import ExecutionContext

# Try to import story bible formatter
try:
    from agents.story_bible import format_story_bible_for_chapter
except ImportError:
    def format_story_bible_for_chapter(story_bible, user_constraints=None):
        return "No story bible available."


CHAPTER_WRITING_PROMPT = """You are an expert novelist writing Chapter {chapter_number}: "{chapter_title}".

## CRITICAL: CHARACTER & SETTING CONSISTENCY
You MUST use EXACTLY these names throughout the chapter. NO variations, NO alternatives:

{character_names_block}

**FAILURE TO USE EXACT NAMES WILL RESULT IN CONTINUITY ERRORS.**

---

{story_bible_reference}

## VOICE & STYLE RULES
{voice_specification}

## THIS CHAPTER'S BLUEPRINT
- **Goal**: {chapter_goal}
- **POV**: {pov}
- **Opening Hook**: {opening_hook}
- **Closing Hook**: {closing_hook}
- **Word Target**: {word_target} words

## SCENES TO WRITE
{scenes}

## CHARACTER REFERENCE
{character_reference}

## WORLD RULES
{world_rules}

## PREVIOUS CHAPTER SUMMARY
{previous_summary}

## THEMATIC FOCUS
{thematic_focus}

## INSTRUCTIONS
Write the complete chapter following these guidelines:

1. **Opening**: Begin with the specified opening hook - draw readers in immediately
2. **Scenes**: Execute each scene's goal while maintaining tension and character consistency
3. **Voice**: Maintain the specified narrative voice throughout
4. **Pacing**: Vary sentence length and paragraph density based on scene tension
5. **Dialogue**: Make each character's voice distinct; use subtext
6. **Sensory Details**: Include specific, grounding details (1-2 per paragraph)
7. **Transitions**: Smooth scene transitions that maintain momentum
8. **Closing**: End with the specified closing hook to pull readers forward

Write publication-quality prose. Show, don't tell. Trust the reader.

## OUTPUT FORMAT
Start with:
# Chapter {chapter_number}: {chapter_title}

Then write the chapter prose. Use scene breaks with "* * *" between scenes.
DO NOT use placeholder characters like "?" for the chapter number - use the EXACT number: {chapter_number}

---

BEGIN CHAPTER {chapter_number}: {chapter_title}
"""


async def execute_chapter_writer(
    context: ExecutionContext,
    chapter_number: int,
    quick_mode: bool = False
) -> Dict[str, Any]:
    """
    Write a single chapter with full context from the pipeline.

    Args:
        context: Execution context with all pipeline inputs
        chapter_number: Which chapter to write (1-indexed)
        quick_mode: If True, write a shorter preview (~500 words) for faster generation

    Returns:
        Dict containing the chapter text and metadata
    """
    llm = context.llm_client

    # Get chapter blueprint
    chapter_blueprint = context.inputs.get("chapter_blueprint", {})
    chapter_outline = chapter_blueprint.get("chapter_outline", [])

    # Find the specific chapter
    chapter_data = None
    for ch in chapter_outline:
        if ch.get("number") == chapter_number:
            chapter_data = ch
            break

    if not chapter_data:
        return {
            "error": f"Chapter {chapter_number} not found in blueprint",
            "chapter_number": chapter_number,
            "text": None
        }

    # Format scenes for the prompt
    scenes_text = ""
    for scene in chapter_data.get("scenes", []):
        scenes_text += f"""
### Scene {scene.get('scene_number', '?')}
- **Question**: {scene.get('scene_question', 'N/A')}
- **Characters**: {', '.join(scene.get('characters', []))}
- **Location**: {scene.get('location', 'N/A')}
- **Conflict Type**: {scene.get('conflict_type', 'N/A')}
- **Outcome**: {scene.get('outcome', 'N/A')}
- **Word Target**: {scene.get('word_target', 1500)} words
"""

    # Get character info for the POV character - ensure dict type
    character_arch = context.inputs.get("character_architecture", {})
    if not isinstance(character_arch, dict):
        character_arch = {}
    protagonist = character_arch.get("protagonist_profile", {})
    if not isinstance(protagonist, dict):
        protagonist = {}
    supporting = character_arch.get("supporting_cast", [])
    if not isinstance(supporting, list):
        supporting = []

    character_reference = f"""
**Protagonist**: {protagonist.get('name', 'Protagonist') if isinstance(protagonist, dict) else 'Protagonist'}
- Traits: {', '.join(protagonist.get('traits', []) if isinstance(protagonist, dict) else [])}
- Wound: {protagonist.get('backstory_wound', 'N/A') if isinstance(protagonist, dict) else 'N/A'}
- Want vs Need: {character_arch.get('want_vs_need', {}) if isinstance(character_arch, dict) else {}}

**Supporting Cast**:
"""
    for char in supporting[:3]:  # Limit to avoid token overflow
        if isinstance(char, dict):
            character_reference += f"- {char.get('name', '?')}: {char.get('function', 'N/A')}\n"

    # Get previous chapter summary if available
    previous_summary = "This is the first chapter."
    if chapter_number > 1:
        # Check if we have previous chapters in manuscript
        manuscript = context.project.manuscript
        if isinstance(manuscript, dict):
            prev_chapters = manuscript.get("chapters", [])
            for prev_ch in prev_chapters:
                if isinstance(prev_ch, dict) and prev_ch.get("number") == chapter_number - 1:
                    previous_summary = prev_ch.get("summary", "Previous chapter completed.")
                    break

    # Get thematic focus - ensure dict type
    thematic = context.inputs.get("thematic_architecture", {})
    if not isinstance(thematic, dict):
        thematic = {}
    primary_theme = thematic.get('primary_theme', {})
    if not isinstance(primary_theme, dict):
        primary_theme = {}
    thematic_focus = f"""
- Primary Theme: {primary_theme.get('statement', 'N/A')}
- Thematic Question: {thematic.get('thematic_question', 'N/A')}
"""

    # Adjust word target for quick mode
    word_target = 500 if quick_mode else chapter_data.get("word_target", 3000)

    # Get story bible reference for consistency - ensure dict types
    story_bible = context.inputs.get("story_bible", {})
    if not isinstance(story_bible, dict):
        story_bible = {"raw_content": str(story_bible)} if story_bible else {}
    user_constraints = context.inputs.get("user_constraints", {})
    if not isinstance(user_constraints, dict):
        user_constraints = {}
    story_bible_reference = format_story_bible_for_chapter(story_bible, user_constraints)

    # Build explicit character names block to prevent name drift
    character_names_block = _build_character_names_block(story_bible, character_arch)

    # If user provided their own story_bible or detailed description, add it directly to ensure their vision is preserved
    user_story_content = user_constraints.get("story_bible", "") or user_constraints.get("description", "")
    if user_story_content and len(str(user_story_content)) > 500:
        story_bible_reference = f"""## AUTHOR'S STORY BIBLE (MUST FOLLOW EXACTLY)
The author provided the following canonical story bible. All character names,
settings, relationships, and details MUST match this exactly:

{user_story_content[:5000]}

---

{story_bible_reference}"""

    # Build the prompt
    prompt = CHAPTER_WRITING_PROMPT.format(
        chapter_number=chapter_number,
        chapter_title=chapter_data.get("title", f"Chapter {chapter_number}"),
        character_names_block=character_names_block,
        story_bible_reference=story_bible_reference,
        voice_specification=_format_voice_spec(context.inputs.get("voice_specification", {})),
        chapter_goal=chapter_data.get("chapter_goal", "Advance the story"),
        pov=chapter_data.get("pov", "Protagonist"),
        opening_hook=chapter_data.get("opening_hook", ""),
        closing_hook=chapter_data.get("closing_hook", ""),
        word_target=word_target,
        scenes=scenes_text,
        character_reference=character_reference,
        world_rules=_format_world_rules(context.inputs.get("world_rules", {})),
        previous_summary=previous_summary,
        thematic_focus=thematic_focus
    )

    # Add quick mode instruction
    if quick_mode:
        prompt += "\n\n**IMPORTANT: Write a CONDENSED version (~500 words) focusing on the key moments and dialogue. This is a preview draft.**\n\n"

    if llm:
        # Adjust token limit based on mode
        max_tokens = 1500 if quick_mode else 12000

        try:
            # Generate the chapter
            chapter_text = await llm.generate(
                prompt,
                max_tokens=max_tokens,
                temperature=0.8   # Slightly more creative for prose
            )

            # Handle case where LLM returns dict instead of string
            if isinstance(chapter_text, dict):
                chapter_text = chapter_text.get("text", chapter_text.get("content", str(chapter_text)))

            # Validate we got actual content
            if not chapter_text or len(str(chapter_text)) < 50:
                return {
                    "error": f"LLM returned empty or too short response for chapter {chapter_number}",
                    "chapter_number": chapter_number,
                    "text": None
                }

            # Skip summary in quick mode to save time
            if quick_mode:
                summary = f"Preview of Chapter {chapter_number}"
            else:
                # Generate a summary for context in next chapter
                summary_prompt = f"""Summarize this chapter in 2-3 sentences, focusing on:
1. Key plot developments
2. Character emotional state at end
3. Any cliffhangers or hooks

Chapter text:
{str(chapter_text)[:3000]}...

Summary:"""
                summary = await llm.generate(summary_prompt, max_tokens=200)
                if isinstance(summary, dict):
                    summary = summary.get("summary", str(summary))

            word_count = len(str(chapter_text).split())

            return {
                "chapter_number": chapter_number,
                "title": chapter_data.get("title", f"Chapter {chapter_number}"),
                "text": str(chapter_text),
                "summary": str(summary) if summary else f"Chapter {chapter_number} summary",
                "word_count": word_count,
                "target_word_count": word_target,
                "pov": chapter_data.get("pov", "Unknown"),
                "scenes_written": len(chapter_data.get("scenes", [])),
                "quick_mode": quick_mode
            }
        except Exception as e:
            return {
                "error": f"LLM error for chapter {chapter_number}: {str(e)}",
                "chapter_number": chapter_number,
                "text": None
            }
    else:
        # Demo mode placeholder
        return {
            "chapter_number": chapter_number,
            "title": chapter_data.get("title", f"Chapter {chapter_number}"),
            "text": f"[Chapter {chapter_number} would be generated here with LLM]\n\n{chapter_data.get('opening_hook', '')}",
            "summary": f"Chapter {chapter_number} placeholder summary",
            "word_count": 0,
            "target_word_count": chapter_data.get("word_target", 3000),
            "pov": chapter_data.get("pov", "Unknown"),
            "scenes_written": len(chapter_data.get("scenes", []))
        }


def _build_character_names_block(story_bible: Dict[str, Any], character_arch: Dict[str, Any]) -> str:
    """
    Build an explicit character names block to prevent name drift during chapter generation.
    This creates a clear list of canonical names that the LLM must use.
    """
    # Ensure inputs are dicts
    if not isinstance(story_bible, dict):
        story_bible = {}
    if not isinstance(character_arch, dict):
        character_arch = {}

    lines = []

    # Get protagonist name from character architecture first (most reliable)
    protagonist = character_arch.get("protagonist_profile", {})
    if isinstance(protagonist, dict) and protagonist.get("name"):
        lines.append(f"**PROTAGONIST**: {protagonist.get('name')} (use this exact name)")

    # Get supporting cast from character architecture
    supporting = character_arch.get("supporting_cast", [])
    if isinstance(supporting, list) and supporting:
        lines.append("\n**SUPPORTING CHARACTERS**:")
        for char in supporting[:6]:  # Limit to prevent token overflow
            if isinstance(char, dict):
                name = char.get("name", "")
                function = char.get("function", char.get("role", ""))
                if name:
                    lines.append(f"- {name}: {function}")

    # Also get from story bible character registry for completeness
    char_registry = story_bible.get("character_registry", [])
    if isinstance(char_registry, list) and char_registry and not lines:
        lines.append("**CHARACTERS (use EXACT names)**:")
        for char in char_registry[:8]:
            if isinstance(char, dict):
                name = char.get("canonical_name", char.get("name", ""))
                role = char.get("role", "")
                if name:
                    lines.append(f"- {name}: {role}")
            elif isinstance(char, str):
                lines.append(f"- {char}")

    # Get primary location
    loc_registry = story_bible.get("location_registry", {})
    if isinstance(loc_registry, dict) and loc_registry.get("primary_city"):
        lines.append(f"\n**PRIMARY SETTING**: {loc_registry.get('primary_city')}")

    if not lines:
        return "Use character names as established in the story bible."

    return "\n".join(lines)


def _format_voice_spec(voice_spec: Dict[str, Any]) -> str:
    """Format voice specification for the prompt."""
    if not voice_spec or not isinstance(voice_spec, dict):
        return "Standard third-person narrative voice."

    narrative = voice_spec.get("narrative_voice", {})
    if not isinstance(narrative, dict):
        narrative = {}
    syntax = voice_spec.get("syntax_patterns", {})
    if not isinstance(syntax, dict):
        syntax = {}
    dialogue = voice_spec.get("dialogue_style", {})
    if not isinstance(dialogue, dict):
        dialogue = {}
    style_guide = voice_spec.get("style_guide", {})
    if not isinstance(style_guide, dict):
        style_guide = {}

    dos = style_guide.get('dos', ['Show dont tell'])
    if not isinstance(dos, list):
        dos = ['Show dont tell']
    donts = style_guide.get('donts', ['Avoid info dumps'])
    if not isinstance(donts, list):
        donts = ['Avoid info dumps']

    return f"""
**Narrative Voice**: {narrative.get('pov_type', 'third person')} - {narrative.get('tone', 'neutral')}
**Distance**: {narrative.get('distance', 'moderate')}
**Sentence Style**: {syntax.get('avg_sentence_length', '15-20 words')}, {syntax.get('complexity', 'varied')}
**Dialogue**: {dialogue.get('tag_approach', 'minimal tags')}, {dialogue.get('subtext_level', 'moderate')}

**Do**: {', '.join(dos[:5])}
**Dont**: {', '.join(donts[:5])}
"""


def _format_world_rules(world_rules: Dict[str, Any]) -> str:
    """Format world rules for context."""
    if not world_rules or not isinstance(world_rules, dict):
        return "Contemporary realistic setting."

    physical = world_rules.get("physical_rules", {})
    if not isinstance(physical, dict):
        physical = {}
    social = world_rules.get("social_rules", {})
    if not isinstance(social, dict):
        social = {}

    result = ""
    if physical.get("technology"):
        result += f"**Technology**: {physical.get('technology')}\n"
    if physical.get("geography"):
        result += f"**Setting**: {physical.get('geography')}\n"
    if social.get("norms"):
        norms = social.get("norms", [])
        if isinstance(norms, list):
            result += f"**Social Norms**: {', '.join(str(n) for n in norms[:3])}\n"

    return result or "Contemporary realistic setting."


# Export for registration
CHAPTER_WRITER_EXECUTORS = {
    "chapter_writer": execute_chapter_writer,
}
