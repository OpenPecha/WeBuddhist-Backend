from typing import Optional, List
from uuid import UUID
import logging

from ..db.database import SessionLocal
from ..uploads.S3_utils import generate_presigned_access_url
from ..config import get
from .timer_repository import get_timers_by_group, get_user_timers_by_group
from .timer_response_models import TimersResponse, TimerDTO
from .timer_model import Timer
from .timer_enums import TimerType

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


def convert_timers_to_dtos(timers: List[Timer]) -> List[TimerDTO]:
    return [
        TimerDTO(
            id=timer.id,
            user_id=timer.user_id,
            group_id=timer.group_id,
            type=TimerType(timer.type.value) if hasattr(timer.type, 'value') else timer.type,
            name=timer.name,
            description=timer.description,
            duration=timer.duration,
            audio_url=generate_audio_presigned_url(timer.audio_url),
            created_at=timer.created_at,
            updated_at=timer.updated_at
        )
        for timer in timers
    ]


def get_all_timers_service(
    group_id: UUID,
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
    group_id: UUID,
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
