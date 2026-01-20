from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated

from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest
from pecha_api.text_uploader.pipeline import pipeline

oauth2_scheme = HTTPBearer()

text_uploader_router = APIRouter(
    prefix="/text-uploader",
    tags=["Text Uploader"]
)

@text_uploader_router.post("")
async def upload_text(
    text_upload_request: TextUploadRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
    ):
        response = await pipeline(text_upload_request=text_upload_request, token=authentication_credential.credentials)
        return response