from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from starlette import status
from typing import List, Dict, Optional
from uuid import UUID

from pecha_api.config import TIME_FORMAT_PATTERN, get
from pecha_api.plans.authors.plan_authors_service import safe_get_image_url
from pecha_api.plans.media.media_response_models import ImageUrlModel
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.db.database import SessionLocal
from pecha_api.users.users_service import validate_and_extract_user_details
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST
from pecha_api.texts.texts_models import Text
from pecha_api.plans.users.plan_users_models import UserPlanProgress
from pecha_api.plans.users.recitation_collection.recitation_collection_models import RecitationCollection
from pecha_api.plans.plans_enums import UserPlanStatus
from datetime import datetime, timezone
from pecha_api.plans.users.plan_users_progress_repository import (
    get_plan_progress_by_user_id_and_plan_ids,
)
from pecha_api.plans.shared.metadata_utils import filter_by_language_with_fallback
from pecha_api.timezone_utils import normalize_timezone_name
from pecha_api.accumulator.accumulator_models import Accumulator
from pecha_api.accumulator.accumulator_enums import AccumulatorType
from pecha_api.accumulator.accumulator_service import resolve_mala_image_fields

from .routines_models import Routine, RoutineTimeBlock, RoutineSession
from .routines_enums import SessionType
from .routines_repository import (
    get_routine_by_user_id,
    get_routine_by_id_and_user,
    get_existing_collection_source_ids,
    get_existing_collection_source_ids_in_routine,
    get_collection_source_ids_by_time_block_id,
    time_block_exists_for_routine,
    get_time_block_by_id_and_routine,
    get_plan_source_ids_by_time_block_id,
    get_series_source_ids_by_time_block_id,
    get_plans_by_ids,
    get_time_block_by_routine_and_time,
    delete_sessions_by_time_block_id,
    save_routine,
    save_time_block,
    save_sessions,
    soft_delete_time_block,
    update_time_block as update_time_block_repo,
    get_time_blocks,
    get_sessions_by_time_block_ids,
    get_routine_series_and_recitation_counts,
)
from .response_message import (
    DUPLICATE_PLAN,
    DUPLICATE_SERIES,
    DUPLICATE_RECITATION_COLLECTION,
    DUPLICATE_ACCUMULATOR,
    INVALID_TIME_FORMAT,
    INVALID_TIMER_DURATION,
    ROUTINE_ALREADY_EXISTS,
    ROUTINE_NOT_FOUND,
    SESSIONS_REQUIRED,
    SOURCE_ID_REQUIRED,
    TIME_ALREADY_EXISTS,
    TIME_BLOCK_NOT_FOUND,
    TIME_BLOCK_TIME_CONFLICT,
    NO_ROUTINE_CREATED_FOR_USER,
    SERIES_NOT_FOUND,
    PRESET_ACCUMULATOR_NOT_FOUND,
    ACCUMULATOR_ID_REQUIRED,
)
from .routines_response_models import (
    SessionRequest,
    CreateTimeBlockRequest,
    UpdateTimeBlockRequest,
    SessionDTO,
    TimeBlockDTO,
    RoutineWithTimeBlocksResponse,
    RoutineResponse,
    RoutineInfoResponse,
)


def _validate_time_block_request(request: CreateTimeBlockRequest) -> None:
    # At least one session required
    if not request.sessions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=SESSIONS_REQUIRED
            ).model_dump(),
        )

    # Time must be valid HH:MM 24-hour format
    if not TIME_FORMAT_PATTERN.match(request.time):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=INVALID_TIME_FORMAT
            ).model_dump(),
        )

    # TIMER sessions carry a positive duration_ms; PLAN/SERIES/RECITATION carry a source_id
    for session in request.sessions:
        if session.session_type == SessionType.TIMER:
            if session.duration_ms is None or session.duration_ms <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=ResponseError(
                        error=BAD_REQUEST, message=INVALID_TIMER_DURATION
                    ).model_dump(),
                )
        elif session.session_type == SessionType.ACCUMULATOR:
            if session.source_id is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=ResponseError(
                        error=BAD_REQUEST, message=ACCUMULATOR_ID_REQUIRED
                    ).model_dump(),
                )
        elif session.source_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ResponseError(
                    error=BAD_REQUEST, message=SOURCE_ID_REQUIRED
            ).model_dump(),
        )

    _validate_session_uniqueness(request.sessions)


