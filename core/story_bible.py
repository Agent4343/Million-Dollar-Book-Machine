"""
Story Bible Module for Book Generation Pipeline

Manages canonical story data, character details, timeline events,
and validation to ensure consistency across all generated content.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result from validating content against Story Bible."""
    passed: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    checked_rules: int = 0

    def add_error(self, error_type: str, message: str, details: Dict = None):
        """Add an error to the validation result."""
        self.errors.append({
            "type": error_type,
            "message": message,
            "details": details or {},
            "severity": "error"
        })
        self.passed = False

    def add_warning(self, warning_type: str, message: str, details: Dict = None):
        """Add a warning to the validation result."""
        self.warnings.append({
            "type": warning_type,
            "message": message,
            "details": details or {},
            "severity": "warning"
        })


@dataclass
class Character:
    """Canonical character definition."""
    name: str
    full_name: str = ""
    age: Optional[int] = None
    profession: str = ""
    description: str = ""
    traits: List[str] = field(default_factory=list)
    backstory: str = ""
    relationships: Dict[str, str] = field(default_factory=dict)
    locked_facts: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "full_name": self.full_name,
            "age": self.age,
            "profession": self.profession,
            "description": self.description,
            "traits": self.traits,
            "backstory": self.backstory,
            "relationships": self.relationships,
            "locked_facts": self.locked_facts,
            "aliases": self.aliases
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Character":
        return cls(**data)


