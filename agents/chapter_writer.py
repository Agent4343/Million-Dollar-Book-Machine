"""
Chapter Writer Agent

Production-ready agent for writing individual chapters with:
- Full context from the book development pipeline
- Scene-by-scene generation for better control
- Consistency tracking across chapters
- Continuation support for long chapters
- Character voice consistency
"""

from typing import Dict, Any, Optional, List
from core.orchestrator import ExecutionContext
import logging
import json

logger = logging.getLogger(__name__)


# =============================================================================
# CHAPTER WRITING SYSTEM PROMPT
# =============================================================================

CHAPTER_SYSTEM_PROMPT = """You are a professional novelist with decades of experience writing compelling fiction. You write with precision, emotional depth, and narrative momentum. Every sentence serves the story.

Your writing principles:
1. SHOW, don't tell - render emotion through action, dialogue, and sensory detail
2. Every scene has purpose - advances plot, reveals character, or both
3. Dialogue is subtext - what characters say often masks what they mean
4. Sensory grounding - readers need to feel they're IN the scene
5. Tension on every page - even quiet scenes have underlying tension
6. Character consistency - each character has a distinct voice and psychology
7. Trust the reader - don't over-explain or repeat

You write clean, professional prose free of:
- Clichés and overused phrases
- Adverb overuse ("she said angrily")
- Telling emotions instead of showing them
- Purple prose and overwrought descriptions
- Info dumps disguised as dialogue
- Head-hopping in limited POV"""


# =============================================================================
# CHAPTER WRITING PROMPT
# =============================================================================

CHAPTER_WRITING_PROMPT = """## CHAPTER {chapter_number}: "{chapter_title}"

### VOICE RULES (Follow Precisely)
{voice_specification}

### CHAPTER BLUEPRINT
**Goal**: {chapter_goal}
**POV**: {pov}
**Word Target**: {word_target} words
**Opening Hook**: {opening_hook}
**Closing Hook**: {closing_hook}

### SCENES TO WRITE
{scenes}

### CHARACTER QUICK REFERENCE
{character_reference}

### WORLD CONTEXT
{world_rules}

### CONTINUITY FROM PREVIOUS CHAPTER
{previous_summary}

### THEMATIC THREAD
{thematic_focus}

### WRITING INSTRUCTIONS

**OPENING** (First 200-300 words):
- Start in action or with a compelling image
- NO "throat-clearing" - don't warm up, dive in
- Establish POV and location quickly
- Create immediate tension or intrigue

**BODY** (Main chapter):
- Execute each scene's beats while making them feel organic
- Balance action, dialogue, and interiority
- Include 1-2 sensory details per paragraph (but not always visual)
- Make each dialogue exchange do double duty (reveal character AND advance plot)
- Vary paragraph length - use short paragraphs for emphasis
- Use scene breaks (marked with ###) between distinct scenes

**CLOSING** (Final 200-300 words):
- Build to the closing hook
- Leave readers wanting to turn the page
- End on action, revelation, or emotional beat - NOT summary

**POV DISCIPLINE**:
- Stay in {pov}'s head throughout
- Only describe what {pov} can observe/know
- Render {pov}'s thoughts naturally, not as internal monologue dumps
- Emotions through physical sensation, not labels

**DIALOGUE RULES**:
- Use "said" primarily; action beats often better than tags
- Each character sounds different (vocabulary, rhythm, concerns)
- Conversations should have conflict or tension
- Subtext > text (what's NOT said matters)

---

WRITE CHAPTER {chapter_number} NOW. Produce publication-quality prose.

"""


# =============================================================================
# SCENE CONTINUATION PROMPT
# =============================================================================

SCENE_CONTINUATION_PROMPT = """Continue writing the scene. Pick up EXACTLY where the text left off.

### WHAT'S BEEN WRITTEN SO FAR (Last 500 words):
{last_text}

### REMAINING BEATS TO COVER:
{remaining_beats}

### CONTINUITY NOTES:
- Current POV: {pov}
- Current location: {location}
- Characters present: {characters}
- Emotional state: {emotional_state}

### INSTRUCTIONS:
1. Continue SEAMLESSLY from the last sentence
2. Do NOT repeat what's already written
3. Do NOT start a new scene unless indicated
4. Maintain the same voice and tense
5. Cover the remaining beats naturally
6. Target approximately {remaining_words} more words

Continue writing:"""


