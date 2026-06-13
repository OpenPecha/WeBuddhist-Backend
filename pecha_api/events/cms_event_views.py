from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from .event_response_models import CreateEventRequest, UpdateEventRequest, EventDTO
from .event_service import create_event_service, update_event_service, delete_event_service

oauth2_scheme = HTTPBearer()

cms_events_router = APIRouter(
    prefix="/cms/events",
    tags=["CMS Events"],
)


@cms_events_router.post("", status_code=status.HTTP_201_CREATED, response_model=EventDTO)
async def create_event_endpoint(
    request: CreateEventRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> EventDTO:
    return create_event_service(token=credentials.credentials, request=request)


@cms_events_router.put("/{event_id}", status_code=status.HTTP_200_OK, response_model=EventDTO)
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
