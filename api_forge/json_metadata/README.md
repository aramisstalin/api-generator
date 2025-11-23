# JSON Metadata Generation - Usage Guide

## Overview

API Forge now supports generating FastAPI applications from JSON metadata files, providing an alternative to Schema.org-based generation. This approach gives you full control over your application structure, database schema, and business logic.

## Quick Start

### 1. Create Metadata File

Create a JSON file (e.g., `my-app.json`) with your application definition:

```json
{
  "app": {
    "name": "MyApp",
    "description": "My FastAPI application",
    "version": "1.0.0",
    "backend": {
      "framework": "fastapi",
      "database": {
        "engine": "postgresql"
      }
    }
  },
  "entities": [
    {
      "name": "User",
      "table_name": "users",
      "description": "Application users",
      "fields": [
        {
          "name": "id",
          "type": "uuid",
          "primary": true
        },
        {
          "name": "email",
          "type": "string",
          "format": "email",
          "unique": true,
          "nullable": false
        }
      ],
      "endpoints": {
        "base_path": "/api/users",
        "crud": true
      }
    }
  ]
}
```

### 2. Generate Application

```bash
# Basic generation
api-forge json generate my-app.json

# With AI enhancement
api-forge json generate my-app.json --ai

# Custom output directory
api-forge json generate my-app.json -o ./my-backend

# Dry run (preview only)
api-forge json generate my-app.json --dry-run
```

### 3. Run Your Application

```bash
cd generated
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database URL
alembic upgrade head
uvicorn main:app --reload
```

## CLI Commands

### Generate

Generate FastAPI application from JSON metadata:

```bash
api-forge json generate METADATA_FILE [OPTIONS]

Options:
  -o, --output PATH          Output directory [default: ./generated]
  --ai/--no-ai              Enable AI enhancement [default: no-ai]
  --api-key TEXT            Anthropic API key (or use ANTHROPIC_API_KEY env)
  -f, --force               Overwrite existing output directory
  --dry-run                 Preview generation without creating files
```

### Validate

Validate metadata file without generating:

```bash
api-forge json validate METADATA_FILE
```

Checks for:
- Valid JSON syntax
- Required fields present
- Relationship consistency
- Foreign key references

### Inspect

Inspect metadata and view entity details:

```bash
# List all entities
api-forge json inspect METADATA_FILE

# Inspect specific entity
api-forge json inspect METADATA_FILE --entity User
```

## Metadata Structure

### Application Configuration

```json
{
  "app": {
    "name": "AppName",
    "description": "App description",
    "version": "1.0.0",
    "locale": "en-US",
    "timezone": "UTC",
    "backend": {
      "framework": "fastapi",
      "orm": "sqlalchemy",
      "database": {
        "engine": "postgresql",
        "driver": "psycopg2",
        "connection_url_env": "DATABASE_URL",
        "migrations": "alembic"
      },
      "auth": {
        "type": "jwt",
        "jwt_secret_env": "JWT_SECRET",
        "roles": ["ADMIN", "USER"]
      },
      "features": {
        "enable_soft_delete": true,
        "enable_audit_log": true,
        "enable_rate_limit": {
          "enabled": true,
          "requests_per_minute": 120
        }
      }
    }
  }
}
```

### Entity Definition

```json
{
  "name": "Product",
  "table_name": "products",
  "description": "Product catalog",
  "audit": true,
  "soft_delete": true,
  "permissions": {
    "create": ["ADMIN"],
    "read": ["ADMIN", "USER"],
    "update": ["ADMIN"],
    "delete": ["ADMIN"]
  },
  "fields": [...],
  "relationships": [...],
  "endpoints": {...}
}
```

### Field Types

Supported field types:

- **string**: Variable-length text
- **text**: Long text
- **int**: Integer
- **bigint**: Large integer
- **uuid**: UUID
- **boolean**: True/False
- **decimal**: Decimal number
- **float**: Floating point
- **date**: Date only
- **datetime**: Date and time
- **time**: Time only
- **jsonb**: JSON data
- **uuid[]**: Array of UUIDs
- **string[]**: Array of strings

### Field Definition

```json
{
  "name": "email",
  "type": "string",
  "format": "email",
  "max_length": 254,
  "unique": true,
  "nullable": false,
  "description": "User email address",
  "validation": {
    "pattern": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
  },
  "frontend": {
    "form_control": "input",
    "form_type": "email",
    "validators": ["required", "email"],
    "visible_in_list": true
  }
}
```

### Relationships

#### Many-to-One (Foreign Key)

```json
{
  "type": "many-to-one",
  "target": "Category",
  "local_field": "category_id",
  "remote_field": "id",
  "name": "category"
}
```

#### One-to-Many (Reverse FK)

```json
{
  "type": "one-to-many",
  "target": "OrderItem",
  "local_field": "id",
  "remote_field": "order_id",
  "name": "items",
  "cascade": "all, delete-orphan"
}
```

#### Many-to-Many (Join Table)

```json
{
  "type": "many-to-many",
  "target": "Tag",
  "via": "ProductTag",
  "name": "tags"
}
```

#### One-to-One

```json
{
  "type": "one-to-one",
  "target": "UserProfile",
  "local_field": "profile_id",
  "remote_field": "id",
  "name": "profile"
}
```

#### Self-Referencing

