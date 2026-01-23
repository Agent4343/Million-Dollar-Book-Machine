# CLAUDE.md - AI Assistant Guide for Million Dollar Book Machine

## Project Overview

Million Dollar Book Machine is an AI-powered multi-agent system for developing books from concept to publication-ready manuscript. It uses **21 specialized agents** orchestrated across **21 development layers** to guide a book from idea to publishing package.

## Quick Reference

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn api.index:app --reload --port 3000

# Deploy to Vercel
vercel
```

**Default Password**: `Blake2011@` (configurable via `APP_PASSWORD` env var)

## Project Structure

```
Million-Dollar-Book-Machine/
├── api/
│   └── index.py              # FastAPI REST endpoints (~600 lines)
├── core/
│   ├── orchestrator.py       # Central pipeline controller (~455 lines)
│   ├── llm.py                # Claude API client wrapper (~212 lines)
│   └── export.py             # Document export (DOCX, EPUB, Markdown)
├── models/
│   ├── state.py              # Data classes: BookProject, LayerState, AgentState
│   └── agents.py             # Agent definitions registry (~513 lines)
├── agents/
│   ├── strategic.py          # Layers 0-4: Strategy & concept agents
│   ├── story_system.py       # Layers 5-7: Story world & characters
│   ├── structural.py         # Layers 8-12: Plot & structure agents
│   ├── validation.py         # Layers 13-20: QA & publishing agents
│   └── chapter_writer.py     # Draft chapter generation with timeout handling
├── public/
│   └── index.html            # Single-page web UI (~1585 lines)
├── requirements.txt          # Python dependencies
├── vercel.json               # Vercel deployment config (60s timeout)
└── .env.example              # Environment variable template
```

## Key Files to Know

| File | Purpose | When to Modify |
|------|---------|----------------|
| `models/agents.py` | Agent definitions with inputs/outputs/gates | Adding/modifying agents |
| `models/state.py` | Data structures, layer definitions | Changing state schema |
| `core/orchestrator.py` | Pipeline control, agent execution | Changing orchestration logic |
| `core/llm.py` | Claude API integration | Changing LLM behavior |
| `api/index.py` | REST API endpoints | Adding API endpoints |
| `agents/*.py` | Agent execution prompts | Modifying agent behavior |
| `public/index.html` | Web interface | UI changes |

## Architecture Concepts

### Agents
Each agent has:
- **agent_id**: Unique snake_case identifier (e.g., `market_intelligence`)
- **layer**: Development stage (0-20)
- **inputs**: Required outputs from previous agents
- **outputs**: What it produces
- **gate_criteria**: What must be true to pass
- **fail_condition**: What causes rejection
- **dependencies**: Agent IDs that must complete first

### Layers
- Layers 0-4: Strategic Foundation (concept, market, themes)
- Layers 5-7: Story System Design (world, characters, relationships)
- Layers 8-12: Structural Engine (plot, pacing, chapters, voice, drafts)
- Layers 13-20: Quality Control (validation, legal, editing, publishing)

### State Flow
```
PENDING → RUNNING → PASSED/FAILED
LOCKED → AVAILABLE → IN_PROGRESS → COMPLETED
```

### Gate System
- Every agent must pass gate validation to proceed
- Failed gates trigger retries (max 3 attempts)
- Gates are validated in `core/orchestrator.py:_validate_gate()`

## Code Conventions

### Naming
- **Agent IDs**: snake_case (`market_intelligence`, `plot_structure`)
- **Classes**: PascalCase (`BookProject`, `AgentState`)
- **Functions**: snake_case (`execute_agent`, `gather_inputs`)
- **Constants**: UPPERCASE (`AGENT_REGISTRY`, `LAYERS`)

### Async Pattern
All agent executors and orchestrator methods are async:
```python
async def execute_market_intelligence(project: BookProject, inputs: dict) -> dict:
    # Agent implementation
    pass
```

### Data Validation
Pydantic is used for all data models in `models/state.py`:
```python
@dataclass
class AgentOutput:
    agent_id: str
    output: dict
    raw_response: str
    timestamp: str
```

## Important Constraints

### Vercel Deployment
- **60-second function timeout** configured in `vercel.json`
- Chapter writing uses timeout-aware logic with auto-resume
- Lazy initialization of LLM client for environment variables

### Demo Mode
- System runs without API key using placeholder responses
- Check `core/llm.py` for demo mode behavior
- Useful for testing UI without API costs

### Authentication
- Session-based with HMAC token cookies
- Auth middleware in `api/index.py`
- All `/api/projects/*` endpoints require auth

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `ANTHROPIC_API_KEY` | For AI | None | Claude API key |
| `APP_PASSWORD` | No | `Blake2011@` | Login password |
| `SESSION_SECRET` | No | Auto-generated | Session signing |

## Common Development Tasks

### Adding a New Agent

1. Define in `models/agents.py`:
```python
"new_agent": AgentDefinition(
    agent_id="new_agent",
    name="New Agent",
    layer=X,
    agent_type=AgentType.CREATIVE,
    purpose="What it does",
    inputs=["required_input_from_other_agent"],
    outputs=["what_it_produces"],
    gate_criteria="What must be true to pass",
    fail_condition="What causes rejection",
    dependencies=["previous_agent_id"]
)
```

2. Add executor function in appropriate `agents/*.py` file
3. Register in orchestrator's agent dispatch

### Modifying Agent Prompts

Agent prompts are in `agents/*.py` files. Each executor follows this pattern:
```python
async def execute_agent_name(project: BookProject, inputs: dict) -> dict:
    prompt = f"""Based on: {inputs}

    Generate: [specific output requirements]

    Return as JSON: {{ "key": "value" }}
    """

    result = await llm_client.generate(prompt)
    return result
```

### Adding API Endpoints

Add to `api/index.py`:
```python
@app.get("/api/new-endpoint")
async def new_endpoint(user = Depends(require_auth)):
    return {"data": "value"}
```

### Modifying the Web UI

The UI is a single file at `public/index.html` with:
- Vanilla JavaScript (no frameworks)
- CSS Grid/Flexbox layout
- Fetch API for HTTP requests
- Real-time status polling

## Testing

No formal test suite exists. Validation happens through:
- Gate system for agent outputs
- Manual API testing
- Demo mode for UI testing

## API Endpoint Reference

### Core Endpoints
- `POST /api/auth/login` - Authenticate
- `POST /api/projects` - Create project
- `GET /api/projects/{id}` - Get project status
- `POST /api/projects/{id}/execute/{agent}` - Run agent
- `GET /api/projects/{id}/manuscript` - Export manuscript

### System Endpoints
- `GET /api/system/agents` - List all agents
- `GET /api/system/layers` - List all layers
- `GET /api/system/llm-status` - Check Claude API status

## Debugging Tips

1. **Check LLM status**: `GET /api/system/llm-status`
2. **View agent output**: `GET /api/projects/{id}/agent/{agent}/output`
3. **Check available agents**: `GET /api/projects/{id}/available-agents`
4. **Demo mode active?**: Look for `"enabled": false` in LLM status

## Git Workflow

- Feature branches: `claude/feature-name-*`
- Commit messages: Descriptive, imperative mood
- Push to feature branch, create PR to main

## Model Information

- **LLM**: Claude claude-sonnet-4-20250514 (`claude-sonnet-4-20250514`)
- **Max tokens**: 16,000 per request
- **JSON repair**: Handles truncated responses gracefully
