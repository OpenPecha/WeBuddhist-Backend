from datetime import date
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.plans.analytics.analytics_response_models import AnalyticsOverviewResponse
from pecha_api.plans.analytics.analytics_service import get_analytics_overview

oauth2_scheme = HTTPBearer()

analytics_router = APIRouter(
    prefix="/cms/analytics",
    tags=["CMS Analytics"],
)


@analytics_router.get(
    "/overview",
    status_code=status.HTTP_200_OK,
    response_model=AnalyticsOverviewResponse,
)
def get_cms_analytics_overview(
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    start_date: Annotated[
        Optional[date],
        Query(description="Inclusive start date (UTC). Defaults to 30 days ago."),
    ] = None,
    end_date: Annotated[
        Optional[date],
        Query(description="Inclusive end date (UTC). Defaults to today."),
    ] = None,
    group_id: Annotated[
        Optional[UUID],
        Query(description="Optional author group filter"),
    ] = None,
    top_limit: Annotated[
        int,
        Query(ge=1, le=50, description="Number of top plans to return"),
    ] = 10,
):
    return get_analytics_overview(
        token=authentication_credential.credentials,
        start_date=start_date,
        end_date=end_date,
        group_id=group_id,
        top_limit=top_limit,
    )