# =============================================================================
# CHAPTER SUMMARY PROMPT
# =============================================================================

CHAPTER_SUMMARY_PROMPT = """Analyze this chapter and provide a continuity summary for the next chapter's writer.

## Chapter {chapter_number}: {chapter_title}

{chapter_text}

---

Provide a JSON summary with:
{{
    "plot_summary": "2-3 sentences of what happened",
    "character_states": {{
        "protagonist": "Emotional/psychological state at chapter end",
        "other_characters": {{"name": "their state"}}
    }},
    "new_information_revealed": ["List of things reader now knows"],
    "unresolved_tensions": ["What's hanging in the air"],
    "cliffhanger_or_hook": "What the reader is wondering",
    "time_elapsed": "How much story time passed",
    "location_at_end": "Where chapter ended",
    "key_dialogue_or_moments": ["Memorable lines or beats to remember"],
    "foreshadowing_planted": ["Seeds planted for later"],
    "continuity_alerts": ["Things the next chapter must remember"]
}}"""


# =============================================================================
# CONSISTENCY CHECK PROMPT
# =============================================================================

CONSISTENCY_CHECK_PROMPT = """Review this chapter for consistency issues.

## Chapter Content:
{chapter_text}

## Character Bible:
{character_reference}

## World Rules:
{world_rules}

## Previous Chapter Summary:
{previous_summary}

---

Check for and report any issues with:

1. **Character Consistency**
   - Does each character behave according to their established psychology?
   - Are voices distinctive and consistent?
   - Any out-of-character moments?

2. **World Rule Violations**
   - Does anything break established world rules?
   - Technology/magic consistency?
   - Social rules honored?

3. **Continuity Errors**
   - Timeline issues?
   - Location consistency?
   - Character knowledge (do they know things they shouldn't)?
   - Physical continuity (objects, appearances)?

4. **Voice Drift**
   - Does the prose stay in specified voice?
   - POV violations?
   - Tense shifts?

5. **Quality Flags**
   - Clichés detected?
   - Telling instead of showing?
   - Info dumps?

Report in JSON:
{{
    "character_issues": [],
    "world_rule_violations": [],
    "continuity_errors": [],
    "voice_drift": [],
    "quality_flags": [],
    "overall_consistency_score": 90,
    "critical_issues": [],
    "suggested_fixes": []
}}"""


# =============================================================================
# MAIN EXECUTOR
# =============================================================================

