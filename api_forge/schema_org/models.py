"""
Data models for Schema.org entities.

Represents parsed Schema.org entity definitions in a structured format.
"""

from dataclasses import field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum

from pydantic import BaseModel


class PropertyType(str, Enum):
    """Type of Schema.org property."""
    DATATYPE = "datatype"  # Basic data types (Text, Number, etc.)
    ENTITY = "entity"  # Reference to another Schema.org entity
    ENUMERATION = "enumeration"  # Enumeration values


class RelationshipType(str, Enum):
    """Type of relationship between entities."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class SchemaProperty(BaseModel):
    """
    Represents a property/field property.

    Attributes:
        name: Property name
        description: Human-readable description
        expected_types: List of expected Schema.org types
        domain_includes: Entities that can have this property
        range_includes: Possible types for this property
        required: Whether the property is required
        multiple: Whether property can have multiple values
    """
    name: str
    description: str
    expected_types: List[str] = field(default_factory=list)
    domain_includes: List[str] = field(default_factory=list)
    range_includes: List[str] = field(default_factory=list)

    required: Optional[bool] = False
    multiple: Optional[bool] = False

    # default_value: Optional[Any] = None

    # Type information (added by type mapper)
    type_info: Optional[Dict[str, Any]] = None

    # Field metadata (from JSON metadata)
    field_metadata: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

    @property
    def property_type(self) -> PropertyType:
        """Determine if this is a datatype or entity property."""
        if self.type_info:
            return self.type_info.get("property_type")

        # Check if any expected type is a Schema.org entity
        schema_datatypes = {
            "Text", "Number", "Integer", "Float", "Boolean",
            "Date", "DateTime", "Time", "URL", "Duration"
        }

        for expected_type in self.expected_types:
            if expected_type not in schema_datatypes:
                return PropertyType.ENTITY

        return PropertyType.DATATYPE

    @property
    def is_relationship(self) -> bool:
        """Check if this property represents a relationship."""
        return self.property_type == PropertyType.ENTITY

    @property
    def python_type(self) -> str:
        """Get Python type."""
        if self.type_info:
            return self.type_info.get("python_type", "Any")
        return "Any"

    @property
    def is_array(self) -> bool:
        """Check if this is an array type."""
        if self.type_info:
            return self.type_info.get("is_array", False)
        return False

    @property
    def is_optional(self) -> bool:
        """Check if this field is optional."""
        return not self.required

    @property
    def is_primary_key(self) -> bool:
        """Check if this is a primary key field."""
        if self.field_metadata:
            return self.field_metadata.get("primary", False)
        return self.name == "id"

    @property
    def is_unique(self) -> bool:
        """Check if this field has unique constraint."""
        if self.field_metadata:
            return self.field_metadata.get("unique", False)
        return False

    @property
    def is_foreign_key(self) -> bool:
        """Check if this is a foreign key."""
        if self.field_metadata:
            return self.field_metadata.get("foreign_key") is not None
        return False

    @property
    def default_value(self) -> Any:
        """Get default value if specified."""
        if self.field_metadata:
            return self.field_metadata.get("default")
        return None

    @property
    def max_length(self) -> Optional[int]:
        """Get max length constraint."""
        if self.field_metadata:
            return self.field_metadata.get("max_length")
        return None

    @property
    def validation_rules(self) -> Dict[str, Any]:
        """Get validation rules."""
        if self.field_metadata:
            return self.field_metadata.get("validation", {})
        return {}


class RelationshipInfo(BaseModel):
    """
    Information about a relationship between entities.

    Attributes:
        type: Type of relationship
        target_entity: Target entity name
        foreign_key: Foreign key field name (for many_to_one)
        association_table: Association table name (for many_to_many)
        back_populates: Name for back reference
    """
    type: RelationshipType
    target_entity: str
    source_entity: str
    property_name: Optional[str] = None # Can be None in many-to-many relationships
    name: Optional[str] = None
    foreign_key: Optional[str] = None
    association_table: Optional[str] = None
    back_populates: Optional[str] = None

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = None

    @property
    def is_one_to_one(self) -> bool:
        """Check if this is a one-to-one relationship."""
        return self.type == "one-to-one"

    @property
    def is_one_to_many(self) -> bool:
        """Check if this is a one-to-many relationship."""
        return self.type == "one-to-many"

    @property
    def is_many_to_one(self) -> bool:
        """Check if this is a many-to-one relationship."""
        return self.type == "many-to-one"

    @property
    def is_many_to_many(self) -> bool:
        """Check if this is a many-to-many relationship."""
        return self.type == "many-to-many"

    @property
    def is_self_referencing(self) -> bool:
        """Check if this is a self-referencing relationship."""
        return self.type == "self-referencing" or self.source_entity == self.target_entity

    @property
    def via_table(self) -> Optional[str]:
        """Get join table name for many-to-many."""
        if self.metadata:
            return self.metadata.get("via")
        return None

    @property
    def cascade(self) -> Optional[str]:
        """Get cascade rule."""
        if self.metadata:
            return self.metadata.get("cascade")
        return None

    @property
    def eager_load(self) -> bool:
        """Check if relationship should be eager loaded."""
        if self.metadata:
            return self.metadata.get("eager_load", False)
        return False


class ValidationRule(BaseModel):
    """
    Validation rule for a property.

    Attributes:
        type: Type of validation (e.g., "string_length", "url_validation")
        params: Parameters for the validation
        validator: Pydantic validator name
        error_message: Custom error message
    """
    type: str
    params: Dict[str, Any] = field(default_factory=dict)
    validator: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def is_required(self) -> bool:
        """Check if this is a required validation."""
        return self.type == "required"

    @property
    def is_unique(self) -> bool:
        """Check if this is a unique validation."""
        return self.type == "unique"

    @property
    def is_pattern(self) -> bool:
        """Check if this is a pattern validation."""
        return self.type == "pattern"


class TypeInfo(BaseModel):
    """
    Information about mapped Python types.

    Attributes:
        python_type: Python type annotation
        sql_type: SQLAlchemy column type
        pydantic_annotation: Pydantic type annotation string
        is_relationship: Whether this is a relationship type
        is_optional: Whether the type is optional
    """
    python_type: str
    sql_type: str
    pydantic_annotation: str
    is_relationship: bool = False
    is_optional: bool = True


class SchemaEntity(BaseModel):
    """
    Represents a complete Schema.org entity definition.

    Attributes:
        name: Entity name (e.g., "Person", "Organization")
        url: Schema.org URL for this entity
        description: Human-readable description
        properties: Dictionary of property definitions
        parent_types: List of parent types (inheritance)
        sub_types: List of child types
        relationships: List of relationships to other entities
        validation_rules: Dictionary of validation rules per property
    """
    name: Optional[str] = None
    url: Optional[str] = None
    description: str
    properties: Dict[str, SchemaProperty] = field(default_factory=dict)
    parent_types: List[str] = field(default_factory=list)
    sub_types: List[str] = field(default_factory=list)
    relationships: List[RelationshipInfo] = field(default_factory=list)
    validation_rules: Dict[str, List[ValidationRule]] = field(default_factory=dict)

    # Additional metadata (from JSON metadata)
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

    @property
    def table_name(self) -> str:
        """Get the database table name for this entity."""
        if self.metadata:
            return self.metadata.get("table_name", self.name.lower() + "s")
        return self.name.lower()

    @property
    def primary_keys(self) -> List[str]:
        """Get primary key field names."""
        pks = []
        for prop_name, prop in self.properties.items():
            if prop.is_primary_key:
                pks.append(prop_name)

        # Check for composite primary key in metadata
        if self.metadata and self.metadata.get("composite_primary_key"):
            return self.metadata["composite_primary_key"]

        return pks or ["id"]

    @property
    def unique_fields(self) -> List[str]:
        """Get unique field names."""
        return [
            prop_name for prop_name, prop in self.properties.items()
            if prop.is_unique
        ]

    @property
    def foreign_keys(self) -> Dict[str, Dict[str, Any]]:
        """Get foreign key mappings."""
        fks = {}
        for prop_name, prop in self.properties.items():
            if prop.is_foreign_key and prop.field_metadata:
                fks[prop_name] = prop.field_metadata["foreign_key"]
        return fks

    @property
    def has_relationships(self) -> bool:
        """Check if entity has any relationships."""
        return len(self.relationships) > 0

    def add_relationship(self, relationship: RelationshipInfo) -> None:
        """Add a relationship to this entity."""
        self.relationships.append(relationship)

    def get_relationship(self, name: str) -> Optional[RelationshipInfo]:
        """Get relationship by name."""
        for rel in self.relationships:
            if rel.name == name:
                return rel
        return None

    @property
    def required_properties(self) -> List[SchemaProperty]:
        """Get list of required properties."""
        return [prop for prop in self.properties.values() if prop.required]

    @property
    def optional_properties(self) -> List[SchemaProperty]:
        """Get list of optional properties."""
        return [prop for prop in self.properties.values() if not prop.required]

    @property
    def has_audit(self) -> bool:
        """Check if audit logging is enabled."""
        if self.metadata:
            return self.metadata.get("audit", False)
        return False

    @property
    def has_soft_delete(self) -> bool:
        """Check if soft delete is enabled."""
        if self.metadata:
            return self.metadata.get("soft_delete", False)
        return False

    @property
    def permissions(self) -> Optional[Dict[str, List[str]]]:
        """Get permissions configuration."""
        if self.metadata:
            return self.metadata.get("permissions")
        return None

    @property
    def indexes(self) -> List[Dict[str, Any]]:
        """Get index definitions."""
        if self.metadata:
            return self.metadata.get("indexes", [])
        return []

    def get_property(self, name: str) -> Optional[SchemaProperty]:
        """Get a property by name."""
        return self.properties.get(name)

    def add_validation_rule(self, property_name: str, rule: ValidationRule) -> None:
        """Add a validation rule for a property."""
        if property_name not in self.validation_rules:
            self.validation_rules[property_name] = []
        self.validation_rules[property_name].append(rule)


class EntityAnalysis(BaseModel):
    """
    Enhanced entity analysis from AI.

    Contains business logic insights and recommendations from AI analysis.

    Attributes:
        entity: The base Schema.org entity
        suggested_indexes: List of fields that should be indexed
        unique_fields: Fields that should be unique
        immutable_fields: Fields that can't be changed after creation
        computed_fields: Fields that are computed from other fields
        business_rules: Custom business logic rules
        security_considerations: Security-related notes
    """
    entity: SchemaEntity
    suggested_indexes: List[str] = field(default_factory=list)
    unique_fields: List[str] = field(default_factory=list)
    immutable_fields: List[str] = field(default_factory=list)
    computed_fields: Dict[str, str] = field(default_factory=dict)
    business_rules: List[Dict[str, Any]] = field(default_factory=list)
    security_considerations: List[str] = field(default_factory=list)
    recommended_defaults: Dict[str, Any] = field(default_factory=dict)

    # AI enhancement metadata
    ai_enhanced: bool = False
    analysis_timestamp: Optional[datetime] = None

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

    @property
    def has_ai_insights(self) -> bool:
        """Check if AI insights are present."""
        return bool(
            self.business_rules or
            self.security_considerations or
            self.ai_enhanced
        )

    @property
    def total_properties(self) -> int:
        """Get total number of properties."""
        return len(self.entity.properties)

    @property
    def total_relationships(self) -> int:
        """Get total number of relationships."""
        return len(self.entity.relationships)

    @property
    def required_fields_count(self) -> int:
        """Get count of required fields."""
        return len(self.entity.get_required_properties())

    def get_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        return {
            "entity_name": self.entity.name,
            "table_name": self.entity.table_name,
            "properties": self.total_properties,
            "relationships": self.total_relationships,
            "required_fields": self.required_fields_count,
            "unique_fields": len(self.unique_fields),
            "suggested_indexes": len(self.suggested_indexes),
            "immutable_fields": len(self.immutable_fields),
            "has_audit": self.entity.has_audit,
            "has_soft_delete": self.entity.has_soft_delete,
            "ai_enhanced": self.ai_enhanced,
        }

__all__ = [
    "PropertyType",
    "RelationshipType",
    "SchemaProperty",
    "RelationshipInfo",
    "ValidationRule",
    "TypeInfo",
    "SchemaEntity",
    "EntityAnalysis",
]