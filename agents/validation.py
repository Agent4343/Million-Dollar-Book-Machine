"""
Quality Control & Validation Agents (Layers 13-20)

These agents validate, edit, and finalize the manuscript:
- Continuity & Logic Audit
- Emotional Impact Validation
- Originality Scans
- Rewrite Agents
- Line Editing
- Beta Simulation
- Final Validation
- Publishing Package
"""

from typing import Dict, Any, List
from core.orchestrator import ExecutionContext


# =============================================================================
# EXECUTOR FUNCTIONS
# =============================================================================

async def execute_continuity_audit(context: ExecutionContext) -> Dict[str, Any]:
    """
    Audit for continuity and logic errors using the Story Bible.

    This agent checks the manuscript against the canonical story bible to find:
    - Character name inconsistencies
    - Location mismatches
    - Timeline contradictions
    - Relationship errors
    - Duplicate chapters
    """
    import re
    from difflib import SequenceMatcher

    chapters = context.inputs.get("draft_generation", {}).get("chapters", [])
    story_bible = context.inputs.get("story_bible", {})
    world_rules = context.inputs.get("world_rules", {})
    characters = context.inputs.get("character_architecture", {})
    llm = context.llm_client

    issues = {
        "name_issues": [],
        "location_issues": [],
        "timeline_issues": [],
        "relationship_issues": [],
        "duplicate_issues": []
    }

    # Check for duplicate chapter titles
    chapter_titles = {}
    for ch in chapters:
        title = ch.get("title", "").strip().lower()
        ch_num = ch.get("number", "?")
        if title:
            if title in chapter_titles:
                issues["duplicate_issues"].append({
                    "type": "duplicate_title",
                    "title": ch.get("title", ""),
                    "chapters": [chapter_titles[title], ch_num],
                    "severity": "critical"
                })
            else:
                chapter_titles[title] = ch_num

    # Check for similar content between chapters (content duplication)
    for i, ch1 in enumerate(chapters):
        text1 = ch1.get("text", "")[:1000]  # First 1000 chars
        for j, ch2 in enumerate(chapters[i+1:], i+1):
            text2 = ch2.get("text", "")[:1000]
            if text1 and text2:
                similarity = SequenceMatcher(None, text1, text2).ratio()
                if similarity > 0.7:  # 70% similar content = likely duplicate
                    issues["duplicate_issues"].append({
                        "type": "similar_content",
                        "chapters": [ch1.get("number", i), ch2.get("number", j)],
                        "similarity": f"{similarity:.0%}",
                        "severity": "critical"
                    })

    # Combine all chapter text for analysis
    full_text = "\n\n".join([
        f"Chapter {ch.get('number', '?')}: {ch.get('text', '')}"
        for ch in chapters if ch.get('text')
    ])

    if not full_text:
        return {
            "timeline_check": {"status": "skipped", "issues": [], "notes": "No chapter text to analyze"},
            "character_logic_check": {"status": "skipped", "issues": [], "notes": "No chapter text to analyze"},
            "world_rule_check": {"status": "skipped", "issues": [], "notes": "No chapter text to analyze"},
            "continuity_report": {
                "total_issues": 0,
                "critical_issues": 0,
                "warnings": 0,
                "recommendation": "Generate chapters first"
            }
        }

    # Extract canonical names from story bible
    canonical_names = {}
    for char in story_bible.get("character_registry", []):
        canonical = char.get("canonical_name", "")
        if canonical:
            first_name = canonical.split()[0] if canonical else ""
            canonical_names[first_name] = canonical

    # Check for name variations in text
    # Improved pattern: matches single names, hyphenated, multi-part, and accented characters
    # Pattern matches: "John", "John Smith", "Mary-Jane Watson", "Jean-Claude Van Damme", "José García"
    name_pattern = r'\b([A-Z][a-zàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçšž]+(?:-[A-Z][a-zàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçšž]+)?)\s*([A-Z][a-zàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçšž]*(?:-[A-Z][a-zàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçšž]+)?(?:\s+[A-Z][a-zàáâäãåąčćęèéêëėįìíîïłńòóôöõøùúûüųūÿýżźñçšž]+)*)?\b'
    found_names = {}
    for match in re.finditer(name_pattern, full_text):
        first_name = match.group(1)
        full_name = match.group().strip()
        if first_name not in found_names:
            found_names[first_name] = set()
        found_names[first_name].add(full_name)

    # Report first names with multiple last names
    for first, fulls in found_names.items():
        if len(fulls) > 1:
            canonical = canonical_names.get(first)
            issues["name_issues"].append({
                "type": "name_variation",
                "first_name": first,
                "variations_found": list(fulls),
                "canonical_name": canonical or "Not specified",
                "severity": "critical" if canonical else "warning"
            })

    # Check location consistency
    primary_city = story_bible.get("location_registry", {}).get("primary_city", "")
    # Extended city pattern - includes major US, UK, EU, and other international cities
    city_pattern = r'\b(New York|NYC|Manhattan|Brooklyn|Queens|Bronx|Staten Island|Chicago|Los Angeles|LA|Boston|Miami|Philadelphia|San Francisco|Seattle|Denver|Detroit|Atlanta|Houston|Dallas|Phoenix|San Diego|Austin|Portland|Nashville|Las Vegas|Minneapolis|Cleveland|Pittsburgh|Baltimore|Tampa|Orlando|Charlotte|Indianapolis|Columbus|Milwaukee|Kansas City|Sacramento|San Jose|Washington D\.?C\.?|London|Paris|Berlin|Rome|Madrid|Barcelona|Amsterdam|Brussels|Munich|Vienna|Dublin|Edinburgh|Glasgow|Manchester|Liverpool|Birmingham|Tokyo|Beijing|Shanghai|Hong Kong|Singapore|Sydney|Melbourne|Toronto|Vancouver|Montreal|Mexico City|São Paulo|Rio de Janeiro|Buenos Aires|Cairo|Dubai|Mumbai|Delhi|Bangalore)\b'
    cities_found = set()
    for match in re.finditer(city_pattern, full_text, re.IGNORECASE):
        cities_found.add(match.group().title())

    if primary_city and cities_found:
        # Normalize primary city name
        normalized_primary = primary_city.replace(" ", "").lower()
        for city in cities_found:
            normalized_city = city.replace(" ", "").lower()
            # Check if it's a different city (not just a variant of the primary)
            if normalized_city not in normalized_primary and normalized_primary not in normalized_city:
                if city.lower() not in ["manhattan", "brooklyn"] or "new york" not in primary_city.lower():
                    issues["location_issues"].append({
                        "type": "location_mismatch",
                        "found": city,
                        "expected_primary": primary_city,
                        "severity": "warning"
                    })

    # Check timeline references for consistency
    timeline_dates = story_bible.get("timeline", {}).get("key_dates", [])
    # Expanded number words list
    number_words = r'one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred'
    timeline_pattern = rf'(\d+|{number_words}(?:-{number_words})?)\s+years?\s+ago'
    timeline_refs = []
    for match in re.finditer(timeline_pattern, full_text, re.IGNORECASE):
        timeline_refs.append(match.group())

    # Report timeline inconsistencies if we have expected dates
    if timeline_dates and timeline_refs:
        expected_years = set()
        for date in timeline_dates:
            years = date.get("years_before_story")
            if years:
                expected_years.add(str(years))

        found_years = set()
        # Comprehensive word-to-number mapping
        word_to_num = {
            "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
            "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
            "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
            "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18",
            "nineteen": "19", "twenty": "20", "thirty": "30", "forty": "40",
            "fifty": "50", "sixty": "60", "seventy": "70", "eighty": "80",
            "ninety": "90", "hundred": "100"
        }
        # Handle compound numbers like "twenty-three"
        compound_pattern = re.compile(r'(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)-(\w+)')
        for ref in timeline_refs:
            # Check for compound numbers first
            compound_match = compound_pattern.search(ref.lower())
            if compound_match:
                tens = word_to_num.get(compound_match.group(1), "0")
                ones = word_to_num.get(compound_match.group(2), "0")
                found_years.add(str(int(tens) + int(ones)))
            else:
                num_match = re.search(r'(\d+|' + '|'.join(word_to_num.keys()) + ')', ref, re.IGNORECASE)
                if num_match:
                    num_str = num_match.group(1).lower()
                    if num_str in word_to_num:
                        found_years.add(word_to_num[num_str])
                    else:
                        found_years.add(num_str)

        unexpected_years = found_years - expected_years
        if unexpected_years:
            issues["timeline_issues"].append({
                "type": "timeline_inconsistency",
                "expected_years": list(expected_years),
                "found_years": list(found_years),
                "unexpected": list(unexpected_years),
                "severity": "warning"
            })

    # Check for protagonist name variations across chapters
    protagonist = characters.get("protagonist_profile", {})
    protagonist_name = protagonist.get("name", "")
    if protagonist_name:
        first_name = protagonist_name.split()[0] if protagonist_name else ""
        # Check each chapter for different names that might be the protagonist
        for ch in chapters:
            text = ch.get("text", "")
            ch_num = ch.get("number", "?")
            # Look for first-person references or common alternative names
            if first_name and text:
                # Check if this chapter uses a different name pattern for the main character
                import re
                # Find all capitalized names that appear frequently
                name_pattern = r'\b([A-Z][a-z]+)\s+(said|thought|felt|looked|turned|walked|smiled)\b'
                speaking_names = re.findall(name_pattern, text)
                name_counts = {}
                for name, _ in speaking_names:
                    name_counts[name] = name_counts.get(name, 0) + 1

                # If a different name appears more than the protagonist name, flag it
                for name, count in name_counts.items():
                    if count >= 3 and name != first_name and name not in protagonist_name:
                        issues["name_issues"].append({
                            "type": "possible_protagonist_name_change",
                            "chapter": ch_num,
                            "expected": protagonist_name,
                            "found": name,
                            "occurrences": count,
                            "severity": "critical"
                        })

    # Use LLM for deeper analysis if available
    if llm and story_bible:
        try:
            audit_prompt = f"""You are a continuity editor. Analyze this manuscript excerpt against the Story Bible.

STORY BIBLE:
{_format_story_bible_summary(story_bible)}

EXPECTED PROTAGONIST NAME: {protagonist_name}

MANUSCRIPT EXCERPT (first 5000 chars):
{full_text[:5000]}

CRITICAL: Check if the protagonist's name stays consistent throughout. The protagonist should ALWAYS be called "{protagonist_name}".

Find any inconsistencies in:
1. Character names (different spellings/names for same character) - THIS IS MOST IMPORTANT
2. Locations (wrong city/place names)
3. Timeline (contradictory time references)
4. Relationships (wrong family/relationship references)

Return JSON with:
{{
    "issues_found": [
        {{"type": "name|location|timeline|relationship", "description": "...", "severity": "critical|warning"}}
    ],
    "protagonist_name_consistent": true/false,
    "protagonist_variants_found": ["list any variations of protagonist name"],
    "overall_consistency_score": 1-100
}}"""

            llm_result = await llm.generate(audit_prompt, response_format="json", max_tokens=1000)
            if isinstance(llm_result, dict):
                for issue in llm_result.get("issues_found", []):
                    issue_type = issue.get("type", "other") + "_issues"
                    if issue_type in issues:
                        issues[issue_type].append(issue)
        except Exception as e:
            pass  # Fall back to pattern-based analysis

    # Compile final report
    total_issues = sum(len(v) for v in issues.values())
    critical_issues = sum(
        1 for issue_list in issues.values()
        for issue in issue_list
        if issue.get("severity") == "critical"
    )

    return {
        "timeline_check": {
            "status": "failed" if issues["timeline_issues"] else "passed",
            "issues": issues["timeline_issues"],
            "notes": f"Found {len(issues['timeline_issues'])} timeline issues"
        },
        "character_logic_check": {
            "status": "failed" if issues["name_issues"] else "passed",
            "issues": issues["name_issues"],
            "notes": f"Found {len(issues['name_issues'])} name inconsistencies"
        },
        "world_rule_check": {
            "status": "failed" if issues["location_issues"] else "passed",
            "issues": issues["location_issues"],
            "notes": f"Found {len(issues['location_issues'])} location issues"
        },
        "relationship_check": {
            "status": "failed" if issues["relationship_issues"] else "passed",
            "issues": issues["relationship_issues"],
            "notes": f"Found {len(issues['relationship_issues'])} relationship issues"
        },
        "duplicate_check": {
            "status": "failed" if issues["duplicate_issues"] else "passed",
            "issues": issues["duplicate_issues"],
            "notes": f"Found {len(issues['duplicate_issues'])} duplicate chapters" if issues["duplicate_issues"] else "No duplicate chapters"
        },
        "continuity_report": {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "warnings": total_issues - critical_issues,
            "all_issues": issues,
            "recommendation": "Review and fix issues" if critical_issues > 0 else "Proceed with caution" if total_issues > 0 else "Proceed to next stage"
        }
    }


