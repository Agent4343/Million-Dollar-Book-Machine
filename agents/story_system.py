"""
Story System Design Agents (Layers 5-7)

Production-ready agents that design the story's operating system:
- World / Context Rules
- Character Architecture  
- Relationship Dynamics

These agents create the living, breathing elements of your story world.
"""

from typing import Dict, Any, List, Optional
from core.orchestrator import ExecutionContext
import logging
import json

logger = logging.getLogger(__name__)


# =============================================================================
# WORLD RULES PROMPT
# =============================================================================

WORLD_RULES_PROMPT = """You are a master worldbuilder who has created settings for bestselling novels. You understand that world rules aren't window dressing—they're the constraints that generate conflict and meaning.

## Story Foundation:
- Story Question: {story_question}
- Theme: {theme}
- Genre: {genre}

## User Vision:
{user_constraints}

## Your Task: Design the Story World's Operating System

The world's rules should:
- Create CONSTRAINTS that force difficult choices
- Make the protagonist's journey HARDER
- Feel internally CONSISTENT and logical
- Support the THEME through metaphor

### 1. PHYSICAL RULES (The Laws of This World)

**Possibilities:**
- What CAN happen in this world?
- What special abilities, technologies, or phenomena exist?
- What resources are available?

**Impossibilities:**
- What CANNOT happen?
- These constraints should create story tension
- Breaking these rules should have consequences

**Technology/Magic Level:**
- What tools are available to solve problems?
- What limitations prevent easy solutions?
- How does this compare to our world?

**Geography & Environment:**
- Where does the story take place?
- How does geography constrain movement/action?
- What environmental challenges exist?

**Time Rules:**
- When is this set? (era, season, time pressure)
- How does time work? (deadlines, aging, urgency)
- What historical context matters?

### 2. SOCIAL RULES (How Society Operates)

**Power Structures:**
- Who has power in this world?
- How is power maintained?
- What threatens power?
- How does the protagonist relate to power?

**Social Hierarchy:**
- What classes/groups exist?
- How do they interact?
- What mobility is possible?
- What prejudices exist?

**Norms & Taboos:**
- What behavior is expected?
- What is forbidden?
- What happens when norms are violated?
- Which norms will the protagonist challenge?

**Economic Reality:**
- How do people survive/thrive?
- What is scarce?
- What is valued?
- How does money/resources flow?

### 3. POWER RULES (How Change Happens)

**Sources of Power:**
- What gives individuals power?
- Knowledge? Strength? Connections? Money? Magic?
- What power does the protagonist have/lack?

**Power Dynamics:**
- How is power transferred?
- What costs power?
- What corrupts?
- How can the powerless gain power?

**Limitations:**
- What can't power do?
- What resists control?
- What equalizes power?

### 4. WORLD BIBLE (Key Facts)

**Essential History:**
- What past events shape the present?
- What do characters remember/forget?
- What secrets lurk in history?

**Culture & Custom:**
- How do people live day-to-day?
- What rituals matter?
- What do people believe?
- What art/entertainment exists?

**Key Terminology:**
- What words are unique to this world?
- What concepts need defining?
- What language patterns exist?

**Sensory Palette:**
- What does this world LOOK like? (colors, light, architecture)
- What does it SOUND like? (ambient noise, music, silence)
- What does it SMELL like? (distinctive scents)
- What does it FEEL like? (textures, temperatures)
- What does it TASTE like? (food, air, culture)

### 5. CONSTRAINT LIST (Story Tension Generators)

Identify 5-10 specific constraints that will:
- Prevent the protagonist from taking the easy path
- Force difficult choices
- Create ticking clocks
- Limit resources
- Complicate relationships

For each constraint:
- What is it?
- Why can't the protagonist avoid it?
- How will it create conflict?

## Output Format (JSON):
{{
    "physical_rules": {{
        "possibilities": ["..."],
        "impossibilities": ["..."],
        "technology_magic_level": {{
            "description": "...",
            "key_tools": ["..."],
            "key_limitations": ["..."]
        }},
        "geography": {{
            "primary_setting": "...",
            "key_locations": ["..."],
            "environmental_challenges": ["..."],
            "movement_constraints": "..."
        }},
        "time_context": {{
            "era": "...",
            "timeline_pressure": "...",
            "relevant_history": "..."
        }}
    }},
    "social_rules": {{
        "power_structure": {{
            "who_has_power": "...",
            "how_maintained": "...",
            "protagonist_relationship": "..."
        }},
        "hierarchy": {{
            "groups": ["..."],
            "mobility": "...",
            "prejudices": ["..."]
        }},
        "norms": ["..."],
        "taboos": ["..."],
        "norm_violation_consequences": "...",
        "economics": {{
            "scarcity": "...",
            "valued_resources": ["..."],
            "economic_pressure": "..."
        }}
    }},
    "power_rules": {{
        "sources": ["..."],
        "protagonist_power": "...",
        "protagonist_power_gap": "...",
        "how_gained": "...",
        "how_lost": "...",
        "limitations": ["..."],
        "corruption_risk": "..."
    }},
    "world_bible": {{
        "essential_history": ["..."],
        "culture": {{
            "daily_life": "...",
            "rituals": ["..."],
            "beliefs": ["..."]
        }},
        "terminology": {{
            "term": "definition"
        }},
        "sensory_palette": {{
            "visual": "...",
            "auditory": "...",
            "olfactory": "...",
            "tactile": "...",
            "gustatory": "..."
        }}
    }},
    "constraint_list": [
        {{
            "constraint": "...",
            "why_unavoidable": "...",
            "conflict_generated": "...",
            "story_function": "..."
        }}
    ],
    "world_coherence_score": 90
}}
"""


