"""Generate Google search queries from entity list for automated discovery.

This script reads the comprehensive entity list and generates search queries
that can be used to find procurement portals programmatically.
"""
import sys
from pathlib import Path
import pandas as pd
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# Procurement-related keywords
PROCUREMENT_TERMS = [
    "procurement",
    "purchasing",
    "bids",
    "current bids",
    "bid opportunities",
    "RFP",
    "RFQ",
    "IFB",
    "solicitations",
    "contracts",
]

# Construction-specific terms
CONSTRUCTION_TERMS = [
    "construction bids",
    "construction RFP",
    "public works",
    "capital projects",
    "construction contracts",
]


def load_entities(csv_path: str) -> pd.DataFrame:
    """Load entities from CSV file."""
    df = pd.read_csv(csv_path)
    return df


def generate_basic_queries(entity_name: str, search_keywords: str) -> list[str]:
    """Generate basic search queries for an entity.

    Args:
        entity_name: Official entity name
        search_keywords: Comma-separated search term variations

    Returns:
        List of search query strings
    """
    queries = []

    # Parse keywords
    keywords = [k.strip() for k in search_keywords.split(",")]

    # For each keyword variation
    for keyword in keywords:
        # Basic procurement query
        queries.append(f'"{keyword}" procurement')

        # Current bids query
        queries.append(f'"{keyword}" current bids')

        # RFP query
        queries.append(f'"{keyword}" RFP')

    return queries


def generate_site_restricted_queries(
    entity_name: str, state: str, search_keywords: str
) -> list[str]:
    """Generate site-restricted search queries.

    Args:
        entity_name: Official entity name
        state: State code (NY, NJ, CT)
        search_keywords: Comma-separated search term variations

    Returns:
        List of site-restricted search queries
    """
    queries = []

    # Determine domain extension
    if state == "NJ":
        domains = ["nj.us", "nj.gov"]
    elif state == "NY":
        domains = ["ny.us", "ny.gov", "nyc.gov"]
    elif state == "CT":
        domains = ["ct.us", "ct.gov"]
    else:
        domains = ["gov"]

    keywords = [k.strip() for k in search_keywords.split(",")]

    for keyword in keywords[:2]:  # Limit to top 2 keyword variations
        for domain in domains:
            queries.append(f'site:.{domain} "{keyword}" procurement')
            queries.append(f'site:.{domain} "{keyword}" current bids')

    return queries


def generate_construction_specific_queries(
    entity_name: str, search_keywords: str
) -> list[str]:
    """Generate construction-specific queries.

    Args:
        entity_name: Official entity name
        search_keywords: Comma-separated search term variations

    Returns:
        List of construction-focused queries
    """
    queries = []
    keywords = [k.strip() for k in search_keywords.split(",")]

    for keyword in keywords[:1]:  # Use primary keyword only
        queries.append(f'"{keyword}" construction bids')
        queries.append(f'"{keyword}" public works RFP')
        queries.append(f'"{keyword}" capital projects procurement')

    return queries


def generate_all_queries(df: pd.DataFrame, priority_min: int = 0) -> dict:
    """Generate all search queries for entities.

    Args:
        df: DataFrame with entity data
        priority_min: Minimum priority (0-10) to include

    Returns:
        Dict mapping entity names to their search queries
    """
    results = {}

    # Filter by priority
    df_filtered = df[df["priority"] >= priority_min].copy()

    print(f"Generating queries for {len(df_filtered)} entities (priority >= {priority_min})")

    for idx, row in df_filtered.iterrows():
        entity_name = row["entity_name"]
        state = row["state"]
        search_keywords = row["search_keywords"]
        priority = row["priority"]

        queries = {
            "entity_name": entity_name,
            "state": state,
            "entity_type": row["entity_type"],
            "priority": int(priority),
            "basic_queries": generate_basic_queries(entity_name, search_keywords),
            "site_restricted_queries": generate_site_restricted_queries(
                entity_name, state, search_keywords
            ),
            "construction_queries": generate_construction_specific_queries(
                entity_name, search_keywords
            ),
        }

        results[entity_name] = queries

    return results


def export_queries_json(queries: dict, output_path: str):
    """Export queries to JSON file.

    Args:
        queries: Dict of entity queries
        output_path: Path to output JSON file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, indent=2)

    print(f"Success: Exported queries to {output_path}")


def export_queries_txt(queries: dict, output_path: str):
    """Export queries to plain text file (one per line).

    Args:
        queries: Dict of entity queries
        output_path: Path to output text file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        for entity_name, data in queries.items():
            f.write(f"\n# {entity_name} (Priority {data['priority']})\n")

            # Write all queries
            all_queries = (
                data["basic_queries"]
                + data["site_restricted_queries"]
                + data["construction_queries"]
            )

            for query in all_queries:
                f.write(f"{query}\n")

    print(f"Success: Exported text queries to {output_path}")


def generate_priority_batches(df: pd.DataFrame) -> dict:
    """Generate queries in priority batches for phased execution.

    Args:
        df: DataFrame with entity data

    Returns:
        Dict with queries organized by priority batch
    """
    batches = {
        "phase_1_critical": generate_all_queries(df, priority_min=9),  # Priority 9-10
        "phase_2_high": generate_all_queries(df[df["priority"].between(7, 8)], priority_min=7),
        "phase_3_medium": generate_all_queries(df[df["priority"].between(5, 6)], priority_min=5),
        "phase_4_all": generate_all_queries(df, priority_min=4),
    }

    return batches


def main():
    """Main execution function."""
    # Paths
    csv_path = Path(__file__).resolve().parents[2] / "docs" / "data" / "tristate-entities-comprehensive.csv"
    output_dir = Path(__file__).resolve().parents[2] / "docs" / "data"

    if not csv_path.exists():
        print(f"Error: Error: CSV file not found at {csv_path}")
        return

    # Load entities
    print(f"Loading entities from {csv_path}")
    df = load_entities(str(csv_path))
    print(f"Loaded {len(df)} entities")

    # Generate queries for all entities
    print("\nGenerating search queries...")
    all_queries = generate_all_queries(df, priority_min=4)

    # Export to JSON
    json_output = output_dir / "search-queries-all.json"
    export_queries_json(all_queries, str(json_output))

    # Export to text
    txt_output = output_dir / "search-queries-all.txt"
    export_queries_txt(all_queries, str(txt_output))

    # Generate priority batches
    print("\nGenerating priority batches...")
    batches = generate_priority_batches(df)

    for batch_name, batch_queries in batches.items():
        json_output = output_dir / f"search-queries-{batch_name}.json"
        export_queries_json(batch_queries, str(json_output))

    # Summary
    print("\nSummary:")
    print(f"  Total entities: {len(df)}")
    print(f"  Priority 9-10 (Critical): {len(batches['phase_1_critical'])} entities")
    print(f"  Priority 7-8 (High): {len(batches['phase_2_high'])} entities")
    print(f"  Priority 5-6 (Medium): {len(batches['phase_3_medium'])} entities")
    print(f"  Priority 4+ (All): {len(batches['phase_4_all'])} entities")

    # Calculate total queries
    total_queries = sum(
        len(data["basic_queries"])
        + len(data["site_restricted_queries"])
        + len(data["construction_queries"])
        for data in all_queries.values()
    )
    print(f"  Total search queries generated: {total_queries}")

    print("\nQuery generation complete!")
    print("\nNext steps:")
    print("1. Review generated queries in docs/data/search-queries-*.json")
    print("2. Use automated_entity_search.py to execute searches")
    print("3. Analyze results to find procurement portals")


if __name__ == "__main__":
    main()
