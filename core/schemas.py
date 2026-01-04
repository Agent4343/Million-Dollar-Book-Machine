"""
Pydantic schemas for agent outputs.

These schemas let us validate that agent outputs are well-formed and complete.
They intentionally focus on "structure + minimum viable quality" rather than
subjective literary quality.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class ReaderAvatar(BaseModel):
    demographics: str = Field(min_length=3)
    psychographics: str = Field(min_length=3)
    reading_habits: str = Field(min_length=3)
    problems_to_solve: List[str] = Field(min_length=1)


class MarketGap(BaseModel):
    unmet_need: str = Field(min_length=3)
    timing: str = Field(min_length=3)
    opportunity_size: str = Field(min_length=1)


class PositioningAngle(BaseModel):
    unique_value: str = Field(min_length=3)
    differentiators: List[str] = Field(min_length=1)
    competitive_advantage: str = Field(min_length=3)


class CompTitle(BaseModel):
    title: str = Field(min_length=1)
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)


class MarketIntelligenceOutput(BaseModel):
    reader_avatar: ReaderAvatar
    market_gap: MarketGap
    positioning_angle: PositioningAngle
    comp_analysis: List[CompTitle] = Field(min_length=1)


class CorePromise(BaseModel):
    transformation: str = Field(min_length=3)
    value: str = Field(min_length=3)
    emotional_payoff: str = Field(min_length=3)


class UniqueEngine(BaseModel):
    mechanism: str = Field(min_length=3)
    novelty: str = Field(min_length=3)
    credibility: str = Field(min_length=3)


class ConceptDefinitionOutput(BaseModel):
    one_line_hook: str = Field(min_length=8)
    core_promise: CorePromise
    unique_engine: UniqueEngine
    elevator_pitch: str = Field(min_length=20)


class ThemeStatement(BaseModel):
    statement: str = Field(min_length=8)
    universal_truth: str = Field(min_length=8)
    argument: str = Field(min_length=8)


class CounterTheme(BaseModel):
    statement: str = Field(min_length=8)
    represented_by: str = Field(min_length=3)
    argument: str = Field(min_length=8)


class ValueConflict(BaseModel):
    value_a: str = Field(min_length=2)
    value_b: str = Field(min_length=2)
    why_incompatible: str = Field(min_length=8)


class ThematicArchitectureOutput(BaseModel):
    primary_theme: ThemeStatement
    counter_theme: CounterTheme
    value_conflict: ValueConflict
    thematic_question: str = Field(min_length=8)


class StakesLevel(BaseModel):
    risk: str = Field(min_length=3)
    consequence: str = Field(min_length=3)


class StakesLadder(BaseModel):
    level_1: StakesLevel
    level_2: StakesLevel
    level_3: StakesLevel


class BinaryOutcome(BaseModel):
    success: str = Field(min_length=3)
    failure: str = Field(min_length=3)


class ReaderInvestment(BaseModel):
    relatability: str = Field(min_length=3)
    emotional_hooks: List[str] = Field(min_length=1)
    curiosity_drivers: List[str] = Field(min_length=1)


class StoryQuestionOutput(BaseModel):
    central_dramatic_question: str = Field(min_length=8)
    stakes_ladder: StakesLadder
    binary_outcome: BinaryOutcome
    reader_investment: ReaderInvestment


class PhysicalRules(BaseModel):
    possibilities: List[str] = Field(min_length=1)
    impossibilities: List[str] = Field(default_factory=list)
    technology: str = Field(min_length=1)
    geography: str = Field(min_length=1)


class SocialRules(BaseModel):
    power_structures: str = Field(min_length=1)
    norms: List[str] = Field(min_length=1)
    taboos: List[str] = Field(default_factory=list)
    economics: str = Field(min_length=1)


class PowerRules(BaseModel):
    who_has_power: str = Field(min_length=1)
    how_gained: str = Field(min_length=1)
    how_lost: str = Field(min_length=1)
    limitations: List[str] = Field(default_factory=list)


class WorldBible(BaseModel):
    relevant_history: str = Field(min_length=1)
    culture: str = Field(min_length=1)
    terminology: Dict[str, Any] = Field(default_factory=dict)


class WorldRulesOutput(BaseModel):
    physical_rules: PhysicalRules
    social_rules: SocialRules
    power_rules: PowerRules
    world_bible: WorldBible
    constraint_list: List[str] = Field(min_length=1)


class ProtagonistProfile(BaseModel):
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    traits: List[str] = Field(min_length=1)
    backstory_wound: str = Field(min_length=3)
    skills: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)


class ProtagonistArc(BaseModel):
    starting_state: str = Field(min_length=3)
    ending_state: str = Field(min_length=3)
    transformation: str = Field(min_length=3)


class WantVsNeed(BaseModel):
    want: str = Field(min_length=3)
    need: str = Field(min_length=3)
    conflict: str = Field(min_length=8)


class AntagonistProfile(BaseModel):
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    worldview: str = Field(min_length=3)
    opposition_reason: str = Field(min_length=3)
    strength: str = Field(min_length=3)


class AntagonisticForce(BaseModel):
    external: str = Field(min_length=1)
    internal: str = Field(min_length=1)
    societal: str = Field(min_length=1)


class SupportingCharacter(BaseModel):
    name: str = Field(min_length=1)
    function: str = Field(min_length=1)
    challenge: str = Field(min_length=1)
    arc: str = Field(min_length=1)


class CharacterFunctions(BaseModel):
    mentor: str = Field(min_length=1)
    ally: str = Field(min_length=1)
    shapeshifter: str = Field(min_length=1)
    threshold_guardian: str = Field(min_length=1)


class CharacterArchitectureOutput(BaseModel):
    protagonist_profile: ProtagonistProfile
    protagonist_arc: ProtagonistArc
    want_vs_need: WantVsNeed
    antagonist_profile: AntagonistProfile
    antagonistic_force: AntagonisticForce
    supporting_cast: List[SupportingCharacter] = Field(min_length=1)
    character_functions: CharacterFunctions


class ConflictWebItem(BaseModel):
    characters: List[str] = Field(min_length=2)
    tension: str = Field(min_length=3)
    source: str = Field(min_length=3)
    each_wants: Dict[str, str] = Field(default_factory=dict)


class PowerShiftItem(BaseModel):
    characters: List[str] = Field(min_length=2)
    initial_balance: str = Field(min_length=3)
    shift_moment: str = Field(min_length=3)
    final_state: str = Field(min_length=3)


class DependencyArcItem(BaseModel):
    dependent: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    nature: str = Field(min_length=3)
    evolution: str = Field(min_length=3)
    breaking_point: str = Field(min_length=3)


class RelationshipMatrixItem(BaseModel):
    char_a: str = Field(min_length=1)
    char_b: str = Field(min_length=1)
    type: str = Field(min_length=1)
    start_state: str = Field(min_length=3)
    end_state: str = Field(min_length=3)


class RelationshipDynamicsOutput(BaseModel):
    conflict_web: List[ConflictWebItem] = Field(min_length=1)
    power_shifts: List[PowerShiftItem] = Field(min_length=1)
    dependency_arcs: List[DependencyArcItem] = Field(min_length=1)
    relationship_matrix: List[RelationshipMatrixItem] = Field(min_length=1)


class PlotAct(BaseModel):
    percentage: int = Field(ge=1, le=100)
    purpose: str = Field(min_length=3)
    key_events: List[str] = Field(min_length=1)


class ActStructure(BaseModel):
    act_1: PlotAct
    act_2: PlotAct
    act_3: PlotAct


class MajorBeat(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=3)
    page_target: str = Field(min_length=1)


class Reversal(BaseModel):
    name: str = Field(min_length=1)
    what_changes: str = Field(min_length=3)
    impact: str = Field(min_length=3)


class PointOfNoReturn(BaseModel):
    moment: str = Field(min_length=3)
    why_irreversible: str = Field(min_length=3)
    protagonist_commitment: str = Field(min_length=3)


class ClimaxDesign(BaseModel):
    setup: str = Field(min_length=3)
    confrontation: str = Field(min_length=3)
    resolution: str = Field(min_length=3)


class Resolution(BaseModel):
    external_resolution: str = Field(min_length=3)
    internal_resolution: str = Field(min_length=3)
    final_image: str = Field(min_length=3)


class PlotStructureOutput(BaseModel):
    act_structure: ActStructure
    major_beats: List[MajorBeat] = Field(min_length=1)
    reversals: List[Reversal] = Field(min_length=1)
    point_of_no_return: PointOfNoReturn
    climax_design: ClimaxDesign
    resolution: Resolution


class TensionPoint(BaseModel):
    point: str = Field(min_length=1)
    level: int = Field(ge=1, le=10)
    description: str = Field(min_length=3)


class DensitySection(BaseModel):
    action_reflection_ratio: str = Field(min_length=3)
    dialogue_description: str = Field(min_length=3)


class SceneDensityMap(BaseModel):
    act_1: DensitySection
    act_2_first_half: DensitySection
    act_2_second_half: DensitySection
    act_3: DensitySection


class BreatherPoint(BaseModel):
    after: str = Field(min_length=1)
    type: str = Field(min_length=1)
    purpose: str = Field(min_length=3)


class AccelerationZone(BaseModel):
    section: str = Field(min_length=1)
    technique: str = Field(min_length=3)
    effect: str = Field(min_length=3)


class PacingDesignOutput(BaseModel):
    tension_curve: List[TensionPoint] = Field(min_length=3)
    scene_density_map: SceneDensityMap
    breather_points: List[BreatherPoint] = Field(default_factory=list)
    acceleration_zones: List[AccelerationZone] = Field(default_factory=list)


class BlueprintScene(BaseModel):
    scene_number: int = Field(ge=1)
    scene_question: str = Field(min_length=3)
    characters: List[str] = Field(min_length=1)
    location: str = Field(min_length=1)
    conflict_type: str = Field(min_length=1)
    outcome: str = Field(min_length=1)
    word_target: int = Field(ge=100)


class BlueprintChapter(BaseModel):
    number: int = Field(ge=1)
    title: str = Field(min_length=1)
    act: int = Field(ge=1, le=3)
    chapter_goal: str = Field(min_length=3)
    pov: str = Field(min_length=1)
    opening_hook: str = Field(min_length=3)
    closing_hook: str = Field(min_length=3)
    word_target: int = Field(ge=300)
    scenes: List[BlueprintScene] = Field(min_length=1)


class Hooks(BaseModel):
    chapter_hooks: List[str] = Field(default_factory=list)
    scene_hooks: List[str] = Field(default_factory=list)


class ChapterBlueprintOutput(BaseModel):
    chapter_outline: List[BlueprintChapter] = Field(min_length=3)
    chapter_goals: Dict[str, str] = Field(default_factory=dict)
    scene_list: List[str] = Field(default_factory=list)
    scene_questions: Dict[str, str] = Field(default_factory=dict)
    hooks: Hooks = Field(default_factory=Hooks)
    pov_assignments: Dict[str, str] = Field(default_factory=dict)


class NarrativeVoice(BaseModel):
    pov_type: str = Field(min_length=3)
    distance: str = Field(min_length=1)
    personality: str = Field(min_length=3)
    tone: str = Field(min_length=3)


class PovRules(BaseModel):
    perspective_character: str = Field(min_length=1)
    knowledge_limits: str = Field(min_length=3)
    rules: List[str] = Field(min_length=1)


class TenseRules(BaseModel):
    primary_tense: str = Field(min_length=2)
    exceptions: List[str] = Field(default_factory=list)


class SyntaxPatterns(BaseModel):
    avg_sentence_length: str = Field(min_length=1)
    complexity: str = Field(min_length=1)
    rhythm: str = Field(min_length=1)


class SensoryDensity(BaseModel):
    visual: str = Field(min_length=1)
    other_senses: str = Field(min_length=1)
    frequency: str = Field(min_length=1)


class DialogueStyle(BaseModel):
    tag_approach: str = Field(min_length=1)
    subtext_level: str = Field(min_length=1)
    differentiation: str = Field(min_length=1)


class StyleGuide(BaseModel):
    dos: List[str] = Field(min_length=1)
    donts: List[str] = Field(min_length=1)
    example_passages: List[str] = Field(min_length=1)


class VoiceSpecificationOutput(BaseModel):
    narrative_voice: NarrativeVoice
    pov_rules: PovRules
    tense_rules: TenseRules
    syntax_patterns: SyntaxPatterns
    sensory_density: SensoryDensity
    dialogue_style: DialogueStyle
    style_guide: StyleGuide


class ChapterText(BaseModel):
    number: int = Field(ge=1)
    title: str = Field(min_length=1)
    text: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    word_count: int = Field(ge=0)


class ChapterMetadataItem(BaseModel):
    number: int = Field(ge=1)
    title: str = Field(min_length=1)
    scenes: int = Field(ge=0)
    pov: str = Field(min_length=1)


class DraftGenerationOutput(BaseModel):
    chapters: List[ChapterText] = Field(min_length=1)
    chapter_metadata: List[ChapterMetadataItem] = Field(min_length=1)
    word_counts: Dict[str, int] = Field(default_factory=dict)
    scene_tags: Dict[str, Any] = Field(default_factory=dict)
    outline_adherence: Dict[str, Any] = Field(default_factory=dict)
    chapter_scores: Dict[str, int] = Field(default_factory=dict)
    deviations: List[Dict[str, Any]] = Field(default_factory=list)
    fix_plan: List[str] = Field(default_factory=list)


class AuditIssue(BaseModel):
    chapter: Optional[int] = Field(default=None, ge=1)
    location: str = Field(min_length=1)
    severity: Literal["critical", "major", "minor"] = "minor"
    description: str = Field(min_length=3)
    suggested_fix: str = Field(min_length=3)


class AuditCheck(BaseModel):
    status: Literal["passed", "failed", "warning"] = "passed"
    issues: List[AuditIssue] = Field(default_factory=list)
    notes: str = Field(min_length=1)


class ContinuityReport(BaseModel):
    total_issues: int = Field(ge=0)
    critical_issues: int = Field(ge=0)
    warnings: int = Field(ge=0)
    recommendation: str = Field(min_length=3)


class ContinuityAuditOutput(BaseModel):
    timeline_check: AuditCheck
    character_logic_check: AuditCheck
    world_rule_check: AuditCheck
    continuity_report: ContinuityReport


class ArcFulfillmentCheck(BaseModel):
    protagonist_arc_complete: bool
    transformation_earned: bool
    supporting_arcs_resolved: bool
    notes: str = Field(min_length=1)


class EmotionalPeak(BaseModel):
    chapter: int = Field(ge=1)
    type: str = Field(min_length=1)
    intensity: int = Field(ge=1, le=10)


class EmotionalValidationOutput(BaseModel):
    scene_resonance_scores: Dict[str, Any]
    arc_fulfillment_check: ArcFulfillmentCheck
    emotional_peaks_map: List[EmotionalPeak] = Field(default_factory=list)


class StructuralSimilarityReport(BaseModel):
    similar_works_found: List[str] = Field(default_factory=list)
    similarity_level: str = Field(min_length=1)
    unique_elements: List[str] = Field(default_factory=list)


class PhraseRecurrenceCheck(BaseModel):
    overused_phrases: List[str] = Field(default_factory=list)
    cliches_found: List[str] = Field(default_factory=list)
    recommendation: str = Field(min_length=1)


class OriginalityScanOutput(BaseModel):
    structural_similarity_report: StructuralSimilarityReport
    phrase_recurrence_check: PhraseRecurrenceCheck
    originality_score: int = Field(ge=0, le=100)


class SimilarityCheck(BaseModel):
    status: str = Field(min_length=1)
    flags: List[str] = Field(default_factory=list)
    confidence: int = Field(ge=0, le=100)


class LikenessCheck(BaseModel):
    status: str = Field(min_length=1)
    similar_characters: List[str] = Field(default_factory=list)
    notes: str = Field(min_length=1)


class SceneReplicationCheck(BaseModel):
    status: str = Field(min_length=1)
    similar_scenes: List[str] = Field(default_factory=list)
    notes: str = Field(min_length=1)


class ProtectedExpressionCheck(BaseModel):
    status: str = Field(min_length=1)
    flags: List[str] = Field(default_factory=list)
    notes: str = Field(min_length=1)


class PlagiarismAuditOutput(BaseModel):
    substantial_similarity_check: SimilarityCheck
    character_likeness_check: LikenessCheck
    scene_replication_check: SceneReplicationCheck
    protected_expression_check: ProtectedExpressionCheck
    legal_risk_score: int = Field(ge=0, le=100)


class IndependentCreationProof(BaseModel):
    documented: bool
    creation_timeline: str = Field(min_length=1)
    influence_sources: str = Field(min_length=1)


class MarketConfusionCheck(BaseModel):
    risk_level: str = Field(min_length=1)
    similar_titles: List[str] = Field(default_factory=list)
    recommendation: str = Field(min_length=1)


class TransformativeDistance(BaseModel):
    score: int = Field(ge=0, le=100)
    analysis: str = Field(min_length=3)


class TransformativeVerificationOutput(BaseModel):
    independent_creation_proof: IndependentCreationProof
    market_confusion_check: MarketConfusionCheck
    transformative_distance: TransformativeDistance


class RevisionLogItem(BaseModel):
    chapter: int = Field(ge=1)
    changes: str = Field(min_length=3)


class StructuralRewriteOutput(BaseModel):
    revised_chapters: List[ChapterText] = Field(min_length=1)
    revision_log: List[RevisionLogItem] = Field(default_factory=list)
    resolved_flags: int = Field(ge=0)


class RewriteOriginalityCheck(BaseModel):
    status: str = Field(min_length=1)
    new_issues: List[str] = Field(default_factory=list)


class PostRewriteScanOutput(BaseModel):
    rewrite_originality_check: RewriteOriginalityCheck
    new_similarity_flags: List[str] = Field(default_factory=list)


class EditReport(BaseModel):
    total_changes: int = Field(ge=0)
    major_changes: int = Field(ge=0)
    minor_changes: int = Field(ge=0)
    readability_improvement: str = Field(min_length=1)


class LineEditOutput(BaseModel):
    edited_chapters: List[ChapterText] = Field(min_length=1)
    grammar_fixes: int = Field(ge=0)
    rhythm_improvements: int = Field(ge=0)
    edit_report: EditReport


class EngagementScores(BaseModel):
    opening: float = Field(ge=0, le=10)
    middle: float = Field(ge=0, le=10)
    climax: float = Field(ge=0, le=10)
    ending: float = Field(ge=0, le=10)
    overall: float = Field(ge=0, le=10)


class FeedbackSummary(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    quotes: List[str] = Field(default_factory=list)


class BetaSimulationOutput(BaseModel):
    dropoff_points: List[str] = Field(default_factory=list)
    confusion_zones: List[str] = Field(default_factory=list)
    engagement_scores: EngagementScores
    feedback_summary: FeedbackSummary


class ThemePayoffCheck(BaseModel):
    theme_delivered: bool
    thematic_question_addressed: bool
    value_conflict_resolved: bool


class PromiseFulfillment(BaseModel):
    core_promise_delivered: bool
    reader_expectation_met: bool
    emotional_payoff_achieved: bool


class ReleaseRecommendation(BaseModel):
    approved: bool
    confidence: int = Field(ge=0, le=100)
    notes: str = Field(min_length=1)


class FinalValidationOutput(BaseModel):
    concept_match_score: int = Field(ge=0, le=100)
    theme_payoff_check: ThemePayoffCheck
    promise_fulfillment: PromiseFulfillment
    release_recommendation: ReleaseRecommendation


class ProductionReadinessOutput(BaseModel):
    quality_score: int = Field(ge=0, le=100)
    release_blockers: List[str] = Field(default_factory=list)
    major_issues: List[str] = Field(default_factory=list)
    minor_issues: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)


class HumanEditorReviewOutput(BaseModel):
    approved: bool
    confidence: int = Field(ge=0, le=100)
    editorial_letter: str = Field(min_length=10)
    required_changes: List[str] = Field(default_factory=list)
    optional_suggestions: List[str] = Field(default_factory=list)


class PublishingMetadata(BaseModel):
    title: str = Field(min_length=1)
    genre: str = Field(min_length=1)
    word_count: int = Field(ge=0)
    audience: str = Field(min_length=1)


class PublishingPackageOutput(BaseModel):
    blurb: str = Field(min_length=1)
    synopsis: str = Field(min_length=1)
    metadata: PublishingMetadata
    keywords: List[str] = Field(min_length=1)
    series_hooks: List[str] = Field(default_factory=list)
    author_bio: str = Field(min_length=1)


class TitleConflictCheck(BaseModel):
    status: str = Field(min_length=1)
    similar_titles: List[str] = Field(default_factory=list)
    recommendation: str = Field(min_length=1)


class SeriesNamingCheck(BaseModel):
    status: str = Field(min_length=1)
    conflicts: List[str] = Field(default_factory=list)


class CharacterNamingCheck(BaseModel):
    status: str = Field(min_length=1)
    conflicts: List[str] = Field(default_factory=list)


class ClearanceStatus(BaseModel):
    approved: bool
    notes: str = Field(min_length=1)


class IPClearanceOutput(BaseModel):
    title_conflict_check: TitleConflictCheck
    series_naming_check: SeriesNamingCheck
    character_naming_check: CharacterNamingCheck
    clearance_status: ClearanceStatus


class ExportSubReport(BaseModel):
    generated: bool
    valid: bool
    issues: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class FrontMatterReport(BaseModel):
    included_pages: List[str] = Field(default_factory=list)
    missing_recommended: List[str] = Field(default_factory=list)


class KDPReadinessOutput(BaseModel):
    kindle_ready: bool
    epub_report: ExportSubReport
    docx_report: ExportSubReport
    front_matter_report: FrontMatterReport
    recommendations: List[str] = Field(default_factory=list)

AGENT_OUTPUT_MODELS: Dict[str, type[BaseModel]] = {
    "market_intelligence": MarketIntelligenceOutput,
    "concept_definition": ConceptDefinitionOutput,
    "thematic_architecture": ThematicArchitectureOutput,
    "story_question": StoryQuestionOutput,
    "world_rules": WorldRulesOutput,
    "character_architecture": CharacterArchitectureOutput,
    "relationship_dynamics": RelationshipDynamicsOutput,
    "plot_structure": PlotStructureOutput,
    "pacing_design": PacingDesignOutput,
    "chapter_blueprint": ChapterBlueprintOutput,
    "voice_specification": VoiceSpecificationOutput,
    "draft_generation": DraftGenerationOutput,
    "continuity_audit": ContinuityAuditOutput,
    "emotional_validation": EmotionalValidationOutput,
    "originality_scan": OriginalityScanOutput,
    "plagiarism_audit": PlagiarismAuditOutput,
    "transformative_verification": TransformativeVerificationOutput,
    "structural_rewrite": StructuralRewriteOutput,
    "post_rewrite_scan": PostRewriteScanOutput,
    "line_edit": LineEditOutput,
    "beta_simulation": BetaSimulationOutput,
    "final_validation": FinalValidationOutput,
    "human_editor_review": HumanEditorReviewOutput,
    "production_readiness": ProductionReadinessOutput,
    "publishing_package": PublishingPackageOutput,
    "kdp_readiness": KDPReadinessOutput,
    "ip_clearance": IPClearanceOutput,
}

