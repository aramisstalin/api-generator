"""
JSON metadata loader.

Loads application metadata from JSON files and converts to internal entity models.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from pydantic import BaseModel, Field, field_validator

from api_forge.core.exceptions import ValidationError
from api_forge.core.console import console


class AppMetadata(BaseModel):
    """Application-level metadata."""
    name: str
    description: str
    version: str
    locale: str = "en-US"
    timezone: str = "UTC"
    backend: Dict[str, Any]
    frontend: Optional[Dict[str, Any]] = None


class FieldMetadata(BaseModel):
    """Field definition from JSON."""
    name: str
    type: str
    primary: bool = False
    auto_increment: bool = False
    nullable: bool = True
    unique: bool = False
    default: Optional[Any] = None
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    format: Optional[str] = None
    description: Optional[str] = None
    private: bool = False
    enum: Optional[List[str]] = None
    foreign_key: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    frontend: Optional[Dict[str, Any]] = None


class RelationshipMetadata(BaseModel):
    """Relationship definition from JSON."""
    type: str  # one-to-one, one-to-many, many-to-one, many-to-many, self-referencing
    target: str
    local_field: Optional[str] = None
    remote_field: Optional[str] = None
    via: Optional[str] = None  # For many-to-many join table
    name: str
    eager_load: bool = False
    cascade: Optional[str] = None
    representation_in_ui: Optional[str] = None


class EndpointMetadata(BaseModel):
    """Endpoint configuration from JSON."""
    base_path: str
    crud: bool = True
    search: Optional[Dict[str, Any]] = None
    bulk: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None
    read: Optional[Dict[str, Any]] = None
    pdf_export: bool = False
    reporting: bool = False
    upload: Optional[Dict[str, Any]] = None
    download: Optional[Dict[str, Any]] = None


class EntityMetadata(BaseModel):
    """Complete entity definition from JSON."""
    name: str
    table_name: str
    description: str
    audit: bool = False
    soft_delete: bool = False
    composite_primary_key: Optional[List[str]] = None
    indexes: Optional[List[Dict[str, Any]]] = None
    permissions: Optional[Dict[str, List[str]]] = None
    fields: List[FieldMetadata]
    relationships: List[RelationshipMetadata] = Field(default_factory=list)
    endpoints: EndpointMetadata
    seed: Optional[List[Dict[str, Any]]] = None


class JSONMetadata(BaseModel):
    """Complete JSON metadata structure."""
    app: AppMetadata
    entities: List[EntityMetadata]
    relationships_global: Optional[Dict[str, Any]] = None
    generation_options: Optional[Dict[str, Any]] = None
    ui_hints: Optional[Dict[str, Any]] = None
    dto_policies: Optional[Dict[str, Any]] = None
    client_behaviors: Optional[Dict[str, Any]] = None
    examples: Optional[Dict[str, Any]] = None
    notes: Optional[Dict[str, Any]] = None

    @field_validator('entities')
    def validate_entities(cls, v):
        """Ensure entities list is not empty."""
        if not v:
            raise ValueError("At least one entity must be defined")
        return v


class JSONMetadataLoader:
    """
    Loads and validates JSON metadata files.

    Converts JSON metadata into internal entity models compatible
    with the generation pipeline.
    """

    def __init__(self):
        """Initialize loader."""
        self.metadata: Optional[JSONMetadata] = None

    def load_from_file(self, file_path: Path) -> JSONMetadata:
        """
        Load metadata from JSON file.

        Args:
            file_path: Path to JSON metadata file

        Returns:
            Parsed and validated metadata

        Raises:
            ValidationError: If JSON is invalid or validation fails
        """
        console.print(f"\n[bold cyan]Loading metadata from:[/bold cyan] {file_path}")

        if not file_path.exists():
            raise ValidationError(f"File not found: {file_path}")

        if not file_path.suffix.lower() == '.json':
            raise ValidationError(f"File must be JSON: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}")
        except Exception as e:
            raise ValidationError(f"Failed to read file: {e}")

        try:
            self.metadata = JSONMetadata(**data)
        except Exception as e:
            raise ValidationError(f"Validation failed: {e}")

        console.print(f"[green]✓[/green] Loaded {len(self.metadata.entities)} entities")

        return self.metadata

    def load_from_string(self, json_str: str) -> JSONMetadata:
        """
        Load metadata from JSON string.

        Args:
            json_str: JSON string

        Returns:
            Parsed and validated metadata

        Raises:
            ValidationError: If JSON is invalid or validation fails
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}")

        try:
            self.metadata = JSONMetadata(**data)
        except Exception as e:
            raise ValidationError(f"Validation failed: {e}")

        console.print(f"[green]✓[/green] Loaded {len(self.metadata.entities)} entities")

        return self.metadata

    def get_entity(self, name: str) -> Optional[EntityMetadata]:
        """
        Get entity by name.

        Args:
            name: Entity name

        Returns:
            Entity metadata or None if not found
        """
        if not self.metadata:
            return None

        for entity in self.metadata.entities:
            if entity.name == name:
                return entity

        return None

    def validate_relationships(self) -> List[str]:
        """
        Validate all relationships reference existing entities.

        Returns:
            List of validation errors (empty if valid)
        """
        if not self.metadata:
            return ["No metadata loaded"]

        errors = []
        entity_names = {e.name for e in self.metadata.entities}

        for entity in self.metadata.entities:
            for rel in entity.relationships:
                # Check target entity exists
                if rel.target not in entity_names:
                    errors.append(
                        f"{entity.name}.{rel.name}: Target entity '{rel.target}' not found"
                    )

                # Check via entity exists (for many-to-many)
                if rel.via and rel.via not in entity_names:
                    errors.append(
                        f"{entity.name}.{rel.name}: Via entity '{rel.via}' not found"
                    )

                # Validate fields exist
                if rel.local_field and rel.local_field not in [f.name for f in entity.fields]:
                    errors.append(
                        f"{entity.name}.{rel.name}: Local field '{rel.local_field}' not found"
                    )

        return errors

    def validate_foreign_keys(self) -> List[str]:
        """
        Validate all foreign key references.

        Returns:
            List of validation errors (empty if valid)
        """
        if not self.metadata:
            return ["No metadata loaded"]

        errors = []
        entity_map = {e.name: e for e in self.metadata.entities}

        for entity in self.metadata.entities:
            for field in entity.fields:
                if not field.foreign_key:
                    continue

                fk_ref = field.foreign_key.get('references', '')
                if '.' not in fk_ref:
                    errors.append(
                        f"{entity.name}.{field.name}: Invalid foreign key format '{fk_ref}'"
                    )
                    continue

                target_entity, target_field = fk_ref.split('.', 1)

                if target_entity not in entity_map:
                    errors.append(
                        f"{entity.name}.{field.name}: Foreign key references unknown entity '{target_entity}'"
                    )
                    continue

                target = entity_map[target_entity]
                if target_field not in [f.name for f in target.fields]:
                    errors.append(
                        f"{entity.name}.{field.name}: Foreign key references unknown field '{target_entity}.{target_field}'"
                    )

        return errors

    def get_summary(self) -> Dict[str, Any]:
        """
        Get metadata summary.

        Returns:
            Summary statistics
        """
        if not self.metadata:
            return {"status": "No metadata loaded"}

        total_fields = sum(len(e.fields) for e in self.metadata.entities)
        total_relationships = sum(len(e.relationships) for e in self.metadata.entities)

        entities_with_audit = sum(1 for e in self.metadata.entities if e.audit)
        entities_with_soft_delete = sum(1 for e in self.metadata.entities if e.soft_delete)

        return {
            "app_name": self.metadata.app.name,
            "version": self.metadata.app.version,
            "total_entities": len(self.metadata.entities),
            "total_fields": total_fields,
            "total_relationships": total_relationships,
            "entities_with_audit": entities_with_audit,
            "entities_with_soft_delete": entities_with_soft_delete,
            "backend_framework": self.metadata.app.backend.get("framework", "unknown"),
            "database_engine": self.metadata.app.backend.get("database", {}).get("engine", "unknown"),
        }


    def get_generation_options(self) -> Dict[str, Any]:
        """
        Get generation options.

        Returns:
            Generation options or default empty dict
        """
        if not self.metadata or not self.metadata.generation_options:
            return {}
        return self.metadata.generation_options


__all__ = [
    "JSONMetadataLoader",
    "JSONMetadata",
    "EntityMetadata",
    "FieldMetadata",
    "RelationshipMetadata",
    "EndpointMetadata",
    "AppMetadata",
]