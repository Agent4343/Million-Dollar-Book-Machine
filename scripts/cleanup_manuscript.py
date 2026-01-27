#!/usr/bin/env python3
"""
Manuscript Cleanup Script

Fixes consistency issues in generated manuscripts by applying
find/replace rules for character names, locations, and other
canonical facts.

Usage:
    python scripts/cleanup_manuscript.py input.md output.md --config corrections.json

Or with inline corrections:
    python scripts/cleanup_manuscript.py input.md output.md \
        --replace "Vincent Torrino:Vincent Blackwood" \
        --replace "Vincent Moretti:Vincent Blackwood" \
        --replace "Chicago:New York"
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# Common consistency issues patterns to detect
CONSISTENCY_PATTERNS = {
    "name_variations": [
        # Pattern: (regex to find variations, what they should be replaced with)
        (r'\b(Vincent|Vincenzo)\s+(Blackwood|Torrino|Moretti)\b', 'name_main_villain'),
        (r'\b(Marcus|Marc)\s+(Romano|Romani)\b', 'name_protagonist'),
    ],
    "timeline_phrases": [
        # Phrases that indicate timeline references that may be inconsistent
        (r'(\d+)\s+years?\s+ago', 'timeline_reference'),
        (r'(three|four|five|ten|fifteen|twenty)\s+years?\s+ago', 'timeline_reference'),
        (r'when\s+(he|she|I)\s+was\s+(\d+|a child|young)', 'timeline_reference'),
    ],
    "relationship_phrases": [
        (r'(his|her|my)\s+(sister|mother|brother|father)\s+(\w+)', 'relationship_reference'),
    ],
}


def load_corrections(config_path: str) -> Dict[str, str]:
    """Load corrections from a JSON config file.

    The config file can have flat corrections or nested categories like:
    {
        "character_name_corrections": {"old": "new"},
        "location_corrections": {"old": "new"}
    }
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    corrections = {}
    for key, value in config.items():
        # Skip metadata keys
        if key.startswith('_'):
            continue
        # If value is a dict, it's a category of corrections
        if isinstance(value, dict):
            corrections.update(value)
        # If it's a string, it's a direct correction
        elif isinstance(value, str):
            corrections[key] = value

    return corrections


def parse_inline_corrections(corrections: List[str]) -> Dict[str, str]:
    """Parse inline corrections in format 'old:new'."""
    result = {}
    for correction in corrections:
        if ':' in correction:
            old, new = correction.split(':', 1)
            result[old.strip()] = new.strip()
    return result


def apply_corrections(text: str, corrections: Dict[str, str]) -> Tuple[str, List[Dict]]:
    """
    Apply corrections to text and return modified text with change log.

    Args:
        text: The manuscript text to clean up
        corrections: Dict mapping old strings to new strings

    Returns:
        Tuple of (corrected_text, list of changes made)
    """
    changes = []
    result = text

    for old, new in corrections.items():
        if old in result:
            count = result.count(old)
            result = result.replace(old, new)
            changes.append({
                "type": "replacement",
                "old": old,
                "new": new,
                "count": count
            })

    return result, changes


def apply_regex_corrections(text: str, regex_corrections: List[Tuple[str, str]]) -> Tuple[str, List[Dict]]:
    """
    Apply regex-based corrections.

    Args:
        text: The manuscript text
        regex_corrections: List of (pattern, replacement) tuples

    Returns:
        Tuple of (corrected_text, list of changes made)
    """
    changes = []
    result = text

    for pattern, replacement in regex_corrections:
        matches = list(re.finditer(pattern, result, re.IGNORECASE))
        if matches:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
            changes.append({
                "type": "regex_replacement",
                "pattern": pattern,
                "replacement": replacement,
                "count": len(matches),
                "examples": [m.group() for m in matches[:3]]  # First 3 examples
            })

    return result, changes


def detect_inconsistencies(text: str) -> Dict[str, List]:
    """
    Detect potential inconsistencies in the manuscript.

    Returns a dict of detected issues grouped by type.
    """
    issues = {
        "name_variations": [],
        "timeline_references": [],
        "relationship_references": [],
        "location_mentions": [],
    }

    # Find all name variations
    name_pattern = r'\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b'
    names = {}
    for match in re.finditer(name_pattern, text):
        full_name = match.group()
        first_name = match.group(1)
        if first_name not in names:
            names[first_name] = set()
        names[first_name].add(full_name)

    # Report first names with multiple last names
    for first, fulls in names.items():
        if len(fulls) > 1:
            issues["name_variations"].append({
                "first_name": first,
                "variations": list(fulls)
            })

    # Find timeline references
    timeline_pattern = r'(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|twenty-three)\s+years?\s+ago'
    timeline_refs = []
    for match in re.finditer(timeline_pattern, text, re.IGNORECASE):
        context_start = max(0, match.start() - 50)
        context_end = min(len(text), match.end() + 50)
        timeline_refs.append({
            "match": match.group(),
            "context": text[context_start:context_end].replace('\n', ' ')
        })

    if timeline_refs:
        issues["timeline_references"] = timeline_refs

    # Find city mentions
    city_pattern = r'\b(New York|NYC|Manhattan|Brooklyn|Chicago|Los Angeles|LA|Boston|Miami|Philadelphia)\b'
    cities = set()
    for match in re.finditer(city_pattern, text, re.IGNORECASE):
        cities.add(match.group())

    if len(cities) > 1:
        issues["location_mentions"].append({
            "cities_found": list(cities),
            "warning": "Multiple cities mentioned - verify this is intentional"
        })

    return issues


