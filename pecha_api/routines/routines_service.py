from fastapi import HTTPException
from starlette import status
from typing import List, Dict
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
    get_plans_by_ids,
    save_routine,
    save_time_block,
    save_sessions,
    get_time_blocks,
    get_sessions_by_time_block_ids,
)
from .response_message import (
    DUPLICATE_PLAN,
    INVALID_TIME_FORMAT,
    ROUTINE_ALREADY_EXISTS,
    SESSIONS_REQUIRED,
)
from .routines_response_models import (
    CreateTimeBlockRequest,
    SessionDTO,
    TimeBlockDTO,
    RoutineWithTimeBlocksResponse,
    RoutineResponse,
)


def _validate_create_routine_request(request: CreateTimeBlockRequest) -> None:
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

    _validate_create_routine_request(request)

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

        time_block_dto = await build_time_block_dto(
            db=db, time_block=saved_time_block, sessions=saved_sessions
        )

        return RoutineWithTimeBlocksResponse(
            id=saved_routine.id,
            time_blocks=[time_block_dto],
        )

async def get_user_routine(token: str, skip: int = 0, limit: int = 20) -> RoutineResponse:

    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        routine = get_routine_by_user_id(
            db=db, user_id=current_user.id, include_deleted=False
        )

        if routine is None:
            routine = Routine(user_id=current_user.id)
            routine = save_routine(db=db, routine=routine)
            return RoutineResponse(id=routine.id, time_blocks=[], skip=skip, limit=limit, total=0)

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
            return RoutineResponse(id=routine.id, time_blocks=[], skip=skip, limit=limit, total=total)

        time_block_ids = [tb.id for tb in time_blocks]
        all_sessions = get_sessions_by_time_block_ids(
            db=db,
            time_block_ids=time_block_ids,
            order_by_field=RoutineSession.display_order,
            order_desc=False,
        )
        sessions_by_block = group_sessions_by_block(all_sessions)

        time_block_dtos = [
            await build_time_block_dto(db=db, time_block=tb, sessions=sessions_by_block.get(tb.id, []))
            for tb in time_blocks
        ]

        return RoutineResponse(id=routine.id, time_blocks=time_block_dtos, skip=skip, limit=limit, total=total)

