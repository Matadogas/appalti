# Source Discovery & Coverage Master Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a systematic process to discover, track, and scrape ALL NYC + NJ public construction RFP/RFQ/IFB sources using Crawl4AI, ensuring 100% coverage with cross-checking mechanisms.

**Architecture:** Discovery pipeline → Portal vendor detection → Adapter-based scraping with Crawl4AI → Coverage verification → Continuous monitoring. Treats procurement data as a supply chain with quality controls at every stage.

**Tech Stack:** Python 3.11+, Crawl4AI, PostgreSQL, pandas, openpyxl (for spreadsheets), LLM-assisted portal detection

---

## Overview: The Procurement Data Supply Chain

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Discovery     │────▶│ Portal Vendor    │────▶│  Adapter        │
│   Pipeline      │     │   Detection      │     │  Configuration  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Coverage      │◀────│   Scraping       │◀────│  Crawl4AI       │
│   Verification  │     │   Execution      │     │  Engine         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## Phase 1: Source Registry & Tracking Infrastructure

### Task 1: Create Source Registry Database Schema

**Files:**
- Create: `backend/app/models/source_registry.py`
- Create: `backend/alembic/versions/XXXX_add_source_registry.py`

**Step 1: Create source registry model**

Create `backend/app/models/source_registry.py`:
```python
"""Source registry model for tracking all procurement portals."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    Integer,
    Enum,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from app.database import Base


class JurisdictionType(str, enum.Enum):
    """Jurisdiction type enum."""

    NYC = "nyc"
    NJ_STATE = "nj_state"
    NJ_COUNTY = "nj_county"
    NJ_CITY = "nj_city"
    NJ_SCHOOL_DISTRICT = "nj_school_district"
    NJ_AUTHORITY = "nj_authority"
    NY_STATE = "ny_state"
    NY_COUNTY = "ny_county"


class PortalVendor(str, enum.Enum):
    """Portal vendor enum."""

    PASSPORT = "passport"
    NJSTART = "njstart"
    BIDEXPRESS = "bidexpress"
    OPENGOV = "opengov"
    PROCURENOW = "procurenow"
    BONFIRE = "bonfire"
    DEMANDSTAR = "demandstar"
    PLANETBIDS = "planetbids"
    PUBLICPURCHASE = "publicpurchase"
    CUSTOM_HTML = "custom_html"
    UNKNOWN = "unknown"


class AccessMode(str, enum.Enum):
    """Access mode enum."""

    PUBLIC = "public"
    FREE_REGISTRATION = "free_registration"
    PAID = "paid"
    RESTRICTED = "restricted"


class SourceRegistry(Base):
    """Registry entry for a procurement portal."""

    __tablename__ = "source_registry"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Entity information
    jurisdiction = Column(Enum(JurisdictionType), nullable=False, index=True)
    entity_name = Column(String(200), nullable=False, index=True)
    entity_type = Column(String(100))  # "City", "Authority", "School District", etc.

    # Portal information
    portal_vendor = Column(Enum(PortalVendor), default=PortalVendor.UNKNOWN)
    portal_version = Column(String(50))  # For tracking portal software versions

    # URLs
    bid_list_url = Column(String(500), nullable=False)
    base_domain = Column(String(200), index=True)
    docs_detail_url_pattern = Column(String(500))
    search_url = Column(String(500))

    # Access & Technical
    access_mode = Column(Enum(AccessMode), default=AccessMode.PUBLIC)
    requires_javascript = Column(Boolean, default=False)
    has_captcha = Column(Boolean, default=False)
    rate_limit_per_minute = Column(Integer)

    # Adapter configuration
    adapter_class = Column(String(100))  # Which adapter to use
    adapter_config = Column(JSONB, default=dict)  # Adapter-specific settings
    css_selectors = Column(JSONB, default=dict)  # Parsing selectors

    # Discovery metadata
    discovery_method = Column(String(100))  # "google_search", "directory", "manual", etc.
    discovery_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    verified_date = Column(DateTime(timezone=True))  # Last manual verification
    verified_by = Column(String(100))

    # Status
    active = Column(Boolean, default=True)
    priority = Column(Integer, default=5)  # 1-10, higher = more important
    notes = Column(Text)
    issues = Column(JSONB, default=list)  # Known issues/blockers

    # Coverage tracking
    expected_monthly_postings = Column(Integer)  # Historical average
    last_successful_scrape = Column(DateTime(timezone=True))
    consecutive_failures = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<SourceRegistry {self.entity_name} ({self.portal_vendor.value})>"
```

**Step 2: Create migration**

```bash
docker-compose exec backend alembic revision --autogenerate -m "add source registry table"
```

**Step 3: Run migration**

```bash
docker-compose exec backend alembic upgrade head
```

**Step 4: Verify table created**

```bash
docker-compose exec postgres psql -U tristate -d tristate_bids -c "\d source_registry"
```

Expected: Table structure displayed

**Step 5: Commit source registry model**

```bash
git add backend/app/models/source_registry.py backend/alembic/
git commit -m "feat: add source registry model for tracking all procurement portals"
```

---

### Task 2: Create Coverage Scorecard Schema

**Files:**
- Create: `backend/app/models/coverage_scorecard.py`
- Create: `backend/alembic/versions/XXXX_add_coverage_scorecard.py`

**Step 1: Create coverage scorecard model**

Create `backend/app/models/coverage_scorecard.py`:
```python
"""Coverage scorecard for monitoring source health."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class CoverageScorecard(Base):
    """Weekly scorecard for source coverage monitoring."""

    __tablename__ = "coverage_scorecard"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_registry_id = Column(
        UUID(as_uuid=True), ForeignKey("source_registry.id"), nullable=False, index=True
    )

    # Time period
    week_start = Column(DateTime(timezone=True), nullable=False, index=True)
    week_end = Column(DateTime(timezone=True), nullable=False)

    # Counts
    tenders_scraped = Column(Integer, default=0)
    tenders_new = Column(Integer, default=0)
    tenders_updated = Column(Integer, default=0)

    # Expected vs actual
    expected_count = Column(Integer)  # Based on historical average
    actual_count = Column(Integer)
    variance_pct = Column(Float)  # (actual - expected) / expected * 100

    # Health metrics
    scrape_attempts = Column(Integer, default=0)
    scrape_successes = Column(Integer, default=0)
    scrape_failures = Column(Integer, default=0)
    avg_response_time_ms = Column(Float)

    # Anomalies
    is_anomaly = Column(String(50))  # "zero_results", "low_count", "parse_errors", "ok"
    anomaly_details = Column(JSONB)

    # Sentinel checks (specific keyword searches)
    sentinel_keywords = Column(JSONB, default=list)  # Keywords searched
    sentinel_hits = Column(Integer)  # How many tenders matched

    # Manual verification
    manually_verified = Column(DateTime(timezone=True))
    manual_count = Column(Integer)  # What human saw on the portal
    match_accuracy_pct = Column(Float)  # manual_count vs actual_count

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    source = relationship(
        "SourceRegistry",
        foreign_keys=[source_registry_id],
        backref="coverage_scores",
    )

    def __repr__(self) -> str:
        return f"<CoverageScorecard {self.source_registry_id} {self.week_start}>"
```

**Step 2: Create migration**

