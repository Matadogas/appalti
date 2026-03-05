"""Seed initial sources into database."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.source import Source


def seed_sources():
    """Seed initial sources."""
    db = SessionLocal()

    try:
        sources = [
            {
                "name": "NYC PASSPort",
                "state": "NY",
                "base_url": "https://passport.cityofnewyork.us/page.aspx/en/rfp/request_browse_public",
                "scraper_class": "nyc_passport",
                "active": True,
                "config": {},
            },
            {
                "name": "NYS OGS Procurement",
                "state": "NY",
                "base_url": "https://ogs.ny.gov/procurement/bid-opportunities",
                "scraper_class": "nys_ogs",
                "active": True,
                "config": {},
            },
            {
                "name": "Port Authority of NY & NJ",
                "state": "NY",
                "base_url": "https://panynj.bonfirehub.com/PublicPortal/getOpenPublicOpportunitiesSectionData",
                "scraper_class": "port_authority",
                "active": True,
                "config": {},
            },
        ]

        for source_data in sources:
            # Check if source exists
            existing = (
                db.query(Source)
                .filter(Source.name == source_data["name"])
                .first()
            )

            if existing:
                # Update URL if it changed
                if existing.base_url != source_data["base_url"]:
                    existing.base_url = source_data["base_url"]
                    print(f"Updated URL for source: {source_data['name']}")
                else:
                    print(f"Source '{source_data['name']}' already exists")
                continue

            source = Source(**source_data)
            db.add(source)
            print(f"Added source: {source_data['name']}")

        db.commit()
        print("Sources seeded successfully")

    except Exception as e:
        print(f"Error seeding sources: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_sources()
