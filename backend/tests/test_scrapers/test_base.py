"""Test base scraper."""
import pytest
from app.scrapers.base import BaseScraper
from app.schemas.tender import TenderCreate


class TestBaseScraper:
    """Test BaseScraper interface."""

    def test_base_scraper_is_abstract(self):
        """Test that BaseScraper cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseScraper()

    def test_subclass_must_implement_scrape(self):
        """Test that subclasses must implement scrape method."""

        class IncompleteScraper(BaseScraper):
            def get_source_name(self) -> str:
                return "Test"

        with pytest.raises(TypeError):
            IncompleteScraper()
