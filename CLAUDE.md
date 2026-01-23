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

# Deploy to Railway
railway up
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

---

## Production Readiness for Kindle Publishing

### Current State Assessment

The system provides a solid foundation but requires enhancements for production-ready Kindle Direct Publishing (KDP).

**What Works:**
- 21-agent pipeline for book development (concept → manuscript)
- EPUB export (compatible with modern Kindles)
- DOCX export for traditional publishing
- Chapter writing with voice/style consistency
- Basic publishing package (blurb, synopsis, keywords)

**What's Missing for Production Kindle Books:**

### Critical Gaps

#### 1. Export & Format Issues
| Gap | Impact | Priority |
|-----|--------|----------|
| No cover image integration | Can't publish without cover | HIGH |
| No KPF (Kindle Package Format) | Limits formatting control | MEDIUM |
| MOBI generation not implemented | Legacy device support | LOW |
| Front/back matter missing | Unprofessional appearance | HIGH |

**Required front/back matter:**
- Title page (exists but basic)
- Copyright page
- Dedication page
- Also By page
- About the Author
- Acknowledgments
- Mailing list signup call-to-action

#### 2. KDP Metadata Gaps
| Field | Current State | Required |
|-------|---------------|----------|
| Author name | Hardcoded placeholder | Configurable |
| ISBN | Not supported | Optional for KDP |
| ASIN | Not generated | Amazon assigns |
| BISAC categories | Not implemented | 2 required |
| Age range | Not specified | Required for some genres |
| Series info | Basic | Number in series, series name |
| Publication date | Not tracked | Required |
| Publisher name | Not specified | Optional |

#### 3. Content Quality Issues
| Issue | Location | Fix Required |
|-------|----------|--------------|
| Publishing package returns placeholders | `agents/validation.py:253-265` | Real LLM-generated blurbs |
| Demo mode gives fake content | `core/llm.py` | Requires API key |
| No proofreading validation | Missing agent | Add proofreading layer |
| No formatting validation | Missing | Verify KDP compliance |

#### 4. Amazon-Specific Requirements
- **Book description**: HTML formatting for KDP (bold, italic, lists)
- **Keywords**: 7 keywords max, search-optimized
- **Categories**: BISAC codes mapped to Amazon categories
- **Look Inside**: First 10% must hook readers
- **A+ Content**: Enhanced brand content (optional but recommended)

### Recommended Development Roadmap

#### Phase 1: Core Publishing Infrastructure
```
Priority: HIGH
Files to modify:
- models/state.py - Add author, ISBN, publisher fields
- core/export.py - Add front/back matter generation
- agents/validation.py - Real blurb/synopsis generation
```

**Tasks:**
1. Add `BookMetadata` dataclass with all KDP fields
2. Create front matter generator (copyright, dedication, etc.)
3. Create back matter generator (about author, also by, etc.)
4. Implement cover image handling (path/URL storage)

#### Phase 2: Real Content Generation
```
Priority: HIGH
Files to modify:
- agents/validation.py - publishing_package executor
- core/llm.py - Ensure real LLM calls
```

**Tasks:**
1. Replace placeholder blurb with LLM-generated compelling description
2. Generate HTML-formatted book description for KDP
3. Implement keyword research/optimization agent
4. Add BISAC category suggestion

#### Phase 3: Export Enhancements
```
Priority: MEDIUM
Files to modify:
- core/export.py - Enhanced EPUB generation
- api/index.py - New export endpoints
```

**Tasks:**
1. Embed cover image in EPUB
2. Add proper CSS styling for Kindle
3. Implement scene break formatting
4. Add chapter drop caps (optional)
5. Create KDP-ready package endpoint

#### Phase 4: Persistence & Multi-User
```
Priority: MEDIUM
New files needed:
- core/database.py - SQLite or PostgreSQL
- models/user.py - User management
```

**Tasks:**
1. Add database persistence (SQLite for simple, PostgreSQL for production)
2. Implement proper user accounts
3. Add project versioning/history
4. Backup/restore functionality

### Implementation Examples

#### Adding Cover Image Support

