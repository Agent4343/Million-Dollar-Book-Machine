"""
Book Development API - Million Dollar Book Machine

Multi-agent system for developing books from concept to publication.
"""

import hashlib
import hmac
import io
import os
import sys
import time
import json
from typing import Optional, List, Any, Dict

# Load .env file before accessing environment variables
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, Response, Cookie, Depends
from fastapi.responses import StreamingResponse
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
from agents.chapter_writer import execute_chapter_writer

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

# Lazy initialization for LLM client (Vercel env vars may not be ready at import time)
_llm_client = None
_orchestrator = None

def get_llm_client():
    """Get or create LLM client with lazy initialization."""
    global _llm_client
    if _llm_client is None:
        # Check for API key at request time, not import time
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            _llm_client = create_llm_client(api_key=api_key)
    return _llm_client

def get_orchestrator():
    """Get or create orchestrator with lazy initialization."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator(llm_client=get_llm_client())
        # Register all agent executors
        for agent_id, executor in ALL_EXECUTORS.items():
            _orchestrator.register_executor(agent_id, executor)
    # Update LLM client in case it wasn't available before
    if _orchestrator.llm_client is None:
        _orchestrator.llm_client = get_llm_client()
    return _orchestrator

# Register all agent executors
ALL_EXECUTORS = {
    **STRATEGIC_EXECUTORS,
    **STORY_SYSTEM_EXECUTORS,
    **STRUCTURAL_EXECUTORS,
    **VALIDATION_EXECUTORS,
}


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
        "llm_enabled": get_llm_client() is not None
    }


@app.get("/api/system/llm-status")
async def llm_status(auth: bool = Depends(require_auth)):
    """Check LLM configuration status."""
    client = get_llm_client()
    if client is None:
        # Also check if env var exists but client creation failed
        has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
        return {
            "enabled": False,
            "model": None,
            "has_env_var": has_key,
            "message": "No ANTHROPIC_API_KEY configured. Running in demo mode with placeholder responses." if not has_key else "API key found but client initialization failed."
        }
    return {
        "enabled": True,
        "model": client.model,
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

    project = get_orchestrator().create_project(request.title, constraints)

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
    for pid, project in get_orchestrator().projects.items():
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
    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return get_orchestrator().get_project_status(project)


@app.get("/api/projects/{project_id}/available-agents")
async def get_available_agents(project_id: str, auth: bool = Depends(require_auth)):
    """Get agents ready to execute."""
    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    available = get_orchestrator().get_available_agents(project)

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
    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if agent_id not in AGENT_REGISTRY:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {agent_id}")

    available = get_orchestrator().get_available_agents(project)
    if agent_id not in available:
        raise HTTPException(status_code=400, detail=f"Agent {agent_id} is not available (dependencies not met)")

    try:
        output = await get_orchestrator().execute_agent(project, agent_id)
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
    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    results = []
    available = get_orchestrator().get_available_agents(project)

    for agent_id in available:
        agent_def = AGENT_REGISTRY.get(agent_id)
        if agent_def and agent_def.layer == layer_id:
            try:
                output = await get_orchestrator().execute_agent(project, agent_id)
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
    project = get_orchestrator().get_project(project_id)
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
    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return get_orchestrator().export_manuscript(project)


@app.post("/api/projects/{project_id}/checkpoint")
async def save_checkpoint(project_id: str, name: str = "checkpoint", auth: bool = Depends(require_auth)):
    """Save a project checkpoint."""
    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.save_checkpoint(name)
    return {"success": True, "checkpoint": name, "total_checkpoints": len(project.checkpoints)}


@app.get("/api/projects/{project_id}/export")
async def export_project(project_id: str, auth: bool = Depends(require_auth)):
    """Export full project state as JSON for saving."""
    project = get_orchestrator().get_project(project_id)
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
    project = get_orchestrator().create_project(data.title, data.user_constraints)

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
    get_orchestrator().projects[data.project_id] = project

    return {
        "success": True,
        "project_id": project.project_id,
        "title": project.title,
        "message": "Project imported successfully"
    }


# =============================================================================
# Chapter Writing
# =============================================================================

class ChapterWriteRequest(BaseModel):
    """Request model for chapter writing."""
    quick_mode: bool = False  # If True, write shorter preview chapters


@app.post("/api/projects/{project_id}/write-chapter/{chapter_number}")
async def write_chapter(
    project_id: str,
    chapter_number: int,
    request: Optional[ChapterWriteRequest] = None,
    auth: bool = Depends(require_auth)
):
    """Write a specific chapter using the chapter writer agent."""
    from core.orchestrator import ExecutionContext

    quick_mode = request.quick_mode if request else False

    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if chapter blueprint exists
    chapter_blueprint = None
    for layer in project.layers.values():
        if "chapter_blueprint" in layer.agents:
            agent_state = layer.agents["chapter_blueprint"]
            if agent_state.current_output:
                chapter_blueprint = agent_state.current_output.content
                break

    if not chapter_blueprint:
        raise HTTPException(
            status_code=400,
            detail="Chapter blueprint not yet generated. Run pipeline through layer 10 first."
        )

    # Build execution context with all inputs
    inputs = {"chapter_blueprint": chapter_blueprint}

    # Gather all previous agent outputs as inputs
    for layer in project.layers.values():
        for agent_id, agent_state in layer.agents.items():
            if agent_state.current_output:
                inputs[agent_id] = agent_state.current_output.content

    context = ExecutionContext(
        project=project,
        inputs=inputs,
        llm_client=get_llm_client()
    )

    try:
        result = await execute_chapter_writer(context, chapter_number, quick_mode=quick_mode)

        # Store chapter in manuscript
        if result.get("text") and not result.get("error"):
            if "chapters" not in project.manuscript:
                project.manuscript["chapters"] = []

            # Update or add chapter
            chapter_exists = False
            for i, ch in enumerate(project.manuscript["chapters"]):
                if ch.get("number") == chapter_number:
                    project.manuscript["chapters"][i] = result
                    chapter_exists = True
                    break

            if not chapter_exists:
                project.manuscript["chapters"].append(result)

            # Sort chapters by number
            project.manuscript["chapters"].sort(key=lambda x: x.get("number", 0))

        return {
            "success": True,
            "chapter": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BatchWriteRequest(BaseModel):
    """Request model for batch chapter writing."""
    timeout_seconds: int = 8  # Stop before Vercel's 10s limit
    max_chapters: int = 1     # How many chapters to attempt
    quick_mode: bool = True   # Use quick mode by default for Vercel (shorter chapters)


@app.post("/api/projects/{project_id}/write-chapters-batch")
async def write_chapters_batch(project_id: str, request: BatchWriteRequest, auth: bool = Depends(require_auth)):
    """
    Write chapters with timeout awareness.
    Stops before timeout and returns progress so frontend can resume.
    """
    import time
    from core.orchestrator import ExecutionContext

    start_time = time.time()
    timeout = request.timeout_seconds

    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get chapter blueprint
    chapter_blueprint = None
    for layer in project.layers.values():
        if "chapter_blueprint" in layer.agents:
            agent_state = layer.agents["chapter_blueprint"]
            if agent_state.current_output:
                chapter_blueprint = agent_state.current_output.content
                break

    if not chapter_blueprint:
        return {
            "success": False,
            "error": "Chapter blueprint not yet generated",
            "chapters_written": [],
            "chapters_remaining": [],
            "should_continue": False
        }

    # Get chapter outline
    chapter_outline = chapter_blueprint.get("chapter_outline", [])
    if not chapter_outline:
        return {
            "success": False,
            "error": "No chapters in blueprint",
            "chapters_written": [],
            "chapters_remaining": [],
            "should_continue": False
        }

    # Find which chapters are already written
    existing_chapters = {ch.get("number") for ch in project.manuscript.get("chapters", [])}
    chapters_to_write = [ch for ch in chapter_outline if ch.get("number") not in existing_chapters]

    if not chapters_to_write:
        return {
            "success": True,
            "message": "All chapters already written",
            "chapters_written": list(existing_chapters),
            "chapters_remaining": [],
            "should_continue": False
        }

    # Build inputs for chapter writing
    inputs = {"chapter_blueprint": chapter_blueprint}
    for layer in project.layers.values():
        for agent_id, agent_state in layer.agents.items():
            if agent_state.current_output:
                inputs[agent_id] = agent_state.current_output.content

    context = ExecutionContext(
        project=project,
        inputs=inputs,
        llm_client=get_llm_client()
    )

    chapters_written = []
    chapters_failed = []

    # Write chapters until timeout approaches
    for i, ch in enumerate(chapters_to_write[:request.max_chapters]):
        elapsed = time.time() - start_time

        # Stop if we're approaching timeout (leave 2 seconds buffer)
        if elapsed > (timeout - 2):
            break

        chapter_num = ch.get("number")
        try:
            result = await execute_chapter_writer(context, chapter_num, quick_mode=request.quick_mode)

            if result.get("text") and not result.get("error"):
                # Store chapter
                if "chapters" not in project.manuscript:
                    project.manuscript["chapters"] = []

                chapter_exists = False
                for idx, existing_ch in enumerate(project.manuscript["chapters"]):
                    if existing_ch.get("number") == chapter_num:
                        project.manuscript["chapters"][idx] = result
                        chapter_exists = True
                        break

                if not chapter_exists:
                    project.manuscript["chapters"].append(result)

                project.manuscript["chapters"].sort(key=lambda x: x.get("number", 0))
                chapters_written.append(chapter_num)
            else:
                chapters_failed.append({"number": chapter_num, "error": result.get("error", "Unknown error")})

        except Exception as e:
            chapters_failed.append({"number": chapter_num, "error": str(e)})

    # Calculate remaining chapters
    all_written = existing_chapters.union(set(chapters_written))
    remaining = [ch.get("number") for ch in chapter_outline if ch.get("number") not in all_written]

    return {
        "success": True,
        "chapters_written": chapters_written,
        "chapters_failed": chapters_failed,
        "chapters_remaining": remaining,
        "total_chapters": len(chapter_outline),
        "completed_count": len(all_written),
        "should_continue": len(remaining) > 0,
        "elapsed_seconds": time.time() - start_time
    }


@app.get("/api/projects/{project_id}/chapters")
async def list_chapters(project_id: str, auth: bool = Depends(require_auth)):
    """List all written chapters for a project."""
    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chapters = project.manuscript.get("chapters", [])

    return {
        "total_chapters": len(chapters),
        "chapters": [
            {
                "number": ch.get("number"),
                "title": ch.get("title"),
                "word_count": ch.get("word_count", 0),
                "has_text": bool(ch.get("text"))
            }
            for ch in chapters
        ]
    }


@app.get("/api/projects/{project_id}/chapters/{chapter_number}")
async def get_chapter(project_id: str, chapter_number: int, auth: bool = Depends(require_auth)):
    """Get a specific written chapter."""
    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chapters = project.manuscript.get("chapters", [])
    for ch in chapters:
        if ch.get("number") == chapter_number:
            return ch

    raise HTTPException(status_code=404, detail=f"Chapter {chapter_number} not found")


# =============================================================================
# Export Endpoints
# =============================================================================

@app.get("/api/projects/{project_id}/export/outline")
async def export_outline(project_id: str, auth: bool = Depends(require_auth)):
    """Export project as structured markdown outline."""
    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    markdown = generate_outline_markdown(project)

    return {
        "format": "markdown",
        "filename": f"{project.title.replace(' ', '_')}_Outline.md",
        "content": markdown
    }


@app.get("/api/projects/{project_id}/export/manuscript")
async def export_full_manuscript(project_id: str, auth: bool = Depends(require_auth)):
    """Export full manuscript as markdown."""
    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    markdown = generate_manuscript_markdown(project)

    return {
        "format": "markdown",
        "filename": f"{project.title.replace(' ', '_')}_Manuscript.md",
        "content": markdown
    }


@app.get("/api/projects/{project_id}/export/docx")
async def export_docx(project_id: str, include_outline: bool = False, auth: bool = Depends(require_auth)):
    """Export manuscript as Word document (.docx)."""
    from core.export import generate_docx

    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        docx_bytes = generate_docx(project, include_outline=include_outline)
        filename = f"{project.title.replace(' ', '_')}.docx"

        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="python-docx not installed. Please install it with: pip install python-docx"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Word document: {str(e)}")


@app.get("/api/projects/{project_id}/export/epub")
async def export_epub(project_id: str, auth: bool = Depends(require_auth)):
    """Export manuscript as EPUB for Kindle/eReaders."""
    from core.export import generate_epub

    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        epub_bytes = generate_epub(project)
        filename = f"{project.title.replace(' ', '_')}.epub"

        return StreamingResponse(
            io.BytesIO(epub_bytes),
            media_type="application/epub+zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="ebooklib not installed. Please install it with: pip install ebooklib"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate EPUB: {str(e)}")


@app.get("/api/projects/{project_id}/stats")
async def get_project_stats(project_id: str, auth: bool = Depends(require_auth)):
    """Get project statistics including word count and chapter status."""
    from core.export import get_word_count, get_chapter_summary

    project = get_orchestrator().get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chapters = get_chapter_summary(project)
    total_words = get_word_count(project)
    target_words = project.user_constraints.get('target_word_count', 80000)

    return {
        "title": project.title,
        "total_chapters": len(chapters),
        "written_chapters": sum(1 for ch in chapters if ch['written']),
        "total_words": total_words,
        "target_words": target_words,
        "progress_percent": round((total_words / target_words) * 100, 1) if target_words > 0 else 0,
        "chapters": chapters
    }


def generate_outline_markdown(project) -> str:
    """Generate a comprehensive markdown outline from project data."""
    lines = []

    # Title and metadata
    lines.append(f"# {project.title}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # User constraints
    constraints = project.user_constraints
    lines.append("## Project Overview")
    lines.append("")
    lines.append(f"**Genre:** {constraints.get('genre', 'N/A')}")
    lines.append(f"**Target Word Count:** {constraints.get('target_word_count', 'N/A'):,}")
    lines.append(f"**Target Audience:** {constraints.get('target_audience', 'N/A')}")
    lines.append("")

    if constraints.get('description'):
        lines.append("### Description")
        lines.append(constraints['description'])
        lines.append("")

    if constraints.get('themes'):
        lines.append("### Themes")
        for theme in constraints['themes']:
            lines.append(f"- {theme}")
        lines.append("")

    if constraints.get('comparable_titles'):
        lines.append("### Comparable Titles")
        for title in constraints['comparable_titles']:
            lines.append(f"- {title}")
        lines.append("")

    # Get agent outputs
    outputs = {}
    for layer in project.layers.values():
        for agent_id, agent_state in layer.agents.items():
            if agent_state.current_output:
                outputs[agent_id] = agent_state.current_output.content

    # Market Intelligence
    if "market_intelligence" in outputs:
        mi = outputs["market_intelligence"]
        lines.append("---")
        lines.append("")
        lines.append("## Market Intelligence")
        lines.append("")

        if mi.get("reader_avatar"):
            ra = mi["reader_avatar"]
            lines.append("### Target Reader")
            lines.append(f"**Demographics:** {ra.get('demographics', 'N/A')}")
            lines.append("")
            lines.append(f"**Psychographics:** {ra.get('psychographics', 'N/A')}")
            lines.append("")
            if ra.get("problems_to_solve"):
                lines.append("**Problems to Solve:**")
                for prob in ra["problems_to_solve"]:
                    lines.append(f"- {prob}")
            lines.append("")

        if mi.get("market_gap"):
            mg = mi["market_gap"]
            lines.append("### Market Gap")
            lines.append(f"**Unmet Need:** {mg.get('unmet_need', 'N/A')}")
            lines.append("")

        if mi.get("positioning_angle"):
            pa = mi["positioning_angle"]
            lines.append("### Positioning")
            lines.append(f"**Unique Value:** {pa.get('unique_value', 'N/A')}")
            lines.append("")
            if pa.get("differentiators"):
                lines.append("**Differentiators:**")
                for diff in pa["differentiators"]:
                    lines.append(f"- {diff}")
            lines.append("")

    # Core Concept
    if "concept_definition" in outputs:
        cd = outputs["concept_definition"]
        lines.append("---")
        lines.append("")
        lines.append("## Core Concept")
        lines.append("")
        lines.append(f"### One-Line Hook")
        lines.append(f"> {cd.get('one_line_hook', 'N/A')}")
        lines.append("")

        if cd.get("core_promise"):
            cp = cd["core_promise"]
            lines.append("### Core Promise")
            lines.append(f"**Transformation:** {cp.get('transformation', 'N/A')}")
            lines.append("")
            lines.append(f"**Emotional Payoff:** {cp.get('emotional_payoff', 'N/A')}")
            lines.append("")

        if cd.get("elevator_pitch"):
            lines.append("### Elevator Pitch")
            lines.append(cd["elevator_pitch"])
            lines.append("")

    # Thematic Architecture
    if "thematic_architecture" in outputs:
        ta = outputs["thematic_architecture"]
        lines.append("---")
        lines.append("")
        lines.append("## Thematic Architecture")
        lines.append("")

        if ta.get("primary_theme"):
            pt = ta["primary_theme"]
            lines.append("### Primary Theme")
            lines.append(f"> {pt.get('statement', 'N/A')}")
            lines.append("")
            lines.append(f"**Universal Truth:** {pt.get('universal_truth', 'N/A')}")
            lines.append("")

        if ta.get("counter_theme"):
            ct = ta["counter_theme"]
            lines.append("### Counter-Theme")
            lines.append(f"> {ct.get('statement', 'N/A')}")
            lines.append("")

        if ta.get("thematic_question"):
            lines.append("### Thematic Question")
            lines.append(f"*{ta['thematic_question']}*")
            lines.append("")

    # Story Question & Stakes
    if "story_question" in outputs:
        sq = outputs["story_question"]
        lines.append("---")
        lines.append("")
        lines.append("## Central Story Question")
        lines.append("")
        lines.append(f"> {sq.get('central_dramatic_question', 'N/A')}")
        lines.append("")

        if sq.get("stakes_ladder"):
            sl = sq["stakes_ladder"]
            lines.append("### Stakes Ladder")
            for level, data in sl.items():
                if isinstance(data, dict):
                    lines.append(f"**{level.replace('_', ' ').title()}:** {data.get('risk', 'N/A')} → {data.get('consequence', 'N/A')}")
            lines.append("")

    # Characters
    if "character_architecture" in outputs:
        ca = outputs["character_architecture"]
        lines.append("---")
        lines.append("")
        lines.append("## Character Architecture")
        lines.append("")

        if ca.get("protagonist_profile"):
            pp = ca["protagonist_profile"]
            lines.append("### Protagonist")
            lines.append(f"**Name:** {pp.get('name', 'N/A')}")
            lines.append(f"**Role:** {pp.get('role', 'N/A')}")
            lines.append("")
            if pp.get("traits"):
                lines.append(f"**Traits:** {', '.join(pp['traits'])}")
            lines.append("")
            lines.append(f"**Wound:** {pp.get('backstory_wound', 'N/A')}")
            lines.append("")

        if ca.get("protagonist_arc"):
            pa = ca["protagonist_arc"]
            lines.append("### Character Arc")
            lines.append(f"**Starting State:** {pa.get('starting_state', 'N/A')}")
            lines.append("")
            lines.append(f"**Transformation:** {pa.get('transformation', 'N/A')}")
            lines.append("")
            lines.append(f"**Ending State:** {pa.get('ending_state', 'N/A')}")
            lines.append("")

        if ca.get("want_vs_need"):
            wvn = ca["want_vs_need"]
            lines.append("### Want vs Need")
            lines.append(f"**Want:** {wvn.get('want', 'N/A')}")
            lines.append("")
            lines.append(f"**Need:** {wvn.get('need', 'N/A')}")
            lines.append("")

        if ca.get("antagonist_profile"):
            ap = ca["antagonist_profile"]
            lines.append("### Antagonist")
            lines.append(f"**Name:** {ap.get('name', 'N/A')}")
            lines.append(f"**Role:** {ap.get('role', 'N/A')}")
            lines.append("")
            lines.append(f"**Worldview:** {ap.get('worldview', 'N/A')}")
            lines.append("")

        if ca.get("supporting_cast"):
            lines.append("### Supporting Cast")
            for char in ca["supporting_cast"]:
                lines.append(f"- **{char.get('name', '?')}:** {char.get('function', 'N/A')}")
            lines.append("")

    # Plot Structure
    if "plot_structure" in outputs:
        ps = outputs["plot_structure"]
        lines.append("---")
        lines.append("")
        lines.append("## Plot Structure")
        lines.append("")

        if ps.get("act_structure"):
            lines.append("### Three-Act Structure")
            for act_name, act_data in ps["act_structure"].items():
                if isinstance(act_data, dict):
                    lines.append(f"**{act_name.replace('_', ' ').title()}** ({act_data.get('percentage', '?')}%)")
                    lines.append(f"*Purpose:* {act_data.get('purpose', 'N/A')}")
                    if act_data.get("key_events"):
                        for event in act_data["key_events"]:
                            lines.append(f"  - {event}")
                    lines.append("")

        if ps.get("major_beats"):
            lines.append("### Major Beats")
            for beat in ps["major_beats"]:
                lines.append(f"- **{beat.get('name', '?')}:** {beat.get('description', 'N/A')}")
            lines.append("")

        if ps.get("climax_design"):
            cd = ps["climax_design"]
            lines.append("### Climax Design")
            lines.append(f"**Setup:** {cd.get('setup', 'N/A')}")
            lines.append(f"**Confrontation:** {cd.get('confrontation', 'N/A')}")
            lines.append(f"**Resolution:** {cd.get('resolution', 'N/A')}")
            lines.append("")

    # Chapter Blueprint
    if "chapter_blueprint" in outputs:
        cb = outputs["chapter_blueprint"]
        lines.append("---")
        lines.append("")
        lines.append("## Chapter Outline")
        lines.append("")

        chapter_outline = cb.get("chapter_outline", [])
        for chapter in chapter_outline:
            ch_num = chapter.get("number", "?")
            ch_title = chapter.get("title", f"Chapter {ch_num}")
            lines.append(f"### Chapter {ch_num}: {ch_title}")
            lines.append("")
            lines.append(f"**Act:** {chapter.get('act', '?')} | **POV:** {chapter.get('pov', '?')} | **Words:** ~{chapter.get('word_target', 3000):,}")
            lines.append("")
            lines.append(f"**Goal:** {chapter.get('chapter_goal', 'N/A')}")
            lines.append("")
            lines.append(f"**Opening Hook:** *{chapter.get('opening_hook', 'N/A')}*")
            lines.append("")

            if chapter.get("scenes"):
                lines.append("**Scenes:**")
                for scene in chapter["scenes"]:
                    lines.append(f"  {scene.get('scene_number', '?')}. {scene.get('scene_question', 'N/A')}")
                    lines.append(f"     - Location: {scene.get('location', '?')} | Conflict: {scene.get('conflict_type', '?')}")
                lines.append("")

            lines.append(f"**Closing Hook:** *{chapter.get('closing_hook', 'N/A')}*")
            lines.append("")

    # Voice Specification
    if "voice_specification" in outputs:
        vs = outputs["voice_specification"]
        lines.append("---")
        lines.append("")
        lines.append("## Voice & Style Guide")
        lines.append("")

        if vs.get("narrative_voice"):
            nv = vs["narrative_voice"]
            lines.append("### Narrative Voice")
            lines.append(f"**POV Type:** {nv.get('pov_type', 'N/A')}")
            lines.append(f"**Distance:** {nv.get('distance', 'N/A')}")
            lines.append(f"**Tone:** {nv.get('tone', 'N/A')}")
            lines.append("")

        if vs.get("style_guide"):
            sg = vs["style_guide"]
            if sg.get("dos"):
                lines.append("### Do")
                for do in sg["dos"]:
                    lines.append(f"- {do}")
                lines.append("")
            if sg.get("donts"):
                lines.append("### Don't")
                for dont in sg["donts"]:
                    lines.append(f"- {dont}")
                lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"*Generated by Million Dollar Book Machine*")
    lines.append(f"*Project ID: {project.project_id}*")

    return "\n".join(lines)


def generate_manuscript_markdown(project) -> str:
    """Generate full manuscript markdown from written chapters."""
    lines = []

    lines.append(f"# {project.title}")
    lines.append("")
    lines.append("---")
    lines.append("")

    chapters = project.manuscript.get("chapters", [])

    if not chapters:
        lines.append("*No chapters have been written yet.*")
        lines.append("")
        lines.append("Use the chapter writer to generate chapters from the outline.")
    else:
        total_words = sum(ch.get("word_count", 0) for ch in chapters)
        lines.append(f"**Total Chapters:** {len(chapters)} | **Total Words:** {total_words:,}")
        lines.append("")
        lines.append("---")
        lines.append("")

        for chapter in sorted(chapters, key=lambda x: x.get("number", 0)):
            ch_num = chapter.get("number", "?")
            ch_title = chapter.get("title", f"Chapter {ch_num}")

            lines.append(f"## Chapter {ch_num}: {ch_title}")
            lines.append("")

            if chapter.get("text"):
                lines.append(chapter["text"])
            else:
                lines.append("*Chapter not yet written.*")

            lines.append("")
            lines.append("---")
            lines.append("")

    lines.append(f"*{project.title}*")
    lines.append(f"*Generated by Million Dollar Book Machine*")

    return "\n".join(lines)
