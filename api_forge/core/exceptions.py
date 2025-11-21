"""
Custom exceptions for API Forge.

These exceptions provide clear, actionable error messages for various failure scenarios.
"""

from typing import Optional, Any, Dict


class APIForgeException(Exception):
    """Base exception for all API Forge errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(APIForgeException):
    """Raised when configuration is invalid or missing."""
    pass


class SchemaOrgError(APIForgeException):
    """Raised when Schema.org operations fail."""
    pass


class CodeGenerationError(APIForgeException):
    """Raised when code generation fails."""
    pass


class TemplateError(APIForgeException):
    """Raised when template rendering fails."""
    pass


class ValidationError(APIForgeException):
    """Raised when validation fails."""
    pass


class ProjectExistsError(APIForgeException):
    """Raised when attempting to create a project that already exists."""
    pass


class ProjectNotFoundError(APIForgeException):
    """Raised when project is not found."""
    pass


class AIGenerationError(APIForgeException):
    """Raised when AI-assisted generation fails."""
    pass


__all__ = [
    "APIForgeException",
    "ConfigurationError",
    "SchemaOrgError",
    "CodeGenerationError",
    "TemplateError",
    "ValidationError",
    "ProjectExistsError",
    "ProjectNotFoundError",
    "AIGenerationError",
]