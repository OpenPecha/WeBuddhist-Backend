from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.plans.shared.permissions import require_can_edit_content
from pecha_api.plans.response_message import (
    BAD_REQUEST,
    INVALID_YOUTUBE_URL,
    PLAN_NOT_FOUND,
    PLAN_VIDEO_NOT_FOUND,
)
from pecha_api.plans.videos.plan_video_models import PlanVideo
from pecha_api.plans.videos.plan_video_repository import (
    create_plan_video,
    delete_plan_video,
    get_next_display_order,
    get_plan_video_by_id,
    get_plan_videos_by_plan_id,
    get_plan_videos_by_segment_id,
    reorder_plan_videos,
)
from pecha_api.plans.videos.plan_video_response_models import (
    CreatePlanVideoRequest,
    PlanVideoDTO,
    PlanVideoListResponse,
    ReorderPlanVideosRequest,
)
from pecha_api.plans.videos.youtube_utils import extract_youtube_video_id


def _to_dto(video: PlanVideo) -> PlanVideoDTO:
    return PlanVideoDTO(
        id=video.id,
        plan_id=video.plan_id,
        url=video.url,
        video_id=video.video_id,
        title=video.title,
        display_order=video.display_order,
        created_at=video.created_at,
    )


def _get_author_plan(db, plan_id: UUID, current_author):
    plan = get_plan_by_id(db=db, plan_id=plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(error=BAD_REQUEST, message=PLAN_NOT_FOUND).model_dump(),
        )
    require_can_edit_content(
        db=db,
        group_id=plan.group_id,
        author=current_author,
        content_status=plan.status,
    )
    return plan


def get_public_plan_videos_by_segment_id(segment_id: UUID) -> PlanVideoListResponse:
    """Public, unauthenticated read of the videos for the plan(s) a segment belongs to.

    A segment may belong to multiple plans (its id can appear in sub-tasks across
    plans). Videos from all matching plans are returned as a single flat list,
    de-duplicated so a video shared across plans is shown once. If the segment
    belongs to no plan, an empty list is returned.
    """
    with SessionLocal() as db:
        videos = get_plan_videos_by_segment_id(db=db, segment_id=segment_id)

    deduped: list[PlanVideoDTO] = []
    seen: set[str] = set()
    for video in videos:
        # collapse the same video shared across plans: prefer video_id, fall back to url
        key = video.video_id or video.url
        if key in seen:
            continue
        seen.add(key)
        deduped.append(_to_dto(video))
    return PlanVideoListResponse(videos=deduped)


def list_plan_videos(token: str, plan_id: UUID) -> PlanVideoListResponse:
    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        _get_author_plan(db=db, plan_id=plan_id, current_author=current_author)
        videos = get_plan_videos_by_plan_id(db=db, plan_id=plan_id)
        return PlanVideoListResponse(videos=[_to_dto(video) for video in videos])


def add_plan_video(token: str, plan_id: UUID, request: CreatePlanVideoRequest) -> PlanVideoDTO:
    url = request.url.strip()
    video_id = extract_youtube_video_id(url)
    if not video_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(error=BAD_REQUEST, message=INVALID_YOUTUBE_URL).model_dump(),
        )

    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        _get_author_plan(db=db, plan_id=plan_id, current_author=current_author)

        display_order = get_next_display_order(db=db, plan_id=plan_id)
        video = create_plan_video(
            db=db,
            plan_video=PlanVideo(
                plan_id=plan_id,
                url=url,
                video_id=video_id,
                title=request.title,
                display_order=display_order,
                created_by=current_author.email,
            ),
        )
        return _to_dto(video)


def remove_plan_video(token: str, plan_id: UUID, video_id: UUID) -> None:
    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        _get_author_plan(db=db, plan_id=plan_id, current_author=current_author)

        video = get_plan_video_by_id(db=db, plan_id=plan_id, video_id=video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=BAD_REQUEST, message=PLAN_VIDEO_NOT_FOUND).model_dump(),
            )
        delete_plan_video(db=db, plan_id=plan_id, video_id=video_id)


def reorder_plan_videos_entries(
    token: str, plan_id: UUID, request: ReorderPlanVideosRequest
) -> PlanVideoListResponse:
    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        _get_author_plan(db=db, plan_id=plan_id, current_author=current_author)

        order_by_id = {item.id: item.display_order for item in request.videos}
        reorder_plan_videos(db=db, plan_id=plan_id, order_by_id=order_by_id)

        videos = get_plan_videos_by_plan_id(db=db, plan_id=plan_id)
        return PlanVideoListResponse(videos=[_to_dto(video) for video in videos])
