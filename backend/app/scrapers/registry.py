"""Scraper registry for managing available scrapers."""
from typing import Dict, Type, List
import structlog

from app.scrapers.base import BaseScraper

logger = structlog.get_logger()


class ScraperRegistry:
    """Registry for managing scraper classes."""

    def __init__(self):
        """Initialize registry."""
        self._scrapers: Dict[str, Type[BaseScraper]] = {}

    def register(self, name: str, scraper_class: Type[BaseScraper]) -> None:
        """Register a scraper class."""
        self._scrapers[name] = scraper_class
        logger.info(f"Registered scraper: {name}")

    def get_scraper(self, name: str) -> Type[BaseScraper]:
        """Get scraper class by name."""
        if name not in self._scrapers:
            raise KeyError(f"Scraper '{name}' not found in registry")
        return self._scrapers[name]

    def list_scrapers(self) -> List[str]:
        """List all registered scraper names."""
        return list(self._scrapers.keys())

    def create_scraper(self, name: str, config: dict = None) -> BaseScraper:
        """Create scraper instance."""
        scraper_class = self.get_scraper(name)
        return scraper_class(config=config)


# Global registry instance
registry = ScraperRegistry()

# Import and register all scrapers
from app.scrapers.sources.nyc_passport import NYCPassportScraper
from app.scrapers.sources.nys_ogs import NYSOGSScraper
from app.scrapers.sources.port_authority import PortAuthorityScraper

registry.register("nyc_passport", NYCPassportScraper)
registry.register("nys_ogs", NYSOGSScraper)
registry.register("port_authority", PortAuthorityScraper)
