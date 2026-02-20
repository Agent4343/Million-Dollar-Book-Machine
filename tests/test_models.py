import unittest

from models.agents import AGENT_REGISTRY, get_agent_execution_order


class TestAgentRegistry(unittest.TestCase):

    def test_all_dependencies_exist_in_registry(self):
        for agent_id, agent_def in AGENT_REGISTRY.items():
            for dep in agent_def.dependencies:
                self.assertIn(
                    dep,
                    AGENT_REGISTRY,
                    msg=f"Agent '{agent_id}' has dependency '{dep}' not in AGENT_REGISTRY",
                )

    def test_no_circular_dependencies(self):
        order = get_agent_execution_order()
        # Same number of unique entries as registry size
        self.assertEqual(len(set(order)), len(AGENT_REGISTRY))
        # No agent appears before one of its dependencies
        position = {agent_id: idx for idx, agent_id in enumerate(order)}
        for agent_id, agent_def in AGENT_REGISTRY.items():
            for dep in agent_def.dependencies:
                self.assertLess(
                    position[dep],
                    position[agent_id],
                    msg=f"Agent '{agent_id}' appears before its dependency '{dep}'",
                )

    def test_layer_0_has_no_dependencies(self):
        for agent_id, agent_def in AGENT_REGISTRY.items():
            if agent_def.layer == 0:
                self.assertEqual(
                    agent_def.dependencies,
                    [],
                    msg=f"Layer-0 agent '{agent_id}' must have no dependencies",
                )

    def test_agent_outputs_are_non_empty(self):
        for agent_id, agent_def in AGENT_REGISTRY.items():
            self.assertTrue(
                len(agent_def.outputs) > 0,
                msg=f"Agent '{agent_id}' has an empty outputs list",
            )


if __name__ == "__main__":
    unittest.main()
