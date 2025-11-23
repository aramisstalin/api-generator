"""
Tests for JSON metadata loader.
"""

import pytest
import json
from pathlib import Path
from api_forge.core.exceptions import ValidationError
from api_forge.json_metadata.loader import (
    JSONMetadataLoader,
    EntityMetadata,
    FieldMetadata,
    EndpointMetadata
)


@pytest.fixture
def sample_metadata_dict():
    """Sample metadata as dictionary."""
    return {
        "app": {
            "name": "TestApp",
            "description": "Test application",
            "version": "1.0.0",
            "backend": {
                "framework": "fastapi",
                "database": {"engine": "postgresql"}
            }
        },
        "entities": [
            {
                "name": "User",
                "table_name": "users",
                "description": "Test user",
                "fields": [
                    {
                        "name": "id",
                        "type": "uuid",
                        "primary": True,
                        "nullable": False
                    },
                    {
                        "name": "email",
                        "type": "string",
                        "format": "email",
                        "unique": True,
                        "nullable": False
                    }
                ],
                "relationships": [],
                "endpoints": {
                    "base_path": "/api/users",
                    "crud": True
                }
            }
        ]
    }


@pytest.fixture
def sample_metadata_file(tmp_path, sample_metadata_dict):
    """Create temporary metadata file."""
    file_path = tmp_path / "metadata.json"
    with open(file_path, 'w') as f:
        json.dump(sample_metadata_dict, f)
    return file_path