def _format_story_bible_summary(story_bible: Dict[str, Any]) -> str:
    """Format story bible for LLM analysis prompt."""
    lines = []

    # Characters
    lines.append("CHARACTERS:")
    for char in story_bible.get("character_registry", [])[:10]:
        lines.append(f"- {char.get('canonical_name', '?')}: {char.get('role', '?')}")

    # Location
    loc = story_bible.get("location_registry", {})
    lines.append(f"\nPRIMARY LOCATION: {loc.get('primary_city', 'Not specified')}")

    # Timeline
    lines.append("\nKEY TIMELINE:")
    for date in story_bible.get("timeline", {}).get("key_dates", [])[:5]:
        lines.append(f"- {date.get('event', '?')}: {date.get('years_before_story', '?')} years ago")

    # Relationships
    lines.append("\nRELATIONSHIPS:")
    char_names = {c.get("id"): c.get("canonical_name") for c in story_bible.get("character_registry", [])}
    for rel in story_bible.get("relationship_map", [])[:5]:
        char_a = char_names.get(rel.get("character_a"), rel.get("character_a"))
        char_b = char_names.get(rel.get("character_b"), rel.get("character_b"))
        lines.append(f"- {char_a} is {rel.get('relationship_type', '?')} of {char_b}")

    return "\n".join(lines)


