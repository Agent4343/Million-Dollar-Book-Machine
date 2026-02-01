"""
Story System Design Agents (Layers 5-7)

These agents design the story's operating system:
- World / Context Rules
- Character Architecture
- Relationship Dynamics
"""

from typing import Dict, Any
from core.orchestrator import ExecutionContext


# =============================================================================
# PROMPTS
# =============================================================================

WORLD_RULES_PROMPT = """You are a worldbuilder. Design the rules and constraints of the story world.

## Story Question:
{story_question}

## Genre:
{genre}

## User Constraints:
{user_constraints}

## Task:
Define the world's operating rules:

1. **Physical Rules**: Laws of the world
   - What's possible/impossible
   - Technology level
   - Geography constraints

2. **Social Rules**: How society operates
   - Power structures
   - Social norms and taboos
   - Economic systems

3. **Power Rules**: How power works
   - Who has power and why
   - How power is gained/lost
   - Limitations on power

4. **World Bible**: Key world facts
   - History that matters
   - Culture and customs
   - Language and terminology

5. **Constraint List**: Rules that create tension
   - What the protagonist cannot do
   - Time limits
   - Resource scarcity

## Output Format (JSON):
{{
    "physical_rules": {{
        "possibilities": ["..."],
        "impossibilities": ["..."],
        "technology": "...",
        "geography": "..."
    }},
    "social_rules": {{
        "power_structures": "...",
        "norms": ["..."],
        "taboos": ["..."],
        "economics": "..."
    }},
    "power_rules": {{
        "who_has_power": "...",
        "how_gained": "...",
        "how_lost": "...",
        "limitations": ["..."]
    }},
    "world_bible": {{
        "relevant_history": "...",
        "culture": "...",
        "terminology": {{}}
    }},
    "constraint_list": ["..."]
}}
"""

CHARACTER_ARCHITECTURE_PROMPT = """You are a character architect. Design the cast of characters as agents of thematic change.

## CRITICAL: User-Provided Character Details
{user_story_bible}

**If the user provided character names, physical descriptions, or backstory above, you MUST use those EXACT details. Do NOT invent new names or change any details they provided.**

## Theme:
{primary_theme}

## Story Question:
{central_dramatic_question}

## World Rules:
{world_rules}

## Task:
Design the character system:

1. **Protagonist Profile**: The main character
   - Name and role
   - Defining traits
   - Backstory wounds
   - Skills and weaknesses

2. **Protagonist Arc**: The change journey
   - Starting state (who they are at start)
   - Ending state (who they become)
   - The transformation required

3. **Want vs Need**:
   - What they WANT (conscious goal)
   - What they NEED (unconscious need)
   - Why these conflict

4. **Antagonist Profile**: The opposing force
   - Name and role
   - Their valid worldview
   - Why they oppose protagonist
   - Their strength

5. **Antagonistic Force**: The nature of opposition
   - External antagonist
   - Internal obstacles
   - Societal forces

6. **Supporting Cast**: Key secondary characters
   - Each character's function
   - How they challenge/support protagonist
   - Their own mini-arcs

7. **Character Functions**: Role in story
   - Mentor figure
   - Ally
   - Shapeshifter
   - Threshold guardian

## Output Format (JSON):
{{
    "protagonist_profile": {{
        "name": "...",
        "role": "...",
        "traits": ["..."],
        "backstory_wound": "...",
        "skills": ["..."],
        "weaknesses": ["..."]
    }},
    "protagonist_arc": {{
        "starting_state": "...",
        "ending_state": "...",
        "transformation": "..."
    }},
    "want_vs_need": {{
        "want": "...",
        "need": "...",
        "conflict": "..."
    }},
    "antagonist_profile": {{
        "name": "...",
        "role": "...",
        "worldview": "...",
        "opposition_reason": "...",
        "strength": "..."
    }},
    "antagonistic_force": {{
        "external": "...",
        "internal": "...",
        "societal": "..."
    }},
    "supporting_cast": [
        {{"name": "...", "function": "...", "challenge": "...", "arc": "..."}}
    ],
    "character_functions": {{
        "mentor": "...",
        "ally": "...",
        "shapeshifter": "...",
        "threshold_guardian": "..."
    }}
}}
"""

