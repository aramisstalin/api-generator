"""
Service layer generator.

Generates business logic services.
"""

from pathlib import Path
from typing import Dict, Any, List

from api_forge.generators.base import BaseGenerator
from api_forge.generators.artifacts import CodeArtifact, ArtifactType, GenerationContext
from api_forge.schema_org.models import SchemaEntity
from api_forge.core.console import console


class ServiceGenerator(BaseGenerator):
    """
    Generates service layer classes.

    Creates business logic layer with:
    - CRUD operations with validation
    - Business rules enforcement
    - Event hooks (after create, update, delete)
    - Custom business methods
    """

    def generate(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> CodeArtifact:
        """
        Generate service for an entity.

        Args:
            entity: Schema.org entity
            context: Generation context

        Returns:
            Generated service artifact
        """
        console.print(f"[cyan]Generating service for:[/cyan] {entity.name}")

        # Prepare template context
        template_context = self._prepare_context(entity, context)

        # Render template
        code = self.render_template("service.py.jinja", template_context)

        # Format code
        code = self.format_code(code)

        # Create artifact
        artifact = CodeArtifact(
            type=ArtifactType.SERVICE,
            path=Path(context.app_name) / "services" / f"{entity.name.lower()}_service.py",
            content=code,
            entity_name=entity.name,
        )

        # Add dependencies
        artifact.add_dependency(f"{context.app_name}/models/{entity.name.lower()}.py")
        artifact.add_dependency(f"{context.app_name}/schemas/{entity.name.lower()}.py")
        artifact.add_dependency(f"{context.app_name}/repositories/{entity.name.lower()}_repository.py")
        artifact.add_dependency(f"{context.app_name}/services/base.py")

        # Validate
        if self.validate_artifact(artifact):
            artifact.mark_generated()
            console.print(f"[green]✓[/green] Service generated: {artifact.lines} lines")

        return artifact

    def _prepare_context(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> Dict[str, Any]:
        """
        Prepare template context for service generation.

        Args:
            entity: Schema.org entity
            context: Generation context

        Returns:
            Template context dictionary
        """
        # Generate validation methods
        create_validations = self._generate_create_validations(entity)
        update_validations = self._generate_update_validations(entity)
        delete_validations = self._generate_delete_validations(entity)

        # Generate business methods
        business_methods = self._generate_business_methods(entity)

        has_validations = (
                len(create_validations) > 0 or
                len(update_validations) > 0 or
                len(delete_validations) > 0
        )

        return {
            "entity": entity,
            "app_name": context.app_name,
            "has_validations": has_validations,
            "create_validations": create_validations,
            "update_validations": update_validations,
            "delete_validations": delete_validations,
            "has_events": True,  # Always include event hooks
            "business_methods": business_methods,
        }

    def _generate_create_validations(
            self,
            entity: SchemaEntity
    ) -> List[Dict[str, Any]]:
        """Generate validation rules for create operations."""
        validations = []

        # Check for duplicate unique fields
        for prop_name, prop in entity.properties.items():
            if not prop.is_relationship:
                lower_name = prop_name.lower()

                if "email" in lower_name:
                    validations.append({
                        "description": f"Check if {prop_name} already exists",
                        "code": f"""if '{prop_name}' in obj_data:
            existing = await self.repository.get_by_{prop_name}(obj_data['{prop_name}'])
            if existing:
                raise ValueError('{prop_name} already exists')"""
                    })

                elif "username" in lower_name:
                    validations.append({
                        "description": f"Check if {prop_name} already exists",
                        "code": f"""if '{prop_name}' in obj_data:
            existing = await self.repository.get_by_{prop_name}(obj_data['{prop_name}'])
            if existing:
                raise ValueError('{prop_name} already taken')"""
                    })

        return validations

    def _generate_update_validations(
            self,
            entity: SchemaEntity
    ) -> List[Dict[str, Any]]:
        """Generate validation rules for update operations."""
        validations = []

        # Add immutability checks
        for prop_name, prop in entity.properties.items():
            lower_name = prop_name.lower()

            # Some fields shouldn't be updated
            if any(pattern in lower_name for pattern in ["id", "created"]):
                validations.append({
                    "description": f"Prevent updating {prop_name}",
                    "code": f"""if '{prop_name}' in update_data:
            raise ValueError('{prop_name} cannot be updated')"""
                })

        return validations

    def _generate_delete_validations(
            self,
            entity: SchemaEntity
    ) -> List[Dict[str, Any]]:
        """Generate validation rules for delete operations."""
        validations = []

        # Add relationship checks
        if entity.relationships:
            validations.append({
                "description": "Check for related records",
                "code": """# TODO: Check for dependent relationships before deletion
        pass"""
            })

        return validations

    def _generate_business_methods(
            self,
            entity: SchemaEntity
    ) -> List[Dict[str, Any]]:
        """Generate custom business methods."""
        methods = []

        # Generate activate/deactivate methods if has status field
        for prop_name, prop in entity.properties.items():
            if not prop.is_relationship:
                lower_name = prop_name.lower()

                if "status" in lower_name or "active" in lower_name:
                    methods.append({
                        "name": f"activate",
                        "parameters": ", id: UUID",
                        "return_type": f"{entity.name}",
                        "description": f"Activate {entity.name}",
                        "args_doc": "id: Entity ID",
                        "returns_doc": f"Activated {entity.name}",
                        "body": f"""entity = await self.get_by_id(id)
        if not entity:
            raise ValueError('{entity.name} not found')

        update_data = {{'{prop_name}': True}}
        return await self.update(id, update_data)"""
                    })

                    methods.append({
                        "name": f"deactivate",
                        "parameters": ", id: UUID",
                        "return_type": f"{entity.name}",
                        "description": f"Deactivate {entity.name}",
                        "args_doc": "id: Entity ID",
                        "returns_doc": f"Deactivated {entity.name}",
                        "body": f"""entity = await self.get_by_id(id)
        if not entity:
            raise ValueError('{entity.name} not found')

        update_data = {{'{prop_name}': False}}
        return await self.update(id, update_data)"""
                    })

        return methods


__all__ = ["ServiceGenerator"]