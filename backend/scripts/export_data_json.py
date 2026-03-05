"""Export scraped data as JSON for the frontend demo."""
import asyncio
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.scrapers.sources.port_authority import PortAuthorityScraper
from app.scrapers.sources.nyc_passport import NYCPassportScraper
from app.scrapers.sources.nys_ogs import NYSOGSScraper


async def main():
    scrapers = [
        ("Port Authority of NY & NJ", PortAuthorityScraper),
        ("NYC PASSPort", NYCPassportScraper),
        ("NYS OGS Procurement", NYSOGSScraper),
    ]

    all_tenders = []
    source_counts = {}

    for source_name, scraper_class in scrapers:
        print(f"Scraping {source_name}...")
        scraper = scraper_class()
        try:
            tenders = await scraper.scrape()
            source_counts[source_name] = len(tenders)
            print(f"  Got {len(tenders)} tenders")

            for tender in tenders:
                # Generate stable ID from fingerprint
                components = [tender.source_url, tender.title, str(tender.publish_date) if tender.publish_date else ""]
                fp = hashlib.sha256("|".join(components).encode()).hexdigest()[:12]

                # Extract due date from rawRef if not set
                due_date = tender.due_date
                if not due_date and tender.raw_ref:
                    raw = tender.raw_ref.get("raw", {})
                    date_close = raw.get("DateClose", "")
                    if date_close:
                        try:
                            due_date = datetime.strptime(date_close.split(" ")[0], "%Y-%m-%d")
                        except (ValueError, IndexError):
                            pass

                # Skip placeholder dates far in the future
                due_str = None
                if due_date:
                    if due_date.year < 2090:
                        due_str = due_date.strftime("%Y-%m-%d")

                # Clean up title - remove duplicate ref prefix
                title = tender.title
                parts = title.split(" - ", 2)
                if len(parts) >= 3 and parts[0].strip() == parts[1].strip():
                    title = f"{parts[0].strip()} - {parts[2].strip()}"

                all_tenders.append({
                    "id": fp,
                    "title": title,
                    "agency": tender.agency,
                    "state": tender.state,
                    "city": tender.city or "",
                    "category": tender.category.value,
                    "status": tender.status.value,
                    "dueDate": due_str,
                    "publishDate": tender.publish_date.strftime("%Y-%m-%d") if tender.publish_date else None,
                    "sourceUrl": tender.source_url,
                    "source": source_name,
                    "description": tender.description_text or "",
                    "rawRef": tender.raw_ref or {},
                })
        except Exception as e:
            print(f"  FAILED: {e}")

    output = {
        "scrapedAt": datetime.now().isoformat(),
        "totalCount": len(all_tenders),
        "sourceCounts": source_counts,
        "tenders": all_tenders,
    }

    # Write to frontend data dir
    out_path = Path(__file__).resolve().parents[2] / "frontend" / "src" / "data"
    out_path.mkdir(parents=True, exist_ok=True)
    out_file = out_path / "tenders.json"
    out_file.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nExported {len(all_tenders)} tenders to {out_file}")


if __name__ == "__main__":
    asyncio.run(main())