def _validate_session_uniqueness(sessions: List[SessionRequest]) -> None:
    plan_source_ids = [
        session.source_id
        for session in sessions
        if session.session_type == SessionType.PLAN
    ]
    if len(plan_source_ids) != len(set(plan_source_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=DUPLICATE_PLAN
            ).model_dump(),
        )

    series_source_ids = [
        session.source_id
        for session in sessions
        if session.session_type == SessionType.SERIES
    ]
    if len(series_source_ids) != len(set(series_source_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=DUPLICATE_SERIES
            ).model_dump(),
        )

    collection_source_ids = [
        session.source_id
        for session in sessions
        if session.session_type == SessionType.RECITATION_COLLECTION
    ]
    if len(collection_source_ids) != len(set(collection_source_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=DUPLICATE_RECITATION_COLLECTION
            ).model_dump(),
        )

    accumulator_source_ids = [
        session.source_id
        for session in sessions
        if session.session_type == SessionType.ACCUMULATOR
    ]
    if len(accumulator_source_ids) != len(set(accumulator_source_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=DUPLICATE_ACCUMULATOR
            ).model_dump(),
        )


def _check_duplicate_collections(db, routine_id: UUID, sessions: List) -> None:
    """Check for duplicate recitation collections when adding a new time block."""
    existing_collection_ids = get_existing_collection_source_ids(db=db, routine_id=routine_id)
    new_collection_ids = [s.source_id for s in sessions if s.session_type == SessionType.RECITATION_COLLECTION]
    overlap = set(new_collection_ids) & set(existing_collection_ids)
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=DUPLICATE_RECITATION_COLLECTION
            ).model_dump(),
        )


def _check_duplicate_collections_on_update(
    db, routine_id: UUID, time_block_id: UUID, sessions: List
) -> None:
    """Check for duplicate recitation collections when updating a time block."""
    existing_collection_ids = get_existing_collection_source_ids_in_routine(
        db=db, routine_id=routine_id, exclude_time_block_id=time_block_id
    )
    new_collection_ids = [s.source_id for s in sessions if s.session_type == SessionType.RECITATION_COLLECTION]
    overlap = set(new_collection_ids) & set(existing_collection_ids)
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=DUPLICATE_RECITATION_COLLECTION
            ).model_dump(),
        )


def _check_duplicate_time(db, routine_id: UUID, time: str) -> None:
    if time_block_exists_for_routine(db=db, routine_id=routine_id, time=time):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(
                error=BAD_REQUEST, message=TIME_ALREADY_EXISTS
            ).model_dump(),
        )


def _extract_plan_ids(sessions: List) -> List[UUID]:
    return [s.source_id for s in sessions if s.session_type == SessionType.PLAN]


def _extract_series_ids(sessions: List) -> List[UUID]:
    return [s.source_id for s in sessions if s.session_type == SessionType.SERIES]


def _normalize_plan_sessions_to_series(db, sessions: List[SessionRequest]) -> List[SessionRequest]:
    plan_ids = [
        session.source_id
        for session in sessions
        if session.session_type == SessionType.PLAN and session.source_id is not None
    ]
    if not plan_ids:
        return sessions

    plans = get_plans_by_ids(db=db, plan_ids=plan_ids)
    plan_series_map = {
        plan.id: plan.series_id
        for plan in plans
        if getattr(plan, "series_id", None) is not None
    }
    if not plan_series_map:
        return sessions

    normalized: List[SessionRequest] = []
    for session in sessions:
        if (
            session.session_type == SessionType.PLAN
            and session.source_id in plan_series_map
        ):
            normalized.append(
                SessionRequest(
                    session_type=SessionType.SERIES,
                    source_id=plan_series_map[session.source_id],
                    display_order=session.display_order,
                )
            )
        else:
            normalized.append(session)
    return normalized


def _validate_accumulators(db, sessions: List[SessionRequest]) -> None:
    preset_ids = [
        session.source_id
        for session in sessions
        if session.session_type == SessionType.ACCUMULATOR and session.source_id is not None
    ]
    if not preset_ids:
        return

    found_ids = {
        row.id
        for row in db.query(Accumulator.id)
        .filter(
            Accumulator.id.in_(preset_ids),
            Accumulator.type == AccumulatorType.PRESET,
            Accumulator.deleted_at.is_(None),
        )
        .all()
    }
    if set(preset_ids) - found_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(
                error=BAD_REQUEST, message=PRESET_ACCUMULATOR_NOT_FOUND
            ).model_dump(),
        )


