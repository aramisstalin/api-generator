"""
FastAPI router generator.

Generates API endpoint routers.
"""

from pathlib import Path
from typing import Dict, Any, List

from api_forge.generators.base import BaseGenerator
from api_forge.generators.artifacts import CodeArtifact, ArtifactType, GenerationContext
from api_forge.schema_org.models import SchemaEntity
from api_forge.core.console import console


class RouterGenerator(BaseGenerator):
    """
    Generates FastAPI routers.

    Creates API endpoints with:
    - CRUD operations (Create, Read, Update, Delete, List)
    - Pagination and filtering
    - Authentication and authorization
    - OpenAPI documentation
    """

    def generate(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> CodeArtifact:
        """
        Generate FastAPI router for an entity.

        Args:
            entity: Schema.org entity
            context: Generation context

        Returns:
            Generated router artifact
        """
        console.print(f"[cyan]Generating router for:[/cyan] {entity.name}")

        # Prepare template context
        template_context = self._prepare_context(entity, context)

        # Render template
        code = self.render_template("router.py.jinja", template_context)

        # Format code
        code = self.format_code(code)

        # Create artifact
        artifact = CodeArtifact(
            type=ArtifactType.ROUTER,
            path=Path(context.app_name) / "api" / "v1" / "endpoints" / f"{entity.name.lower()}.py",
            content=code,
            entity_name=entity.name,
        )

        # Add dependencies
        artifact.add_dependency(f"{context.app_name}/models/{entity.name.lower()}.py")
        artifact.add_dependency(f"{context.app_name}/schemas/{entity.name.lower()}.py")
        artifact.add_dependency(f"{context.app_name}/services/{entity.name.lower()}_service.py")

        # Validate
        if self.validate_artifact(artifact):
            artifact.mark_generated()
            console.print(f"[green]✓[/green] Router generated: {artifact.lines} lines")

        return artifact

    def _prepare_context(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> Dict[str, Any]:
        """
        Prepare template context for router generation.

        Args:
            entity: Schema.org entity
            context: Generation context

        Returns:
            Template context dictionary
        """
        # Determine if authentication is required
        requires_auth = True  # Default to requiring auth
        if context.config:
            requires_auth = context.config.generation.authentication != "none"

        # Determine if RBAC is enabled
        enable_rbac = False
        if context.config:
            enable_rbac = context.config.generation.enable_rbac

        # Generate permissions based on entity name
        permissions = self._generate_permissions(entity) if enable_rbac else {}

        return {
            "entity": entity,
            "app_name": context.app_name,
            "requires_auth": requires_auth,
            "enable_rbac": enable_rbac,
            "permissions": permissions,
            "enable_pagination": context.config.generation.enable_pagination if context.config else True,
            "enable_filtering": context.config.generation.enable_filtering if context.config else True,
        }

    def _generate_permissions(self, entity: SchemaEntity) -> Dict[str, str]:
        """Generate permission strings for RBAC."""
        entity_lower = entity.name.lower()
        return {
            "create": f"{entity_lower}:create",
            "read": f"{entity_lower}:read",
            "update": f"{entity_lower}:update",
            "delete": f"{entity_lower}:delete",
        }


__all__ = ["RouterGenerator"]