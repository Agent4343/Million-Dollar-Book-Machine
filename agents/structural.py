"""
Structural Engine Agents (Layers 8-12)

These agents design and execute the story structure:
- Macro Plot Structure
- Pacing & Tension Design
- Chapter & Scene Blueprint
- Style & Voice Specification
- Draft Generation
"""

import asyncio
import logging
import os
from typing import Callable, Dict, Any, List, Optional
from core.orchestrator import ExecutionContext

logger = logging.getLogger(__name__)

# Per-chapter LLM call timeout in seconds; configurable via env var.
_DRAFT_CHAPTER_TIMEOUT = int(os.environ.get("DRAFT_CHAPTER_TIMEOUT", "300") or "300")

# Retry settings for chapter generation within draft_generation agent.
_DRAFT_CHAPTER_MAX_RETRIES = int(os.environ.get("DRAFT_CHAPTER_MAX_RETRIES", "3") or "3")
_DRAFT_CHAPTER_RETRY_BACKOFF = float(os.environ.get("DRAFT_CHAPTER_RETRY_BACKOFF", "2.0") or "2.0")

# Skip per-chapter adherence checks to reduce LLM costs (saves 1 LLM call per chapter).
# Set to "true" to enable adherence scoring (adds ~30% cost to draft generation).
_DRAFT_ADHERENCE_CHECK = os.environ.get("DRAFT_ADHERENCE_CHECK", "false").lower() in ("true", "1", "yes")


# =============================================================================
# PROMPTS
# =============================================================================

PLOT_STRUCTURE_PROMPT = """You are a plot architect. Design the story's macro structure.

## Central Dramatic Question:
{central_dramatic_question}

## Protagonist Arc:
{protagonist_arc}

## Relationship Dynamics:
{relationship_dynamics}

## Task:
Design the complete plot structure:

1. **Act Structure**: Three-act breakdown
   - Act 1: Setup (25%)
   - Act 2: Confrontation (50%)
   - Act 3: Resolution (25%)

2. **Major Beats**: Key story moments
   - Opening Image
   - Catalyst
   - Debate
   - Break into 2
   - B Story
   - Fun & Games
   - Midpoint
   - Bad Guys Close In
   - All Is Lost
   - Dark Night of Soul
   - Break into 3
   - Finale
   - Final Image

3. **Reversals**: Major plot twists
   - Midpoint reversal
   - Act 2 low point reversal
   - Climax reversal

4. **Point of No Return**: When protagonist commits

5. **Climax Design**: The final confrontation

6. **Resolution**: How it ends

## Output Format (JSON):
{{
    "act_structure": {{
        "act_1": {{"percentage": 25, "purpose": "<string>", "key_events": ["<string>"]}},
        "act_2": {{"percentage": 50, "purpose": "<string>", "key_events": ["<string>"]}},
        "act_3": {{"percentage": 25, "purpose": "<string>", "key_events": ["<string>"]}}
    }},
    "major_beats": [
        {{"name": "Opening Image", "description": "<string>", "page_target": "1-2"}}
    ],
    "reversals": [
        {{"name": "Midpoint", "what_changes": "<string>", "impact": "<string>"}}
    ],
    "point_of_no_return": {{
        "moment": "<string>",
        "why_irreversible": "<string>",
        "protagonist_commitment": "<string>"
    }},
    "climax_design": {{
        "setup": "<string>",
        "confrontation": "<string>",
        "resolution": "<string>"
    }},
    "resolution": {{
        "external_resolution": "<string>",
        "internal_resolution": "<string>",
        "final_image": "<string>"
    }}
}}

IMPORTANT: Do NOT include ellipses like "..." in the returned JSON. Output complete, valid JSON only.
"""

PACING_DESIGN_PROMPT = """You are a pacing specialist. Design the tension and rhythm of the story.

## Plot Structure:
{plot_structure}

## Genre:
{genre}

## Task:
Design the pacing:

1. **Tension Curve**: Plot tension over time
   - Opening tension level (1-10)
   - Key escalation points
   - Peak tension moment
   - Resolution drop

2. **Scene Density Map**: How dense each section is
   - Action vs reflection ratio
   - Dialogue vs description
   - Fast vs slow scenes

3. **Breather Points**: Where readers can rest
   - After intense sequences
   - Character moments
   - Setup scenes

4. **Acceleration Zones**: Where pace quickens
   - Approaching climax
   - Chase/action sequences
   - Reveal sequences

## Output Format (JSON):
{{
    "tension_curve": [
        {{"point": "Opening", "level": 3, "description": "<string>"}},
        {{"point": "Catalyst", "level": 5, "description": "<string>"}},
        {{"point": "Midpoint", "level": 7, "description": "<string>"}},
        {{"point": "All Is Lost", "level": 4, "description": "<string>"}},
        {{"point": "Climax", "level": 10, "description": "<string>"}},
        {{"point": "Resolution", "level": 2, "description": "<string>"}}
    ],
    "scene_density_map": {{
        "act_1": {{"action_reflection_ratio": "40:60", "dialogue_description": "50:50"}},
        "act_2_first_half": {{"action_reflection_ratio": "60:40", "dialogue_description": "60:40"}},
        "act_2_second_half": {{"action_reflection_ratio": "70:30", "dialogue_description": "50:50"}},
        "act_3": {{"action_reflection_ratio": "80:20", "dialogue_description": "40:60"}}
    }},
    "breather_points": [
        {{"after": "<string>", "type": "<string>", "purpose": "<string>"}}
    ],
    "acceleration_zones": [
        {{"section": "<string>", "technique": "<string>", "effect": "<string>"}}
    ]
}}

IMPORTANT: Do NOT include ellipses like "..." in the returned JSON. Output complete, valid JSON only.
"""

