"""
Book Development API - Million Dollar Book Machine

Multi-agent system for developing books from concept to publication.
"""

import hashlib
import hmac
import os
import sys
import time
import json
from typing import Optional, List, Any, Dict

from fastapi import FastAPI, HTTPException, Request, Response, Cookie, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.state import BookProject, LAYERS, AgentStatus, LayerStatus
from models.agents import AGENT_REGISTRY, get_agent_execution_order
from core.orchestrator import Orchestrator
from core.llm import create_llm_client

# Import agent executors
from agents.strategic import STRATEGIC_EXECUTORS
from agents.story_system import STORY_SYSTEM_EXECUTORS
from agents.structural import STRUCTURAL_EXECUTORS
from agents.validation import VALIDATION_EXECUTORS

# Initialize app
app = FastAPI(
    title="Million Dollar Book Machine",
    description="AI-powered book development from concept to publication",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Authentication (same as before)
# =============================================================================

APP_PASSWORD = os.environ.get("APP_PASSWORD", "Blake2011@")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "book-machine-secret")
SESSION_DURATION = 60 * 60 * 24 * 7

# Initialize LLM client (uses ANTHROPIC_API_KEY env var)
llm_client = create_llm_client()

# Global orchestrator instance with LLM
orchestrator = Orchestrator(llm_client=llm_client)

# Register all agent executors
ALL_EXECUTORS = {
    **STRATEGIC_EXECUTORS,
    **STORY_SYSTEM_EXECUTORS,
    **STRUCTURAL_EXECUTORS,
    **VALIDATION_EXECUTORS,
}

for agent_id, executor in ALL_EXECUTORS.items():
    orchestrator.register_executor(agent_id, executor)