def generate_consistency_report(text: str, output_path: str = None) -> str:
    """Generate a report of potential consistency issues."""
    issues = detect_inconsistencies(text)

    lines = ["# Manuscript Consistency Report", ""]

    # Name variations
    if issues["name_variations"]:
        lines.append("## Character Name Variations")
        lines.append("")
        for item in issues["name_variations"]:
            lines.append(f"- **{item['first_name']}**: {', '.join(item['variations'])}")
        lines.append("")

    # Timeline references
    if issues["timeline_references"]:
        lines.append("## Timeline References")
        lines.append("")
        lines.append("The following time references were found (verify consistency):")
        lines.append("")
        for item in issues["timeline_references"][:20]:  # Limit to first 20
            lines.append(f"- \"{item['match']}\" in context: ...{item['context']}...")
        lines.append("")

    # Location mentions
    if issues["location_mentions"]:
        lines.append("## Location Mentions")
        lines.append("")
        for item in issues["location_mentions"]:
            lines.append(f"- Cities found: {', '.join(item['cities_found'])}")
            lines.append(f"  - {item['warning']}")
        lines.append("")

    report = "\n".join(lines)

    if output_path:
        with open(output_path, 'w') as f:
            f.write(report)

    return report


def remove_duplicate_chapters(text: str) -> Tuple[str, List[Dict]]:
    """
    Detect and remove duplicate chapter content.

    Chapters are considered duplicates if they have the same chapter number
    and similar content (even if slightly different).
    """
    changes = []

    # Find all chapter headings
    chapter_pattern = r'(#+\s*)?Chapter\s+(\d+)[:\s]+'
    chapters = []

    for match in re.finditer(chapter_pattern, text, re.IGNORECASE):
        chapter_num = int(match.group(2))
        start = match.start()
        chapters.append({
            "number": chapter_num,
            "start": start,
            "header": match.group()
        })

    # Find end positions
    for i, ch in enumerate(chapters):
        if i + 1 < len(chapters):
            ch["end"] = chapters[i + 1]["start"]
        else:
            ch["end"] = len(text)
        ch["content"] = text[ch["start"]:ch["end"]]

    # Group by chapter number
    by_number = {}
    for ch in chapters:
        num = ch["number"]
        if num not in by_number:
            by_number[num] = []
        by_number[num].append(ch)

    # Find duplicates
    sections_to_remove = []
    for num, instances in by_number.items():
        if len(instances) > 1:
            # Keep the first instance, mark others for removal
            changes.append({
                "type": "duplicate_chapter",
                "chapter": num,
                "instances_found": len(instances),
                "kept": "first",
                "removed": len(instances) - 1
            })
            for inst in instances[1:]:
                sections_to_remove.append((inst["start"], inst["end"]))

    # Remove duplicates (in reverse order to preserve indices)
    result = text
    for start, end in sorted(sections_to_remove, reverse=True):
        result = result[:start] + result[end:]

    return result, changes


def main():
    parser = argparse.ArgumentParser(
        description="Clean up consistency issues in generated manuscripts"
    )
    parser.add_argument("input", help="Input manuscript file (markdown)")
    parser.add_argument("output", nargs="?", help="Output file (default: modify in place)")
    parser.add_argument("--config", help="JSON config file with corrections")
    parser.add_argument("--replace", action="append", default=[],
                       help="Inline correction in format 'old:new'")
    parser.add_argument("--regex", action="append", default=[],
                       help="Regex correction in format 'pattern:replacement'")
    parser.add_argument("--report", action="store_true",
                       help="Generate consistency report without making changes")
    parser.add_argument("--remove-duplicates", action="store_true",
                       help="Remove duplicate chapters")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be changed without modifying")

    args = parser.parse_args()

    # Read input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    text = input_path.read_text(encoding='utf-8')

    # Report mode
    if args.report:
        report = generate_consistency_report(text)
        print(report)
        return

    # Collect all corrections
    corrections = {}

    if args.config:
        corrections.update(load_corrections(args.config))

    if args.replace:
        corrections.update(parse_inline_corrections(args.replace))

    regex_corrections = []
    if args.regex:
        for r in args.regex:
            if ':' in r:
                pattern, replacement = r.split(':', 1)
                regex_corrections.append((pattern, replacement))

    # Apply corrections
    all_changes = []
    result = text

    # Remove duplicate chapters if requested
    if args.remove_duplicates:
        result, dup_changes = remove_duplicate_chapters(result)
        all_changes.extend(dup_changes)

    # Apply string replacements
    if corrections:
        result, string_changes = apply_corrections(result, corrections)
        all_changes.extend(string_changes)

    # Apply regex replacements
    if regex_corrections:
        result, regex_changes = apply_regex_corrections(result, regex_corrections)
        all_changes.extend(regex_changes)

    # Report changes
    if all_changes:
        print("Changes made:")
        for change in all_changes:
            if change["type"] == "replacement":
                print(f"  - Replaced '{change['old']}' with '{change['new']}' ({change['count']} times)")
            elif change["type"] == "regex_replacement":
                print(f"  - Regex '{change['pattern']}' → '{change['replacement']}' ({change['count']} matches)")
            elif change["type"] == "duplicate_chapter":
                print(f"  - Removed {change['removed']} duplicate(s) of Chapter {change['chapter']}")
    else:
        print("No changes made.")

    # Write output
    if not args.dry_run:
        output_path = args.output or args.input
        Path(output_path).write_text(result, encoding='utf-8')
        print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
