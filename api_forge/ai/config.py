"""
AI configuration.

Settings for AI-powered features.
"""

from typing import Optional
from pydantic import BaseModel, Field
import os


class AIConfig(BaseModel):
    """Configuration for AI features"""

    enabled: bool = Field(
        default=True,
        description="Enable AI-powered features"
    )

    provider: str = Field(
        default="anthropic",
        description="AI provider (anthropic, openai)"
    )

    model: str = Field(
        default="claude-sonnet-4",
        description="AI model to use"
    )

    api_key: Optional[str] = Field(
        default=None,
        description="API key (loaded from environment if not provided)"
    )

    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Temperature for generation (0.0-1.0)"
    )

    max_tokens: int = Field(
        default=4000,
        ge=100,
        le=8000,
        description="Maximum tokens for generation"
    )

    timeout: int = Field(
        default=60,
        description="Request timeout in seconds"
    )

    def __init__(self, **data):
        super().__init__(**data)

        # Load API key from environment if not provided
        if self.api_key is None:
            if self.provider == "anthropic":
                self.api_key = os.getenv("ANTHROPIC_API_KEY")
            elif self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")

    @property
    def is_configured(self) -> bool:
        """Check if AI is properly configured"""
        return self.enabled and self.api_key is not None


__all__ = ["AIConfig"]