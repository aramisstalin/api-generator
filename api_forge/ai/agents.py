"""
AI agent system.

Implements specialized agents for different code generation tasks.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import asyncio

from api_forge.ai.client import AIClient
from api_forge.ai.config import AIConfig
from api_forge.ai.prompts import PromptTemplates
from api_forge.schema_org.models import SchemaEntity, EntityAnalysis
from api_forge.core.console import console
from api_forge.core.exceptions import AIGenerationError


@dataclass
class AgentTask:
    """Represents a task for an AI agent"""
    id: str
    description: str
    input_data: Dict[str, Any]
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class AgentResult:
    """Result from an AI agent"""
    task_id: str
    success: bool
    data: Any
    error: Optional[str] = None


class SchemaAnalystAgent:
    """
    Analyzes Schema.org entities to provide business insights.

    Uses AI to understand semantic meaning and suggest:
    - Required vs optional fields
    - Validation rules
    - Business logic
    - Security considerations
    """

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client
        self.prompts = PromptTemplates()

    async def analyze(self, entity: SchemaEntity) -> EntityAnalysis:
        """
        Analyze entity and produce enhanced specification.

        Args:
            entity: Schema.org entity

        Returns:
            Enhanced entity analysis
        """
        console.print(f"[dim]AI analyzing {entity.name}...[/dim]")

        try:
            # Generate analysis prompt
            prompt = self.prompts.analyze_entity(entity)

            # Get AI analysis
            analysis_data = await self.ai_client.generate_structured(
                prompt=prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "required_fields": {"type": "array"},
                        "unique_fields": {"type": "array"},
                        "indexed_fields": {"type": "array"},
                        "immutable_fields": {"type": "array"},
                        "default_values": {"type": "object"},
                        "validation_rules": {"type": "array"},
                        "business_rules": {"type": "array"},
                        "security_notes": {"type": "array"},
                        "custom_methods": {"type": "array"},
                        "use_soft_delete": {"type": "boolean"},
                        "searchable_fields": {"type": "array"}
                    }
                },
                system_prompt=self.prompts.SYSTEM_PYTHON_EXPERT
            )

            # Create enhanced analysis
            analysis = EntityAnalysis(
                entity=entity,
                suggested_indexes=analysis_data.get("indexed_fields", []),
                unique_fields=analysis_data.get("unique_fields", []),
                immutable_fields=analysis_data.get("immutable_fields", []),
                computed_fields={},  # Populated from custom methods
                business_rules=analysis_data.get("business_rules", []),
                security_considerations=analysis_data.get("security_notes", []),
                recommended_defaults=analysis_data.get("default_values", {})
            )

            console.print(f"[green]✓[/green] [dim]AI analysis complete for {entity.name}[/dim]")

            return analysis

        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] [dim]AI analysis failed, using defaults[/dim]")
            # Return basic analysis on failure
            return EntityAnalysis(entity=entity)


class CodeGeneratorAgent:
    """
    Generates code using AI.

    Specialized in:
    - Business logic methods
    - Complex validations
    - Custom queries
    """

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client
        self.prompts = PromptTemplates()

    async def generate_business_method(
            self,
            entity_name: str,
            method_description: str,
            context: Dict[str, Any]
    ) -> str:
        """
        Generate a business logic method.

        Args:
            entity_name: Entity name
            method_description: What the method should do
            context: Additional context (fields, relationships, etc.)

        Returns:
            Generated Python method code
        """
        console.print(f"[dim]AI generating method: {method_description}[/dim]")

        prompt = self.prompts.generate_business_method(
            entity_name,
            method_description,
            context
        )

        code = await self.ai_client.generate_code(
            prompt=prompt,
            language="python",
            system_prompt=self.prompts.SYSTEM_PYTHON_EXPERT
        )

        return code

    async def generate_validation(
            self,
            entity_name: str,
            field_name: str,
            validation_type: str,
            context: Dict[str, Any]
    ) -> str:
        """
        Generate a Pydantic validator.

        Args:
            entity_name: Entity name
            field_name: Field to validate
            validation_type: Type of validation
            context: Additional context

        Returns:
            Generated validator code
        """
        prompt = self.prompts.generate_validation(
            entity_name,
            field_name,
            validation_type,
            context
        )

        code = await self.ai_client.generate_code(
            prompt=prompt,
            language="python"
        )

        return code


class TestGeneratorAgent:
    """
    Generates comprehensive test suites.

    Creates:
    - Unit tests
    - Integration tests
    - E2E tests
    - Edge case tests
    """

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client
        self.prompts = PromptTemplates()

    async def generate_test_suite(
            self,
            entity_name: str,
            endpoints: List[str],
            context: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive test suite.

        Args:
            entity_name: Entity name
            endpoints: List of API endpoints
            context: Additional context

        Returns:
            Generated test code
        """
        console.print(f"[dim]AI generating tests for {entity_name}...[/dim]")

        prompt = self.prompts.generate_test_suite(
            entity_name,
            endpoints,
            context
        )

        code = await self.ai_client.generate_code(
            prompt=prompt,
            language="python",
            system_prompt=self.prompts.SYSTEM_PYTHON_EXPERT
        )

        console.print(f"[green]✓[/green] [dim]Tests generated for {entity_name}[/dim]")

        return code


class AgentSystem:
    """
    Orchestrates multiple AI agents.

    Coordinates specialist agents to provide comprehensive
    AI-powered code generation.
    """

    def __init__(self, config: AIConfig):
        """
        Initialize agent system.

        Args:
            config: AI configuration
        """
        self.config = config
        self.ai_client = AIClient(config)

        # Initialize specialist agents
        self.analyst = SchemaAnalystAgent(self.ai_client)
        self.code_generator = CodeGeneratorAgent(self.ai_client)
        self.test_generator = TestGeneratorAgent(self.ai_client)

    async def analyze_entity(self, entity: SchemaEntity) -> EntityAnalysis:
        """Analyze entity using AI"""
        if not self.config.enabled:
            return EntityAnalysis(entity=entity)

        return await self.analyst.analyze(entity)

    async def generate_business_method(
            self,
            entity_name: str,
            method_description: str,
            context: Dict[str, Any]
    ) -> str:
        """Generate business method using AI"""
        if not self.config.enabled:
            return "# AI generation disabled"

        return await self.code_generator.generate_business_method(
            entity_name,
            method_description,
            context
        )

    async def generate_tests(
            self,
            entity_name: str,
            endpoints: List[str],
            context: Dict[str, Any]
    ) -> str:
        """Generate tests using AI"""
        if not self.config.enabled:
            return "# AI generation disabled"

        return await self.test_generator.generate_test_suite(
            entity_name,
            endpoints,
            context
        )

    async def close(self) -> None:
        """Close agent system"""
        await self.ai_client.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()


__all__ = [
    "AgentTask",
    "AgentResult",
    "SchemaAnalystAgent",
    "CodeGeneratorAgent",
    "TestGeneratorAgent",
    "AgentSystem",
]