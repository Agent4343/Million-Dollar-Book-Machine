"""
Marketing & Commercial Optimization Agents

These agents create market-ready materials optimized for Kindle/Amazon:
- Blurb Generator (Amazon-optimized book descriptions)
- Keyword Optimizer (KDP keywords and categories)
- Series Bible (multi-book continuity tracking)
"""

from typing import Dict, Any, List
from core.orchestrator import ExecutionContext


# =============================================================================
# BLURB GENERATOR
# =============================================================================

BLURB_PROMPT = """You are an Amazon bestseller copywriter. Write a book description that SELLS.

## Book Details:
Title: {title}
Genre: {genre}
Core Promise: {core_promise}
One-Line Hook: {hook}
Protagonist: {protagonist}
Stakes: {stakes}

## Blurb Structure (follow exactly):

**HOOK (1-2 sentences)**: Grab attention immediately. Start with the protagonist's situation or a provocative question.

**SETUP (2-3 sentences)**: Introduce the conflict. What does the protagonist want? What's stopping them?

**STAKES (2-3 sentences)**: What happens if they fail? Make readers FEEL the danger/desire.

**TEASE (1 sentence)**: Hint at the journey without spoilers. Create curiosity.

**CALL TO ACTION (1 sentence)**: Why they should read NOW. Use urgency.

## Amazon Best Practices:
- First 100 characters are CRUCIAL (shown in search results)
- Use power words: "discover," "secret," "forbidden," "dangerous," "ultimate"
- Include emotional triggers for the genre
- Keep paragraphs short (mobile readers)
- Total: 150-200 words (Amazon sweet spot)

## Genre-Specific Triggers:
- Romance: passion, forbidden, heart, desire, love, surrender
- Thriller: deadly, secret, conspiracy, truth, survival, hunt
- Fantasy: ancient, power, destiny, kingdom, magic, prophecy
- Mystery: truth, hidden, deadly, secret, past, lies

## Output Format (JSON):
{{
    "short_blurb": "100-character version for ads/previews",
    "full_blurb": "Full 150-200 word description with HTML formatting",
    "a_plus_content": "Extended 300-word version for A+ Content",
    "tagline": "One punchy line for marketing",
    "comparison_pitch": "For fans of [Author] and [Author]..."
}}
"""


async def execute_blurb_generator(context: ExecutionContext) -> Dict[str, Any]:
    """Generate Amazon-optimized book blurbs."""
    llm = context.llm_client

    # Gather inputs
    concept = context.inputs.get("concept_definition", {})
    characters = context.inputs.get("character_architecture", {})
    story_question = context.inputs.get("story_question", {})
    constraints = context.inputs.get("user_constraints", {})

    protagonist = characters.get("protagonist_profile", {})
    stakes = story_question.get("stakes_ladder", {})

    prompt = BLURB_PROMPT.format(
        title=context.project.title,
        genre=constraints.get("genre", "Fiction"),
        core_promise=concept.get("core_promise", {}).get("transformation", ""),
        hook=concept.get("one_line_hook", ""),
        protagonist=f"{protagonist.get('name', 'The protagonist')} - {protagonist.get('role', '')}",
        stakes=stakes.get("ultimate", {}).get("risk", "Everything is at stake")
    )

    if llm:
        result = await llm.generate(prompt, response_format="json", max_tokens=1500)
        if isinstance(result, dict):
            return result

    # Fallback for demo mode
    title = context.project.title
    genre = constraints.get("genre", "Fiction")

    return {
        "short_blurb": f"A gripping {genre.lower()} that will keep you turning pages until the stunning finale.",
        "full_blurb": f"""<p><b>{protagonist.get('name', 'They')} thought they knew the rules.</b></p>

<p>But when {concept.get('one_line_hook', 'everything changes')}, nothing will ever be the same.</p>

<p>Now, with everything on the line, one choice will determine their fate—and the fate of everyone they love.</p>

<p><i>Some secrets are worth dying for. Some truths are worth killing for.</i></p>

<p><b>{title}</b> is a pulse-pounding {genre.lower()} that fans of the genre won't want to miss.</p>

<p><b>Scroll up and click "Buy Now" to start reading today!</b></p>""",
        "a_plus_content": f"[Extended A+ Content for {title} - 300 words with author bio and series info]",
        "tagline": concept.get("one_line_hook", f"A {genre.lower()} you won't forget."),
        "comparison_pitch": f"For fans of bestselling {genre.lower()} authors..."
    }


