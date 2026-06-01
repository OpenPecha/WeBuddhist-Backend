from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.notification.notification_service import (
    _notification_to_dto,
    create_notification_record,
    list_notifications,
    mark_notification_as_read,
)


def _make_notification_row(**kwargs):
    row = MagicMock()
    row.id = kwargs.get("id", uuid4())
    row.title = kwargs.get("title", "Title")
    row.description = kwargs.get("description", "Desc")
    row.category = kwargs.get("category", "group_invite")
    row.reference_type = kwargs.get("reference_type", "author_group_invite")
    row.reference_id = kwargs.get("reference_id", uuid4())
    row.is_read = kwargs.get("is_read", False)
    row.read_at = kwargs.get("read_at", None)
    row.created_at = kwargs.get("created_at", datetime.now(timezone.utc))
    row.action_1_label = kwargs.get("action_1_label", "Accept")
    row.action_1_method = kwargs.get("action_1_method", "POST")
    row.action_1_path = kwargs.get("action_1_path", "/accept")
    row.action_2_label = kwargs.get("action_2_label", "Reject")
    row.action_2_method = kwargs.get("action_2_method", "POST")
    row.action_2_path = kwargs.get("action_2_path", "/reject")
    return row


def test_notification_to_dto_includes_both_actions():
    dto = _notification_to_dto(_make_notification_row())
    assert len(dto.actions) == 2
    assert dto.actions[0].label == "Accept"


def test_notification_to_dto_without_actions():
    row = _make_notification_row(
        action_1_label=None,
        action_1_method=None,
        action_1_path=None,
        action_2_label=None,
        action_2_method=None,
        action_2_path=None,
    )
    dto = _notification_to_dto(row)
    assert dto.actions == []


def test_notification_to_dto_single_action():
    row = _make_notification_row(
        action_2_label=None,
        action_2_method=None,
        action_2_path=None,
    )
    dto = _notification_to_dto(row)
    assert len(dto.actions) == 1


def test_create_notification_record():
    recipient_id = uuid4()
    created = MagicMock()
    with patch("pecha_api.notification.notification_service.SessionLocal") as mock_session, patch(
        "pecha_api.notification.notification_service.create_notification",
        return_value=created,
    ) as mock_create:
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_session.return_value.__exit__.return_value = False
        result = create_notification_record(
            recipient_author_id=recipient_id,
            title="Invitation",
            description="You were invited",
            category="group_invite",
            reference_type="author_group_invite",
            reference_id=uuid4(),
            action_1_label="Accept",
            action_1_method="POST",
            action_1_path="/accept",
        )
    assert result is created
    mock_create.assert_called_once()


def test_list_notifications():
    author = MagicMock()
    author.id = uuid4()
    row = _make_notification_row()
    with patch(
        "pecha_api.notification.notification_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.notification.notification_service.SessionLocal") as mock_session, patch(
        "pecha_api.notification.notification_service.get_notifications_paginated",
        return_value=([row], 1),
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_session.return_value.__exit__.return_value = False
        result = list_notifications(token="t", skip=0, limit=10, unread_only=True)
    assert result.total == 1
    assert result.skip == 0
    assert result.limit == 10
    assert len(result.notifications) == 1


def test_mark_notification_as_read_success():
    author = MagicMock()
    author.id = uuid4()
    row = _make_notification_row(is_read=False)
    updated = _make_notification_row(is_read=True)
    with patch(
        "pecha_api.notification.notification_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.notification.notification_service.SessionLocal") as mock_session, patch(
        "pecha_api.notification.notification_service.get_notification_by_id",
        return_value=row,
    ), patch(
        "pecha_api.notification.notification_service.mark_notification_read",
        return_value=updated,
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_session.return_value.__exit__.return_value = False
        dto = mark_notification_as_read(token="t", notification_id=row.id)
    assert dto.is_read is True


def test_mark_notification_as_read_not_found():
    author = MagicMock()
    author.id = uuid4()
    with patch(
        "pecha_api.notification.notification_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.notification.notification_service.SessionLocal") as mock_session, patch(
        "pecha_api.notification.notification_service.get_notification_by_id",
        return_value=None,
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_session.return_value.__exit__.return_value = False
        with pytest.raises(HTTPException) as exc:
            mark_notification_as_read(token="t", notification_id=uuid4())
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc.value.detail == "Notification not found"
