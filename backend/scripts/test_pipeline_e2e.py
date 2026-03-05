"""End-to-end pipeline test - no Docker required.

Tests the full orchestration:
1. Scrapers fetch real data from government portals
2. Tender deduplication via fingerprinting
3. Database storage (SQLite for testing)
4. API query layer

Runs against live portals, uses SQLite in-memory for DB.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Override config BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite:///test_pipeline.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ANTHROPIC_API_KEY"] = "sk-test-placeholder"

# Now patch the database module to use SQLite
import sqlalchemy
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Import models (this triggers config load, but env vars are set)
from app.database import Base
from app.models.tender import Tender, TenderStatus, TenderCategory
from app.models.source import Source
from app.models.scrape_run import ScrapeRun

# Import scrapers
from app.scrapers.sources.port_authority import PortAuthorityScraper
from app.scrapers.sources.nyc_passport import NYCPassportScraper
from app.scrapers.sources.nys_ogs import NYSOGSScraper
from app.scrapers.base import BaseScraper

# Create SQLite engine for testing
DB_PATH = Path(__file__).parent / "test_pipeline.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# SQLite doesn't support UUID natively - we'll handle this
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

SessionLocal = sessionmaker(bind=engine)


def setup_database():
    """Create tables in SQLite."""
    print("\n[STEP 1] Setting up database...")

    # Drop and recreate
    if DB_PATH.exists():
        DB_PATH.unlink()

    # SQLite can't handle PostgreSQL-specific types directly,
    # so we create simplified tables
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text("""
            CREATE TABLE sources (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                state TEXT NOT NULL,
                base_url TEXT NOT NULL,
                scraper_class TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                config TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(sqlalchemy.text("""
            CREATE TABLE tenders (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                source_url TEXT NOT NULL,
                title TEXT NOT NULL,
                description_text TEXT,
                agency TEXT,
                state TEXT NOT NULL,
                city TEXT,
                county TEXT,
                category TEXT DEFAULT 'other',
                status TEXT DEFAULT 'active',
                publish_date TIMESTAMP,
                due_date TIMESTAMP,
                budget_amount REAL,
                currency TEXT DEFAULT 'USD',
                documents TEXT DEFAULT '[]',
                contact TEXT,
                fingerprint TEXT UNIQUE NOT NULL,
                ai_summary TEXT,
                ai_trade_tags TEXT DEFAULT '[]',
                ai_requirements TEXT,
                confidence REAL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_ref TEXT,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            )
        """))
        conn.execute(sqlalchemy.text("""
            CREATE TABLE scrape_runs (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                status TEXT DEFAULT 'running',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                tenders_found INTEGER DEFAULT 0,
                tenders_new INTEGER DEFAULT 0,
                tenders_updated INTEGER DEFAULT 0,
                error_message TEXT,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            )
        """))
        conn.commit()

    print("  Database created with tables: sources, tenders, scrape_runs")
    return True


def seed_sources():
    """Seed sources into database."""
    print("\n[STEP 2] Seeding sources...")
    import uuid
    import json

    with engine.connect() as conn:
        sources = [
            {
                "id": str(uuid.uuid4()),
                "name": "Port Authority of NY & NJ",
                "state": "NY",
                "base_url": "https://panynj.bonfirehub.com/PublicPortal/getOpenPublicOpportunitiesSectionData",
                "scraper_class": "port_authority",
                "config": "{}",
            },
            {
                "id": str(uuid.uuid4()),
                "name": "NYC PASSPort",
                "state": "NY",
                "base_url": "https://passport.cityofnewyork.us/page.aspx/en/rfp/request_browse_public",
                "scraper_class": "nyc_passport",
                "config": "{}",
            },
            {
                "id": str(uuid.uuid4()),
                "name": "NYS OGS Procurement",
                "state": "NY",
                "base_url": "https://ogs.ny.gov/procurement/bid-opportunities",
                "scraper_class": "nys_ogs",
                "config": "{}",
            },
        ]

        for s in sources:
            conn.execute(
                sqlalchemy.text(
                    "INSERT INTO sources (id, name, state, base_url, scraper_class, config) "
                    "VALUES (:id, :name, :state, :base_url, :scraper_class, :config)"
                ),
                s,
            )
        conn.commit()

    print(f"  Seeded {len(sources)} sources")
    return sources


async def run_scraper(scraper_class, source_id: str, source_name: str) -> dict:
    """Run a single scraper and store results."""
    import uuid
    import json
    import hashlib

    print(f"\n  --- Scraping: {source_name} ---")

    run_id = str(uuid.uuid4())
    scraper = scraper_class()

    with engine.connect() as conn:
        conn.execute(
            sqlalchemy.text(
                "INSERT INTO scrape_runs (id, source_id, status) VALUES (:id, :source_id, 'running')"
            ),
            {"id": run_id, "source_id": source_id},
        )
        conn.commit()

    try:
        tenders = await scraper.scrape()

        new_count = 0
        updated_count = 0

        with engine.connect() as conn:
            for tender in tenders:
                # Generate fingerprint
                components = [
                    tender.source_url,
                    tender.title,
                    str(tender.publish_date) if tender.publish_date else "",
                ]
                fingerprint = hashlib.sha256("|".join(components).encode()).hexdigest()

                # Check for existing
                existing = conn.execute(
                    sqlalchemy.text("SELECT id FROM tenders WHERE fingerprint = :fp"),
                    {"fp": fingerprint},
                ).fetchone()

                if existing:
                    updated_count += 1
                    continue

                tender_id = str(uuid.uuid4())
                conn.execute(
                    sqlalchemy.text("""
                        INSERT INTO tenders (
                            id, source_id, source_url, title, description_text,
                            agency, state, city, category, status,
                            publish_date, due_date, fingerprint, raw_ref
                        ) VALUES (
                            :id, :source_id, :source_url, :title, :description_text,
                            :agency, :state, :city, :category, :status,
                            :publish_date, :due_date, :fingerprint, :raw_ref
                        )
                    """),
                    {
                        "id": tender_id,
                        "source_id": source_id,
                        "source_url": tender.source_url,
                        "title": tender.title,
                        "description_text": tender.description_text,
                        "agency": tender.agency,
                        "state": tender.state,
                        "city": tender.city,
                        "category": tender.category.value,
                        "status": tender.status.value,
                        "publish_date": str(tender.publish_date) if tender.publish_date else None,
                        "due_date": str(tender.due_date) if tender.due_date else None,
                        "fingerprint": fingerprint,
                        "raw_ref": json.dumps(tender.raw_ref) if tender.raw_ref else None,
                    },
                )
                new_count += 1

            # Update scrape run
            conn.execute(
                sqlalchemy.text("""
                    UPDATE scrape_runs SET
                        status = 'completed',
                        completed_at = CURRENT_TIMESTAMP,
                        tenders_found = :found,
                        tenders_new = :new,
                        tenders_updated = :updated
                    WHERE id = :id
                """),
                {
                    "id": run_id,
                    "found": len(tenders),
                    "new": new_count,
                    "updated": updated_count,
                },
            )
            conn.commit()

        result = {
            "source": source_name,
            "found": len(tenders),
            "new": new_count,
            "updated": updated_count,
            "status": "completed",
        }
        print(f"    Found: {len(tenders)} | New: {new_count} | Updated: {updated_count}")
        return result

    except Exception as e:
        with engine.connect() as conn:
            conn.execute(
                sqlalchemy.text(
                    "UPDATE scrape_runs SET status = 'failed', error_message = :err WHERE id = :id"
                ),
                {"id": run_id, "err": str(e)[:500]},
            )
            conn.commit()
        print(f"    FAILED: {str(e)}")
        return {"source": source_name, "status": "failed", "error": str(e)}


async def run_all_scrapers(sources: list) -> list:
    """Run all scrapers sequentially."""
    print("\n[STEP 3] Running scrapers against live government portals...")

    scraper_map = {
        "port_authority": PortAuthorityScraper,
        "nyc_passport": NYCPassportScraper,
        "nys_ogs": NYSOGSScraper,
    }

    results = []
    for source in sources:
        scraper_class = scraper_map.get(source["scraper_class"])
        if scraper_class:
            result = await run_scraper(scraper_class, source["id"], source["name"])
            results.append(result)

    return results


def test_deduplication():
    """Test that running scrapers again doesn't create duplicates."""
    print("\n[STEP 4] Testing deduplication...")

    with engine.connect() as conn:
        count_before = conn.execute(
            sqlalchemy.text("SELECT COUNT(*) FROM tenders")
        ).scalar()

    print(f"  Tenders before re-scrape: {count_before}")
    return count_before


async def run_dedup_test(sources: list, count_before: int):
    """Run scrapers again and verify no duplicates."""
    scraper_map = {
        "port_authority": PortAuthorityScraper,
        "nyc_passport": NYCPassportScraper,
        "nys_ogs": NYSOGSScraper,
    }

    for source in sources:
        scraper_class = scraper_map.get(source["scraper_class"])
        if scraper_class:
            await run_scraper(scraper_class, source["id"], source["name"])

    with engine.connect() as conn:
        count_after = conn.execute(
            sqlalchemy.text("SELECT COUNT(*) FROM tenders")
        ).scalar()

    print(f"\n  Tenders after re-scrape: {count_after}")
    if count_after == count_before:
        print("  DEDUP TEST: PASSED (no duplicates created)")
        return True
    else:
        new = count_after - count_before
        print(f"  DEDUP TEST: FAILED ({new} duplicates created)")
        return False


def test_api_queries():
    """Test the API query layer against stored data."""
    print("\n[STEP 5] Testing API query layer...")

    with engine.connect() as conn:
        # Total count
        total = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM tenders")).scalar()
        print(f"  Total tenders: {total}")

        # By state
        ny_count = conn.execute(
            sqlalchemy.text("SELECT COUNT(*) FROM tenders WHERE state = 'NY'")
        ).scalar()
        print(f"  NY tenders: {ny_count}")

        # By category
        categories = conn.execute(
            sqlalchemy.text(
                "SELECT category, COUNT(*) as cnt FROM tenders GROUP BY category ORDER BY cnt DESC"
            )
        ).fetchall()
        print("  By category:")
        for cat, cnt in categories:
            print(f"    {cat}: {cnt}")

        # By source
        sources = conn.execute(
            sqlalchemy.text("""
                SELECT s.name, COUNT(t.id) as cnt
                FROM sources s LEFT JOIN tenders t ON s.id = t.source_id
                GROUP BY s.name ORDER BY cnt DESC
            """)
        ).fetchall()
        print("  By source:")
        for name, cnt in sources:
            print(f"    {name}: {cnt}")

        # Recent tenders (with due dates)
        upcoming = conn.execute(
            sqlalchemy.text("""
                SELECT title, due_date, agency
                FROM tenders
                WHERE due_date IS NOT NULL
                ORDER BY due_date ASC
                LIMIT 5
            """)
        ).fetchall()
        print("  Upcoming deadlines:")
        for title, due, agency in upcoming:
            print(f"    {due} | {title[:60]} ({agency})")

        # Scrape run history
        runs = conn.execute(
            sqlalchemy.text("""
                SELECT s.name, sr.status, sr.tenders_found, sr.tenders_new, sr.started_at
                FROM scrape_runs sr JOIN sources s ON sr.source_id = s.id
                ORDER BY sr.started_at DESC
            """)
        ).fetchall()
        print(f"  Scrape runs: {len(runs)}")
        for name, status, found, new, started in runs:
            print(f"    {name}: {status} (found={found}, new={new})")

    return total > 0


def cleanup():
    """Remove test database."""
    try:
        engine.dispose()
        if DB_PATH.exists():
            DB_PATH.unlink()
            print("\n  Cleaned up test database")
    except OSError:
        print(f"\n  Note: Could not delete {DB_PATH} (file locked). Delete manually.")


async def main():
    print("=" * 70)
    print("  TriState Bids - End-to-End Pipeline Test")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    try:
        # Step 1: Setup
        setup_database()

        # Step 2: Seed
        sources = seed_sources()

        # Step 3: Run scrapers
        results = await run_all_scrapers(sources)

        # Step 4: Dedup test
        count_before = test_deduplication()
        print("  Running scrapers again to test dedup...")
        dedup_ok = await run_dedup_test(sources, count_before)

        # Step 5: API queries
        api_ok = test_api_queries()

        # Summary
        print(f"\n{'=' * 70}")
        print("  PIPELINE TEST RESULTS")
        print(f"{'=' * 70}")

        total_found = sum(r.get("found", 0) for r in results if r.get("status") == "completed")
        total_new = sum(r.get("new", 0) for r in results if r.get("status") == "completed")
        failed = [r for r in results if r.get("status") == "failed"]

        print(f"  Scrapers run:      {len(results)}")
        print(f"  Scrapers passed:   {len(results) - len(failed)}")
        print(f"  Scrapers failed:   {len(failed)}")
        print(f"  Total tenders:     {total_found}")
        print(f"  New tenders:       {total_new}")
        print(f"  Deduplication:     {'PASS' if dedup_ok else 'FAIL'}")
        print(f"  API queries:       {'PASS' if api_ok else 'FAIL'}")

        for r in results:
            status = "PASS" if r.get("status") == "completed" else "FAIL"
            print(f"  {r['source']}: {status} ({r.get('found', 0)} found, {r.get('new', 0)} new)")

        all_pass = len(failed) == 0 and dedup_ok and api_ok
        print(f"\n  OVERALL: {'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
        print(f"{'=' * 70}")

    finally:
        cleanup()


if __name__ == "__main__":
    asyncio.run(main())
