"""
SQLAlchemy model generator.

Generates database models from Schema.org entities.
"""

from pathlib import Path
from typing import Dict, Any, List

from api_forge.generators.base import BaseGenerator
from api_forge.generators.artifacts import CodeArtifact, ArtifactType, GenerationContext
from api_forge.schema_org.models import SchemaEntity, RelationshipType
from api_forge.core.console import console


class ModelGenerator(BaseGenerator):
    """
    Generates SQLAlchemy models.

    Creates complete database models with:
    - Primary keys
    - Columns with proper types
    - Relationships (foreign keys, many-to-many)
    - Indexes
    - Constraints
    - Mixins (timestamps, soft delete)
    """

    def generate(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> CodeArtifact:
        """
        Generate SQLAlchemy model for an entity.

        Args:
            entity: Schema.org entity
            context: Generation context

        Returns:
            Generated model artifact
        """
        console.print(f"[cyan]Generating model for:[/cyan] {entity.name}")

        # Prepare template context
        template_context = self._prepare_context(entity, context)

        # Render template
        code = self.render_template("model.py.jinja", template_context)

        # Format code
        code = self.format_code(code)

        # Create artifact
        artifact = CodeArtifact(
            type=ArtifactType.MODEL,
            path=Path(context.app_name) / "models" / f"{entity.name.lower()}.py",
            content=code,
            entity_name=entity.name,
        )

        # Validate
        if self.validate_artifact(artifact):
            artifact.mark_generated()
            console.print(f"[green]✓[/green] Model generated: {artifact.lines} lines")

        return artifact

    def _prepare_context(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> Dict[str, Any]:
        """
        Prepare template context for model generation.

        Args:
            entity: Schema.org entity
            context: Generation context

        Returns:
            Template context dictionary
        """
        # Process properties
        columns = []
        relationships = []
        imports = set()

        # Add standard imports
        imports.add("from datetime import datetime")
        imports.add("from uuid import UUID, uuid4")
        imports.add("from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Text, ForeignKey")
        imports.add("from sqlalchemy.dialects.postgresql import UUID as PG_UUID")
        imports.add("from sqlalchemy.orm import relationship")
        imports.add(f"from {context.app_name}.db.base import BaseModel")

        # Process regular properties (columns)
        for prop_name, prop in entity.properties.items():
            if not prop.is_relationship:
                column_info = self._generate_column_info(prop)
                columns.append(column_info)

        # Process relationships
        for rel in entity.relationships:
            rel_info = self._generate_relationship_info(rel, entity)
            relationships.append(rel_info)

            # Add import for target entity
            imports.add(
                f"from {context.app_name}.models.{rel.target_entity.lower()} "
                f"import {rel.target_entity}"
            )

        # Determine mixins
        mixins = ["BaseModel"]  # Always include BaseModel (has timestamps)

        # Check if soft delete is enabled
        if context.config and context.config.generation.use_soft_delete:
            mixins.append("SoftDeleteMixin")
            imports.add(f"from {context.app_name}.db.base import SoftDeleteMixin")

        return {
            "entity": entity,
            "app_name": context.app_name,
            "columns": columns,
            "relationships": relationships,
            "mixins": mixins,
            "imports": sorted(list(imports)),
            "table_name": entity.table_name,
        }

    def _generate_column_info(self, prop: Any) -> Dict[str, Any]:
        """
        Generate column information from property.

        Args:
            prop: Schema property with type_info

        Returns:
            Dictionary with column information
        """
        type_info = getattr(prop, 'type_info', None)
        if not type_info:
            # Fallback to Text if no type info
            sql_type = "String(255)"
        else:
            sql_type = type_info.get('python_type')
            # sql_type = type_info.sql_type.replace("sa.", "")

        return {
            "name": prop.name,
            "type": sql_type,
            "nullable": not prop.required,
            "unique": self._should_be_unique(prop.name),
            "index": self._should_be_indexed(prop.name),
            "description": prop.description,
        }

    def _generate_relationship_info(
            self,
            rel: Any,
            entity: SchemaEntity
    ) -> Dict[str, Any]:
        """
        Generate relationship information.

        Args:
            rel: RelationshipInfo object
            entity: Source entity

        Returns:
            Dictionary with relationship information
        """
        if rel.type == RelationshipType.MANY_TO_ONE:
            return {
                "name": rel.property_name,
                "type": "many_to_one",
                "target": rel.target_entity,
                "foreign_key": rel.foreign_key,
                "back_populates": rel.back_populates,
            }

        elif rel.type == RelationshipType.MANY_TO_MANY:
            return {
                "name": rel.property_name,
                "type": "many_to_many",
                "target": rel.target_entity,
                "association_table": rel.association_table,
                "back_populates": rel.back_populates,
            }

        elif rel.type == RelationshipType.ONE_TO_ONE:
            return {
                "name": rel.property_name,
                "type": "one_to_one",
                "target": rel.target_entity,
                "foreign_key": rel.foreign_key,
                "back_populates": rel.back_populates,
            }

        return {}

    @staticmethod
    def _should_be_unique(field_name: str) -> bool:
        """Determine if field should be unique."""
        unique_patterns = ["email", "username", "slug", "code", "identifier"]
        return any(pattern in field_name.lower() for pattern in unique_patterns)

    @staticmethod
    def _should_be_indexed(field_name: str) -> bool:
        """Determine if field should be indexed."""
        index_patterns = ["email", "username", "status", "type", "category", "date"]
        return any(pattern in field_name.lower() for pattern in index_patterns)

    def generate_association_table(
            self,
            table_name: str,
            source_entity: str,
            target_entity: str,
            context: GenerationContext
    ) -> CodeArtifact:
        """
        Generate association table for many-to-many relationships.

        Args:
            table_name: Name of association table
            source_entity: Source entity name
            target_entity: Target entity name
            context: Generation context

        Returns:
            Generated association table artifact
        """
        template_context = {
            "table_name": table_name,
            "source_entity": source_entity,
            "target_entity": target_entity,
            "app_name": context.app_name,
        }

        code = self.render_template("association_table.py.jinja", template_context)
        code = self.format_code(code)

        artifact = CodeArtifact(
            type=ArtifactType.MODEL,
            path=Path(context.app_name) / "models" / f"{table_name}.py",
            content=code,
            entity_name=table_name,
        )

        return artifact


__all__ = ["ModelGenerator"]
