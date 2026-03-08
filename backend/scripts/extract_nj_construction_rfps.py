"""Extract construction RFPs from NJ portals.

Focuses on finding actual construction bid opportunities across NJ.
"""
import sys
import asyncio
import csv
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# Known major NJ procurement portals (manually curated)
MAJOR_NJ_PORTALS = [
    {
        "name": "NJ START (State)",
        "url": "https://www.njstart.gov/bso/",
        "type": "state",
        "note": "Main state portal - requires login for full access",
        "priority": 10,
    },
    {
        "name": "NJ Transit",
        "url": "https://www.njtransit.com/business-center/solicitations",
        "type": "authority",
        "priority": 10,
    },
    {
        "name": "Port Authority NY/NJ",
        "url": "https://www.panynj.gov/port-authority/en/business-opportunities.html",
        "type": "authority",
        "priority": 10,
    },
    {
        "name": "NJ Turnpike Authority",
        "url": "https://www.njta.com/business-opportunities",
        "type": "authority",
        "priority": 9,
    },
    {
        "name": "NJ Schools Development Authority",
        "url": "https://www.njsda.gov/business/procurement",
        "type": "authority",
        "priority": 9,
    },
    {
        "name": "NJ Sports & Exposition Authority",
        "url": "https://www.njsea.com/doing-business/",
        "type": "authority",
        "priority": 8,
    },
    {
        "name": "Bergen County",
        "url": "https://www.co.bergen.nj.us/index.aspx?NID=162",
        "type": "county",
        "priority": 9,
    },
    {
        "name": "Essex County",
        "url": "https://www.essexcountynj.org/purchasing/",
        "type": "county",
        "priority": 9,
    },
    {
        "name": "Hudson County",
        "url": "https://www.hudsoncountynj.org/purchasing-department/",
        "type": "county",
        "priority": 9,
    },
    {
        "name": "Middlesex County",
        "url": "https://www.middlesexcountynj.gov/government/departments/departments-a-m/central-services/purchasing",
        "type": "county",
        "priority": 9,
    },
    {
        "name": "Morris County",
        "url": "https://www.morriscountynj.gov/Government/Departments/Purchasing-1",
        "type": "county",
        "priority": 8,
    },
    {
        "name": "Ocean County",
        "url": "https://www.oceancountygov.com/en-US/purchasing",
        "type": "county",
        "priority": 7,
    },
    {
        "name": "Newark",
        "url": "https://www.newarknj.gov/departments/finance/purchasing",
        "type": "city",
        "priority": 10,
    },
    {
        "name": "Jersey City",
        "url": "https://www.jerseycitynj.gov/cityhall/purchasing",
        "type": "city",
        "priority": 9,
    },
    {
        "name": "Paterson",
        "url": "https://www.patersonnj.gov/egov/apps/document/center.egov?fDD=14-49",
        "type": "city",
        "priority": 8,
    },
    {
        "name": "Elizabeth",
        "url": "https://www.elizabethnj.org/departments/purchasing/",
        "type": "city",
        "priority": 8,
    },
    {
        "name": "Woodbridge Township",
        "url": "https://www.twp.woodbridge.nj.us/207/Purchasing-Department",
        "type": "township",
        "priority": 7,
    },
    {
        "name": "Lakewood Township",
        "url": "https://www.lakewoodnj.gov/bids",
        "type": "township",
        "priority": 7,
    },
    {
        "name": "Toms River Township",
        "url": "https://www.tomsrivernj.gov/departments/purchasing/",
        "type": "township",
        "priority": 7,
    },
]


