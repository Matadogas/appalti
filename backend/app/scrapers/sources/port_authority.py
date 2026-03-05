"""Port Authority of NY & NJ scraper.

Scrapes procurement opportunities from the Bonfire portal JSON API.
API URL: https://panynj.bonfirehub.com/PublicPortal/getOpenPublicOpportunitiesSectionData
"""
from typing import List, Optional
from datetime import datetime
import httpx

from app.scrapers.base import BaseScraper
from app.schemas.tender import TenderCreate
from app.models.tender import TenderCategory, TenderStatus


class PortAuthorityScraper(BaseScraper):
    """Scraper for Port Authority of NY & NJ (Bonfire hub)."""

    API_URL = "https://panynj.bonfirehub.com/PublicPortal/getOpenPublicOpportunitiesSectionData"
    PORTAL_BASE = "https://panynj.bonfirehub.com/opportunities"

    CATEGORY_KEYWORDS = {
        TenderCategory.CONSTRUCTION: [
            "construction", "building", "renovation", "infrastructure",
            "roadway", "bridge", "demolition", "paving", "roofing",
            "concrete", "steel", "masonry",
        ],
        TenderCategory.ENGINEERING: [
            "engineering", "design", "architectural", "survey",
            "geotechnical", "structural", "inspection", "testing",
        ],
        TenderCategory.FACILITIES: [
            "facilities", "maintenance", "repair", "janitorial",
            "hvac", "plumbing", "electrical", "elevator", "cleaning",
        ],
    }

    def get_source_name(self) -> str:
        return "port_authority"

    async def scrape(self) -> List[TenderCreate]:
        """Scrape Port Authority opportunities via Bonfire JSON API."""
        self.log_info("Starting Port Authority scrape")
        tenders = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.API_URL)
                response.raise_for_status()

                data = response.json()

                # API returns either a list of sections or a dict with payload
                opportunities = []
                if isinstance(data, list):
                    for section in data:
                        opps = section.get("opportunities", [])
                        opportunities.extend(opps)
                elif isinstance(data, dict):
                    # Handle {"success": 1, "payload": {"projects": {...}}}
                    payload = data.get("payload", {})
                    projects = payload.get("projects", {})
                    if isinstance(projects, dict):
                        opportunities = list(projects.values())
                    elif isinstance(projects, list):
                        opportunities = projects
                    # Also check for direct list in payload
                    if not opportunities and isinstance(payload, list):
                        for section in payload:
                            opps = section.get("opportunities", [])
                            opportunities.extend(opps)

                self.log_info(f"Found {len(opportunities)} opportunities")

                for opp in opportunities:
                    try:
                        tender = self._parse_opportunity(opp)
                        if tender:
                            tenders.append(tender)
                    except Exception as e:
                        self.log_error(f"Error parsing opportunity: {str(e)}")
                        continue

            self.log_info(f"Scraped {len(tenders)} tenders from Port Authority")
            return tenders

        except Exception as e:
            self.log_error(f"Port Authority scraping failed: {str(e)}")
            raise

    def _parse_opportunity(self, opp: dict) -> Optional[TenderCreate]:
        """Parse a single opportunity from the Bonfire API response."""
        # Handle both API response formats
        title = (
            opp.get("name")
            or opp.get("ProjectName")
            or opp.get("title")
        )
        if not title:
            return None

        ref_number = (
            opp.get("referenceNumber")
            or opp.get("ReferenceID")
            or opp.get("reference_number")
            or ""
        )

        # Build detail URL
        opp_id = opp.get("id") or opp.get("ProjectID") or ""
        source_url = f"{self.PORTAL_BASE}/{opp_id}" if opp_id else self.API_URL

        # Parse closure date
        close_date_str = (
            opp.get("closureDate")
            or opp.get("ClosingDate")
            or opp.get("close_date")
        )
        due_date = self._parse_date(close_date_str)

        # Parse publish date
        publish_date_str = (
            opp.get("openDate")
            or opp.get("OpeningDate")
            or opp.get("publish_date")
        )
        publish_date = self._parse_date(publish_date_str)

        description = (
            opp.get("description")
            or opp.get("Description")
            or ""
        )

        # Build full title with reference number
        full_title = f"{ref_number} - {title}" if ref_number else title
        if len(full_title) > 490:
            full_title = full_title[:490]

        category = self._categorize(full_title, description)

        return TenderCreate(
            source_url=source_url,
            title=full_title,
            description_text=description or None,
            agency="Port Authority of NY & NJ",
            state="NY",
            city="New York",
            category=category,
            status=TenderStatus.ACTIVE,
            publish_date=publish_date,
            due_date=due_date,
            documents=[],
            raw_ref={
                "reference_number": ref_number,
                "bonfire_id": str(opp_id),
                "raw": {k: str(v)[:200] for k, v in opp.items()},
            },
        )

    def _categorize(self, title: str, description: str) -> TenderCategory:
        text = f"{title} {description}".lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return category
        return TenderCategory.OTHER

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None

        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y %I:%M:%S %p",
            "%m/%d/%Y",
            "%B %d, %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue

        return None
