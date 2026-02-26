"""Source model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class Source(Base):
    """Source model representing a procurement portal."""

    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    state = Column(String(2), nullable=False)  # NY or NJ
    base_url = Column(String(500), nullable=False)
    scraper_class = Column(String(100), nullable=False)  # e.g., "NYCPassportScraper"

    active = Column(Boolean, default=True)
    config = Column(JSONB, default=dict)  # Scraper-specific config

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenders = relationship("Tender", back_populates="source")
    scrape_runs = relationship("ScrapeRun", back_populates="source")

    def __repr__(self) -> str:
        return f"<Source {self.name}>"
