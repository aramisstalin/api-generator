"""
Project template generator.

Creates complete project structure with all necessary files and directories
for a new API Forge project.
"""

from pathlib import Path
from api_forge.core.config import ProjectConfig


class ProjectTemplate:
    """
    Generates complete project structure from template.

    Creates all necessary directories, configuration files, and boilerplate code
    for a new API Forge project.
    """

    def __init__(self, project_path: Path, config: ProjectConfig):
        self.project_path = project_path
        self.config = config
        self.app_name = config.name.replace("-", "_")

    def create_structure(self) -> None:
        """Create complete directory structure."""

        # Create base directory
        self.project_path.mkdir(parents=True, exist_ok=True)

        # Main application directories
        directories = [
            # Application package
            f"{self.app_name}",
            f"{self.app_name}/api",
            f"{self.app_name}/api/v1",
            f"{self.app_name}/api/v1/endpoints",
            f"{self.app_name}/core",
            f"{self.app_name}/core/endpoints",
            f"{self.app_name}/core/helpers",
            f"{self.app_name}/core/middleware",
            f"{self.app_name}/core/models",
            f"{self.app_name}/core/repositories",
            f"{self.app_name}/core/schemas",
            f"{self.app_name}/core/services",
            f"{self.app_name}/db",
            f"{self.app_name}/templates",

            # Database migrations
            "alembic",
            "alembic/versions",

            # Tests
            "tests",
            "tests/factories",
            "tests/unit",
            "tests/integration",
            "tests/e2e",

            # Documentation
            "docs",

            # Scripts
            "scripts",

            # Kubernetes configs (if enabled)
            "k8s" if self.config.deployment.kubernetes else None,

            # Nginx configs (if enabled)
            "nginx" if self.config.deployment.dockerfile else None,
        ]

        # Create all directories
        for directory in directories:
            if directory:  # Skip None entries
                dir_path = self.project_path / directory
                dir_path.mkdir(parents=True, exist_ok=True)

                # Create __init__.py for Python packages
                if directory.startswith(self.app_name) or directory.startswith("tests"):
                    init_file = dir_path / "__init__.py"
                    if not init_file.exists():
                        init_file.write_text('"""\n"""\n', encoding="utf-8")

    def generate_core_files(self, skip_docker: bool = False) -> None:
        """Generate core project files."""

        # README.md
        self._create_readme()

        # .gitignore
        self._create_gitignore()

        # requirements.txt
        self._create_requirements()

        # requirements-dev.txt
        self._create_requirements_dev()

        # .env.example
        self._create_env_example()

        # main.py (FastAPI app)
        self._create_main_app()

        # Docker files
        if not skip_docker:
            self._create_dockerfile()
            self._create_docker_compose()

        # Alembic configuration
        self._create_alembic_ini()
        self._create_alembic_env()

        # pytest configuration
        self._create_pytest_ini()

        # pyproject.toml
        self._create_pyproject_toml()

    def generate_config_files(self) -> None:
        """Generate configuration files."""

        # Save API Forge configuration
        config_path = self.project_path / "api-forge.yaml"
        self.config.save_to_file(config_path)

        # Core configuration module
        self._create_core_config()
        self._create_preflight_middleware()

        # Database session module
        self._create_db_session()

        # API router
        self._create_api_router()

        # Pytest conftest.py
        self._create_conftest()

    def generate_common_files(self) -> None:
        """Generate common project files and basic classes that will be used by others in the project."""

        # create endpoints folder and related files
        self._create_endpoints()

        # create helpers folder and related files
        self._create_helpers()

        # create models folder and related files
        self._create_models()

        # create repositories folder and related files
        self._create_repositories()

        # create schemas folder and related files
        self._create_schemas()

        # create services folders and related files
        self._create_services()

    def _create_readme(self) -> None:
        """Create README.md file."""
        content = f"""## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+ (optional, for caching and rate limiting)

### Setup

1. Clone the repository and navigate to the project:
```bash
cd {self.config.name}
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\\venv\\Scripts\\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials and settings
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start the development server:
```bash
uvicorn {self.app_name}.main:app --reload
```

7. Access the API documentation:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Development

### Generate a new entity
```bash
api-forge generate entity Organization
```

### Create a database migration
```bash
alembic revision --autogenerate -m "Add organization table"
alembic upgrade head
```

### Run tests
```bash
pytest
```

### Run with Docker
```bash
docker-compose up -d
```

## Project Structure
        {self.config.name}/
        ├── {self.app_name}/          # Main application package
        │   ├── api/                  # API routes
        │   ├── core/                 # Core utilities
        │   ├── db/                   # Database configuration
        │   ├── models/               # SQLAlchemy models
        │   ├── repositories/         # Data access layer
        │   ├── schemas/              # Pydantic schemas
        │   ├── services/             # Business logic
        │   └── utils/                # Utility functions
        ├── alembic/                  # Database migrations
        ├── tests/                    # Test suite
        ├── docs/                     # Documentation
        └── scripts/                  # Utility scripts

## API Documentation

The API is automatically documented using OpenAPI (Swagger) specification.

- Interactive API docs: http://localhost:8000/api/v1/docs
- Alternative docs: http://localhost:8000/api/v1/redoc
- OpenAPI schema: http://localhost:8000/api/v1/openapi.json

## Generated with API Forge

This project was generated using [API Forge](https://github.com/apiforge/api-forge) - 
an enterprise-grade FastAPI application generator from Schema.org definitions.

## License

MIT
"""
        (self.project_path / "README.md").write_text(content, encoding="utf-8")

    def _create_gitignore(self) -> None:
        """Create .gitignore file."""
        content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover

# Environment
.env
.env.local

# Database
*.db
*.sqlite3

# Logs
*.log
logs/