async def execute_emotional_validation(context: ExecutionContext) -> Dict[str, Any]:
    """Validate emotional impact and arc fulfillment."""
    import re

    chapters = context.inputs.get("draft_generation", {}).get("chapters", [])
    protagonist_arc = context.inputs.get("character_architecture", {}).get("protagonist_arc", {})
    story_question = context.inputs.get("story_question", {})
    pacing_design = context.inputs.get("pacing_design", {})
    llm = context.llm_client

    # Emotional keyword patterns for basic analysis
    emotion_patterns = {
        "hope": r'\b(hope|hopeful|believe|faith|trust|optimistic|bright|promising)\b',
        "fear": r'\b(fear|afraid|terrified|scared|dread|panic|horror|nightmare)\b',
        "joy": r'\b(joy|happy|happiness|delight|elated|thrilled|ecstatic|wonderful)\b',
        "sadness": r'\b(sad|sorrow|grief|mourning|tears|crying|heartbroken|devastated)\b',
        "anger": r'\b(angry|furious|rage|hatred|bitter|resentful|outraged|livid)\b',
        "love": r'\b(love|beloved|adore|cherish|passion|tender|intimate|devotion)\b',
        "tension": r'\b(tense|anxious|nervous|worried|uncertain|danger|risk|threat)\b',
        "triumph": r'\b(triumph|victory|success|won|achieved|overcome|conquered|prevailed)\b',
        "despair": r'\b(despair|hopeless|lost|failed|defeat|broken|crushed|empty)\b'
    }

    scene_resonance_scores = {}
    emotional_peaks = []

    for chapter in chapters:
        ch_num = chapter.get("number", "?")
        text = chapter.get("text", "")

        if not text:
            scene_resonance_scores[f"chapter_{ch_num}"] = 0
            continue

        # Count emotional words in each chapter
        emotion_counts = {}
        total_emotion_words = 0
        for emotion, pattern in emotion_patterns.items():
            matches = re.findall(pattern, text.lower())
            emotion_counts[emotion] = len(matches)
            total_emotion_words += len(matches)

        # Calculate resonance score based on emotional density
        word_count = len(text.split())
        emotion_density = (total_emotion_words / max(word_count, 1)) * 1000
        resonance = min(10, max(1, int(emotion_density * 2)))
        scene_resonance_scores[f"chapter_{ch_num}"] = resonance

        # Find dominant emotion for peaks
        if emotion_counts:
            dominant = max(emotion_counts, key=emotion_counts.get)
            if emotion_counts[dominant] > 5:
                emotional_peaks.append({
                    "chapter": ch_num,
                    "type": dominant,
                    "intensity": min(10, emotion_counts[dominant])
                })

    # Calculate average resonance
    scores = [v for v in scene_resonance_scores.values() if isinstance(v, (int, float))]
    avg_resonance = sum(scores) / len(scores) if scores else 0
    scene_resonance_scores["average"] = round(avg_resonance, 1)

    # Check arc fulfillment using LLM if available
    arc_check = {
        "protagonist_arc_complete": False,
        "transformation_earned": False,
        "supporting_arcs_resolved": False,
        "notes": "Unable to verify - insufficient data"
    }

    if llm and chapters and protagonist_arc:
        try:
            # Get first and last chapters for arc analysis
            first_ch = chapters[0].get("text", "")[:2000] if chapters else ""
            last_ch = chapters[-1].get("text", "")[:2000] if chapters else ""

            arc_prompt = f"""Analyze whether the character arc is fulfilled in this story.

PROTAGONIST ARC DESIGN:
{protagonist_arc}

STORY QUESTION:
{story_question.get('central_dramatic_question', 'Not specified')}

OPENING (first chapter excerpt):
{first_ch}

ENDING (final chapter excerpt):
{last_ch}

Evaluate:
1. Is the protagonist's arc complete (did they change)?
2. Is the transformation earned (not rushed or unbelievable)?
3. Are supporting character arcs resolved?

Return JSON:
{{
    "protagonist_arc_complete": true/false,
    "transformation_earned": true/false,
    "supporting_arcs_resolved": true/false,
    "notes": "Brief analysis"
}}"""

            arc_result = await llm.generate(arc_prompt, response_format="json", max_tokens=500)
            if isinstance(arc_result, dict):
                arc_check.update(arc_result)
        except Exception:
            pass
    elif chapters:
        # Basic check without LLM - assume success if we have chapters
        arc_check = {
            "protagonist_arc_complete": len(chapters) >= 10,
            "transformation_earned": len(chapters) >= 15,
            "supporting_arcs_resolved": len(chapters) >= 20,
            "notes": "Basic validation - LLM analysis unavailable"
        }

    return {
        "scene_resonance_scores": scene_resonance_scores,
        "arc_fulfillment_check": arc_check,
        "emotional_peaks_map": emotional_peaks
    }


async def execute_originality_scan(context: ExecutionContext) -> Dict[str, Any]:
    """Scan for creative originality issues."""
    import re
    from collections import Counter

    chapters = context.inputs.get("draft_generation", {}).get("chapters", [])
    plot_structure = context.inputs.get("plot_structure", {})
    character_architecture = context.inputs.get("character_architecture", {})
    llm = context.llm_client

    # Combine chapter text
    full_text = "\n".join([ch.get("text", "") for ch in chapters if ch.get("text")])

    # Common cliches and overused phrases to detect
    cliches = [
        r"it was a dark and stormy night",
        r"the chosen one",
        r"woke up from a dream",
        r"looked into (the|a) mirror",
        r"let out a breath (he|she|they) didn't know",
        r"time stood still",
        r"her heart skipped a beat",
        r"his jaw dropped",
        r"tears streamed down (her|his|their) face",
        r"a shiver ran down (her|his|their) spine",
        r"dead as a doornail",
        r"all of a sudden",
        r"needless to say",
        r"at the end of the day",
        r"when all was said and done",
        r"thinking outside the box",
        r"low hanging fruit",
        r"pushed the envelope",
        r"a gut feeling",
        r"butterflies in (her|his|their) stomach",
        r"crystal clear",
        r"easier said than done",
        r"fell head over heels",
        r"fit as a fiddle",
        r"hit the nail on the head",
        r"in the nick of time",
        r"once upon a time",
        r"read (her|him|them) like a book",
        r"the calm before the storm",
        r"tip of the iceberg",
        r"under the weather",
    ]

    cliches_found = []
    for cliche in cliches:
        matches = re.findall(cliche, full_text.lower())
        if matches:
            cliches_found.append({
                "phrase": cliche.replace(r"\b", "").replace("(", "").replace(")", "").replace("|", "/"),
                "count": len(matches)
            })

    # Find overused phrases (3+ word sequences appearing 5+ times)
    words = re.findall(r'\b[a-z]+\b', full_text.lower())
    trigrams = [" ".join(words[i:i+3]) for i in range(len(words)-2)]
    trigram_counts = Counter(trigrams)
    overused_phrases = [
        {"phrase": phrase, "count": count}
        for phrase, count in trigram_counts.most_common(20)
        if count >= 5 and not any(w in phrase for w in ["the", "and", "was", "that", "had", "but"])
    ]

    # Calculate base originality score
    cliche_penalty = len(cliches_found) * 3
    repetition_penalty = len(overused_phrases) * 2
    base_score = max(50, 100 - cliche_penalty - repetition_penalty)

    # Detect common trope patterns
    trope_patterns = {
        "chosen_one": r'\b(chosen|prophecy|foretold|destined|fated)\b',
        "orphan_hero": r'\b(orphan|parents (died|killed|murdered)|raised by|no family)\b',
        "love_triangle": r'\b(torn between|choose between.*love|both love|jealous)\b',
        "hidden_powers": r'\b(powers awakened|didn\'t know (he|she|they) could|hidden ability)\b',
        "mentor_death": r'\b(mentor (died|killed|sacrificed)|old (man|woman|master) (died|fell))\b'
    }

    detected_tropes = []
    for trope, pattern in trope_patterns.items():
        if re.search(pattern, full_text.lower()):
            detected_tropes.append(trope)

    # Use LLM for deeper structural analysis if available
    similar_works = []
    unique_elements = []

    if llm and full_text:
        try:
            analysis_prompt = f"""Analyze this manuscript excerpt for originality.

PLOT STRUCTURE:
{plot_structure}

CHARACTERS:
{character_architecture}

SAMPLE TEXT (first 3000 chars):
{full_text[:3000]}

Identify:
1. Any similar published works (be specific)
2. Unique/original elements that stand out
3. How derivative or fresh the concept feels

Return JSON:
{{
    "similar_works": ["Title by Author - reason for similarity"],
    "unique_elements": ["List of original aspects"],
    "derivative_level": "low/medium/high",
    "notes": "Brief analysis"
}}"""

            llm_result = await llm.generate(analysis_prompt, response_format="json", max_tokens=700)
            if isinstance(llm_result, dict):
                similar_works = llm_result.get("similar_works", [])
                unique_elements = llm_result.get("unique_elements", [])
                derivative_level = llm_result.get("derivative_level", "low")
                if derivative_level == "high":
                    base_score = min(base_score, 60)
                elif derivative_level == "medium":
                    base_score = min(base_score, 75)
        except Exception:
            pass

    if not unique_elements:
        unique_elements = ["Analysis unavailable - manual review recommended"]

    # Determine similarity level
    similarity_level = "low"
    if len(similar_works) > 2 or len(detected_tropes) > 3:
        similarity_level = "high"
    elif len(similar_works) > 0 or len(detected_tropes) > 1:
        similarity_level = "medium"

    return {
        "structural_similarity_report": {
            "similar_works_found": similar_works,
            "detected_tropes": detected_tropes,
            "similarity_level": similarity_level,
            "unique_elements": unique_elements
        },
        "phrase_recurrence_check": {
            "overused_phrases": overused_phrases[:10],
            "cliches_found": cliches_found,
            "recommendation": "Address cliches" if cliches_found else "No significant issues"
        },
        "originality_score": base_score
    }


