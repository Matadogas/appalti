"""Comprehensive NJ procurement portal discovery.

Strategy:
1. Start with known major portals (state, counties, cities, authorities)
2. Validate each URL
3. Crawl to find additional procurement pages
4. Extract RFP listings
5. Focus on construction/public works
"""
import sys
import asyncio
import csv
import json
from pathlib import Path
from typing import Set, List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class NJComprehensiveDiscovery:
    """Comprehensive NJ procurement portal discovery."""

    def __init__(self, max_concurrent: int = 20):
        """Initialize discovery.

        Args:
            max_concurrent: Max concurrent requests
        """
        self.max_concurrent = max_concurrent
        self.visited_urls: Set[str] = set()
        self.discovered_portals: List[Dict] = []

        # Procurement keywords
        self.procurement_keywords = [
            "procurement", "purchasing", "bid", "bids", "rfp", "rfq", "ifb",
            "solicitation", "contract", "proposal", "vendor", "supplier",
            "current bids", "open bids", "active bids", "construction bids",
        ]

        # Construction keywords
        self.construction_keywords = [
            "construction", "contractor", "building", "infrastructure",
            "public works", "capital project", "roadwork", "highway",
            "bridge", "demolition", "excavation", "concrete", "paving",
            "electrical", "plumbing", "hvac", "renovation",
        ]

    async def check_url(
        self,
        client: httpx.AsyncClient,
        url: str,
        name: str,
        entity_type: str,
        priority: int,
    ) -> Optional[Dict]:
        """Check if URL is accessible and is a procurement portal.

        Args:
            client: HTTP client
            url: URL to check
            name: Entity name
            entity_type: Type (state, county, city, authority)
            priority: Priority score

        Returns:
            Portal dict if valid, None otherwise
        """
        if url in self.visited_urls:
            return None

        self.visited_urls.add(url)

        try:
            response = await client.get(
                url,
                follow_redirects=True,
                timeout=15.0,
            )

            if response.status_code != 200:
                return None

            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            # Extract metadata
            title = ""
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                description = meta_desc["content"]

            # Get page text
            page_text = soup.get_text().lower()

            # Check if it's actually a procurement page
            procurement_score = 0
            for keyword in self.procurement_keywords:
                if keyword in page_text:
                    procurement_score += page_text.count(keyword)

            if procurement_score < 2:
                return None  # Not a procurement page

            # Check for construction content
            construction_score = 0
            for keyword in self.construction_keywords:
                if keyword in page_text:
                    construction_score += page_text.count(keyword)

            has_construction = construction_score >= 2

            # Estimate RFP count (look for bid numbers, RFP listings)
            rfp_indicators = ["rfp-", "rfq-", "bid-", "bid #", "solicitation #"]
            rfp_count = 0
            for indicator in rfp_indicators:
                rfp_count += page_text.count(indicator)

            # Look for table rows (common in bid listings)
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                # If table has many rows, likely a bid listing
                if len(rows) > 5:
                    rfp_count += len(rows) - 1  # Subtract header row

            rfp_count = min(rfp_count, 200)  # Cap estimate

            # Find additional procurement links on this page
            additional_links = []
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                link_text = a_tag.get_text(strip=True).lower()

                absolute_url = urljoin(url, href)

                # Check if it's a procurement-related link
                if any(kw in link_text or kw in href.lower() for kw in self.procurement_keywords):
                    # Same domain only
                    if urlparse(absolute_url).netloc == urlparse(url).netloc:
                        additional_links.append({
                            "url": absolute_url,
                            "text": link_text,
                        })

            portal = {
                "url": str(response.url),  # Final URL after redirects
                "original_url": url,
                "name": name,
                "entity_type": entity_type,
                "priority": priority,
                "title": title,
                "description": description,
                "procurement_score": procurement_score,
                "has_construction": has_construction,
                "construction_score": construction_score,
                "rfp_count_estimate": rfp_count,
                "additional_links": additional_links[:10],  # Limit to 10
                "status": "accessible",
            }

            return portal

        except httpx.TimeoutException:
            return {"url": url, "name": name, "status": "timeout"}
        except Exception as e:
            return {"url": url, "name": name, "status": f"error: {str(e)[:50]}"}

    async def discover_from_seeds(self, seed_file: str) -> List[Dict]:
        """Discover portals from seed file.

        Args:
            seed_file: Path to nj_seed_portals.json

        Returns:
            List of discovered portals
        """
        # Load seeds
        with open(seed_file, "r", encoding="utf-8") as f:
            seeds = json.load(f)

        # Build URL list
        urls_to_check = []

        # Major portals
        for portal in seeds["major_portals"]:
            urls_to_check.append({
                "url": portal["url"],
                "name": portal["name"],
                "type": portal["type"],
                "priority": portal["priority"],
            })

        # Counties
        for county in seeds["county_patterns"]:
            for url in county["urls"]:
                urls_to_check.append({
                    "url": url,
                    "name": f"{county['county']} County",
                    "type": "county",
                    "priority": county["priority"],
                })

        # Cities
        for city in seeds["major_cities"]:
            for url in city["urls"]:
                urls_to_check.append({
                    "url": url,
                    "name": city["city"],
                    "type": "city",
                    "priority": city["priority"],
                })

        print(f"Checking {len(urls_to_check)} seed URLs...")
        print()

        # Check all URLs
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            limits=httpx.Limits(max_connections=self.max_concurrent),
        ) as client:

            tasks = []
            for item in urls_to_check:
                task = self.check_url(
                    client,
                    item["url"],
                    item["name"],
                    item["type"],
                    item["priority"],
                )
                tasks.append(task)

            # Execute with progress bar
            results = []
            for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Validating URLs"):
                result = await task
                if result and result.get("status") == "accessible":
                    results.append(result)

        self.discovered_portals = results

        # Now check additional links from accessible portals
        print(f"\nFound {len(results)} accessible portals")
        print("Checking additional procurement links...")

        additional_urls = []
        for portal in results:
            for link in portal.get("additional_links", []):
                if link["url"] not in self.visited_urls:
                    additional_urls.append({
                        "url": link["url"],
                        "name": f"{portal['name']} - {link['text'][:30]}",
                        "type": portal["entity_type"],
                        "priority": portal["priority"],
                    })

        if additional_urls:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=15.0,
                limits=httpx.Limits(max_connections=self.max_concurrent),
            ) as client:

                tasks = []
                for item in additional_urls[:100]:  # Limit to 100
                    task = self.check_url(
                        client,
                        item["url"],
                        item["name"],
                        item["type"],
                        item["priority"],
                    )
                    tasks.append(task)

                for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Checking linked pages"):
                    result = await task
                    if result and result.get("status") == "accessible":
                        self.discovered_portals.append(result)

        return self.discovered_portals


