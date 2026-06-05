from typing import Optional, List
import logging
from uuid import UUID
from typing import Optional
from starlette import status
from pecha_api.config import get
from fastapi import HTTPException
from pecha_api.db.database import SessionLocal
from pecha_api.error_contants import ErrorConstants
from pecha_api.plans.items.plan_items_repository import get_days_by_plan_id, get_plan_day_with_tasks_and_subtasks
from datetime import date as DateType, timedelta, datetime as dt, timezone
from pecha_api.plans.public.plan_response_models import PublicPlansResponse, PublicPlanDTO, PlanDayDTO, AuthorDTO,PlanDaysResponse, PlanDayBasic, SubTaskDTO, TaskDTO, ImageUrlModel, TagsResponse, DailyPlanResponse, SeriesDTO, SeriesMetadataDTO
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.plans_enums import ContentType, UserPlanStatus
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.plans.public.plan_repository import (
    get_published_plans_from_db,
    get_published_plans_count,
    get_published_plan_by_id,
    get_published_plans_in_series,
    get_all_unique_tags,
    get_next_plan_in_series,
    get_previous_plan_in_series,
)
from pecha_api.plans.users.plan_users_progress_repository import get_plan_progress_by_user_id_and_plan_id, save_plan_progress
from pecha_api.plans.users.plan_users_models import UserPlanProgress
from pecha_api.routines.routines_repository import (
    get_time_blocks_containing_plan,
    get_max_display_order_in_time_block,
    add_plan_session_to_time_block,
)
from pecha_api.plans.groups.groups_repository import get_group_id_for_plan, get_group_ids_by_plan_ids
from pecha_api.plans.tags.tag_helpers import tags_to_summary_dtos
from pecha_api.plans.tags.tag_repository import get_published_tags_for_language, get_all_tags_paginated
from pecha_api.plans.tags.tag_response_models import PublicTagsListResponse
from pecha_api.plans.shared.metadata_utils import format_metadata_response

logger = logging.getLogger(__name__)

async def get_image_url(image_url: Optional[str]) -> Optional[ImageUrlModel]:
    if not image_url:
        return None
        
    thumbnail_url = image_url.replace("original", "thumbnail")
    medium_url = image_url.replace("original", "medium")
    original_url = image_url
    return ImageUrlModel(
        thumbnail=generate_presigned_access_url(bucket_name=get("AWS_BUCKET_NAME"), s3_key=thumbnail_url),
        medium=generate_presigned_access_url(bucket_name=get("AWS_BUCKET_NAME"), s3_key=medium_url),
        original=generate_presigned_access_url(bucket_name=get("AWS_BUCKET_NAME"), s3_key=original_url)
    )

async def get_published_plans(
    tag: Optional[str] = None,
    group_id: Optional[UUID] = None,
    search: Optional[str] = None, 
    language: str = "en", 
    sort_by: str = "title", 
    sort_order: str = "asc", 
    skip: int = 0, 
    limit: int = 20
    ) -> PublicPlansResponse:
    
    try:
        with SessionLocal() as db:
            language_upper = language.upper()
            plan_aggregates = get_published_plans_from_db(
                db=db,
                skip=skip,
                limit=limit,
                search=search,
                language=language_upper,
                sort_by=sort_by,
                sort_order=sort_order,
                tag=tag,
                group_id=group_id,
            )
            
            plan_ids = [plan_aggregate.plan.id for plan_aggregate in plan_aggregates]
            group_id_by_plan_id = get_group_ids_by_plan_ids(db=db, plan_ids=plan_ids)

            plan_dtos = []
            for plan_aggregate in plan_aggregates:
                plan = plan_aggregate.plan
                
                plan_image = await get_image_url(image_url=plan.image_url)
                
                author_dto = None
                if plan.author:
                    author_image = await get_image_url(image_url=plan.author.image_url)
                    author_dto = AuthorDTO(
                        id=plan.author.id, 
                        firstname=plan.author.first_name, 
                        lastname=plan.author.last_name, 
                        image=author_image 
                    )
                
                plan_dto = PublicPlanDTO(
                    id=plan.id,
                    title=plan.title,
                    description=plan.description,
                    language=plan.language.value if hasattr(plan.language, 'value') else plan.language,
                    difficulty_level=plan.difficulty_level,
                    image=plan_image,
                    total_days=plan_aggregate.total_days,
                    tags=tags_to_summary_dtos(plan.tag_list),
                    author=author_dto,
                    start_date=plan.start_date,
                    display_order=plan.display_order,
                    group_id=group_id_by_plan_id.get(plan.id),
                )
                plan_dtos.append(plan_dto)
            
            total = get_published_plans_count(
                db=db,
                search=search,
                language=language_upper,
                tag=tag,
                group_id=group_id,
            )
            
            return PublicPlansResponse(plans=plan_dtos, skip=skip, limit=limit, total=total)
    
    except Exception as e:
        logger.error(f"Error fetching published plans: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch published plans: {str(e)}"
        )


