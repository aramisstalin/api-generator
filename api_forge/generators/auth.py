"""
Authentication system generator.

Generates complete authentication infrastructure including:
- User/Role/Permission models
- Authentication endpoints
- Security utilities
- Dependencies
- Middleware
"""

from pathlib import Path
from typing import Dict, Any, List

from api_forge.generators.base import BaseGenerator
from api_forge.generators.artifacts import CodeArtifact, ArtifactType, GenerationContext
from api_forge.core.console import console
from api_forge.schema_org import SchemaEntity


class AuthGenerator(BaseGenerator):
    """
    Generates authentication and authorization system.

    Creates:
    - User, Role, Permission models
    - Authentication endpoints (login, register, refresh)
    - Security utilities (JWT, password hashing)
    - Authentication dependencies
    - RBAC support
    """

    def generate(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> CodeArtifact:
        """
        Generate method required by BaseGenerator.

        Note: AuthGenerator uses generate_all() instead.
        This method is not used but required by the abstract base class.
        """
        raise NotImplementedError(
            "AuthGenerator uses generate_all() method instead of generate()"
        )

    def generate_all(
            self,
            context: GenerationContext
    ) -> List[CodeArtifact]:
        """
        Generate complete authentication system.

        Args:
            context: Generation context

        Returns:
            List of generated artifacts
        """
        console.print(f"[cyan]Generating authentication system...[/cyan]")

        artifacts = []

        # 1. User models (User, Role, Permission)
        console.print("  • Generating user models...")
        user_model = self._generate_user_model(context)
        artifacts.append(user_model)

        # 2. Auth schemas
        console.print("  • Generating auth schemas...")
        auth_schemas = self._generate_auth_schemas(context)
        artifacts.append(auth_schemas)

        # 3. User schemas
        console.print("  • Generating user schemas...")
        user_schemas = self._generate_user_schemas(context)
        artifacts.append(user_schemas)

        # 4. Security utilities
        console.print("  • Generating security utilities...")
        security = self._generate_security(context)
        artifacts.append(security)

        # 5. Dependencies
        console.print("  • Generating auth dependencies...")
        dependencies = self._generate_dependencies(context)
        artifacts.append(dependencies)

        # 6. Auth endpoints
        console.print("  • Generating auth endpoints...")
        auth_router = self._generate_auth_router(context)
        artifacts.append(auth_router)

        # 7. User repository
        console.print("  • Generating user repository...")
        user_repo = self._generate_user_repository(context)
        artifacts.append(user_repo)

        # 8. User service
        console.print("  • Generating user service...")
        user_service = self._generate_user_service(context)
        artifacts.append(user_service)

        # 9. Exceptions
        console.print("  • Generating exception classes...")
        exceptions = self._generate_exceptions(context)
        artifacts.append(exceptions)

        # 10. Exception handlers
        console.print("  • Generating exception handlers...")
        handlers = self._generate_exception_handlers(context)
        artifacts.append(handlers)

        # 11. Middleware
        console.print("  • Generating middleware...")
        middleware_artifacts = self._generate_middleware(context)
        artifacts.extend(middleware_artifacts)

        # 12. Utilities
        console.print("  • Generating utilities...")
        util_artifacts = self._generate_utilities(context)
        artifacts.extend(util_artifacts)

        # Validate all artifacts
        for artifact in artifacts:
            if self.validate_artifact(artifact):
                artifact.mark_generated()

        console.print(f"[green]✓[/green] Authentication system generated: {len(artifacts)} files")

        return artifacts

    def _generate_user_model(self, context: GenerationContext) -> CodeArtifact:
        """Generate User, Role, Permission models"""
        template_context = {
            "app_name": context.app_name
        }

        code = self.render_template("user_model.py.jinja", template_context)
        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.MODEL,
            path=Path(context.app_name) / "models" / "user.py",
            content=code,
            entity_name="User"
        )

    def _generate_auth_schemas(self, context: GenerationContext) -> CodeArtifact:
        """Generate authentication schemas"""
        code = '''"""
Authentication schemas.

Pydantic models for authentication requests and responses.
"""

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request"""
    refresh_token: str


class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "SecurePass123!",
                "full_name": "John Doe"
            }
        }
    }


class UserLogin(BaseModel):
    """User login request"""
    email_or_username: str
    password: str
'''

        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.SCHEMA,
            path=Path(context.app_name) / "schemas" / "auth.py",
            content=code,
            entity_name="Auth"
        )

    def _generate_user_schemas(self, context: GenerationContext) -> CodeArtifact:
        """Generate user schemas"""
        code = '''"""
User schemas.

Pydantic models for user requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response schema"""
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    """Paginated user list response"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
'''

        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.SCHEMA,
            path=Path(context.app_name) / "schemas" / "user.py",
            content=code,
            entity_name="User"
        )

    def _generate_security(self, context: GenerationContext) -> CodeArtifact:
        """Generate security utilities"""
        template_context = {
            "app_name": context.app_name
        }

        code = self.render_template("security.py.jinja", template_context)
        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.CONFIG,
            path=Path(context.app_name) / "core" / "security.py",
            content=code,
            entity_name="Security"
        )

    def _generate_dependencies(self, context: GenerationContext) -> CodeArtifact:
        """Generate authentication dependencies"""
        # Add settings import to template context
        template_context = {
            "app_name": context.app_name
        }

        # First, render the template
        code = self.render_template("dependencies.py.jinja", template_context)

        # Add the missing import at the top
        imports_to_add = [
            f"from {context.app_name}.core.config import settings"
        ]

        code = self.add_imports(code, imports_to_add)
        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.CONFIG,
            path=Path(context.app_name) / "core" / "dependencies.py",
            content=code,
            entity_name="Dependencies"
        )

    def _generate_auth_router(self, context: GenerationContext) -> CodeArtifact:
        """Generate authentication endpoints"""
        template_context = {
            "app_name": context.app_name
        }

        code = self.render_template("auth.py.jinja", template_context)
        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.ROUTER,
            path=Path(context.app_name) / "api" / "v1" / "endpoints" / "auth.py",
            content=code,
            entity_name="Auth"
        )

    def _generate_user_repository(self, context: GenerationContext) -> CodeArtifact:
        """Generate user repository"""
        code = f'''"""
User repository.

Data access layer for User entity.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from {context.app_name}.models.user import User
from {context.app_name}.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email_or_username(
        self,
        email_or_username: str
    ) -> Optional[User]:
        """Get user by email or username"""
        query = select(User).where(
            (User.email == email_or_username) | 
            (User.username == email_or_username)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
'''

        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.REPOSITORY,
            path=Path(context.app_name) / "repositories" / "user_repository.py",
            content=code,
            entity_name="User"
        )

    def _generate_user_service(self, context: GenerationContext) -> CodeArtifact:
        """Generate user service"""
        code = f'''"""
User service.

Business logic for user management and authentication.
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from {context.app_name}.models.user import User
from {context.app_name}.schemas.auth import UserRegister
from {context.app_name}.schemas.user import UserCreate, UserUpdate
from {context.app_name}.repositories.user_repository import UserRepository
from {context.app_name}.services.base import BaseService
from {context.app_name}.core.security import get_password_hash, verify_password


class UserService(BaseService[User, UserCreate, UserUpdate]):
    """Service for user management"""

    def __init__(self, db: AsyncSession):
        repository = UserRepository(db)
        super().__init__(repository, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.repository.get_by_email(email)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return await self.repository.get_by_username(username)

    async def create_user(self, user_in: UserRegister) -> User:
        """
        Create new user with hashed password.

        Args:
            user_in: User registration data

        Returns:
            Created user
        """
        user_data = {{
            "email": user_in.email,
            "username": user_in.username,
            "full_name": user_in.full_name,
            "hashed_password": get_password_hash(user_in.password),
            "is_active": True,
            "is_superuser": False
        }}

        return await self.repository.create(user_data)

    async def authenticate(
        self,
        email_or_username: str,
        password: str
    ) -> Optional[User]:
        """
        Authenticate user with email/username and password.

        Args:
            email_or_username: Email or username
            password: Plain text password

        Returns:
            User if authentication succeeds, None otherwise
        """
        user = await self.repository.get_by_email_or_username(email_or_username)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        return user

    async def update_password(
        self,
        user_id: UUID,
        new_password: str
    ) -> Optional[User]:
        """
        Update user password.

        Args:
            user_id: User ID
            new_password: New plain text password

        Returns:
            Updated user
        """
        hashed_password = get_password_hash(new_password)
        return await self.repository.update(
            user_id,
            {{"hashed_password": hashed_password}}
        )
'''

        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.SERVICE,
            path=Path(context.app_name) / "services" / "user_service.py",
            content=code,
            entity_name="User"
        )

    def _generate_exceptions(self, context: GenerationContext) -> CodeArtifact:
        """Generate exception classes"""
        template_context = {
            "app_name": context.app_name
        }

        code = self.render_template("exceptions.py.jinja", template_context)
        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.CONFIG,
            path=Path(context.app_name) / "core" / "exceptions.py",
            content=code,
            entity_name="Exceptions"
        )

    def _generate_exception_handlers(self, context: GenerationContext) -> CodeArtifact:
        """Generate exception handlers"""
        template_context = {
            "app_name": context.app_name
        }

        code = self.render_template("exception_handlers.py.jinja", template_context)
        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.CONFIG,
            path=Path(context.app_name) / "core" / "exception_handlers.py",
            content=code,
            entity_name="ExceptionHandlers"
        )

    def _generate_middleware(self, context: GenerationContext) -> List[CodeArtifact]:
        """Generate middleware components"""
        artifacts = []
        template_context = {"app_name": context.app_name}

        # Logging middleware
        logging_code = self.render_template("middleware_logging.py.jinja", template_context)
        artifacts.append(CodeArtifact(
            type=ArtifactType.CONFIG,
            path=Path(context.app_name) / "middleware" / "logging.py",
            content=self.format_code(logging_code),
            entity_name="Middleware"
        ))

        # Rate limiting middleware
        rate_limit_code = self.render_template("middleware_rate_limit.py.jinja", template_context)
        artifacts.append(CodeArtifact(
            type=ArtifactType.CONFIG,
            path=Path(context.app_name) / "middleware" / "rate_limit.py",
            content=self.format_code(rate_limit_code),
            entity_name="Middleware"
        ))

        # Correlation ID middleware
        correlation_code = self.render_template("middleware_correlation.py.jinja", template_context)
        artifacts.append(CodeArtifact(
            type=ArtifactType.CONFIG,
            path=Path(context.app_name) / "middleware" / "correlation_id.py",
            content=self.format_code(correlation_code),
            entity_name="Middleware"
        ))

        return artifacts

    def _generate_utilities(self, context: GenerationContext) -> List[CodeArtifact]:
        """Generate utility modules"""
        artifacts = []
        template_context = {"app_name": context.app_name}

        # Pagination utilities
        pagination_code = self.render_template("utils_pagination.py.jinja", template_context)
        artifacts.append(CodeArtifact(
            type=ArtifactType.CONFIG,
            path=Path(context.app_name) / "utils" / "pagination.py",
            content=self.format_code(pagination_code),
            entity_name="Utils"
        ))

        # Filtering utilities
        filtering_code = self.render_template("utils_filtering.py.jinja", template_context)
        artifacts.append(CodeArtifact(
            type=ArtifactType.CONFIG,
            path=Path(context.app_name) / "utils" / "filtering.py",
            content=self.format_code(filtering_code),
            entity_name="Utils"
        ))

        return artifacts


__all__ = ["AuthGenerator"]