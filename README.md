# API Forge

🔨 Enterprise-grade FastAPI application generator from Schema.org definitions with AI enhancement.

## Installation
```bash
# Navigate to the API Forge directory
cd C:\api-forge

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# **Expected Output:**

Successfully installed api-forge

#Verify Installation:
api-forge --version

api-forge info
```


## Overview

API Forge automatically generates production-ready FastAPI applications with:
- **Complete CRUD operations** with async database support
- **AI-enhanced code generation** for business logic and tests
- **JWT authentication & RBAC** authorization
- **Comprehensive test suites** with realistic scenarios
- **Docker & Kubernetes** deployment configs
- **CI/CD pipelines** ready to use
- **Type-safe validation** with Pydantic
- **Production-ready** error handling and middleware

## Quick Start

### Installation
```bash
pip install -e .
```

### Create a New Project
```bash
api-forge init project my-api --path ./projects
cd projects/my-api
```

### Generate Authentication System
```bash
api-forge generate auth
```

### Generate Entities
```bash
# With AI enhancement (recommended)
export ANTHROPIC_API_KEY=your-api-key
api-forge generate entity Person

# Without AI
api-forge generate entity Product --no-ai

# Batch generation
api-forge generate batch Person Organization Product
```

### Setup Database
```bash
# Create migration
alembic revision --autogenerate -m "Initial setup"
alembic upgrade head
```

### Run Development Server
```bash
api-forge serve dev
# or
uvicorn my_api.main:app --reload
```

### Visit API Documentation

http://localhost:8000/api/v1/docs

## Features

### 🤖 AI-Enhanced Generation

When AI is enabled, API Forge uses Claude to:
- Analyze entities and suggest smart field configurations
- Identify required vs optional fields
- Suggest unique constraints and indexes
- Generate business rules and validations
- Create comprehensive test scenarios
- Add security insights

### 🔐 Complete Authentication

- User, Role, Permission models
- JWT access and refresh tokens
- Password hashing with bcrypt
- OAuth2 password flow
- Role-based access control (RBAC)
- Permission decorators

### 🛡️ Production-Ready Security

- Rate limiting per client
- Request correlation IDs for tracing
- Comprehensive logging
- Standardized error responses
- Input validation
- Audit logging ready

### 📊 Generated Per Entity

From a single command:
```bash
api-forge generate entity Product
```

You get:
- SQLAlchemy model with relationships
- Pydantic schemas (Create, Update, Response, List)
- Repository with custom queries
- Service layer with business logic hooks
- FastAPI router with full CRUD
- Test suite with factories
- All properly typed and documented

### 🧪 Comprehensive Testing

- Auto-generated test factories
- E2E API tests
- Unit tests for services
- Integration tests for database
- AI-generated edge case tests

## Project Structure
```
my-api/
├── my_api/                # Main application package
│   ├── api/              # API routes
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── router.py
│   ├── core/             # Core utilities
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── dependencies.py
│   │   └── exceptions.py
│   ├── db/               # Database configuration
│   ├── middleware/       # Middleware components
│   ├── models/           # SQLAlchemy models
│   ├── repositories/     # Data access layer
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── utils/            # Utility functions
├── alembic/              # Database migrations
├── tests/                # Test suite
│   ├── factories/        # Test data factories
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docker-compose.yml
├── Dockerfile
└── api-forge.yaml        # Project configuration
```

## Configuration

### Environment Variables
```env
# Required
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://localhost:6379/0

# Optional - AI Enhancement
ANTHROPIC_API_KEY=your-api-key

# Optional - OAuth
OAUTH2_GOOGLE_CLIENT_ID=...
OAUTH2_GOOGLE_CLIENT_SECRET=...
```

### Project Configuration (`api-forge.yaml`)
```yaml
project:
  name: "My API"
  version: "1.0.0"

generation:
  ai_enabled: true
  ai_provider: anthropic
  ai_model: claude-sonnet-4
  use_soft_delete: true
  enable_rbac: true

testing:
  coverage_threshold: 80
  generate_tests: true
  generate_factories: true
```

## CLI Commands

### Project Initialization
```bash
api-forge init <name> [--path PATH] [--template TEMPLATE]
```

### Code Generation
```bash
# Generate single entity
api-forge generate entity <Name> [--force] [--no-ai] [--no-tests]

# Generate multiple entities
api-forge generate batch Person Organization Product

# Generate authentication
api-forge generate auth
```

### Database Migrations
```bash
api-forge migrate create "description"
api-forge migrate apply
api-forge migrate rollback [--steps N]
```

### Development Server
```bash
api-forge serve dev [--port PORT] [--host HOST]
```

### Testing
```bash
api-forge test run [--coverage] [--markers MARKERS]
```

## Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis 7+ (optional, for caching and rate limiting)
- Docker (optional)

## AI Features

API Forge uses Claude (Anthropic) for AI-enhanced generation:

### Entity Analysis
- Smart field detection (required, unique, indexed)
- Business rule suggestions
- Security considerations
- Validation recommendations

### Code Generation
- Business logic methods
- Complex validations
- Custom queries

### Test Generation
- Comprehensive test scenarios
- Edge case coverage
- Realistic test data

To enable AI features:
```bash
export ANTHROPIC_API_KEY=your-api-key
```

## Examples

### Generate a Blog API
```bash
# Initialize project
api-forge init blog-api
cd blog-api

# Generate authentication
api-forge generate auth

# Generate entities
api-forge generate entity Person
api-forge generate entity BlogPosting
api-forge generate entity Comment

# Setup database
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

# Run server
api-forge serve dev
```

### Generate E-commerce API
```bash
api-forge init store-api
cd store-api

api-forge generate auth
api-forge generate batch Product Organization Person Order

alembic upgrade head
api-forge serve dev
```

## Development

### Run Tests
```bash
pytest
```

### Code Quality
```bash
black api_forge tests
isort api_forge tests
ruff check api_forge tests
mypy api_forge
```

## Documentation

- [Architecture](docs/architecture.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)
- [API Reference](docs/api.md)

## License

MIT License

## Credits

Built with:
- FastAPI
- SQLAlchemy
- Pydantic
- Anthropic Claude
- Rich
- Typer

## Status

✅ **Production Ready** - All core features complete and tested

### Completed Phases

- ✅ Phase 1: Foundation (CLI, project templates)
- ✅ Phase 2: Code Generation (models, schemas, services, routers)
- ✅ Phase 3: API Layer (auth, middleware, error handling)
- ✅ Phase 4: AI Integration (enhanced generation, test creation)

### Feature Completeness

- ✅ Project initialization
- ✅ Entity generation from Schema.org
- ✅ Complete CRUD APIs
- ✅ Authentication & RBAC
- ✅ Middleware layer
- ✅ Error handling
- ✅ AI-enhanced generation
- ✅ Test generation
- ✅ Docker support
- ✅ Database migrations

## Support

- GitHub Issues: https://github.com/apiforge/api-forge/issues
- Documentation: https://docs.apiforge.dev
