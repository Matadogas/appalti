"""Automated website discovery via Google search.

This script:
1. Loads search queries from JSON files
2. Executes Google searches via API
3. Stores candidate websites in database
4. Scores and prioritizes candidates for review

Usage:
    python scripts/automated_discovery.py --phase 1 --api-key YOUR_KEY --cse-id YOUR_CSE
"""
import asyncio
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
import os

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.services.google_search_service import GoogleSearchService
from app.services.google_custom_search import GoogleCustomSearchAPI, SerpAPIClient
from app.config import settings


async def run_discovery_phase(
    phase: int,
    api_key: str,
    cse_id: str = None,
    use_serpapi: bool = False,
    max_entities: int = None,
    results_per_query: int = 10,
):
    """Run automated discovery for a specific phase.

    Args:
        phase: Phase number (1-4)
        api_key: Google Custom Search API key or SerpAPI key
        cse_id: Custom Search Engine ID (for Google API)
        use_serpapi: Use SerpAPI instead of Google Custom Search
        max_entities: Max entities to process (for testing)
        results_per_query: Results per search query
    """
    db = SessionLocal()

    try:
        # Load search queries for phase
        queries_file = (
            Path(__file__).resolve().parents[2]
            / "docs"
            / "data"
            / f"search-queries-phase_{phase}_critical.json"
            if phase == 1
            else Path(__file__).resolve().parents[2]
            / "docs"
            / "data"
            / f"search-queries-phase_{phase}_high.json"
            if phase == 2
            else Path(__file__).resolve().parents[2]
            / "docs"
            / "data"
            / f"search-queries-phase_{phase}_medium.json"
            if phase == 3
            else Path(__file__).resolve().parents[2]
            / "docs"
            / "data"
            / f"search-queries-phase_{phase}_all.json"
        )

        if not queries_file.exists():
            print(f"Error: Query file not found: {queries_file}")
            return

        print(f"Loading queries from: {queries_file}")
        with open(queries_file, "r", encoding="utf-8") as f:
            queries_data = json.load(f)

        print(f"Loaded queries for {len(queries_data)} entities")

        # Limit entities if specified (for testing)
        if max_entities:
            entities = list(queries_data.items())[:max_entities]
            queries_data = dict(entities)
            print(f"Limited to {max_entities} entities for testing")

        # Initialize API client
        if use_serpapi:
            print("Using SerpAPI")
            api_client = SerpAPIClient(api_key)
        else:
            if not cse_id:
                print("Error: --cse-id required for Google Custom Search API")
                return
            print("Using Google Custom Search API")
            api_client = GoogleCustomSearchAPI(api_key, cse_id)

        # Initialize search service
        search_service = GoogleSearchService(db)

        # Track statistics
        total_queries = 0
        total_candidates = 0
        entities_processed = 0

        # Process each entity
        for entity_name, entity_data in queries_data.items():
            print(f"\n{'='*60}")
            print(f"Processing: {entity_name}")
            print(f"Priority: {entity_data['priority']}")
            print(f"{'='*60}")

            entity_state = entity_data["state"]
            entity_type = entity_data["entity_type"]

            # Get all queries for this entity
            all_queries = (
                entity_data["basic_queries"]
                + entity_data["site_restricted_queries"]
                + entity_data["construction_queries"]
            )

            print(f"Total queries for {entity_name}: {len(all_queries)}")

            # Execute searches (limit to first 3 queries per entity to conserve API quota)
            for query in all_queries[:3]:
                try:
                    print(f"\nSearching: {query}")

                    # Execute search
                    results = await api_client.search(
                        query, num_results=results_per_query
                    )

                    if not results:
                        print("  No results found")
                        continue

                    print(f"  Found {len(results)} results")

                    # Store candidates
                    candidates = await search_service.search_and_store(
                        query=query,
                        entity_name=entity_name,
                        entity_state=entity_state,
                        entity_type=entity_type,
                        max_results=len(results),
                    )

                    total_candidates += len(candidates)
                    total_queries += 1

                    print(f"  Stored {len(candidates)} new candidates")

                    # Rate limiting - wait between queries
                    await asyncio.sleep(1.0)

                except Exception as e:
                    print(f"  Error: {str(e)}")
                    if "rate limit" in str(e).lower():
                        print("\nRate limit exceeded - stopping")
                        break
                    continue

            entities_processed += 1

            # Progress update
            print(f"\nProgress: {entities_processed}/{len(queries_data)} entities")
            print(f"Total queries: {total_queries}, Total candidates: {total_candidates}")

        # Final statistics
        print(f"\n{'='*60}")
        print("DISCOVERY COMPLETE")
        print(f"{'='*60}")
        print(f"Entities processed: {entities_processed}")
        print(f"Queries executed: {total_queries}")
        print(f"Candidates discovered: {total_candidates}")

        # Get database statistics
        stats = search_service.get_statistics()
        print(f"\nDatabase Statistics:")
        print(f"  Total candidates: {stats['total_candidates']}")
        print(f"  By status: {stats['by_status']}")
        print(f"  By state: {stats['by_state']}")
        print(f"  Avg relevance score: {stats['average_relevance_score']:.1f}")
        print(f"  Gov domains: {stats['government_domain_percentage']:.1f}%")

        # Close API client
        await api_client.close()

        print("\nNext steps:")
        print("1. Review candidates: python scripts/review_candidates.py")
        print("2. Export to CSV: python scripts/export_candidates.py")
        print("3. Verify high-priority candidates manually")

    finally:
        db.close()