async def execute_chapter_writer(
    context: ExecutionContext,
    chapter_number: int,
    quick_mode: bool = False
) -> Dict[str, Any]:
    """
    Write a single chapter with full context from the pipeline.
    
    Features:
    - Scene-by-scene generation for better control
    - Continuation support for long chapters
    - Consistency tracking
    - Quality validation
    
    Args:
        context: Execution context with all pipeline inputs
        chapter_number: Which chapter to write (1-indexed)
        quick_mode: If True, write a shorter preview (~500 words)
    
    Returns:
        Dict containing chapter text, metadata, and quality metrics
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
    
    # Build context components
    voice_spec = _format_voice_specification(context.inputs.get("voice_specification", {}))
    scenes_text = _format_scenes(chapter_data.get("scenes", []))
    character_reference = _build_character_reference(context.inputs.get("character_architecture", {}))
    world_rules = _format_world_rules(context.inputs.get("world_rules", {}))
    previous_summary = _get_previous_chapter_context(context, chapter_number)
    thematic_focus = _format_thematic_focus(context.inputs.get("thematic_architecture", {}))
    
    # Determine word target
    base_word_target = chapter_data.get("word_target", 3500)
    word_target = 500 if quick_mode else base_word_target
    
    # Build the main prompt
    prompt = CHAPTER_WRITING_PROMPT.format(
        chapter_number=chapter_number,
        chapter_title=chapter_data.get("title", f"Chapter {chapter_number}"),
        voice_specification=voice_spec,
        chapter_goal=_format_chapter_goal(chapter_data.get("chapter_goal", {})),
        pov=chapter_data.get("pov", "Protagonist"),
        word_target=word_target,
        opening_hook=_format_hook(chapter_data.get("opening_hook", {})),
        closing_hook=_format_hook(chapter_data.get("closing_hook", {})),
        scenes=scenes_text,
        character_reference=character_reference,
        world_rules=world_rules,
        previous_summary=previous_summary,
        thematic_focus=thematic_focus
    )
    
    if quick_mode:
        prompt += "\n\n**PREVIEW MODE: Write a condensed ~500 word preview hitting key moments.**\n"
    
    if llm:
        # Calculate token budget
        max_tokens = 1500 if quick_mode else min(16000, word_target * 2)
        
        try:
            # Generate the chapter
            chapter_text = await llm.generate(
                prompt,
                system=CHAPTER_SYSTEM_PROMPT,
                max_tokens=max_tokens,
                temperature=0.8
            )
            
            word_count = len(chapter_text.split())
            
            # Check if we need continuation
            if not quick_mode and word_count < word_target * 0.7:
                logger.info(f"Chapter {chapter_number} needs continuation ({word_count}/{word_target} words)")
                chapter_text = await _continue_chapter(
                    llm=llm,
                    current_text=chapter_text,
                    chapter_data=chapter_data,
                    target_words=word_target,
                    voice_spec=voice_spec
                )
                word_count = len(chapter_text.split())
            
            # Generate summary for continuity
            if quick_mode:
                summary = f"Preview of Chapter {chapter_number}"
            else:
                summary = await _generate_continuity_summary(
                    llm=llm,
                    chapter_text=chapter_text,
                    chapter_number=chapter_number,
                    chapter_title=chapter_data.get("title", "")
                )
            
            # Run consistency check (optional, can be skipped in quick mode)
            consistency_report = None
            if not quick_mode and word_count > 1000:
                consistency_report = await _check_consistency(
                    llm=llm,
                    chapter_text=chapter_text,
                    character_reference=character_reference,
                    world_rules=world_rules,
                    previous_summary=previous_summary
                )
            
            return {
                "chapter_number": chapter_number,
                "title": chapter_data.get("title", f"Chapter {chapter_number}"),
                "text": chapter_text,
                "summary": summary,
                "word_count": word_count,
                "target_word_count": word_target,
                "target_met": word_count >= word_target * 0.85,
                "pov": chapter_data.get("pov", "Unknown"),
                "scenes_written": len(chapter_data.get("scenes", [])),
                "quick_mode": quick_mode,
                "consistency_report": consistency_report,
                "quality_score": consistency_report.get("overall_consistency_score", 85) if consistency_report else 85
            }
            
        except Exception as e:
            logger.error(f"Chapter {chapter_number} generation failed: {e}")
            return {
                "chapter_number": chapter_number,
                "title": chapter_data.get("title", f"Chapter {chapter_number}"),
                "text": f"[Generation failed: {e}]",
                "summary": "Generation failed",
                "word_count": 0,
                "error": str(e)
            }
    
    else:
        # Demo mode - return placeholder
        return {
            "chapter_number": chapter_number,
            "title": chapter_data.get("title", f"Chapter {chapter_number}"),
            "text": _generate_placeholder_chapter(chapter_number, chapter_data),
            "summary": f"Chapter {chapter_number} placeholder summary",
            "word_count": 0,
            "target_word_count": word_target,
            "pov": chapter_data.get("pov", "Unknown"),
            "scenes_written": len(chapter_data.get("scenes", [])),
            "demo_mode": True
        }


# =============================================================================
# CONTINUATION SUPPORT
# =============================================================================

async def _continue_chapter(
    llm,
    current_text: str,
    chapter_data: Dict[str, Any],
    target_words: int,
    voice_spec: str,
    max_continuations: int = 3
) -> str:
    """Continue generating chapter content until word target is met."""
    
    chapter_text = current_text
    continuations = 0
    
    while len(chapter_text.split()) < target_words * 0.85 and continuations < max_continuations:
        continuations += 1
        current_words = len(chapter_text.split())
        remaining_words = target_words - current_words
        
        logger.info(f"Continuation {continuations}: {current_words} words, need ~{remaining_words} more")
        
        # Get last portion of text for context
        last_text = " ".join(chapter_text.split()[-500:])
        
        # Determine remaining beats based on what's written
        scenes = chapter_data.get("scenes", [])
        remaining_beats = []
        for scene in scenes:
            beats = scene.get("beat_outline", [])
            remaining_beats.extend(beats)
        
        continuation_prompt = SCENE_CONTINUATION_PROMPT.format(
            last_text=last_text,
            remaining_beats="\n".join(remaining_beats[-5:]) if remaining_beats else "Continue to chapter conclusion",
            pov=chapter_data.get("pov", "Protagonist"),
            location=scenes[-1].get("location", "Current location") if scenes else "Current location",
            characters=", ".join(scenes[-1].get("characters", [])) if scenes else "Current characters",
            emotional_state="Building toward chapter climax",
            remaining_words=remaining_words
        )
        
        try:
            continuation = await llm.generate(
                continuation_prompt,
                system=CHAPTER_SYSTEM_PROMPT,
                max_tokens=min(8000, remaining_words * 2),
                temperature=0.8
            )
            
            chapter_text = chapter_text + "\n\n" + continuation
            
        except Exception as e:
            logger.warning(f"Continuation {continuations} failed: {e}")
            break
    
    return chapter_text


# =============================================================================
# SUMMARY GENERATION
# =============================================================================

async def _generate_continuity_summary(
    llm,
    chapter_text: str,
    chapter_number: int,
    chapter_title: str
) -> Dict[str, Any]:
    """Generate a structured summary for continuity tracking."""
    
    prompt = CHAPTER_SUMMARY_PROMPT.format(
        chapter_number=chapter_number,
        chapter_title=chapter_title,
        chapter_text=chapter_text[:6000]  # Limit for token efficiency
    )
    
    try:
        result = await llm.generate(
            prompt,
            response_format="json",
            max_tokens=1000,
            temperature=0.3
        )
        return result
    except Exception as e:
        logger.warning(f"Summary generation failed: {e}")
        return {
            "plot_summary": f"Chapter {chapter_number} completed",
            "character_states": {},
            "unresolved_tensions": []
        }


# =============================================================================
# CONSISTENCY CHECKING
# =============================================================================

async def _check_consistency(
    llm,
    chapter_text: str,
    character_reference: str,
    world_rules: str,
    previous_summary: str
) -> Dict[str, Any]:
    """Run consistency check on generated chapter."""
    
    prompt = CONSISTENCY_CHECK_PROMPT.format(
        chapter_text=chapter_text[:5000],  # Limit for efficiency
        character_reference=character_reference,
        world_rules=world_rules,
        previous_summary=previous_summary
    )
    
    try:
        result = await llm.generate(
            prompt,
            response_format="json",
            max_tokens=1000,
            temperature=0.3
        )
        return result
    except Exception as e:
        logger.warning(f"Consistency check failed: {e}")
        return {
            "overall_consistency_score": 80,
            "critical_issues": [],
            "suggested_fixes": []
        }


# =============================================================================
# FORMATTING HELPERS
# =============================================================================

def _format_voice_specification(voice_spec: Dict[str, Any]) -> str:
    """Format voice specification for the prompt."""
    if not voice_spec:
        return "Standard third-person limited, past tense, close narrative distance."
    
    narrative = voice_spec.get("narrative_voice", {})
    prose = voice_spec.get("prose_style", {})
    tense = voice_spec.get("tense_rules", {})
    dialogue = voice_spec.get("dialogue_style", {})
    
    return f"""**POV**: {narrative.get('pov_type', 'Third person limited')}
