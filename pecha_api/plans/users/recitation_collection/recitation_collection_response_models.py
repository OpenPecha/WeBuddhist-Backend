from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class RecitationCollectionItemDTO(BaseModel):
    """DTO for collection item with text details from MongoDB"""
    id: UUID
    text_id: UUID
    title: str
    language: Optional[str] = None
    type: Optional[str] = None
    display_order: int


class RecitationCollectionDTO(BaseModel):
    """DTO for collection list (without items)"""
    id: UUID
    name: str
    img_url: Optional[str] = None
    item_count: int
    created_at: str
    updated_at: str


class RecitationCollectionDetailDTO(BaseModel):
    """DTO for single collection with items"""
    id: UUID
    name: str
    img_url: Optional[str] = None
    created_at: str
    updated_at: str
    items: List[RecitationCollectionItemDTO]


class RecitationCollectionsResponse(BaseModel):
    """Response for list collections endpoint"""
    collections: List[RecitationCollectionDTO]
    skip: int
    limit: int
    total: int
