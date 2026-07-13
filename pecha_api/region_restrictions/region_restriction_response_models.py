from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType


class ChinaRestrictedItemDTO(BaseModel):
    id: UUID
    item_type: RestrictedItemType
    item_id: UUID
    title: Optional[str] = None
    subtitle: Optional[str] = None
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


class ChinaRestrictionCandidateDTO(BaseModel):
    id: UUID
    title: str
    subtitle: Optional[str] = None


class ChinaRestrictionCandidateListResponse(BaseModel):
    items: list[ChinaRestrictionCandidateDTO]
    skip: int
    limit: int
    total: int
