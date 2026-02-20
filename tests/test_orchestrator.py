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
        self.assertEqual(project.status, "blocked")

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


if __name__ == "__main__":
    unittest.main()
