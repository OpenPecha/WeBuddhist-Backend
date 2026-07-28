import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.groups.groups_repository import get_group_by_id
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.uploads.S3_utils import generate_presigned_access_url

from pecha_api.group_posts.enums import GroupPostStatus
from pecha_api.group_posts.models import GroupPost
from pecha_api.group_posts.repository import get_group_posts, get_post_by_id
from pecha_api.group_posts.response_models import (
    GroupPostDTO,
    GroupPostLinkDTO,
    GroupPostMediaDTO,
    GroupPostsResponse,
)

logger = logging.getLogger(__name__)


def _generate_presigned_url(s3_key: Optional[str]) -> Optional[str]:
    """Safely generate presigned URL for S3 key."""
    if not s3_key:
        return None
    try:
        return generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=s3_key,
        )
    except Exception:
        logger.exception(f"Failed to generate presigned URL for {s3_key}")
        return None


def _validate_group_is_public(db: Session, group_id: UUID) -> None:
    """Validate that group exists and is public."""
    group = get_group_by_id(db=db, group_id=group_id)
    if not group or not group.is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )


def _isoformat(value) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def build_post_dto(post: GroupPost) -> GroupPostDTO:
    """Build a post DTO with presigned media URLs and ordered media/links."""
    media_dto = [
        GroupPostMediaDTO(
            id=media.id,
            media_type=_enum_value(media.media_type),
            url=_generate_presigned_url(media.media_key),
            thumbnail_url=_generate_presigned_url(media.thumbnail_key),
            width=media.width,
            height=media.height,
            duration_ms=media.duration_ms,
            display_order=media.display_order,
        )
        for media in sorted(post.media, key=lambda entry: entry.display_order)
    ]
    links_dto = [
        GroupPostLinkDTO(
            id=link.id,
            type=link.type,
            url=link.url,
            label=link.label,
            display_order=link.display_order,
        )
        for link in sorted(post.links, key=lambda entry: entry.display_order)
    ]
    return GroupPostDTO(
        id=post.id,
        group_id=post.group_id,
        caption=post.caption,
        status=_enum_value(post.status),
        published_at=_isoformat(post.published_at),
        media=media_dto,
        links=links_dto,
        created_at=_isoformat(post.created_at),
        updated_at=_isoformat(post.updated_at),
    )


def list_group_posts_service(
    group_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> GroupPostsResponse:
    """Public chronological feed of published posts for a public group."""
    with SessionLocal() as db:
        _validate_group_is_public(db, group_id)

        posts, total = get_group_posts(
            db=db,
            group_id=group_id,
            skip=skip,
            limit=limit,
            status=GroupPostStatus.PUBLISHED,
        )

        return GroupPostsResponse(
            posts=[build_post_dto(post) for post in posts],
            skip=skip,
            limit=limit,
            total=total,
        )


def get_group_post_detail_service(
    group_id: UUID,
    post_id: UUID,
) -> GroupPostDTO:
    """Public post detail. HIDDEN and soft-deleted posts return 404."""
    with SessionLocal() as db:
        _validate_group_is_public(db, group_id)

        post = get_post_by_id(
            db=db,
            post_id=post_id,
            group_id=group_id,
            status=GroupPostStatus.PUBLISHED,
        )

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NOT_FOUND,
            )

        return build_post_dto(post)
