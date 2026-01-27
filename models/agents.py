"""
Agent Definitions for Book Development System

Each agent has:
- Purpose: What it accomplishes
- Inputs: What it needs from previous agents
- Outputs: What it produces
- Gate: Quality check that must pass
- Fail condition: What causes rejection
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum


class AgentType(Enum):
    """Types of agents in the system."""
    RESEARCH = "research"
    CREATIVE = "creative"
    STRUCTURAL = "structural"
    VALIDATION = "validation"
    GENERATION = "generation"
    EDITING = "editing"
    LEGAL = "legal"


@dataclass
class AgentDefinition:
    """Definition of an agent's capabilities and requirements."""
    agent_id: str
    name: str
    layer: int
    agent_type: AgentType
    purpose: str
    inputs: List[str]  # Required inputs from other agents
    outputs: List[str]  # What this agent produces
    gate_criteria: str  # What must be true to pass
    fail_condition: str  # What causes failure
    dependencies: List[str] = field(default_factory=list)  # Agent IDs that must complete first
    prompts: Dict[str, str] = field(default_factory=dict)  # LLM prompts for this agent
    retry_limit: int = 3


# =============================================================================
# LAYER 0: ORCHESTRATION & STATE CONTROL
# =============================================================================

ORCHESTRATOR = AgentDefinition(
    agent_id="orchestrator",
    name="Orchestration & State Control",
    layer=0,
    agent_type=AgentType.STRUCTURAL,
    purpose="Control flow, manage dependencies, handle versioning and checkpoints",
    inputs=["user_constraints"],
    outputs=["agent_map", "stage_order", "state_json", "checkpoint_rules"],
    gate_criteria="All agents registered and dependencies valid",
    fail_condition="Missing constraints or circular dependencies",
    dependencies=[]
)


# =============================================================================
# LAYER 1: STRATEGIC FOUNDATION
# =============================================================================

MARKET_INTELLIGENCE = AgentDefinition(
    agent_id="market_intelligence",
    name="Market & Reader Intelligence",
    layer=1,
    agent_type=AgentType.RESEARCH,
    purpose="Analyze market demand and define target reader",
    inputs=["user_constraints", "genre", "comparable_titles"],
    outputs=["reader_avatar", "market_gap", "positioning_angle", "comp_analysis"],
    gate_criteria="Clear market differentiation identified",
    fail_condition="Commodity concept with no unique angle",
    dependencies=["orchestrator"]
)

CONCEPT_DEFINITION = AgentDefinition(
    agent_id="concept_definition",
    name="Core Concept Definition",
    layer=2,
    agent_type=AgentType.CREATIVE,
    purpose="Define the book's core promise and unique value",
    inputs=["market_gap", "positioning_angle", "user_vision"],
    outputs=["one_line_hook", "core_promise", "unique_engine", "elevator_pitch"],
    gate_criteria="Hook is clear, memorable, and marketable",
    fail_condition="Vague or generic premise",
    dependencies=["market_intelligence"]
)

THEMATIC_ARCHITECTURE = AgentDefinition(
    agent_id="thematic_architecture",
    name="Thematic Architecture",
    layer=3,
    agent_type=AgentType.CREATIVE,
    purpose="Establish the meaning layer and value conflicts",
    inputs=["core_promise", "unique_engine"],
    outputs=["primary_theme", "counter_theme", "value_conflict", "thematic_question"],
    gate_criteria="Theme actively drives story conflict",
    fail_condition="Theme is decorative only, not structural",
    dependencies=["concept_definition"]
)

STORY_QUESTION = AgentDefinition(
    agent_id="story_question",
    name="Central Story Question",
    layer=4,
    agent_type=AgentType.CREATIVE,
    purpose="Define the narrative's central dramatic question",
    inputs=["primary_theme", "value_conflict", "core_promise"],
    outputs=["central_dramatic_question", "stakes_ladder", "binary_outcome", "reader_investment"],
    gate_criteria="Question has binary yes/no outcome with clear stakes",
    fail_condition="No real loss if protagonist fails",
    dependencies=["thematic_architecture"]
)


# =============================================================================
# LAYER 2: STORY SYSTEM DESIGN
# =============================================================================

