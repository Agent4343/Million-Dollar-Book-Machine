"""
Claude LLM Client Wrapper

Provides a consistent interface for the Anthropic Claude API
that integrates with the book development orchestrator.
"""

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
        max_tokens: int = 4096
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
        temperature: float = 0.7
    ) -> Any:
        """
        Generate content using Claude.

        Args:
            prompt: The prompt to send to Claude
            response_format: If "json", parse response as JSON
            system: Optional system prompt
            temperature: Creativity level (0-1)

        Returns:
            Generated content (dict if JSON, str otherwise)
        """
        messages = [{"role": "user", "content": prompt}]

        system_prompt = system or (
            "You are an expert book development AI assistant. "
            "Provide detailed, creative, and professional responses. "
            "When asked for JSON output, respond ONLY with valid JSON, no markdown or explanations."
        )

        try:
            # Use synchronous client (Anthropic SDK handles it)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages,
                temperature=temperature
            )

            content = response.content[0].text

            if response_format == "json":
                # Extract JSON from response (handle markdown code blocks)
                json_str = self._extract_json(content)
                return json.loads(json_str)

            return content

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {content}")
            raise ValueError(f"Invalid JSON response from Claude: {e}")

    def _extract_json(self, content: str) -> str:
        """Extract JSON from response, handling markdown code blocks."""
        content = content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        return content.strip()

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
