"""
Type mapper for Schema.org to Python types.

Maps Schema.org data types to appropriate Python, SQLAlchemy, and Pydantic types.
"""

from typing import Dict, List, Tuple, Optional
import sqlalchemy as sa
from datetime import date, datetime, time, timedelta

from api_forge.schema_org.models import TypeInfo, SchemaProperty
from api_forge.core.exceptions import SchemaOrgError


class TypeMapper:
    """
    Maps Schema.org types to Python ecosystem types.

    Provides mapping for:
    - Python native types
    - SQLAlchemy column types
    - Pydantic type annotations
    """

    # Core type mappings: Schema.org -> (Python type, SQLAlchemy type, Pydantic annotation)
    TYPE_MAP: Dict[str, Tuple[str, str, str]] = {
        # Text types
        "Text": ("str", "sa.String(255)", "str"),
        "URL": ("str", "sa.String(500)", "AnyHttpUrl"),

        # Numeric types
        "Integer": ("int", "sa.Integer", "int"),
        "Float": ("float", "sa.Float", "float"),
        "Number": ("float", "sa.Numeric(10, 2)", "Decimal"),

        # Boolean
        "Boolean": ("bool", "sa.Boolean", "bool"),

        # Date/Time types
        "Date": ("date", "sa.Date", "date"),
        "DateTime": ("datetime", "sa.DateTime", "datetime"),
        "Time": ("time", "sa.Time", "time"),
        "Duration": ("timedelta", "sa.Interval", "timedelta"),

        # Special types
        "DataType": ("str", "sa.String(255)", "str"),
        "Thing": ("str", "sa.String(255)", "str"),
    }

    # Email patterns for property names
    EMAIL_PATTERNS = ["email", "emailaddress", "contactemail"]

    # Phone patterns for property names
    PHONE_PATTERNS = ["phone", "telephone", "fax", "mobile"]

    # Common large text fields
    TEXT_FIELDS = ["description", "abstract", "text", "content", "body", "bio", "about"]

    def __init__(self):
        """Initialize type mapper."""
        pass

    def resolve_type(
            self,
            schema_property: SchemaProperty,
            allow_multiple: bool = False
    ) -> TypeInfo:
        """
        Resolve Schema.org property to Python types.

        Args:
            schema_property: Schema.org property to resolve
            allow_multiple: Whether to allow multiple values (arrays)

        Returns:
            TypeInfo with mapped types

        Raises:
            SchemaOrgError: If type cannot be resolved
        """
        # Get expected types
        expected_types = schema_property.expected_types

        if not expected_types:
            # Default to Text if no type specified
            expected_types = ["Text"]

        # Take the first expected type (primary type)
        primary_type = expected_types[0]

        # Check if it's a known Schema.org datatype
        if primary_type in self.TYPE_MAP:
            base_type = self.TYPE_MAP[primary_type]

            # Apply special handling based on property name
            base_type = self._apply_special_handling(schema_property.name, base_type)

            # Handle multiple values (arrays)
            if allow_multiple or schema_property.multiple:
                return TypeInfo(
                    python_type=f"List[{base_type[0]}]",
                    sql_type=f"sa.ARRAY({base_type[1]})",
                    pydantic_annotation=f"List[{base_type[2]}]",
                    is_relationship=False,
                    is_optional=not schema_property.required
                )

            return TypeInfo(
                python_type=base_type[0],
                sql_type=base_type[1],
                pydantic_annotation=base_type[2],
                is_relationship=False,
                is_optional=not schema_property.required
            )

        # It's a Schema.org entity reference (relationship)
        return TypeInfo(
            python_type=primary_type,
            sql_type="sa.Integer",  # Will be foreign key
            pydantic_annotation=f"Optional['{primary_type}Schema']",
            is_relationship=True,
            is_optional=not schema_property.required
        )

    def _apply_special_handling(
            self,
            property_name: str,
            base_type: Tuple[str, str, str]
    ) -> Tuple[str, str, str]:
        """
        Apply special handling based on property name patterns.

        Args:
            property_name: Name of the property
            base_type: Base type tuple

        Returns:
            Modified type tuple
        """
        lower_name = property_name.lower()

        # Email fields
        if any(pattern in lower_name for pattern in self.EMAIL_PATTERNS):
            return ("str", "sa.String(255)", "EmailStr")

        # Phone fields
        if any(pattern in lower_name for pattern in self.PHONE_PATTERNS):
            return ("str", "sa.String(20)", "str")

        # Large text fields
        if any(pattern in lower_name for pattern in self.TEXT_FIELDS):
            return ("str", "sa.Text", "str")

        # URL fields (even if not typed as URL)
        if "url" in lower_name or "link" in lower_name or "website" in lower_name:
            return ("str", "sa.String(500)", "AnyHttpUrl")

        return base_type

    def get_python_type(self, schema_type: str) -> str:
        """Get Python type for Schema.org type."""
        if schema_type in self.TYPE_MAP:
            return self.TYPE_MAP[schema_type][0]
        return schema_type  # Entity type

    def get_sqlalchemy_type(self, schema_type: str) -> str:
        """Get SQLAlchemy type for Schema.org type."""
        if schema_type in self.TYPE_MAP:
            return self.TYPE_MAP[schema_type][1]
        return "sa.Integer"  # Foreign key for relationships

    def get_pydantic_annotation(self, schema_type: str) -> str:
        """Get Pydantic annotation for Schema.org type."""
        if schema_type in self.TYPE_MAP:
            return self.TYPE_MAP[schema_type][2]
        return f"Optional['{schema_type}Schema']"  # Relationship

    def is_numeric_type(self, schema_type: str) -> bool:
        """Check if type is numeric."""
        return schema_type in ["Integer", "Float", "Number"]

    def is_datetime_type(self, schema_type: str) -> bool:
        """Check if type is date/time related."""
        return schema_type in ["Date", "DateTime", "Time", "Duration"]

    def is_text_type(self, schema_type: str) -> bool:
        """Check if type is text-based."""
        return schema_type in ["Text", "URL", "DataType"]

    def needs_validation(self, property_name: str, schema_type: str) -> List[str]:
        """
        Determine what validations are needed for a property.

        Args:
            property_name: Name of the property
            schema_type: Schema.org type

        Returns:
            List of validator names to apply
        """
        validators = []
        lower_name = property_name.lower()

        # Email validation
        if any(pattern in lower_name for pattern in self.EMAIL_PATTERNS):
            validators.append("email_validator")

        # URL validation
        if schema_type == "URL" or "url" in lower_name:
            validators.append("url_validator")

        # Phone validation
        if any(pattern in lower_name for pattern in self.PHONE_PATTERNS):
            validators.append("phone_validator")

        # Numeric range validation
        if self.is_numeric_type(schema_type):
            if "age" in lower_name:
                validators.append("age_validator")
            elif "rating" in lower_name:
                validators.append("rating_validator")

        # String length validation
        if self.is_text_type(schema_type):
            validators.append("string_length_validator")

        return validators


__all__ = ["TypeMapper"]