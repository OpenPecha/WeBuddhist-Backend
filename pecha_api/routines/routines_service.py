from uuid import UUID

from fastapi import HTTPException
from starlette import status
from typing import List
from uuid import UUID

from pecha_api.config import TIME_FORMAT_PATTERN
from pecha_api.db.database import SessionLocal
from pecha_api.users.users_service import validate_and_extract_user_details
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST
from pecha_api.texts.texts_models import Text

from .routines_models import Routine, RoutineTimeBlock, RoutineSession
from .routines_enums import SessionType
from .routines_repository import (
    get_routine_by_user_id,
    get_routine_by_id_and_user,
    get_existing_plan_source_ids,
    time_block_exists_for_routine,
    get_routine_by_id,
    get_time_block_by_id,
    get_plans_by_ids,
    get_existing_plan_source_ids_in_routine,
    get_time_block_by_routine_and_time,
    delete_sessions_by_time_block_id,
    save_routine,
    save_time_block,
    save_sessions,
    get_time_block_by_id,
    soft_delete_time_block,
    update_time_block as update_time_block_repo,
)
from .response_message import (
    DUPLICATE_PLAN,
    INVALID_TIME_FORMAT,
    ROUTINE_ALREADY_EXISTS,
    ROUTINE_NOT_FOUND,
    ROUTINE_NOT_FOUND,
    ROUTINE_FORBIDDEN,
    SESSIONS_REQUIRED,
    TIME_ALREADY_EXISTS,
    TIME_BLOCK_NOT_FOUND,
    TIME_BLOCK_NOT_FOUND,
    TIME_BLOCK_TIME_CONFLICT,
)
from .routines_response_models import (
    CreateTimeBlockRequest,
    UpdateTimeBlockRequest,
    SessionDTO,
    TimeBlockDTO,
    RoutineWithTimeBlocksResponse,
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


def _check_duplicate_time(db, routine_id: UUID, time: str) -> None:
    if time_block_exists_for_routine(db=db, routine_id=routine_id, time=time):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(
                error=BAD_REQUEST, message=TIME_ALREADY_EXISTS
            ).model_dump(),
        )


def _resolve_plan_sessions(db, plan_sessions: List[RoutineSession]) -> List[SessionDTO]:
    if not plan_sessions:
        return []

    plan_ids = [session.source_id for session in plan_sessions]
    plans = get_plans_by_ids(db=db, plan_ids=plan_ids)
    plan_map = {plan.id: plan for plan in plans}

    resolved = []
    for session in plan_sessions:
        plan = plan_map.get(session.source_id)
        if plan is None:
            continue
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
                image_url=plan.image_url,
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


async def create_routine_with_time_block(
    token: str, request: CreateTimeBlockRequest
) -> RoutineWithTimeBlocksResponse:

    current_user = validate_and_extract_user_details(token=token)

    _validate_time_block_request(request)

    with SessionLocal() as db:
        # Check routine doesn't already exist
        existing_routine = get_routine_by_user_id(db=db, user_id=current_user.id)
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

        # Create sessions
        session_models = [
            RoutineSession(
                time_block_id=saved_time_block.id,
                session_type=session.session_type,
                source_id=session.source_id,
                display_order=session.display_order,
            )
            for session in request.sessions
        ]
        saved_sessions = save_sessions(db=db, sessions=session_models)

        resolved_sessions = await _resolve_sessions(db=db, sessions=saved_sessions)

        return RoutineWithTimeBlocksResponse(
            id=saved_routine.id,
            time_blocks=[
                TimeBlockDTO(
                    id=saved_time_block.id,
                    time=saved_time_block.time,
                    time_int=saved_time_block.time_int,
                    notification_enabled=saved_time_block.notification_enabled,
                    sessions=resolved_sessions,
                )
            ],
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

        # Save sessions
        session_models = [
            RoutineSession(
                time_block_id=saved_time_block.id,
                session_type=session.session_type,
                source_id=session.source_id,
                display_order=session.display_order,
            )
            for session in request.sessions
        ]
        saved_sessions = save_sessions(db=db, sessions=session_models)

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
        time_block = get_time_block_by_id(
            db=db, time_block_id=time_block_id, routine_id=routine_id
        )
        if not time_block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(
                    error=BAD_REQUEST, message=TIME_BLOCK_NOT_FOUND
                ).model_dump(),
            )

        # Soft delete
        soft_delete_time_block(db=db, time_block=time_block)


async def update_time_block_service(token: str, routine_id: str, time_block_id: str, request: UpdateTimeBlockRequest) -> TimeBlockDTO:
    current_user = validate_and_extract_user_details(token=token)
    
    _validate_create_routine_request(request)
    
    routine_uuid = UUID(routine_id)
    time_block_uuid = UUID(time_block_id)
    
    with SessionLocal() as db:
       
        routine = get_routine_by_id(db=db, routine_id=routine_uuid)
        if not routine:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=ResponseError(error=BAD_REQUEST, message=ROUTINE_NOT_FOUND).model_dump())
        
        if routine.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail=ResponseError(error=BAD_REQUEST, message=ROUTINE_FORBIDDEN).model_dump())
        
        time_block = get_time_block_by_id(db=db, time_block_id=time_block_uuid)
        if not time_block:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=ResponseError(error=BAD_REQUEST, message=TIME_BLOCK_NOT_FOUND).model_dump())
        
        if time_block.routine_id != routine_uuid:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=ResponseError(error=BAD_REQUEST, message=TIME_BLOCK_NOT_FOUND).model_dump())
        
        existing_time_block = get_time_block_by_routine_and_time(
            db=db,
            routine_id=routine_uuid,
            time=request.time,
            exclude_time_block_id=time_block_uuid,
        )
        if existing_time_block:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=ResponseError(error=BAD_REQUEST, message=TIME_BLOCK_TIME_CONFLICT).model_dump())
        
        existing_plan_ids = get_existing_plan_source_ids_in_routine(
            db=db,
            routine_id=routine_uuid,
            exclude_time_block_id=time_block_uuid,
        )
        new_plan_ids = [
            session.source_id
            for session in request.sessions
            if session.session_type == SessionType.PLAN
        ]
        duplicate_plans = set(existing_plan_ids) & set(new_plan_ids)
        if duplicate_plans:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,detail=ResponseError(error=BAD_REQUEST, message=DUPLICATE_PLAN).model_dump())
        
        delete_sessions_by_time_block_id(db=db, time_block_id=time_block_uuid)
        
        updated_time_block = update_time_block_repo(
            db=db,
            time_block=time_block,
            time=request.time,
            time_int=request.time_int,
            notification_enabled=request.notification_enabled,
        )
        
        session_models = [
            RoutineSession(
                time_block_id=updated_time_block.id,
                session_type=session.session_type,
                source_id=session.source_id,
                display_order=session.display_order,
            )
            for session in request.sessions
        ]
        saved_sessions = save_sessions(db=db, sessions=session_models)
        
        resolved_sessions = await _resolve_sessions(db=db, sessions=saved_sessions)
        
        return TimeBlockDTO(
            id=updated_time_block.id,
            time=updated_time_block.time,
            time_int=updated_time_block.time_int,
            notification_enabled=updated_time_block.notification_enabled,
            sessions=resolved_sessions,
        )
