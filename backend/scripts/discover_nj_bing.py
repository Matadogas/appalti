"""Comprehensive NJ procurement portal discovery using Bing Search API.

This script:
1. Loads all NJ entities from CSV
2. Uses Bing Search API to find procurement portals
3. Validates and scores candidates
4. Outputs comprehensive list of NJ construction RFP portals

Free tier: 1,000 searches/month
For 145 NJ entities × 3 queries = 435 searches (under free limit)
"""
import sys
import asyncio
import csv
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.bing_search_service import BingSearchService
from app.database import SessionLocal
from tqdm import tqdm


async def load_nj_entities(csv_path: str) -> List[Dict]:
    """Load NJ entities from CSV.

    Args:
        csv_path: Path to entity CSV

    Returns:
        List of NJ entity dicts
    """
    entities = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Filter to NJ only
            if row["state"] == "NJ":
                entities.append({
                    "entity_name": row["entity_name"],
                    "state": row["state"],
                    "entity_type": row["entity_type"],
                    "priority": int(row.get("priority", 5)),
                    "search_keywords": row.get("search_keywords", ""),
                })

    return entities


async def discover_nj_portals(
    api_key: str,
    entity_csv: str,
    queries_per_entity: int = 3,
    max_entities: int = None,
) -> List[Dict]:
    """Discover NJ procurement portals using Bing.

    Args:
        api_key: Bing Search API key
        entity_csv: Path to entity CSV
        queries_per_entity: Queries per entity (default: 3)
        max_entities: Max entities to process (for testing)

    Returns:
        List of discovered candidate dicts
    """
    # Load entities
    print(f"Loading NJ entities from {entity_csv}...")
    entities = await load_nj_entities(entity_csv)

    if max_entities:
        entities = entities[:max_entities]
        print(f"Limited to first {max_entities} entities for testing")

    print(f"Found {len(entities)} NJ entities")
    print(f"Queries per entity: {queries_per_entity}")
    print(f"Total searches: {len(entities) * queries_per_entity}")
    print()

    # Create service
    db = SessionLocal()
    service = BingSearchService(db, api_key)

    # Discover portals
    print("Starting discovery with Bing Search API...")
    print("Rate limit: ~3 searches/second")
    print()

    all_candidates = []

    try:
        for entity in tqdm(entities, desc="Discovering portals"):
            entity_name = entity["entity_name"]
            state = entity["state"]
            entity_type = entity["entity_type"]

            # Discover for this entity
            candidates = await service.discover_entity_portals(
                entity_name,
                state,
                entity_type,
                num_queries=queries_per_entity,
            )

            # Add entity priority
            for candidate in candidates:
                candidate["entity_priority"] = entity["priority"]

            all_candidates.extend(candidates)

    finally:
        db.close()

    return all_candidates


def deduplicate_candidates(candidates: List[Dict]) -> List[Dict]:
    """Deduplicate candidates by URL, keeping highest scored.

    Args:
        candidates: List of candidate dicts

    Returns:
        Deduplicated list
    """
    url_map = {}

    for candidate in candidates:
        url = candidate["url"]

        if url not in url_map:
            url_map[url] = candidate
        else:
            # Keep higher scored candidate
            if candidate["relevance_score"] > url_map[url]["relevance_score"]:
                url_map[url] = candidate

    return list(url_map.values())


