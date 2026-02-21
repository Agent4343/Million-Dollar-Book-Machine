"""
Tests for:
1. Demo mode gate bypass (placeholder _status bypasses strict validation)
2. Failed agent recovery (reset_agent + _check_layer_completion with terminal failures)
3. gather_inputs O(1) index optimization
"""

import unittest

from core.gates import validate_agent_output
from core.orchestrator import ExecutionContext, Orchestrator
from models.agents import AGENT_REGISTRY
from models.state import AgentOutput, AgentStatus, GateResult, LayerStatus


class TestDemoModeGateBypass(unittest.TestCase):
    """Gate validation should auto-pass placeholder outputs from demo mode."""

    def test_placeholder_status_bypasses_gate(self):
        content = {
            "_agent": "market_intelligence",
            "_status": "placeholder",
            "_message": "Awaiting LLM implementation",
            "reader_avatar": "[Generated reader_avatar]",
            "market_size": "[Generated market_size]",
        }
        passed, message, details, normalized = validate_agent_output(
            agent_id="market_intelligence",
            content=content,
            expected_outputs=["reader_avatar", "market_size"],
        )
        self.assertTrue(passed)
        self.assertIn("placeholder", message.lower())
        self.assertTrue(details.get("placeholder"))

    def test_non_placeholder_still_validated(self):
        # A result without _status=placeholder should still fail if outputs are missing
        content = {
            "some_key": "some_value",
        }
        passed, _, _, _ = validate_agent_output(
            agent_id="market_intelligence",
            content=content,
            expected_outputs=["reader_avatar"],
        )
        self.assertFalse(passed)

    def test_default_executor_produces_placeholder(self):
        """_default_executor output should pass gate validation in demo mode."""
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Demo Test", {"genre": "Thriller"})

        # Run _default_executor for the first agent in layer 0
        agent_id = next(iter(project.layers[0].agents))
        agent_def = AGENT_REGISTRY[agent_id]
        ctx = ExecutionContext(project=project, inputs={}, agent_def=agent_def, llm_client=None)
        result = orch._default_executor(ctx)

        self.assertEqual(result.get("_status"), "placeholder")

        passed, _, details, _ = validate_agent_output(
            agent_id=agent_id,
            content=result,
            expected_outputs=agent_def.outputs,
        )
        self.assertTrue(passed)
        self.assertTrue(details.get("placeholder"))


class TestFailedAgentRecovery(unittest.TestCase):
    """Tests for reset_agent and terminal-failure layer completion."""

    def _make_failed_agent(self, orch, project, agent_id):
        """Helper to mark an agent as FAILED with exhausted retries."""
        agent_state = orch._find_agent_state(project, agent_id)
        agent_def = AGENT_REGISTRY[agent_id]
        agent_state.status = AgentStatus.FAILED
        agent_state.attempts = agent_def.retry_limit
        agent_state.last_error = "Test failure"
        return agent_state

    def test_reset_agent_clears_failed_state(self):
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Reset Test", {"genre": "Mystery"})

        # Pick first agent in layer 0, mark it failed
        agent_id = next(iter(project.layers[0].agents))
        self._make_failed_agent(orch, project, agent_id)

        # Reset it
        agent_state = orch.reset_agent(project, agent_id)

        self.assertEqual(agent_state.status, AgentStatus.PENDING)
        self.assertEqual(agent_state.attempts, 0)
        self.assertIsNone(agent_state.last_error)

    def test_reset_agent_raises_if_not_failed(self):
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Reset Test", {"genre": "Mystery"})

        agent_id = next(iter(project.layers[0].agents))
        # Agent starts PENDING — reset should raise
        with self.assertRaises(ValueError):
            orch.reset_agent(project, agent_id)

    def test_reset_agent_raises_if_agent_not_found(self):
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Reset Test", {"genre": "Mystery"})

        with self.assertRaises(ValueError):
            orch.reset_agent(project, "nonexistent_agent")

    def test_terminal_failure_unlocks_next_layer(self):
        """A layer where all agents are terminally failed should still unlock the next layer."""
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Terminal Test", {"genre": "SciFi"})

        layer0 = project.layers[0]
        # Mark all agents in layer 0 as FAILED with exhausted retries
        for agent_id in list(layer0.agents.keys()):
            self._make_failed_agent(orch, project, agent_id)

        # Run layer completion check
        orch._check_layer_completion(project, 0)

        self.assertEqual(layer0.status, LayerStatus.COMPLETED)
        self.assertEqual(project.layers[1].status, LayerStatus.AVAILABLE)

    def test_layer_not_completed_while_agent_still_pending(self):
        """A layer with a PENDING agent should not complete."""
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Pending Test", {"genre": "Fantasy"})

        layer0 = project.layers[0]
        agents = list(layer0.agents.keys())

        # Mark all but one as PASSED
        for agent_id in agents[:-1]:
            layer0.agents[agent_id].status = AgentStatus.PASSED

        # Last one stays PENDING
        orch._check_layer_completion(project, 0)

        self.assertNotEqual(layer0.status, LayerStatus.COMPLETED)

    def test_reset_reopens_completed_layer(self):
        """Resetting an agent in a completed layer should reopen it to IN_PROGRESS."""
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Reopen Test", {"genre": "Romance"})

        layer0 = project.layers[0]

        # Mark all agents as FAILED then trigger completion
        for agent_id in list(layer0.agents.keys()):
            self._make_failed_agent(orch, project, agent_id)
        orch._check_layer_completion(project, 0)
        self.assertEqual(layer0.status, LayerStatus.COMPLETED)

        # Reset one agent — layer should reopen
        first_agent_id = next(iter(layer0.agents))
        orch.reset_agent(project, first_agent_id)
        self.assertEqual(layer0.status, LayerStatus.IN_PROGRESS)