# =============================================================================
# CHARACTER ARCHITECTURE PROMPT
# =============================================================================

CHARACTER_ARCHITECTURE_PROMPT = """You are a character psychologist who creates dimensional, memorable characters. You understand that character is revealed through choice under pressure, and that every character believes they are the hero of their own story.

## Story Foundation:
- Theme: {primary_theme}
- Story Question: {central_dramatic_question}
- World Rules: {world_rules}
- Genre: {genre}

## Your Task: Architect the Character System

Characters must:
- EMBODY the thematic conflict
- Have PSYCHOLOGICAL depth and consistency
- CREATE conflict through competing agendas
- CHANGE through the story (or fail to)

### 1. PROTAGONIST PROFILE

**Identity:**
- Name (meaningful, memorable)
- Age (affects worldview and capabilities)
- Role in their world (profession, position)
- Defining physical trait (something readers will picture)

**Psychological Core:**
- Core DESIRE (what they consciously pursue)
- Core FEAR (what they avoid at all costs)
- Core WOUND (the formative injury that shaped them)
- Core BELIEF (the lie or truth they build life around)
- Core STRENGTH (their superpower)
- Core FLAW (the trait that causes problems)

**Backstory That Matters:**
- The WOUND: What happened? When? Who was involved?
- How did this shape their worldview?
- What defense mechanisms did they develop?
- What false beliefs did they form?

**Voice & Personality:**
- How do they speak? (patterns, vocabulary, rhythm)
- How do they think? (organized/chaotic, optimistic/cynical)
- How do they relate to others? (trusting/suspicious, warm/cold)
- What's their sense of humor?
- What makes them distinctive?

### 2. PROTAGONIST ARC

**Starting State:**
- Who are they when we meet them?
- What's their status quo?
- What's working in their life?
- What's broken but they don't see it?

**The Lie They Believe:**
- What false belief controls their behavior?
- How did the wound create this lie?
- How does this lie protect them?
- How does this lie hurt them?

**The Truth They Need:**
- What must they learn?
- How does this truth threaten them?
- Why is accepting this truth hard?
- How will this truth free them?

**Transformation Arc:**
- How will they change?
- What will they give up?
- What will they gain?
- What choice proves transformation?

**Ending State:**
- Who do they become?
- How is this different from start?
- What can they do now that they couldn't before?

### 3. WANT VS NEED (The Engine of Internal Conflict)

**External WANT:**
- What do they consciously pursue?
- What goal do they articulate?
- What do they think will make them happy?

**Internal NEED:**
- What do they actually require for fulfillment?
- What are they blind to?
- What would actually heal their wound?

**The Conflict:**
- How does pursuing the want prevent the need?
- What must they sacrifice to get the need?
- When does this conflict become visible?

### 4. ANTAGONIST PROFILE

**Identity:**
- Name and role
- Relationship to protagonist

**Antagonist Psychology:**
- What do THEY want?
- What's THEIR wound?
- What's THEIR belief system?
- Why do they believe they're RIGHT?

**The Dark Mirror:**
- How does the antagonist represent the protagonist's shadow?
- What path does the antagonist show the protagonist could take?
- What do they have in common?
- What makes them different?

**Antagonist Strength:**
- Why are they dangerous?
- What advantage do they have?
- What makes them hard to defeat?

**Antagonist Humanity:**
- What makes them sympathetic?
- What moment reveals their humanity?
- Could the reader understand their choices?

### 5. SUPPORTING CAST

For each major supporting character (4-6 characters):

**Character Function:**
- MENTOR: Guides the protagonist
- ALLY: Supports the protagonist  
- SKEPTIC: Challenges the protagonist
- TEMPTER: Offers the easy path
- LOVE INTEREST: Reflects the protagonist's capacity for connection
- THRESHOLD GUARDIAN: Tests worthiness

**Character Design:**
- Name and relationship to protagonist
- Their own want and need (even if minor)
- How they pressure the protagonist
- Their own mini-arc
- What makes them memorable

### 6. CHARACTER CONSTELLATION

How do all characters relate to the theme?
- Which characters argue FOR the theme?
- Which characters argue AGAINST?
- Which characters show consequences of choices?
- How does each character pressure the protagonist?

## Output Format (JSON):
{{
    "protagonist_profile": {{
        "identity": {{
            "name": "...",
            "age": "...",
            "role": "...",
            "defining_physical_trait": "..."
        }},
        "psychological_core": {{
            "core_desire": "...",
            "core_fear": "...",
            "core_wound": "...",
            "core_belief": "...",
            "core_strength": "...",
            "core_flaw": "..."
        }},
        "backstory": {{
            "wound_event": "...",
            "wound_impact": "...",
            "defense_mechanisms": ["..."],
            "false_beliefs_formed": ["..."]
        }},
        "voice": {{
            "speech_patterns": "...",
            "thinking_style": "...",
            "relationship_style": "...",
            "humor": "...",
            "distinctive_traits": ["..."]
        }}
    }},
    "protagonist_arc": {{
        "starting_state": {{
            "who_they_are": "...",
            "status_quo": "...",
            "whats_working": "...",
            "whats_broken": "..."
        }},
        "lie_believed": {{
            "the_lie": "...",
            "origin": "...",
            "how_it_protects": "...",
            "how_it_hurts": "..."
        }},
        "truth_needed": {{
            "the_truth": "...",
            "why_threatening": "...",
            "why_hard_to_accept": "...",
            "how_it_frees": "..."
        }},
        "transformation": {{
            "change_description": "...",
            "what_given_up": "...",
            "what_gained": "...",
            "proof_moment": "..."
        }},
        "ending_state": "..."
    }},
    "want_vs_need": {{
        "want": {{
            "description": "...",
            "why_they_want_it": "...",
            "what_they_think_it_provides": "..."
        }},
        "need": {{
            "description": "...",
            "why_blind_to_it": "...",
            "what_it_actually_provides": "..."
        }},
        "conflict": {{
            "how_want_blocks_need": "...",
            "required_sacrifice": "...",
            "revelation_moment": "..."
        }}
    }},
    "antagonist_profile": {{
        "identity": {{
            "name": "...",
            "role": "...",
            "relationship_to_protagonist": "..."
        }},
        "psychology": {{
            "want": "...",
            "wound": "...",
            "belief_system": "...",
            "why_they_believe_theyre_right": "..."
        }},
        "dark_mirror": {{
            "shadow_element": "...",
            "alternate_path": "...",
            "common_ground": "...",
            "key_difference": "..."
        }},
        "strength": {{
            "danger": "...",
            "advantage": "...",
            "difficulty_to_defeat": "..."
        }},
        "humanity": {{
            "sympathetic_element": "...",
            "humanizing_moment": "...",
            "understandable_choices": "..."
        }}
    }},
    "supporting_cast": [
        {{
            "name": "...",
            "function": "...",
            "relationship_to_protagonist": "...",
            "their_want": "...",
            "their_need": "...",
            "how_they_pressure_protagonist": "...",
            "their_arc": "...",
            "memorable_trait": "...",
            "voice_distinctive": "..."
        }}
    ],
    "character_constellation": {{
        "theme_supporters": ["..."],
        "theme_challengers": ["..."],
        "consequence_demonstrators": ["..."],
        "pressure_dynamics": "..."
    }},
    "character_depth_score": 90
}}
"""


