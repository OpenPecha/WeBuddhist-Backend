from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class GroupRecitationCollectionItemDTO(BaseModel):
    """DTO for collection item with text details from MongoDB"""
    id: UUID
    text_id: UUID
    title: str
    language: Optional[str] = None
    type: Optional[str] = None
    display_order: int


class GroupRecitationCollectionDTO(BaseModel):
    """DTO for collection list (without items)"""
    id: UUID
    group_id: UUID
    name: str
    img_url: Optional[str] = None
    item_count: int
    created_at: str


class GroupRecitationCollectionDetailDTO(BaseModel):
    """DTO for single collection with items"""
    id: UUID
    group_id: UUID
    name: str
    img_url: Optional[str] = None
    created_at: str
    items: List[GroupRecitationCollectionItemDTO]


class GroupRecitationCollectionsResponse(BaseModel):
    """Response for list collections endpoint"""
    collections: List[GroupRecitationCollectionDTO]
    skip: int
    limit: int
    total: int