async def get_published_plan(plan_id: UUID) -> PublicPlanDTO:

    try:
        with SessionLocal() as db:
            plan = get_published_plan_by_id(db=db, plan_id=plan_id)
            
            if not plan:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.PLAN_NOT_FOUND)
            
            plan_image= await get_image_url(image_url=plan.image_url)
            
            author_dto = None
            if plan.author:
                author_image = await get_image_url(image_url=plan.author.image_url)
                author_dto = AuthorDTO(
                    id=plan.author.id, 
                    firstname=plan.author.first_name, 
                    lastname=plan.author.last_name, 
                    image=author_image
                )
            
            
            total_days = db.query(PlanItem).filter(PlanItem.plan_id == plan_id).count()
            group_id = get_group_id_for_plan(db=db, plan_id=plan.id)

            return PublicPlanDTO(
                id=plan.id,
                title=plan.title,
                description=plan.description,
                language=plan.language.value if hasattr(plan.language, 'value') else plan.language,
                difficulty_level=plan.difficulty_level,
                image=plan_image,  
                total_days=total_days,
                tags=tags_to_summary_dtos(plan.tag_list),
                author=author_dto,
                start_date=plan.start_date,
                display_order=plan.display_order,
                group_id=group_id,
            )
    
    except Exception as e:
        logger.error(f"Error fetching published plan details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch published plan details: {str(e)}"
        )

def is_user_enrolled_in_previous_plan(db, user_id: UUID, plan) -> Optional[UUID]:
    """Check if user is enrolled in the previous plan of the series. Returns previous plan ID if enrolled."""
    if not plan.series_id or plan.display_order is None:
        return None
    
    previous_plan = get_previous_plan_in_series(
        db=db, series_id=plan.series_id, current_display_order=plan.display_order
    )
    if not previous_plan:
        return None
    
    previous_enrollment = get_plan_progress_by_user_id_and_plan_id(
        db=db, user_id=user_id, plan_id=previous_plan.id
    )
    return previous_plan.id if previous_enrollment else None


def is_within_plan_date_range(db, plan) -> bool:
    """Check if current date is within the plan's valid date range."""
    if not plan.start_date:
        return False
    
    today = dt.now(timezone.utc).date()
    plan_start = plan.start_date.date() if hasattr(plan.start_date, 'date') else plan.start_date
    
    if today < plan_start:
        return False
    
    next_plan = get_next_plan_in_series(
        db=db, series_id=plan.series_id, current_display_order=plan.display_order
    )
    
    if next_plan and next_plan.start_date:
        next_plan_start = next_plan.start_date.date() if hasattr(next_plan.start_date, 'date') else next_plan.start_date
        if today >= next_plan_start:
            return False
    
    return True


