from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.notification.notification_response_models import (
    NotificationDTO,
    NotificationListResponse,
)

client = TestClient(api)


def test_get_notifications_delegates_to_service():
    response_model = NotificationListResponse(
        notifications=[],
        skip=0,
        limit=20,
        total=0,
    )
    with patch(
        "pecha_api.notification.notification_views.list_notifications",
        return_value=response_model,
    ) as mock_service:
        response = client.get(
            "/cms/notifications?unread_only=true&skip=0&limit=20",
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == status.HTTP_200_OK
    mock_service.assert_called_once_with(
        token="dummy",
        skip=0,
        limit=20,
        unread_only=True,
    )


def test_patch_mark_notification_read_delegates_to_service():
    notification_id = uuid4()
    dto = NotificationDTO(
        id=notification_id,
        title="Invite",
        category="group_invite",
        is_read=True,
        created_at=datetime.now(timezone.utc),
    )
    with patch(
        "pecha_api.notification.notification_views.mark_notification_as_read",
        return_value=dto,
    ) as mock_service:
        response = client.patch(
            f"/cms/notifications/{notification_id}/read",
            headers={"Authorization": "Bearer dummy"},
        )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_read"] is True
    mock_service.assert_called_once_with(token="dummy", notification_id=notification_id)
