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
│   └── orchestrator.py       # Central orchestrator
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

## Connecting to LLM

To enable actual content generation, provide an LLM client to the orchestrator:

```python
from core.orchestrator import Orchestrator
from your_llm_client import LLMClient

llm = LLMClient(api_key="your-key")
orchestrator = Orchestrator(llm_client=llm)
```

The system expects the LLM client to have a `.generate(prompt, response_format=None)` method.

## License

MIT
