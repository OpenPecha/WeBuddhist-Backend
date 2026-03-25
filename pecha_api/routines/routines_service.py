import re
from fastapi import HTTPException
from starlette import status
from typing import List, Dict
from uuid import UUID

from pecha_api.db.database import SessionLocal
from pecha_api.users.users_service import validate_and_extract_user_details
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.texts.texts_models import Text

from .routines_models import Routine, RoutineTimeBlock, RoutineSession
from .routines_enums import SessionType
from .routines_repository import (
    get_routine_by_user_id,
    save_routine,
    save_time_block,
    save_sessions,
    get_time_blocks_with_sessions,
    get_sessions_by_time_block_ids,
)
from .routines_response_models import (
    CreateTimeBlockRequest,
    SessionDTO,
    TimeBlockDTO,
    RoutineWithTimeBlocksResponse,
    RoutineResponse,
)

TIME_FORMAT_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

ROUTINE_ALREADY_EXISTS = "Routine already exists for this user"
INVALID_TIME_FORMAT = "Time must be in HH:MM 24-hour format (00:00 to 23:59)"
SESSIONS_REQUIRED = "At least one session is required"
DUPLICATE_PLAN = "A plan can only appear once across the entire routine"


async def create_routine_with_time_block(
    token: str, request: CreateTimeBlockRequest
) -> RoutineWithTimeBlocksResponse:

    current_user = validate_and_extract_user_details(token=token)

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
        s.source_id for s in request.sessions if s.session_type == SessionType.PLAN
    ]
    if len(plan_source_ids) != len(set(plan_source_ids)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ResponseError(
                error=BAD_REQUEST, message=DUPLICATE_PLAN
            ).model_dump(),
        )

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
                session_type=s.session_type,
                source_id=s.source_id,
                display_order=s.display_order,
            )
            for s in request.sessions
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


async def _resolve_sessions(db, sessions: List[RoutineSession]) -> List[SessionDTO]:
    resolved = []
    plan_sessions = [s for s in sessions if s.session_type == SessionType.PLAN]
    recitation_sessions = [
        s for s in sessions if s.session_type == SessionType.RECITATION
    ]

    for s in plan_sessions:
        plan = get_plan_by_id(db=db, plan_id=s.source_id)
        if plan is None:
            continue
        resolved.append(
            SessionDTO(
                id=s.id,
                session_type=s.session_type,
                source_id=s.source_id,
                title=plan.title,
                language=(
                    plan.language.value
                    if hasattr(plan.language, "value")
                    else str(plan.language)
                ),
                image_url=plan.image_url,
                display_order=s.display_order,
            )
        )

    if recitation_sessions:
        text_ids = [str(s.source_id) for s in recitation_sessions]
        texts = await Text.get_texts_by_ids(text_ids)
        text_map = {str(t.id): t for t in texts}

        for s in recitation_sessions:
            text = text_map.get(str(s.source_id))
            if text is None:
                continue
            resolved.append(
                SessionDTO(
                    id=s.id,
                    session_type=s.session_type,
                    source_id=s.source_id,
                    title=text.title,
                    language=text.language or "en",
                    image_url=None,
                    display_order=s.display_order,
                )
            )

    resolved.sort(key=lambda s: s.display_order)

    return resolved


async def get_user_routine(
    token: str, skip: int = 0, limit: int = 20
) -> RoutineResponse:

    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        routine = get_routine_by_user_id(db=db, user_id=current_user.id)

        if routine is None:
            routine = Routine(user_id=current_user.id)
            from .routines_repository import save_routine
            routine = save_routine(db=db, routine=routine)
            return RoutineResponse(
                id=routine.id,
                time_blocks=[],
                skip=skip,
                limit=limit,
                total=0,
            )

        time_blocks, total = get_time_blocks_with_sessions(
            db=db, routine_id=routine.id, skip=skip, limit=limit
        )

        if not time_blocks:
            return RoutineResponse(
                id=routine.id,
                time_blocks=[],
                skip=skip,
                limit=limit,
                total=total,
            )

        time_block_ids = [tb.id for tb in time_blocks]
        all_sessions = get_sessions_by_time_block_ids(db=db, time_block_ids=time_block_ids)

        sessions_by_block: Dict[UUID, List[RoutineSession]] = {}
        for session in all_sessions:
            if session.time_block_id not in sessions_by_block:
                sessions_by_block[session.time_block_id] = []
            sessions_by_block[session.time_block_id].append(session)

        time_block_dtos = []
        for tb in time_blocks:
            block_sessions = sessions_by_block.get(tb.id, [])
            resolved_sessions = await _resolve_sessions(db=db, sessions=block_sessions)
            time_block_dtos.append(
                TimeBlockDTO(
                    id=tb.id,
                    time=tb.time,
                    time_int=tb.time_int,
                    notification_enabled=tb.notification_enabled,
                    sessions=resolved_sessions,
                )
            )

        return RoutineResponse(
            id=routine.id,
            time_blocks=time_block_dtos,
            skip=skip,
            limit=limit,
            total=total,
        )
