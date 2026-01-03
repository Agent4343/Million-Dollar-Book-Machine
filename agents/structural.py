"""
Structural Engine Agents (Layers 8-12)

Production-ready agents for story structure:
- Macro Plot Structure
- Pacing & Tension Design
- Chapter & Scene Blueprint
- Style & Voice Specification
- Draft Generation (Scene-by-Scene)

These agents create the architecture that turns concept into manuscript.
"""

from typing import Dict, Any, List, Optional
from core.orchestrator import ExecutionContext
import logging
import json

logger = logging.getLogger(__name__)


# =============================================================================
# PLOT STRUCTURE PROMPT
# =============================================================================

PLOT_STRUCTURE_PROMPT = """You are a master story architect who has analyzed thousands of successful narratives. You understand that plot is not a sequence of events—it's a cascade of cause and effect driven by character choice.

## Story Foundation:
- Central Dramatic Question: {central_dramatic_question}
- Protagonist Arc: {protagonist_arc}
- Relationship Dynamics: {relationship_dynamics}
- Theme: {theme}
- Genre: {genre}

## Target Structure:
- Word Count: {target_word_count} words
- Chapter Count: {num_chapters} chapters
- Approximate words per chapter: {words_per_chapter}

## Your Task: Design the Complete Plot Architecture

### 1. ACT STRUCTURE

**ACT 1 - SETUP (First 25%)**
Purpose: Establish normal world, introduce protagonist and stakes, end with commitment

- Opening Image: First impression that sets tone
- Character Introduction: Show protagonist in normal world
- Establish Stakes: What matters to protagonist
- Inciting Incident: The disruption that starts everything
- Debate: Protagonist resists change
- First Plot Point: Protagonist commits to the journey

**ACT 2A - RISING ACTION (25-50%)**
Purpose: Tests, allies, enemies, raising stakes

- B Story Launch: Secondary plot thread begins
- Fun and Games: Promise of the premise delivered
- Tests and Trials: Protagonist tries and learns
- Midpoint: Major revelation or reversal

**ACT 2B - COMPLICATIONS (50-75%)**
Purpose: Mounting pressure, closing options, approaching crisis

- Stakes Escalate: Consequences become more severe
- Bad Guys Close In: Opposition intensifies
- Allies Lost or Tested: Relationships strained
- All Is Lost: Protagonist's lowest point
- Dark Night of Soul: Internal crisis

**ACT 3 - RESOLUTION (Final 25%)**
Purpose: Final confrontation, climax, new equilibrium

- Break Into Three: New plan or understanding
- Gathering Forces: Preparation for finale
- Climax: Final confrontation
- Resolution: Outcome and consequences
- Final Image: New normal, mirror of opening

### 2. MAJOR BEATS

For each beat, define:
- What happens (external event)
- Why it matters (internal significance)
- What changes (story state before/after)
- Page/chapter placement

Key Beats:
1. Opening Image
2. Theme Stated
3. Setup
4. Catalyst/Inciting Incident
5. Debate
6. Break Into Two (First Plot Point)
7. B Story
8. Fun and Games
9. Midpoint
10. Bad Guys Close In
11. All Is Lost
12. Dark Night of Soul
13. Break Into Three
14. Finale
15. Final Image

### 3. REVERSALS & REVEALS

Plan 3-5 major reversals/reveals:
- What the reversal is
- What the reader believed before
- What they learn
- How this changes everything
- Optimal placement

### 4. POINT OF NO RETURN

The moment when the protagonist cannot go back:
- What happens
- Why they can't undo it
- What they've committed to
- What they've sacrificed

### 5. CLIMAX DESIGN

The final confrontation must:
- Test everything the protagonist has learned
- Force the choice between want and need
- Embody the thematic question
- Have genuine possibility of failure

**Climax Architecture:**
- Setup: What brings all forces together
- Confrontation: The actual clash
- Crisis Choice: The moment of decision
- Resolution: The outcome
- Aftermath: Immediate consequences

### 6. RESOLUTION & ENDING

**External Resolution:**
- How is the plot resolved?
- What is the new status quo?

**Internal Resolution:**
- How has the protagonist changed?
- What do they understand now?

**Thematic Resolution:**
- How is the theme answered?
- What truth has been proven?

**Final Image:**
- What image closes the book?
- How does it mirror/contrast the opening?
- What emotion does it leave?

## Output Format (JSON):
{{
    "act_structure": {{
        "act_1": {{
            "percentage": 25,
            "word_count_target": 0,
            "chapter_range": [1, 0],
            "purpose": "...",
            "key_events": [
                {{"event": "...", "chapter": 1, "significance": "..."}}
            ],
            "protagonist_state": {{
                "beginning": "...",
                "end": "..."
            }}
        }},
        "act_2a": {{
            "percentage": 25,
            "word_count_target": 0,
            "chapter_range": [0, 0],
            "purpose": "...",
            "key_events": [
                {{"event": "...", "chapter": 0, "significance": "..."}}
            ],
            "protagonist_state": {{
                "beginning": "...",
                "end": "..."
            }}
        }},
        "act_2b": {{
            "percentage": 25,
            "word_count_target": 0,
            "chapter_range": [0, 0],
            "purpose": "...",
            "key_events": [
                {{"event": "...", "chapter": 0, "significance": "..."}}
            ],
            "protagonist_state": {{
                "beginning": "...",
                "end": "..."
            }}
        }},
        "act_3": {{
            "percentage": 25,
            "word_count_target": 0,
            "chapter_range": [0, 0],
            "purpose": "...",
            "key_events": [
                {{"event": "...", "chapter": 0, "significance": "..."}}
            ],
            "protagonist_state": {{
                "beginning": "...",
                "end": "..."
            }}
        }}
    }},
    "major_beats": [
        {{
            "name": "Opening Image",
            "description": "...",
            "internal_significance": "...",
            "story_state_change": "...",
            "chapter_placement": 1,
            "approximate_page": "1-2"
        }}
    ],
    "reversals": [
        {{
            "name": "...",
            "what_reverses": "...",
            "believed_before": "...",
            "revealed_truth": "...",
            "how_changes_everything": "...",
            "placement": "...",
            "chapter": 0
        }}
    ],
    "point_of_no_return": {{
        "moment": "...",
        "chapter": 0,
        "what_happens": "...",
        "why_irreversible": "...",
        "commitment_made": "...",
        "sacrifice": "..."
    }},
    "climax_design": {{
        "chapter": 0,
        "setup": "...",
        "confrontation": "...",
        "crisis_choice": "...",
        "choice_made": "...",
        "resolution": "...",
        "aftermath": "..."
    }},
    "resolution": {{
        "external": "...",
        "internal": "...",
        "thematic": "...",
        "final_image": {{
            "description": "...",
            "mirrors_opening": "...",
            "final_emotion": "..."
        }}
    }},
    "b_story": {{
        "description": "...",
        "thematic_function": "...",
        "intersection_points": [0],
        "resolution": "..."
    }},
    "subplot_threads": [
        {{
            "name": "...",
            "purpose": "...",
            "key_chapters": [0]
        }}
    ],
    "plot_coherence_score": 90
}}
"""