# =============================================================================
# KEYWORD OPTIMIZER
# =============================================================================

KEYWORD_PROMPT = """You are a KDP keyword specialist. Generate keywords that will maximize discoverability.

## Book Details:
Title: {title}
Genre: {genre}
Themes: {themes}
Setting: {setting}
Protagonist Type: {protagonist_type}
Plot Elements: {plot_elements}

## KDP Keyword Rules:
- 7 keyword phrases maximum
- Each phrase can be up to 50 characters
- Use phrases readers actually search for
- Mix broad and specific terms
- Include tropes and reader expectations
- NO author names, NO competitor titles
- NO subjective claims ("best," "amazing")

## Keyword Categories to Cover:
1. **Genre + Subgenre**: "dark romance mafia" or "cozy mystery small town"
2. **Tropes**: "enemies to lovers" or "chosen one fantasy"
3. **Setting**: "new york romance" or "victorian mystery"
4. **Mood/Tone**: "suspenseful thriller" or "heartwarming romance"
5. **Protagonist**: "strong female lead" or "billionaire romance"
6. **Comp Titles/Authors**: Use style, not names: "mafia romance like dark mafia books"
7. **Reader Need**: "beach read" or "book club fiction"

## BISAC Categories:
Select the 2 most appropriate BISAC categories for this book.

## Output Format (JSON):
{{
    "primary_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7"],
    "backup_keywords": ["alt1", "alt2", "alt3", "alt4", "alt5"],
    "bisac_categories": [
        {{"code": "FIC027020", "name": "FICTION / Romance / Contemporary"}},
        {{"code": "FIC031010", "name": "FICTION / Thrillers / Crime"}}
    ],
    "amazon_categories": [
        "Kindle Store > Kindle eBooks > Romance > Contemporary",
        "Kindle Store > Kindle eBooks > Romance > Romantic Suspense"
    ],
    "search_volume_notes": "Notes on which keywords have highest search volume",
    "competition_notes": "Notes on keyword competition levels"
}}
"""