def auto_enroll_plan(plan_id: UUID, user_id: Optional[UUID] = None) -> None:
    """
    Auto enroll user in a plan if all conditions are met:
    1. User is not already enrolled in this plan
    2. User is enrolled in the previous plan (within the same series)
    3. Current date is within the plan's date range (start_date <= today < next_plan.start_date)
    
    Args:
        plan_id: The plan to potentially auto-enroll the user in
        user_id: The user's ID (None if not authenticated)
    """
    if user_id is None:
        return
    
    try:
        with SessionLocal() as db:
            plan = get_published_plan_by_id(db=db, plan_id=plan_id)
            if not plan:
                return
            
            existing_enrollment = get_plan_progress_by_user_id_and_plan_id(
                db=db, user_id=user_id, plan_id=plan_id
            )
            if existing_enrollment:
                return
            
            previous_plan_id = is_user_enrolled_in_previous_plan(db, user_id, plan)
            if not previous_plan_id:
                return
            
            if not is_within_plan_date_range(db, plan):
                return
            
            new_progress = UserPlanProgress(
                user_id=user_id,
                plan_id=plan_id,
                streak_count=0,
                longest_streak=0,
                status=UserPlanStatus.NOT_STARTED,
                started_at=dt.now(timezone.utc),
                created_at=dt.now(timezone.utc),
                is_completed=False,
            )
            save_plan_progress(db=db, plan_progress=new_progress)
            logger.info(f"Auto-enrolled user {user_id} in plan {plan_id}")
            
            add_plan_to_routine_time_blocks(
                db=db,
                user_id=user_id,
                previous_plan_id=previous_plan_id,
                new_plan_id=plan_id
            )
            
    except Exception as e:
        logger.exception(f"Error during auto-enrollment for user {user_id} in plan {plan_id}: {str(e)}")


def add_plan_to_routine_time_blocks(
    db,
    user_id: UUID,
    previous_plan_id: UUID,
    new_plan_id: UUID
) -> None:
    """
    Add the new plan to all routine time blocks where the previous plan exists.
    The new plan is added after the previous plan in display_order.
    """
    try:
        time_blocks = get_time_blocks_containing_plan(
            db=db, user_id=user_id, plan_id=previous_plan_id
        )
        
        for time_block in time_blocks:
            max_order = get_max_display_order_in_time_block(db=db, time_block_id=time_block.id)
            add_plan_session_to_time_block(
                db=db,
                time_block_id=time_block.id,
                plan_id=new_plan_id,
                display_order=max_order + 1
            )
            logger.info(f"Added plan {new_plan_id} to time block {time_block.id} for user {user_id}")
            
    except Exception as e:
        logger.exception(f"Error adding plan to routine time blocks: {str(e)}")

async def get_plan_days(plan_id: UUID) -> PlanDaysResponse:
    """Get all days for a specific plan"""
    
    with SessionLocal() as db:
        plan_model = get_plan_by_id(db=db, plan_id=plan_id)
        if not plan_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorConstants.PLAN_NOT_FOUND
            )
        plan_days=get_days_by_plan_id(db=db, plan_id=plan_id)
        days_basic =[]
        for day_model in plan_days:
            day_basic = PlanDayBasic(
                id=str(day_model.id),
                day_number=day_model.day_number,
            )
            days_basic.append(day_basic)
        return PlanDaysResponse(days=days_basic)

from pecha_api.plans.audio.dto_helpers import (
    build_plan_day_audio_fields,
    build_subtask_timestamp_fields,
    generate_subtask_content_url,
)


def build_task_dto(task) -> TaskDTO:
    subtasks = []
    for subtask in sorted(task.sub_tasks, key=lambda st: st.display_order):
        start_ms, end_ms = build_subtask_timestamp_fields(subtask)
        audio_url = (
            generate_presigned_access_url(bucket_name=get("AWS_BUCKET_NAME"), s3_key=subtask.audio_url)
            if subtask.audio_url else None
        )
        subtasks.append(
            SubTaskDTO(
                id=subtask.id,
                content_type=subtask.content_type,
                duration=subtask.duration,
                content=generate_subtask_content_url(subtask.content_type, subtask.content or ""),
                image_url=subtask.content if subtask.content_type == ContentType.IMAGE else None,
                audio_url=audio_url,
                source_text_id=subtask.source_text_id,
                pecha_segment_id=subtask.pecha_segment_id,
                segment_ids=subtask.segment_ids,
                display_order=subtask.display_order,
                start_ms=start_ms,
                end_ms=end_ms,
            )
        )

    return TaskDTO(
        id=task.id,
        title=task.title,
        estimated_time=task.estimated_time,
        display_order=task.display_order,
        subtasks=subtasks,
    )


