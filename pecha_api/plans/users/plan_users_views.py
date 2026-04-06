from fastapi import APIRouter, Query, Depends
from typing import Optional
from uuid import UUID
from starlette import status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated

from pecha_api.plans.plans_response_models import PlansResponse
from pecha_api.plans.users.plan_users_response_models import (
    UserPlanEnrollRequest, 
    UserPlanProgressResponse, 
    UserPlanDayDetailsResponse,
    UserPlansResponse,
    UserPlanDayCompletionStatusResponse
)

from pecha_api.plans.users.plan_users_service import (
    get_user_enrolled_plans,
    enroll_user_in_plan,
    get_user_plan_days_completion_status_service,
    unenroll_user_from_plan,
    get_user_plan_progress,
    complete_task_service,
    complete_sub_task_service,
    delete_task_service,
    get_user_plan_day_details_service
)


oauth2_scheme = HTTPBearer()

user_progress_router = APIRouter(
    prefix="/users/me",
    tags=["User Progress"]
)


@user_progress_router.get("/plans", status_code=status.HTTP_200_OK, response_model=UserPlansResponse)
async def get_user_plans(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    status_filter: Optional[str] = Query(None, description="Filter by plan status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50)
):
    return await get_user_enrolled_plans(token=authentication_credential.credentials,status_filter=status_filter,skip=skip,limit=limit)


@user_progress_router.post("/plans", status_code=status.HTTP_204_NO_CONTENT)
def enroll_in_plan(
    enroll_request: UserPlanEnrollRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    enroll_user_in_plan(
        token=authentication_credential.credentials,
        enroll_request=enroll_request
    )

@user_progress_router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def unenroll_from_plan(
    plan_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    unenroll_user_from_plan(
        token=authentication_credential.credentials,
        plan_id=plan_id
    )

@user_progress_router.get("/plans/{plan_id}", status_code=status.HTTP_200_OK, response_model=UserPlanProgressResponse)
async def get_user_plan_progress_details(
    plan_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    """Get user's progress for specific plan"""
    return get_user_plan_progress(
        token=authentication_credential.credentials,
        plan_id=plan_id
    )

@user_progress_router.get("/plans/{plan_id}/days/completion_status", status_code=status.HTTP_200_OK, response_model=UserPlanDayCompletionStatusResponse)
async def get_user_plan_days_completion_status(
    plan_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    return await get_user_plan_days_completion_status_service(token=authentication_credential.credentials, plan_id=plan_id)

@user_progress_router.post("/sub-tasks/{sub_task_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
def complete_sub_task(
    sub_task_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    complete_sub_task_service(
        token=authentication_credential.credentials,
        id=sub_task_id
    )

@user_progress_router.post("/tasks/{task_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
def complete_task(
    task_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    return complete_task_service(
        token=authentication_credential.credentials,
        task_id=task_id
    )


@user_progress_router.delete("/task/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    return delete_task_service(
        token=authentication_credential.credentials,
        task_id=task_id
    )


@user_progress_router.get("/plan/{plan_id}/days/{day_number}", status_code=status.HTTP_200_OK, response_model=UserPlanDayDetailsResponse)
async def get_user_plan_day_details(
    plan_id: UUID,
    day_number: int,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    return get_user_plan_day_details_service(
        token=authentication_credential.credentials,
        plan_id=plan_id,
        day_number=day_number
    )