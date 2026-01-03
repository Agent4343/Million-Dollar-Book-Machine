"""
Strategic Foundation Agents (Layers 0-4)

These agents establish the foundational strategy for the book:
- Orchestrator (Layer 0)
- Market & Reader Intelligence
- Core Concept Definition
- Thematic Architecture
- Central Story Question
"""

from typing import Dict, Any
from core.orchestrator import ExecutionContext
from models.agents import AGENT_REGISTRY, get_agent_execution_order


# =============================================================================
# LAYER 0: ORCHESTRATOR
# =============================================================================

async def execute_orchestrator(context: ExecutionContext) -> Dict[str, Any]:
    """Execute orchestrator agent - initializes the pipeline."""
    # The orchestrator doesn't need LLM - it just sets up the pipeline
    return {
        "agent_map": sorted(list(AGENT_REGISTRY.keys())),
        "stage_order": get_agent_execution_order(),
        "state_json": {
            "initialized": True,
            "title": context.project.title,
            "constraints": context.inputs.get("user_constraints", {})
        },
        "checkpoint_rules": {
            "auto_save": True,
            "save_after_each_layer": True,
            "max_checkpoints": 10
        }
    }


# =============================================================================
# PROMPTS
# =============================================================================

MARKET_INTELLIGENCE_PROMPT = """You are a book market analyst. Analyze the market opportunity for a new book.

## User Constraints:
{constraints}

## Task:
Create a comprehensive market analysis including:

1. **Reader Avatar**: Define the ideal reader
   - Demographics (age, education, interests)
   - Psychographics (values, fears, desires)
   - Reading habits (frequency, preferred formats)
   - What problems they want solved

2. **Market Gap**: Identify the underserved need
   - What existing books don't provide
   - What readers are asking for but not getting
   - Timing opportunities

3. **Positioning Angle**: How this book will stand out
   - Unique value proposition
   - Key differentiators from competition
   - Competitive advantage

4. **Comp Analysis**: 3-5 comparable titles
   - What they do well
   - What they miss
   - How this book improves on them

## Output Format (JSON):
{{
    "reader_avatar": {{
        "demographics": "...",
        "psychographics": "...",
        "reading_habits": "...",
        "problems_to_solve": ["..."]
    }},
    "market_gap": {{
        "unmet_need": "...",
        "timing": "...",
        "opportunity_size": "..."
    }},
    "positioning_angle": {{
        "unique_value": "...",
        "differentiators": ["..."],
        "competitive_advantage": "..."
    }},
    "comp_analysis": [
        {{"title": "...", "strengths": ["..."], "gaps": ["..."]}}
    ]
}}
"""

CONCEPT_DEFINITION_PROMPT = """You are a book concept strategist. Define the core concept that will make this book irresistible.

## Market Analysis:
{market_intelligence}

## User Vision:
{user_constraints}

## Task:
Create a compelling core concept:

1. **One-Line Hook**: A single sentence that sells the book
   - Must create instant intrigue
   - Should be quotable and memorable
   - Contains the core conflict or promise

2. **Core Promise**: What the reader will get
   - The transformation or value delivered
   - Why it matters to them
   - The emotional payoff

3. **Unique Engine**: The mechanism that makes this book work
   - What's the secret sauce?
   - Why hasn't this been done before?
   - What makes it credible?

4. **Elevator Pitch**: 2-3 sentences that sell the book

## Output Format (JSON):
{{
    "one_line_hook": "...",
    "core_promise": {{
        "transformation": "...",
        "value": "...",
        "emotional_payoff": "..."
    }},
    "unique_engine": {{
        "mechanism": "...",
        "novelty": "...",
        "credibility": "..."
    }},
    "elevator_pitch": "..."
}}
"""

THEMATIC_ARCHITECTURE_PROMPT = """You are a story architect specializing in thematic structure. Design the meaning layer of this book.

## Core Concept:
{concept_definition}

## Task:
Create the thematic architecture:

1. **Primary Theme**: The central truth the story explores
   - A universal human truth
   - Expressed as a thematic statement
   - Must be arguable (not a platitude)

2. **Counter-Theme**: The opposing viewpoint
   - What argues against the primary theme?
   - Represented by antagonistic forces
   - Creates meaningful conflict

3. **Value Conflict**: The core tension
   - What values are in opposition?
   - E.g., Freedom vs Security, Love vs Duty
   - Must be impossible to have both

4. **Thematic Question**: The question readers will ponder
   - Open-ended, not rhetorical
   - The story argues both sides
   - Reader draws their own conclusion

## Output Format (JSON):
{{
    "primary_theme": {{
        "statement": "...",
        "universal_truth": "...",
        "argument": "..."
    }},
    "counter_theme": {{
        "statement": "...",
        "represented_by": "...",
        "argument": "..."
    }},
    "value_conflict": {{
        "value_a": "...",
        "value_b": "...",
        "why_incompatible": "..."
    }},
    "thematic_question": "..."
}}
"""