def _build_plan_day_dto(plan_item) -> PlanDayDTO:
    audio_url, audio_duration_ms, _, _ = build_plan_day_audio_fields(plan_item)
    return PlanDayDTO(
        id=plan_item.id,
        day_number=plan_item.day_number,
        tasks=[build_task_dto(task) for task in sorted(plan_item.tasks, key=lambda t: t.display_order)],
        audio_url=audio_url,
        audio_duration_ms=audio_duration_ms,
    )

def get_plan_day_details(plan_id: UUID, day_number: int) -> PlanDayDTO:
    """Get specific day's content with tasks"""

    with SessionLocal() as db:
        plan_item = get_plan_day_with_tasks_and_subtasks(db=db, plan_id=plan_id, day_number=day_number)
        return _build_plan_day_dto(plan_item)


def _filter_series_metadata_by_language(metadata_entries, language: Optional[str]):
    if not language or not metadata_entries:
        return metadata_entries or []
    language_upper = language.upper()
    return [
        entry
        for entry in metadata_entries
        if (
            entry.language.value
            if hasattr(entry.language, "value")
            else str(entry.language)
        ).upper()
        == language_upper
    ]


def _to_plan_date(value) -> DateType:
    if isinstance(value, dt):
        return value.date()
    return value


def _resolve_plan_for_date_in_series(plans: List, reference_date: DateType):
    sorted_plans = sorted(
        plans,
        key=lambda plan: (plan.display_order is None, plan.display_order or 0),
    )
    if not sorted_plans:
        return None

    for index, plan in enumerate(sorted_plans):
        if not plan.start_date:
            continue
        plan_start = _to_plan_date(plan.start_date)
        next_start = None
        if index + 1 < len(sorted_plans) and sorted_plans[index + 1].start_date:
            next_start = _to_plan_date(sorted_plans[index + 1].start_date)
        if plan_start <= reference_date and (next_start is None or reference_date < next_start):
            return plan

    for plan in sorted_plans:
        if plan.start_date:
            return plan

    return sorted_plans[0]


def _resolve_daily_plan(
    db,
    plan_id: UUID,
    requested_date: Optional[DateType],
    language: Optional[str],
):
    entry_plan = get_published_plan_by_id(db=db, plan_id=plan_id)
    if not entry_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorConstants.PLAN_NOT_FOUND,
        )

    if not entry_plan.series_id:
        return entry_plan

    plan_language = language
    if not plan_language:
        plan_language = (
            entry_plan.language.value
            if hasattr(entry_plan.language, "value")
            else str(entry_plan.language)
        )

    series_plans = get_published_plans_in_series(
        db=db,
        series_id=entry_plan.series_id,
        language=plan_language,
    )
    if not series_plans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorConstants.PLAN_NOT_FOUND,
        )

    today = dt.now(timezone.utc).date()
    reference_date = requested_date if requested_date is not None else today
    resolved_plan = _resolve_plan_for_date_in_series(series_plans, reference_date)
    if not resolved_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorConstants.PLAN_NOT_FOUND,
        )
    return resolved_plan


