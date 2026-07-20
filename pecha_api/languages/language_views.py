from typing import Annotated

from fastapi import APIRouter, Query
from starlette import status

from pecha_api.languages.language_response_models import LanguageListResponse
from pecha_api.languages.language_service import list_languages_service

language_router = APIRouter(
    prefix="/languages",
    tags=["Languages"],
)


@language_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=LanguageListResponse,
)
async def list_languages(
    enabled_only: Annotated[
        bool,
        Query(description="When true, only return languages with enabled=true"),
    ] = True,
) -> LanguageListResponse:
    return list_languages_service(enabled_only=enabled_only)