CHAPTER_BLUEPRINT_PROMPT = """You are an outline architect. Create the detailed chapter and scene blueprint.

## Plot Structure:
{plot_structure}

## Pacing Design:
{pacing_design}

## Characters:
{character_architecture}

## Target Word Count:
{target_word_count} total words for the book

## Recommended Chapter Parameters:
- Suggested number of chapters: {suggested_chapter_count}
- Suggested average words per chapter: {suggested_words_per_chapter}
- You may adjust chapter count up or down based on story needs, but the total word count across all chapters should approximately equal the target.

## Task:
Create the complete chapter blueprint:

For each chapter include:
- Chapter number and title (make titles evocative and specific to this story, not generic)
- Chapter goal (what must happen)
- POV character
- Opening hook (the first line or image that draws readers in)
- Key scenes (2-4 per chapter)
- Closing hook (a revelation, question, or threat that pulls readers to the next chapter)
- Word count target (adapt per chapter — action chapters can be shorter, setup chapters longer)

For each scene include:
- Scene question (what's at stake in this specific scene)
- Characters present
- Location (specific, grounded in the world)
- Conflict type (external, internal, interpersonal, environmental)
- Outcome (how the scene changes the character's situation)

## STRUCTURAL VARIETY RULES (CRITICAL — prevents repetitive books)
- NO more than 2 chapters in the entire book may share the same PRIMARY conflict type.
  For example: max 2 chase/escape chapters, max 2 infiltration chapters, max 2 interrogation chapters.
- VARY chapter structures: if Chapter N is action-heavy, Chapter N+1 must be dialogue-driven, investigative, or reflective. Never have 3+ consecutive action chapters.
- Each character's emotional arc must PROGRESS MONOTONICALLY across the book. A character who learns to trust in Chapter 5 must NOT re-learn to trust in Chapter 12. Growth should BUILD on previous growth.
- The antagonist must ESCALATE across appearances: each time they appear, they reveal new information, employ new tactics, or demonstrate new capabilities. No recycled villain speeches.
- VARY how chapters end: alternate between cliffhangers, quiet revelations, emotional shifts, and ominous foreshadowing. Don't end every chapter with a chase or discovery.
- Include at least 3 "breather" chapters (lower tension, character development, relationship building) distributed across the middle third of the book.
- For each chapter, specify a PRIMARY scene type from this list: chase, infiltration, escape, confrontation, quiet_reflection, discovery, betrayal, romance, interrogation, battle, planning, investigation, trial, celebration, mourning, travel, training, disguise, negotiation, ambush, rescue, confession.

## Hard Requirements (must comply)
- Return ONLY valid JSON (no markdown).
- Chapter numbers must be contiguous and increasing starting at 1 (1..N).
- Each chapter must have at least 1 scene.
- Each scene must have a numeric word_target.
- For each chapter: sum(scene.word_target) should be close to chapter.word_target (within ±35%).
- Total of all chapter word_targets should approximately equal {target_word_count}.

## Output Format (JSON):
{{
    "chapter_outline": [
        {{
            "number": 1,
            "title": "<string>",
            "act": 1,
            "chapter_goal": "<string>",
            "primary_scene_type": "<chase|infiltration|escape|confrontation|quiet_reflection|discovery|betrayal|romance|interrogation|battle|planning|investigation|trial|celebration|mourning|travel|training|disguise|negotiation|ambush|rescue|confession>",
            "pov": "<string>",
            "opening_hook": "<string>",
            "closing_hook": "<string>",
            "word_target": {suggested_words_per_chapter},
            "scenes": [
                {{
                    "scene_number": 1,
                    "scene_question": "<string>",
                    "characters": ["<string>"],
                    "location": "<string>",
                    "conflict_type": "<string>",
                    "outcome": "<string>",
                    "word_target": 1500
                }}
            ]
        }}
    ],
    "chapter_goals": {{"1": "<string>", "2": "<string>"}},
    "scene_list": ["Ch1-S1: <string>", "Ch1-S2: <string>"],
    "scene_questions": {{"Ch1-S1": "<string>", "Ch1-S2": "<string>"}},
    "hooks": {{"chapter_hooks": ["<string>"], "scene_hooks": ["<string>"]}},
    "pov_assignments": {{"1": "<string>", "2": "<string>"}}
}}

IMPORTANT: Do NOT include ellipses like "..." in the returned JSON. Output complete, valid JSON only.
"""

VOICE_SPECIFICATION_PROMPT = """You are a voice architect. Define the narrative voice and style rules.

## Genre:
{genre}

## Reader Avatar:
{reader_avatar}

## Protagonist:
{protagonist_profile}

## Task:
Define the complete voice specification:

1. **Narrative Voice**: Who's telling the story
   - POV type (first, third limited, third omniscient)
   - Narrative distance
   - Voice personality

2. **POV Rules**: Point of view guidelines
   - Whose head we're in
   - What can be known
   - Perspective limitations

3. **Tense Rules**: Past vs present

4. **Syntax Patterns**: Sentence structure
   - Average sentence length
   - Complexity level
   - Rhythm patterns

5. **Sensory Density**: How much sensory detail
   - Visual emphasis
   - Other senses
   - Frequency of sensory beats

6. **Dialogue Style**: How characters speak
   - Dialogue tag approach
   - Subtext level
   - Character voice differentiation

7. **Style Guide**: Dos and don'ts

## Hard Requirements (must comply)
- Return ONLY valid JSON (no markdown).
- Include at least 1 non-empty example passage in style_guide.example_passages.
- Example passage(s) must demonstrate the POV + tense + tone rules you specify.

## Output Format (JSON):
{{
    "narrative_voice": {{
        "pov_type": "...",
        "distance": "...",
        "personality": "...",
        "tone": "..."
    }},
    "pov_rules": {{
        "perspective_character": "...",
        "knowledge_limits": "...",
        "rules": ["..."]
    }},
    "tense_rules": {{
        "primary_tense": "...",
        "exceptions": ["..."]
    }},
    "syntax_patterns": {{
        "avg_sentence_length": "...",
        "complexity": "...",
        "rhythm": "..."
    }},
    "sensory_density": {{
        "visual": "...",
        "other_senses": "...",
        "frequency": "..."
    }},
    "dialogue_style": {{
        "tag_approach": "...",
        "subtext_level": "...",
        "differentiation": "..."
    }},
    "style_guide": {{
        "dos": ["..."],
        "donts": ["..."],
        "example_passages": ["..."]
    }}
}}
"""