# =============================================================================
# PACING DESIGN PROMPT
# =============================================================================

PACING_DESIGN_PROMPT = """You are a pacing specialist who understands that great books are experienced as a rhythm of tension and release. You control when readers can't put the book down and when they can breathe.

## Plot Structure:
{plot_structure}

## Genre Expectations:
- Genre: {genre}
- Target Audience: {target_audience}

## Book Metrics:
- Word Count: {target_word_count}
- Chapter Count: {num_chapters}

## Your Task: Design the Pacing Architecture

### 1. TENSION CURVE

Map tension levels (1-10) throughout the book:
- Where are the peaks?
- Where are the valleys?
- How does tension escalate overall?
- Where are the crucial acceleration points?

### 2. SCENE DENSITY

Different parts of the book require different scene types:

**Scene Types:**
- ACTION: High tension, external conflict, things happening
- REACTION: Processing, emotional response, planning
- DIALOGUE: Character interaction, information exchange
- REFLECTION: Internal, quiet, character depth
- TRANSITION: Moving between situations

Plan the ratio of scene types for each act.

### 3. SENTENCE & PARAGRAPH RHYTHM

Guide the prose rhythm:
- Tense scenes: Short sentences, short paragraphs
- Contemplative scenes: Longer, more complex sentences
- Dialogue scenes: Rapid exchange with beats
- Emotional scenes: Varied for emphasis

### 4. CHAPTER ARCHITECTURE

For each chapter, define:
- Length (word count)
- Pacing type (fast/medium/slow)
- Number of scenes
- Entry tension level
- Exit tension level
- Hook type (question, revelation, cliffhanger)

### 5. BREATHER POINTS

Readers need rest. Plan strategic breathers:
- After intense sequences
- Before major reveals
- Character bonding moments
- Worldbuilding that doesn't feel like exposition

### 6. ACCELERATION ZONES

Where the book picks up speed:
- Approaching act breaks
- Chase/conflict sequences
- Revelation cascades
- The final sprint

### 7. PAGE-TURNER MECHANICS

What keeps readers reading:
- End-of-chapter hooks (every chapter)
- Micro-tensions (within scenes)
- Questions raised vs answered ratio
- Promise and payoff timing

## Output Format (JSON):
{{
    "tension_curve": [
        {{
            "chapter": 1,
            "tension_level": 4,
            "description": "...",
            "key_emotion": "..."
        }}
    ],
    "overall_tension_map": {{
        "opening_tension": 4,
        "act_1_peak": 6,
        "midpoint_tension": 7,
        "all_is_lost": 3,
        "climax_peak": 10,
        "resolution": 3
    }},
    "scene_density_by_act": {{
        "act_1": {{
            "action_percentage": 30,
            "reaction_percentage": 25,
            "dialogue_percentage": 30,
            "reflection_percentage": 10,
            "transition_percentage": 5
        }},
        "act_2a": {{
            "action_percentage": 40,
            "reaction_percentage": 20,
            "dialogue_percentage": 25,
            "reflection_percentage": 10,
            "transition_percentage": 5
        }},
        "act_2b": {{
            "action_percentage": 50,
            "reaction_percentage": 15,
            "dialogue_percentage": 25,
            "reflection_percentage": 5,
            "transition_percentage": 5
        }},
        "act_3": {{
            "action_percentage": 60,
            "reaction_percentage": 10,
            "dialogue_percentage": 20,
            "reflection_percentage": 5,
            "transition_percentage": 5
        }}
    }},
    "prose_rhythm_guide": {{
        "tense_scenes": "Short, punchy sentences. Fragments okay. White space.",
        "contemplative_scenes": "Longer sentences with subordinate clauses. Dense paragraphs.",
        "dialogue_scenes": "Rapid exchanges. Minimal tags. Action beats for pacing.",
        "emotional_scenes": "Vary for emphasis. Long setup, short punch. Repetition for effect."
    }},
    "chapter_pacing": [
        {{
            "chapter": 1,
            "word_target": 3500,
            "pacing_type": "medium",
            "scene_count": 3,
            "entry_tension": 3,
            "exit_tension": 5,
            "hook_type": "question",
            "hook_description": "..."
        }}
    ],
    "breather_points": [
        {{
            "after_chapter": 0,
            "type": "character_bonding",
            "purpose": "...",
            "duration": "one scene"
        }}
    ],
    "acceleration_zones": [
        {{
            "chapters": [0, 0],
            "description": "...",
            "techniques": ["shorter scenes", "more dialogue", "cliffhanger endings"],
            "effect": "..."
        }}
    ],
    "page_turner_mechanics": {{
        "chapter_hooks": "Every chapter ends with unresolved tension",
        "micro_tension_strategy": "Each scene has its own question",
        "questions_strategy": "Raise 3 for every 1 answered until climax",
        "promise_payoff_timing": "Major promises pay off within 3-5 chapters"
    }},
    "pacing_coherence_score": 90
}}
"""


