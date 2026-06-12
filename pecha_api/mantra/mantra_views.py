from fastapi import APIRouter, Query
from typing import Annotated, Optional
from starlette import status

from .mantra_response_models import MantraResponse
from .mantra_service import get_mantras_service

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
