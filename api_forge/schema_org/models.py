"""
Data models for Schema.org entities.

Represents parsed Schema.org entity definitions in a structured format.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


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


@dataclass
class SchemaProperty:
    """
    Represents a Schema.org property.

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
    required: bool = False
    multiple: bool = False
    default_value: Optional[Any] = None

    @property
    def property_type(self) -> PropertyType:
        """Determine if this is a datatype or entity property."""
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


@dataclass
class RelationshipInfo:
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
    property_name: str
    foreign_key: Optional[str] = None
    association_table: Optional[str] = None
    back_populates: Optional[str] = None
    cascade: Optional[str] = None


@dataclass
class ValidationRule:
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


@dataclass
class TypeInfo:
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


@dataclass
class SchemaEntity:
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
    name: str
    url: str
    description: str
    properties: Dict[str, SchemaProperty] = field(default_factory=dict)
    parent_types: List[str] = field(default_factory=list)
    sub_types: List[str] = field(default_factory=list)
    relationships: List[RelationshipInfo] = field(default_factory=list)
    validation_rules: Dict[str, List[ValidationRule]] = field(default_factory=dict)

    @property
    def table_name(self) -> str:
        """Get the database table name for this entity."""
        return self.name.lower() + "s"

    @property
    def has_relationships(self) -> bool:
        """Check if entity has any relationships."""
        return len(self.relationships) > 0

    @property
    def required_properties(self) -> List[SchemaProperty]:
        """Get list of required properties."""
        return [prop for prop in self.properties.values() if prop.required]

    @property
    def optional_properties(self) -> List[SchemaProperty]:
        """Get list of optional properties."""
        return [prop for prop in self.properties.values() if not prop.required]

    def get_property(self, name: str) -> Optional[SchemaProperty]:
        """Get a property by name."""
        return self.properties.get(name)

    def add_relationship(self, relationship: RelationshipInfo) -> None:
        """Add a relationship to this entity."""
        self.relationships.append(relationship)

    def add_validation_rule(self, property_name: str, rule: ValidationRule) -> None:
        """Add a validation rule for a property."""
        if property_name not in self.validation_rules:
            self.validation_rules[property_name] = []
        self.validation_rules[property_name].append(rule)


@dataclass
class EntityAnalysis:
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