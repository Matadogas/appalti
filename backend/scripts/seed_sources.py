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
                "base_url": "https://www1.nyc.gov/site/mocs/public-rfx/public-rfx.page",
                "scraper_class": "nyc_passport",
                "active": True,
                "config": {},
            },
            {
                "name": "NYS OGS Procurement",
                "state": "NY",
                "base_url": "https://online.ogs.ny.gov/purchase/spg/",
                "scraper_class": "nys_ogs",
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
