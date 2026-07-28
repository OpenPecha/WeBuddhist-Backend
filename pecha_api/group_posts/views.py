from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from starlette import status

from pecha_api.group_posts.response_models import GroupPostDTO, GroupPostsResponse
from pecha_api.group_posts.service import (
    get_group_post_detail_service,
    list_group_posts_service,
)

public_group_posts_router = APIRouter(
    prefix="/author/groups/{group_id}/posts",
    tags=["Public Group Posts"],
)


@public_group_posts_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=GroupPostsResponse,
)
def list_group_posts(
    group_id: UUID,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Chronological feed of published posts for a public group."""
    return list_group_posts_service(group_id=group_id, skip=skip, limit=limit)


@public_group_posts_router.get(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=GroupPostDTO,
)
def get_group_post_detail(group_id: UUID, post_id: UUID):
    """Get a published post with presigned media URLs."""
    return get_group_post_detail_service(group_id=group_id, post_id=post_id)
