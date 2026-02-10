from fastapi import APIRouter, UploadFile, File, status, Depends, Query, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .media_services import upload_plan_image, upload_text_image
from .media_response_models import PlanUploadResponse, TextImageUploadResponse
from typing import Annotated, Optional

oauth2_scheme = HTTPBearer()

media_router = APIRouter(
    prefix="/cms/media",
    tags=["Media"]
)


@media_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_media_image(authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)], plan_id: Optional[str] = Query(None), file: UploadFile = File(...)) -> PlanUploadResponse:
    return upload_plan_image(token=authentication_credential.credentials, plan_id=plan_id, file=file)


@media_router.post("/upload/text", status_code=status.HTTP_201_CREATED)
async def upload_text_media_image(authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)], text_id: str = Form(...), file: UploadFile = File(...)) -> TextImageUploadResponse:
    return await upload_text_image(token=authentication_credential.credentials, text_id=text_id, file=file)
