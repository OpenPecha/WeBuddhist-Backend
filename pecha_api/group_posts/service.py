import logging
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.groups.follow_scope import resolve_public_group_scope
from pecha_api.plans.groups.groups_repository import (
    get_group_by_id,
    get_public_group_ids,
)
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.uploads.S3_utils import generate_presigned_access_url

from pecha_api.group_posts.enums import GroupPostStatus
from pecha_api.group_posts.models import GroupPost
from pecha_api.group_posts.repository import (
    get_group_posts,
    get_post_by_id_only,
    get_posts_for_group_ids,
)
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


def _author_display_name(author) -> str:
    return f"{author.first_name} {author.last_name}".strip()


def build_post_dto(
    post: GroupPost,
    *,
    creator_name: Optional[str] = None,
    creator_image_url: Optional[str] = None,
    like_count: int = 0,
    comment_count: int = 0,
    liked_by_me: bool = False,
) -> GroupPostDTO:
    """Build a post DTO with presigned media URLs, creator, and engagement counts."""
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
        creator_name=creator_name,
        creator_image_url=creator_image_url,
        like_count=like_count,
        comment_count=comment_count,
        created_at=_isoformat(post.created_at),
        updated_at=_isoformat(post.updated_at),
        liked_by_me=liked_by_me,
    )


def build_post_dtos(
    db: Session,
    posts: List[GroupPost],
    user_id: Optional[UUID] = None,
) -> List[GroupPostDTO]:
    """Build post DTOs with creator profiles and like/comment counts batched."""
    if not posts:
        return []

    # Lazy imports avoid pulling author/like/comment mappers during module import
    # (unit tests instantiate GroupPostMedia without the full model graph).
    from pecha_api.plans.authors.plan_authors_repository import get_authors_by_emails
    from pecha_api.group_posts.comment_repository import get_comment_counts_by_post_ids
    from pecha_api.group_posts.like_repository import (
        batch_check_posts_liked_by_user,
        get_like_counts_by_post_ids,
    )

    post_ids = [post.id for post in posts]
    emails = list({post.created_by for post in posts if post.created_by})
    authors_by_email: Dict[str, object] = {
        author.email: author
        for author in get_authors_by_emails(db=db, emails=emails)
    }
    like_counts = get_like_counts_by_post_ids(db=db, post_ids=post_ids)
    comment_counts = get_comment_counts_by_post_ids(db=db, post_ids=post_ids)
    liked_posts = (
        batch_check_posts_liked_by_user(db=db, post_ids=post_ids, user_id=user_id)
        if user_id
        else set()
    )

    dtos: List[GroupPostDTO] = []
    for post in posts:
        author = authors_by_email.get(post.created_by)
        creator_name = _author_display_name(author) if author else None
        creator_image_url = (
            _generate_presigned_url(author.image_url) if author else None
        )
        dtos.append(
            build_post_dto(
                post,
                creator_name=creator_name,
                creator_image_url=creator_image_url,
                like_count=like_counts.get(post.id, 0),
                comment_count=comment_counts.get(post.id, 0),
                liked_by_me=post.id in liked_posts,
            )
        )
    return dtos


def list_group_posts_service(
    group_id: UUID,
    skip: int = 0,
    limit: int = 20,
    user_id: Optional[UUID] = None,
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
            posts=build_post_dtos(db, posts, user_id=user_id),
            skip=skip,
            limit=limit,
            total=total,
        )


def list_public_group_posts_service(
    *,
    skip: int = 0,
    limit: int = 20,
    user_id: Optional[UUID] = None,
    should_include_unfollowed: bool = False,
) -> GroupPostsResponse:
    """List published posts across followed or all public groups."""
    with SessionLocal() as db:
        if user_id:
            group_ids, _ = resolve_public_group_scope(
                db=db,
                user_id=user_id,
                should_include_unfollowed=should_include_unfollowed,
            )
        else:
            group_ids = get_public_group_ids(db=db)

        posts, total = get_posts_for_group_ids(
            db=db,
            group_ids=group_ids,
            skip=skip,
            limit=limit,
            status=GroupPostStatus.PUBLISHED,
        )
        return GroupPostsResponse(
            posts=build_post_dtos(db, posts, user_id=user_id),
            skip=skip,
            limit=limit,
            total=total,
        )


def get_group_post_detail_service(
    post_id: UUID,
    user_id: Optional[UUID] = None,
) -> GroupPostDTO:
    """Public post detail. HIDDEN and soft-deleted posts return 404."""
    with SessionLocal() as db:
        post = get_post_by_id_only(
            db=db,
            post_id=post_id,
            status=GroupPostStatus.PUBLISHED,
        )

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NOT_FOUND,
            )

        _validate_group_is_public(db, post.group_id)

        return build_post_dtos(db, [post], user_id=user_id)[0]
