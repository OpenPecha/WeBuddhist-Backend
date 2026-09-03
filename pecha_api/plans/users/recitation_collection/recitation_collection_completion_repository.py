from datetime import date, datetime, timezone
from typing import List
from uuid import UUID

from sqlalchemy import func, distinct
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pecha_api.plans.users.recitation_collection.recitation_collection_completion_models import (
    RecitationCollectionChantCompletion,
)


def get_user_completions_today(
    db: Session,
    user_id: UUID,
    collection_id: UUID,
    today: date,
) -> List[UUID]:
    """Get list of chant_ids completed by user today for a specific collection."""
    completions = (
        db.query(RecitationCollectionChantCompletion.chant_id)
        .filter(
            RecitationCollectionChantCompletion.user_id == user_id,
            RecitationCollectionChantCompletion.collection_id == collection_id,
            RecitationCollectionChantCompletion.completion_date == today,
        )
        .all()
    )
    return [completion.chant_id for completion in completions]


def count_unique_completion_days(
    db: Session,
    user_id: UUID,
    collection_id: UUID,
) -> int:
    """Count distinct days on which the user completed at least one chant in the collection."""
    return (
        db.query(func.count(distinct(RecitationCollectionChantCompletion.completion_date)))
        .filter(
            RecitationCollectionChantCompletion.user_id == user_id,
            RecitationCollectionChantCompletion.collection_id == collection_id,
        )
        .scalar()
    ) or 0


def check_completion_exists(
    db: Session,
    user_id: UUID,
    chant_id: UUID,
    completion_date: date,
) -> bool:
    """Check if a completion already exists for this user, chant, and date."""
    return (
        db.query(RecitationCollectionChantCompletion)
        .filter(
            RecitationCollectionChantCompletion.user_id == user_id,
            RecitationCollectionChantCompletion.chant_id == chant_id,
            RecitationCollectionChantCompletion.completion_date == completion_date,
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
) -> None:
    """Create a new chant completion record, tolerating a concurrent duplicate.

    A prior check_completion_exists() call can race with another request for
    the same (user, chant, date); the unique constraint is the real guard, so
    an IntegrityError here just means someone else already logged it.
    """
    completion = RecitationCollectionChantCompletion(
        user_id=user_id,
        chant_id=chant_id,
        collection_id=collection_id,
        completion_date=completion_date,
        created_at=datetime.now(timezone.utc),
    )
    db.add(completion)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
