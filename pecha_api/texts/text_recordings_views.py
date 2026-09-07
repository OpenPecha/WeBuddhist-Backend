from typing import Annotated, List

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from .text_recordings_models import (
    RecordingCreateMetadata,
    RecordingPatchRequest,
    RecordingResponse,
)
from .text_recordings_service import (
    create_edition_recording,
    delete_recording,
    get_edition_recordings,
    get_recording,
    get_recording_audio_redirect_url,
    update_recording,
)

oauth2_scheme = HTTPBearer()

recordings_router = APIRouter(
    prefix="/cms",
    tags=["CMS Recordings"],
)


@recordings_router.get("/editions/{edition_id}/recordings")
async def list_edition_recordings(
    edition_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> List[RecordingResponse]:
    return await get_edition_recordings(
        token=authentication_credential.credentials,
        edition_id=edition_id,
    )


@recordings_router.post(
    "/editions/{edition_id}/recordings",
    status_code=status.HTTP_201_CREATED,
)
async def add_edition_recording(
    edition_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    audio: Annotated[UploadFile, File()],
    metadata: Annotated[str, Form()],
) -> RecordingResponse:
    parsed_metadata = RecordingCreateMetadata.model_validate_json(metadata)
    return await create_edition_recording(
        token=authentication_credential.credentials,
        edition_id=edition_id,
        file=audio,
        metadata=parsed_metadata,
    )


@recordings_router.get("/recordings/{recording_id}")
async def fetch_recording(
    recording_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> RecordingResponse:
    return await get_recording(
        token=authentication_credential.credentials,
        recording_id=recording_id,
    )


@recordings_router.get("/recordings/{recording_id}/audio")
async def fetch_recording_audio(
    recording_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> RedirectResponse:
    location = await get_recording_audio_redirect_url(
        token=authentication_credential.credentials,
        recording_id=recording_id,
    )
    return RedirectResponse(url=location, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@recordings_router.patch("/recordings/{recording_id}")
async def patch_recording(
    recording_id: str,
    request: RecordingPatchRequest,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> RecordingResponse:
    return await update_recording(
        token=authentication_credential.credentials,
        recording_id=recording_id,
        request=request,
    )


@recordings_router.delete(
    "/recordings/{recording_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_recording(
    recording_id: str,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> Response:
    await delete_recording(
        token=authentication_credential.credentials,
        recording_id=recording_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
