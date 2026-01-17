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
        # Convert both to int to handle JSON type coercion (string vs int)
        if int(ch.get("number", 0)) == int(chapter_number):
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
    for char in (supporting or [])[:3]:  # Limit to avoid token overflow
        character_reference += f"- {char.get('name', '?')}: {char.get('function', 'N/A')}\n"

    # Get previous chapter summary if available
    previous_summary = "This is the first chapter."
    if chapter_number > 1:
        # Check if we have previous chapters in manuscript
        manuscript = context.project.manuscript
        prev_chapters = manuscript.get("chapters", [])
        for prev_ch in prev_chapters:
            # Convert to int to handle JSON type coercion
            if int(prev_ch.get("number", 0)) == int(chapter_number) - 1:
                previous_summary = prev_ch.get("summary", "Previous chapter completed.")
                break

    # Get thematic focus
    thematic = context.inputs.get("thematic_architecture", {})
    thematic_focus = f"""
- Primary Theme: {thematic.get('primary_theme', {}).get('statement', 'N/A')}
- Thematic Question: {thematic.get('thematic_question', 'N/A')}
"""

    # Adjust word target for quick mode
    word_target = 500 if quick_mode else chapter_data.get("word_target", 3000)

    # Build the prompt
    prompt = CHAPTER_WRITING_PROMPT.format(
        chapter_number=chapter_number,
        chapter_title=chapter_data.get("title", f"Chapter {chapter_number}"),
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

        # Generate the chapter
        chapter_text = await llm.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=0.8   # Slightly more creative for prose
        )

        # Generate summary for context in next chapter (shorter in quick mode)
        summary_prompt = f"""Summarize this chapter in {'1-2' if quick_mode else '2-3'} sentences, focusing on:
1. Key plot developments
2. Character emotional state at end
3. Any cliffhangers or hooks

Chapter text:
{chapter_text[:2000 if quick_mode else 3000]}...

Summary:"""
        summary = await llm.generate(summary_prompt, max_tokens=100 if quick_mode else 200)

        word_count = len(chapter_text.split())

        return {
            "chapter_number": chapter_number,
            "title": chapter_data.get("title", f"Chapter {chapter_number}"),
            "text": chapter_text,
            "summary": summary,
            "word_count": word_count,
            "target_word_count": word_target,
            "pov": chapter_data.get("pov", "Unknown"),
            "scenes_written": len(chapter_data.get("scenes", [])),
            "quick_mode": quick_mode
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
    """Format complete world rules and story bible for chapter context."""
    if not world_rules:
        return "Contemporary realistic setting."

    result = ""

    # Physical Rules
    physical = world_rules.get("physical_rules", {})
    if physical:
        result += "**PHYSICAL WORLD**\n"
        if physical.get("technology"):
            result += f"- Technology: {physical.get('technology')}\n"
        if physical.get("geography"):
            result += f"- Setting/Geography: {physical.get('geography')}\n"
        possibilities = physical.get("possibilities", [])
        if possibilities and isinstance(possibilities, list):
            result += f"- What's Possible: {', '.join(possibilities[:3])}\n"
        impossibilities = physical.get("impossibilities", [])
        if impossibilities and isinstance(impossibilities, list):
            result += f"- What's Impossible: {', '.join(impossibilities[:3])}\n"
        result += "\n"

    # Social Rules
    social = world_rules.get("social_rules", {})
    if social:
        result += "**SOCIAL WORLD**\n"
        if social.get("power_structures"):
            result += f"- Power Structures: {social.get('power_structures')}\n"
        norms = social.get("norms", [])
        if norms and isinstance(norms, list):
            result += f"- Social Norms: {', '.join(norms[:4])}\n"
        taboos = social.get("taboos", [])
        if taboos and isinstance(taboos, list):
            result += f"- Taboos: {', '.join(taboos[:3])}\n"
        if social.get("economics"):
            result += f"- Economics: {social.get('economics')}\n"
        result += "\n"

    # Power Rules
    power = world_rules.get("power_rules", {})
    if power:
        result += "**POWER DYNAMICS**\n"
        if power.get("who_has_power"):
            result += f"- Who Has Power: {power.get('who_has_power')}\n"
        if power.get("how_gained"):
            result += f"- How Power is Gained: {power.get('how_gained')}\n"
        if power.get("how_lost"):
            result += f"- How Power is Lost: {power.get('how_lost')}\n"
        limitations = power.get("limitations", [])
        if limitations and isinstance(limitations, list):
            result += f"- Limitations: {', '.join(limitations[:3])}\n"
        result += "\n"

    # Story Bible (World Bible)
    world_bible = world_rules.get("world_bible", {})
    if world_bible:
        result += "**STORY BIBLE**\n"
        if world_bible.get("relevant_history"):
            result += f"- History: {world_bible.get('relevant_history')}\n"
        if world_bible.get("culture"):
            result += f"- Culture: {world_bible.get('culture')}\n"
        terminology = world_bible.get("terminology", {})
        if terminology and isinstance(terminology, dict):
            terms = [f"{k}: {v}" for k, v in list(terminology.items())[:5]]
            if terms:
                result += f"- Key Terms: {'; '.join(terms)}\n"
        result += "\n"

    # Constraint List (Tension Creators)
    constraints = world_rules.get("constraint_list", [])
    if constraints and isinstance(constraints, list):
        result += "**STORY CONSTRAINTS** (Create Tension)\n"
        for constraint in constraints[:5]:
            result += f"- {constraint}\n"

    return result.strip() or "Contemporary realistic setting."


# Export for registration
CHAPTER_WRITER_EXECUTORS = {
    "chapter_writer": execute_chapter_writer,
}
