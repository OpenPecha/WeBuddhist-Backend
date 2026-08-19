from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from pecha_api.app import api
from pecha_api.push_devices.push_device_enums import PushPlatform
from pecha_api.push_devices.push_device_response_models import (
    PushDeviceTokenDTO,
    PushDeviceTokensResponse,
    RegisterPushDeviceRequest,
)

client = TestClient(api)


def test_register_push_device_success():
    token_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_device = PushDeviceTokenDTO(
        id=token_id,
        platform=PushPlatform.ANDROID,
        device_id="device-abc",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    with patch("pecha_api.push_devices.push_device_views.register_push_device_service") as mock_service:
        mock_service.return_value = mock_device

        response = client.post(
            "/users/me/push-devices",
            json={
                "token": "fcm-token-123",
                "platform": "ANDROID",
                "device_id": "device-abc",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(token_id)
        assert data["platform"] == "ANDROID"
        assert data["device_id"] == "device-abc"
        assert data["is_active"] is True


def test_register_push_device_ios_without_device_id():
    token_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_device = PushDeviceTokenDTO(
        id=token_id,
        platform=PushPlatform.IOS,
        device_id=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    with patch("pecha_api.push_devices.push_device_views.register_push_device_service") as mock_service:
        mock_service.return_value = mock_device

        response = client.post(
            "/users/me/push-devices",
            json={
                "token": "apns-token-456",
                "platform": "IOS",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["platform"] == "IOS"
        assert data["device_id"] is None


def test_register_push_device_blank_token():
    response = client.post(
        "/users/me/push-devices",
        json={
            "token": "   ",
            "platform": "ANDROID",
        },
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 422


def test_register_push_device_invalid_platform():
    response = client.post(
        "/users/me/push-devices",
        json={
            "token": "some-token",
            "platform": "WINDOWS",
        },
        headers={"Authorization": "Bearer test_token"},
    )

    assert response.status_code == 422


def test_register_push_device_unauthorized():
    response = client.post(
        "/users/me/push-devices",
        json={
            "token": "fcm-token-123",
            "platform": "ANDROID",
        },
    )

    assert response.status_code == 403


def test_get_push_devices_success():
    token_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_response = PushDeviceTokensResponse(
        devices=[
            PushDeviceTokenDTO(
                id=token_id,
                platform=PushPlatform.ANDROID,
                device_id="device-abc",
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        ]
    )

    with patch("pecha_api.push_devices.push_device_views.get_push_devices_service") as mock_service:
        mock_service.return_value = mock_response

        response = client.get(
            "/users/me/push-devices",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["devices"]) == 1
        assert data["devices"][0]["id"] == str(token_id)


def test_delete_push_device_success():
    token_id = uuid4()

    with patch("pecha_api.push_devices.push_device_views.delete_push_device_service") as mock_service:
        mock_service.return_value = None

        response = client.delete(
            f"/users/me/push-devices/{token_id}",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 204
        mock_service.assert_called_once()
