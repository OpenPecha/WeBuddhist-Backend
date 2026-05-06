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
from pecha_api.plans.public.plan_response_models import (
    PublicPlansResponse, 
    PublicPlanDTO, 
    PlanDayDTO, 
    AuthorDTO,
    PlanDaysResponse, 
    PlanDayBasic, 
    SubTaskDTO, 
    TaskDTO, 
    ImageUrlModel, 
    TagsResponse, 
    DailyPlanResponse, 
    SeriesDTO,
    SeriesProgressResponse,
    PlanProgressDTO
)
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.plans_enums import ContentType
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.plans.public.plan_repository import (
    get_published_plans_from_db, 
    get_published_plans_count, 
    get_published_plan_by_id, 
    get_all_unique_tags,
    get_published_plans_by_series_id,
    get_series_by_id
)

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
            plan_aggregates = get_published_plans_from_db(db=db, skip=skip, limit=limit, search=search, language=language_upper, sort_by=sort_by, sort_order=sort_order, tag=tag)
            
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
                    tags=plan.tags if plan.tags else [],
                    author=author_dto
                )
                plan_dtos.append(plan_dto)
            
            total = get_published_plans_count(db=db, search=search, language=language_upper, tag=tag)
            
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

            return PublicPlanDTO(
                id=plan.id,
                title=plan.title,
                description=plan.description,
                language=plan.language.value if hasattr(plan.language, 'value') else plan.language,
                difficulty_level=plan.difficulty_level,
                image=plan_image,  
                total_days=total_days,
                tags=plan.tags if plan.tags else [],
                author=author_dto,
                start_date=plan.start_date
            )
    
    except Exception as e:
        logger.error(f"Error fetching published plan details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch published plan details: {str(e)}"
        )


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

def generate_subtask_content_url(content_type: ContentType, content: str) -> str:
    if content_type == ContentType.IMAGE:
        return generate_presigned_access_url(bucket_name=get("AWS_BUCKET_NAME"), s3_key=content)
    return content


def build_task_dto(task) -> TaskDTO:
    subtasks = [
        SubTaskDTO(
            id=subtask.id,
            content_type=subtask.content_type,
            duration=subtask.duration,
            content=generate_subtask_content_url(subtask.content_type, subtask.content),
            image_url=subtask.content if subtask.content_type == ContentType.IMAGE else None,
            source_text_id=subtask.source_text_id,
            pecha_segment_id=subtask.pecha_segment_id,
            segment_ids=subtask.segment_ids,
            display_order=subtask.display_order,
        )
        for subtask in sorted(task.sub_tasks, key=lambda st: st.display_order)
    ]

    return TaskDTO(
        id=task.id,
        title=task.title,
        estimated_time=task.estimated_time,
        display_order=task.display_order,
        subtasks=subtasks,
    )

def get_plan_day_details(plan_id: UUID, day_number: int) -> PlanDayDTO:
    """Get specific day's content with tasks"""

    with SessionLocal() as db:
        plan_item = get_plan_day_with_tasks_and_subtasks(db=db, plan_id=plan_id, day_number=day_number)
        return PlanDayDTO(
            id=plan_item.id,
            day_number=plan_item.day_number,
            tasks=[build_task_dto(task) for task in sorted(plan_item.tasks, key=lambda t: t.display_order)]
        )


async def get_plan_daily_content(plan_id: UUID, requested_date: Optional[DateType] = None) -> DailyPlanResponse:
    with SessionLocal() as db:
        plan = get_published_plan_by_id(db=db, plan_id=plan_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorConstants.PLAN_NOT_FOUND
            )

        today = dt.now(timezone.utc).date()

        if plan.start_date:
            start = plan.start_date.date() if isinstance(plan.start_date, dt) else plan.start_date
        else:
            start = today

        total_days = db.query(PlanItem).filter(PlanItem.plan_id == plan_id).count()
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
            db=db, plan_id=plan_id, day_number=day_number
        )

        plan_image = await get_image_url(image_url=plan.image_url)

        series_dto = None
        if plan.series:
            series_image = await get_image_url(image_url=plan.series.image)
            series_dto = SeriesDTO(
                id=plan.series.id,
                name=plan.series.name,
                image=series_image,
            )

        previous_date = requested_date - timedelta(days=1) if day_number > 1 else None
        next_date = requested_date + timedelta(days=1) if day_number < total_days else None

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
            tasks=[build_task_dto(task) for task in sorted(plan_item.tasks, key=lambda t: t.display_order)]
        )