# =============================================================================
# CHAPTER BLUEPRINT PROMPT
# =============================================================================

CHAPTER_BLUEPRINT_PROMPT = """You are an outline architect who creates detailed execution maps. Your blueprints allow each chapter to be written with clarity of purpose and guaranteed story progression.

## Plot Structure:
{plot_structure}

## Pacing Design:
{pacing_design}

## Characters:
{character_architecture}

## World Rules:
{world_rules}

## Book Metrics:
- Target Word Count: {target_word_count}
- Number of Chapters: {num_chapters}
- Words per Chapter (average): {words_per_chapter}

## Your Task: Create the Complete Chapter & Scene Blueprint

For each chapter, you must define:

### CHAPTER COMPONENTS

1. **Chapter Header:**
   - Number and title
   - Which act it belongs to
   - Word target
   - POV character

2. **Chapter Goal:**
   - What MUST happen in this chapter
   - What changes from beginning to end
   - Why this chapter is necessary (can't be cut)

3. **Opening Hook:**
   - First line approach
   - What draws reader in
   - Tension or question established

4. **Scenes:**
   For each scene in the chapter:
   - Scene number
   - Scene question (what's at stake)
   - Characters present
   - Location (specific)
   - Scene type (action/reaction/dialogue/reflection)
   - Conflict type (internal/external/interpersonal)
   - What happens (beat by beat)
   - What changes
   - Outcome (success/failure/partial/twist)
   - Word target

5. **Closing Hook:**
   - How chapter ends
   - What question/tension carries forward
   - Why reader must continue

6. **Character Tracking:**
   - Protagonist's emotional state at start
   - Protagonist's emotional state at end
   - Key character moments
   - Relationship developments

7. **Plot Advancement:**
   - What moves forward in main plot
   - Any subplot developments
   - Foreshadowing planted
   - Payoffs delivered

### SCENE DESIGN PRINCIPLES

Every scene must have:
- A clear question being answered
- A character who wants something
- An obstacle to getting it
- A turning point
- A reason readers care

### CONTINUITY TRACKING

Track across chapters:
- Time passing
- Location changes
- Character knowledge states
- Planted information
- Pending payoffs

## Output Format (JSON):
{{
    "chapter_outline": [
        {{
            "number": 1,
            "title": "...",
            "act": 1,
            "word_target": 3500,
            "pov": "Protagonist Name",
            "chapter_goal": {{
                "must_happen": "...",
                "state_change": "...",
                "why_necessary": "..."
            }},
            "opening_hook": {{
                "approach": "...",
                "tension_established": "..."
            }},
            "scenes": [
                {{
                    "scene_number": 1,
                    "scene_question": "...",
                    "characters": ["..."],
                    "location": "...",
                    "scene_type": "action|reaction|dialogue|reflection",
                    "conflict_type": "internal|external|interpersonal",
                    "beat_outline": [
                        "Beat 1: ...",
                        "Beat 2: ...",
                        "Turning point: ..."
                    ],
                    "what_changes": "...",
                    "outcome": "success|failure|partial|twist",
                    "word_target": 1500,
                    "emotional_tone": "..."
                }}
            ],
            "closing_hook": {{
                "description": "...",
                "tension_forward": "...",
                "hook_type": "question|revelation|cliffhanger|promise"
            }},
            "character_tracking": {{
                "protagonist_start_state": "...",
                "protagonist_end_state": "...",
                "key_moments": ["..."],
                "relationship_developments": ["..."]
            }},
            "plot_advancement": {{
                "main_plot": "...",
                "subplots": ["..."],
                "foreshadowing": ["..."],
                "payoffs": ["..."]
            }},
            "continuity": {{
                "time_covered": "...",
                "day_in_story": 1,
                "new_information_revealed": ["..."],
                "pending_threads": ["..."]
            }}
        }}
    ],
    "global_continuity": {{
        "story_timeline": [
            {{"chapter": 1, "day": 1, "key_events": ["..."]}}
        ],
        "information_reveals": {{
            "chapter_1": ["Info revealed in ch1"],
            "chapter_2": ["Info revealed in ch2"]
        }},
        "planted_payoffs": [
            {{"planted_chapter": 1, "payoff_chapter": 5, "element": "..."}}
        ]
    }},
    "chapter_summary_list": [
        "Ch1: [Brief summary]"
    ],
    "pov_distribution": {{
        "Protagonist Name": [1, 2, 3],
        "Secondary Character": [4]
    }},
    "word_count_distribution": {{
        "act_1_total": 0,
        "act_2_total": 0,
        "act_3_total": 0,
        "grand_total": 0
    }},
    "blueprint_completeness_score": 95
}}
"""


# =============================================================================
# VOICE SPECIFICATION PROMPT
# =============================================================================

