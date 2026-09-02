from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from pecha_api.events.event_response_models import (
    CreateEventRequest,
    UpdateEventRequest,
    EventDTO,
)


def test_create_event_request_accepts_valid_event_formats():
    """Test that CreateEventRequest accepts valid event_format values."""
    now = datetime.now(timezone.utc)
    
    for format_value in ["online", "offline", "hybrid"]:
        request = CreateEventRequest(
            group_id=uuid4(),
            start_date=now,
            end_date=now,
            metadata=[{"name": "Event", "language": "EN"}],
            event_format=format_value,
        )
        assert request.event_format == format_value


def test_create_event_request_rejects_invalid_event_format():
    """Test that CreateEventRequest rejects invalid event_format values."""
    now = datetime.now(timezone.utc)
    
    with pytest.raises(ValidationError) as exc_info:
        CreateEventRequest(
            group_id=uuid4(),
            start_date=now,
            end_date=now,
            metadata=[{"name": "Event", "language": "EN"}],
            event_format="invalid_format",
        )
    
    assert "event_format" in str(exc_info.value)


def test_create_event_request_event_format_is_optional():
    """Test that event_format is optional in CreateEventRequest."""
    now = datetime.now(timezone.utc)
    
    request = CreateEventRequest(
        group_id=uuid4(),
        start_date=now,
        end_date=now,
        metadata=[{"name": "Event", "language": "EN"}],
    )
    assert request.event_format is None


def test_update_event_request_accepts_valid_event_formats():
    """Test that UpdateEventRequest accepts valid event_format values."""
    for format_value in ["online", "offline", "hybrid"]:
        request = UpdateEventRequest(event_format=format_value)
        assert request.event_format == format_value


def test_update_event_request_rejects_invalid_event_format():
    """Test that UpdateEventRequest rejects invalid event_format values."""
    with pytest.raises(ValidationError) as exc_info:
        UpdateEventRequest(event_format="in-person")
    
    assert "event_format" in str(exc_info.value)


def test_update_event_request_event_format_is_optional():
    """Test that event_format is optional in UpdateEventRequest."""
    request = UpdateEventRequest()
    assert request.event_format is None


def test_event_dto_includes_event_format():
    """Test that EventDTO includes event_format field."""
    now = datetime.now(timezone.utc)
    
    event = EventDTO(
        id=uuid4(),
        group_id=uuid4(),
        start_date=now,
        end_date=now,
        is_one_day=True,
        featured=False,
        event_format="online",
        metadata=[],
        created_at=now,
        created_by="author@example.com",
    )
    
    assert event.event_format == "online"


def test_event_dto_event_format_can_be_none():
    """Test that EventDTO event_format can be None."""
    now = datetime.now(timezone.utc)
    
    event = EventDTO(
        id=uuid4(),
        group_id=uuid4(),
        start_date=now,
        end_date=now,
        is_one_day=True,
        featured=False,
        event_format=None,
        metadata=[],
        created_at=now,
        created_by="author@example.com",
    )
    
    assert event.event_format is None


def test_create_event_service_sets_event_format():
    """Test that create_event_service properly sets event_format."""
    now = datetime.now(timezone.utc)
    group_id = uuid4()
    
    request = CreateEventRequest(
        group_id=group_id,
        start_date=now,
        end_date=now,
        metadata=[{"name": "Test Event", "language": "EN"}],
        event_format="hybrid",
    )
    
    mock_event = MagicMock()
    mock_event.id = uuid4()
    mock_event.group_id = group_id
    mock_event.start_date = now
    mock_event.end_date = now
    mock_event.event_format = "hybrid"
    mock_event.featured = False
    mock_event.is_recurring = False
    mock_event.metadata_entries = []
    mock_event.links = []
    mock_event.created_at = now
    mock_event.created_by = "test@example.com"
    mock_event.updated_at = None
    mock_event.image_url = None
    mock_event.plan_id = None
    mock_event.accumulator_id = None
    mock_event.mantra_id = None
    mock_event.timer_id = None
    mock_event.group_recitation_collection_id = None
    mock_event.location_id = None
    mock_event.location = None
    
    with patch("pecha_api.events.event_service.validate_cms_author_details") as mock_auth, \
         patch("pecha_api.events.event_service.SessionLocal") as mock_session, \
         patch("pecha_api.events.event_service.save_event", return_value=mock_event) as mock_save, \
         patch("pecha_api.events.event_service.require_can_create_content"), \
         patch("pecha_api.events.event_service.enqueue_event_notification"):
        
        mock_auth.return_value = MagicMock(email="test@example.com")
        mock_session.return_value.__enter__.return_value = MagicMock()
        
        from pecha_api.events.event_service import create_event_service
        result = create_event_service(token="test-token", request=request)
        
        # Verify Event object was created with event_format
        call_args = mock_save.call_args
        event_arg = call_args[0][1]  # Second positional arg is the Event object
        assert event_arg.event_format == "hybrid"
        
        # Verify the returned DTO includes event_format
        assert result.event_format == "hybrid"


def test_update_event_service_updates_event_format():
    """Test that update_event_service properly updates event_format."""
    now = datetime.now(timezone.utc)
    event_id = uuid4()
    
    request = UpdateEventRequest(event_format="offline")
    
    mock_event = MagicMock()
    mock_event.id = event_id
    mock_event.group_id = uuid4()
    mock_event.start_date = now
    mock_event.end_date = now
    mock_event.event_format = "online"  # Original value
    mock_event.featured = False
    mock_event.is_recurring = False
    mock_event.metadata_entries = []
    mock_event.links = []
    mock_event.created_at = now
    mock_event.created_by = "test@example.com"
    mock_event.updated_at = None
    mock_event.image_url = None
    mock_event.location = None
    mock_event.plan_id = None
    mock_event.accumulator_id = None
    mock_event.mantra_id = None
    mock_event.timer_id = None
    mock_event.group_recitation_collection_id = None
    mock_event.location_id = None
    
    with patch("pecha_api.events.event_service.validate_cms_author_details") as mock_auth, \
         patch("pecha_api.events.event_service.SessionLocal") as mock_session, \
         patch("pecha_api.events.event_service.get_event_by_id", return_value=mock_event), \
         patch("pecha_api.events.event_service.update_event", return_value=mock_event) as mock_update, \
         patch("pecha_api.events.event_service._require_can_edit_event"):
        
        mock_auth.return_value = MagicMock(email="test@example.com")
        mock_session.return_value.__enter__.return_value = MagicMock()
        
        from pecha_api.events.event_service import update_event_service
        result = update_event_service(token="test-token", event_id=event_id, request=request)
        
        # Verify event_format was updated
        assert mock_event.event_format == "offline"
        
        # Verify the returned DTO includes updated event_format
        assert result.event_format == "offline"
