"""
Book Development State Model

Tracks the complete state of a book project through all development layers.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
import json
import uuid


class AgentStatus(Enum):
    """Status of an agent's execution."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


class LayerStatus(Enum):
    """Status of a development layer."""
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class GateResult:
    """Result of a quality gate check."""
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class AgentOutput:
    """Output from an agent's execution."""
    agent_id: str
    content: Dict[str, Any]
    gate_result: Optional[GateResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: int = 1


@dataclass
class AgentState:
    """State of a single agent."""
    agent_id: str
    name: str
    layer: int
    status: AgentStatus = AgentStatus.PENDING
    outputs: List[AgentOutput] = field(default_factory=list)
    current_output: Optional[AgentOutput] = None
    attempts: int = 0
    last_error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "layer": self.layer,
            "status": self.status.value,
            "outputs_count": len(self.outputs),
            "current_output": self.current_output.content if self.current_output else None,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "dependencies": self.dependencies
        }


@dataclass
class LayerState:
    """State of a development layer."""
    layer_id: int
    name: str
    status: LayerStatus = LayerStatus.LOCKED
    agents: Dict[str, AgentState] = field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_id": self.layer_id,
            "name": self.name,
            "status": self.status.value,
            "agents": {k: v.to_dict() for k, v in self.agents.items()},
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }


@dataclass
class BookProject:
    """Complete state of a book development project."""
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Project"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # User constraints and inputs
    user_constraints: Dict[str, Any] = field(default_factory=dict)

    # Layer states
    layers: Dict[int, LayerState] = field(default_factory=dict)

    # Current position
    current_layer: int = 0
    current_agent: Optional[str] = None

    # Global state
    status: str = "initialized"
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)

    # Generated content
    manuscript: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_constraints": self.user_constraints,
            "layers": {k: v.to_dict() for k, v in self.layers.items()},
            "current_layer": self.current_layer,
            "current_agent": self.current_agent,
            "status": self.status,
            "checkpoints_count": len(self.checkpoints),
            "manuscript_chapters": len(self.manuscript.get("chapters", []))
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def save_checkpoint(self, name: str) -> None:
        """Save current state as a checkpoint."""
        self.checkpoints.append({
            "name": name,
            "timestamp": datetime.utcnow().isoformat(),
            "layer": self.current_layer,
            "agent": self.current_agent,
            "state_snapshot": self.to_dict()
        })

    def update_timestamp(self) -> None:
        """Update the last modified timestamp."""
        self.updated_at = datetime.utcnow().isoformat()


# Layer definitions
LAYERS = {
    0: "Orchestration & State Control",
    1: "Market & Reader Intelligence",
    2: "Core Concept Definition",
    3: "Thematic Architecture",
    4: "Central Story Question",
    5: "World / Context Rules",
    6: "Character Architecture",
    7: "Relationship Dynamics",
    8: "Macro Plot Structure",
    9: "Pacing & Tension Design",
    10: "Chapter & Scene Blueprint",
    11: "Style & Voice Specification",
    12: "Draft Generation",
    13: "Continuity & Logic Audit",
    14: "Emotional Impact Validation",
    15: "Originality & Legal Safety",
    16: "Rewrite & Revalidation",
    17: "Line & Copy Edit",
    18: "Beta Reader Simulation",
    19: "Final Quality Validation",
    20: "Publishing Package"
}