VOICE_SPECIFICATION_PROMPT = """You are a voice coach for novelists who creates distinctive, consistent narrative voices. You understand that voice is how the story sounds in the reader's head—it's the author's fingerprint on every sentence.

## Story Context:
- Genre: {genre}
- Reader Avatar: {reader_avatar}
- Protagonist: {protagonist_profile}
- Tone: {tone}

## Your Task: Define the Complete Voice Specification

### 1. NARRATIVE VOICE

**Point of View:**
- POV Type: First person / Third person limited / Third person omniscient
- Whose POV are we in?
- How close are we to their thoughts?
- What are the implications for information access?

**Narrative Distance:**
- Close (inside the character's head)
- Medium (following close behind)
- Distant (observing from outside)

**Narrative Personality:**
- How does the narrator "sound"?
- What's their attitude?
- Are they reliable?
- Do they have a distinct personality?

### 2. PROSE STYLE

**Sentence Architecture:**
- Average sentence length (short: 8-12 words, medium: 15-20, long: 25+)
- Complexity (simple, compound, complex)
- Rhythm patterns (staccato, flowing, varied)
- Signature patterns

**Paragraph Style:**
- Typical length
- How paragraphs are organized
- White space philosophy

**Word Choice:**
- Vocabulary level (everyday, elevated, technical)
- Concrete vs abstract preference
- Formal vs informal register
- Time period appropriateness

### 3. TENSE & TIME

**Primary Tense:**
- Past or present
- Why this choice?

**Time Handling:**
- How flashbacks are handled
- How time transitions work
- Tense exceptions allowed

### 4. SENSORY APPROACH

**Sensory Priority:**
Which senses dominate and why?
- Visual style
- Sound treatment
- Smell and taste usage
- Tactile details

**Detail Density:**
- How many sensory details per paragraph?
- When to increase/decrease?
- What makes details specific vs generic?

### 5. DIALOGUE STYLE

**Tag Philosophy:**
- Minimal ("said" only)
- Varied tags
- Action beats instead of tags
- Mix approach

**Dialogue Rhythm:**
- Short exchanges
- Long speeches
- Interruptions
- Subtext level

**Character Voice Differentiation:**
- How do different characters sound different?
- Verbal tics
- Vocabulary differences
- Rhythm differences

### 6. STYLE GUIDE

**Do's:**
- Specific techniques that fit this voice
- Examples of good sentences for this voice

**Don'ts:**
- What to avoid
- Common mistakes for this style
- Dealbreakers

**Example Passages:**
Write 3 sample passages demonstrating the voice:
1. Action scene
2. Emotional/introspective scene
3. Dialogue scene

## Output Format (JSON):
{{
    "narrative_voice": {{
        "pov_type": "...",
        "pov_character": "...",
        "thought_access": "...",
        "information_limits": "...",
        "distance": "...",
        "narrator_personality": "...",
        "reliability": "...",
        "tone": "..."
    }},
    "prose_style": {{
        "sentence_length": {{
            "average": "...",
            "range": "...",
            "when_short": "...",
            "when_long": "..."
        }},
        "complexity": "...",
        "rhythm": "...",
        "signature_patterns": ["..."],
        "paragraph_length": "...",
        "white_space": "...",
        "vocabulary": {{
            "level": "...",
            "concrete_vs_abstract": "...",
            "register": "...",
            "period_appropriate": "..."
        }}
    }},
    "tense_rules": {{
        "primary": "...",
        "rationale": "...",
        "flashback_handling": "...",
        "transition_markers": ["..."],
        "exceptions": ["..."]
    }},
    "sensory_approach": {{
        "primary_sense": "...",
        "secondary_sense": "...",
        "visual_style": "...",
        "sound_treatment": "...",
        "smell_taste_usage": "...",
        "tactile_focus": "...",
        "detail_density": "...",
        "when_more_detail": "...",
        "when_less_detail": "..."
    }},
    "dialogue_style": {{
        "tag_approach": "...",
        "preferred_tags": ["..."],
        "beat_usage": "...",
        "exchange_rhythm": "...",
        "subtext_level": "...",
        "character_differentiation": {{
            "technique": "...",
            "protagonist_voice": "...",
            "antagonist_voice": "...",
            "supporting_voices": ["..."]
        }}
    }},
    "style_guide": {{
        "dos": [
            {{"rule": "...", "example": "..."}}
        ],
        "donts": [
            {{"rule": "...", "example_of_mistake": "..."}}
        ]
    }},
    "example_passages": {{
        "action_scene": "...",
        "emotional_scene": "...",
        "dialogue_scene": "..."
    }},
    "voice_consistency_markers": [
        "Things to check for voice drift"
    ],
    "voice_specification_score": 90
}}
"""


# =============================================================================
# DRAFT GENERATION - SCENE LEVEL PROMPT
# =============================================================================

SCENE_GENERATION_PROMPT = """You are a novelist writing a scene with precision and craft. Write publishable prose that brings this scene to life.

## VOICE SPECIFICATION
{voice_specification}

## SCENE BLUEPRINT
- Scene Number: {scene_number} of Chapter {chapter_number}
- Scene Question: {scene_question}
- Scene Type: {scene_type}
- Location: {location}
- Characters Present: {characters}
- Word Target: {word_target} words

## SCENE BEATS TO EXECUTE
{beat_outline}

## CHARACTER REFERENCE
{character_reference}

## PREVIOUS CONTEXT
{previous_context}

## WRITING INSTRUCTIONS

1. **OPEN STRONG**: Start in the middle of something happening. No throat-clearing.

2. **EXECUTE THE BEATS**: Hit each story beat while making them feel organic.

3. **VOICE CONSISTENCY**: Match the specified voice throughout:
   - POV: {pov_type}
   - Tense: {tense}
   - Tone: {tone}
   - Sentence Style: {sentence_style}

4. **SENSORY GROUNDING**: Include specific sensory details (1-2 per paragraph):
   - Visual: What do we see?
   - Other senses: Sound, smell, touch, taste as appropriate

5. **DIALOGUE RULES**:
   - Each character sounds distinct
   - Subtext > Text (what's unsaid matters)
   - {dialogue_approach}

6. **SCENE DYNAMICS**:
   - Clear scene question at stake
   - Tension throughout
   - Turning point moment
   - Clear outcome: {expected_outcome}

7. **CLOSING**: End with {hook_type} that propels forward

## DO NOT:
- Start with description blocks
- Use clichéd phrases
- Tell emotions instead of showing them
- Write generic placeholder details
- Lose the character's voice
- Forget the scene's purpose

## WRITE THE SCENE NOW:

---
"""


# =============================================================================
# EXECUTOR FUNCTIONS
# =============================================================================

