"""
Book Development Orchestrator

Central controller that manages the execution flow of all agents,
handles state transitions, validates gates, and coordinates the
complete book development pipeline.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

from models.state import (
    BookProject, LayerState, AgentState, AgentOutput, GateResult,
    AgentStatus, LayerStatus, LAYERS
)
from models.agents import AGENT_REGISTRY, AgentDefinition, get_agent_execution_order

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context passed to agent executors."""
    project: BookProject
    agent_def: AgentDefinition
    inputs: Dict[str, Any]
    llm_client: Any = None  # LLM client for generation


class Orchestrator:
    """
    Central orchestrator for book development.

    Manages:
    - Project initialization
    - Agent execution order
    - Gate validation
    - State persistence
    - Error recovery
    """

    def __init__(self, llm_client: Any = None):
        """
        Initialize the orchestrator.

        Args:
            llm_client: Client for LLM API calls (e.g., Anthropic, OpenAI)
        """
        self.llm_client = llm_client
        self.agent_executors: Dict[str, Callable] = {}
        self.projects: Dict[str, BookProject] = {}

    def create_project(self, title: str, constraints: Dict[str, Any]) -> BookProject:
        """
        Create a new book development project.

        Args:
            title: Project/book title
            constraints: User-provided constraints and preferences

        Returns:
            Initialized BookProject
        """
        project = BookProject(
            title=title,
            user_constraints=constraints,
            status="initialized"
        )

        # Initialize all layers
        for layer_id, layer_name in LAYERS.items():
            layer_state = LayerState(
                layer_id=layer_id,
                name=layer_name,
                status=LayerStatus.LOCKED if layer_id > 0 else LayerStatus.AVAILABLE
            )

            # Add agents for this layer
            for agent_id, agent_def in AGENT_REGISTRY.items():
                if agent_def.layer == layer_id:
                    layer_state.agents[agent_id] = AgentState(
                        agent_id=agent_id,
                        name=agent_def.name,
                        layer=layer_id,
                        dependencies=agent_def.dependencies
                    )

            project.layers[layer_id] = layer_state

        # Unlock layer 0
        project.layers[0].status = LayerStatus.AVAILABLE

        self.projects[project.project_id] = project
        logger.info(f"Created project: {project.project_id} - {title}")

        return project

    def get_project(self, project_id: str) -> Optional[BookProject]:
        """Get a project by ID."""
        return self.projects.get(project_id)

    def get_available_agents(self, project: BookProject) -> List[str]:
        """
        Get agents that are ready to execute.

        An agent is available if:
        1. Its layer is available/in_progress
        2. All dependencies have passed
        3. It hasn't already passed
        """
        available = []

        for layer_id, layer in project.layers.items():
            if layer.status not in [LayerStatus.AVAILABLE, LayerStatus.IN_PROGRESS]:
                continue

            for agent_id, agent_state in layer.agents.items():
                if agent_state.status != AgentStatus.PENDING:
                    continue

                # Check dependencies
                deps_met = True
                for dep_id in agent_state.dependencies:
                    dep_state = self._find_agent_state(project, dep_id)
                    if not dep_state or dep_state.status != AgentStatus.PASSED:
                        deps_met = False
                        break

                if deps_met:
                    available.append(agent_id)

        return available

    def _find_agent_state(self, project: BookProject, agent_id: str) -> Optional[AgentState]:
        """Find an agent's state across all layers."""
        for layer in project.layers.values():
            if agent_id in layer.agents:
                return layer.agents[agent_id]
        return None

    def gather_inputs(self, project: BookProject, agent_id: str) -> Dict[str, Any]:
        """
        Gather all required inputs for an agent.

        Inputs come from:
        1. User constraints
        2. Previous agent outputs
        """
        agent_def = AGENT_REGISTRY.get(agent_id)
        if not agent_def:
            return {}

        inputs = {}

        # Add user constraints
        inputs["user_constraints"] = project.user_constraints

        # Gather from dependencies and their outputs
        for dep_id in agent_def.dependencies:
            dep_state = self._find_agent_state(project, dep_id)
            if dep_state and dep_state.current_output:
                inputs[dep_id] = dep_state.current_output.content

        # Also search for specific named inputs
        for input_name in agent_def.inputs:
            if input_name in project.user_constraints:
                inputs[input_name] = project.user_constraints[input_name]

            # Search all completed agents for this output
            for layer in project.layers.values():
                for agent_state in layer.agents.values():
                    if agent_state.current_output:
                        content = agent_state.current_output.content
                        if input_name in content:
                            inputs[input_name] = content[input_name]

        return inputs

    async def execute_agent(
        self,
        project: BookProject,
        agent_id: str,
        executor: Optional[Callable] = None
    ) -> AgentOutput:
        """
        Execute a single agent.

        Args:
            project: The book project
            agent_id: Agent to execute
            executor: Optional custom executor function

        Returns:
            AgentOutput with results
        """
        agent_def = AGENT_REGISTRY.get(agent_id)
        if not agent_def:
            raise ValueError(f"Unknown agent: {agent_id}")

        agent_state = self._find_agent_state(project, agent_id)
        if not agent_state:
            raise ValueError(f"Agent not found in project: {agent_id}")

        # Update status
        agent_state.status = AgentStatus.RUNNING
        agent_state.attempts += 1
        project.current_agent = agent_id

        # Update layer status
        layer = project.layers[agent_def.layer]
        if layer.status == LayerStatus.AVAILABLE:
            layer.status = LayerStatus.IN_PROGRESS
            layer.started_at = datetime.utcnow().isoformat()

        # Gather inputs
        inputs = self.gather_inputs(project, agent_id)

        # Create execution context
        context = ExecutionContext(
            project=project,
            agent_def=agent_def,
            inputs=inputs,
            llm_client=self.llm_client
        )

        try:
            # Execute the agent
            if executor:
                result = await executor(context)
            elif agent_id in self.agent_executors:
                result = await self.agent_executors[agent_id](context)
            else:
                # Default executor that returns placeholder
                result = self._default_executor(context)

            # Create output
            output = AgentOutput(
                agent_id=agent_id,
                content=result,
                metadata={
                    "attempt": agent_state.attempts,
                    "inputs_used": list(inputs.keys())
                }
            )

            # Validate gate
            gate_result = self._validate_gate(agent_def, output)
            output.gate_result = gate_result

            if gate_result.passed:
                agent_state.status = AgentStatus.PASSED
                agent_state.current_output = output
                agent_state.outputs.append(output)
                logger.info(f"Agent {agent_id} PASSED gate")
            else:
                if agent_state.attempts >= agent_def.retry_limit:
                    agent_state.status = AgentStatus.FAILED
                    agent_state.last_error = gate_result.message
                    logger.error(f"Agent {agent_id} FAILED after {agent_state.attempts} attempts")
                else:
                    agent_state.status = AgentStatus.PENDING
                    logger.warning(f"Agent {agent_id} failed gate, will retry")

            # Check if layer is complete
            self._check_layer_completion(project, agent_def.layer)

            project.update_timestamp()
            return output

        except Exception as e:
            agent_state.status = AgentStatus.FAILED
            agent_state.last_error = str(e)
            logger.exception(f"Agent {agent_id} raised exception")
            raise

    def _default_executor(self, context: ExecutionContext) -> Dict[str, Any]:
        """
        Default executor that creates placeholder output.
        In production, this would call the LLM.
        """
        agent_def = context.agent_def

        # Create placeholder outputs
        result = {
            "_agent": agent_def.agent_id,
            "_status": "placeholder",
            "_message": "Awaiting LLM implementation"
        }

        for output_name in agent_def.outputs:
            result[output_name] = f"[Generated {output_name}]"

        return result

    def _validate_gate(self, agent_def: AgentDefinition, output: AgentOutput) -> GateResult:
        """
        Validate an agent's output against its gate criteria.

        In production, this would do sophisticated validation.
        For now, checks that all expected outputs exist.
        """
        content = output.content
        missing_outputs = []

        for expected in agent_def.outputs:
            if expected not in content:
                missing_outputs.append(expected)

        if missing_outputs:
            return GateResult(
                passed=False,
                message=f"Missing outputs: {missing_outputs}",
                details={"missing": missing_outputs}
            )

        # Check for explicit failure markers
        if content.get("_gate_failed"):
            return GateResult(
                passed=False,
                message=content.get("_gate_message", "Gate validation failed"),
                details=content.get("_gate_details", {})
            )

        return GateResult(
            passed=True,
            message="All outputs present and gate passed",
            details={"outputs": list(content.keys())}
        )

    def _check_layer_completion(self, project: BookProject, layer_id: int) -> None:
        """Check if a layer is complete and unlock the next one."""
        layer = project.layers[layer_id]

        # Check if all agents in this layer have passed
        all_passed = all(
            agent.status == AgentStatus.PASSED
            for agent in layer.agents.values()
        )

        if all_passed:
            layer.status = LayerStatus.COMPLETED
            layer.completed_at = datetime.utcnow().isoformat()

            # Unlock next layer
            next_layer_id = layer_id + 1
            if next_layer_id in project.layers:
                project.layers[next_layer_id].status = LayerStatus.AVAILABLE

            logger.info(f"Layer {layer_id} completed, unlocked layer {next_layer_id}")

    def register_executor(self, agent_id: str, executor: Callable) -> None:
        """Register a custom executor for an agent."""
        self.agent_executors[agent_id] = executor

    def get_project_status(self, project: BookProject) -> Dict[str, Any]:
        """Get comprehensive status of a project."""
        layers_status = {}
        for layer_id, layer in project.layers.items():
            agents_status = {
                aid: {
                    "status": a.status.value,
                    "attempts": a.attempts,
                    "has_output": a.current_output is not None
                }
                for aid, a in layer.agents.items()
            }
            layers_status[layer_id] = {
                "name": layer.name,
                "status": layer.status.value,
                "agents": agents_status
            }

        return {
            "project_id": project.project_id,
            "title": project.title,
            "status": project.status,
            "current_layer": project.current_layer,
            "current_agent": project.current_agent,
            "layers": layers_status,
            "available_agents": self.get_available_agents(project),
            "updated_at": project.updated_at
        }

    async def run_to_completion(
        self,
        project: BookProject,
        max_iterations: int = 100
    ) -> BookProject:
        """
        Run all available agents until project is complete or blocked.

        Args:
            project: The book project
            max_iterations: Safety limit on iterations

        Returns:
            Updated project
        """
        iterations = 0

        while iterations < max_iterations:
            available = self.get_available_agents(project)

            if not available:
                # Check if we're done or blocked
                all_complete = all(
                    layer.status == LayerStatus.COMPLETED
                    for layer in project.layers.values()
                )
                if all_complete:
                    project.status = "completed"
                    logger.info("Project completed!")
                else:
                    project.status = "blocked"
                    logger.warning("Project blocked - no available agents")
                break

            # Execute next available agent
            agent_id = available[0]
            await self.execute_agent(project, agent_id)
            iterations += 1

        return project

    def export_manuscript(self, project: BookProject) -> Dict[str, Any]:
        """Export the generated manuscript and metadata."""
        # Gather all chapter content from draft_generation agent
        draft_agent = self._find_agent_state(project, "draft_generation")

        manuscript = {
            "title": project.title,
            "generated_at": datetime.utcnow().isoformat(),
            "chapters": [],
            "metadata": {}
        }

        if draft_agent and draft_agent.current_output:
            content = draft_agent.current_output.content
            manuscript["chapters"] = content.get("chapters", [])

        # Gather publishing package
        pub_agent = self._find_agent_state(project, "publishing_package")
        if pub_agent and pub_agent.current_output:
            content = pub_agent.current_output.content
            manuscript["metadata"] = {
                "blurb": content.get("blurb"),
                "synopsis": content.get("synopsis"),
                "keywords": content.get("keywords"),
            }

        return manuscript