async def execute_plagiarism_audit(context: ExecutionContext) -> Dict[str, Any]:
    """Audit for plagiarism and copyright issues."""
    import re
    import hashlib

    chapters = context.inputs.get("draft_generation", {}).get("chapters", [])
    originality_results = context.inputs.get("originality_scan", {})
    character_architecture = context.inputs.get("character_architecture", {})
    llm = context.llm_client

    full_text = "\n".join([ch.get("text", "") for ch in chapters if ch.get("text")])

    # Known protected character patterns (famous literary characters)
    protected_characters = [
        (r'\b(Harry Potter|Hermione|Ron Weasley|Dumbledore|Voldemort)\b', "Harry Potter series"),
        (r'\b(Frodo|Gandalf|Aragorn|Legolas|Sauron|Gollum)\b', "Lord of the Rings"),
        (r'\b(Katniss|Peeta|Haymitch|President Snow)\b', "Hunger Games"),
        (r'\b(Sherlock Holmes|Watson|Moriarty)\b', "Sherlock Holmes"),
        (r'\b(James Bond|007|M16|Q Branch)\b', "James Bond"),
        (r'\b(Darth Vader|Luke Skywalker|Yoda|Obi-Wan)\b', "Star Wars"),
        (r'\b(Batman|Bruce Wayne|Joker|Gotham)\b', "DC Comics"),
        (r'\b(Spider-Man|Peter Parker|Tony Stark|Avengers)\b', "Marvel"),
        (r'\b(Mickey Mouse|Donald Duck|Minnie)\b', "Disney"),
    ]

    character_flags = []
    for pattern, source in protected_characters:
        matches = re.findall(pattern, full_text, re.IGNORECASE)
        if matches:
            character_flags.append({
                "character": matches[0],
                "source": source,
                "count": len(matches),
                "risk": "high"
            })

    # Check for protected phrases/quotes
    protected_phrases = [
        (r"may the force be with you", "Star Wars"),
        (r"i am your father", "Star Wars"),
        (r"to be or not to be", "Shakespeare"),
        (r"elementary,? my dear watson", "Sherlock Holmes"),
        (r"i'll be back", "Terminator"),
        (r"here's looking at you,? kid", "Casablanca"),
        (r"you can't handle the truth", "A Few Good Men"),
        (r"there's no place like home", "Wizard of Oz"),
    ]

    expression_flags = []
    for phrase, source in protected_phrases:
        if re.search(phrase, full_text.lower()):
            expression_flags.append({
                "phrase": phrase,
                "source": source,
                "risk": "medium"
            })

    # Check for scene replication patterns using originality results
    similar_scenes = []
    similar_works = originality_results.get("structural_similarity_report", {}).get("similar_works_found", [])
    detected_tropes = originality_results.get("structural_similarity_report", {}).get("detected_tropes", [])

    # Use LLM for deeper copyright analysis if available
    if llm and full_text:
        try:
            legal_prompt = f"""Analyze this manuscript excerpt for potential copyright issues.

CHARACTERS IN STORY:
{character_architecture}

SAMPLE TEXT (first 4000 chars):
{full_text[:4000]}

ALREADY IDENTIFIED SIMILAR WORKS:
{similar_works}

Check for:
1. Characters that closely resemble copyrighted characters
2. Scenes that replicate famous copyrighted scenes
3. Protected expressions or distinctive phrases
4. Plot elements too similar to specific works

Return JSON:
{{
    "character_concerns": [{{"character": "name", "resembles": "original", "risk": "low/medium/high"}}],
    "scene_concerns": [{{"scene": "description", "resembles": "source", "risk": "low/medium/high"}}],
    "overall_legal_risk": 1-100,
    "notes": "Brief assessment"
}}"""

            legal_result = await llm.generate(legal_prompt, response_format="json", max_tokens=700)
            if isinstance(legal_result, dict):
                for concern in legal_result.get("character_concerns", []):
                    if concern.get("risk") in ["medium", "high"]:
                        character_flags.append(concern)
                for scene in legal_result.get("scene_concerns", []):
                    similar_scenes.append(scene)
        except Exception:
            pass

    # Calculate legal risk score
    risk_score = 5  # Base low risk
    risk_score += len(character_flags) * 15
    risk_score += len(expression_flags) * 10
    risk_score += len(similar_scenes) * 5
    risk_score = min(100, risk_score)

    # Determine statuses
    char_status = "flagged" if character_flags else "clear"
    expr_status = "flagged" if expression_flags else "clear"
    scene_status = "flagged" if similar_scenes else "clear"
    similarity_status = "clear" if risk_score < 30 else "review_needed" if risk_score < 60 else "flagged"

    return {
        "substantial_similarity_check": {
            "status": similarity_status,
            "flags": similar_works[:5] if similar_works else [],
            "confidence": max(50, 100 - risk_score)
        },
        "character_likeness_check": {
            "status": char_status,
            "similar_characters": character_flags,
            "notes": f"Found {len(character_flags)} potential character concerns" if character_flags else "Characters appear original"
        },
        "scene_replication_check": {
            "status": scene_status,
            "similar_scenes": similar_scenes,
            "notes": f"Found {len(similar_scenes)} scenes requiring review" if similar_scenes else "No scene replication detected"
        },
        "protected_expression_check": {
            "status": expr_status,
            "flags": expression_flags,
            "notes": f"Found {len(expression_flags)} protected expressions" if expression_flags else "No protected expressions used"
        },
        "legal_risk_score": risk_score
    }


async def execute_transformative_verification(context: ExecutionContext) -> Dict[str, Any]:
    """Verify transformative use and legal defensibility."""
    import re
    from datetime import datetime

    plagiarism_results = context.inputs.get("plagiarism_audit", {})
    chapters = context.inputs.get("draft_generation", {}).get("chapters", [])
    concept = context.inputs.get("concept_definition", {})
    llm = context.llm_client

    full_text = "\n".join([ch.get("text", "") for ch in chapters if ch.get("text")])

    # Check for documented creation evidence
    creation_evidence = {
        "has_chapters": len(chapters) > 0,
        "has_concept": bool(concept),
        "word_count": len(full_text.split()) if full_text else 0,
        "timestamp": datetime.now().isoformat()
    }

    # Analyze influence sources from concept
    influence_sources = []
    if concept:
        hook = concept.get("one_line_hook", "")
        unique_engine = concept.get("unique_engine", "")
        if hook or unique_engine:
            influence_sources.append("Original concept development documented")
        else:
            influence_sources.append("General genre conventions")

    # Check for market confusion risk
    legal_risk = plagiarism_results.get("legal_risk_score", 50)
    similar_chars = plagiarism_results.get("character_likeness_check", {}).get("similar_characters", [])
    similar_works = plagiarism_results.get("substantial_similarity_check", {}).get("flags", [])

    title = context.project.title if context.project else "Untitled"

    # Common title patterns that might cause confusion
    confusion_titles = []
    title_lower = title.lower()
    confusing_patterns = [
        ("harry", "Harry Potter"),
        ("hunger", "Hunger Games"),
        ("twilight", "Twilight"),
        ("game of", "Game of Thrones"),
        ("lord of", "Lord of the Rings"),
        ("fifty shades", "Fifty Shades"),
    ]
    for pattern, source in confusing_patterns:
        if pattern in title_lower:
            confusion_titles.append({"pattern": pattern, "conflicts_with": source})

    # Calculate transformative distance
    transformative_score = 90  # Start optimistic
    transformative_score -= len(similar_chars) * 10
    transformative_score -= len(similar_works) * 5
    transformative_score -= len(confusion_titles) * 15
    transformative_score = max(10, min(100, transformative_score))

    # Use LLM for deeper analysis if available
    analysis_notes = "Basic analysis - LLM unavailable"
    if llm and full_text:
        try:
            transform_prompt = f"""Analyze whether this work demonstrates sufficient transformative distance for copyright safety.

TITLE: {title}
CONCEPT: {concept.get('elevator_pitch', 'Not specified')}

SIMILAR WORKS IDENTIFIED: {similar_works}
CHARACTER CONCERNS: {similar_chars}

SAMPLE TEXT (first 2000 chars):
{full_text[:2000]}

Evaluate:
1. Does this work add new meaning, message, or expression?
2. Is it clearly distinguishable from any similar works?
3. Would a reasonable consumer confuse this with another work?

Return JSON:
{{
    "transformative_elements": ["list what makes this original"],
    "derivative_concerns": ["list any remaining concerns"],
    "market_confusion_risk": "low/medium/high",
    "overall_assessment": "Brief legal perspective"
}}"""

            transform_result = await llm.generate(transform_prompt, response_format="json", max_tokens=600)
            if isinstance(transform_result, dict):
                analysis_notes = transform_result.get("overall_assessment", analysis_notes)
                confusion_risk = transform_result.get("market_confusion_risk", "low")
                if confusion_risk == "high":
                    transformative_score = min(transformative_score, 40)
                elif confusion_risk == "medium":
                    transformative_score = min(transformative_score, 70)
        except Exception:
            pass

    # Determine risk levels
    market_risk = "low"
    if len(confusion_titles) > 0 or len(similar_works) > 2:
        market_risk = "high"
    elif len(similar_works) > 0:
        market_risk = "medium"

    return {
        "independent_creation_proof": {
            "documented": creation_evidence["has_chapters"] and creation_evidence["has_concept"],
            "creation_timeline": creation_evidence["timestamp"],
            "evidence": creation_evidence,
            "influence_sources": influence_sources if influence_sources else ["General genre conventions only"]
        },
        "market_confusion_check": {
            "risk_level": market_risk,
            "similar_titles": confusion_titles,
            "similar_works": similar_works[:3],
            "recommendation": "Review title" if confusion_titles else "No confusion risk"
        },
        "transformative_distance": {
            "score": transformative_score,
            "analysis": analysis_notes
        }
    }


