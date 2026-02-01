"""
Story Bible Agent

Creates and maintains a canonical reference document that locks in all story facts
to ensure consistency across all generated chapters.

This addresses issues like:
- Character name changes (e.g., "Vincent Blackwood" vs "Vincent Torrino")
- Location inconsistencies (e.g., Chicago vs New York)
- Timeline discrepancies (e.g., father died 3 years ago vs 20 years ago)
- Relationship confusion (e.g., "Elena as sister" vs "Elena as mother")
"""

from typing import Dict, Any, List
from core.orchestrator import ExecutionContext


STORY_BIBLE_PROMPT = """You are a story bible architect. Create a canonical reference document that locks in ALL story facts.

## Character Architecture:
{character_architecture}

## World Rules:
{world_rules}

## Relationship Dynamics:
{relationship_dynamics}

## Genre & Setting:
{genre_setting}

## CRITICAL TASK:
Create a Story Bible - the AUTHORITATIVE reference for all story facts. Every chapter writer MUST follow this exactly.

Generate the following with SPECIFIC, LOCKED-IN details:

1. **CHARACTER REGISTRY** - Every character with EXACT details:
   - Full name (ONLY ONE canonical spelling)
   - Age (exact number)
   - Physical description (specific details)
   - Role in story
   - Key relationships (who is related to whom, how)
   - Occupation/position
   - Distinctive traits/mannerisms

2. **LOCATION REGISTRY** - Every location with EXACT details:
   - City name (ONLY ONE)
   - Specific addresses/neighborhoods
   - Key buildings/places
   - Geographic context

3. **TIMELINE** - Key dates and time periods:
   - Story present date/year
   - Key past events with EXACT time references
   - Character ages at key events
   - Chronological order of backstory events

4. **RELATIONSHIP MAP** - How characters are connected:
   - Family relationships (parent/child/sibling)
   - Romantic relationships
   - Professional relationships
   - Antagonistic relationships

5. **TERMINOLOGY** - Consistent naming:
   - Organization names
   - Title/honorifics
   - Nicknames and aliases
   - Technical terms specific to the world

6. **BACKSTORY FACTS** - Locked-in history:
   - What happened to whom, when
   - Causes and effects
   - Secrets and revelations

## Output Format (JSON):
{{
    "character_registry": [
        {{
            "id": "char_001",
            "canonical_name": "First Last",
            "aliases": [],
            "age": 32,
            "physical": {{
                "height": "...",
                "build": "...",
                "hair": "...",
                "eyes": "...",
                "distinguishing_features": ["..."]
            }},
            "role": "protagonist|antagonist|supporting",
            "occupation": "...",
            "relationships": {{
                "char_002": "relationship type"
            }},
            "traits": ["..."],
            "mannerisms": ["..."]
        }}
    ],
    "location_registry": {{
        "primary_city": "...",
        "key_locations": [
            {{
                "id": "loc_001",
                "name": "...",
                "type": "...",
                "description": "...",
                "significance": "..."
            }}
        ]
    }},
    "timeline": {{
        "story_present": "...",
        "key_dates": [
            {{
                "event": "...",
                "when": "...",
                "years_before_story": 0,
                "characters_involved": ["..."]
            }}
        ]
    }},
    "relationship_map": [
        {{
            "character_a": "char_001",
            "character_b": "char_002",
            "relationship_type": "...",
            "dynamic": "..."
        }}
    ],
    "terminology": {{
        "organizations": {{}},
        "titles": {{}},
        "technical_terms": {{}}
    }},
    "backstory_facts": [
        {{
            "fact_id": "bs_001",
            "description": "...",
            "characters_involved": ["..."],
            "impact_on_story": "..."
        }}
    ],
    "consistency_rules": [
        "Rule 1: Always refer to [character] as [canonical name]",
        "Rule 2: Story takes place in [city], never reference other cities as home base",
        "..."
    ]
}}

IMPORTANT: Be SPECIFIC. Don't use placeholders. Generate actual names, ages, dates, and details.
These become the CANONICAL facts that all chapters must follow.
"""


