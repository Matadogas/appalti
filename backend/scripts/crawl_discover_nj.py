"""Enhanced web crawler for discovering NJ procurement portals.

This script:
1. Starts with known accessible NJ portals
2. Crawls each site to find government links
3. Discovers procurement pages on those sites
4. Recursively finds more portals
5. Focuses on construction/public works RFPs
"""
import sys
import asyncio
import csv
import json
from pathlib import Path
from typing import Set, List, Dict, Optional
from urllib.parse import urljoin, urlparse
from collections import defaultdict

import httpx
from bs4 import BeautifulSoup
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# Keywords indicating procurement/bid pages
PROCUREMENT_KEYWORDS = [
    "procurement", "purchasing", "bid", "bids", "rfp", "rfq", "ifb",
    "solicitation", "contract", "proposal", "vendor", "supplier",
    "current-bids", "open-bids", "bid-opportunities", "active-bids",
    "construction-bids", "public-works", "capital-projects",
]

# Construction-specific keywords
CONSTRUCTION_KEYWORDS = [
    "construction", "contractor", "building", "infrastructure",
    "public works", "capital project", "roadwork", "highway",
    "bridge", "demolition", "excavation", "concrete", "paving",
    "electrical", "plumbing", "hvac", "renovation", "repair",
]


class NJPortalCrawler:
    """Crawler for discovering NJ procurement portals."""

    def __init__(self, max_depth: int = 2, max_concurrent: int = 10):
        """Initialize crawler.

        Args:
            max_depth: Max crawl depth (1 = seed sites only, 2 = seed + linked sites)
            max_concurrent: Max concurrent requests
        """
        self.max_depth = max_depth
        self.max_concurrent = max_concurrent

        # Track visited URLs to avoid duplicates
        self.visited_urls: Set[str] = set()
        self.visited_domains: Set[str] = set()

        # Store discovered portals
        self.discovered_portals: List[Dict] = []

        # Track government domains
        self.gov_domains: Set[str] = set()

        # Statistics
        self.stats = {
            "pages_crawled": 0,
            "portals_found": 0,
            "gov_domains_found": 0,
            "construction_rfps_found": 0,
        }

    def is_nj_government_domain(self, url: str) -> bool:
        """Check if URL is NJ government domain.

        Args:
            url: URL to check

        Returns:
            True if NJ government domain
        """
        domain = urlparse(url).netloc.lower()

        # NJ-specific patterns
        nj_patterns = [
            ".nj.gov",
            ".nj.us",
            "nj.gov",
            "nj.us",
            ".state.nj.us",
        ]

        # Generic government
        gov_patterns = [
            ".gov",
            ".us",
        ]

        # Check NJ-specific first
        for pattern in nj_patterns:
            if pattern in domain:
                return True

        # Check generic government + NJ in domain name
        for pattern in gov_patterns:
            if pattern in domain and "nj" in domain:
                return True

        return False

    def is_procurement_url(self, url: str, text: str = "") -> bool:
        """Check if URL or text contains procurement keywords.

        Args:
            url: URL to check
            text: Link text or page title

        Returns:
            True if likely procurement page
        """
        url_lower = url.lower()
        text_lower = text.lower()

        for keyword in PROCUREMENT_KEYWORDS:
            if keyword in url_lower or keyword in text_lower:
                return True

        return False

    def has_construction_keywords(self, text: str) -> bool:
        """Check if text contains construction keywords.

        Args:
            text: Text to check

        Returns:
            True if construction-related
        """
        text_lower = text.lower()

        for keyword in CONSTRUCTION_KEYWORDS:
            if keyword in text_lower:
                return True

        return False

    async def fetch_page(self, client: httpx.AsyncClient, url: str) -> Optional[str]:
        """Fetch page HTML.

        Args:
            client: HTTP client
            url: URL to fetch

        Returns:
            HTML content or None if failed
        """
        try:
            response = await client.get(
                url,
                follow_redirects=True,
                timeout=15.0,
            )

            if response.status_code == 200:
                return response.text

        except Exception as e:
            # Silently fail for now
            pass

        return None

    def extract_links(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """Extract all links from HTML.

        Args:
            html: HTML content
            base_url: Base URL for resolving relative links

        Returns:
            List of dicts with 'url' and 'text'
        """
        soup = BeautifulSoup(html, "html.parser")
        links = []

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            text = a_tag.get_text(strip=True)

            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)

            # Skip non-http URLs
            if not absolute_url.startswith("http"):
                continue

            links.append({
                "url": absolute_url,
                "text": text,
            })

        return links

    def extract_page_info(self, html: str, url: str) -> Dict:
        """Extract metadata from page.

        Args:
            html: HTML content
            url: Page URL

        Returns:
            Dict with title, description, keywords
        """
        soup = BeautifulSoup(html, "html.parser")

        info = {
            "url": url,
            "title": "",
            "description": "",
            "has_construction_content": False,
            "rfp_count_estimate": 0,
        }

        # Extract title
        title_tag = soup.find("title")
        if title_tag:
            info["title"] = title_tag.get_text(strip=True)

        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            info["description"] = meta_desc["content"]

        # Check for construction keywords
        page_text = soup.get_text()
        info["has_construction_content"] = self.has_construction_keywords(page_text)

        # Estimate RFP count (rough heuristic)
        # Look for table rows, list items with bid/RFP patterns
        bid_patterns = ["rfp", "rfq", "ifb", "bid #", "solicitation"]
        rfp_count = 0

        for pattern in bid_patterns:
            rfp_count += page_text.lower().count(pattern)

        # Cap at reasonable estimate
        info["rfp_count_estimate"] = min(rfp_count // 3, 100)  # Divide by 3 to avoid overcounting

        return info

    async def crawl_site(
        self,
        client: httpx.AsyncClient,
        seed_url: str,
        depth: int = 0,
    ) -> List[Dict]:
        """Crawl a site to discover procurement portals.

        Args:
            client: HTTP client
            seed_url: Starting URL
            depth: Current recursion depth

        Returns:
            List of discovered portal dicts
        """
        if depth > self.max_depth:
            return []

        if seed_url in self.visited_urls:
            return []

        self.visited_urls.add(seed_url)

        # Fetch page
        html = await self.fetch_page(client, seed_url)
        if not html:
            return []

        self.stats["pages_crawled"] += 1

        # Extract page info
        page_info = self.extract_page_info(html, seed_url)

        # Extract links
        links = self.extract_links(html, seed_url)

        discovered = []

        # Check if this is a procurement portal
        if self.is_procurement_url(seed_url, page_info["title"]):
            domain = urlparse(seed_url).netloc

            if domain not in self.visited_domains:
                self.visited_domains.add(domain)

                portal = {
                    "url": seed_url,
                    "domain": domain,
                    "title": page_info["title"],
                    "description": page_info["description"],
                    "has_construction_content": page_info["has_construction_content"],
                    "rfp_count_estimate": page_info["rfp_count_estimate"],
                    "depth": depth,
                    "is_nj_gov": self.is_nj_government_domain(seed_url),
                }

                discovered.append(portal)
                self.stats["portals_found"] += 1

                if page_info["has_construction_content"]:
                    self.stats["construction_rfps_found"] += 1

        # Track government domains
        if self.is_nj_government_domain(seed_url):
            domain = urlparse(seed_url).netloc
            if domain not in self.gov_domains:
                self.gov_domains.add(domain)
                self.stats["gov_domains_found"] += 1

        # Find procurement links on this page
        procurement_links = []
        gov_domain_links = []

        for link in links:
            link_url = link["url"]
            link_text = link["text"]

            # Skip if already visited
            if link_url in self.visited_urls:
                continue

            # Procurement links (same domain)
            if self.is_procurement_url(link_url, link_text):
                if urlparse(link_url).netloc == urlparse(seed_url).netloc:
                    procurement_links.append(link_url)

            # NJ government domain links (for recursive crawl)
            if self.is_nj_government_domain(link_url):
                if depth < self.max_depth:
                    gov_domain_links.append(link_url)

        # Crawl procurement links first (same domain)
        for proc_url in procurement_links[:10]:  # Limit to 10 per page
            child_portals = await self.crawl_site(client, proc_url, depth)
            discovered.extend(child_portals)

        # Recursively crawl government domain links
        if depth < self.max_depth:
            for gov_url in gov_domain_links[:20]:  # Limit to 20 per page
                child_portals = await self.crawl_site(client, gov_url, depth + 1)
                discovered.extend(child_portals)

        return discovered

    async def discover_portals(self, seed_urls: List[str]) -> List[Dict]:
        """Discover NJ procurement portals from seed URLs.

        Args:
            seed_urls: Starting URLs (our 12 accessible NJ portals)

        Returns:
            List of discovered portal dicts
        """
        print(f"Starting discovery with {len(seed_urls)} seed URLs...")
        print(f"Max depth: {self.max_depth}")
        print(f"Max concurrent: {self.max_concurrent}")
        print()

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=15.0,
            limits=httpx.Limits(max_connections=self.max_concurrent),
        ) as client:

            # Crawl each seed URL
            for seed_url in tqdm(seed_urls, desc="Crawling seed URLs"):
                portals = await self.crawl_site(client, seed_url, depth=0)
                self.discovered_portals.extend(portals)

        # Deduplicate by URL
        seen_urls = set()
        unique_portals = []

        for portal in self.discovered_portals:
            if portal["url"] not in seen_urls:
                seen_urls.add(portal["url"])
                unique_portals.append(portal)

        self.discovered_portals = unique_portals

        return self.discovered_portals