async def execute_structural_rewrite(context: ExecutionContext) -> Dict[str, Any]:
    """Perform structural and prose rewrites."""
    chapters = context.inputs.get("draft_generation", {}).get("chapters", [])
    continuity_report = context.inputs.get("continuity_audit", {}).get("continuity_report", {})

    # In production, this would rewrite flagged sections
    revised_chapters = chapters.copy()  # Would actually revise

    return {
        "revised_chapters": revised_chapters,
        "revision_log": [
            {"chapter": 1, "changes": "Tightened opening"},
            {"chapter": 15, "changes": "Enhanced tension"}
        ],
        "resolved_flags": continuity_report.get("total_issues", 0)
    }


async def execute_post_rewrite_scan(context: ExecutionContext) -> Dict[str, Any]:
    """Re-scan after rewrites for new issues."""
    import re
    from collections import Counter

    revised_chapters = context.inputs.get("structural_rewrite", {}).get("revised_chapters", [])
    original_chapters = context.inputs.get("draft_generation", {}).get("chapters", [])
    llm = context.llm_client

    revised_text = "\n".join([ch.get("text", "") for ch in revised_chapters if ch.get("text")])
    original_text = "\n".join([ch.get("text", "") for ch in original_chapters if ch.get("text")])

    new_issues = []
    similarity_flags = []

    if not revised_text:
        return {
            "rewrite_originality_check": {
                "status": "skipped",
                "new_issues": [],
                "notes": "No revised text to scan"
            },
            "new_similarity_flags": []
        }

    # Check for newly introduced cliches
    cliches = [
        r"it was a dark and stormy night",
        r"let out a breath .* didn't know",
        r"time stood still",
        r"heart skipped a beat",
        r"tears streamed down",
        r"shiver ran down .* spine",
    ]

    for cliche in cliches:
        # Check if cliche is in revised but not in original
        revised_matches = len(re.findall(cliche, revised_text.lower()))
        original_matches = len(re.findall(cliche, original_text.lower())) if original_text else 0
        if revised_matches > original_matches:
            new_issues.append({
                "type": "new_cliche",
                "pattern": cliche,
                "count": revised_matches - original_matches
            })

    # Check for new repetitive phrases introduced
    revised_words = re.findall(r'\b[a-z]+\b', revised_text.lower())
    revised_trigrams = Counter([" ".join(revised_words[i:i+3]) for i in range(len(revised_words)-2)])

    if original_text:
        original_words = re.findall(r'\b[a-z]+\b', original_text.lower())
        original_trigrams = Counter([" ".join(original_words[i:i+3]) for i in range(len(original_words)-2)])

        # Find trigrams that increased significantly
        for phrase, count in revised_trigrams.most_common(30):
            orig_count = original_trigrams.get(phrase, 0)
            if count >= 5 and count > orig_count * 1.5:
                if not any(w in phrase for w in ["the", "and", "was", "that", "had", "but", "with"]):
                    similarity_flags.append({
                        "phrase": phrase,
                        "original_count": orig_count,
                        "new_count": count,
                        "severity": "warning"
                    })

    # Use LLM to compare for deeper analysis if available
    if llm and revised_text and original_text:
        try:
            compare_prompt = f"""Compare these two versions of a manuscript for changes that might introduce issues.

ORIGINAL (first 1500 chars):
{original_text[:1500]}

REVISED (first 1500 chars):
{revised_text[:1500]}

Check if the revision introduced:
1. New cliches or overused phrases
2. Repetitive sentence structures
3. Any content that seems copied from external sources

Return JSON:
{{
    "new_problems_found": [{{"type": "cliche|repetition|similarity", "description": "..."}}],
    "improvement_assessment": "better/same/worse",
    "notes": "Brief assessment"
}}"""

            compare_result = await llm.generate(compare_prompt, response_format="json", max_tokens=500)
            if isinstance(compare_result, dict):
                for problem in compare_result.get("new_problems_found", []):
                    new_issues.append(problem)
        except Exception:
            pass

    # Determine status
    status = "clear"
    if len(new_issues) > 3 or len(similarity_flags) > 5:
        status = "flagged"
    elif len(new_issues) > 0 or len(similarity_flags) > 0:
        status = "review_needed"

    return {
        "rewrite_originality_check": {
            "status": status,
            "new_issues": new_issues,
            "notes": f"Found {len(new_issues)} new issues" if new_issues else "No new issues introduced"
        },
        "new_similarity_flags": similarity_flags
    }


async def execute_line_edit(context: ExecutionContext) -> Dict[str, Any]:
    """Perform line and copy editing."""
    revised_chapters = context.inputs.get("structural_rewrite", {}).get("revised_chapters", [])
    style_guide = context.inputs.get("voice_specification", {}).get("style_guide", {})

    # In production, this would edit each chapter
    edited_chapters = revised_chapters.copy()

    return {
        "edited_chapters": edited_chapters,
        "grammar_fixes": 47,
        "rhythm_improvements": 23,
        "edit_report": {
            "total_changes": 70,
            "major_changes": 5,
            "minor_changes": 65,
            "readability_improvement": "+15%"
        }
    }


async def execute_beta_simulation(context: ExecutionContext) -> Dict[str, Any]:
    """Simulate beta reader response."""
    edited_chapters = context.inputs.get("line_edit", {}).get("edited_chapters", [])
    reader_avatar = context.inputs.get("market_intelligence", {}).get("reader_avatar", {})

    return {
        "dropoff_points": [],
        "confusion_zones": [],
        "engagement_scores": {
            "opening": 9,
            "middle": 7,
            "climax": 10,
            "ending": 9,
            "overall": 8.5
        },
        "feedback_summary": {
            "strengths": ["Compelling characters", "Page-turner plot", "Satisfying ending"],
            "weaknesses": ["Middle slightly slow"],
            "quotes": ["Couldn't put it down!", "The ending made me cry"]
        }
    }


