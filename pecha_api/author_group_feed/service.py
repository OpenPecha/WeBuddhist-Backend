from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from pecha_api.config import get
from pecha_api.events.event_participant_repository import (
    get_event_participant_counts,
    get_joined_event_ids_by_user,
)
from pecha_api.events.event_repository import get_events
from pecha_api.events.event_service import _event_to_dto
from pecha_api.group_posts.enums import GroupPostStatus
from pecha_api.group_posts.repository import get_posts_for_group_ids
from pecha_api.group_posts.service import build_post_dtos
from pecha_api.plans.groups.groups_models import AuthorGroup
from pecha_api.plans.groups.groups_repository import (
    get_groups_by_ids,
    get_joined_group_ids_by_user,
    get_public_group_ids,
)
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.users.users_service import validate_and_extract_user_details

from pecha_api.author_group_feed.response_models import (
    AuthorGroupFeedItemDTO,
    AuthorGroupFeedItemType,
    AuthorGroupFeedResponse,
)


def _as_aware_utc(value: Optional[datetime]) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _isoformat(value: datetime) -> str:
    return _as_aware_utc(value).isoformat()


def _group_avatar_url(avatar_key: Optional[str]) -> Optional[str]:
    if not avatar_key:
        return None
    try:
        return generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=avatar_key,
        )
    except Exception:
        return None


def _group_display_name(group: AuthorGroup, language: Optional[str] = None) -> str:
    entries = group.metadata_entries or []
    if not entries:
        return group.slug or "Group"

    def _lang(entry) -> str:
        value = entry.language
        return value.value if hasattr(value, "value") else str(value)

    if language:
        requested = language.upper()
        for entry in entries:
            if _lang(entry).upper() == requested:
                return entry.title

    for entry in entries:
        if _lang(entry).upper() == "EN":
            return entry.title
    return entries[0].title


def _resolve_feed_group_ids(
    *,
    joined_ids: List[UUID],
    should_include_unfollowed: bool,
    db: Session,
) -> Tuple[List[UUID], Set[UUID]]:
    """Return (group_ids_to_query, joined_id_set)."""
    public_joined = [
        group.id
        for group in get_groups_by_ids(db=db, group_ids=joined_ids)
        if group.is_public
    ]
    joined_set = set(public_joined)

    if not should_include_unfollowed:
        return public_joined, joined_set

    public_ids = get_public_group_ids(db=db)
    return public_ids, joined_set


def _build_group_card_map(
    db: Session,
    group_ids: List[UUID],
    language: Optional[str],
) -> Dict[UUID, dict]:
    groups = get_groups_by_ids(db=db, group_ids=group_ids)
    return {
        group.id: {
            "group_id": group.id,
            "group_name": _group_display_name(group, language=language),
            "group_slug": group.slug,
            "group_avatar_url": _group_avatar_url(group.avatar_key),
        }
        for group in groups
    }


def _get_author_group_feed(
    db: Session,
    token: str,
    should_include_unfollowed: bool,
    skip: int = 0,
    limit: int = 20,
    language: Optional[str] = None,
) -> AuthorGroupFeedResponse:
    """Authenticated mixed feed of posts and events from author groups.

    Default: only groups the user joined.
    With should_include_unfollowed=True: mix in other public groups.
    """
    current_user = validate_and_extract_user_details(token=token)

    joined_group_ids = get_joined_group_ids_by_user(db=db, user_id=current_user.id)
    group_ids, joined_group_id_set = _resolve_feed_group_ids(
        joined_ids=joined_group_ids,
        should_include_unfollowed=should_include_unfollowed,
        db=db,
    )

    if not group_ids:
        return AuthorGroupFeedResponse(
            items=[],
            skip=skip,
            limit=limit,
            total=0,
            should_include_unfollowed=should_include_unfollowed,
        )

    # Fetch enough of each type to fill the requested page after merge.
    fetch_limit = skip + limit

    posts, posts_total = get_posts_for_group_ids(
        db=db,
        group_ids=group_ids,
        skip=0,
        limit=fetch_limit,
        status=GroupPostStatus.PUBLISHED,
    )
    post_dtos = build_post_dtos(db, posts, user_id=current_user.id)

    events, events_total = get_events(
        db=db,
        restrict_group_ids=group_ids,
        skip=0,
        limit=fetch_limit,
        should_sort_newest_first=True,
    )
    event_ids = [event.id for event in events]
    counts_by_event = get_event_participant_counts(db=db, event_ids=event_ids)
    joined_event_ids = set(
        get_joined_event_ids_by_user(
            db=db,
            user_id=current_user.id,
            event_ids=event_ids,
        )
    )

    page_group_ids = list({
        *[post.group_id for post in posts],
        *[event.group_id for event in events],
    })
    group_cards = _build_group_card_map(db, page_group_ids, language)

    cards: List[Tuple[datetime, AuthorGroupFeedItemDTO]] = []

    for post, post_dto in zip(posts, post_dtos):
        feed_at = _as_aware_utc(post.published_at)
        group_info = group_cards.get(post.group_id, {})
        cards.append(
            (
                feed_at,
                AuthorGroupFeedItemDTO(
                    type=AuthorGroupFeedItemType.POST,
                    feed_at=_isoformat(feed_at),
                    is_joined=post.group_id in joined_group_id_set,
                    group_id=post.group_id,
                    group_name=group_info.get("group_name"),
                    group_slug=group_info.get("group_slug"),
                    group_avatar_url=group_info.get("group_avatar_url"),
                    post=post_dto,
                ),
            )
        )

    for event in events:
        feed_at = _as_aware_utc(event.created_at)
        group_info = group_cards.get(event.group_id, {})
        cards.append(
            (
                feed_at,
                AuthorGroupFeedItemDTO(
                    type=AuthorGroupFeedItemType.EVENT,
                    feed_at=_isoformat(feed_at),
                    is_joined=event.group_id in joined_group_id_set,
                    group_id=event.group_id,
                    group_name=group_info.get("group_name"),
                    group_slug=group_info.get("group_slug"),
                    group_avatar_url=group_info.get("group_avatar_url"),
                    event=_event_to_dto(
                        event,
                        language=language,
                        participant_count=counts_by_event.get(event.id, 0),
                        is_joined=event.id in joined_event_ids,
                    ),
                ),
            )
        )

    cards.sort(key=lambda entry: (entry[0], entry[1].type.value), reverse=True)
    total = posts_total + events_total
    page = [card for _, card in cards[skip:skip + limit]]

    return AuthorGroupFeedResponse(
        items=page,
        skip=skip,
        limit=limit,
        total=total,
        should_include_unfollowed=should_include_unfollowed,
    )


async def get_author_group_feed_service(
    db: Session,
    token: str,
    should_include_unfollowed: bool = False,
    skip: int = 0,
    limit: int = 20,
    language: Optional[str] = None,
) -> AuthorGroupFeedResponse:
    """Build the feed without blocking the application's event loop."""
    return await run_in_threadpool(
        _get_author_group_feed,
        db=db,
        token=token,
        should_include_unfollowed=should_include_unfollowed,
        skip=skip,
        limit=limit,
        language=language,
    )