RELATIONSHIP_DYNAMICS_PROMPT = """You are a relationship architect. Map the emotional engine of the story through character relationships.

## Characters:
{character_architecture}

## Theme:
{primary_theme}

## Value Conflict:
{value_conflict}

## Task:
Design the relationship dynamics:

1. **Conflict Web**: Who conflicts with whom
   - Main relationship tensions
   - Source of each conflict
   - What each party wants

2. **Power Shifts**: How power moves between characters
   - Initial power balance
   - Key moments of shift
   - Final power state

3. **Dependency Arcs**: How dependencies evolve
   - Who depends on whom
   - How this changes
   - What breaks dependencies

4. **Relationship Matrix**: All key relationships
   - Character A vs Character B
   - Relationship type
   - Evolution through story

## Output Format (JSON):
{{
    "conflict_web": [
        {{
            "characters": ["A", "B"],
            "tension": "...",
            "source": "...",
            "each_wants": {{"A": "...", "B": "..."}}
        }}
    ],
    "power_shifts": [
        {{
            "characters": ["A", "B"],
            "initial_balance": "...",
            "shift_moment": "...",
            "final_state": "..."
        }}
    ],
    "dependency_arcs": [
        {{
            "dependent": "...",
            "provider": "...",
            "nature": "...",
            "evolution": "...",
            "breaking_point": "..."
        }}
    ],
    "relationship_matrix": [
        {{
            "char_a": "...",
            "char_b": "...",
            "type": "...",
            "start_state": "...",
            "end_state": "..."
        }}
    ]
}}
"""


# =============================================================================
# EXECUTOR FUNCTIONS
# =============================================================================

