"""
Structural Engine Agents (Layers 8-12)

These agents design and execute the story structure:
- Macro Plot Structure
- Pacing & Tension Design
- Chapter & Scene Blueprint
- Style & Voice Specification
- Draft Generation
"""

from typing import Dict, Any, List
from core.orchestrator import ExecutionContext


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
{target_word_count}

## Task:
Create the complete chapter blueprint:

For each chapter include:
- Chapter number and title
- Chapter goal (what must happen)
- POV character
- Opening hook
- Key scenes
- Closing hook
- Word count target

For each scene include:
- Scene question (what's at stake)
- Characters present
- Location
- Conflict type
- Outcome

## Hard Requirements (must comply)
- Return ONLY valid JSON (no markdown).
- Chapter numbers must be contiguous and increasing starting at 1 (1..N).
- Each chapter must have at least 1 scene.
- Each scene must have a numeric word_target.
- For each chapter: sum(scene.word_target) should be close to chapter.word_target (within ±35%).

## Output Format (JSON):
{{
    "chapter_outline": [
        {{
            "number": 1,
            "title": "<string>",
            "act": 1,
            "chapter_goal": "<string>",
            "pov": "<string>",
            "opening_hook": "<string>",
            "closing_hook": "<string>",
            "word_target": 3000,
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

## World Rules:
{world_rules}

## Previous Chapter Summary (if applicable):
{previous_summary}

## Task:
Write the complete chapter following:
- The scene blueprint exactly
- The voice specification rules
- Character consistency
- World rule compliance

Write engaging, publication-quality prose that:
- Opens with the specified hook
- Executes each scene's goal
- Closes with the specified hook
- Hits the word target approximately

## Output the chapter text directly.
"""


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
    """Execute chapter blueprint agent."""
    llm = context.llm_client
    constraints = context.inputs.get("user_constraints", {})

    prompt = CHAPTER_BLUEPRINT_PROMPT.format(
        plot_structure=context.inputs.get("plot_structure", {}),
        pacing_design=context.inputs.get("pacing_design", {}),
        character_architecture=context.inputs.get("character_architecture", {}),
        target_word_count=constraints.get("target_word_count", 80000)
    )

    if llm:
        response = await llm.generate(prompt, response_format="json")
        return response
    else:
        # Generate placeholder chapter outline
        chapters = []
        for i in range(1, 26):  # 25 chapters
            act = 1 if i <= 6 else (2 if i <= 18 else 3)
            chapters.append({
                "number": i,
                "title": f"Chapter {i}",
                "act": act,
                "chapter_goal": f"[Goal for chapter {i}]",
                "pov": "Protagonist",
                "opening_hook": f"[Hook for chapter {i}]",
                "closing_hook": f"[Closing hook for chapter {i}]",
                "word_target": 3200,
                "scenes": [
                    {
                        "scene_number": 1,
                        "scene_question": f"[Scene question for Ch{i}-S1]",
                        "characters": ["Protagonist"],
                        "location": "[Location]",
                        "conflict_type": "internal" if i % 2 == 0 else "external",
                        "outcome": "[Outcome]",
                        "word_target": 1600
                    },
                    {
                        "scene_number": 2,
                        "scene_question": f"[Scene question for Ch{i}-S2]",
                        "characters": ["Protagonist", "Supporting"],
                        "location": "[Location]",
                        "conflict_type": "interpersonal",
                        "outcome": "[Outcome]",
                        "word_target": 1600
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
        return response
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


async def execute_draft_generation(context: ExecutionContext) -> Dict[str, Any]:
    """Execute draft generation agent - generates all chapters."""
    llm = context.llm_client
    chapter_blueprint = context.inputs.get("chapter_blueprint", {})

    chapters = []
    chapter_metadata = []
    scene_tags: Dict[str, Any] = {}
    deviations: List[Dict[str, Any]] = []
    fix_plan: List[str] = []
    chapter_scores: Dict[str, int] = {}

    outline = chapter_blueprint.get("chapter_outline", [])

    for chapter in outline:
        chapter_num = chapter.get("number", 0)
        chapter_title = chapter.get("title", f"Chapter {chapter_num}")

        if llm:
            # Generate each chapter with LLM
            previous_summary = ""
            if chapters:
                previous_summary = f"Previous chapter ended with: {chapters[-1].get('summary', '')}"

            prompt = DRAFT_GENERATION_PROMPT.format(
                chapter_number=chapter_num,
                chapter_title=chapter_title,
                voice_specification=context.inputs.get("voice_specification", {}),
                chapter_blueprint=chapter,
                character_architecture=context.inputs.get("character_architecture", {}),
                world_rules=context.inputs.get("world_rules", {}),
                previous_summary=previous_summary
            )

            chapter_text = await llm.generate(prompt)
            summary = await llm.generate(f"Summarize this chapter in 2 sentences:\n{chapter_text[:2000]}")

            # Evaluate outline adherence (structured) for this chapter
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
            adherence = await llm.generate(adherence_prompt, response_format="json", temperature=0.2, max_tokens=1600)

            score = adherence.get("outline_adherence_score")
            if isinstance(score, int):
                chapter_scores[str(chapter_num)] = score
            else:
                chapter_scores[str(chapter_num)] = 0

            scene_tags[f"Ch{chapter_num}"] = adherence.get("scene_checks", [])
            for d in adherence.get("chapter_deviations", []) if isinstance(adherence, dict) else []:
                if isinstance(d, dict):
                    deviations.append(d)

            chapters.append({
                "number": chapter_num,
                "title": chapter_title,
                "text": chapter_text,
                "summary": summary,
                "word_count": len(chapter_text.split())
            })
        else:
            # Placeholder
            chapters.append({
                "number": chapter_num,
                "title": chapter_title,
                "text": f"[Chapter {chapter_num} content would be generated here by LLM]",
                "summary": f"Chapter {chapter_num} summary placeholder",
                "word_count": 0
            })
            chapter_scores[str(chapter_num)] = 0
            scene_tags[f"Ch{chapter_num}"] = []

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
        "fix_plan": fix_plan
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
