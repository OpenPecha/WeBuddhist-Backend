import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.plans.groups.groups_enums import AuthorGroupMemberRole
from pecha_api.plans.platform_enums import PlatformRole
from pecha_api.plans.transfers.transfer_enums import ContentTransferStatus, TransferEntityType
from pecha_api.plans.transfers.transfer_response_models import CreateTransferRequestBody, TransferRequestDTO
from pecha_api.plans.transfers.transfer_service import (
    accept_transfer_request,
    create_plan_transfer_request,
    list_incoming_transfer_requests,
    list_outgoing_transfer_requests,
    list_incoming_transfer_requests_for_group,
    list_outgoing_transfer_requests_for_group,
    reject_transfer_request,
    revoke_transfer_request,
    _group_title,
    _requester_display_name,
)


def _session_local_context(mock_session_local):
    mock_db = MagicMock()
    mock_session_local.return_value.__enter__.return_value = mock_db
    mock_session_local.return_value.__exit__.return_value = False
    return mock_db


def _make_author(*, platform_role=PlatformRole.CREATOR, email="author@example.com"):
    author = MagicMock()
    author.id = uuid.uuid4()
    author.email = email
    author.first_name = "Test"
    author.last_name = "Author"
    author.platform_role = platform_role.value
    author.is_active = True
    return author


def _make_transfer_dto(**overrides) -> TransferRequestDTO:
    defaults = dict(
        id=uuid.uuid4(),
        entity_type=TransferEntityType.PLAN,
        entity_id=uuid.uuid4(),
        from_group_id=uuid.uuid4(),
        to_group_id=uuid.uuid4(),
        status=ContentTransferStatus.PENDING,
        requested_by="author@example.com",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return TransferRequestDTO(**defaults)


def _make_transfer(*, status=ContentTransferStatus.PENDING):
    transfer = MagicMock()
    transfer.id = uuid.uuid4()
    transfer.entity_type = TransferEntityType.PLAN
    transfer.entity_id = uuid.uuid4()
    transfer.from_group_id = uuid.uuid4()
    transfer.to_group_id = uuid.uuid4()
    transfer.status = status.value
    transfer.requested_by = "author@example.com"
    transfer.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    transfer.created_at = datetime.now(timezone.utc)
    return transfer


def test_group_title_fallback():
    assert _group_title(None) == "Group"
    group = MagicMock(metadata_entries=[])
    assert _group_title(group) == "Group"
    meta = MagicMock(title="My Group")
    assert _group_title(MagicMock(metadata_entries=[meta])) == "My Group"


def test_requester_display_name_uses_email_when_no_name():
    author = MagicMock(first_name="", last_name="", email="only@example.com")
    assert _requester_display_name(author) == "only@example.com"


def test_create_plan_transfer_request_success():
    from_group_id = uuid.uuid4()
    to_group_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    author = _make_author()
    plan = MagicMock()
    plan.deleted_at = None
    plan.series_id = None
    plan.group_id = from_group_id
    plan.title = "Test Plan"
    transfer = _make_transfer()
    target_group = MagicMock(metadata_entries=[MagicMock(title="Target")])
    from_group = MagicMock(metadata_entries=[MagicMock(title="Source")])

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_plan_by_id",
        return_value=plan,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.get_group_by_id",
        side_effect=lambda db, group_id: target_group if group_id == to_group_id else from_group,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.get_member_role",
        return_value=AuthorGroupMemberRole.ADMIN,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.require_can_request_transfer",
    ), patch(
        "pecha_api.plans.transfers.transfer_service.has_pending_transfer",
        return_value=False,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.create_transfer_request",
        return_value=transfer,
    ), patch(
        "pecha_api.plans.transfers.transfer_service._notify_target_admins",
        return_value=uuid.uuid4(),
    ), patch(
        "pecha_api.plans.transfers.transfer_service._to_dto",
    ) as mock_to_dto:
        _session_local_context(mock_session_local)
        mock_to_dto.return_value = _make_transfer_dto()
        resp = create_plan_transfer_request(
            token="token",
            plan_id=plan_id,
            body=CreateTransferRequestBody(target_group_id=to_group_id),
        )

    assert resp.notification_id is not None
    mock_to_dto.assert_called_once()