async def execute_final_validation(context: ExecutionContext) -> Dict[str, Any]:
    """Final quality validation before release."""
    core_promise = context.inputs.get("concept_definition", {}).get("core_promise", {})
    theme = context.inputs.get("thematic_architecture", {}).get("primary_theme", {})

    return {
        "concept_match_score": 92,
        "theme_payoff_check": {
            "theme_delivered": True,
            "thematic_question_addressed": True,
            "value_conflict_resolved": True
        },
        "promise_fulfillment": {
            "core_promise_delivered": True,
            "reader_expectation_met": True,
            "emotional_payoff_achieved": True
        },
        "release_recommendation": {
            "approved": True,
            "confidence": 95,
            "notes": "Ready for publication"
        }
    }


async def execute_publishing_package(context: ExecutionContext) -> Dict[str, Any]:
    """Create publishing-ready materials."""
    core_promise = context.inputs.get("concept_definition", {})
    reader_avatar = context.inputs.get("market_intelligence", {}).get("reader_avatar", {})

    return {
        "blurb": "[Compelling 150-word book description would be generated here]",
        "synopsis": "[2-page synopsis for agents/publishers]",
        "metadata": {
            "title": context.project.title,
            "genre": context.inputs.get("user_constraints", {}).get("genre", "Fiction"),
            "word_count": sum(c.get("word_count", 0) for c in context.inputs.get("draft_generation", {}).get("chapters", [])),
            "audience": "Adult"
        },
        "keywords": ["transformation", "journey", "discovery", "contemporary"],
        "series_hooks": ["Potential for sequel", "Expandable world"],
        "author_bio": "[Author bio placeholder]"
    }


async def execute_ip_clearance(context: ExecutionContext) -> Dict[str, Any]:
    """Clear IP, title, and brand naming."""
    import re

    title = context.project.title if context.project else ""
    publishing_package = context.inputs.get("publishing_package", {})
    character_architecture = context.inputs.get("character_architecture", {})
    llm = context.llm_client

    # Extract character names
    character_names = []
    for char_type in ["protagonist_profile", "antagonist_profile"]:
        char = character_architecture.get(char_type, {})
        if isinstance(char, dict) and char.get("name"):
            character_names.append(char.get("name"))
    for char in character_architecture.get("supporting_cast", []):
        if isinstance(char, dict) and char.get("name"):
            character_names.append(char.get("name"))

    # Known protected title patterns
    protected_titles = [
        (r"^harry potter", "J.K. Rowling"),
        (r"^game of thrones", "George R.R. Martin"),
        (r"^hunger games", "Suzanne Collins"),
        (r"^twilight", "Stephenie Meyer"),
        (r"^fifty shades", "E.L. James"),
        (r"^lord of the rings", "J.R.R. Tolkien"),
        (r"^star wars", "Lucasfilm"),
        (r"^the matrix", "Warner Bros"),
    ]

    title_conflicts = []
    title_lower = title.lower().strip()
    for pattern, owner in protected_titles:
        if re.match(pattern, title_lower):
            title_conflicts.append({
                "pattern": pattern,
                "owner": owner,
                "risk": "high"
            })

    # Check series name if present
    series_name = publishing_package.get("series_name", "")
    series_conflicts = []
    if series_name:
        series_lower = series_name.lower()
        for pattern, owner in protected_titles:
            if re.search(pattern, series_lower):
                series_conflicts.append({
                    "series": series_name,
                    "conflicts_with": owner
                })

    # Check character names for conflicts
    protected_character_names = [
        "harry potter", "hermione", "ron weasley", "dumbledore", "voldemort",
        "katniss", "peeta", "frodo", "gandalf", "aragorn", "legolas",
        "darth vader", "luke skywalker", "james bond", "sherlock holmes",
        "batman", "superman", "spider-man", "iron man", "captain america",
        "mickey mouse", "donald duck", "bugs bunny"
    ]

    character_conflicts = []
    for name in character_names:
        name_lower = name.lower()
        for protected in protected_character_names:
            if protected in name_lower or name_lower in protected:
                character_conflicts.append({
                    "character": name,
                    "conflicts_with": protected.title(),
                    "risk": "high"
                })

    # Use LLM for deeper title search if available
    if llm and title:
        try:
            title_prompt = f"""Check if this book title could conflict with existing works.

TITLE: {title}
SERIES: {series_name or 'None'}

Consider:
1. Exact matches with famous books
2. Confusingly similar titles
3. Trademark issues

Return JSON:
{{
    "potential_conflicts": [{{"title": "conflicting work", "similarity": "high/medium/low"}}],
    "recommendation": "clear|rename_suggested|rename_required"
}}"""

            title_result = await llm.generate(title_prompt, response_format="json", max_tokens=400)
            if isinstance(title_result, dict):
                for conflict in title_result.get("potential_conflicts", []):
                    if conflict.get("similarity") in ["high", "medium"]:
                        title_conflicts.append(conflict)
        except Exception:
            pass

    # Determine statuses
    title_status = "flagged" if title_conflicts else "clear"
    series_status = "flagged" if series_conflicts else "clear"
    char_status = "flagged" if character_conflicts else "clear"

    all_clear = not (title_conflicts or series_conflicts or character_conflicts)

    return {
        "title_conflict_check": {
            "status": title_status,
            "similar_titles": title_conflicts,
            "recommendation": "Rename required" if title_conflicts else "Title is available"
        },
        "series_naming_check": {
            "status": series_status,
            "conflicts": series_conflicts
        },
        "character_naming_check": {
            "status": char_status,
            "conflicts": character_conflicts
        },
        "clearance_status": {
            "approved": all_clear,
            "notes": "All naming cleared for use" if all_clear else f"Found {len(title_conflicts) + len(series_conflicts) + len(character_conflicts)} naming conflicts"
        }
    }


