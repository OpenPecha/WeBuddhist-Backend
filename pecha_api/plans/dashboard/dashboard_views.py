from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.plans.dashboard.dashboard_response_models import (
    DashboardItemsResponse,
    DashboardTab,
)
from pecha_api.plans.dashboard.dashboard_service import get_dashboard_items_list
from pecha_api.plans.plans_enums import PlanStatus

oauth2_scheme = HTTPBearer()

dashboard_router = APIRouter(
    prefix="/cms/dashboard",
    tags=["CMS Dashboard"],
)


@dashboard_router.get(
    "/items",
    status_code=status.HTTP_200_OK,
    response_model=DashboardItemsResponse,
)
async def list_dashboard_items(
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    tab: DashboardTab = Query(default="all"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None),
    status: Optional[PlanStatus] = Query(default=None),
    language: Optional[str] = Query(default=None),
    featured: Optional[bool] = Query(default=None),
    sort: Optional[str] = Query(default=None, description="Reserved; default sort is applied"),
):
    return await get_dashboard_items_list(
        token=authentication_credential.credentials,
        tab=tab,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        language=language,
        featured=featured,
    )