# =============================================================================
# RELATIONSHIP DYNAMICS PROMPT
# =============================================================================

RELATIONSHIP_DYNAMICS_PROMPT = """You are a relationship architect who understands that the emotional engine of any story is the relationships between characters. Every great book is about how people connect, conflict, and change each other.

## Character Architecture:
{character_architecture}

## Theme:
{primary_theme}

## Value Conflict:
{value_conflict}

## Your Task: Map the Relationship Dynamics

Relationships must:
- EVOLVE through the story
- CREATE emotional stakes
- REFLECT and PRESSURE the theme
- GENERATE both conflict and connection

### 1. CONFLICT WEB

Map all the significant tensions between characters:

For each conflict:
- WHO is in conflict? (Character A vs Character B)
- WHAT is the surface tension? (What they fight about)
- WHAT is the deeper tension? (What they're really fighting about)
- WHAT does each party want from the other?
- HOW does this conflict escalate?
- HOW does this conflict relate to the theme?

### 2. POWER DYNAMICS

Track how power moves through relationships:

For each key relationship:
- Who has power initially?
- What is the source of that power?
- When does power shift?
- What causes the shift?
- Where does power rest at the end?
- What does this power dynamic reveal?

### 3. DEPENDENCY ARCS

Map the web of dependency:

For each dependency:
- Who depends on whom?
- What do they depend on them for?
- Is this healthy or unhealthy?
- How does this dependency change?
- What breaks the dependency?
- What replaces it?

### 4. EMOTIONAL BEATS

For each major relationship, identify:

**The First Impression:**
- How do they meet/first interact?
- What's the immediate dynamic?
- What assumptions are made?

**The Bonding Moment:**
- What creates connection?
- What vulnerability is shown?
- What is shared?

**The Conflict Point:**
- What drives them apart?
- What wounds are inflicted?
- What's at stake?

**The Low Point:**
- When is the relationship at its worst?
- What feels irreparable?
- What's been lost?

**The Resolution:**
- How is the relationship resolved?
- What changes?
- What truth is acknowledged?

### 5. RELATIONSHIP MATRIX

Create a comprehensive map showing:
- Every significant relationship
- The type of relationship
- Start state → End state
- Key transformation moments
- Thematic function

### 6. SECONDARY RELATIONSHIPS

Don't forget relationships that support the main ones:
- Allies to each other
- Mentors and students
- Rivals
- Family dynamics
- Professional relationships
- Past relationships that influence present

## Output Format (JSON):
{{
    "conflict_web": [
        {{
            "characters": ["Character A", "Character B"],
            "surface_tension": "...",
            "deeper_tension": "...",
            "character_a_wants": "...",
            "character_b_wants": "...",
            "escalation_pattern": "...",
            "thematic_connection": "...",
            "resolution_potential": "..."
        }}
    ],
    "power_dynamics": [
        {{
            "relationship": "A and B",
            "initial_power_holder": "...",
            "power_source": "...",
            "shift_triggers": ["..."],
            "final_power_state": "...",
            "thematic_meaning": "..."
        }}
    ],
    "dependency_arcs": [
        {{
            "dependent": "...",
            "provider": "...",
            "dependency_type": "...",
            "healthy_or_unhealthy": "...",
            "evolution": "...",
            "breaking_point": "...",
            "what_replaces_it": "..."
        }}
    ],
    "emotional_beats": {{
        "relationship_name": {{
            "first_impression": {{
                "moment": "...",
                "dynamic": "...",
                "assumptions": "..."
            }},
            "bonding_moment": {{
                "trigger": "...",
                "vulnerability_shown": "...",
                "what_shared": "..."
            }},
            "conflict_point": {{
                "cause": "...",
                "wounds_inflicted": "...",
                "stakes": "..."
            }},
            "low_point": {{
                "description": "...",
                "what_feels_lost": "..."
            }},
            "resolution": {{
                "how_resolved": "...",
                "what_changes": "...",
                "truth_acknowledged": "..."
            }}
        }}
    }},
    "relationship_matrix": [
        {{
            "char_a": "...",
            "char_b": "...",
            "type": "...",
            "start_state": "...",
            "key_moments": ["..."],
            "end_state": "...",
            "thematic_function": "..."
        }}
    ],
    "secondary_relationships": [
        {{
            "relationship": "...",
            "function": "...",
            "how_it_supports_main_relationships": "..."
        }}
    ],
    "relationship_complexity_score": 85
}}
"""


