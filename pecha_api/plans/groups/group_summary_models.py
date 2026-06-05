from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel

from pecha_api.plans.tags.tag_response_models import TagSummaryDTO


class GroupMetadataDTO(BaseModel):
    id: UUID
    title: str
    sub_title: Optional[str] = None
    description: Optional[str] = None
    language: str


GroupMetadataResponse = Union[GroupMetadataDTO, List[GroupMetadataDTO], None]


class AuthorGroupSummaryDTO(BaseModel):
    id: UUID
    slug: str
    is_public: bool
    metadata: GroupMetadataResponse = []
    tags: List[TagSummaryDTO] = []
    follower_count: int = 0
    member_count: int = 0