def _prepare_sessions(db, sessions: List[SessionRequest]) -> List[SessionRequest]:
    sessions = _normalize_plan_sessions_to_series(db=db, sessions=sessions)
    _validate_session_uniqueness(sessions)
    _validate_accumulators(db=db, sessions=sessions)
    return sessions


def _enroll_plans(db, user_id: UUID, plan_ids: List[UUID]) -> None:
    if not plan_ids:
        return

    already_enrolled = {
        row.plan_id
        for row in db.query(UserPlanProgress.plan_id)
        .filter(
            UserPlanProgress.user_id == user_id,
            UserPlanProgress.plan_id.in_(plan_ids),
        )
        .all()
    }

    for plan_id in plan_ids:
        if plan_id not in already_enrolled:
            new_progress = UserPlanProgress(
                user_id=user_id,
                plan_id=plan_id,
                streak_count=0,
                longest_streak=0,
                status=UserPlanStatus.NOT_STARTED,
                is_completed=False,
            )
            db.add(new_progress)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()


def _enroll_series(db, user_id: UUID, series_ids: List[UUID]) -> None:
    if not series_ids:
        return

    from pecha_api.plans.plans_enums import SeriesStatus
    from pecha_api.plans.series.series_model import Series
    from pecha_api.plans.users.plan_users_models import UserSeriesEnrollment
    from pecha_api.plans.users.plan_user_series_repository import (
        get_user_series_enrollment_by_user_and_series,
        save_user_series_enrollment,
        get_first_plan_in_series,
    )
    from pecha_api.plans.users.plan_users_service import auto_enroll_in_next_plan

    for series_id in series_ids:
        series = (
            db.query(Series)
            .filter(Series.id == series_id, Series.deleted_at.is_(None))
            .first()
        )
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(
                    error=BAD_REQUEST, message=SERIES_NOT_FOUND
                ).model_dump(),
            )

        existing_enrollment = get_user_series_enrollment_by_user_and_series(
            db=db, user_id=user_id, series_id=series_id
        )
        if existing_enrollment:
            continue

        first_plan = get_first_plan_in_series(db=db, series_id=series_id)
        enrollment = UserSeriesEnrollment(
            user_id=user_id,
            series_id=series_id,
            status=SeriesStatus.ACTIVE,
            auto_enroll_next=True,
            current_plan_id=first_plan.id if first_plan else None,
            enrolled_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            is_completed=False,
        )
        save_user_series_enrollment(db=db, enrollment=enrollment)

        if first_plan:
            auto_enroll_in_next_plan(
                db=db,
                user_id=user_id,
                plan_id=first_plan.id,
                series_enrollment_id=enrollment.id,
            )


def _enroll_new_sessions_on_update(
    db, user_id: UUID, time_block_id: UUID, new_sessions: List
) -> None:
    old_plan_ids = set(
        get_plan_source_ids_by_time_block_id(db=db, time_block_id=time_block_id)
    )
    new_plan_ids = set(_extract_plan_ids(new_sessions))
    _enroll_plans(db=db, user_id=user_id, plan_ids=list(new_plan_ids - old_plan_ids))

    old_series_ids = set(
        get_series_source_ids_by_time_block_id(db=db, time_block_id=time_block_id)
    )
    new_series_ids = set(_extract_series_ids(new_sessions))
    _enroll_series(db=db, user_id=user_id, series_ids=list(new_series_ids - old_series_ids))


def _validate_and_sync_update(
    db,
    user_id: UUID,
    routine_id: UUID,
    time_block_id: UUID,
    time: str,
    sessions: List[SessionRequest],
) -> None:
    existing_time_block = get_time_block_by_routine_and_time(
        db=db,
        routine_id=routine_id,
        time=time,
        exclude_time_block_id=time_block_id,
    )
    if existing_time_block:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(
                error=BAD_REQUEST, message=TIME_BLOCK_TIME_CONFLICT
            ).model_dump(),
        )

    _check_duplicate_collections_on_update(
        db=db,
        routine_id=routine_id,
        time_block_id=time_block_id,
        sessions=sessions,
    )

    _enroll_new_sessions_on_update(
        db=db,
        user_id=user_id,
        time_block_id=time_block_id,
        new_sessions=sessions,
    )