WORLD_RULES = AgentDefinition(
    agent_id="world_rules",
    name="World / Context Rules",
    layer=5,
    agent_type=AgentType.CREATIVE,
    purpose="Define the constraints and rules of the story world",
    inputs=["central_dramatic_question", "genre", "user_constraints"],
    outputs=["physical_rules", "social_rules", "power_rules", "world_bible", "constraint_list"],
    gate_criteria="Constraints actively enforce story tension",
    fail_condition="Rules break plot or remove tension",
    dependencies=["story_question"]
)

CHARACTER_ARCHITECTURE = AgentDefinition(
    agent_id="character_architecture",
    name="Character Architecture",
    layer=6,
    agent_type=AgentType.CREATIVE,
    purpose="Design characters as agents of thematic change",
    inputs=["primary_theme", "central_dramatic_question", "world_rules"],
    outputs=[
        "protagonist_profile", "protagonist_arc", "want_vs_need",
        "antagonist_profile", "antagonistic_force",
        "supporting_cast", "character_functions"
    ],
    gate_criteria="Every character pressures the theme",
    fail_condition="Passive protagonist or purposeless characters",
    dependencies=["world_rules"]
)

RELATIONSHIP_DYNAMICS = AgentDefinition(
    agent_id="relationship_dynamics",
    name="Relationship Dynamics",
    layer=7,
    agent_type=AgentType.CREATIVE,
    purpose="Map the emotional engine through character relationships",
    inputs=["character_architecture", "primary_theme", "value_conflict"],
    outputs=["conflict_web", "power_shifts", "dependency_arcs", "relationship_matrix"],
    gate_criteria="Relationships evolve meaningfully through story",
    fail_condition="Static interactions that don't change",
    dependencies=["character_architecture"]
)

STORY_BIBLE = AgentDefinition(
    agent_id="story_bible",
    name="Story Bible",
    layer=7,
    agent_type=AgentType.CREATIVE,
    purpose="Create canonical reference document to ensure consistency across all chapters",
    inputs=["character_architecture", "world_rules", "relationship_dynamics"],
    outputs=["character_registry", "location_registry", "timeline", "relationship_map", "terminology", "backstory_facts", "consistency_rules"],
    gate_criteria="All canonical facts locked in with no ambiguity",
    fail_condition="Missing key character details or conflicting facts",
    dependencies=["relationship_dynamics"]
)


# =============================================================================
# LAYER 3: STRUCTURAL ENGINE
# =============================================================================

PLOT_STRUCTURE = AgentDefinition(
    agent_id="plot_structure",
    name="Macro Plot Structure",
    layer=8,
    agent_type=AgentType.STRUCTURAL,
    purpose="Design the story's momentum and major beats",
    inputs=["central_dramatic_question", "protagonist_arc", "relationship_dynamics"],
    outputs=[
        "act_structure", "major_beats", "reversals",
        "point_of_no_return", "climax_design", "resolution"
    ],
    gate_criteria="Clear escalation through all acts",
    fail_condition="Flat middle or unearned climax",
    dependencies=["relationship_dynamics"]
)

PACING_DESIGN = AgentDefinition(
    agent_id="pacing_design",
    name="Pacing & Tension Design",
    layer=9,
    agent_type=AgentType.STRUCTURAL,
    purpose="Control reader energy and engagement rhythm",
    inputs=["plot_structure", "act_structure", "genre"],
    outputs=["tension_curve", "scene_density_map", "breather_points", "acceleration_zones"],
    gate_criteria="No dead zones in tension",
    fail_condition="Prolonged low tension or reader fatigue",
    dependencies=["plot_structure"]
)

CHAPTER_BLUEPRINT = AgentDefinition(
    agent_id="chapter_blueprint",
    name="Chapter & Scene Blueprint",
    layer=10,
    agent_type=AgentType.STRUCTURAL,
    purpose="Create detailed execution map for writing",
    inputs=["plot_structure", "pacing_design", "character_architecture"],
    outputs=[
        "chapter_outline", "chapter_goals", "scene_list",
        "scene_questions", "hooks", "pov_assignments"
    ],
    gate_criteria="Each chapter changes story state",
    fail_condition="Filler scenes with no purpose",
    dependencies=["pacing_design"]
)


# =============================================================================
# LAYER 4: VOICE & EXECUTION
# =============================================================================

