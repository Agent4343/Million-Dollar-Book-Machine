import asyncio
import unittest

from core.orchestrator import Orchestrator
from models.state import AgentOutput, AgentStatus, LayerStatus


class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orch = Orchestrator(llm_client=None)

    # ------------------------------------------------------------------
    # test_create_project_initializes_all_layers
    # ------------------------------------------------------------------
    def test_create_project_initializes_all_layers(self):
        project = self.orch.create_project("My Book", {"genre": "fantasy"})
        # All 21 layers (0-20) must be present
        for layer_id in range(21):
            self.assertIn(layer_id, project.layers)
        # Layer 0 is AVAILABLE; all others are LOCKED
        self.assertEqual(project.layers[0].status, LayerStatus.AVAILABLE)
        for layer_id in range(1, 21):
            self.assertEqual(project.layers[layer_id].status, LayerStatus.LOCKED)

    # ------------------------------------------------------------------
    # test_get_available_agents_returns_orchestrator_first
    # ------------------------------------------------------------------
    def test_get_available_agents_returns_orchestrator_first(self):
        project = self.orch.create_project("My Book", {})
        available = self.orch.get_available_agents(project)
        self.assertIn("orchestrator", available)

    # ------------------------------------------------------------------
    # test_project_status_structure
    # ------------------------------------------------------------------
    def test_project_status_structure(self):
        project = self.orch.create_project("Status Test", {})
        status = self.orch.get_project_status(project)
        for key in ("project_id", "title", "status", "current_layer", "current_agent", "layers", "available_agents", "updated_at"):
            self.assertIn(key, status)

    # ------------------------------------------------------------------
    # test_export_and_import_roundtrip
    # ------------------------------------------------------------------
    def test_export_and_import_roundtrip(self):
        project = self.orch.create_project("Roundtrip Book", {"genre": "sci-fi"})
        # Manually mark a couple of agents as PASSED with fake output
        orch_state = self.orch._find_agent_state(project, "orchestrator")
        orch_state.status = AgentStatus.PASSED
        orch_state.current_output = AgentOutput(
            agent_id="orchestrator",
            content={"agent_map": {}, "stage_order": [], "state_json": "{}", "checkpoint_rules": []},
        )

        exported = self.orch.export_project_state(project)

        new_orch = Orchestrator(llm_client=None)
        imported = new_orch.import_project_state(exported)

        self.assertEqual(imported.project_id, project.project_id)
        self.assertEqual(imported.title, project.title)
        orch_imported = new_orch._find_agent_state(imported, "orchestrator")
        self.assertEqual(orch_imported.status, AgentStatus.PASSED)

    # ------------------------------------------------------------------
    # test_run_to_completion_no_llm_blocked
    # ------------------------------------------------------------------
    def test_run_to_completion_no_llm_blocked(self):
        project = self.orch.create_project("Blocked Book", {})
        asyncio.run(self.orch.run_to_completion(project))
        # With placeholder gate bypass, demo mode (no LLM) produces placeholder
        # outputs that pass gate validation, so the project completes.
        self.assertEqual(project.status, "completed")

    # ------------------------------------------------------------------
    # test_gather_inputs_includes_user_constraints
    # ------------------------------------------------------------------
    def test_gather_inputs_includes_user_constraints(self):
        constraints = {"genre": "thriller", "author_name": "Jane Doe"}
        project = self.orch.create_project("Constraint Test", constraints)
        inputs = self.orch.gather_inputs(project, "market_intelligence")
        self.assertIn("user_constraints", inputs)
        self.assertEqual(inputs["user_constraints"], constraints)

    # ------------------------------------------------------------------
    # test_gather_inputs_character_names_extraction
    # ------------------------------------------------------------------
    def test_gather_inputs_character_names_extraction(self):
        project = self.orch.create_project("Character Test", {})
        ca_state = self.orch._find_agent_state(project, "character_architecture")
        ca_state.status = AgentStatus.PASSED
        ca_state.current_output = AgentOutput(
            agent_id="character_architecture",
            content={
                "protagonist_profile": {"name": "Alice"},
                "antagonist_profile": {"name": "Bob"},
                "supporting_cast": [{"name": "Carol"}],
            },
        )
        inputs = self.orch.gather_inputs(project, "ip_clearance")
        self.assertIn("character_names", inputs)
        self.assertEqual(inputs["character_names"], ["Alice", "Bob", "Carol"])


    # ------------------------------------------------------------------
    # test_import_normalizes_chapter_number_key
    # ------------------------------------------------------------------
    def test_import_normalizes_chapter_number_key(self):
        """Importing a project with 'chapter_number' in chapters should normalize to 'number'."""
        project = self.orch.create_project("Key Test", {"genre": "romance"})
        export = self.orch.export_project_state(project)

        # Simulate old-format chapters with 'chapter_number' instead of 'number'
        export["manuscript"] = {
            "chapters": [
                {"chapter_number": 1, "title": "Ch 1", "text": "A", "word_count": 1},
                {"chapter_number": 2, "title": "Ch 2", "text": "B", "word_count": 1},
                {"chapter_number": 1, "title": "Ch 1 dup", "text": "C", "word_count": 1},  # duplicate
            ]
        }

        new_orch = Orchestrator(llm_client=None)
        imported = new_orch.import_project_state(export)
        chapters = imported.manuscript.get("chapters", [])

        # All chapters should have 'number' key
        for ch in chapters:
            self.assertIn("number", ch, f"Chapter missing 'number' key: {ch}")

        # Duplicates should be removed (keep latest)
        chapter_nums = [ch["number"] for ch in chapters]
        self.assertEqual(sorted(chapter_nums), [1, 2], "Should have exactly chapters 1 and 2")

        # The duplicate ch1 ("C") should win (last entry)
        ch1 = [ch for ch in chapters if ch["number"] == 1][0]
        self.assertEqual(ch1["text"], "C", "Latest duplicate should be kept")

    # ------------------------------------------------------------------
    # test_chapter_writer_returns_number_key
    # ------------------------------------------------------------------
    def test_chapter_writer_returns_number_key(self):
        """execute_chapter_writer should return 'number', not 'chapter_number'."""
        from agents.chapter_writer import execute_chapter_writer
        from core.orchestrator import ExecutionContext
        from unittest.mock import MagicMock

        project = MagicMock()
        project.manuscript = {"chapters": []}
        inputs = {
            "chapter_blueprint": {
                "chapter_outline": [
                    {"number": 1, "title": "Test", "scenes": [], "word_target": 100}
                ]
            },
            "voice_specification": {},
            "character_architecture": {},
            "world_rules": {},
        }
        context = ExecutionContext(project=project, inputs=inputs, llm_client=None)

        result = asyncio.run(execute_chapter_writer(context, 1))
        self.assertIn("number", result, "Chapter writer should return 'number' key")
        self.assertEqual(result["number"], 1)
        self.assertNotIn("chapter_number", result, "Should NOT have 'chapter_number' key")


if __name__ == "__main__":
    unittest.main()