def build_session_models(time_block_id: UUID, sessions: List) -> List[RoutineSession]:
    return [
        RoutineSession(
            time_block_id=time_block_id,
            session_type=session.session_type,
            source_id=None if session.session_type == SessionType.TIMER else session.source_id,
            duration_ms=session.duration_ms if session.session_type == SessionType.TIMER else None,
            display_order=session.display_order,
        )
        for session in sessions
    ]


def _resolve_plan_sessions(db, plan_sessions: List[RoutineSession], user_id: UUID) -> List[SessionDTO]:
    if not plan_sessions:
        return []

    plan_ids = [session.source_id for session in plan_sessions]
    plans = get_plans_by_ids(db=db, plan_ids=plan_ids)
    plan_map = {plan.id: plan for plan in plans}
    
    # Fetch user progress data for all plan sessions
    progress_map = get_plan_progress_by_user_id_and_plan_ids(
        db=db, user_id=user_id, plan_ids=plan_ids
    )
    
    resolved = []
    for session in plan_sessions:
        plan = plan_map.get(session.source_id)
        if plan is None:
            continue

        plan_image = safe_get_image_url(
            plan.image_url, resource_id=plan.id, resource_type="plan"
        )
        
        # Get user progress for this plan
        progress = progress_map.get(session.source_id)
        
        resolved.append(
            SessionDTO(
                id=session.id,
                session_type=session.session_type,
                source_id=session.source_id,
                title=plan.title,
                language=(
                    plan.language.value
                    if hasattr(plan.language, "value")
                    else str(plan.language)
                ),
                image=plan_image,
                display_order=session.display_order,
                start_date=plan.start_date,  # Plan's start_date
                started_at=progress.started_at if progress else None,  # User's started_at
            )
        )
    return resolved


async def _resolve_recitation_sessions(
    recitation_sessions: List[RoutineSession],
) -> List[SessionDTO]:
    if not recitation_sessions:
        return []

    text_ids = [str(session.source_id) for session in recitation_sessions]
    texts = await Text.get_texts_by_ids(text_ids)
    text_map = {str(text.id): text for text in texts}

    resolved = []
    for session in recitation_sessions:
        text = text_map.get(str(session.source_id))
        if text is None:
            continue
        resolved.append(
            SessionDTO(
                id=session.id,
                session_type=session.session_type,
                source_id=session.source_id,
                title=text.title,
                language=text.language or "en",
                image=None,
                display_order=session.display_order,
            )
        )
    return resolved


def _resolve_timer_sessions(timer_sessions: List[RoutineSession]) -> List[SessionDTO]:
    return [
        SessionDTO(
            id=session.id,
            session_type=session.session_type,
            source_id=None,
            duration_ms=session.duration_ms,
            display_order=session.display_order,
        )
        for session in timer_sessions
    ]


def _resolve_recitation_collection_sessions(
    db, collection_sessions: List[RoutineSession], user_id: UUID
) -> List[SessionDTO]:
    """Resolve recitation collection sessions by fetching collection details."""
    if not collection_sessions:
        return []

    collection_ids = [session.source_id for session in collection_sessions]
    
    # Fetch collections owned by the user
    collections = (
        db.query(RecitationCollection)
        .filter(
            RecitationCollection.id.in_(collection_ids),
            RecitationCollection.user_id == user_id,
        )
        .all()
    )
    collection_map = {collection.id: collection for collection in collections}
    
    # Get item counts for each collection
    from sqlalchemy import func
    from pecha_api.plans.users.recitation_collection.recitation_collection_models import RecitationCollectionItem
    
    item_counts = dict(
        db.query(
            RecitationCollectionItem.recitation_collection_id,
            func.count(RecitationCollectionItem.id)
        )
        .filter(RecitationCollectionItem.recitation_collection_id.in_(collection_ids))
        .group_by(RecitationCollectionItem.recitation_collection_id)
        .all()
    )

    resolved = []
    for session in collection_sessions:
        collection = collection_map.get(session.source_id)
        if collection is None:
            continue
        
        # Generate presigned URL for collection image
        collection_image = safe_get_image_url(
            collection.img_url, resource_id=collection.id, resource_type="collection"
        )
        
        resolved.append(
            SessionDTO(
                id=session.id,
                session_type=session.session_type,
                source_id=session.source_id,
                title=collection.name,
                image=collection_image,
                display_order=session.display_order,
                item_count=item_counts.get(collection.id, 0),
            )
        )
    return resolved


