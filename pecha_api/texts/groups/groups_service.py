from ...error_contants import ErrorConstants
from fastapi import HTTPException
from starlette import status
from uuid import UUID
from typing import Dict, List
import logging

from .groups_repository import (
    create_group,
    check_group_exists,
    get_group_by_id,
    get_groups_by_ids,
    delete_group_by_id
)

from .groups_response_models import (
    CreateGroupRequest,
    GroupDTO
)

from pecha_api.users.users_service import (
    validate_user_exists
)

from .groups_cache_service import (
    get_group_by_id_cache,
    set_group_by_id_cache
)
from pecha_api.cache.cache_enums import CacheType

async def validate_group_exists(group_id: str) -> bool:
    is_exists = False
    try:
        uuid_group_id = UUID(group_id)
        is_exists = await check_group_exists(group_id=uuid_group_id)
        return is_exists
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorConstants.INVALID_UUID_MESSAGE
        )
    
async def get_groups_by_list_of_ids(group_ids: List[str]) -> Dict[str, GroupDTO]:
    groups: Dict[str, GroupDTO] = await get_groups_by_ids(group_ids=group_ids)
    return groups

async def get_group_details(group_id: str) -> GroupDTO | None:
    cache_data: GroupDTO = await get_group_by_id_cache(group_id=group_id, cache_type=CacheType.GROUP_DETAIL)
    if cache_data:
        return cache_data
    try:
        uuid_group_id = UUID(group_id)
        group_details = await get_group_by_id(group_id=uuid_group_id)
        if not group_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorConstants.GROUP_NOT_FOUND_MESSAGE
            )
        response = GroupDTO(
            id=str(group_details.id),
            type=group_details.type
        )
        await set_group_by_id_cache(group_id=group_id, cache_type=CacheType.GROUP_DETAIL, data=response)
        return response
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorConstants.INVALID_UUID_MESSAGE
        )

async def create_new_group(
    create_group_request: CreateGroupRequest,
    token: str
) -> GroupDTO:
    is_valid_user = validate_user_exists(token=token)
    if not is_valid_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorConstants.TOKEN_ERROR_MESSAGE
        )
    return await create_group(
        create_group_request=create_group_request
    )

async def delete_group_by_group_id(group_id: str):
    is_valid_group = await validate_group_exists(group_id=group_id)
    if not is_valid_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorConstants.GROUP_NOT_FOUND_MESSAGE
        )
    await delete_group_by_id(group_id=group_id)