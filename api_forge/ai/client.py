"""
AI API client.

Handles communication with AI providers (Anthropic, OpenAI).
"""

from typing import Dict, Any, List, Optional
import httpx
from anthropic import AsyncAnthropic
import json

from api_forge.ai.config import AIConfig
from api_forge.core.exceptions import AIGenerationError
from api_forge.core.console import console


class AIClient:
    """
    Client for AI API interactions.

    Supports multiple providers:
    - Anthropic (Claude)
    - OpenAI (GPT)
    """

    def __init__(self, config: AIConfig):
        """
        Initialize AI client.

        Args:
            config: AI configuration
        """
        self.config = config

        if not config.is_configured:
            raise AIGenerationError(
                "AI client not properly configured. Set ANTHROPIC_API_KEY environment variable."
            )

        # Initialize provider client
        if config.provider == "anthropic":
            self.client = AsyncAnthropic(api_key=config.api_key)
        else:
            raise AIGenerationError(f"Unsupported AI provider: {config.provider}")

    async def generate(
            self,
            prompt: str,
            system_prompt: Optional[str] = None,
            response_format: Optional[str] = None
    ) -> str:
        """
        Generate text using AI.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            response_format: Expected response format (e.g., "json", "code")

        Returns:
            Generated text

        Raises:
            AIGenerationError: If generation fails
        """
        try:
            if self.config.provider == "anthropic":
                return await self._generate_anthropic(
                    prompt,
                    system_prompt,
                    response_format
                )
            else:
                raise AIGenerationError(f"Unsupported provider: {self.config.provider}")

        except Exception as e:
            raise AIGenerationError(
                f"AI generation failed: {e}",
                details={"error": str(e)}
            )

    async def _generate_anthropic(
            self,
            prompt: str,
            system_prompt: Optional[str],
            response_format: Optional[str]
    ) -> str:
        """Generate using Anthropic Claude API"""

        messages = [
            {"role": "user", "content": prompt}
        ]

        # Add format instructions if specified
        if response_format == "json":
            messages[0]["content"] += "\n\nRespond with valid JSON only, no other text."
        elif response_format == "code":
            messages[0]["content"] += "\n\nRespond with code only, no explanations."

        response = await self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
            system=system_prompt or "You are an expert software engineer specializing in Python and FastAPI.",
            messages=messages
        )

        # Extract text from response
        if response.content and len(response.content) > 0:
            return response.content[0].text

        return ""

    async def generate_structured(
            self,
            prompt: str,
            schema: Dict[str, Any],
            system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured data (JSON) using AI.

        Args:
            prompt: User prompt
            schema: JSON schema describing expected structure
            system_prompt: System prompt (optional)

        Returns:
            Parsed JSON response

        Raises:
            AIGenerationError: If generation or parsing fails
        """
        # Add schema to prompt
        full_prompt = f"{prompt}\n\nRespond with JSON matching this schema:\n{json.dumps(schema, indent=2)}"

        response = await self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            response_format="json"
        )

        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            return json.loads(response)

        except json.JSONDecodeError as e:
            raise AIGenerationError(
                f"Failed to parse JSON response: {e}",
                details={"response": response}
            )

    async def generate_code(
            self,
            prompt: str,
            language: str = "python",
            system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate code using AI.

        Args:
            prompt: Description of what code to generate
            language: Programming language
            system_prompt: System prompt (optional)

        Returns:
            Generated code
        """
        full_prompt = f"Generate {language} code for the following:\n\n{prompt}"

        if not system_prompt:
            system_prompt = f"You are an expert {language} developer. Generate clean, production-ready code following best practices."

        response = await self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            response_format="code"
        )

        # Extract code from markdown blocks
        response = response.strip()
        if response.startswith(f"```{language}"):
            response = response[len(f"```{language}"):].strip()
        elif response.startswith("```"):
            response = response[3:].strip()

        if response.endswith("```"):
            response = response[:-3].strip()

        return response

    async def close(self) -> None:
        """Close client connections"""
        if hasattr(self.client, 'close'):
            await self.client.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


__all__ = ["AIClient"]