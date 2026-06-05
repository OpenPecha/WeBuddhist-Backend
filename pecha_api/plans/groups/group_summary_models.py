from typing import List
from uuid import UUID

from pydantic import BaseModel

from pecha_api.plans.tags.tag_response_models import TagSummaryDTO


class GroupMetadataDTO(BaseModel):
    id: UUID
    title: str
    description: str | None = None
    language: str


class AuthorGroupSummaryDTO(BaseModel):
    id: UUID
    slug: str
    is_public: bool
    metadata: List[GroupMetadataDTO]
    tags: List[TagSummaryDTO] = []
    follower_count: int = 0
    member_count: int = 0
