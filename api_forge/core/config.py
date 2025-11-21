"""
Configuration management for API Forge.

Handles loading and validation of configuration from various sources:
- Command-line arguments
- Environment variables
- Configuration files (schema-gen.yaml)
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
import yaml

from api_forge.core.exceptions import ConfigurationError


class GenerationConfig(BaseModel):
    """Configuration for code generation."""

    ai_enabled: bool = Field(default=True, description="Enable AI-assisted generation")
    ai_provider: str = Field(default="anthropic", description="AI provider (anthropic, openai)")
    ai_model: str = Field(default="claude-sonnet-4", description="AI model to use")

    use_async: bool = Field(default=True, description="Generate async code")
    use_soft_delete: bool = Field(default=True, description="Enable soft delete by default")
    use_audit_timestamps: bool = Field(default=True, description="Add created_at/updated_at")

    authentication: str = Field(default="jwt", description="Authentication method")
    enable_oauth2: bool = Field(default=True, description="Enable OAuth2 support")
    enable_rbac: bool = Field(default=True, description="Enable RBAC")

    enable_pagination: bool = Field(default=True, description="Enable pagination")
    enable_filtering: bool = Field(default=True, description="Enable filtering")
    enable_sorting: bool = Field(default=True, description="Enable sorting")
    default_page_size: int = Field(default=20, ge=1, le=100)
    max_page_size: int = Field(default=100, ge=1, le=1000)


class DatabaseConfig(BaseModel):
    """Database configuration."""

    provider: str = Field(default="postgresql", description="Database provider")
    host: str = Field(default="localhost")
    port: int = Field(default=5432, ge=1, le=65535)
    name: str = Field(default="apiforge_db")
    user: Optional[str] = None
    password: Optional[str] = None


class TestingConfig(BaseModel):
    """Testing configuration."""

    coverage_threshold: int = Field(default=80, ge=0, le=100)
    generate_factories: bool = Field(default=True)
    generate_fixtures: bool = Field(default=True)
    generate_tests: bool = Field(default=True)


class DeploymentConfig(BaseModel):
    """Deployment configuration."""

    dockerfile: bool = Field(default=True)
    docker_compose: bool = Field(default=True)
    kubernetes: bool = Field(default=False)
    ci_cd: str = Field(default="github_actions", description="CI/CD platform")


class ProjectConfig(BaseModel):
    """Complete project configuration."""

    name: str = Field(description="Project name")
    version: str = Field(default="1.0.0")
    description: str = Field(default="Auto-generated API from Schema.org")

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    testing: TestingConfig = Field(default_factory=TestingConfig)
    deployment: DeploymentConfig = Field(default_factory=DeploymentConfig)

    entities: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate project name."""
        if not v:
            raise ValueError("Project name cannot be empty")

        # Check for valid Python package name
        if not v.replace("-", "_").replace("_", "").isalnum():
            raise ValueError("Project name must contain only letters, numbers, hyphens, and underscores")

        return v

    @classmethod
    def load_from_file(cls, config_path: Path) -> "ProjectConfig":
        """Load configuration from YAML file."""
        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                raise ConfigurationError("Configuration file is empty")

            return cls(**data)

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in configuration file: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.model_dump(exclude_none=True),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )

        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")


class CLIConfig:
    """
    Global CLI configuration.

    This class manages the API Forge CLI configuration, including:
    - Current working directory
    - Default settings
    - User preferences
    """

    def __init__(self):
        self.cwd = Path.cwd()
        self.config_file_name = "api-forge.yaml"

    def find_project_config(self, start_path: Optional[Path] = None) -> Optional[Path]:
        """
        Find project configuration file by walking up the directory tree.

        Args:
            start_path: Starting directory (defaults to CWD)

        Returns:
            Path to config file if found, None otherwise
        """
        current = start_path or self.cwd

        # Walk up directory tree
        for parent in [current, *current.parents]:
            config_path = parent / self.config_file_name
            if config_path.exists():
                return config_path

        return None

    def load_project_config(self, config_path: Optional[Path] = None) -> Optional[ProjectConfig]:
        """
        Load project configuration.

        Args:
            config_path: Explicit path to config file

        Returns:
            ProjectConfig if found and valid, None otherwise
        """
        if config_path is None:
            config_path = self.find_project_config()

        if config_path is None:
            return None

        return ProjectConfig.load_from_file(config_path)


# Global CLI config instance
cli_config = CLIConfig()

__all__ = [
    "ProjectConfig",
    "GenerationConfig",
    "DatabaseConfig",
    "TestingConfig",
    "DeploymentConfig",
    "CLIConfig",
    "cli_config",
]