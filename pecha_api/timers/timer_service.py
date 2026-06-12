from typing import Optional, List
from uuid import UUID, uuid4
import logging

from fastapi import HTTPException
from starlette import status
from ..db.database import SessionLocal
from ..uploads.S3_utils import generate_presigned_access_url
from ..config import get
from ..users.users_service import validate_and_extract_user_details
from .timer_repository import (
    get_timers_by_group, 
    get_user_timers_by_group,
    save_timer,
    get_timer_by_id,
    update_timer,
    delete_timer
)
from .timer_response_models import (
    TimersResponse, 
    TimerDTO, 
    CreateTimerRequest, 
    UpdateTimerRequest
)
from .timer_model import Timer
from .timer_enums import TimerType
from .response_message import (
    NOT_FOUND,
    FORBIDDEN,
    TIMER_NOT_FOUND,
    TIMER_UPDATE_NOT_ALLOWED,
    TIMER_DELETE_NOT_ALLOWED,
    ONLY_USER_TIMERS_CAN_BE_UPDATED,
    ONLY_USER_TIMERS_CAN_BE_DELETED
)

logger = logging.getLogger(__name__)


def generate_audio_presigned_url(audio_url: Optional[str]) -> Optional[str]:
    if not audio_url:
        return None
    try:
        bucket_name = get("AWS_BUCKET_NAME")
        return generate_presigned_access_url(bucket_name, audio_url)
    except Exception as e:
        logger.error(f"Failed to generate presigned URL for audio: {audio_url}", exc_info=True)
        return None


def convert_timer_to_dto(timer: Timer) -> TimerDTO:
    timer_type = TimerType(timer.type.value) if hasattr(timer.type, 'value') else timer.type
    return TimerDTO(
        id=timer.id,
        user_id=timer.user_id,
        group_id=timer.group_id,
        type=timer_type,
        name=timer.name,
        description=timer.description,
        duration=timer.duration,
        audio_url=generate_audio_presigned_url(timer.audio_url),
        created_at=timer.created_at,
        updated_at=timer.updated_at
    )


def convert_timers_to_dtos(timers: List[Timer]) -> List[TimerDTO]:
    return [convert_timer_to_dto(timer) for timer in timers]


def is_user_created_timer(timer: Timer) -> bool:
    timer_type = timer.type.value if hasattr(timer.type, 'value') else timer.type
    return timer_type == TimerType.USER.value


def get_all_timers_service(
    group_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 20
) -> TimersResponse:
    with SessionLocal() as db:
        timers, total = get_timers_by_group(db, group_id, skip, limit)
        return TimersResponse(
            timers=convert_timers_to_dtos(timers),
            total=total,
            skip=skip,
            limit=limit
        )


def get_user_timers_service(
    user_id: UUID,
    group_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 20
) -> TimersResponse:
    with SessionLocal() as db:
        timers, total = get_user_timers_by_group(db, user_id, group_id, skip, limit)
        return TimersResponse(
            timers=convert_timers_to_dtos(timers),
            total=total,
            skip=skip,
            limit=limit
        )


def create_timer_service(token: str, request: CreateTimerRequest) -> TimerDTO:
    current_user = validate_and_extract_user_details(token=token)
    
    with SessionLocal() as db:
        new_timer = Timer(
            id=uuid4(),
            user_id=current_user.id,
            group_id=request.group_id,
            type=TimerType.USER,
            name=request.name,
            description=request.description,
            duration=request.duration,
            audio_url=request.audio_url
        )
        
        saved_timer = save_timer(db, new_timer)
        return convert_timer_to_dto(saved_timer)


def update_timer_service(token: str, timer_id: UUID, request: UpdateTimerRequest) -> TimerDTO:
    current_user = validate_and_extract_user_details(token=token)
    
    with SessionLocal() as db:
        timer = get_timer_by_id(db, timer_id)
        
        if not timer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": NOT_FOUND, "message": TIMER_NOT_FOUND}
            )
        
        if timer.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": FORBIDDEN, "message": TIMER_UPDATE_NOT_ALLOWED}
            )
        
        if not is_user_created_timer(timer):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": FORBIDDEN, "message": ONLY_USER_TIMERS_CAN_BE_UPDATED}
            )
        
        if request.name is not None:
            timer.name = request.name
        if request.description is not None:
            timer.description = request.description
        if request.duration is not None:
            timer.duration = request.duration
        if request.audio_url is not None:
            timer.audio_url = request.audio_url
        
        updated_timer = update_timer(db, timer)
        return convert_timer_to_dto(updated_timer)


def delete_timer_service(token: str, timer_id: UUID) -> None:
    current_user = validate_and_extract_user_details(token=token)
    
    with SessionLocal() as db:
        timer = get_timer_by_id(db, timer_id)
        
        if not timer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": NOT_FOUND, "message": TIMER_NOT_FOUND}
            )
        
        if timer.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": FORBIDDEN, "message": TIMER_DELETE_NOT_ALLOWED}
            )
        
        if not is_user_created_timer(timer):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": FORBIDDEN, "message": ONLY_USER_TIMERS_CAN_BE_DELETED}
            )
        
        delete_timer(db, timer)
