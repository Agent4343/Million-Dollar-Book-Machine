# Million Dollar Book Machine

AI-powered multi-agent system for developing books from concept to publication.

## System Overview

This system uses **21 specialized agents** across **11 development layers** to take a book from initial concept through to publication-ready manuscript.

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
| 19 | Final Quality Validation | final_validation |
| 20 | Publishing Package | publishing_package, ip_clearance |

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

Password: `Blake2011@` (configurable via APP_PASSWORD env var)

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
- `POST /api/projects/{id}/execute/{agent}` - Run specific agent
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
**Line Edit**: Grammar, rhythm, editorial polish
**Beta Simulation**: Simulated reader response, engagement analysis
**Final Validation**: Core promise fulfillment check
**Publishing Package**: Blurb, synopsis, metadata, keywords
**IP Clearance**: Title and naming safety verification

## Claude API Configuration

The system uses the **Anthropic Claude API** for content generation.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required for AI generation |
| `APP_PASSWORD` | Login password | `Blake2011@` |
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

### Railway Deployment

Railway supports long-running processes with persistent volumes, making it ideal for production use.

#### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-...` |
| `APP_PASSWORD` | Login password | A strong password |
| `SESSION_SECRET` | Session signing secret (random string) | `openssl rand -hex 32` output |

#### Recommended Environment Variables

| Variable | Description | Recommended Value |
|----------|-------------|-------------------|
| `CORS_ORIGINS` | Allowed origins for CORS | Your Railway URL, e.g. `https://your-app.railway.app` |
| `COOKIE_SECURE` | Set Secure flag on session cookie | `true` |
| `COOKIE_SAMESITE` | SameSite cookie policy | `lax` (same-origin) or `none` (cross-origin, requires `COOKIE_SECURE=true`) |
| `PROJECT_STORAGE_DIR` | Directory for project files | `/data/projects` |
| `JOB_STORAGE_DIR` | Directory for job state files | `/data/jobs` |
| `MAX_CONCURRENT_JOBS` | Max simultaneous background jobs | `1` |

#### CORS Configuration

Cookie-based authentication requires explicit CORS origins when the frontend and backend are on different domains.

- **Same origin (frontend served by FastAPI)**: No `CORS_ORIGINS` needed; requests are same-origin.
- **Cross-origin (separate frontend)**: Set `CORS_ORIGINS=https://your-frontend.railway.app`.
- **⚠️ Do NOT use `CORS_ORIGINS=*`**: Wildcard CORS disables `allow_credentials`, which breaks session cookies. The server logs a startup warning when `*` is detected.

#### Persistent Volume (Recommended)

Add a Railway volume mounted at `/data` and set:

```
PROJECT_STORAGE_DIR=/data/projects
JOB_STORAGE_DIR=/data/jobs
```

This preserves project state and background job status across redeploys and restarts.

#### Chapter Writing on Railway

Chapter generation can take several minutes per chapter. The system uses a **background job approach** to avoid HTTP timeouts:

1. The UI calls `POST /api/projects/{id}/write-chapters-job` which starts a background job and returns immediately.
2. The UI polls `GET /api/jobs/{job_id}` every 4 seconds to display progress.
3. No HTTP timeout issues — the generation runs server-side and the client just polls.

This is handled automatically by the UI's "Write All Chapters" flow.

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