async def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Discover NJ procurement portals using Bing Search"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Bing Search API key",
    )
    parser.add_argument(
        "--entities",
        type=str,
        default="../../docs/data/tristate-entities-comprehensive.csv",
        help="Path to entity CSV",
    )
    parser.add_argument(
        "--queries-per-entity",
        type=int,
        default=3,
        help="Number of search queries per entity (default: 3)",
    )
    parser.add_argument(
        "--max-entities",
        type=int,
        help="Max entities to process (for testing)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="nj_portals_bing_discovery.csv",
        help="Output CSV file",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: search for 'Bergen County NJ procurement'",
    )

    args = parser.parse_args()

    # Test mode
    if args.test:
        print("TEST MODE: Running sample Bing search...")
        print()

        if not args.api_key:
            print("Error: --api-key required for testing")
            sys.exit(1)

        from app.services.bing_search_service import BingSearchAPI

        client = BingSearchAPI(args.api_key)

        try:
            results = await client.search(
                "Bergen County NJ procurement",
                num_results=5,
            )

            print(f"Success! Found {len(results)} results:")
            print()

            for i, result in enumerate(results, 1):
                print(f"{i}. {result['title']}")
                print(f"   URL: {result['url']}")
                print(f"   Snippet: {result['snippet'][:100]}...")
                print()

            print("✓ Bing Search API is working!")
            print()
            print("Next step: Run full discovery:")
            print(f"  python {Path(__file__).name} --api-key YOUR_KEY")

        except Exception as e:
            print(f"✗ Bing Search API failed: {e}")
            print()
            print("Troubleshooting:")
            print("1. Check your API key is correct")
            print("2. Verify you've enabled Bing Search v7 in Azure")
            print("3. Make sure billing is enabled (free tier is fine)")
            sys.exit(1)

        return

    # Full discovery mode
    if not args.api_key:
        print("Error: --api-key required")
        print()
        print("Get your Bing Search API key:")
        print("1. Go to https://portal.azure.com")
        print("2. Create 'Bing Search v7' resource")
        print("3. Get API key from 'Keys and Endpoint'")
        print()
        print("Then run:")
        print(f"  python {Path(__file__).name} --api-key YOUR_KEY")
        sys.exit(1)

    script_dir = Path(__file__).parent
    entity_csv = (script_dir / args.entities).resolve()

    if not entity_csv.exists():
        print(f"Error: Entity CSV not found: {entity_csv}")
        sys.exit(1)

    # Discover portals
    candidates = await discover_nj_portals(
        args.api_key,
        str(entity_csv),
        args.queries_per_entity,
        args.max_entities,
    )

    # Deduplicate
    print()
    print(f"Found {len(candidates)} total candidates")
    print("Deduplicating by URL...")

    unique_candidates = deduplicate_candidates(candidates)

    print(f"After deduplication: {len(unique_candidates)} unique portals")
    print()

    # Sort by priority and relevance
    sorted_candidates = sorted(
        unique_candidates,
        key=lambda c: (
            c.get("entity_priority", 0),
            c.get("relevance_score", 0),
            c.get("priority", 0),
        ),
        reverse=True,
    )

    # Statistics
    gov_domains = sum(1 for c in sorted_candidates if c.get("is_government_domain"))
    high_score = sum(1 for c in sorted_candidates if c.get("relevance_score", 0) >= 50)

    by_type = {}
    for c in sorted_candidates:
        entity_type = c.get("entity_type", "unknown")
        by_type[entity_type] = by_type.get(entity_type, 0) + 1

    print("="*60)
    print("DISCOVERY COMPLETE")
    print("="*60)
    print(f"Total unique portals: {len(sorted_candidates)}")
    print(f"Government domains (.gov, .us): {gov_domains} ({gov_domains/len(sorted_candidates)*100:.1f}%)")
    print(f"High relevance (score ≥ 50): {high_score}")
    print(f"By entity type: {by_type}")
    print()

    # Write to CSV
    output_path = (script_dir / args.output).resolve()

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "entity_name",
            "entity_state",
            "entity_type",
            "entity_priority",
            "url",
            "title",
            "snippet",
            "relevance_score",
            "priority",
            "is_government_domain",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for candidate in sorted_candidates:
            writer.writerow({
                "entity_name": candidate.get("entity_name", ""),
                "entity_state": candidate.get("entity_state", ""),
                "entity_type": candidate.get("entity_type", ""),
                "entity_priority": candidate.get("entity_priority", 0),
                "url": candidate.get("url", ""),
                "title": candidate.get("title", ""),
                "snippet": candidate.get("snippet", "")[:200],
                "relevance_score": candidate.get("relevance_score", 0),
                "priority": candidate.get("priority", 0),
                "is_government_domain": candidate.get("is_government_domain", False),
            })

    print(f"Results written to: {output_path}")
    print()

    # Show top 20 portals
    print("="*60)
    print("TOP 20 NJ PROCUREMENT PORTALS")
    print("="*60)
    for i, candidate in enumerate(sorted_candidates[:20], 1):
        print(f"{i}. {candidate.get('entity_name')} ({candidate.get('entity_type')})")
        print(f"   URL: {candidate.get('url')}")
        print(f"   Score: {candidate.get('relevance_score')}/100")
        print(f"   Gov: {'Yes' if candidate.get('is_government_domain') else 'No'}")
        print(f"   Priority: {candidate.get('priority')}/10")
        print()

    print("="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Review top portals in CSV")
    print("2. Validate URLs with validation script:")
    print(f"   python validate_candidates.py --input {args.output}")
    print("3. Begin scraping accessible portals")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