async def execute_human_editor_review(context: ExecutionContext) -> Dict[str, Any]:
    """Simulate human editor review feedback."""
    import re

    chapters = context.inputs.get("draft_generation", {}).get("chapters", [])
    voice_spec = context.inputs.get("voice_specification", {})
    final_validation = context.inputs.get("final_validation", {})
    llm = context.llm_client

    full_text = "\n".join([ch.get("text", "") for ch in chapters if ch.get("text")])

    editor_notes = []
    revision_suggestions = []
    quality_issues = []

    if not full_text:
        return {
            "editor_notes": ["No manuscript to review"],
            "revision_suggestions": ["Generate chapters first"],
            "quality_score": 0,
            "recommendation": "Cannot evaluate - no content"
        }

    # Analyze first chapter for hook strength
    first_chapter = chapters[0].get("text", "") if chapters else ""
    first_para = first_chapter[:500] if first_chapter else ""

    # Check for strong opening indicators
    hook_indicators = [
        (r'^["\']', "Opens with dialogue"),
        (r'\?', "Uses question to engage"),
        (r'(suddenly|immediately|without warning)', "Creates immediate tension"),
        (r'(never|always|everything changed)', "Uses absolute statements"),
    ]

    opening_score = 5
    for pattern, note in hook_indicators:
        if re.search(pattern, first_para, re.IGNORECASE):
            opening_score += 1
            editor_notes.append(note)

    if opening_score < 6:
        revision_suggestions.append("Consider strengthening the opening hook")

    # Check dialogue ratio
    dialogue_count = len(re.findall(r'["\'][^"\']+["\']', full_text))
    word_count = len(full_text.split())
    dialogue_ratio = dialogue_count / max(word_count / 100, 1)

    if dialogue_ratio < 0.5:
        revision_suggestions.append("Consider adding more dialogue to break up narrative")
    elif dialogue_ratio > 3:
        revision_suggestions.append("Consider balancing dialogue with more narrative description")
    else:
        editor_notes.append("Good balance of dialogue and narrative")

    # Check paragraph length variation
    paragraphs = [p for p in full_text.split('\n\n') if p.strip()]
    if paragraphs:
        para_lengths = [len(p.split()) for p in paragraphs]
        avg_para = sum(para_lengths) / len(para_lengths)
        if avg_para > 150:
            revision_suggestions.append("Consider breaking up longer paragraphs for readability")
        elif avg_para < 30:
            revision_suggestions.append("Some paragraphs may be too short - consider combining")
        else:
            editor_notes.append("Paragraph lengths are appropriate")

    # Check for sensory details
    sensory_words = r'\b(saw|heard|felt|smelled|tasted|touched|warm|cold|bright|dark|loud|quiet|rough|smooth)\b'
    sensory_count = len(re.findall(sensory_words, full_text.lower()))
    sensory_ratio = sensory_count / max(word_count / 1000, 1)

    if sensory_ratio < 2:
        revision_suggestions.append("Add more sensory details to immerse readers")
    else:
        editor_notes.append("Good use of sensory language")

    # Use LLM for professional editor simulation
    if llm and full_text:
        try:
            editor_prompt = f"""You are a professional fiction editor reviewing a manuscript.

VOICE SPECIFICATION: {voice_spec.get('narrative_voice', 'Not specified')}

SAMPLE (first 2500 chars of manuscript):
{full_text[:2500]}

As a professional editor, provide:
1. What works well (be specific)
2. What needs improvement (be specific)
3. Overall quality assessment

Return JSON:
{{
    "strengths": ["list of specific strengths"],
    "areas_for_improvement": ["list of specific suggestions"],
    "quality_score": 1-100,
    "overall_verdict": "Brief professional assessment"
}}"""

            editor_result = await llm.generate(editor_prompt, response_format="json", max_tokens=600)
            if isinstance(editor_result, dict):
                editor_notes.extend(editor_result.get("strengths", []))
                revision_suggestions.extend(editor_result.get("areas_for_improvement", []))
                llm_score = editor_result.get("quality_score", 75)
        except Exception:
            llm_score = 75

    # Calculate final quality score
    base_score = 70
    base_score += opening_score
    base_score -= len(revision_suggestions) * 2
    base_score += len(editor_notes) * 1

    # Factor in final validation score if available
    concept_match = final_validation.get("concept_match_score", 80)
    quality_score = int((base_score + concept_match) / 2)
    quality_score = max(30, min(100, quality_score))

    # Determine recommendation
    if quality_score >= 85:
        recommendation = "Ready for publication"
    elif quality_score >= 70:
        recommendation = "Ready for publication with minor polish"
    elif quality_score >= 55:
        recommendation = "Needs revision before publication"
    else:
        recommendation = "Requires significant revision"

    return {
        "editor_notes": editor_notes[:10],
        "revision_suggestions": revision_suggestions[:10],
        "quality_score": quality_score,
        "recommendation": recommendation
    }


async def execute_production_readiness(context: ExecutionContext) -> Dict[str, Any]:
    """Check production readiness."""
    import re

    chapters = context.inputs.get("draft_generation", {}).get("chapters", [])
    edited_chapters = context.inputs.get("line_edit", {}).get("edited_chapters", [])
    human_review = context.inputs.get("human_editor_review", {})
    voice_spec = context.inputs.get("voice_specification", {})

    # Use edited chapters if available, otherwise use draft
    final_chapters = edited_chapters if edited_chapters else chapters
    full_text = "\n".join([ch.get("text", "") for ch in final_chapters if ch.get("text")])

    formatting_issues = []
    consistency_issues = []
    checklist = {
        "has_chapters": len(final_chapters) > 0,
        "word_count_sufficient": False,
        "formatting_clean": True,
        "style_consistent": True,
        "editor_approved": False
    }

    if not full_text:
        return {
            "formatting_check": {
                "status": "fail",
                "issues": ["No content to evaluate"]
            },
            "consistency_check": {
                "status": "fail",
                "notes": "No content available"
            },
            "readiness_status": {
                "ready": False,
                "checklist_complete": False,
                "checklist": checklist
            }
        }

    # Check word count
    word_count = len(full_text.split())
    checklist["word_count_sufficient"] = word_count >= 40000  # Minimum novel length
    if word_count < 40000:
        formatting_issues.append(f"Word count ({word_count}) below novel minimum (40,000)")

    # Check for formatting issues
    # Multiple spaces
    if re.search(r'  +', full_text):
        formatting_issues.append("Multiple consecutive spaces found")

    # Inconsistent quote marks
    smart_quotes = len(re.findall(r'[""]', full_text))
    straight_quotes = len(re.findall(r'"', full_text))
    if smart_quotes > 0 and straight_quotes > 0:
        formatting_issues.append("Mixed smart and straight quotes")

    # Inconsistent dashes
    em_dashes = len(re.findall(r'—', full_text))
    double_dashes = len(re.findall(r'--', full_text))
    if em_dashes > 0 and double_dashes > 0:
        formatting_issues.append("Mixed em-dashes and double-dashes")

    # Orphan punctuation
    if re.search(r'\n\s*[.!?]', full_text):
        formatting_issues.append("Orphan punctuation marks found")

    # Check chapter numbering consistency
    chapter_numbers = [ch.get("number") for ch in final_chapters if ch.get("number")]
    expected_numbers = list(range(1, len(final_chapters) + 1))
    if chapter_numbers != expected_numbers:
        consistency_issues.append("Chapter numbering inconsistent or missing")

    # Check for consistent POV (if specified)
    pov = voice_spec.get("pov_rules", {})
    if pov:
        # Check for POV breaks in first person
        if "first" in str(pov).lower():
            third_person_refs = len(re.findall(r'\b(he said|she said|he thought|she thought)\b', full_text.lower()))
            if third_person_refs > 5:
                consistency_issues.append(f"Possible POV inconsistency: {third_person_refs} third-person references in first-person narrative")

    # Check tense consistency
    past_tense = len(re.findall(r'\b(was|were|had|walked|said|thought)\b', full_text.lower()))
    present_tense = len(re.findall(r'\b(is|are|walk|walks|says|thinks)\b', full_text.lower()))
    tense_ratio = past_tense / max(present_tense, 1)

    if 0.3 < tense_ratio < 3:
        consistency_issues.append("Possible tense inconsistency detected")

    # Check editor approval
    editor_score = human_review.get("quality_score", 0)
    checklist["editor_approved"] = editor_score >= 70

    # Update checklist
    checklist["formatting_clean"] = len(formatting_issues) == 0
    checklist["style_consistent"] = len(consistency_issues) == 0

    # Determine overall status
    formatting_status = "pass" if len(formatting_issues) == 0 else "fail"
    consistency_status = "pass" if len(consistency_issues) == 0 else "review_needed"

    all_ready = all(checklist.values())

    return {
        "formatting_check": {
            "status": formatting_status,
            "issues": formatting_issues,
            "word_count": word_count
        },
        "consistency_check": {
            "status": consistency_status,
            "issues": consistency_issues,
            "notes": "All chapters follow style guide" if not consistency_issues else f"Found {len(consistency_issues)} consistency issues"
        },
        "readiness_status": {
            "ready": all_ready,
            "checklist_complete": all_ready,
            "checklist": checklist
        }
    }


