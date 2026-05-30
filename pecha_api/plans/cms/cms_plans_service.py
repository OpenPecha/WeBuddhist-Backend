import struct
from io import BytesIO
from typing import Optional, List, Dict
from starlette import status
from pecha_api.plans.audio.tts_service import generate_tts_audio
from pecha_api.plans.audio.plan_item_audio_models import PlanItemAudio
from pecha_api.plans.audio.plan_item_audio_repository import upsert_plan_item_audio
from pecha_api.plans.audio.sub_task_timestamps_repository import upsert_sub_task_timestamp
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.users.plan_users_models import UserPlanProgress
from pecha_api.plans.cms.cms_plans_repository import save_plan, get_plan_by_id, get_plans_by_author_id, update_plan
from pecha_api.plans.groups.groups_repository import get_group_id_for_plan, get_group_ids_by_plan_ids
from pecha_api.plans.series.series_repository import get_series_by_id
from pecha_api.plans.tags.tag_helpers import tags_to_summary_dtos
from pecha_api.plans.tags.tag_repository import set_plan_tags
from pecha_api.plans.tags.tag_service import validate_tag_ids
from pecha_api.plans.items.plan_items_repository import save_plan_items, get_plan_items_by_plan_id, get_plan_day_with_tasks_and_subtasks, get_plan_day_by_id_any_plan
from pecha_api.plans.users.plan_users_progress_repository import get_plan_progress
from pecha_api.plans.authors.plan_authors_model import Author
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.plans_enums import LanguageCode, PlanStatus, ContentType, PlanAudioType
from pecha_api.plans.plans_response_models import PlansResponse, PlanDTO, CreatePlanRequest, TaskDTO, PlanDayDTO, \
    PlanWithDays, UpdatePlanRequest, PlanStatusUpdate, PlansRepositoryResponse, PlanWithAggregates, AuthorDTO, SubTaskDTO
    
from pecha_api.plans.tasks.plan_tasks_repository import get_tasks_by_item_ids
from pecha_api.plans.tasks.plan_tasks_models import PlanTask
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_repository import get_sub_task_by_subtask_id
from sqlalchemy.orm import Session

from pecha_api.db.database import SessionLocal
from pecha_api.config import get
from pecha_api.uploads.S3_utils import generate_presigned_access_url, upload_bytes
from uuid import uuid4, UUID
from fastapi import HTTPException
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST, PLAN_NOT_FOUND, FORBIDDEN, UNAUTHORIZED_PLAN_DELETE, PLAN_AUTHOR_MISMATCH, PLAN_MUST_HAVE_AT_LEAST_ONE_DAY_WITH_CONTENT_TO_BE_PUBLISHED, PLAN_START_DATE_UPDATE_NOT_ALLOWED_FOR_PUBLISHED_WITH_SUBSCRIBERS
from datetime import datetime, timezone
from sqlalchemy import func

DUMMY_PLANS = [
    PlanDTO(
        id=uuid4(),
        title="Introduction to Buddhist Meditation",
        description="A 7-day beginner's guide to Buddhist meditation practices",
        language="en",
        image_url="https://example.com/meditation.jpg",
        total_days=7,
        status=PlanStatus.PUBLISHED,
        subscription_count=150
    ),
    PlanDTO(
        id=uuid4(),
        title="The Four Noble Truths Study",
        description="Deep dive into the foundational teachings of Buddhism",
        language="en",
        image_url="https://example.com/four-truths.jpg",
        total_days=14,
        status=PlanStatus.PUBLISHED,
        subscription_count=89
    ),
    PlanDTO(
        id=uuid4(),
        title="Mindfulness in Daily Life",
        description="Practical applications of mindfulness for modern living",
        language="en",
        image_url="https://example.com/mindfulness.jpg",
        total_days=21,
        status=PlanStatus.DRAFT,
        subscription_count=0    
    )
]
DUMMY_TASKS = [
    TaskDTO(
        id=uuid4(),
        title="Morning Breathing Exercise",
        estimated_time=15,
        display_order=1
    ),
    TaskDTO(
        id=uuid4(),
        title="Listen to Dharma Talk",
        estimated_time=30,
        display_order=2
    )
]

