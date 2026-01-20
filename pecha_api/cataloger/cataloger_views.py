from __future__ import annotations
from typing import Optional
from fastapi import APIRouter,Query
from fastapi.security import HTTPBearer
from starlette import status
from pecha_api.cataloger.cataloger_service import (
    get_cataloged_texts_details,
    get_cataloged_texts,
)
from pecha_api.cataloger.cataloger_response_model import CatalogedTextsDetailsResponse


oauth2_scheme = HTTPBearer()
cataloger_router = APIRouter(prefix="/cataloger", tags=["cataloger"])


@cataloger_router.get("/texts", status_code=status.HTTP_200_OK)
async def read_cataloged_texts(
    search: Optional[str] = Query(default=None, description="Search by text title"),
    skip: int = Query(default=0),
    limit: int = Query(default=10)
):
    return await get_cataloged_texts(search=search, skip=skip, limit=limit)

@cataloger_router.get("/texts/{text_id}", status_code=status.HTTP_200_OK, response_model=CatalogedTextsDetailsResponse)
async def read_cataloged_texts_details(
        text_id: str
)->CatalogedTextsDetailsResponse:
    return await get_cataloged_texts_details(
        text_id=text_id
    )
