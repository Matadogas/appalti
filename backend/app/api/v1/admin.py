"""Admin API endpoints."""
from uuid import UUID
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.worker.tasks import scrape_source
from app.services.scrape_service import ScrapeService

router = APIRouter()


@router.post("/admin/scrape/{source_id}")
async def trigger_scrape(
    source_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger scrape for a specific source.

    Args:
        source_id: Source UUID
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Status message
    """
    # Queue scrape task
    task = scrape_source.delay(str(source_id))

    return {
        "status": "queued",
        "task_id": task.id,
        "message": f"Scrape queued for source {source_id}",
    }


@router.get("/admin/scrape-runs")
async def list_scrape_runs(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List recent scrape runs.

    Args:
        limit: Maximum number of runs to return
        db: Database session

    Returns:
        List of scrape runs
    """
    service = ScrapeService(db)
    runs = service.get_recent_scrape_runs(limit=limit)

    return {
        "runs": [
            {
                "id": str(run.id),
                "source_id": str(run.source_id),
                "status": run.status.value,
                "tenders_found": run.tenders_found,
                "tenders_new": run.tenders_new,
                "tenders_updated": run.tenders_updated,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "error_message": run.error_message,
            }
            for run in runs
        ]
    }