DUMMY_DAYS = [
    PlanDayDTO(
        id=uuid4(),
        day_number=1,
        title="Day 1: Beginning the Journey",
        tasks=DUMMY_TASKS
    ),
    PlanDayDTO(
        id=uuid4(),
        day_number=2,
        title="Day 2: Deepening Practice",
        tasks=[DUMMY_TASKS[0]]
    )
]

def _generate_audio_segments(
    tasks, audio_type: PlanAudioType
) -> tuple[List[bytes], list]:
    wav_header_size = 44
    audio_segments: List[bytes] = []
    subtask_refs = []
    allowed_types = {ContentType.TEXT, ContentType.SOURCE_REFERENCE}
    for task in tasks:
        subtask = task.sub_tasks[0] if task.sub_tasks else None
        if not subtask:
            continue
        if subtask.content_type not in allowed_types:
            continue
        wav_bytes = generate_tts_audio(subtask.content, audio_type)
        raw_pcm = wav_bytes[wav_header_size:]
        audio_segments.append(raw_pcm)
        subtask_refs.append(subtask)
    return audio_segments, subtask_refs


def _update_subtask_timestamps(
    db: Session,
    audio_segments: List[bytes],
    subtask_refs: list,
    sample_rate: int,
    bytes_per_sample: int,
) -> int:
    current_offset_ms = 0
    for i, raw_pcm in enumerate(audio_segments):
        segment_samples = len(raw_pcm) // bytes_per_sample
        segment_duration_ms = int((segment_samples / sample_rate) * 1000)
        upsert_sub_task_timestamp(
            db=db,
            sub_task_id=subtask_refs[i].id,
            start_ms=current_offset_ms,
            end_ms=current_offset_ms + segment_duration_ms,
            created_by="system",
        )
        current_offset_ms += segment_duration_ms
    return current_offset_ms


def _build_combined_wav(audio_segments: List[bytes]) -> tuple[bytes, int]:
    sample_rate = 24000
    bits_per_sample = 16
    num_channels = 1
    bytes_per_sample = bits_per_sample // 8

    combined_pcm = b"".join(audio_segments)
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    data_size = len(combined_pcm)
    chunk_size = 36 + data_size

    wav_header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", chunk_size, b"WAVE",
        b"fmt ", 16, 1, num_channels,
        sample_rate, byte_rate, block_align, bits_per_sample,
        b"data", data_size,
    )
    return wav_header + combined_pcm, data_size


def _upload_and_persist_audio(
    db: Session,
    combined_wav: bytes,
    duration_ms: int,
    plan_id: UUID,
    plan_item_id: UUID,
) -> PlanItemAudio:
    s3_key = f"audio/plan_days/{plan_id}/{plan_item_id}/{uuid4()}.wav"
    upload_bytes(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=s3_key,
        file=BytesIO(combined_wav),
        content_type="audio/wav",
    )
    return upsert_plan_item_audio(
        db=db,
        plan_item_audio=PlanItemAudio(
            plan_item_id=plan_item_id,
            audio_key=s3_key,
            duration_ms=duration_ms,
            mime_type="audio/wav",
            file_size_bytes=len(combined_wav),
            created_by="system",
        ),
    )


async def generate_plan_audio_service(
    language: str,
    day_id: Optional[UUID] = None,
    sub_task_id: Optional[UUID] = None,
    audio_type: PlanAudioType = PlanAudioType.TEXT_READING,
):
    if sub_task_id:
        return await _generate_subtask_audio(sub_task_id=sub_task_id, audio_type=audio_type)

    SAMPLE_RATE = 24000
    BYTES_PER_SAMPLE = 2

    with SessionLocal() as db:
        plan_item: PlanItem = get_plan_day_by_id_any_plan(db=db, day_id=day_id)

        audio_segments, subtask_refs = _generate_audio_segments(plan_item.tasks, audio_type)
        if not audio_segments:
            return []

        duration_ms = _update_subtask_timestamps(
            db=db,
            audio_segments=audio_segments,
            subtask_refs=subtask_refs,
            sample_rate=SAMPLE_RATE,
            bytes_per_sample=BYTES_PER_SAMPLE,
        )

        combined_wav, _ = _build_combined_wav(audio_segments)

        audio_row = _upload_and_persist_audio(
            db=db,
            combined_wav=combined_wav,
            duration_ms=duration_ms,
            plan_id=plan_item.plan_id,
            plan_item_id=plan_item.id,
        )

    audio_url = generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=audio_row.audio_key,
    )

    return {
        "audio_url": audio_url,
        "audio_duration_ms": audio_row.duration_ms,
        "s3_key": audio_row.audio_key,
    }


