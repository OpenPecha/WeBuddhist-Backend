from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID


class TagSummaryDTO(BaseModel):
    id: UUID
    name: str
    image: Optional[str] = None
    image_key: Optional[str] = None
    description: Optional[str] = None
    featured: bool = False


class TagDTO(TagSummaryDTO):
    plan_ids: List[UUID] = []


class CreateTagRequest(BaseModel):
    name: str
    image_key: Optional[str] = None
    description: Optional[str] = None
    featured: bool = False
    plan_ids: Optional[List[UUID]] = None


class UpdateTagRequest(BaseModel):
    name: Optional[str] = None
    image_key: Optional[str] = None
    description: Optional[str] = None
    featured: Optional[bool] = None
    plan_ids: Optional[List[UUID]] = None


class TagsListResponse(BaseModel):
    tags: List[TagDTO]
    skip: int
    limit: int
    total: int


class PublicTagsResponse(BaseModel):
    tags: List[TagSummaryDTO]


class PublicTagsListResponse(BaseModel):
    tags: List[TagSummaryDTO]
    skip: int
    limit: int
    total: int
