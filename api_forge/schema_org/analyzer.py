"""
Schema.org entity analyzer.

High-level orchestrator that combines fetching, parsing, type mapping,
relationship resolution, and validation extraction with AI enhancement.
"""

from typing import Dict, List, Optional
from pathlib import Path

from api_forge.schema_org.models import SchemaEntity, EntityAnalysis
from api_forge.schema_org.fetcher import SchemaOrgFetcher
from api_forge.schema_org.parser import SchemaOrgParser
from api_forge.schema_org.type_mapper import TypeMapper
from api_forge.schema_org.relationship_resolver import RelationshipResolver
from api_forge.schema_org.validation_extractor import ValidationExtractor
from api_forge.ai.agents import AgentSystem  # NEW
from api_forge.ai.config import AIConfig  # NEW
from api_forge.core.exceptions import SchemaOrgError
from api_forge.core.console import console


class SchemaOrgAnalyzer:
    """
    High-level Schema.org entity analyzer.

    Orchestrates all Schema.org integration components and uses AI
    to provide enhanced analysis and insights.
    """

    def __init__(self, cache_dir: Optional[Path] = None, ai_config: Optional[AIConfig] = None):
        """
        Initialize analyzer.

        Args:
            cache_dir: Directory for caching Schema.org definitions
            ai_config: AI configuration (optional, enables AI features)
        """
        self.fetcher = SchemaOrgFetcher(cache_dir)
        self.parser = SchemaOrgParser()
        self.type_mapper = TypeMapper()
        self.relationship_resolver = RelationshipResolver()
        self.validation_extractor = ValidationExtractor()

        # AI enhancement (optional)
        self.ai_enabled = ai_config and ai_config.is_configured
        if self.ai_enabled:
            self.ai_system = AgentSystem(ai_config)
            console.print("[dim]AI enhancement enabled[/dim]")
        else:
            self.ai_system = None

        self.analyzed_entities: Dict[str, SchemaEntity] = {}

    async def analyze_entity(
            self,
            entity_name: str,
            force_refresh: bool = False,
            use_ai: bool = True
    ) -> EntityAnalysis:
        """
        Analyze a single Schema.org entity with optional AI enhancement.

        Args:
            entity_name: Name of the Schema.org entity
            force_refresh: Force refresh from schema.org
            use_ai: Use AI for enhanced analysis

        Returns:
            EntityAnalysis with AI insights (if enabled)

        Raises:
            SchemaOrgError: If analysis fails
        """
        console.print(f"\n[bold cyan]Analyzing Schema.org entity:[/bold cyan] {entity_name}")

        # Fetch JSONLD definition
        jsonld_data = await self.fetcher.fetch_entity(entity_name, force_refresh)

        # Parse into SchemaEntity
        entity = self.parser.parse(jsonld_data)

        # Map types for all properties
        for property_name, property in entity.properties.items():
            type_info = self.type_mapper.resolve_type(property)
            # Store type info in property for later use
            property.type_info = type_info  # type: ignore

        # Resolve relationships
        relationships = self.relationship_resolver.resolve_all_relationships(
            entity,
            self.analyzed_entities
        )
        entity.relationships = relationships

        # Extract validation rules
        validations = self.validation_extractor.extract_all_validations(entity)
        entity.validation_rules = validations

        # Store for reference
        self.analyzed_entities[entity_name] = entity

        console.print(f"[green]✓[/green] Analysis complete for {entity_name}")
        console.print(f"  • Properties: {len(entity.properties)}")
        console.print(f"  • Relationships: {len(entity.relationships)}")
        console.print(f"  • Validations: {sum(len(rules) for rules in validations.values())}")

        # AI-enhanced analysis (optional)
        if use_ai and self.ai_enabled and self.ai_system:
            console.print(f"\n[cyan]Running AI analysis...[/cyan]")
            analysis = await self.ai_system.analyze_entity(entity)

            # Apply AI insights to entity
            self._apply_ai_insights(entity, analysis)

            console.print(f"[green]✓[/green] AI analysis complete")
            console.print(f"  • Unique fields: {len(analysis.unique_fields)}")
            console.print(f"  • Indexed fields: {len(analysis.suggested_indexes)}")
            console.print(f"  • Business rules: {len(analysis.business_rules)}")

            return analysis
        else:
            # Return basic analysis without AI
            return EntityAnalysis(entity=entity)

    def _apply_ai_insights(
            self,
            entity: SchemaEntity,
            analysis: EntityAnalysis
    ) -> None:
        """
        Apply AI insights to entity.

        Updates entity properties based on AI recommendations.

        Args:
            entity: Entity to update
            analysis: AI analysis results
        """
        # Mark fields as required based on AI analysis
        for field_name in analysis.entity.properties.keys():
            if field_name in getattr(analysis, '_required_fields', []):
                entity.properties[field_name].required = True

        # Store AI insights as metadata
        entity.metadata = {  # type: ignore
            "ai_enhanced": True,
            "unique_fields": analysis.unique_fields,
            "indexed_fields": analysis.suggested_indexes,
            "immutable_fields": analysis.immutable_fields,
            "business_rules": analysis.business_rules,
            "security_notes": analysis.security_considerations,
        }

    async def analyze_multiple(
            self,
            entity_names: List[str],
            force_refresh: bool = False,
            use_ai: bool = True
    ) -> Dict[str, EntityAnalysis]:
        """
        Analyze multiple Schema.org entities.

        Args:
            entity_names: List of entity names to analyze
            force_refresh: Force refresh from schema.org
            use_ai: Use AI for enhanced analysis

        Returns:
            Dictionary mapping entity names to analyzed entities
        """
        results = {}

        for entity_name in entity_names:
            try:
                analysis = await self.analyze_entity(entity_name, force_refresh, use_ai)
                results[entity_name] = analysis
            except SchemaOrgError as e:
                console.print(f"[red]✗[/red] Failed to analyze {entity_name}: {e.message}")
                continue

        # Second pass: validate relationships now that we have all entities
        entities = {name: analysis.entity for name, analysis in results.items()}
        self._validate_all_relationships(entities)

        return results

    def _validate_all_relationships(self, entities: Dict[str, SchemaEntity]) -> None:
        """
        Validate all relationships between entities.

        Args:
            entities: Dictionary of all analyzed entities
        """
        for entity_name, entity in entities.items():
            valid_relationships = []

            for relationship in entity.relationships:
                if self.relationship_resolver.validate_relationship(
                        relationship,
                        entity,
                        entities
                ):
                    valid_relationships.append(relationship)

            entity.relationships = valid_relationships

    async def get_entity_hierarchy(self, entity_name: str) -> List[str]:
        """
        Get the inheritance hierarchy for an entity.

        Args:
            entity_name: Name of the entity

        Returns:
            List of entity names in inheritance order (parent to child)
        """
        analysis = await self.analyze_entity(entity_name)
        entity = analysis.entity

        hierarchy = []
        current = entity

        # Walk up the parent chain
        while current.parent_types:
            parent_name = current.parent_types[0]  # Take first parent
            hierarchy.insert(0, parent_name)

            # Fetch parent entity
            try:
                parent_analysis = await self.analyze_entity(parent_name)
                current = parent_analysis.entity
            except SchemaOrgError:
                break

        hierarchy.append(entity_name)
        return hierarchy

    def get_all_properties(self, entity: SchemaEntity) -> Dict[str, any]:
        """
        Get all properties including inherited ones.

        Args:
            entity: Entity to get properties for

        Returns:
            Dictionary of all properties (own + inherited)
        """
        all_properties = {}

        # Add inherited properties (if parents are analyzed)
        for parent_name in entity.parent_types:
            if parent_name in self.analyzed_entities:
                parent = self.analyzed_entities[parent_name]
                all_properties.update(parent.properties)

        # Add own properties (overrides inherited)
        all_properties.update(entity.properties)

        return all_properties

    async def close(self) -> None:
        """Close resources."""
        await self.fetcher.close()
        if self.ai_system:
            await self.ai_system.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    __all__ = ["SchemaOrgAnalyzer"]