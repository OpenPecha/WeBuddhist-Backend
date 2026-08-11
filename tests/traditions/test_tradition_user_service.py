import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from pecha_api.traditions.tradition_response_models import SaveUserTraditionRequest
from pecha_api.traditions.tradition_service import (
    delete_user_tradition_service,
    update_user_tradition_service,
)


def _session_cm(db_mock):
    session_cm = MagicMock()
    session_cm.__enter__.return_value = db_mock
    session_cm.__exit__.return_value = False
    return session_cm


@pytest.mark.asyncio
async def test_update_user_tradition_service_returns_updated_dto():
    user_id = uuid.uuid4()
    user_tradition_id = uuid.uuid4()
    update_request = SaveUserTraditionRequest(tradition_code="chinese")
    updated_record = SimpleNamespace(
        id=user_tradition_id,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-02T00:00:00Z",
    )
    db_mock = MagicMock()
    session_cm = _session_cm(db_mock)

    with patch(
        "pecha_api.traditions.tradition_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.traditions.tradition_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.traditions.tradition_service.update_user_tradition",
        return_value=updated_record,
    ) as mock_update, patch(
        "pecha_api.traditions.tradition_service._build_user_tradition_dto",
        return_value=SimpleNamespace(
            id=user_tradition_id,
            tradition_code="chinese",
            tradition_name="Chinese scriptures",
            created_at=updated_record.created_at,
            updated_at=updated_record.updated_at,
        ),
    ) as mock_build_dto:
        result = await update_user_tradition_service(
            token="tok",
            user_tradition_id=user_tradition_id,
            update_request=update_request,
        )

    mock_update.assert_called_once_with(
        db=db_mock,
        user_id=user_id,
        user_tradition_id=user_tradition_id,
        tradition_code="chinese",
    )
    mock_build_dto.assert_called_once()
    assert result.tradition_code == "chinese"


@pytest.mark.asyncio
async def test_delete_user_tradition_service_delegates_to_repository():
    user_id = uuid.uuid4()
    user_tradition_id = uuid.uuid4()
    db_mock = MagicMock()
    session_cm = _session_cm(db_mock)

    with patch(
        "pecha_api.traditions.tradition_service.validate_and_extract_user_details",
        return_value=SimpleNamespace(id=user_id),
    ), patch(
        "pecha_api.traditions.tradition_service.SessionLocal",
        return_value=session_cm,
    ), patch(
        "pecha_api.traditions.tradition_service.delete_user_tradition",
    ) as mock_delete:
        await delete_user_tradition_service(token="tok", user_tradition_id=user_tradition_id)

    mock_delete.assert_called_once_with(
        db=db_mock,
        user_id=user_id,
        user_tradition_id=user_tradition_id,
    )


def test_update_user_tradition_raises_404_when_missing():
    from pecha_api.traditions.tradition_repository import update_user_tradition

    db_mock = MagicMock()
    db_mock.query.return_value.options.return_value.filter.return_value.first.return_value = None

    with patch(
        "pecha_api.traditions.tradition_repository.joinedload",
        return_value=MagicMock(),
    ), pytest.raises(HTTPException) as exc_info:
        update_user_tradition(
            db=db_mock,
            user_id=uuid.uuid4(),
            user_tradition_id=uuid.uuid4(),
            tradition_code="pali",
        )

    assert exc_info.value.status_code == 404


def test_update_user_tradition_raises_409_when_target_already_exists():
    from pecha_api.traditions.tradition_repository import update_user_tradition

    user_id = uuid.uuid4()
    user_tradition_id = uuid.uuid4()
    existing = SimpleNamespace(id=user_tradition_id, tradition_id=uuid.uuid4(), tradition=None)
    conflicting = SimpleNamespace(id=uuid.uuid4())
    target_tradition = SimpleNamespace(id=uuid.uuid4(), code="tibetan", metadata_entries=[])

    load_query = MagicMock()
    load_query.options.return_value.filter.return_value.first.return_value = existing
    conflict_query = MagicMock()
    conflict_query.filter.return_value.first.return_value = conflicting

    db_mock = MagicMock()
    db_mock.query.side_effect = [load_query, conflict_query]

    with patch(
        "pecha_api.traditions.tradition_repository.joinedload",
        return_value=MagicMock(),
    ), patch(
        "pecha_api.traditions.tradition_repository.get_tradition_by_code",
        return_value=target_tradition,
    ), pytest.raises(HTTPException) as exc_info:
        update_user_tradition(
            db=db_mock,
            user_id=user_id,
            user_tradition_id=user_tradition_id,
            tradition_code="tibetan",
        )

    assert exc_info.value.status_code == 409
