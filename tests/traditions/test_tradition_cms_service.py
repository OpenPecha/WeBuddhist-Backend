from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.traditions.tradition_response_models import (
    CreateTraditionRequest,
    UpdateTraditionRequest,
)
from pecha_api.traditions.tradition_service import (
    create_cms_tradition,
    delete_cms_tradition,
    get_cms_tradition_detail,
    get_cms_traditions_list,
    update_cms_tradition,
)


def _session_cm(db):
    session = MagicMock()
    session.__enter__.return_value = db
    session.__exit__.return_value = False
    return session


def _tradition(code="zen"):
    metadata = SimpleNamespace(
        id=uuid4(),
        language=LanguageCode.EN,
        name="Zen",
        description="Zen tradition",
        other_names=["Chan"],
    )
    return SimpleNamespace(
        id=uuid4(),
        code=code,
        regions=["Japan"],
        parent_id=None,
        metadata_entries=[metadata],
    )


def test_get_cms_traditions_list_builds_paginated_dtos():
    db = MagicMock()
    tradition = _tradition()

    with patch(
        "pecha_api.traditions.tradition_service.validate_and_extract_author_details"
    ) as mock_validate, patch(
        "pecha_api.traditions.tradition_service.SessionLocal",
        return_value=_session_cm(db),
    ), patch(
        "pecha_api.traditions.tradition_service.list_traditions_cms",
        return_value=([tradition], 1),
    ) as mock_list:
        response = get_cms_traditions_list(
            token="token",
            search="zen",
            language="EN",
            skip=5,
            limit=10,
        )

    mock_validate.assert_called_once_with(token="token")
    mock_list.assert_called_once_with(db=db, search="zen", skip=5, limit=10)
    assert response.total == 1
    assert response.skip == 5
    assert response.traditions[0].name == "Zen"
    assert response.traditions[0].metadata[0].other_names == ["Chan"]


def test_get_cms_tradition_detail_returns_dto_and_rejects_legacy():
    db = MagicMock()
    tradition_id = uuid4()

    with patch(
        "pecha_api.traditions.tradition_service.validate_and_extract_author_details"
    ), patch(
        "pecha_api.traditions.tradition_service.SessionLocal",
        return_value=_session_cm(db),
    ), patch(
        "pecha_api.traditions.tradition_service.get_tradition_by_id",
        side_effect=[_tradition(), _tradition(code="legacy_old")],
    ):
        response = get_cms_tradition_detail("token", tradition_id)
        with pytest.raises(HTTPException) as exc_info:
            get_cms_tradition_detail("token", tradition_id)

    assert response.code == "zen"
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_and_update_cms_tradition_delegate_to_repository():
    db = MagicMock()
    tradition_id = uuid4()
    created = _tradition()
    updated = _tradition()
    create_request = CreateTraditionRequest(
        code="zen",
        regions=["Japan"],
        metadata=[{"language": "en", "name": "Zen"}],
    )
    update_request = UpdateTraditionRequest(regions=["China", "Japan"])

    with patch(
        "pecha_api.traditions.tradition_service.validate_and_extract_author_details"
    ), patch(
        "pecha_api.traditions.tradition_service.SessionLocal",
        return_value=_session_cm(db),
    ), patch(
        "pecha_api.traditions.tradition_service.create_tradition",
        return_value=created,
    ) as mock_create, patch(
        "pecha_api.traditions.tradition_service.update_tradition",
        return_value=updated,
    ) as mock_update:
        created_dto = await create_cms_tradition("token", create_request)
        updated_dto = await update_cms_tradition(
            "token",
            tradition_id,
            update_request,
        )

    mock_create.assert_called_once_with(
        db=db,
        code="zen",
        regions=["Japan"],
        parent_id=None,
        metadata_inputs=create_request.metadata,
    )
    mock_update.assert_called_once_with(
        db=db,
        tradition_id=tradition_id,
        code=None,
        regions=["China", "Japan"],
        parent_id=None,
        metadata_inputs=None,
    )
    assert created_dto.code == "zen"
    assert updated_dto.name == "Zen"


def test_delete_cms_tradition_delegates_to_repository():
    db = MagicMock()
    tradition_id = uuid4()

    with patch(
        "pecha_api.traditions.tradition_service.validate_and_extract_author_details"
    ), patch(
        "pecha_api.traditions.tradition_service.SessionLocal",
        return_value=_session_cm(db),
    ), patch(
        "pecha_api.traditions.tradition_service.delete_tradition"
    ) as mock_delete:
        delete_cms_tradition("token", tradition_id)

    mock_delete.assert_called_once_with(db=db, tradition_id=tradition_id)