```json
{
  "type": "self-referencing",
  "target": "Category",
  "local_field": "parent_id",
  "remote_field": "id",
  "name": "parent"
}
```

### Endpoints Configuration

```json
{
  "base_path": "/api/products",
  "crud": true,
  "search": {
    "enabled": true,
    "fields": ["name", "description", "sku"]
  },
  "bulk": {
    "bulk_create": true,
    "bulk_update": true,
    "bulk_delete": true
  },
  "extra": {
    "activate": {
      "method": "POST",
      "path": "/api/products/{id}/activate",
      "auth_required": true
    }
  }
}
```

## Programmatic Usage

### Python API

```python
from pathlib import Path
from api_forge.analyzer_factory import AnalyzerFactory
from api_forge.generators.fastapi_generator import FastAPIGenerator

async def generate_app():
    # Create analyzer
    analyzer = AnalyzerFactory.create(
        source=Path("metadata.json"),
        ai_config=ai_config  # Optional
    )
    
    async with analyzer:
        # Analyze all entities
        analyses = await analyzer.analyze_all(use_ai=True)
        
        # Get generation config
        config = analyzer.get_generation_config()
        
        # Generate code
        generator = FastAPIGenerator(
            output_dir=Path("./generated"),
            config=config
        )
        
        await generator.generate_all(analyses)

# Run
import asyncio
asyncio.run(generate_app())
```

### Load and Validate Only

```python
from api_forge.json_metadata.loader import JSONMetadataLoader

loader = JSONMetadataLoader()
metadata = loader.load_from_file(Path("metadata.json"))

# Validate relationships
errors = loader.validate_relationships()
if errors:
    for error in errors:
        print(f"Error: {error}")

# Validate foreign keys
fk_errors = loader.validate_foreign_keys()
if fk_errors:
    for error in fk_errors:
        print(f"FK Error: {error}")

# Get summary
summary = loader.get_summary()
print(f"Entities: {summary['total_entities']}")
```

### Convert to Internal Models

```python
from api_forge.json_metadata.converter import JSONToEntityConverter

converter = JSONToEntityConverter()
analyses = converter.convert_metadata(metadata)

# Access entities
for name, analysis in analyses.items():
    entity = analysis.entity
    print(f"{name}: {len(entity.properties)} fields")
```

## AI Enhancement

Enable AI-powered analysis for better code generation:

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key"

# Generate with AI
api-forge json generate metadata.json --ai
```

AI provides:
- **Smart field analysis**: Identifies unique, indexed, and immutable fields
- **Business rule detection**: Suggests validation rules and constraints
- **Security recommendations**: Identifies sensitive fields and access patterns
- **Relationship optimization**: Suggests eager/lazy loading strategies

## Advanced Features

### Composite Primary Keys

```json
{
  "name": "ProductSupplier",
  "composite_primary_key": ["product_id", "supplier_id"],
  "fields": [
    {
      "name": "product_id",
      "type": "uuid",
      "foreign_key": {
        "references": "Product.id",
        "on_delete": "CASCADE"
      }
    },
    {
      "name": "supplier_id",
      "type": "uuid",
      "foreign_key": {
        "references": "Supplier.id",
        "on_delete": "CASCADE"
      }
    }
  ]
}
```

### Custom Indexes

```json
{
  "indexes": [
    {
      "fields": ["sku"],
      "unique": true
    },
    {
      "fields": ["name", "category_id"],
      "unique": false
    }
  ]
}
```

### Enum Fields

```json
{
  "name": "status",
  "type": "string",
  "enum": ["draft", "published", "archived"],
  "default": "draft"
}
```

### Seed Data

```json
{
  "seed": [
    {
      "name": "Admin",
      "email": "admin@example.com",
      "role": "ADMIN"
    }
  ]
}
```

## Examples

See the full InventoryERP example in the provided metadata file for a complete, production-ready application with:

- User authentication & authorization
- Product catalog with categories
- Inventory management
- Order processing
- Invoice generation
- File attachments
- Audit logging
- Multi-language support

## Best Practices

1. **Use descriptive names**: Entity and field names should be clear and self-documenting
2. **Set proper constraints**: Use nullable, unique, and validation rules appropriately
3. **Define relationships carefully**: Ensure foreign key references are correct
4. **Enable auditing**: Use audit and soft_delete for critical entities
5. **Configure permissions**: Set role-based permissions for sensitive operations
6. **Validate early**: Use `validate` command before generating
7. **Use AI enhancement**: Enable AI for better field analysis and recommendations
8. **Version your metadata**: Keep metadata files in version control

## Troubleshooting

### Validation Errors

If validation fails, check:
- JSON syntax is correct
- All required fields are present
- Entity names in relationships exist
- Foreign key references are valid

### Generation Fails

Common issues:
- Output directory already exists (use `--force`)
- Invalid field types
- Circular relationship dependencies
- Missing required configuration

### AI Enhancement Issues

If AI enhancement fails:
- Check ANTHROPIC_API_KEY is set
- Ensure API key is valid
- Generation continues without AI insights

## Migration from Schema.org

To migrate from Schema.org generation:

1. Export your Schema.org entities to JSON
2. Add application-specific configuration
3. Define custom fields and relationships
4. Configure endpoints and permissions
5. Test with `validate` and `--dry-run`
6. Generate and compare outputs

## Support

For issues or questions:
- Check documentation
- Use `--help` for command options
- Review example metadata file
- Enable verbose logging for debugging