async def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Comprehensive NJ procurement portal discovery"
    )
    parser.add_argument(
        "--seeds",
        type=str,
        default="nj_seed_portals.json",
        help="Seed portals JSON file",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="nj_portals_comprehensive.csv",
        help="Output CSV file",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=20,
        help="Max concurrent requests",
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    seed_file = (script_dir / args.seeds).resolve()

    if not seed_file.exists():
        print(f"Error: Seed file not found: {seed_file}")
        sys.exit(1)

    # Create discovery
    discovery = NJComprehensiveDiscovery(max_concurrent=args.max_concurrent)

    # Discover portals
    portals = await discovery.discover_from_seeds(str(seed_file))

    # Sort by priority, then RFP count
    portals_sorted = sorted(
        portals,
        key=lambda p: (
            p.get("priority", 0),
            p.get("rfp_count_estimate", 0),
            p.get("has_construction", False),
        ),
        reverse=True,
    )

    # Statistics
    total = len(portals)
    with_construction = sum(1 for p in portals if p.get("has_construction"))
    total_rfps = sum(p.get("rfp_count_estimate", 0) for p in portals)

    by_type = {}
    for p in portals:
        entity_type = p.get("entity_type", "unknown")
        by_type[entity_type] = by_type.get(entity_type, 0) + 1

    print()
    print("="*60)
    print("DISCOVERY COMPLETE")
    print("="*60)
    print(f"Total portals found: {total}")
    print(f"With construction content: {with_construction}")
    print(f"Estimated total RFPs: {total_rfps}")
    print(f"By type: {by_type}")
    print()

    # Write to CSV
    output_path = (script_dir / args.output).resolve()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "name",
            "entity_type",
            "priority",
            "url",
            "title",
            "rfp_count_estimate",
            "has_construction",
            "procurement_score",
            "construction_score",
            "description",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for portal in portals_sorted:
            writer.writerow({
                "name": portal.get("name", ""),
                "entity_type": portal.get("entity_type", ""),
                "priority": portal.get("priority", 0),
                "url": portal.get("url", ""),
                "title": portal.get("title", ""),
                "rfp_count_estimate": portal.get("rfp_count_estimate", 0),
                "has_construction": portal.get("has_construction", False),
                "procurement_score": portal.get("procurement_score", 0),
                "construction_score": portal.get("construction_score", 0),
                "description": portal.get("description", "")[:200],
            })

    print(f"Results written to: {output_path}")
    print()

    # Show top 15 portals
    print("="*60)
    print("TOP 15 PORTALS")
    print("="*60)
    for i, portal in enumerate(portals_sorted[:15], 1):
        print(f"{i}. {portal.get('name')} ({portal.get('entity_type')})")
        print(f"   URL: {portal.get('url')}")
        print(f"   Est. RFPs: {portal.get('rfp_count_estimate', 0)}")
        print(f"   Construction: {'Yes' if portal.get('has_construction') else 'No'}")
        print(f"   Priority: {portal.get('priority', 0)}/10")
        print()


if __name__ == "__main__":
    asyncio.run(main())
