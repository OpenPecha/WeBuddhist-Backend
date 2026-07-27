from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from pecha_api.group_posts.enums import GroupPostMediaType, GroupPostStatus


class GroupPostMediaDTO(BaseModel):
    """DTO for a post media item with presigned URLs."""
    id: UUID
    media_type: str
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None
    display_order: int


class GroupPostLinkDTO(BaseModel):
    """DTO for a post external link."""
    id: UUID
    type: str
    url: str
    label: Optional[str] = None
    display_order: int


class GroupPostDTO(BaseModel):
    """DTO for a single post with media and links."""
    id: UUID
    group_id: UUID
    caption: Optional[str] = None
    status: str
    published_at: str
    media: List[GroupPostMediaDTO]
    links: List[GroupPostLinkDTO]
    created_at: str
    updated_at: Optional[str] = None


class GroupPostsResponse(BaseModel):
    """Response for list posts endpoints."""
    posts: List[GroupPostDTO]
    skip: int
    limit: int
    total: int


class GroupPostMediaRequest(BaseModel):
    """Request payload for one media item on a post."""
    media_type: GroupPostMediaType
    media_key: str
    thumbnail_key: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration_ms: Optional[int] = None
    display_order: int = 1

    @field_validator("media_key")
    @classmethod
    def validate_media_key(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("media_key must not be empty")
        return value.strip()


class GroupPostLinkRequest(BaseModel):
    """Request payload for one external link on a post."""
    type: str
    url: str
    label: Optional[str] = None
    display_order: int = 1

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()
        if not value.lower().startswith("https://"):
            raise ValueError("url must start with https://")
        return value


class CreateGroupPostRequest(BaseModel):
    """Request to create a new post."""
    caption: Optional[str] = None
    status: GroupPostStatus = GroupPostStatus.PUBLISHED
    published_at: Optional[datetime] = None
    media: List[GroupPostMediaRequest] = []
    links: List[GroupPostLinkRequest] = []


class UpdateGroupPostRequest(BaseModel):
    """Request to update caption / status / published_at. Pass an empty
    caption string to clear the caption."""
    caption: Optional[str] = None
    status: Optional[GroupPostStatus] = None
    published_at: Optional[datetime] = None


class ReplaceGroupPostMediaRequest(BaseModel):
    """Request to replace the full ordered media set of a post."""
    media: List[GroupPostMediaRequest] = []


class ReplaceGroupPostLinksRequest(BaseModel):
    """Request to replace the full ordered link set of a post."""
    links: List[GroupPostLinkRequest] = []
