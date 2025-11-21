"""
Generation orchestrator.

Coordinates all generators to produce complete, integrated code artifacts.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio

from api_forge.ai.config import AIConfig
from api_forge.generators.artifacts import (
    CodeArtifact,
    GenerationContext,
    ArtifactType
)
from api_forge.generators.tests import TestGenerator
from api_forge.generators.auth import AuthGenerator
from api_forge.generators.models import ModelGenerator
from api_forge.generators.schemas import SchemaGenerator
from api_forge.generators.repositories import RepositoryGenerator
from api_forge.generators.services import ServiceGenerator
from api_forge.generators.routers import RouterGenerator
from api_forge.schema_org.models import SchemaEntity, EntityAnalysis
from api_forge.schema_org.analyzer import SchemaOrgAnalyzer
from api_forge.core.config import ProjectConfig
from api_forge.core.console import console
from api_forge.core.exceptions import CodeGenerationError


class GenerationOrchestrator:
    """
    Orchestrates code generation process.

    Coordinates multiple generators to produce a complete,
    integrated application from Schema.org entities.
    """

    def __init__(self, project_path: Path, config: ProjectConfig, ai_config: Optional[AIConfig] = None):
        """
        Initialize orchestrator.

        Args:
            project_path: Root path of the project
            config: Project configuration
            ai_config: AI configuration for enhanced generation
        """
        self.project_path = project_path
        self.config = config
        self.app_name = config.name.replace("-", "_")
        self.ai_config = ai_config

        # Initialize generators
        self.model_generator = ModelGenerator()
        self.schema_generator = SchemaGenerator()
        self.repository_generator = RepositoryGenerator()
        self.service_generator = ServiceGenerator()
        self.router_generator = RouterGenerator()
        self.auth_generator = AuthGenerator()
        self.test_generator = TestGenerator(ai_config)

        # Track generated artifacts
        self.artifacts: List[CodeArtifact] = []

    async def generate_entity(
            self,
            entity_name: str,
            force: bool = False,
            write_files: bool = True
    ) -> List[CodeArtifact]:
        """
        Generate complete CRUD application for an entity.

        Args:
            entity_name: Name of Schema.org entity
            force: Force overwrite existing files
            write_files: Write artifacts to disk

        Returns:
            List of generated artifacts

        Raises:
            CodeGenerationError: If generation fails
        """
        console.print(f"\n[bold cyan]🔨 Generating application for:[/bold cyan] [bold]{entity_name}[/bold]\n")

        try:
            # Step 1: Analyze Schema.org entity (with AI)
            analysis = await self._analyze_entity(entity_name)

            # Step 2: Create generation context
            context = GenerationContext(
                project_path=self.project_path,
                app_name=self.app_name,
                entity_name=entity_name,
                config=self.config
            )

            # Step 3: Generate all artifacts
            artifacts = await self._generate_all_artifacts(analysis, context)

            # Step 4: Validate artifacts
            self._validate_artifacts(artifacts)

            # Step 5: Write to disk if requested
            if write_files:
                self._write_artifacts(artifacts, force)

            # Step 6: Update router registry
            if write_files:
                self._update_router_registry(entity_name)

            console.print(
                f"\n[bold green]✓[/bold green] Successfully generated {len(artifacts)} files for {entity_name}")

            return artifacts

        except Exception as e:
            raise CodeGenerationError(
                f"Failed to generate entity {entity_name}: {e}",
                details={"entity": entity_name, "error": str(e)}
            )

    async def generate_multiple(
            self,
            entity_names: List[str],
            force: bool = False
    ) -> Dict[str, List[CodeArtifact]]:
        """
        Generate applications for multiple entities.

        Args:
            entity_names: List of Schema.org entity names
            force: Force overwrite existing files

        Returns:
            Dictionary mapping entity names to their artifacts
        """
        results = {}

        for entity_name in entity_names:
            try:
                artifacts = await self.generate_entity(entity_name, force)
                results[entity_name] = artifacts
            except CodeGenerationError as e:
                console.print(f"[red]✗[/red] Failed to generate {entity_name}: {e.message}")
                continue

        return results

    async def _analyze_entity(self, entity_name: str) -> EntityAnalysis:
        """
        Analyze Schema.org entity.

        Args:
            entity_name: Entity name

        Returns:
            EntityAnalysis with AI insights
        """
        console.print(f"[cyan]Step 1:[/cyan] Analyzing Schema.org definition...")

        async with SchemaOrgAnalyzer(ai_config=self.ai_config) as analyzer:
            # Use AI if configured
            use_ai = self.ai_config and self.ai_config.enabled
            analysis = await analyzer.analyze_entity(entity_name, use_ai=use_ai)

        return analysis

    async def _generate_all_artifacts(
            self,
            analysis: EntityAnalysis,
            context: GenerationContext
    ) -> List[CodeArtifact]:
        """
        Generate all code artifacts for an entity.

        Args:
            analysis: Entity analysis (with AI insights)
            context: Generation context

        Returns:
            List of generated artifacts
        """
        console.print(f"\n[cyan]Step 2:[/cyan] Generating code artifacts...")

        artifacts = []
        entity = analysis.entity

        # Generate in dependency order

        # 1. Model (no dependencies)
        console.print("  • Generating model...")
        model_artifact = self.model_generator.generate(entity, context)
        artifacts.append(model_artifact)
        context.add_artifact(model_artifact)

        # 2. Schema (depends on model)
        console.print("  • Generating schemas...")
        schema_artifact = self.schema_generator.generate(entity, context)
        artifacts.append(schema_artifact)
        context.add_artifact(schema_artifact)

        # 3. Repository (depends on model)
        console.print("  • Generating repository...")
        repository_artifact = self.repository_generator.generate(entity, context)
        artifacts.append(repository_artifact)
        context.add_artifact(repository_artifact)

        # 4. Service (depends on model, schema, repository)
        console.print("  • Generating service...")
        service_artifact = self.service_generator.generate(entity, context)
        artifacts.append(service_artifact)
        context.add_artifact(service_artifact)

        # 5. Router (depends on all above)
        console.print("  • Generating API router...")
        router_artifact = self.router_generator.generate(entity, context)
        artifacts.append(router_artifact)
        context.add_artifact(router_artifact)

        # 6. Tests (NEW)
        if context.config and context.config.testing.generate_tests:
            console.print("  • Generating tests...")
            test_artifacts = self.test_generator.generate(
                entity,
                context,
                use_ai=self.ai_config and self.ai_config.enabled
            )
            artifacts.extend(test_artifacts)
            for test_artifact in test_artifacts:
                context.add_artifact(test_artifact)

        return artifacts

    def _validate_artifacts(self, artifacts: List[CodeArtifact]) -> None:
        """
        Validate all generated artifacts.

        Args:
            artifacts: List of artifacts to validate

        Raises:
            CodeGenerationError: If validation fails
        """
        console.print(f"\n[cyan]Step 3:[/cyan] Validating generated code...")

        errors = []

        for artifact in artifacts:
            if not artifact.status.value == "validated":
                errors.append(f"{artifact.path}: Not validated")

        if errors:
            raise CodeGenerationError(
                "Artifact validation failed",
                details={"errors": errors}
            )

        console.print(f"[green]✓[/green] All artifacts validated successfully")

    def _write_artifacts(
            self,
            artifacts: List[CodeArtifact],
            force: bool = False
    ) -> None:
        """
        Write artifacts to disk.

        Args:
            artifacts: Artifacts to write
            force: Force overwrite existing files
        """
        console.print(f"\n[cyan]Step 4:[/cyan] Writing files to disk...")

        written = 0
        skipped = 0

        for artifact in artifacts:
            # Check if file exists
            file_path = self.project_path / artifact.path

            if file_path.exists() and not force:
                console.print(f"[yellow]⊘[/yellow] Skipped (exists): {artifact.path}")
                skipped += 1
                continue

            # Write file
            if self._write_artifact(artifact):
                written += 1

        console.print(f"\n[green]✓[/green] Written: {written} files")
        if skipped > 0:
            console.print(f"[yellow]⊘[/yellow] Skipped: {skipped} files (use --force to overwrite)")

    def _write_artifact(self, artifact: CodeArtifact) -> bool:
        """
        Write a single artifact to disk.

        Args:
            artifact: Artifact to write

        Returns:
            True if written successfully
        """
        try:
            file_path = self.project_path / artifact.path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(artifact.content, encoding='utf-8')
            artifact.mark_written()

            console.print(f"[green]✓[/green] {artifact.path} ({artifact.lines} lines)")
            return True

        except Exception as e:
            console.print(f"[red]✗[/red] Failed to write {artifact.path}: {e}")
            artifact.mark_error()
            return False

    def _update_router_registry(self, entity_name: str) -> None:
        """
        Update the main API router to include the new entity router.

        Args:
            entity_name: Name of the entity
        """
        router_file = self.project_path / self.app_name / "api" / "v1" / "router.py"

        if not router_file.exists():
            console.print(f"[yellow]⚠[/yellow] Router file not found: {router_file}")
            return

        try:
            # Read existing router
            content = router_file.read_text(encoding='utf-8')

            entity_lower = entity_name.lower()
            import_line = f"from {self.app_name}.api.v1.endpoints import {entity_lower}"
            include_line = f'api_router.include_router({entity_lower}.router, prefix="/{entity_lower}s", tags=["{entity_name}"])'

            # Check if already imported
            if import_line in content:
                console.print(f"[dim]Router already registered for {entity_name}[/dim]")
                return

            # Find where to insert import
            lines = content.split('\n')
            import_index = 0
            for i, line in enumerate(lines):
                if line.startswith('from') and 'endpoints import' in line:
                    import_index = i + 1

            # Insert import
            if import_index > 0:
                lines.insert(import_index, import_line)

            # Find where to insert include
            include_index = 0
            for i, line in enumerate(lines):
                if 'api_router.include_router' in line:
                    include_index = i + 1

            # Insert include
            if include_index > 0:
                lines.insert(include_index, include_line)
            else:
                # Add at end of file
                lines.append('')
                lines.append(include_line)

            # Write back
            router_file.write_text('\n'.join(lines), encoding='utf-8')
            console.print(f"[green]✓[/green] Updated API router registry")

        except Exception as e:
            console.print(f"[yellow]⚠[/yellow] Failed to update router registry: {e}")

    def get_generation_summary(self) -> Dict[str, Any]:
        """
        Get summary of generation process.

        Returns:
            Summary dictionary
        """
        artifacts_by_type = {}
        for artifact in self.artifacts:
            type_name = artifact.type.value
            if type_name not in artifacts_by_type:
                artifacts_by_type[type_name] = []
            artifacts_by_type[type_name].append(artifact)

        total_lines = sum(a.lines for a in self.artifacts)
        total_size = sum(a.size for a in self.artifacts)

        return {
            "total_artifacts": len(self.artifacts),
            "total_lines": total_lines,
            "total_size": total_size,
            "by_type": {
                type_name: len(artifacts)
                for type_name, artifacts in artifacts_by_type.items()
            }
        }

    async def generate_auth_system(
            self,
            write_files: bool = True
    ) -> List[CodeArtifact]:
        """
        Generate complete authentication system.

        Args:
            write_files: Write artifacts to disk

        Returns:
            List of generated artifacts
        """
        console.print("\n[bold cyan]🔐 Generating Authentication System[/bold cyan]\n")

        try:
            # Create generation context
            context = GenerationContext(
                project_path=self.project_path,
                app_name=self.app_name,
                entity_name="Auth",
                config=self.config
            )

            # Generate all auth artifacts
            artifacts = self.auth_generator.generate_all(context)

            # Validate artifacts
            self._validate_artifacts(artifacts)

            # Write to disk if requested
            if write_files:
                self._write_artifacts(artifacts, force=False)

            console.print(f"\n[bold green]✓[/bold green] Authentication system generated successfully")

            return artifacts

        except Exception as e:
            raise CodeGenerationError(
                f"Failed to generate authentication system: {e}",
                details={"error": str(e)}
            )

__all__ = ["GenerationOrchestrator"]