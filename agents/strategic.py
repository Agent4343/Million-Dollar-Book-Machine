"""
Strategic Foundation Agents (Layers 0-4)

Production-ready agents that establish the foundational strategy for the book:
- Orchestrator (Layer 0)
- Market & Reader Intelligence
- Core Concept Definition
- Thematic Architecture
- Central Story Question

These agents create the DNA of the book that all subsequent agents build upon.
"""

from typing import Dict, Any, List, Optional
from core.orchestrator import ExecutionContext
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# LAYER 0: ORCHESTRATOR
# =============================================================================

async def execute_orchestrator(context: ExecutionContext) -> Dict[str, Any]:
    """Execute orchestrator agent - initializes the pipeline with validation."""
    constraints = context.inputs.get("user_constraints", {})
    
    # Validate minimum required constraints
    required_fields = ["genre", "target_word_count"]
    missing = [f for f in required_fields if f not in constraints]
    
    # Set sensible defaults for optional fields
    defaults = {
        "genre": "literary fiction",
        "target_word_count": 80000,
        "tone": "engaging",
        "pov": "third person limited",
        "target_audience": "adult general",
        "setting_era": "contemporary",
        "num_chapters": None  # Will be calculated based on word count
    }
    
    for key, value in defaults.items():
        if key not in constraints:
            constraints[key] = value
    
    # Calculate optimal chapter count if not specified
    if constraints.get("num_chapters") is None:
        word_count = constraints.get("target_word_count", 80000)
        # Optimal chapter length: 3000-4000 words
        constraints["num_chapters"] = max(10, min(40, word_count // 3500))
    
    return {
        "agent_map": list(constraints.keys()),
        "stage_order": [
            "market_intelligence", "concept_definition", "thematic_architecture",
            "story_question", "world_rules", "character_architecture",
            "relationship_dynamics", "plot_structure", "pacing_design",
            "chapter_blueprint", "voice_specification", "draft_generation",
            "continuity_audit", "emotional_validation", "originality_scan",
            "structural_rewrite", "line_edit", "beta_simulation",
            "final_validation", "publishing_package"
        ],
        "state_json": {
            "initialized": True,
            "title": context.project.title,
            "constraints": constraints,
            "validation_passed": len(missing) == 0
        },
        "checkpoint_rules": {
            "auto_save": True,
            "save_after_each_layer": True,
            "max_checkpoints": 20,
            "save_on_chapter_complete": True
        }
    }


# =============================================================================
# PROMPTS - Professional Grade
# =============================================================================

MARKET_INTELLIGENCE_PROMPT = """You are a senior book market analyst with 20 years of publishing experience. Your analysis directly influences whether books succeed commercially.

## Project Parameters:
- Genre: {genre}
- Target Word Count: {target_word_count} words
- Author's Vision: {author_vision}
- Additional Constraints: {additional_constraints}

## Your Analysis Must Include:

### 1. READER AVATAR (Be Specific)
Create a vivid, three-dimensional portrait of the ideal reader:

**Demographics:**
- Age range (specific, e.g., "32-45")
- Education/profession patterns
- Geographic concentrations
- Income bracket (affects pricing/format preferences)

**Psychographics:**
- Core values and beliefs
- Current life stage and challenges
- Entertainment preferences beyond books
- Social media behavior and communities

**Reading Behavior:**
- Reading frequency (books/month)
- Format preferences (ebook vs print vs audio)
- Discovery channels (how they find new books)
- Series vs standalone preference
- Reading occasions (commute, evening, etc.)

**Pain Points:**
- What problems does this reader face?
- What emotional needs are unmet?
- What questions keep them up at night?
- What transformation do they secretly desire?

### 2. MARKET GAP ANALYSIS
Identify the specific opportunity:

**Unmet Need:**
- What are readers asking for but not getting?
- What frustrations do they express in reviews of similar books?
- What's missing from current offerings?

**Timing Opportunity:**
- Current cultural moments this book can tap into
- Trends on the rise vs decline
- Seasonal considerations

**Competitive Landscape:**
- How saturated is this niche?
- What's the discovery opportunity?
- Price point expectations

### 3. POSITIONING STRATEGY
How this book will stand out:

**Unique Value Proposition:**
- The ONE thing this book offers that others don't
- Why this matters to the target reader
- How to articulate this in marketing

**Differentiation Angles:**
- 3-5 specific ways this book differs from competition
- Which angle is strongest for marketing?

**Category Strategy:**
- Primary category for listing
- Secondary categories for discoverability
- Keywords and tags

### 4. COMPETITIVE ANALYSIS
Analyze 4-6 comparable titles:

For each comp:
- Title, author, publication year
- Amazon rank/sales estimate
- What it does exceptionally well
- Critical gaps or reader complaints
- How our book improves on it
- What we can learn from its success/failure

## Output Format (JSON):
{{
    "reader_avatar": {{
        "demographics": {{
            "age_range": "...",
            "primary_professions": ["..."],
            "education_level": "...",
            "geographic_focus": "...",
            "income_bracket": "..."
        }},
        "psychographics": {{
            "core_values": ["..."],
            "life_stage": "...",
            "entertainment_preferences": ["..."],
            "online_communities": ["..."]
        }},
        "reading_behavior": {{
            "books_per_month": "...",
            "format_preference": "...",
            "discovery_channels": ["..."],
            "reading_occasions": ["..."]
        }},
        "pain_points": ["..."],
        "desired_transformation": "..."
    }},
    "market_gap": {{
        "unmet_need": "...",
        "reader_frustrations": ["..."],
        "timing_opportunity": "...",
        "saturation_level": "...",
        "price_expectations": "..."
    }},
    "positioning_angle": {{
        "unique_value_proposition": "...",
        "differentiators": ["..."],
        "primary_angle": "...",
        "category_strategy": {{
            "primary": "...",
            "secondary": ["..."],
            "keywords": ["..."]
        }}
    }},
    "comp_analysis": [
        {{
            "title": "...",
            "author": "...",
            "year": "...",
            "estimated_rank": "...",
            "strengths": ["..."],
            "gaps": ["..."],
            "lessons": "..."
        }}
    ],
    "market_viability_score": 85,
    "recommended_adjustments": ["..."]
}}
"""

CONCEPT_DEFINITION_PROMPT = """You are a bestselling author's developmental editor, known for crystallizing book concepts that resonate deeply with readers.

## Market Analysis:
{market_intelligence}

## Author's Vision:
{user_constraints}

## Your Task: Define the Book's Core Concept

The concept is the DNA of the book. It must be:
- **Memorable**: Can be repeated word-for-word
- **Intriguing**: Creates immediate curiosity
- **Unique**: Not "another book about X"
- **Marketable**: Works in a query, pitch, or ad

### 1. ONE-LINE HOOK (The Logline)
Create a single sentence (under 25 words) that:
- Contains a protagonist with a defining characteristic
- States a goal or situation
- Implies the central conflict or stakes
- Creates a "I need to know more" reaction

Test: Would someone repeat this to a friend?

Examples of great hooks:
- "A boy wizard discovers he's famous in a hidden magical world, but the dark lord who killed his parents wants to finish the job."
- "A shark terrorizes a beach town, and only three men can stop it."
- "A chef who's lost her sense of taste must win a competition to save her grandmother's restaurant."

### 2. CORE PROMISE
What will readers FEEL by the end?

**Emotional Transformation:**
- Starting emotional state when they pick up the book
- Ending emotional state when they finish
- The journey between

**Value Delivered:**
- What insight, escape, or experience do they get?
- What question gets answered?
- What itch gets scratched?

**The Payoff:**
- Why will they recommend this book?
- What moment will stick with them?
- What will they think about days later?

### 3. UNIQUE ENGINE
What makes this book work in a way others don't?

**The Secret Sauce:**
- What's the unique mechanism or approach?
- Why hasn't this been done exactly this way before?
- What gives you permission to tell this story?

**Credibility:**
- What makes this authentic?
- Why will readers trust this perspective?

### 4. ELEVATOR PITCH (30 seconds)
2-3 sentences that could be spoken aloud:
- Sentence 1: Setup and protagonist
- Sentence 2: Conflict and stakes
- Sentence 3: The promise/hook

### 5. BACK COVER COPY (150 words)
The actual text that would go on the back of the book:
- Opening hook
- Character introduction
- Stakes and conflict
- Closing question or hook (no spoilers)

## Output Format (JSON):
{{
    "one_line_hook": "...",
    "hook_analysis": {{
        "protagonist_element": "...",
        "goal_element": "...",
        "conflict_element": "...",
        "intrigue_factor": "..."
    }},
    "core_promise": {{
        "emotional_journey": {{
            "starting_state": "...",
            "ending_state": "...",
            "transformation_arc": "..."
        }},
        "value_delivered": "...",
        "memorable_payoff": "...",
        "recommendation_trigger": "..."
    }},
    "unique_engine": {{
        "mechanism": "...",
        "novelty_factor": "...",
        "permission_to_tell": "...",
        "credibility_source": "..."
    }},
    "elevator_pitch": "...",
    "back_cover_copy": "...",
    "concept_strength_score": 85,
    "potential_weaknesses": ["..."],
    "strengthening_suggestions": ["..."]
}}
"""

THEMATIC_ARCHITECTURE_PROMPT = """You are a literary analyst who has studied the thematic structures of award-winning novels. You understand that theme is not decoration—it's the skeleton that holds everything together.

## Core Concept:
{concept_definition}

## Genre Context:
{genre}

## Your Task: Build the Thematic Architecture

Theme is the "why" behind your story. It's the argument your book makes about human existence. Without strong theme, even well-plotted books feel empty.

### 1. PRIMARY THEME (The Central Argument)

**Thematic Statement:**
Express the theme as a complete statement, not a single word.
- Bad: "Love"
- Good: "Love requires the courage to be vulnerable, even when vulnerability has led to pain."

**Universal Truth:**
What aspect of human experience does this touch?
- Why does this matter to anyone, anywhere, at any time?
- What fundamental question about existence does it address?

**Arguability:**
A good theme is ARGUABLE. Reasonable people could disagree.
- If everyone agrees, it's a platitude, not a theme.
- The counter-argument should be defensible.

### 2. COUNTER-THEME (The Opposition)

**Counter Statement:**
The opposite argument that's equally valid.
- This isn't the "villain's view"—it's a legitimate alternative.
- The story's tension comes from both being partially true.

**Representation:**
How does this counter-theme appear in the story?
- Through which characters?
- Through which situations?
- Through which consequences?

### 3. VALUE CONFLICT (The Engine)

The heart of your story is a conflict between two GOOD things that can't coexist:
- Love vs. Duty
- Freedom vs. Security
- Truth vs. Loyalty
- Individual vs. Community
- Justice vs. Mercy
- Ambition vs. Contentment

**Value A:** What is it? Why is it valuable?
**Value B:** What is it? Why is it valuable?
**Why They Conflict:** Why can't the protagonist have both?
**The Choice:** What must be sacrificed?

### 4. THEMATIC QUESTION

The question the story explores (NOT answers definitively):
- Must be open-ended
- Should haunt the reader after finishing
- The story argues multiple sides

### 5. THEMATIC EXPRESSION PLAN

How theme will manifest throughout the book:
- **Through Plot:** Key moments that embody the theme
- **Through Character:** How character arcs reflect theme
- **Through Symbol:** Recurring images/objects that carry meaning
- **Through Dialogue:** Lines that articulate the theme
- **Through Setting:** How environment reflects theme

## Output Format (JSON):
{{
    "primary_theme": {{
        "statement": "...",
        "universal_truth": "...",
        "why_it_matters": "...",
        "arguability_check": "..."
    }},
    "counter_theme": {{
        "statement": "...",
        "validity": "...",
        "representation_plan": {{
            "characters": ["..."],
            "situations": ["..."],
            "consequences": ["..."]
        }}
    }},
    "value_conflict": {{
        "value_a": {{
            "name": "...",
            "why_valuable": "...",
            "what_protagonist_gains": "..."
        }},
        "value_b": {{
            "name": "...",
            "why_valuable": "...",
            "what_protagonist_gains": "..."
        }},
        "incompatibility": "...",
        "required_sacrifice": "..."
    }},
    "thematic_question": "...",
    "expression_plan": {{
        "through_plot": ["..."],
        "through_character": ["..."],
        "through_symbol": {{
            "symbol": "...",
            "meaning": "...",
            "occurrences": ["..."]
        }},
        "key_thematic_dialogue": ["..."],
        "setting_reflection": "..."
    }},
    "theme_coherence_score": 90
}}
"""

STORY_QUESTION_PROMPT = """You are a screenwriting professor who has analyzed hundreds of successful narratives. You know that reader engagement depends on a single, clear dramatic question.

## Thematic Architecture:
{thematic_architecture}

## Core Concept:
{concept_definition}

## Genre:
{genre}

## Your Task: Define the Central Dramatic Question

The Central Dramatic Question (CDQ) is the spine of your story. Everything that happens either advances toward or retreats from answering this question.

### 1. THE CENTRAL DRAMATIC QUESTION

Formulate a single yes/no question that:
- Is answered at the climax
- Has clear stakes if "yes" vs "no"
- Keeps readers turning pages
- Ties directly to the protagonist's goal

**Structure:**
"Will [PROTAGONIST] [ACHIEVE GOAL] despite [OBSTACLE]?"

**Examples:**
- "Will Frodo destroy the ring before Sauron's forces stop him?"
- "Will Elizabeth and Darcy overcome their pride and prejudice to find love?"
- "Will the family escape the house before the ghosts kill them?"

**Test:** Can you point to the exact scene where this question is answered?

### 2. STAKES LADDER (Escalating Consequences)

Stakes must escalate. Early chapters have small stakes; later chapters have devastating ones.

**Level 1 - Surface Stakes (Act 1):**
What does the protagonist initially risk?
- Career, money, reputation, convenience
- What they'll lose if they fail here

**Level 2 - Personal Stakes (Mid-Act 2):**
What becomes at risk as they go deeper?
- Relationships, identity, beliefs
- What they'll lose if they quit now

**Level 3 - Ultimate Stakes (Act 3):**
What's at risk at the climax?
- Life, soul, everything they care about
- The worst possible outcome

**Level 4 - Universal Stakes (Theme):**
What does this mean beyond the protagonist?
- What larger truth is at stake?
- What will this prove about humanity?

### 3. BINARY OUTCOME

Define both possible endings with equal specificity:

**If YES (Success):**
- External result
- Internal transformation
- Relationship changes
- Thematic confirmation

**If NO (Failure):**
- External consequence
- Internal devastation
- Relationship destruction
- Thematic implication

Both outcomes must be MEANINGFUL. If failure doesn't hurt, success doesn't matter.

### 4. READER INVESTMENT STRATEGY

Why will readers CARE about this question?

**Relatability:**
- What universal experience does this tap into?
- What has the reader felt that connects them?

**Emotional Hooks:**
- What emotions will drive engagement?
- Fear of? Hope for? Curiosity about?

**Curiosity Drivers:**
- What questions will keep them reading?
- What mystery elements exist?

**Identification:**
- Why will readers root for the protagonist?
- What makes them sympathetic despite flaws?

## Output Format (JSON):
{{
    "central_dramatic_question": "...",
    "cdq_analysis": {{
        "protagonist": "...",
        "goal": "...",
        "obstacle": "...",
        "climax_scene_description": "..."
    }},
    "stakes_ladder": {{
        "level_1_surface": {{
            "risk": "...",
            "consequence": "...",
            "when_established": "..."
        }},
        "level_2_personal": {{
            "risk": "...",
            "consequence": "...",
            "escalation_trigger": "..."
        }},
        "level_3_ultimate": {{
            "risk": "...",
            "consequence": "...",
            "point_of_no_return": "..."
        }},
        "level_4_universal": {{
            "thematic_risk": "...",
            "what_it_proves": "..."
        }}
    }},
    "binary_outcome": {{
        "success": {{
            "external": "...",
            "internal": "...",
            "relationships": "...",
            "thematic": "..."
        }},
        "failure": {{
            "external": "...",
            "internal": "...",
            "relationships": "...",
            "thematic": "..."
        }}
    }},
    "reader_investment": {{
        "universal_experience": "...",
        "emotional_hooks": ["..."],
        "curiosity_drivers": ["..."],
        "identification_factors": ["..."],
        "sympathy_builders": ["..."]
    }},
    "question_strength_score": 90
}}
"""


# =============================================================================
# EXECUTOR FUNCTIONS WITH ERROR HANDLING
# =============================================================================

async def execute_market_intelligence(context: ExecutionContext) -> Dict[str, Any]:
    """Execute market intelligence agent with robust error handling."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    prompt = MARKET_INTELLIGENCE_PROMPT.format(
        genre=constraints.get("genre", "general fiction"),
        target_word_count=constraints.get("target_word_count", 80000),
        author_vision=constraints.get("author_vision", constraints.get("premise", "Not specified")),
        additional_constraints=_format_constraints(constraints)
    )

    if llm:
        try:
            response = await llm.generate(prompt, response_format="json", max_tokens=4000)
            # Validate response has required fields
            response = _validate_market_response(response)
            return response
        except Exception as e:
            logger.error(f"Market intelligence generation failed: {e}")
            return _get_market_intelligence_fallback(constraints)
    else:
        return _get_market_intelligence_fallback(constraints)


async def execute_concept_definition(context: ExecutionContext) -> Dict[str, Any]:
    """Execute concept definition agent."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    prompt = CONCEPT_DEFINITION_PROMPT.format(
        market_intelligence=_format_for_prompt(context.inputs.get("market_intelligence", {})),
        user_constraints=_format_constraints(constraints)
    )

    if llm:
        try:
            response = await llm.generate(prompt, response_format="json", max_tokens=3000)
            response = _validate_concept_response(response)
            return response
        except Exception as e:
            logger.error(f"Concept definition generation failed: {e}")
            return _get_concept_fallback(constraints)
    else:
        return _get_concept_fallback(constraints)


async def execute_thematic_architecture(context: ExecutionContext) -> Dict[str, Any]:
    """Execute thematic architecture agent."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    prompt = THEMATIC_ARCHITECTURE_PROMPT.format(
        concept_definition=_format_for_prompt(context.inputs.get("concept_definition", {})),
        genre=constraints.get("genre", "general fiction")
    )

    if llm:
        try:
            response = await llm.generate(prompt, response_format="json", max_tokens=3000)
            return response
        except Exception as e:
            logger.error(f"Thematic architecture generation failed: {e}")
            return _get_thematic_fallback()
    else:
        return _get_thematic_fallback()


async def execute_story_question(context: ExecutionContext) -> Dict[str, Any]:
    """Execute story question agent."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    prompt = STORY_QUESTION_PROMPT.format(
        thematic_architecture=_format_for_prompt(context.inputs.get("thematic_architecture", {})),
        concept_definition=_format_for_prompt(context.inputs.get("concept_definition", {})),
        genre=constraints.get("genre", "general fiction")
    )

    if llm:
        try:
            response = await llm.generate(prompt, response_format="json", max_tokens=3000)
            return response
        except Exception as e:
            logger.error(f"Story question generation failed: {e}")
            return _get_story_question_fallback()
    else:
        return _get_story_question_fallback()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _format_constraints(constraints: Dict[str, Any]) -> str:
    """Format constraints for inclusion in prompts."""
    if not constraints:
        return "No additional constraints specified."
    
    lines = []
    for key, value in constraints.items():
        if key not in ["genre", "target_word_count", "author_vision"]:
            lines.append(f"- {key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(lines) if lines else "No additional constraints specified."


def _format_for_prompt(data: Dict[str, Any], max_length: int = 2000) -> str:
    """Format dictionary data for inclusion in prompts with length limit."""
    import json
    formatted = json.dumps(data, indent=2)
    if len(formatted) > max_length:
        # Truncate intelligently
        formatted = formatted[:max_length] + "\n... [truncated for context]"
    return formatted


def _validate_market_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and ensure market intelligence response has required fields."""
    required_fields = ["reader_avatar", "market_gap", "positioning_angle", "comp_analysis"]
    for field in required_fields:
        if field not in response:
            response[field] = {}
    return response


def _validate_concept_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Validate concept definition response."""
    required_fields = ["one_line_hook", "core_promise", "unique_engine", "elevator_pitch"]
    for field in required_fields:
        if field not in response:
            response[field] = "[Generation incomplete]"
    return response


def _get_market_intelligence_fallback(constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback market intelligence when LLM unavailable."""
    genre = constraints.get("genre", "fiction")
    return {
        "reader_avatar": {
            "demographics": {
                "age_range": "25-55",
                "primary_professions": ["Professional", "Creative"],
                "education_level": "College-educated",
                "geographic_focus": "English-speaking markets",
                "income_bracket": "Middle to upper-middle class"
            },
            "psychographics": {
                "core_values": ["Personal growth", "Entertainment", "Intellectual stimulation"],
                "life_stage": "Established adults seeking meaningful entertainment",
                "entertainment_preferences": ["Quality TV", "Podcasts", "Theater"],
                "online_communities": ["Goodreads", "Book clubs", "Literary forums"]
            },
            "reading_behavior": {
                "books_per_month": "2-4",
                "format_preference": "Ebook and audiobook primary, print for favorites",
                "discovery_channels": ["Recommendations", "Social media", "Book reviews"],
                "reading_occasions": ["Evening relaxation", "Commute", "Vacation"]
            },
            "pain_points": [
                "Finding quality books worth their time",
                "Stories that feel derivative or predictable",
                "Wanting emotional engagement without cheap manipulation"
            ],
            "desired_transformation": "To feel moved, challenged, or transported"
        },
        "market_gap": {
            "unmet_need": f"Fresh perspectives in {genre}",
            "reader_frustrations": ["Predictable plots", "Shallow characters"],
            "timing_opportunity": "Growing demand for thoughtful entertainment",
            "saturation_level": "Moderate - room for quality entries",
            "price_expectations": "$12-18 ebook, $16-28 print"
        },
        "positioning_angle": {
            "unique_value_proposition": "To be defined based on specific concept",
            "differentiators": ["Original voice", "Deep characterization", "Thematic resonance"],
            "primary_angle": "Literary quality with commercial appeal",
            "category_strategy": {
                "primary": genre.title(),
                "secondary": ["Contemporary Fiction", "Book Club Fiction"],
                "keywords": [genre, "compelling", "literary", "character-driven"]
            }
        },
        "comp_analysis": [
            {
                "title": f"[Representative {genre} title]",
                "author": "[Author]",
                "year": "2023",
                "estimated_rank": "Top 10,000",
                "strengths": ["Strong voice", "Emotional resonance"],
                "gaps": ["Pacing issues", "Underdeveloped secondary characters"],
                "lessons": "Prioritize character depth and pacing"
            }
        ],
        "market_viability_score": 75,
        "recommended_adjustments": ["Define unique angle more sharply", "Clarify target reader"]
    }


def _get_concept_fallback(constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback concept definition."""
    premise = constraints.get("premise", "A transformative journey")
    return {
        "one_line_hook": f"[Hook based on: {premise}]",
        "hook_analysis": {
            "protagonist_element": "[To be defined]",
            "goal_element": "[To be defined]",
            "conflict_element": "[To be defined]",
            "intrigue_factor": "High potential"
        },
        "core_promise": {
            "emotional_journey": {
                "starting_state": "Unfulfilled/seeking",
                "ending_state": "Transformed/resolved",
                "transformation_arc": "Through challenge and growth"
            },
            "value_delivered": "Emotional catharsis and insight",
            "memorable_payoff": "[Key moment to be developed]",
            "recommendation_trigger": "Emotional impact"
        },
        "unique_engine": {
            "mechanism": "[Unique approach to be defined]",
            "novelty_factor": "[What makes it fresh]",
            "permission_to_tell": "Universal human experience",
            "credibility_source": "Authentic character psychology"
        },
        "elevator_pitch": f"[Pitch based on: {premise}]",
        "back_cover_copy": "[To be written based on full concept development]",
        "concept_strength_score": 70,
        "potential_weaknesses": ["Needs sharper definition"],
        "strengthening_suggestions": ["Clarify unique angle", "Define protagonist more specifically"]
    }


def _get_thematic_fallback() -> Dict[str, Any]:
    """Fallback thematic architecture."""
    return {
        "primary_theme": {
            "statement": "Authentic connection requires the courage to be vulnerable",
            "universal_truth": "Human need for belonging while fearing rejection",
            "why_it_matters": "Everyone struggles with authenticity vs. protection",
            "arguability_check": "Counter: self-protection is wisdom, not weakness"
        },
        "counter_theme": {
            "statement": "Self-protection and boundaries are necessary for survival",
            "validity": "Opening yourself to others means opening yourself to harm",
            "representation_plan": {
                "characters": ["Antagonist", "Wounded mentor figure"],
                "situations": ["Betrayal consequences", "Failed vulnerability"],
                "consequences": ["Characters who opened up and were hurt"]
            }
        },
        "value_conflict": {
            "value_a": {
                "name": "Authenticity",
                "why_valuable": "True connection, self-knowledge, fulfillment",
                "what_protagonist_gains": "Real relationships, inner peace"
            },
            "value_b": {
                "name": "Self-Protection",
                "why_valuable": "Safety, control, predictability",
                "what_protagonist_gains": "Security, independence"
            },
            "incompatibility": "Cannot be fully open and fully protected simultaneously",
            "required_sacrifice": "Must risk pain to gain connection"
        },
        "thematic_question": "Is the risk of vulnerability worth the potential for genuine connection?",
        "expression_plan": {
            "through_plot": ["Protagonist's protective walls challenged", "Moments of forced vulnerability"],
            "through_character": ["Arc from guarded to open"],
            "through_symbol": {
                "symbol": "[Recurring symbol]",
                "meaning": "The barrier between self and others",
                "occurrences": ["Opening", "Midpoint", "Climax"]
            },
            "key_thematic_dialogue": ["Lines that articulate the theme's tension"],
            "setting_reflection": "Environment mirrors protagonist's internal state"
        },
        "theme_coherence_score": 75
    }


def _get_story_question_fallback() -> Dict[str, Any]:
    """Fallback story question."""
    return {
        "central_dramatic_question": "Will the protagonist overcome their internal barriers to achieve their goal?",
        "cdq_analysis": {
            "protagonist": "[Protagonist name/type]",
            "goal": "[External goal]",
            "obstacle": "[Primary obstacle]",
            "climax_scene_description": "Protagonist faces ultimate test"
        },
        "stakes_ladder": {
            "level_1_surface": {
                "risk": "Immediate goal/comfort",
                "consequence": "Disappointment, inconvenience",
                "when_established": "Opening chapters"
            },
            "level_2_personal": {
                "risk": "Relationships, identity",
                "consequence": "Isolation, self-doubt",
                "escalation_trigger": "Midpoint revelation"
            },
            "level_3_ultimate": {
                "risk": "Everything that matters",
                "consequence": "Devastation, loss of self",
                "point_of_no_return": "End of Act 2"
            },
            "level_4_universal": {
                "thematic_risk": "What the outcome means for the theme",
                "what_it_proves": "Whether the theme is true"
            }
        },
        "binary_outcome": {
            "success": {
                "external": "Goal achieved",
                "internal": "Growth/transformation complete",
                "relationships": "Deepened or reconciled",
                "thematic": "Theme affirmed through action"
            },
            "failure": {
                "external": "Goal lost",
                "internal": "Growth rejected",
                "relationships": "Destroyed or abandoned",
                "thematic": "Counter-theme victorious"
            }
        },
        "reader_investment": {
            "universal_experience": "Everyone faces internal vs external conflicts",
            "emotional_hooks": ["Hope for protagonist", "Fear of failure", "Recognition of self"],
            "curiosity_drivers": ["How will they overcome?", "What's the cost?"],
            "identification_factors": ["Relatable flaws", "Understandable desires"],
            "sympathy_builders": ["Past wounds", "Good intentions", "Underdog status"]
        },
        "question_strength_score": 75
    }


# =============================================================================
# REGISTRATION
# =============================================================================

STRATEGIC_EXECUTORS = {
    "orchestrator": execute_orchestrator,
    "market_intelligence": execute_market_intelligence,
    "concept_definition": execute_concept_definition,
    "thematic_architecture": execute_thematic_architecture,
    "story_question": execute_story_question,
}
