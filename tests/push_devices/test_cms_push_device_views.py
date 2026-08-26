from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from pecha_api.app import api
from pecha_api.push_devices.push_device_enums import PushPlatform
from pecha_api.push_devices.push_device_response_models import (
    AdminPushDeviceTokenDTO,
    AdminPushDeviceTokensListResponse,
)

client = TestClient(api)


def test_list_all_push_devices_success():
    user_id = uuid4()
    token_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_response = AdminPushDeviceTokensListResponse(
        devices=[
            AdminPushDeviceTokenDTO(
                id=token_id,
                user_id=user_id,
                token="fcm-token-123",
                platform=PushPlatform.ANDROID,
                device_id="device-abc",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        ],
        total=1,
        skip=0,
        limit=100,
    )

    with patch("pecha_api.push_devices.push_device_views.list_all_push_devices_service") as mock_service:
        mock_service.return_value = mock_response

        response = client.get(
            "/cms/push-devices",
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["devices"]) == 1
        assert data["devices"][0]["token"] == "fcm-token-123"
        assert data["devices"][0]["user_id"] == str(user_id)


def test_list_all_push_devices_with_filters():
    with patch("pecha_api.push_devices.push_device_views.list_all_push_devices_service") as mock_service:
        mock_service.return_value = AdminPushDeviceTokensListResponse(
            devices=[],
            total=0,
            skip=10,
            limit=50,
        )

        response = client.get(
            "/cms/push-devices?skip=10&limit=50&platform=IOS&active_only=false",
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == 200
        mock_service.assert_called_once()
        call_kwargs = mock_service.call_args.kwargs
        assert call_kwargs["skip"] == 10
        assert call_kwargs["limit"] == 50
        assert call_kwargs["platform"] == PushPlatform.IOS
        assert call_kwargs["active_only"] is False


def test_list_all_push_devices_unauthorized():
    response = client.get("/cms/push-devices")

    assert response.status_code == 403
