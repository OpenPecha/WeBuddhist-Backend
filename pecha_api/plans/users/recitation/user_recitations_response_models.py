from enum import Enum

from pydantic import BaseModel, model_serializer
from uuid import UUID
from typing import List, Optional


class UserRecitationItemType(str, Enum):
    RECITATION = "RECITATION"
    RECITATION_COLLECTION = "RECITATION_COLLECTION"
    GROUP_RECITATION_COLLECTION = "GROUP_RECITATION_COLLECTION"


class CreateUserRecitationRequest(BaseModel):
    text_id: UUID


class UserRecitationDTO(BaseModel):
    type: UserRecitationItemType = UserRecitationItemType.RECITATION
    title: Optional[str] = None
    name: Optional[str] = None
    text_id: Optional[UUID] = None
    collection_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    image_url: Optional[str] = None
    language: Optional[str] = None
    display_order: Optional[int] = None
    item_count: Optional[int] = None

    @model_serializer(mode="wrap")
    def _omit_inapplicable_fields(self, serializer) -> dict:
        data = serializer(self)
        if self.type == UserRecitationItemType.RECITATION:
            for field in ("name", "collection_id", "group_id", "item_count"):
                data.pop(field, None)
        elif self.type == UserRecitationItemType.RECITATION_COLLECTION:
            for field in ("title", "text_id", "language", "display_order", "group_id"):
                data.pop(field, None)
        elif self.type == UserRecitationItemType.GROUP_RECITATION_COLLECTION:
            for field in ("title", "text_id", "language", "display_order"):
                data.pop(field, None)
        return data


class UserRecitationsResponse(BaseModel):
    recitations: List[UserRecitationDTO]


class RecitationOrderItem(BaseModel):
    text_id: UUID
    display_order: int


class UpdateRecitationOrderRequest(BaseModel):
    recitations: List[RecitationOrderItem]
