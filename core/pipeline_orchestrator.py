"""
Pipeline Orchestrator for Multi-Agent Book Generation

Integrates with the existing Orchestrator to provide:
- Story Bible management and injection
- Chapter validation with retry logic
- Enhanced context building for each layer
- Generation logging and continuity tracking
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

from core.story_bible import StoryBible, ValidationResult, load_or_create
from core.orchestrator import Orchestrator, ExecutionContext
from models.state import BookProject, AgentStatus, LayerStatus
from models.agents import AGENT_REGISTRY

logger = logging.getLogger(__name__)


@dataclass
class LayerResult:
    """Result from running an agent layer."""
    layer_number: int
    agent_name: str
    success: bool
    output: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PipelineOrchestrator:
    """
    Enhanced orchestrator with Story Bible integration.

    Wraps the existing Orchestrator to add:
    - Story Bible state management
    - Chapter validation and retry
    - Enhanced context for generation
    - Continuity tracking
    """

    # Layer categories
    DEFINITION_LAYERS = [6, 7, 8, 10, 11]  # Write to Story Bible
    GENERATION_LAYERS = [12]  # Generate content
    VALIDATION_LAYERS = [13, 14, 18, 19]  # Validate content
    EDITING_LAYERS = [16, 17]  # Edit content

    LAYER_NAMES = {
        0: "orchestrator",
        1: "market_intelligence",
        2: "concept_definition",
        3: "thematic_architecture",
        4: "story_question",
        5: "world_rules",
        6: "character_architecture",
        7: "relationship_dynamics",
        8: "plot_structure",
        9: "pacing_design",
        10: "chapter_blueprint",
        11: "voice_specification",
        12: "draft_generation",
        13: "continuity_audit",
        14: "emotional_validation",
        15: "originality_scan",
        16: "structural_rewrite",
        17: "line_edit",
        18: "beta_simulation",
        19: "final_validation",
        20: "publishing_package"
    }

    def __init__(self, base_orchestrator: Orchestrator, project_dir: str = "projects"):
        """
        Initialize pipeline orchestrator.

        Args:
            base_orchestrator: The existing Orchestrator instance
            project_dir: Directory for project files
        """
        self.orchestrator = base_orchestrator
        self.project_dir = Path(project_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # Story Bible cache per project
        self._story_bibles: Dict[str, StoryBible] = {}

        # Layer results cache per project
        self._layer_results: Dict[str, Dict[int, LayerResult]] = {}

        # Generated chapters cache
        self._generated_chapters: Dict[str, Dict[int, str]] = {}

    # =========================================================================
    # STORY BIBLE MANAGEMENT
    # =========================================================================

    def get_story_bible(self, project: BookProject) -> StoryBible:
        """Get or create Story Bible for a project."""
        if project.project_id not in self._story_bibles:
            # Try to load from disk
            bible_path = self.project_dir / project.project_id / "story_bible.json"

            if bible_path.exists():
                try:
                    self._story_bibles[project.project_id] = StoryBible.load(str(bible_path))
                    logger.info(f"Loaded Story Bible for {project.project_id}")
                except Exception as e:
                    logger.warning(f"Failed to load Story Bible: {e}")
                    self._story_bibles[project.project_id] = StoryBible()
            else:
                self._story_bibles[project.project_id] = StoryBible()

            # Initialize from user constraints if present
            story_bible_text = project.user_constraints.get("story_bible", "")
            if story_bible_text:
                self._story_bibles[project.project_id].load_from_text(story_bible_text)
                self._story_bibles[project.project_id].meta["title"] = project.title

        return self._story_bibles[project.project_id]

    def save_story_bible(self, project: BookProject):
        """Save Story Bible for a project."""
        if project.project_id in self._story_bibles:
            project_path = self.project_dir / project.project_id
            project_path.mkdir(parents=True, exist_ok=True)
            bible_path = project_path / "story_bible.json"

            try:
                self._story_bibles[project.project_id].save(str(bible_path))
                logger.info(f"Saved Story Bible for {project.project_id}")
            except Exception as e:
                logger.error(f"Failed to save Story Bible: {e}")

    def update_story_bible_from_agent(self, project: BookProject, agent_id: str, output: Dict):
        """Update Story Bible with agent output."""
        agent_def = AGENT_REGISTRY.get(agent_id)
        if not agent_def:
            return

        layer = agent_def.layer
        if layer in self.DEFINITION_LAYERS:
            story_bible = self.get_story_bible(project)
            story_bible.update_from_layer(layer, output)
            self.save_story_bible(project)
            logger.info(f"Updated Story Bible from agent {agent_id} (layer {layer})")

    # =========================================================================
    # ENHANCED CONTEXT BUILDING
    # =========================================================================

    def build_enhanced_context(self, project: BookProject, agent_id: str) -> Dict[str, Any]:
        """
        Build enhanced context with Story Bible integration.

        Args:
            project: The book project
            agent_id: The agent requesting context

        Returns:
            Enhanced context dictionary
        """
        # Get base inputs from existing orchestrator
        inputs = self.orchestrator.gather_inputs(project, agent_id)

        # Add user constraints (includes story_bible text)
        inputs["user_constraints"] = project.user_constraints

        # Get agent layer
        agent_def = AGENT_REGISTRY.get(agent_id)
        layer = agent_def.layer if agent_def else 0

        # Add Story Bible context
        story_bible = self.get_story_bible(project)
        inputs["story_bible_context"] = story_bible.get_context_for_layer(layer)

        # For generation layers, add injection text
        if layer in self.GENERATION_LAYERS:
            inputs["story_bible_injection"] = story_bible.build_chapter_injection(0)

        # Add generated chapters for validation layers
        if layer in self.VALIDATION_LAYERS or layer in self.EDITING_LAYERS:
            if project.project_id in self._generated_chapters:
                inputs["generated_chapters"] = self._generated_chapters[project.project_id]

        return inputs

    # =========================================================================
    # CHAPTER GENERATION WITH VALIDATION
    # =========================================================================

    async def generate_chapter_with_validation(
        self,
        project: BookProject,
        chapter_number: int,
        chapter_writer_func: Callable,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate a chapter with Story Bible validation and retry.

        Args:
            project: The book project
            chapter_number: Chapter to generate
            chapter_writer_func: Async function to generate chapter
            max_retries: Maximum retry attempts

        Returns:
            Chapter result dictionary
        """
        story_bible = self.get_story_bible(project)

        # Build context with Story Bible injection
        context = self.build_enhanced_context(project, "draft_generation")
        context["chapter_number"] = chapter_number
        context["story_bible_injection"] = story_bible.build_chapter_injection(chapter_number)

        # Generate chapter
        result = await chapter_writer_func(context, chapter_number)

        if result.get("error"):
            return result

        chapter_text = result.get("text", "")

        # Validate against Story Bible
        validation = story_bible.validate_chapter(chapter_text, chapter_number)

        # Retry on validation failure
        retry_count = 0
        while not validation.passed and retry_count < max_retries:
            logger.warning(
                f"Chapter {chapter_number} validation failed. "
                f"Retry {retry_count + 1}/{max_retries}"
            )

            # Add error feedback to context
            context["validation_errors"] = [
                f"{e.get('type')}: {e.get('message')}"
                for e in validation.errors
            ]
            context["previous_draft"] = chapter_text

            # Regenerate
            result = await chapter_writer_func(context, chapter_number)
            if result.get("error"):
                break

            chapter_text = result.get("text", "")
            validation = story_bible.validate_chapter(chapter_text, chapter_number)
            retry_count += 1

        # Log generation
        story_bible.log_chapter_generation(
            chapter_number,
            facts_established=[],  # Could extract with NLP
            validation=validation
        )

        # Cache generated chapter
        if project.project_id not in self._generated_chapters:
            self._generated_chapters[project.project_id] = {}
        self._generated_chapters[project.project_id][chapter_number] = chapter_text

        # Add validation info to result
        result["validation"] = {
            "passed": validation.passed,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "retry_count": retry_count
        }

        return result

    # =========================================================================
    # CONTINUITY AUDIT
    # =========================================================================

    def run_continuity_audit(self, project: BookProject) -> Dict:
        """
        Run full continuity audit across all chapters.

        Args:
            project: The book project

        Returns:
            Audit results dictionary
        """
        story_bible = self.get_story_bible(project)
        chapters = self._generated_chapters.get(project.project_id, {})

        # Also check manuscript chapters
        manuscript_chapters = project.manuscript.get("chapters", [])
        for ch in manuscript_chapters:
            ch_num = ch.get("number")
            if ch_num and ch.get("text"):
                chapters[ch_num] = ch["text"]

        all_errors = []
        all_warnings = []

        for chapter_num, chapter_text in chapters.items():
            validation = story_bible.validate_chapter(chapter_text, chapter_num)

            for error in validation.errors:
                error["chapter"] = chapter_num
                all_errors.append(error)

            for warning in validation.warnings:
                warning["chapter"] = chapter_num
                all_warnings.append(warning)

        # Summarize by error type
        error_summary = {}
        for error in all_errors:
            error_type = error.get("type", "unknown")
            error_summary[error_type] = error_summary.get(error_type, 0) + 1

        return {
            "passed": len(all_errors) == 0,
            "total_chapters": len(chapters),
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings),
            "errors": all_errors,
            "warnings": all_warnings,
            "error_summary": error_summary
        }

    # =========================================================================
    # PROJECT STATE MANAGEMENT
    # =========================================================================

    def save_project_state(self, project: BookProject):
        """Save complete project state including Story Bible."""
        project_path = self.project_dir / project.project_id
        project_path.mkdir(parents=True, exist_ok=True)

        # Save Story Bible
        self.save_story_bible(project)

        # Save generated chapters
        chapters_dir = project_path / "chapters"
        chapters_dir.mkdir(exist_ok=True)

        chapters = self._generated_chapters.get(project.project_id, {})
        for ch_num, text in chapters.items():
            ch_path = chapters_dir / f"chapter_{ch_num:02d}.md"
            try:
                with open(ch_path, 'w', encoding='utf-8') as f:
                    f.write(text)
            except Exception as e:
                logger.error(f"Failed to save chapter {ch_num}: {e}")

        # Save layer results
        if project.project_id in self._layer_results:
            results_path = project_path / "layer_results.json"
            results_data = {
                str(k): {
                    "layer_number": v.layer_number,
                    "agent_name": v.agent_name,
                    "success": v.success,
                    "errors": v.errors,
                    "warnings": v.warnings
                }
                for k, v in self._layer_results[project.project_id].items()
            }
            try:
                with open(results_path, 'w', encoding='utf-8') as f:
                    json.dump(results_data, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save layer results: {e}")

        logger.info(f"Saved project state for {project.project_id}")

    def load_project_state(self, project: BookProject):
        """Load project state from disk."""
        project_path = self.project_dir / project.project_id

        # Load Story Bible (handled by get_story_bible)
        self.get_story_bible(project)

        # Load generated chapters
        chapters_dir = project_path / "chapters"
        if chapters_dir.exists():
            self._generated_chapters[project.project_id] = {}
            for ch_file in sorted(chapters_dir.glob("chapter_*.md")):
                ch_num = int(ch_file.stem.split("_")[1])
                try:
                    with open(ch_file, 'r', encoding='utf-8') as f:
                        self._generated_chapters[project.project_id][ch_num] = f.read()
                except Exception as e:
                    logger.error(f"Failed to load chapter {ch_num}: {e}")

        # Load layer results
        results_path = project_path / "layer_results.json"
        if results_path.exists():
            try:
                with open(results_path, 'r', encoding='utf-8') as f:
                    results_data = json.load(f)
                self._layer_results[project.project_id] = {
                    int(k): LayerResult(
                        layer_number=v["layer_number"],
                        agent_name=v["agent_name"],
                        success=v["success"],
                        errors=v.get("errors", []),
                        warnings=v.get("warnings", [])
                    )
                    for k, v in results_data.items()
                }
            except Exception as e:
                logger.error(f"Failed to load layer results: {e}")

        logger.info(f"Loaded project state for {project.project_id}")

    # =========================================================================
    # REPORTING
    # =========================================================================

    def generate_project_report(self, project: BookProject) -> Dict:
        """Generate comprehensive project report."""
        story_bible = self.get_story_bible(project)
        chapters = self._generated_chapters.get(project.project_id, {})

        # Count completed layers
        completed_layers = 0
        for layer in project.layers.values():
            if layer.status == LayerStatus.COMPLETED:
                completed_layers += 1

        # Count written chapters
        manuscript_chapters = len(project.manuscript.get("chapters", []))

        return {
            "project_id": project.project_id,
            "title": project.title,
            "status": project.status,
            "generated_at": datetime.now().isoformat(),
            "layers": {
                "total": len(project.layers),
                "completed": completed_layers
            },
            "chapters": {
                "in_manuscript": manuscript_chapters,
                "cached": len(chapters)
            },
            "story_bible": {
                "has_raw_text": bool(story_bible.raw_text),
                "characters": len(story_bible.characters),
                "timeline_events": len(story_bible.timeline),
                "locked_facts": len(story_bible.locked_facts)
            }
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_pipeline_orchestrator(
    base_orchestrator: Orchestrator,
    project_dir: str = "projects"
) -> PipelineOrchestrator:
    """
    Create a PipelineOrchestrator instance.

    Args:
        base_orchestrator: The existing Orchestrator
        project_dir: Directory for project files

    Returns:
        Configured PipelineOrchestrator
    """
    return PipelineOrchestrator(base_orchestrator, project_dir)