async def execute_keyword_optimizer(context: ExecutionContext) -> Dict[str, Any]:
    """Generate optimized KDP keywords and categories."""
    llm = context.llm_client

    # Gather inputs
    constraints = context.inputs.get("user_constraints", {})
    world_rules = context.inputs.get("world_rules", {})
    characters = context.inputs.get("character_architecture", {})
    thematic = context.inputs.get("thematic_architecture", {})
    plot = context.inputs.get("plot_structure", {})

    # Extract plot elements
    plot_elements = []
    for beat in plot.get("major_beats", [])[:5]:
        if isinstance(beat, dict):
            plot_elements.append(beat.get("name", ""))

    prompt = KEYWORD_PROMPT.format(
        title=context.project.title,
        genre=constraints.get("genre", "Fiction"),
        themes=constraints.get("themes", []),
        setting=world_rules.get("physical_rules", {}).get("geography", "Contemporary"),
        protagonist_type=characters.get("protagonist_profile", {}).get("role", ""),
        plot_elements=", ".join(plot_elements) if plot_elements else "character-driven story"
    )

    if llm:
        result = await llm.generate(prompt, response_format="json", max_tokens=1000)
        if isinstance(result, dict):
            return result

    # Fallback with genre-specific defaults
    genre = constraints.get("genre", "Fiction").lower()

    genre_keywords = {
        "romance": [
            "contemporary romance",
            "emotional love story",
            "second chance romance",
            "strong female lead romance",
            "romantic fiction",
            "love story books",
            "romance novels"
        ],
        "thriller": [
            "psychological thriller",
            "suspense thriller",
            "crime thriller fiction",
            "mystery suspense",
            "page turner thriller",
            "dark thriller",
            "twisty thriller"
        ],
        "fantasy": [
            "epic fantasy adventure",
            "fantasy fiction",
            "magic and adventure",
            "fantasy world building",
            "fantasy series",
            "sword and sorcery",
            "fantasy quest"
        ],
        "mystery": [
            "mystery fiction",
            "detective mystery",
            "whodunit mystery",
            "cozy mystery",
            "crime fiction mystery",
            "amateur sleuth",
            "mystery suspense"
        ]
    }

    keywords = genre_keywords.get(genre, [
        f"{genre} fiction",
        "contemporary fiction",
        "book club reads",
        "literary fiction",
        "character driven fiction",
        "emotional fiction",
        "adult fiction"
    ])

    return {
        "primary_keywords": keywords[:7],
        "backup_keywords": keywords[3:] + ["bestseller fiction", "new release"],
        "bisac_categories": [
            {"code": "FIC000000", "name": f"FICTION / General"},
            {"code": "FIC019000", "name": f"FICTION / Literary"}
        ],
        "amazon_categories": [
            f"Kindle Store > Kindle eBooks > Literature & Fiction > {genre.title()}",
            "Kindle Store > Kindle eBooks > Literature & Fiction > Contemporary Fiction"
        ],
        "search_volume_notes": "Keywords selected based on common genre search patterns",
        "competition_notes": "Mix of high-volume and niche keywords for balanced visibility"
    }


# =============================================================================
# SERIES BIBLE
# =============================================================================

SERIES_BIBLE_PROMPT = """You are a series continuity manager. Create a Series Bible for multi-book planning.

## Current Book:
Title: {title}
Story Bible: {story_bible_summary}

## Manuscript Summary:
{manuscript_summary}

## Task:
Create a Series Bible that tracks:

1. **Unresolved Threads**: Plot points that could continue
2. **Character Arcs Remaining**: Growth potential for future books
3. **World Expansion Opportunities**: Unexplored areas of the world
4. **Relationship Dynamics**: Evolving relationships to continue
5. **Series Potential**: Could this be a series? What kind?

## Output Format (JSON):
{{
    "series_potential": {{
        "score": 1-10,
        "type": "standalone|duology|trilogy|open_series",
        "reasoning": "Why this could/couldn't be a series"
    }},
    "unresolved_threads": [
        {{"thread": "...", "potential": "How it could develop", "book": "Which book it fits"}}
    ],
    "character_futures": [
        {{"character": "...", "arc_completed": true/false, "future_potential": "..."}}
    ],
    "world_expansion": [
        {{"area": "...", "explored_in_book_1": true/false, "expansion_ideas": "..."}}
    ],
    "series_hooks": [
        "Explicit hooks planted for sequels"
    ],
    "spinoff_potential": [
        {{"character": "...", "spinoff_concept": "..."}}
    ],
    "timeline_for_series": {{
        "book_1": "Current story timeframe",
        "book_2_potential": "When book 2 could take place",
        "book_3_potential": "When book 3 could take place"
    }},
    "recurring_elements": [
        "Elements that should appear in all books"
    ],
    "series_title_suggestions": [
        "Potential series name options"
    ]
}}
"""


