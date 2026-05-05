from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from starlette import status
from typing import List, Dict
from uuid import UUID

from pecha_api.config import TIME_FORMAT_PATTERN, get
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.db.database import SessionLocal
from pecha_api.users.users_service import validate_and_extract_user_details
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST
from pecha_api.texts.texts_models import Text
from pecha_api.plans.users.plan_users_models import UserPlanProgress
from pecha_api.plans.plans_enums import UserPlanStatus
from pecha_api.plans.users.plan_users_progress_repository import (
    delete_user_plan_progress,
)

from .routines_models import Routine, RoutineTimeBlock, RoutineSession
from .routines_enums import SessionType
from .routines_repository import (
    get_routine_by_user_id,
    get_routine_by_id_and_user,
    get_existing_plan_source_ids,
    get_existing_plan_source_ids_in_routine,
    time_block_exists_for_routine,
    get_time_block_by_id_and_routine,
    get_plan_source_ids_by_time_block_id,
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
)
from .response_message import (
    DUPLICATE_PLAN,
    INVALID_TIME_FORMAT,
    ROUTINE_ALREADY_EXISTS,
    ROUTINE_NOT_FOUND,
    SESSIONS_REQUIRED,
    TIME_ALREADY_EXISTS,
    TIME_BLOCK_NOT_FOUND,
    TIME_BLOCK_TIME_CONFLICT,
    NO_ROUTINE_CREATED_FOR_USER,
)
from .routines_response_models import (
    CreateTimeBlockRequest,
    UpdateTimeBlockRequest,
    SessionDTO,
    TimeBlockDTO,
    RoutineWithTimeBlocksResponse,
    RoutineResponse,
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

    # Duplicate plan source_ids within the request
    plan_source_ids = [
        session.source_id
        for session in request.sessions
        if session.session_type == SessionType.PLAN
    ]
    if len(plan_source_ids) != len(set(plan_source_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=DUPLICATE_PLAN
            ).model_dump(),
        )


def _check_duplicate_plans(db, routine_id: UUID, sessions: List) -> None:
    existing_plan_ids = get_existing_plan_source_ids(db=db, routine_id=routine_id)
    new_plan_ids = [s.source_id for s in sessions if s.session_type == SessionType.PLAN]
    overlap = set(new_plan_ids) & set(existing_plan_ids)
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=DUPLICATE_PLAN
            ).model_dump(),
        )


def _check_duplicate_plans_on_update(
    db, routine_id: UUID, time_block_id: UUID, sessions: List
) -> None:
    existing_plan_ids = get_existing_plan_source_ids_in_routine(
        db=db, routine_id=routine_id, exclude_time_block_id=time_block_id
    )
    new_plan_ids = [s.source_id for s in sessions if s.session_type == SessionType.PLAN]
    overlap = set(new_plan_ids) & set(existing_plan_ids)
    if overlap:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=DUPLICATE_PLAN
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


def _unenroll_plans(db, user_id: UUID, plan_ids: List[UUID]) -> None:
    if not plan_ids:
        return

    for plan_id in plan_ids:
        try:
            delete_user_plan_progress(db=db, user_id=user_id, plan_id=plan_id)
        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                continue
            raise


def _sync_plan_enrollments_on_update(
    db, user_id: UUID, time_block_id: UUID, new_sessions: List
) -> None:
    old_plan_ids = set(
        get_plan_source_ids_by_time_block_id(db=db, time_block_id=time_block_id)
    )
    new_plan_ids = set(_extract_plan_ids(new_sessions))

    added_plans = list(new_plan_ids - old_plan_ids)
    removed_plans = list(old_plan_ids - new_plan_ids)

    _enroll_plans(db=db, user_id=user_id, plan_ids=added_plans)
    _unenroll_plans(db=db, user_id=user_id, plan_ids=removed_plans)


def _validate_and_sync_update(
    db,
    user_id: UUID,
    routine_id: UUID,
    time_block_id: UUID,
    request: UpdateTimeBlockRequest,
) -> None:
    existing_time_block = get_time_block_by_routine_and_time(
        db=db,
        routine_id=routine_id,
        time=request.time,
        exclude_time_block_id=time_block_id,
    )
    if existing_time_block:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(
                error=BAD_REQUEST, message=TIME_BLOCK_TIME_CONFLICT
            ).model_dump(),
        )

    _check_duplicate_plans_on_update(
        db=db,
        routine_id=routine_id,
        time_block_id=time_block_id,
        sessions=request.sessions,
    )

    _sync_plan_enrollments_on_update(
        db=db,
        user_id=user_id,
        time_block_id=time_block_id,
        new_sessions=request.sessions,
    )


def build_session_models(time_block_id: UUID, sessions: List) -> List[RoutineSession]:
    return [
        RoutineSession(
            time_block_id=time_block_id,
            session_type=session.session_type,
            source_id=session.source_id,
            display_order=session.display_order,
        )
        for session in sessions
    ]


