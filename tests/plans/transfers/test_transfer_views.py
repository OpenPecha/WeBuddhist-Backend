import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from pecha_api.plans.transfers.transfer_enums import ContentTransferStatus, TransferEntityType
from pecha_api.plans.transfers.transfer_response_models import (
    CreateTransferRequestBody,
    TransferRequestCreatedResponse,
    TransferRequestDTO,
    TransferRequestListResponse,
)
from pecha_api.plans.transfers.transfer_views import (
    get_incoming_transfer_requests,
    get_outgoing_transfer_requests,
    post_plan_transfer_request,
)


def test_get_incoming_transfer_requests_delegates():
    expected = TransferRequestListResponse(transfers=[], total=0)

    with patch(
        "pecha_api.plans.transfers.transfer_views.list_incoming_transfer_requests",
        return_value=expected,
    ) as mock_service:
        resp = get_incoming_transfer_requests(status_filter=None, token="token123")

    assert resp == expected
    mock_service.assert_called_once_with(token="token123", status_filter=None)


def test_get_outgoing_transfer_requests_delegates():
    expected = TransferRequestListResponse(transfers=[], total=0)

    with patch(
        "pecha_api.plans.transfers.transfer_views.list_outgoing_transfer_requests",
        return_value=expected,
    ) as mock_service:
        resp = get_outgoing_transfer_requests(status_filter=None, token="token123")

    assert resp == expected
    mock_service.assert_called_once_with(token="token123", status_filter=None)


def test_post_plan_transfer_request_delegates():
    plan_id = uuid.uuid4()
    body = CreateTransferRequestBody(target_group_id=uuid.uuid4())
    expected = TransferRequestCreatedResponse(
        transfer=TransferRequestDTO(
            id=uuid.uuid4(),
            entity_type=TransferEntityType.PLAN,
            entity_id=plan_id,
            from_group_id=uuid.uuid4(),
            to_group_id=body.target_group_id,
            status=ContentTransferStatus.PENDING,
            requested_by="author@example.com",
            expires_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        ),
        notification_id=None,
    )

    with patch(
        "pecha_api.plans.transfers.transfer_views.create_plan_transfer_request",
        return_value=expected,
    ) as mock_service:
        resp = post_plan_transfer_request(plan_id=plan_id, body=body, token="token123")

    assert resp == expected
    mock_service.assert_called_once_with(token="token123", plan_id=plan_id, body=body)
