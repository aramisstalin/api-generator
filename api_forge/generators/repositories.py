"""
Repository generator.

Generates data access layer repositories.
"""

from pathlib import Path
from typing import Dict, Any, List

from api_forge.generators.base import BaseGenerator
from api_forge.generators.artifacts import CodeArtifact, ArtifactType, GenerationContext
from api_forge.schema_org.models import SchemaEntity
from api_forge.core.console import console


class RepositoryGenerator(BaseGenerator):
    """
    Generates repository classes.

    Creates data access layer with:
    - CRUD operations (inherited from BaseRepository)
    - Custom query methods
    - Relationship loading
    - Search functionality
    """

    def generate(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> CodeArtifact:
        """
        Generate repository for an entity.

        Args:
            entity: Schema.org entity
            context: Generation context

        Returns:
            Generated repository artifact
        """
        console.print(f"[cyan]Generating repository for:[/cyan] {entity.name}")

        # Prepare template context
        template_context = self._prepare_context(entity, context)

        # Render template
        code = self.render_template("repository.py.jinja", template_context)

        # Format code
        code = self.format_code(code)

        # Create artifact
        artifact = CodeArtifact(
            type=ArtifactType.REPOSITORY,
            path=Path(context.app_name) / "repositories" / f"{entity.name.lower()}_repository.py",
            content=code,
            entity_name=entity.name,
        )

        # Add dependencies
        artifact.add_dependency(f"{context.app_name}/models/{entity.name.lower()}.py")
        artifact.add_dependency(f"{context.app_name}/repositories/base.py")

        # Validate
        if self.validate_artifact(artifact):
            artifact.mark_generated()
            console.print(f"[green]✓[/green] Repository generated: {artifact.lines} lines")

        return artifact

    def _prepare_context(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> Dict[str, Any]:
        """
        Prepare template context for repository generation.

        Args:
            entity: Schema.org entity
            context: Generation context

        Returns:
            Template context dictionary
        """
        # Generate custom methods based on entity properties
        custom_methods = self._generate_custom_methods(entity)

        # Identify searchable fields (text fields)
        searchable_fields = self._identify_searchable_fields(entity)

        return {
            "entity": entity,
            "app_name": context.app_name,
            "custom_methods": custom_methods,
            "has_relationships": len(entity.relationships) > 0,
            "searchable_fields": searchable_fields,
        }

    def _generate_custom_methods(self, entity: SchemaEntity) -> List[Dict[str, Any]]:
        """
        Generate custom repository methods based on entity properties.

        Args:
            entity: Schema.org entity

        Returns:
            List of method definitions
        """
        methods = []

        # Generate finder methods for unique fields
        for prop_name, prop in entity.properties.items():
            if not prop.is_relationship:
                lower_name = prop_name.lower()

                # Email finder
                if "email" in lower_name:
                    methods.append({
                        "name": f"get_by_{prop_name}",
                        "parameters": f", {prop_name}: str",
                        "return_type": f"Optional[{entity.name}]",
                        "description": f"Get {entity.name} by {prop_name}",
                        "body": f"""query = select({entity.name}).where({entity.name}.{prop_name} == {prop_name})
        result = await self.db.execute(query)
        return result.scalar_one_or_none()"""
                    })

                # Username finder
                elif "username" in lower_name:
                    methods.append({
                        "name": f"get_by_{prop_name}",
                        "parameters": f", {prop_name}: str",
                        "return_type": f"Optional[{entity.name}]",
                        "description": f"Get {entity.name} by {prop_name}",
                        "body": f"""query = select({entity.name}).where({entity.name}.{prop_name} == {prop_name})
        result = await self.db.execute(query)
        return result.scalar_one_or_none()"""
                    })

                # Status filter
                elif "status" in lower_name:
                    methods.append({
                        "name": f"get_by_{prop_name}",
                        "parameters": f", {prop_name}: str, skip: int = 0, limit: int = 100",
                        "return_type": f"tuple[List[{entity.name}], int]",
                        "description": f"Get {entity.name} entities by {prop_name}",
                        "body": f"""query = select({entity.name}).where({entity.name}.{prop_name} == {prop_name})

        # Get total count
        from sqlalchemy import func
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return items, total"""
                    })

        return methods

    def _identify_searchable_fields(self, entity: SchemaEntity) -> List[str]:
        """
        Identify fields that should be searchable.

        Args:
            entity: Schema.org entity

        Returns:
            List of field names
        """
        searchable = []

        for prop_name, prop in entity.properties.items():
            if not prop.is_relationship:
                type_info = getattr(prop, 'type_info', None)
                if type_info and type_info.python_type == "str":
                    # Add text fields to searchable
                    lower_name = prop_name.lower()
                    if any(pattern in lower_name for pattern in ["name", "title", "description", "text"]):
                        searchable.append(prop_name)

        return searchable


__all__ = ["RepositoryGenerator"]