VOICE_SPECIFICATION = AgentDefinition(
    agent_id="voice_specification",
    name="Style & Voice Specification",
    layer=11,
    agent_type=AgentType.CREATIVE,
    purpose="Define consistent narrative voice and style rules",
    inputs=["genre", "reader_avatar", "protagonist_profile", "user_constraints"],
    outputs=[
        "narrative_voice", "pov_rules", "tense_rules",
        "syntax_patterns", "sensory_density", "dialogue_style",
        "style_guide"
    ],
    gate_criteria="Style test passages pass consistency check",
    fail_condition="Voice drift or inconsistent tone",
    dependencies=["chapter_blueprint"]
)


# =============================================================================
# LAYER 5: CONTENT GENERATION
# =============================================================================

DRAFT_GENERATION = AgentDefinition(
    agent_id="draft_generation",
    name="Draft Generation",
    layer=12,
    agent_type=AgentType.GENERATION,
    purpose="Produce the manuscript chapters",
    inputs=[
        "chapter_blueprint", "voice_specification", "character_architecture",
        "world_rules", "style_guide"
    ],
    outputs=[
        "chapters",
        "chapter_metadata",
        "word_counts",
        "scene_tags",
        "outline_adherence",
        "chapter_scores",
        "deviations",
        "fix_plan",
    ],
    gate_criteria="Draft follows outline and voice spec",
    fail_condition="Off-outline drift or voice inconsistency",
    dependencies=["voice_specification"]
)


# =============================================================================
# LAYER 6: INTERNAL QUALITY CONTROL
# =============================================================================

CONTINUITY_AUDIT = AgentDefinition(
    agent_id="continuity_audit",
    name="Continuity & Logic Audit",
    layer=13,
    agent_type=AgentType.VALIDATION,
    purpose="Verify canon integrity and internal consistency",
    inputs=["chapters", "world_rules", "character_architecture", "chapter_blueprint"],
    outputs=["timeline_check", "character_logic_check", "world_rule_check", "continuity_report"],
    gate_criteria="Zero contradictions in canon",
    fail_condition="Canon breaks or timeline errors",
    dependencies=["draft_generation"]
)

EMOTIONAL_VALIDATION = AgentDefinition(
    agent_id="emotional_validation",
    name="Emotional Impact Validation",
    layer=14,
    agent_type=AgentType.VALIDATION,
    purpose="Verify reader payoff and emotional resonance",
    inputs=["chapters", "protagonist_arc", "stakes_ladder", "tension_curve"],
    outputs=["scene_resonance_scores", "arc_fulfillment_check", "emotional_peaks_map"],
    gate_criteria="Emotional peaks land as designed",
    fail_condition="Flat climax or unearned emotions",
    dependencies=["continuity_audit"]
)


# =============================================================================
# LAYER 7: ORIGINALITY & LEGAL SAFETY
# =============================================================================

ORIGINALITY_SCAN = AgentDefinition(
    agent_id="originality_scan",
    name="Creative Originality Scan",
    layer=15,
    agent_type=AgentType.LEGAL,
    purpose="Detect trope cloning and unintentional similarity",
    inputs=["chapters", "plot_structure", "character_architecture"],
    outputs=["structural_similarity_report", "phrase_recurrence_check", "originality_score"],
    gate_criteria="Originality threshold met",
    fail_condition="Pattern collision with known works",
    dependencies=["emotional_validation"]
)

PLAGIARISM_AUDIT = AgentDefinition(
    agent_id="plagiarism_audit",
    name="Legal Plagiarism & Copyright Audit",
    layer=15,
    agent_type=AgentType.LEGAL,
    purpose="Assess legal risk from similarity to existing works",
    # Use the producing agent id so orchestrator wiring is reliable.
    inputs=["chapters", "originality_scan"],
    outputs=[
        "substantial_similarity_check", "character_likeness_check",
        "scene_replication_check", "protected_expression_check", "legal_risk_score"
    ],
    gate_criteria="Low legal risk score",
    fail_condition="Infringement risk detected",
    dependencies=["originality_scan"]
)

TRANSFORMATIVE_VERIFICATION = AgentDefinition(
    agent_id="transformative_verification",
    name="Transformative Use Verification",
    layer=15,
    agent_type=AgentType.LEGAL,
    purpose="Verify legal defensibility of creative choices",
    inputs=["chapters", "plagiarism_audit"],
    outputs=["independent_creation_proof", "market_confusion_check", "transformative_distance"],
    gate_criteria="Sufficient transformative distance",
    fail_condition="Derivative exposure risk",
    dependencies=["plagiarism_audit"]
)


