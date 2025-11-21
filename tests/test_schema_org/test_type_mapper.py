"""
Unit tests for TypeMapper.
"""

import pytest
from api_forge.schema_org.type_mapper import TypeMapper
from api_forge.schema_org.models import SchemaProperty


class TestTypeMapper:
    """Test TypeMapper functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mapper = TypeMapper()

    def test_resolve_text_type(self):
        """Test resolving Text type."""
        prop = SchemaProperty(
            name="name",
            description="Person's name",
            expected_types=["Text"]
        )

        type_info = self.mapper.resolve_type(prop)

        assert type_info.python_type == "str"
        assert "String" in type_info.sql_type
        assert type_info.pydantic_annotation == "str"
        assert not type_info.is_relationship

    def test_resolve_integer_type(self):
        """Test resolving Integer type."""
        prop = SchemaProperty(
            name="age",
            description="Person's age",
            expected_types=["Integer"]
        )

        type_info = self.mapper.resolve_type(prop)

        assert type_info.python_type == "int"
        assert "Integer" in type_info.sql_type
        assert type_info.pydantic_annotation == "int"

    def test_resolve_email_property(self):
        """Test special handling for email properties."""
        prop = SchemaProperty(
            name="email",
            description="Email address",
            expected_types=["Text"]
        )

        type_info = self.mapper.resolve_type(prop)

        assert type_info.pydantic_annotation == "EmailStr"

    def test_resolve_url_type(self):
        """Test resolving URL type."""
        prop = SchemaProperty(
            name="website",
            description="Website URL",
            expected_types=["URL"]
        )

        type_info = self.mapper.resolve_type(prop)

        assert type_info.pydantic_annotation == "AnyHttpUrl"

    def test_resolve_entity_relationship(self):
        """Test resolving entity relationships."""
        prop = SchemaProperty(
            name="organization",
            description="Person's organization",
            expected_types=["Organization"]
        )

        type_info = self.mapper.resolve_type(prop)

        assert type_info.python_type == "Organization"
        assert type_info.is_relationship
        assert "OrganizationSchema" in type_info.pydantic_annotation

    def test_resolve_multiple_values(self):
        """Test resolving array/multiple values."""
        prop = SchemaProperty(
            name="tags",
            description="Tags",
            expected_types=["Text"],
            multiple=True
        )

        type_info = self.mapper.resolve_type(prop, allow_multiple=True)

        assert "List" in type_info.python_type
        assert "ARRAY" in type_info.sql_type

    def test_needs_validation(self):
        """Test validation detection."""
        validators = self.mapper.needs_validation("email", "Text")
        assert "email_validator" in validators

        validators = self.mapper.needs_validation("age", "Integer")
        assert "age_validator" in validators

        validators = self.mapper.needs_validation("website", "URL")
        assert "url_validator" in validators