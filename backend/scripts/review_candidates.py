"""Review discovered candidate websites.

Interactive script to review and verify candidate websites.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.services.google_search_service import GoogleSearchService
from app.models.candidate_website import WebsiteStatus


def review_candidates_interactive():
    """Interactive review of candidates."""
    db = SessionLocal()

    try:
        service = GoogleSearchService(db)

        # Get statistics
        stats = service.get_statistics()
        print("="*60)
        print("CANDIDATE WEBSITE REVIEW")
        print("="*60)
        print(f"Total candidates: {stats['total_candidates']}")
        print(f"By status: {stats['by_status']}")
        print(f"By state: {stats['by_state']}")
        print(f"Avg relevance: {stats['average_relevance_score']:.1f}")
        print(f"Gov domains: {stats['government_domain_percentage']:.1f}%\n")

        # Get candidates needing review
        candidates = service.get_candidates_for_review(
            status=WebsiteStatus.DISCOVERED, limit=50
        )

        if not candidates:
            print("No candidates need review!")
            return

        print(f"Found {len(candidates)} candidates needing review\n")

        reviewed = 0

        for candidate in candidates:
            print("="*60)
            print(f"CANDIDATE {reviewed + 1}/{len(candidates)}")
            print("="*60)
            print(f"Entity: {candidate.entity_name} ({candidate.entity_state})")
            print(f"URL: {candidate.url}")
            print(f"Title: {candidate.title}")
            print(f"Description: {candidate.description or 'N/A'}")
            print(f"Search query: {candidate.search_query}")
            print(f"Search rank: {candidate.search_rank}")
            print(f"Relevance score: {candidate.relevance_score:.1f}")
            print(f"Keywords found: {', '.join(candidate.procurement_keywords_found) if candidate.procurement_keywords_found else 'None'}")
            print(f"Gov domain: {'Yes' if candidate.is_government_domain else 'No'}")
            print(f"Priority: {candidate.priority}/10")

            print("\nActions:")
            print("  v = Verified (has RFPs)")
            print("  a = Approved (ready for scraping)")
            print("  r = Rejected (no RFPs)")
            print("  d = Duplicate")
            print("  i = Inaccessible")
            print("  s = Skip (review later)")
            print("  o = Open URL in browser")
            print("  q = Quit")

            action = input("\nAction: ").lower().strip()

            if action == "q":
                print("\nExiting review...")
                break
            elif action == "s":
                print("Skipped\n")
                continue
            elif action == "o":
                import webbrowser
                webbrowser.open(candidate.url)
                print(f"Opened {candidate.url} in browser")
                continue
            elif action == "v":
                status = WebsiteStatus.VERIFIED
            elif action == "a":
                status = WebsiteStatus.APPROVED
            elif action == "r":
                status = WebsiteStatus.REJECTED
            elif action == "d":
                status = WebsiteStatus.DUPLICATE
            elif action == "i":
                status = WebsiteStatus.INACCESSIBLE
            else:
                print("Invalid action, skipping")
                continue

            # Get notes
            notes = input("Notes (optional): ").strip() or None

            # Verify
            service.verify_candidate(
                str(candidate.id),
                status,
                verified_by="manual_review",
                notes=notes,
            )

            reviewed += 1
            print(f"Marked as {status.value}\n")

        print("="*60)
        print(f"Reviewed {reviewed} candidates")
        print("="*60)

        # Updated stats
        stats = service.get_statistics()
        print(f"\nUpdated statistics:")
        print(f"By status: {stats['by_status']}")

    finally:
        db.close()


def list_candidates(status: str = None, limit: int = 50):
    """List candidates by status.

    Args:
        status: Filter by status (discovered, verified, approved, etc.)
        limit: Max results
    """
    db = SessionLocal()

    try:
        service = GoogleSearchService(db)

        if status:
            status_enum = WebsiteStatus(status.lower())
            candidates = service.get_candidates_for_review(status_enum, limit)
            print(f"\nCandidates with status '{status}':\n")
        else:
            from app.models.candidate_website import CandidateWebsite
            candidates = (
                db.query(CandidateWebsite)
                .order_by(CandidateWebsite.priority.desc())
                .limit(limit)
                .all()
            )
            print(f"\nAll candidates (top {limit}):\n")

        for i, candidate in enumerate(candidates, 1):
            print(f"{i}. {candidate.entity_name} ({candidate.entity_state})")
            print(f"   URL: {candidate.url}")
            print(f"   Status: {candidate.status.value}")
            print(f"   Priority: {candidate.priority}/10, Score: {candidate.relevance_score:.1f}")
            print(f"   Gov domain: {'Yes' if candidate.is_government_domain else 'No'}")
            print()

        print(f"Total: {len(candidates)} candidates")

    finally:
        db.close()


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Review candidate websites")
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Interactive review mode",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List candidates",
    )
    parser.add_argument(
        "--status",
        type=str,
        choices=["discovered", "verified", "approved", "rejected", "duplicate", "inaccessible"],
        help="Filter by status",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max results (default: 50)",
    )

    args = parser.parse_args()

    if args.interactive:
        review_candidates_interactive()
    elif args.list:
        list_candidates(args.status, args.limit)
    else:
        # Default: interactive mode
        review_candidates_interactive()


if __name__ == "__main__":
    main()
