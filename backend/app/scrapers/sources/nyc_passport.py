"""NYC PASSPort scraper.

Scrapes public RFx opportunities from NYC PASSPort portal.
Base URL: https://www1.nyc.gov/site/mocs/public-rfx/public-rfx.page
"""
from typing import List, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import structlog

from app.scrapers.base import BaseScraper
from app.schemas.tender import TenderCreate, DocumentSchema, ContactSchema
from app.models.tender import TenderCategory, TenderStatus

logger = structlog.get_logger()


class NYCPassportScraper(BaseScraper):
    """Scraper for NYC PASSPort public opportunities."""

    BASE_URL = "https://www1.nyc.gov/site/mocs/public-rfx/public-rfx.page"

    # Mapping of keywords to categories
    CATEGORY_KEYWORDS = {
        TenderCategory.CONSTRUCTION: [
            "construction", "building", "renovation", "infrastructure",
            "roadway", "bridge", "site work", "demolition"
        ],
        TenderCategory.ENGINEERING: [
            "engineering", "design", "architectural", "survey",
            "geotechnical", "structural"
        ],
        TenderCategory.FACILITIES: [
            "facilities", "maintenance", "repair", "janitorial",
            "hvac", "plumbing", "electrical"
        ],
    }

    def get_source_name(self) -> str:
        """Return source name."""
        return "nyc_passport"

    async def scrape(self) -> List[TenderCreate]:
        """Scrape NYC PASSPort opportunities.

        Returns:
            List of TenderCreate objects
        """
        self.log_info("Starting NYC PASSPort scrape")
        tenders = []

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Fetch the page
                response = await client.get(self.BASE_URL)
                response.raise_for_status()

                # Parse HTML
                soup = BeautifulSoup(response.text, "lxml")

                # Find tender listings
                # Note: Actual selectors will need to be updated based on real page structure
                tender_items = soup.select(".rfx-listing-item") or soup.select("tr.rfx-row")

                if not tender_items:
                    self.log_info("No tender items found - checking alternative selectors")
                    # Try alternative structure
                    tender_items = soup.select("div[class*='opportunity']") or []

                self.log_info(f"Found {len(tender_items)} tender items")

                for item in tender_items:
                    try:
                        tender = await self._parse_tender_item(item, client)
                        if tender:
                            tenders.append(tender)
                    except Exception as e:
                        self.log_error(f"Error parsing tender item: {str(e)}")
                        continue

            self.log_info(f"Scraped {len(tenders)} tenders")
            return tenders

        except Exception as e:
            self.log_error(f"Scraping failed: {str(e)}")
            raise

    async def _parse_tender_item(
        self, item: BeautifulSoup, client: httpx.AsyncClient
    ) -> Optional[TenderCreate]:
        """Parse a single tender item.

        Args:
            item: BeautifulSoup element containing tender data
            client: HTTP client for fetching detail pages

        Returns:
            TenderCreate object or None if parsing fails
        """
        try:
            # Extract title and URL
            title_elem = item.select_one("a.rfx-title") or item.select_one("td.title a")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")

            # Make URL absolute
            if url and not url.startswith("http"):
                url = f"https://www1.nyc.gov{url}"

            if not url:
                return None

            # Extract agency
            agency_elem = item.select_one(".agency") or item.select_one("td.agency")
            agency = agency_elem.get_text(strip=True) if agency_elem else "NYC PASSPort"

            # Extract due date
            due_date_elem = item.select_one(".due-date") or item.select_one("td.due-date")
            due_date = self._parse_date(
                due_date_elem.get_text(strip=True) if due_date_elem else None
            )

            # Extract description
            desc_elem = item.select_one(".description") or item.select_one("td.description")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # Determine category from title and description
            category = self._categorize_tender(title, description)

            # Create tender object
            tender = TenderCreate(
                source_url=url,
                title=title,
                description_text=description or None,
                agency=agency,
                state="NY",
                city="New York",
                category=category,
                status=TenderStatus.ACTIVE,
                due_date=due_date,
                documents=[],
                raw_ref={"html": str(item)[:1000]},  # Store first 1000 chars
            )

            return tender

        except Exception as e:
            self.log_error(f"Error parsing tender item: {str(e)}")
            return None

    def _categorize_tender(self, title: str, description: str) -> TenderCategory:
        """Categorize tender based on title and description.

        Args:
            title: Tender title
            description: Tender description

        Returns:
            TenderCategory enum value
        """
        text = f"{title} {description}".lower()

        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return category

        return TenderCategory.OTHER

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime.

        Args:
            date_str: Date string in various formats

        Returns:
            datetime object or None
        """
        if not date_str:
            return None

        # Try common date formats
        formats = [
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None