def _accumulator_metadata_language(metadata) -> Optional[str]:
    if metadata is None:
        return None
    return (
        metadata.language.value
        if hasattr(metadata.language, "value")
        else str(metadata.language)
    )


def _select_accumulator_metadata(metadata_entries, language: Optional[str]):
    if not metadata_entries:
        return None
    matched = filter_by_language_with_fallback(
        entries=list(metadata_entries),
        language=language,
        language_of=_accumulator_metadata_language,
    )
    return matched[0] if matched else metadata_entries[0]


def _accumulator_mala_image(accumulator: Accumulator) -> Optional[ImageUrlModel]:
    _, mala_image_url = resolve_mala_image_fields(accumulator)
    if not mala_image_url:
        return None
    return ImageUrlModel(
        thumbnail=mala_image_url,
        medium=mala_image_url,
        original=mala_image_url,
    )


def _resolve_accumulator_sessions(
    db,
    accumulator_sessions: List[RoutineSession],
    user_id: UUID,
    language: Optional[str] = None,
) -> List[SessionDTO]:
    if not accumulator_sessions:
        return []

    preset_ids = [session.source_id for session in accumulator_sessions]
    presets = (
        db.query(Accumulator)
        .filter(
            Accumulator.id.in_(preset_ids),
            Accumulator.type == AccumulatorType.PRESET,
            Accumulator.deleted_at.is_(None),
        )
        .all()
    )
    preset_map = {preset.id: preset for preset in presets}

    resolved = []
    for session in accumulator_sessions:
        preset = preset_map.get(session.source_id)
        if preset is None:
            continue

        metadata = _select_accumulator_metadata(
            preset.metadata_entries, language
        )
        resolved.append(
            SessionDTO(
                id=session.id,
                session_type=session.session_type,
                source_id=session.source_id,
                accumulator_id=session.source_id,
                title=metadata.name if metadata else "Untitled",
                language=_accumulator_metadata_language(metadata),
                image=_accumulator_mala_image(preset),
                display_order=session.display_order,
            )
        )
    return resolved


def _series_metadata_language(metadata) -> Optional[str]:
    if metadata is None:
        return None
    return (
        metadata.language.value
        if hasattr(metadata.language, "value")
        else str(metadata.language)
    )


def _select_series_metadata(metadata_entries, language: Optional[str]):
    """Pick the metadata entry for ``language``, falling back to 'en', then first."""
    if not metadata_entries:
        return None
    matched = filter_by_language_with_fallback(
        entries=list(metadata_entries),
        language=language,
        language_of=_series_metadata_language,
    )
    return matched[0] if matched else metadata_entries[0]


def _plan_language(plan) -> str:
    return (
        plan.language.value
        if hasattr(plan.language, "value")
        else str(plan.language)
    )


def _filter_plans_by_language(plans: List, language: Optional[str]) -> List:
    if not plans:
        return []
    return filter_by_language_with_fallback(
        entries=list(plans),
        language=language,
        language_of=_plan_language,
    )


def _build_series_session_dto(
    session, series, first_plan, progress, current_plan, language: Optional[str] = None
) -> SessionDTO:
    metadata = _select_series_metadata(series.metadata_entries, language)
    series_image = safe_get_image_url(
        series.image, resource_id=series.id, resource_type="series"
    )
    return SessionDTO(
        id=session.id,
        session_type=session.session_type,
        source_id=session.source_id,
        title=metadata.title if metadata else "Untitled Series",
        language=_series_metadata_language(metadata),
        image=series_image,
        display_order=session.display_order,
        start_date=first_plan.start_date if first_plan else None,  # First plan's start_date
        started_at=progress.started_at if progress else None,  # User's started_at for first plan
        current_plan_id=current_plan.id if current_plan else None,
        current_plan_title=current_plan.title if current_plan else None,
    )