async def execute_series_bible(context: ExecutionContext) -> Dict[str, Any]:
    """Create a series bible for multi-book continuity."""
    llm = context.llm_client

    # Gather inputs
    story_bible = context.inputs.get("story_bible", {})
    draft = context.inputs.get("draft_generation", {})
    characters = context.inputs.get("character_architecture", {})

    # Create story bible summary
    bible_summary = []
    for char in story_bible.get("character_registry", [])[:5]:
        bible_summary.append(f"- {char.get('canonical_name')}: {char.get('role')}")

    # Create manuscript summary from chapters
    chapters = draft.get("chapters", [])
    manuscript_summary = f"{len(chapters)} chapters written"
    if chapters:
        first_ch = chapters[0].get("summary", "")
        last_ch = chapters[-1].get("summary", "") if len(chapters) > 1 else ""
        manuscript_summary += f"\nOpening: {first_ch[:200]}\nEnding: {last_ch[:200]}"

    prompt = SERIES_BIBLE_PROMPT.format(
        title=context.project.title,
        story_bible_summary="\n".join(bible_summary) or "No story bible available",
        manuscript_summary=manuscript_summary
    )

    if llm:
        result = await llm.generate(prompt, response_format="json", max_tokens=2000)
        if isinstance(result, dict):
            return result

    # Fallback
    protagonist = characters.get("protagonist_profile", {}).get("name", "Protagonist")

    return {
        "series_potential": {
            "score": 7,
            "type": "trilogy",
            "reasoning": "Strong character foundation with room for growth"
        },
        "unresolved_threads": [
            {"thread": "Antagonist's larger network", "potential": "Could be explored in book 2", "book": "2"},
            {"thread": "Protagonist's past", "potential": "Deeper exploration", "book": "2-3"}
        ],
        "character_futures": [
            {"character": protagonist, "arc_completed": True, "future_potential": "New challenges in changed role"},
            {"character": "Supporting cast", "arc_completed": False, "future_potential": "Could lead spinoffs"}
        ],
        "world_expansion": [
            {"area": "Other locations mentioned", "explored_in_book_1": False, "expansion_ideas": "Set book 2 there"}
        ],
        "series_hooks": [
            "Hints at larger conspiracy",
            "Unresolved romantic subplot",
            "Mentor's hidden past"
        ],
        "spinoff_potential": [
            {"character": "Key supporting character", "spinoff_concept": "Their origin story"}
        ],
        "timeline_for_series": {
            "book_1": "Present day",
            "book_2_potential": "6 months later",
            "book_3_potential": "1-2 years later"
        },
        "recurring_elements": [
            "Core location",
            "Key relationships",
            "Thematic questions"
        ],
        "series_title_suggestions": [
            f"The {context.project.title.split()[0]} Series",
            f"{protagonist}'s Journey",
            "Themed series name based on central conflict"
        ]
    }


# =============================================================================
# ALSO BOUGHT / COMP TITLE ANALYZER
# =============================================================================

async def execute_comp_analysis(context: ExecutionContext) -> Dict[str, Any]:
    """Analyze comparable titles for positioning."""
    constraints = context.inputs.get("user_constraints", {})
    comparable_titles = constraints.get("comparable_titles", [])
    genre = constraints.get("genre", "Fiction")

    # In production, this would scrape Amazon for actual comp data
    return {
        "provided_comps": comparable_titles,
        "positioning_recommendations": [
            f"Position as fresh take on {genre.lower()}",
            "Emphasize unique elements in blurb",
            "Target readers of similar authors"
        ],
        "price_positioning": {
            "launch_price": "$2.99-$4.99 for visibility",
            "regular_price": "$4.99-$6.99",
            "ku_recommendation": "Enroll in Kindle Unlimited for first 90 days"
        },
        "launch_strategy": [
            "Pre-order 2-4 weeks before launch",
            "ARC readers for launch day reviews",
            "Newsletter swap with similar authors",
            "Amazon Ads targeting comp titles"
        ]
    }


# =============================================================================
# REGISTRATION
# =============================================================================

MARKETING_EXECUTORS = {
    "blurb_generator": execute_blurb_generator,
    "keyword_optimizer": execute_keyword_optimizer,
    "series_bible": execute_series_bible,
    "comp_analysis": execute_comp_analysis,
}
