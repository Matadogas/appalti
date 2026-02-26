"""Test NYC PASSPort scraper."""
import pytest
from app.scrapers.sources.nyc_passport import NYCPassportScraper


class TestNYCPassportScraper:
    """Test NYC PASSPort scraper."""

    def test_get_source_name(self):
        """Test source name."""
        scraper = NYCPassportScraper()
        assert scraper.get_source_name() == "nyc_passport"

    @pytest.mark.asyncio
    async def test_scrape_returns_list(self):
        """Test scrape returns list of tenders."""
        scraper = NYCPassportScraper()
        tenders = await scraper.scrape()
        assert isinstance(tenders, list)

    @pytest.mark.asyncio
    async def test_scraped_tenders_have_required_fields(self):
        """Test scraped tenders have required fields."""
        scraper = NYCPassportScraper()
        tenders = await scraper.scrape()

        if len(tenders) > 0:
            tender = tenders[0]
            assert tender.source_url
            assert tender.title
            assert tender.state == "NY"
            assert tender.city == "New York"
