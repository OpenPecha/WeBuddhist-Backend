from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.recitations.recitations_services import (
    get_list_of_recitations_service,
    get_recitation_details_service,
)
from pecha_api.recitations.recitations_response_models import (
    RecitationsResponse,
    ListRecitationsRequest,
    RecitationDetailsRequest,
    RecitationDetailsResponse,
)

optional_oauth2_scheme = HTTPBearer(auto_error=False)

recitation_router = APIRouter(
    prefix="/recitations",
    tags=["Recitations"],
)


@recitation_router.get("", status_code=status.HTTP_200_OK, response_model=RecitationsResponse)
async def get_list_of_recitations(
    search: Optional[str] = Query(None, description="Search by Recitation title"),
    language: str = Query(),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    should_include_collections: Annotated[
        bool,
        Query(description="Include the user's individual recitation collections (requires auth)"),
    ] = False,
    should_include_group_collections: Annotated[
        bool,
        Query(
            description=(
                "Include group recitation collections from groups the user follows "
                "or has joined (requires auth)"
            )
        ),
    ] = False,
    x_timezone: Annotated[
        Optional[str],
        Header(
            alias="X-Timezone",
            description=(
                "IANA timezone (e.g. Asia/Shanghai). Restricted recitations are "
                "hidden for Chinese timezones."
            ),
        ),
    ] = None,
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(optional_oauth2_scheme),
    ] = None,
) -> RecitationsResponse:
    token = credentials.credentials if credentials else None
    return await get_list_of_recitations_service(
        request=ListRecitationsRequest(
            search=search,
            language=language,
            skip=skip,
            limit=limit,
            timezone_name=x_timezone,
            token=token,
            should_include_collections=should_include_collections,
            should_include_group_collections=should_include_group_collections,
        )
    )


@recitation_router.post("/{text_id}", status_code=status.HTTP_200_OK, response_model=RecitationDetailsResponse)
async def get_recitation_details(
    text_id: str,
    recitation_details_request: RecitationDetailsRequest,
    x_timezone: Annotated[
        Optional[str],
        Header(
            alias="X-Timezone",
            description=(
                "IANA timezone (e.g. Asia/Shanghai). Restricted recitations are "
                "hidden for Chinese timezones."
            ),
        ),
    ] = None,
) -> RecitationDetailsResponse:
    return await get_recitation_details_service(
        text_id=text_id,
        recitation_details_request=recitation_details_request,
        timezone_name=x_timezone,
    )
