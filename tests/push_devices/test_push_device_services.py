from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.push_devices.push_device_enums import PushPlatform
from pecha_api.push_devices.push_device_models import PushDeviceToken
from pecha_api.push_devices.push_device_response_models import RegisterPushDeviceRequest
from pecha_api.push_devices.push_device_service import (
    _upsert_push_device_token,
    delete_push_device_service,
    get_push_devices_service,
    list_all_push_devices_service,
    register_push_device_service,
)


@pytest.mark.asyncio
async def test_register_push_device_service_success():
    user_id = uuid4()
    token_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_user = MagicMock()
    mock_user.id = user_id

    mock_push_device_token = MagicMock()
    mock_push_device_token.id = token_id
    mock_push_device_token.platform = PushPlatform.ANDROID
    mock_push_device_token.device_id = "device-abc"
    mock_push_device_token.is_active = True
    mock_push_device_token.created_at = now
    mock_push_device_token.updated_at = now

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    request = RegisterPushDeviceRequest(
        token="fcm-token-123",
        platform=PushPlatform.ANDROID,
        device_id="device-abc",
    )

    with patch(
        "pecha_api.push_devices.push_device_service.validate_and_extract_user_details"
    ) as mock_validate, patch(
        "pecha_api.push_devices.push_device_service.SessionLocal"
    ) as mock_session, patch(
        "pecha_api.push_devices.push_device_service._upsert_push_device_token"
    ) as mock_upsert:
        mock_validate.return_value = mock_user
        mock_session.return_value = mock_db
        mock_upsert.return_value = mock_push_device_token

        result = await register_push_device_service(token="test_token", register_request=request)

        assert result.id == token_id
        assert result.platform == PushPlatform.ANDROID
        assert result.device_id == "device-abc"
        mock_upsert.assert_called_once_with(
            db=mock_db,
            user_id=user_id,
            token="fcm-token-123",
            platform=PushPlatform.ANDROID,
            device_id="device-abc",
        )


@pytest.mark.asyncio
async def test_get_push_devices_service_success():
    user_id = uuid4()
    token_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_user = MagicMock()
    mock_user.id = user_id

    mock_push_device_token = MagicMock()
    mock_push_device_token.id = token_id
    mock_push_device_token.platform = PushPlatform.IOS
    mock_push_device_token.device_id = None
    mock_push_device_token.is_active = True
    mock_push_device_token.created_at = now
    mock_push_device_token.updated_at = now

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with patch(
        "pecha_api.push_devices.push_device_service.validate_and_extract_user_details"
    ) as mock_validate, patch(
        "pecha_api.push_devices.push_device_service.SessionLocal"
    ) as mock_session, patch(
        "pecha_api.push_devices.push_device_service.get_active_push_device_tokens_by_user_id"
    ) as mock_get_tokens:
        mock_validate.return_value = mock_user
        mock_session.return_value = mock_db
        mock_get_tokens.return_value = [mock_push_device_token]

        result = await get_push_devices_service(token="test_token")

        assert len(result.devices) == 1
        assert result.devices[0].id == token_id
        assert result.devices[0].platform == PushPlatform.IOS


@pytest.mark.asyncio
async def test_delete_push_device_service_success():
    user_id = uuid4()
    token_id = uuid4()

    mock_user = MagicMock()
    mock_user.id = user_id

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with patch(
        "pecha_api.push_devices.push_device_service.validate_and_extract_user_details"
    ) as mock_validate, patch(
        "pecha_api.push_devices.push_device_service.SessionLocal"
    ) as mock_session, patch(
        "pecha_api.push_devices.push_device_service.delete_push_device_token"
    ) as mock_delete:
        mock_validate.return_value = mock_user
        mock_session.return_value = mock_db

        await delete_push_device_service(token="test_token", push_device_token_id=token_id)

        mock_delete.assert_called_once_with(
            db=mock_db,
            user_id=user_id,
            push_device_token_id=token_id,
        )