```bash
docker-compose exec backend alembic revision --autogenerate -m "add coverage scorecard table"
```

**Step 3: Run migration**

```bash
docker-compose exec backend alembic upgrade head
```

**Step 4: Commit coverage scorecard**

```bash
git add backend/app/models/coverage_scorecard.py backend/alembic/
git commit -m "feat: add coverage scorecard for monitoring source health"
```

---

### Task 3: Create Source Registry Spreadsheet Templates

**Files:**
- Create: `docs/templates/source-registry-template.csv`
- Create: `docs/templates/coverage-scorecard-template.csv`
- Create: `docs/templates/discovery-checklist.csv`
- Create: `backend/scripts/export_registry_to_excel.py`

**Step 1: Create source registry CSV template**

Create `docs/templates/source-registry-template.csv`:
```csv
jurisdiction,entity_name,entity_type,portal_vendor,bid_list_url,base_domain,access_mode,requires_javascript,priority,expected_monthly_postings,discovery_method,verified_date,notes
nyc,NYC PASSPort,City Procurement,passport,https://www1.nyc.gov/site/mocs/public-rfx/public-rfx.page,nyc.gov,public,true,10,50,directory,2026-02-27,Primary NYC procurement portal
nj_state,NJ Treasury Purchase & Property,State Purchasing,custom_html,https://www.njstart.gov/bso/,njstart.gov,public,false,10,40,directory,2026-02-27,NJ state purchasing hub
nj_state,NJSTART Public Search,State eProcurement,njstart,https://www.njstart.gov/bso/external/advanceSearch.sdo,njstart.gov,free_registration,true,10,60,directory,2026-02-27,NJ state eProcurement system
nj_state,NJDOT Solicitations,Transportation Authority,bidexpress,https://www.bidexpress.com/businesses/20025/home,bidexpress.com,free_registration,true,9,30,directory,2026-02-27,All NJDOT bids via BidExpress
nj_city,City of Newark,City Procurement,opengov,https://procure.cityofnewark.org/CurrentBids.aspx,cityofnewark.org,public,true,8,15,directory,2026-02-27,Uses OpenGov + ProcureNow
nj_authority,NJ Economic Development Authority,State Authority,custom_html,https://www.njeda.gov/about/public-information/requests-for-proposals/,njeda.gov,public,false,7,5,directory,2026-02-27,Authority-specific portal
```

**Step 2: Create coverage scorecard CSV template**

Create `docs/templates/coverage-scorecard-template.csv`:
```csv
entity_name,week_start,week_end,expected_count,actual_count,variance_pct,scrape_attempts,scrape_successes,scrape_failures,is_anomaly,anomaly_details,manually_verified,manual_count,match_accuracy_pct
NYC PASSPort,2026-02-24,2026-02-28,50,48,-4.0,7,7,0,ok,,,,
NJ Treasury,2026-02-24,2026-02-28,40,0,-100.0,7,0,7,zero_results,Scraper broken - selector changed,,,
NJDOT,2026-02-24,2026-02-28,30,32,6.7,7,7,0,ok,,2026-02-27,32,100.0
```

**Step 3: Create discovery checklist template**

Create `docs/templates/discovery-checklist.csv`:
```csv
jurisdiction_type,entity_name,procurement_page_found,procurement_url,portal_vendor_detected,priority,added_to_registry,notes
nj_county,Bergen County,yes,https://www.co.bergen.nj.us/procurement,unknown,6,no,Need to investigate portal type
nj_county,Hudson County,yes,https://www.hudsoncountynj.org/purchasing,unknown,6,no,Simple HTML listing
nj_city,Jersey City,yes,https://www.jerseycitynj.gov/city_hall/purchasing,demandstar,7,no,Uses DemandStar
nj_city,Paterson,searching,,,5,no,Need to find procurement page
nj_school_district,Newark Public Schools,yes,https://www.nps.k12.nj.us/departments/business-administration/,custom_html,5,no,Basic current bids page
```

**Step 4: Create Excel export script**

Create `backend/scripts/export_registry_to_excel.py`:
```python
"""Export source registry to Excel for manual review."""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.source_registry import SourceRegistry


def export_to_excel(output_path: str = "source_registry_export.xlsx"):
    """Export source registry to Excel."""
    db = SessionLocal()

    try:
        # Query all sources
        sources = db.query(SourceRegistry).order_by(
            SourceRegistry.jurisdiction, SourceRegistry.priority.desc()
        ).all()

        # Convert to DataFrame
        data = []
        for source in sources:
            data.append({
                "jurisdiction": source.jurisdiction.value,
                "entity_name": source.entity_name,
                "entity_type": source.entity_type,
                "portal_vendor": source.portal_vendor.value,
                "bid_list_url": source.bid_list_url,
                "access_mode": source.access_mode.value,
                "priority": source.priority,
                "expected_monthly_postings": source.expected_monthly_postings,
                "last_successful_scrape": source.last_successful_scrape,
                "consecutive_failures": source.consecutive_failures,
                "active": source.active,
                "notes": source.notes,
            })

        df = pd.DataFrame(data)

        # Export to Excel with formatting
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Source Registry", index=False)

            # Get workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets["Source Registry"]

            # Auto-adjust column widths
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)

        print(f"✅ Exported {len(sources)} sources to {output_path}")

    except Exception as e:
        print(f"❌ Export failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "source_registry_export.xlsx"
    export_to_excel(output)
```

**Step 5: Add pandas and openpyxl to requirements**

Edit `backend/requirements.txt` - add:
```txt
pandas==2.1.4
openpyxl==3.1.2
```

**Step 6: Test export script**

```bash
docker-compose exec backend pip install pandas openpyxl
docker-compose exec backend python scripts/export_registry_to_excel.py
```

Expected: Excel file created

**Step 7: Commit templates and export script**

```bash
git add docs/templates/ backend/scripts/export_registry_to_excel.py backend/requirements.txt
git commit -m "feat: add source registry spreadsheet templates and Excel export"
```

---

## Phase 2: Crawl4AI Integration

### Task 4: Install and Configure Crawl4AI

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/app/crawlers/__init__.py`
- Create: `backend/app/crawlers/crawl4ai_wrapper.py`
- Create: `backend/tests/test_crawlers/test_crawl4ai_wrapper.py`

**Step 1: Add Crawl4AI to requirements**

Edit `backend/requirements.txt` - add:
```txt
crawl4ai==0.3.74
playwright==1.44.0
```

**Step 2: Write test for Crawl4AI wrapper**

Create `backend/tests/test_crawlers/__init__.py`:
```python
"""Crawler tests."""
```

Create `backend/tests/test_crawlers/test_crawl4ai_wrapper.py`:
```python
"""Test Crawl4AI wrapper."""
import pytest
from app.crawlers.crawl4ai_wrapper import Crawl4AIWrapper