async def execute_plot_structure(context: ExecutionContext) -> Dict[str, Any]:
    """Execute plot structure agent with comprehensive story architecture."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    # Gather all context
    story_question = context.inputs.get("story_question", {})
    character_arch = context.inputs.get("character_architecture", {})
    relationships = context.inputs.get("relationship_dynamics", {})
    thematic = context.inputs.get("thematic_architecture", {})
    
    target_word_count = constraints.get("target_word_count", 80000)
    num_chapters = constraints.get("num_chapters", max(10, min(40, target_word_count // 3500)))

    prompt = PLOT_STRUCTURE_PROMPT.format(
        central_dramatic_question=story_question.get("central_dramatic_question", ""),
        protagonist_arc=_format_for_prompt(character_arch.get("protagonist_arc", {})),
        relationship_dynamics=_format_for_prompt(relationships, max_length=1500),
        theme=_format_for_prompt(thematic.get("primary_theme", {})),
        genre=constraints.get("genre", "general fiction"),
        target_word_count=target_word_count,
        num_chapters=num_chapters,
        words_per_chapter=target_word_count // num_chapters
    )

    if llm:
        try:
            response = await llm.generate(prompt, response_format="json", max_tokens=6000)
            response = _calculate_act_word_counts(response, target_word_count, num_chapters)
            return response
        except Exception as e:
            logger.error(f"Plot structure generation failed: {e}")
            return _get_plot_structure_fallback(target_word_count, num_chapters)
    else:
        return _get_plot_structure_fallback(target_word_count, num_chapters)


async def execute_pacing_design(context: ExecutionContext) -> Dict[str, Any]:
    """Execute pacing design agent."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    plot_structure = context.inputs.get("plot_structure", {})
    target_word_count = constraints.get("target_word_count", 80000)
    num_chapters = constraints.get("num_chapters", 25)

    prompt = PACING_DESIGN_PROMPT.format(
        plot_structure=_format_for_prompt(plot_structure, max_length=3000),
        genre=constraints.get("genre", "general fiction"),
        target_audience=constraints.get("target_audience", "adult general"),
        target_word_count=target_word_count,
        num_chapters=num_chapters
    )

    if llm:
        try:
            response = await llm.generate(prompt, response_format="json", max_tokens=5000)
            return response
        except Exception as e:
            logger.error(f"Pacing design generation failed: {e}")
            return _get_pacing_fallback(num_chapters)
    else:
        return _get_pacing_fallback(num_chapters)


async def execute_chapter_blueprint(context: ExecutionContext) -> Dict[str, Any]:
    """Execute chapter blueprint agent with detailed scene-level planning."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    # Gather all context
    plot_structure = context.inputs.get("plot_structure", {})
    pacing_design = context.inputs.get("pacing_design", {})
    character_arch = context.inputs.get("character_architecture", {})
    world_rules = context.inputs.get("world_rules", {})
    
    target_word_count = constraints.get("target_word_count", 80000)
    num_chapters = constraints.get("num_chapters", 25)
    words_per_chapter = target_word_count // num_chapters

    prompt = CHAPTER_BLUEPRINT_PROMPT.format(
        plot_structure=_format_for_prompt(plot_structure, max_length=3000),
        pacing_design=_format_for_prompt(pacing_design, max_length=2000),
        character_architecture=_format_for_prompt(character_arch, max_length=2000),
        world_rules=_format_for_prompt(world_rules, max_length=1000),
        target_word_count=target_word_count,
        num_chapters=num_chapters,
        words_per_chapter=words_per_chapter
    )

    if llm:
        try:
            response = await llm.generate(prompt, response_format="json", max_tokens=8000)
            return response
        except Exception as e:
            logger.error(f"Chapter blueprint generation failed: {e}")
            return _get_chapter_blueprint_fallback(num_chapters, words_per_chapter)
    else:
        return _get_chapter_blueprint_fallback(num_chapters, words_per_chapter)


async def execute_voice_specification(context: ExecutionContext) -> Dict[str, Any]:
    """Execute voice specification agent."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    # Gather context
    market = context.inputs.get("market_intelligence", {})
    character_arch = context.inputs.get("character_architecture", {})

    prompt = VOICE_SPECIFICATION_PROMPT.format(
        genre=constraints.get("genre", "general fiction"),
        reader_avatar=_format_for_prompt(market.get("reader_avatar", {})),
        protagonist_profile=_format_for_prompt(character_arch.get("protagonist_profile", {})),
        tone=constraints.get("tone", "engaging and immersive")
    )

    if llm:
        try:
            response = await llm.generate(prompt, response_format="json", max_tokens=5000)
            return response
        except Exception as e:
            logger.error(f"Voice specification generation failed: {e}")
            return _get_voice_fallback()
    else:
        return _get_voice_fallback()


async def execute_draft_generation(context: ExecutionContext) -> Dict[str, Any]:
    """
    Execute draft generation agent with scene-by-scene generation.
    
    This is a coordinating function - actual chapter/scene writing 
    is done by the chapter_writer agent for memory efficiency.
    """
    llm = context.llm_client
    chapter_blueprint = context.inputs.get("chapter_blueprint", {})
    voice_spec = context.inputs.get("voice_specification", {})
    character_arch = context.inputs.get("character_architecture", {})
    world_rules = context.inputs.get("world_rules", {})

    chapters = []
    chapter_outline = chapter_blueprint.get("chapter_outline", [])
    
    logger.info(f"Starting draft generation for {len(chapter_outline)} chapters")

    for chapter in chapter_outline:
        chapter_num = chapter.get("number", len(chapters) + 1)
        chapter_title = chapter.get("title", f"Chapter {chapter_num}")
        
        logger.info(f"Generating Chapter {chapter_num}: {chapter_title}")
        
        if llm:
            try:
                # Generate chapter using detailed prompt
                chapter_text = await _generate_chapter_with_scenes(
                    llm=llm,
                    chapter=chapter,
                    voice_spec=voice_spec,
                    character_arch=character_arch,
                    world_rules=world_rules,
                    previous_chapters=chapters
                )
                
                # Generate summary for continuity
                summary = await _generate_chapter_summary(llm, chapter_text, chapter_num)
                
                chapters.append({
                    "number": chapter_num,
                    "title": chapter_title,
                    "text": chapter_text,
                    "summary": summary,
                    "word_count": len(chapter_text.split()),
                    "target_word_count": chapter.get("word_target", 3500)
                })
                
            except Exception as e:
                logger.error(f"Chapter {chapter_num} generation failed: {e}")
                chapters.append({
                    "number": chapter_num,
                    "title": chapter_title,
                    "text": f"[Chapter {chapter_num} generation failed: {e}]",
                    "summary": "Generation failed",
                    "word_count": 0,
                    "error": str(e)
                })
        else:
            # Placeholder for demo mode
            chapters.append({
                "number": chapter_num,
                "title": chapter_title,
                "text": f"[Chapter {chapter_num}: {chapter_title}]\n\n[Content would be generated here by LLM]",
                "summary": f"Chapter {chapter_num} placeholder",
                "word_count": 0
            })

    total_words = sum(c.get("word_count", 0) for c in chapters)
    
    return {
        "chapters": chapters,
        "chapter_metadata": [
            {
                "number": c["number"],
                "title": c["title"],
                "word_count": c["word_count"],
                "target_met": c["word_count"] >= c.get("target_word_count", 0) * 0.8
            }
            for c in chapters
        ],
        "word_counts": {str(c["number"]): c["word_count"] for c in chapters},
        "total_word_count": total_words,
        "generation_complete": True
    }