def test_create_plan_transfer_rejects_same_group():
    group_id = uuid.uuid4()
    author = _make_author()
    plan = MagicMock(deleted_at=None, series_id=None, group_id=group_id, title="Plan")

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_plan_by_id",
        return_value=plan,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.get_group_by_id",
        return_value=_make_transfer_dto(),
    ):
        _session_local_context(mock_session_local)
        with pytest.raises(HTTPException) as exc_info:
            create_plan_transfer_request(
                token="token",
                plan_id=uuid.uuid4(),
                body=CreateTransferRequestBody(target_group_id=group_id),
            )

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_create_plan_transfer_forbidden_when_not_target_member():
    from_group_id = uuid.uuid4()
    to_group_id = uuid.uuid4()
    author = _make_author()
    plan = MagicMock(deleted_at=None, series_id=None, group_id=from_group_id, title="Plan")

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_plan_by_id",
        return_value=plan,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.get_group_by_id",
        return_value=_make_transfer_dto(),
    ), patch(
        "pecha_api.plans.transfers.transfer_service.require_can_request_transfer",
    ), patch(
        "pecha_api.plans.transfers.transfer_service.get_member_role",
        return_value=None,
    ):
        _session_local_context(mock_session_local)
        with pytest.raises(HTTPException) as exc_info:
            create_plan_transfer_request(
                token="token",
                plan_id=uuid.uuid4(),
                body=CreateTransferRequestBody(target_group_id=to_group_id),
            )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


def test_list_incoming_transfer_requests_success():
    author = _make_author()
    transfer = _make_transfer()

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service._managed_group_ids",
        return_value=[uuid.uuid4()],
    ), patch(
        "pecha_api.plans.transfers.transfer_service.list_incoming_transfers",
        return_value=[transfer],
    ), patch(
        "pecha_api.plans.transfers.transfer_service._to_dto",
    ) as mock_to_dto:
        _session_local_context(mock_session_local)
        mock_to_dto.return_value = _make_transfer_dto()
        resp = list_incoming_transfer_requests(token="token")

    assert resp.total == 1


def test_list_outgoing_transfer_requests_super_admin():
    author = _make_author(platform_role=PlatformRole.SUPER_ADMIN)
    transfer = _make_transfer()
    mock_db = MagicMock()
    mock_db.query.return_value.order_by.return_value.all.return_value = [transfer]

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service._to_dto",
        return_value=_make_transfer_dto(),
    ):
        mock_session_local.return_value.__enter__.return_value = mock_db
        mock_session_local.return_value.__exit__.return_value = False
        resp = list_outgoing_transfer_requests(token="token")

    assert resp.total == 1


def test_list_incoming_for_group_not_found():
    author = _make_author()

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_group_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session_local)
        with pytest.raises(HTTPException) as exc_info:
            list_incoming_transfer_requests_for_group(
                token="token",
                group_id=uuid.uuid4(),
            )

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_list_outgoing_for_group_not_member():
    author = _make_author()
    group_id = uuid.uuid4()
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_group_by_id",
        return_value=_make_transfer_dto(),
    ), patch(
        "pecha_api.plans.transfers.transfer_service.is_super_admin",
        return_value=False,
    ):
        mock_session_local.return_value.__enter__.return_value = mock_db
        mock_session_local.return_value.__exit__.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            list_outgoing_transfer_requests_for_group(
                token="token",
                group_id=group_id,
            )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


def test_accept_transfer_request_success():
    author = _make_author(platform_role=PlatformRole.SUPER_ADMIN)
    transfer = _make_transfer()

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_transfer_by_id",
        return_value=transfer,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.save_transfer",
        return_value=transfer,
    ), patch(
        "pecha_api.plans.transfers.transfer_service._apply_transfer_accept",
    ), patch(
        "pecha_api.plans.transfers.transfer_service._mark_transfer_notifications_read",
    ), patch(
        "pecha_api.plans.transfers.transfer_service._to_dto",
        return_value=_make_transfer_dto(),
    ):
        _session_local_context(mock_session_local)
        dto = accept_transfer_request(token="token", transfer_id=transfer.id)

    assert dto is not None
    assert transfer.status == ContentTransferStatus.ACCEPTED


