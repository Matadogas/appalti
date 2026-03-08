"""Export candidate websites to CSV for review."""
import sys
from pathlib import Path
import csv
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.candidate_website import CandidateWebsite, WebsiteStatus


def export_candidates_csv(
    output_path: str = None,
    status: WebsiteStatus = None,
    min_priority: int = 0,
):
    """Export candidates to CSV.

    Args:
        output_path: Output CSV file path
        status: Filter by status
        min_priority: Minimum priority (0-10)
    """
    db = SessionLocal()

    try:
        # Build query
        query = db.query(CandidateWebsite)

        if status:
            query = query.filter(CandidateWebsite.status == status)

        if min_priority > 0:
            query = query.filter(CandidateWebsite.priority >= min_priority)

        # Order by priority and relevance
        query = query.order_by(
            CandidateWebsite.priority.desc(),
            CandidateWebsite.relevance_score.desc(),
        )

        candidates = query.all()

        if not candidates:
            print("No candidates found matching criteria")
            return

        # Generate output path if not specified
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filter_str = f"_{status.value}" if status else ""
            output_path = f"candidates{filter_str}_{timestamp}.csv"

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "entity_name",
                "entity_state",
                "entity_type",
                "url",
                "title",
                "description",
                "status",
                "priority",
                "relevance_score",
                "gov_domain",
                "keywords_found",
                "search_query",
                "search_rank",
                "verified_by",
                "verification_notes",
                "discovered_at",
            ])

            # Data rows
            for candidate in candidates:
                writer.writerow([
                    candidate.entity_name,
                    candidate.entity_state,
                    candidate.entity_type,
                    candidate.url,
                    candidate.title,
                    candidate.description or "",
                    candidate.status.value,
                    candidate.priority,
                    f"{candidate.relevance_score:.1f}",
                    "Yes" if candidate.is_government_domain else "No",
                    ", ".join(candidate.procurement_keywords_found or []),
                    candidate.search_query,
                    candidate.search_rank,
                    candidate.verified_by or "",
                    candidate.verification_notes or "",
                    candidate.discovered_at.isoformat() if candidate.discovered_at else "",
                ])

        print(f"Success: Exported {len(candidates)} candidates to {output_path}")

        # Summary statistics
        by_status = {}
        by_state = {}
        for candidate in candidates:
            by_status[candidate.status.value] = by_status.get(candidate.status.value, 0) + 1
            by_state[candidate.entity_state or "Unknown"] = by_state.get(candidate.entity_state or "Unknown", 0) + 1

        print(f"\nExport Summary:")
        print(f"  Total candidates: {len(candidates)}")
        print(f"  By status: {by_status}")
        print(f"  By state: {by_state}")
        print(f"  Output file: {output_path}")

    finally:
        db.close()


def export_for_manual_verification(output_path: str = "candidates_for_review.csv"):
    """Export high-priority discovered candidates for manual verification.

    Args:
        output_path: Output CSV path
    """
    print("Exporting high-priority candidates for manual review...")

    export_candidates_csv(
        output_path=output_path,
        status=WebsiteStatus.DISCOVERED,
        min_priority=7,  # Priority 7+ only
    )

    print(f"\nManual review workflow:")
    print("1. Open {output_path} in Excel/Sheets")
    print("2. Add column 'verification_status' (verified/approved/rejected)")
    print("3. Add column 'notes' for comments")
    print("4. Save and import back using import_verified_candidates.py")


def export_approved_for_scraping(output_path: str = "candidates_approved_for_scraping.csv"):
    """Export approved candidates ready for Crawl4AI scraping.

    Args:
        output_path: Output CSV path
    """
    print("Exporting approved candidates for scraping...")

    export_candidates_csv(
        output_path=output_path,
        status=WebsiteStatus.APPROVED,
        min_priority=0,
    )

    print(f"\nNext steps:")
    print("1. Configure scrapers for these URLs")
    print("2. Use Crawl4AI to extract RFP data")
    print("3. Add to source_registry after successful scraping")


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Export candidate websites to CSV")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output CSV file path",
    )
    parser.add_argument(
        "--status",
        type=str,
        choices=["discovered", "verified", "approved", "rejected", "duplicate", "inaccessible"],
        help="Filter by status",
    )
    parser.add_argument(
        "--min-priority",
        type=int,
        default=0,
        help="Minimum priority (0-10, default: 0)",
    )
    parser.add_argument(
        "--for-review",
        action="store_true",
        help="Export high-priority candidates for manual review",
    )
    parser.add_argument(
        "--for-scraping",
        action="store_true",
        help="Export approved candidates for scraping",
    )

    args = parser.parse_args()

    if args.for_review:
        export_for_manual_verification(args.output or "candidates_for_review.csv")
    elif args.for_scraping:
        export_approved_for_scraping(args.output or "candidates_approved_for_scraping.csv")
    else:
        status_enum = WebsiteStatus(args.status) if args.status else None
        export_candidates_csv(
            output_path=args.output,
            status=status_enum,
            min_priority=args.min_priority,
        )


if __name__ == "__main__":
    main()
