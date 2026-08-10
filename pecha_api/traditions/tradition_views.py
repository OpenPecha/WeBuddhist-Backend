from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status
from typing import Annotated, Optional
from uuid import UUID

from pecha_api.plans.language_constants import language_query_description
from pecha_api.traditions.tradition_response_models import (
    SaveUserTraditionRequest,
    TraditionListResponse,
    TraditionOnboardingResponse,
    UserTraditionDTO,
    UserTraditionsResponse,
)
from pecha_api.traditions.tradition_service import (
    delete_user_tradition_service,
    get_tradition_onboarding_service,
    get_user_traditions_service,
    list_traditions_service,
    save_user_tradition_service,
    update_user_tradition_service,
)

oauth2_scheme = HTTPBearer()

tradition_router = APIRouter(
    prefix="/traditions",
    tags=["Traditions"],
)

user_tradition_router = APIRouter(
    prefix="/users/me/traditions",
    tags=["User Traditions"],
)


@tradition_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=TraditionListResponse,
    response_model_exclude_none=True,
)
async def list_traditions(
    language: Annotated[
        Optional[str],
        Query(
            description=language_query_description(
                "Localize tradition names",
                lowercase_example=True,
            )
        ),
    ] = "en",
):
    return await list_traditions_service(language=language or "en")


@user_tradition_router.get(
    "/onboarding",
    status_code=status.HTTP_200_OK,
    response_model=TraditionOnboardingResponse,
    response_model_exclude_none=True,
)
async def get_tradition_onboarding(
    language: Annotated[
        Optional[str],
        Query(
            description=language_query_description(
                "Localize tradition onboarding content",
                lowercase_example=True,
            )
        ),
    ] = "en",
):
    return await get_tradition_onboarding_service(language=language or "en")


@user_tradition_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=UserTraditionDTO,
    response_model_exclude_none=True,
)
async def save_user_tradition(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    save_request: SaveUserTraditionRequest,
):
    return await save_user_tradition_service(
        token=authentication_credential.credentials,
        save_request=save_request,
    )


@user_tradition_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=UserTraditionsResponse,
    response_model_exclude_none=True,
)
async def get_user_traditions(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return await get_user_traditions_service(
        token=authentication_credential.credentials,
    )


@user_tradition_router.put(
    "/{user_tradition_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserTraditionDTO,
    response_model_exclude_none=True,
)
async def update_user_tradition(
    user_tradition_id: UUID,
    update_request: SaveUserTraditionRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return await update_user_tradition_service(
        token=authentication_credential.credentials,
        user_tradition_id=user_tradition_id,
        update_request=update_request,
    )


@user_tradition_router.delete(
    "/{user_tradition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user_tradition(
    user_tradition_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    await delete_user_tradition_service(
        token=authentication_credential.credentials,
        user_tradition_id=user_tradition_id,
    )
