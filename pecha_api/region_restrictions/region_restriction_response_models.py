from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType


class ChinaRestrictedItemDTO(BaseModel):
    id: UUID
    item_type: RestrictedItemType
    item_id: UUID
    created_at: str
    updated_at: Optional[str] = None


class ChinaRestrictedItemListResponse(BaseModel):
    items: list[ChinaRestrictedItemDTO]
    skip: int
    limit: int
    total: int


class CreateChinaRestrictedItemRequest(BaseModel):
    item_type: RestrictedItemType
    item_id: UUID
