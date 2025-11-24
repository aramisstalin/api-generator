"""
Property type enumeration.

Defines all supported property types for entity fields.
"""

from enum import Enum


class PropertyType(str, Enum):
    """
    Property type enumeration for entity fields.

    This enum defines all supported field types that can be used
    in both Schema.org and JSON metadata definitions.
    """

    # Text types
    STRING = "string"
    TEXT = "text"

    # Numeric types
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"

    # Boolean
    BOOLEAN = "boolean"

    # Date/Time types
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"

    # UUID
    UUID = "uuid"

    # Structured data
    JSON = "json"
    JSONB = "jsonb"

    # Array types
    ARRAY = "array"

    # Binary
    BINARY = "binary"
    BLOB = "blob"

    # Special types
    ENUM = "enum"
    REFERENCE = "reference"  # For relationships

    def __str__(self) -> str:
        """String representation."""
        return self.value

    @classmethod
    def from_string(cls, value: str) -> "PropertyType":
        """
        Get PropertyType from string value.

        Args:
            value: String value (case-insensitive)

        Returns:
            PropertyType enum member

        Raises:
            ValueError: If value is not a valid PropertyType
        """
        try:
            return cls(value.lower())
        except ValueError:
            # Try to find by name
            for member in cls:
                if member.name.lower() == value.lower():
                    return member
            raise ValueError(f"Invalid PropertyType: {value}")

    @property
    def python_type(self) -> str:
        """
        Get corresponding Python type annotation.

        Returns:
            Python type as string
        """
        mapping = {
            PropertyType.STRING: "str",
            PropertyType.TEXT: "str",
            PropertyType.INTEGER: "int",
            PropertyType.FLOAT: "float",
            PropertyType.DECIMAL: "Decimal",
            PropertyType.BOOLEAN: "bool",
            PropertyType.DATE: "date",
            PropertyType.DATETIME: "datetime",
            PropertyType.TIME: "time",
            PropertyType.UUID: "UUID",
            PropertyType.JSON: "Dict[str, Any]",
            PropertyType.JSONB: "Dict[str, Any]",
            PropertyType.ARRAY: "List",
            PropertyType.BINARY: "bytes",
            PropertyType.BLOB: "bytes",
            PropertyType.ENUM: "str",
            PropertyType.REFERENCE: "Any",
        }
        return mapping.get(self, "Any")

    @property
    def sqlalchemy_type(self) -> str:
        """
        Get corresponding SQLAlchemy column type.

        Returns:
            SQLAlchemy type as string
        """
        mapping = {
            PropertyType.STRING: "String",
            PropertyType.TEXT: "Text",
            PropertyType.INTEGER: "Integer",
            PropertyType.FLOAT: "Float",
            PropertyType.DECIMAL: "Numeric",
            PropertyType.BOOLEAN: "Boolean",
            PropertyType.DATE: "Date",
            PropertyType.DATETIME: "DateTime",
            PropertyType.TIME: "Time",
            PropertyType.UUID: "UUID",
            PropertyType.JSON: "JSON",
            PropertyType.JSONB: "JSONB",
            PropertyType.ARRAY: "ARRAY",
            PropertyType.BINARY: "LargeBinary",
            PropertyType.BLOB: "LargeBinary",
            PropertyType.ENUM: "Enum",
            PropertyType.REFERENCE: "ForeignKey",
        }
        return mapping.get(self, "String")

    @property
    def pydantic_type(self) -> str:
        """
        Get corresponding Pydantic field type.

        Returns:
            Pydantic type as string
        """
        mapping = {
            PropertyType.STRING: "str",
            PropertyType.TEXT: "str",
            PropertyType.INTEGER: "int",
            PropertyType.FLOAT: "float",
            PropertyType.DECIMAL: "condecimal(decimal_places=2)",
            PropertyType.BOOLEAN: "bool",
            PropertyType.DATE: "date",
            PropertyType.DATETIME: "datetime",
            PropertyType.TIME: "time",
            PropertyType.UUID: "UUID",
            PropertyType.JSON: "Dict[str, Any]",
            PropertyType.JSONB: "Dict[str, Any]",
            PropertyType.ARRAY: "List",
            PropertyType.BINARY: "bytes",
            PropertyType.BLOB: "bytes",
            PropertyType.ENUM: "str",
            PropertyType.REFERENCE: "UUID",
        }
        return mapping.get(self, "Any")

    @property
    def requires_import(self) -> list[str]:
        """
        Get required imports for this type.

        Returns:
            List of import statements needed
        """
        imports = {
            PropertyType.DECIMAL: ["from decimal import Decimal"],
            PropertyType.DATE: ["from datetime import date"],
            PropertyType.DATETIME: ["from datetime import datetime"],
            PropertyType.TIME: ["from datetime import time"],
            PropertyType.UUID: ["from uuid import UUID"],
            PropertyType.JSON: ["from typing import Dict, Any"],
            PropertyType.JSONB: ["from typing import Dict, Any"],
            PropertyType.ARRAY: ["from typing import List"],
            PropertyType.REFERENCE: ["from typing import Any"],
        }
        return imports.get(self, [])

    @property
    def is_numeric(self) -> bool:
        """Check if this is a numeric type."""
        return self in {
            PropertyType.INTEGER,
            PropertyType.FLOAT,
            PropertyType.DECIMAL
        }

    @property
    def is_temporal(self) -> bool:
        """Check if this is a date/time type."""
        return self in {
            PropertyType.DATE,
            PropertyType.DATETIME,
            PropertyType.TIME
        }

    @property
    def is_text(self) -> bool:
        """Check if this is a text type."""
        return self in {
            PropertyType.STRING,
            PropertyType.TEXT
        }

    @property
    def is_structured(self) -> bool:
        """Check if this is a structured data type."""
        return self in {
            PropertyType.JSON,
            PropertyType.JSONB,
            PropertyType.ARRAY
        }

    @property
    def supports_length(self) -> bool:
        """Check if this type supports length constraint."""
        return self in {
            PropertyType.STRING,
            PropertyType.BINARY,
            PropertyType.BLOB
        }

    @property
    def supports_precision(self) -> bool:
        """Check if this type supports precision/scale."""
        return self in {
            PropertyType.DECIMAL,
            PropertyType.FLOAT
        }

    @property
    def default_max_length(self) -> int | None:
        """Get default max length for this type."""
        defaults = {
            PropertyType.STRING: 255,
            PropertyType.UUID: 36,
        }
        return defaults.get(self)


# Type mapping for JSON metadata loader
JSON_TYPE_MAPPING = {
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
    "jsonb": PropertyType.JSONB,
    "json": PropertyType.JSON,
    "uuid[]": PropertyType.ARRAY,
    "string[]": PropertyType.ARRAY,
    "int[]": PropertyType.ARRAY,
    "binary": PropertyType.BINARY,
    "blob": PropertyType.BLOB,
}

# Reverse mapping for code generation
PROPERTY_TYPE_TO_JSON = {v: k for k, v in JSON_TYPE_MAPPING.items()}


def get_property_type(type_str: str) -> PropertyType:
    """
    Get PropertyType from string.

    Tries JSON mapping first, then enum conversion.

    Args:
        type_str: Type string

    Returns:
        PropertyType

    Raises:
        ValueError: If type is not recognized
    """
    # Try JSON mapping first
    if type_str.lower() in JSON_TYPE_MAPPING:
        return JSON_TYPE_MAPPING[type_str.lower()]

    # Try enum conversion
    return PropertyType.from_string(type_str)


__all__ = [
    "PropertyType",
    "JSON_TYPE_MAPPING",
    "PROPERTY_TYPE_TO_JSON",
    "get_property_type",
]