async def _generate_subtask_audio(sub_task_id: UUID, audio_type: PlanAudioType):
    SAMPLE_RATE = 24000
    BYTES_PER_SAMPLE = 2
    WAV_HEADER_SIZE = 44

    with SessionLocal() as db:
        subtask: PlanSubTask = get_sub_task_by_subtask_id(db=db, id=sub_task_id)
        if not subtask:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=BAD_REQUEST, message="Sub task not found").model_dump(),
            )

        allowed_types = {ContentType.TEXT, ContentType.SOURCE_REFERENCE}
        if subtask.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ResponseError(
                    error=BAD_REQUEST,
                    message="Sub task content type must be TEXT or SOURCE_REFERENCE for audio generation",
                ).model_dump(),
            )

        wav_bytes = generate_tts_audio(subtask.content, audio_type)
        raw_pcm = wav_bytes[WAV_HEADER_SIZE:]

        segment_samples = len(raw_pcm) // BYTES_PER_SAMPLE
        duration_ms = int((segment_samples / SAMPLE_RATE) * 1000)

        combined_wav, _ = _build_combined_wav([raw_pcm])

        s3_key = f"audio/plan_subtasks/{subtask.task_id}/{sub_task_id}/{uuid4()}.wav"
        upload_bytes(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=s3_key,
            file=BytesIO(combined_wav),
            content_type="audio/wav",
        )

        subtask.audio_url = s3_key
        subtask.duration = str(duration_ms)
        db.commit()

        upsert_sub_task_timestamp(
            db=db,
            sub_task_id=sub_task_id,
            start_ms=0,
            end_ms=duration_ms,
            created_by="system",
        )

    audio_url = generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=s3_key,
    )

    return {
        "audio_url": audio_url,
        "audio_duration_ms": duration_ms,
        "s3_key": s3_key,
    }

async def get_filtered_plans(token: str, search: Optional[str], sort_by: str, sort_order: str, skip: int, limit: int, tag: Optional[str] = None, language: Optional[str] = None) -> PlansResponse:
    # Validate token and author context (authorization can be extended later)
    current_author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db_session:
        plan_repository_response : PlansRepositoryResponse = get_plans_by_author_id(
            db=db_session,
            author_id=current_author.id,
            is_admin=current_author.is_admin,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            skip=skip,
            limit=limit,
            tag=tag,
            language=language,
        )

        plans: List[PlanDTO] = []
        plan_ids = [plan_info.plan.id for plan_info in plan_repository_response.plan_info]
        group_id_by_plan_id = get_group_ids_by_plan_ids(db=db_session, plan_ids=plan_ids)

        for plan_info in plan_repository_response.plan_info:
            plan_info: PlanWithAggregates
            selected_plan = plan_info.plan

            plans.append(
                PlanDTO(
                    id=selected_plan.id,
                    title=selected_plan.title,
                    description=selected_plan.description,
                    language=selected_plan.language.value if selected_plan.language and hasattr(selected_plan.language, 'value') else (selected_plan.language or 'EN'),
                    difficulty_level=selected_plan.difficulty_level,
                    image_url= generate_presigned_access_url(bucket_name=get("AWS_BUCKET_NAME"), s3_key=selected_plan.image_url),
                    plan_image_url=selected_plan.image_url,
                    total_days=int(plan_info.total_days or 0),
                    tags=tags_to_summary_dtos(selected_plan.tag_list),
                    status=PlanStatus(selected_plan.status.value),
                    featured=selected_plan.featured,
                    subscription_count=int(plan_info.subscription_count or 0),
                    author=AuthorDTO(
                        id=selected_plan.author_id,
                        firstname=selected_plan.author.first_name,
                        lastname=selected_plan.author.last_name,
                        image_url=(
                            generate_presigned_access_url(
                                bucket_name=get("AWS_BUCKET_NAME"),
                                s3_key=selected_plan.author.image_url
                            )
                        )
                    ),
                    series_id=selected_plan.series_id,
                    display_order=selected_plan.display_order,
                    group_id=group_id_by_plan_id.get(selected_plan.id),
                )
            )

        return PlansResponse(plans=plans, skip=skip, limit=limit, total=plan_repository_response.total)


