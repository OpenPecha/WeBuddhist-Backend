import logging
from datetime import date
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.users.users_service import validate_and_extract_user_details

from pecha_api.plans.users.recitation_collection.recitation_collection_models import (
    RecitationCollection,
)
from pecha_api.plans.users.recitation_collection.recitation_collection_repository import (
    get_collection_by_id,
    get_collection_item_by_id,
)
from pecha_api.plans.users.recitation_collection.recitation_collection_completion_repository import (
    get_user_completions_today,
    create_chant_completion,
    check_completion_exists,
    count_unique_completion_days,
)
from pecha_api.plans.users.recitation_collection.recitation_collection_completion_response_models import (
    TodayChantCompletionsResponse,
    ChantCompletionDayCountResponse,
)

logger = logging.getLogger(__name__)

_CHANT_NOT_IN_COLLECTION = "CHANT_NOT_IN_COLLECTION"


def _get_collection_or_404(
    db,
    collection_id: UUID,
    user_id: UUID,
) -> RecitationCollection:
    """Resolve the collection by id, validating it belongs to the user."""
    collection = get_collection_by_id(db=db, collection_id=collection_id, user_id=user_id)
    if not collection:
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
        _get_collection_or_404(db=db, collection_id=collection_id, user_id=user.id)

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
        _get_collection_or_404(db=db, collection_id=collection_id, user_id=user.id)

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
        _get_collection_or_404(db=db, collection_id=collection_id, user_id=user.id)

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

        today = date.today()
        if check_completion_exists(
            db=db,
            user_id=user.id,
            chant_id=chant_id,
            completion_date=today,
        ):
            # Already completed today - return success (idempotent)
            return

        create_chant_completion(
            db=db,
            user_id=user.id,
            chant_id=chant_id,
            collection_id=collection_id,
            completion_date=today,
        )