# =============================================================================
# LAYER 8: REWRITE & REVALIDATION
# =============================================================================

STRUCTURAL_REWRITE = AgentDefinition(
    agent_id="structural_rewrite",
    name="Structural & Prose Rewrite",
    layer=16,
    agent_type=AgentType.EDITING,
    purpose="Improve clarity, force, and resolve flagged issues",
    # Use producing agent ids so inputs are always discoverable.
    inputs=["chapters", "continuity_audit", "emotional_validation", "originality_scan", "plagiarism_audit", "transformative_verification"],
    outputs=["revised_chapters", "revision_log", "resolved_flags"],
    gate_criteria="All flagged issues resolved",
    fail_condition="New inconsistencies introduced",
    dependencies=["transformative_verification"]
)

POST_REWRITE_SCAN = AgentDefinition(
    agent_id="post_rewrite_scan",
    name="Post-Rewrite Originality Re-Scan",
    layer=16,
    agent_type=AgentType.LEGAL,
    purpose="Catch rewrite-introduced similarity",
    inputs=["revised_chapters"],
    outputs=["rewrite_originality_check", "new_similarity_flags"],
    gate_criteria="Clean scan with no new flags",
    fail_condition="Reintroduced similarity patterns",
    dependencies=["structural_rewrite"]
)


# =============================================================================
# LAYER 9: LANGUAGE & READER TESTING
# =============================================================================

LINE_EDIT = AgentDefinition(
    agent_id="line_edit",
    name="Line & Copy Edit",
    layer=17,
    agent_type=AgentType.EDITING,
    purpose="Polish prose for precision and rhythm",
    inputs=["revised_chapters", "style_guide"],
    outputs=["edited_chapters", "grammar_fixes", "rhythm_improvements", "edit_report"],
    gate_criteria="Editorial standards met",
    fail_condition="Mechanical errors remain",
    dependencies=["post_rewrite_scan"]
)

BETA_SIMULATION = AgentDefinition(
    agent_id="beta_simulation",
    name="Beta Reader Simulation",
    layer=18,
    agent_type=AgentType.VALIDATION,
    purpose="Simulate market reader response",
    inputs=["edited_chapters", "reader_avatar", "genre"],
    outputs=["dropoff_points", "confusion_zones", "engagement_scores", "feedback_summary"],
    gate_criteria="Engagement sustained throughout",
    fail_condition="Reader abandonment predicted",
    dependencies=["line_edit"]
)


# =============================================================================
# LAYER 10: FINAL APPROVAL & RELEASE
# =============================================================================

FINAL_VALIDATION = AgentDefinition(
    agent_id="final_validation",
    name="Final Quality Validation",
    layer=19,
    agent_type=AgentType.VALIDATION,
    purpose="Verify complete promise fulfillment",
    inputs=["edited_chapters", "core_promise", "primary_theme", "central_dramatic_question"],
    outputs=["concept_match_score", "theme_payoff_check", "promise_fulfillment", "release_recommendation"],
    gate_criteria="Release approved",
    fail_condition="Core promise not delivered",
    dependencies=["human_editor_review"]
)

HUMAN_EDITOR_REVIEW = AgentDefinition(
    agent_id="human_editor_review",
    name="Human Editor Review (AI Simulation)",
    layer=19,
    agent_type=AgentType.VALIDATION,
    purpose="Simulate a professional human editor's review with required changes and an editorial letter",
    inputs=[
        "edited_chapters",
        "voice_specification",
        "chapter_blueprint",
        "market_intelligence",
        "concept_definition",
        "thematic_architecture",
        "story_question",
        "user_constraints",
    ],
    outputs=["approved", "confidence", "editorial_letter", "required_changes", "optional_suggestions"],
    gate_criteria="approved=true and required_changes empty",
    fail_condition="Editor requests required changes before publication",
    dependencies=["beta_simulation"]
)

PRODUCTION_READINESS = AgentDefinition(
    agent_id="production_readiness",
    name="Production Readiness Report",
    layer=19,
    agent_type=AgentType.VALIDATION,
    purpose="Create a QA-style release checklist and blockers for publication",
    inputs=["edited_chapters", "release_recommendation", "metadata", "user_constraints"],
    outputs=["quality_score", "release_blockers", "major_issues", "minor_issues", "recommended_actions"],
    gate_criteria="No release blockers and quality_score >= 85",
    fail_condition="Release blockers present or quality score below threshold",
    dependencies=["final_validation"]
)

