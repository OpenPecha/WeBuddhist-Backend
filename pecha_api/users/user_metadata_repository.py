from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import _datetime
from _datetime import datetime

from .user_metadata_model import UserMetadata
from ..plans.plans_enums import LanguageCode


def get_user_metadata_by_user_id(db: Session, user_id: UUID) -> Optional[UserMetadata]:
    """Get user metadata by user ID."""
    return db.query(UserMetadata).filter(UserMetadata.user_id == user_id).first()


def upsert_user_timezone(db: Session, user_id: UUID, timezone: str) -> UserMetadata:
    """Create or update user metadata with timezone."""
    metadata = get_user_metadata_by_user_id(db, user_id)
    
    if metadata:
        metadata.timezone = timezone
        metadata.updated_at = datetime.now(_datetime.timezone.utc)
    else:
        metadata = UserMetadata(
            user_id=user_id,
            timezone=timezone
        )
        db.add(metadata)
    
    db.commit()
    db.refresh(metadata)
    return metadata


def upsert_user_language(db: Session, user_id: UUID, language: LanguageCode) -> UserMetadata:
    """Create or update user metadata with language."""
    metadata = get_user_metadata_by_user_id(db, user_id)
    
    if metadata:
        metadata.language = language
        metadata.updated_at = datetime.now(_datetime.timezone.utc)
    else:
        metadata = UserMetadata(
            user_id=user_id,
            language=language
        )
        db.add(metadata)
    
    db.commit()
    db.refresh(metadata)
    return metadata