class TestCascadeFailures(unittest.TestCase):
    """Cascade terminal failures to transitive dependents."""

    def test_cascade_on_layer_completion(self):
        """When an agent fails terminally, all transitive dependents should be FAILED."""
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Cascade Test", {"genre": "SciFi"})

        # Fail the orchestrator terminally (layer 0)
        agent = project.layers[0].agents["orchestrator"]
        agent.status = AgentStatus.FAILED
        agent.attempts = 3

        orch._check_layer_completion(project, 0)

        # Layer 0 completed, layer 1 unlocked
        self.assertEqual(project.layers[0].status, LayerStatus.COMPLETED)
        self.assertEqual(project.layers[1].status, LayerStatus.AVAILABLE)

        # market_intelligence depends on orchestrator → cascade-failed
        mi = orch._find_agent_state(project, "market_intelligence")
        self.assertEqual(mi.status, AgentStatus.FAILED)
        self.assertIn("Cascade:", mi.last_error)

        # draft_generation is a transitive dependent → also cascade-failed
        dg = orch._find_agent_state(project, "draft_generation")
        self.assertEqual(dg.status, AgentStatus.FAILED)

    def test_cascade_on_import(self):
        """Importing a persisted project with terminal failures should cascade."""
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Import Cascade", {"genre": "Thriller"})

        # Simulate a persisted state: orchestrator FAILED, dependents still PENDING
        exported = orch.export_project_state(project)
        exported["layers"]["0"]["agents"]["orchestrator"]["status"] = "failed"
        exported["layers"]["0"]["agents"]["orchestrator"]["attempts"] = 3
        exported["layers"]["0"]["status"] = "completed"
        exported["layers"]["1"]["status"] = "available"

        # Import — cascade should apply
        orch2 = Orchestrator(llm_client=None)
        imported = orch2.import_project_state(exported)

        mi = orch2._find_agent_state(imported, "market_intelligence")
        self.assertEqual(mi.status, AgentStatus.FAILED)
        self.assertIn("Cascade:", mi.last_error)

        # No agents should be available
        available = orch2.get_available_agents(imported)
        self.assertEqual(available, [])

    def test_reset_uncascades(self):
        """Resetting a root-failed agent should uncascade its dependents."""
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Uncascade Test", {"genre": "Fantasy"})

        agent = project.layers[0].agents["orchestrator"]
        agent.status = AgentStatus.FAILED
        agent.attempts = 3
        orch._check_layer_completion(project, 0)

        # Verify cascade happened
        mi = orch._find_agent_state(project, "market_intelligence")
        self.assertEqual(mi.status, AgentStatus.FAILED)

        # Reset the root agent
        orch.reset_agent(project, "orchestrator")

        # Orchestrator back to PENDING
        self.assertEqual(agent.status, AgentStatus.PENDING)
        # Dependents uncascaded back to PENDING
        mi = orch._find_agent_state(project, "market_intelligence")
        self.assertEqual(mi.status, AgentStatus.PENDING)

    def test_no_available_agents_returns_empty(self):
        """get_available_agents returns [] when all agents are terminal."""
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Dead Pipeline", {"genre": "Horror"})

        # Fail orchestrator terminally and cascade
        agent = project.layers[0].agents["orchestrator"]
        agent.status = AgentStatus.FAILED
        agent.attempts = 3
        orch._check_layer_completion(project, 0)

        available = orch.get_available_agents(project)
        self.assertEqual(available, [])


class TestGatherInputsPerformance(unittest.TestCase):
    """gather_inputs should use indexed lookup (no nested loop over all agents per input)."""

    def test_gather_inputs_finds_output_by_key(self):
        """An output produced by any upstream agent should be discoverable by key."""
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Input Test", {"genre": "Horror"})

        # Manually inject a completed agent output that contains a known key
        layer0 = project.layers[0]
        first_agent_id = next(iter(layer0.agents))
        layer0.agents[first_agent_id].current_output = AgentOutput(
            agent_id=first_agent_id,
            content={"some_custom_output_key": "custom_value"},
            gate_result=GateResult(passed=True, message="ok"),
        )
        layer0.agents[first_agent_id].status = AgentStatus.PASSED

        test_agent_id = list(layer0.agents.keys())[0]
        agent_def = AGENT_REGISTRY.get(test_agent_id)
        if agent_def is None:
            return  # skip if registry is empty

        # Override inputs to include our custom key to verify index lookup works
        original_inputs = agent_def.inputs
        agent_def.inputs = list(original_inputs) + ["some_custom_output_key"]
        try:
            inputs = orch.gather_inputs(project, test_agent_id)
            self.assertIn("some_custom_output_key", inputs)
            self.assertEqual(inputs["some_custom_output_key"], "custom_value")
        finally:
            agent_def.inputs = original_inputs

    def test_gather_inputs_includes_agent_id_inputs(self):
        """Regression: agent-id wiring (e.g. draft_generation → chapter_blueprint) still works."""
        orch = Orchestrator(llm_client=None)
        project = orch.create_project("Wiring Test", {"genre": "Fiction"})

        cb_state = orch._find_agent_state(project, "chapter_blueprint")
        self.assertIsNotNone(cb_state)
        cb_state.status = AgentStatus.PASSED
        cb_state.current_output = AgentOutput(
            agent_id="chapter_blueprint",
            content={"chapter_outline": []},
        )

        inputs = orch.gather_inputs(project, "draft_generation")
        self.assertIn("chapter_blueprint", inputs)


if __name__ == "__main__":
    unittest.main()
