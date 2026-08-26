from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from pecha_api.traditions.tradition_response_models import (
    CreateTraditionRequest,
    SaveUserTraditionRequest,
    UpdateTraditionRequest,
)
from pecha_api.traditions.tradition_views import (
    cms_create_tradition,
    cms_delete_tradition,
    cms_get_tradition,
    cms_list_traditions,
    cms_update_tradition,
    delete_user_tradition,
    get_tradition_onboarding,
    get_user_traditions,
    list_traditions,
    save_user_tradition,
    update_user_tradition,
)


@pytest.fixture
def credentials():
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")


@pytest.mark.asyncio
async def test_public_tradition_views_forward_fallback_language():
    with patch(
        "pecha_api.traditions.tradition_views.list_traditions_service",
        new=AsyncMock(return_value="traditions"),
    ) as mock_list, patch(
        "pecha_api.traditions.tradition_views.get_tradition_onboarding_service",
        new=AsyncMock(return_value="onboarding"),
    ) as mock_onboarding:
        assert await list_traditions(language=None) == "traditions"
        assert await get_tradition_onboarding(language=None) == "onboarding"

    mock_list.assert_awaited_once_with(language="en")
    mock_onboarding.assert_awaited_once_with(language="en")


@pytest.mark.asyncio
async def test_user_tradition_views_delegate(credentials):
    tradition_id = uuid4()
    request = SaveUserTraditionRequest(tradition_code="pali")

    with patch(
        "pecha_api.traditions.tradition_views.save_user_tradition_service",
        new=AsyncMock(return_value="saved"),
    ) as mock_save, patch(
        "pecha_api.traditions.tradition_views.get_user_traditions_service",
        new=AsyncMock(return_value="listed"),
    ) as mock_list, patch(
        "pecha_api.traditions.tradition_views.update_user_tradition_service",
        new=AsyncMock(return_value="updated"),
    ) as mock_update, patch(
        "pecha_api.traditions.tradition_views.delete_user_tradition_service",
        new=AsyncMock(),
    ) as mock_delete:
        assert await save_user_tradition(credentials, request) == "saved"
        assert await get_user_traditions(credentials, language=None) == "listed"
        assert await update_user_tradition(tradition_id, request, credentials) == "updated"
        assert await delete_user_tradition(tradition_id, credentials) is None

    mock_save.assert_awaited_once_with(token="token", save_request=request)
    mock_list.assert_awaited_once_with(token="token", language="en")
    mock_update.assert_awaited_once_with(
        token="token",
        user_tradition_id=tradition_id,
        update_request=request,
    )
    mock_delete.assert_awaited_once_with(
        token="token",
        user_tradition_id=tradition_id,
    )


@pytest.mark.asyncio
async def test_cms_tradition_views_delegate(credentials):
    tradition_id = uuid4()
    create_request = CreateTraditionRequest(
        code="zen",
        metadata=[{"language": "en", "name": "Zen"}],
    )
    update_request = UpdateTraditionRequest(regions=["Japan"])

    with patch(
        "pecha_api.traditions.tradition_views.get_cms_traditions_list",
        return_value="listed",
    ) as mock_list, patch(
        "pecha_api.traditions.tradition_views.get_cms_tradition_detail",
        return_value="detail",
    ) as mock_detail, patch(
        "pecha_api.traditions.tradition_views.create_cms_tradition",
        new=AsyncMock(return_value="created"),
    ) as mock_create, patch(
        "pecha_api.traditions.tradition_views.update_cms_tradition",
        new=AsyncMock(return_value="updated"),
    ) as mock_update, patch(
        "pecha_api.traditions.tradition_views.delete_cms_tradition",
    ) as mock_delete:
        assert await cms_list_traditions(
            credentials,
            search="zen",
            language=None,
            skip=5,
            limit=10,
        ) == "listed"
        assert await cms_get_tradition(tradition_id, credentials, language=None) == "detail"
        assert await cms_create_tradition(credentials, create_request, language=None) == "created"
        assert (
            await cms_update_tradition(
                tradition_id,
                credentials,
                update_request,
                language=None,
            )
            == "updated"
        )
        assert await cms_delete_tradition(tradition_id, credentials) is None

    mock_list.assert_called_once_with(
        token="token",
        search="zen",
        language="EN",
        skip=5,
        limit=10,
    )
    mock_detail.assert_called_once_with(
        token="token",
        tradition_id=tradition_id,
        language="EN",
    )
    mock_create.assert_awaited_once_with(
        token="token",
        create_request=create_request,
        language="EN",
    )
    mock_update.assert_awaited_once_with(
        token="token",
        tradition_id=tradition_id,
        update_request=update_request,
        language="EN",
    )
    mock_delete.assert_called_once_with(token="token", tradition_id=tradition_id)
