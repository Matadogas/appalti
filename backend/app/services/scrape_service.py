"""Scrape service for managing scrape runs."""
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
import structlog

from app.models.source import Source
from app.models.scrape_run import ScrapeRun, ScrapeRunStatus
from app.scrapers.registry import registry
from app.services.tender_service import TenderService

logger = structlog.get_logger()


class ScrapeService:
    """Service for managing scrape operations."""

    def __init__(self, db: Session):
        """Initialize service."""
        self.db = db
        self.tender_service = TenderService(db)

    async def execute_scrape(self, source_id: UUID) -> Dict[str, Any]:
        """Execute scrape for a specific source.

        Args:
            source_id: Source UUID

        Returns:
            Dict with scrape results
        """
        # Get source
        source = self.db.query(Source).filter(Source.id == source_id).first()
        if not source:
            raise ValueError(f"Source {source_id} not found")

        if not source.active:
            logger.info(f"Source {source.name} is inactive, skipping")
            return {"status": "skipped", "reason": "inactive"}

        # Create scrape run
        scrape_run = ScrapeRun(
            source_id=source_id,
            status=ScrapeRunStatus.RUNNING,
            started_at=datetime.utcnow(),
        )
        self.db.add(scrape_run)
        self.db.commit()

        try:
            # Get scraper
            scraper = registry.create_scraper(source.scraper_class, source.config)

            # Execute scrape
            logger.info(f"Starting scrape for {source.name}")
            tenders = await scraper.scrape()

            # Process tenders
            new_count = 0
            updated_count = 0

            for tender_data in tenders:
                result = self.tender_service.create_or_update_tender(
                    tender_data, source_id
                )
                if result["action"] == "created":
                    new_count += 1
                else:
                    updated_count += 1

            # Update scrape run
            scrape_run.status = ScrapeRunStatus.SUCCESS
            scrape_run.completed_at = datetime.utcnow()
            scrape_run.tenders_found = len(tenders)
            scrape_run.tenders_new = new_count
            scrape_run.tenders_updated = updated_count

            self.db.commit()

            logger.info(
                f"Scrape complete for {source.name}: "
                f"{new_count} new, {updated_count} updated"
            )

            return {
                "status": "success",
                "source": source.name,
                "tenders_found": len(tenders),
                "tenders_new": new_count,
                "tenders_updated": updated_count,
            }

        except Exception as e:
            logger.error(f"Scrape failed for {source.name}: {str(e)}")

            scrape_run.status = ScrapeRunStatus.FAILED
            scrape_run.completed_at = datetime.utcnow()
            scrape_run.error_message = str(e)[:1000]
            scrape_run.errors_count = 1

            self.db.commit()

            return {
                "status": "failed",
                "source": source.name,
                "error": str(e),
            }

    def get_active_sources(self) -> List[Source]:
        """Get all active sources."""
        return self.db.query(Source).filter(Source.active == True).all()

    def get_recent_scrape_runs(self, limit: int = 50) -> List[ScrapeRun]:
        """Get recent scrape runs."""
        return (
            self.db.query(ScrapeRun)
            .order_by(ScrapeRun.created_at.desc())
            .limit(limit)
            .all()
        )
