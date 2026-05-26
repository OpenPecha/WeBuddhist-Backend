from uuid import UUID
from beanie.exceptions import CollectionWasNotInitialized
import logging
from typing import List, Dict
from ...constants import Constants
from starlette import status
from fastapi import HTTPException
from pecha_api.error_contants import ErrorConstants

from .groups_models import Group
from .groups_response_models import (
    CreateGroupRequest,
    GroupDTO
)

async def check_group_exists(group_id: UUID) -> bool:
    try:
        is_group_exists = await Group.check_exists(group_id=group_id)
        return is_group_exists
    except CollectionWasNotInitialized as e:
        logging.error(e)
        return False

async def get_group_by_id(group_id: UUID) -> GroupDTO | None:
    group = await Group.get_group_by_id(group_id=group_id)
    if not group:
        return None
    return GroupDTO(
        id=str(group.id),
        type=group.type
    )

async def get_groups_by_ids(group_ids: List[str]) -> Dict[str, GroupDTO]:
    try:
        if not group_ids:
            return {}
        list_of_groups = await Group.get_groups_by_ids(group_ids=group_ids)
        return {str(group.id): GroupDTO(
            id=str(group.id),
            type=group.type
        ) for group in list_of_groups}
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return {}

async def create_group(
    create_group_request: CreateGroupRequest
) -> GroupDTO:

    group = Group(
        type=create_group_request.type.value
    )
    saved_group = await group.insert()

    return GroupDTO(
        id=str(saved_group.id),
        type=saved_group.type
    )

async def delete_group_by_id(group_id: str):
    try:
        group_uuid = UUID(group_id)
        await Group.delete_group_by_id(group_id=group_uuid)
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return None