class NJConstructionRFPExtractor:
    """Extract construction RFPs from NJ portals."""

    def __init__(self):
        self.construction_keywords = [
            "construction", "contractor", "building", "infrastructure",
            "public works", "roadwork", "highway", "bridge",
            "demolition", "excavation", "concrete", "paving",
            "electrical", "plumbing", "hvac", "renovation",
            "repair", "maintenance", "facility",
        ]

    async def extract_portal_info(
        self,
        client: httpx.AsyncClient,
        portal: Dict,
    ) -> Optional[Dict]:
        """Extract information from a portal.

        Args:
            client: HTTP client
            portal: Portal dict

        Returns:
            Portal info with accessibility and content details
        """
        try:
            response = await client.get(
                portal["url"],
                follow_redirects=True,
                timeout=20.0,
            )

            if response.status_code != 200:
                return {
                    **portal,
                    "status": "inaccessible",
                    "status_code": response.status_code,
                }

            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            # Extract title
            title = ""
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

            # Get page text
            page_text = soup.get_text().lower()

            # Check for construction content
            construction_matches = 0
            for keyword in self.construction_keywords:
                construction_matches += page_text.count(keyword)

            has_construction = construction_matches >= 3

            # Look for RFP/bid listings
            # Common patterns: tables, lists with dates and project names
            rfp_links = []

            # Find links with procurement keywords
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                link_text = a_tag.get_text(strip=True)

                # Check if it's likely an RFP
                link_lower = link_text.lower()
                href_lower = href.lower()

                if any(kw in link_lower or kw in href_lower for kw in ["rfp", "rfq", "bid", "solicitation", "project"]):
                    absolute_url = urljoin(str(response.url), href)

                    # Check if construction-related
                    is_construction = any(kw in link_lower for kw in self.construction_keywords)

                    rfp_links.append({
                        "text": link_text,
                        "url": absolute_url,
                        "is_construction": is_construction,
                    })

            # Look for tables (common in bid listings)
            tables = soup.find_all("table")
            table_row_count = sum(len(table.find_all("tr")) for table in tables)

            return {
                **portal,
                "status": "accessible",
                "final_url": str(response.url),
                "title": title,
                "has_construction_content": has_construction,
                "construction_keyword_count": construction_matches,
                "rfp_links_found": len(rfp_links),
                "construction_rfp_links": sum(1 for link in rfp_links if link["is_construction"]),
                "table_rows": table_row_count,
                "sample_rfp_links": rfp_links[:5],  # First 5
            }

        except httpx.TimeoutException:
            return {**portal, "status": "timeout"}
        except Exception as e:
            return {**portal, "status": "error", "error": str(e)[:100]}

    async def extract_all_portals(
        self,
        portals: List[Dict],
    ) -> List[Dict]:
        """Extract info from all portals.

        Args:
            portals: List of portal dicts

        Returns:
            List of portal info dicts
        """
        print(f"Extracting information from {len(portals)} portals...")
        print()

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=20.0,
            limits=httpx.Limits(max_connections=20),
        ) as client:

            tasks = []
            for portal in portals:
                task = self.extract_portal_info(client, portal)
                tasks.append(task)

            results = []
            for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Extracting portal info"):
                result = await task
                if result:
                    results.append(result)

        return results


async def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract NJ construction RFPs"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="nj_construction_portals_final.csv",
        help="Output CSV file",
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent

    # Use major portals list
    portals = MAJOR_NJ_PORTALS

    # Extract info
    extractor = NJConstructionRFPExtractor()
    results = await extractor.extract_all_portals(portals)

    # Filter to accessible only
    accessible = [r for r in results if r.get("status") == "accessible"]

    # Sort by priority, construction content, RFP count
    sorted_results = sorted(
        accessible,
        key=lambda r: (
            r.get("priority", 0),
            r.get("has_construction_content", False),
            r.get("rfp_links_found", 0),
        ),
        reverse=True,
    )

    # Statistics
    total_accessible = len(accessible)
    with_construction = sum(1 for r in accessible if r.get("has_construction_content"))
    total_rfp_links = sum(r.get("rfp_links_found", 0) for r in accessible)
    construction_links = sum(r.get("construction_rfp_links", 0) for r in accessible)

    by_type = {}
    for r in accessible:
        entity_type = r.get("type", "unknown")
        by_type[entity_type] = by_type.get(entity_type, 0) + 1

    print()
    print("="*60)
    print("EXTRACTION COMPLETE")
    print("="*60)
    print(f"Total accessible portals: {total_accessible}/{len(results)}")
    print(f"With construction content: {with_construction}")
    print(f"Total RFP links found: {total_rfp_links}")
    print(f"Construction RFP links: {construction_links}")
    print(f"By type: {by_type}")
    print()

    # Write to CSV
    output_path = (script_dir / args.output).resolve()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "name",
            "type",
            "priority",
            "url",
            "final_url",
            "status",
            "title",
            "has_construction_content",
            "construction_keyword_count",
            "rfp_links_found",
            "construction_rfp_links",
            "table_rows",
            "note",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in sorted_results:
            writer.writerow({
                "name": result.get("name", ""),
                "type": result.get("type", ""),
                "priority": result.get("priority", 0),
                "url": result.get("url", ""),
                "final_url": result.get("final_url", ""),
                "status": result.get("status", ""),
                "title": result.get("title", ""),
                "has_construction_content": result.get("has_construction_content", False),
                "construction_keyword_count": result.get("construction_keyword_count", 0),
                "rfp_links_found": result.get("rfp_links_found", 0),
                "construction_rfp_links": result.get("construction_rfp_links", 0),
                "table_rows": result.get("table_rows", 0),
                "note": result.get("note", ""),
            })

    print(f"Results written to: {output_path}")
    print()

    # Show top portals
    print("="*60)
    print("TOP NJ CONSTRUCTION PROCUREMENT PORTALS")
    print("="*60)
    for i, result in enumerate(sorted_results[:15], 1):
        print(f"{i}. {result.get('name')} ({result.get('type')})")
        print(f"   URL: {result.get('url')}")
        print(f"   RFP Links: {result.get('rfp_links_found', 0)} ({result.get('construction_rfp_links', 0)} construction)")
        print(f"   Construction Content: {'Yes' if result.get('has_construction_content') else 'No'}")
        print(f"   Priority: {result.get('priority', 0)}/10")
        if result.get("note"):
            print(f"   Note: {result.get('note')}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