def get_tags(language: str = "en") -> TagsResponse:
    try:
        with SessionLocal() as db:
            language_upper = language.upper()
            tags = get_all_unique_tags(db=db, language=language_upper)
            return TagsResponse(tags=tags)
    except Exception as e:
        logger.error(f"Error fetching tags: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch tags: {str(e)}",
        )


async def get_series_progress(series_id: UUID) -> SeriesProgressResponse:
    try:
        with SessionLocal() as db:
            series = get_series_by_id(db=db, series_id=series_id)
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Series not found"
                )
            
            plans_with_days = get_published_plans_by_series_id(db=db, series_id=series_id)
            
            if not plans_with_days:
                series_image = await get_image_url(image_url=series.image)
                return SeriesProgressResponse(
                    series_id=series.id,
                    series_name=series.name,
                    series_image=series_image,
                    total_plans=0,
                    total_series_days=0,
                    current_plan_index=None,
                    current_plan_id=None,
                    current_day_in_plan=None,
                    days_completed_in_series=0,
                    progress_percentage=0.0,
                    series_start_date=None,
                    series_end_date=None,
                    is_before_series=False,
                    is_after_series=False,
                    plans=[]
                )
            
            today = dt.now(timezone.utc).date()
            plan_progress_list: list[PlanProgressDTO] = []
            total_series_days = 0
            current_start_date = None
            
            for idx, (plan, total_days) in enumerate(plans_with_days):
                if plan.start_date:
                    plan_start = plan.start_date.date() if isinstance(plan.start_date, dt) else plan.start_date
                else:
                    plan_start = current_start_date if current_start_date else today
                
                plan_end = plan_start + timedelta(days=total_days - 1) if total_days > 0 else plan_start
                
                plan_progress_list.append(PlanProgressDTO(
                    plan_id=plan.id,
                    plan_title=plan.title,
                    plan_index=idx,
                    total_days=total_days,
                    start_date=plan_start,
                    end_date=plan_end
                ))
                
                total_series_days += total_days
                current_start_date = plan_end + timedelta(days=1)
            
            series_start_date = plan_progress_list[0].start_date if plan_progress_list else None
            series_end_date = plan_progress_list[-1].end_date if plan_progress_list else None
            
            current_plan_index = None
            current_plan_id = None
            current_day_in_plan = None
            days_completed_in_series = 0
            is_before_series = False
            is_after_series = False
            
            if series_start_date and today < series_start_date:
                is_before_series = True
                days_completed_in_series = 0
            elif series_end_date and today > series_end_date:
                is_after_series = True
                days_completed_in_series = total_series_days
            else:
                cumulative_days = 0
                for plan_dto in plan_progress_list:
                    if plan_dto.start_date <= today <= plan_dto.end_date:
                        current_plan_index = plan_dto.plan_index
                        current_plan_id = plan_dto.plan_id
                        current_day_in_plan = (today - plan_dto.start_date).days + 1
                        days_completed_in_series = cumulative_days + current_day_in_plan
                        break
                    cumulative_days += plan_dto.total_days
            
            progress_percentage = (days_completed_in_series / total_series_days * 100) if total_series_days > 0 else 0.0
            
            series_image = await get_image_url(image_url=series.image)
            
            return SeriesProgressResponse(
                series_id=series.id,
                series_name=series.name,
                series_image=series_image,
                total_plans=len(plan_progress_list),
                total_series_days=total_series_days,
                current_plan_index=current_plan_index,
                current_plan_id=current_plan_id,
                current_day_in_plan=current_day_in_plan,
                days_completed_in_series=days_completed_in_series,
                progress_percentage=round(progress_percentage, 2),
                series_start_date=series_start_date,
                series_end_date=series_end_date,
                is_before_series=is_before_series,
                is_after_series=is_after_series,
                plans=plan_progress_list
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching series progress: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch series progress: {str(e)}"
        )
