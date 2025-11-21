"""
Schema.org integration layer.

This module provides functionality to fetch, parse, and process Schema.org
entity definitions for code generation.
"""

__all__ = [
    "SchemaOrgFetcher",
    "SchemaOrgParser",
    "TypeMapper",
    "RelationshipResolver",
    "ValidationExtractor",
    "SchemaEntity",
    "SchemaProperty",
]

from api_forge.schema_org.fetcher import SchemaOrgFetcher
from api_forge.schema_org.parser import SchemaOrgParser
from api_forge.schema_org.type_mapper import TypeMapper
from api_forge.schema_org.relationship_resolver import RelationshipResolver
from api_forge.schema_org.validation_extractor import ValidationExtractor
from api_forge.schema_org.models import SchemaEntity, SchemaProperty