class TestJSONMetadataLoader:
    """Test JSONMetadataLoader class."""

    def test_load_from_file_success(self, sample_metadata_file):
        """Test successful file loading."""
        loader = JSONMetadataLoader()
        metadata = loader.load_from_file(sample_metadata_file)

        assert metadata is not None
        assert metadata.app.name == "TestApp"
        assert len(metadata.entities) == 1
        assert metadata.entities[0].name == "User"

    def test_load_from_file_not_found(self):
        """Test loading non-existent file."""
        loader = JSONMetadataLoader()

        with pytest.raises(ValidationError) as exc:
            loader.load_from_file(Path("nonexistent.json"))

        assert "not found" in str(exc.value.message).lower()

    def test_load_from_file_invalid_json(self, tmp_path):
        """Test loading invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("{ invalid json }")

        loader = JSONMetadataLoader()

        with pytest.raises(ValidationError) as exc:
            loader.load_from_file(file_path)

        assert "invalid json" in str(exc.value.message).lower()

    def test_load_from_string_success(self, sample_metadata_dict):
        """Test loading from JSON string."""
        loader = JSONMetadataLoader()
        json_str = json.dumps(sample_metadata_dict)

        metadata = loader.load_from_string(json_str)

        assert metadata is not None
        assert metadata.app.name == "TestApp"

    def test_load_from_string_invalid(self):
        """Test loading invalid JSON string."""
        loader = JSONMetadataLoader()

        with pytest.raises(ValidationError):
            loader.load_from_string("{ invalid }")

    def test_get_entity_found(self, sample_metadata_file):
        """Test getting entity by name."""
        loader = JSONMetadataLoader()
        loader.load_from_file(sample_metadata_file)

        entity = loader.get_entity("User")

        assert entity is not None
        assert entity.name == "User"
        assert entity.table_name == "users"

    def test_get_entity_not_found(self, sample_metadata_file):
        """Test getting non-existent entity."""
        loader = JSONMetadataLoader()
        loader.load_from_file(sample_metadata_file)

        entity = loader.get_entity("NonExistent")

        assert entity is None

    def test_validate_relationships_valid(self, sample_metadata_file):
        """Test validating correct relationships."""
        loader = JSONMetadataLoader()
        loader.load_from_file(sample_metadata_file)

        errors = loader.validate_relationships()

        assert errors == []

    def test_validate_relationships_invalid_target(self, tmp_path):
        """Test validation with invalid relationship target."""
        metadata = {
            "app": {
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "backend": {"framework": "fastapi"}
            },
            "entities": [
                {
                    "name": "Order",
                    "table_name": "orders",
                    "description": "Orders",
                    "fields": [{"name": "id", "type": "uuid", "primary": True}],
                    "relationships": [
                        {
                            "type": "many-to-one",
                            "target": "NonExistent",
                            "local_field": "user_id",
                            "remote_field": "id",
                            "name": "user"
                        }
                    ],
                    "endpoints": {"base_path": "/api/orders", "crud": True}
                }
            ]
        }

        file_path = tmp_path / "invalid_rel.json"
        with open(file_path, 'w') as f:
            json.dump(metadata, f)

        loader = JSONMetadataLoader()
        loader.load_from_file(file_path)

        errors = loader.validate_relationships()

        assert len(errors) > 0
        assert any("NonExistent" in error for error in errors)

    def test_validate_foreign_keys_valid(self, tmp_path):
        """Test validating correct foreign keys."""
        metadata = {
            "app": {
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "backend": {"framework": "fastapi"}
            },
            "entities": [
                {
                    "name": "User",
                    "table_name": "users",
                    "description": "Users",
                    "fields": [
                        {"name": "id", "type": "uuid", "primary": True}
                    ],
                    "relationships": [],
                    "endpoints": {"base_path": "/api/users", "crud": True}
                },
                {
                    "name": "Post",
                    "table_name": "posts",
                    "description": "Posts",
                    "fields": [
                        {"name": "id", "type": "uuid", "primary": True},
                        {
                            "name": "user_id",
                            "type": "uuid",
                            "foreign_key": {
                                "references": "User.id",
                                "on_delete": "CASCADE"
                            }
                        }
                    ],
                    "relationships": [],
                    "endpoints": {"base_path": "/api/posts", "crud": True}
                }
            ]
        }

        file_path = tmp_path / "valid_fk.json"
        with open(file_path, 'w') as f:
            json.dump(metadata, f)

        loader = JSONMetadataLoader()
        loader.load_from_file(file_path)

        errors = loader.validate_foreign_keys()

        assert errors == []

    def test_validate_foreign_keys_invalid(self, tmp_path):
        """Test validation with invalid foreign key."""
        metadata = {
            "app": {
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "backend": {"framework": "fastapi"}
            },
            "entities": [
                {
                    "name": "Post",
                    "table_name": "posts",
                    "description": "Posts",
                    "fields": [
                        {"name": "id", "type": "uuid", "primary": True},
                        {
                            "name": "user_id",
                            "type": "uuid",
                            "foreign_key": {
                                "references": "NonExistent.id"
                            }
                        }
                    ],
                    "relationships": [],
                    "endpoints": {"base_path": "/api/posts", "crud": True}
                }
            ]
        }

        file_path = tmp_path / "invalid_fk.json"
        with open(file_path, 'w') as f:
            json.dump(metadata, f)

        loader = JSONMetadataLoader()
        loader.load_from_file(file_path)

        errors = loader.validate_foreign_keys()

        assert len(errors) > 0
        assert any("NonExistent" in error for error in errors)

    def test_get_summary(self, sample_metadata_file):
        """Test getting metadata summary."""
        loader = JSONMetadataLoader()
        loader.load_from_file(sample_metadata_file)

        summary = loader.get_summary()

        assert summary['app_name'] == "TestApp"
        assert summary['version'] == "1.0.0"
        assert summary['total_entities'] == 1
        assert summary['total_fields'] == 2
        assert summary['backend_framework'] == "fastapi"

    def test_validation_empty_entities(self):
        """Test validation with no entities."""
        loader = JSONMetadataLoader()

        metadata_dict = {
            "app": {
                "name": "Test",
                "description": "Test",
                "version": "1.0.0",
                "backend": {"framework": "fastapi"}
            },
            "entities": []
        }

        with pytest.raises(ValidationError):
            loader.load_from_string(json.dumps(metadata_dict))


class TestFieldMetadata:
    """Test FieldMetadata model."""

    def test_field_metadata_basic(self):
        """Test basic field creation."""
        field = FieldMetadata(
            name="id",
            type="uuid",
            primary=True,
            nullable=False
        )

        assert field.name == "id"
        assert field.type == "uuid"
        assert field.primary is True
        assert field.nullable is False

    def test_field_metadata_defaults(self):
        """Test field defaults."""
        field = FieldMetadata(
            name="email",
            type="string"
        )

        assert field.primary is False
        assert field.nullable is True
        assert field.unique is False

    def test_field_metadata_with_validation(self):
        """Test field with validation rules."""
        field = FieldMetadata(
            name="email",
            type="string",
            validation={
                "pattern": "^[^@]+@[^@]+$",
                "min_length": 5,
                "max_length": 100
            }
        )

        assert field.validation is not None
        assert "pattern" in field.validation


class TestEntityMetadata:
    """Test EntityMetadata model."""

    def test_entity_metadata_basic(self):
        """Test basic entity creation."""
        entity = EntityMetadata(
            name="User",
            table_name="users",
            description="User entity",
            fields=[
                FieldMetadata(name="id", type="uuid", primary=True)
            ],
            endpoints=EndpointMetadata(
                base_path="/api/users",
                crud=True
            )
        )

        assert entity.name == "User"
        assert entity.table_name == "users"
        assert len(entity.fields) == 1
        assert entity.audit is False

    def test_entity_metadata_with_features(self):
        """Test entity with audit and soft delete."""
        entity = EntityMetadata(
            name="Product",
            table_name="products",
            description="Products",
            audit=True,
            soft_delete=True,
            fields=[
                FieldMetadata(name="id", type="uuid", primary=True)
            ],
            endpoints=EndpointMetadata(
                base_path="/api/products",
                crud=True
            )
        )

        assert entity.audit is True
        assert entity.soft_delete is True