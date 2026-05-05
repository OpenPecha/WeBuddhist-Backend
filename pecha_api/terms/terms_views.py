
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status
from typing import Annotated, Optional

from ..terms.terms_response_models import CreateTermRequest, UpdateTermRequest
from ..terms.terms_service import get_all_terms, create_new_term, update_existing_term, delete_existing_term

oauth2_scheme = HTTPBearer()
terms_router = APIRouter(
    prefix="/terms",
    tags=["Terms"]
)


@terms_router.get(
    "",
    status_code=status.HTTP_200_OK,
    deprecated=True,
    summary="Get terms (DEPRECATED)",
    description="**DEPRECATED**: This endpoint will be removed on June 1, 2026. Please migrate to /api/v2/terms."
)
async def read_terms(
        parent_id: Optional[str] = Query(None, description="Filter topics by title prefix"),
        language: Optional[str] = None,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(default=10, ge=1, le=100, description="Number of records to return")
):
    return await get_all_terms(
        parent_id=parent_id,
        language=language,
        skip=skip,
        limit=limit
    )


@terms_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    deprecated=True,
    summary="Create term (DEPRECATED)",
    description="**DEPRECATED**: This endpoint will be removed on June 1, 2026. Please migrate to /api/v2/terms."
)
async def create_terms(language: str | None, create_term_request: CreateTermRequest,
                       authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]):
    return await create_new_term(
        create_term_request=create_term_request,
        token=authentication_credential.credentials,
        language=language
    )


@terms_router.put(
    "{term_id}",
    status_code=status.HTTP_202_ACCEPTED,
    deprecated=True,
    summary="Update term (DEPRECATED)",
    description="**DEPRECATED**: This endpoint will be removed on June 1, 2026. Please migrate to /api/v2/terms."
)
async def update_term_by_id(term_id: str, language: str | None, update_term_request: UpdateTermRequest,
                            authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]):
    return await update_existing_term(
        term_id=term_id,
        update_term_request=update_term_request,
        token=authentication_credential.credentials,
        language=language
    )


@terms_router.delete(
    "/terms{term_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
    summary="Delete term (DEPRECATED)",
    description="**DEPRECATED**: This endpoint will be removed on June 1, 2026. Please migrate to /api/v2/terms."
)
async def delete_term_by_id(term_id: str,
                            authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]):
    return await delete_existing_term(
        term_id=term_id,
        token=authentication_credential.credentials
    )
