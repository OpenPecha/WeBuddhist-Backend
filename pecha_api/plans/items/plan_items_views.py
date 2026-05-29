from fastapi import APIRouter
from .plan_items_response_models import ItemDTO, ReorderDaysRequest, CreateDaysRequest, DeleteDaysRequest
from .plan_items_services import create_plan_item, delete_plan_days, update_plans_day_number
from pecha_api.plans.audio.plan_day_audio_service import delete_plan_day_audio
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from starlette import status
from uuid import UUID
from typing import Annotated, List
oauth2_scheme = HTTPBearer()

items_router = APIRouter(
    prefix="/cms/plans",
    tags=["Items"],
)

@items_router.post("/{plan_id}/days", status_code=status.HTTP_201_CREATED, response_model=List[ItemDTO])
async def create_new_item(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    plan_id: UUID,
    create_days_request: CreateDaysRequest = CreateDaysRequest(),
):
    return create_plan_item(
        token=authentication_credential.credentials,
        plan_id=plan_id,
        create_days_request=create_days_request,
    )

@items_router.delete("/{plan_id}/days", status_code=status.HTTP_204_NO_CONTENT)
async def delete_items(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    plan_id: UUID,
    delete_days_request: DeleteDaysRequest,
):
    return delete_plan_days(
        token=authentication_credential.credentials,
        plan_id=plan_id,
        delete_days_request=delete_days_request,
    )


@items_router.delete("/days/{day_id}/audio", status_code=status.HTTP_204_NO_CONTENT)
async def delete_day_audio(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    day_id: UUID,
):
    return delete_plan_day_audio(
        token=authentication_credential.credentials,
        day_id=day_id,
    )


@items_router.put("/{plan_id}/reorder-days", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_days(authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
                      plan_id: UUID,
                      reorder_days_request: ReorderDaysRequest):
    update_plans_day_number(
        token=authentication_credential.credentials,
        plan_id=plan_id,
        reorder_days_request=reorder_days_request
    )