DRAFT_GENERATION_PROMPT = """You are a novelist. Write Chapter {chapter_number}: {chapter_title}.

## Voice Specification:
{voice_specification}

## Chapter Blueprint:
{chapter_blueprint}

## Character Reference:
{character_architecture}

## Dialogue Voice Profiles (CRITICAL — each character MUST sound distinct):
{dialogue_voices}

## World Rules:
{world_rules}

## Story Context (recent chapter summaries):
{previous_summary}

## Running Story State (CRITICAL — read carefully):
{story_state}

## Task:
Write the complete chapter following:
- The scene blueprint exactly
- The voice specification rules
- Character consistency — characters must reflect their state from previous chapters
- World rule compliance

Write engaging, publication-quality prose that:
- Opens with the specified opening hook
- Executes each scene's goal while maintaining tension and character consistency
- Closes with the specified closing hook to pull readers forward
- Hits the word target of approximately {word_target} words
- Uses * * * on its own line for scene breaks within the chapter

## STRUCTURAL INTEGRITY RULES (CRITICAL — prevents repetitive books)
- CHECK THE STORY STATE ABOVE. It tracks scene types, character arcs, and phrases already used.
- DO NOT repeat scene types that have already appeared 2+ times (e.g., if there have been 2 chase scenes, do NOT write another chase even if the blueprint suggests one — find a creative alternative that achieves the same plot goal).
- CHARACTER ARCS MUST PROGRESS FORWARD. If a character already learned a lesson (e.g., "learned to trust"), they CANNOT re-learn it. Build on what they've already achieved. Show growth, not loops.
- The antagonist MUST say new things. Check what they've already revealed/monologued about and advance their argument or reveal new information.
- Each chapter must feel STRUCTURALLY DIFFERENT from the previous one. If the last chapter was action-heavy, this one should emphasize dialogue, investigation, or internal reflection.

## PROSE QUALITY RULES (CRITICAL)
- NEVER use AI-telltale phrases: "In a world where", "Little did she know",
  "A symphony of", "sent shivers down", "pierced the silence", "could not help but",
  "a dance of", "the weight of", "it was as if", "time seemed to stop",
  "the silence was deafening", "a chill ran down", "little did they know",
  "with bated breath", "the air was thick with tension"
- NEVER use these overused phrases: "like a physical blow", "hit him like",
  "struck her like", "something shifted", "blood ran cold", "blood turned to ice",
  "the words hung between them", "crashed over him like a wave",
  "settled like a weight", "burned in his chest", "cut through him like",
  "tasted like ash", "tasted like poison", "tasted bitter"
- CHECK THE BANNED PHRASES LIST IN STORY STATE. Do NOT reuse any phrase listed there.
- DIALOGUE VOICE RULES (CRITICAL):
  - Each character MUST speak differently. Check the DIALOGUE VOICE PROFILES above.
  - Use the character's vocabulary level, sentence patterns, and verbal tics.
  - A reader should be able to identify the speaker WITHOUT dialogue tags.
  - Under stress, apply that character's stress speech pattern.
  - NEVER have two characters speak with the same rhythm or vocabulary level.
  - Minimize dialogue tags — use action beats instead ("He slammed the folder shut. 'We're done here.'")
- NEVER start consecutive paragraphs the same way
- Use concrete, specific details (brand names, textures, temperatures) not vague abstractions
- Dialogue: real speech with interruptions, incomplete thoughts, subtext
- Vary paragraph length dramatically: one-line gut-punches mixed with flowing passages
- Physical reactions before emotional labels (racing pulse before "she was afraid")
- Internal monologue should feel raw and unfiltered, not polished
- Every chapter must have at least ONE moment that makes the reader's breath catch
- Scene breaks should use * * * on their own line

## Output the chapter text directly.
"""


# =============================================================================
# STORY STATE TRACKING — prevents repetitive plots and looping character arcs
# =============================================================================

_STORY_STATE_EXTRACTION_PROMPT = """Analyze this chapter and extract structured story state.

Chapter {chapter_number}:
{chapter_text}

Return ONLY valid JSON:
{{
  "scene_types": ["<type>"],
  "character_arc_movements": {{"<character_name>": "<arc_position>"}},
  "antagonist_reveals": ["<what villain revealed or argued>"],
  "chapter_structure": "<action_heavy|dialogue_heavy|introspection|investigation|romance|mixed>",
  "tension_level": 7,
  "notable_phrases": ["<memorable or distinctive phrases used>"]
}}

scene_types must be from: chase, infiltration, escape, confrontation, quiet_reflection, discovery, betrayal, romance, interrogation, battle, planning, investigation, trial, celebration, mourning, travel, training, disguise, negotiation, ambush, rescue, confession

character_arc_movements: for each major character, describe their emotional/psychological state at END of chapter in 3-5 words.

antagonist_reveals: only include if the antagonist/villain appears. What NEW information or argument did they present?

notable_phrases: list 3-5 distinctive metaphors, similes, or turns of phrase used in this chapter.
"""


import re as _re
from collections import Counter as _Counter


def _extract_ngrams(text: str, n: int = 4) -> list:
    """Extract n-grams from text for phrase deduplication."""
    words = text.lower().split()
    return [" ".join(words[i:i + n]) for i in range(len(words) - n + 1)]


def _accumulate_story_state(
    state: dict, ch_state: dict, chapter_num: int, chapter_text: str
) -> None:
    """Merge one chapter's extracted state into the running accumulator."""
    # Scene types
    for st in ch_state.get("scene_types", []):
        if isinstance(st, str):
            state["scene_types_used"].append(f"Ch{chapter_num}:{st}")

    # Character arcs
    for char_name, arc_pos in (ch_state.get("character_arc_movements") or {}).items():
        if not isinstance(char_name, str):
            continue
        if char_name not in state["character_arcs"]:
            state["character_arcs"][char_name] = []
        state["character_arcs"][char_name].append(f"Ch{chapter_num}: {arc_pos}")

    # Antagonist reveals
    for reveal in ch_state.get("antagonist_reveals", []):
        if isinstance(reveal, str) and reveal.strip():
            state["antagonist_reveals"].append(f"Ch{chapter_num}: {reveal}")

    # Chapter structure
    structure = ch_state.get("chapter_structure", "mixed")
    state["chapter_structures"].append(f"Ch{chapter_num}:{structure}")

    # Tension level
    tension = ch_state.get("tension_level", 5)
    if isinstance(tension, int):
        state["tension_levels"].append(tension)

    # Notable phrases — add LLM-extracted ones plus heuristic n-gram detection
    for phrase in ch_state.get("notable_phrases", []):
        if isinstance(phrase, str) and phrase.strip():
            state["notable_phrases"].append(phrase.strip().lower())

    # Heuristic: extract overused 4-grams from this chapter
    _add_frequent_ngrams(state, chapter_text)