async def _generate_chapter_with_scenes(
    llm,
    chapter: Dict[str, Any],
    voice_spec: Dict[str, Any],
    character_arch: Dict[str, Any],
    world_rules: Dict[str, Any],
    previous_chapters: List[Dict[str, Any]]
) -> str:
    """Generate a single chapter by combining scene-by-scene generation."""
    
    chapter_text_parts = []
    scenes = chapter.get("scenes", [])
    
    # Build previous context summary
    previous_context = ""
    if previous_chapters:
        last_chapter = previous_chapters[-1]
        previous_context = f"Previous chapter ended: {last_chapter.get('summary', 'Unknown')}"
    
    # Get voice parameters
    narrative_voice = voice_spec.get("narrative_voice", {})
    prose_style = voice_spec.get("prose_style", {})
    dialogue_style = voice_spec.get("dialogue_style", {})
    
    for scene in scenes:
        scene_prompt = SCENE_GENERATION_PROMPT.format(
            voice_specification=_format_for_prompt(voice_spec, max_length=1000),
            scene_number=scene.get("scene_number", 1),
            chapter_number=chapter.get("number", 1),
            scene_question=scene.get("scene_question", "What happens next?"),
            scene_type=scene.get("scene_type", "action"),
            location=scene.get("location", "Unknown location"),
            characters=", ".join(scene.get("characters", ["Protagonist"])),
            word_target=scene.get("word_target", 1500),
            beat_outline="\n".join(scene.get("beat_outline", ["Scene unfolds"])),
            character_reference=_format_for_prompt(character_arch, max_length=800),
            previous_context=previous_context,
            pov_type=narrative_voice.get("pov_type", "Third person limited"),
            tense=voice_spec.get("tense_rules", {}).get("primary", "past"),
            tone=narrative_voice.get("tone", "engaging"),
            sentence_style=prose_style.get("rhythm", "varied"),
            dialogue_approach=dialogue_style.get("tag_approach", "minimal tags"),
            expected_outcome=scene.get("outcome", "progression"),
            hook_type="momentum" if scene.get("scene_number", 1) < len(scenes) else chapter.get("closing_hook", {}).get("hook_type", "question")
        )
        
        try:
            scene_text = await llm.generate(
                scene_prompt,
                max_tokens=scene.get("word_target", 1500) * 2,
                temperature=0.8
            )
            chapter_text_parts.append(scene_text)
            
            # Update context for next scene
            previous_context = f"Previous scene: {scene_text[-500:]}"
            
        except Exception as e:
            logger.error(f"Scene generation failed: {e}")
            chapter_text_parts.append(f"[Scene {scene.get('scene_number', '?')} failed: {e}]")
    
    return "\n\n".join(chapter_text_parts)


async def _generate_chapter_summary(llm, chapter_text: str, chapter_num: int) -> str:
    """Generate a brief summary of the chapter for continuity tracking."""
    summary_prompt = f"""Summarize this chapter in 2-3 sentences for continuity reference.
Focus on:
1. Key plot events that happened
2. Character emotional states at the end
3. Any cliffhangers or unresolved tensions

Chapter {chapter_num}:
{chapter_text[:4000]}...

Summary:"""
    
    try:
        return await llm.generate(summary_prompt, max_tokens=200, temperature=0.5)
    except Exception:
        return f"Chapter {chapter_num} completed."


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _format_for_prompt(data: Dict[str, Any], max_length: int = 2000) -> str:
    """Format data for prompt inclusion with length limit."""
    if not data:
        return "Not specified"
    formatted = json.dumps(data, indent=2)
    if len(formatted) > max_length:
        formatted = formatted[:max_length] + "\n... [truncated]"
    return formatted


def _calculate_act_word_counts(response: Dict[str, Any], target_words: int, num_chapters: int) -> Dict[str, Any]:
    """Calculate and fill in word count targets for each act."""
    act_structure = response.get("act_structure", {})
    
    # Calculate word counts per act
    act_percentages = {
        "act_1": 0.25,
        "act_2a": 0.25,
        "act_2b": 0.25,
        "act_3": 0.25
    }
    
    for act_name, percentage in act_percentages.items():
        if act_name in act_structure:
            act_structure[act_name]["word_count_target"] = int(target_words * percentage)
    
    # Calculate chapter ranges
    chapters_per_section = num_chapters // 4
    act_structure.get("act_1", {})["chapter_range"] = [1, chapters_per_section]
    act_structure.get("act_2a", {})["chapter_range"] = [chapters_per_section + 1, chapters_per_section * 2]
    act_structure.get("act_2b", {})["chapter_range"] = [chapters_per_section * 2 + 1, chapters_per_section * 3]
    act_structure.get("act_3", {})["chapter_range"] = [chapters_per_section * 3 + 1, num_chapters]
    
    response["act_structure"] = act_structure
    return response


