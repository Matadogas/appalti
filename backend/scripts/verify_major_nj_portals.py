"""Manual verification of major NJ procurement portals.

This script validates the top 30+ major NJ portals to give us
50-70% coverage of all NJ construction RFPs.
"""
import sys
import asyncio
import json
import csv
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class MajorPortalVerifier:
    """Verify major NJ procurement portals."""

    def __init__(self):
        self.construction_keywords = [
            "construction", "contractor", "building", "infrastructure",
            "public works", "roadwork", "highway", "bridge",
            "demolition", "excavation", "concrete", "paving",
        ]

        self.procurement_keywords = [
            "rfp", "rfq", "ifb", "bid", "solicitation", "procurement",
            "purchasing", "contract", "proposal",
        ]

    async def try_urls(
        self,
        client: httpx.AsyncClient,
        urls: List[str],
    ) -> Optional[Dict]:
        """Try multiple URLs for a portal, return first working one.

        Args:
            client: HTTP client
            urls: List of URLs to try

        Returns:
            Dict with working URL and page info, or None
        """
        for url in urls:
            try:
                response = await client.get(
                    url,
                    follow_redirects=True,
                    timeout=15.0,
                )

                if response.status_code == 200:
                    return {
                        "original_url": url,
                        "final_url": str(response.url),
                        "status_code": 200,
                        "html": response.text,
                        "accessible": True,
                    }

            except:
                continue

        # All URLs failed
        return {
            "original_url": urls[0],
            "final_url": None,
            "status_code": None,
            "html": None,
            "accessible": False,
        }

    def analyze_page(
        self,
        html: str,
        url: str,
    ) -> Dict:
        """Analyze procurement page for RFPs and construction content.

        Args:
            html: Page HTML
            url: Page URL

        Returns:
            Analysis dict with RFP counts, links, etc.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Get page text
        page_text = soup.get_text().lower()

        # Count procurement keywords
        procurement_mentions = sum(
            page_text.count(kw) for kw in self.procurement_keywords
        )

        # Count construction keywords
        construction_mentions = sum(
            page_text.count(kw) for kw in self.construction_keywords
        )

        has_construction = construction_mentions >= 3

        # Find RFP/bid links
        rfp_links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            link_text = a_tag.get_text(strip=True).lower()

            # Check if likely an RFP link
            is_rfp = any(kw in link_text or kw in href.lower() for kw in ["rfp", "rfq", "bid", "solicitation"])

            if is_rfp and link_text:
                # Make absolute URL
                from urllib.parse import urljoin
                absolute_url = urljoin(url, href)

                # Check if construction-related
                is_construction = any(kw in link_text for kw in self.construction_keywords)

                rfp_links.append({
                    "text": link_text[:100],
                    "url": absolute_url,
                    "is_construction": is_construction,
                })

        # Look for tables (common in bid listings)
        tables = soup.find_all("table")
        table_count = len(tables)
        table_rows = sum(len(table.find_all("tr")) for table in tables)

        # Estimate RFP count
        rfp_count_estimate = min(len(rfp_links) + (table_rows // 2), 200)

        return {
            "title": title,
            "procurement_mentions": procurement_mentions,
            "construction_mentions": construction_mentions,
            "has_construction_content": has_construction,
            "rfp_links_found": len(rfp_links),
            "construction_rfp_links": sum(1 for link in rfp_links if link["is_construction"]),
            "table_count": table_count,
            "table_rows": table_rows,
            "rfp_count_estimate": rfp_count_estimate,
            "sample_rfp_links": rfp_links[:10],  # First 10
            "has_bid_list": table_rows > 10 or len(rfp_links) > 5,
        }

    async def verify_portal(
        self,
        client: httpx.AsyncClient,
        portal: Dict,
    ) -> Dict:
        """Verify a single portal.

        Args:
            client: HTTP client
            portal: Portal dict with name, urls_to_try, etc.

        Returns:
            Verified portal dict
        """
        # Try all URLs
        result = await self.try_urls(client, portal["urls_to_try"])

        verified = {
            "name": portal["name"],
            "entity": portal["entity"],
            "priority": portal["priority"],
            "expected_rfps": portal["expected_rfps"],
            "accessible": result["accessible"],
            "tried_urls": portal["urls_to_try"],
        }

        if result["accessible"]:
            # Analyze page
            analysis = self.analyze_page(result["html"], result["final_url"])

            verified.update({
                "working_url": result["final_url"],
                "original_url": result["original_url"],
                **analysis,
            })
        else:
            verified.update({
                "working_url": None,
                "original_url": portal["urls_to_try"][0],
                "title": "",
                "procurement_mentions": 0,
                "construction_mentions": 0,
                "has_construction_content": False,
                "rfp_links_found": 0,
                "construction_rfp_links": 0,
                "table_count": 0,
                "table_rows": 0,
                "rfp_count_estimate": 0,
                "sample_rfp_links": [],
                "has_bid_list": False,
            })

        return verified

    async def verify_all_portals(
        self,
        portals_file: str,
    ) -> List[Dict]:
        """Verify all major portals.

        Args:
            portals_file: Path to JSON file with portals

        Returns:
            List of verified portal dicts
        """
        # Load portals
        with open(portals_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Flatten all portals
        all_portals = []
        all_portals.extend(data.get("state_portals", []))
        all_portals.extend(data.get("authorities", []))
        all_portals.extend(data.get("counties", []))
        all_portals.extend(data.get("major_cities", []))

        print(f"Verifying {len(all_portals)} major NJ portals...")
        print()

        # Verify each portal
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            limits=httpx.Limits(max_connections=10),
        ) as client:

            verified_portals = []

            for portal in tqdm(all_portals, desc="Verifying portals"):
                verified = await self.verify_portal(client, portal)
                verified_portals.append(verified)

                # Small delay to be respectful
                await asyncio.sleep(0.5)

        return verified_portals


async def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify major NJ procurement portals manually"
    )
    parser.add_argument(
        "--portals",
        type=str,
        default="major_nj_portals_manual.json",
        help="JSON file with portals to verify",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="nj_major_portals_verified.csv",
        help="Output CSV file",
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    portals_file = (script_dir / args.portals).resolve()

    if not portals_file.exists():
        print(f"Error: Portals file not found: {portals_file}")
        sys.exit(1)

    # Verify portals
    verifier = MajorPortalVerifier()
    verified = await verifier.verify_all_portals(str(portals_file))

    # Filter to accessible only
    accessible = [p for p in verified if p["accessible"]]
    inaccessible = [p for p in verified if not p["accessible"]]

    # Sort by priority and RFP count
    sorted_portals = sorted(
        accessible,
        key=lambda p: (
            p.get("priority", 0),
            p.get("rfp_count_estimate", 0),
            p.get("has_construction_content", False),
        ),
        reverse=True,
    )

    # Statistics
    total = len(verified)
    accessible_count = len(accessible)
    with_construction = sum(1 for p in accessible if p.get("has_construction_content"))
    with_bid_list = sum(1 for p in accessible if p.get("has_bid_list"))
    total_rfps = sum(p.get("rfp_count_estimate", 0) for p in accessible)

    print()
    print("="*60)
    print("VERIFICATION COMPLETE")
    print("="*60)
    print(f"Total portals checked: {total}")
    print(f"Accessible: {accessible_count} ({accessible_count/total*100:.1f}%)")
    print(f"Inaccessible: {len(inaccessible)}")
    print(f"With construction content: {with_construction}")
    print(f"With active bid lists: {with_bid_list}")
    print(f"Estimated total RFPs: {total_rfps}")
    print()

    # Write to CSV
    output_path = (script_dir / args.output).resolve()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "name",
            "entity",
            "priority",
            "accessible",
            "working_url",
            "original_url",
            "expected_rfps",
            "rfp_count_estimate",
            "has_construction_content",
            "has_bid_list",
            "rfp_links_found",
            "construction_rfp_links",
            "procurement_mentions",
            "construction_mentions",
            "title",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for portal in sorted_portals:
            writer.writerow({
                "name": portal.get("name", ""),
                "entity": portal.get("entity", ""),
                "priority": portal.get("priority", 0),
                "accessible": portal.get("accessible", False),
                "working_url": portal.get("working_url", ""),
                "original_url": portal.get("original_url", ""),
                "expected_rfps": portal.get("expected_rfps", ""),
                "rfp_count_estimate": portal.get("rfp_count_estimate", 0),
                "has_construction_content": portal.get("has_construction_content", False),
                "has_bid_list": portal.get("has_bid_list", False),
                "rfp_links_found": portal.get("rfp_links_found", 0),
                "construction_rfp_links": portal.get("construction_rfp_links", 0),
                "procurement_mentions": portal.get("procurement_mentions", 0),
                "construction_mentions": portal.get("construction_mentions", 0),
                "title": portal.get("title", "")[:100],
            })

    print(f"Results written to: {output_path}")
    print()

    # Show accessible portals
    print("="*60)
    print(f"ACCESSIBLE PORTALS ({len(accessible)})")
    print("="*60)
    for i, portal in enumerate(sorted_portals, 1):
        print(f"{i}. {portal.get('name')} ({portal.get('entity')})")
        print(f"   URL: {portal.get('working_url')}")
        print(f"   Est. RFPs: {portal.get('rfp_count_estimate')} (expected: {portal.get('expected_rfps')})")
        print(f"   Construction: {'Yes' if portal.get('has_construction_content') else 'No'}")
        print(f"   Active list: {'Yes' if portal.get('has_bid_list') else 'No'}")
        print(f"   Priority: {portal.get('priority')}/10")
        print()

    # Show inaccessible portals
    if inaccessible:
        print("="*60)
        print(f"INACCESSIBLE PORTALS ({len(inaccessible)})")
        print("="*60)
        for i, portal in enumerate(inaccessible, 1):
            print(f"{i}. {portal.get('name')} ({portal.get('entity')})")
            print(f"   Tried URLs: {len(portal.get('tried_urls', []))}")
            print(f"   Expected RFPs: {portal.get('expected_rfps')}")
            print()

    print("="*60)
    print("NEXT STEPS")
    print("="*60)
    print(f"1. Review {output_path}")
    print("2. For inaccessible portals:")
    print("   - Try URLs manually in browser")
    print("   - Update URLs in major_nj_portals_manual.json")
    print("   - Re-run verification")
    print("3. Begin scraping accessible portals")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