async def execute_story_bible(context: ExecutionContext) -> Dict[str, Any]:
    """
    Execute story bible agent - creates canonical reference for consistency.

    This runs after character_architecture, world_rules, and relationship_dynamics
    to lock in all story facts before chapter writing begins.

    IMPORTANT: If the user provides their own story_bible content (via user_constraints),
    that content takes PRIORITY over generated content to preserve the user's vision.
    """
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})
    if not isinstance(constraints, dict):
        constraints = {}

    # Check if user provided their own story bible content
    user_story_bible = constraints.get("story_bible", "")
    user_description = constraints.get("description", "")

    # If user provided a detailed story bible (check for character names,
    # physical descriptions, or other story bible markers)
    user_content = user_story_bible or user_description

    # Ensure user_content is a string before any operations
    if not isinstance(user_content, str):
        user_content = str(user_content) if user_content else ""

    story_bible_markers = [
        "protagonist", "antagonist", "physical description", "eye color",
        "hair color", "age:", "occupation:", "backstory", "character",
        "setting:", "location:", "timeline", "chapter outline", "canonical"
    ]

    # Check if user content looks like a comprehensive story bible
    is_comprehensive_story_bible = False
    if user_content and len(user_content) > 500:  # Substantial content
        markers_found = sum(1 for marker in story_bible_markers
                          if marker.lower() in user_content.lower())
        is_comprehensive_story_bible = markers_found >= 3  # At least 3 markers

    if is_comprehensive_story_bible:
        # User provided their own comprehensive story bible - parse and use it
        # Store both the raw text and try to structure it
        if llm:
            # Use LLM to structure the user's story bible into our format
            structure_prompt = f"""The user has provided a comprehensive story bible.
Parse this content and structure it into JSON format, preserving ALL details exactly as provided.

USER'S STORY BIBLE:
{user_content[:12000]}

Extract and structure into this JSON format, preserving the EXACT names, ages, descriptions, and details from the user's content:
{{
    "character_registry": [
        {{
            "id": "char_001",
            "canonical_name": "[EXACT name from user's content]",
            "aliases": ["any nicknames mentioned"],
            "age": [age as number],
            "physical": {{
                "height": "...",
                "build": "...",
                "hair": "...",
                "eyes": "...",
                "distinguishing_features": [...]
            }},
            "role": "protagonist|antagonist|supporting",
            "occupation": "...",
            "relationships": {{}},
            "traits": [...],
            "backstory": "..."
        }}
    ],
    "location_registry": {{
        "primary_city": "[city from user's content]",
        "key_locations": [...]
    }},
    "timeline": {{
        "story_present": "...",
        "key_dates": [...]
    }},
    "user_provided_story_bible": true,
    "raw_user_content": "[first 2000 chars of user content for reference]"
}}

CRITICAL: Use the EXACT names, ages, and details from the user's content. Do NOT invent or change anything."""

            response = await llm.generate(structure_prompt, response_format="json")
            response["user_provided_story_bible"] = True
            response["raw_user_content"] = user_content[:3000]
            return response
        else:
            # Demo mode - return the user's content as-is
            return {
                "user_provided_story_bible": True,
                "raw_user_content": user_content,
                "character_registry": [],
                "location_registry": {},
                "timeline": {},
                "consistency_rules": ["Follow the user's story bible exactly"]
            }

    # No user-provided story bible - generate one from agent outputs
    prompt = STORY_BIBLE_PROMPT.format(
        character_architecture=context.inputs.get("character_architecture", {}),
        world_rules=context.inputs.get("world_rules", {}),
        relationship_dynamics=context.inputs.get("relationship_dynamics", {}),
        genre_setting=f"Genre: {constraints.get('genre', 'fiction')}, Setting: {constraints.get('setting', 'contemporary')}"
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        # Demo mode - return structured placeholder
        return {
            "character_registry": [
                {
                    "id": "char_001",
                    "canonical_name": "[Protagonist Full Name]",
                    "aliases": [],
                    "age": 30,
                    "physical": {
                        "height": "5'10\"",
                        "build": "athletic",
                        "hair": "dark brown",
                        "eyes": "green",
                        "distinguishing_features": ["small scar on left eyebrow"]
                    },
                    "role": "protagonist",
                    "occupation": "[Occupation]",
                    "relationships": {
                        "char_002": "antagonist"
                    },
                    "traits": ["determined", "intelligent", "guarded"],
                    "mannerisms": ["runs hand through hair when thinking"]
                },
                {
                    "id": "char_002",
                    "canonical_name": "[Antagonist Full Name]",
                    "aliases": [],
                    "age": 45,
                    "physical": {
                        "height": "6'2\"",
                        "build": "imposing",
                        "hair": "silver-gray",
                        "eyes": "cold blue",
                        "distinguishing_features": []
                    },
                    "role": "antagonist",
                    "occupation": "[Antagonist Occupation]",
                    "relationships": {
                        "char_001": "adversary"
                    },
                    "traits": ["calculating", "charming", "ruthless"],
                    "mannerisms": ["speaks softly when threatening"]
                }
            ],
            "location_registry": {
                "primary_city": "[City Name]",
                "key_locations": [
                    {
                        "id": "loc_001",
                        "name": "[Key Location 1]",
                        "type": "workplace",
                        "description": "[Description]",
                        "significance": "Primary setting for conflict"
                    }
                ]
            },
            "timeline": {
                "story_present": "[Year/Season]",
                "key_dates": [
                    {
                        "event": "[Key past event]",
                        "when": "[Date/Time period]",
                        "years_before_story": 5,
                        "characters_involved": ["char_001"]
                    }
                ]
            },
            "relationship_map": [
                {
                    "character_a": "char_001",
                    "character_b": "char_002",
                    "relationship_type": "adversarial",
                    "dynamic": "Protagonist must overcome antagonist"
                }
            ],
            "terminology": {
                "organizations": {},
                "titles": {},
                "technical_terms": {}
            },
            "backstory_facts": [
                {
                    "fact_id": "bs_001",
                    "description": "[Key backstory event]",
                    "characters_involved": ["char_001"],
                    "impact_on_story": "Drives protagonist motivation"
                }
            ],
            "consistency_rules": [
                "Always use canonical names from character_registry",
                "All events occur in the primary_city unless specified otherwise",
                "Timeline references must match key_dates exactly"
            ]
        }


def format_story_bible_for_chapter(story_bible: Dict[str, Any], user_constraints: Dict[str, Any] = None) -> str:
    """
    Format the story bible into a concise reference string for chapter writers.
    This is injected into every chapter writing prompt to ensure consistency.

    If user provided their own story bible, that content is included directly
    to ensure their character names, settings, and details are preserved.
    """
    if not story_bible:
        return "No story bible available."

    # Handle case where story_bible is a string (from text-based storage)
    if isinstance(story_bible, str):
        return f"## STORY BIBLE REFERENCE\n\n{story_bible}"

    lines = ["## STORY BIBLE - CANONICAL REFERENCE (MUST FOLLOW EXACTLY)"]

    # If this is a user-provided story bible, include their raw content prominently
    if story_bible.get("user_provided_story_bible"):
        raw_content = story_bible.get("raw_user_content", "")
        if raw_content:
            lines.append("")
            lines.append("### USER-PROVIDED CANONICAL REFERENCE")
            lines.append("**The following is the author's canonical story bible. All names, ")
            lines.append("settings, character details, and relationships MUST match exactly:**")
            lines.append("")
            lines.append(raw_content[:4000])  # Include substantial portion
            lines.append("")
            lines.append("---")
            lines.append("")

    # Also include user description/story_bible if provided in constraints
    if user_constraints:
        user_story_bible = user_constraints.get("story_bible", "")
        user_description = user_constraints.get("description", "")
        user_content = user_story_bible or user_description

        if user_content and len(user_content) > 200:
            # Check if it looks like story content
            story_markers = ["protagonist", "antagonist", "character", "chapter", "setting"]
            if any(marker in user_content.lower() for marker in story_markers):
                lines.append("")
                lines.append("### AUTHOR'S VISION (use these details exactly)")
                lines.append(user_content[:3000])
                lines.append("")
                lines.append("---")
                lines.append("")
    lines.append("")

    # Characters
    lines.append("### CHARACTERS (use ONLY these names)")
    for char in story_bible.get("character_registry", []):
        name = char.get("canonical_name", "Unknown")
        role = char.get("role", "")
        age = char.get("age", "?")
        occupation = char.get("occupation", "")
        aliases = char.get("aliases", [])

        alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
        lines.append(f"- **{name}**{alias_str}: {role}, age {age}, {occupation}")

        # Add key relationships
        for rel_id, rel_type in char.get("relationships", {}).items():
            # Find the related character's name
            for other_char in story_bible.get("character_registry", []):
                if other_char.get("id") == rel_id:
                    lines.append(f"  → {rel_type} of {other_char.get('canonical_name', rel_id)}")
                    break

    lines.append("")

    # Location
    loc_reg = story_bible.get("location_registry", {})
    if loc_reg:
        lines.append("### LOCATION (story takes place here)")
        lines.append(f"- **Primary City**: {loc_reg.get('primary_city', 'Not specified')}")
        for loc in loc_reg.get("key_locations", [])[:5]:
            lines.append(f"- {loc.get('name', '?')}: {loc.get('description', '')[:50]}...")

    lines.append("")

    # Timeline
    timeline = story_bible.get("timeline", {})
    if timeline:
        lines.append("### TIMELINE (use these exact timeframes)")
        lines.append(f"- **Story Present**: {timeline.get('story_present', 'Not specified')}")
        for event in timeline.get("key_dates", [])[:5]:
            years = event.get("years_before_story", "?")
            lines.append(f"- {event.get('event', '?')}: {years} years ago")

    lines.append("")

    # Relationship map
    rel_map = story_bible.get("relationship_map", [])
    if rel_map:
        lines.append("### RELATIONSHIPS")
        char_names = {c.get("id"): c.get("canonical_name") for c in story_bible.get("character_registry", [])}
        for rel in rel_map[:8]:
            char_a = char_names.get(rel.get("character_a"), rel.get("character_a"))
            char_b = char_names.get(rel.get("character_b"), rel.get("character_b"))
            lines.append(f"- {char_a} ↔ {char_b}: {rel.get('relationship_type', '?')}")

    lines.append("")

    # Consistency rules
    rules = story_bible.get("consistency_rules", [])
    if rules:
        lines.append("### CONSISTENCY RULES (MUST FOLLOW)")
        for rule in rules[:10]:
            lines.append(f"- {rule}")

    return "\n".join(lines)


# Registration
STORY_BIBLE_EXECUTORS = {
    "story_bible": execute_story_bible,
}