# =============================================================================
# EXECUTOR FUNCTIONS
# =============================================================================

async def execute_world_rules(context: ExecutionContext) -> Dict[str, Any]:
    """Execute world rules agent with comprehensive world-building."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    # Gather context from previous agents
    story_question = context.inputs.get("story_question", {})
    thematic = context.inputs.get("thematic_architecture", {})
    
    prompt = WORLD_RULES_PROMPT.format(
        story_question=_format_for_prompt(story_question),
        theme=_format_for_prompt(thematic.get("primary_theme", {})),
        genre=constraints.get("genre", "general fiction"),
        user_constraints=_format_constraints(constraints)
    )

    if llm:
        try:
            response = await llm.generate(prompt, response_format="json", max_tokens=5000)
            response = _validate_world_rules(response)
            return response
        except Exception as e:
            logger.error(f"World rules generation failed: {e}")
            return _get_world_rules_fallback(constraints)
    else:
        return _get_world_rules_fallback(constraints)


async def execute_character_architecture(context: ExecutionContext) -> Dict[str, Any]:
    """Execute character architecture agent with deep psychological profiling."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    # Gather all required context
    thematic = context.inputs.get("thematic_architecture", {})
    story_question = context.inputs.get("story_question", {})
    world_rules = context.inputs.get("world_rules", {})
    
    prompt = CHARACTER_ARCHITECTURE_PROMPT.format(
        primary_theme=_format_for_prompt(thematic.get("primary_theme", {})),
        central_dramatic_question=story_question.get("central_dramatic_question", ""),
        world_rules=_format_for_prompt(world_rules, max_length=1500),
        genre=constraints.get("genre", "general fiction")
    )

    if llm:
        try:
            response = await llm.generate(prompt, response_format="json", max_tokens=6000)
            response = _validate_character_architecture(response)
            return response
        except Exception as e:
            logger.error(f"Character architecture generation failed: {e}")
            return _get_character_fallback(constraints)
    else:
        return _get_character_fallback(constraints)


