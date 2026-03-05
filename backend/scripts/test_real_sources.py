"""Test the REAL, current government procurement portal URLs."""
import asyncio
import json
from datetime import datetime

import httpx
from bs4 import BeautifulSoup


async def test_port_authority_api():
    """Port Authority Bonfire JSON API - confirmed working."""
    print("\n" + "=" * 60)
    print("TEST 1: Port Authority of NY & NJ (Bonfire JSON API)")
    print("=" * 60)

    url = "https://panynj.bonfirehub.com/PublicPortal/getOpenPublicOpportunitiesSectionData"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")

        if response.status_code == 200:
            data = response.json()
            print(f"Type of response: {type(data)}")
            if isinstance(data, list):
                print(f"Total sections: {len(data)}")
                total_opps = 0
                for section in data:
                    name = section.get("name", "Unknown")
                    opps = section.get("opportunities", [])
                    total_opps += len(opps)
                    print(f"  Section: {name} ({len(opps)} opportunities)")
                    for opp in opps[:2]:
                        print(f"    - {opp.get('name', 'N/A')}")
                        print(f"      Ref: {opp.get('referenceNumber', 'N/A')}")
                        print(f"      Closes: {opp.get('closureDate', 'N/A')}")
                print(f"\nTOTAL OPPORTUNITIES: {total_opps}")
            elif isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
                print(json.dumps(data, indent=2)[:500])
            return True
        else:
            print(f"FAILED: {response.text[:200]}")
            return False


async def test_nyc_passport():
    """NYC PASSPort - new URL."""
    print("\n" + "=" * 60)
    print("TEST 2: NYC PASSPort (New URL)")
    print("=" * 60)

    url = "https://passport.cityofnewyork.us/page.aspx/en/rfp/request_browse_public"

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        print(f"Status: {response.status_code}")
        print(f"Final URL: {response.url}")
        print(f"Content length: {len(response.text):,} chars")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            title = soup.title.string if soup.title else "No title"
            print(f"Page title: {title}")

            # Look for GridView / table data
            tables = soup.select("table")
            print(f"Tables found: {len(tables)}")

            # Look for any bid/RFP rows
            rows = soup.select("tr")
            print(f"Table rows: {len(rows)}")

            # Check for AJAX-loaded content indicators
            scripts = soup.select("script")
            for s in scripts:
                src = s.get("src", "")
                text = s.string or ""
                if "ajax" in src.lower() or "ajax" in text[:200].lower():
                    print(f"  AJAX script found: {src[:80] or text[:80]}")

            # Look for links
            links = soup.select("a[href]")
            rfp_links = [a for a in links if any(kw in (a.get("href", "") + a.get_text()).lower() for kw in ["rfp", "rfx", "solicitation", "bid", "request"])]
            print(f"RFP-related links: {len(rfp_links)}")
            for l in rfp_links[:5]:
                print(f"  -> {l.get_text(strip=True)[:60]}: {l.get('href', '')[:80]}")

            return len(rows) > 5 or len(rfp_links) > 0
        return False


async def test_nys_ogs():
    """NYS OGS - new URL."""
    print("\n" + "=" * 60)
    print("TEST 3: NYS OGS Bid Opportunities (New URL)")
    print("=" * 60)

    url = "https://ogs.ny.gov/procurement/bid-opportunities"

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        print(f"Status: {response.status_code}")
        print(f"Final URL: {response.url}")
        print(f"Content length: {len(response.text):,} chars")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            title = soup.title.string if soup.title else "No title"
            print(f"Page title: {title}")

            # Look for bid tables/lists
            tables = soup.select("table")
            print(f"Tables: {len(tables)}")

            for i, table in enumerate(tables[:3]):
                rows = table.select("tr")
                print(f"  Table {i}: {len(rows)} rows")
                for row in rows[:2]:
                    cells = row.select("td, th")
                    text = " | ".join(c.get_text(strip=True)[:30] for c in cells)
                    print(f"    {text}")

            # Look for bid links
            links = soup.select("a[href]")
            bid_links = [a for a in links if any(kw in (a.get("href", "") + a.get_text()).lower() for kw in ["bid", "solicitation", "contract", "group"])]
            print(f"Bid-related links: {len(bid_links)}")
            for l in bid_links[:5]:
                print(f"  -> {l.get_text(strip=True)[:60]}: {l.get('href', '')[:80]}")

            return len(tables) > 0 or len(bid_links) > 0
        return False


async def test_nyc_city_record():
    """NYC City Record Online - DDC bids."""
    print("\n" + "=" * 60)
    print("TEST 4: NYC City Record Online (DDC Agency Code 069)")
    print("=" * 60)

    url = "https://a856-cityrecord.nyc.gov/Search"

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text):,} chars")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            title = soup.title.string if soup.title else "No title"
            print(f"Page title: {title}")

            # Check for search form
            forms = soup.select("form")
            print(f"Forms: {len(forms)}")
            selects = soup.select("select")
            print(f"Dropdowns: {len(selects)}")
            for s in selects:
                name = s.get("name", s.get("id", "unnamed"))
                options = s.select("option")
                print(f"  {name}: {len(options)} options")

            return True
        return False


async def main():
    print("=" * 60)
    print("  TriState Bids - Real Source URL Testing")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    r1 = await test_port_authority_api()
    r2 = await test_nyc_passport()
    r3 = await test_nys_ogs()
    r4 = await test_nyc_city_record()

    print("\n" + "=" * 60)
    print("  RESULTS")
    print("=" * 60)
    print(f"  Port Authority JSON API: {'WORKING' if r1 else 'FAILED'}")
    print(f"  NYC PASSPort:            {'ACCESSIBLE' if r2 else 'FAILED'}")
    print(f"  NYS OGS:                 {'ACCESSIBLE' if r3 else 'FAILED'}")
    print(f"  NYC City Record:         {'ACCESSIBLE' if r4 else 'FAILED'}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
