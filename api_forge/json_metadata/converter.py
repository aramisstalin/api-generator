"""
JSON to Entity converter.

Converts JSON metadata into internal SchemaEntity models compatible
with the existing generation pipeline.
"""

from typing import Dict, List, Optional
from api_forge.schema_org.models import (
    SchemaEntity,
    SchemaProperty,
    PropertyType,
    Relationship,
    ValidationRule,
    EntityAnalysis
)
from api_forge.json_metadata.loader import (
    EntityMetadata,
    FieldMetadata,
    RelationshipMetadata,
    JSONMetadata
)
from api_forge.core.console import console


class JSONToEntityConverter:
    """
    Converts JSON metadata to SchemaEntity models.

    Bridges the gap between JSON metadata and the internal
    entity model used by generators.
    """

    # Type mapping from JSON types to PropertyType
    TYPE_MAPPING = {
        "string": PropertyType.STRING,
        "text": PropertyType.TEXT,
        "int": PropertyType.INTEGER,
        "bigint": PropertyType.INTEGER,
        "uuid": PropertyType.UUID,
        "boolean": PropertyType.BOOLEAN,
        "decimal": PropertyType.DECIMAL,
        "float": PropertyType.FLOAT,
        "date": PropertyType.DATE,
        "datetime": PropertyType.DATETIME,
        "time": PropertyType.TIME,
        "jsonb": PropertyType.JSON,
        "json": PropertyType.JSON,
        "uuid[]": PropertyType.ARRAY,
        "string[]": PropertyType.ARRAY,
        "int[]": PropertyType.ARRAY,
    }

    def __init__(self):
        """Initialize converter."""
        self.entity_cache: Dict[str, SchemaEntity] = {}

    def convert_metadata(self, metadata: JSONMetadata) -> Dict[str, EntityAnalysis]:
        """
        Convert complete JSON metadata to entity analyses.

        Args:
            metadata: Loaded JSON metadata

        Returns:
            Dictionary mapping entity names to EntityAnalysis objects
        """
        console.print("\n[bold cyan]Converting JSON metadata to entities...[/bold cyan]")

        results = {}

        # First pass: convert all entities
        for entity_meta in metadata.entities:
            entity = self._convert_entity(entity_meta)
            self.entity_cache[entity.name] = entity

        # Second pass: resolve relationships
        for entity_meta in metadata.entities:
            entity = self.entity_cache[entity_meta.name]
            relationships = self._convert_relationships(entity_meta, entity)
            entity.relationships = relationships

        # Third pass: create analyses
        for entity_name, entity in self.entity_cache.items():
            analysis = EntityAnalysis(
                entity=entity,
                unique_fields=self._extract_unique_fields(entity),
                suggested_indexes=self._extract_indexes(entity),
                immutable_fields=self._extract_immutable_fields(entity),
                business_rules=[],
                security_considerations=[],
            )
            results[entity_name] = analysis

        console.print(f"[green]✓[/green] Converted {len(results)} entities")
        return results

    def _convert_entity(self, entity_meta: EntityMetadata) -> SchemaEntity:
        """
        Convert EntityMetadata to SchemaEntity.

        Args:
            entity_meta: JSON entity metadata

        Returns:
            SchemaEntity object
        """
        entity = SchemaEntity(
            name=entity_meta.name,
            description=entity_meta.description,
            properties={},
            parent_types=[],
            child_types=[],
            relationships=[],
            validation_rules={},
        )

        # Convert fields to properties
        for field_meta in entity_meta.fields:
            prop = self._convert_field(field_meta)
            entity.properties[field_meta.name] = prop

        # Store metadata
        entity.metadata = {  # type: ignore
            "table_name": entity_meta.table_name,
            "audit": entity_meta.audit,
            "soft_delete": entity_meta.soft_delete,
            "permissions": entity_meta.permissions,
            "composite_primary_key": entity_meta.composite_primary_key,
            "indexes": entity_meta.indexes or [],
            "endpoints": entity_meta.endpoints.dict(),
            "seed": entity_meta.seed or [],
        }

        return entity

    def _convert_field(self, field_meta: FieldMetadata) -> SchemaProperty:
        """
        Convert FieldMetadata to SchemaProperty.

        Args:
            field_meta: JSON field metadata

        Returns:
            SchemaProperty object
        """
        # Determine property type
        prop_type = self.TYPE_MAPPING.get(
            field_meta.type.lower(),
            PropertyType.STRING
        )

        # Build range info
        range_includes = []
        if field_meta.type in self.TYPE_MAPPING:
            range_includes.append(field_meta.type)

        prop = SchemaProperty(
            name=field_meta.name,
            description=field_meta.description or "",
            range_includes=range_includes,
            required=not field_meta.nullable,
        )

        # Store type info
        prop.type_info = {  # type: ignore
            "property_type": prop_type,
            "python_type": self._get_python_type(field_meta),
            "is_array": field_meta.type.endswith("[]"),
            "is_enum": field_meta.enum is not None,
        }

        # Store field metadata
        prop.field_metadata = {  # type: ignore
            "primary": field_meta.primary,
            "auto_increment": field_meta.auto_increment,
            "unique": field_meta.unique,
            "default": field_meta.default,
            "max_length": field_meta.max_length,
            "precision": field_meta.precision,
            "scale": field_meta.scale,
            "format": field_meta.format,
            "private": field_meta.private,
            "enum": field_meta.enum,
            "foreign_key": field_meta.foreign_key,
            "validation": field_meta.validation,
            "frontend": field_meta.frontend,
        }

        return prop

    def _get_python_type(self, field_meta: FieldMetadata) -> str:
        """
        Get Python type string for field.

        Args:
            field_meta: Field metadata

        Returns:
            Python type string
        """
        type_map = {
            "string": "str",
            "text": "str",
            "int": "int",
            "bigint": "int",
            "uuid": "UUID",
            "boolean": "bool",
            "decimal": "Decimal",
            "float": "float",
            "date": "date",
            "datetime": "datetime",
            "time": "time",
            "jsonb": "Dict",
            "json": "Dict",
            "uuid[]": "List[UUID]",
            "string[]": "List[str]",
            "int[]": "List[int]",
        }

        base_type = type_map.get(field_meta.type.lower(), "Any")

        if field_meta.nullable and not field_meta.primary:
            return f"Optional[{base_type}]"

        return base_type

    def _convert_relationships(
            self,
            entity_meta: EntityMetadata,
            entity: SchemaEntity
    ) -> List[Relationship]:
        """
        Convert relationship metadata to Relationship objects.

        Args:
            entity_meta: JSON entity metadata
            entity: Converted SchemaEntity

        Returns:
            List of Relationship objects
        """
        relationships = []

        for rel_meta in entity_meta.relationships:
            rel = Relationship(
                name=rel_meta.name,
                type=rel_meta.type,
                target_entity=rel_meta.target,
                source_entity=entity.name,
                source_property=rel_meta.local_field,
                target_property=rel_meta.remote_field,
            )

            # Store additional metadata
            rel.metadata = {  # type: ignore
                "via": rel_meta.via,
                "eager_load": rel_meta.eager_load,
                "cascade": rel_meta.cascade,
                "representation_in_ui": rel_meta.representation_in_ui,
            }

            relationships.append(rel)

        return relationships

    def _extract_unique_fields(self, entity: SchemaEntity) -> List[str]:
        """
        Extract fields marked as unique.

        Args:
            entity: SchemaEntity

        Returns:
            List of unique field names
        """
        unique_fields = []

        for prop_name, prop in entity.properties.items():
            field_meta = getattr(prop, 'field_metadata', {})
            if field_meta.get('unique') or field_meta.get('primary'):
                unique_fields.append(prop_name)

        return unique_fields

    def _extract_indexes(self, entity: SchemaEntity) -> List[str]:
        """
        Extract suggested indexes from metadata.

        Args:
            entity: SchemaEntity

        Returns:
            List of field names to index
        """
        indexes = []
        metadata = getattr(entity, 'metadata', {})

        # Add indexes from metadata
        for idx in metadata.get('indexes', []):
            if 'fields' in idx:
                indexes.extend(idx['fields'])

        # Add foreign keys (always indexed)
        for prop_name, prop in entity.properties.items():
            field_meta = getattr(prop, 'field_metadata', {})
            if field_meta.get('foreign_key'):
                indexes.append(prop_name)

        # Add unique fields
        indexes.extend(self._extract_unique_fields(entity))

        return list(set(indexes))  # Remove duplicates

    def _extract_immutable_fields(self, entity: SchemaEntity) -> List[str]:
        """
        Extract immutable fields (primary keys, created_at, etc.).

        Args:
            entity: SchemaEntity

        Returns:
            List of immutable field names
        """
        immutable = []

        for prop_name, prop in entity.properties.items():
            field_meta = getattr(prop, 'field_metadata', {})

            # Primary keys are immutable
            if field_meta.get('primary'):
                immutable.append(prop_name)

            # created_at is immutable
            if prop_name in ['created_at', 'id']:
                immutable.append(prop_name)

        return immutable

    def get_entity(self, name: str) -> Optional[SchemaEntity]:
        """
        Get converted entity by name.

        Args:
            name: Entity name

        Returns:
            SchemaEntity or None
        """
        return self.entity_cache.get(name)

    def clear_cache(self) -> None:
        """Clear entity cache."""
        self.entity_cache.clear()


__all__ = ["JSONToEntityConverter"]