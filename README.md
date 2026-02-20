# Million Dollar Book Machine

AI-powered multi-agent system for developing books from concept to publication.

## System Overview

This system uses **27 specialized agents** across **21 development layers** to take a book from initial concept through to publication-ready manuscript.

### Development Layers

| Layer | Name | Agents |
|-------|------|--------|
| 0 | Orchestration & State Control | orchestrator |
| 1 | Market & Reader Intelligence | market_intelligence |
| 2 | Core Concept Definition | concept_definition |
| 3 | Thematic Architecture | thematic_architecture |
| 4 | Central Story Question | story_question |
| 5 | World / Context Rules | world_rules |
| 6 | Character Architecture | character_architecture |
| 7 | Relationship Dynamics | relationship_dynamics |
| 8 | Macro Plot Structure | plot_structure |
| 9 | Pacing & Tension Design | pacing_design |
| 10 | Chapter & Scene Blueprint | chapter_blueprint |
| 11 | Style & Voice Specification | voice_specification |
| 12 | Draft Generation | draft_generation |
| 13 | Continuity & Logic Audit | continuity_audit |
| 14 | Emotional Impact Validation | emotional_validation |
| 15 | Originality & Legal Safety | originality_scan, plagiarism_audit, transformative_verification |
| 16 | Rewrite & Revalidation | structural_rewrite, post_rewrite_scan |
| 17 | Line & Copy Edit | line_edit |
| 18 | Beta Reader Simulation | beta_simulation |
| 19 | Final Quality Validation | human_editor_review, final_validation, production_readiness |
| 20 | Publishing Package | publishing_package, final_proof, kdp_readiness, ip_clearance |

### How It Works

1. **Create a project** with your book idea, genre, and constraints
2. **Agents execute in order**, each with gate criteria to pass
3. **Each layer unlocks the next** when all agents pass their gates
4. **Final output**: Publication-ready manuscript with blurb, metadata, and legal clearance

### Gate System

Every agent has:
- **Gate Criteria**: What must be true to pass
- **Fail Condition**: What causes rejection and retry

Failed gates trigger retries (up to 3 attempts) or block progress until resolved.

## Quick Start

### Local Development

```bash
pip install -r requirements.txt
uvicorn api.index:app --reload --port 3000
```

### Deploy to Vercel

```bash
vercel
```

Password: Set the `APP_PASSWORD` environment variable before starting (an auto-generated password is printed to the log if unset).

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with password
- `POST /api/auth/logout` - Logout
- `GET /api/auth/check` - Check auth status

### System
- `GET /api/system/agents` - List all agents
- `GET /api/system/layers` - List all layers
- `GET /api/system/llm-status` - Check Claude API configuration

### Projects
- `POST /api/projects` - Create new project
- `GET /api/projects` - List all projects
- `GET /api/projects/{id}` - Get project details
- `GET /api/projects/{id}/available-agents` - Get agents ready to run
- `GET /api/projects/{id}/debug/availability` - Diagnose why a project is blocked (unmet deps, locked layers)
- `POST /api/projects/{id}/execute/{agent}` - Run specific agent
- `POST /api/projects/{id}/agents/{agent}/reset` - Reset a failed agent back to PENDING
- `GET /api/projects/{id}/agent/{agent}/output` - Get agent output
- `GET /api/projects/{id}/manuscript` - Export manuscript

## Project Structure

```
Million-Dollar-Book-Machine/
├── api/
│   └── index.py              # FastAPI endpoints
├── core/
│   ├── orchestrator.py       # Central orchestrator
│   └── llm.py                # Claude API client
├── agents/
│   ├── strategic.py          # Layers 1-4 agents
│   ├── story_system.py       # Layers 5-7 agents
│   ├── structural.py         # Layers 8-12 agents
│   └── validation.py         # Layers 13-20 agents
├── models/
│   ├── state.py              # State management
│   └── agents.py             # Agent definitions
├── public/
│   └── index.html            # Web interface
├── requirements.txt
├── vercel.json
└── README.md
```

## Agent Details

### Strategic Foundation (Layers 1-4)

**Market Intelligence**: Analyzes market, defines reader avatar, identifies gaps
**Concept Definition**: Creates one-line hook, core promise, unique engine
**Thematic Architecture**: Designs theme, counter-theme, value conflicts
**Story Question**: Defines central dramatic question and stakes ladder

### Story System Design (Layers 5-7)

**World Rules**: Physical, social, and power rules of the story world
**Character Architecture**: Protagonist arc, antagonist, supporting cast
**Relationship Dynamics**: Conflict web, power shifts, dependencies