async def execute_relationship_dynamics(context: ExecutionContext) -> Dict[str, Any]:
    """Execute relationship dynamics agent."""
    llm = context.llm_client
    
    # Gather context
    character_arch = context.inputs.get("character_architecture", {})
    thematic = context.inputs.get("thematic_architecture", {})

    prompt = RELATIONSHIP_DYNAMICS_PROMPT.format(
        character_architecture=_format_for_prompt(character_arch, max_length=3000),
        primary_theme=_format_for_prompt(thematic.get("primary_theme", {})),
        value_conflict=_format_for_prompt(thematic.get("value_conflict", {}))
    )

    if llm:
        try:
            response = await llm.generate(prompt, response_format="json", max_tokens=5000)
            return response
        except Exception as e:
            logger.error(f"Relationship dynamics generation failed: {e}")
            return _get_relationship_fallback(character_arch)
    else:
        return _get_relationship_fallback(character_arch)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _format_for_prompt(data: Dict[str, Any], max_length: int = 2000) -> str:
    """Format dictionary data for inclusion in prompts."""
    if not data:
        return "Not yet defined"
    
    formatted = json.dumps(data, indent=2)
    if len(formatted) > max_length:
        formatted = formatted[:max_length] + "\n... [truncated]"
    return formatted


def _format_constraints(constraints: Dict[str, Any]) -> str:
    """Format user constraints for prompts."""
    if not constraints:
        return "No specific constraints provided."
    
    lines = []
    key_fields = ["premise", "setting", "time_period", "tone", "special_requirements"]
    for key in key_fields:
        if key in constraints:
            lines.append(f"- {key.replace('_', ' ').title()}: {constraints[key]}")
    
    return "\n".join(lines) if lines else "Standard constraints for genre."


def _validate_world_rules(response: Dict[str, Any]) -> Dict[str, Any]:
    """Validate world rules response has required fields."""
    required = ["physical_rules", "social_rules", "power_rules", "world_bible", "constraint_list"]
    for field in required:
        if field not in response:
            response[field] = {}
    return response


def _validate_character_architecture(response: Dict[str, Any]) -> Dict[str, Any]:
    """Validate character architecture has required fields."""
    required = ["protagonist_profile", "protagonist_arc", "want_vs_need", 
                "antagonist_profile", "supporting_cast"]
    for field in required:
        if field not in response:
            response[field] = {}
    return response