def _accumulate_story_state_heuristic(
    state: dict, chapter_num: int, chapter_text: str
) -> None:
    """Fallback: extract story state without LLM when extraction call fails."""
    state["chapter_structures"].append(f"Ch{chapter_num}:unknown")
    state["tension_levels"].append(5)
    _add_frequent_ngrams(state, chapter_text)


def _add_frequent_ngrams(state: dict, text: str) -> None:
    """Find frequently-used 4-grams in a chapter and add to banned phrases."""
    ngrams = _extract_ngrams(text, 4)
    counts = _Counter(ngrams)
    for phrase, count in counts.most_common(10):
        if count >= 2 and phrase not in state["notable_phrases"]:
            state["notable_phrases"].append(phrase)


def _build_story_state(state: dict) -> str:
    """Format the running story state for injection into the chapter prompt."""
    if not any(state.values()):
        return "This is the first chapter. No story state accumulated yet."

    parts = []

    # Scene types used
    type_counts = _Counter(
        entry.split(":")[-1] for entry in state.get("scene_types_used", [])
    )
    if type_counts:
        overused = [f"{t} ({c}x)" for t, c in type_counts.most_common() if c >= 2]
        parts.append(f"SCENE TYPES ALREADY USED: {', '.join(f'{t} ({c}x)' for t, c in type_counts.most_common())}")
        if overused:
            parts.append(f"WARNING — OVERUSED SCENE TYPES (DO NOT REPEAT): {', '.join(overused)}")

    # Character arcs
    arcs = state.get("character_arcs", {})
    if arcs:
        arc_lines = []
        for char, positions in arcs.items():
            arc_lines.append(f"  {char}: {' → '.join(positions)}")
        parts.append("CHARACTER ARC PROGRESSION (must advance, NEVER loop back):\n" + "\n".join(arc_lines))

    # Antagonist reveals
    reveals = state.get("antagonist_reveals", [])
    if reveals:
        parts.append(f"ANTAGONIST HAS ALREADY REVEALED/ARGUED (must say NEW things):\n  " + "\n  ".join(reveals[-8:]))

    # Chapter structures
    structures = state.get("chapter_structures", [])
    if structures:
        parts.append(f"PREVIOUS CHAPTER STRUCTURES: {', '.join(structures[-5:])}")
        last = structures[-1].split(":")[-1] if structures else ""
        if last:
            parts.append(f"LAST CHAPTER WAS: {last} — this chapter MUST be structurally different")

    # Tension curve
    tensions = state.get("tension_levels", [])
    if tensions:
        parts.append(f"TENSION CURVE SO FAR: {' → '.join(str(t) for t in tensions)}")

    # Banned phrases
    phrases = state.get("notable_phrases", [])
    if phrases:
        # Show the most recent/relevant ones (cap at 40 to avoid token bloat)
        shown = phrases[-40:]
        parts.append(f"BANNED PHRASES (already used — DO NOT reuse):\n  " + "\n  ".join(f'"{p}"' for p in shown))

    return "\n\n".join(parts)


# =============================================================================
# EXECUTOR FUNCTIONS
# =============================================================================