def _get_plot_structure_fallback(target_words: int, num_chapters: int) -> Dict[str, Any]:
    """Fallback plot structure."""
    words_per_act = target_words // 4
    chapters_per_act = num_chapters // 4
    
    return {
        "act_structure": {
            "act_1": {
                "percentage": 25,
                "word_count_target": words_per_act,
                "chapter_range": [1, chapters_per_act],
                "purpose": "Setup the world, introduce protagonist, establish stakes, commit to journey",
                "key_events": [
                    {"event": "Opening - establish normal world", "chapter": 1, "significance": "Reader orientation"},
                    {"event": "Inciting incident", "chapter": 2, "significance": "Story begins"},
                    {"event": "First plot point", "chapter": chapters_per_act, "significance": "Point of no return"}
                ],
                "protagonist_state": {"beginning": "Normal life", "end": "Committed to change"}
            },
            "act_2a": {
                "percentage": 25,
                "word_count_target": words_per_act,
                "chapter_range": [chapters_per_act + 1, chapters_per_act * 2],
                "purpose": "Tests, allies, enemies, learning",
                "key_events": [
                    {"event": "New world exploration", "chapter": chapters_per_act + 1, "significance": "Promise of premise"},
                    {"event": "Midpoint", "chapter": chapters_per_act * 2, "significance": "Major revelation/reversal"}
                ],
                "protagonist_state": {"beginning": "Optimistic explorer", "end": "Sobered by midpoint"}
            },
            "act_2b": {
                "percentage": 25,
                "word_count_target": words_per_act,
                "chapter_range": [chapters_per_act * 2 + 1, chapters_per_act * 3],
                "purpose": "Complications, stakes rise, approaching crisis",
                "key_events": [
                    {"event": "Bad guys close in", "chapter": chapters_per_act * 2 + 2, "significance": "Increasing pressure"},
                    {"event": "All is lost", "chapter": chapters_per_act * 3 - 1, "significance": "Lowest point"},
                    {"event": "Dark night of soul", "chapter": chapters_per_act * 3, "significance": "Internal crisis"}
                ],
                "protagonist_state": {"beginning": "Fighting back", "end": "Broken but ready to rise"}
            },
            "act_3": {
                "percentage": 25,
                "word_count_target": words_per_act,
                "chapter_range": [chapters_per_act * 3 + 1, num_chapters],
                "purpose": "Final confrontation, climax, resolution",
                "key_events": [
                    {"event": "Break into three", "chapter": chapters_per_act * 3 + 1, "significance": "New understanding"},
                    {"event": "Climax", "chapter": num_chapters - 1, "significance": "Final battle"},
                    {"event": "Resolution", "chapter": num_chapters, "significance": "New equilibrium"}
                ],
                "protagonist_state": {"beginning": "Transformed understanding", "end": "Changed person"}
            }
        },
        "major_beats": [
            {"name": "Opening Image", "description": "Establish tone and protagonist's world", "chapter_placement": 1},
            {"name": "Catalyst", "description": "Event that disrupts normal life", "chapter_placement": 2},
            {"name": "Break Into Two", "description": "Protagonist commits to new world", "chapter_placement": chapters_per_act},
            {"name": "Midpoint", "description": "Major revelation changes everything", "chapter_placement": chapters_per_act * 2},
            {"name": "All Is Lost", "description": "Protagonist's lowest point", "chapter_placement": chapters_per_act * 3 - 1},
            {"name": "Break Into Three", "description": "Solution discovered", "chapter_placement": chapters_per_act * 3 + 1},
            {"name": "Finale", "description": "Final confrontation", "chapter_placement": num_chapters - 1},
            {"name": "Final Image", "description": "New world established", "chapter_placement": num_chapters}
        ],
        "reversals": [
            {"name": "Midpoint Reversal", "what_reverses": "Understanding of true situation", "chapter": chapters_per_act * 2},
            {"name": "All Is Lost Reversal", "what_reverses": "Hope and resources", "chapter": chapters_per_act * 3 - 1}
        ],
        "point_of_no_return": {
            "moment": "End of Act 1",
            "chapter": chapters_per_act,
            "what_happens": "Protagonist commits to the journey",
            "why_irreversible": "Cannot return to old life"
        },
        "climax_design": {
            "chapter": num_chapters - 1,
            "setup": "All forces converge",
            "confrontation": "Protagonist vs antagonist",
            "crisis_choice": "Choose between want and need",
            "resolution": "Theme proven through action"
        },
        "resolution": {
            "external": "Plot conflict resolved",
            "internal": "Character transformation complete",
            "thematic": "Theme answered through action",
            "final_image": {"description": "Mirror of opening showing change"}
        },
        "plot_coherence_score": 75
    }


