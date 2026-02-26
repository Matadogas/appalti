"""Test scraper registry."""
import pytest
from app.scrapers.registry import ScraperRegistry
from app.scrapers.base import BaseScraper


class TestScraperRegistry:
    """Test scraper registry."""

    def test_register_scraper(self):
        """Test registering a scraper."""
        registry = ScraperRegistry()

        class TestScraper(BaseScraper):
            def get_source_name(self) -> str:
                return "test_source"

            async def scrape(self):
                return []

        registry.register("test_source", TestScraper)
        assert "test_source" in registry.list_scrapers()

    def test_get_scraper(self):
        """Test retrieving a scraper."""
        registry = ScraperRegistry()

        class TestScraper(BaseScraper):
            def get_source_name(self) -> str:
                return "test_source"

            async def scrape(self):
                return []

        registry.register("test_source", TestScraper)
        scraper_class = registry.get_scraper("test_source")
        assert scraper_class == TestScraper

    def test_get_nonexistent_scraper(self):
        """Test getting scraper that doesn't exist."""
        registry = ScraperRegistry()
        with pytest.raises(KeyError):
            registry.get_scraper("nonexistent")