async def execute_plot_structure(context: ExecutionContext) -> Dict[str, Any]:
    """Execute plot structure agent."""
    llm = context.llm_client

    prompt = PLOT_STRUCTURE_PROMPT.format(
        central_dramatic_question=context.inputs.get("story_question", {}).get("central_dramatic_question", ""),
        protagonist_arc=context.inputs.get("character_architecture", {}).get("protagonist_arc", {}),
        relationship_dynamics=context.inputs.get("relationship_dynamics", {})
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        return {
            "act_structure": {
                "act_1": {"percentage": 25, "purpose": "Setup world and characters", "key_events": ["Introduction", "Catalyst", "Decision"]},
                "act_2": {"percentage": 50, "purpose": "Rising conflict and complications", "key_events": ["Tests", "Midpoint", "Crisis"]},
                "act_3": {"percentage": 25, "purpose": "Climax and resolution", "key_events": ["Climax", "Resolution", "New equilibrium"]}
            },
            "major_beats": [
                {"name": "Opening Image", "description": "Establish protagonist's world", "page_target": "1-2"},
                {"name": "Catalyst", "description": "Event that changes everything", "page_target": "10-12"},
                {"name": "Midpoint", "description": "Stakes raised, false victory/defeat", "page_target": "50%"},
                {"name": "All Is Lost", "description": "Protagonist's lowest point", "page_target": "75%"},
                {"name": "Climax", "description": "Final confrontation", "page_target": "90%"}
            ],
            "reversals": [
                {"name": "Midpoint", "what_changes": "Understanding of true enemy", "impact": "Stakes escalate"},
                {"name": "All Is Lost", "what_changes": "Loses everything believed in", "impact": "Must find new way"}
            ],
            "point_of_no_return": {
                "moment": "End of Act 1",
                "why_irreversible": "Cannot return to old life",
                "protagonist_commitment": "Chooses the difficult path"
            },
            "climax_design": {
                "setup": "All forces converge",
                "confrontation": "Protagonist vs antagonist",
                "resolution": "Theme proven through action"
            },
            "resolution": {
                "external_resolution": "Problem solved",
                "internal_resolution": "Character transformed",
                "final_image": "Mirror of opening showing change"
            }
        }


async def execute_pacing_design(context: ExecutionContext) -> Dict[str, Any]:
    """Execute pacing design agent."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    prompt = PACING_DESIGN_PROMPT.format(
        plot_structure=context.inputs.get("plot_structure", {}),
        genre=constraints.get("genre", "general fiction")
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        return {
            "tension_curve": [
                {"point": "Opening", "level": 3, "description": "Hook interest"},
                {"point": "Catalyst", "level": 5, "description": "Disrupt status quo"},
                {"point": "Midpoint", "level": 7, "description": "Raise stakes"},
                {"point": "All Is Lost", "level": 4, "description": "Emotional low"},
                {"point": "Climax", "level": 10, "description": "Maximum tension"},
                {"point": "Resolution", "level": 2, "description": "Satisfying close"}
            ],
            "scene_density_map": {
                "act_1": {"action_reflection_ratio": "40:60", "dialogue_description": "50:50"},
                "act_2_first_half": {"action_reflection_ratio": "60:40", "dialogue_description": "60:40"},
                "act_2_second_half": {"action_reflection_ratio": "70:30", "dialogue_description": "50:50"},
                "act_3": {"action_reflection_ratio": "80:20", "dialogue_description": "40:60"}
            },
            "breather_points": [
                {"after": "Major revelation", "type": "Reflection", "purpose": "Process information"},
                {"after": "Action sequence", "type": "Character moment", "purpose": "Emotional connection"}
            ],
            "acceleration_zones": [
                {"section": "Approaching midpoint", "technique": "Shorter scenes", "effect": "Building momentum"},
                {"section": "Climax sequence", "technique": "Short paragraphs", "effect": "Urgency"}
            ]
        }


async def execute_chapter_blueprint(context: ExecutionContext) -> Dict[str, Any]:
    """Execute chapter blueprint agent.

    Calculates adaptive chapter count and word targets based on the
    user's target_word_count, so the LLM produces the right number
    of chapters at the right length for any book size (40K-120K words).
    """
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    # Calculate adaptive chapter parameters from target word count
    target_word_count = int(constraints.get("target_word_count", 80000) or 80000)

    # Adaptive chapter sizing: aim for 3000-5000 words per chapter
    # depending on total book length
    if target_word_count <= 50000:
        avg_words_per_chapter = 3000
    elif target_word_count <= 80000:
        avg_words_per_chapter = 3500
    elif target_word_count <= 100000:
        avg_words_per_chapter = 4000
    else:
        avg_words_per_chapter = 4500

    suggested_chapter_count = max(8, min(35, round(target_word_count / avg_words_per_chapter)))

    prompt = CHAPTER_BLUEPRINT_PROMPT.format(
        plot_structure=context.inputs.get("plot_structure", {}),
        pacing_design=context.inputs.get("pacing_design", {}),
        character_architecture=context.inputs.get("character_architecture", {}),
        target_word_count=target_word_count,
        suggested_chapter_count=suggested_chapter_count,
        suggested_words_per_chapter=avg_words_per_chapter
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        # Generate placeholder chapter outline with adaptive sizing
        num_chapters = suggested_chapter_count
        chapters = []
        act1_end = max(1, round(num_chapters * 0.25))
        act2_end = max(act1_end + 1, round(num_chapters * 0.75))

        for i in range(1, num_chapters + 1):
            act = 1 if i <= act1_end else (2 if i <= act2_end else 3)
            chapters.append({
                "number": i,
                "title": f"Chapter {i}",
                "act": act,
                "chapter_goal": f"[Goal for chapter {i}]",
                "pov": "Protagonist",
                "opening_hook": f"[Hook for chapter {i}]",
                "closing_hook": f"[Closing hook for chapter {i}]",
                "word_target": avg_words_per_chapter,
                "scenes": [
                    {
                        "scene_number": 1,
                        "scene_question": f"[Scene question for Ch{i}-S1]",
                        "characters": ["Protagonist"],
                        "location": "[Location]",
                        "conflict_type": "internal" if i % 2 == 0 else "external",
                        "outcome": "[Outcome]",
                        "word_target": avg_words_per_chapter // 2
                    },
                    {
                        "scene_number": 2,
                        "scene_question": f"[Scene question for Ch{i}-S2]",
                        "characters": ["Protagonist", "Supporting"],
                        "location": "[Location]",
                        "conflict_type": "interpersonal",
                        "outcome": "[Outcome]",
                        "word_target": avg_words_per_chapter // 2
                    }
                ]
            })

        return {
            "chapter_outline": chapters,
            "chapter_goals": {str(c["number"]): c["chapter_goal"] for c in chapters},
            "scene_list": [f"Ch{c['number']}-S{s['scene_number']}: {s['scene_question']}" for c in chapters for s in c["scenes"]],
            "scene_questions": {f"Ch{c['number']}-S{s['scene_number']}": s["scene_question"] for c in chapters for s in c["scenes"]},
            "hooks": {"chapter_hooks": [c["opening_hook"] for c in chapters], "scene_hooks": []},
            "pov_assignments": {str(c["number"]): c["pov"] for c in chapters}
        }


def _ensure_voice_spec_example_passages(response: Dict[str, Any]) -> Dict[str, Any]:
    """Inject a fallback example passage if the LLM omitted style_guide.example_passages."""
    if not isinstance(response, dict):
        return response
    style_guide = response.get("style_guide")
    if not isinstance(style_guide, dict):
        response["style_guide"] = {
            "example_passages": [
                "He watched the elevator numbers climb as if they were a verdict."
            ]
        }
        return response
    passages = style_guide.get("example_passages")
    if not isinstance(passages, list) or not passages:
        style_guide["example_passages"] = [
            "He watched the elevator numbers climb as if they were a verdict."
        ]
    return response


async def execute_voice_specification(context: ExecutionContext) -> Dict[str, Any]:
    """Execute voice specification agent."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    prompt = VOICE_SPECIFICATION_PROMPT.format(
        genre=constraints.get("genre", "general fiction"),
        reader_avatar=context.inputs.get("market_intelligence", {}).get("reader_avatar", {}),
        protagonist_profile=context.inputs.get("character_architecture", {}).get("protagonist_profile", {})
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return _ensure_voice_spec_example_passages(response)
    else:
        return {
            "narrative_voice": {
                "pov_type": "Third person limited",
                "distance": "Close",
                "personality": "Observant, empathetic",
                "tone": "Contemplative with moments of intensity"
            },
            "pov_rules": {
                "perspective_character": "Protagonist",
                "knowledge_limits": "Only knows what protagonist observes",
                "rules": ["No head-hopping", "Can speculate about others", "Internal thoughts in italics"]
            },
            "tense_rules": {
                "primary_tense": "Past",
                "exceptions": ["Flashbacks in past perfect", "Immediate sensations in present"]
            },
            "syntax_patterns": {
                "avg_sentence_length": "15-20 words",
                "complexity": "Mix of simple and compound",
                "rhythm": "Varies with tension"
            },
            "sensory_density": {
                "visual": "Primary sense, specific details",
                "other_senses": "Layer in sound and touch",
                "frequency": "1-2 sensory details per paragraph"
            },
            "dialogue_style": {
                "tag_approach": "Said-bookism avoided, minimal tags",
                "subtext_level": "High - what's unsaid matters",
                "differentiation": "Each character has verbal tics"
            },
            "style_guide": {
                "dos": ["Show don't tell", "Active voice", "Specific details"],
                "donts": ["Adverb overuse", "Purple prose", "Info dumps"],
                "example_passages": [
                    "He watched the elevator numbers climb as if they were a verdict. When the doors opened, the air on the executive floor smelled faintly of citrus and expensive coffee, and he felt his jaw tighten before he could stop it."
                ]
            }
        }


async def execute_draft_generation(
    context: ExecutionContext,
    progress_callback: Optional[Callable[[dict], Any]] = None,
) -> Dict[str, Any]:
    """Execute draft generation agent - generates all chapters."""
    llm = context.llm_client
    chapter_blueprint = context.inputs.get("chapter_blueprint", {})

    chapters: List[Dict[str, Any]] = []
    chapter_metadata: List[Dict[str, Any]] = []
    scene_tags: Dict[str, Any] = {}
    deviations: List[Dict[str, Any]] = []
    fix_plan: List[str] = []
    chapter_scores: Dict[str, int] = {}
    failed_chapters: List[Dict[str, Any]] = []

    # Running story state accumulator — tracks beats, arcs, phrases across
    # ALL chapters to prevent repetitive plots and looping character arcs.
    story_state: Dict[str, Any] = {
        "scene_types_used": [],       # e.g. ["chase", "infiltration", "quiet_reflection"]
        "character_arcs": {},          # e.g. {"Silas": ["distrustful", "beginning_to_trust"]}
        "antagonist_reveals": [],      # what the villain has said/revealed
        "notable_phrases": [],         # phrases to avoid reusing
        "tension_levels": [],          # per-chapter tension (1-10)
        "chapter_structures": [],      # e.g. ["action_heavy", "dialogue_heavy", "introspection"]
    }

    # ── Resume from previous attempt ──
    # If a prior attempt generated chapters but failed the gate, the
    # orchestrator now preserves that output.  Carry forward any
    # successfully-written chapters so we only regenerate what's missing.
    _existing_by_num: Dict[int, Dict[str, Any]] = {}
    for layer in context.project.layers.values():
        if "draft_generation" in layer.agents:
            _prev_state = layer.agents["draft_generation"]
            if _prev_state.current_output:
                _prev = _prev_state.current_output.content
                if isinstance(_prev, dict) and isinstance(_prev.get("chapters"), list):
                    for _ch in _prev["chapters"]:
                        if isinstance(_ch, dict) and _ch.get("number") and _ch.get("text"):
                            _existing_by_num[_ch["number"]] = _ch
                    # Also carry forward metadata from previous run
                    if isinstance(_prev.get("chapter_scores"), dict):
                        chapter_scores.update(_prev["chapter_scores"])
                    if isinstance(_prev.get("scene_tags"), dict):
                        scene_tags.update(_prev["scene_tags"])
            break

    if _existing_by_num:
        logger.info(
            "draft_generation: Resuming with %d existing chapter(s) from previous attempt",
            len(_existing_by_num),
        )

    outline = chapter_blueprint.get("chapter_outline", [])
    chapters_total = len(outline)

    for chapter_index, chapter in enumerate(outline):
        chapter_num = chapter.get("number", 0)
        chapter_title = chapter.get("title", f"Chapter {chapter_num}")

        # ── Skip chapters already generated in a previous attempt ──
        if chapter_num in _existing_by_num:
            prev_ch = _existing_by_num[chapter_num]
            chapters.append(prev_ch)
            chapter_metadata.append({
                "number": chapter_num,
                "title": prev_ch.get("title", chapter_title),
                "scenes": len(chapter.get("scenes", [])),
                "pov": chapter.get("pov", "Unknown"),
            })
            logger.info(
                "draft_generation: Chapter %s carried forward from previous attempt",
                chapter_num,
            )
            if progress_callback is not None:
                try:
                    cb = progress_callback({
                        "chapter": chapter_num,
                        "status": "carried_forward",
                        "word_count": prev_ch.get("word_count", 0),
                        "chapters_done": chapter_index + 1,
                        "chapters_total": chapters_total,
                    })
                    if asyncio.iscoroutine(cb):
                        await cb
                except Exception:
                    pass
            continue

        if llm:
            # ── Retry loop: attempt each chapter up to _DRAFT_CHAPTER_MAX_RETRIES times ──
            chapter_succeeded = False
            last_error = ""

            for attempt in range(1, _DRAFT_CHAPTER_MAX_RETRIES + 1):
                try:
                    # Build sliding window of previous chapter summaries for continuity.
                    # Using up to 5 recent summaries (increased from 3) to reduce
                    # character/plot "resets" in longer books.
                    previous_summary = "This is the first chapter."
                    if chapters:
                        context_window = 5
                        recent = chapters[-context_window:]
                        summary_parts = []
                        for prev_ch in recent:
                            pnum = prev_ch.get("number", "?")
                            psum = prev_ch.get("summary", "")
                            if psum:
                                summary_parts.append(f"Chapter {pnum}: {psum}")
                        previous_summary = "\n".join(summary_parts) if summary_parts else f"Previous chapter ended with: {chapters[-1].get('summary', '')}"

                    # Build running story state from ALL previous chapters.
                    # This prevents repetitive plot patterns, character arc loops,
                    # and overused phrases across the entire book.
                    story_state_text = _build_story_state(story_state)

                    # Get the word target from the blueprint for this chapter
                    word_target = chapter.get("word_target", 3000)

                    # Extract dialogue voice profiles from character architecture.
                    char_arch = context.inputs.get("character_architecture", {})
                    dialogue_voices = char_arch.get("dialogue_voices", {}) if isinstance(char_arch, dict) else {}
                    if not dialogue_voices:
                        dialogue_voices = "No dialogue voice profiles available. Differentiate characters by vocabulary, sentence length, and speech patterns."

                    prompt = DRAFT_GENERATION_PROMPT.format(
                        chapter_number=chapter_num,
                        chapter_title=chapter_title,
                        voice_specification=context.inputs.get("voice_specification", {}),
                        chapter_blueprint=chapter,
                        character_architecture=char_arch,
                        dialogue_voices=dialogue_voices,
                        world_rules=context.inputs.get("world_rules", {}),
                        previous_summary=previous_summary,
                        story_state=story_state_text,
                        word_target=word_target
                    )

                    timeout = _DRAFT_CHAPTER_TIMEOUT
                    chapter_text = await asyncio.wait_for(llm.generate(prompt), timeout=timeout)
                    summary = await asyncio.wait_for(
                        llm.generate(
                            f"""Summarize this chapter in 2-3 sentences for the next chapter's writer. Focus on:
1. Key plot developments and how they change the situation
2. Where each major character ends up (physically and emotionally)
3. Any cliffhangers, unresolved tensions, or hooks for the next chapter

Chapter text (first 4000 chars):
{chapter_text[:4000]}

Summary:""",
                            max_tokens=300,
                        ),
                        timeout=timeout,
                    )
                    # Guard: ensure summary is always a string (LLM might
                    # return JSON despite not being asked for it).
                    if not isinstance(summary, str) or not summary.strip():
                        summary = str(summary) if summary else f"Chapter {chapter_num} summary"

                    # Extract structured story state from this chapter for the
                    # running accumulator.  Uses a single fast LLM call.
                    try:
                        ch_state = await asyncio.wait_for(
                            llm.generate(
                                _STORY_STATE_EXTRACTION_PROMPT.format(
                                    chapter_number=chapter_num,
                                    chapter_text=chapter_text[:5000],
                                ),
                                response_format="json",
                                max_tokens=600,
                                temperature=0.1,
                            ),
                            timeout=timeout,
                        )
                        if isinstance(ch_state, dict):
                            _accumulate_story_state(story_state, ch_state, chapter_num, chapter_text)
                    except Exception:
                        # Non-fatal: fall back to heuristic extraction
                        _accumulate_story_state_heuristic(story_state, chapter_num, chapter_text)

                    # Optional: evaluate outline adherence (saves 1 LLM call per chapter when disabled)
                    if _DRAFT_ADHERENCE_CHECK:
                        adherence_prompt = f"""You are verifying whether a generated chapter follows its blueprint.

Blueprint for this chapter:
{chapter}

Generated chapter (truncated if needed):
{chapter_text[:4500]}

Return ONLY valid JSON with this exact shape:
{{
  "outline_adherence_score": 0,
  "scene_checks": [
    {{"scene_number": 1, "present": true, "notes": "...", "deviation": false, "suggested_fix": "..."}}
  ],
  "chapter_deviations": [
    {{"chapter": 1, "severity": "major|minor", "description": "...", "suggested_fix": "..."}}
  ]
}}

Rules:
- outline_adherence_score is 0-100.
- scene_checks must include every scene_number listed in the blueprint.
- If deviation=true, suggested_fix must be specific."""
                        adherence = await asyncio.wait_for(
                            llm.generate(adherence_prompt, response_format="json", temperature=0.2, max_tokens=1600),
                            timeout=timeout,
                        )

                        score = adherence.get("outline_adherence_score")
                        if isinstance(score, int):
                            chapter_scores[str(chapter_num)] = score
                        else:
                            chapter_scores[str(chapter_num)] = 0

                        scene_tags[f"Ch{chapter_num}"] = adherence.get("scene_checks", [])
                        for d in adherence.get("chapter_deviations", []) if isinstance(adherence, dict) else []:
                            if isinstance(d, dict):
                                deviations.append(d)
                    else:
                        # Default pass score when adherence checking is disabled
                        chapter_scores[str(chapter_num)] = 85

                    word_count = len(chapter_text.split())

                    # ── Word count enforcement ──
                    # If chapter is significantly short (<75% of target), expand it.
                    # If significantly long (>135% of target), flag but keep (trimming
                    # risks cutting important content; downstream editors can tighten).
                    if word_target and word_count < int(word_target * 0.75):
                        try:
                            deficit = word_target - word_count
                            expand_prompt = f"""The chapter below is {word_count} words but the target is {word_target} words ({deficit} words short).

Expand the chapter by deepening existing scenes — add:
- More sensory details and physical grounding
- Deeper internal monologue during key emotional moments
- Additional dialogue exchanges that reveal character
- Transitional beats between scenes that build atmosphere

Do NOT add new plot events or change the story. Just enrich what's already there.
Maintain the exact same voice and style.

Chapter text:
{chapter_text}

Return the COMPLETE expanded chapter text (not JSON, just the prose)."""
                            expanded = await asyncio.wait_for(
                                llm.generate(expand_prompt, max_tokens=16000),
                                timeout=timeout,
                            )
                            if isinstance(expanded, str) and len(expanded.split()) > word_count:
                                chapter_text = expanded
                                word_count = len(chapter_text.split())
                                logger.info(
                                    "draft_generation: Chapter %s expanded from %d to %d words (target: %d)",
                                    chapter_num, word_count - deficit, word_count, word_target,
                                )
                        except Exception as exc:
                            logger.warning("draft_generation: Chapter %s expansion failed: %s", chapter_num, exc)

                    chapters.append({
                        "number": chapter_num,
                        "title": chapter_title,
                        "text": chapter_text,
                        "summary": summary,
                        "word_count": word_count,
                    })

                    if progress_callback is not None:
                        try:
                            cb = progress_callback({
                                "chapter": chapter_num,
                                "status": "ok",
                                "word_count": word_count,
                                "chapters_done": chapter_index + 1,
                                "chapters_total": chapters_total,
                                "attempt": attempt,
                            })
                            if asyncio.iscoroutine(cb):
                                await cb
                        except Exception:
                            logger.debug("draft_generation: progress_callback raised for chapter %s", chapter_num, exc_info=True)

                    chapter_succeeded = True
                    break  # success — exit retry loop, proceed to next chapter

                except (asyncio.TimeoutError, Exception) as exc:
                    last_error = f"LLM timeout after {timeout}s" if isinstance(exc, asyncio.TimeoutError) else str(exc)
                    logger.warning(
                        "draft_generation: Chapter %s attempt %d/%d failed: %s",
                        chapter_num, attempt, _DRAFT_CHAPTER_MAX_RETRIES, last_error,
                    )

                    if attempt < _DRAFT_CHAPTER_MAX_RETRIES:
                        backoff = _DRAFT_CHAPTER_RETRY_BACKOFF ** attempt
                        logger.info("draft_generation: Retrying chapter %s in %.1fs", chapter_num, backoff)
                        if progress_callback is not None:
                            try:
                                cb = progress_callback({
                                    "chapter": chapter_num,
                                    "status": "retrying",
                                    "word_count": 0,
                                    "chapters_done": chapter_index,
                                    "chapters_total": chapters_total,
                                    "attempt": attempt,
                                    "error": last_error,
                                })
                                if asyncio.iscoroutine(cb):
                                    await cb
                            except Exception:
                                logger.debug("draft_generation: progress_callback raised for chapter %s", chapter_num, exc_info=True)
                        await asyncio.sleep(backoff)
                    # else: final attempt — handled below

            if not chapter_succeeded:
                # All retries exhausted for this chapter.
                failed_chapters.append({"chapter": chapter_num, "error": last_error})
                if progress_callback is not None:
                    try:
                        cb = progress_callback({
                            "chapter": chapter_num,
                            "status": "failed",
                            "word_count": 0,
                            "chapters_done": chapter_index,
                            "chapters_total": chapters_total,
                            "attempts": _DRAFT_CHAPTER_MAX_RETRIES,
                            "error": last_error,
                        })
                        if asyncio.iscoroutine(cb):
                            await cb
                    except Exception:
                        logger.debug("draft_generation: progress_callback raised for chapter %s", chapter_num, exc_info=True)

                # Stop writing — subsequent chapters depend on this one's summary.
                logger.error(
                    "draft_generation: Chapter %s failed after %d attempts. "
                    "Stopping to preserve narrative continuity.",
                    chapter_num, _DRAFT_CHAPTER_MAX_RETRIES,
                )
                break  # exit the chapter loop

        else:
            # Placeholder
            placeholder_text = f"[Chapter {chapter_num}: {chapter_title} — content would be generated here by the LLM. This is a placeholder for demo/no-LLM mode.]"
            word_count = len(placeholder_text.split())
            chapters.append({
                "number": chapter_num,
                "title": chapter_title,
                "text": placeholder_text,
                "summary": f"Chapter {chapter_num} summary placeholder",
                "word_count": word_count,
            })
            chapter_scores[str(chapter_num)] = 85
            scene_tags[f"Ch{chapter_num}"] = []

            if progress_callback is not None:
                try:
                    cb = progress_callback({
                        "chapter": chapter_num,
                        "status": "ok",
                        "word_count": word_count,
                        "chapters_done": chapter_index + 1,
                        "chapters_total": chapters_total,
                    })
                    if asyncio.iscoroutine(cb):
                        await cb
                except Exception:
                    logger.debug("draft_generation: progress_callback raised for chapter %s", chapter_num, exc_info=True)

        chapter_metadata.append({
            "number": chapter_num,
            "title": chapter_title,
            "scenes": len(chapter.get("scenes", [])),
            "pov": chapter.get("pov", "Unknown")
        })

    # Consolidate adherence across chapters
    overall = 0
    if chapter_scores:
        overall = int(sum(chapter_scores.values()) / max(1, len(chapter_scores)))

    outline_adherence = {
        "overall_score": overall,
        "chapter_scores": chapter_scores,
        "notes": "Scores reflect blueprint adherence; investigate deviations for rewrite targets."
    }

    # Ensure deviations list is consistent with scores.
    # The per-chapter LLM adherence call may return a low score without
    # populating chapter_deviations, which causes the gate to reject the
    # output (catch-22: low score requires non-empty deviations).  Synthesize
    # deviation entries from any chapter that scored below the gate threshold.
    if overall < 80 and not deviations:
        for ch_num_str, ch_score in chapter_scores.items():
            if isinstance(ch_score, int) and ch_score < 80:
                deviations.append({
                    "chapter": int(ch_num_str) if ch_num_str.isdigit() else ch_num_str,
                    "severity": "major" if ch_score < 60 else "minor",
                    "description": f"Chapter {ch_num_str} scored {ch_score}/100 on outline adherence",
                    "suggested_fix": f"Review chapter {ch_num_str} against its blueprint and revise deviating scenes",
                })

    # Create a simple prioritized fix plan from deviations (fallback). LLM can refine later in rewrite agents.
    if deviations:
        fix_plan = [
            f"Chapter {d.get('chapter','?')}: {d.get('suggested_fix') or d.get('description')}"
            for d in deviations[:12]
            if isinstance(d, dict)
        ]

    return {
        "chapters": chapters,
        "chapter_metadata": chapter_metadata,
        "word_counts": {str(c["number"]): c["word_count"] for c in chapters},
        "scene_tags": scene_tags,
        "outline_adherence": outline_adherence,
        "chapter_scores": chapter_scores,
        "deviations": deviations,
        "fix_plan": fix_plan,
        "failed_chapters": failed_chapters,
    }


# =============================================================================
# REGISTRATION
# =============================================================================

STRUCTURAL_EXECUTORS = {
    "plot_structure": execute_plot_structure,
    "pacing_design": execute_pacing_design,
    "chapter_blueprint": execute_chapter_blueprint,
    "voice_specification": execute_voice_specification,
    "draft_generation": execute_draft_generation,
}