PUBLISHING_PACKAGE = AgentDefinition(
    agent_id="publishing_package",
    name="Publishing Package",
    layer=20,
    agent_type=AgentType.GENERATION,
    purpose="Create market-ready publishing materials",
    inputs=["edited_chapters", "core_promise", "reader_avatar", "positioning_angle"],
    outputs=["blurb", "synopsis", "metadata", "keywords", "series_hooks", "author_bio"],
    gate_criteria="Platform-ready package complete",
    fail_condition="Weak positioning or missing elements",
    dependencies=["final_validation", "production_readiness"]
)

KDP_READINESS = AgentDefinition(
    agent_id="kdp_readiness",
    name="Kindle / KDP Readiness",
    layer=20,
    agent_type=AgentType.VALIDATION,
    purpose="Validate EPUB/DOCX exports and ensure front/back matter readiness for Kindle publishing",
    inputs=["edited_chapters", "publishing_package", "user_constraints", "title", "author_name"],
    outputs=["kindle_ready", "epub_report", "docx_report", "front_matter_report", "recommendations"],
    gate_criteria="kindle_ready=true and no critical issues in export reports",
    fail_condition="EPUB/DOCX export validation fails or front matter is missing",
    dependencies=["publishing_package", "final_proof"]
)

FINAL_PROOF = AgentDefinition(
    agent_id="final_proof",
    name="Final Proof (Full Manuscript)",
    layer=20,
    agent_type=AgentType.EDITING,
    purpose="Run a full-manuscript proof/copy check and consistency scan before Kindle release",
    inputs=["edited_chapters", "style_guide", "voice_specification", "chapter_blueprint", "user_constraints"],
    outputs=["approved", "overall_score", "critical_issues", "major_issues", "minor_issues", "per_chapter_issues", "consistency_findings", "recommended_actions"],
    gate_criteria="approved=true and critical_issues=0",
    fail_condition="Critical proof issues remain",
    dependencies=["production_readiness"]
)

IP_CLEARANCE = AgentDefinition(
    agent_id="ip_clearance",
    name="IP, Title & Brand Clearance",
    layer=20,
    agent_type=AgentType.LEGAL,
    purpose="Verify naming safety for publication",
    inputs=["title", "character_names", "series_name"],
    outputs=["title_conflict_check", "series_naming_check", "character_naming_check", "clearance_status"],
    gate_criteria="All naming cleared",
    fail_condition="Rename required",
    dependencies=["kdp_readiness"]
)


# =============================================================================
# LAYER 21: MARKETING & COMMERCIAL OPTIMIZATION
# =============================================================================

BLURB_GENERATOR = AgentDefinition(
    agent_id="blurb_generator",
    name="Amazon Blurb Generator",
    layer=21,
    agent_type=AgentType.GENERATION,
    purpose="Generate Amazon-optimized book descriptions and marketing copy",
    inputs=["concept_definition", "character_architecture", "story_question", "user_constraints"],
    outputs=["short_blurb", "full_blurb", "a_plus_content", "tagline", "comparison_pitch"],
    gate_criteria="Blurb follows Amazon best practices and hooks reader",
    fail_condition="Generic blurb without emotional hooks",
    dependencies=["publishing_package"]
)

KEYWORD_OPTIMIZER = AgentDefinition(
    agent_id="keyword_optimizer",
    name="KDP Keyword Optimizer",
    layer=21,
    agent_type=AgentType.RESEARCH,
    purpose="Generate optimized KDP keywords and BISAC categories",
    inputs=["user_constraints", "world_rules", "character_architecture", "thematic_architecture", "plot_structure"],
    outputs=["primary_keywords", "backup_keywords", "bisac_categories", "amazon_categories", "search_volume_notes", "competition_notes"],
    gate_criteria="7 high-quality keywords with proper categorization",
    fail_condition="Keywords too generic or violate KDP rules",
    dependencies=["blurb_generator"]
)

