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


AGENT_OUTPUT_MODELS: Dict[str, type[BaseModel]] = {
    "market_intelligence": MarketIntelligenceOutput,
    "concept_definition": ConceptDefinitionOutput,
    "thematic_architecture": ThematicArchitectureOutput,
    "story_question": StoryQuestionOutput,
    "world_rules": WorldRulesOutput,
    "character_architecture": CharacterArchitectureOutput,
    "plot_structure": PlotStructureOutput,
    "pacing_design": PacingDesignOutput,
    "chapter_blueprint": ChapterBlueprintOutput,
    "voice_specification": VoiceSpecificationOutput,
}

