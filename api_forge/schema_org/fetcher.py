"""
Schema.org definition fetcher.

Downloads and caches Schema.org entity definitions in JSONLD format.
"""

import httpx
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from black import timezone

from api_forge.core.exceptions import SchemaOrgError
from api_forge.core.console import console


class SchemaOrgFetcher:
    """
    Fetches Schema.org entity definitions.

    Downloads the complete Schema.org vocabulary and extracts entities.
    Caches the vocabulary locally to avoid repeated network requests.
    """

    VOCAB_URL = "https://schema.org/version/latest/schemaorg-all-https.jsonld"
    CACHE_TTL = timedelta(days=7)

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize fetcher.

        Args:
            cache_dir: Directory for caching definitions (default: .schema_cache)
        """
        self.cache_dir = cache_dir or Path.cwd() / ".schema_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "Accept": "application/ld+json",
                "User-Agent": "API-Forge/0.1.0"
            }
        )

        # Vocabulary cache
        self._vocabulary: Optional[Dict[str, Any]] = None

    async def _load_vocabulary(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Load the complete Schema.org vocabulary."""
        if self._vocabulary and not force_refresh:
            return self._vocabulary

        cache_file = self.cache_dir / "schemaorg-vocabulary.json"
        metadata_file = self.cache_dir / "schemaorg-vocabulary.meta"

        # Check cache
        if not force_refresh and cache_file.exists() and metadata_file.exists():
            try:
                metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
                cached_time = datetime.fromisoformat(metadata["cached_at"])

                if datetime.now(timezone.utc) - cached_time <= self.CACHE_TTL:
                    console.print("[dim]Using cached Schema.org vocabulary[/dim]")
                    self._vocabulary = json.loads(cache_file.read_text(encoding="utf-8"))
                    return self._vocabulary
            except Exception:
                pass

        # Download vocabulary
        console.print("[cyan]Downloading Schema.org vocabulary...[/cyan]")

        try:
            response = await self.client.get(self.VOCAB_URL)
            response.raise_for_status()

            self._vocabulary = response.json()

            # Save to cache
            cache_file.write_text(
                json.dumps(self._vocabulary, indent=2),
                encoding="utf-8"
            )

            metadata = {
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "url": self.VOCAB_URL
            }
            metadata_file.write_text(
                json.dumps(metadata, indent=2),
                encoding="utf-8"
            )

            console.print("[green]✓[/green] Schema.org vocabulary downloaded")
            return self._vocabulary

        except Exception as e:
            raise SchemaOrgError(
                f"Failed to download Schema.org vocabulary: {e}",
                details={"url": self.VOCAB_URL, "error": str(e)}
            )

    async def fetch_entity(self, entity_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch Schema.org entity definition with its properties from vocabulary.

        Args:
            entity_name: Name of the Schema.org entity (e.g., "Person", "Organization")
            force_refresh: Force refresh vocabulary from schema.org

        Returns:
            Dictionary containing:
            - @context: Schema.org context
            - @graph: Full graph (for property resolution)
            - entity: The class definition
            - properties: List of properties that apply to this entity

        Raises:
            SchemaOrgError: If entity cannot be found
        """
        # Load vocabulary
        vocab = await self._load_vocabulary(force_refresh)

        # Extract @graph
        if "@graph" not in vocab:
            raise SchemaOrgError(
                "Invalid Schema.org vocabulary structure",
                details={"missing": "@graph"}
            )

        graph = vocab["@graph"]

        # Find entity class in graph
        entity_id = f"schema:{entity_name}"
        entity_data = None

        for item in graph:
            if item.get("@id") == entity_id and item.get("@type") == "rdfs:Class":
                entity_data = item
                break

        if not entity_data:
            raise SchemaOrgError(
                f"Entity '{entity_name}' not found in Schema.org vocabulary",
                details={"entity_id": entity_id}
            )

        # Find all properties that apply to this entity
        entity_properties = []

        for item in graph:
            # Look for properties
            item_type = item.get("@type")
            if item_type not in ["rdf:Property", "schema:Property"]:
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
                    domain_id = str(domain)

                if domain_id == entity_id:
                    applies_to_entity = True
                    break

            if applies_to_entity:
                entity_properties.append(item)

        console.print(f"[green]✓[/green] Found {entity_name} with {len(entity_properties)} properties")

        # Return entity with its properties and full graph for reference
        return {
            "@context": vocab.get("@context", {}),
            "@graph": graph,
            "entity": entity_data,
            "properties": entity_properties
        }

    async def fetch_multiple(self, entity_names: list[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch multiple entity definitions.

        Args:
            entity_names: List of entity names to fetch

        Returns:
            Dictionary mapping entity names to their definitions
        """
        results = {}

        for entity_name in entity_names:
            try:
                results[entity_name] = await self.fetch_entity(entity_name)
            except SchemaOrgError as e:
                console.print(f"[red]✗[/red] Failed to fetch {entity_name}: {e.message}")
                # Continue with other entities
                continue

        return results

    def _get_from_cache(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """Get entity definition from cache if not expired."""
        cache_file = self.cache_dir / f"{entity_name}.json"
        metadata_file = self.cache_dir / f"{entity_name}.meta"

        if not cache_file.exists() or not metadata_file.exists():
            return None

        # Check if cache is expired
        try:
            metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
            cached_time = datetime.fromisoformat(metadata["cached_at"])

            if datetime.now(timezone.utc) - cached_time > self.CACHE_TTL:
                # Cache expired
                return None

            # Load cached data
            return json.loads(cache_file.read_text(encoding="utf-8"))

        except Exception:
            # Invalid cache, ignore
            return None

    def _save_to_cache(self, entity_name: str, data: Dict[str, Any]) -> None:
        """Save entity definition to cache."""
        try:
            cache_file = self.cache_dir / f"{entity_name}.json"
            metadata_file = self.cache_dir / f"{entity_name}.meta"

            # Save data
            cache_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

            # Save metadata
            metadata = {
                "entity_name": entity_name,
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "ttl_days": self.CACHE_TTL.days
            }
            metadata_file.write_text(
                json.dumps(metadata, indent=2),
                encoding="utf-8"
            )

        except Exception as e:
            # Don't fail if cache save fails
            console.print(f"[yellow]⚠[/yellow] Failed to cache {entity_name}: {e}")

    def _validate_jsonld(self, data: Dict[str, Any]) -> bool:
        """
        Validate basic JSONLD structure.

        Args:
            data: JSONLD data to validate

        Returns:
            True if valid, False otherwise
        """
        # Check for required JSONLD fields
        if "@context" not in data:
            return False

        if "@graph" not in data and "@type" not in data:
            return False

        return True

    def clear_cache(self, entity_name: Optional[str] = None) -> None:
        """
        Clear cached definitions.

        Args:
            entity_name: Specific entity to clear, or None to clear all
        """
        if entity_name:
            # Clear specific entity
            cache_file = self.cache_dir / f"{entity_name}.json"
            metadata_file = self.cache_dir / f"{entity_name}.meta"

            cache_file.unlink(missing_ok=True)
            metadata_file.unlink(missing_ok=True)

            console.print(f"[green]✓[/green] Cleared cache for {entity_name}")
        else:
            # Clear all cache
            for file in self.cache_dir.glob("*.json"):
                file.unlink()
            for file in self.cache_dir.glob("*.meta"):
                file.unlink()

            console.print("[green]✓[/green] Cleared all Schema.org cache")

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


__all__ = ["SchemaOrgFetcher"]