async def test_search_api(api_key: str, cse_id: str = None, use_serpapi: bool = False):
    """Test search API with a single query.

    Args:
        api_key: API key
        cse_id: CSE ID (for Google)
        use_serpapi: Use SerpAPI
    """
    print("Testing search API...")

    test_query = "Bergen County NJ procurement"

    if use_serpapi:
        print("Using SerpAPI")
        async with SerpAPIClient(api_key) as client:
            results = await client.search(test_query, num_results=5)
    else:
        if not cse_id:
            print("Error: --cse-id required for Google Custom Search")
            return
        print("Using Google Custom Search API")
        async with GoogleCustomSearchAPI(api_key, cse_id) as client:
            results = await client.search(test_query, num_results=5)

    print(f"\nResults for '{test_query}':")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['title']}")
        print(f"   URL: {result['url']}")
        print(f"   Snippet: {result['snippet'][:100]}...")

    print(f"\nSuccess! Found {len(results)} results")
    print("API is working correctly")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Automated website discovery via Google search"
    )
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4],
        help="Discovery phase (1=critical, 2=high, 3=medium, 4=all)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Google Custom Search API key or SerpAPI key",
    )
    parser.add_argument(
        "--cse-id",
        type=str,
        help="Custom Search Engine ID (required for Google API)",
    )
    parser.add_argument(
        "--use-serpapi",
        action="store_true",
        help="Use SerpAPI instead of Google Custom Search",
    )
    parser.add_argument(
        "--max-entities",
        type=int,
        help="Max entities to process (for testing)",
    )
    parser.add_argument(
        "--results-per-query",
        type=int,
        default=10,
        help="Results per search query (default: 10)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test API connection with single query",
    )

    args = parser.parse_args()

    # Get API key from args or environment
    api_key = args.api_key or os.getenv("GOOGLE_SEARCH_API_KEY")
    if not api_key:
        print("Error: API key required")
        print("Provide via --api-key or GOOGLE_SEARCH_API_KEY env variable")
        return

    # Get CSE ID if using Google API
    cse_id = args.cse_id or os.getenv("GOOGLE_CSE_ID")
    if not args.use_serpapi and not cse_id:
        print("Error: CSE ID required for Google Custom Search API")
        print("Provide via --cse-id or GOOGLE_CSE_ID env variable")
        print("Or use --use-serpapi to use SerpAPI instead")
        return

    # Run test or discovery
    if args.test:
        asyncio.run(test_search_api(api_key, cse_id, args.use_serpapi))
    elif args.phase:
        asyncio.run(
            run_discovery_phase(
                args.phase,
                api_key,
                cse_id,
                args.use_serpapi,
                args.max_entities,
                args.results_per_query,
            )
        )
    else:
        print("Error: Specify --phase or --test")
        parser.print_help()


if __name__ == "__main__":
    main()
