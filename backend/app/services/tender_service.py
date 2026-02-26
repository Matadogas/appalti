"""Tender service for CRUD operations."""
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime
import hashlib
from sqlalchemy.orm import Session
import structlog

from app.models.tender import Tender
from app.schemas.tender import TenderCreate
from app.models.tender import TenderStatus

logger = structlog.get_logger()


class TenderService:
    """Service for managing tenders."""

    def __init__(self, db: Session):
        """Initialize service."""
        self.db = db

    def _generate_fingerprint(self, tender: TenderCreate) -> str:
        """Generate unique fingerprint for deduplication.

        Uses source_url + title + publish_date to create stable hash.
        """
        components = [
            tender.source_url,
            tender.title,
            str(tender.publish_date) if tender.publish_date else "",
        ]
        content = "|".join(components).encode("utf-8")
        return hashlib.sha256(content).hexdigest()

    def create_or_update_tender(
        self, tender_data: TenderCreate, source_id: UUID
    ) -> Dict[str, Any]:
        """Create new tender or update existing one based on fingerprint.

        Args:
            tender_data: Tender data
            source_id: Source UUID

        Returns:
            Dict with action ("created" or "updated") and tender object
        """
        fingerprint = self._generate_fingerprint(tender_data)

        # Check if tender exists
        existing = self.db.query(Tender).filter_by(fingerprint=fingerprint).first()

        if existing:
            # Update existing tender
            logger.info(f"Updating existing tender: {existing.id}")

            for field, value in tender_data.model_dump().items():
                if value is not None and field != "raw_ref":  # Don't overwrite with None
                    setattr(existing, field, value)

            existing.updated_at = datetime.utcnow()
            existing.scraped_at = datetime.utcnow()

            self.db.add(existing)
            self.db.commit()
            self.db.refresh(existing)

            return {"action": "updated", "tender": existing}
        else:
            # Create new tender
            logger.info(f"Creating new tender: {tender_data.title}")

            tender = Tender(
                source_id=source_id,
                fingerprint=fingerprint,
                **tender_data.model_dump(),
            )

            self.db.add(tender)
            self.db.commit()
            self.db.refresh(tender)

            return {"action": "created", "tender": tender}

    def get_tender(self, tender_id: UUID) -> Optional[Tender]:
        """Get tender by ID."""
        return self.db.query(Tender).filter(Tender.id == tender_id).first()

    def list_tenders(
        self,
        skip: int = 0,
        limit: int = 100,
        state: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[TenderStatus] = None,
    ) -> List[Tender]:
        """List tenders with filters."""
        query = self.db.query(Tender)

        if state:
            query = query.filter(Tender.state == state)
        if category:
            query = query.filter(Tender.category == category)
        if status:
            query = query.filter(Tender.status == status)

        query = query.order_by(Tender.scraped_at.desc())
        return query.offset(skip).limit(limit).all()

    def count_tenders(
        self,
        state: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[TenderStatus] = None,
    ) -> int:
        """Count tenders with filters."""
        query = self.db.query(Tender)

        if state:
            query = query.filter(Tender.state == state)
        if category:
            query = query.filter(Tender.category == category)
        if status:
            query = query.filter(Tender.status == status)

        return query.count()