def _get_next_display_order_in_series(db: Session, series_id: UUID) -> int:
    result = db.query(func.max(Plan.display_order)).filter(
        Plan.series_id == series_id,
        Plan.deleted_at.is_(None),
    ).scalar()
    return 0 if result is None else result + 1


def _validate_series_for_plan_attachment(
    db: Session,
    series_id: UUID,
    author_id: UUID,
    is_admin: bool,
) -> None:
    series = get_series_by_id(db=db, series_id=series_id)
    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Series with id '{series_id}' not found",
        )
    if not is_admin and series.author_id != author_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to attach plans to this series",
        )


def _apply_series_attachment_to_plan(
    db: Session,
    plan: Plan,
    series_id: UUID,
    author_id: UUID,
    is_admin: bool,
    display_order: Optional[int] = None,
) -> None:
    if plan.series_id is not None and plan.series_id != series_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan is already attached to another series",
        )
    _validate_series_for_plan_attachment(db, series_id, author_id, is_admin)
    plan.series_id = series_id
    plan.display_order = (
        display_order
        if display_order is not None
        else _get_next_display_order_in_series(db, series_id)
    )


def _detach_plan_from_series(plan: Plan) -> None:
    plan.series_id = None
    plan.display_order = None


def _apply_create_plan_series_fields(
    db: Session,
    plan: Plan,
    create_plan_request: CreatePlanRequest,
    author_id: UUID,
    is_admin: bool,
) -> None:
    if not create_plan_request.series_id:
        return
    _apply_series_attachment_to_plan(
        db=db,
        plan=plan,
        series_id=create_plan_request.series_id,
        author_id=author_id,
        is_admin=is_admin,
        display_order=create_plan_request.display_order,
    )


def create_new_plan(token: str, create_plan_request: CreatePlanRequest) -> PlanDTO:

    current_author = validate_and_extract_author_details(token=token)

    language = create_plan_request.language.upper() if create_plan_request.language else get("SITE_LANGUAGE").upper()

    new_plan_model = Plan(
        title=create_plan_request.title,
        description=create_plan_request.description,
        image_url=create_plan_request.image_url,
        start_date=create_plan_request.start_date,
        author_id=current_author.id,
        difficulty_level=create_plan_request.difficulty_level,
        status=PlanStatus.DRAFT,
        featured=False,
        language=LanguageCode(language),
        created_by=current_author.email
    )

    # Save to database
    with SessionLocal() as db_session:
        if create_plan_request.tag_ids:
            validate_tag_ids(db=db_session, tag_ids=create_plan_request.tag_ids)
        _apply_create_plan_series_fields(
            db=db_session,
            plan=new_plan_model,
            create_plan_request=create_plan_request,
            author_id=current_author.id,
            is_admin=bool(current_author.is_admin),
        )
        saved_plan = save_plan(db=db_session, plan=new_plan_model)
        if create_plan_request.tag_ids:
            set_plan_tags(db=db_session, plan=saved_plan, tag_ids=create_plan_request.tag_ids)
            db_session.refresh(saved_plan)

        new_item_models = [
            PlanItem(
                plan_id=saved_plan.id,
                day_number=day,
                created_by=current_author.email
            )
            for day in range(1, create_plan_request.total_days + 1)
        ]

        saved_items = save_plan_items(db=db_session, plan_items=new_item_models)
        plan_progress = get_plan_progress(db=db_session, plan_id=saved_plan.id)

        total_subscription_count = len(plan_progress)
        total_days = len(saved_items)

        group_id = get_group_id_for_plan(db=db_session, plan_id=saved_plan.id)

        return PlanDTO(
            id=saved_plan.id,
            title=saved_plan.title,
            description=saved_plan.description,
            language=saved_plan.language.value if hasattr(saved_plan.language, 'value') else saved_plan.language,
            difficulty_level=saved_plan.difficulty_level,
            image_url=saved_plan.image_url,
            image_key=saved_plan.image_url,
            total_days=total_days,
            tags=tags_to_summary_dtos(saved_plan.tag_list),
            status=saved_plan.status,
            subscription_count=total_subscription_count,
            start_date=saved_plan.start_date,
            series_id=saved_plan.series_id,
            display_order=saved_plan.display_order,
            group_id=group_id,
        )

