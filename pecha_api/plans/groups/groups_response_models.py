from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from pecha_api.plans.groups.groups_enums import AuthorGroupInviteStatus, AuthorGroupMemberRole, AuthorGroupType
from pecha_api.plans.groups.group_summary_models import (
    AuthorGroupSummaryDTO,
    GroupMetadataDTO,
    GroupMetadataResponse,
)
from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.plans.plans_response_models import PlanDTO
from pecha_api.plans.series.series_response_models import SeriesListItemDTO
from pecha_api.plans.tags.tag_response_models import TagSummaryDTO

__all__ = [
    "AuthorGroupSummaryDTO",
    "GroupMetadataDTO",
    "GroupMetadataResponse",
    "GroupMetadataInput",
    "GroupSocialLinkInput",
    "GroupSocialLinkDTO",
    "AuthorGroupMemberDTO",
    "AuthorGroupDetailDTO",
    "AuthorGroupListResponse",
    "CreateAuthorGroupRequest",
    "UpdateAuthorGroupRequest",
    "ReplaceGroupTagsRequest",
    "ReplaceGroupSeriesRequest",
    "ReplaceGroupPlansRequest",
    "ReplaceGroupSocialLinksRequest",
    "CreateGroupInviteRequest",
    "GroupInviteDTO",
    "GroupInviteListResponse",
    "GroupInviteCreatedResponse",
    "UpdateGroupMemberRoleRequest",
    "TransferGroupOwnershipRequest",
]


class GroupMetadataInput(BaseModel):
    title: str
    sub_title: Optional[str] = None
    description: Optional[str] = None
    language: LanguageCode


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


class AuthorGroupDetailDTO(BaseModel):
    id: UUID
    slug: str
    group_type: AuthorGroupType
    is_public: bool
    avatar_key: Optional[str] = None
    banner_key: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    metadata: GroupMetadataResponse = []
    members: List[AuthorGroupMemberDTO] = []
    tags: List[TagSummaryDTO] = []
    social_links: List[GroupSocialLinkDTO] = []
    series: List[SeriesListItemDTO] = []
    plans: List[PlanDTO] = []
    follower_count: int = 0
    joiner_count: int = 0


class PublicAuthorGroupSummaryDTO(AuthorGroupSummaryDTO):
    tags: List[str] = []


class PublicAuthorGroupDetailDTO(AuthorGroupDetailDTO):
    tags: List[str] = []


class AuthorGroupListResponse(BaseModel):
    groups: List[AuthorGroupSummaryDTO]
    skip: int
    limit: int
    total: int


class PublicAuthorGroupListResponse(BaseModel):
    groups: List[PublicAuthorGroupSummaryDTO]
    skip: int
    limit: int
    total: int


class CreateAuthorGroupRequest(BaseModel):
    slug: str
    group_type: AuthorGroupType = AuthorGroupType.PAGE
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


class GroupInviteDTO(BaseModel):
    id: UUID
    group_id: UUID
    group_name: str
    target_email: str
    role: AuthorGroupMemberRole
    status: AuthorGroupInviteStatus
    expires_at: datetime
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime
    created_by: str
    inviter_name: str
    inviter_email: str


class GroupInviteListResponse(BaseModel):
    invites: List[GroupInviteDTO]
    total: int


class GroupInviteCreatedResponse(BaseModel):
    invite: GroupInviteDTO
    notification_id: Optional[UUID] = None


class UpdateGroupMemberRoleRequest(BaseModel):
    role: AuthorGroupMemberRole


class TransferGroupOwnershipRequest(BaseModel):
    new_owner_author_id: UUID
