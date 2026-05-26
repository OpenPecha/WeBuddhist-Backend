from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from typing import List, Dict
from fastapi import HTTPException
from starlette import status
from pecha_api.error_contants import ErrorConstants

from pecha_api.texts.groups.groups_service import (
    validate_group_exists,
    get_groups_by_list_of_ids,
    get_group_details,
    create_new_group,
    delete_group_by_group_id
)

from pecha_api.texts.groups.groups_response_models import (
    GroupDTO,
    CreateGroupRequest
)

from pecha_api.texts.groups.groups_enums import GroupType

@pytest.mark.asyncio
async def test_validate_group_exists_success():
    group_id = "4d2f3498-3cc6-4bc6-9beb-37d2f7dc0163"
    with patch("pecha_api.texts.groups.groups_service.check_group_exists", new_callable=AsyncMock, return_value=True):
        response = await validate_group_exists(group_id=group_id)
        assert response == True

@pytest.mark.asyncio
async def test_validate_group_exists_invalid_group_id():
    group_id = "4d2f3498-3cc6-4bc6-9beb-37d2f7dc0163"
    with patch("pecha_api.texts.groups.groups_service.check_group_exists", new_callable=AsyncMock, return_value=False):
        response = await validate_group_exists(group_id=group_id)
        assert response == False
    
@pytest.mark.asyncio
async def test_validate_group_exists_invalid_uuid():
    group_id = "invalid_uuid"
    with pytest.raises(HTTPException) as exc_info:
        await validate_group_exists(group_id=group_id)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == ErrorConstants.INVALID_UUID_MESSAGE
    
@pytest.mark.asyncio
async def test_get_list_of_group_details_success():
    group_ids: List[str] = [
        "4d2f3498-3cc6-4bc6-9beb-37d2f7dc0163",
        "4d2f3498-3cc6-4bc6-9beb-37d2f7dc0164"
    ]
    group_details = {
        group_ids[0]: GroupDTO(
            id=group_ids[0],
            type="version"
        ),
        group_ids[1]: GroupDTO(
            id=group_ids[1],
            type="commentary"
        )
    }
    with patch("pecha_api.texts.groups.groups_service.get_groups_by_ids", new_callable=AsyncMock) as mock_group_details:
        mock_group_details.return_value = group_details
        response: Dict[str, GroupDTO] = await get_groups_by_list_of_ids(group_ids=group_ids)
        # check if dict is null or not
        # check if len(dict) is 2
        # get the fist item and check if the first item is null or not
        # two assertion for the first item
        # don't use directly 0 create a variable
        item_index = 0
        assert response is not None
        assert len(response) == 2
        assert response[group_ids[item_index]] is not None
        assert isinstance(response[group_ids[item_index]], GroupDTO)
        assert response[group_ids[item_index]].id == group_ids[0]
        assert response[group_ids[item_index]].type == "version"
    
@pytest.mark.asyncio
async def test_get_group_details_success():
    group_id = "4d2f3498-3cc6-4bc6-9beb-37d2f7dc0163"
    group_details = GroupDTO(
        id=group_id,
        type="version"
    )
    with patch("pecha_api.texts.groups.groups_service.get_group_by_id", new_callable=AsyncMock) as mock_group_details, \
        patch("pecha_api.texts.groups.groups_service.get_group_by_id_cache", new_callable=AsyncMock, return_value=None), \
        patch("pecha_api.texts.groups.groups_service.set_group_by_id_cache", new_callable=AsyncMock):
        mock_group_details.return_value = group_details
        response = await get_group_details(group_id=group_id)
        assert response is not None
        assert isinstance(response, GroupDTO)
        assert response.id == group_id
        assert response.type == "version"
    
@pytest.mark.asyncio
async def test_get_group_details_invalid_group_id():
    group_id = "4d2f3498-3cc6-4bc6-9beb-37d2f7dc0163"
    with patch("pecha_api.texts.groups.groups_service.get_group_by_id", new_callable=AsyncMock) as mock_group_details,\
        patch("pecha_api.texts.groups.groups_service.get_group_by_id_cache", new_callable=AsyncMock, return_value=None), \
        patch("pecha_api.texts.groups.groups_service.set_group_by_id_cache", new_callable=AsyncMock):
        mock_group_details.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await get_group_details(group_id=group_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ErrorConstants.GROUP_NOT_FOUND_MESSAGE
        
@pytest.mark.asyncio
async def test_get_group_details_invalid_uuid():
    group_id = "invalid_uuid"
    with patch("pecha_api.texts.groups.groups_service.get_group_by_id", new_callable=AsyncMock) as mock_group_details,\
        patch("pecha_api.texts.groups.groups_service.get_group_by_id_cache", new_callable=AsyncMock, return_value=None), \
        patch("pecha_api.texts.groups.groups_service.set_group_by_id_cache", new_callable=AsyncMock):
        mock_group_details.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await get_group_details(group_id=group_id)
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == ErrorConstants.INVALID_UUID_MESSAGE

@pytest.mark.asyncio
async def test_create_new_group_success():
    group_id = "4d2f3498-3cc6-4bc6-9beb-37d2f7dc0163"
    type_ = GroupType.TEXT
    create_group_request = CreateGroupRequest(
        type=GroupType.TEXT
    )
    group_details: GroupDTO = GroupDTO(
        id=group_id,
        type=type_
    )
    with patch("pecha_api.texts.groups.groups_service.validate_user_exists", return_value=True), \
        patch("pecha_api.texts.groups.groups_service.create_group", new_callable=AsyncMock) as mock_create_group:
        mock_create_group.return_value = group_details
        response = await create_new_group(create_group_request=create_group_request, token="valid_token")
        assert response is not None
        assert isinstance(response, GroupDTO)
        assert response.id == group_id
        assert response.type == type_.value

@pytest.mark.asyncio
async def test_create_new_group_not_admin():
    create_group_request = CreateGroupRequest(
        type=GroupType.TEXT
    )
    with patch("pecha_api.texts.groups.groups_service.validate_user_exists", return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await create_new_group(create_group_request=create_group_request, token="valid_token")
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == ErrorConstants.TOKEN_ERROR_MESSAGE

@pytest.mark.asyncio
async def test_delete_group_by_group_id_success():
    group_id = "4d2f3498-3cc6-4bc6-9beb-37d2f7dc0163"
    with patch("pecha_api.texts.groups.groups_service.validate_group_exists", new_callable=AsyncMock, return_value=True),\
        patch("pecha_api.texts.groups.groups_service.delete_group_by_id", new_callable=AsyncMock):
        response = await delete_group_by_group_id(group_id=group_id)
        assert response is None

@pytest.mark.asyncio
async def test_delete_group_by_group_id_invalid_group_id():
    group_id = "4d2f3498-3cc6-4bc6-9beb-37d2f7dc0163"
    with patch("pecha_api.texts.groups.groups_service.validate_group_exists", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await delete_group_by_group_id(group_id=group_id)
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == ErrorConstants.GROUP_NOT_FOUND_MESSAGE