from fastapi import APIRouter, Query
from fastapi.security import HTTPBearer
from starlette import status

from .featured_day_service import get_featured_day_service
from .featured_day_response_model import PlanDayDTO


oauth2_scheme = HTTPBearer()
user_follow_router = APIRouter(
    prefix="/plans/featured", 
    tags=["Featured Plans"]
    )


@user_follow_router.get("/day", status_code=status.HTTP_200_OK, response_model=PlanDayDTO)
async def get_featured_day(language: str = Query("en")) -> PlanDayDTO:
    return await get_featured_day_service(language=language)