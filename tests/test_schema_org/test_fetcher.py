"""
Unit tests for SchemaOrgFetcher.
"""

import pytest
from pathlib import Path
import tempfile
import json

from api_forge.schema_org.fetcher import SchemaOrgFetcher
from api_forge.core.exceptions import SchemaOrgError


class TestSchemaOrgFetcher:
    """Test SchemaOrgFetcher functionality."""

    @pytest.fixture
    async def fetcher(self):
        """Create fetcher with temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fetcher = SchemaOrgFetcher(cache_dir=Path(tmpdir))
            yield fetcher
            await fetcher.close()

    @pytest.mark.asyncio
    async def test_fetch_person_entity(self, fetcher):
        """Test fetching Person entity."""
        data = await fetcher.fetch_entity("Person")

        assert data is not None
        assert "@context" in data
        assert "@graph" in data or "@type" in data

    @pytest.mark.asyncio
    async def test_fetch_invalid_entity(self, fetcher):
        """Test fetching non-existent entity."""
        with pytest.raises(SchemaOrgError) as exc_info:
            await fetcher.fetch_entity("NonExistentEntity12345")

        assert "not found" in str(exc_info.value.message).lower()

    @pytest.mark.asyncio
    async def test_cache_usage(self, fetcher):
        """Test that cache is used on second fetch."""
        # First fetch (from network)
        data1 = await fetcher.fetch_entity("Organization")

        # Second fetch (from cache)
        data2 = await fetcher.fetch_entity("Organization")

        assert data1 == data2

        # Check cache file exists
        cache_file = fetcher.cache_dir / "Organization.json"
        assert cache_file.exists()

    @pytest.mark.asyncio
    async def test_force_refresh(self, fetcher):
        """Test force refresh bypasses cache."""
        # First fetch
        await fetcher.fetch_entity("Thing")

        # Second fetch with force_refresh
        data = await fetcher.fetch_entity("Thing", force_refresh=True)

        assert data is not None

    @pytest.mark.asyncio
    async def test_clear_cache(self, fetcher):
        """Test clearing cache."""
        # Fetch and cache entity
        await fetcher.fetch_entity("Person")

        cache_file = fetcher.cache_dir / "Person.json"
        assert cache_file.exists()

        # Clear cache
        fetcher.clear_cache("Person")

        assert not cache_file.exists()
