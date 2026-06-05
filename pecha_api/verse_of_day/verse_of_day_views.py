from fastapi import APIRouter, Query
from typing import Annotated, Optional
from uuid import UUID
from datetime import date
from starlette import status

from .verse_of_day_response_models import VerseOfDayPublicResponse
from .verse_of_day_service import get_verse_of_day, get_verse_of_day_by_id_service


verse_of_day_router = APIRouter(
    prefix="/verse-of-day",
    tags=["Verse of Day"]
)


@verse_of_day_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=VerseOfDayPublicResponse
)
def get_verse_of_day_endpoint(
    group_id: Annotated[Optional[UUID], Query(description="Filter by group ID")] = None,
    date: Annotated[Optional[date], Query(description="Filter by date (YYYY-MM-DD)")] = None,
):
 
    return get_verse_of_day(group_id=group_id, filter_date=date)


@verse_of_day_router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=VerseOfDayPublicResponse
)
def get_verse_of_day_by_id_endpoint(id: UUID):

    return get_verse_of_day_by_id_service(verse_id=id)
