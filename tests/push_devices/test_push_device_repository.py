from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.push_devices.push_device_enums import PushPlatform
from pecha_api.push_devices.push_device_models import PushDeviceToken
from pecha_api.push_devices.push_device_repository import (
    delete_push_device_token,
    upsert_push_device_token,
)


def _make_query_chain(result):
    chain = MagicMock()
    chain.filter.return_value = chain
    chain.order_by.return_value = chain
    chain.first.return_value = result
    chain.all.return_value = result if isinstance(result, list) else []
    return chain


def test_upsert_push_device_token_creates_new_record():
    user_id = uuid4()
    db = MagicMock()
    db.query.return_value = _make_query_chain(None)

    result = upsert_push_device_token(
        db=db,
        user_id=user_id,
        token="new-token",
        platform=PushPlatform.ANDROID,
        device_id="device-1",
    )

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.refresh.assert_called_once()
    assert isinstance(result, PushDeviceToken)


def test_upsert_push_device_token_updates_existing_by_token():
    user_id = uuid4()
    existing = PushDeviceToken(
        id=uuid4(),
        user_id=uuid4(),
        token="existing-token",
        platform=PushPlatform.IOS,
        device_id="old-device",
        is_active=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db = MagicMock()
    db.query.return_value = _make_query_chain(existing)

    result = upsert_push_device_token(
        db=db,
        user_id=user_id,
        token="existing-token",
        platform=PushPlatform.ANDROID,
        device_id="new-device",
    )

    assert result.user_id == user_id
    assert result.platform == PushPlatform.ANDROID
    assert result.device_id == "new-device"
    assert result.is_active is True
    db.add.assert_not_called()
    db.commit.assert_called_once()


def test_delete_push_device_token_not_found_raises_404():
    user_id = uuid4()
    db = MagicMock()
    db.query.return_value = _make_query_chain(None)

    with pytest.raises(HTTPException) as exc_info:
        delete_push_device_token(db=db, user_id=user_id, push_device_token_id=uuid4())

    assert exc_info.value.status_code == 404