@dataclass
class TimelineEvent:
    """A canonical event in the story timeline."""
    chapter: int
    event_id: str
    description: str
    characters_involved: List[str] = field(default_factory=list)
    location: str = ""
    locked: bool = True

    def to_dict(self) -> Dict:
        return {
            "chapter": self.chapter,
            "event_id": self.event_id,
            "description": self.description,
            "characters_involved": self.characters_involved,
            "location": self.location,
            "locked": self.locked
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TimelineEvent":
        return cls(**data)


class StoryBible:
    """
    Central repository for all canonical story information.

    The Story Bible maintains:
    - Character definitions and relationships
    - Timeline of events
    - World/setting rules
    - Style guidelines
    - Locked facts that cannot be contradicted
    """

    def __init__(self):
        """Initialize an empty Story Bible."""
        self.meta: Dict[str, Any] = {
            "title": "",
            "genre": "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": "1.0",
            "chapter_count": 20
        }

        # Core data stores
        self.characters: Dict[str, Character] = {}
        self.relationships: Dict[str, Dict[str, str]] = {}
        self.timeline: Dict[str, TimelineEvent] = {}
        self.settings: Dict[str, Dict[str, Any]] = {}
        self.style_guide: Dict[str, Any] = {}

        # Validation rules
        self.locked_facts: List[str] = []
        self.forbidden_elements: List[str] = []

        # Generation log
        self.generation_log: List[Dict[str, Any]] = []

        # Raw story bible text (user-provided)
        self.raw_text: str = ""

    # =========================================================================
    # LOADING AND SAVING
    # =========================================================================

    def save(self, filepath: str):
        """Save Story Bible to JSON file."""
        data = {
            "meta": self.meta,
            "characters": {k: v.to_dict() for k, v in self.characters.items()},
            "relationships": self.relationships,
            "timeline": {k: v.to_dict() for k, v in self.timeline.items()},
            "settings": self.settings,
            "style_guide": self.style_guide,
            "locked_facts": self.locked_facts,
            "forbidden_elements": self.forbidden_elements,
            "generation_log": self.generation_log,
            "raw_text": self.raw_text
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Story Bible saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "StoryBible":
        """Load Story Bible from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        bible = cls()
        bible.meta = data.get("meta", bible.meta)
        bible.characters = {
            k: Character.from_dict(v)
            for k, v in data.get("characters", {}).items()
        }
        bible.relationships = data.get("relationships", {})
        bible.timeline = {
            k: TimelineEvent.from_dict(v)
            for k, v in data.get("timeline", {}).items()
        }
        bible.settings = data.get("settings", {})
        bible.style_guide = data.get("style_guide", {})
        bible.locked_facts = data.get("locked_facts", [])
        bible.forbidden_elements = data.get("forbidden_elements", [])
        bible.generation_log = data.get("generation_log", [])
        bible.raw_text = data.get("raw_text", "")

        logger.info(f"Story Bible loaded from {filepath}")
        return bible

    # =========================================================================
    # INITIALIZATION FROM RAW TEXT
    # =========================================================================

    def load_from_text(self, story_bible_text: str):
        """
        Initialize Story Bible from raw text document.

        This parses the user-provided Story Bible text and extracts
        structured data where possible.
        """
        self.raw_text = story_bible_text
        self.meta["updated_at"] = datetime.now().isoformat()

        # Extract title if present
        title_match = re.search(r"STORY BIBLE\s*\n\s*(.+?)\s*\n", story_bible_text)
        if title_match:
            self.meta["title"] = title_match.group(1).strip()

        # Extract character names mentioned
        self._extract_characters_from_text(story_bible_text)

        # Store the full text as a locked fact reference
        self.locked_facts.append("Full Story Bible document defines canonical facts")

        logger.info(f"Story Bible initialized from text ({len(story_bible_text)} chars)")

    def _extract_characters_from_text(self, text: str):
        """Extract character names from Story Bible text."""
        # Look for LOCKED patterns like "🔒 LOCKED: NAME"
        locked_chars = re.findall(r"🔒 LOCKED:\s*([A-Z][A-Z\s]+)\s*—", text)
        for char_name in locked_chars:
            clean_name = char_name.strip().title()
            if clean_name and clean_name not in self.characters:
                self.characters[clean_name.lower().replace(" ", "_")] = Character(
                    name=clean_name,
                    locked_facts=["Character defined in Story Bible"]
                )

        # Look for "Full Name" entries
        full_names = re.findall(r"Full Name\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", text)
        for name in full_names:
            key = name.lower().replace(" ", "_")
            if key not in self.characters:
                self.characters[key] = Character(name=name)
            else:
                self.characters[key].full_name = name

    # =========================================================================
    # LAYER INTEGRATION
    # =========================================================================

    def update_from_layer(self, layer_number: int, output: Dict[str, Any]):
        """
        Update Story Bible with output from a definition layer.

        Args:
            layer_number: The layer that produced this output
            output: The agent output dictionary
        """
        self.meta["updated_at"] = datetime.now().isoformat()

        if layer_number == 6:  # Character Architecture
            self._update_from_character_layer(output)
        elif layer_number == 7:  # Relationship Dynamics
            self._update_from_relationship_layer(output)
        elif layer_number == 8:  # Plot Structure
            self._update_from_plot_layer(output)
        elif layer_number == 10:  # Chapter Blueprint
            self._update_from_blueprint_layer(output)
        elif layer_number == 11:  # Voice Specification
            self._update_from_voice_layer(output)

        logger.info(f"Story Bible updated from layer {layer_number}")

    def _update_from_character_layer(self, output: Dict):
        """Update characters from character architecture output."""
        if "protagonist_profile" in output:
            prot = output["protagonist_profile"]
            self.characters["protagonist"] = Character(
                name=prot.get("name", "Protagonist"),
                traits=prot.get("traits", []),
                backstory=prot.get("backstory_wound", "")
            )

        if "supporting_cast" in output:
            for char in output["supporting_cast"]:
                key = char.get("name", "unknown").lower().replace(" ", "_")
                self.characters[key] = Character(
                    name=char.get("name", "Unknown"),
                    description=char.get("function", "")
                )

    def _update_from_relationship_layer(self, output: Dict):
        """Update relationships from relationship dynamics output."""
        if "relationship_map" in output:
            self.relationships = output["relationship_map"]

    def _update_from_plot_layer(self, output: Dict):
        """Update timeline from plot structure output."""
        if "plot_points" in output:
            for i, point in enumerate(output["plot_points"]):
                event_id = f"plot_point_{i}"
                self.timeline[event_id] = TimelineEvent(
                    chapter=point.get("chapter", 0),
                    event_id=event_id,
                    description=point.get("description", "")
                )

    def _update_from_blueprint_layer(self, output: Dict):
        """Update chapter blueprints from chapter blueprint output."""
        if "chapter_outline" in output:
            self.meta["chapter_count"] = len(output["chapter_outline"])
            for chapter in output["chapter_outline"]:
                ch_num = chapter.get("number", 0)
                key = f"chapter_{ch_num}"
                self.timeline[key] = TimelineEvent(
                    chapter=ch_num,
                    event_id=key,
                    description=chapter.get("chapter_goal", ""),
                    location=chapter.get("scenes", [{}])[0].get("location", "") if chapter.get("scenes") else ""
                )

    def _update_from_voice_layer(self, output: Dict):
        """Update style guide from voice specification output."""
        self.style_guide = {
            "pov": output.get("narrative_voice", {}).get("pov_type", "third_limited"),
            "tense": output.get("tense_rules", {}).get("primary_tense", "past"),
            "tone": output.get("narrative_voice", {}).get("tone", ""),
            "chapter_word_count": 3500
        }

    # =========================================================================
    # CONTEXT BUILDING
    # =========================================================================

    def get_context_for_layer(self, layer_number: int) -> Dict[str, Any]:
        """
        Get relevant Story Bible context for a specific layer.

        Args:
            layer_number: The layer requesting context

        Returns:
            Dictionary with relevant context data
        """
        context = {
            "meta": self.meta,
            "style_guide": self.style_guide
        }

        # All layers get character info
        context["characters"] = {k: v.to_dict() for k, v in self.characters.items()}

        # Generation and validation layers get full context
        if layer_number >= 12:
            context["relationships"] = self.relationships
            context["timeline"] = {k: v.to_dict() for k, v in self.timeline.items()}
            context["settings"] = self.settings
            context["locked_facts"] = self.locked_facts

        return context

    def build_chapter_injection(self, chapter_number: int) -> str:
        """
        Build the Story Bible injection text for chapter generation.

        This is the text that gets prepended to every chapter generation
        prompt to ensure consistency.
        """
        # If we have raw text, use it directly (it's the user's Story Bible)
        if self.raw_text:
            return f"""## STORY BIBLE - CANONICAL REFERENCE (LOCKED FACTS)
⚠️ CRITICAL: All facts below are LOCKED. Never contradict this document.

{self.raw_text}

--- END STORY BIBLE ---

GENERATING: Chapter {chapter_number}
"""

        # Otherwise build from structured data
        lines = [
            "## STORY BIBLE - CANONICAL REFERENCE",
            f"Title: {self.meta.get('title', 'Untitled')}",
            f"Genre: {self.meta.get('genre', 'Fiction')}",
            "",
            "### CHARACTERS"
        ]

        for key, char in self.characters.items():
            lines.append(f"- **{char.name}**: {char.description or char.profession}")
            if char.locked_facts:
                for fact in char.locked_facts[:3]:
                    lines.append(f"  - LOCKED: {fact}")

        lines.extend(["", "### STYLE GUIDE"])
        lines.append(f"- POV: {self.style_guide.get('pov', 'third limited')}")
        lines.append(f"- Tense: {self.style_guide.get('tense', 'past')}")

        if self.locked_facts:
            lines.extend(["", "### LOCKED FACTS"])
            for fact in self.locked_facts[:10]:
                lines.append(f"- {fact}")

        lines.extend(["", f"GENERATING: Chapter {chapter_number}", ""])

        return "\n".join(lines)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate_chapter(self, chapter_text: str, chapter_number: int) -> ValidationResult:
        """
        Validate generated chapter text against Story Bible rules.

        Args:
            chapter_text: The generated chapter text
            chapter_number: Which chapter this is

        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(passed=True)

        # Check character name consistency
        self._validate_character_names(chapter_text, result)

        # Check for forbidden elements
        self._validate_forbidden_elements(chapter_text, result)

        # Check timeline consistency
        self._validate_timeline(chapter_text, chapter_number, result)

        result.checked_rules = 3
        return result

    def _validate_character_names(self, text: str, result: ValidationResult):
        """Validate character names are used correctly."""
        for key, char in self.characters.items():
            # Check if character is mentioned with wrong name variations
            if char.full_name:
                # This is a simple check - could be enhanced with NLP
                wrong_names = [
                    char.full_name.replace(char.name, "").strip(),  # Last name only when full should be used
                ]
                for wrong in wrong_names:
                    if wrong and len(wrong) > 2 and wrong in text:
                        result.add_warning(
                            "character_name",
                            f"Character '{char.name}' may be referred to inconsistently",
                            {"character": char.name}
                        )

    def _validate_forbidden_elements(self, text: str, result: ValidationResult):
        """Check for forbidden elements in text."""
        text_lower = text.lower()
        for forbidden in self.forbidden_elements:
            if forbidden.lower() in text_lower:
                result.add_error(
                    "forbidden_element",
                    f"Text contains forbidden element: '{forbidden}'",
                    {"element": forbidden}
                )

    def _validate_timeline(self, text: str, chapter_number: int, result: ValidationResult):
        """Validate timeline consistency."""
        # Check if chapter references future events
        for key, event in self.timeline.items():
            if event.chapter > chapter_number:
                # Check if this future event is mentioned
                if event.description and len(event.description) > 10:
                    # Simple substring check - could use NLP for better matching
                    keywords = event.description.split()[:5]
                    matches = sum(1 for kw in keywords if kw.lower() in text.lower())
                    if matches >= 3:
                        result.add_warning(
                            "timeline_spoiler",
                            f"Chapter may reference future event from chapter {event.chapter}",
                            {"event": event.description[:50]}
                        )

    # =========================================================================
    # GENERATION LOGGING
    # =========================================================================

    def log_chapter_generation(self, chapter_number: int,
                                facts_established: List[str],
                                validation: ValidationResult):
        """Log chapter generation for tracking."""
        self.generation_log.append({
            "chapter": chapter_number,
            "generated_at": datetime.now().isoformat(),
            "facts_established": facts_established,
            "validation_passed": validation.passed,
            "error_count": len(validation.errors),
            "warning_count": len(validation.warnings)
        })


def load_or_create(filepath: str) -> StoryBible:
    """Load existing Story Bible or create new one."""
    path = Path(filepath)
    if path.exists():
        try:
            return StoryBible.load(filepath)
        except Exception as e:
            logger.warning(f"Failed to load Story Bible, creating new: {e}")

    bible = StoryBible()
    return bible
