from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from pecha_api.group_recitation_collection.user_chant_completion_models import (
    UserChantCompletion,
)


def get_user_completions_today(
    db: Session,
    user_id: UUID,
    collection_id: UUID,
    today: date,
) -> List[UUID]:
    """Get list of chant_ids completed by user today for a specific collection."""
    completions = (
        db.query(UserChantCompletion.chant_id)
        .filter(
            UserChantCompletion.user_id == user_id,
            UserChantCompletion.chant_collection_id == collection_id,
            UserChantCompletion.completion_date == today,
        )
        .all()
    )
    return [completion.chant_id for completion in completions]


def check_completion_exists(
    db: Session,
    user_id: UUID,
    chant_id: UUID,
    completion_date: date,
) -> bool:
    """Check if a completion already exists for this user, chant, and date."""
    return (
        db.query(UserChantCompletion)
        .filter(
            UserChantCompletion.user_id == user_id,
            UserChantCompletion.chant_id == chant_id,
            UserChantCompletion.completion_date == completion_date,
        )
        .first()
        is not None
    )


def create_chant_completion(
    db: Session,
    user_id: UUID,
    chant_id: UUID,
    collection_id: UUID,
    completion_date: date,
) -> UserChantCompletion:
    """Create a new chant completion record."""
    completion = UserChantCompletion(
        user_id=user_id,
        chant_id=chant_id,
        chant_collection_id=collection_id,
        completion_date=completion_date,
        created_at=datetime.now(timezone.utc),
    )
    db.add(completion)
    db.commit()
    db.refresh(completion)
    return completion
