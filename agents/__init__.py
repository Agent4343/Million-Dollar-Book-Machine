"""
Book Development Agent System

Production-ready multi-agent system for generating complete books.

Agent Categories:
- Strategic Agents (Layers 0-4): Foundation and concept development
- Story System Agents (Layers 5-7): World, character, and relationship design
- Structural Agents (Layers 8-12): Plot, pacing, and draft generation
- Validation Agents (Layers 13-20): Quality control and publishing prep
- Chapter Writer: Dedicated agent for individual chapter writing

Utilities:
- Retry logic with exponential backoff
- Progress tracking
- Quality metrics
- Token management
- Rate limiting
"""

# Strategic Foundation Agents
from agents.strategic import (
    STRATEGIC_EXECUTORS,
    execute_orchestrator,
    execute_market_intelligence,
    execute_concept_definition,
    execute_thematic_architecture,
    execute_story_question,
)

# Story System Agents
from agents.story_system import (
    STORY_SYSTEM_EXECUTORS,
    execute_world_rules,
    execute_character_architecture,
    execute_relationship_dynamics,
)

# Structural Engine Agents
from agents.structural import (
    STRUCTURAL_EXECUTORS,
    execute_plot_structure,
    execute_pacing_design,
    execute_chapter_blueprint,
    execute_voice_specification,
    execute_draft_generation,
)

# Validation Agents
from agents.validation import (
    VALIDATION_EXECUTORS,
    execute_continuity_audit,
    execute_emotional_validation,
    execute_originality_scan,
    execute_plagiarism_audit,
    execute_transformative_verification,
    execute_structural_rewrite,
    execute_post_rewrite_scan,
    execute_line_edit,
    execute_beta_simulation,
    execute_final_validation,
    execute_publishing_package,
    execute_ip_clearance,
)

# Chapter Writer
from agents.chapter_writer import (
    CHAPTER_WRITER_EXECUTORS,
    execute_chapter_writer,
    generate_chapters_batch,
)

# Utilities
from agents.utils import (
    RetryConfig,
    retry_async,
    with_retry,
    ProgressTracker,
    ProgressEvent,
    QualityMetrics,
    TokenUsage,
    TokenTracker,
    RateLimiter,
    process_in_chunks,
    estimate_tokens,
    chunk_text,
    clean_generated_text,
)


# Combined executor registry
ALL_EXECUTORS = {
    **STRATEGIC_EXECUTORS,
    **STORY_SYSTEM_EXECUTORS,
    **STRUCTURAL_EXECUTORS,
    **VALIDATION_EXECUTORS,
    **CHAPTER_WRITER_EXECUTORS,
}


def get_executor(agent_id: str):
    """Get the executor function for an agent."""
    return ALL_EXECUTORS.get(agent_id)


def register_all_executors(orchestrator) -> None:
    """Register all agent executors with an orchestrator."""
    for agent_id, executor in ALL_EXECUTORS.items():
        orchestrator.register_executor(agent_id, executor)


__all__ = [
    # Executor registries
    'STRATEGIC_EXECUTORS',
    'STORY_SYSTEM_EXECUTORS',
    'STRUCTURAL_EXECUTORS',
    'VALIDATION_EXECUTORS',
    'CHAPTER_WRITER_EXECUTORS',
    'ALL_EXECUTORS',
    
    # Strategic agents
    'execute_orchestrator',
    'execute_market_intelligence',
    'execute_concept_definition',
    'execute_thematic_architecture',
    'execute_story_question',
    
    # Story system agents
    'execute_world_rules',
    'execute_character_architecture',
    'execute_relationship_dynamics',
    
    # Structural agents
    'execute_plot_structure',
    'execute_pacing_design',
    'execute_chapter_blueprint',
    'execute_voice_specification',
    'execute_draft_generation',
    
    # Validation agents
    'execute_continuity_audit',
    'execute_emotional_validation',
    'execute_originality_scan',
    'execute_plagiarism_audit',
    'execute_transformative_verification',
    'execute_structural_rewrite',
    'execute_post_rewrite_scan',
    'execute_line_edit',
    'execute_beta_simulation',
    'execute_final_validation',
    'execute_publishing_package',
    'execute_ip_clearance',
    
    # Chapter writer
    'execute_chapter_writer',
    'generate_chapters_batch',
    
    # Utilities
    'RetryConfig',
    'retry_async',
    'with_retry',
    'ProgressTracker',
    'ProgressEvent',
    'QualityMetrics',
    'TokenUsage',
    'TokenTracker',
    'RateLimiter',
    'process_in_chunks',
    'estimate_tokens',
    'chunk_text',
    'clean_generated_text',
    
    # Helper functions
    'get_executor',
    'register_all_executors',
]