def _get_world_rules_fallback(constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback world rules when LLM unavailable."""
    setting = constraints.get("setting", "contemporary urban")
    return {
        "physical_rules": {
            "possibilities": ["Modern technology", "Global travel", "Digital communication"],
            "impossibilities": ["Magic", "Supernatural elements", "Time manipulation"],
            "technology_magic_level": {
                "description": "Contemporary technology level",
                "key_tools": ["Smartphones", "Internet", "Modern transportation"],
                "key_limitations": ["No instant solutions", "Technology can fail"]
            },
            "geography": {
                "primary_setting": setting,
                "key_locations": ["To be defined based on story"],
                "environmental_challenges": ["Urban density", "Weather", "Distance"],
                "movement_constraints": "Realistic travel times and logistics"
            },
            "time_context": {
                "era": "Present day",
                "timeline_pressure": "To be defined",
                "relevant_history": "Recent history affects characters"
            }
        },
        "social_rules": {
            "power_structure": {
                "who_has_power": "Economic and institutional leaders",
                "how_maintained": "Money, influence, connections",
                "protagonist_relationship": "Outside traditional power structures"
            },
            "hierarchy": {
                "groups": ["Economic classes", "Professional hierarchies", "Social circles"],
                "mobility": "Possible but difficult",
                "prejudices": ["Class assumptions", "Professional stereotypes"]
            },
            "norms": ["Social politeness", "Professional conduct", "Digital etiquette"],
            "taboos": ["Public failure", "Showing weakness", "Breaking trust"],
            "norm_violation_consequences": "Social ostracism, professional damage",
            "economics": {
                "scarcity": "Time, attention, genuine connection",
                "valued_resources": ["Money", "Status", "Relationships"],
                "economic_pressure": "To be defined based on character"
            }
        },
        "power_rules": {
            "sources": ["Wealth", "Knowledge", "Connections", "Skills"],
            "protagonist_power": "To be defined",
            "protagonist_power_gap": "What they lack vs antagonist",
            "how_gained": "Through achievement, relationships, growth",
            "how_lost": "Through scandal, failure, betrayal",
            "limitations": ["Legal constraints", "Social consequences", "Personal ethics"],
            "corruption_risk": "Power without accountability"
        },
        "world_bible": {
            "essential_history": ["Recent events shaping present"],
            "culture": {
                "daily_life": "Contemporary patterns",
                "rituals": ["Work routines", "Social gatherings"],
                "beliefs": ["To be defined based on setting"]
            },
            "terminology": {},
            "sensory_palette": {
                "visual": "Urban landscapes, interior spaces",
                "auditory": "City sounds, conversation, technology",
                "olfactory": "Coffee, food, urban air",
                "tactile": "Modern textures, temperature contrasts",
                "gustatory": "Contemporary cuisine"
            }
        },
        "constraint_list": [
            {
                "constraint": "Time pressure",
                "why_unavoidable": "External deadline or consequence",
                "conflict_generated": "Forces difficult choices",
                "story_function": "Creates urgency"
            },
            {
                "constraint": "Limited resources",
                "why_unavoidable": "Character's circumstances",
                "conflict_generated": "Can't buy way out of problems",
                "story_function": "Requires creativity and sacrifice"
            },
            {
                "constraint": "Social expectations",
                "why_unavoidable": "Character's role/position",
                "conflict_generated": "Can't act freely",
                "story_function": "Internal vs external conflict"
            }
        ],
        "world_coherence_score": 70
    }


def _get_character_fallback(constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback character architecture."""
    return {
        "protagonist_profile": {
            "identity": {
                "name": "[Protagonist Name]",
                "age": "30s",
                "role": "Professional navigating change",
                "defining_physical_trait": "[To be defined]"
            },
            "psychological_core": {
                "core_desire": "Connection and meaning",
                "core_fear": "Being truly seen and rejected",
                "core_wound": "Past rejection or abandonment",
                "core_belief": "I must prove my worth to be loved",
                "core_strength": "Determination and intelligence",
                "core_flaw": "Defensive self-reliance"
            },
            "backstory": {
                "wound_event": "[Formative experience]",
                "wound_impact": "Created fear of vulnerability",
                "defense_mechanisms": ["Achievement focus", "Emotional distance"],
                "false_beliefs_formed": ["Love must be earned", "Vulnerability is weakness"]
            },
            "voice": {
                "speech_patterns": "Articulate but guarded",
                "thinking_style": "Analytical with emotional undercurrents",
                "relationship_style": "Warm surface, protected core",
                "humor": "Dry, self-deprecating",
                "distinctive_traits": ["Specific mannerism", "Recurring phrase"]
            }
        },
        "protagonist_arc": {
            "starting_state": {
                "who_they_are": "Successful but unfulfilled",
                "status_quo": "Life works on the surface",
                "whats_working": "Career, competence",
                "whats_broken": "Intimacy, authenticity"
            },
            "lie_believed": {
                "the_lie": "I don't need anyone",
                "origin": "Past betrayal/abandonment",
                "how_it_protects": "Prevents rejection",
                "how_it_hurts": "Creates isolation"
            },
            "truth_needed": {
                "the_truth": "Vulnerability is the price of connection",
                "why_threatening": "Risks the pain they've avoided",
                "why_hard_to_accept": "Requires giving up control",
                "how_it_frees": "Opens possibility of real love"
            },
            "transformation": {
                "change_description": "From guarded to open",
                "what_given_up": "The illusion of safety",
                "what_gained": "Authentic connection",
                "proof_moment": "A choice that demonstrates change"
            },
            "ending_state": "Whole, connected, at peace"
        },
        "want_vs_need": {
            "want": {
                "description": "External goal: success, achievement, or specific outcome",
                "why_they_want_it": "Believes it will prove their worth",
                "what_they_think_it_provides": "Validation, security, happiness"
            },
            "need": {
                "description": "Authentic connection and self-acceptance",
                "why_blind_to_it": "Would require vulnerability",
                "what_it_actually_provides": "True fulfillment"
            },
            "conflict": {
                "how_want_blocks_need": "Pursuing achievement at cost of relationship",
                "required_sacrifice": "Must risk failure to gain connection",
                "revelation_moment": "Crisis shows want won't fulfill need"
            }
        },
        "antagonist_profile": {
            "identity": {
                "name": "[Antagonist Name]",
                "role": "Shadow figure or external opposition",
                "relationship_to_protagonist": "Rival, ex, authority figure"
            },
            "psychology": {
                "want": "What they're trying to achieve",
                "wound": "What made them this way",
                "belief_system": "Their valid worldview",
                "why_they_believe_theyre_right": "From their perspective, they are right"
            },
            "dark_mirror": {
                "shadow_element": "What protagonist could become",
                "alternate_path": "The path not taken",
                "common_ground": "What they share",
                "key_difference": "The choice that separates them"
            },
            "strength": {
                "danger": "Real threat they pose",
                "advantage": "What they have protagonist lacks",
                "difficulty_to_defeat": "Why simple solutions won't work"
            },
            "humanity": {
                "sympathetic_element": "What makes them understandable",
                "humanizing_moment": "When we see their pain",
                "understandable_choices": "Why someone could choose their path"
            }
        },
        "supporting_cast": [
            {
                "name": "[Mentor Figure]",
                "function": "mentor",
                "relationship_to_protagonist": "Guide or teacher",
                "their_want": "To help protagonist succeed",
                "their_need": "Own redemption or purpose",
                "how_they_pressure_protagonist": "Challenges comfort zone",
                "their_arc": "From detached to invested",
                "memorable_trait": "Distinctive wisdom style",
                "voice_distinctive": "Speaks in questions"
            },
            {
                "name": "[Best Friend/Ally]",
                "function": "ally",
                "relationship_to_protagonist": "Close friend",
                "their_want": "Protagonist's happiness",
                "their_need": "Own growth journey",
                "how_they_pressure_protagonist": "Honest feedback",
                "their_arc": "From support to confrontation to reconciliation",
                "memorable_trait": "Specific hobby or obsession",
                "voice_distinctive": "Humor and warmth"
            },
            {
                "name": "[Love Interest or Key Relationship]",
                "function": "love_interest",
                "relationship_to_protagonist": "Romantic potential",
                "their_want": "Genuine connection",
                "their_need": "To be seen for who they are",
                "how_they_pressure_protagonist": "Requires vulnerability",
                "their_arc": "Trust building to testing to resolution",
                "memorable_trait": "What makes them unique",
                "voice_distinctive": "Their particular expression style"
            }
        ],
        "character_constellation": {
            "theme_supporters": ["Mentor", "Love Interest"],
            "theme_challengers": ["Antagonist", "Past self"],
            "consequence_demonstrators": ["Characters who made different choices"],
            "pressure_dynamics": "Each character pushes protagonist toward truth"
        },
        "character_depth_score": 75
    }


def _get_relationship_fallback(character_arch: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback relationship dynamics."""
    protagonist = character_arch.get("protagonist_profile", {})
    antagonist = character_arch.get("antagonist_profile", {})
    
    return {
        "conflict_web": [
            {
                "characters": ["Protagonist", "Antagonist"],
                "surface_tension": "Competing for same goal",
                "deeper_tension": "Different values and worldviews",
                "character_a_wants": "Meaningful success",
                "character_b_wants": "Victory at any cost",
                "escalation_pattern": "Each confrontation raises stakes",
                "thematic_connection": "Embodies theme's value conflict",
                "resolution_potential": "Through protagonist's transformation"
            },
            {
                "characters": ["Protagonist", "Love Interest"],
                "surface_tension": "Misunderstanding or circumstance",
                "deeper_tension": "Fear of vulnerability vs desire for connection",
                "character_a_wants": "Connection without risk",
                "character_b_wants": "Authentic intimacy",
                "escalation_pattern": "Closer to connection, more fear surfaces",
                "thematic_connection": "Tests whether protagonist can change",
                "resolution_potential": "Protagonist chooses vulnerability"
            }
        ],
        "power_dynamics": [
            {
                "relationship": "Protagonist and Antagonist",
                "initial_power_holder": "Antagonist",
                "power_source": "Resources, position, fewer scruples",
                "shift_triggers": ["Protagonist gains knowledge", "Alliance formation", "Antagonist error"],
                "final_power_state": "Equalized or protagonist ascendant",
                "thematic_meaning": "Power of integrity vs power of force"
            }
        ],
        "dependency_arcs": [
            {
                "dependent": "Protagonist",
                "provider": "Old identity/defenses",
                "dependency_type": "Emotional safety",
                "healthy_or_unhealthy": "Unhealthy - prevents growth",
                "evolution": "Gradually releasing control",
                "breaking_point": "Crisis forces letting go",
                "what_replaces_it": "Self-acceptance and healthy connection"
            }
        ],
        "emotional_beats": {
            "protagonist_love_interest": {
                "first_impression": {
                    "moment": "Initial meeting or re-meeting",
                    "dynamic": "Interest mixed with resistance",
                    "assumptions": "Both make incorrect assumptions"
                },
                "bonding_moment": {
                    "trigger": "Shared experience or revelation",
                    "vulnerability_shown": "Glimpse behind defenses",
                    "what_shared": "Personal truth"
                },
                "conflict_point": {
                    "cause": "Protagonist's flaw creates problem",
                    "wounds_inflicted": "Trust damaged",
                    "stakes": "Relationship survival"
                },
                "low_point": {
                    "description": "Separation or betrayal",
                    "what_feels_lost": "Hope for connection"
                },
                "resolution": {
                    "how_resolved": "Protagonist demonstrates change",
                    "what_changes": "Authenticity replaces performance",
                    "truth_acknowledged": "Both accept each other fully"
                }
            }
        },
        "relationship_matrix": [
            {
                "char_a": "Protagonist",
                "char_b": "Antagonist",
                "type": "Opposition",
                "start_state": "Unaware or underestimated",
                "key_moments": ["First confrontation", "Stakes escalation", "Final battle"],
                "end_state": "Defeated or transformed",
                "thematic_function": "External embodiment of internal conflict"
            },
            {
                "char_a": "Protagonist",
                "char_b": "Mentor",
                "type": "Student-Teacher",
                "start_state": "Reluctant student",
                "key_moments": ["Teaching moments", "Disagreement", "Understanding"],
                "end_state": "Equals or passing the torch",
                "thematic_function": "Guide toward truth"
            },
            {
                "char_a": "Protagonist",
                "char_b": "Best Friend",
                "type": "Friendship",
                "start_state": "Comfortable but surface-level",
                "key_moments": ["Truth-telling", "Testing friendship", "Reconciliation"],
                "end_state": "Deepened bond",
                "thematic_function": "Mirror and truth-speaker"
            }
        ],
        "secondary_relationships": [
            {
                "relationship": "Supporting characters to each other",
                "function": "Subplot and world texture",
                "how_it_supports_main_relationships": "Provides contrast or parallel"
            }
        ],
        "relationship_complexity_score": 70
    }


# =============================================================================
# REGISTRATION
# =============================================================================

STORY_SYSTEM_EXECUTORS = {
    "world_rules": execute_world_rules,
    "character_architecture": execute_character_architecture,
    "relationship_dynamics": execute_relationship_dynamics,
}