def test_accept_transfer_not_found():
    author = _make_author(platform_role=PlatformRole.SUPER_ADMIN)

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_transfer_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session_local)
        with pytest.raises(HTTPException) as exc_info:
            accept_transfer_request(token="token", transfer_id=uuid.uuid4())

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_reject_transfer_request_success():
    author = _make_author(platform_role=PlatformRole.SUPER_ADMIN)
    transfer = _make_transfer()

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_transfer_by_id",
        return_value=transfer,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.save_transfer",
        return_value=transfer,
    ), patch(
        "pecha_api.plans.transfers.transfer_service._mark_transfer_notifications_read",
    ), patch(
        "pecha_api.plans.transfers.transfer_service._to_dto",
        return_value=_make_transfer_dto(),
    ):
        _session_local_context(mock_session_local)
        reject_transfer_request(token="token", transfer_id=transfer.id)

    assert transfer.status == ContentTransferStatus.REJECTED


def test_revoke_transfer_request_success():
    author = _make_author(email="author@example.com")
    transfer = _make_transfer()
    transfer.requested_by = author.email

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_transfer_by_id",
        return_value=transfer,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.save_transfer",
        return_value=transfer,
    ), patch(
        "pecha_api.plans.transfers.transfer_service._to_dto",
        return_value=_make_transfer_dto(),
    ):
        _session_local_context(mock_session_local)
        revoke_transfer_request(token="token", transfer_id=transfer.id)

    assert transfer.status == ContentTransferStatus.REVOKED


def test_create_plan_transfer_plan_not_found():
    author = _make_author()
    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_plan_by_id",
        return_value=None,
    ):
        _session_local_context(mock_session_local)
        with pytest.raises(HTTPException) as exc_info:
            create_plan_transfer_request(
                token="token",
                plan_id=uuid.uuid4(),
                body=CreateTransferRequestBody(target_group_id=uuid.uuid4()),
            )
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


def test_create_plan_transfer_rejects_plan_in_series():
    author = _make_author()
    plan = MagicMock(deleted_at=None, series_id=uuid.uuid4(), group_id=uuid.uuid4(), title="Plan")
    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_plan_by_id",
        return_value=plan,
    ):
        _session_local_context(mock_session_local)
        with pytest.raises(HTTPException) as exc_info:
            create_plan_transfer_request(
                token="token",
                plan_id=uuid.uuid4(),
                body=CreateTransferRequestBody(target_group_id=uuid.uuid4()),
            )
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_create_series_transfer_request_success():
    from pecha_api.plans.transfers.transfer_service import create_series_transfer_request

    from_group_id = uuid.uuid4()
    to_group_id = uuid.uuid4()
    author = _make_author()
    series = MagicMock(deleted_at=None, group_id=from_group_id, metadata_entries=[MagicMock(title="Series")])

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_series_by_id",
        return_value=series,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.get_group_by_id",
        return_value=MagicMock(metadata_entries=[MagicMock(title="Group")]),
    ), patch(
        "pecha_api.plans.transfers.transfer_service.get_member_role",
        return_value=AuthorGroupMemberRole.ADMIN,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.require_can_request_transfer",
    ), patch(
        "pecha_api.plans.transfers.transfer_service.has_pending_transfer",
        return_value=False,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.create_transfer_request",
        return_value=_make_transfer(),
    ), patch(
        "pecha_api.plans.transfers.transfer_service._notify_target_admins",
        return_value=uuid.uuid4(),
    ), patch(
        "pecha_api.plans.transfers.transfer_service._to_dto",
        return_value=_make_transfer_dto(entity_type=TransferEntityType.SERIES),
    ):
        _session_local_context(mock_session_local)
        resp = create_series_transfer_request(
            token="token",
            series_id=uuid.uuid4(),
            body=CreateTransferRequestBody(target_group_id=to_group_id),
        )
    assert resp.notification_id is not None