**Tense**: {tense.get('primary', 'Past')}
**Distance**: {narrative.get('distance', 'Close')}
**Tone**: {narrative.get('tone', 'Engaging')}
**Sentences**: {prose.get('sentence_length', {}).get('average', '15-20 words')}, {prose.get('rhythm', 'varied')}
**Dialogue Tags**: {dialogue.get('tag_approach', 'Minimal - said preferred, action beats often better')}"""


def _format_scenes(scenes: List[Dict[str, Any]]) -> str:
    """Format scenes into detailed instructions."""
    if not scenes:
        return "Write a cohesive chapter advancing the plot."
    
    scenes_text = ""
    for scene in scenes:
        beats = scene.get("beat_outline", ["Scene unfolds naturally"])
        beats_formatted = "\n  ".join(f"• {beat}" for beat in beats)
        
        scenes_text += f"""
### Scene {scene.get('scene_number', '?')}
**Question at stake**: {scene.get('scene_question', 'What happens next?')}
**Location**: {scene.get('location', 'Current setting')}
**Characters**: {', '.join(scene.get('characters', ['Protagonist']))}
**Scene Type**: {scene.get('scene_type', 'action')} | **Conflict**: {scene.get('conflict_type', 'external')}
**Target**: ~{scene.get('word_target', 1500)} words
**Beats to hit**:
  {beats_formatted}
