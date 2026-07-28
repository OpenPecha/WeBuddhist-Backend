from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.events.event_response_models import EventsResponse
from pecha_api.events.event_service import (
    get_cms_events_service,
    get_cms_event_by_id_service,
)

MODULE = "pecha_api.events.event_service"


def _author(author_id=None):
    return MagicMock(id=author_id or uuid4())


def _event(group_id=None):
    now = datetime.now(timezone.utc)
    event = MagicMock()
    event.id = uuid4()
    event.plan_id = None
    event.accumulator_id = None
    event.mantra_id = None
    event.timer_id = None
    event.group_recitation_collection_id = None
    event.group_id = group_id or uuid4()
    event.start_date = now
    event.end_date = now
    event.image_url = None
    event.metadata_entries = []
    event.created_at = now
    event.created_by = "author@example.com"
    event.updated_at = None
    return event


# --------------------------- list: get_cms_events_service ---------------------------


@patch(f"{MODULE}.validate_cms_author_details")
@patch(f"{MODULE}.is_super_admin", return_value=True)
@patch(f"{MODULE}.is_reviewer", return_value=False)
@patch(f"{MODULE}.get_events_service")
def test_super_admin_sees_all_no_group_restriction(
    mock_get_events, _mock_reviewer, _mock_super, mock_validate
):
    mock_validate.return_value = _author()
    expected = EventsResponse(events=[], total=0, skip=0, limit=20)
    mock_get_events.return_value = expected

    result = get_cms_events_service(token="tok")

    assert result is expected
    # super admin => restrict_group_ids stays None (no scoping)
    assert mock_get_events.call_args.kwargs["restrict_group_ids"] is None


@patch(f"{MODULE}.validate_cms_author_details")
@patch(f"{MODULE}.is_super_admin", return_value=False)
@patch(f"{MODULE}.is_reviewer", return_value=True)
@patch(f"{MODULE}.get_events_service")
def test_reviewer_sees_all_no_group_restriction(
    mock_get_events, _mock_reviewer, _mock_super, mock_validate
):
    mock_validate.return_value = _author()
    expected = EventsResponse(events=[], total=0, skip=0, limit=20)
    mock_get_events.return_value = expected

    result = get_cms_events_service(token="tok")

    assert result is expected
    assert mock_get_events.call_args.kwargs["restrict_group_ids"] is None


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.get_author_group_ids")
@patch(f"{MODULE}.validate_cms_author_details")
@patch(f"{MODULE}.is_super_admin", return_value=False)
@patch(f"{MODULE}.is_reviewer", return_value=False)
@patch(f"{MODULE}.get_events_service")
def test_member_scoped_to_own_groups(
    mock_get_events,
    _mock_reviewer,
    _mock_super,
    mock_validate,
    mock_group_ids,
    mock_session,
):
    mock_session.return_value.__enter__.return_value = MagicMock()
    mock_validate.return_value = _author()
    group_ids = [uuid4(), uuid4()]
    mock_group_ids.return_value = group_ids
    expected = EventsResponse(events=[], total=0, skip=0, limit=20)
    mock_get_events.return_value = expected

    result = get_cms_events_service(token="tok", language="en")

    assert result is expected
    # normal member => scoped to exactly their group ids
    assert mock_get_events.call_args.kwargs["restrict_group_ids"] == group_ids
    assert mock_get_events.call_args.kwargs["language"] == "en"


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.get_author_group_ids")
@patch(f"{MODULE}.validate_cms_author_details")
@patch(f"{MODULE}.is_super_admin", return_value=False)
@patch(f"{MODULE}.is_reviewer", return_value=False)
@patch(f"{MODULE}.get_events_service")
def test_member_with_no_groups_gets_empty_response(
    mock_get_events,
    _mock_reviewer,
    _mock_super,
    mock_validate,
    mock_group_ids,
    mock_session,
):
    mock_session.return_value.__enter__.return_value = MagicMock()
    mock_validate.return_value = _author()
    mock_group_ids.return_value = []

    result = get_cms_events_service(token="tok", skip=5, limit=10)

    # short-circuits to empty without hitting the events query at all
    assert result == EventsResponse(events=[], total=0, skip=5, limit=10)
    mock_get_events.assert_not_called()


# --------------------------- detail: get_cms_event_by_id_service ---------------------------


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.require_can_read_group_content")
@patch(f"{MODULE}.get_event_by_id")
@patch(f"{MODULE}.validate_cms_author_details")
def test_detail_returns_event_when_permitted(
    mock_validate, mock_get_by_id, mock_require_read, mock_session
):
    mock_db = MagicMock()
    mock_session.return_value.__enter__.return_value = mock_db
    author = _author()
    mock_validate.return_value = author
    event = _event()
    mock_get_by_id.return_value = event

    result = get_cms_event_by_id_service(token="tok", event_id=event.id)

    assert result.id == event.id
    mock_require_read.assert_called_once_with(
        db=mock_db, group_id=event.group_id, author=author
    )


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.require_can_read_group_content")
@patch(f"{MODULE}.get_event_by_id")
@patch(f"{MODULE}.validate_cms_author_details")
def test_detail_404_when_missing(
    mock_validate, mock_get_by_id, mock_require_read, mock_session
):
    mock_session.return_value.__enter__.return_value = MagicMock()
    mock_validate.return_value = _author()
    mock_get_by_id.return_value = None
    event_id = uuid4()

    with pytest.raises(HTTPException) as exc:
        get_cms_event_by_id_service(token="tok", event_id=event_id)

    assert exc.value.status_code == 404
    # permission check never runs for a missing event
    mock_require_read.assert_not_called()


@patch(f"{MODULE}.SessionLocal")
@patch(f"{MODULE}.require_can_read_group_content")
@patch(f"{MODULE}.get_event_by_id")
@patch(f"{MODULE}.validate_cms_author_details")
def test_detail_403_when_not_group_member(
    mock_validate, mock_get_by_id, mock_require_read, mock_session
):
    mock_session.return_value.__enter__.return_value = MagicMock()
    mock_validate.return_value = _author()
    mock_get_by_id.return_value = _event()
    mock_require_read.side_effect = HTTPException(status_code=403, detail="NO_GROUP_MEMBERSHIP")

    with pytest.raises(HTTPException) as exc:
        get_cms_event_by_id_service(token="tok", event_id=uuid4())

    assert exc.value.status_code == 403
