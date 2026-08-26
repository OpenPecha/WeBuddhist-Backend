from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.push_devices.push_device_enums import PushPlatform
from pecha_api.push_devices.push_device_models import PushDeviceToken
from pecha_api.push_devices.push_device_repository import (
    delete_push_device_token,
    delete_push_device_token_by_token,
    save_push_device_token,
)


def _make_query_chain(result):
    chain = MagicMock()
    chain.filter.return_value = chain
    chain.order_by.return_value = chain
    chain.first.return_value = result
    chain.all.return_value = result if isinstance(result, list) else []
    return chain


def test_save_push_device_token_creates_new_record():
    db = MagicMock()
    push_device_token = PushDeviceToken(
        id=uuid4(),
        user_id=uuid4(),
        token="new-token",
        platform=PushPlatform.ANDROID,
        device_id="device-1",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    result = save_push_device_token(db=db, push_device_token=push_device_token, is_new=True)

    db.add.assert_called_once_with(push_device_token)
    db.commit.assert_called_once()
    db.refresh.assert_called_once()
    assert result is push_device_token


def test_delete_push_device_token_by_token_removes_all_conflicting_records():
    conflicting_one = PushDeviceToken(
        id=uuid4(),
        user_id=uuid4(),
        token="conflicting-token",
        platform=PushPlatform.ANDROID,
        device_id="device-1",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    conflicting_two = PushDeviceToken(
        id=uuid4(),
        user_id=uuid4(),
        token="conflicting-token",
        platform=PushPlatform.IOS,
        device_id="device-2",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db = MagicMock()
    db.query.return_value = _make_query_chain([conflicting_one, conflicting_two])

    delete_push_device_token_by_token(db=db, token="conflicting-token")

    assert db.delete.call_count == 2
    db.delete.assert_any_call(conflicting_one)
    db.delete.assert_any_call(conflicting_two)
    db.flush.assert_called_once()


def test_delete_push_device_token_not_found_raises_404():
    user_id = uuid4()
    db = MagicMock()
    db.query.return_value = _make_query_chain(None)

    with pytest.raises(HTTPException) as exc_info:
        delete_push_device_token(db=db, user_id=user_id, push_device_token_id=uuid4())

    assert exc_info.value.status_code == 404
