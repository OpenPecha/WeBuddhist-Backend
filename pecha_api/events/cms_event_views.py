from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from .event_response_models import (
    CreateEventRequest,
    UpdateEventRequest,
    EventDTO,
    EventsResponse,
    EventParticipantsResponse,
)
from .event_service import (
    create_event_service,
    update_event_service,
    delete_event_service,
    get_cms_events_service,
    get_cms_event_by_id_service,
)
from .event_participant_service import get_cms_event_participants_service

oauth2_scheme = HTTPBearer()

cms_events_router = APIRouter(
    prefix="/cms/events",
    tags=["CMS Events"],
)


@cms_events_router.get("", status_code=status.HTTP_200_OK, response_model=EventsResponse, response_model_exclude_none=True)
async def get_cms_events_endpoint(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
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
    return get_cms_events_service(
        token=credentials.credentials,
        group_id=group_id,
        plan_id=plan_id,
        accumulator_id=accumulator_id,
        mantra_id=mantra_id,
        timer_id=timer_id,
        from_date=from_date,
        to_date=to_date,
        language=language,
        skip=skip,
        limit=limit,
    )


@cms_events_router.get("/{event_id}", status_code=status.HTTP_200_OK, response_model=EventDTO, response_model_exclude_none=True)
async def get_cms_event_by_id_endpoint(
    event_id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    language: Annotated[Optional[str], Query(description="Filter metadata by language code")] = None,
) -> EventDTO:
    return get_cms_event_by_id_service(
        token=credentials.credentials,
        event_id=event_id,
        language=language,
    )


@cms_events_router.get(
    "/{event_id}/participants",
    status_code=status.HTTP_200_OK,
    response_model=EventParticipantsResponse,
    response_model_exclude_none=True,
)
async def get_cms_event_participants_endpoint(
    event_id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> EventParticipantsResponse:
    return get_cms_event_participants_service(
        token=credentials.credentials,
        event_id=event_id,
        skip=skip,
        limit=limit,
    )


@cms_events_router.post("", status_code=status.HTTP_201_CREATED, response_model=EventDTO, response_model_exclude_none=True)
async def create_event_endpoint(
    request: CreateEventRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> EventDTO:
    return create_event_service(token=credentials.credentials, request=request)


@cms_events_router.put("/{event_id}", status_code=status.HTTP_200_OK, response_model=EventDTO, response_model_exclude_none=True)
async def update_event_endpoint(
    event_id: UUID,
    request: UpdateEventRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> EventDTO:
    return update_event_service(
        token=credentials.credentials,
        event_id=event_id,
        request=request,
    )


@cms_events_router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event_endpoint(
    event_id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> None:
    delete_event_service(token=credentials.credentials, event_id=event_id)