async def execute_world_rules(context: ExecutionContext) -> Dict[str, Any]:
    """Execute world rules agent."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    prompt = WORLD_RULES_PROMPT.format(
        story_question=context.inputs.get("story_question", {}),
        genre=constraints.get("genre", "general fiction"),
        user_constraints=constraints
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        return {
            "physical_rules": {
                "possibilities": ["Modern technology", "Travel", "Communication"],
                "impossibilities": ["Magic", "Time travel"],
                "technology": "Contemporary",
                "geography": "Urban setting"
            },
            "social_rules": {
                "power_structures": "Corporate hierarchy",
                "norms": ["Professional conduct", "Social media presence"],
                "taboos": ["Failure", "Vulnerability"],
                "economics": "Capitalist, competitive"
            },
            "power_rules": {
                "who_has_power": "Those with status and money",
                "how_gained": "Success, connections, inheritance",
                "how_lost": "Scandal, failure, isolation",
                "limitations": ["Public perception", "Legal constraints"]
            },
            "world_bible": {
                "relevant_history": "Post-2020 world",
                "culture": "Achievement-obsessed",
                "terminology": {}
            },
            "constraint_list": [
                "Limited time",
                "Social expectations",
                "Past commitments",
                "Financial pressures"
            ]
        }


async def execute_character_architecture(context: ExecutionContext) -> Dict[str, Any]:
    """Execute character architecture agent."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})
    if not isinstance(constraints, dict):
        constraints = {}

    # Check for user-provided story bible content
    user_story_bible = constraints.get("story_bible", "")
    user_description = constraints.get("description", "")
    user_content = user_story_bible or user_description

    # Ensure user_content is a string before slicing
    if not isinstance(user_content, str):
        user_content = str(user_content) if user_content else ""

    # Format user content for the prompt
    if user_content and len(user_content) > 200:
        user_story_bible_block = f"""The author has provided the following story bible/description:

{user_content[:8000]}

**IMPORTANT: Extract and use the EXACT character names, ages, physical descriptions,
relationships, and backstories from the above content. Do NOT invent new names or details.**
"""
    else:
        user_story_bible_block = "(No user-provided character details - create original characters based on theme and story question)"

    prompt = CHARACTER_ARCHITECTURE_PROMPT.format(
        user_story_bible=user_story_bible_block,
        primary_theme=context.inputs.get("thematic_architecture", {}).get("primary_theme", {}),
        central_dramatic_question=context.inputs.get("story_question", {}).get("central_dramatic_question", ""),
        world_rules=context.inputs.get("world_rules", {})
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        return {
            "protagonist_profile": {
                "name": "[Protagonist Name]",
                "role": "Seeker",
                "traits": ["Intelligent", "Driven", "Guarded"],
                "backstory_wound": "Early failure created fear of vulnerability",
                "skills": ["Analysis", "Persuasion"],
                "weaknesses": ["Trust issues", "Workaholism"]
            },
            "protagonist_arc": {
                "starting_state": "Successful but empty",
                "ending_state": "Purposeful and connected",
                "transformation": "Learns to value relationships over achievement"
            },
            "want_vs_need": {
                "want": "More success and recognition",
                "need": "Authentic connection and meaning",
                "conflict": "Pursuing success pushes away what they need"
            },
            "antagonist_profile": {
                "name": "[Antagonist Name]",
                "role": "Shadow self",
                "worldview": "Success at any cost is justified",
                "opposition_reason": "Represents the path protagonist must reject",
                "strength": "Already has what protagonist wants"
            },
            "antagonistic_force": {
                "external": "Competitive industry",
                "internal": "Fear of vulnerability",
                "societal": "Success culture pressure"
            },
            "supporting_cast": [
                {"name": "[Mentor]", "function": "Guide", "challenge": "Pushes comfort zone", "arc": "Reveals own struggles"},
                {"name": "[Ally]", "function": "Support", "challenge": "Offers unwanted honesty", "arc": "Grows alongside protagonist"}
            ],
            "character_functions": {
                "mentor": "Wise figure who's walked the path",
                "ally": "Friend who speaks truth",
                "shapeshifter": "Character with hidden agenda",
                "threshold_guardian": "Gatekeeper to new world"
            }
        }


async def execute_relationship_dynamics(context: ExecutionContext) -> Dict[str, Any]:
    """Execute relationship dynamics agent."""
    llm = context.llm_client

    prompt = RELATIONSHIP_DYNAMICS_PROMPT.format(
        character_architecture=context.inputs.get("character_architecture", {}),
        primary_theme=context.inputs.get("thematic_architecture", {}).get("primary_theme", {}),
        value_conflict=context.inputs.get("thematic_architecture", {}).get("value_conflict", {})
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        return {
            "conflict_web": [
                {
                    "characters": ["Protagonist", "Antagonist"],
                    "tension": "Competing worldviews",
                    "source": "Different values",
                    "each_wants": {"Protagonist": "Meaning", "Antagonist": "Power"}
                }
            ],
            "power_shifts": [
                {
                    "characters": ["Protagonist", "Antagonist"],
                    "initial_balance": "Antagonist dominant",
                    "shift_moment": "Protagonist discovers truth",
                    "final_state": "Protagonist empowered"
                }
            ],
            "dependency_arcs": [
                {
                    "dependent": "Protagonist",
                    "provider": "Old systems",
                    "nature": "Security and identity",
                    "evolution": "Gradually breaks free",
                    "breaking_point": "Crisis forces choice"
                }
            ],
            "relationship_matrix": [
                {
                    "char_a": "Protagonist",
                    "char_b": "Mentor",
                    "type": "Student-Teacher",
                    "start_state": "Resistant",
                    "end_state": "Grateful"
                },
                {
                    "char_a": "Protagonist",
                    "char_b": "Ally",
                    "type": "Friendship",
                    "start_state": "Surface level",
                    "end_state": "Deep bond"
                }
            ]
        }


# =============================================================================
# REGISTRATION
# =============================================================================

STORY_SYSTEM_EXECUTORS = {
    "world_rules": execute_world_rules,
    "character_architecture": execute_character_architecture,
    "relationship_dynamics": execute_relationship_dynamics,
}
