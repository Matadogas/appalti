"""Candidate website model for storing potential RFP sources."""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    Integer,
    Float,
    Text,
    Enum,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum

from app.database import Base


class WebsiteStatus(str, enum.Enum):
    """Website verification status."""

    DISCOVERED = "discovered"  # Found via search
    VERIFIED = "verified"  # Manually confirmed has RFPs
    APPROVED = "approved"  # Ready for scraping
    REJECTED = "rejected"  # Doesn't have RFPs
    DUPLICATE = "duplicate"  # Duplicate of existing source
    INACCESSIBLE = "inaccessible"  # Site down or blocked


class DiscoveryMethod(str, enum.Enum):
    """How the website was discovered."""

    GOOGLE_SEARCH = "google_search"
    MANUAL = "manual"
    REFERRAL = "referral"  # Linked from another site
    DIRECTORY = "directory"  # From government directory


class CandidateWebsite(Base):
    """Candidate website for potential scraping."""

    __tablename__ = "candidate_websites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Website info
    url = Column(String(500), nullable=False, unique=True, index=True)
    domain = Column(String(200), index=True)
    title = Column(String(500))  # Page title
    description = Column(Text)  # Meta description or snippet

    # Entity association
    entity_name = Column(String(200), index=True)
    entity_state = Column(String(2))  # NY, NJ, CT
    entity_type = Column(String(50))  # county, city, authority, etc.

    # Discovery metadata
    discovery_method = Column(Enum(DiscoveryMethod), default=DiscoveryMethod.GOOGLE_SEARCH)
    search_query = Column(String(500))  # Query that found this
    search_rank = Column(Integer)  # Position in search results (1-100)
    discovered_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Scoring (automated analysis)
    relevance_score = Column(Float, default=0.0)  # 0-100, how relevant it appears
    procurement_keywords_found = Column(JSONB, default=list)  # Keywords detected
    has_bid_list = Column(Boolean)  # Appears to have bid listing
    has_search_function = Column(Boolean)  # Has search capability
    requires_login = Column(Boolean)  # Requires authentication

    # Portal detection
    detected_portal_vendor = Column(String(50))  # opengov, bidexpress, etc.
    is_government_domain = Column(Boolean, default=False)  # .gov or .us domain

    # Verification
    status = Column(Enum(WebsiteStatus), default=WebsiteStatus.DISCOVERED, index=True)
    verified_at = Column(DateTime(timezone=True))
    verified_by = Column(String(100))  # User who verified
    verification_notes = Column(Text)

    # Manual review
    priority = Column(Integer, default=5)  # 1-10 for review priority
    notes = Column(Text)
    screenshot_path = Column(String(500))  # Path to screenshot if taken

    # Technical details
    response_time_ms = Column(Float)  # Page load time
    http_status = Column(Integer)  # HTTP status code
    ssl_valid = Column(Boolean)
    robots_txt_allows_crawl = Column(Boolean)

    # Metadata
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_checked_at = Column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<CandidateWebsite {self.url} ({self.status.value})>"