def _resolve_plan_sessions(db, plan_sessions: List[RoutineSession]) -> List[SessionDTO]:
    if not plan_sessions:
        return []

    plan_ids = [session.source_id for session in plan_sessions]
    plans = get_plans_by_ids(db=db, plan_ids=plan_ids)
    plan_map = {plan.id: plan for plan in plans}
    bucket_name = get("AWS_BUCKET_NAME")

    resolved = []
    for session in plan_sessions:
        plan = plan_map.get(session.source_id)
        if plan is None:
            continue

        image_url = ""
        if plan.image_url:
            try:
                image_url = generate_presigned_access_url(
                    bucket_name=bucket_name, s3_key=plan.image_url
                )
            except Exception:
                image_url = ""

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
                image_url=image_url,
                display_order=session.display_order,
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
                image_url=None,
                display_order=session.display_order,
            )
        )
    return resolved


async def _resolve_sessions(db, sessions: List[RoutineSession]) -> List[SessionDTO]:
    plan_sessions = [
        session for session in sessions if session.session_type == SessionType.PLAN
    ]
    recitation_sessions = [
        session
        for session in sessions
        if session.session_type == SessionType.RECITATION
    ]

    resolved_plans = _resolve_plan_sessions(db=db, plan_sessions=plan_sessions)
    resolved_recitations = await _resolve_recitation_sessions(
        recitation_sessions=recitation_sessions
    )

    resolved = resolved_plans + resolved_recitations
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
    db, time_block: RoutineTimeBlock, sessions: List[RoutineSession]
) -> TimeBlockDTO:
    resolved_sessions = await _resolve_sessions(db=db, sessions=sessions)
    return TimeBlockDTO(
        id=time_block.id,
        time=time_block.time,
        time_int=time_block.time_int,
        notification_enabled=time_block.notification_enabled,
        sessions=resolved_sessions,
    )


async def create_routine_with_time_block(
    token: str, request: CreateTimeBlockRequest
) -> RoutineWithTimeBlocksResponse:

    current_user = validate_and_extract_user_details(token=token)

    _validate_time_block_request(request)

    with SessionLocal() as db:
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
        routine = Routine(user_id=current_user.id)
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
            time_block_id=saved_time_block.id, sessions=request.sessions
        )
        saved_sessions = save_sessions(db=db, sessions=session_models)

        # Auto-enroll plans
        _enroll_plans(
            db=db, user_id=current_user.id, plan_ids=_extract_plan_ids(request.sessions)
        )

        time_block_dto = await build_time_block_dto(
            db=db, time_block=saved_time_block, sessions=saved_sessions
        )

        return RoutineWithTimeBlocksResponse(
            id=saved_routine.id,
            time_blocks=[time_block_dto],
        )


async def get_user_routine(
    token: str, skip: int = 0, limit: int = 20
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
                db=db, time_block=tb, sessions=sessions_by_block.get(tb.id, [])
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


async def add_time_block_to_routine(
    token: str, routine_id: UUID, request: CreateTimeBlockRequest
) -> TimeBlockDTO:

    current_user = validate_and_extract_user_details(token=token)

    _validate_time_block_request(request)

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

        _check_duplicate_plans(db=db, routine_id=routine_id, sessions=request.sessions)
        _check_duplicate_time(db=db, routine_id=routine_id, time=request.time)

        # Save time block
        time_block = RoutineTimeBlock(
            routine_id=routine_id,
            time=request.time,
            time_int=request.time_int,
            notification_enabled=request.notification_enabled,
        )
        saved_time_block = save_time_block(db=db, time_block=time_block)

        session_models = build_session_models(
            time_block_id=saved_time_block.id, sessions=request.sessions
        )
        saved_sessions = save_sessions(db=db, sessions=session_models)

        # Auto-enroll plans
        _enroll_plans(
            db=db, user_id=current_user.id, plan_ids=_extract_plan_ids(request.sessions)
        )

        resolved_sessions = await _resolve_sessions(db=db, sessions=saved_sessions)

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

        # Auto-unenroll plans before soft delete
        plan_ids = get_plan_source_ids_by_time_block_id(
            db=db, time_block_id=time_block_id
        )
        _unenroll_plans(db=db, user_id=current_user.id, plan_ids=plan_ids)

        # Soft delete
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

        _validate_and_sync_update(
            db=db,
            user_id=current_user.id,
            routine_id=routine_id,
            time_block_id=time_block_id,
            request=request,
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
            time_block_id=updated_time_block.id, sessions=request.sessions
        )
        saved_sessions = save_sessions(db=db, sessions=session_models)

        resolved_sessions = await _resolve_sessions(db=db, sessions=saved_sessions)

        return TimeBlockDTO(
            id=updated_time_block.id,
            time=updated_time_block.time,
            time_int=updated_time_block.time_int,
            notification_enabled=updated_time_block.notification_enabled,
            sessions=resolved_sessions,
        )
