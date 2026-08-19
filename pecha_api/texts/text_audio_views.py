from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from .text_audio_models import (
    TextAudioOtrContentResponse,
    TextAudioOtrResponse,
    TextAudioResponse,
    TextAudioSegmentsResponse,
    UpdateTextAudioNameRequest,
)
from .text_audio_service import (
    delete_text_audio,
    delete_text_audio_otr,
    get_text_audio_otr_content,
    get_text_audio_otrs,
    get_text_audios,
    get_text_segments_in_order,
    update_text_audio_name,
    upload_text_audio,
    upload_text_audio_otr,
)

oauth2_scheme = HTTPBearer()

text_audio_router = APIRouter(
    prefix="/cms/texts",
    tags=["CMS Text Audio"],
)


@text_audio_router.get("/{text_id}/audios")
async def fetch_text_audios(
    text_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> List[TextAudioResponse]:
    return await get_text_audios(
        token=authentication_credential.credentials,
        text_id=text_id,
    )


@text_audio_router.post(
    "/{text_id}/audios",
    status_code=status.HTTP_201_CREATED,
)
async def add_text_audio(
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


@text_audio_router.patch("/{text_id}/audios/{audio_id}")
async def rename_text_audio(
    text_id: str,
    audio_id: str,
    request: UpdateTextAudioNameRequest,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> TextAudioResponse:
    return await update_text_audio_name(
        token=authentication_credential.credentials,
        text_id=text_id,
        audio_id=audio_id,
        request=request,
    )


@text_audio_router.delete(
    "/{text_id}/audios/{audio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_text_audio(
    text_id: str,
    audio_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> Response:
    await delete_text_audio(
        token=authentication_credential.credentials,
        text_id=text_id,
        audio_id=audio_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@text_audio_router.get("/{text_id}/segments")
async def fetch_text_segments(
    text_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> TextAudioSegmentsResponse:
    return await get_text_segments_in_order(
        token=authentication_credential.credentials,
        text_id=text_id,
    )


@text_audio_router.get("/{text_id}/audios/{audio_id}/otr")
async def fetch_text_audio_otrs(
    text_id: str,
    audio_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> List[TextAudioOtrResponse]:
    return await get_text_audio_otrs(
        token=authentication_credential.credentials,
        text_id=text_id,
        audio_id=audio_id,
    )


@text_audio_router.post(
    "/{text_id}/audios/{audio_id}/otr",
    status_code=status.HTTP_201_CREATED,
)
async def add_text_audio_otr(
    text_id: str,
    audio_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    file: Annotated[UploadFile, File()],
    name: Annotated[Optional[str], Form()] = None,
) -> TextAudioOtrResponse:
    return await upload_text_audio_otr(
        token=authentication_credential.credentials,
        text_id=text_id,
        audio_id=audio_id,
        file=file,
        name=name,
    )


@text_audio_router.get("/{text_id}/audios/{audio_id}/otr/{otr_id}")
async def fetch_text_audio_otr_json(
    text_id: str,
    audio_id: str,
    otr_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> TextAudioOtrContentResponse:
    return await get_text_audio_otr_content(
        token=authentication_credential.credentials,
        text_id=text_id,
        audio_id=audio_id,
        otr_id=otr_id,
    )


@text_audio_router.delete(
    "/{text_id}/audios/{audio_id}/otr/{otr_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_text_audio_otr(
    text_id: str,
    audio_id: str,
    otr_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> Response:
    await delete_text_audio_otr(
        token=authentication_credential.credentials,
        text_id=text_id,
        audio_id=audio_id,
        otr_id=otr_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
