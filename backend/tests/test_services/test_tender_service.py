"""Test tender service."""
import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from datetime import datetime

from app.services.tender_service import TenderService
from app.schemas.tender import TenderCreate
from app.models.tender import TenderCategory, TenderStatus


class TestTenderService:
    """Test TenderService."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()

    @pytest.fixture
    def service(self, mock_db):
        """Create tender service."""
        return TenderService(mock_db)

    @pytest.fixture
    def sample_tender_create(self):
        """Sample tender create data."""
        return TenderCreate(
            source_url="https://example.com/tender/123",
            title="Test Construction Project",
            description_text="Test description",
            agency="Test Agency",
            state="NY",
            city="New York",
            category=TenderCategory.CONSTRUCTION,
            status=TenderStatus.ACTIVE,
        )

    def test_generate_fingerprint(self, service, sample_tender_create):
        """Test fingerprint generation."""
        fp1 = service._generate_fingerprint(sample_tender_create)
        fp2 = service._generate_fingerprint(sample_tender_create)

        assert fp1 == fp2
        assert len(fp1) == 64  # SHA256 hex digest

    def test_create_or_update_new_tender(self, service, mock_db, sample_tender_create):
        """Test creating new tender."""
        source_id = uuid4()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.create_or_update_tender(sample_tender_create, source_id)

        assert result["action"] == "created"
        assert mock_db.add.called

    def test_create_or_update_existing_tender(self, service, mock_db, sample_tender_create):
        """Test updating existing tender."""
        source_id = uuid4()
        existing_tender = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = existing_tender

        result = service.create_or_update_tender(sample_tender_create, source_id)

        assert result["action"] == "updated"
        assert mock_db.add.called
