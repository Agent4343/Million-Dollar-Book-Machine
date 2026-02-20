"""
Claude LLM Client Wrapper

Provides a consistent interface for the Anthropic Claude API
that integrates with the book development orchestrator.
"""

import asyncio
import json
import logging
import os
from typing import Any, Optional

import anthropic

logger = logging.getLogger(__name__)


class ClaudeLLMClient:
    """
    Claude API client wrapper for book development agents.

    Provides async generation with JSON parsing support.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 16000  # Increased for longer content like chapter outlines
    ):
        """
        Initialize the Claude client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.max_tokens = max_tokens

        logger.info(f"Initialized Claude client with model: {model}")

    async def generate(
        self,
        prompt: str,
        response_format: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None  # Allow per-call override
    ) -> Any:
        """
        Generate content using Claude.

        Args:
            prompt: The prompt to send to Claude
            response_format: If "json", parse response as JSON
            system: Optional system prompt
            temperature: Creativity level (0-1)
            max_tokens: Override default max_tokens for this call

        Returns:
            Generated content (dict if JSON, str otherwise)
        """
        messages = [{"role": "user", "content": prompt}]

        system_prompt = system or (
            "You are an expert book development AI assistant. "
            "Provide detailed, creative, and professional responses. "
            "When asked for JSON output, respond ONLY with valid JSON, no markdown or explanations. "
            "Keep responses concise and within token limits."
        )

        tokens = max_tokens or self.max_tokens

        try:
            # Anthropic SDK client is synchronous; run in a thread so we don't
            # block the event loop (critical for background jobs + API polling).
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=tokens,
                system=system_prompt,
                messages=messages,
                temperature=temperature,
            )

            content = response.content[0].text

            # Check if response was truncated
            if response.stop_reason == "max_tokens":
                logger.warning(f"Response truncated due to max_tokens limit ({tokens})")
                # Try to fix truncated JSON by closing brackets
                if response_format == "json":
                    content = self._fix_truncated_json(content)

            if response_format == "json":
                # Extract JSON from response (handle markdown code blocks / stray text)
                json_str = self._extract_json(content)
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # One more attempt: ask Claude to repair its own JSON.
                    repaired = await self._repair_json_via_llm(content)
                    if repaired is not None:
                        return repaired
                    raise

            return content

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {content}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")

    def _extract_json(self, content: str) -> str:
        """
        Extract JSON from a response, handling:
        - Markdown code fences
        - Leading/trailing commentary
        """
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        # Fast path: already valid JSON
        if content and content[0] in "{[":
            return content

        # If there's surrounding text, try to grab the outermost JSON object/array.
        first_obj = content.find("{")
        first_arr = content.find("[")
        starts = [i for i in [first_obj, first_arr] if i != -1]
        if not starts:
            return content

        start = min(starts)
        # Heuristic end: last closing brace/bracket
        last_obj = content.rfind("}")
        last_arr = content.rfind("]")
        end = max(last_obj, last_arr)
        if end == -1 or end <= start:
            return content[start:]

        candidate = content[start : end + 1].strip()

        # Try trimming from the end until JSON parses (handles extra trailing text).
        # Keep this bounded to avoid pathological behavior.
        for _ in range(25):
            try:
                json.loads(candidate)
                return candidate
            except Exception:
                candidate = candidate[:-1].rstrip()
                if not candidate:
                    break

        return content[start : end + 1].strip()

    def _fix_truncated_json(self, content: str) -> str:
        """Attempt to fix truncated JSON by closing open brackets."""
        content = content.strip()

        # Remove trailing incomplete string
        if content.count('"') % 2 == 1:
            # Odd number of quotes - find last complete field
            last_quote = content.rfind('"')
            if last_quote > 0:
                # Look for the last complete key-value pair
                last_colon = content.rfind(':', 0, last_quote)
                last_comma = content.rfind(',', 0, last_colon) if last_colon > 0 else -1
                if last_comma > 0:
                    content = content[:last_comma]

        # Build nesting stack to determine correct closing order (respects actual JSON structure).
        # escape_next handles backslash-escaped characters inside strings (e.g. \") so they
        # don't accidentally toggle in_string state.
        stack = []
        in_string = False
        escape_next = False
        for ch in content:
            if escape_next:
                escape_next = False
                continue
            if ch == '\\' and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                stack.append('}')
            elif ch == '[':
                stack.append(']')
            elif ch in ('}', ']') and stack and stack[-1] == ch:
                stack.pop()

        # Add closing brackets in reverse order of opening
        content = content.rstrip(',')  # Remove trailing comma
        content += ''.join(reversed(stack))

        return content

    async def _repair_json_via_llm(self, bad_content: str) -> Optional[dict]:
        """
        Ask the model to convert a non-parseable JSON-like response into valid JSON.
        Returns None if repair fails.
        """
        try:
            prompt = f"""Fix the following content into valid JSON.

Rules:
- Output ONLY valid JSON (no markdown, no commentary).
- Do not use ellipses like ... anywhere.
- If something is missing, infer a reasonable value rather than leaving placeholders.

Content to repair:
{bad_content}
"""
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=min(self.max_tokens, 6000),
                system="You are a JSON repair assistant. Return only valid JSON.",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            fixed = response.content[0].text
            json_str = self._extract_json(fixed)
            return json.loads(json_str)
        except Exception:
            logger.exception("JSON repair attempt failed")
            return None

    async def generate_structured(
        self,
        prompt: str,
        schema: dict,
        system: Optional[str] = None
    ) -> dict:
        """
        Generate structured output matching a schema.

        Args:
            prompt: The prompt
            schema: JSON schema for expected output
            system: Optional system prompt

        Returns:
            Structured dict matching schema
        """
        enhanced_prompt = f"""{prompt}

## Required Output Schema:
{json.dumps(schema, indent=2)}

Respond with valid JSON matching this schema exactly."""

        return await self.generate(
            prompt=enhanced_prompt,
            response_format="json",
            system=system
        )


def create_llm_client(
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> Optional[ClaudeLLMClient]:
    """
    Factory function to create LLM client.

    Returns None if no API key is available (graceful degradation).
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    if not key:
        logger.warning(
            "No ANTHROPIC_API_KEY found. Running in demo mode with placeholder responses."
        )
        return None

    kwargs = {"api_key": key}
    if model:
        kwargs["model"] = model

    return ClaudeLLMClient(**kwargs)