def _resolve_series_sessions(
    db, series_sessions: List[RoutineSession], user_id: UUID, language: Optional[str] = None
) -> List[SessionDTO]:
    if not series_sessions:
        return []

    from pecha_api.plans.public.plan_service import _resolve_plan_for_date_in_series
    from pecha_api.plans.series.series_repository import get_series_by_ids
    from pecha_api.plans.users.plan_user_series_repository import get_plans_by_series_ids

    series_ids = [session.source_id for session in series_sessions]
    series_list = get_series_by_ids(db=db, series_ids=series_ids)
    series_map = {series.id: series for series in series_list}

    plans_by_series = get_plans_by_series_ids(db=db, series_ids=series_ids)
    today = datetime.now(timezone.utc).date()
    language_plans_by_series = {
        series_id: _filter_plans_by_language(plans, language)
        for series_id, plans in plans_by_series.items()
    }
    current_plan_map = {
        series_id: _resolve_plan_for_date_in_series(language_plans, today)
        for series_id, language_plans in language_plans_by_series.items()
    }
    first_plan_map = {
        series_id: language_plans[0] if language_plans else None
        for series_id, language_plans in language_plans_by_series.items()
    }
    first_plan_ids = [plan.id for plan in first_plan_map.values() if plan is not None]
    progress_map = get_plan_progress_by_user_id_and_plan_ids(
        db=db, user_id=user_id, plan_ids=first_plan_ids
    )

    resolved = []
    for session in series_sessions:
        series = series_map.get(session.source_id)
        if series is None:
            continue

        first_plan = first_plan_map.get(session.source_id)
        progress = progress_map.get(first_plan.id) if first_plan else None
        current_plan = current_plan_map.get(session.source_id)
        resolved.append(
            _build_series_session_dto(
                session, series, first_plan, progress, current_plan, language=language
            )
        )
    return resolved


async def _resolve_sessions(db, sessions: List[RoutineSession], user_id: UUID, language: Optional[str] = None) -> List[SessionDTO]:
    plan_sessions = [
        session for session in sessions if session.session_type == SessionType.PLAN
    ]
    series_sessions = [
        session for session in sessions if session.session_type == SessionType.SERIES
    ]
    recitation_sessions = [
        session
        for session in sessions
        if session.session_type == SessionType.RECITATION
    ]
    recitation_collection_sessions = [
        session
        for session in sessions
        if session.session_type == SessionType.RECITATION_COLLECTION
    ]
    timer_sessions = [
        session for session in sessions if session.session_type == SessionType.TIMER
    ]
    accumulator_sessions = [
        session
        for session in sessions
        if session.session_type == SessionType.ACCUMULATOR
    ]

    resolved_plans = _resolve_plan_sessions(db=db, plan_sessions=plan_sessions, user_id=user_id)
    resolved_series = _resolve_series_sessions(db=db, series_sessions=series_sessions, user_id=user_id, language=language)
    resolved_recitations = await _resolve_recitation_sessions(
        recitation_sessions=recitation_sessions
    )
    resolved_collections = _resolve_recitation_collection_sessions(
        db=db, collection_sessions=recitation_collection_sessions, user_id=user_id
    )
    resolved_timers = _resolve_timer_sessions(timer_sessions=timer_sessions)
    resolved_accumulators = _resolve_accumulator_sessions(
        db=db,
        accumulator_sessions=accumulator_sessions,
        user_id=user_id,
        language=language,
    )

    resolved = (
        resolved_plans
        + resolved_series
        + resolved_recitations
        + resolved_collections
        + resolved_timers
        + resolved_accumulators
    )
    resolved.sort(key=lambda session: session.display_order)

    return resolved


def group_sessions_by_block(
    sessions: List[RoutineSession],
) -> Dict[UUID, List[RoutineSession]]:
    sessions_by_block: Dict[UUID, List[RoutineSession]] = {}
    for session in sessions:
        if session.time_block_id not in sessions_by_block:
            sessions_by_block[session.time_block_id] = []
        sessions_by_block[session.time_block_id].append(session)
    return sessions_by_block


async def build_time_block_dto(
    db, time_block: RoutineTimeBlock, sessions: List[RoutineSession], user_id: UUID, language: Optional[str] = None
) -> TimeBlockDTO:
    resolved_sessions = await _resolve_sessions(db=db, sessions=sessions, user_id=user_id, language=language)
    return TimeBlockDTO(
        id=time_block.id,
        time=time_block.time,
        time_int=time_block.time_int,
        notification_enabled=time_block.notification_enabled,
        sessions=resolved_sessions,
    )


