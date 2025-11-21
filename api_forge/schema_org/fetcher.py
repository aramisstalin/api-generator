"""
Schema.org definition fetcher.

Downloads and caches Schema.org entity definitions in JSONLD format.
"""

import httpx
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from api_forge.core.exceptions import SchemaOrgError
from api_forge.core.console import console


class SchemaOrgFetcher:
    """
    Fetches Schema.org entity definitions.

    Downloads JSONLD definitions from schema.org and caches them locally
    to avoid repeated network requests.
    """

    BASE_URL = "https://schema.org"
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

    async def fetch_entity(self, entity_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetch Schema.org entity definition.

        Args:
            entity_name: Name of the Schema.org entity (e.g., "Person", "Organization")
            force_refresh: Force refresh from schema.org, ignoring cache

        Returns:
            Dictionary containing the JSONLD definition

        Raises:
            SchemaOrgError: If entity cannot be fetched
        """
        # Check cache first
        if not force_refresh:
            cached = self._get_from_cache(entity_name)
            if cached:
                console.print(f"[dim]Using cached definition for {entity_name}[/dim]")
                return cached

        # Fetch from schema.org
        console.print(f"[cyan]Fetching {entity_name} from Schema.org...[/cyan]")

        try:
            url = urljoin(self.BASE_URL, f"{entity_name}.jsonld")
            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()

            # Validate JSONLD structure
            if not self._validate_jsonld(data):
                raise SchemaOrgError(
                    f"Invalid JSONLD structure for {entity_name}",
                    details={"url": url}
                )

            # Save to cache
            self._save_to_cache(entity_name, data)

            console.print(f"[green]✓[/green] Successfully fetched {entity_name}")
            return data

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise SchemaOrgError(
                    f"Entity '{entity_name}' not found in Schema.org",
                    details={"status_code": 404, "url": str(e.request.url)}
                )
            raise SchemaOrgError(
                f"HTTP error fetching {entity_name}: {e}",
                details={"status_code": e.response.status_code}
            )

        except httpx.RequestError as e:
            raise SchemaOrgError(
                f"Network error fetching {entity_name}: {e}",
                details={"error": str(e)}
            )

        except json.JSONDecodeError as e:
            raise SchemaOrgError(
                f"Invalid JSON in response for {entity_name}: {e}",
                details={"error": str(e)}
            )

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

            if datetime.utcnow() - cached_time > self.CACHE_TTL:
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
                "cached_at": datetime.utcnow().isoformat(),
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