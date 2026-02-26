"""Scrape run model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ScrapeRunStatus(str, enum.Enum):
    """Scrape run status enum."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ScrapeRun(Base):
    """Scrape run model tracking scraper execution."""

    __tablename__ = "scrape_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)

    status = Column(Enum(ScrapeRunStatus), default=ScrapeRunStatus.PENDING)

    # Counts
    tenders_found = Column(Integer, default=0)
    tenders_new = Column(Integer, default=0)
    tenders_updated = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)

    # Execution details
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    error_message = Column(String(1000))
    error_details = Column(JSONB)  # Stack trace, context, etc.

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    source = relationship("Source", back_populates="scrape_runs")

    def __repr__(self) -> str:
        return f"<ScrapeRun {self.source_id} {self.status}>"
