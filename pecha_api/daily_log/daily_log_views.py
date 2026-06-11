from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.daily_log.daily_log_response_models import UserStreakResponse
from pecha_api.daily_log.daily_log_service import get_user_streak_service

oauth2_scheme = HTTPBearer()
daily_log_router = APIRouter(
    prefix="/users/me",
    tags=["Daily Log"],
)


@daily_log_router.get("/streak", status_code=status.HTTP_200_OK, response_model=UserStreakResponse)
async def get_user_streak(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> UserStreakResponse:
    return await get_user_streak_service(token=authentication_credential.credentials)
