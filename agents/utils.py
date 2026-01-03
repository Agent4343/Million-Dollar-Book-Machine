"""
Production Utilities for Book Generation Agents

Provides:
- Retry logic with exponential backoff
- Progress tracking and callbacks
- Quality metrics calculation
- Token management
- Cost estimation
- Rate limiting
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


# =============================================================================
# RETRY LOGIC
# =============================================================================

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: float = 0.1
    retryable_exceptions: tuple = (Exception,)
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt with exponential backoff and jitter."""
        import random
        delay = min(
            self.max_delay,
            self.base_delay * (self.exponential_base ** attempt)
        )
        # Add jitter
        jitter_range = delay * self.jitter
        delay += random.uniform(-jitter_range, jitter_range)
        return max(0, delay)


async def retry_async(
    func: Callable[..., T],
    *args,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    **kwargs
) -> T:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        config: Retry configuration
        on_retry: Callback called on each retry with (attempt, exception)
        *args, **kwargs: Arguments to pass to func
    
    Returns:
        Result of func
    
    Raises:
        Last exception if all retries exhausted
    """
    config = config or RetryConfig()
    last_exception = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt < config.max_retries:
                delay = config.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s"
                )
                
                if on_retry:
                    on_retry(attempt + 1, e)
                
                await asyncio.sleep(delay)
            else:
                logger.error(f"All {config.max_retries + 1} attempts failed")
    
    raise last_exception


def with_retry(config: Optional[RetryConfig] = None):
    """Decorator to add retry logic to async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(func, *args, config=config, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# PROGRESS TRACKING
# =============================================================================

@dataclass
class ProgressEvent:
    """Single progress event."""
    timestamp: datetime
    stage: str
    message: str
    progress_pct: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressTracker:
    """
    Track progress through book generation pipeline.
    
    Usage:
        tracker = ProgressTracker(total_stages=20)
        tracker.add_callback(lambda e: print(f"{e.progress_pct}%: {e.message}"))
        
        tracker.start_stage("market_intelligence")
        # ... do work ...
        tracker.complete_stage("market_intelligence", {"score": 85})
    """
    total_stages: int
    current_stage: int = 0
    events: List[ProgressEvent] = field(default_factory=list)
    callbacks: List[Callable[[ProgressEvent], None]] = field(default_factory=list)
    stage_weights: Dict[str, float] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialize default stage weights if not provided."""
        if not self.stage_weights:
            # Default weights - draft generation is heaviest
            self.stage_weights = {
                "orchestrator": 0.01,
                "market_intelligence": 0.03,
                "concept_definition": 0.03,
                "thematic_architecture": 0.03,
                "story_question": 0.03,
                "world_rules": 0.04,
                "character_architecture": 0.05,
                "relationship_dynamics": 0.04,
                "plot_structure": 0.05,
                "pacing_design": 0.04,
                "chapter_blueprint": 0.06,
                "voice_specification": 0.04,
                "draft_generation": 0.35,  # Heaviest - actual chapter writing
                "continuity_audit": 0.04,
                "emotional_validation": 0.04,
                "originality_scan": 0.03,
                "structural_rewrite": 0.05,
                "line_edit": 0.06,
                "beta_simulation": 0.03,
                "final_validation": 0.02,
                "publishing_package": 0.03,
            }
    
    def add_callback(self, callback: Callable[[ProgressEvent], None]) -> None:
        """Add a progress callback."""
        self.callbacks.append(callback)
    
    def _emit_event(self, event: ProgressEvent) -> None:
        """Emit event to all callbacks."""
        self.events.append(event)
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
    
    def _calculate_progress(self, stage: str, stage_progress: float = 0.0) -> float:
        """Calculate overall progress percentage."""
        completed_weight = sum(
            self.stage_weights.get(s, 1/self.total_stages)
            for s in [e.stage for e in self.events if "completed" in e.message.lower()]
        )
        current_weight = self.stage_weights.get(stage, 1/self.total_stages) * stage_progress
        return min(100, (completed_weight + current_weight) * 100)
    
    def start(self) -> None:
        """Mark pipeline start."""
        self.started_at = datetime.utcnow()
        event = ProgressEvent(
            timestamp=self.started_at,
            stage="pipeline",
            message="Book generation started",
            progress_pct=0.0
        )
        self._emit_event(event)
    
    def start_stage(self, stage: str, message: Optional[str] = None) -> None:
        """Mark stage start."""
        event = ProgressEvent(
            timestamp=datetime.utcnow(),
            stage=stage,
            message=message or f"Starting {stage.replace('_', ' ')}",
            progress_pct=self._calculate_progress(stage, 0.0)
        )
        self._emit_event(event)
    
    def update_stage(
        self, 
        stage: str, 
        progress: float, 
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update progress within a stage."""
        event = ProgressEvent(
            timestamp=datetime.utcnow(),
            stage=stage,
            message=message or f"{stage} {int(progress*100)}% complete",
            progress_pct=self._calculate_progress(stage, progress),
            metadata=metadata or {}
        )
        self._emit_event(event)
    
    def complete_stage(
        self, 
        stage: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Mark stage complete."""
        self.current_stage += 1
        event = ProgressEvent(
            timestamp=datetime.utcnow(),
            stage=stage,
            message=f"Completed {stage.replace('_', ' ')}",
            progress_pct=self._calculate_progress(stage, 1.0),
            metadata=metadata or {}
        )
        self._emit_event(event)
    
    def complete(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mark pipeline complete."""
        elapsed = None
        if self.started_at:
            elapsed = (datetime.utcnow() - self.started_at).total_seconds()
        
        event = ProgressEvent(
            timestamp=datetime.utcnow(),
            stage="pipeline",
            message="Book generation complete",
            progress_pct=100.0,
            metadata={
                "elapsed_seconds": elapsed,
                "stages_completed": self.current_stage,
                **(metadata or {})
            }
        )
        self._emit_event(event)
    
    def error(self, stage: str, error: Exception) -> None:
        """Record an error."""
        event = ProgressEvent(
            timestamp=datetime.utcnow(),
            stage=stage,
            message=f"Error in {stage}: {str(error)}",
            progress_pct=self._calculate_progress(stage, 0.0),
            metadata={"error": str(error), "error_type": type(error).__name__}
        )
        self._emit_event(event)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary."""
        return {
            "total_stages": self.total_stages,
            "completed_stages": self.current_stage,
            "progress_pct": self.events[-1].progress_pct if self.events else 0,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "events_count": len(self.events),
            "last_event": self.events[-1].message if self.events else None
        }


# =============================================================================
# QUALITY METRICS
# =============================================================================

@dataclass
class QualityMetrics:
    """Aggregated quality metrics for a generated book."""
    
    # Core scores
    concept_score: float = 0.0
    character_depth_score: float = 0.0
    plot_coherence_score: float = 0.0
    voice_consistency_score: float = 0.0
    
    # Validation scores
    continuity_score: float = 0.0
    emotional_impact_score: float = 0.0
    originality_score: float = 0.0
    
    # Final scores
    beta_reader_score: float = 0.0
    market_fit_score: float = 0.0
    
    # Metadata
    word_count: int = 0
    chapter_count: int = 0
    target_word_count: int = 80000
    
    @property
    def overall_score(self) -> float:
        """Calculate weighted overall quality score."""
        weights = {
            "concept": 0.10,
            "character": 0.15,
            "plot": 0.15,
            "voice": 0.10,
            "continuity": 0.10,
            "emotional": 0.15,
            "originality": 0.10,
            "beta": 0.10,
            "market": 0.05
        }
        
        scores = {
            "concept": self.concept_score,
            "character": self.character_depth_score,
            "plot": self.plot_coherence_score,
            "voice": self.voice_consistency_score,
            "continuity": self.continuity_score,
            "emotional": self.emotional_impact_score,
            "originality": self.originality_score,
            "beta": self.beta_reader_score,
            "market": self.market_fit_score
        }
        
        return sum(scores[k] * weights[k] for k in weights)
    
    @property
    def word_count_achievement(self) -> float:
        """Percentage of target word count achieved."""
        if self.target_word_count == 0:
            return 0.0
        return min(100, (self.word_count / self.target_word_count) * 100)
    
    @property
    def publication_ready(self) -> bool:
        """Whether the book meets publication standards."""
        return (
            self.overall_score >= 75 and
            self.word_count_achievement >= 90 and
            self.continuity_score >= 70 and
            self.originality_score >= 70
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scores": {
                "concept": self.concept_score,
                "character_depth": self.character_depth_score,
                "plot_coherence": self.plot_coherence_score,
                "voice_consistency": self.voice_consistency_score,
                "continuity": self.continuity_score,
                "emotional_impact": self.emotional_impact_score,
                "originality": self.originality_score,
                "beta_reader": self.beta_reader_score,
                "market_fit": self.market_fit_score,
                "overall": self.overall_score
            },
            "metrics": {
                "word_count": self.word_count,
                "chapter_count": self.chapter_count,
                "target_word_count": self.target_word_count,
                "word_count_achievement_pct": self.word_count_achievement
            },
            "status": {
                "publication_ready": self.publication_ready,
                "overall_rating": self._get_rating()
            }
        }
    
    def _get_rating(self) -> str:
        """Get human-readable rating."""
        score = self.overall_score
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Needs Work"
    
    @classmethod
    def from_pipeline_outputs(cls, outputs: Dict[str, Any]) -> 'QualityMetrics':
        """Create metrics from pipeline agent outputs."""
        metrics = cls()
        
        # Extract from concept definition
        concept = outputs.get("concept_definition", {})
        metrics.concept_score = concept.get("concept_strength_score", 75)
        
        # Extract from character architecture
        character = outputs.get("character_architecture", {})
        metrics.character_depth_score = character.get("character_depth_score", 75)
        
        # Extract from plot structure
        plot = outputs.get("plot_structure", {})
        metrics.plot_coherence_score = plot.get("plot_coherence_score", 75)
        
        # Extract from voice specification
        voice = outputs.get("voice_specification", {})
        metrics.voice_consistency_score = voice.get("voice_specification_score", 75)
        
        # Extract from validation agents
        continuity = outputs.get("continuity_audit", {})
        metrics.continuity_score = continuity.get("continuity_report", {}).get("overall_score", 75)
        
        emotional = outputs.get("emotional_validation", {})
        metrics.emotional_impact_score = emotional.get("overall_emotional_score", 75)
        
        originality = outputs.get("originality_scan", {})
        metrics.originality_score = originality.get("overall_originality_score", 75)
        
        beta = outputs.get("beta_simulation", {})
        metrics.beta_reader_score = (beta.get("predicted_ratings", {}).get("average", 4.0) / 5.0) * 100
        metrics.market_fit_score = beta.get("market_readiness", {}).get("market_fit_score", 75)
        
        # Extract word counts
        draft = outputs.get("draft_generation", {})
        metrics.word_count = draft.get("total_word_count", 0)
        metrics.chapter_count = len(draft.get("chapters", []))
        
        constraints = outputs.get("user_constraints", {})
        metrics.target_word_count = constraints.get("target_word_count", 80000)
        
        return metrics


# =============================================================================
# TOKEN & COST MANAGEMENT
# =============================================================================

@dataclass
class TokenUsage:
    """Track token usage for cost estimation."""
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = "claude-sonnet-4-20250514"
    
    # Pricing per 1M tokens (approximate, update as needed)
    PRICING = {
        "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4o": {"input": 5.0, "output": 15.0},
    }
    
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
    
    @property
    def estimated_cost(self) -> float:
        """Estimate cost in USD."""
        pricing = self.PRICING.get(self.model, {"input": 3.0, "output": 15.0})
        input_cost = (self.input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost
    
    def add(self, input_tokens: int, output_tokens: int) -> None:
        """Add token usage."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "estimated_cost_usd": round(self.estimated_cost, 2)
        }


class TokenTracker:
    """Track token usage across the pipeline."""
    
    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model
        self.by_stage: Dict[str, TokenUsage] = {}
        self.total = TokenUsage(model=model)
    
    def record(self, stage: str, input_tokens: int, output_tokens: int) -> None:
        """Record token usage for a stage."""
        if stage not in self.by_stage:
            self.by_stage[stage] = TokenUsage(model=self.model)
        
        self.by_stage[stage].add(input_tokens, output_tokens)
        self.total.add(input_tokens, output_tokens)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get usage summary."""
        return {
            "total": self.total.to_dict(),
            "by_stage": {
                stage: usage.to_dict()
                for stage, usage in self.by_stage.items()
            },
            "heaviest_stages": sorted(
                [(s, u.total_tokens) for s, u in self.by_stage.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """
    Simple rate limiter for API calls.
    
    Usage:
        limiter = RateLimiter(requests_per_minute=50)
        
        async def make_request():
            async with limiter:
                await api_call()
    """
    
    def __init__(
        self,
        requests_per_minute: int = 50,
        tokens_per_minute: int = 100000
    ):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.request_times: List[float] = []
        self.token_usage: List[tuple] = []  # (timestamp, tokens)
        self._lock = asyncio.Lock()
    
    async def acquire(self, estimated_tokens: int = 1000) -> None:
        """Wait until rate limit allows the request."""
        async with self._lock:
            now = time.time()
            minute_ago = now - 60
            
            # Clean old entries
            self.request_times = [t for t in self.request_times if t > minute_ago]
            self.token_usage = [(t, tok) for t, tok in self.token_usage if t > minute_ago]
            
            # Check request rate
            if len(self.request_times) >= self.requests_per_minute:
                sleep_time = self.request_times[0] - minute_ago
                if sleep_time > 0:
                    logger.debug(f"Rate limit: waiting {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            
            # Check token rate
            current_tokens = sum(tok for _, tok in self.token_usage)
            if current_tokens + estimated_tokens > self.tokens_per_minute:
                # Find when we can proceed
                sleep_time = self.token_usage[0][0] - minute_ago
                if sleep_time > 0:
                    logger.debug(f"Token limit: waiting {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            
            # Record this request
            self.request_times.append(time.time())
            self.token_usage.append((time.time(), estimated_tokens))
    
    async def __aenter__(self):
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# =============================================================================
# CHUNK PROCESSING
# =============================================================================

async def process_in_chunks(
    items: List[Any],
    processor: Callable[[Any], Any],
    chunk_size: int = 5,
    delay_between_chunks: float = 1.0,
    on_chunk_complete: Optional[Callable[[int, int], None]] = None
) -> List[Any]:
    """
    Process items in chunks with delays.
    
    Useful for rate-limited APIs or memory management.
    
    Args:
        items: Items to process
        processor: Async function to process each item
        chunk_size: Items per chunk
        delay_between_chunks: Seconds to wait between chunks
        on_chunk_complete: Callback(completed_count, total_count)
    
    Returns:
        List of results
    """
    results = []
    total = len(items)
    
    for i in range(0, total, chunk_size):
        chunk = items[i:i + chunk_size]
        
        # Process chunk
        chunk_results = await asyncio.gather(
            *[processor(item) for item in chunk],
            return_exceptions=True
        )
        
        results.extend(chunk_results)
        
        completed = min(i + chunk_size, total)
        if on_chunk_complete:
            on_chunk_complete(completed, total)
        
        # Delay before next chunk (unless last)
        if completed < total and delay_between_chunks > 0:
            await asyncio.sleep(delay_between_chunks)
    
    return results


# =============================================================================
# TEXT UTILITIES
# =============================================================================

def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    
    Rough approximation: ~4 characters per token for English.
    """
    return len(text) // 4


def chunk_text(text: str, max_tokens: int = 3000, overlap: int = 200) -> List[str]:
    """
    Split text into chunks suitable for LLM processing.
    
    Args:
        text: Text to split
        max_tokens: Maximum tokens per chunk
        overlap: Token overlap between chunks for context
    
    Returns:
        List of text chunks
    """
    max_chars = max_tokens * 4
    overlap_chars = overlap * 4
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chars
        
        # Try to break at paragraph
        if end < len(text):
            # Look for paragraph break
            para_break = text.rfind('\n\n', start, end)
            if para_break > start + max_chars // 2:
                end = para_break + 2
            else:
                # Look for sentence break
                sentence_break = text.rfind('. ', start, end)
                if sentence_break > start + max_chars // 2:
                    end = sentence_break + 2
        
        chunks.append(text[start:end].strip())
        start = end - overlap_chars
    
    return chunks


def clean_generated_text(text: str) -> str:
    """
    Clean LLM-generated text.
    
    Removes common artifacts like:
    - Triple quotes
    - Markdown headers within prose
    - Multiple consecutive blank lines
    """
    import re
    
    # Remove triple quotes
    text = text.replace('"""', '').replace("'''", '')
    
    # Remove markdown headers within prose
    text = re.sub(r'\n#+\s+[^\n]+\n', '\n', text)
    
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
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
]
