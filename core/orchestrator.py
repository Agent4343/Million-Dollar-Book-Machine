"""
Book Development Orchestrator

Central controller that manages the execution flow of all agents,
handles state transitions, validates gates, and coordinates the
complete book development pipeline.
"""

import inspect
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

from models.state import (
    BookProject, LayerState, AgentState, AgentOutput, GateResult,
    AgentStatus, LayerStatus, LAYERS
)
from models.agents import AGENT_REGISTRY, AgentDefinition, get_agent_execution_order
from core.gates import validate_agent_output

logger = logging.getLogger(__name__)

# Default retry limit used when an agent definition is not found in the registry.
DEFAULT_RETRY_LIMIT = 3


@dataclass
class ExecutionContext:
    """Context passed to agent executors."""
    project: BookProject
    inputs: Dict[str, Any]
    agent_def: Optional[AgentDefinition] = None
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
        project.current_layer = 0

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
        inputs["title"] = project.title

        # Gather from dependencies and their outputs
        for dep_id in agent_def.dependencies:
            dep_state = self._find_agent_state(project, dep_id)
            if dep_state and dep_state.current_output:
                inputs[dep_id] = dep_state.current_output.content

        # Build an output-name index once so lookups are O(1) instead of O(agents × inputs).
        # project.layers is a plain dict with integer keys inserted in ascending order (0-20),
        # so iteration is in layer-dependency order and earlier layers take precedence.
        output_index: Dict[str, Any] = {}
        for layer in project.layers.values():
            for agent_state in layer.agents.values():
                if agent_state.current_output:
                    content = agent_state.current_output.content
                    if isinstance(content, dict):
                        for k, v in content.items():
                            # First writer wins — earlier layers take precedence
                            if k not in output_index:
                                output_index[k] = v

        # Also search for specific named inputs
        for input_name in agent_def.inputs:
            if input_name in project.user_constraints:
                inputs[input_name] = project.user_constraints[input_name]

            # If the input name is an agent id, include that agent's full output
            # (this fixes common wiring issues like draft_generation needing chapter_blueprint).
            if input_name in AGENT_REGISTRY:
                upstream = self._find_agent_state(project, input_name)
                if upstream and upstream.current_output:
                    inputs[input_name] = upstream.current_output.content

            # Derived inputs
            if input_name == "title":
                inputs["title"] = project.title
            if input_name == "author_name":
                c = project.user_constraints or {}
                if isinstance(c, dict):
                    author = c.get("author_name") or c.get("pen_name") or "Author Name"
                    inputs["author_name"] = author
            if input_name == "character_names":
                ca = self._find_agent_state(project, "character_architecture")
                names: List[str] = []
                if ca and ca.current_output and isinstance(ca.current_output.content, dict):
                    cap = ca.current_output.content
                    pro = (cap.get("protagonist_profile") or {}) if isinstance(cap.get("protagonist_profile"), dict) else {}
                    ant = (cap.get("antagonist_profile") or {}) if isinstance(cap.get("antagonist_profile"), dict) else {}
                    if pro.get("name"):
                        names.append(pro["name"])
                    if ant.get("name"):
                        names.append(ant["name"])
                    for s in cap.get("supporting_cast") or []:
                        if isinstance(s, dict) and s.get("name"):
                            names.append(s["name"])
                # De-dup while preserving order
                deduped: List[str] = []
                for n in names:
                    if n and n not in deduped:
                        deduped.append(n)
                if deduped:
                    inputs["character_names"] = deduped

            # O(1) lookup via pre-built index
            if input_name in output_index:
                inputs[input_name] = output_index[input_name]

        return inputs

    async def execute_agent(
        self,
        project: BookProject,
        agent_id: str,
        executor: Optional[Callable] = None,
        progress_callback: Optional[Callable] = None,
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
            layer.started_at = datetime.now(timezone.utc).isoformat()

        # Gather inputs
        inputs = self.gather_inputs(project, agent_id)

        # Create execution context
        context = ExecutionContext(
            project=project,
            inputs=inputs,
            agent_def=agent_def,
            llm_client=self.llm_client
        )

        try:
            # Execute the agent
            if executor:
                fn = executor
            elif agent_id in self.agent_executors:
                fn = self.agent_executors[agent_id]
            else:
                fn = None

            if fn is not None:
                # Pass progress_callback only if the executor accepts it.
                try:
                    sig = inspect.signature(fn)
                    supports_cb = "progress_callback" in sig.parameters
                except (ValueError, TypeError):
                    supports_cb = False

                if supports_cb and progress_callback is not None:
                    result = await fn(context, progress_callback=progress_callback)
                else:
                    result = await fn(context)
            else:
                # Default executor that returns placeholder
                result = self._default_executor(context)

            # Optional self-heal loop: if we expect JSON/dict and gates fail, ask the LLM
            # to repair the output using the gate errors and retry within this attempt.
            repair_rounds = 0
            max_repairs = 2
            gate_result, normalized = self._validate_and_normalize_gate(agent_def, result)

            # Skip repair for agents whose output is too large to fit in a
            # repair prompt (e.g. draft_generation contains full chapter text).
            # Serialising the output for repair would exceed the LLM context
            # and the 8 000-token response can't reproduce the manuscript.
            _output_too_large = (
                isinstance(result, dict)
                and len(json.dumps(result, ensure_ascii=False, default=str)) > 50_000
            )

            while (
                not gate_result.passed
                and self.llm_client is not None
                and isinstance(result, dict)
                and repair_rounds < max_repairs
                and not _output_too_large
            ):
                repaired = await self._repair_output(
                    agent_def=agent_def,
                    inputs=inputs,
                    bad_output=result,
                    gate_result=gate_result,
                )
                if repaired is None:
                    break
                result = repaired
                repair_rounds += 1
                gate_result, normalized = self._validate_and_normalize_gate(agent_def, result)

            # Create output
            output = AgentOutput(
                agent_id=agent_id,
                content=normalized if isinstance(normalized, dict) and normalized else (result if isinstance(result, dict) else {"result": result}),
                metadata={
                    "attempt": agent_state.attempts,
                    "inputs_used": list(inputs.keys()),
                    "repair_rounds": repair_rounds,
                }
            )

            # Gate result from validation above
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

    def _validate_and_normalize_gate(
        self,
        agent_def: AgentDefinition,
        result: Any,
    ) -> tuple[GateResult, Dict[str, Any]]:
        """
        Validate and normalize an agent's output against its gate.

        This performs:
        - Required key checks (backwards compatible with agent_def.outputs)
        - Pydantic schema checks for supported agents
        - Lightweight semantic sanity checks
        """
        if not isinstance(result, dict):
            return (
                GateResult(
                    passed=False,
                    message="Agent returned non-JSON output where JSON was expected.",
                    details={"error": "non_dict_output", "type": str(type(result))},
                ),
                {},
            )

        # Explicit failure markers from agents (kept for compatibility)
        if result.get("_gate_failed"):
            return (
                GateResult(
                    passed=False,
                    message=result.get("_gate_message", "Gate validation failed"),
                    details=result.get("_gate_details", {}),
                ),
                result,
            )

        passed, message, details, normalized = validate_agent_output(
            agent_id=agent_def.agent_id,
            content=result,
            expected_outputs=agent_def.outputs,
        )

        return GateResult(passed=passed, message=message, details=details), normalized

    async def _repair_output(
        self,
        *,
        agent_def: AgentDefinition,
        inputs: Dict[str, Any],
        bad_output: Dict[str, Any],
        gate_result: GateResult,
    ) -> Optional[Dict[str, Any]]:
        """
        Ask the LLM to repair an invalid JSON output.

        This is a focused "fix the JSON to satisfy constraints" step, not a re-run.
        """
        if self.llm_client is None:
            return None

        # Keep repair prompt small: inputs can be huge.
        # We send only the *keys* of inputs plus user_constraints if present.
        input_keys = list(inputs.keys())
        user_constraints = inputs.get("user_constraints", {})

        prompt = f"""You are repairing the output of agent "{agent_def.agent_id}" ({agent_def.name}).

The previous JSON output FAILED validation.

## Validation failure
Message: {gate_result.message}
Details: {json.dumps(gate_result.details, ensure_ascii=False)}

## Required output keys
{json.dumps(agent_def.outputs)}

## Available input keys (do not request more)
{json.dumps(input_keys)}

## User constraints (if relevant)
{json.dumps(user_constraints, ensure_ascii=False)}

## Bad JSON output to repair
{json.dumps(bad_output, ensure_ascii=False)}

Return ONLY corrected JSON (no markdown, no commentary)."""

        try:
            repaired = await self.llm_client.generate(prompt, response_format="json", temperature=0.2, max_tokens=8000)
            if isinstance(repaired, dict):
                return repaired
            return None
        except Exception:
            logger.exception("Repair attempt failed")
            return None

    def _check_layer_completion(self, project: BookProject, layer_id: int) -> None:
        """Check if a layer is complete and unlock the next one."""
        layer = project.layers[layer_id]

        # A layer is "done" when every agent has either passed or terminally failed
        # (exhausted all retries with FAILED status).  Permanently-failed agents are
        # not retried automatically but can be reset by the user via reset_agent().
        def _is_terminal(agent: AgentState) -> bool:
            if agent.status == AgentStatus.PASSED:
                return True
            if agent.status == AgentStatus.FAILED:
                agent_def = AGENT_REGISTRY.get(agent.agent_id)
                retry_limit = agent_def.retry_limit if agent_def else DEFAULT_RETRY_LIMIT
                return agent.attempts >= retry_limit
            return False

        all_terminal = all(_is_terminal(agent) for agent in layer.agents.values())

        if all_terminal:
            layer.status = LayerStatus.COMPLETED
            layer.completed_at = datetime.now(timezone.utc).isoformat()
            project.current_layer = layer_id

            # Collect agent IDs that failed terminally in this layer.
            failed_ids = {
                a.agent_id
                for a in layer.agents.values()
                if a.status == AgentStatus.FAILED
            }

            # Cascade failure: mark any downstream PENDING agent whose
            # dependency chain includes a terminally-failed agent as FAILED
            # too, so the pipeline doesn't get stuck with unexecutable agents.
            if failed_ids:
                self._cascade_failures(project, failed_ids)

            # Unlock next layer
            next_layer_id = layer_id + 1
            if next_layer_id in project.layers:
                project.layers[next_layer_id].status = LayerStatus.AVAILABLE
                project.current_layer = next_layer_id
                logger.info(f"Layer {layer_id} completed, unlocked layer {next_layer_id}")
            else:
                logger.info(f"Layer {layer_id} completed (final layer)")

    def _cascade_failures(self, project: BookProject, failed_ids: set) -> None:
        """Mark PENDING agents as FAILED if any dependency is in *failed_ids*.

        Walks the full agent graph so transitive dependents are also cascaded.
        """
        changed = True
        while changed:
            changed = False
            for layer in project.layers.values():
                for agent_state in layer.agents.values():
                    if agent_state.status != AgentStatus.PENDING:
                        continue
                    for dep_id in agent_state.dependencies:
                        if dep_id in failed_ids:
                            agent_state.status = AgentStatus.FAILED
                            agent_state.last_error = (
                                f"Cascade: dependency '{dep_id}' failed terminally"
                            )
                            failed_ids.add(agent_state.agent_id)
                            changed = True
                            logger.warning(
                                "Agent %s cascade-failed (dependency %s failed)",
                                agent_state.agent_id,
                                dep_id,
                            )
                            break

    def register_executor(self, agent_id: str, executor: Callable) -> None:
        """Register a custom executor for an agent."""
        self.agent_executors[agent_id] = executor

    def reset_agent(self, project: BookProject, agent_id: str) -> AgentState:
        """
        Reset a FAILED agent back to PENDING so it can be retried.

        This also re-evaluates the layer status so that previously locked
        downstream layers can be re-locked if they depended on this agent.

        Args:
            project: The book project
            agent_id: Agent to reset

        Returns:
            The updated AgentState

        Raises:
            ValueError: If the agent doesn't exist or is not in FAILED status
        """
        agent_state = self._find_agent_state(project, agent_id)
        if not agent_state:
            raise ValueError(f"Agent not found in project: {agent_id}")
        if agent_state.status != AgentStatus.FAILED:
            raise ValueError(f"Agent {agent_id} is not in FAILED status (current: {agent_state.status.value})")

        agent_def = AGENT_REGISTRY.get(agent_id)
        if not agent_def:
            raise ValueError(f"Unknown agent: {agent_id}")

        # Reset the agent
        agent_state.status = AgentStatus.PENDING
        agent_state.attempts = 0
        agent_state.last_error = None

        # Ensure the agent's layer is available so it can be picked up
        layer = project.layers[agent_def.layer]
        if layer.status == LayerStatus.COMPLETED:
            layer.status = LayerStatus.IN_PROGRESS
            layer.completed_at = None

        # Also reset any agents that were cascade-failed due to this agent.
        self._uncascade_failures(project, agent_id)

        project.update_timestamp()
        logger.info(f"Agent {agent_id} reset to PENDING")
        return agent_state

    def _uncascade_failures(self, project: BookProject, reset_agent_id: str) -> None:
        """Reset cascade-failed dependents back to PENDING.

        When an agent is reset, any downstream agent that was only failed
        because of a cascade from this agent should also be reset.
        """
        changed = True
        reset_ids = {reset_agent_id}
        while changed:
            changed = False
            for layer in project.layers.values():
                for agent_state in layer.agents.values():
                    if agent_state.status != AgentStatus.FAILED:
                        continue
                    err = agent_state.last_error or ""
                    if not err.startswith("Cascade: dependency '"):
                        continue
                    # Check if the cascade was from an agent we're resetting
                    for rid in reset_ids:
                        if f"'{rid}'" in err:
                            agent_state.status = AgentStatus.PENDING
                            agent_state.attempts = 0
                            agent_state.last_error = None
                            reset_ids.add(agent_state.agent_id)
                            # Re-open the layer if needed
                            agent_def = AGENT_REGISTRY.get(agent_state.agent_id)
                            if agent_def and agent_def.layer in project.layers:
                                lyr = project.layers[agent_def.layer]
                                if lyr.status == LayerStatus.COMPLETED:
                                    lyr.status = LayerStatus.IN_PROGRESS
                                    lyr.completed_at = None
                            changed = True
                            break

    def get_blocked_agents_diagnostics(self, project: BookProject) -> Dict[str, Any]:
        """
        Return a structured diagnostic payload explaining why the project is blocked.

        For every PENDING agent whose layer is AVAILABLE or IN_PROGRESS but whose
        dependencies are not all PASSED, report which dependency is unmet and what
        status it currently has.  Also summarises layer-level lock reasons.
        """
        blocked_candidates: List[Dict[str, Any]] = []
        agent_status_counts: Dict[str, int] = {}
        layer_status_counts: Dict[str, int] = {}

        for layer_id, layer in project.layers.items():
            ls = layer.status.value
            layer_status_counts[ls] = layer_status_counts.get(ls, 0) + 1

            for agent_id, agent_state in layer.agents.items():
                ags = agent_state.status.value
                agent_status_counts[ags] = agent_status_counts.get(ags, 0) + 1

                # Only care about agents that could potentially run but are stuck
                if agent_state.status.value != "pending":
                    continue

                unmet_deps: List[Dict[str, str]] = []
                for dep_id in agent_state.dependencies:
                    dep_state = self._find_agent_state(project, dep_id)
                    if dep_state is None:
                        unmet_deps.append({"dep_id": dep_id, "dep_status": "missing"})
                    elif dep_state.status.value != "passed":
                        unmet_deps.append({"dep_id": dep_id, "dep_status": dep_state.status.value})

                if unmet_deps:
                    blocked_candidates.append(
                        {
                            "agent_id": agent_id,
                            "agent_name": agent_state.name,
                            "layer": layer_id,
                            "layer_name": layer.name,
                            "layer_status": layer.status.value,
                            "unmet_dependencies": unmet_deps,
                        }
                    )

        # Explain why the *next* locked layer hasn't unlocked
        locked_layer_reasons: List[Dict[str, Any]] = []
        for layer_id, layer in project.layers.items():
            if layer.status.value != "locked":
                continue
            prev_layer_id = layer_id - 1
            if prev_layer_id not in project.layers:
                continue
            prev_layer = project.layers[prev_layer_id]
            not_passed = [
                {"agent_id": aid, "status": a.status.value}
                for aid, a in prev_layer.agents.items()
                if a.status.value != "passed"
            ]
            locked_layer_reasons.append(
                {
                    "locked_layer": layer_id,
                    "locked_layer_name": layer.name,
                    "blocking_layer": prev_layer_id,
                    "blocking_layer_name": prev_layer.name,
                    "blocking_layer_status": prev_layer.status.value,
                    "agents_not_yet_passed": not_passed,
                }
            )

        return {
            "project_id": project.project_id,
            "project_status": project.status,
            "blocked_candidates": blocked_candidates,
            "locked_layer_reasons": locked_layer_reasons,
            "agent_status_counts": agent_status_counts,
            "layer_status_counts": layer_status_counts,
        }

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
        # Prefer explicitly written chapters (chapter writer endpoint),
        # then edited/revised drafts, then raw draft_generation output.

        manuscript = {
            "title": project.title,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "chapters": [],
            "metadata": {}
        }

        # 1) Chapters written via chapter writer endpoint
        if isinstance(project.manuscript.get("chapters"), list) and project.manuscript.get("chapters"):
            manuscript["chapters"] = project.manuscript.get("chapters", [])
        else:
            # 2) Prefer line-edited chapters if available
            line_edit = self._find_agent_state(project, "line_edit")
            if line_edit and line_edit.current_output:
                content = line_edit.current_output.content
                if isinstance(content, dict) and isinstance(content.get("edited_chapters"), list):
                    manuscript["chapters"] = content.get("edited_chapters", [])

            # 3) Revised chapters
            if not manuscript["chapters"]:
                rewrite = self._find_agent_state(project, "structural_rewrite")
                if rewrite and rewrite.current_output:
                    content = rewrite.current_output.content
                    if isinstance(content, dict) and isinstance(content.get("revised_chapters"), list):
                        manuscript["chapters"] = content.get("revised_chapters", [])

            # 4) Raw draft generation
            if not manuscript["chapters"]:
                draft_agent = self._find_agent_state(project, "draft_generation")
                if draft_agent and draft_agent.current_output:
                    content = draft_agent.current_output.content
                    if isinstance(content, dict) and isinstance(content.get("chapters"), list):
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

    def export_project_state(self, project: BookProject) -> Dict[str, Any]:
        """Export full project state as JSON (stable persistence format)."""
        export_data: Dict[str, Any] = {
            "version": "1.0",
            "project_id": project.project_id,
            "title": project.title,
            "status": project.status,
            "current_layer": project.current_layer,
            "user_constraints": project.user_constraints,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "manuscript": project.manuscript,
            "layers": {},
        }

        for layer_id, layer in project.layers.items():
            export_data["layers"][str(layer_id)] = {
                "name": layer.name,
                "status": layer.status.value,
                "agents": {},
            }
            for agent_id, agent_state in layer.agents.items():
                agent_export: Dict[str, Any] = {
                    "status": agent_state.status.value,
                    "attempts": agent_state.attempts,
                    "output": None,
                }
                if agent_state.current_output:
                    agent_export["output"] = {
                        "content": agent_state.current_output.content,
                        "gate_passed": agent_state.current_output.gate_result.passed if agent_state.current_output.gate_result else None,
                        "gate_message": agent_state.current_output.gate_result.message if agent_state.current_output.gate_result else None,
                    }
                export_data["layers"][str(layer_id)]["agents"][agent_id] = agent_export

        return export_data

    def import_project_state(self, data: Dict[str, Any]) -> BookProject:
        """Import a previously exported project state."""
        from models.state import LayerStatus, AgentOutput, GateResult

        title = data.get("title") or "Untitled Project"
        user_constraints = data.get("user_constraints") or {}

        project = self.create_project(title, user_constraints)

        # Override with imported data
        project.project_id = data.get("project_id", project.project_id)
        project.status = data.get("status", project.status)
        project.current_layer = int(data.get("current_layer", project.current_layer) or 0)
        project.created_at = data.get("created_at", project.created_at)
        project.updated_at = data.get("updated_at", project.updated_at)
        project.manuscript = data.get("manuscript") or {}

        layers = data.get("layers") or {}
        if isinstance(layers, dict):
            for layer_id_str, layer_data in layers.items():
                try:
                    layer_id = int(layer_id_str)
                except Exception:
                    continue
                if layer_id not in project.layers:
                    continue
                if isinstance(layer_data, dict) and layer_data.get("status"):
                    project.layers[layer_id].status = LayerStatus(layer_data["status"])
                agents = layer_data.get("agents") if isinstance(layer_data, dict) else None
                if not isinstance(agents, dict):
                    continue
                for agent_id, agent_data in agents.items():
                    if agent_id not in project.layers[layer_id].agents or not isinstance(agent_data, dict):
                        continue
                    agent_state = project.layers[layer_id].agents[agent_id]
                    if agent_data.get("status"):
                        agent_state.status = AgentStatus(agent_data["status"])
                    agent_state.attempts = int(agent_data.get("attempts", 0) or 0)

                    output = agent_data.get("output")
                    if isinstance(output, dict) and isinstance(output.get("content"), dict):
                        gate_result = None
                        if output.get("gate_passed") is not None:
                            gate_result = GateResult(
                                passed=bool(output.get("gate_passed")),
                                message=str(output.get("gate_message") or ""),
                            )
                        agent_state.current_output = AgentOutput(
                            agent_id=agent_id,
                            content=output["content"],
                            gate_result=gate_result,
                        )

        # Register in orchestrator
        self.projects[project.project_id] = project
        return project
