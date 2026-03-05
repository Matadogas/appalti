"""Live test of all scrapers - no database required.

Instantiates each scraper directly and runs it against real government portals.
Shows exactly what data each scraper extracts.
"""
import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scrapers.sources.port_authority import PortAuthorityScraper
from app.scrapers.sources.nyc_passport import NYCPassportScraper
from app.scrapers.sources.nys_ogs import NYSOGSScraper


def print_tender(tender, index: int):
    """Pretty-print a single tender."""
    print(f"\n  [{index}] {tender.title[:90]}")
    print(f"      URL: {tender.source_url[:80]}")
    print(f"      Agency: {tender.agency}")
    print(f"      State: {tender.state} | City: {tender.city or 'N/A'}")
    print(f"      Category: {tender.category.value}")
    print(f"      Status: {tender.status.value}")
    if tender.due_date:
        print(f"      Due: {tender.due_date.strftime('%Y-%m-%d')}")
    if tender.publish_date:
        print(f"      Published: {tender.publish_date.strftime('%Y-%m-%d')}")
    if tender.raw_ref:
        ref = tender.raw_ref.get("reference_number") or tender.raw_ref.get("bid_number") or ""
        if ref:
            print(f"      Ref#: {ref}")


async def test_scraper(scraper_class, name: str) -> int:
    """Test a single scraper and return the number of tenders found."""
    print(f"\n{'=' * 70}")
    print(f"  TESTING: {name}")
    print(f"  Scraper class: {scraper_class.__name__}")
    print(f"{'=' * 70}")

    scraper = scraper_class()
    try:
        tenders = await scraper.scrape()
        print(f"\n  RESULT: {len(tenders)} tenders scraped successfully")

        # Show first 5 tenders
        for i, tender in enumerate(tenders[:5], 1):
            print_tender(tender, i)

        if len(tenders) > 5:
            print(f"\n  ... and {len(tenders) - 5} more tenders")

        # Category breakdown
        categories = {}
        for t in tenders:
            cat = t.category.value
            categories[cat] = categories.get(cat, 0) + 1
        if categories:
            print(f"\n  Categories: {json.dumps(categories)}")

        return len(tenders)

    except Exception as e:
        print(f"\n  FAILED: {type(e).__name__}: {str(e)}")
        return 0


async def main():
    print("=" * 70)
    print("  TriState Bids - Live Scraper Test")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    scrapers = [
        (PortAuthorityScraper, "Port Authority of NY & NJ (Bonfire JSON API)"),
        (NYCPassportScraper, "NYC PASSPort (ASP.NET Portal)"),
        (NYSOGSScraper, "NYS OGS (Drupal Table)"),
    ]

    results = {}
    for scraper_class, name in scrapers:
        count = await test_scraper(scraper_class, name)
        results[name] = count

    print(f"\n{'=' * 70}")
    print("  SUMMARY")
    print(f"{'=' * 70}")
    total = 0
    for name, count in results.items():
        status = "WORKING" if count > 0 else "NO DATA"
        print(f"  {name}:")
        print(f"    {count} tenders [{status}]")
        total += count
    print(f"\n  TOTAL: {total} tenders across all sources")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(main())
