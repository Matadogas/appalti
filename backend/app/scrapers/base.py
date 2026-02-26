"""Base scraper interface."""
from abc import ABC, abstractmethod
from typing import List, Optional
import hashlib
import structlog

from app.schemas.tender import TenderCreate

logger = structlog.get_logger()


class BaseScraper(ABC):
    """Base class for all scrapers.

    Each scraper must implement:
    - get_source_name(): Return the unique source name
    - scrape(): Execute scraping and return list of tenders
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize scraper with optional config."""
        self.config = config or {}
        self.logger = logger.bind(scraper=self.get_source_name())

    @abstractmethod
    def get_source_name(self) -> str:
        """Return unique source name (e.g., 'nyc_passport')."""
        pass

    @abstractmethod
    async def scrape(self) -> List[TenderCreate]:
        """Execute scraping and return tender data.

        Returns:
            List of TenderCreate objects

        Raises:
            Exception: If scraping fails
        """
        pass

    def generate_fingerprint(self, tender: TenderCreate) -> str:
        """Generate unique fingerprint for deduplication.

        Uses source_url + title + publish_date to create stable hash.
        """
        components = [
            tender.source_url,
            tender.title,
            str(tender.publish_date) if tender.publish_date else "",
        ]
        content = "|".join(components).encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def log_info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(message, **kwargs)

    def log_error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, **kwargs)
