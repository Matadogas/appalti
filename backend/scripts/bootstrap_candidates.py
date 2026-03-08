"""Bootstrap candidate websites from entity list using common URL patterns.

This script generates candidate URLs based on common government procurement portal patterns
without needing the Google Search API.
"""
import sys
import csv
import json
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def generate_url_patterns(entity_name: str, state: str, entity_type: str) -> List[Dict]:
    """Generate common URL patterns for government procurement portals.

    Args:
        entity_name: Entity name (e.g., "Bergen County")
        state: State code (NY, NJ, CT)
        entity_type: Type of entity (county, city, etc.)

    Returns:
        List of candidate URLs with metadata
    """
    candidates = []

    # Normalize entity name for URLs
    name_lower = entity_name.lower()
    name_slug = name_lower.replace(" ", "").replace(".", "").replace("'", "")
    name_dash = name_lower.replace(" ", "-").replace(".", "").replace("'", "")
    name_underscore = name_lower.replace(" ", "_").replace(".", "").replace("'", "")

    # Extract base name (remove "County", "City", etc.)
    base_name = entity_name
    for suffix in [" County", " City", " Township", " Village", " Town", " Borough"]:
        if base_name.endswith(suffix):
            base_name = base_name[:-len(suffix)]
            break

    base_slug = base_name.lower().replace(" ", "").replace(".", "").replace("'", "")
    base_dash = base_name.lower().replace(" ", "-").replace(".", "").replace("'", "")

    # State-specific TLDs
    state_tld_map = {
        "NY": "ny.us",
        "NJ": "nj.us",
        "CT": "ct.us",
    }
    state_tld = state_tld_map.get(state, "gov")

    # Common URL patterns for government procurement portals
    url_patterns = []

    # Pattern 1: .gov domains
    if entity_type == "county":
        url_patterns.extend([
            f"https://{name_slug}.gov/procurement",
            f"https://{name_slug}.gov/purchasing",
            f"https://{name_slug}.gov/bids",
            f"https://www.co.{base_slug}.{state.lower()}.us/procurement",
            f"https://www.{base_slug}county{state.lower()}.gov/procurement",
            f"https://{base_slug}countynj.org/procurement" if state == "NJ" else None,
        ])
    elif entity_type == "city":
        url_patterns.extend([
            f"https://{name_slug}.gov/procurement",
            f"https://{name_slug}.gov/purchasing",
            f"https://{name_slug}.gov/bids",
            f"https://www.cityof{base_slug}.{state.lower()}.us/procurement",
            f"https://{base_slug}nj.org/procurement" if state == "NJ" else None,
        ])
    elif entity_type == "authority":
        url_patterns.extend([
            f"https://{name_slug}.org/procurement",
            f"https://{name_slug}.gov/procurement",
            f"https://www.{name_slug}.org/bids",
        ])
    elif entity_type == "school_district":
        url_patterns.extend([
            f"https://{name_slug}.org/procurement",
            f"https://{name_slug}.k12.{state.lower()}.us/purchasing",
        ])

    # Pattern 2: Common procurement paths
    procurement_paths = [
        "/procurement",
        "/purchasing",
        "/bids",
        "/rfp",
        "/solicitations",
        "/bid-opportunities",
        "/current-bids",
        "/open-bids",
        "/vendor-opportunities",
    ]

    # Pattern 3: Third-party platforms
    third_party_patterns = [
        f"https://{name_dash}.bonfirehub.com",
        f"https://{name_slug}.bidsync.com",
        f"https://{name_slug}.ionwave.net",
        f"https://{name_slug}.questcdn.com",
        f"https://{name_slug}.publicpurchase.com",
    ]

    url_patterns.extend(third_party_patterns)

    # Remove None values and duplicates
    url_patterns = list(set([p for p in url_patterns if p]))

    # Create candidate objects
    for url in url_patterns:
        # Determine likely platform/vendor
        vendor = "custom_html"
        if "bonfirehub" in url:
            vendor = "bonfire"
        elif "bidsync" in url:
            vendor = "bidsync"
        elif "ionwave" in url:
            vendor = "ionwave"
        elif "questcdn" in url:
            vendor = "questcdn"
        elif "publicpurchase" in url:
            vendor = "publicpurchase"

        candidates.append({
            "entity_name": entity_name,
            "entity_state": state,
            "entity_type": entity_type,
            "url": url,
            "estimated_vendor": vendor,
            "confidence": "low",  # Since we're guessing
        })

    return candidates