### Structural Engine (Layers 8-12)

**Plot Structure**: Act structure, beats, reversals, climax design
**Pacing Design**: Tension curve, scene density, breather points
**Chapter Blueprint**: Detailed chapter-by-chapter outline with scenes
**Voice Specification**: Narrative voice, POV rules, style guide
**Draft Generation**: Produces actual manuscript chapters

### Quality Control (Layers 13-20)

**Continuity Audit**: Timeline, character logic, world rule compliance
**Emotional Validation**: Arc fulfillment, emotional peak verification
**Originality Scan**: Structural similarity, phrase recurrence checks
**Plagiarism Audit**: Legal risk assessment
**Transformative Verification**: Legal defensibility check
**Structural Rewrite**: Prose improvement, flag resolution
**Post-Rewrite Scan**: Re-validates quality after rewrite
**Line Edit**: Grammar, rhythm, editorial polish
**Beta Simulation**: Simulated reader response, engagement analysis
**Human Editor Review**: AI-simulated senior editor assessment with editorial letter
**Final Validation**: Core promise fulfillment check
**Production Readiness**: QA release checklist and blocker identification
**Publishing Package**: Blurb, synopsis, metadata, keywords
**Final Proof**: Full-manuscript copy check and consistency scan
**KDP Readiness**: Validates EPUB/DOCX exports for Kindle publishing
**IP Clearance**: Title and naming safety verification

## Claude API Configuration

The system uses the **Anthropic Claude API** for content generation.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required for AI generation |
| `APP_PASSWORD` | Login password | Auto-generated (printed to log) |
| `SESSION_SECRET` | Session signing secret | Auto-generated |

### Local Development

```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Install and run
pip install -r requirements.txt
uvicorn api.index:app --reload --port 3000
```

### Vercel Deployment

1. Deploy to Vercel:
```bash
vercel
```

2. Add environment variable in Vercel dashboard:
   - Go to Project Settings → Environment Variables
   - Add `ANTHROPIC_API_KEY` with your API key

### Demo Mode

Without an API key, the system runs in **demo mode** with placeholder responses. This lets you explore the UI and pipeline without API costs.

### Check LLM Status

After login, check `/api/system/llm-status` to verify Claude is configured:
```json
{
  "enabled": true,
  "model": "claude-sonnet-4-20250514",
  "message": "Claude API configured and ready"
}
```

## License

MIT

## Railway Deployment

1. Connect your GitHub repository to [Railway](https://railway.app)
2. Add environment variables in the Railway dashboard:
   - `ANTHROPIC_API_KEY` — your Anthropic API key
   - `APP_PASSWORD` — your chosen login password
   - `SESSION_SECRET` — a stable random secret (e.g. `openssl rand -hex 32`)
3. Railway will auto-detect the `Procfile` and deploy

## Debugging a Blocked Project

If a pipeline job ends with status `blocked`, the job record's `progress.blocked_reason` field contains a
full diagnostic payload.  You can also query the debug endpoint directly:

```bash
# 1. Login and capture the session cookie
curl -c cookies.txt -X POST https://your-app/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"password": "YOUR_APP_PASSWORD"}'

# 2. List your projects
curl -b cookies.txt https://your-app/api/projects

# 3. Get project status
curl -b cookies.txt https://your-app/api/projects/<project_id>

# 4. See which agents are ready to run
curl -b cookies.txt https://your-app/api/projects/<project_id>/available-agents

# 5. Debug why the project is blocked (unmet dependencies, locked layers)
curl -b cookies.txt https://your-app/api/projects/<project_id>/debug/availability

# 6. Reset a failed agent so it can be retried
curl -b cookies.txt -X POST https://your-app/api/projects/<project_id>/agents/<agent_id>/reset
```

The debug endpoint returns:
- **`available_agents`** – agents that can run right now (should be empty when blocked)
- **`blocked_candidates`** – PENDING agents with at least one dependency not yet PASSED, including which dep and its current status
- **`locked_layer_reasons`** – locked layers with the list of agents in the preceding layer that haven't passed yet
- **`agent_status_counts`** – summary counts across all agents by status (pending, passed, failed, …)
- **`layer_status_counts`** – summary counts across all layers by status (locked, available, in_progress, completed)

A blocked job can be resumed once the underlying cause is resolved:

```bash
curl -b cookies.txt -X POST https://your-app/api/jobs/<job_id>/resume \
  -H 'Content-Type: application/json' \
  -d '{"max_iterations": 200}'
```
