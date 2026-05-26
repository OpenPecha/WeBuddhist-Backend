import uuid
from beanie import Document
from uuid import UUID
from typing import List
from pydantic import Field

from .groups_response_models import (
    GroupDTO
)
from .groups_enums import GroupType

class Group(Document):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type: GroupType

    class Settings:
        collection = "groups"
    
    @classmethod
    async def check_exists(cls, group_id: UUID) -> bool:
        group = await cls.find_one(cls.id == group_id)
        return group is not None

    @classmethod
    async def get_group_by_id(cls, group_id: UUID):
        return await cls.find_one(cls.id == group_id)

    @classmethod
    async def get_groups_by_ids(cls, group_ids: List[str]) -> List["Group"]:
        group_ids = [UUID(group_id) for group_id in group_ids]
        search = await cls.find({"_id": {"$in": group_ids}}).to_list()
        return search
    
    @classmethod
    async def delete_group_by_id(cls, group_id: UUID):
        return await cls.find_one(cls.id == group_id).delete()
