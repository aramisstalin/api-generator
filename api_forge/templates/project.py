"""
Project template generator.

Creates complete project structure with all necessary files and directories
for a new API Forge project.
"""

from pathlib import Path
from typing import Optional
import shutil

from api_forge.core.config import ProjectConfig
from api_forge.core.exceptions import ProjectExistsError


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
            f"{self.app_name}/db",
            f"{self.app_name}/middleware",
            f"{self.app_name}/models",
            f"{self.app_name}/repositories",
            f"{self.app_name}/schemas",
            f"{self.app_name}/services",
            f"{self.app_name}/utils",

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

        # Database session module
        self._create_db_session()

        # Base model
        self._create_base_model()

        # API router
        self._create_api_router()

        # Pytest conftest.py
        self._create_conftest()

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
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.12.1
psycopg2-binary==2.9.9

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
cryptography==41.0.7

# HTTP Client
httpx==0.25.2

# Caching
redis==5.0.1

# Utilities
python-dotenv==1.0.0
"""
        (self.project_path / "requirements.txt").write_text(content, encoding="utf-8")

    def _create_requirements_dev(self) -> None:
        """Create requirements-dev.txt file."""
        content = """-r requirements.txt

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
faker==20.1.0

# Code Quality
black==23.11.0
isort==5.12.0
ruff==0.1.6
mypy==1.7.0

# Security
bandit==1.7.5
"""
        (self.project_path / "requirements-dev.txt").write_text(content, encoding="utf-8")

    def _create_env_example(self) -> None:
        """Create .env.example file."""
        content = f"""# Application
PROJECT_NAME="{self.config.name}"
VERSION="{self.config.version}"
ENVIRONMENT=development

# API
API_V1_STR=/api/v1

# Security
SECRET_KEY=change-this-to-a-secure-random-string-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
POSTGRES_SERVER={self.config.database.host}
POSTGRES_USER={self.config.database.user or "postgres"}
POSTGRES_PASSWORD=change-this-password
POSTGRES_DB={self.config.database.name}
DATABASE_URL=postgresql+asyncpg://{self.config.database.user or "postgres"}:password@{self.config.database.host}:{self.config.database.port}/{self.config.database.name}

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

# Logging
LOG_LEVEL=INFO
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
from {self.app_name}.core.preflight import CORSPreflightMiddleware
from {self.app_name}.api.v1.router import api_router
import logging

logger = logging.getLogger(__name__)


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
    openapi_url=f"{{settings.API_V1_STR}}/openapi.json",
    docs_url=f"{{settings.API_V1_STR}}/docs",
    redoc_url=f"{{settings.API_V1_STR}}/redoc",
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],,
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Type"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


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
from pydantic import AnyHttpUrl, PostgresDsn, field_validator
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
    PROJECT_NAME: str = "{self.config.name}"
    VERSION: str = "{self.config.version}"
    API_V1_STR: str = "/api/v1"

    # --- Security & JWT Configuration ---
    # To generate a good secret key: openssl rand -hex 32
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_SECONDS: int = os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", 900)  # 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS: int = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)  # 7 days
    
    # --- Email Configuration ---
    EMAILS_FROM_EMAIL: str = os.getenv("EMAILS_FROM_EMAIL")
    EMAILS_FROM_NAME: str = os.getenv("EMAILS_FROM_NAME")
    SMTP_HOST: str = os.getenv("SMTP_HOST")
    SMTP_PORT: int = os.getenv("SMTP_PORT")

    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", ["http://localhost:4200"])

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
    LOG_LEVEL: str = os.getenv("REDIS_URL", "INFO")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")


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

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    is_deleted = Column(Boolean, default=False, index=True, nullable=False)
    deleted_at = Column(DateTime, nullable=True)


class BaseModel(Base, TimestampMixin):
    """Base model with common fields."""

    __abstract__ = True

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

    @declared_attr
    def __tablename__(cls) -> str:
        """Auto-generate table name from class name."""
        return cls.__name__.lower() + "s"

    def dict(self):
        """Convert model to dictionary."""
        return {{
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }}
'''
        base_path = self.project_path / self.app_name / "db" / "base.py"
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

    __all__ = ["ProjectTemplate"]