"""
JSON metadata analyzer.

High-level orchestrator for JSON-based entity generation.
Parallels SchemaOrgAnalyzer but works with JSON metadata files.
"""

from typing import Dict, List, Optional
from pathlib import Path

from api_forge.schema_org.models import SchemaEntity, EntityAnalysis
from api_forge.json_metadata.loader import JSONMetadataLoader, JSONMetadata, EntityMetadata
from api_forge.json_metadata.converter import JSONToEntityConverter
from api_forge.ai.agents import AgentSystem
from api_forge.ai.config import AIConfig
from api_forge.core.exceptions import ValidationError
from api_forge.core.console import console


class JSONMetadataAnalyzer:
    """
    High-level JSON metadata analyzer.

    Orchestrates JSON metadata loading, conversion, and optional AI enhancement.
    Provides the same interface as SchemaOrgAnalyzer for seamless integration.
    """

    def __init__(
            self,
            metadata_file: Optional[Path] = None,
            ai_config: Optional[AIConfig] = None
    ):
        """
        Initialize analyzer.

        Args:
            metadata_file: Path to JSON metadata file (optional, can load later)
            ai_config: AI configuration (optional, enables AI features)
        """
        self.loader = JSONMetadataLoader()
        self.converter = JSONToEntityConverter()

        self.metadata: Optional[JSONMetadata] = None
        self.analyzed_entities: Dict[str, SchemaEntity] = {}
        self.entity_analyses: Dict[str, EntityAnalysis] = {}

        # AI enhancement (optional)
        self.ai_enabled = ai_config and ai_config.is_configured
        if self.ai_enabled:
            self.ai_system = AgentSystem(ai_config)
            console.print("[dim]AI enhancement enabled[/dim]")
        else:
            self.ai_system = None

        # Load metadata if provided
        if metadata_file:
            self.load_metadata(metadata_file)

    def load_metadata(self, file_path: Path) -> JSONMetadata:
        """
        Load metadata from JSON file.

        Args:
            file_path: Path to JSON metadata file

        Returns:
            Loaded metadata

        Raises:
            ValidationError: If loading or validation fails
        """
        self.metadata = self.loader.load_from_file(file_path)

        # Validate relationships and foreign keys
        rel_errors = self.loader.validate_relationships()
        if rel_errors:
            console.print("[yellow]⚠ Relationship validation warnings:[/yellow]")
            for error in rel_errors[:5]:  # Show first 5
                console.print(f"  • {error}")
            if len(rel_errors) > 5:
                console.print(f"  ... and {len(rel_errors) - 5} more")

        fk_errors = self.loader.validate_foreign_keys()
        if fk_errors:
            console.print("[yellow]⚠ Foreign key validation warnings:[/yellow]")
            for error in fk_errors[:5]:
                console.print(f"  • {error}")
            if len(fk_errors) > 5:
                console.print(f"  ... and {len(fk_errors) - 5} more")

        # Show summary
        summary = self.loader.get_summary()
        console.print("\n[bold]Metadata Summary:[/bold]")
        console.print(f"  • App: {summary['app_name']} v{summary['version']}")
        console.print(f"  • Entities: {summary['total_entities']}")
        console.print(f"  • Fields: {summary['total_fields']}")
        console.print(f"  • Relationships: {summary['total_relationships']}")
        console.print(f"  • Backend: {summary['backend_framework']}")
        console.print(f"  • Database: {summary['database_engine']}")

        return self.metadata

    async def analyze_all(self, use_ai: bool = True) -> Dict[str, EntityAnalysis]:
        """
        Analyze all entities from loaded metadata.

        Args:
            use_ai: Use AI for enhanced analysis

        Returns:
            Dictionary mapping entity names to EntityAnalysis objects

        Raises:
            ValidationError: If no metadata is loaded
        """
        if not self.metadata:
            raise ValidationError("No metadata loaded. Call load_metadata() first.")

        console.print("\n[bold cyan]Analyzing all entities...[/bold cyan]")

        # Convert all entities
        self.entity_analyses = self.converter.convert_metadata(self.metadata)

        # Cache entities
        for name, analysis in self.entity_analyses.items():
            self.analyzed_entities[name] = analysis.entity

        # AI enhancement (optional)
        if use_ai and self.ai_enabled and self.ai_system:
            console.print("\n[cyan]Running AI enhancement...[/cyan]")

            enhanced_count = 0
            for name, analysis in self.entity_analyses.items():
                try:
                    ai_analysis = await self.ai_system.analyze_entity(analysis.entity)

                    # Merge AI insights
                    analysis.unique_fields = ai_analysis.unique_fields
                    analysis.suggested_indexes = ai_analysis.suggested_indexes
                    analysis.immutable_fields = ai_analysis.immutable_fields
                    analysis.business_rules = ai_analysis.business_rules
                    analysis.security_considerations = ai_analysis.security_considerations

                    # Apply insights to entity
                    self._apply_ai_insights(analysis.entity, ai_analysis)

                    enhanced_count += 1
                except Exception as e:
                    console.print(f"[yellow]⚠ AI enhancement failed for {name}: {e}[/yellow]")

            console.print(f"[green]✓[/green] AI enhanced {enhanced_count}/{len(self.entity_analyses)} entities")

        console.print(f"\n[green]✓[/green] Analysis complete")
        return self.entity_analyses

    async def analyze_entity(
            self,
            entity_name: str,
            use_ai: bool = True
    ) -> EntityAnalysis:
        """
        Analyze a single entity.

        Args:
            entity_name: Name of entity to analyze
            use_ai: Use AI for enhanced analysis

        Returns:
            EntityAnalysis for the entity

        Raises:
            ValidationError: If entity not found or no metadata loaded
        """
        if not self.metadata:
            raise ValidationError("No metadata loaded. Call load_metadata() first.")

        # Get entity metadata
        entity_meta = self.loader.get_entity(entity_name)
        if not entity_meta:
            raise ValidationError(f"Entity '{entity_name}' not found in metadata")

        console.print(f"\n[bold cyan]Analyzing entity:[/bold cyan] {entity_name}")

        # Convert to SchemaEntity
        entity = self.converter._convert_entity(entity_meta)
        relationships = self.converter._convert_relationships(entity_meta, entity)
        entity.relationships = relationships

        # Create analysis
        analysis = EntityAnalysis(
            entity=entity,
            unique_fields=self.converter._extract_unique_fields(entity),
            suggested_indexes=self.converter._extract_indexes(entity),
            immutable_fields=self.converter._extract_immutable_fields(entity),
            business_rules=[],
            security_considerations=[],
        )

        # AI enhancement (optional)
        if use_ai and self.ai_enabled and self.ai_system:
            console.print(f"[cyan]Running AI analysis...[/cyan]")
            try:
                ai_analysis = await self.ai_system.analyze_entity(entity)

                # Merge AI insights
                analysis.unique_fields = ai_analysis.unique_fields
                analysis.suggested_indexes = ai_analysis.suggested_indexes
                analysis.immutable_fields = ai_analysis.immutable_fields
                analysis.business_rules = ai_analysis.business_rules
                analysis.security_considerations = ai_analysis.security_considerations

                self._apply_ai_insights(entity, ai_analysis)

                console.print(f"[green]✓[/green] AI analysis complete")
            except Exception as e:
                console.print(f"[yellow]⚠ AI enhancement failed: {e}[/yellow]")

        # Cache
        self.analyzed_entities[entity_name] = entity
        self.entity_analyses[entity_name] = analysis

        console.print(f"[green]✓[/green] Analysis complete for {entity_name}")
        console.print(f"  • Properties: {len(entity.properties)}")
        console.print(f"  • Relationships: {len(entity.relationships)}")
        console.print(f"  • Unique fields: {len(analysis.unique_fields)}")
        console.print(f"  • Indexed fields: {len(analysis.suggested_indexes)}")

        return analysis

    def _apply_ai_insights(
            self,
            entity: SchemaEntity,
            analysis: EntityAnalysis
    ) -> None:
        """
        Apply AI insights to entity.

        Args:
            entity: Entity to update
            analysis: AI analysis results
        """
        # Mark fields as required based on AI
        for field_name in analysis.entity.properties.keys():
            if field_name in getattr(analysis, '_required_fields', []):
                entity.properties[field_name].required = True

        # Store AI insights as metadata
        if not hasattr(entity, 'metadata'):
            entity.metadata = {}  # type: ignore

        entity.metadata.update({  # type: ignore
            "ai_enhanced": True,
            "ai_unique_fields": analysis.unique_fields,
            "ai_indexed_fields": analysis.suggested_indexes,
            "ai_immutable_fields": analysis.immutable_fields,
            "ai_business_rules": analysis.business_rules,
            "ai_security_notes": analysis.security_considerations,
        })

    def get_entity(self, name: str) -> Optional[SchemaEntity]:
        """
        Get analyzed entity by name.

        Args:
            name: Entity name

        Returns:
            SchemaEntity or None
        """
        return self.analyzed_entities.get(name)

    def get_analysis(self, name: str) -> Optional[EntityAnalysis]:
        """
        Get entity analysis by name.

        Args:
            name: Entity name

        Returns:
            EntityAnalysis or None
        """
        return self.entity_analyses.get(name)

    def get_all_entities(self) -> Dict[str, SchemaEntity]:
        """
        Get all analyzed entities.

        Returns:
            Dictionary of entities
        """
        return self.analyzed_entities.copy()

    def get_all_analyses(self) -> Dict[str, EntityAnalysis]:
        """
        Get all entity analyses.

        Returns:
            Dictionary of analyses
        """
        return self.entity_analyses.copy()

    def get_generation_config(self) -> Dict:
        """
        Get generation configuration from metadata.

        Returns:
            Generation options dictionary
        """
        if not self.metadata:
            return {}

        return {
            "app": self.metadata.app.dict(),
            "generation_options": self.metadata.generation_options or {},
            "ui_hints": self.metadata.ui_hints or {},
            "dto_policies": self.metadata.dto_policies or {},
            "client_behaviors": self.metadata.client_behaviors or {},
            "relationships_global": self.metadata.relationships_global or {},
        }

    def get_entity_hierarchy(self, entity_name: str) -> List[str]:
        """
        Get inheritance hierarchy for entity.

        Note: JSON metadata doesn't support inheritance, so this returns
        just the entity itself.

        Args:
            entity_name: Entity name

        Returns:
            List with single entity name
        """
        if entity_name in self.analyzed_entities:
            return [entity_name]
        return []

    def get_all_properties(self, entity: SchemaEntity) -> Dict:
        """
        Get all properties for entity.

        Note: JSON metadata doesn't support inheritance, so this returns
        just the entity's own properties.

        Args:
            entity: Entity

        Returns:
            Dictionary of properties
        """
        return entity.properties.copy()

    async def close(self) -> None:
        """Close resources."""
        if self.ai_system:
            await self.ai_system.close()
        self.converter.clear_cache()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


__all__ = ["JSONMetadataAnalyzer"]