def test_accept_transfer_expired():
    author = _make_author(platform_role=PlatformRole.SUPER_ADMIN)
    transfer = _make_transfer()
    transfer.expires_at = datetime.now(timezone.utc) - timedelta(days=1)

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_transfer_by_id",
        return_value=transfer,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.save_transfer",
        return_value=transfer,
    ):
        _session_local_context(mock_session_local)
        with pytest.raises(HTTPException) as exc_info:
            accept_transfer_request(token="token", transfer_id=transfer.id)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_accept_transfer_not_pending():
    author = _make_author(platform_role=PlatformRole.SUPER_ADMIN)
    transfer = _make_transfer(status=ContentTransferStatus.ACCEPTED)

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_transfer_by_id",
        return_value=transfer,
    ):
        _session_local_context(mock_session_local)
        with pytest.raises(HTTPException) as exc_info:
            accept_transfer_request(token="token", transfer_id=transfer.id)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_list_outgoing_transfer_requests_creator():
    author = _make_author()
    transfer = _make_transfer()
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = [
        (uuid.uuid4(),)
    ]

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.is_super_admin",
        return_value=False,
    ), patch(
        "pecha_api.plans.transfers.transfer_service.list_outgoing_transfers",
        return_value=[transfer],
    ), patch(
        "pecha_api.plans.transfers.transfer_service._to_dto",
        return_value=_make_transfer_dto(),
    ):
        mock_session_local.return_value.__enter__.return_value = mock_db
        mock_session_local.return_value.__exit__.return_value = False
        resp = list_outgoing_transfer_requests(token="token")

    assert resp.total == 1


def test_list_incoming_for_group_success():
    author = _make_author(platform_role=PlatformRole.SUPER_ADMIN)
    group_id = uuid.uuid4()
    transfer = _make_transfer()

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_group_by_id",
        return_value=MagicMock(),
    ), patch(
        "pecha_api.plans.transfers.transfer_service.list_incoming_transfers",
        return_value=[transfer],
    ), patch(
        "pecha_api.plans.transfers.transfer_service._to_dto",
        return_value=_make_transfer_dto(),
    ):
        _session_local_context(mock_session_local)
        resp = list_incoming_transfer_requests_for_group(token="token", group_id=group_id)

    assert resp.total == 1


def test_list_outgoing_for_group_success():
    author = _make_author(platform_role=PlatformRole.SUPER_ADMIN)
    group_id = uuid.uuid4()
    transfer = _make_transfer()

    with patch(
        "pecha_api.plans.transfers.transfer_service.validate_and_extract_author_details",
        return_value=author,
    ), patch("pecha_api.plans.transfers.transfer_service.SessionLocal") as mock_session_local, patch(
        "pecha_api.plans.transfers.transfer_service.get_group_by_id",
        return_value=MagicMock(),
    ), patch(
        "pecha_api.plans.transfers.transfer_service.list_outgoing_transfers",
        return_value=[transfer],
    ), patch(
        "pecha_api.plans.transfers.transfer_service._to_dto",
        return_value=_make_transfer_dto(),
    ):
        _session_local_context(mock_session_local)
        resp = list_outgoing_transfer_requests_for_group(token="token", group_id=group_id)

    assert resp.total == 1


def test_apply_transfer_accept_updates_plan_group():
    from pecha_api.plans.transfers.transfer_service import _apply_transfer_accept

    plan = MagicMock()
    transfer = _make_transfer()
    transfer.entity_type = TransferEntityType.PLAN
    transfer.entity_id = plan.id
    mock_db = MagicMock()

    with patch(
        "pecha_api.plans.transfers.transfer_service.get_plan_by_id",
        return_value=plan,
    ):
        _apply_transfer_accept(db=mock_db, transfer=transfer)

    assert plan.group_id == transfer.to_group_id
    mock_db.commit.assert_called_once()