async def get_details_plan(token:str,plan_id: UUID) -> PlanWithDays:
    validate_and_extract_author_details(token=token)
    with SessionLocal() as db_session:
        return _get_plan_details(db_session, plan_id)


def _get_plan_details(db: Session, plan_id: UUID) -> PlanWithDays:
    # Fetch base plan
    plan: Plan = _check_author_plan_availability(plan_id=plan_id)

    # Fetch items (days)
    items = get_plan_items_by_plan_id(db=db, plan_id=plan.id)
    plan_item_ids = [item.id for item in items]

    # Fetch tasks for all items in one query
    tasks = get_tasks_by_item_ids(db=db, plan_item_ids=plan_item_ids)
    tasks_by_item: Dict[UUID, List[PlanTask]] = {}
    for task in tasks:
        tasks_by_item.setdefault(task.plan_item_id, []).append(task)

    from pecha_api.plans.audio.plan_item_audio_repository import get_plan_item_audio_by_plan_item_ids

    audio_by_item = {
        row.plan_item_id: row
        for row in get_plan_item_audio_by_plan_item_ids(db=db, plan_item_ids=plan_item_ids)
    }

    day_dtos: List[PlanDayDTO] = []
    for item in items:
        audio_row = audio_by_item.get(item.id)
        audio_url = None
        audio_duration_ms = None
        has_audio = False
        if audio_row:
            has_audio = True
            audio_url = generate_presigned_access_url(
                bucket_name=get("AWS_BUCKET_NAME"),
                s3_key=audio_row.audio_key,
            )
            audio_duration_ms = audio_row.duration_ms
        day_dtos.append(
            PlanDayDTO(
                id=item.id,
                day_number=item.day_number,
                audio_url=audio_url,
                audio_duration_ms=audio_duration_ms,
                has_audio=has_audio,
                tasks=[
                    TaskDTO(
                        id=task.id,
                        title=task.title,
                        estimated_time=task.estimated_time,
                        display_order=task.display_order,
                    )
                    for task in tasks_by_item.get(item.id, [])
                ],
            )
        )

    group_id = get_group_id_for_plan(db=db, plan_id=plan.id)

    return PlanWithDays(
        id=plan.id,
        title=plan.title,
        description=plan.description or "",
        language=plan.language or "EN",
        image_url=generate_presigned_access_url(bucket_name=get("AWS_BUCKET_NAME"), s3_key=plan.image_url),
        plan_image_url=plan.image_url, 
        total_days=len(items),
        difficulty_level=plan.difficulty_level,
        tags=tags_to_summary_dtos(plan.tag_list),
        status=plan.status,
        days=day_dtos,
        start_date=plan.start_date,
        series_id=plan.series_id,
        display_order=plan.display_order,
        group_id=group_id,
    )
    
def _get_subscription_count(db: Session, plan_id: UUID) -> int:
    return db.query(func.count(func.distinct(UserPlanProgress.user_id))).filter(
        UserPlanProgress.plan_id == plan_id
    ).scalar() or 0


def _validate_start_date_update(db: Session, plan: Plan, plan_id: UUID):
    subscription_count = _get_subscription_count(db, plan_id)
    if plan.status == PlanStatus.PUBLISHED and subscription_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(
                error=BAD_REQUEST,
                message=PLAN_START_DATE_UPDATE_NOT_ALLOWED_FOR_PUBLISHED_WITH_SUBSCRIBERS,
            ).model_dump(),
        )