async def get_plan_daily_content(
    plan_id: UUID,
    requested_date: Optional[DateType] = None,
    language: Optional[str] = None,
) -> DailyPlanResponse:

    with SessionLocal() as db:
        plan = _resolve_daily_plan(
            db=db,
            plan_id=plan_id,
            requested_date=requested_date,
            language=language,
        )

        navigation_language = language
        if not navigation_language:
            navigation_language = (
                plan.language.value
                if hasattr(plan.language, "value")
                else str(plan.language)
            )

        today = dt.now(timezone.utc).date()

        if plan.start_date:
            start = _to_plan_date(plan.start_date)
        else:
            start = today

        total_days = db.query(PlanItem).filter(PlanItem.plan_id == plan.id).count()
        if total_days == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This plan has no content yet."
            )

        end = start + timedelta(days=total_days - 1)

        if requested_date is None:
            if plan.start_date:
                if start <= today <= end:
                    requested_date = today
                else:
                    requested_date = start
            else:
                requested_date = today

        day_number = (requested_date - start).days + 1

        if day_number < 1 or day_number > total_days:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No content for date {requested_date}. Plan runs from {start} to {end}."
            )

        plan_item = get_plan_day_with_tasks_and_subtasks(
            db=db, plan_id=plan.id, day_number=day_number
        )

        plan_image = await get_image_url(image_url=plan.image_url)

        series_dto = None
        if plan.series:
            series_image = await get_image_url(image_url=plan.series.image)
            metadata_entries = getattr(plan.series, "metadata_entries", None) or []
            if language:
                metadata_entries = _filter_series_metadata_by_language(
                    metadata_entries,
                    language=language,
                )
            series_metadata = [
                SeriesMetadataDTO(
                    id=entry.id,
                    title=entry.title,
                    sub_title=entry.sub_title if isinstance(entry.sub_title, str) else None,
                    description=entry.description,
                    language=entry.language.value
                    if hasattr(entry.language, "value")
                    else str(entry.language),
                )
                for entry in sorted(
                    metadata_entries,
                    key=lambda item: item.language.value
                    if hasattr(item.language, "value")
                    else str(item.language),
                )
            ]
            series_dto = SeriesDTO(
                id=plan.series.id,
                metadata=format_metadata_response(series_metadata, language=language),
                image=series_image,
            )

        previous_date = requested_date - timedelta(days=1) if day_number > 1 else None
        next_date = requested_date + timedelta(days=1) if day_number < total_days else None

        previous_plan_id = None
        next_plan_id = None

        if plan.series_id and plan.display_order is not None:
            if previous_date is None:
                previous_plan = get_previous_plan_in_series(
                    db=db,
                    series_id=plan.series_id,
                    current_display_order=plan.display_order,
                    language=navigation_language,
                )
                if previous_plan:
                    previous_plan_id = previous_plan.id

            if next_date is None:
                next_plan = get_next_plan_in_series(
                    db=db,
                    series_id=plan.series_id,
                    current_display_order=plan.display_order,
                    language=navigation_language,
                )
                if next_plan:
                    next_plan_id = next_plan.id

        audio_url, audio_duration_ms, _, _ = build_plan_day_audio_fields(plan_item)
        return DailyPlanResponse(
            plan_id=plan.id,
            plan_title=plan.title,
            plan_description=plan.description,
            image=plan_image,
            series=series_dto,
            date=requested_date,
            day_number=day_number,
            total_days=total_days,
            start_date=start,
            end_date=end,
            previous_date=previous_date,
            next_date=next_date,
            previous_plan_id=previous_plan_id,
            next_plan_id=next_plan_id,
            audio_url=audio_url,
            audio_duration_ms=audio_duration_ms,
            tasks=[build_task_dto(task) for task in sorted(plan_item.tasks, key=lambda t: t.display_order)]
        )


def get_tags(language: str = "en") -> TagsResponse:
    try:
        with SessionLocal() as db:
            language_upper = language.upper()
            tag_rows = get_published_tags_for_language(db=db, language=language_upper)
            return TagsResponse(tags=tags_to_summary_dtos(tag_rows))
    except Exception as e:
        logger.error(f"Error fetching tags: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tags: {str(e)}",
        )


def get_public_tags(
    featured: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> PublicTagsListResponse:
    try:
        with SessionLocal() as db:
            tag_rows, total = get_all_tags_paginated(
                db=db,
                featured=featured,
                search=search,
                skip=skip,
                limit=limit,
            )
            return PublicTagsListResponse(
                tags=tags_to_summary_dtos(tag_rows, preserve_order=True),
                skip=skip,
                limit=limit,
                total=total,
            )
    except Exception as e:
        logger.error(f"Error fetching public tags: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch public tags: {str(e)}",
        )
