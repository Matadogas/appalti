"""Tenders API endpoints."""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.tender import TenderResponse
from app.services.tender_service import TenderService
from app.models.tender import TenderStatus, TenderCategory

router = APIRouter()


@router.get("/tenders", response_model=List[TenderResponse])
async def list_tenders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    state: Optional[str] = Query(None, pattern="^(NY|NJ)$"),
    category: Optional[TenderCategory] = None,
    status: Optional[TenderStatus] = None,
    db: Session = Depends(get_db),
):
    """List tenders with optional filters.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        state: Filter by state (NY or NJ)
        category: Filter by category
        status: Filter by status
        db: Database session

    Returns:
        List of tenders
    """
    service = TenderService(db)
    tenders = service.list_tenders(
        skip=skip,
        limit=limit,
        state=state,
        category=category,
        status=status,
    )
    return tenders


@router.get("/tenders/count")
async def count_tenders(
    state: Optional[str] = Query(None, pattern="^(NY|NJ)$"),
    category: Optional[TenderCategory] = None,
    status: Optional[TenderStatus] = None,
    db: Session = Depends(get_db),
):
    """Count tenders with optional filters.

    Args:
        state: Filter by state (NY or NJ)
        category: Filter by category
        status: Filter by status
        db: Database session

    Returns:
        Count of matching tenders
    """
    service = TenderService(db)
    count = service.count_tenders(
        state=state,
        category=category,
        status=status,
    )
    return {"count": count}


@router.get("/tenders/{tender_id}", response_model=TenderResponse)
async def get_tender(
    tender_id: UUID,
    db: Session = Depends(get_db),
):
    """Get tender by ID.

    Args:
        tender_id: Tender UUID
        db: Database session

    Returns:
        Tender details

    Raises:
        HTTPException: If tender not found
    """
    service = TenderService(db)
    tender = service.get_tender(tender_id)

    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")

    return tender
