"""Standalone scraper test - no database or app context needed.

Tests the actual HTTP fetching and HTML parsing of each scraper
against the real government portals.
"""
import asyncio
import sys
import json
from datetime import datetime

import httpx
from bs4 import BeautifulSoup


async def test_nyc_passport():
    """Test NYC PASSPort portal scraping."""
    print("\n" + "=" * 60)
    print("TESTING: NYC PASSPort Portal")
    print("URL: https://www1.nyc.gov/site/mocs/public-rfx/public-rfx.page")
    print("=" * 60)

    url = "https://www1.nyc.gov/site/mocs/public-rfx/public-rfx.page"

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            print(f"\n[1] Fetching page...")
            response = await client.get(url)
            print(f"    Status: {response.status_code}")
            print(f"    Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"    Content length: {len(response.text):,} chars")

            if response.status_code != 200:
                print(f"    ERROR: Non-200 status code")
                # Check if redirected
                print(f"    Final URL: {response.url}")
                return

            print(f"\n[2] Parsing HTML...")
            soup = BeautifulSoup(response.text, "lxml")
            title = soup.title.string if soup.title else "No title"
            print(f"    Page title: {title}")

            # Try various selectors to find bid listings
            selectors_to_try = [
                (".rfx-listing-item", "rfx-listing-item"),
                ("tr.rfx-row", "rfx-row"),
                ("div[class*='opportunity']", "opportunity div"),
                ("table.table tbody tr", "table rows"),
                (".table-responsive tbody tr", "responsive table rows"),
                ("a[href*='passport']", "passport links"),
                ("a[href*='rfx']", "rfx links"),
                ("a[href*='solicitation']", "solicitation links"),
                (".about-description a", "about-description links"),
                ("#block-system-main a", "main block links"),
                (".view-content .views-row", "views rows"),
                (".field-content", "field content"),
            ]

            print(f"\n[3] Searching for bid listings...")
            found_any = False
            for selector, name in selectors_to_try:
                items = soup.select(selector)
                if items:
                    print(f"    FOUND {len(items)} items with: {selector} ({name})")
                    found_any = True
                    # Show first few items
                    for i, item in enumerate(items[:3]):
                        text = item.get_text(strip=True)[:120]
                        href = item.get("href", "N/A") if item.name == "a" else "N/A"
                        link = item.select_one("a")
                        if link:
                            href = link.get("href", "N/A")
                        print(f"      [{i+1}] {text}")
                        if href != "N/A":
                            print(f"          Link: {href}")

            if not found_any:
                print("    No items found with standard selectors.")
                print(f"\n[4] Page structure analysis...")
                # Show all links on the page that might be bids
                all_links = soup.select("a[href]")
                bid_links = [a for a in all_links if any(
                    kw in (a.get("href", "") + " " + a.get_text()).lower()
                    for kw in ["bid", "rfx", "solicitation", "procurement", "contract", "opportunity"]
                )]
                print(f"    Total links on page: {len(all_links)}")
                print(f"    Procurement-related links: {len(bid_links)}")
                for i, link in enumerate(bid_links[:10]):
                    print(f"      [{i+1}] {link.get_text(strip=True)[:80]}")
                    print(f"          {link.get('href', '')}")

            print(f"\n    RESULT: {'DATA FOUND' if found_any else 'NEEDS SELECTOR UPDATE'}")
            return found_any

    except Exception as e:
        print(f"    FAILED: {str(e)}")
        return False


async def test_nys_ogs():
    """Test NYS OGS portal scraping."""
    print("\n" + "=" * 60)
    print("TESTING: NYS Office of General Services")
    print("URL: https://online.ogs.ny.gov/purchase/spg/")
    print("=" * 60)

    url = "https://online.ogs.ny.gov/purchase/spg/"

    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            print(f"\n[1] Fetching page...")
            response = await client.get(url)
            print(f"    Status: {response.status_code}")
            print(f"    Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"    Content length: {len(response.text):,} chars")
            print(f"    Final URL: {response.url}")

            if response.status_code != 200:
                print(f"    ERROR: Non-200 status code")
                return False

            print(f"\n[2] Parsing HTML...")
            soup = BeautifulSoup(response.text, "lxml")
            title = soup.title.string if soup.title else "No title"
            print(f"    Page title: {title}")

            selectors_to_try = [
                ("tr.bid-row", "bid-row"),
                ("div.bid-item", "bid-item"),
                ("table tbody tr", "table rows"),
                ("a[href*='bid']", "bid links"),
                ("a[href*='contract']", "contract links"),
                ("a[href*='solicitation']", "solicitation links"),
                (".contentArea a", "content area links"),
                ("#content a", "content links"),
            ]

            print(f"\n[3] Searching for bid listings...")
            found_any = False
            for selector, name in selectors_to_try:
                items = soup.select(selector)
                if items:
                    print(f"    FOUND {len(items)} items with: {selector} ({name})")
                    found_any = True
                    for i, item in enumerate(items[:3]):
                        text = item.get_text(strip=True)[:120]
                        href = item.get("href", "N/A") if item.name == "a" else "N/A"
                        link = item.select_one("a")
                        if link:
                            href = link.get("href", "N/A")
                        print(f"      [{i+1}] {text}")
                        if href != "N/A":
                            print(f"          Link: {href}")

            if not found_any:
                print("    No items found with standard selectors.")
                print(f"\n[4] Page structure analysis...")
                all_links = soup.select("a[href]")
                procurement_links = [a for a in all_links if any(
                    kw in (a.get("href", "") + " " + a.get_text()).lower()
                    for kw in ["bid", "solicitation", "procurement", "contract", "opportunity", "purchase"]
                )]
                print(f"    Total links on page: {len(all_links)}")
                print(f"    Procurement-related links: {len(procurement_links)}")
                for i, link in enumerate(procurement_links[:10]):
                    print(f"      [{i+1}] {link.get_text(strip=True)[:80]}")
                    print(f"          {link.get('href', '')}")

            print(f"\n    RESULT: {'DATA FOUND' if found_any else 'NEEDS SELECTOR UPDATE'}")
            return found_any

    except Exception as e:
        print(f"    FAILED: {str(e)}")
        return False


async def test_additional_sources():
    """Test additional NY/NJ procurement portals to find working sources."""
    sources = [
        {
            "name": "NYC DDC (Design & Construction)",
            "url": "https://www1.nyc.gov/site/ddc/about/bids-proposals.page",
        },
        {
            "name": "NJ Treasury - Bid Solicitations",
            "url": "https://www.state.nj.us/treasury/purchase/bid/summary/all.shtml",
        },
        {
            "name": "Port Authority of NY & NJ",
            "url": "https://www.panynj.gov/port-authority/en/business-opportunities/solicitations-702.html",
        },
    ]

    print("\n" + "=" * 60)
    print("TESTING: Additional Procurement Sources")
    print("=" * 60)

    results = {}

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for source in sources:
            print(f"\n--- {source['name']} ---")
            print(f"    URL: {source['url']}")
            try:
                response = await client.get(source["url"])
                print(f"    Status: {response.status_code}")
                print(f"    Final URL: {response.url}")
                print(f"    Content length: {len(response.text):,} chars")

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    title = soup.title.string if soup.title else "No title"
                    print(f"    Page title: {title}")

                    # Count links that look procurement-related
                    all_links = soup.select("a[href]")
                    bid_links = [a for a in all_links if any(
                        kw in (a.get("href", "") + " " + a.get_text()).lower()
                        for kw in ["bid", "solicitation", "procurement", "contract", "rfp", "rfq"]
                    )]
                    print(f"    Total links: {len(all_links)}")
                    print(f"    Procurement links: {len(bid_links)}")

                    # Show sample
                    for link in bid_links[:3]:
                        print(f"      -> {link.get_text(strip=True)[:80]}")

                    results[source["name"]] = {
                        "status": "OK",
                        "procurement_links": len(bid_links),
                    }
                else:
                    results[source["name"]] = {"status": f"HTTP {response.status_code}"}

            except Exception as e:
                print(f"    ERROR: {str(e)}")
                results[source["name"]] = {"status": f"ERROR: {str(e)[:60]}"}

    return results


async def main():
    print("=" * 60)
    print("  TriState Public Works Finder - Scraper Test Suite")
    print(f"  Running at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    nyc_ok = await test_nyc_passport()
    nys_ok = await test_nys_ogs()
    additional = await test_additional_sources()

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  NYC PASSPort:  {'PASS' if nyc_ok else 'NEEDS WORK'}")
    print(f"  NYS OGS:       {'PASS' if nys_ok else 'NEEDS WORK'}")
    for name, result in additional.items():
        status = result.get("status", "UNKNOWN")
        links = result.get("procurement_links", 0)
        indicator = "VIABLE" if links > 5 else "CHECK"
        print(f"  {name}: {status} ({links} procurement links) [{indicator}]")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
