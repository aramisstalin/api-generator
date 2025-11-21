"""
Relationship resolver for Schema.org entities.

Analyzes Schema.org properties to determine relationship types and configurations.
"""

from typing import List, Dict, Optional
from api_forge.schema_org.models import (
    SchemaEntity,
    SchemaProperty,
    RelationshipInfo,
    RelationshipType
)
from api_forge.core.console import console


class RelationshipResolver:
    """
    Resolves relationships between Schema.org entities.

    Analyzes properties to determine:
    - Foreign key relationships (many-to-one)
    - Many-to-many relationships
    - One-to-one relationships
    """

    # Properties that typically indicate one-to-many relationships
    COLLECTION_INDICATORS = [
        "s",  # Plural ending
        "list",
        "collection",
        "set",
    ]

    # Properties that typically indicate one-to-one
    ONE_TO_ONE_INDICATORS = [
        "primary",
        "main",
        "current",
        "active",
    ]

    def __init__(self):
        """Initialize resolver."""
        pass

    def analyze_property(
            self,
            property: SchemaProperty,
            entity: SchemaEntity,
            all_entities: Optional[Dict[str, SchemaEntity]] = None
    ) -> Optional[RelationshipInfo]:
        """
        Analyze a property to determine if it represents a relationship.

        Args:
            property: Property to analyze
            entity: Entity containing this property
            all_entities: Dictionary of all known entities (for validation)

        Returns:
            RelationshipInfo if property is a relationship, None otherwise
        """
        # Only process entity-type properties
        if not property.is_relationship:
            return None

        # Get target entity types
        target_entities = [
            t for t in property.expected_types
            if t not in ["Thing", "DataType"]  # Skip generic types
        ]

        if not target_entities:
            return None

        # Determine relationship type based on property name and cardinality
        relationship_type = self._determine_relationship_type(
            property.name,
            target_entities,
            property.multiple
        )

        if relationship_type == RelationshipType.MANY_TO_ONE:
            # Standard foreign key relationship
            return RelationshipInfo(
                type=relationship_type,
                target_entity=target_entities[0],
                property_name=property.name,
                foreign_key=f"{property.name}_id",
                back_populates=f"{entity.name.lower()}s",
                cascade="all, delete-orphan"
            )

        elif relationship_type == RelationshipType.MANY_TO_MANY:
            # Many-to-many with association table
            association_table = self._generate_association_table_name(
                entity.name,
                property.name
            )

            return RelationshipInfo(
                type=relationship_type,
                target_entity=target_entities[0],
                property_name=property.name,
                association_table=association_table,
                back_populates=f"{entity.name.lower()}s"
            )

        elif relationship_type == RelationshipType.ONE_TO_ONE:
            # One-to-one relationship
            return RelationshipInfo(
                type=relationship_type,
                target_entity=target_entities[0],
                property_name=property.name,
                foreign_key=f"{property.name}_id",
                back_populates=entity.name.lower()
            )

        return None

    def _determine_relationship_type(
            self,
            property_name: str,
            target_entities: List[str],
            multiple: bool
    ) -> RelationshipType:
        """
        Determine the type of relationship based on property characteristics.

        Args:
            property_name: Name of the property
            target_entities: List of target entity types
            multiple: Whether property can have multiple values

        Returns:
            RelationshipType enum value
        """
        lower_name = property_name.lower()

        # Check for explicit multiple values
        if multiple:
            return RelationshipType.MANY_TO_MANY

        # Check for plural form (likely collection)
        if property_name.endswith('s') or property_name.endswith('es'):
            return RelationshipType.MANY_TO_MANY

        # Check for collection indicators
        if any(indicator in lower_name for indicator in self.COLLECTION_INDICATORS):
            return RelationshipType.MANY_TO_MANY

        # Check for one-to-one indicators
        if any(indicator in lower_name for indicator in self.ONE_TO_ONE_INDICATORS):
            return RelationshipType.ONE_TO_ONE

        # Default to many-to-one (most common)
        return RelationshipType.MANY_TO_ONE

    def _generate_association_table_name(
            self,
            entity_name: str,
            property_name: str
    ) -> str:
        """
        Generate association table name for many-to-many relationships.

        Args:
            entity_name: Source entity name
            property_name: Property name

        Returns:
            Association table name
        """
        # Format: entity_property (e.g., person_memberships)
        return f"{entity_name.lower()}_{property_name.lower()}"

    def resolve_all_relationships(
            self,
            entity: SchemaEntity,
            all_entities: Optional[Dict[str, SchemaEntity]] = None
    ) -> List[RelationshipInfo]:
        """
        Resolve all relationships for an entity.

        Args:
            entity: Entity to analyze
            all_entities: Dictionary of all known entities

        Returns:
            List of resolved relationships
        """
        relationships = []

        for property in entity.properties.values():
            relationship = self.analyze_property(property, entity, all_entities)
            if relationship:
                relationships.append(relationship)

        return relationships

    def validate_relationship(
            self,
            relationship: RelationshipInfo,
            source_entity: SchemaEntity,
            all_entities: Dict[str, SchemaEntity]
    ) -> bool:
        """
        Validate that a relationship is valid.

        Args:
            relationship: Relationship to validate
            source_entity: Source entity
            all_entities: All known entities

        Returns:
            True if valid, False otherwise
        """
        # Check if target entity exists
        if relationship.target_entity not in all_entities:
            console.print(
                f"[yellow]⚠[/yellow] Target entity '{relationship.target_entity}' "
                f"not found for relationship in {source_entity.name}"
            )
            return False

        return True

    def generate_back_reference_name(
            self,
            source_entity: str,
            relationship_type: RelationshipType
    ) -> str:
        """
        Generate appropriate back reference name.

        Args:
            source_entity: Name of source entity
            relationship_type: Type of relationship

        Returns:
            Back reference name
        """
        base_name = source_entity.lower()

        if relationship_type in [RelationshipType.MANY_TO_MANY, RelationshipType.ONE_TO_MANY]:
            # Pluralize for collections
            return f"{base_name}s"
        else:
            # Singular for one-to-one or many-to-one (from target perspective)
            return base_name


__all__ = ["RelationshipResolver"]