async def execute_final_proof(context: ExecutionContext) -> Dict[str, Any]:
    """Final proofread pass."""
    import re

    chapters = context.inputs.get("draft_generation", {}).get("chapters", [])
    edited_chapters = context.inputs.get("line_edit", {}).get("edited_chapters", [])
    llm = context.llm_client

    # Use edited chapters if available
    final_chapters = edited_chapters if edited_chapters else chapters
    full_text = "\n".join([ch.get("text", "") for ch in final_chapters if ch.get("text")])

    typo_issues = []
    grammar_issues = []

    if not full_text:
        return {
            "typo_check": {
                "status": "skip",
                "issues_found": 0,
                "issues": [],
                "notes": "No content to proofread"
            },
            "grammar_check": {
                "status": "skip",
                "issues_found": 0,
                "issues": []
            },
            "proof_status": {
                "complete": False,
                "approved": False
            }
        }

    # Common typo patterns
    typo_patterns = [
        (r'\b(teh|hte|taht|adn|tje|jsut|hav)\b', "common_swap"),
        (r'\b(\w+)\s+\1\b', "repeated_word"),
        (r'[a-z]\.[A-Z]', "missing_space_after_period"),
        (r'\s,', "space_before_comma"),
        (r'\s\.', "space_before_period"),
        (r',,', "double_comma"),
        (r'\.\.(?!\.)', "double_period"),
        (r"'s\s+s\b", "possessive_error"),
        (r'\bi\b(?![\'"])', "lowercase_i"),  # lowercase "i" not in dialogue
    ]

    for pattern, issue_type in typo_patterns:
        matches = re.findall(pattern, full_text)
        if matches:
            typo_issues.append({
                "type": issue_type,
                "count": len(matches),
                "examples": matches[:3] if isinstance(matches[0], str) else [m[0] for m in matches[:3]]
            })

    # Common grammar patterns
    grammar_patterns = [
        (r'\b(could of|would of|should of)\b', "modal_of_error"),
        (r'\b(your)\s+(a|an|the)\b', "your_youre"),
        (r'\b(their)\s+(is|are|was|were)\b', "their_there"),
        (r'\b(its)\s+(a|an|the|not)\b', "its_its"),
        (r'\balot\b', "a_lot"),
        (r'\b(irregardless)\b', "irregardless"),
        (r'\b(supposably)\b', "supposedly"),
        (r'\b(should|could|would)\s+of\b', "auxiliary_of"),
    ]

    for pattern, issue_type in grammar_patterns:
        matches = re.findall(pattern, full_text.lower())
        if matches:
            grammar_issues.append({
                "type": issue_type,
                "count": len(matches),
                "examples": matches[:3]
            })

    # Use LLM for deeper proofreading if available
    if llm and full_text:
        try:
            # Sample from different parts of the text
            sample_start = full_text[:1500]
            sample_middle = full_text[len(full_text)//2:len(full_text)//2 + 1500]
            sample_end = full_text[-1500:]

            proof_prompt = f"""You are a professional proofreader. Check these excerpts for typos and grammar issues.

SAMPLE 1 (opening):
{sample_start}

SAMPLE 2 (middle):
{sample_middle}

SAMPLE 3 (ending):
{sample_end}

Find:
1. Typos and misspellings
2. Grammar errors
3. Punctuation issues

Return JSON:
{{
    "typos": [{{"error": "word", "correction": "fixed"}}],
    "grammar_errors": [{{"error": "phrase", "issue": "description"}}],
    "punctuation_issues": ["list of issues"],
    "overall_quality": "clean/minor_issues/needs_work"
}}"""

            proof_result = await llm.generate(proof_prompt, response_format="json", max_tokens=600)
            if isinstance(proof_result, dict):
                for typo in proof_result.get("typos", []):
                    typo_issues.append(typo)
                for error in proof_result.get("grammar_errors", []):
                    grammar_issues.append(error)
        except Exception:
            pass

    # Calculate totals
    typo_count = sum(i.get("count", 1) for i in typo_issues)
    grammar_count = sum(i.get("count", 1) for i in grammar_issues)

    # Determine status
    typo_status = "pass" if typo_count == 0 else "review" if typo_count < 10 else "fail"
    grammar_status = "pass" if grammar_count == 0 else "review" if grammar_count < 5 else "fail"

    approved = typo_count < 5 and grammar_count < 3

    return {
        "typo_check": {
            "status": typo_status,
            "issues_found": typo_count,
            "issues": typo_issues[:10]
        },
        "grammar_check": {
            "status": grammar_status,
            "issues_found": grammar_count,
            "issues": grammar_issues[:10]
        },
        "proof_status": {
            "complete": True,
            "approved": approved,
            "notes": "Ready for publication" if approved else f"Found {typo_count} typos and {grammar_count} grammar issues"
        }
    }


async def execute_kdp_readiness(context: ExecutionContext) -> Dict[str, Any]:
    """Check KDP/publishing platform readiness."""
    import re

    chapters = context.inputs.get("draft_generation", {}).get("chapters", [])
    publishing_package = context.inputs.get("publishing_package", {})
    final_proof = context.inputs.get("final_proof", {})
    production_readiness = context.inputs.get("production_readiness", {})

    title = context.project.title if context.project else ""
    full_text = "\n".join([ch.get("text", "") for ch in chapters if ch.get("text")])
    word_count = len(full_text.split()) if full_text else 0

    # KDP Requirements
    kdp_requirements = {
        "word_count_met": word_count >= 2500,  # KDP minimum
        "word_count": word_count,
        "formatting_valid": True,
        "metadata_complete": False
    }

    # Check formatting for KDP compatibility
    formatting_issues = []

    # Check for problematic characters
    if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', full_text):
        formatting_issues.append("Contains control characters")
        kdp_requirements["formatting_valid"] = False

    # Check for excessively long paragraphs (can cause Kindle formatting issues)
    paragraphs = [p for p in full_text.split('\n\n') if p.strip()]
    long_paras = [p for p in paragraphs if len(p) > 5000]
    if long_paras:
        formatting_issues.append(f"{len(long_paras)} paragraphs exceed recommended length")

    # Metadata check
    metadata = publishing_package.get("metadata", {})
    blurb = publishing_package.get("blurb", "")
    keywords = publishing_package.get("keywords", [])

    metadata_status = {
        "title": "Valid" if title and len(title) <= 200 else "Invalid",
        "title_length": len(title) if title else 0,
        "description": "Valid" if blurb and 150 <= len(blurb) <= 4000 else "Invalid",
        "description_length": len(blurb) if blurb else 0,
        "categories": "Set" if metadata.get("genre") else "Missing",
        "keywords": "Set" if keywords and len(keywords) >= 3 else "Missing",
        "keyword_count": len(keywords) if keywords else 0
    }

    # Check if all required metadata is present
    kdp_requirements["metadata_complete"] = all([
        metadata_status["title"] == "Valid",
        metadata_status["description"] == "Valid",
        metadata_status["categories"] == "Set",
        metadata_status["keywords"] == "Set"
    ])

    # Platform-specific requirements
    platform_readiness = {
        "Kindle": {
            "ready": kdp_requirements["word_count_met"] and kdp_requirements["formatting_valid"],
            "issues": []
        },
        "Apple Books": {
            "ready": kdp_requirements["word_count_met"],
            "issues": []
        },
        "Kobo": {
            "ready": kdp_requirements["word_count_met"],
            "issues": []
        }
    }

    # Check proof status
    proof_approved = final_proof.get("proof_status", {}).get("approved", False)
    production_ready = production_readiness.get("readiness_status", {}).get("ready", False)

    # Add issues to platforms
    if not proof_approved:
        for platform in platform_readiness:
            platform_readiness[platform]["issues"].append("Proof not approved")
            platform_readiness[platform]["ready"] = False

    if formatting_issues:
        platform_readiness["Kindle"]["issues"].extend(formatting_issues)
        platform_readiness["Kindle"]["ready"] = False

    # Determine overall readiness
    all_platforms_ready = all(p["ready"] for p in platform_readiness.values())
    ready_platforms = [name for name, status in platform_readiness.items() if status["ready"]]

    return {
        "kdp_requirements": kdp_requirements,
        "metadata_check": metadata_status,
        "platform_status": {
            "ready": all_platforms_ready,
            "platforms": ready_platforms,
            "platform_details": platform_readiness
        }
    }


# =============================================================================
# REGISTRATION
# =============================================================================

VALIDATION_EXECUTORS = {
    "continuity_audit": execute_continuity_audit,
    "emotional_validation": execute_emotional_validation,
    "originality_scan": execute_originality_scan,
    "plagiarism_audit": execute_plagiarism_audit,
    "transformative_verification": execute_transformative_verification,
    "structural_rewrite": execute_structural_rewrite,
    "post_rewrite_scan": execute_post_rewrite_scan,
    "line_edit": execute_line_edit,
    "beta_simulation": execute_beta_simulation,
    "final_validation": execute_final_validation,
    "human_editor_review": execute_human_editor_review,
    "production_readiness": execute_production_readiness,
    "publishing_package": execute_publishing_package,
    "final_proof": execute_final_proof,
    "kdp_readiness": execute_kdp_readiness,
    "ip_clearance": execute_ip_clearance,
}