STORY_QUESTION_PROMPT = """You are a narrative strategist. Define the central dramatic question that will drive reader engagement.

## Thematic Architecture:
{thematic_architecture}

## Core Promise:
{concept_definition}

## Task:
Create the central story question:

1. **Central Dramatic Question (CDQ)**: The question readers must know the answer to
   - Binary yes/no outcome
   - High personal stakes for protagonist
   - Directly tied to theme

2. **Stakes Ladder**: Escalating consequences
   - Level 1: What's at risk initially
   - Level 2: What escalates the stakes
   - Level 3: Ultimate stakes (what if protagonist fails completely)
   - Each level more personal and devastating

3. **Binary Outcome**: The two possible endings
   - What happens if protagonist succeeds
   - What happens if protagonist fails
   - Both must be meaningful

4. **Reader Investment**: Why readers will care
   - Universal relatability
   - Emotional hooks
   - Curiosity drivers

## Output Format (JSON):
{{
    "central_dramatic_question": "...",
    "stakes_ladder": {{
        "level_1": {{"risk": "...", "consequence": "..."}},
        "level_2": {{"risk": "...", "consequence": "..."}},
        "level_3": {{"risk": "...", "consequence": "..."}}
    }},
    "binary_outcome": {{
        "success": "...",
        "failure": "..."
    }},
    "reader_investment": {{
        "relatability": "...",
        "emotional_hooks": ["..."],
        "curiosity_drivers": ["..."]
    }}
}}
"""


# =============================================================================
# EXECUTOR FUNCTIONS
# =============================================================================

async def execute_market_intelligence(context: ExecutionContext) -> Dict[str, Any]:
    """Execute market intelligence agent."""
    llm = context.llm_client

    prompt = MARKET_INTELLIGENCE_PROMPT.format(
        constraints=context.inputs.get("user_constraints", {})
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        # Placeholder for demo
        return {
            "reader_avatar": {
                "demographics": "Adults 25-45, college-educated",
                "psychographics": "Growth-minded, curious, seeks transformation",
                "reading_habits": "1-2 books/month, prefers ebooks",
                "problems_to_solve": ["Need for meaning", "Career uncertainty"]
            },
            "market_gap": {
                "unmet_need": "Practical wisdom for modern challenges",
                "timing": "Post-pandemic introspection wave",
                "opportunity_size": "Large underserved market"
            },
            "positioning_angle": {
                "unique_value": "Actionable philosophy for real life",
                "differentiators": ["Story-driven", "Modern examples"],
                "competitive_advantage": "Combines narrative and instruction"
            },
            "comp_analysis": [
                {"title": "Example Comp 1", "strengths": ["Engaging"], "gaps": ["Too theoretical"]}
            ]
        }


async def execute_concept_definition(context: ExecutionContext) -> Dict[str, Any]:
    """Execute concept definition agent."""
    llm = context.llm_client

    prompt = CONCEPT_DEFINITION_PROMPT.format(
        market_intelligence=context.inputs.get("market_intelligence", {}),
        user_constraints=context.inputs.get("user_constraints", {})
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        return {
            "one_line_hook": "A transformative journey that changes everything",
            "core_promise": {
                "transformation": "From lost to found",
                "value": "Clarity and purpose",
                "emotional_payoff": "Hope and empowerment"
            },
            "unique_engine": {
                "mechanism": "Unique framework",
                "novelty": "Never been done this way",
                "credibility": "Based on real experience"
            },
            "elevator_pitch": "This book takes readers on a journey from confusion to clarity through a unique framework."
        }


async def execute_thematic_architecture(context: ExecutionContext) -> Dict[str, Any]:
    """Execute thematic architecture agent."""
    llm = context.llm_client

    prompt = THEMATIC_ARCHITECTURE_PROMPT.format(
        concept_definition=context.inputs.get("concept_definition", {})
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        return {
            "primary_theme": {
                "statement": "True freedom comes through discipline",
                "universal_truth": "Constraints enable creativity",
                "argument": "Structure provides foundation for expression"
            },
            "counter_theme": {
                "statement": "Rules are prisons that limit potential",
                "represented_by": "Characters who reject all structure",
                "argument": "Freedom means no constraints"
            },
            "value_conflict": {
                "value_a": "Freedom",
                "value_b": "Discipline",
                "why_incompatible": "Each seems to negate the other"
            },
            "thematic_question": "Can true freedom exist within discipline?"
        }


async def execute_story_question(context: ExecutionContext) -> Dict[str, Any]:
    """Execute story question agent."""
    llm = context.llm_client

    prompt = STORY_QUESTION_PROMPT.format(
        thematic_architecture=context.inputs.get("thematic_architecture", {}),
        concept_definition=context.inputs.get("concept_definition", {})
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        return {
            "central_dramatic_question": "Will the protagonist find meaning before it's too late?",
            "stakes_ladder": {
                "level_1": {"risk": "Career stagnation", "consequence": "Continued unhappiness"},
                "level_2": {"risk": "Relationship loss", "consequence": "Isolation"},
                "level_3": {"risk": "Complete despair", "consequence": "Loss of self"}
            },
            "binary_outcome": {
                "success": "Transforms and finds purpose",
                "failure": "Remains trapped in meaninglessness"
            },
            "reader_investment": {
                "relatability": "Everyone questions their purpose",
                "emotional_hooks": ["Fear of wasted potential", "Hope for change"],
                "curiosity_drivers": ["How will they escape?", "What's the solution?"]
            }
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
