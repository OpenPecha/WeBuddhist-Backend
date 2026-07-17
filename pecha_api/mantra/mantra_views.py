from fastapi import APIRouter, Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Annotated, Optional
from starlette import status

from pecha_api.plans.language_constants import language_query_description
from .mantra_response_models import CreateMantraRequest, MantraDTO, MantraResponse
from .mantra_service import create_mantra_service, get_mantras_service

oauth2_scheme = HTTPBearer()

mantra_router = APIRouter(
    prefix="/mantra",
    tags=["Mantra"]
)

cms_mantra_router = APIRouter(
    prefix="/cms/mantras",
    tags=["CMS Mantras"],
)


@mantra_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=MantraResponse
)
def get_mantras_endpoint(
    language: Annotated[Optional[str], Query(description=language_query_description("Filter by language code", lowercase_example=True))] = None,
    x_timezone: Annotated[
        Optional[str],
        Header(alias="X-Timezone", description="IANA timezone (e.g. Asia/Shanghai). Restricted mantras are hidden for Chinese timezones."),
    ] = None,
):

    return get_mantras_service(language=language, timezone_name=x_timezone)


@cms_mantra_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=MantraDTO,
)
def create_mantra_endpoint(
    create_mantra_request: CreateMantraRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> MantraDTO:
    return create_mantra_service(
        token=authentication_credential.credentials,
        request=create_mantra_request,
    )