async def create_routine_with_time_block(
    token: str, request: CreateTimeBlockRequest, timezone_name: Optional[str] = None
) -> RoutineWithTimeBlocksResponse:

    current_user = validate_and_extract_user_details(token=token)

    _validate_time_block_request(request)
    timezone_name = normalize_timezone_name(timezone_name)

    with SessionLocal() as db:
        prepared_sessions = _prepare_sessions(db=db, sessions=request.sessions)

        # Check routine doesn't already exist (business rule: exclude soft-deleted)
        existing_routine = get_routine_by_user_id(
            db=db, user_id=current_user.id, include_deleted=False
        )
        if existing_routine:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ResponseError(
                    error=BAD_REQUEST, message=ROUTINE_ALREADY_EXISTS
                ).model_dump(),
            )

        # Create routine
        routine = Routine(user_id=current_user.id, timezone=timezone_name)
        saved_routine = save_routine(db=db, routine=routine)

        # Create time block
        time_block = RoutineTimeBlock(
            routine_id=saved_routine.id,
            time=request.time,
            time_int=request.time_int,
            notification_enabled=request.notification_enabled,
        )
        saved_time_block = save_time_block(db=db, time_block=time_block)

        session_models = build_session_models(
            time_block_id=saved_time_block.id, sessions=prepared_sessions
        )
        saved_sessions = save_sessions(db=db, sessions=session_models)

        _enroll_plans(
            db=db, user_id=current_user.id, plan_ids=_extract_plan_ids(prepared_sessions)
        )
        _enroll_series(
            db=db, user_id=current_user.id, series_ids=_extract_series_ids(prepared_sessions)
        )

        time_block_dto = await build_time_block_dto(
            db=db, time_block=saved_time_block, sessions=saved_sessions, user_id=current_user.id
        )

        return RoutineWithTimeBlocksResponse(
            id=saved_routine.id,
            time_blocks=[time_block_dto],
        )


async def get_user_routine(
    token: str, skip: int = 0, limit: int = 20, language: Optional[str] = None
) -> RoutineResponse:

    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        routine = get_routine_by_user_id(
            db=db, user_id=current_user.id, include_deleted=False
        )

        if routine is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ResponseError(
                    error=BAD_REQUEST, message=NO_ROUTINE_CREATED_FOR_USER
                ).model_dump(),
            )

        time_blocks, total = get_time_blocks(
            db=db,
            routine_id=routine.id,
            include_deleted=False,
            order_by_field=RoutineTimeBlock.time_int,
            order_desc=False,
            skip=skip,
            limit=limit,
        )

        if not time_blocks:
            return RoutineResponse(
                id=routine.id, time_blocks=[], skip=skip, limit=limit, total=total
            )

        time_block_ids = [tb.id for tb in time_blocks]
        all_sessions = get_sessions_by_time_block_ids(
            db=db,
            time_block_ids=time_block_ids,
            order_by_field=RoutineSession.display_order,
            order_desc=False,
        )
        sessions_by_block = group_sessions_by_block(all_sessions)

        time_block_dtos = [
            await build_time_block_dto(
                db=db, time_block=tb, sessions=sessions_by_block.get(tb.id, []), user_id=current_user.id, language=language
            )
            for tb in time_blocks
        ]

        return RoutineResponse(
            id=routine.id,
            time_blocks=time_block_dtos,
            skip=skip,
            limit=limit,
            total=total,
        )


async def get_user_routine_info(token: str) -> RoutineInfoResponse:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        routine = get_routine_by_user_id(
            db=db, user_id=current_user.id, include_deleted=False
        )

        if routine is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ResponseError(
                    error=BAD_REQUEST, message=NO_ROUTINE_CREATED_FOR_USER
                ).model_dump(),
            )

        series_count, recitation_count = get_routine_series_and_recitation_counts(
            db=db, routine_id=routine.id
        )

        return RoutineInfoResponse(
            series_count=series_count,
            recitation_count=recitation_count,
        )


