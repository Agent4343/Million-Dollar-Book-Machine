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

    def test_draft_generation_low_score_requires_deviations(self):
        bad = {
            "chapters": [{"number": 1, "title": "One", "text": "Hello", "summary": "Hi", "word_count": 1}],
            "chapter_metadata": [{"number": 1, "title": "One", "scenes": 1, "pov": "Protagonist"}],
            "word_counts": {"1": 1},
            "scene_tags": {"Ch1": []},
            "outline_adherence": {"overall_score": 50, "chapter_scores": {"1": 50}, "notes": "x"},
            "chapter_scores": {"1": 50},
            "deviations": [],
            "fix_plan": [],
        }
        passed, _, details, _ = validate_agent_output(agent_id="draft_generation", content=bad, expected_outputs=list(bad.keys()))
        self.assertFalse(passed)
        self.assertTrue("errors" in details)

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