**Outcome**: {scene.get('outcome', 'progression')}
"""
    return scenes_text


def _build_character_reference(char_arch: Dict[str, Any]) -> str:
    """Build compact character reference for writing context."""
    if not char_arch:
        return "Use established character traits and voice."
    
    protag = char_arch.get("protagonist_profile", {})
    identity = protag.get("identity", {})
    psych = protag.get("psychological_core", {})
    voice = protag.get("voice", {})
    
    antagonist = char_arch.get("antagonist_profile", {})
    supporting = char_arch.get("supporting_cast", [])
    
    ref = f"""**PROTAGONIST: {identity.get('name', 'Protagonist')}**
- Core: {psych.get('core_desire', 'Unknown desire')} vs {psych.get('core_fear', 'unknown fear')}
- Wound: {psych.get('core_wound', 'Past trauma')}
- Strength: {psych.get('core_strength', 'Determination')} | Flaw: {psych.get('core_flaw', 'Blind spot')}
- Voice: {voice.get('speech_patterns', 'Natural')}, {voice.get('humor', 'Varied')}
"""
    
    if antagonist:
        antag_id = antagonist.get("identity", {})
        ref += f"""
**ANTAGONIST: {antag_id.get('name', 'Antagonist')}**
- Want: {antagonist.get('psychology', {}).get('want', 'Opposition')}
- Belief: {antagonist.get('psychology', {}).get('belief_system', 'Different worldview')}
"""
    
    for char in supporting[:3]:
        ref += f"""
**{char.get('name', 'Supporting').upper()}** ({char.get('function', 'Support')}): {char.get('memorable_trait', 'Distinctive')}"""
    
    return ref


def _format_world_rules(world_rules: Dict[str, Any]) -> str:
    """Format world rules for context."""
    if not world_rules:
        return "Contemporary realistic setting. Modern technology. Social norms apply."
    
    physical = world_rules.get("physical_rules", {})
    social = world_rules.get("social_rules", {})
    sensory = world_rules.get("world_bible", {}).get("sensory_palette", {})
    
    result = []
    
    if physical.get("technology_magic_level"):
        tech = physical["technology_magic_level"]
        result.append(f"**Tech Level**: {tech.get('description', 'Modern')}")
    
    if physical.get("geography"):
        geo = physical["geography"]
        result.append(f"**Setting**: {geo.get('primary_setting', 'Urban')}")
    
    if social.get("norms"):
        norms = social["norms"][:3] if isinstance(social["norms"], list) else [social["norms"]]
        result.append(f"**Social Rules**: {', '.join(norms)}")
    
    if sensory:
        result.append(f"**Sensory**: Visual-{sensory.get('visual', 'varied')}, Sounds-{sensory.get('auditory', 'ambient')}")
    
    return "\n".join(result) if result else "Standard contemporary setting."


def _get_previous_chapter_context(context: ExecutionContext, chapter_number: int) -> str:
    """Get context from previous chapter for continuity."""
    if chapter_number <= 1:
        return "This is the opening chapter. No previous context."
    
    manuscript = context.project.manuscript
    prev_chapters = manuscript.get("chapters", [])
    
    for prev_ch in prev_chapters:
        if prev_ch.get("number") == chapter_number - 1:
            summary = prev_ch.get("summary", {})
            if isinstance(summary, dict):
                return f"""**Previous Chapter Summary**: {summary.get('plot_summary', 'Unknown')}
