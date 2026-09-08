import logging
from datetime import date, datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.users.users_service import validate_and_extract_user_details
from pecha_api.plans.groups.groups_repository import get_group_by_id, is_group_published

from pecha_api.group_recitation_collection.models import GroupRecitationCollection
from pecha_api.group_recitation_collection.repository import (
    get_collection_item_by_id,
    get_collection_without_group_filter,
)
from pecha_api.group_recitation_collection.user_chant_completion_repository import (
    get_user_completions_today,
    create_chant_completion,
    check_completion_exists,
    count_unique_completion_days,
)
from pecha_api.group_recitation_collection.user_chant_completion_response_models import (
    TodayChantCompletionsResponse,
    ChantCompletionDayCountResponse,
)

logger = logging.getLogger(__name__)

_CHANT_NOT_IN_COLLECTION = "CHANT_NOT_IN_COLLECTION"
_ALREADY_COMPLETED_TODAY = "ALREADY_COMPLETED_TODAY"


def _get_collection_or_404(
    db,
    collection_id: UUID,
) -> GroupRecitationCollection:
    """Resolve the collection by id and validate its owning group exists."""
    collection = get_collection_without_group_filter(db=db, collection_id=collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )

    group = get_group_by_id(db=db, group_id=collection.group_id)
    if not group or not is_group_published(group):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )
    return collection


def get_today_completions_service(
    token: str,
    collection_id: UUID,
) -> TodayChantCompletionsResponse:
    """Get list of chants completed today by the authenticated user."""
    user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        _get_collection_or_404(db=db, collection_id=collection_id)

        # Get today's completions
        today = date.today()
        completed_chant_ids = get_user_completions_today(
            db=db,
            user_id=user.id,
            collection_id=collection_id,
            today=today,
        )
        
        return TodayChantCompletionsResponse(
            completed_chant_ids=completed_chant_ids,
            date=today.isoformat(),
        )


def get_completion_day_count_service(
    token: str,
    collection_id: UUID,
) -> ChantCompletionDayCountResponse:
    """Get the number of unique days the user completed at least one chant in the collection."""
    user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        _get_collection_or_404(db=db, collection_id=collection_id)

        day_count = count_unique_completion_days(
            db=db,
            user_id=user.id,
            collection_id=collection_id,
        )

        return ChantCompletionDayCountResponse(
            collection_id=collection_id,
            day_count=day_count,
        )


def create_chant_completion_service(
    token: str,
    collection_id: UUID,
    chant_id: UUID,
) -> None:
    """Create a new chant completion log for the authenticated user."""
    user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        _get_collection_or_404(db=db, collection_id=collection_id)

        # Validate chant exists in collection
        chant_item = get_collection_item_by_id(
            db=db,
            item_id=chant_id,
            collection_id=collection_id,
        )
        if not chant_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=_CHANT_NOT_IN_COLLECTION,
            )
        
        # Check if already completed today (make it idempotent)
        today = date.today()
        if check_completion_exists(
            db=db,
            user_id=user.id,
            chant_id=chant_id,
            completion_date=today,
        ):
            # Already completed today - return success (idempotent)
            return
        
        # Create completion log
        create_chant_completion(
            db=db,
            user_id=user.id,
            chant_id=chant_id,
            collection_id=collection_id,
            completion_date=today,
        )
