import logging
from uuid import UUID
from fastapi import HTTPException
from starlette import status

from ..db.database import SessionLocal
from ..timezone_utils import normalize_timezone_name
from ..plans.plans_enums import LanguageCode
from .user_metadata_repository import upsert_user_timezone, upsert_user_language
from .user_metadata_response_models import UserMetadataDTO
from .users_service import validate_and_extract_user_details

logger = logging.getLogger(__name__)


def sync_user_timezone(user_id: UUID, timezone: str) -> None:
    """Validate and upsert user timezone. Raises HTTPException if invalid."""
    validated_timezone = normalize_timezone_name(timezone)
    
    if not validated_timezone:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid timezone"
        )
    
    with SessionLocal() as db:
        upsert_user_timezone(db, user_id, validated_timezone)


def update_user_language(token: str, language: LanguageCode) -> UserMetadataDTO:
    """Update user language preference."""
    current_user = validate_and_extract_user_details(token=token)
    
    with SessionLocal() as db:
        metadata = upsert_user_language(db, current_user.id, language)
        return UserMetadataDTO(
            language=metadata.language,
            timezone=metadata.timezone
        )