async def add_time_block_to_routine(
    token: str, routine_id: UUID, request: CreateTimeBlockRequest, timezone_name: Optional[str] = None
) -> TimeBlockDTO:

    current_user = validate_and_extract_user_details(token=token)

    _validate_time_block_request(request)
    timezone_name = normalize_timezone_name(timezone_name)

    with SessionLocal() as db:
        # Check routine exists and belongs to user
        routine = get_routine_by_id_and_user(
            db=db, routine_id=routine_id, user_id=current_user.id
        )
        if not routine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(
                    error=BAD_REQUEST, message=ROUTINE_NOT_FOUND
                ).model_dump(),
            )

        # Refresh the routine's stored timezone when the header is provided
        if timezone_name is not None:
            routine.timezone = timezone_name

        _check_duplicate_collections(db=db, routine_id=routine_id, sessions=request.sessions)
        _check_duplicate_time(db=db, routine_id=routine_id, time=request.time)

        prepared_sessions = _prepare_sessions(db=db, sessions=request.sessions)

        # Save time block
        time_block = RoutineTimeBlock(
            routine_id=routine_id,
            time=request.time,
            time_int=request.time_int,
            notification_enabled=request.notification_enabled,
        )
        saved_time_block = save_time_block(db=db, time_block=time_block)

        session_models = build_session_models(
            time_block_id=saved_time_block.id, sessions=prepared_sessions
        )
        saved_sessions = save_sessions(db=db, sessions=session_models)

        _enroll_plans(
            db=db, user_id=current_user.id, plan_ids=_extract_plan_ids(prepared_sessions)
        )
        _enroll_series(
            db=db, user_id=current_user.id, series_ids=_extract_series_ids(prepared_sessions)
        )

        resolved_sessions = await _resolve_sessions(db=db, sessions=saved_sessions, user_id=current_user.id)

        return TimeBlockDTO(
            id=saved_time_block.id,
            time=saved_time_block.time,
            time_int=saved_time_block.time_int,
            notification_enabled=saved_time_block.notification_enabled,
            sessions=resolved_sessions,
        )


def delete_time_block(token: str, routine_id: UUID, time_block_id: UUID) -> None:

    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        routine = get_routine_by_id_and_user(
            db=db, routine_id=routine_id, user_id=current_user.id
        )
        if not routine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(
                    error=BAD_REQUEST, message=ROUTINE_NOT_FOUND
                ).model_dump(),
            )

        # Find the time block
        time_block = get_time_block_by_id_and_routine(
            db=db, time_block_id=time_block_id, routine_id=routine_id
        )
        if not time_block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(
                    error=BAD_REQUEST, message=TIME_BLOCK_NOT_FOUND
                ).model_dump(),
            )

        soft_delete_time_block(db=db, time_block=time_block)


async def update_time_block_service(
    token: str, routine_id: UUID, time_block_id: UUID, request: UpdateTimeBlockRequest
) -> TimeBlockDTO:

    current_user = validate_and_extract_user_details(token=token)

    _validate_time_block_request(request)

    with SessionLocal() as db:
        routine = get_routine_by_id_and_user(
            db=db, routine_id=routine_id, user_id=current_user.id
        )
        if not routine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(
                    error=BAD_REQUEST, message=ROUTINE_NOT_FOUND
                ).model_dump(),
            )

        time_block = get_time_block_by_id_and_routine(
            db=db, time_block_id=time_block_id, routine_id=routine_id
        )
        if not time_block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(
                    error=BAD_REQUEST, message=TIME_BLOCK_NOT_FOUND
                ).model_dump(),
            )

        prepared_sessions = _prepare_sessions(db=db, sessions=request.sessions)

        _validate_and_sync_update(
            db=db,
            user_id=current_user.id,
            routine_id=routine_id,
            time_block_id=time_block_id,
            time=request.time,
            sessions=prepared_sessions,
        )

        delete_sessions_by_time_block_id(db=db, time_block_id=time_block_id)

        updated_time_block = update_time_block_repo(
            db=db,
            time_block=time_block,
            time=request.time,
            time_int=request.time_int,
            notification_enabled=request.notification_enabled,
        )

        session_models = build_session_models(
            time_block_id=updated_time_block.id, sessions=prepared_sessions
        )
        saved_sessions = save_sessions(db=db, sessions=session_models)

        resolved_sessions = await _resolve_sessions(db=db, sessions=saved_sessions, user_id=current_user.id)

        return TimeBlockDTO(
            id=updated_time_block.id,
            time=updated_time_block.time,
            time_int=updated_time_block.time_int,
            notification_enabled=updated_time_block.notification_enabled,
            sessions=resolved_sessions,
        )
