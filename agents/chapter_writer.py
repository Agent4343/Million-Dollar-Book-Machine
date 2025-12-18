"""
Chapter Writer Agent

Dedicated agent for writing individual chapters with full context
from the book development pipeline.
"""

from typing import Dict, Any, Optional
from core.orchestrator import ExecutionContext


CHAPTER_WRITING_PROMPT = """You are an expert novelist writing Chapter {chapter_number}: "{chapter_title}".

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

---

BEGIN CHAPTER {chapter_number}:
"""


async def execute_chapter_writer(
    context: ExecutionContext,
    chapter_number: int
) -> Dict[str, Any]:
    """
    Write a single chapter with full context from the pipeline.

    Args:
        context: Execution context with all pipeline inputs
        chapter_number: Which chapter to write (1-indexed)

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

    # Get character info for the POV character
    character_arch = context.inputs.get("character_architecture", {})
    protagonist = character_arch.get("protagonist_profile", {})
    supporting = character_arch.get("supporting_cast", [])

    character_reference = f"""
**Protagonist**: {protagonist.get('name', 'Protagonist')}
- Traits: {', '.join(protagonist.get('traits', []))}
- Wound: {protagonist.get('backstory_wound', 'N/A')}
- Want vs Need: {context.inputs.get('character_architecture', {}).get('want_vs_need', {})}

**Supporting Cast**:
"""
    for char in supporting[:3]:  # Limit to avoid token overflow
        character_reference += f"- {char.get('name', '?')}: {char.get('function', 'N/A')}\n"

    # Get previous chapter summary if available
    previous_summary = "This is the first chapter."
    if chapter_number > 1:
        # Check if we have previous chapters in manuscript
        manuscript = context.project.manuscript
        prev_chapters = manuscript.get("chapters", [])
        for prev_ch in prev_chapters:
            if prev_ch.get("number") == chapter_number - 1:
                previous_summary = prev_ch.get("summary", "Previous chapter completed.")
                break

    # Get thematic focus
    thematic = context.inputs.get("thematic_architecture", {})
    thematic_focus = f"""
- Primary Theme: {thematic.get('primary_theme', {}).get('statement', 'N/A')}
- Thematic Question: {thematic.get('thematic_question', 'N/A')}
"""

    # Build the prompt
    prompt = CHAPTER_WRITING_PROMPT.format(
        chapter_number=chapter_number,
        chapter_title=chapter_data.get("title", f"Chapter {chapter_number}"),
        voice_specification=_format_voice_spec(context.inputs.get("voice_specification", {})),
        chapter_goal=chapter_data.get("chapter_goal", "Advance the story"),
        pov=chapter_data.get("pov", "Protagonist"),
        opening_hook=chapter_data.get("opening_hook", ""),
        closing_hook=chapter_data.get("closing_hook", ""),
        word_target=chapter_data.get("word_target", 3000),
        scenes=scenes_text,
        character_reference=character_reference,
        world_rules=_format_world_rules(context.inputs.get("world_rules", {})),
        previous_summary=previous_summary,
        thematic_focus=thematic_focus
    )

    if llm:
        # Generate the chapter with higher token limit for prose
        chapter_text = await llm.generate(
            prompt,
            max_tokens=12000,  # Chapters need more tokens
            temperature=0.8   # Slightly more creative for prose
        )

        # Generate a summary for context in next chapter
        summary_prompt = f"""Summarize this chapter in 2-3 sentences, focusing on:
1. Key plot developments
2. Character emotional state at end
3. Any cliffhangers or hooks

Chapter text:
{chapter_text[:3000]}...

Summary:"""

        summary = await llm.generate(summary_prompt, max_tokens=200)

        word_count = len(chapter_text.split())

        return {
            "chapter_number": chapter_number,
            "title": chapter_data.get("title", f"Chapter {chapter_number}"),
            "text": chapter_text,
            "summary": summary,
            "word_count": word_count,
            "target_word_count": chapter_data.get("word_target", 3000),
            "pov": chapter_data.get("pov", "Unknown"),
            "scenes_written": len(chapter_data.get("scenes", []))
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


def _format_voice_spec(voice_spec: Dict[str, Any]) -> str:
    """Format voice specification for the prompt."""
    if not voice_spec:
        return "Standard third-person narrative voice."

    narrative = voice_spec.get("narrative_voice", {})
    syntax = voice_spec.get("syntax_patterns", {})
    dialogue = voice_spec.get("dialogue_style", {})
    style_guide = voice_spec.get("style_guide", {})

    return f"""
**Narrative Voice**: {narrative.get('pov_type', 'third person')} - {narrative.get('tone', 'neutral')}
**Distance**: {narrative.get('distance', 'moderate')}
**Sentence Style**: {syntax.get('avg_sentence_length', '15-20 words')}, {syntax.get('complexity', 'varied')}
**Dialogue**: {dialogue.get('tag_approach', 'minimal tags')}, {dialogue.get('subtext_level', 'moderate')}

**Do**: {', '.join(style_guide.get('dos', ['Show don\'t tell'])[:5])}
**Don't**: {', '.join(style_guide.get('donts', ['Avoid info dumps'])[:5])}
"""


def _format_world_rules(world_rules: Dict[str, Any]) -> str:
    """Format world rules for context."""
    if not world_rules:
        return "Contemporary realistic setting."

    physical = world_rules.get("physical_rules", {})
    social = world_rules.get("social_rules", {})

    result = ""
    if physical.get("technology"):
        result += f"**Technology**: {physical.get('technology')}\n"
    if physical.get("geography"):
        result += f"**Setting**: {physical.get('geography')}\n"
    if social.get("norms"):
        norms = social.get("norms", [])
        if isinstance(norms, list):
            result += f"**Social Norms**: {', '.join(norms[:3])}\n"

    return result or "Contemporary realistic setting."


# Export for registration
CHAPTER_WRITER_EXECUTORS = {
    "chapter_writer": execute_chapter_writer,
}
