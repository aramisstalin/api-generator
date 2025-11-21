"""
Code artifact models.

Represents generated code files with metadata.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum


class ArtifactType(str, Enum):
    """Type of code artifact."""
    MODEL = "model"
    SCHEMA = "schema"
    REPOSITORY = "repository"
    SERVICE = "service"
    ROUTER = "router"
    TEST = "test"
    MIGRATION = "migration"
    CONFIG = "config"


class ArtifactStatus(str, Enum):
    """Status of artifact generation."""
    PENDING = "pending"
    GENERATED = "generated"
    VALIDATED = "validated"
    WRITTEN = "written"
    ERROR = "error"


@dataclass
class CodeArtifact:
    """
    Represents a generated code file.

    Attributes:
        type: Type of artifact
        path: Relative path from project root
        content: Generated code content
        entity_name: Name of entity this artifact is for
        language: Programming language (default: python)
        status: Current status
        dependencies: Other artifacts this depends on
        metadata: Additional metadata
    """
    type: ArtifactType
    path: Path
    content: str
    entity_name: str
    language: str = "python"
    status: ArtifactStatus = ArtifactStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def filename(self) -> str:
        """Get filename from path."""
        return self.path.name

    @property
    def lines(self) -> int:
        """Count lines of code."""
        return len(self.content.split('\n'))

    @property
    def size(self) -> int:
        """Get size in bytes."""
        return len(self.content.encode('utf-8'))

    def mark_generated(self) -> None:
        """Mark artifact as generated."""
        self.status = ArtifactStatus.GENERATED

    def mark_validated(self) -> None:
        """Mark artifact as validated."""
        self.status = ArtifactStatus.VALIDATED

    def mark_written(self) -> None:
        """Mark artifact as written to disk."""
        self.status = ArtifactStatus.WRITTEN

    def mark_error(self) -> None:
        """Mark artifact as having an error."""
        self.status = ArtifactStatus.ERROR

    def add_dependency(self, artifact_path: str) -> None:
        """Add a dependency on another artifact."""
        if artifact_path not in self.dependencies:
            self.dependencies.append(artifact_path)


@dataclass
class GenerationContext:
    """
    Context for code generation.

    Contains all information needed for generating code artifacts.

    Attributes:
        project_path: Root path of the project
        app_name: Application package name
        entity_name: Entity being generated
        artifacts: List of generated artifacts
        config: Project configuration
        options: Generation options
    """
    project_path: Path
    app_name: str
    entity_name: str
    artifacts: List[CodeArtifact] = field(default_factory=list)
    config: Optional[Any] = None
    options: Dict[str, Any] = field(default_factory=dict)

    def add_artifact(self, artifact: CodeArtifact) -> None:
        """Add an artifact to the context."""
        self.artifacts.append(artifact)

    def get_artifacts_by_type(self, artifact_type: ArtifactType) -> List[CodeArtifact]:
        """Get all artifacts of a specific type."""
        return [a for a in self.artifacts if a.type == artifact_type]

    def get_artifact_by_path(self, path: Path) -> Optional[CodeArtifact]:
        """Get artifact by its path."""
        for artifact in self.artifacts:
            if artifact.path == path:
                return artifact
        return None


__all__ = [
    "ArtifactType",
    "ArtifactStatus",
    "CodeArtifact",
    "GenerationContext",
]