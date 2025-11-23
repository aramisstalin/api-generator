"""
Analyzer factory.

Creates appropriate analyzer based on input source (Schema.org or JSON).
"""

from typing import Union, Optional
from pathlib import Path
from enum import Enum

from api_forge.schema_org.analyzer import SchemaOrgAnalyzer
from api_forge.json_metadata.analyzer import JSONMetadataAnalyzer
from api_forge.ai.config import AIConfig
from api_forge.core.console import console


class AnalyzerType(Enum):
    """Type of analyzer to create."""
    SCHEMA_ORG = "schema_org"
    JSON_METADATA = "json_metadata"
    AUTO = "auto"


class AnalyzerFactory:
    """
    Factory for creating appropriate analyzer based on input source.

    Simplifies analyzer creation and provides unified interface.
    """

    @staticmethod
    def create(
            source: Optional[Union[str, Path]] = None,
            analyzer_type: AnalyzerType = AnalyzerType.AUTO,
            cache_dir: Optional[Path] = None,
            ai_config: Optional[AIConfig] = None,
    ) -> Union[SchemaOrgAnalyzer, JSONMetadataAnalyzer]:
        """
        Create appropriate analyzer.

        Args:
            source: Source file path (for JSON) or None (for Schema.org)
            analyzer_type: Type of analyzer to create (AUTO detects from source)
            cache_dir: Cache directory for Schema.org fetcher
            ai_config: AI configuration

        Returns:
            Configured analyzer instance

        Examples:
            # Schema.org analyzer
            analyzer = AnalyzerFactory.create()

            # JSON metadata analyzer (explicit)
            analyzer = AnalyzerFactory.create(
                source="metadata.json",
                analyzer_type=AnalyzerType.JSON_METADATA
            )

            # Auto-detect from file extension
            analyzer = AnalyzerFactory.create(source="metadata.json")
        """
        # Auto-detect analyzer type
        if analyzer_type == AnalyzerType.AUTO:
            if source is None:
                analyzer_type = AnalyzerType.SCHEMA_ORG
            else:
                source_path = Path(source) if isinstance(source, str) else source
                if source_path.suffix.lower() == '.json':
                    analyzer_type = AnalyzerType.JSON_METADATA
                else:
                    analyzer_type = AnalyzerType.SCHEMA_ORG

        # Create analyzer
        if analyzer_type == AnalyzerType.JSON_METADATA:
            console.print("[bold]Creating JSON metadata analyzer[/bold]")

            metadata_file = Path(source) if source else None
            return JSONMetadataAnalyzer(
                metadata_file=metadata_file,
                ai_config=ai_config
            )

        else:  # SCHEMA_ORG
            console.print("[bold]Creating Schema.org analyzer[/bold]")

            return SchemaOrgAnalyzer(
                cache_dir=cache_dir,
                ai_config=ai_config
            )

    @staticmethod
    def create_schema_org(
            cache_dir: Optional[Path] = None,
            ai_config: Optional[AIConfig] = None,
    ) -> SchemaOrgAnalyzer:
        """
        Create Schema.org analyzer (explicit).

        Args:
            cache_dir: Cache directory
            ai_config: AI configuration

        Returns:
            SchemaOrgAnalyzer instance
        """
        console.print("[bold]Creating Schema.org analyzer[/bold]")
        return SchemaOrgAnalyzer(cache_dir=cache_dir, ai_config=ai_config)

    @staticmethod
    def create_json_metadata(
            metadata_file: Optional[Path] = None,
            ai_config: Optional[AIConfig] = None,
    ) -> JSONMetadataAnalyzer:
        """
        Create JSON metadata analyzer (explicit).

        Args:
            metadata_file: Path to JSON metadata file
            ai_config: AI configuration

        Returns:
            JSONMetadataAnalyzer instance
        """
        console.print("[bold]Creating JSON metadata analyzer[/bold]")
        return JSONMetadataAnalyzer(
            metadata_file=metadata_file,
            ai_config=ai_config
        )


__all__ = ["AnalyzerFactory", "AnalyzerType"]