async def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Discover NJ procurement portals via web crawling"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Max crawl depth (1=seed only, 2=seed+linked sites)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=10,
        help="Max concurrent requests",
    )
    parser.add_argument(
        "--seed-urls",
        type=str,
        default="../scripts/target_websites.csv",
        help="CSV with seed URLs",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="nj_discovered_portals.csv",
        help="Output CSV file",
    )

    args = parser.parse_args()

    # Load seed URLs (NJ only)
    script_dir = Path(__file__).parent
    seed_csv = (script_dir / args.seed_urls).resolve()

    if not seed_csv.exists():
        print(f"Error: Seed URL file not found: {seed_csv}")
        sys.exit(1)

    seed_urls = []
    with open(seed_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["state"] == "NJ":  # NJ only
                seed_urls.append(row["website_url"])

    print(f"Loaded {len(seed_urls)} NJ seed URLs")
    print()

    # Create crawler
    crawler = NJPortalCrawler(
        max_depth=args.depth,
        max_concurrent=args.max_concurrent,
    )

    # Discover portals
    portals = await crawler.discover_portals(seed_urls)

    # Print statistics
    print()
    print("="*60)
    print("DISCOVERY COMPLETE")
    print("="*60)
    print(f"Pages crawled: {crawler.stats['pages_crawled']}")
    print(f"Unique portals found: {len(portals)}")
    print(f"NJ government domains: {crawler.stats['gov_domains_found']}")
    print(f"With construction content: {crawler.stats['construction_rfps_found']}")
    print()

    # Sort by RFP count estimate (descending)
    portals_sorted = sorted(
        portals,
        key=lambda p: (p["rfp_count_estimate"], p["has_construction_content"]),
        reverse=True,
    )

    # Write to CSV
    output_path = (script_dir / args.output).resolve()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "url",
            "domain",
            "title",
            "description",
            "has_construction_content",
            "rfp_count_estimate",
            "depth",
            "is_nj_gov",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(portals_sorted)

    print(f"Wrote results to: {output_path}")
    print()

    # Print top portals
    print("="*60)
    print("TOP 10 PORTALS (by estimated RFP count)")
    print("="*60)
    for i, portal in enumerate(portals_sorted[:10], 1):
        print(f"{i}. {portal['domain']}")
        print(f"   URL: {portal['url']}")
        print(f"   Title: {portal['title']}")
        print(f"   Est. RFPs: {portal['rfp_count_estimate']}")
        print(f"   Construction: {'Yes' if portal['has_construction_content'] else 'No'}")
        print(f"   NJ Gov: {'Yes' if portal['is_nj_gov'] else 'No'}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
