from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.events.event_response_models import EventDTO
from pecha_api.events.event_service import (
    get_featured_events_service,
    update_event_featured_service,
)

MODULE = "pecha_api.events.event_service"


def _author(author_id=None):
    return MagicMock(id=author_id or uuid4())


def _event(event_id=None, group_id=None, featured=False):
    now = datetime.now(timezone.utc)
    event = MagicMock()
    event.id = event_id or uuid4()
    event.plan_id = None
    event.accumulator_id = None
    event.mantra_id = None
    event.timer_id = None
    event.group_recitation_collection_id = None
    event.group_id = group_id or uuid4()
    event.start_date = now
    event.end_date = now
    event.image_url = None
    event.featured = featured
    event.metadata_entries = []
    event.links = []
    event.created_at = now
    event.created_by = "author@example.com"
    event.updated_at = None
    return event


# --------------------------- get_featured_events_service ---------------------------


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.get_event_participant_counts", return_value={})
@patch(f"{MODULE}.get_featured_events")
def test_get_featured_events_returns_list(mock_get_featured, _mock_counts, mock_session):
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    
    event1 = _event(featured=True)
    event2 = _event(featured=True)
    mock_get_featured.return_value = [event1, event2]

    result = get_featured_events_service(language="en", limit=10)

    assert len(result) == 2
    assert all(isinstance(e, EventDTO) for e in result)
    assert all(e.is_joined is None for e in result)
    mock_get_featured.assert_called_once_with(mock_db, limit=10)


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.get_event_participant_counts", return_value={})
@patch(f"{MODULE}.get_featured_events")
def test_get_featured_events_empty_list(mock_get_featured, _mock_counts, mock_session):
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    mock_get_featured.return_value = []

    result = get_featured_events_service(language="en", limit=10)

    assert result == []
    mock_get_featured.assert_called_once_with(mock_db, limit=10)


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.get_event_participant_counts", return_value={})
@patch(f"{MODULE}.get_featured_events")
def test_get_featured_events_with_language(mock_get_featured, _mock_counts, mock_session):
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    
    event = _event(featured=True)
    mock_get_featured.return_value = [event]

    result = get_featured_events_service(language="bo", limit=5)

    assert len(result) == 1
    mock_get_featured.assert_called_once_with(mock_db, limit=5)


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.get_event_participant_counts", return_value={})
@patch(f"{MODULE}.get_featured_events")
def test_get_featured_events_respects_limit(mock_get_featured, _mock_counts, mock_session):
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    
    events = [_event(featured=True) for _ in range(3)]
    mock_get_featured.return_value = events

    result = get_featured_events_service(limit=3)

    assert len(result) == 3
    mock_get_featured.assert_called_once_with(mock_db, limit=3)


# --------------------------- update_event_featured_service ---------------------------


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.validate_cms_author_details")
@patch(f"{MODULE}.get_event_by_id")
@patch(f"{MODULE}.require_can_change_status")
@patch(f"{MODULE}.update_event")
def test_update_featured_toggles_false_to_true(
    mock_update, mock_require, mock_get_by_id, mock_validate, mock_session
):
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    
    author = _author()
    mock_validate.return_value = author
    
    event = _event(featured=False)
    mock_get_by_id.return_value = event

    update_event_featured_service(token="tok", event_id=event.id)

    assert event.featured is True
    assert event.updated_at is not None
    mock_require.assert_called_once_with(db=mock_db, group_id=event.group_id, author=author)
    mock_update.assert_called_once_with(mock_db, event)


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.validate_cms_author_details")
@patch(f"{MODULE}.get_event_by_id")
@patch(f"{MODULE}.require_can_change_status")
@patch(f"{MODULE}.update_event")
def test_update_featured_toggles_true_to_false(
    mock_update, mock_require, mock_get_by_id, mock_validate, mock_session
):
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    
    author = _author()
    mock_validate.return_value = author
    
    event = _event(featured=True)
    mock_get_by_id.return_value = event

    update_event_featured_service(token="tok", event_id=event.id)

    assert event.featured is False
    assert event.updated_at is not None
    mock_require.assert_called_once_with(db=mock_db, group_id=event.group_id, author=author)
    mock_update.assert_called_once_with(mock_db, event)


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.validate_cms_author_details")
@patch(f"{MODULE}.get_event_by_id")
def test_update_featured_404_when_not_found(mock_get_by_id, mock_validate, mock_session):
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    
    mock_validate.return_value = _author()
    mock_get_by_id.return_value = None
    
    event_id = uuid4()

    with pytest.raises(HTTPException) as exc:
        update_event_featured_service(token="tok", event_id=event_id)

    assert exc.value.status_code == 404
    assert f"Event with id '{event_id}' not found" in exc.value.detail


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.validate_cms_author_details")
@patch(f"{MODULE}.get_event_by_id")
@patch(f"{MODULE}.require_can_change_status")
def test_update_featured_403_no_permission(
    mock_require, mock_get_by_id, mock_validate, mock_session
):
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    
    author = _author()
    mock_validate.return_value = author
    
    event = _event(featured=False)
    mock_get_by_id.return_value = event
    
    mock_require.side_effect = HTTPException(status_code=403, detail="STATUS_CHANGE_FORBIDDEN")

    with pytest.raises(HTTPException) as exc:
        update_event_featured_service(token="tok", event_id=event.id)

    assert exc.value.status_code == 403


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.validate_cms_author_details")
@patch(f"{MODULE}.get_event_by_id")
@patch(f"{MODULE}.require_can_change_status")
@patch(f"{MODULE}.update_event")
def test_update_featured_updates_timestamp(
    mock_update, mock_require, mock_get_by_id, mock_validate, mock_session
):
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    
    author = _author()
    mock_validate.return_value = author
    
    event = _event(featured=False)
    event.updated_at = None
    mock_get_by_id.return_value = event

    update_event_featured_service(token="tok", event_id=event.id)

    assert event.updated_at is not None
    assert event.updated_at.tzinfo is not None
    mock_update.assert_called_once_with(mock_db, event)
