from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from pecha_api.plans.groups.groups_enums import AuthorGroupMemberRole
from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.plans.tags.tag_response_models import TagSummaryDTO


class GroupMetadataInput(BaseModel):
    title: str
    description: Optional[str] = None
    language: LanguageCode


class GroupMetadataDTO(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    language: str


class GroupSocialLinkInput(BaseModel):
    platform: str
    url: str


class GroupSocialLinkDTO(BaseModel):
    id: UUID
    platform: str
    url: str


class AuthorGroupMemberDTO(BaseModel):
    author_id: UUID
    role: AuthorGroupMemberRole
    firstname: str
    lastname: str
    email: str


class AuthorGroupSummaryDTO(BaseModel):
    id: UUID
    slug: str
    is_public: bool
    metadata: List[GroupMetadataDTO]
    tags: List[TagSummaryDTO] = []
    follower_count: int = 0
    member_count: int = 0


class AuthorGroupDetailDTO(BaseModel):
    id: UUID
    slug: str
    is_public: bool
    avatar_key: Optional[str] = None
    banner_key: Optional[str] = None
    metadata: List[GroupMetadataDTO]
    members: List[AuthorGroupMemberDTO] = []
    tags: List[TagSummaryDTO] = []
    social_links: List[GroupSocialLinkDTO] = []
    series_ids: List[UUID] = []
    plan_ids: List[UUID] = []
    follower_count: int = 0


class AuthorGroupListResponse(BaseModel):
    groups: List[AuthorGroupSummaryDTO]
    skip: int
    limit: int
    total: int


class CreateAuthorGroupRequest(BaseModel):
    slug: str
    is_public: bool = True
    avatar_key: Optional[str] = None
    banner_key: Optional[str] = None
    metadata: List[GroupMetadataInput]

    @field_validator("metadata")
    @classmethod
    def validate_metadata_not_empty(cls, value: List[GroupMetadataInput]):
        if not value:
            raise ValueError("At least one metadata entry is required")
        return value


class UpdateAuthorGroupRequest(BaseModel):
    slug: Optional[str] = None
    is_public: Optional[bool] = None
    avatar_key: Optional[str] = None
    banner_key: Optional[str] = None
    metadata: Optional[List[GroupMetadataInput]] = None


class ReplaceGroupTagsRequest(BaseModel):
    tag_ids: List[UUID]


class ReplaceGroupSeriesRequest(BaseModel):
    series_ids: List[UUID]


class ReplaceGroupPlansRequest(BaseModel):
    plan_ids: List[UUID]


class ReplaceGroupSocialLinksRequest(BaseModel):
    social_links: List[GroupSocialLinkInput]


class CreateGroupInviteRequest(BaseModel):
    target_email: str
    role: AuthorGroupMemberRole
    expires_at: datetime
    max_uses: int = 1


class GroupInviteCreatedResponse(BaseModel):
    invite_id: UUID
    token: str
    target_email: str
    role: AuthorGroupMemberRole
    expires_at: datetime
    max_uses: int


class AcceptGroupInviteRequest(BaseModel):
    token: str


class UpdateGroupMemberRoleRequest(BaseModel):
    role: AuthorGroupMemberRole
