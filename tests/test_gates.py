import unittest

from core.gates import validate_agent_output
from core.orchestrator import Orchestrator
from models.state import AgentStatus


class TestGates(unittest.TestCase):
    def test_voice_spec_requires_example_passage(self):
        bad = {
            "narrative_voice": {"pov_type": "Third person limited", "distance": "Close", "personality": "Wry", "tone": "Tense"},
            "pov_rules": {"perspective_character": "Protagonist", "knowledge_limits": "Limited", "rules": ["No head-hopping"]},
            "tense_rules": {"primary_tense": "Past", "exceptions": []},
            "syntax_patterns": {"avg_sentence_length": "15-20 words", "complexity": "Varied", "rhythm": "Varies"},
            "sensory_density": {"visual": "High", "other_senses": "Medium", "frequency": "1-2 per paragraph"},
            "dialogue_style": {"tag_approach": "Minimal", "subtext_level": "High", "differentiation": "Distinct"},
            "style_guide": {"dos": ["Show"], "donts": ["Tell"], "example_passages": [""]},
        }
        passed, _, _, _ = validate_agent_output(agent_id="voice_specification", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)

    def test_draft_generation_requires_chapters(self):
        bad = {
            "chapters": [],
            "chapter_metadata": [],
            "word_counts": {},
            "scene_tags": {},
            "outline_adherence": {},
            "chapter_scores": {},
            "deviations": [],
            "fix_plan": [],
        }
        passed, _, _, _ = validate_agent_output(agent_id="draft_generation", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)

    def test_draft_generation_low_score_synthesizes_deviations(self):
        """Low adherence score with empty deviations should auto-synthesize deviations and pass."""
        content = {
            "chapters": [{"number": 1, "title": "One", "text": "Hello", "summary": "Hi", "word_count": 1}],
            "chapter_metadata": [{"number": 1, "title": "One", "scenes": 1, "pov": "Protagonist"}],
            "word_counts": {"1": 1},
            "scene_tags": {"Ch1": []},
            "outline_adherence": {"overall_score": 50, "chapter_scores": {"1": 50}, "notes": "x"},
            "chapter_scores": {"1": 50},
            "deviations": [],
            "fix_plan": [],
        }
        passed, msg, _, normalized = validate_agent_output(agent_id="draft_generation", content=content, expected_outputs=list(content.keys()))
        self.assertTrue(passed, msg)
        # Gate should have synthesized deviations and fix_plan from chapter_scores
        self.assertTrue(len(normalized.get("deviations", [])) > 0)
        self.assertTrue(len(normalized.get("fix_plan", [])) > 0)

    def test_human_editor_review_not_approved_requires_required_changes(self):
        bad = {
            "approved": False,
            "confidence": 60,
            "editorial_letter": "Needs work.",
            "required_changes": [],
            "optional_suggestions": [],
        }
        passed, _, _, _ = validate_agent_output(agent_id="human_editor_review", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)

    def test_kdp_readiness_requires_kindle_ready(self):
        bad = {
            "kindle_ready": False,
            "epub_report": {"generated": True, "valid": True, "issues": [], "details": {}},
            "docx_report": {"generated": True, "valid": True, "issues": [], "details": {}},
            "front_matter_report": {"included_pages": ["title_page"], "missing_recommended": []},
            "recommendations": [],
        }
        passed, _, _, _ = validate_agent_output(agent_id="kdp_readiness", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)

    def test_final_proof_cannot_approve_with_critical_issues(self):
        bad = {
            "approved": True,
            "overall_score": 90,
            "critical_issues": 1,
            "major_issues": 0,
            "minor_issues": 0,
            "per_chapter_issues": [{"chapter": 1, "title": "One", "issues": [{"severity": "critical", "location": "p1", "description": "x", "suggested_fix": "y"}]}],
            "consistency_findings": [],
            "recommended_actions": [],
        }
        passed, _, _, _ = validate_agent_output(agent_id="final_proof", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)

    def test_chapter_blueprint_requires_contiguous_numbers(self):
        bad = {
            "chapter_outline": [
                {
                    "number": 1,
                    "title": "One",
                    "act": 1,
                    "chapter_goal": "Do something",
                    "pov": "Protagonist",
                    "opening_hook": "Hook",
                    "closing_hook": "Cliff",
                    "word_target": 1000,
                    "scenes": [
                        {
                            "scene_number": 1,
                            "scene_question": "What happens?",
                            "characters": ["Protagonist"],
                            "location": "Here",
                            "conflict_type": "internal",
                            "outcome": "Shift",
                            "word_target": 1000,
                        }
                    ],
                },
                {
                    "number": 2,
                    "title": "Two",
                    "act": 1,
                    "chapter_goal": "Do something else",
                    "pov": "Protagonist",
                    "opening_hook": "Hook",
                    "closing_hook": "Cliff",
                    "word_target": 1000,
                    "scenes": [
                        {
                            "scene_number": 1,
                            "scene_question": "Then what?",
                            "characters": ["Protagonist"],
                            "location": "There",
                            "conflict_type": "external",
                            "outcome": "Complication",
                            "word_target": 1000,
                        }
                    ],
                },
                {
                    "number": 4,  # gap at 3
                    "title": "Four",
                    "act": 1,
                    "chapter_goal": "Escalate",
                    "pov": "Protagonist",
                    "opening_hook": "Hook",
                    "closing_hook": "Cliff",
                    "word_target": 1000,
                    "scenes": [
                        {
                            "scene_number": 1,
                            "scene_question": "Now what?",
                            "characters": ["Protagonist"],
                            "location": "Somewhere",
                            "conflict_type": "external",
                            "outcome": "Turn",
                            "word_target": 1000,
                        }
                    ],
                },
            ],
            "chapter_goals": {"1": "Do something", "2": "Do something else", "4": "Escalate"},
            "scene_list": [],
            "scene_questions": {},
            "hooks": {"chapter_hooks": [], "scene_hooks": []},
            "pov_assignments": {"1": "Protagonist", "2": "Protagonist", "4": "Protagonist"},
        }
        passed, _, details, _ = validate_agent_output(agent_id="chapter_blueprint", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)
        self.assertTrue("errors" in details or "schema_errors" in details)

    # ------------------------------------------------------------------
    # Shared helper
    # ------------------------------------------------------------------

    @staticmethod
    def _make_blueprint_chapter(num: int) -> dict:
        return {
            "number": num,
            "title": f"Chapter {num}",
            "act": 1,
            "chapter_goal": "Advance the plot here",
            "pov": "Protagonist",
            "opening_hook": "A compelling opening hook",
            "closing_hook": "A cliffhanger ending here",
            "word_target": 1000,
            "scenes": [{"scene_number": 1, "scene_question": "What happens next here?", "characters": ["Protagonist"], "location": "The city", "conflict_type": "external", "outcome": "shift", "word_target": 1000}],
        }

    # ------------------------------------------------------------------
    # chapter_blueprint additional cases
    # ------------------------------------------------------------------

    def test_chapter_blueprint_empty_outline(self):
        bad = {
            "chapter_outline": [],
            "chapter_goals": {},
            "scene_list": [],
            "scene_questions": {},
            "hooks": {"chapter_hooks": [], "scene_hooks": []},
            "pov_assignments": {},
        }
        passed, _, _, _ = validate_agent_output(agent_id="chapter_blueprint", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)

    def test_chapter_blueprint_non_contiguous_chapters(self):
        bad = {
            "chapter_outline": [self._make_blueprint_chapter(1), self._make_blueprint_chapter(3), self._make_blueprint_chapter(4)],
            "chapter_goals": {"1": "goal one", "3": "goal three", "4": "goal four"},
            "scene_list": [],
            "scene_questions": {},
            "hooks": {"chapter_hooks": [], "scene_hooks": []},
            "pov_assignments": {},
        }
        passed, _, details, _ = validate_agent_output(agent_id="chapter_blueprint", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)
        errors = details.get("errors", details.get("schema_errors", []))
        msgs = [e.get("msg", "") for e in errors]
        self.assertTrue(any("non_contiguous" in m for m in msgs))

    def test_chapter_blueprint_duplicate_chapters(self):
        bad = {
            "chapter_outline": [self._make_blueprint_chapter(1), self._make_blueprint_chapter(1), self._make_blueprint_chapter(2)],
            "chapter_goals": {"1": "goal one", "2": "goal two"},
            "scene_list": [],
            "scene_questions": {},
            "hooks": {"chapter_hooks": [], "scene_hooks": []},
            "pov_assignments": {},
        }
        passed, _, details, _ = validate_agent_output(agent_id="chapter_blueprint", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)
        errors = details.get("errors", details.get("schema_errors", []))
        msgs = [e.get("msg", "") for e in errors]
        self.assertTrue(any("duplicate" in m for m in msgs))

    def test_chapter_blueprint_valid_passes(self):
        good = {
            "chapter_outline": [self._make_blueprint_chapter(1), self._make_blueprint_chapter(2), self._make_blueprint_chapter(3)],
            "chapter_goals": {"1": "goal one", "2": "goal two", "3": "goal three"},
            "scene_list": [],
            "scene_questions": {},
            "hooks": {"chapter_hooks": [], "scene_hooks": []},
            "pov_assignments": {"1": "Protagonist", "2": "Protagonist", "3": "Protagonist"},
        }
        passed, _, _, _ = validate_agent_output(agent_id="chapter_blueprint", content=good, expected_outputs=list(good.keys()))
        self.assertTrue(passed)

    # ------------------------------------------------------------------
    # draft_generation additional cases
    # ------------------------------------------------------------------

    def test_draft_generation_placeholder_passes_gate(self):
        """Placeholder output (no-LLM/demo mode) should pass gate validation."""
        placeholder_text = "[Chapter 1: Opening — content would be generated here by the LLM. This is a placeholder for demo/no-LLM mode.]"
        placeholder_wc = len(placeholder_text.split())
        good = {
            "chapters": [{
                "number": 1,
                "title": "Opening",
                "text": placeholder_text,
                "summary": "Chapter 1 summary placeholder",
                "word_count": placeholder_wc,
            }],
            "chapter_metadata": [{"number": 1, "title": "Opening", "scenes": 2, "pov": "Protagonist"}],
            "word_counts": {"1": placeholder_wc},
            "scene_tags": {"Ch1": []},
            "outline_adherence": {"overall_score": 85, "chapter_scores": {"1": 85}, "notes": "placeholder"},
            "chapter_scores": {"1": 85},
            "deviations": [],
            "fix_plan": [],
        }
        passed, msg, _, _ = validate_agent_output(agent_id="draft_generation", content=good, expected_outputs=list(good.keys()))
        self.assertTrue(passed, msg)

    def test_draft_generation_deviations_without_fix_plan_synthesizes(self):
        """Deviations with empty fix_plan should auto-synthesize fix_plan and pass."""
        content = {
            "chapters": [{"number": 1, "title": "One", "text": "Hello world this is text", "summary": "Hi", "word_count": 5}],
            "chapter_metadata": [{"number": 1, "title": "One", "scenes": 1, "pov": "Protagonist"}],
            "word_counts": {"1": 5},
            "scene_tags": {"Ch1": []},
            "outline_adherence": {"overall_score": 90, "chapter_scores": {"1": 90}, "notes": "ok"},
            "chapter_scores": {"1": 90},
            "deviations": [{"chapter": 1, "description": "minor deviation"}],
            "fix_plan": [],
        }
        passed, msg, _, normalized = validate_agent_output(agent_id="draft_generation", content=content, expected_outputs=list(content.keys()))
        self.assertTrue(passed, msg)
        # Gate should have synthesized fix_plan from deviations
        self.assertTrue(len(normalized.get("fix_plan", [])) > 0)

    # ------------------------------------------------------------------
    # production_readiness additional cases
    # ------------------------------------------------------------------

    def test_production_readiness_low_score_no_blockers(self):
        bad = {
            "quality_score": 70,
            "release_blockers": [],
        }
        passed, _, _, _ = validate_agent_output(agent_id="production_readiness", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)

    # ------------------------------------------------------------------
    # final_proof additional cases
    # ------------------------------------------------------------------

    def test_final_proof_approved_with_critical_issues(self):
        bad = {
            "approved": True,
            "overall_score": 95,
            "critical_issues": 3,
            "major_issues": 0,
            "minor_issues": 0,
            "per_chapter_issues": [],
            "consistency_findings": [],
            "recommended_actions": [],
        }
        passed, _, _, _ = validate_agent_output(agent_id="final_proof", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)

    def test_final_proof_not_approved_without_actions(self):
        bad = {
            "approved": False,
            "overall_score": 60,
            "critical_issues": 0,
            "major_issues": 2,
            "minor_issues": 5,
            "per_chapter_issues": [],
            "consistency_findings": [],
            "recommended_actions": [],
        }
        passed, _, _, _ = validate_agent_output(agent_id="final_proof", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)

    # ------------------------------------------------------------------
    # validate_non_dict_output
    # ------------------------------------------------------------------

    def test_validate_non_dict_output(self):
        passed, _, details, _ = validate_agent_output(agent_id="orchestrator", content="not a dict", expected_outputs=None)  # type: ignore[arg-type]
        self.assertFalse(passed)
        errors = details.get("errors", [])
        msgs = [e.get("msg", "") for e in errors]
        self.assertTrue(any("not_a_dict" in m for m in msgs))

    def test_gather_inputs_includes_agent_id_inputs(self):
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Test", {"genre": "Fiction"})

        # Mark chapter_blueprint as passed with a minimal valid structure
        cb_state = orch._find_agent_state(project, "chapter_blueprint")  # type: ignore[attr-defined]
        self.assertIsNotNone(cb_state)
        cb_state.status = AgentStatus.PASSED
        cb_state.current_output = type("O", (), {"content": {"chapter_outline": []}})()  # minimal stub

        inputs = orch.gather_inputs(project, "draft_generation")
        # draft_generation declares "chapter_blueprint" as an input; ensure it gets the upstream output by agent id.
        self.assertIn("chapter_blueprint", inputs)


if __name__ == "__main__":
    unittest.main()

