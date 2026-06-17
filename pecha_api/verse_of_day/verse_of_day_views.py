from fastapi import APIRouter, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, Optional
from uuid import UUID
from datetime import date
from starlette import status

from .verse_of_day_response_models import VerseOfDayPublicResponse, VerseOfDayListResponse, CreateVerseOfDayRequest, UpdateVerseOfDayRequest, VerseOfDayDTO
from .verse_of_day_service import get_verse_of_day, get_verses_of_day_list_service, get_verse_of_day_by_id_service, get_verse_of_day_today_service, create_verse_of_day_service, update_verse_of_day_service, delete_verse_of_day_service
from pecha_api.users.users_service import validate_and_extract_user_details

oauth2_scheme = HTTPBearer()

verse_of_day_router = APIRouter(
    prefix="/verse-of-day",
    tags=["Verse of Day"]
)

cms_verse_of_day_router = APIRouter(
    prefix="/cms/verse-of-day",
    tags=["CMS Verse of Day"]
)


@verse_of_day_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=VerseOfDayPublicResponse
)
def get_verse_of_day_endpoint(
    group_id: Annotated[Optional[UUID], Query(description="Filter by group ID")] = None,
    date: Annotated[Optional[date], Query(description="Filter by date (YYYY-MM-DD)")] = None,
    lang: Annotated[Optional[str], Query(description="Filter by language (en, bo, zh, hi, ne, mn). Returns all languages if not specified.")] = None,
):
 
    return get_verse_of_day(group_id=group_id, filter_date=date, lang=lang)


@verse_of_day_router.get(
    "/today",
    status_code=status.HTTP_200_OK,
    response_model=VerseOfDayPublicResponse
)
def get_verse_of_day_today_endpoint(
    lang: Annotated[Optional[str], Query(description="Filter by language (en, bo, zh, hi, ne, mn). Returns all languages if not specified.")] = None,
):

    return get_verse_of_day_today_service(lang=lang)


@verse_of_day_router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=VerseOfDayPublicResponse
)
def get_verse_of_day_by_id_endpoint(
    id: UUID,
    lang: Annotated[Optional[str], Query(description="Filter by language (en, bo, zh, hi, ne, mn). Returns all languages if not specified.")] = None,
):

    return get_verse_of_day_by_id_service(verse_id=id, lang=lang)


@cms_verse_of_day_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=VerseOfDayListResponse
)
def cms_get_verse_of_day_endpoint(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    group_id: Annotated[Optional[UUID], Query(description="Filter by group ID")] = None,
    date: Annotated[Optional[date], Query(description="Filter by date (YYYY-MM-DD)")] = None,
    lang: Annotated[Optional[str], Query(description="Filter by language (en, bo, zh, hi, ne, mn). Returns all languages if not specified.")] = None,
    skip: Annotated[int, Query(description="Number of records to skip", ge=0)] = 0,
    limit: Annotated[int, Query(description="Maximum number of records to return", ge=1, le=100)] = 100,
):
    validate_and_extract_user_details(credentials.credentials)
    return get_verses_of_day_list_service(group_id=group_id, filter_date=date, lang=lang, skip=skip, limit=limit)


@cms_verse_of_day_router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=VerseOfDayPublicResponse
)
def cms_get_verse_of_day_by_id_endpoint(
    id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    lang: Annotated[Optional[str], Query(description="Filter by language (en, bo, zh, hi, ne, mn). Returns all languages if not specified.")] = None,
):
    validate_and_extract_user_details(credentials.credentials)
    return get_verse_of_day_by_id_service(verse_id=id, lang=lang)


@cms_verse_of_day_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=VerseOfDayDTO
)
def create_verse_of_day_endpoint(
    request: CreateVerseOfDayRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):

    user = validate_and_extract_user_details(credentials.credentials)
    return create_verse_of_day_service(request=request, created_by=user.email)


@cms_verse_of_day_router.put(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=VerseOfDayDTO
)
def update_verse_of_day_endpoint(
    id: UUID,
    request: UpdateVerseOfDayRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):

    user = validate_and_extract_user_details(credentials.credentials)
    return update_verse_of_day_service(verse_id=id, request=request, updated_by=user.email)


@cms_verse_of_day_router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_verse_of_day_endpoint(
    id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):

    validate_and_extract_user_details(credentials.credentials)
    delete_verse_of_day_service(verse_id=id)
