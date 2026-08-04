from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from pecha_api.events.event_response_models import EventDTO
from pecha_api.group_posts.response_models import GroupPostDTO


class AuthorGroupFeedItemType(str, Enum):
    POST = "post"
    EVENT = "event"


class AuthorGroupFeedRequest(BaseModel):
    """Optional body to control feed scope.

    My tab: include_unfollowed=false (followed groups only).
    Discover tab: include_unfollowed=true (mix in other public groups).
    """
    include_unfollowed: bool = False


class AuthorGroupFeedItemDTO(BaseModel):
    type: AuthorGroupFeedItemType
    feed_at: str
    is_followed: bool
    group_id: UUID
    group_name: Optional[str] = None
    group_slug: Optional[str] = None
    group_avatar_url: Optional[str] = None
    post: Optional[GroupPostDTO] = None
    event: Optional[EventDTO] = None


class AuthorGroupFeedResponse(BaseModel):
    items: List[AuthorGroupFeedItemDTO]
    skip: int
    limit: int
    total: int
    include_unfollowed: bool
