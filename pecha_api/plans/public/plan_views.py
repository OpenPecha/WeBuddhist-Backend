from fastapi import APIRouter, Query, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, Optional
from uuid import UUID
from datetime import date as DateType
from starlette import status

from pecha_api.plans.public.plan_response_models import PublicPlansResponse, PublicPlanDTO,PlanDaysResponse , PlanDayDTO, TagsResponse, DailyPlanResponse
from pecha_api.plans.public.plan_service import (
    get_published_plans, 
    get_published_plan, 
    get_plan_days,
    get_plan_day_details,
    get_plan_daily_content,
    get_tags,
    auto_enroll_plan
)
from pecha_api.users.users_service import validate_and_extract_user_details

optional_oauth2_scheme = HTTPBearer(auto_error=False)


# Create router for public plan endpoints
public_plans_router = APIRouter(
    prefix="/plans",
    tags=["Public Plans"]
)


@public_plans_router.get("", status_code=status.HTTP_200_OK, response_model=PublicPlansResponse)
async def get_plans(
    tag: Annotated[Optional[str], Query(description="Filter by tag")] = None,
    group_id: Annotated[Optional[UUID], Query(description="Filter by author group")] = None,
    search: Annotated[Optional[str], Query(description="Search by plan title")] = None,
    language: Annotated[
        str,
        Query(description="Filter by language code (e.g., 'bo', 'en', 'zh'). Defaults to 'en'."),
    ] = "en",
    sort_by: Annotated[str, Query(enum=["title", "total_days", "subscription_count"])] = "title",
    sort_order: Annotated[str, Query(enum=["asc", "desc"])] = "asc",
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    return await get_published_plans(
        tag=tag,
        group_id=group_id,
        search=search,
        language=language,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )


@public_plans_router.get(
    "/tags", status_code=status.HTTP_200_OK, response_model=TagsResponse
)
def get_plan_tags(
    language: Annotated[
        str,
        Query(description="Filter by language code (e.g., 'bo', 'en', 'zh'). Defaults to 'en'."),
    ] = "en",
):
    return get_tags(language=language)


@public_plans_router.get("/{plan_id}", status_code=status.HTTP_200_OK, response_model=PublicPlanDTO)
async def get_plan_details(plan_id: UUID):
    return await get_published_plan(plan_id=plan_id)


@public_plans_router.get("/{plan_id}/daily", status_code=status.HTTP_200_OK, response_model=DailyPlanResponse)

async def get_plan_daily(
    plan_id: UUID,
    date: Annotated[
        Optional[DateType],
        Query(description="Date in YYYY-MM-DD format. Defaults to today if not provided."),
    ] = None,
):
    return await get_plan_daily_content(plan_id=plan_id, requested_date=date)


@public_plans_router.get("/{plan_id}/days", status_code=status.HTTP_200_OK, response_model=PlanDaysResponse)
async def get_plan_days_list(
    plan_id: UUID,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(optional_oauth2_scheme)]
):
    user_id = None
    if credentials:
        try:
            user = validate_and_extract_user_details(token=credentials.credentials)
            user_id = user.id
        except Exception:
            pass
    
    auto_enroll_plan(plan_id=plan_id, user_id=user_id)
    return await get_plan_days(plan_id=plan_id)


@public_plans_router.get("/{plan_id}/days/{day_number}", status_code=status.HTTP_200_OK, response_model=PlanDayDTO)
async def get_plan_day_content(plan_id: UUID, day_number: int):
    """Get specific day's content with tasks"""
    return get_plan_day_details(plan_id=plan_id, day_number=day_number)
