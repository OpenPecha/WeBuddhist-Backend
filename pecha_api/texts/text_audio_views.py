from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from .text_audio_models import TextAudioResponse
from .text_audio_service import (
    delete_text_audio,
    get_text_audio,
    upload_text_audio,
)

oauth2_scheme = HTTPBearer()

text_audio_router = APIRouter(
    prefix="/cms/texts",
    tags=["CMS Text Audio"],
)


@text_audio_router.get("/{text_id}/audio")
async def fetch_text_audio(
    text_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> Optional[TextAudioResponse]:
    return await get_text_audio(
        token=authentication_credential.credentials,
        text_id=text_id,
    )


@text_audio_router.post(
    "/{text_id}/audio",
    status_code=status.HTTP_201_CREATED,
)
async def replace_text_audio(
    text_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    file: Annotated[UploadFile, File()],
    duration_ms: Annotated[Optional[int], Form()] = None,
) -> TextAudioResponse:
    return await upload_text_audio(
        token=authentication_credential.credentials,
        text_id=text_id,
        file=file,
        duration_ms=duration_ms,
    )


@text_audio_router.delete(
    "/{text_id}/audio",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_text_audio(
    text_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> Response:
    await delete_text_audio(
        token=authentication_credential.credentials,
        text_id=text_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
