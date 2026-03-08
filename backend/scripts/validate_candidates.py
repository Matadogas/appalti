"""Validate candidate URLs by checking if they're accessible.

This script checks each candidate URL to see if it responds with a valid HTTP status.
"""
import sys
import csv
import json
import asyncio
from pathlib import Path
from typing import List, Dict
import httpx
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def check_url(client: httpx.AsyncClient, url: str) -> Dict:
    """Check if a URL is accessible.

    Args:
        client: HTTP client
        url: URL to check

    Returns:
        Dict with url, status, accessible, redirect_url
    """
    result = {
        "url": url,
        "status": None,
        "accessible": False,
        "redirect_url": None,
        "error": None,
    }

    try:
        response = await client.head(
            url,
            follow_redirects=True,
            timeout=10.0,
        )
        result["status"] = response.status_code
        result["accessible"] = 200 <= response.status_code < 400

        if response.url != url:
            result["redirect_url"] = str(response.url)

    except httpx.TimeoutException:
        result["error"] = "timeout"
    except httpx.ConnectError:
        result["error"] = "connection_failed"
    except Exception as e:
        result["error"] = str(e)[:100]

    return result


async def validate_candidates(
    input_csv: str,
    output_csv: str,
    max_concurrent: int = 50,
    limit: int = None,
):
    """Validate candidate URLs.

    Args:
        input_csv: Input CSV with candidates
        output_csv: Output CSV with validation results
        max_concurrent: Max concurrent requests
        limit: Max URLs to check (for testing)
    """
    print(f"Loading candidates from {input_csv}...")

    # Read candidates
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        candidates = list(reader)

    if limit:
        candidates = candidates[:limit]
        print(f"Limited to first {limit} candidates for testing")

    print(f"Validating {len(candidates)} candidate URLs...")
    print(f"Max concurrent requests: {max_concurrent}")

    # Create HTTP client
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=10.0,
        limits=httpx.Limits(max_connections=max_concurrent),
    ) as client:
        # Create tasks
        tasks = []
        for candidate in candidates:
            url = candidate["url"]
            task = check_url(client, url)
            tasks.append((candidate, task))

        # Execute with progress bar
        results = []
        accessible_count = 0

        # Use tqdm for progress tracking
        for candidate, task in tqdm(tasks, desc="Validating URLs"):
            validation = await task

            # Merge candidate data with validation result
            result = {**candidate, **validation}
            results.append(result)

            if validation["accessible"]:
                accessible_count += 1

    # Write results
    print(f"\nWriting results to {output_csv}...")

    fieldnames = [
        "entity_name",
        "entity_state",
        "entity_type",
        "url",
        "accessible",
        "status",
        "redirect_url",
        "error",
        "estimated_vendor",
        "confidence",
        "priority",
        "search_keywords",
    ]

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Summary statistics
    total = len(results)
    accessible = accessible_count
    inaccessible = total - accessible

    by_state = {}
    by_vendor = {}
    accessible_by_state = {}

    for result in results:
        state = result["entity_state"]
        vendor = result["estimated_vendor"]
        is_accessible = result["accessible"]

        by_state[state] = by_state.get(state, 0) + 1
        by_vendor[vendor] = by_vendor.get(vendor, 0) + 1

        if is_accessible:
            accessible_by_state[state] = accessible_by_state.get(state, 0) + 1

    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60)
    print(f"Total URLs checked: {total}")
    print(f"Accessible: {accessible} ({accessible/total*100:.1f}%)")
    print(f"Inaccessible: {inaccessible} ({inaccessible/total*100:.1f}%)")
    print(f"\nAccessible by state: {accessible_by_state}")
    print(f"\nOutput file: {output_csv}")
    print("="*60)


def create_final_target_list(
    validated_csv: str,
    output_csv: str,
    accessible_only: bool = True,
):
    """Create final target list for scraping.

    Args:
        validated_csv: CSV with validated candidates
        output_csv: Final output CSV
        accessible_only: Only include accessible URLs
    """
    print(f"Creating final target list from {validated_csv}...")

    # Read validated candidates
    with open(validated_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        candidates = list(reader)

    # Filter to accessible only
    if accessible_only:
        candidates = [c for c in candidates if c["accessible"] == "True"]
        print(f"Filtered to {len(candidates)} accessible URLs")

    # Write final list
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "website_url",
            "website_name",
            "state",
            "entity_type",
            "entity_name",
            "estimated_platform",
            "priority",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for candidate in candidates:
            writer.writerow({
                "website_url": candidate["url"],
                "website_name": candidate["entity_name"],
                "state": candidate["entity_state"],
                "entity_type": candidate["entity_type"],
                "entity_name": candidate["entity_name"],
                "estimated_platform": candidate["estimated_vendor"],
                "priority": candidate["priority"],
            })

    print(f"Final target list written to {output_csv}")
    print(f"Total targets: {len(candidates)}")


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate candidate URLs")
    parser.add_argument(
        "--input",
        type=str,
        default="bootstrap_candidates.csv",
        help="Input CSV with candidates",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="validated_candidates.csv",
        help="Output CSV with validation results",
    )
    parser.add_argument(
        "--final-output",
        type=str,
        default="target_websites.csv",
        help="Final target list CSV",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=50,
        help="Max concurrent requests",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of URLs to check (for testing)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation, just create final list from existing validated CSV",
    )

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent
    input_csv = (script_dir / args.input).resolve()
    output_csv = (script_dir / args.output).resolve()
    final_output = (script_dir / args.final_output).resolve()

    if not args.skip_validation:
        if not input_csv.exists():
            print(f"Error: Input CSV not found at {input_csv}")
            sys.exit(1)

        # Run validation
        asyncio.run(
            validate_candidates(
                str(input_csv),
                str(output_csv),
                args.max_concurrent,
                args.limit,
            )
        )

    # Create final target list
    if output_csv.exists():
        create_final_target_list(
            str(output_csv),
            str(final_output),
            accessible_only=True,
        )
    else:
        print(f"Error: Validated CSV not found at {output_csv}")
        print("Run validation first or provide existing validated CSV")


if __name__ == "__main__":
    main()