```python
# In models/state.py
@dataclass
class BookMetadata:
    author_name: str = "Author Name"
    author_bio: str = ""
    cover_image_path: Optional[str] = None
    isbn: Optional[str] = None
    publisher: str = "Self-Published"
    publication_date: Optional[str] = None
    series_name: Optional[str] = None
    series_number: Optional[int] = None
    bisac_categories: List[str] = field(default_factory=list)
    amazon_keywords: List[str] = field(default_factory=list)
```

#### Generating Real Blurbs

```python
# In agents/validation.py - replace placeholder
async def execute_publishing_package(context: ExecutionContext) -> Dict[str, Any]:
    llm = context.llm_client

    # Gather context
    concept = context.inputs.get("concept_definition", {})
    characters = context.inputs.get("character_architecture", {})

    blurb_prompt = f"""Write a compelling 150-word book description for Amazon.

    Title: {context.project.title}
    Genre: {context.project.user_constraints.get('genre')}
    Hook: {concept.get('one_line_hook', '')}
    Protagonist: {characters.get('protagonist_profile', {}).get('name', 'the protagonist')}

    Requirements:
    - Open with a hook that creates intrigue
    - Introduce the protagonist and their stakes
    - Hint at the conflict without spoilers
    - End with a question or cliffhanger
    - Use short paragraphs (2-3 sentences each)

    Return as JSON: {{"blurb": "...", "tagline": "..."}}
    """

    result = await llm.generate(blurb_prompt, json_output=True)
    # ... rest of implementation
```

#### Front Matter Generation

```python
# In core/export.py - add function
def generate_front_matter(project, metadata: BookMetadata) -> List[epub.EpubHtml]:
    """Generate standard front matter pages for EPUB."""
    pages = []

    # Copyright page
    copyright_page = epub.EpubHtml(title='Copyright', file_name='copyright.xhtml')
    copyright_page.content = f'''
    <html><body>
    <p style="text-align: center; margin-top: 30%;">
        <strong>{project.title}</strong><br/>
        Copyright © {datetime.now().year} {metadata.author_name}<br/>
        All rights reserved.<br/><br/>
        This is a work of fiction. Names, characters, places, and incidents
        are either products of the author's imagination or used fictitiously.
    </p>
    </body></html>
    '''
    pages.append(copyright_page)

    # Add more pages...
    return pages
```

### Testing for Kindle

**Manual Testing Checklist:**
1. [ ] Upload EPUB to Kindle Previewer
2. [ ] Check TOC navigation works
3. [ ] Verify chapter breaks display correctly
4. [ ] Test on multiple device emulations (Kindle, iPad, Phone)
5. [ ] Confirm no formatting errors in preview
6. [ ] Validate metadata appears correctly
7. [ ] Check cover displays in library view

**Kindle Previewer Download:** https://www.amazon.com/Kindle-Previewer/

### KDP Publishing Checklist

Before publishing, ensure:
- [ ] Cover image: 2560x1600px minimum, RGB, JPEG/TIFF
- [ ] Book description: Under 4000 characters
- [ ] 7 keywords selected (research with Publisher Rocket or similar)
- [ ] 2 BISAC categories chosen
- [ ] Price set ($2.99-$9.99 for 70% royalty)
- [ ] Preview reviewed in Kindle Previewer
- [ ] Proofreading complete
- [ ] All placeholder text removed
- [ ] Front/back matter in place
- [ ] Series info set (if applicable)

### Environment Variables for Production

Add to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...       # Required for real content
DEFAULT_AUTHOR_NAME=Your Name      # Author name
DEFAULT_PUBLISHER=Your Publisher   # Publisher name
STORAGE_PATH=/path/to/storage      # For covers, exports
DATABASE_URL=sqlite:///books.db    # Persistence
```

### Known Issues

1. **Syntax Error Fixed**: `agents/chapter_writer.py:236-237` - f-string with backslash (fixed in current session)
2. **In-Memory Only**: Projects lost on server restart - needs database
3. **Single User**: Password shared for all users - needs user accounts
4. **60s Timeout**: Vercel limits chapter writing - use batch endpoints
