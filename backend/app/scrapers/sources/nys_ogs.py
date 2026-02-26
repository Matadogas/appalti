"""NYS OGS Procurement Services scraper.

Scrapes bid opportunities from New York State Office of General Services.
Base URL: https://online.ogs.ny.gov/purchase/spg/
"""
from typing import List, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper
from app.schemas.tender import TenderCreate
from app.models.tender import TenderCategory, TenderStatus


class NYSOGSScraper(BaseScraper):
    """Scraper for NYS OGS procurement opportunities."""

    BASE_URL = "https://online.ogs.ny.gov/purchase/spg/"

    def get_source_name(self) -> str:
        """Return source name."""
        return "nys_ogs"

    async def scrape(self) -> List[TenderCreate]:
        """Scrape NYS OGS opportunities."""
        self.log_info("Starting NYS OGS scrape")
        tenders = []

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(self.BASE_URL)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")

                # Parse bid listings
                # Note: Update selectors based on actual page structure
                bid_items = soup.select("tr.bid-row") or soup.select("div.bid-item")

                self.log_info(f"Found {len(bid_items)} bid items")

                for item in bid_items:
                    try:
                        tender = await self._parse_bid_item(item)
                        if tender:
                            tenders.append(tender)
                    except Exception as e:
                        self.log_error(f"Error parsing bid: {str(e)}")
                        continue

            self.log_info(f"Scraped {len(tenders)} tenders from NYS OGS")
            return tenders

        except Exception as e:
            self.log_error(f"NYS OGS scraping failed: {str(e)}")
            raise

    async def _parse_bid_item(self, item: BeautifulSoup) -> Optional[TenderCreate]:
        """Parse a single bid item."""
        try:
            # Extract title and URL
            title_elem = item.select_one("a")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            url = title_elem.get("href", "")

            if url and not url.startswith("http"):
                url = f"https://online.ogs.ny.gov{url}"

            if not url:
                return None

            # Extract description
            desc_elem = item.select_one(".description")
            description = desc_elem.get_text(strip=True) if desc_elem else ""

            # Extract due date
            due_elem = item.select_one(".due-date")
            due_date = self._parse_date(
                due_elem.get_text(strip=True) if due_elem else None
            )

            tender = TenderCreate(
                source_url=url,
                title=title,
                description_text=description or None,
                agency="NYS Office of General Services",
                state="NY",
                category=TenderCategory.OTHER,
                status=TenderStatus.ACTIVE,
                due_date=due_date,
                documents=[],
                raw_ref={"html": str(item)[:1000]},
            )

            return tender

        except Exception as e:
            self.log_error(f"Error parsing NYS OGS bid: {str(e)}")
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string."""
        if not date_str:
            return None

        formats = ["%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y"]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None