@pytest.mark.asyncio
async def test_list_all_push_devices_service_success():
    user_id = uuid4()
    token_id = uuid4()
    now = datetime.now(timezone.utc)

    mock_push_device_token = MagicMock()
    mock_push_device_token.id = token_id
    mock_push_device_token.user_id = user_id
    mock_push_device_token.token = "fcm-token-123"
    mock_push_device_token.platform = PushPlatform.ANDROID
    mock_push_device_token.device_id = "device-abc"
    mock_push_device_token.is_active = True
    mock_push_device_token.created_at = now
    mock_push_device_token.updated_at = now

    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with patch(
        "pecha_api.push_devices.push_device_service.verify_admin_access",
        return_value=True,
    ), patch(
        "pecha_api.push_devices.push_device_service.SessionLocal"
    ) as mock_session, patch(
        "pecha_api.push_devices.push_device_service.get_all_push_device_tokens",
        return_value=[mock_push_device_token],
    ), patch(
        "pecha_api.push_devices.push_device_service.count_push_device_tokens",
        return_value=1,
    ):
        mock_session.return_value = mock_db

        result = await list_all_push_devices_service(token="admin_token", skip=0, limit=100)

        assert result.total == 1
        assert len(result.devices) == 1
        assert result.devices[0].token == "fcm-token-123"
        assert result.devices[0].user_id == user_id


@pytest.mark.asyncio
async def test_list_all_push_devices_service_forbidden():
    with patch(
        "pecha_api.push_devices.push_device_service.verify_admin_access",
        return_value=False,
    ):
        with pytest.raises(HTTPException) as exc_info:
            await list_all_push_devices_service(token="user_token")

        assert exc_info.value.status_code == 403


def test_upsert_push_device_token_creates_new_installation():
    user_id = uuid4()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with patch(
        "pecha_api.push_devices.push_device_service.get_push_device_token_by_user_and_device_id",
        return_value=None,
    ), patch(
        "pecha_api.push_devices.push_device_service.get_push_device_token_by_token",
        return_value=None,
    ), patch(
        "pecha_api.push_devices.push_device_service.delete_push_device_token_by_token",
    ) as mock_delete_by_token, patch(
        "pecha_api.push_devices.push_device_service.save_push_device_token",
    ) as mock_save:
        mock_save.return_value = MagicMock()

        _upsert_push_device_token(
            db=db,
            user_id=user_id,
            token="new-token",
            platform=PushPlatform.ANDROID,
            device_id="device-1",
        )

        mock_delete_by_token.assert_called_once_with(db=db, token="new-token")
        saved_token = mock_save.call_args.kwargs["push_device_token"]
        assert saved_token.user_id == user_id
        assert saved_token.token == "new-token"
        assert saved_token.device_id == "device-1"
        assert mock_save.call_args.kwargs["is_new"] is True


def test_upsert_push_device_token_same_installation_same_token_updates_last_seen():
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    existing = PushDeviceToken(
        id=uuid4(),
        user_id=user_id,
        token="same-token",
        platform=PushPlatform.ANDROID,
        device_id="device-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    with patch(
        "pecha_api.push_devices.push_device_service.get_push_device_token_by_user_and_device_id",
        return_value=existing,
    ), patch(
        "pecha_api.push_devices.push_device_service.save_push_device_token",
    ) as mock_save:
        mock_save.return_value = existing

        result = _upsert_push_device_token(
            db=MagicMock(),
            user_id=user_id,
            token="same-token",
            platform=PushPlatform.ANDROID,
            device_id="device-1",
        )

        assert result is existing
        assert result.is_active is True
        assert result.updated_at >= now
        mock_save.assert_called_once_with(db=mock_save.call_args.kwargs["db"], push_device_token=existing)


def test_upsert_push_device_token_same_installation_different_token_replaces_token():
    user_id = uuid4()
    now = datetime.now(timezone.utc)
    existing = PushDeviceToken(
        id=uuid4(),
        user_id=user_id,
        token="old-token",
        platform=PushPlatform.IOS,
        device_id="device-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db = MagicMock()

    with patch(
        "pecha_api.push_devices.push_device_service.get_push_device_token_by_user_and_device_id",
        return_value=existing,
    ), patch(
        "pecha_api.push_devices.push_device_service.delete_push_device_token_by_token",
    ) as mock_delete_by_token, patch(
        "pecha_api.push_devices.push_device_service.save_push_device_token",
    ) as mock_save:
        mock_save.return_value = existing

        result = _upsert_push_device_token(
            db=db,
            user_id=user_id,
            token="new-token",
            platform=PushPlatform.ANDROID,
            device_id="device-1",
        )

        mock_delete_by_token.assert_called_once_with(
            db=db,
            token="new-token",
            exclude_id=existing.id,
        )
        assert result.token == "new-token"
        assert result.platform == PushPlatform.ANDROID
        assert result.is_active is True