def _get_pacing_fallback(num_chapters: int) -> Dict[str, Any]:
    """Fallback pacing design."""
    tension_curve = []
    for i in range(1, num_chapters + 1):
        # Calculate tension based on position
        if i <= num_chapters * 0.25:
            tension = 3 + (i / (num_chapters * 0.25)) * 3
        elif i <= num_chapters * 0.5:
            tension = 6 + ((i - num_chapters * 0.25) / (num_chapters * 0.25)) * 2
        elif i <= num_chapters * 0.75:
            tension = 4 if i == int(num_chapters * 0.7) else 7 + ((i - num_chapters * 0.5) / (num_chapters * 0.25))
        else:
            tension = 8 + ((i - num_chapters * 0.75) / (num_chapters * 0.25)) * 2
        
        tension = min(10, max(1, int(tension)))
        tension_curve.append({
            "chapter": i,
            "tension_level": tension,
            "description": f"Chapter {i} tension point"
        })
    
    return {
        "tension_curve": tension_curve,
        "overall_tension_map": {
            "opening_tension": 4,
            "act_1_peak": 6,
            "midpoint_tension": 8,
            "all_is_lost": 3,
            "climax_peak": 10,
            "resolution": 3
        },
        "scene_density_by_act": {
            "act_1": {"action_percentage": 30, "reaction_percentage": 25, "dialogue_percentage": 30, "reflection_percentage": 15},
            "act_2a": {"action_percentage": 40, "reaction_percentage": 20, "dialogue_percentage": 30, "reflection_percentage": 10},
            "act_2b": {"action_percentage": 50, "reaction_percentage": 15, "dialogue_percentage": 25, "reflection_percentage": 10},
            "act_3": {"action_percentage": 60, "reaction_percentage": 10, "dialogue_percentage": 25, "reflection_percentage": 5}
        },
        "prose_rhythm_guide": {
            "tense_scenes": "Short sentences, fragments, white space",
            "contemplative_scenes": "Longer flowing sentences",
            "dialogue_scenes": "Rapid exchanges, action beats",
            "emotional_scenes": "Varied length for emphasis"
        },
        "chapter_pacing": [
            {
                "chapter": i,
                "word_target": 3500,
                "pacing_type": "medium",
                "scene_count": 2,
                "entry_tension": tension_curve[i-1]["tension_level"] - 1,
                "exit_tension": tension_curve[i-1]["tension_level"],
                "hook_type": "question"
            }
            for i in range(1, num_chapters + 1)
        ],
        "pacing_coherence_score": 75
    }


def _get_chapter_blueprint_fallback(num_chapters: int, words_per_chapter: int) -> Dict[str, Any]:
    """Fallback chapter blueprint."""
    chapters = []
    for i in range(1, num_chapters + 1):
        act = 1 if i <= num_chapters * 0.25 else (2 if i <= num_chapters * 0.75 else 3)
        
        chapters.append({
            "number": i,
            "title": f"Chapter {i}",
            "act": act,
            "word_target": words_per_chapter,
            "pov": "Protagonist",
            "chapter_goal": {
                "must_happen": f"Chapter {i} key event",
                "state_change": "Story advances",
                "why_necessary": "Plot progression"
            },
            "opening_hook": {
                "approach": "In medias res",
                "tension_established": "Question raised"
            },
            "scenes": [
                {
                    "scene_number": 1,
                    "scene_question": f"Chapter {i}, Scene 1 question",
                    "characters": ["Protagonist"],
                    "location": "Primary location",
                    "scene_type": "action",
                    "conflict_type": "external",
                    "beat_outline": ["Opening beat", "Development", "Turning point"],
                    "outcome": "partial",
                    "word_target": words_per_chapter // 2
                },
                {
                    "scene_number": 2,
                    "scene_question": f"Chapter {i}, Scene 2 question",
                    "characters": ["Protagonist", "Supporting"],
                    "location": "Secondary location",
                    "scene_type": "dialogue",
                    "conflict_type": "interpersonal",
                    "beat_outline": ["Scene setup", "Exchange", "Resolution/hook"],
                    "outcome": "twist",
                    "word_target": words_per_chapter // 2
                }
            ],
            "closing_hook": {
                "description": "Chapter ends with forward momentum",
                "hook_type": "question"
            }
        })
    
    return {
        "chapter_outline": chapters,
        "global_continuity": {
            "story_timeline": [{"chapter": i, "day": i, "key_events": [f"Ch{i} events"]} for i in range(1, num_chapters + 1)]
        },
        "word_count_distribution": {
            "act_1_total": words_per_chapter * (num_chapters // 4),
            "act_2_total": words_per_chapter * (num_chapters // 2),
            "act_3_total": words_per_chapter * (num_chapters // 4),
            "grand_total": words_per_chapter * num_chapters
        },
        "blueprint_completeness_score": 70
    }


def _get_voice_fallback() -> Dict[str, Any]:
    """Fallback voice specification."""
    return {
        "narrative_voice": {
            "pov_type": "Third person limited",
            "pov_character": "Protagonist",
            "thought_access": "Full access to POV character's thoughts",
            "information_limits": "Only knows what POV character observes/knows",
            "distance": "Close",
            "narrator_personality": "Observant, empathetic, occasionally wry",
            "reliability": "Reliable but limited by character's perception",
            "tone": "Contemplative with moments of intensity"
        },
        "prose_style": {
            "sentence_length": {"average": "15-20 words", "range": "5-30 words"},
            "complexity": "Mix of simple and compound-complex",
            "rhythm": "Varied based on scene tension",
            "paragraph_length": "3-5 sentences typically",
            "vocabulary": {"level": "Accessible but precise", "register": "Contemporary"}
        },
        "tense_rules": {
            "primary": "Past tense",
            "flashback_handling": "Past perfect for transitions, then simple past",
            "exceptions": ["Immediate sensory in present for emphasis"]
        },
        "sensory_approach": {
            "primary_sense": "Visual",
            "detail_density": "1-2 specific details per paragraph",
            "when_more_detail": "New locations, emotional peaks",
            "when_less_detail": "Action sequences, familiar settings"
        },
        "dialogue_style": {
            "tag_approach": "Minimal - mostly 'said', action beats preferred",
            "subtext_level": "High - what's unsaid matters",
            "character_differentiation": {"technique": "Vocabulary, rhythm, verbal tics"}
        },
        "style_guide": {
            "dos": [
                {"rule": "Show don't tell", "example": "Her hands trembled vs She was nervous"},
                {"rule": "Active voice", "example": "She grabbed the knife vs The knife was grabbed"},
                {"rule": "Specific details", "example": "A 1967 Mustang vs a car"}
            ],
            "donts": [
                {"rule": "Adverb overuse", "example_of_mistake": "She said angrily"},
                {"rule": "Purple prose", "example_of_mistake": "The cerulean orbs of her optical organs"},
                {"rule": "Info dumps", "example_of_mistake": "As you know, Bob, the war started..."}
            ]
        },
        "voice_specification_score": 75
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