def create_session_token(timestamp: int) -> str:
    message = f"{timestamp}:{hashlib.sha256(APP_PASSWORD.encode()).hexdigest()}"
    signature = hmac.new(SESSION_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()
    return f"{timestamp}:{signature}"


def verify_session_token(token: str) -> bool:
    if not token:
        return False
    try:
        parts = token.split(":")
        if len(parts) != 2:
            return False
        timestamp = int(parts[0])
        if time.time() - timestamp > SESSION_DURATION:
            return False
        expected = create_session_token(timestamp)
        return hmac.compare_digest(token, expected)
    except:
        return False


async def require_auth(session: Optional[str] = Cookie(None, alias="book_session")):
    if not verify_session_token(session):
        raise HTTPException(status_code=401, detail="Authentication required")
    return True


# =============================================================================
# Models
# =============================================================================

class LoginRequest(BaseModel):
    password: str


class ProjectCreate(BaseModel):
    title: str
    genre: str
    target_word_count: int = 80000
    description: Optional[str] = None
    comparable_titles: Optional[List[str]] = None
    themes: Optional[List[str]] = None
    target_audience: Optional[str] = None
    tone: Optional[str] = None
    additional_constraints: Optional[Dict[str, Any]] = None


class AgentExecuteRequest(BaseModel):
    project_id: str
    agent_id: str


# =============================================================================
# Auth Endpoints
# =============================================================================

@app.post("/api/auth/login")
async def login(request: LoginRequest, response: Response):
    if request.password == APP_PASSWORD:
        token = create_session_token(int(time.time()))
        response.set_cookie(
            key="book_session",
            value=token,
            max_age=SESSION_DURATION,
            httponly=True,
            secure=True,
            samesite="strict"
        )
        return {"success": True, "message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid password")


@app.post("/api/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="book_session")
    return {"success": True}


@app.get("/api/auth/check")
async def check_auth(session: Optional[str] = Cookie(None, alias="book_session")):
    return {"authenticated": verify_session_token(session)}


# =============================================================================
# System Info
# =============================================================================

@app.get("/")
async def root():
    return {
        "service": "Million Dollar Book Machine",
        "version": "1.0.0",
        "description": "AI-powered book development system",
        "total_agents": len(AGENT_REGISTRY),
        "total_layers": len(LAYERS),
        "llm_enabled": llm_client is not None
    }


@app.get("/api/system/llm-status")
async def llm_status(auth: bool = Depends(require_auth)):
    """Check LLM configuration status."""
    if llm_client is None:
        return {
            "enabled": False,
            "model": None,
            "message": "No ANTHROPIC_API_KEY configured. Running in demo mode with placeholder responses."
        }
    return {
        "enabled": True,
        "model": llm_client.model,
        "message": "Claude API configured and ready"
    }


@app.get("/api/system/agents")
async def list_agents(auth: bool = Depends(require_auth)):
    """List all available agents."""
    agents = []
    for agent_id, agent_def in AGENT_REGISTRY.items():
        agents.append({
            "id": agent_def.agent_id,
            "name": agent_def.name,
            "layer": agent_def.layer,
            "layer_name": LAYERS.get(agent_def.layer, "Unknown"),
            "type": agent_def.agent_type.value,
            "purpose": agent_def.purpose,
            "gate": agent_def.gate_criteria,
            "fail_condition": agent_def.fail_condition
        })
    return {"agents": sorted(agents, key=lambda x: (x["layer"], x["id"]))}


@app.get("/api/system/layers")
async def list_layers(auth: bool = Depends(require_auth)):
    """List all development layers."""
    layers = []
    for layer_id, layer_name in LAYERS.items():
        agents = [a.agent_id for a in AGENT_REGISTRY.values() if a.layer == layer_id]
        layers.append({
            "id": layer_id,
            "name": layer_name,
            "agents": agents
        })
    return {"layers": layers}


# =============================================================================
# Project Management
# =============================================================================

@app.post("/api/projects")
async def create_project(request: ProjectCreate, auth: bool = Depends(require_auth)):
    """Create a new book development project."""
    constraints = {
        "genre": request.genre,
        "target_word_count": request.target_word_count,
        "description": request.description,
        "comparable_titles": request.comparable_titles or [],
        "themes": request.themes or [],
        "target_audience": request.target_audience,
        "tone": request.tone,
    }
    if request.additional_constraints:
        constraints.update(request.additional_constraints)

    project = orchestrator.create_project(request.title, constraints)

    return {
        "success": True,
        "project_id": project.project_id,
        "title": project.title,
        "message": f"Project created with {len(AGENT_REGISTRY)} agents ready"
    }


@app.get("/api/projects")
async def list_projects(auth: bool = Depends(require_auth)):
    """List all projects."""
    projects = []
    for pid, project in orchestrator.projects.items():
        projects.append({
            "project_id": project.project_id,
            "title": project.title,
            "status": project.status,
            "current_layer": project.current_layer,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        })
    return {"projects": projects}


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str, auth: bool = Depends(require_auth)):
    """Get project details."""
    project = orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return orchestrator.get_project_status(project)


@app.get("/api/projects/{project_id}/available-agents")
async def get_available_agents(project_id: str, auth: bool = Depends(require_auth)):
    """Get agents ready to execute."""
    project = orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    available = orchestrator.get_available_agents(project)

    agents = []
    for agent_id in available:
        agent_def = AGENT_REGISTRY.get(agent_id)
        if agent_def:
            agents.append({
                "id": agent_id,
                "name": agent_def.name,
                "layer": agent_def.layer,
                "purpose": agent_def.purpose
            })

    return {"available_agents": agents}


@app.post("/api/projects/{project_id}/execute/{agent_id}")
async def execute_agent(project_id: str, agent_id: str, auth: bool = Depends(require_auth)):
    """Execute a specific agent."""
    project = orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_id}")

    available = orchestrator.get_available_agents(project)
    if agent_id not in available:
        raise HTTPException(status_code=400, detail=f"Agent {agent_id} is not available (dependencies not met)")

    try:
        output = await orchestrator.execute_agent(project, agent_id)
        return {
            "success": True,
            "agent_id": agent_id,
            "gate_passed": output.gate_result.passed if output.gate_result else False,
            "gate_message": output.gate_result.message if output.gate_result else "",
            "output_keys": list(output.content.keys())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/run-layer/{layer_id}")
async def run_layer(project_id: str, layer_id: int, auth: bool = Depends(require_auth)):
    """Run all agents in a layer."""
    project = orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    results = []
    available = orchestrator.get_available_agents(project)

    for agent_id in available:
        agent_def = AGENT_REGISTRY.get(agent_id)
        if agent_def and agent_def.layer == layer_id:
            try:
                output = await orchestrator.execute_agent(project, agent_id)
                results.append({
                    "agent_id": agent_id,
                    "success": output.gate_result.passed if output.gate_result else False,
                    "message": output.gate_result.message if output.gate_result else ""
                })
            except Exception as e:
                results.append({
                    "agent_id": agent_id,
                    "success": False,
                    "message": str(e)
                })

    return {"layer": layer_id, "results": results}


@app.get("/api/projects/{project_id}/agent/{agent_id}/output")
async def get_agent_output(project_id: str, agent_id: str, auth: bool = Depends(require_auth)):
    """Get the output from a specific agent."""
    project = orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find agent state
    for layer in project.layers.values():
        if agent_id in layer.agents:
            agent_state = layer.agents[agent_id]
            if agent_state.current_output:
                return {
                    "agent_id": agent_id,
                    "status": agent_state.status.value,
                    "output": agent_state.current_output.content,
                    "gate_passed": agent_state.current_output.gate_result.passed if agent_state.current_output.gate_result else None
                }
            else:
                return {
                    "agent_id": agent_id,
                    "status": agent_state.status.value,
                    "output": None,
                    "message": "No output yet"
                }

    raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")


@app.get("/api/projects/{project_id}/manuscript")
async def get_manuscript(project_id: str, auth: bool = Depends(require_auth)):
    """Export the manuscript."""
    project = orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return orchestrator.export_manuscript(project)


@app.post("/api/projects/{project_id}/checkpoint")
async def save_checkpoint(project_id: str, name: str = "checkpoint", auth: bool = Depends(require_auth)):
    """Save a project checkpoint."""
    project = orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.save_checkpoint(name)
    return {"success": True, "checkpoint": name, "total_checkpoints": len(project.checkpoints)}


@app.get("/api/projects/{project_id}/export")
async def export_project(project_id: str, auth: bool = Depends(require_auth)):
    """Export full project state as JSON for saving."""
    project = orchestrator.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Serialize the entire project state
    export_data = {
        "version": "1.0",
        "project_id": project.project_id,
        "title": project.title,
        "status": project.status,
        "current_layer": project.current_layer,
        "user_constraints": project.user_constraints,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "manuscript": project.manuscript,
        "layers": {}
    }

    # Export each layer and agent state
    for layer_id, layer in project.layers.items():
        export_data["layers"][str(layer_id)] = {
            "name": layer.name,
            "status": layer.status.value,
            "agents": {}
        }
        for agent_id, agent_state in layer.agents.items():
            agent_export = {
                "status": agent_state.status.value,
                "attempts": agent_state.attempts,
                "output": None
            }
            if agent_state.current_output:
                agent_export["output"] = {
                    "content": agent_state.current_output.content,
                    "gate_passed": agent_state.current_output.gate_result.passed if agent_state.current_output.gate_result else None,
                    "gate_message": agent_state.current_output.gate_result.message if agent_state.current_output.gate_result else None
                }
            export_data["layers"][str(layer_id)]["agents"][agent_id] = agent_export

    return export_data


class ProjectImport(BaseModel):
    version: str
    project_id: str
    title: str
    status: str
    current_layer: int
    user_constraints: Dict[str, Any]
    created_at: str
    updated_at: str
    manuscript: Dict[str, Any]
    layers: Dict[str, Any]


@app.post("/api/projects/import")
async def import_project(data: ProjectImport, auth: bool = Depends(require_auth)):
    """Import a previously exported project."""
    from models.state import LayerState, AgentState, AgentStatus, LayerStatus, AgentOutput, GateResult

    # Create base project
    project = orchestrator.create_project(data.title, data.user_constraints)

    # Override with imported data
    project.project_id = data.project_id
    project.status = data.status
    project.current_layer = data.current_layer
    project.created_at = data.created_at
    project.updated_at = data.updated_at
    project.manuscript = data.manuscript

    # Restore layer and agent states
    for layer_id_str, layer_data in data.layers.items():
        layer_id = int(layer_id_str)
        if layer_id in project.layers:
            project.layers[layer_id].status = LayerStatus(layer_data["status"])

            for agent_id, agent_data in layer_data["agents"].items():
                if agent_id in project.layers[layer_id].agents:
                    agent_state = project.layers[layer_id].agents[agent_id]
                    agent_state.status = AgentStatus(agent_data["status"])
                    agent_state.attempts = agent_data.get("attempts", 0)

                    if agent_data.get("output"):
                        output_data = agent_data["output"]
                        gate_result = None
                        if output_data.get("gate_passed") is not None:
                            gate_result = GateResult(
                                passed=output_data["gate_passed"],
                                message=output_data.get("gate_message", "")
                            )
                        agent_state.current_output = AgentOutput(
                            agent_id=agent_id,
                            content=output_data["content"],
                            gate_result=gate_result
                        )

    # Re-register in orchestrator with original ID
    orchestrator.projects[data.project_id] = project

    return {
        "success": True,
        "project_id": project.project_id,
        "title": project.title,
        "message": "Project imported successfully"
    }
