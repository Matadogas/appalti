"""Tender schemas."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, HttpUrl, Field

from app.models.tender import TenderCategory, TenderStatus


class DocumentSchema(BaseModel):
    """Document attachment schema."""

    name: str
    url: str
    size: Optional[int] = None


class ContactSchema(BaseModel):
    """Contact information schema."""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class TenderCreate(BaseModel):
    """Schema for creating a tender."""

    source_url: str = Field(..., max_length=500)
    title: str = Field(..., max_length=500)
    description_text: Optional[str] = None

    agency: Optional[str] = Field(None, max_length=200)
    state: str = Field(..., pattern="^(NY|NJ)$")
    city: Optional[str] = Field(None, max_length=100)
    county: Optional[str] = Field(None, max_length=100)

    category: TenderCategory = TenderCategory.OTHER
    status: TenderStatus = TenderStatus.ACTIVE

    publish_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    budget_amount: Optional[float] = None
    currency: str = "USD"

    documents: List[DocumentSchema] = Field(default_factory=list)
    contact: Optional[ContactSchema] = None

    raw_ref: Optional[Dict[str, Any]] = None


class TenderResponse(BaseModel):
    """Schema for tender response."""

    id: UUID
    source_url: str
    title: str
    description_text: Optional[str]

    agency: Optional[str]
    state: str
    city: Optional[str]
    county: Optional[str]

    category: TenderCategory
    status: TenderStatus

    publish_date: Optional[datetime]
    due_date: Optional[datetime]
    budget_amount: Optional[float]
    currency: str

    documents: List[DocumentSchema]
    contact: Optional[ContactSchema]

    ai_summary: Optional[str]
    ai_trade_tags: List[str]
    ai_requirements: Optional[Dict[str, Any]]
    confidence: Optional[float]

    scraped_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
