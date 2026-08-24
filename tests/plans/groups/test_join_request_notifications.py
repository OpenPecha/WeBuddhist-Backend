from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.plans.groups.groups_enums import AuthorGroupJoinRequestStatus
from pecha_api.plans.groups.join_request_dispatch_service import (
    enqueue_join_request_created,
    enqueue_join_request_decided,
)
from pecha_api.plans.groups.join_request_notification_service import (
    get_join_request_notification_targets,
)
from pecha_api.plans.groups.join_request_sqs_client import (
    JOIN_REQUEST_CREATED_EVENT,
    JOIN_REQUEST_DECIDED_EVENT,
    build_join_request_event_body,
)

_SVC = "pecha_api.plans.groups.join_request_dispatch_service"
_NOTIF = "pecha_api.plans.groups.join_request_notification_service"


def _metadata(title="Chanting Circle", language="EN"):
    entry = MagicMock()
    entry.language = language
    entry.title = title
    return entry


def _join_request(status_value=AuthorGroupJoinRequestStatus.PENDING):
    jr = MagicMock()
    jr.id = uuid4()
    jr.group_id = uuid4()
    jr.user_id = uuid4()
    jr.status = status_value.value
    jr.group = MagicMock()
    jr.group.metadata_entries = [_metadata()]
    return jr


def _device():
    device = MagicMock()
    device.id = uuid4()
    device.token = "fcm-token-abc"
    device.platform = "ANDROID"
    return device


def test_event_body_shape_matches_contract():
    join_request_id = str(uuid4())
    body = build_join_request_event_body(
        join_request_id=join_request_id, event_type=JOIN_REQUEST_CREATED_EVENT
    )
    assert body == {
        "event_type": "JOIN_REQUEST_CREATED",
        "version": 1,
        "join_request_id": join_request_id,
    }


def test_enqueue_skipped_when_queue_not_configured():
    with patch(f"{_SVC}.is_join_request_notification_sqs_configured", return_value=False), patch(
        f"{_SVC}.send_join_request_notification_message"
    ) as mock_send:
        assert enqueue_join_request_created(uuid4()) is None
    mock_send.assert_not_called()


def test_enqueue_records_sqs_message_id():
    join_request_id = uuid4()
    with patch(f"{_SVC}.is_join_request_notification_sqs_configured", return_value=True), patch(
        f"{_SVC}.send_join_request_notification_message", return_value="sqs-123",
    ), patch(f"{_SVC}.SessionLocal") as mock_session, patch(
        f"{_SVC}.mark_join_request_notification_dispatched"
    ) as mock_mark:
        mock_session.return_value.__enter__.return_value = MagicMock()
        result = enqueue_join_request_created(join_request_id)

    assert result == "sqs-123"
    assert mock_mark.call_args.kwargs["decision"] is False


def test_decision_enqueue_marks_decision_column():
    with patch(f"{_SVC}.is_join_request_notification_sqs_configured", return_value=True), patch(
        f"{_SVC}.send_join_request_notification_message", return_value="sqs-456",
    ), patch(f"{_SVC}.SessionLocal") as mock_session, patch(
        f"{_SVC}.mark_join_request_notification_dispatched"
    ) as mock_mark:
        mock_session.return_value.__enter__.return_value = MagicMock()
        enqueue_join_request_decided(uuid4())

    assert mock_mark.call_args.kwargs["decision"] is True


def test_enqueue_swallows_sqs_failure():
    """A queue outage must not surface to the caller."""
    with patch(f"{_SVC}.is_join_request_notification_sqs_configured", return_value=True), patch(
        f"{_SVC}.send_join_request_notification_message",
        side_effect=RuntimeError("SQS unreachable"),
    ):
        assert enqueue_join_request_created(uuid4()) is None


def test_targets_404_for_unknown_request():
    with patch(f"{_NOTIF}.SessionLocal") as mock_session:
        db = MagicMock()
        mock_session.return_value.__enter__.return_value = db
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc:
            get_join_request_notification_targets(
                join_request_id=uuid4(), skip=0, limit=100
            )
    assert exc.value.status_code == 404


def test_pending_request_targets_moderators():
    jr = _join_request(AuthorGroupJoinRequestStatus.PENDING)
    moderator_id = uuid4()
    device = _device()

    with patch(f"{_NOTIF}.SessionLocal") as mock_session, patch(
        f"{_NOTIF}._moderator_user_ids", return_value=[moderator_id],
    ), patch(
        f"{_NOTIF}.get_active_push_devices_by_user_ids", return_value={moderator_id: [device]},
    ):
        db = MagicMock()
        mock_session.return_value.__enter__.return_value = db
        requester = MagicMock(firstname="Tenzin", lastname="Tib")
        db.query.return_value.filter.return_value.first.side_effect = [jr, requester]
        result = get_join_request_notification_targets(
            join_request_id=jr.id, skip=0, limit=100
        )

    assert result.event_type == JOIN_REQUEST_CREATED_EVENT
    assert [r.user_id for r in result.recipients] == [moderator_id]
    assert "Chanting Circle" in result.title
    assert "Tenzin Tib" in result.body
    assert result.recipients[0].push_devices[0].token == "fcm-token-abc"


def test_approved_request_targets_requester():
    jr = _join_request(AuthorGroupJoinRequestStatus.APPROVED)
    device = _device()

    with patch(f"{_NOTIF}.SessionLocal") as mock_session, patch(
        f"{_NOTIF}.get_active_push_devices_by_user_ids", return_value={jr.user_id: [device]},
    ):
        db = MagicMock()
        mock_session.return_value.__enter__.return_value = db
        requester = MagicMock(firstname="Tenzin", lastname="Tib")
        db.query.return_value.filter.return_value.first.side_effect = [jr, requester]
        result = get_join_request_notification_targets(
            join_request_id=jr.id, skip=0, limit=100
        )

    assert result.event_type == JOIN_REQUEST_DECIDED_EVENT
    assert [r.user_id for r in result.recipients] == [jr.user_id]
    assert "joined Chanting Circle" in result.title


def test_rejected_request_copy_differs_from_approved():
    jr = _join_request(AuthorGroupJoinRequestStatus.REJECTED)

    with patch(f"{_NOTIF}.SessionLocal") as mock_session, patch(
        f"{_NOTIF}.get_active_push_devices_by_user_ids", return_value={},
    ):
        db = MagicMock()
        mock_session.return_value.__enter__.return_value = db
        db.query.return_value.filter.return_value.first.side_effect = [jr, None]
        result = get_join_request_notification_targets(
            join_request_id=jr.id, skip=0, limit=100
        )

    assert "declined" in result.title
    assert result.total == 1
    assert result.recipients == []
