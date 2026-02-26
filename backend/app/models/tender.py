"""Tender model."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Float,
    Enum,
    Integer,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class TenderStatus(str, enum.Enum):
    """Tender status enum."""

    ACTIVE = "active"
    CLOSED = "closed"
    AWARDED = "awarded"
    CANCELLED = "cancelled"


class TenderCategory(str, enum.Enum):
    """Tender category enum."""

    CONSTRUCTION = "construction"
    ENGINEERING = "engineering"
    FACILITIES = "facilities"
    OTHER = "other"


class Tender(Base):
    """Tender model representing a public works opportunity."""

    __tablename__ = "tenders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)

    # Core fields
    source_url = Column(String(500), nullable=False)
    title = Column(String(500), nullable=False)
    description_text = Column(Text)

    # Location
    agency = Column(String(200))
    state = Column(String(2), nullable=False)  # NY or NJ
    city = Column(String(100))
    county = Column(String(100))

    # Classification
    category = Column(Enum(TenderCategory), default=TenderCategory.OTHER)
    status = Column(Enum(TenderStatus), default=TenderStatus.ACTIVE)

    # Dates & Budget
    publish_date = Column(DateTime(timezone=True))
    due_date = Column(DateTime(timezone=True))
    budget_amount = Column(Float)
    currency = Column(String(3), default="USD")

    # Documents & Contact
    documents = Column(JSONB, default=list)  # [{"name": str, "url": str, "size": int}]
    contact = Column(JSONB)  # {"name": str, "email": str, "phone": str}

    # Deduplication
    fingerprint = Column(String(64), unique=True, nullable=False, index=True)

    # AI Enrichment
    ai_summary = Column(Text)
    ai_trade_tags = Column(JSONB, default=list)  # ["electrical", "plumbing", ...]
    ai_requirements = Column(JSONB)  # {"bid_bond": bool, "pre_bid_meeting": bool, ...}
    confidence = Column(Float)  # AI confidence score

    # Metadata
    scraped_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    raw_ref = Column(JSONB)  # Reference to raw scrape data

    # Relationships
    source = relationship("Source", back_populates="tenders")

    def __repr__(self) -> str:
        return f"<Tender {self.title[:50]}>"
