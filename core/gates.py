"""
Agent gate validation (production-oriented).

The orchestrator uses these checks to decide whether an agent "passed".
This is intentionally stricter than "keys exist":
- Valid JSON shape via Pydantic schemas (when available)
- Basic semantic sanity checks (non-empty lists, sequential chapter numbers, etc.)
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ValidationError

from core.schemas import AGENT_OUTPUT_MODELS


def _pydantic_errors(e: ValidationError) -> List[Dict[str, Any]]:
    errs: List[Dict[str, Any]] = []
    for item in e.errors():
        errs.append(
            {
                "loc": list(item.get("loc", [])),
                "msg": item.get("msg"),
                "type": item.get("type"),
            }
        )
    return errs


def validate_agent_output(
    *,
    agent_id: str,
    content: Dict[str, Any],
    expected_outputs: Optional[List[str]] = None,
) -> Tuple[bool, str, Dict[str, Any], Dict[str, Any]]:
    """
    Validate agent output.

    Returns:
        (passed, message, details, normalized_content)
    """
    details: Dict[str, Any] = {}
    errors: List[Dict[str, Any]] = []

    if not isinstance(content, dict):
        return False, "Agent output must be a JSON object (dict).", {"errors": [{"msg": "not_a_dict"}]}, {}

    # 1) Required output keys (backwards-compatible with existing system)
    missing: List[str] = []
    if expected_outputs:
        for k in expected_outputs:
            if k not in content:
                missing.append(k)
    if missing:
        return (
            False,
            f"Missing required outputs: {missing}",
            {"missing": missing},
            content,
        )

    # 2) Schema validation (when we have a model)
    model = AGENT_OUTPUT_MODELS.get(agent_id)
    normalized_content = content
    if model:
        try:
            parsed: BaseModel = model.model_validate(content)
            normalized_content = parsed.model_dump(mode="python")
            details["schema"] = "pydantic"
        except ValidationError as e:
            errors.extend(_pydantic_errors(e))
            return (
                False,
                "Output failed schema validation.",
                {"schema_errors": errors, "schema": model.__name__},
                content,
            )

    # 3) Agent-specific sanity checks
    # These are lightweight but catch common "production" failures.
    if agent_id == "chapter_blueprint":
        outline = normalized_content.get("chapter_outline") or []
        chapter_nums = [c.get("number") for c in outline if isinstance(c, dict)]
        if not chapter_nums:
            return False, "Chapter outline is empty.", {"errors": [{"msg": "empty_chapter_outline"}]}, normalized_content

        # Ensure unique, sequential-ish numbering (allowing small gaps is a common error; we disallow).
        if len(set(chapter_nums)) != len(chapter_nums):
            return (
                False,
                "Duplicate chapter numbers found.",
                {"errors": [{"msg": "duplicate_chapter_numbers", "numbers": chapter_nums}]},
                normalized_content,
            )

        sorted_nums = sorted(chapter_nums)
        expected = list(range(sorted_nums[0], sorted_nums[0] + len(sorted_nums)))
        if sorted_nums != expected:
            return (
                False,
                "Chapter numbers must be contiguous and increasing (e.g., 1..N).",
                {"errors": [{"msg": "non_contiguous_chapter_numbers", "found": sorted_nums, "expected": expected}]},
                normalized_content,
            )

        # Scenes word targets should sum roughly to chapter word target (±35%)
        bad_chapters: List[Dict[str, Any]] = []
        for ch in outline:
            if not isinstance(ch, dict):
                continue
            wt = int(ch.get("word_target") or 0)
            scenes = ch.get("scenes") or []
            ssum = 0
            for s in scenes:
                if isinstance(s, dict):
                    ssum += int(s.get("word_target") or 0)
            if wt and ssum:
                if ssum < int(wt * 0.65) or ssum > int(wt * 1.35):
                    bad_chapters.append({"chapter": ch.get("number"), "chapter_word_target": wt, "scenes_sum": ssum})
        if bad_chapters:
            return (
                False,
                "Some chapters have scene word targets that don't match the chapter target.",
                {"errors": [{"msg": "scene_word_targets_mismatch", "chapters": bad_chapters}]},
                normalized_content,
            )

    if agent_id == "voice_specification":
        sg = (normalized_content.get("style_guide") or {}) if isinstance(normalized_content, dict) else {}
        examples = sg.get("example_passages") if isinstance(sg, dict) else None
        if not examples or not isinstance(examples, list) or not any(isinstance(x, str) and x.strip() for x in examples):
            return (
                False,
                "Voice specification must include at least one non-empty example passage.",
                {"errors": [{"msg": "missing_example_passages"}]},
                normalized_content,
            )

    # If we got here, it's structurally valid.
    return True, "Gate passed.", details, normalized_content

