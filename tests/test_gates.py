import unittest

from core.gates import validate_agent_output


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


if __name__ == "__main__":
    unittest.main()