def _apply_plan_field_updates(plan: Plan, update_plan_request: UpdatePlanRequest):
    field_mappings = [
        ('title', 'title'),
        ('description', 'description'),
        ('difficulty_level', 'difficulty_level'),
        ('image_url', 'image_url'),
        ('language', 'language'),
    ]
    for request_field, plan_field in field_mappings:
        value = getattr(update_plan_request, request_field, None)
        if value is not None:
            setattr(plan, plan_field, value)


def _generate_plan_image_url(plan_image_key: Optional[str]) -> Optional[str]:
    if not plan_image_key:
        return None
    try:
        bucket_name = get("AWS_BUCKET_NAME")
        return generate_presigned_access_url(bucket_name, plan_image_key)
    except Exception:
        return plan_image_key


async def update_plan_details(token: str, plan_id: UUID, update_plan_request: UpdatePlanRequest) -> PlanDTO:
    author_details = validate_and_extract_author_details(token=token)
    
    with SessionLocal() as db:
        plan = _check_author_plan_availability(plan_id=plan_id, author_id=author_details.id, is_admin=author_details.is_admin)

        if "start_date" in update_plan_request.model_fields_set:
            _validate_start_date_update(db, plan, plan_id)
            plan.start_date = update_plan_request.start_date
        
        _apply_plan_field_updates(plan, update_plan_request)

        if update_plan_request.tag_ids is not None:
            validate_tag_ids(db=db, tag_ids=update_plan_request.tag_ids)
            set_plan_tags(db=db, plan=plan, tag_ids=update_plan_request.tag_ids)

        if "series_id" in update_plan_request.model_fields_set:
            if update_plan_request.series_id is None:
                _detach_plan_from_series(plan)
            else:
                _apply_series_attachment_to_plan(
                    db=db,
                    plan=plan,
                    series_id=update_plan_request.series_id,
                    author_id=author_details.id,
                    is_admin=bool(author_details.is_admin),
                    display_order=update_plan_request.display_order,
                )
        elif (
            "display_order" in update_plan_request.model_fields_set
            and update_plan_request.display_order is not None
            and plan.series_id is not None
        ):
            plan.display_order = update_plan_request.display_order
        
        plan.updated_at = datetime.now(timezone.utc)
        plan.updated_by = author_details.email
        plan = update_plan(db, plan)
        
        plan_image_key = plan.image_url
        image_url = _generate_plan_image_url(plan_image_key)
        total_days = len(get_plan_items_by_plan_id(db, plan_id))
        subscription_count = _get_subscription_count(db, plan_id)
        
        return PlanDTO(
            id=plan.id,
            title=plan.title,
            description=plan.description or "",
            language=plan.language.value if hasattr(plan.language, 'value') else str(plan.language),
            difficulty_level=plan.difficulty_level,
            image_url=image_url,
            image_key=plan_image_key,
            total_days=total_days,
            tags=tags_to_summary_dtos(plan.tag_list),
            status=plan.status,
            subscription_count=subscription_count,
            start_date=plan.start_date,
            series_id=plan.series_id,
            display_order=plan.display_order,
            group_id=get_group_id_for_plan(db=db, plan_id=plan.id),
        )

async def update_selected_plan_status(token:str,plan_id: UUID, plan_status_update: PlanStatusUpdate) -> PlanDTO:
    
   current_author = validate_and_extract_author_details(token=token)

   with SessionLocal() as db:

        plan = _check_author_plan_availability(plan_id=plan_id, author_id=current_author.id, is_admin=current_author.is_admin)
        _check_published_plan_day_availability(plan_id=plan_id, plan_status=plan_status_update.status)

        plan.status = plan_status_update.status
        plan = update_plan(db=db, plan=plan)
        return PlanDTO(
            id=plan.id,
            title=plan.title,
            description=plan.description or "",
            language=plan.language,
            difficulty_level=plan.difficulty_level,
            image_url=plan.image_url,
            plan_image_url=plan.image_url,
            total_days=len(get_plan_items_by_plan_id(db=db, plan_id=plan_id)),
            tags=tags_to_summary_dtos(plan.tag_list),
            status=plan.status,
            subscription_count=len(get_plan_progress(db=db, plan_id=plan.id)),
            series_id=plan.series_id,
            display_order=plan.display_order,
            group_id=get_group_id_for_plan(db=db, plan_id=plan.id),
        )