def bootstrap_from_entity_list(
    entity_csv_path: str,
    output_json_path: str,
    output_csv_path: str,
):
    """Generate bootstrap candidate list from entity CSV.

    Args:
        entity_csv_path: Path to tristate-entities-comprehensive.csv
        output_json_path: Output JSON file path
        output_csv_path: Output CSV file path
    """
    print(f"Loading entities from {entity_csv_path}...")

    all_candidates = []

    # Read entity list
    with open(entity_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        entities = list(reader)

    print(f"Found {len(entities)} entities")
    print("Generating candidate URLs...")

    # Generate candidates for each entity
    for entity in entities:
        entity_name = entity["entity_name"]
        state = entity["state"]
        entity_type = entity["entity_type"]
        priority = int(entity.get("priority", 5))

        # Generate URL patterns
        candidates = generate_url_patterns(entity_name, state, entity_type)

        # Add priority and other metadata
        for candidate in candidates:
            candidate["priority"] = priority
            candidate["search_keywords"] = entity.get("search_keywords", "")

        all_candidates.extend(candidates)

    print(f"Generated {len(all_candidates)} candidate URLs")

    # Write JSON output
    print(f"Writing JSON to {output_json_path}...")
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(all_candidates, f, indent=2)

    # Write CSV output
    print(f"Writing CSV to {output_csv_path}...")
    with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "entity_name",
            "entity_state",
            "entity_type",
            "url",
            "estimated_vendor",
            "confidence",
            "priority",
            "search_keywords",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_candidates)

    # Summary statistics
    by_state = {}
    by_type = {}
    by_vendor = {}

    for candidate in all_candidates:
        state = candidate["entity_state"]
        entity_type = candidate["entity_type"]
        vendor = candidate["estimated_vendor"]

        by_state[state] = by_state.get(state, 0) + 1
        by_type[entity_type] = by_type.get(entity_type, 0) + 1
        by_vendor[vendor] = by_vendor.get(vendor, 0) + 1

    print("\n" + "="*60)
    print("BOOTSTRAP COMPLETE")
    print("="*60)
    print(f"Total candidates: {len(all_candidates)}")
    print(f"By state: {by_state}")
    print(f"By entity type: {by_type}")
    print(f"By platform: {by_vendor}")
    print(f"\nOutput files:")
    print(f"  JSON: {output_json_path}")
    print(f"  CSV: {output_csv_path}")
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Review the candidate list CSV")
    print("2. Fix Google Search API configuration:")
    print("   - Enable Custom Search API in Google Cloud Console")
    print("   - Check API key restrictions")
    print("   - Verify CSE is configured to search entire web")
    print("3. Run automated discovery to validate/score these URLs")
    print("4. Use web scraping to check which URLs actually exist")
    print("5. Manual verification of high-priority candidates")
    print("="*60)


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Bootstrap candidate websites from entity list"
    )
    parser.add_argument(
        "--entities",
        type=str,
        default="../../docs/data/tristate-entities-comprehensive.csv",
        help="Path to entity CSV",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="bootstrap_candidates.json",
        help="Output JSON file",
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="bootstrap_candidates.csv",
        help="Output CSV file",
    )

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    entities_path = (script_dir / args.entities).resolve()
    output_json = (script_dir / args.output_json).resolve()
    output_csv = (script_dir / args.output_csv).resolve()

    if not entities_path.exists():
        print(f"Error: Entity CSV not found at {entities_path}")
        sys.exit(1)

    bootstrap_from_entity_list(
        str(entities_path),
        str(output_json),
        str(output_csv),
    )


if __name__ == "__main__":
    main()
