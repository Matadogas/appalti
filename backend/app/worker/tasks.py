"""Celery tasks."""
import asyncio
from typing import List
from uuid import UUID
import structlog

from app.worker.celery_app import celery_app
from app.database import SessionLocal
from app.services.scrape_service import ScrapeService

logger = structlog.get_logger()


@celery_app.task(name="app.worker.tasks.scrape_source")
def scrape_source(source_id: str) -> dict:
    """Scrape a specific source.

    Args:
        source_id: Source UUID as string

    Returns:
        Dict with scrape results
    """
    db = SessionLocal()
    try:
        service = ScrapeService(db)

        # Run async scrape in sync context
        result = asyncio.run(service.execute_scrape(UUID(source_id)))

        return result
    finally:
        db.close()


@celery_app.task(name="app.worker.tasks.run_all_scrapers")
def run_all_scrapers() -> dict:
    """Run all active scrapers.

    Returns:
        Dict with results for all scrapers
    """
    logger.info("Starting scheduled scrape for all sources")

    db = SessionLocal()
    try:
        service = ScrapeService(db)
        sources = service.get_active_sources()

        results = []
        for source in sources:
            logger.info(f"Queuing scrape for {source.name}")
            result = scrape_source.delay(str(source.id))
            results.append({
                "source": source.name,
                "task_id": result.id,
            })

        return {
            "status": "queued",
            "sources_queued": len(results),
            "tasks": results,
        }
    finally:
        db.close()