class TestCrawl4AIWrapper:
    """Test Crawl4AI wrapper."""

    @pytest.mark.asyncio
    async def test_fetch_page_simple(self):
        """Test fetching a simple page."""
        crawler = Crawl4AIWrapper()
        result = await crawler.fetch_page("https://example.com")

        assert result is not None
        assert "html" in result
        assert "text" in result
        assert "markdown" in result

    @pytest.mark.asyncio
    async def test_fetch_with_javascript(self):
        """Test fetching page with JavaScript rendering."""
        crawler = Crawl4AIWrapper(enable_javascript=True)
        result = await crawler.fetch_page("https://example.com")

        assert result is not None
        assert result["html"] is not None

    @pytest.mark.asyncio
    async def test_extract_structured_data(self):
        """Test extracting structured data."""
        crawler = Crawl4AIWrapper()

        schema = {
            "name": "Title Extractor",
            "baseSelector": "h1",
            "fields": [
                {"name": "title", "selector": "h1", "type": "text"}
            ]
        }

        result = await crawler.fetch_and_extract(
            "https://example.com",
            schema=schema
        )

        assert result is not None
```

**Step 3: Run test to verify it fails**

```bash
docker-compose exec backend pytest tests/test_crawlers/test_crawl4ai_wrapper.py -v
```

Expected: FAIL - module not found

**Step 4: Create Crawl4AI wrapper**

Create `backend/app/crawlers/__init__.py`:
```python
"""Crawlers package."""
```

Create `backend/app/crawlers/crawl4ai_wrapper.py`:
```python
"""Crawl4AI wrapper for consistent scraping interface."""
from typing import Optional, Dict, Any, List
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy
import structlog

logger = structlog.get_logger()


