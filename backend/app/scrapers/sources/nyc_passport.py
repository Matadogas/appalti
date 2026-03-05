"""NYC PASSPort scraper.

Scrapes public RFx opportunities from NYC PASSPort portal.
URL: https://passport.cityofnewyork.us/page.aspx/en/rfp/request_browse_public

The page has a table with id='body_x_grid_grd' and class='iv-grid-view'
containing RFx listings with headers:
  Editing column | Program | Industry | EPIN | Procurement Name |
  Agency | RFx Status | Procurement Method | Release Date | Due Date | ...
"""
from typing import List, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

from app.scrapers.base import BaseScraper
from app.schemas.tender import TenderCreate
from app.models.tender import TenderCategory, TenderStatus


class NYCPassportScraper(BaseScraper):
    """Scraper for NYC PASSPort public opportunities."""

    BASE_URL = "https://passport.cityofnewyork.us/page.aspx/en/rfp/request_browse_public"
    SITE_BASE = "https://passport.cityofnewyork.us"

    CATEGORY_KEYWORDS = {
        TenderCategory.CONSTRUCTION: [
            "construction", "building", "renovation", "infrastructure",
            "roadway", "bridge", "site work", "demolition", "paving",
            "reconstruction",
        ],
        TenderCategory.ENGINEERING: [
            "engineering", "design", "architectural", "survey",
            "geotechnical", "structural",
        ],
        TenderCategory.FACILITIES: [
            "facilities", "maintenance", "repair", "janitorial",
            "hvac", "plumbing", "electrical", "cleaning",
        ],
    }

    def get_source_name(self) -> str:
        return "nyc_passport"

    async def scrape(self) -> List[TenderCreate]:
        """Scrape NYC PASSPort opportunities."""
        self.log_info("Starting NYC PASSPort scrape")
        tenders = []

        try:
            async with httpx.AsyncClient(
                timeout=30.0, follow_redirects=True
            ) as client:
                response = await client.get(self.BASE_URL)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")
                self.log_info(f"Page loaded: {len(response.text):,} chars")

                # PASSPort grid table: id='body_x_grid_grd', class='iv-grid-view'
                grid = soup.select_one("table.iv-grid-view")
                if not grid:
                    grid = soup.select_one("table#body_x_grid_grd")
                if not grid:
                    # Fallback: find the largest table
                    tables = soup.select("table")
                    grid = max(tables, key=lambda t: len(t.select("tr")), default=None)

                if not grid:
                    self.log_error("No grid table found on PASSPort page")
                    return tenders

                # Get header mapping
                headers = []
                header_cells = grid.select("th")
                if header_cells:
                    headers = [th.get_text(strip=True).lower() for th in header_cells]

                rows = grid.select("tr")[1:]  # Skip header row
                self.log_info(f"Found {len(rows)} grid rows, headers: {headers[:8]}")

                for row in rows:
                    cells = row.select("td")
                    if len(cells) < 5:
                        continue

                    try:
                        tender = self._parse_row(cells, headers)
                        if tender:
                            tenders.append(tender)
                    except Exception as e:
                        self.log_error(f"Error parsing row: {str(e)}")
                        continue

            self.log_info(f"Scraped {len(tenders)} tenders from NYC PASSPort")
            return tenders

        except Exception as e:
            self.log_error(f"NYC PASSPort scraping failed: {str(e)}")
            raise

    def _get_cell(self, cells, headers: list, *names: str) -> str:
        """Get cell text by header name, with fallback to index."""
        for name in names:
            for i, h in enumerate(headers):
                if name in h and i < len(cells):
                    return cells[i].get_text(strip=True)
        return ""

    def _parse_row(self, cells, headers: list) -> Optional[TenderCreate]:
        """Parse a grid row into a TenderCreate."""
        # Known header indices from inspection:
        # 0: Editing column (has link + title)
        # 1: Program
        # 2: Industry
        # 3: EPIN
        # 4: Procurement Name
        # 5: Agency
        # 6: RFx Status
        # 7: Procurement Method
        # 8-9: Release Date / Due Date

        # Get procurement name/title - try column mapping first
        title = self._get_cell(cells, headers, "procurement name")
        epin = self._get_cell(cells, headers, "epin")

        # Fallback: get from first cell (editing column contains the title too)
        if not title:
            first_cell = cells[0].get_text(strip=True)
            # Remove "Edit " prefix from ASP.NET edit button
            if first_cell.startswith("Edit "):
                title = first_cell[5:]
            else:
                title = first_cell

        if not title or len(title) < 3:
            return None

        # Get detail link from first cell
        source_url = self.BASE_URL
        link = cells[0].select_one("a[href]")
        if link:
            href = link.get("href", "")
            if href and "process_manage" in href:
                if href.startswith("http"):
                    source_url = href
                else:
                    source_url = f"{self.SITE_BASE}{href}"

        # Agency
        agency = self._get_cell(cells, headers, "agency")
        if not agency and len(cells) > 5:
            agency = cells[5].get_text(strip=True)
        agency = agency or "NYC Agency"

        # Industry / Program
        industry = self._get_cell(cells, headers, "industry")
        program = self._get_cell(cells, headers, "program")

        # RFx Status
        rfx_status = self._get_cell(cells, headers, "rfx status")

        # Dates
        release_str = self._get_cell(cells, headers, "release date")
        due_str = self._get_cell(cells, headers, "due date")
        publish_date = self._parse_date(release_str)
        due_date = self._parse_date(due_str)

        # Build description from available fields
        desc_parts = []
        if program:
            desc_parts.append(f"Program: {program}")
        if industry:
            desc_parts.append(f"Industry: {industry}")
        if rfx_status:
            desc_parts.append(f"Status: {rfx_status}")
        description = "; ".join(desc_parts) if desc_parts else None

        category = self._categorize(title, industry or "")

        return TenderCreate(
            source_url=source_url,
            title=title[:500],
            description_text=description,
            agency=agency,
            state="NY",
            city="New York",
            category=category,
            status=TenderStatus.ACTIVE,
            publish_date=publish_date,
            due_date=due_date,
            documents=[],
            raw_ref={
                "epin": epin,
                "industry": industry,
                "program": program,
                "rfx_status": rfx_status,
            },
        )

    def _categorize(self, title: str, industry: str) -> TenderCategory:
        text = f"{title} {industry}".lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return category
        return TenderCategory.OTHER

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None

        formats = [
            "%m/%d/%Y %I:%M:%S %p",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %I:%M %p",
            "%m/%d/%Y",
            "%Y-%m-%d",
            "%B %d, %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        return None
