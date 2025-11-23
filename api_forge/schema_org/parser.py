"""
Schema.org JSONLD parser.

Parses JSONLD definitions into structured SchemaEntity objects.
"""

from typing import Dict, Any, List, Optional

from api_forge.schema_org.models import SchemaEntity, SchemaProperty
from api_forge.core.exceptions import SchemaOrgError
from api_forge.core.console import console


class SchemaOrgParser:
    """
    Parses Schema.org JSONLD definitions.

    Converts JSONLD format into structured SchemaEntity objects
    that can be used for code generation.
    """

    def __init__(self):
        """Initialize parser."""
        pass

    def parse(self, jsonld_data: Dict[str, Any]) -> SchemaEntity:
        """
        Parse JSONLD data into SchemaEntity.

        Args:
            jsonld_data: JSONLD data from Schema.org containing:
                - entity: The class definition
                - properties: List of properties for this entity
                - @graph: Full graph for additional lookups

        Returns:
            Parsed SchemaEntity object

        Raises:
            SchemaOrgError: If parsing fails
        """
        try:
            # Extract entity and properties
            entity_data = jsonld_data.get("entity")
            property_list = jsonld_data.get("properties", [])
            graph = jsonld_data.get("@graph", [])

            if not entity_data:
                raise SchemaOrgError("Could not find entity in JSONLD data")

            # Parse basic entity info
            entity_name = self._extract_name(entity_data)
            entity_url = self._extract_url(entity_data)
            description = self._extract_description(entity_data)

            # Parse inheritance
            parent_types = self._extract_parent_types(entity_data)
            sub_types = self._extract_sub_types(entity_data)

            # Create entity
            entity = SchemaEntity(
                name=entity_name,
                url=entity_url,
                description=description,
                parent_types=parent_types,
                sub_types=sub_types
            )

            # Parse properties from the pre-filtered list
            properties = []
            for prop_data in property_list:
                prop = self._parse_property(prop_data)
                if prop:
                    properties.append(prop)

            entity.properties = {prop.name: prop for prop in properties}

            console.print(f"[green]✓[/green] Parsed {entity_name} with {len(properties)} properties")

            return entity

        except Exception as e:
            raise SchemaOrgError(
                f"Failed to parse JSONLD data: {e}",
                details={"error": str(e)}
            )

    def _extract_entity_data(self, jsonld_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract the main entity definition from JSONLD."""
        # Check if data has @graph (list of definitions)
        if "@graph" in jsonld_data:
            graph = jsonld_data["@graph"]
            # Find the main entity (type should be rdfs:Class)
            for item in graph:
                if item.get("@type") == "rdfs:Class":
                    # Skip deprecated entities
                    if "schema:supersededBy" not in item:
                        return item

        # Single entity format
        elif "@type" in jsonld_data:
            return jsonld_data

        return None

    def _extract_name(self, entity_data: Dict[str, Any]) -> str:
        """Extract entity name."""
        # Try @id first
        entity_id = entity_data.get("@id", "")
        if entity_id.startswith("schema:"):
            return entity_id.replace("schema:", "")

        # Try rdfs:label
        label = entity_data.get("rdfs:label", "")
        if label:
            return label

        # Fallback to empty string (will cause error)
        return ""

    def _extract_url(self, entity_data: Dict[str, Any]) -> str:
        """Extract entity URL."""
        entity_id = entity_data.get("@id", "")
        if entity_id.startswith("schema:"):
            name = entity_id.replace("schema:", "")
            return f"https://schema.org/{name}"
        return entity_id

    def _extract_description(self, entity_data: Dict[str, Any]) -> str:
        """Extract entity description."""
        comment = entity_data.get("rdfs:comment", "")
        if comment:
            return comment

        # Try schema:description
        description = entity_data.get("schema:description", "")
        return description

    def _extract_parent_types(self, entity_data: Dict[str, Any]) -> List[str]:
        """Extract parent types (inheritance)."""
        parents = []

        subclass_of = entity_data.get("rdfs:subClassOf", [])
        if not isinstance(subclass_of, list):
            subclass_of = [subclass_of]

        for parent in subclass_of:
            if isinstance(parent, dict):
                parent_id = parent.get("@id", "")
            else:
                parent_id = parent

            if parent_id.startswith("schema:"):
                parents.append(parent_id.replace("schema:", ""))

        return parents

    def _extract_sub_types(self, entity_data: Dict[str, Any]) -> List[str]:
        """Extract sub types (children)."""
        # This would require parsing the full graph
        # For now, return empty list
        return []
    '''
    def _parse_properties(
            self,
            jsonld_data: Dict[str, Any],
            entity_name: str
    ) -> List[SchemaProperty]:
        """
        Parse properties for an entity.

        Properties are defined separately in the @graph with schema:domainIncludes
        """
        properties = []

        if "@graph" not in jsonld_data:
            return properties

        graph = jsonld_data["@graph"]

        for item in graph:
            # Look for properties (type rdf:Property)
            if item.get("@type") not in ["rdf:Property", "schema:Property"]:
                continue

            # Check if this property applies to our entity
            domain_includes = item.get("schema:domainIncludes", [])
            if not isinstance(domain_includes, list):
                domain_includes = [domain_includes]

            # Check if our entity is in the domain
            applies_to_entity = False
            for domain in domain_includes:
                if isinstance(domain, dict):
                    domain_id = domain.get("@id", "")
                else:
                    domain_id = domain

                if domain_id == f"schema:{entity_name}":
                    applies_to_entity = True
                    break

            if not applies_to_entity:
                continue

            # Parse property
            prop = self._parse_property(item)
            if prop:
                properties.append(prop)

        return properties
    '''

    def _parse_property(self, property_data: Dict[str, Any]) -> Optional[SchemaProperty]:
        """
        Parse a single property definition.

        Args:
            property_data: Property node from Schema.org graph

        Returns:
            SchemaProperty object or None if parsing fails
        """
        # Extract property name
        prop_id = property_data.get("@id", "")
        if not prop_id.startswith("schema:"):
            return None

        name = prop_id.replace("schema:", "")

        # Extract description
        description = property_data.get("rdfs:comment", "")
        if isinstance(description, dict):
            description = description.get("@value", "")

        # Extract range (expected types)
        range_includes = property_data.get("schema:rangeIncludes", [])
        if not isinstance(range_includes, list):
            range_includes = [range_includes]

        expected_types = []
        for range_item in range_includes:
            if isinstance(range_item, dict):
                type_id = range_item.get("@id", "")
            else:
                type_id = str(range_item)

            if type_id.startswith("schema:"):
                expected_types.append(type_id.replace("schema:", ""))

        # Extract domain (which entities this property belongs to)
        domain_includes = property_data.get("schema:domainIncludes", [])
        if not isinstance(domain_includes, list):
            domain_includes = [domain_includes]

        domain_list = []
        for domain in domain_includes:
            if isinstance(domain, dict):
                domain_id = domain.get("@id", "")
            else:
                domain_id = str(domain)

            if domain_id.startswith("schema:"):
                domain_list.append(domain_id.replace("schema:", ""))

        return SchemaProperty(
            name=name,
            description=description,
            expected_types=expected_types,
            domain_includes=domain_list,
            range_includes=expected_types,
            required=False,  # Schema.org doesn't specify required
            multiple=False,  # Will be determined by type mapper
        )


__all__ = ["SchemaOrgParser"]