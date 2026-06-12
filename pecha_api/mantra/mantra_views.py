from fastapi import APIRouter, Query
from typing import Annotated, Optional
from starlette import status

from .mantra_response_models import MantraResponse, CreateMantraRequest, MantraDTO
from .mantra_service import get_mantras_service, create_mantra_service

mantra_router = APIRouter(
    prefix="/mantra",
    tags=["Mantra"]
)


@mantra_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=MantraResponse
)
def get_mantras_endpoint(
    language: Annotated[Optional[str], Query(description="Filter by language code (e.g. 'en', 'bo', 'zh')")] = None,
):

    return get_mantras_service(language=language)


@mantra_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=MantraDTO
)
def create_mantra_endpoint(request: CreateMantraRequest):

    return create_mantra_service(request=request)