# Alembic
alembic/versions/*.pyc

# OS
Thumbs.db
"""
        (self.project_path / ".gitignore").write_text(content, encoding="utf-8")

    def _create_requirements(self) -> None:
        """Create requirements.txt file."""
        content = """# Core Framework
fastapi==0.121.3
uvicorn[standard]==0.38.0
pydantic==2.12.4
pydantic-settings==2.12.0

# Database
sqlalchemy==2.0.44
asyncpg==0.30.0
alembic==1.17.2
psycopg2-binary==2.9.11

# Security
python-jose[cryptography]==3.5.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.20
cryptography==46.0.3

# HTTP Client
httpx==0.28.1

# Caching
redis==7.1.0

# CLI
typer[all]==0.20.0
rich==14.2.0

# Templates
jinja2==3.1.6

# Configuration
pyyaml==6.0.3

# AI Integration
anthropic==0.74.0

# Async Support
aiofiles==25.1.0

# Utilities
python-dotenv==1.0.0

# Email
aiosmtplib==5.0.0

slowapi==0.1.9
"""
        (self.project_path / "requirements.txt").write_text(content, encoding="utf-8")

    def _create_requirements_dev(self) -> None:
        """Create requirements-dev.txt file."""
        content = """-r requirements.txt

# Testing
pytest==9.0.1
pytest-asyncio==1.3.0
pytest-cov==7.0.0
faker==38.2.0

# Code Quality
black==25.11.0
isort==7.0.0
ruff==0.14.5
mypy==1.18.2

# Security
bandit==1.9.1
safety==3.7.0

# Type Stubs
types-pyyaml==6.0.12.20250915
types-redis==4.6.0.20241004
"""
        (self.project_path / "requirements-dev.txt").write_text(content, encoding="utf-8")

    def _create_env_example(self) -> None:
        """Create .env.example file."""
        content = f"""# Application
PROJECT_NAME="{self.config.name}"
VERSION="{self.config.version}"
ENVIRONMENT=development

# API
API_STR=/api/v1

# Security
SECRET_KEY=change-this-to-a-secure-random-string-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_SECONDS=900  # 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS=7  # 7 days
RATE_LIMIT_PER_MINUTE=10  # 10 requests per minute

# Email
EMAILS_FROM_EMAIL=from.company.email@example.com
EMAILS_FROM_NAME=Your Company Name
SMTP_HOST=smtp.example.com
SMTP_PORT=587

# Database
POSTGRES_SERVER={self.config.database.host}
POSTGRES_USER={self.config.database.user or "postgres"}
POSTGRES_PASSWORD=change-this-password
POSTGRES_DB={self.config.database.name}
DATABASE_URL=postgresql+asyncpg://{self.config.database.user or "postgres"}:password@{self.config.database.host}:{self.config.database.port}/{self.config.database.name}

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:4200  # comma-separated list

# Logging
LOG_LEVEL=DEBUG
"""
        (self.project_path / ".env.example").write_text(content, encoding="utf-8")

    def _create_main_app(self) -> None:
        """Create main FastAPI application file."""
        content = f'''"""
Main FastAPI application for {self.config.name}.

This module initializes the FastAPI application with all necessary
configurations, middleware, and route handlers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from {self.app_name}.core.config import settings
from {self.app_name}.core.middleware.preflight import CORSPreflightMiddleware
from {self.app_name}.api.v1.router import api_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import logging

# Configure module logger
logger = logging.getLogger(__name__)

# Configure rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("🚀 Application starting up...")
    yield
    # Shutdown
    print("👋 Application shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{{settings.API_STR}}/openapi.json",
    docs_url=f"{{settings.API_STR}}/docs",
    redoc_url=f"{{settings.API_STR}}/redoc",
    lifespan=lifespan,
)

# Add rate limiter state to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(CORSPreflightMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Type"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include API router
app.include_router(api_router, prefix=settings.API_STR)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {{"status": "healthy", "service": settings.PROJECT_NAME}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        main_path = self.project_path / self.app_name / "main.py"
        main_path.write_text(content, encoding="utf-8")

    def _create_preflight_middleware(self) -> None:
        """Create preflight middleware configuration file."""
        content = f'''"""
Middleware to handle OPTIONS requests before they reach route handlers.
This prevents 405 errors on preflight requests.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class CORSPreflightMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return JSONResponse(
                content={{}},
                status_code=200,
                headers={{
                    "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Origin, User-Agent",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Max-Age": "600",
                }}
            )
        
        response = await call_next(request)
        return response'''

        main_path = self.project_path / self.app_name / "core" / "middleware" / "preflight.py"
        main_path.write_text(content, encoding="utf-8")

    def _create_dockerfile(self) -> None:
        """Create Dockerfile."""
        content = f"""# Multi-stage build for production

FROM python:3.11-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

RUN useradd -m -u 1000 appuser && \\
    mkdir -p /app && \\
    chown -R appuser:appuser /app

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

CMD ["uvicorn", "{self.app_name}.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        (self.project_path / "Dockerfile").write_text(content, encoding="utf-8")

    def _create_docker_compose(self) -> None:
        """Create docker-compose.yml."""
        content = f"""version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: {self.config.name}_db
    environment:
      POSTGRES_USER: ${{POSTGRES_USER}}
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD}}
      POSTGRES_DB: ${{POSTGRES_DB}}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${{POSTGRES_USER}}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: {self.config.name}_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: {self.config.name}_app
    environment:
      DATABASE_URL: postgresql+asyncpg://${{POSTGRES_USER}}:${{POSTGRES_PASSWORD}}@db:5432/${{POSTGRES_DB}}
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${{SECRET_KEY}}
      ENVIRONMENT: development
    ports:
      - "8000:8000"
    volumes:
      - ./{self.app_name}:/app/{self.app_name}
      - ./alembic:/app/alembic
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn {self.app_name}.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  postgres_data:
  redis_data:
"""
        (self.project_path / "docker-compose.yml").write_text(content, encoding="utf-8")

    def _create_alembic_ini(self) -> None:
        """Create alembic.ini configuration."""
        content = f"""# Alembic configuration file

[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://postgres:password@localhost:5432/{self.config.database.name}

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        (self.project_path / "alembic.ini").write_text(content, encoding="utf-8")

    def _create_alembic_env(self) -> None:
        """Create alembic/env.py."""
        content = f"""from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from {self.app_name}.core.config import settings
from {self.app_name}.db.base import Base

config = context.config

# Override sqlalchemy.url with our DATABASE_URL
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={{"paramstyle": "named"}},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {{}}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
        env_path = self.project_path / "alembic" / "env.py"
        env_path.write_text(content, encoding="utf-8")

    def _create_pytest_ini(self) -> None:
        """Create pytest.ini configuration."""
        content = f"""[pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    --strict-markers
    --cov={self.app_name}
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -v
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Tests that take a long time
"""
        (self.project_path / "pytest.ini").write_text(content, encoding="utf-8")

    def _create_pyproject_toml(self) -> None:
        """Create pyproject.toml configuration."""
        content = f"""[tool.black]
line-length = 100
target-version = ['py311']
include = '\\.pyi?$'

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.ruff]
line-length = 100
target-version = "py311"
"""
        (self.project_path / "pyproject.toml").write_text(content, encoding="utf-8")

    def _create_core_config(self) -> None:
        """Create core configuration module."""
        content = f'''"""
Application configuration.

Loads settings from environment variables using Pydantic Settings.
"""

import os
from typing import List
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
        from_attributes=True,
    )

    # Project metadata
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "{self.config.name}")
    VERSION: str = os.getenv("VERSION", "{self.config.version}")
    API_STR: str = os.getenv("API_STR", "/api/v1")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # --- Security & JWT Configuration ---
    # To generate a good secret key: openssl rand -hex 32
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_SECONDS: int = os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", 900)  # 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)  # 7 days
    RATE_LIMIT_PER_MINUTE: int = os.getenv("RATE_LIMIT_PER_MINUTE", 10)  # 10 requests per minute
    
    # --- Email Configuration ---
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME")
    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = os.getenv("SMTP_PORT")

    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", ["http://localhost:4200", "http://localhost:3000"]) # comma-separated list with angular and react dev servers as default, adjust as needed

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "{self.config.database.host}")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "{self.config.database.name}")
    DATABASE_URL: PostgresDsn | None = None
    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/test_db")

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v, info):
        if isinstance(v, str) and v:
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=info.data.get("POSTGRES_USER"),
            password=info.data.get("POSTGRES_PASSWORD"),
            host=info.data.get("POSTGRES_SERVER"),
            path=f"{{info.data.get('POSTGRES_DB') or ''}}",
        )

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
'''
        config_path = self.project_path / self.app_name / "core" / "config.py"
        config_path.write_text(content, encoding="utf-8")

    def _create_db_session(self) -> None:
        """Create database session module."""
        content = f'''"""
Database session management.

Provides async database session for dependency injection.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)

from {self.app_name}.core.config import settings

# Create async engine
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.ENVIRONMENT == "development",
    future=True,
    pool_pre_ping=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
'''
        session_path = self.project_path / self.app_name / "db" / "session.py"
        session_path.write_text(content, encoding="utf-8")

    def _create_base_model(self) -> None:
        """Create base SQLAlchemy model."""
        content = f'''"""
Base SQLAlchemy models and mixins.

Provides base model class with common fields and behaviors.
"""

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class BaseModel(Base, TimestampMixin):
    """Base model with common fields."""

    __abstract__ = True

    id: Mapped[str] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    @declared_attr
    def __tablename__(cls) -> str:
        """Auto-generate table name from class name."""
        return cls.__name__.lower() + "s"

    def dict(self):
        """Convert model to dictionary."""
        return {{
            column.name: getattr(self, column.name)
            for column in self.__table__.columns.items()
        }}
'''
        base_path = self.project_path / self.app_name / "core" / "models" / "base_model.py"
        base_path.write_text(content, encoding="utf-8")

    def _create_api_router(self) -> None:
        """Create API v1 router."""
        content = f'''"""
API v1 router.

Aggregates all API endpoints for version 1.
"""

from fastapi import APIRouter

api_router = APIRouter()

# Import and include endpoint routers here as they are generated
# Example:
# from {self.app_name}.api.v1.endpoints import users
# api_router.include_router(users.router, prefix="/users", tags=["users"])


@api_router.get("/")
async def root():
    """API root endpoint."""
    return {{
        "message": "Welcome to {{settings.PROJECT_NAME}} API",
        "version": "1.0.0",
        "docs": "/api/v1/docs"
    }}
'''
        router_path = self.project_path / self.app_name / "api" / "v1" / "router.py"
        router_path.write_text(content, encoding="utf-8")

    def _create_conftest(self) -> None:
        """Create pytest conftest.py."""
        content = f'''"""
Pytest configuration and fixtures.

Provides shared fixtures for testing.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.pool import NullPool

from {self.app_name}.main import app
from {self.app_name}.core.config import settings
from {self.app_name}.db.base import Base
from {self.app_name}.db.session import get_db

# Test database URL
TEST_DATABASE_URL = str(settings.TEST_DATABASE_URL)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create clean database for each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with overridden database dependency."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
'''
        conftest_path = self.project_path / "tests" / "conftest.py"
        conftest_path.write_text(content, encoding="utf-8")

    def _create_helpers(self) -> None:
        """
        Create helpers package and related files
        """

        # Create __init__.py
        self._create_helpers_init()

        # Create filter helper
        self._create_filter_helper()

        # Create paginator helper
        self._create_paginator_helper()

        # Create rate limiter helper
        self._create_rate_limiter_helper()

        # Create user timezone helper
        self._create_user_timezone_helper()

    def _create_helpers_init(self) -> None:
        """Create __init__.py in helpers folder."""
        content = f'''"""
Helpers package to provide utility functions and classes.
"""

from {self.app_name}.core.helpers.filter_helper import apply_filters_and_sorting
from {self.app_name}.core.helpers.paginator_helper import paginate
from {self.app_name}.core.helpers.rate_limiter_helper import RateLimiter, rate_limiter, check_rate_limit
from {self.app_name}.core.helpers.user_timezone_helper import get_user_timezone

__all__ = [
    "apply_filters_and_sorting",
    "paginate",
    "RateLimiter",
    "rate_limiter",
    "check_rate_limit",
    "get_user_timezone",
]'''
        helpers_init_path = self.project_path / self.app_name / "core" / "helpers" / "__init__.py"
        helpers_init_path.write_text(content, encoding="utf-8")

    def _create_filter_helper(self) -> None:
        """Create filter_helper.py in helpers folder."""
        content = f'''"""
Provides a filter function to apply filter and sorting to a query.
(Intended to be used in repositories classes)
"""

from typing import Any, Callable
from sqlalchemy.sql import operators
from sqlalchemy.orm import aliased
from sqlalchemy import and_, or_, asc, desc


OPERATOR_MAPPING: dict[str, Callable[[Any, Any], Any]] = {{
    "eq": operators.eq,
    "ne": operators.ne,
    "lt": operators.lt,
    "lte": operators.le,
    "gt": operators.gt,
    "gte": operators.ge,
    "in": lambda field, value: field.in_(value),
    "not_in": lambda field, value: ~field.in_(value),
    "contains": lambda field, value: field.contains(value),
    "icontains": lambda field, value: field.ilike(f"%{{value}}%"),
    "startswith": lambda field, value: field.startswith(value),
    "istartswith": lambda field, value: field.ilike(f"{{value}}%"),
    "endswith": lambda field, value: field.endswith(value),
    "iendswith": lambda field, value: field.ilike(f"%{{value}}"),
    "isnull": lambda field, value: field.is_(None) if value else field.isnot(None),
    "exact": operators.eq,  # alias for clarity
}}


def apply_filters_and_sorting(query, model, filters: dict, sort: list[str] = None, joins: dict = None, logic_operator: str = "or"):
    joins = joins or {{}}
    conditions = []
    logic_fn = and_ if logic_operator.lower() == "and" else or_

    # FILTERS
    for key, value in filters.items():
        parts = key.split("__")
        field_path = parts[0]
        operator_key = parts[1] if len(parts) > 1 else "eq"

        operator_func = OPERATOR_MAPPING.get(operator_key)
        if not operator_func:
            raise ValueError(f"Unsupported filter operator: {{operator_key}}")

        if "." in field_path:
            rel_name, field_name = field_path.split(".", 1)
            relationship = getattr(model, rel_name)

            if rel_name not in joins:
                related_model = relationship.property.mapper.class_
                alias = aliased(related_model)
                joins[rel_name] = alias
                query = query.join(alias, relationship)
            else:
                alias = joins[rel_name]

            column = getattr(alias, field_name)
        else:
            column = getattr(model, field_path)

        conditions.append(operator_func(column, value))

    if conditions:
        query = query.where(logic_fn(*conditions))

    # SORTING
    if sort:
        order_by = []
        for field in sort:
            direction = asc if field[-1] == "+" else desc
            field = field[:-1]

            if "." in field:
                rel_name, field_name = field.split(".", 1)
                relationship = getattr(model, rel_name)

                if rel_name not in joins:
                    related_model = relationship.property.mapper.class_
                    alias = aliased(related_model)
                    joins[rel_name] = alias
                    query = query.join(alias, relationship)
                else:
                    alias = joins[rel_name]

                column = getattr(alias, field_name)
            else:
                column = getattr(model, field)

            order_by.append(direction(column))

        if order_by:
            query = query.order_by(*order_by)

    return query, joins'''

        filter_helper_path = self.project_path / self.app_name / "core" / "helpers" / "filter_helper.py"
        filter_helper_path.write_text(content, encoding="utf-8")

    def _create_paginator_helper(self) -> None:
        """Create paginator_helper.py in helpers folder."""
        content = f'''"""
Provides a paginate function for paginate a query.
(Intended to be used in repositories classes)
"""

from sqlalchemy import select, func

async def paginate(session, query, page: int = 1, page_size: int = 20):
    # Get total count efficiently
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query) or 0

    offset = (page - 1) * page_size

    # Get paginated items
    paginated_query = query.limit(page_size).offset(offset)
    result = await session.execute(paginated_query)
    items = result.scalars().all()

    return {{
        "total": total,
        "items": items,
    }}
'''
        paginator_helper_path = self.project_path / self.app_name / "core" / "helpers" / "paginator_helper.py"
        paginator_helper_path.write_text(content, encoding="utf-8")

    def _create_rate_limiter_helper(self) -> None:
        """Create rate_limiter_helper.py in helpers folder."""
        content = f'''"""
Provides rate limiting utilities using SlowAPI.
(Intended to be used in route handlers and services)
"""

from fastapi import Request, HTTPException, status
from datetime import datetime, timezone, timedelta
from typing import Dict, List

from {self.app_name}.core.config import settings


class RateLimiter:

    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {{}}

    def is_allowed(self, client_ip: str, limit: int = settings.RATE_LIMIT_PER_MINUTE) -> bool:
        """Check if request is allowed based on rate limit."""
        now = datetime.now(timezone.utc)
        minute_ago = now - timedelta(minutes=1)

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > minute_ago
        ]

        if len(self.requests[client_ip]) >= limit:
            return False

        self.requests[client_ip].append(now)
        return True


rate_limiter = RateLimiter()


async def check_rate_limit(request: Request):
    """Check rate limit for client IP."""
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
'''
        rate_limiter_helper_path = self.project_path / self.app_name / "core" / "helpers" / "rate_limiter_helper.py"
        rate_limiter_helper_path.write_text(content, encoding="utf-8")

    def _create_user_timezone_helper(self) -> None:
        """Create user_timezone_helper.py in helpers folder."""
        content = f'''"""
Provides utility to get user timezone.
(Intended to be used in services and route handlers)
"""

from fastapi import Header
from zoneinfo import ZoneInfo

def get_user_timezone(x_timezone: str = Header(default="UTC")) -> ZoneInfo:
    try:
        return ZoneInfo(x_timezone)
    except Exception:
        return ZoneInfo("UTC")'''

        user_timezone_helper_path = self.project_path / self.app_name / "core" / "helpers" / "user_timezone_helper.py"
        user_timezone_helper_path.write_text(content, encoding="utf-8")

    def _create_models(self) -> None:
        """
        Create models package and related files
        """

        # Create __init__.py
        self._create_models_init()

        # Base model
        self._create_base_model()

        # Base model
        self._create_file_model()

        # Base model
        self._create_exceptions_model()

    def _create_models_init(self) -> None:
        """Create __init__.py in models folder."""
        content = f'''"""
Models package to provide core model classes.
"""

from {self.app_name}.core.models.base_model import BaseModel, SoftDeleteMixin, TimestampMixin
from {self.app_name}.core.models.exception_model import ExternalAPIError, CircuitBreakerError, RateLimitError
from {self.app_name}.core.models.file_model import File

__all__ = [
    "BaseModel",
    "SoftDeleteMixin",
    "TimestampMixin",
    "ExternalAPIError",
    "CircuitBreakerError",
    "RateLimitError",
    "File",
]'''
        models_init_path = self.project_path / self.app_name / "core" / "models" / "__init__.py"
        models_init_path.write_text(content, encoding="utf-8")

    def _create_file_model(self) -> None:
        """Create file_model.py in models folder."""
        content = f'''"""
Provide file model file to map a database table to control uploaded static files to a path.
"""
    
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from . import BaseModel


class File(BaseModel):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4, unique=True, nullable=False)
    filename: Mapped[str]
    url: Mapped[str]
    content_type: Mapped[str]
    size: Mapped[int]
    path: Mapped[str]
'''
        file_model_path = self.project_path / self.app_name / "core" / "models" / "file_model.py"
        file_model_path.write_text(content, encoding="utf-8")

    def _create_exceptions_model(self) -> None:
        """Create exception_model.py in models folder."""
        content = f'''"""
Provide exception models to be used across the application.
"""

class ExternalAPIError(Exception):
    """Custom exception for external API errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class CircuitBreakerError(ExternalAPIError):
    """Exception raised when circuit breaker is open."""
    pass


class RateLimitError(ExternalAPIError):
    """Exception raised when rate limit is exceeded."""
    pass
'''
        exception_model_path = self.project_path / self.app_name / "core" / "models" / "exception_model.py"
        exception_model_path.write_text(content, encoding="utf-8")

    def _create_repositories(self) -> None:
        """
        Create repositories package and related files
        """

        # Create __init__.py
        self._create_repositories_init()

        # Base model
        self._create_base_repository()

        # Base model
        self._create_file_repository()

    def _create_repositories_init(self) -> None:
        """Create __init__.py in repositories folder."""
        content = f'''"""
Repositories package to provide base repository and other base repositories classes.
"""
from .base_repository import BaseRepository
from .file_repository import FileRepository, get_file_repository

__all__ = [
    "BaseRepository",
    "FileRepository",
    "get_file_repository"
]'''

        repositories_init_path = self.project_path / self.app_name / "core" / "repositories" / "__init__.py"
        repositories_init_path.write_text(content, encoding="utf-8")

    def _create_base_repository(self) -> None:
        """Create base_repository.py in repositories folder."""
        content = f'''"""
Base repository file that provide base repository class with most commonly methods.
(This model is intended to be used by others repositories as mixin.)
"""

from {self.app_name}.core.helpers import apply_filters_and_sorting, paginate
from {self.app_name}.core.models import BaseModel
from {self.app_name}.core.schemas import BaseFilter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import TypeVar, Generic

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    def __init__(self, model: Generic[T]):
        self.model = model

    async def create(self, db: AsyncSession, item, schema=None):
        item = self.model(**item.model_dump())
        db.add(item)
        try:
            await db.commit()
            await db.refresh(item)
            if schema:
                return schema.model_validate(item)
            return item.__dict__
        except IntegrityError as e:
            await db.rollback()
            raise ValueError(f"Adicionando {{self.model.__name__}}: ocorreu um erro. {{str(e)}}")

    async def get_by_id(self, db: AsyncSession, item_id, schema=None):
        result = await db.execute(select(self.model).filter(self.model.id == item_id))
        item = result.scalars().first()
        if not item:
            return None
        if schema:
            return schema.model_validate(item)
        return item.__dict__

    async def _get_by_id_orm(self, db: AsyncSession, item_id, schema=None):
        result = await db.execute(select(self.model).filter(self.model.id == item_id))
        item = result.scalars().first()
        if not item:
            return None

        return item

    async def get_all(self, db: AsyncSession, skip: int = 0, limit: int = 20, schema=None):
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        items = result.scalars().all()
        if schema:
            return [schema.model_validate(item) for item in items]
        return [item.__dict__ for item in items]

    async def update(self, db: AsyncSession, item_data, item_id, schema=None):
        item = await self._get_by_id_orm(db, item_id)
        if item is None or not item:
            return None
        update_values = item_data.model_dump(exclude_unset=True)
        for key, value in update_values.items():
            setattr(item, key, value)
        try:
            await db.commit()
            await db.refresh(item)
            if schema:
                return schema.model_validate(item)
            return item.__dict__
        except IntegrityError:
            await db.rollback()
            raise ValueError(f'Atualizando {{self.model.__name__}}: ocorreu um erro. Verifique os dados.')

    async def delete(self, db: AsyncSession, item_id) -> bool:
        item = await self._get_by_id_orm(db, item_id)
        if not item:
            return False
        try:
            await db.delete(item)
            await db.commit()
            return True
        except IntegrityError:
            await db.rollback()
            raise ValueError(f'Excluindo {{self.model.__name__}}: ocorreu um erro. Verifique os dados.')

    async def get_filtered_items(self, db: AsyncSession, filters: BaseFilter):
        try:
            base_query = self.get_filter_query()

            filter_dict, sort_fields, logic_operator = self.build_filters_from_params(filters).values()

            query, _ = apply_filters_and_sorting(base_query, self.model, filters=filter_dict, sort=sort_fields,
                                                 logic_operator=logic_operator)

            return await paginate(db, query, page=filters.page, page_size=filters.page_size)
        except Exception as e:
            raise ValueError(f"Filtrando {{self.model.__name__}}: ocorreu um erro. Verifique os dados. {{e}}")

    def get_filter_query(self):
        return select(self.model)

    def build_filters_from_params(self, filters: BaseFilter):
        filter_dict = filters.model_dump(exclude={{"sort", "page", "page_size", "logic_operator"}}, exclude_none=True)
        sort_fields = filters.sort or []
        logic_operator = filters.logic_operator or "or"

        return {{"filter_dict": filter_dict, "sort_fields": sort_fields, "logic_operator": logic_operator}}
'''
        base_repository_path = self.project_path / self.app_name / "core" / "repositories" / "base_repository.py"
        base_repository_path.write_text(content, encoding="utf-8")

    def _create_file_repository(self) -> None:
        """Create file_repository.py in repositories folder."""
        content = f'''"""
Provide the file repository class to handle file database operations.
"""

import uuid
import os
import shutil

from functools import lru_cache
from fastapi import UploadFile
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from {self.app_name}.core.config import settings
from {self.app_name}.core.models import File
from {self.app_name}.core.repositories import BaseRepository
from {self.app_name}.core.schemas import FileResponse, FileCreate


class FileRepository(BaseRepository):
    async def upload(self, db: AsyncSession, file: UploadFile):
        # Generate a unique ID for the file
        file_id = uuid.uuid4()

        # Get file extension
        _, ext = os.path.splitext(file.filename)

        # Create a unique filename
        unique_filename = f"{{file_id}}{{ext}}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Get file size
        file_size = os.path.getsize(file_path)

        # Create file URL
        file_url = f"{{settings.BASE_URL}}/uploads/{{unique_filename}}"

        # Store file metadata
        file = FileCreate(
            id=file_id,
            filename=unique_filename,
            url=file_url,
            content_type=file.content_type,
            size=file_size,
            path=file_path
        )

        result = await self.create(db, item=file)
        return FileResponse.model_validate(result)

    async def exclude_file(self, db: AsyncSession, file):
        # Delete the file
        os.remove(file.path)
        # Remove file metadata
        return await self.delete(db, file.id)

    async def get_by_name(self, db: AsyncSession, filename):
        result = await db.execute(select(self.model).filter(self.model.filename == filename))
        return result.scalars().first()

@lru_cache()
def get_file_repository() -> FileRepository:
    return FileRepository(File)'''

        file_repository_path = self.project_path / self.app_name / "core" / "repositories" / "file_repository.py"
        file_repository_path.write_text(content, encoding="utf-8")

    def _create_endpoints(self) -> None:
        """
        Create endpoints package and related files
        """

        # Create __init__.py
        self._create_endpoints_init()

        # Endpoints for CRUD operations
        self._create_create_endpoint()
        self._create_delete_endpoint()
        self._create_filter_endpoint()
        self._create_read_endpoint()
        self._create_update_endpoint()

        # CEP endpoints
        self._create_cep_routes()

        # Email endpoints
        self._create_email_routes()

        # File endpoints
        self._create_file_routes()

    def _create_endpoints_init(self) -> None:
        """Create __init__.py in endpoints folder."""
        content = f'''"""
Endpoints package to provide base endpoints and methods.
"""

from .create_endpoint import create
from .delete_endpoint import delete
from .filter_endpoint import filter
from .read_endpoint import read
from .update_endpoint import update

from .cep_routes import router as cep_router
from .file_routes import router as file_router
from .email_routes import router as email_router

__all__ = [
    "create",
    "delete",
    "filter",
    "read",
    "update",
    "cep_router",
    "email_router",
    "file_router",
]'''

        endpoints_init_path = self.project_path / self.app_name / "core" / "endpoints" / "__init__.py"
        endpoints_init_path.write_text(content, encoding="utf-8")

    def _create_create_endpoint(self) -> None:
        """Create create_endpoint.py in endpoints folder."""
        content = f'''"""
Provide base create method to be used by endpoints.
It acts as a wrapped where the create method of the item repository class, return an ApiResponse
and manage errors by returning a successful response with the error info.
"""

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from {self.app_name}.core.schemas import ApiResponse
from {self.app_name}.core.repositories import BaseRepository
from {self.app_name}.core.models import BaseModel


async def create(db: AsyncSession, item: BaseModel, item_repository: BaseRepository, schema):
    try:
        item = await item_repository.create(db, item, schema)

        return ApiResponse(
            status_code=status.HTTP_201_CREATED,
            detail="Cadastrando item: item criado com sucesso",
            data=item
        )
    except ValueError as e:
        return ApiResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=str(e)
        )'''

        create_endpoint_path = self.project_path / self.app_name / "core" / "endpoints" / "create_endpoint.py"
        create_endpoint_path.write_text(content, encoding="utf-8")

    def _create_read_endpoint(self) -> None:
        """Create read_endpoint.py in endpoints folder."""
        content = f'''"""
Provide read item method to be used by endpoints.
It acts as a wrapped where the method of the item repository class are called, return an ApiResponse
and manage errors by returning a successful response with the error info.
"""

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from {self.app_name}.core.schemas import ApiResponse
from {self.app_name}.core.repositories import BaseRepository


async def read(item_id, db: AsyncSession, item_service: BaseRepository, schema) -> ApiResponse:
    try:
        db_item = await item_service.get_by_id(db, item_id, schema)
        if db_item is None:
            return ApiResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Recuperando item: esse item nÃ£o existe."
            )

        return ApiResponse(
            status_code=status.HTTP_200_OK,
            detail="Recuperando item: item recuperado com sucesso",
            data=db_item
        )
    except ValueError as e:
        return ApiResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=str(e)
        )'''

        read_endpoint_path = self.project_path / self.app_name / "core" / "endpoints" / "read_endpoint.py"
        read_endpoint_path.write_text(content, encoding="utf-8")

    def _create_delete_endpoint(self) -> None:
        """Create delete_endpoint.py in endpoints folder."""
        content = f'''"""
Provide delete item method to be used by endpoints.
It acts as a wrapped where the method of the item repository class are called, return an ApiResponse
and manage errors by returning a successful response with the error info.
"""

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from {self.app_name}.core.schemas import ApiResponse
from {self.app_name}.core.repositories import BaseRepository


async def delete(item_id, db: AsyncSession, item_repository: BaseRepository) -> ApiResponse:
    try:
        result = await item_repository.delete(db, item_id)

        return ApiResponse(
                status_code=status.HTTP_200_OK,
                detail="Excluir item: item exluÃ­do com sucesso"
            ) if result else ApiResponse(
                status_code=status.HTTP_417_EXPECTATION_FAILED,
                detail="Excluir item: o item nÃ£o pÃ´de ser excluÃ­do "
            )
    except ValueError as e:
        return ApiResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=str(e)
        )'''

        delete_endpoint_path = self.project_path / self.app_name / "core" / "endpoints" / "delete_endpoint.py"
        delete_endpoint_path.write_text(content, encoding="utf-8")

    def _create_update_endpoint(self) -> None:
        """Create update_endpoint.py in endpoints folder."""
        content = f'''"""
Provide update item method to be used by endpoints.
It acts as a wrapped where the method of the item repository class are called, return an ApiResponse
and manage errors by returning a successful response with the error info.
"""

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from {self.app_name}.core.schemas import ApiResponse
from {self.app_name}.core.repositories import BaseRepository


async def update(db: AsyncSession, item_id, item, item_repository: BaseRepository, schema) -> ApiResponse:
    try:
        db_item = await item_repository.get_by_id(db, item_id, schema)
        if db_item is None:
            return ApiResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Atualizando item: esse item nâo existe."
            )

        result = await item_repository.update(db, item, item_id, schema)

        return ApiResponse(
                status_code=status.HTTP_200_OK,
                detail="Atualizando item: item atualizado com sucesso",
                data=result
            )
    except ValueError as e:
        return ApiResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=str(e)
        )'''

        update_endpoint_path = self.project_path / self.app_name / "core" / "endpoints" / "update_endpoint.py"
        update_endpoint_path.write_text(content, encoding="utf-8")

    def _create_filter_endpoint(self) -> None:
        """Create filter_endpoint.py in endpoints folder."""
        content = f'''"""
Provide filter method to be used by endpoints.
It acts as a wrapped where the method of the item repository class are called, return an ApiResponse
and manage errors by returning a successful response with the error info.
"""

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from {self.app_name}.core.schemas import ApiResponse, BaseFilter
from {self.app_name}.core.repositories import BaseRepository


async def filter(filters: BaseFilter, db: AsyncSession, item_repository: BaseRepository, schema) -> ApiResponse:
    try:
        response = await item_repository.get_filtered_items(db, filters)
        total, items = response.values()

        items = [schema.model_validate(item) for item in items]  # quick serialization

        return ApiResponse(
            status_code=status.HTTP_200_OK,
            detail="Filtrar itens: itens filtrados com sucesso",
            data={{
                "total": total,
                "page": filters.page,
                "page_size": filters.page_size,
                "results": items
            }})
    except ValueError as e:
        return ApiResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=str(e)
        )'''

        filter_endpoint_path = self.project_path / self.app_name / "core" / "endpoints" / "filter_endpoint.py"
        filter_endpoint_path.write_text(content, encoding="utf-8")

    def _create_cep_routes(self) -> None:
        """Create cep_routes.py in endpoints folder."""
        content = f'''"""
Provide cep router with ready to use endpoints.
"""

from typing import Annotated
from fastapi import Depends, status, APIRouter

from {self.app_name}.core.schemas import CEPQuery, ApiResponse
from {self.app_name}.core.security import verify_api_key
from {self.app_name}.core.services import fetch_address_by_cep

prefix = "/cep"
router = APIRouter(prefix=prefix)


@router.get("", response_model=ApiResponse)
async def get_cep_address(
        query: CEPQuery,
        api_key: Annotated[str, Depends(verify_api_key)]
):
    try:
        cep = await fetch_address_by_cep(query.cep)
        return ApiResponse(
            status_code=status.HTTP_200_OK,
            data=cep
        )
    except ValueError as e:
        return ApiResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            error=str(e)
        )'''

        cep_routes_path = self.project_path / self.app_name / "core" / "endpoints" / "cep_routes.py"
        cep_routes_path.write_text(content, encoding="utf-8")

    def _create_email_routes(self) -> None:
        """Create email_routes.py in endpoints folder."""
        content = f'''"""
Provide email router with ready to use endpoints.
"""

from typing import Annotated
from fastapi import APIRouter, status, Depends

from {self.app_name}.core.schemas import ApiResponse, EmailRequest
from {self.app_name}.core.services import send_email
from {self.app_name}.core.security import verify_api_key


prefix="/email"
router = APIRouter(prefix=prefix)

@router.post("")
async def send_emails(
        email: EmailRequest,
        api_key: Annotated[str, Depends(verify_api_key)]
):
    try:
        await send_email(email.to, email.subject, email.body)

        return ApiResponse(
            status_code=status.HTTP_200_OK,
            detail="Email enviado com sucesso",
            data=""
        )
    except ValueError as e:
        return ApiResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=str(e)
        )'''

        email_routes_path = self.project_path / self.app_name / "core" / "endpoints" / "email_routes.py"
        email_routes_path.write_text(content, encoding="utf-8")

    def _create_file_routes(self) -> None:
        """Create file_routes.py in endpoints folder."""
        content = f'''"""
Provide file router with ready to use endpoints.
"""

from fastapi import APIRouter, UploadFile, status
from fastapi.params import Depends
from typing import List, Annotated
from sqlalchemy.ext.asyncio import AsyncSession

from {self.app_name}.api.v1.models import User as UserModel
from {self.app_name}.core.security import verify_api_key, get_current_active_validated_user

from {self.app_name}.core.schemas import ApiResponse, FileResponse
from {self.app_name}.core.repositories import FileRepository, get_file_repository
from {self.app_name}.db.session import get_db

prefix = "/file"
router = APIRouter(prefix=prefix)

@router.post("/upload", response_model=ApiResponse)
async def upload_file(
        file: UploadFile,
        current_user: Annotated[UserModel, Depends(get_current_active_validated_user)],
        api_key: Annotated[str, Depends(verify_api_key)],
        db: Annotated[AsyncSession, Depends(get_db)],
        file_service: Annotated[FileRepository, Depends(get_file_repository)]
):
    """
    Upload a file to the server.
    Returns a file ID and URL that can be used to access the file.
    """
    try:
        file = await file_service.upload(db, file)

        return ApiResponse(
            status_code=status.HTTP_200_OK,
            detail="Arquivo carregado com sucesso",
            data=file
        )

    except Exception as e:
        return ApiResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=f"Erro ao carregar arquivo: {{str(e)}}"
        )


@router.post("/upload-multiple", response_model=ApiResponse)
async def upload_multiple_files(
        files: List[UploadFile],
        current_user: Annotated[UserModel, Depends(get_current_active_validated_user)],
        api_key: Annotated[str, Depends(verify_api_key)]
):
    """
    Upload multiple files to the server.
    Returns a list of file IDs and URLs that can be used to access the files.
    """
    try:
        responses = []
        for file in files:
            response = await upload_file(file)
            if response.status_code == status.HTTP_200_OK:
                responses.append(response.data)
            else:
                for file_info in responses:
                    await delete_file(file_info)
                raise Exception(response.detail)
        return ApiResponse(
            status_code=status.HTTP_200_OK,
            data=responses,
            detail="Arquivos carregados com sucesso"
        )

    except Exception as e:
        return ApiResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error=f"Erro ao carregar arquivos: {{str(e)}}"
    )


@router.get("/{{file_id}}", response_model=ApiResponse)
async def get_file_info(
        file_id: str,
        current_user: Annotated[UserModel, Depends(get_current_active_validated_user)],
        api_key: Annotated[str, Depends(verify_api_key)],
        db: Annotated[AsyncSession, Depends(get_db)],
        file_service: Annotated[FileRepository, Depends(get_file_repository)]
):
    """
    Get file information by ID.
    """
    file = await file_service.get_by_id(db, item_id=file_id)
    if not file or file is None:
        return ApiResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo nÃ£o encontrado"
        )

    return ApiResponse(
        status_code=status.HTTP_200_OK,
        detail="Dados de arquivo",
        data=file
    )


@router.delete("/{{file_id}}")
async def delete_file(
        file_id: str,
        current_user: Annotated[UserModel, Depends(get_current_active_validated_user)],
        api_key: Annotated[str, Depends(verify_api_key)],
        db: Annotated[AsyncSession, Depends(get_db)],
        file_service: Annotated[FileRepository, Depends(get_file_repository)]
):
    """
    Delete a file by ID.
    """
    try:
        file = await file_service.get_by_id(db, item_id=file_id)
        if not file or file is None:
            return ApiResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                error="Arquivo nÃ£o encontrado"
            )

        await file_service.exclude_file(db, file)

        return ApiResponse(
            status_code=status.HTTP_200_OK,
            detail="Arquivo excluÃ­do com sucesso!"
        )
    except Exception as e:
        return  ApiResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error=f"Erro ao excluir arquivo: {{str(e)}}"
        )'''

        file_routes_path = self.project_path / self.app_name / "core" / "endpoints" / "file_routes.py"
        file_routes_path.write_text(content, encoding="utf-8")

    def _create_schemas(self) -> None:
        """
        Create schemas package and related files
        """

        # Create __init__.py
        self._create_schemas_init()

        # Api schemas
        self._create_api_schemas()

        # Create Base schemas
        self._create_base_schemas()

        # Create Cep schemas
        self._create_cep_schemas()

        # Create email schemas
        self._create_email_schemas()

        # External api schemas
        self._create_external_api_schemas()

        # Create filter schemas
        self._create_filter_schemas()

        # Create file schemas
        self._create_file_schemas()

    def _create_schemas_init(self) -> None:
        """Create __init__.py in schemas folder."""
        content = f'''"""
Schemas package to provide base schemas.
"""

from {self.app_name}.core.schemas.api_schemas import ApiResponse, PaginatedResponse
from {self.app_name}.core.schemas.base_schemas import BaseSchema
from {self.app_name}.core.schemas.cep_schemas import CEPQuery, AddressResponse
from {self.app_name}.core.schemas.email_schemas import EmailRequest
from {self.app_name}.core.schemas.external_api_schemas import ExternalApiRequest
from {self.app_name}.core.schemas.file_schemas import FileResponse, FileCreate
from {self.app_name}.core.schemas.filter_schemas import BaseFilter, get_base_filter, ItemFilter

__all__ = [
    "ApiResponse",
    "BaseSchema",
    "PaginatedResponse",
    "CEPQuery",
    "AddressResponse",
    "EmailRequest",
    "ExternalApiRequest",
    "FileResponse",
    "FileCreate",
    "BaseFilter",
    "get_base_filter",
    "ItemFilter",
]'''

        schemas_init_path = self.project_path / self.app_name / "core" / "schemas" / "__init__.py"
        schemas_init_path.write_text(content, encoding="utf-8")

    def _create_api_schemas(self) -> None:
        """Create api_schemas.py in schemas folder."""
        content = f'''"""
General schemas to be used through the application.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from .base_schemas import BaseSchema
from typing import List, Generic, TypeVar

T = TypeVar("T")

class ApiResponse(BaseSchema):
    status_code: int
    error: Optional[str] = None
    detail: Optional[str] = None
    data: Optional[Any] = None
    timestamp: str = datetime.now(timezone.utc).isoformat()


class PaginatedResponse(BaseSchema, Generic[T]):
    page: int
    page_size: int
    total: int
    items: List[T]'''

        api_schemas_path = self.project_path / self.app_name / "core" / "schemas" / "api_schemas.py"
        api_schemas_path.write_text(content, encoding="utf-8")

    def _create_base_schemas(self) -> None:
        """Create base_schemas.py in schemas folder."""
        content = f'''"""
Base schemas to be used through the application
"""

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)'''

        base_schemas_path = self.project_path / self.app_name / "core" / "schemas" / "base_schemas.py"
        base_schemas_path.write_text(content, encoding="utf-8")

    def _create_cep_schemas(self) -> None:
        """Create cep_schemas.py in schemas folder."""
        content = f'''"""
Provide cep schemas to be used through the application.
"""

from typing import Annotated
from pydantic import StringConstraints
from . import BaseSchema


class AddressResponse(BaseSchema):
    cep: str
    logradouro: str
    complemento: str
    bairro: str
    localidade: str
    uf: str
    ibge: str
    gia: str
    ddd: str
    siafi: str


class CEPQuery(BaseSchema):
    cep: Annotated[str, StringConstraints(pattern=r"^\\d{{5}}-?\\d{{3}}$")]  # Only digits, exactly 8 characters'''

        cep_schemas_path = self.project_path / self.app_name / "core" / "schemas" / "cep_schemas.py"
        cep_schemas_path.write_text(content, encoding="utf-8")

    def _create_email_schemas(self) -> None:
        """Create email_schemas.py in schemas folder."""
        content = f'''"""
Provide email schemas to be used through the application.
"""

from . import BaseSchema


class EmailRequest(BaseSchema):
    to: str
    subject: str | None = None
    body: str | None = None'''

        email_schemas_path = self.project_path / self.app_name / "core" / "schemas" / "email_schemas.py"
        email_schemas_path.write_text(content, encoding="utf-8")

    def _create_external_api_schemas(self) -> None:
        """Create external_api_schemas.py in schemas folder."""
        content = f'''"""
Provide external api schemas to be used through the application.
"""

from http import HTTPMethod
from typing import Optional

from . import BaseSchema


class ExternalApiRequest(BaseSchema):
    """
    Represents a request to an external API.
    """
    endpoint: Optional[str] = None
    method: Optional[HTTPMethod] = None
    headers: Optional[str] = None
    query_params: Optional[str] = None
    body: Optional[str] = None'''

        external_api_schemas_path = self.project_path / self.app_name / "core" / "schemas" / "external_api_schemas.py"
        external_api_schemas_path.write_text(content, encoding="utf-8")

    def _create_file_schemas(self) -> None:
        """Create file_schemas.py in schemas folder."""
        content = f'''"""
Provide file schemas to be used through the application.
"""

from {self.app_name}.core.schemas import BaseSchema
from uuid import UUID


class FileCreate(BaseSchema):
    id: UUID
    filename: str
    url: str
    content_type: str
    size: int
    path: str


class FileResponse(BaseSchema):
    id: UUID
    filename: str
    url: str
    content_type: str
    size: int
    # path: str'''

        file_schemas_path = self.project_path / self.app_name / "core" / "schemas" / "file_schemas.py"
        file_schemas_path.write_text(content, encoding="utf-8")

    def _create_filter_schemas(self) -> None:
        """Create filter_schemas.py in schemas folder."""
        content = f'''"""
Provide filter schemas to be used through the application.
"""

from datetime import date
from typing import Optional, List
from pydantic import Field
from fastapi import Query
from . import BaseSchema


class BaseFilter(BaseSchema):
    page: int = Field(default=1, ge=1, description="Page number (starts from 1)")
    page_size: Optional[int] =  Field(default=20, ge=1, le=1000, description="Items per page")
    logic_operator: Optional[str] = Field(default="or", description="Operator to be applied on the query") #"or"
    sort: Optional[List[str]] = None


def get_base_filter(page: Optional[int] = Query(1, ge=1), page_size: Optional[int] = Query(20, ge=1, le=1000), logic_operator: Optional[str] = Query("or"), sort: Optional[List[str]] = Query(None, description="Sort fields like column+ or column-")) -> BaseFilter:
    return BaseFilter(
        page=page,
        page_size=page_size,
        logic_operator=logic_operator,
        sort=sort,
    )

class ItemFilter:
    def __init__(
        self,
        name: Optional[str] = None,
        name_exact: Optional[str] = None,
        name_startswith: Optional[str] = None,
        name_endswith: Optional[str] = None,
        name_icontains: Optional[str] = None,

        created_at: Optional[date] = None,
        created_before: Optional[date] = None,
        created_after: Optional[date] = None,

        price: Optional[int] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,

        sort_by: Optional[str] = Query("id", enum=["id", "name", "created_at", "price"]),
        sort_order: Optional[bool] = False,

        page: int = 1,
        page_size: int = 10,
    ):
        self.name = name
        self.name_exact = name_exact
        self.name_startswith = name_startswith
        self.name_endswith = name_endswith
        self.name_icontains = name_icontains

        self.created_at = created_at
        self.created_before = created_before
        self.created_after = created_after

        self.price = price
        self.price_min = price_min
        self.price_max = price_max

        self.sort_by = sort_by
        self.sort_order = sort_order

        self.page = page
        self.page_size = page_size'''

        filter_schemas_path = self.project_path / self.app_name / "core" / "schemas" / "filter_schemas.py"
        filter_schemas_path.write_text(content, encoding="utf-8")

    def _create_services(self) -> None:
        """
        Create services package and related files
        """

        # Create __init__.py
        self._create_services_init()

        # Cep Service
        self._create_cep_service()

        # Create CircuitBreaker Service
        self._create_circuit_breaker_service()

        # Create Email Service
        self._create_email_service()

        # Create ExternalApi service
        self._create_external_api_service()

        # Create Http Client Manager
        self._create_http_client_manager()

    def _create_services_init(self) -> None:
        """Create __init__.py in services folder."""
        content = f'''"""
Services package to provide general services.
"""

from .cep_service import fetch_address_by_cep
from .circuit_breaker_service import get_circuit_breaker
from .email_service import send_email, send_reset_password_email, send_verification_email
from .external_api_service import ExternalAPIService
from .http_client_manager import get_http_client_manager

__all__ = [
    "fetch_address_by_cep",
    "get_circuit_breaker",
    "send_email",
    "send_reset_password_email",
    "send_verification_email",
    "ExternalAPIService",
    "get_http_client_manager",
]'''

        services_init_path = self.project_path / self.app_name / "core" / "services" / "__init__.py"
        services_init_path.write_text(content, encoding="utf-8")

    def _create_cep_service(self) -> None:
        """Create cep_service.py in services folder."""
        content = f'''"""
Provide a method to fetch the cep.
"""

import httpx
from {self.app_name}.core.schemas import AddressResponse

async def fetch_address_by_cep(cep: str) -> AddressResponse:
    url = f"https://viacep.com.br/ws/{{cep}}/json/"

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(url)

    if response.status_code != 200 or response.json().get("erro"):
        raise ValueError("CEP não encontrado")

    return AddressResponse(**response.json())'''

        cep_service_path = self.project_path / self.app_name / "core" / "services" / "cep_service.py"
        cep_service_path.write_text(content, encoding="utf-8")

    def _create_circuit_breaker_service(self) -> None:
        """Create circuit_breaker_service.py in services folder."""
        content = f'''"""
Provide the CircuitBreaker service.
"""

from datetime import datetime, timezone, timedelta
from functools import lru_cache

from {self.app_name}.core.config import settings


class CircuitBreaker:

    def __init__(self, failure_threshold: int = settings.FAILURE_THRESHOLD, recovery_timeout: int = settings.RECOVERY_TIMEOUT):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if self.last_failure_time and \\
                    datetime.now(timezone.utc) - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = "half_open"
                return True
            return False
        else:  # half_open
            return True

    def record_success(self):
        """Record successful execution."""
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)

        if self.failure_count >= self.failure_threshold:
            self.state = "open"


@lru_cache
def get_circuit_breaker() -> CircuitBreaker:
    """Get a CircuitBreaker instance with configured settings."""
    return CircuitBreaker(
        settings.FAILURE_THRESHOLD,
        settings.RECOVERY_TIMEOUT
    )'''

        circuit_breaker_service_path = self.project_path / self.app_name / "core" / "services" / "circuit_breaker_service.py"
        circuit_breaker_service_path.write_text(content, encoding="utf-8")

    def _create_email_service(self) -> None:
        """Create email_service.py in services folder."""
        content = f'''"""
Provide the email utility methods.
"""

import aiosmtplib
import os

from {self.app_name}.core.config import settings
from email.message import EmailMessage


async def send_email(email_to: str, subject: str, html_content: str):
    msg = EmailMessage()
    msg["From"] = f"{{settings.EMAILS_FROM_NAME}} <{{settings.EMAILS_FROM_EMAIL}}>"
    msg["To"] = email_to
    msg["Subject"] = subject
    msg.set_content(html_content)
    msg.add_alternative(html_content, subtype="html")

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        start_tls=False
    )


async def send_verification_email(email_to: str, token: str):
    verify_url = f"{{settings.FRONTEND_URL}}/auth/verificar-email?token={{token}}"
    email_html = load_email_template("verify_email_template.html", verify_url)

    await send_email(email_to, "Verifique seu e-mail", email_html)


async def send_reset_password_email(email_to: str, token: str):
    verify_url = f"{{settings.FRONTEND_URL}}/auth/confirmar-redefinir-senha?token={{token}}"
    email_html = load_email_template("reset_password_email_template.html", verify_url)

    await send_email(email_to, "Redefinição de senha", email_html)


def load_email_template(template_name, verify_url):
    app_root = os.path.abspath(os.getcwd())
    with (open(f"{{app_root}}/{self.app_name}/templates/{{template_name}}", "r", encoding="utf-8") as file):
        return file.read().replace("{{VERIFY_URL}}", verify_url).replace("{{FRONTEND_URL}}", settings.FRONTEND_URL)'''

        email_service_path = self.project_path / self.app_name / "core" / "services" / "email_service.py"
        email_service_path.write_text(content, encoding="utf-8")

    def _create_external_api_service(self) -> None:
        """Create external_api_service.py in services folder."""
        content = f'''"""
Provide a service to make request to an external api.
"""

import asyncio
import json
import httpx

from datetime import datetime, timezone
from fastapi import status
from http import HTTPMethod
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import query

from {self.app_name}.core.models import CircuitBreakerError, ExternalAPIError
from {self.app_name}.core.schemas import ExternalApiRequest
from {self.app_name}.core.services import get_circuit_breaker, get_http_client_manager


class ExternalAPIService:
    """Service for making external API calls."""

    @staticmethod
    async def make_request(
            endpoint: str,
            method: HTTPMethod,
            headers: Optional[Dict[str, str]] = None,
            query_params: Optional[Dict[str, Any]] = None,
            body: Optional[Dict[str, Any]] = None,
            request_id: Optional[str] = None,
            api_key: Optional[str] = None,
    ):
        """Make HTTP request to external service."""

        circuit_breaker = get_circuit_breaker()

        if not circuit_breaker.can_execute():
            raise CircuitBreakerError(
                message=f"Circuit breaker is open. Cannot execute request.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        start_time = datetime.now(timezone.utc)

        # Prepare headers
        request_headers = {{
            "Content-Type": "application/json",
            "X-API-Key": api_key,
            "X-Request-ID": request_id or f"req_{{int(start_time.timestamp() * 1000)}}"
        }}
        if headers:
            request_headers.update(headers)

        client_manager = get_http_client_manager()

        try:
            client = await client_manager.get_client()
            # Make the request
            response = await client.request(
                method=method,
                url=endpoint,
                headers=request_headers,
                params=query_params,
                json=body if body else None,
            )

            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            # Handle response
            if response.status_code >= 400:
                circuit_breaker.record_failure()
                error_detail = f"External API error: {{response.status_code}}"
                try:
                    error_response = response.json()
                    error_detail = error_response.get('detail', error_detail)
                except:
                    error_detail = response.text[:200]

                raise ExternalAPIError(
                    message=error_detail,
                    status_code=response.status_code
                )

            circuit_breaker.record_success()

            # Parse response
            try:
                response_data = response.json() if response.content else {{}}
            except json.JSONDecodeError:
                response_data = response

            return {{
                "success": response_data.get('status') or False,
                "data": response_data.get('data') or [],
                "message": f"{{response_data.get('message')}}" or response_data or response,
                "execution_time_ms": execution_time,
                "status_code": response.status_code,
                "request_id": request_headers["X-Request-ID"]
            }}

        except httpx.RequestError as e:
            circuit_breaker.record_failure()
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

            raise ExternalAPIError(
                f"Request to {{endpoint}} failed: {{str(e)}}, execution time: {{execution_time}}",
                status_code=503
            )
        finally:
            await client_manager.close()

    @staticmethod
    async def make_requests_batch(
            requests: List[ExternalApiRequest],
            parallel: bool = True
    ) -> List[Dict[str, Any]]:
        """Make multiple requests to external service."""

        if parallel:
            tasks = [
                ExternalAPIService.make_request(
                    endpoint=req.endpoint,
                    method=req.method,
                    headers=req.headers,
                    query_params=req.query_params,
                    body=req.body
                )
                for req in requests
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []
            for req in requests:
                try:
                    result = await ExternalAPIService.make_request(
                        endpoint=req.endpoint,
                        method=req.method,
                        headers=req.headers,
                        query_params=req.query_params,
                        body=req.body
                    )
                    results.append(result)
                except Exception as e:
                    results.append(e)
            return results'''

        external_api_service_path = self.project_path / self.app_name / "core" / "services" / "external_api_service.py"
        external_api_service_path.write_text(content, encoding="utf-8")

    def _create_http_client_manager(self) -> None:
        """Create http_client_manager.py in services folder."""
        content = f'''"""
Provide a method to fetch the cep.
"""

import httpx
from functools import lru_cache
from typing import Optional

from {self.app_name}.core.config import settings


class HTTPClientManager:
    """Manages HTTP client with connection pooling and configuration."""

    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        #headers={{"User-Agent": "FastAPI-External-API-Router/1.0"}},
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.REQUEST_TIMEOUT),
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=10),
                verify=False
            )
        return self.client

    async def close(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None


@lru_cache
def get_http_client_manager() -> HTTPClientManager:
    """Get a singleton instance of HTTPClientManager."""
    return HTTPClientManager()'''

        http_client_manager_path = self.project_path / self.app_name / "core" / "services" / "http_client_manager.py"
        http_client_manager_path.write_text(content, encoding="utf-8")


__all__ = ["ProjectTemplate"]