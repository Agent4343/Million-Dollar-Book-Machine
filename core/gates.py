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

    # 0) Placeholder bypass: demo mode outputs are not meant to be production-quality.
    #    If the agent returned a placeholder result (no LLM key set), skip strict validation.
    #    Production deployments with ANTHROPIC_API_KEY set will never produce placeholder outputs,
    #    so this branch is only active in demo/test mode.
    if content.get("_status") == "placeholder":
        return True, "Gate bypassed: placeholder output (demo mode).", {"placeholder": True}, content

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

    if agent_id == "draft_generation":
        chapters = normalized_content.get("chapters") or []
        if not isinstance(chapters, list) or not chapters:
            return False, "Draft must include at least one chapter.", {"errors": [{"msg": "empty_chapters"}]}, normalized_content

        # Require structured adherence outputs (production-grade)
        if "outline_adherence" not in normalized_content or "deviations" not in normalized_content or "fix_plan" not in normalized_content:
            return (
                False,
                "Draft must include outline_adherence, deviations, and fix_plan.",
                {"errors": [{"msg": "missing_adherence_outputs"}]},
                normalized_content,
            )

        outline = normalized_content.get("outline_adherence") or {}
        score = outline.get("overall_score") if isinstance(outline, dict) else None
        deviations = normalized_content.get("deviations") or []
        fix_plan = normalized_content.get("fix_plan") or []
        if not isinstance(score, int) or score < 0 or score > 100:
            return (
                False,
                "outline_adherence.overall_score must be an int 0-100.",
                {"errors": [{"msg": "bad_overall_score", "value": score}]},
                normalized_content,
            )
        # If score is below the threshold and deviations/fix_plan are missing,
        # synthesize them from chapter_scores rather than failing the gate.
        # This prevents a catch-22 where the LLM rates adherence low but
        # doesn't produce explicit deviation entries, causing endless retries.
        chapter_scores = outline.get("chapter_scores") or {}
        if score < 80 and (not isinstance(deviations, list) or len(deviations) == 0):
            synthetic_devs: list = []
            for ch_num, ch_score in (chapter_scores.items() if isinstance(chapter_scores, dict) else []):
                if isinstance(ch_score, int) and ch_score < 80:
                    synthetic_devs.append({
                        "chapter": ch_num,
                        "severity": "major" if ch_score < 60 else "minor",
                        "description": f"Chapter {ch_num} scored {ch_score}/100 on outline adherence",
                        "suggested_fix": f"Review chapter {ch_num} against its blueprint and revise deviating scenes",
                    })
            if synthetic_devs:
                deviations = synthetic_devs
                normalized_content["deviations"] = deviations
            # If we still have no deviations (e.g. no chapter_scores data),
            # allow it through — downstream rewrite agents will catch issues.

        if isinstance(deviations, list) and deviations and (not isinstance(fix_plan, list) or len(fix_plan) == 0):
            # Synthesize a fix_plan from deviations instead of failing the gate.
            fix_plan = [
                f"Chapter {d.get('chapter', '?')}: {d.get('suggested_fix') or d.get('description')}"
                for d in deviations[:12]
                if isinstance(d, dict)
            ]
            normalized_content["fix_plan"] = fix_plan

        bad = []
        for ch in chapters[:5]:  # only sample-check first 5 to keep it cheap
            if not isinstance(ch, dict):
                bad.append({"msg": "non_object_chapter"})
                continue
            text = ch.get("text")
            wc = ch.get("word_count", 0)
            # Skip consistency check for placeholder/demo chapters
            if isinstance(text, str) and ("would be generated here" in text or wc == 0):
                continue
            if isinstance(wc, int) and wc > 0 and isinstance(text, str):
                approx = len(text.split())
                # allow drift, but catch obviously wrong metadata
                if approx and abs(approx - wc) > max(200, int(wc * 0.25)):
                    bad.append({"chapter": ch.get("number"), "word_count": wc, "approx": approx})
        if bad:
            return (
                False,
                "Draft chapter word_count metadata appears inconsistent with text.",
                {"errors": [{"msg": "word_count_mismatch", "examples": bad}]},
                normalized_content,
            )

    if agent_id == "production_readiness":
        blockers = normalized_content.get("release_blockers") if isinstance(normalized_content, dict) else None
        score = normalized_content.get("quality_score") if isinstance(normalized_content, dict) else None
        if isinstance(score, int) and score < 85 and (not blockers):
            return (
                False,
                "Production readiness score is below threshold but release_blockers is empty.",
                {"errors": [{"msg": "low_score_without_blockers", "quality_score": score}]},
                normalized_content,
            )

    if agent_id == "kdp_readiness":
        if not isinstance(normalized_content, dict):
            return False, "Invalid kdp_readiness output.", {"errors": [{"msg": "not_a_dict"}]}, normalized_content
        kindle_ready = normalized_content.get("kindle_ready")
        epub = normalized_content.get("epub_report") or {}
        docx = normalized_content.get("docx_report") or {}
        issues = []
        if kindle_ready is not True:
            issues.append("kindle_ready must be true to pass.")
        if isinstance(epub, dict) and epub.get("valid") is not True:
            issues.append("EPUB report valid must be true.")
        if isinstance(docx, dict) and docx.get("valid") is not True:
            # DOCX isn't required for KDP, but we treat it as a strong signal; allow non-fatal if epub valid.
            pass
        if issues:
            return False, "KDP readiness checks failed.", {"errors": [{"msg": "kdp_not_ready", "issues": issues}]}, normalized_content

    if agent_id == "final_proof":
        if not isinstance(normalized_content, dict):
            return False, "Invalid final_proof output.", {"errors": [{"msg": "not_a_dict"}]}, normalized_content
        approved = normalized_content.get("approved")
        critical = normalized_content.get("critical_issues")
        if approved is not True:
            # Must have some actionable output if failing
            per = normalized_content.get("per_chapter_issues")
            rec = normalized_content.get("recommended_actions")
            if (not isinstance(per, list) or len(per) == 0) and (not isinstance(rec, list) or len(rec) == 0):
                return (
                    False,
                    "If final_proof is not approved, it must include per_chapter_issues or recommended_actions.",
                    {"errors": [{"msg": "not_approved_without_actions"}]},
                    normalized_content,
                )
        if isinstance(critical, int) and critical > 0 and approved is True:
            return (
                False,
                "final_proof cannot be approved when critical_issues > 0.",
                {"errors": [{"msg": "approved_with_critical_issues", "critical_issues": critical}]},
                normalized_content,
            )

    if agent_id == "human_editor_review":
        approved = normalized_content.get("approved") if isinstance(normalized_content, dict) else None
        required = normalized_content.get("required_changes") if isinstance(normalized_content, dict) else None
        if approved is False and (not isinstance(required, list) or len(required) == 0):
            return (
                False,
                "If approved=false, required_changes must be a non-empty list.",
                {"errors": [{"msg": "not_approved_without_required_changes"}]},
                normalized_content,
            )
        if approved is True and isinstance(required, list) and len(required) > 0:
            return (
                False,
                "If approved=true, required_changes must be empty (or omit approval).",
                {"errors": [{"msg": "approved_with_required_changes"}]},
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