class Crawl4AIWrapper:
    """Wrapper around Crawl4AI for scraping with consistent interface."""

    def __init__(
        self,
        enable_javascript: bool = False,
        headless: bool = True,
        user_agent: Optional[str] = None,
        wait_for_selector: Optional[str] = None,
        rate_limit_delay: float = 1.0,
    ):
        """Initialize Crawl4AI wrapper.

        Args:
            enable_javascript: Whether to enable JavaScript rendering
            headless: Run browser in headless mode
            user_agent: Custom user agent string
            wait_for_selector: CSS selector to wait for before extraction
            rate_limit_delay: Delay between requests in seconds
        """
        self.enable_javascript = enable_javascript
        self.headless = headless
        self.user_agent = user_agent
        self.wait_for_selector = wait_for_selector
        self.rate_limit_delay = rate_limit_delay

        # Browser config
        self.browser_config = BrowserConfig(
            headless=headless,
            verbose=False,
        )

        # Crawler run config
        self.crawler_config = CrawlerRunConfig(
            wait_until="networkidle" if enable_javascript else "domcontentloaded",
            delay_before_return_html=2.0 if enable_javascript else 0.0,
        )

        if wait_for_selector:
            self.crawler_config.wait_for = wait_for_selector

        self._crawler: Optional[AsyncWebCrawler] = None

    async def _get_crawler(self) -> AsyncWebCrawler:
        """Get or create crawler instance."""
        if self._crawler is None:
            self._crawler = AsyncWebCrawler(config=self.browser_config)
            await self._crawler.__aenter__()
        return self._crawler

    async def fetch_page(self, url: str) -> Dict[str, Any]:
        """Fetch a page and return parsed content.

        Args:
            url: URL to fetch

        Returns:
            Dict containing:
                - html: Raw HTML
                - text: Extracted text
                - markdown: Markdown representation
                - links: List of links found
                - metadata: Page metadata
        """
        logger.info(f"Fetching page: {url}")

        try:
            crawler = await self._get_crawler()

            result = await crawler.arun(
                url=url,
                config=self.crawler_config,
            )

            if not result.success:
                logger.error(f"Fetch failed: {result.error_message}")
                raise Exception(f"Failed to fetch {url}: {result.error_message}")

            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)

            return {
                "html": result.html,
                "text": result.markdown,  # Crawl4AI's markdown is cleaner than raw text
                "markdown": result.markdown,
                "links": result.links.get("external", []) + result.links.get("internal", []),
                "metadata": {
                    "title": result.metadata.get("title"),
                    "description": result.metadata.get("description"),
                },
            }

        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            raise

    async def fetch_and_extract(
        self,
        url: str,
        schema: Optional[Dict[str, Any]] = None,
        llm_provider: Optional[str] = None,
        llm_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch page and extract structured data.

        Args:
            url: URL to fetch
            schema: JSON-CSS extraction schema (if using CSS selectors)
            llm_provider: LLM provider name (if using LLM extraction)
            llm_prompt: Prompt for LLM extraction

        Returns:
            Extracted structured data
        """
        logger.info(f"Fetching and extracting from: {url}")

        try:
            crawler = await self._get_crawler()

            # Choose extraction strategy
            if llm_provider and llm_prompt:
                extraction_strategy = LLMExtractionStrategy(
                    provider=llm_provider,
                    instruction=llm_prompt,
                )
            elif schema:
                extraction_strategy = JsonCssExtractionStrategy(schema)
            else:
                # No extraction, just fetch
                return await self.fetch_page(url)

            # Run with extraction
            config = self.crawler_config
            config.extraction_strategy = extraction_strategy

            result = await crawler.arun(url=url, config=config)

            if not result.success:
                raise Exception(f"Extraction failed: {result.error_message}")

            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)

            return {
                "extracted_content": result.extracted_content,
                "html": result.html,
                "markdown": result.markdown,
                "metadata": result.metadata,
            }

        except Exception as e:
            logger.error(f"Error extracting from {url}: {str(e)}")
            raise

    async def close(self):
        """Close crawler and cleanup."""
        if self._crawler:
            await self._crawler.__aexit__(None, None, None)
            self._crawler = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
```

**Step 5: Install Crawl4AI and Playwright**

```bash
docker-compose exec backend pip install crawl4ai playwright
docker-compose exec backend playwright install chromium
```

**Step 6: Run tests**

```bash
docker-compose exec backend pytest tests/test_crawlers/test_crawl4ai_wrapper.py -v
```

Expected: PASS

**Step 7: Commit Crawl4AI integration**

```bash
git add backend/requirements.txt backend/app/crawlers/ backend/tests/test_crawlers/
git commit -m "feat: integrate Crawl4AI for advanced web scraping"
```

---

### Task 5: Refactor BaseScraper to Use Crawl4AI

**Files:**
- Modify: `backend/app/scrapers/base.py`
- Create: `backend/app/scrapers/crawl4ai_scraper.py`
- Modify: `backend/app/scrapers/sources/nyc_passport.py`

**Step 1: Create Crawl4AI-based scraper base class**

Create `backend/app/scrapers/crawl4ai_scraper.py`:
```python
"""Crawl4AI-based scraper base class."""
from typing import Optional
from app.scrapers.base import BaseScraper
from app.crawlers.crawl4ai_wrapper import Crawl4AIWrapper


class Crawl4AIScraper(BaseScraper):
    """Base scraper using Crawl4AI for fetching pages.

    Provides convenient methods for JavaScript-heavy sites and LLM extraction.
    """

    def __init__(self, config: Optional[dict] = None):
        """Initialize scraper."""
        super().__init__(config)

        # Configure Crawl4AI based on config
        enable_js = self.config.get("enable_javascript", False)
        wait_for = self.config.get("wait_for_selector")
        rate_limit = self.config.get("rate_limit_delay", 1.0)

        self.crawler = Crawl4AIWrapper(
            enable_javascript=enable_js,
            wait_for_selector=wait_for,
            rate_limit_delay=rate_limit,
        )

    async def fetch_page(self, url: str):
        """Fetch page using Crawl4AI.

        Returns:
            Dict with html, text, markdown, links, metadata
        """
        return await self.crawler.fetch_page(url)

    async def fetch_with_extraction(self, url: str, schema: dict):
        """Fetch page and extract structured data using CSS selectors.

        Args:
            url: URL to fetch
            schema: JSON-CSS extraction schema

        Returns:
            Extracted structured data
        """
        return await self.crawler.fetch_and_extract(url, schema=schema)

    async def fetch_with_llm(self, url: str, prompt: str, provider: str = "anthropic"):
        """Fetch page and extract using LLM.

        Args:
            url: URL to fetch
            prompt: Extraction prompt for LLM
            provider: LLM provider (anthropic, openai, etc.)

        Returns:
            LLM-extracted data
        """
        return await self.crawler.fetch_and_extract(
            url, llm_provider=provider, llm_prompt=prompt
        )

    async def cleanup(self):
        """Cleanup resources."""
        await self.crawler.close()
```

**Step 2: Update NYC PASSPort scraper to use Crawl4AI**

Edit `backend/app/scrapers/sources/nyc_passport.py`:

Replace the class definition line:
```python
class NYCPassportScraper(BaseScraper):
```

With:
```python
from app.scrapers.crawl4ai_scraper import Crawl4AIScraper

class NYCPassportScraper(Crawl4AIScraper):
```

Replace the httpx client usage in the `scrape` method:
```python
async def scrape(self) -> List[TenderCreate]:
    """Scrape NYC PASSPort opportunities."""
    self.log_info("Starting NYC PASSPort scrape")
    tenders = []

    try:
        # Fetch page using Crawl4AI
        result = await self.fetch_page(self.BASE_URL)

        # Parse HTML
        soup = BeautifulSoup(result["html"], "lxml")

        # Rest of parsing logic remains the same...
```

**Step 3: Test updated scraper**

```bash
docker-compose exec backend pytest tests/test_scrapers/test_nyc_passport.py -v
```

Expected: PASS

**Step 4: Commit Crawl4AI scraper refactor**

```bash
git add backend/app/scrapers/
git commit -m "feat: refactor scrapers to use Crawl4AI for robust fetching"
```

---

## Phase 3: Portal Vendor Detection System

### Task 6: Portal Vendor Detector

**Files:**
- Create: `backend/app/discovery/__init__.py`
- Create: `backend/app/discovery/portal_detector.py`
- Create: `backend/tests/test_discovery/test_portal_detector.py`

**Step 1: Write test for portal detector**

Create `backend/tests/test_discovery/__init__.py`:
```python
"""Discovery tests."""
```

Create `backend/tests/test_discovery/test_portal_detector.py`:
```python
"""Test portal vendor detector."""
import pytest
from app.discovery.portal_detector import PortalDetector
from app.models.source_registry import PortalVendor


class TestPortalDetector:
    """Test portal vendor detection."""

    @pytest.mark.asyncio
    async def test_detect_passport(self):
        """Test detecting NYC PASSPort."""
        detector = PortalDetector()
        vendor = await detector.detect_portal_vendor(
            "https://www1.nyc.gov/site/mocs/public-rfx/public-rfx.page"
        )
        assert vendor == PortalVendor.PASSPORT

    @pytest.mark.asyncio
    async def test_detect_bidexpress(self):
        """Test detecting BidExpress."""
        detector = PortalDetector()
        vendor = await detector.detect_portal_vendor(
            "https://www.bidexpress.com/businesses/20025/home"
        )
        assert vendor == PortalVendor.BIDEXPRESS

    @pytest.mark.asyncio
    async def test_detect_opengov(self):
        """Test detecting OpenGov."""
        detector = PortalDetector()
        vendor = await detector.detect_portal_vendor(
            "https://procurement.opengov.com/portal/cityofnewark"
        )
        assert vendor == PortalVendor.OPENGOV
```

**Step 2: Run test to verify it fails**

```bash
docker-compose exec backend pytest tests/test_discovery/test_portal_detector.py -v
```

Expected: FAIL - module not found

**Step 3: Implement portal detector**

Create `backend/app/discovery/__init__.py`:
```python
"""Discovery package."""
```

Create `backend/app/discovery/portal_detector.py`:
```python
"""Portal vendor detector using domain patterns and HTML signatures."""
from typing import Optional
from urllib.parse import urlparse
import structlog

from app.models.source_registry import PortalVendor
from app.crawlers.crawl4ai_wrapper import Crawl4AIWrapper

logger = structlog.get_logger()


class PortalDetector:
    """Detect portal vendor from URL and page content."""

    # Domain-based detection rules (fast path)
    DOMAIN_PATTERNS = {
        PortalVendor.PASSPORT: ["nyc.gov/site/mocs", "a856-cityrecord"],
        PortalVendor.NJSTART: ["njstart.gov"],
        PortalVendor.BIDEXPRESS: ["bidexpress.com", "bidx.com"],
        PortalVendor.OPENGOV: ["opengov.com/procurement", "procurement.opengov"],
        PortalVendor.PROCURENOW: ["procurenow.com", "bidsandtenders.ca"],
        PortalVendor.BONFIRE: ["bonfirehub.com", "gobonfire.com"],
        PortalVendor.DEMANDSTAR: ["demandstar.com"],
        PortalVendor.PLANETBIDS: ["planetbids.com"],
        PortalVendor.PUBLICPURCHASE: ["publicpurchase.com"],
    }

    # HTML signature patterns (for sites that embed/use portals)
    HTML_SIGNATURES = {
        PortalVendor.OPENGOV: [
            "opengov.com/procurement",
            "OpenGov Procurement",
            "opengov-procurement",
        ],
        PortalVendor.PROCURENOW: [
            "ProcureNow",
            "procurenow.com",
            "Bids & Tenders",
        ],
        PortalVendor.BONFIRE: [
            "Bonfire",
            "bonfirehub",
            "powered by Bonfire",
        ],
        PortalVendor.DEMANDSTAR: [
            "DemandStar",
            "demandstar.com",
        ],
        PortalVendor.PLANETBIDS: [
            "PlanetBids",
            "planetbids.com",
        ],
        PortalVendor.PUBLICPURCHASE: [
            "PublicPurchase",
            "publicpurchase.com",
        ],
    }

    def __init__(self):
        """Initialize detector."""
        self.crawler = Crawl4AIWrapper(enable_javascript=False)

    async def detect_portal_vendor(self, url: str) -> PortalVendor:
        """Detect portal vendor from URL.

        Args:
            url: URL to analyze

        Returns:
            PortalVendor enum value
        """
        logger.info(f"Detecting portal vendor for: {url}")

        # Step 1: Try domain-based detection (fast)
        domain_vendor = self._detect_by_domain(url)
        if domain_vendor != PortalVendor.UNKNOWN:
            logger.info(f"Detected by domain: {domain_vendor.value}")
            return domain_vendor

        # Step 2: Fetch page and check HTML signatures
        try:
            result = await self.crawler.fetch_page(url)
            html_content = result["html"].lower()

            for vendor, signatures in self.HTML_SIGNATURES.items():
                if any(sig.lower() in html_content for sig in signatures):
                    logger.info(f"Detected by HTML signature: {vendor.value}")
                    return vendor

        except Exception as e:
            logger.error(f"Error fetching page for detection: {str(e)}")

        # Step 3: If still unknown, check for common custom patterns
        if self._is_likely_custom_html(url):
            return PortalVendor.CUSTOM_HTML

        logger.info(f"Could not detect portal vendor for {url}")
        return PortalVendor.UNKNOWN

    def _detect_by_domain(self, url: str) -> PortalVendor:
        """Detect vendor by domain patterns."""
        url_lower = url.lower()

        for vendor, patterns in self.DOMAIN_PATTERNS.items():
            if any(pattern in url_lower for pattern in patterns):
                return vendor

        return PortalVendor.UNKNOWN

    def _is_likely_custom_html(self, url: str) -> bool:
        """Check if URL looks like a custom HTML page.

        Heuristics:
        - Government domain (.gov)
        - Path contains "procurement", "bids", "purchasing", "rfp"
        - Not a known portal vendor
        """
        url_lower = url.lower()

        is_gov = ".gov" in url_lower
        has_procurement_path = any(
            keyword in url_lower
            for keyword in ["procurement", "bids", "purchasing", "rfp", "rfq"]
        )

        return is_gov and has_procurement_path

    async def analyze_portal_features(self, url: str) -> dict:
        """Analyze portal features and requirements.

        Returns:
            Dict with:
                - requires_javascript: bool
                - has_search: bool
                - has_pagination: bool
                - authentication_required: bool
        """
        try:
            result = await self.crawler.fetch_page(url)
            html_lower = result["html"].lower()

            return {
                "requires_javascript": self._check_js_requirement(html_lower),
                "has_search": "search" in html_lower and ("form" in html_lower or "input" in html_lower),
                "has_pagination": any(
                    word in html_lower for word in ["pagination", "next page", "previous"]
                ),
                "authentication_required": any(
                    word in html_lower for word in ["login", "sign in", "register"]
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing portal features: {str(e)}")
            return {}

    def _check_js_requirement(self, html_content: str) -> bool:
        """Check if page likely requires JavaScript."""
        # Look for React, Angular, Vue, or heavy JS frameworks
        js_frameworks = [
            "react", "angular", "vue.js", "next.js",
            "__NEXT_DATA__", "ng-app", "data-reactroot"
        ]
        return any(framework in html_content for framework in js_frameworks)

    async def close(self):
        """Cleanup resources."""
        await self.crawler.close()
```

**Step 4: Run tests**

```bash
docker-compose exec backend pytest tests/test_discovery/test_portal_detector.py -v
```

Expected: PASS (some might be slow due to network fetches)

**Step 5: Commit portal detector**

```bash
git add backend/app/discovery/ backend/tests/test_discovery/
git commit -m "feat: add portal vendor detector with domain and HTML signature matching"
```

---

### Task 7: Entity Discovery Service

**Files:**
- Create: `backend/app/discovery/entity_finder.py`
- Create: `backend/scripts/discover_entities.py`

**Step 1: Create entity finder**

Create `backend/app/discovery/entity_finder.py`:
```python
"""Entity discovery service for finding new procurement portals."""
from typing import List, Dict, Any, Optional
import asyncio
from urllib.parse import urljoin, urlparse
import structlog

from app.crawlers.crawl4ai_wrapper import Crawl4AIWrapper
from app.discovery.portal_detector import PortalDetector
from app.models.source_registry import JurisdictionType, PortalVendor

logger = structlog.get_logger()


class EntityFinder:
    """Find new procurement portals via search and discovery."""

    # NJ county list
    NJ_COUNTIES = [
        "Atlantic", "Bergen", "Burlington", "Camden", "Cape May", "Cumberland",
        "Essex", "Gloucester", "Hudson", "Hunterdon", "Mercer", "Middlesex",
        "Monmouth", "Morris", "Ocean", "Passaic", "Salem", "Somerset",
        "Sussex", "Union", "Warren"
    ]

    # Major NJ cities
    NJ_MAJOR_CITIES = [
        "Newark", "Jersey City", "Paterson", "Elizabeth", "Edison",
        "Woodbridge", "Lakewood", "Toms River", "Hamilton", "Trenton",
        "Clifton", "Camden", "Brick", "Cherry Hill", "Passaic"
    ]

    # NY counties (downstate + major upstate)
    NY_COUNTIES = [
        "New York", "Kings", "Queens", "Bronx", "Richmond",  # NYC boroughs
        "Westchester", "Nassau", "Suffolk", "Rockland", "Orange",
        "Putnam", "Dutchess", "Erie", "Monroe", "Onondaga", "Albany"
    ]

    # Procurement page keywords
    PROCUREMENT_KEYWORDS = [
        "procurement", "purchasing", "bids", "rfp", "rfq", "ifb",
        "solicitations", "contracts", "current bids", "bid opportunities"
    ]

    def __init__(self):
        """Initialize finder."""
        self.crawler = Crawl4AIWrapper(enable_javascript=False)
        self.detector = PortalDetector()

    async def find_county_procurement_pages(
        self, state: str = "NJ"
    ) -> List[Dict[str, Any]]:
        """Find procurement pages for all counties in a state.

        Args:
            state: "NJ" or "NY"

        Returns:
            List of dicts with entity info and procurement URLs
        """
        counties = self.NJ_COUNTIES if state == "NJ" else self.NY_COUNTIES
        results = []

        for county in counties:
            logger.info(f"Searching for {county} County, {state} procurement page")

            try:
                entity_info = await self._discover_entity_portal(
                    entity_name=f"{county} County",
                    state=state,
                    jurisdiction_type=JurisdictionType.NJ_COUNTY
                    if state == "NJ"
                    else JurisdictionType.NY_COUNTY,
                )

                if entity_info:
                    results.append(entity_info)

                # Rate limiting
                await asyncio.sleep(2.0)

            except Exception as e:
                logger.error(f"Error discovering {county} County: {str(e)}")
                continue

        return results

    async def find_city_procurement_pages(
        self, cities: Optional[List[str]] = None, state: str = "NJ"
    ) -> List[Dict[str, Any]]:
        """Find procurement pages for cities.

        Args:
            cities: List of city names (defaults to major cities)
            state: "NJ" or "NY"

        Returns:
            List of dicts with entity info and procurement URLs
        """
        if cities is None:
            cities = self.NJ_MAJOR_CITIES if state == "NJ" else []

        results = []

        for city in cities:
            logger.info(f"Searching for {city}, {state} procurement page")

            try:
                entity_info = await self._discover_entity_portal(
                    entity_name=f"City of {city}",
                    state=state,
                    jurisdiction_type=JurisdictionType.NJ_CITY,
                )

                if entity_info:
                    results.append(entity_info)

                await asyncio.sleep(2.0)

            except Exception as e:
                logger.error(f"Error discovering {city}: {str(e)}")
                continue

        return results

    async def _discover_entity_portal(
        self,
        entity_name: str,
        state: str,
        jurisdiction_type: JurisdictionType,
    ) -> Optional[Dict[str, Any]]:
        """Discover procurement portal for a specific entity.

        Strategy:
        1. Try predictable URL patterns first
        2. If not found, use search
        3. Detect portal vendor
        4. Analyze features

        Returns:
            Dict with entity info or None if not found
        """
        # Try predictable URL patterns
        portal_url = await self._try_predictable_urls(entity_name, state)

        if not portal_url:
            logger.info(f"No predictable URL found for {entity_name}, skipping search for now")
            # In production, you'd integrate a search API here
            return None

        # Detect portal vendor
        portal_vendor = await self.detector.detect_portal_vendor(portal_url)

        # Analyze features
        features = await self.detector.analyze_portal_features(portal_url)

        return {
            "entity_name": entity_name,
            "jurisdiction": jurisdiction_type.value,
            "state": state,
            "portal_url": portal_url,
            "portal_vendor": portal_vendor.value,
            "requires_javascript": features.get("requires_javascript", False),
            "has_search": features.get("has_search", False),
            "discovery_method": "predictable_url",
        }

    async def _try_predictable_urls(self, entity_name: str, state: str) -> Optional[str]:
        """Try common URL patterns for procurement pages.

        Examples:
        - https://www.co.bergen.nj.us/procurement
        - https://www.cityofnewark.org/procurement
        """
        # Normalize entity name to URL slug
        name_slug = entity_name.lower().replace(" ", "").replace("city of ", "")

        patterns = []

        if "county" in entity_name.lower():
            county_name = entity_name.lower().replace(" county", "").replace("county of ", "")
            patterns = [
                f"https://www.co.{county_name}.{state.lower()}.us/procurement",
                f"https://www.co.{county_name}.{state.lower()}.us/purchasing",
                f"https://www.{county_name}county{state.lower()}.gov/procurement",
                f"https://www.{county_name}county.org/procurement",
            ]
        elif "city of" in entity_name.lower():
            city_name = entity_name.lower().replace("city of ", "")
            patterns = [
                f"https://www.cityof{city_name}.org/procurement",
                f"https://www.cityof{city_name}.com/purchasing",
                f"https://www.{city_name}.gov/procurement",
                f"https://www.{city_name}{state.lower()}.gov/cityhall/purchasing",
            ]

        # Try each pattern
        for url in patterns:
            try:
                result = await self.crawler.fetch_page(url)
                # Check if page looks like a procurement page
                html_lower = result["html"].lower()

                if any(keyword in html_lower for keyword in self.PROCUREMENT_KEYWORDS):
                    logger.info(f"Found procurement page: {url}")
                    return url

            except Exception:
                continue

        return None

    async def close(self):
        """Cleanup resources."""
        await self.crawler.close()
        await self.detector.close()
```

**Step 2: Create discovery script**

Create `backend/scripts/discover_entities.py`:
```python
"""Discover new procurement entities and add to registry."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.discovery.entity_finder import EntityFinder
from app.database import SessionLocal
from app.models.source_registry import SourceRegistry, JurisdictionType
import pandas as pd


async def discover_and_export():
    """Discover entities and export to CSV."""
    finder = EntityFinder()

    try:
        print("🔍 Discovering NJ county procurement pages...")
        nj_counties = await finder.find_county_procurement_pages(state="NJ")
        print(f"Found {len(nj_counties)} NJ county portals")

        print("\n🔍 Discovering NJ city procurement pages...")
        nj_cities = await finder.find_city_procurement_pages(state="NJ")
        print(f"Found {len(nj_cities)} NJ city portals")

        # Combine results
        all_entities = nj_counties + nj_cities

        # Export to CSV
        if all_entities:
            df = pd.DataFrame(all_entities)
            output_file = "discovered_entities.csv"
            df.to_csv(output_file, index=False)
            print(f"\n✅ Exported {len(all_entities)} entities to {output_file}")
            print("\nNext steps:")
            print("1. Review the CSV file")
            print("2. Manually verify URLs work")
            print("3. Use import script to add to source_registry")
        else:
            print("\n❌ No entities found")

    finally:
        await finder.close()


if __name__ == "__main__":
    asyncio.run(discover_and_export())
```

**Step 3: Run discovery script**

```bash
docker-compose exec backend python scripts/discover_entities.py
```

Expected: CSV file with discovered entities

**Step 4: Commit entity discovery**

```bash
git add backend/app/discovery/entity_finder.py backend/scripts/discover_entities.py
git commit -m "feat: add entity discovery service for finding procurement portals"
```

---

## Phase 4: Coverage Verification & Monitoring

### Task 8: Coverage Scorecard Service

**Files:**
- Create: `backend/app/services/coverage_service.py`
- Create: `backend/scripts/generate_weekly_scorecard.py`

**Step 1: Create coverage service**

Create `backend/app/services/coverage_service.py`:
```python
"""Coverage scorecard service for monitoring source health."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
import structlog

from app.models.coverage_scorecard import CoverageScorecard
from app.models.source_registry import SourceRegistry
from app.models.tender import Tender
from app.models.scrape_run import ScrapeRun, ScrapeRunStatus

logger = structlog.get_logger()


class CoverageService:
    """Service for coverage monitoring and anomaly detection."""

    def __init__(self, db: Session):
        """Initialize service."""
        self.db = db

    def generate_weekly_scorecard(
        self, week_start: datetime, week_end: datetime
    ) -> List[CoverageScorecard]:
        """Generate coverage scorecard for all sources for the week.

        Args:
            week_start: Start of week (datetime)
            week_end: End of week (datetime)

        Returns:
            List of CoverageScorecard objects
        """
        sources = self.db.query(SourceRegistry).filter(
            SourceRegistry.active == True
        ).all()

        scorecards = []

        for source in sources:
            scorecard = self._calculate_source_scorecard(
                source, week_start, week_end
            )
            self.db.add(scorecard)
            scorecards.append(scorecard)

        self.db.commit()
        return scorecards

    def _calculate_source_scorecard(
        self,
        source: SourceRegistry,
        week_start: datetime,
        week_end: datetime,
    ) -> CoverageScorecard:
        """Calculate scorecard for a single source."""

        # Count tenders scraped this week
        tenders_query = (
            self.db.query(Tender)
            .filter(
                Tender.source_id == source.id,
                Tender.scraped_at >= week_start,
                Tender.scraped_at < week_end,
            )
        )

        tenders_scraped = tenders_query.count()
        tenders_new = tenders_query.filter(
            Tender.scraped_at == Tender.updated_at
        ).count()
        tenders_updated = tenders_scraped - tenders_new

        # Get scrape run stats
        runs = (
            self.db.query(ScrapeRun)
            .filter(
                ScrapeRun.source_id == source.id,
                ScrapeRun.created_at >= week_start,
                ScrapeRun.created_at < week_end,
            )
            .all()
        )

        scrape_attempts = len(runs)
        scrape_successes = sum(
            1 for r in runs if r.status == ScrapeRunStatus.SUCCESS
        )
        scrape_failures = sum(
            1 for r in runs if r.status == ScrapeRunStatus.FAILED
        )

        # Calculate variance from expected
        expected_count = source.expected_monthly_postings or 0
        weekly_expected = int(expected_count / 4)  # Rough weekly estimate

        variance_pct = 0.0
        if weekly_expected > 0:
            variance_pct = ((tenders_scraped - weekly_expected) / weekly_expected) * 100

        # Detect anomalies
        is_anomaly, anomaly_details = self._detect_anomaly(
            tenders_scraped,
            weekly_expected,
            scrape_failures,
            scrape_attempts,
        )

        # Sentinel check (look for construction-related keywords)
        sentinel_hits = tenders_query.filter(
            func.lower(Tender.title).contains("construction")
            | func.lower(Tender.title).contains("building")
            | func.lower(Tender.description_text).contains("construction")
        ).count()

        scorecard = CoverageScorecard(
            source_registry_id=source.id,
            week_start=week_start,
            week_end=week_end,
            tenders_scraped=tenders_scraped,
            tenders_new=tenders_new,
            tenders_updated=tenders_updated,
            expected_count=weekly_expected,
            actual_count=tenders_scraped,
            variance_pct=variance_pct,
            scrape_attempts=scrape_attempts,
            scrape_successes=scrape_successes,
            scrape_failures=scrape_failures,
            is_anomaly=is_anomaly,
            anomaly_details=anomaly_details,
            sentinel_keywords=["construction", "building"],
            sentinel_hits=sentinel_hits,
        )

        return scorecard

    def _detect_anomaly(
        self,
        actual_count: int,
        expected_count: int,
        failures: int,
        attempts: int,
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """Detect if metrics indicate an anomaly.

        Returns:
            Tuple of (anomaly_type, details_dict)
        """
        # Zero results
        if actual_count == 0 and expected_count > 0:
            return "zero_results", {
                "message": "No tenders found when some were expected",
                "expected": expected_count,
            }

        # High failure rate
        if attempts > 0 and (failures / attempts) > 0.5:
            return "high_failure_rate", {
                "message": f"{failures}/{attempts} scrapes failed",
                "failure_rate": failures / attempts,
            }

        # Low count (< 50% of expected)
        if expected_count > 0 and actual_count < (expected_count * 0.5):
            return "low_count", {
                "message": f"Only {actual_count} tenders vs {expected_count} expected",
                "variance_pct": ((actual_count - expected_count) / expected_count) * 100,
            }

        # High count (> 200% of expected, might indicate duplicate scraping)
        if expected_count > 0 and actual_count > (expected_count * 2.0):
            return "high_count", {
                "message": f"{actual_count} tenders vs {expected_count} expected",
                "possible_cause": "Duplicate scraping or major event",
            }

        return "ok", None

    def get_anomalies(
        self, week_start: Optional[datetime] = None
    ) -> List[CoverageScorecard]:
        """Get all anomalies for a given week.

        Args:
            week_start: Start of week (defaults to last week)

        Returns:
            List of scorecards with anomalies
        """
        if week_start is None:
            week_start = datetime.utcnow() - timedelta(days=7)

        return (
            self.db.query(CoverageScorecard)
            .filter(
                CoverageScorecard.week_start == week_start,
                CoverageScorecard.is_anomaly != "ok",
            )
            .all()
        )

    def get_scorecard_summary(self, week_start: datetime) -> Dict[str, Any]:
        """Get summary statistics for the week.

        Returns:
            Dict with overall stats
        """
        scorecards = (
            self.db.query(CoverageScorecard)
            .filter(CoverageScorecard.week_start == week_start)
            .all()
        )

        total_sources = len(scorecards)
        total_tenders = sum(s.tenders_scraped for s in scorecards)
        total_new = sum(s.tenders_new for s in scorecards)
        anomalies = [s for s in scorecards if s.is_anomaly != "ok"]

        return {
            "week_start": week_start.isoformat(),
            "total_sources_monitored": total_sources,
            "total_tenders_scraped": total_tenders,
            "total_tenders_new": total_new,
            "sources_with_anomalies": len(anomalies),
            "anomalies_by_type": {
                anomaly_type: len([s for s in anomalies if s.is_anomaly == anomaly_type])
                for anomaly_type in set(s.is_anomaly for s in anomalies)
            },
        }
```

**Step 2: Create weekly scorecard script**

Create `backend/scripts/generate_weekly_scorecard.py`:
```python
"""Generate weekly coverage scorecard."""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.services.coverage_service import CoverageService


def generate_scorecard():
    """Generate weekly scorecard."""
    db = SessionLocal()

    try:
        service = CoverageService(db)

        # Get last week's date range
        today = datetime.utcnow()
        week_start = today - timedelta(days=7)
        week_end = today

        print(f"📊 Generating coverage scorecard for {week_start.date()} to {week_end.date()}")

        # Generate scorecards
        scorecards = service.generate_weekly_scorecard(week_start, week_end)
        print(f"✅ Generated {len(scorecards)} scorecards")

        # Get summary
        summary = service.get_scorecard_summary(week_start)
        print("\n📈 Summary:")
        print(f"  Sources monitored: {summary['total_sources_monitored']}")
        print(f"  Tenders scraped: {summary['total_tenders_scraped']}")
        print(f"  New tenders: {summary['total_tenders_new']}")
        print(f"  Sources with anomalies: {summary['sources_with_anomalies']}")

        # Get and display anomalies
        anomalies = service.get_anomalies(week_start)
        if anomalies:
            print("\n⚠️  Anomalies detected:")
            for scorecard in anomalies:
                source = scorecard.source
                print(f"\n  {source.entity_name} ({source.portal_vendor.value})")
                print(f"    Type: {scorecard.is_anomaly}")
                print(f"    Details: {scorecard.anomaly_details}")
                print(f"    Expected: {scorecard.expected_count}, Actual: {scorecard.actual_count}")
        else:
            print("\n✅ No anomalies detected!")

    finally:
        db.close()


if __name__ == "__main__":
    generate_scorecard()
```

**Step 3: Run scorecard generation**

```bash
docker-compose exec backend python scripts/generate_weekly_scorecard.py
```

Expected: Scorecard with summary and anomalies

**Step 4: Commit coverage service**

```bash
git add backend/app/services/coverage_service.py backend/scripts/generate_weekly_scorecard.py
git commit -m "feat: add coverage scorecard service for monitoring source health"
```

---

## Phase 5: Operational Workflows

### Task 9: Daily Operations Script

**Files:**
- Create: `backend/scripts/daily_operations.py`
- Create: `docs/operations/DAILY_CHECKLIST.md`

**Step 1: Create daily operations script**

Create `backend/scripts/daily_operations.py`:
```python
"""Daily operations script - run this every day."""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.services.coverage_service import CoverageService
from app.models.source_registry import SourceRegistry
from app.worker.tasks import scrape_source


async def run_daily_operations():
    """Execute daily operational tasks."""
    db = SessionLocal()
    print(f"🌅 Starting daily operations - {datetime.utcnow().date()}\n")

    try:
        # 1. Run all active scrapers
        print("1️⃣ Triggering scrapers for all active sources...")
        sources = db.query(SourceRegistry).filter(
            SourceRegistry.active == True
        ).all()

        tasks_queued = 0
        for source in sources:
            scrape_source.delay(str(source.id))
            tasks_queued += 1

        print(f"   ✅ Queued {tasks_queued} scraping tasks\n")

        # 2. Check for sources with consecutive failures
        print("2️⃣ Checking for sources with failures...")
        failing_sources = db.query(SourceRegistry).filter(
            SourceRegistry.consecutive_failures > 3,
            SourceRegistry.active == True,
        ).all()

        if failing_sources:
            print(f"   ⚠️  {len(failing_sources)} sources have 3+ consecutive failures:")
            for source in failing_sources:
                print(f"      - {source.entity_name}: {source.consecutive_failures} failures")
                print(f"        Last success: {source.last_successful_scrape}")
        else:
            print("   ✅ No sources with repeated failures\n")

        # 3. Coverage anomaly check (last 7 days)
        print("3️⃣ Checking for coverage anomalies...")
        coverage_service = CoverageService(db)
        week_start = datetime.utcnow() - timedelta(days=7)
        anomalies = coverage_service.get_anomalies(week_start)

        if anomalies:
            print(f"   ⚠️  {len(anomalies)} sources with anomalies in last 7 days:")
            for scorecard in anomalies[:5]:  # Show top 5
                source = scorecard.source
                print(f"      - {source.entity_name}: {scorecard.is_anomaly}")
        else:
            print("   ✅ No coverage anomalies detected\n")

        # 4. Summary stats
        print("4️⃣ System summary:")
        total_sources = db.query(SourceRegistry).count()
        active_sources = db.query(SourceRegistry).filter(
            SourceRegistry.active == True
        ).count()
        print(f"   Total sources: {total_sources}")
        print(f"   Active sources: {active_sources}")
        print(f"   Inactive sources: {total_sources - active_sources}")

        print("\n✅ Daily operations complete!")
        print("\nNext steps:")
        print("  - Monitor scraping task progress in logs")
        print("  - Review any anomalies or failures")
        print("  - Check admin dashboard for details")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(run_daily_operations())
```

**Step 2: Create daily checklist document**

Create `docs/operations/DAILY_CHECKLIST.md`:
```markdown
# Daily Operations Checklist

## Automated (via script)
Run this daily at 6 AM EST:
```bash
docker-compose exec backend python scripts/daily_operations.py
```

This automatically:
- ✅ Triggers scrapers for all active sources
- ✅ Identifies sources with consecutive failures
- ✅ Detects coverage anomalies
- ✅ Provides system summary

## Manual Review (15 minutes)

### 1. Check Scraper Health
- Open admin dashboard: http://localhost:8000/api/v1/admin/scrape-runs
- Review recent scrape runs
- Investigate any failures

### 2. Anomaly Investigation
If anomalies detected:
- Visit the source's portal manually
- Verify tenders are actually posted
- Check if page structure changed
- Update scraper if needed

### 3. Sample Verification (10 entities)
Randomly select 10 sources and manually verify:
```bash
docker-compose exec backend python scripts/verify_sample.py
```

Compare:
- Our system's count for today
- Actual count on the portal

### 4. Coverage Report
Generate and review weekly scorecard:
```bash
docker-compose exec backend python scripts/generate_weekly_scorecard.py
docker-compose exec backend python scripts/export_registry_to_excel.py
```

Review the Excel export for:
- Sources with zero results
- Variance from expected counts
- Failed scrapes

## Weekly Operations (Every Monday)

### 1. Add New Sources (30-60 min)
Run discovery pipeline:
```bash
docker-compose exec backend python scripts/discover_entities.py
```

Review discovered_entities.csv:
- Manually verify URLs work
- Check portal vendor detection
- Add high-priority sources to registry

### 2. Update Expected Counts
Review historical data and update expected_monthly_postings:
```sql
UPDATE source_registry
SET expected_monthly_postings = <new_value>
WHERE entity_name = '<entity>';
```

### 3. Portal Adapter Expansion
Identify common portal vendors from discoveries:
```bash
SELECT portal_vendor, COUNT(*) as count
FROM source_registry
WHERE active = false
GROUP BY portal_vendor
ORDER BY count DESC;
```

Build adapters for top vendors.

## Monthly Operations (First Monday)

### 1. Full Coverage Audit
- Review all sources in registry
- Verify active sources are still publishing
- Deactivate sources that have stopped posting
- Update contact information

### 2. Quality Metrics
Generate monthly report:
- Total tenders scraped
- Coverage by jurisdiction
- Scraper reliability (success rate)
- New sources added

### 3. User Feedback
Review user-reported issues:
- Missing opportunities
- Parsing errors
- Search/filter problems

## Emergency Procedures

### Source Completely Down
1. Mark source as inactive temporarily
2. Document in notes field
3. Set up monitoring alert
4. Re-enable when confirmed back online

### Major Portal Change
1. Create new scraper version
2. Test in isolation
3. Run parallel with old version
4. Switch when validated
5. Archive old version

### Data Quality Issue
1. Identify affected time range
2. Mark affected tenders for review
3. Re-scrape if needed
4. Update AI enrichment if stale
```

**Step 3: Commit operations documentation**

```bash
git add backend/scripts/daily_operations.py docs/operations/
git commit -m "feat: add daily operations script and operations checklist"
```

---

## Summary & Final Artifacts

This plan provides:

1. **Source Registry Database** - Track all 100+ procurement portals
2. **Coverage Scorecard** - Monitor health and detect anomalies
3. **Crawl4AI Integration** - Robust scraping with JS support
4. **Portal Vendor Detection** - Automatically classify portal types
5. **Entity Discovery** - Systematically find new sources
6. **Operational Workflows** - Daily, weekly, monthly procedures

### Key Files Created:
```
backend/
├── app/
│   ├── models/
│   │   ├── source_registry.py          # Portal tracking
│   │   └── coverage_scorecard.py       # Health monitoring
│   ├── crawlers/
│   │   └── crawl4ai_wrapper.py         # Crawl4AI integration
│   ├── scrapers/
│   │   └── crawl4ai_scraper.py         # Base class using Crawl4AI
│   ├── discovery/
│   │   ├── portal_detector.py          # Auto-detect portal vendor
│   │   └── entity_finder.py            # Discover new entities
│   └── services/
│       └── coverage_service.py         # Coverage monitoring
├── scripts/
│   ├── export_registry_to_excel.py     # Excel export
│   ├── discover_entities.py            # Entity discovery
│   ├── generate_weekly_scorecard.py    # Weekly report
│   └── daily_operations.py             # Daily automation
docs/
├── templates/
│   ├── source-registry-template.csv
│   ├── coverage-scorecard-template.csv
│   └── discovery-checklist.csv
└── operations/
    └── DAILY_CHECKLIST.md
```

### Execution Strategy:

**Week 1: Foundation**
- Tasks 1-3: Database schema and spreadsheets
- Tasks 4-5: Crawl4AI integration
- Run: `docker-compose exec backend python scripts/export_registry_to_excel.py`

**Week 2: Discovery**
- Tasks 6-7: Portal detection and entity discovery
- Run: `docker-compose exec backend python scripts/discover_entities.py`
- Manual: Review discovered_entities.csv, add verified sources

**Week 3: Monitoring**
- Task 8: Coverage scorecard service
- Task 9: Daily operations script
- Setup: Cron job for daily_operations.py at 6 AM

**Ongoing: Expand Coverage**
- Add 5-20 new sources per week
- Build portal adapters as patterns emerge
- Maintain 95%+ coverage score

Would you like me to:
1. Start implementation in a parallel session?
2. Create additional detailed specs for any component?
3. Add more discovery strategies (Google Custom Search API, etc.)?
