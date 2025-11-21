"""
Test suite generator.

Generates comprehensive test suites with AI assistance.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional

from api_forge.generators.base import BaseGenerator
from api_forge.generators.artifacts import CodeArtifact, ArtifactType, GenerationContext
from api_forge.schema_org.models import SchemaEntity, EntityAnalysis
from api_forge.ai.agents import AgentSystem
from api_forge.ai.config import AIConfig
from api_forge.core.console import console


class TestGenerator(BaseGenerator):
    """
    Generates test suites.

    Creates comprehensive tests with:
    - Unit tests (services, repositories)
    - Integration tests (database operations)
    - E2E tests (API endpoints)
    - Factory fixtures
    """

    def __init__(self, ai_config: Optional[AIConfig] = None):
        """
        Initialize test generator.

        Args:
            ai_config: AI configuration for enhanced test generation
        """
        super().__init__()

        # AI enhancement (optional)
        self.ai_enabled = ai_config and ai_config.is_configured
        if self.ai_enabled:
            self.ai_system = AgentSystem(ai_config)

    def generate(
            self,
            entity: SchemaEntity,
            context: GenerationContext,
            use_ai: bool = True
    ) -> List[CodeArtifact]:
        """
        Generate complete test suite for an entity.

        Args:
            entity: Schema.org entity
            context: Generation context
            use_ai: Use AI for test generation

        Returns:
            List of generated test artifacts
        """
        console.print(f"[cyan]Generating tests for:[/cyan] {entity.name}")

        artifacts = []

        # Generate factory
        factory = self._generate_factory(entity, context)
        artifacts.append(factory)

        # Generate E2E tests
        if use_ai and self.ai_enabled:
            e2e_tests = self._generate_e2e_tests_ai(entity, context)
        else:
            e2e_tests = self._generate_e2e_tests_template(entity, context)

        artifacts.append(e2e_tests)

        # Validate all artifacts
        for artifact in artifacts:
            if self.validate_artifact(artifact):
                artifact.mark_generated()

        console.print(f"[green]✓[/green] Tests generated: {len(artifacts)} files")

        return artifacts

    def _generate_factory(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> CodeArtifact:
        """Generate factory for creating test data"""

        code = f'''"""
{entity.name} factory for tests.

Generates test data for {entity.name} entity.
"""

from typing import Optional
from uuid import uuid4
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from {context.app_name}.models.{entity.name.lower()} import {entity.name}

fake = Faker()


class {entity.name}Factory:
    """Factory for creating test {entity.name} objects"""

    @staticmethod
    async def create(
        db: AsyncSession,
        **kwargs
    ) -> {entity.name}:
        """
        Create a test {entity.name}.

        Args:
            db: Database session
            **kwargs: Override default values

        Returns:
            Created {entity.name}
        """
        # Generate default values
        data = {{
            "id": uuid4(),
            {self._generate_factory_defaults(entity)}
        }}

        # Override with provided values
        data.update(kwargs)

        # Create instance
        instance = {entity.name}(**data)

        db.add(instance)
        await db.commit()
        await db.refresh(instance)

        return instance

    @staticmethod
    async def create_batch(
        db: AsyncSession,
        count: int = 5,
        **kwargs
    ) -> list[{entity.name}]:
        """Create multiple test {entity.name} objects"""
        instances = []
        for _ in range(count):
            instance = await {entity.name}Factory.create(db, **kwargs)
            instances.append(instance)
        return instances
'''

        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.TEST,
            path=Path("tests") / "factories" / f"{entity.name.lower()}_factory.py",
            content=code,
            entity_name=entity.name
        )

    def _generate_factory_defaults(self, entity: SchemaEntity) -> str:
        """Generate default values for factory"""
        lines = []

        for prop_name, prop in entity.properties.items():
            if prop.is_relationship or prop_name in ["id", "created_at", "updated_at"]:
                continue

            default_value = self._get_faker_expression(prop)
            lines.append(f'"{prop_name}": {default_value},')

        return "\n            ".join(lines)

    def _get_faker_expression(self, prop: Any) -> str:
        """Get Faker expression for property"""
        lower_name = prop.name.lower()

        if "email" in lower_name:
            return "fake.email()"
        elif "name" in lower_name:
            return "fake.name()"
        elif "phone" in lower_name or "telephone" in lower_name:
            return "fake.phone_number()"
        elif "address" in lower_name:
            return "fake.address()"
        elif "url" in lower_name or "website" in lower_name:
            return "fake.url()"
        elif "description" in lower_name or "text" in lower_name:
            return "fake.text(max_nb_chars=200)"
        elif "date" in lower_name:
            return "fake.date()"

        # Type-based defaults
        type_info = getattr(prop, 'type_info', None)
        if type_info:
            if type_info.python_type == "str":
                return "fake.word()"
            elif type_info.python_type == "int":
                return "fake.random_int(min=1, max=100)"
            elif type_info.python_type == "float":
                return "fake.random.uniform(1.0, 100.0)"
            elif type_info.python_type == "bool":
                return "fake.boolean()"

        return '"test_value"'

    async def _generate_e2e_tests_ai(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> CodeArtifact:
        """Generate E2E tests using AI"""

        entity_lower = entity.name.lower()
        endpoints = [
            f"POST /api/v1/{entity_lower}s",
            f"GET /api/v1/{entity_lower}s",
            f"GET /api/v1/{entity_lower}s/{{id}}",
            f"PATCH /api/v1/{entity_lower}s/{{id}}",
            f"DELETE /api/v1/{entity_lower}s/{{id}}",
        ]

        # Prepare context for AI
        test_context = {
            "required_fields": [
                prop_name for prop_name, prop in entity.properties.items()
                if prop.required and not prop.is_relationship
            ],
            "optional_fields": [
                prop_name for prop_name, prop in entity.properties.items()
                if not prop.required and not prop.is_relationship
            ],
            "unique_fields": getattr(entity, 'metadata', {}).get('unique_fields', []),
            "relationships": [rel.property_name for rel in entity.relationships],
        }

        # Generate tests with AI
        code = await self.ai_system.generate_tests(
            entity_name=entity.name,
            endpoints=endpoints,
            context=test_context
        )

        # Add imports
        imports = [
            "import pytest",
            "from httpx import AsyncClient",
            "from uuid import uuid4",
            f"from tests.factories.{entity_lower}_factory import {entity.name}Factory",
        ]

        code = self.add_imports(code, imports)
        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.TEST,
            path=Path("tests") / "e2e" / f"test_{entity_lower}_crud.py",
            content=code,
            entity_name=entity.name
        )

    def _generate_e2e_tests_template(
            self,
            entity: SchemaEntity,
            context: GenerationContext
    ) -> CodeArtifact:
        """Generate E2E tests using template (fallback)"""

        # Use existing template-based generation
        template_context = {
            "entity": entity,
            "app_name": context.app_name,
        }

        code = self.render_template("test_e2e.py.jinja", template_context)
        code = self.format_code(code)

        return CodeArtifact(
            type=ArtifactType.TEST,
            path=Path("tests") / "e2e" / f"test_{entity.name.lower()}_crud.py",
            content=code,
            entity_name=entity.name
        )


__all__ = ["TestGenerator"]