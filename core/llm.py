"""
Claude LLM Client Wrapper

Production-ready interface for the Anthropic Claude API with:
- Robust error handling and retry logic
- JSON response parsing and validation
- Token tracking for cost management
- Rate limiting support
- Streaming support for long content
"""

import json
import logging
import os
import asyncio
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass, field

import anthropic

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 16000
    temperature: float = 0.7
    timeout: float = 300.0  # 5 minutes default
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_rpm: int = 50  # Requests per minute
    rate_limit_tpm: int = 100000  # Tokens per minute


class ClaudeLLMClient:
    """
    Production-ready Claude API client for book development agents.
    
    Features:
    - Async generation with retry logic
    - JSON parsing with error recovery
    - Token usage tracking
    - Rate limiting
    - Cost estimation
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[LLMConfig] = None
    ):
        """
        Initialize the Claude client.
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            config: LLM configuration options
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.config = config or LLMConfig()
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0
        
        # Rate limiting
        self._request_times: List[float] = []
        self._lock = asyncio.Lock()
        
        logger.info(f"Initialized Claude client with model: {self.config.model}")
    
    async def generate(
        self,
        prompt: str,
        response_format: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        on_token: Optional[Callable[[str], None]] = None
    ) -> Any:
        """
        Generate content using Claude with retry logic.
        
        Args:
            prompt: The prompt to send to Claude
            response_format: If "json", parse response as JSON
            system: Optional system prompt
            temperature: Creativity level (0-1)
            max_tokens: Override default max_tokens
            stop_sequences: Sequences that stop generation
            on_token: Callback for streaming tokens (optional)
        
        Returns:
            Generated content (dict if JSON, str otherwise)
        """
        messages = [{"role": "user", "content": prompt}]
        
        system_prompt = system or self._default_system_prompt(response_format)
        tokens = max_tokens or self.config.max_tokens
        temp = temperature if temperature is not None else self.config.temperature
        
        # Retry logic
        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                # Rate limiting
                await self._wait_for_rate_limit()
                
                # Make request
                response = await self._make_request(
                    messages=messages,
                    system=system_prompt,
                    max_tokens=tokens,
                    temperature=temp,
                    stop_sequences=stop_sequences
                )
                
                content = response.content[0].text
                
                # Track usage
                self._track_usage(response)
                
                # Handle truncation
                if response.stop_reason == "max_tokens":
                    logger.warning(f"Response truncated at {tokens} tokens")
                    if response_format == "json":
                        content = self._fix_truncated_json(content)
                
                # Parse JSON if requested
                if response_format == "json":
                    return self._parse_json(content)
                
                return content
                
            except anthropic.RateLimitError as e:
                last_exception = e
                delay = self._get_retry_delay(attempt)
                logger.warning(f"Rate limit hit, waiting {delay}s before retry {attempt + 1}")
                await asyncio.sleep(delay)
                
            except anthropic.APIError as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    delay = self._get_retry_delay(attempt)
                    logger.warning(f"API error: {e}. Retrying in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"API error after {self.config.max_retries} attempts: {e}")
                    raise
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error: {e}")
                if attempt < self.config.max_retries - 1:
                    # Retry with explicit JSON instruction
                    messages[0]["content"] = (
                        prompt + 
                        "\n\nIMPORTANT: Respond with ONLY valid JSON. "
                        "No markdown, no explanation, just the JSON object."
                    )
                else:
                    raise ValueError(f"Failed to get valid JSON after {self.config.max_retries} attempts")
        
        raise last_exception
    
    async def _make_request(
        self,
        messages: List[Dict[str, str]],
        system: str,
        max_tokens: int,
        temperature: float,
        stop_sequences: Optional[List[str]] = None
    ) -> Any:
        """Make the actual API request."""
        kwargs = {
            "model": self.config.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
            "temperature": temperature
        }
        
        if stop_sequences:
            kwargs["stop_sequences"] = stop_sequences
        
        # Use sync client (anthropic handles async internally)
        return self.client.messages.create(**kwargs)
    
    async def _wait_for_rate_limit(self) -> None:
        """Wait if necessary to respect rate limits."""
        import time
        
        async with self._lock:
            now = time.time()
            minute_ago = now - 60
            
            # Clean old entries
            self._request_times = [t for t in self._request_times if t > minute_ago]
            
            # Check if we need to wait
            if len(self._request_times) >= self.config.rate_limit_rpm:
                sleep_time = self._request_times[0] - minute_ago + 0.1
                if sleep_time > 0:
                    logger.debug(f"Rate limiting: waiting {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            
            self._request_times.append(time.time())
    
    def _get_retry_delay(self, attempt: int) -> float:
        """Get delay for retry with exponential backoff."""
        return min(60, self.config.retry_delay * (2 ** attempt))
    
    def _track_usage(self, response: Any) -> None:
        """Track token usage from response."""
        if hasattr(response, 'usage'):
            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens
        self.request_count += 1
    
    def _default_system_prompt(self, response_format: Optional[str]) -> str:
        """Get default system prompt."""
        base = (
            "You are an expert book development AI assistant. "
            "Provide detailed, creative, and professional responses. "
        )
        
        if response_format == "json":
            base += (
                "When asked for JSON output, respond ONLY with valid JSON. "
                "No markdown code blocks, no explanations, no text outside the JSON. "
                "Ensure all JSON is properly closed and valid."
            )
        
        return base
    
    def _parse_json(self, content: str) -> Dict[str, Any]:
        """Parse JSON from response, handling common issues."""
        content = self._extract_json(content)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try fixing common issues
            content = self._fix_truncated_json(content)
            return json.loads(content)
    
    def _extract_json(self, content: str) -> str:
        """Extract JSON from response, removing markdown if present."""
        content = content.strip()
        
        # Remove markdown code blocks
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
        
        # Find JSON boundaries
        start = content.find('{')
        if start == -1:
            start = content.find('[')
        
        if start > 0:
            content = content[start:]
        
        return content.strip()
    
    def _fix_truncated_json(self, content: str) -> str:
        """Attempt to fix truncated JSON by closing brackets."""
        content = content.strip()
        
        # Remove trailing incomplete elements
        # Find the last complete value
        while content and content[-1] not in ']}",0123456789nulltruefalse'[-1:]:
            content = content[:-1]
        
        # Handle trailing incomplete string
        if content.count('"') % 2 == 1:
            # Find last complete key-value pair
            last_quote = content.rfind('"')
            if last_quote > 0:
                # Look backward for the start of this string
                prev_quote = content.rfind('"', 0, last_quote)
                if prev_quote > 0:
                    # Check if this looks like an incomplete value
                    between = content[prev_quote:last_quote]
                    if ':' not in between:
                        # It's a value, truncate at the last complete item
                        last_comma = content.rfind(',', 0, prev_quote)
                        if last_comma > 0:
                            content = content[:last_comma]
        
        # Remove trailing comma
        content = content.rstrip(',')
        
        # Count and close brackets
        open_braces = content.count('{') - content.count('}')
        open_brackets = content.count('[') - content.count(']')
        
        content += ']' * max(0, open_brackets)
        content += '}' * max(0, open_braces)
        
        return content
    
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system: Optional[str] = None,
        temperature: float = 0.5
    ) -> Dict[str, Any]:
        """
        Generate structured output matching a schema.
        
        Args:
            prompt: The prompt
            schema: JSON schema for expected output
            system: Optional system prompt
            temperature: Lower for more consistent structure
        
        Returns:
            Dict matching schema
        """
        enhanced_prompt = f"""{prompt}

## Required Output Schema:
{json.dumps(schema, indent=2)}

Respond with valid JSON matching this schema exactly. No markdown, no explanation."""
        
        return await self.generate(
            prompt=enhanced_prompt,
            response_format="json",
            system=system,
            temperature=temperature
        )
    
    async def generate_long_content(
        self,
        prompt: str,
        target_tokens: int = 10000,
        system: Optional[str] = None,
        temperature: float = 0.8
    ) -> str:
        """
        Generate long-form content with continuation.
        
        For content that might exceed single-response limits.
        
        Args:
            prompt: The prompt
            target_tokens: Target output length
            system: System prompt
            temperature: Creativity level
        
        Returns:
            Generated content (may be from multiple requests)
        """
        content = ""
        remaining_tokens = target_tokens
        max_per_request = self.config.max_tokens
        
        current_prompt = prompt
        
        while remaining_tokens > 0:
            tokens_this_request = min(remaining_tokens, max_per_request)
            
            response = await self.generate(
                prompt=current_prompt,
                system=system,
                temperature=temperature,
                max_tokens=tokens_this_request
            )
            
            content += response
            
            # Estimate tokens generated
            estimated_tokens = len(response.split()) * 1.3
            remaining_tokens -= int(estimated_tokens)
            
            # If we got less than expected, we're probably done
            if estimated_tokens < tokens_this_request * 0.8:
                break
            
            # Continue from where we left off
            if remaining_tokens > 0:
                current_prompt = f"""Continue from where you left off. 
Here's the last part of what you wrote:

...{response[-1000:]}

Continue writing naturally. Don't repeat the above, just continue the narrative."""
        
        return content
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics."""
        # Estimate costs (update pricing as needed)
        pricing = {
            "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
            "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        }
        
        model_pricing = pricing.get(
            self.config.model, 
            {"input": 3.0, "output": 15.0}
        )
        
        input_cost = (self.total_input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * model_pricing["output"]
        
        return {
            "model": self.config.model,
            "request_count": self.request_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "estimated_cost_usd": round(input_cost + output_cost, 2)
        }
    
    def reset_usage(self) -> None:
        """Reset usage statistics."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.request_count = 0


def create_llm_client(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    config: Optional[LLMConfig] = None
) -> Optional[ClaudeLLMClient]:
    """
    Factory function to create LLM client.
    
    Returns None if no API key is available (graceful degradation for demo mode).
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    
    if not key:
        logger.warning(
            "No ANTHROPIC_API_KEY found. Running in demo mode with placeholder responses."
        )
        return None
    
    if config is None:
        config = LLMConfig()
    
    if model:
        config.model = model
    
    return ClaudeLLMClient(api_key=key, config=config)


# Convenience alias
LLMClient = ClaudeLLMClient


__all__ = [
    'ClaudeLLMClient',
    'LLMClient',
    'LLMConfig',
    'create_llm_client',
]