SERIES_BIBLE_GENERATOR = AgentDefinition(
    agent_id="series_bible",
    name="Series Bible Generator",
    layer=21,
    agent_type=AgentType.GENERATION,
    purpose="Create series continuity bible for multi-book planning",
    inputs=["story_bible", "draft_generation", "character_architecture"],
    outputs=["series_potential", "unresolved_threads", "character_futures", "world_expansion", "series_hooks", "spinoff_potential", "timeline_for_series", "recurring_elements", "series_title_suggestions"],
    gate_criteria="Series bible captures all continuation potential",
    fail_condition="Misses obvious sequel opportunities",
    dependencies=["keyword_optimizer"]
)

COMP_ANALYSIS = AgentDefinition(
    agent_id="comp_analysis",
    name="Comp Title Analysis",
    layer=21,
    agent_type=AgentType.RESEARCH,
    purpose="Analyze comparable titles for market positioning",
    inputs=["user_constraints", "publishing_package"],
    outputs=["provided_comps", "positioning_recommendations", "price_positioning", "launch_strategy"],
    gate_criteria="Clear positioning strategy with actionable recommendations",
    fail_condition="No differentiation from comps",
    dependencies=["series_bible"]
)


# =============================================================================
# AGENT REGISTRY
# =============================================================================

AGENT_REGISTRY: Dict[str, AgentDefinition] = {
    # Layer 0
    "orchestrator": ORCHESTRATOR,
    # Layer 1-4: Strategic Foundation
    "market_intelligence": MARKET_INTELLIGENCE,
    "concept_definition": CONCEPT_DEFINITION,
    "thematic_architecture": THEMATIC_ARCHITECTURE,
    "story_question": STORY_QUESTION,
    # Layer 5-7: Story System Design
    "world_rules": WORLD_RULES,
    "character_architecture": CHARACTER_ARCHITECTURE,
    "relationship_dynamics": RELATIONSHIP_DYNAMICS,
    "story_bible": STORY_BIBLE,
    # Layer 8-10: Structural Engine
    "plot_structure": PLOT_STRUCTURE,
    "pacing_design": PACING_DESIGN,
    "chapter_blueprint": CHAPTER_BLUEPRINT,
    # Layer 11: Voice
    "voice_specification": VOICE_SPECIFICATION,
    # Layer 12: Generation
    "draft_generation": DRAFT_GENERATION,
    # Layer 13-14: Quality Control
    "continuity_audit": CONTINUITY_AUDIT,
    "emotional_validation": EMOTIONAL_VALIDATION,
    # Layer 15: Originality & Legal
    "originality_scan": ORIGINALITY_SCAN,
    "plagiarism_audit": PLAGIARISM_AUDIT,
    "transformative_verification": TRANSFORMATIVE_VERIFICATION,
    # Layer 16: Rewrite
    "structural_rewrite": STRUCTURAL_REWRITE,
    "post_rewrite_scan": POST_REWRITE_SCAN,
    # Layer 17-18: Language & Testing
    "line_edit": LINE_EDIT,
    "beta_simulation": BETA_SIMULATION,
    # Layer 19-20: Final
    "final_validation": FINAL_VALIDATION,
    "human_editor_review": HUMAN_EDITOR_REVIEW,
    "production_readiness": PRODUCTION_READINESS,
    "publishing_package": PUBLISHING_PACKAGE,
    "final_proof": FINAL_PROOF,
    "kdp_readiness": KDP_READINESS,
    "ip_clearance": IP_CLEARANCE,
    # Layer 21: Marketing & Commercial
    "blurb_generator": BLURB_GENERATOR,
    "keyword_optimizer": KEYWORD_OPTIMIZER,
    "series_bible": SERIES_BIBLE_GENERATOR,
    "comp_analysis": COMP_ANALYSIS,
}


def get_agents_by_layer(layer: int) -> List[AgentDefinition]:
    """Get all agents for a specific layer."""
    return [a for a in AGENT_REGISTRY.values() if a.layer == layer]


def get_agent_execution_order() -> List[str]:
    """Get agents in dependency-respecting execution order."""
    order = []
    visited = set()

    def visit(agent_id: str):
        if agent_id in visited:
            return
        agent = AGENT_REGISTRY.get(agent_id)
        if agent:
            for dep in agent.dependencies:
                visit(dep)
            visited.add(agent_id)
            order.append(agent_id)

    for agent_id in AGENT_REGISTRY:
        visit(agent_id)

    return order
