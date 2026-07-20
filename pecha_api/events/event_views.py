from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Header, Query
from starlette import status

from .event_response_models import EventsResponse, EventDTO
from .event_service import (
    get_events_service,
    get_events_today_service,
    get_event_by_id_service,
)

events_router = APIRouter(
    prefix="/events",
    tags=["Events"],
)


@events_router.get("", status_code=status.HTTP_200_OK, response_model=EventsResponse, response_model_exclude_none=True)
def get_events_endpoint(
    group_id: Annotated[Optional[UUID], Query(description="Filter by group ID")] = None,
    plan_id: Annotated[Optional[UUID], Query(description="Filter by plan ID")] = None,
    accumulator_id: Annotated[Optional[UUID], Query(description="Filter by accumulator ID")] = None,
    mantra_id: Annotated[Optional[UUID], Query(description="Filter by mantra ID")] = None,
    timer_id: Annotated[Optional[UUID], Query(description="Filter by timer ID")] = None,
    from_date: Annotated[Optional[datetime], Query(description="Filter events ending on or after this date")] = None,
    to_date: Annotated[Optional[datetime], Query(description="Filter events starting on or before this date")] = None,
    language: Annotated[Optional[str], Query(description="Filter metadata by language code")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> EventsResponse:
    return get_events_service(
        group_id=group_id,
        plan_id=plan_id,
        accumulator_id=accumulator_id,
        mantra_id=mantra_id,
        timer_id=timer_id,
        from_date=from_date,
        to_date=to_date,
        language=language,
        fallback=True,
        skip=skip,
        limit=limit,
    )


@events_router.get("/today", status_code=status.HTTP_200_OK, response_model=EventsResponse, response_model_exclude_none=True)
def get_events_today_endpoint(
    group_id: Annotated[Optional[UUID], Query(description="Filter by group ID")] = None,
    language: Annotated[Optional[str], Query(description="Filter metadata by language code")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    x_timezone: Annotated[
        Optional[str],
        Header(alias="X-Timezone", description="IANA timezone for determining today's date."),
    ] = None,
) -> EventsResponse:
    return get_events_today_service(
        timezone=x_timezone,
        group_id=group_id,
        language=language,
        skip=skip,
        limit=limit,
    )


@events_router.get("/{event_id}", status_code=status.HTTP_200_OK, response_model=EventDTO, response_model_exclude_none=True)
def get_event_by_id_endpoint(
    event_id: UUID,
    language: Annotated[Optional[str], Query(description="Filter metadata by language code")] = None,
) -> EventDTO:
    return get_event_by_id_service(event_id=event_id, language=language)
