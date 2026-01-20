from __future__ import annotations
from fastapi import APIRouter, Query
from fastapi.security import HTTPBearer
from starlette import status

from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.security import HTTPAuthorizationCredentials
from typing import Annotated

from .sheets_enum import (
    SortBy, 
    SortOrder
)
from .sheets_service import (
    create_new_sheet, 
    upload_sheet_image_request, 
    fetch_sheets,
    get_sheet_by_id,
    update_sheet_by_id,
    delete_sheet_by_id
)

from pecha_api.sheets.sheets_response_models import SheetIdResponse

from .sheets_response_models import (
    CreateSheetRequest,
    SheetDetailDTO,
    SheetDTOResponse
)

oauth2_scheme = HTTPBearer()
sheets_router = APIRouter(
    prefix="/sheets",
    tags=["Sheets"]
)

@sheets_router.get("", status_code=status.HTTP_200_OK)
async def get_sheets(
    authentication_credential: Annotated[Optional[HTTPAuthorizationCredentials], Depends(HTTPBearer(auto_error=False))],
    language: Optional[str] = Query(default=None),
    email: Optional[str] = Query(default=None),
    sort_by: Optional[SortBy] = Query(default=None),
    sort_order: Optional[SortOrder] = Query(default=None),
    skip: int = Query(default=0),
    limit: int = Query(default=10)
) -> SheetDTOResponse:
    return await fetch_sheets(
        token=authentication_credential.credentials if authentication_credential else None,
        language=language,
        email=email,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit
    )

@sheets_router.get("/{sheet_id}", status_code=status.HTTP_200_OK)
async def get_sheet(
    sheet_id: str,
    skip: int = Query(default=0),
    limit: int = Query(default=10)
) -> SheetDetailDTO:
    return await get_sheet_by_id(sheet_id=sheet_id, skip=skip, limit=limit)

@sheets_router.post("", status_code=status.HTTP_201_CREATED)
async def create_sheet(
    create_sheet_request: CreateSheetRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> SheetIdResponse:
    return await create_new_sheet(
        create_sheet_request=create_sheet_request,
        token=authentication_credential.credentials
    )


@sheets_router.put("/{sheet_id}", status_code=status.HTTP_200_OK)
async def update_sheet(
    sheet_id: str,
    update_sheet_request: CreateSheetRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> SheetIdResponse:
    return await update_sheet_by_id(
        sheet_id=sheet_id,
        update_sheet_request=update_sheet_request,
        token=authentication_credential.credentials
    )

@sheets_router.delete("/{sheet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sheet(
    sheet_id: str,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    await delete_sheet_by_id(
        sheet_id=sheet_id,
        token=authentication_credential.credentials
    )

@sheets_router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_sheet_image(sheet_id: Optional[str] = None, file: UploadFile = File(...)):
    return upload_sheet_image_request(sheet_id=sheet_id, file=file)