async def delete_selected_plan(token:str,plan_id: UUID):
    current_author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        plan = _check_author_plan_availability(plan_id=plan_id, author_id=current_author.id, is_admin=current_author.is_admin)
        _soft_delete_plan_by_id(db=db, plan_id=plan.id, author=current_author)
        return

def _get_task_subtasks_dto(subtasks: List[PlanSubTask]) -> List[SubTaskDTO]:
    from pecha_api.plans.audio.dto_helpers import build_subtask_timestamp_fields

    subtasks_dto = []
    for subtask in subtasks:
        start_ms, end_ms = build_subtask_timestamp_fields(subtask)
        audio_url = (
            generate_presigned_access_url(bucket_name=get("AWS_BUCKET_NAME"), s3_key=subtask.audio_url)
            if subtask.audio_url else None
        )
        subtasks_dto.append(
            SubTaskDTO(
                id=subtask.id,
                content_type=subtask.content_type,
                content=subtask.content,
                display_order=subtask.display_order,
                start_ms=start_ms,
                end_ms=end_ms,
                audio_url=audio_url,
            )
        )
    return subtasks_dto

async def get_plan_day_details(token:str,plan_id: UUID, day_number: int) -> PlanDayDTO:
    validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        plan_item: PlanItem = get_plan_day_with_tasks_and_subtasks(db=db, plan_id=plan_id, day_number=day_number)
        from pecha_api.plans.audio.dto_helpers import build_plan_day_audio_fields

        audio_url, audio_duration_ms, audio_key, has_audio = build_plan_day_audio_fields(plan_item)
        plan_day_dto: PlanDayDTO = PlanDayDTO(
            id=plan_item.id,
            day_number=plan_item.day_number,
            audio_url=audio_url,
            audio_duration_ms=audio_duration_ms,
            audio_key=audio_key,
            has_audio=has_audio,
            tasks=[
                TaskDTO(
                    id=task.id,
                    title=task.title,
                    estimated_time=task.estimated_time,
                    display_order=task.display_order,
                    subtasks=_get_task_subtasks_dto(task.sub_tasks)
                )
                for task in plan_item.tasks
            ]
        )
        return plan_day_dto

def _soft_delete_plan_by_id(db: Session, plan_id: UUID, author: Author):
    plan = get_plan_by_id(db=db, plan_id=plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ResponseError(error=BAD_REQUEST, message=PLAN_NOT_FOUND).model_dump())
    plan.deleted_at = datetime.now(timezone.utc)
    plan.deleted_by = author.email
    plan = update_plan(db=db, plan=plan)


def _check_author_plan_availability(plan_id: UUID, author_id: Optional[UUID] = None, is_admin: bool = False) -> Plan:
    with SessionLocal() as db:
        plan = get_plan_by_id(db=db, plan_id=plan_id)
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ResponseError(error=BAD_REQUEST, message=PLAN_NOT_FOUND).model_dump())
        if not is_admin and author_id and plan.author_id != author_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ResponseError(error=BAD_REQUEST, message=PLAN_AUTHOR_MISMATCH).model_dump())
        return plan

def _check_published_plan_day_availability(plan_id: UUID, plan_status: PlanStatus):
    with SessionLocal() as db:
        if plan_status == PlanStatus.PUBLISHED and len(get_plan_items_by_plan_id(db=db, plan_id=plan_id)) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ResponseError(error=BAD_REQUEST, message=PLAN_MUST_HAVE_AT_LEAST_ONE_DAY_WITH_CONTENT_TO_BE_PUBLISHED).model_dump())
        return

def update_plan_featured_service(token:str, plan_id: UUID):
    current_author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        plan = _check_author_plan_availability(plan_id=plan_id, author_id=current_author.id, is_admin=current_author.is_admin)
        plan.featured = not plan.featured
        plan = update_plan(db=db, plan=plan)