**Character State**: {json.dumps(summary.get('character_states', {}), indent=2)[:500]}
**Unresolved**: {', '.join(summary.get('unresolved_tensions', ['None stated'])[:3])}
**Hook**: {summary.get('cliffhanger_or_hook', 'Story continues')}"""
            else:
                return f"**Previous Chapter**: {summary}"
    
    return "Previous chapter context not available. Maintain narrative flow."


def _format_thematic_focus(thematic: Dict[str, Any]) -> str:
    """Format thematic focus for the chapter."""
    if not thematic:
        return "Weave theme organically through character choices and consequences."
    
    primary = thematic.get("primary_theme", {})
    question = thematic.get("thematic_question", "")
    
    return f"""**Theme**: {primary.get('statement', 'To be explored through action')}
**Question**: {question or 'What does the story argue?'}
Remember: Theme emerges through character ACTION and CHOICE, not exposition."""


def _format_chapter_goal(goal: Any) -> str:
    """Format chapter goal."""
    if isinstance(goal, dict):
        return f"{goal.get('must_happen', 'Advance the plot')} — {goal.get('state_change', 'Character develops')}"
    return str(goal) if goal else "Advance the story"


def _format_hook(hook: Any) -> str:
    """Format hook information."""
    if isinstance(hook, dict):
        return f"{hook.get('approach', hook.get('description', 'Create tension'))}"
    return str(hook) if hook else "Create compelling momentum"


def _generate_placeholder_chapter(chapter_number: int, chapter_data: Dict[str, Any]) -> str:
    """Generate placeholder content for demo mode."""
    title = chapter_data.get("title", f"Chapter {chapter_number}")
    scenes = chapter_data.get("scenes", [])
    
    placeholder = f"""# Chapter {chapter_number}: {title}

[This chapter would be generated by the LLM with the following structure:]

**Opening Hook**: {_format_hook(chapter_data.get('opening_hook', {}))}

"""
    
    for scene in scenes:
        placeholder += f"""
## Scene {scene.get('scene_number', '?')}
**Question**: {scene.get('scene_question', 'What happens?')}
**Location**: {scene.get('location', 'Setting')}
**Characters**: {', '.join(scene.get('characters', ['Protagonist']))}
**Beats**: {' → '.join(scene.get('beat_outline', ['Beginning', 'Middle', 'End'])[:3])}

[Scene content would be generated here - approximately {scene.get('word_target', 1500)} words]

"""
    
    placeholder += f"""
**Closing Hook**: {_format_hook(chapter_data.get('closing_hook', {}))}

---
*Word Target: {chapter_data.get('word_target', 3500)} words*
*POV: {chapter_data.get('pov', 'Protagonist')}*
"""
    
    return placeholder


# =============================================================================
# BATCH GENERATION HELPER
# =============================================================================

async def generate_chapters_batch(
    context: ExecutionContext,
    chapter_numbers: List[int],
    quick_mode: bool = False
) -> List[Dict[str, Any]]:
    """
    Generate multiple chapters in sequence with continuity.
    
    Args:
        context: Execution context
        chapter_numbers: List of chapter numbers to generate
        quick_mode: If True, generate short previews
    
    Returns:
        List of chapter results
    """
    results = []
    
    for chapter_num in chapter_numbers:
        logger.info(f"Generating chapter {chapter_num} of {len(chapter_numbers)}")
        
        result = await execute_chapter_writer(
            context=context,
            chapter_number=chapter_num,
            quick_mode=quick_mode
        )
        
        results.append(result)
        
        # Update manuscript with result for continuity
        if result.get("text") and not result.get("error"):
            if "chapters" not in context.project.manuscript:
                context.project.manuscript["chapters"] = []
            
            # Update or add chapter
            existing = False
            for i, ch in enumerate(context.project.manuscript["chapters"]):
                if ch.get("number") == chapter_num:
                    context.project.manuscript["chapters"][i] = result
                    existing = True
                    break
            
            if not existing:
                context.project.manuscript["chapters"].append(result)
    
    return results


# =============================================================================
# EXPORT
# =============================================================================

CHAPTER_WRITER_EXECUTORS = {
    "chapter_writer": execute_chapter_writer,
    "chapters_batch": generate_chapters_batch,
}
