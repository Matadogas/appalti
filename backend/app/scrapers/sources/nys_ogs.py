"""NYS OGS Procurement Services scraper.

Scrapes bid opportunities from New York State Office of General Services.
URL: https://ogs.ny.gov/procurement/bid-opportunities

The page has a single table with class='table' containing bid rows.
Columns: Description (with link) | Bid Opening Date | Bid # | Group #
No explicit header row - first tr is a data row.
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

    BASE_URL = "https://ogs.ny.gov/procurement/bid-opportunities"
    SITE_BASE = "https://ogs.ny.gov"

    CATEGORY_KEYWORDS = {
        TenderCategory.CONSTRUCTION: [
            "construction", "building", "renovation", "infrastructure",
            "roadway", "bridge", "demolition", "paving", "concrete",
        ],
        TenderCategory.ENGINEERING: [
            "engineering", "design", "architectural", "inspection",
            "testing", "geotechnical",
        ],
        TenderCategory.FACILITIES: [
            "facilities", "maintenance", "repair", "janitorial",
            "hvac", "plumbing", "electrical", "elevator",
            "kitchen", "laundry", "cleaning", "furniture", "floor",
        ],
    }

    def get_source_name(self) -> str:
        return "nys_ogs"

    async def scrape(self) -> List[TenderCreate]:
        """Scrape NYS OGS opportunities."""
        self.log_info("Starting NYS OGS scrape")
        tenders = []

        try:
            async with httpx.AsyncClient(
                timeout=30.0, follow_redirects=True
            ) as client:
                response = await client.get(self.BASE_URL)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")
                self.log_info(f"Page loaded: {len(response.text):,} chars")

                # OGS has a single table.table with bid data
                # Columns: Description | Bid Opening Date | Bid # | Group #
                table = soup.select_one("table.table")
                if not table:
                    self.log_info("No table.table found, trying first table")
                    table = soup.select_one("table")

                if not table:
                    self.log_error("No bid table found on page")
                    return tenders

                rows = table.select("tr")
                self.log_info(f"Found {len(rows)} table rows")

                for row in rows:
                    cells = row.select("td")
                    if len(cells) < 3:
                        continue

                    # Skip header-like rows (first row has "Description" / "Bid #")
                    first_text = cells[0].get_text(strip=True).lower()
                    if first_text == "description" or first_text.startswith("bid #"):
                        continue

                    try:
                        tender = self._parse_row(cells)
                        if tender:
                            tenders.append(tender)
                    except Exception as e:
                        self.log_error(f"Error parsing row: {str(e)}")
                        continue

            self.log_info(f"Scraped {len(tenders)} tenders from NYS OGS")
            return tenders

        except Exception as e:
            self.log_error(f"NYS OGS scraping failed: {str(e)}")
            raise

    def _parse_row(self, cells) -> Optional[TenderCreate]:
        """Parse a table row with columns: Description | Bid Opening Date | Bid # | Group #"""
        # Column 0: Description (with link)
        desc_cell = cells[0]
        link = desc_cell.select_one("a[href]")
        title = desc_cell.get_text(strip=True)

        if not title or len(title) < 3:
            return None

        # Get detail URL
        source_url = self.BASE_URL
        if link:
            href = link.get("href", "")
            if href.startswith("http"):
                source_url = href
            elif href.startswith("/"):
                source_url = f"{self.SITE_BASE}{href}"

        # Column 1: Bid Opening Date
        bid_date_str = cells[1].get_text(strip=True) if len(cells) > 1 else ""
        due_date = self._parse_date(bid_date_str)

        # Column 2: Bid #
        bid_number = cells[2].get_text(strip=True) if len(cells) > 2 else ""

        # Column 3: Group #
        group_number = cells[3].get_text(strip=True) if len(cells) > 3 else ""

        # Build title with bid number
        if bid_number:
            full_title = f"Bid #{bid_number} - {title}"
        else:
            full_title = title

        if len(full_title) > 490:
            full_title = full_title[:490]

        category = self._categorize(full_title)

        return TenderCreate(
            source_url=source_url,
            title=full_title,
            description_text=None,
            agency="NYS Office of General Services",
            state="NY",
            category=category,
            status=TenderStatus.ACTIVE,
            due_date=due_date,
            documents=[],
            raw_ref={
                "bid_number": bid_number,
                "group_number": group_number,
                "bid_opening_date": bid_date_str,
            },
        )

    def _categorize(self, title: str) -> TenderCategory:
        text = title.lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return category
        return TenderCategory.OTHER

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str or "continuous" in date_str.lower():
            return None

        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None
