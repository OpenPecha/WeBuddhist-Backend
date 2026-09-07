import asyncio
import os
from typing import Any, Dict, List

from fastapi import HTTPException, UploadFile
from starlette import status

from pecha_api.config import DEFAULTS, get_int
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details

from . import recordings_openpecha_api as openpecha_api
from .text_recordings_models import (
    RecordingCreateMetadata,
    RecordingPatchRequest,
    RecordingResponse,
)
from .texts_openpecha_api import fetch_edition_text_id


def validate_recording_audio_file(file: UploadFile) -> None:
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in DEFAULTS["ALLOWED_AUDIO_EXTENSIONS"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported audio file. Use MP3, M4A, WAV, AAC, or OGG.",
        )
    if file.size and file.size > get_int("MAX_AUDIO_FILE_SIZE"):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file is too large.",
        )


async def _to_recording_response(data: Dict[str, Any]) -> RecordingResponse:
    audio_url = await openpecha_api.fetch_recording_audio_location(recording_id=data["id"])
    return RecordingResponse.from_upstream(data, audio_url=audio_url)


async def get_edition_recordings(token: str, edition_id: str) -> List[RecordingResponse]:
    validate_cms_author_details(token=token)
    await fetch_edition_text_id(edition_id=edition_id)
    recordings = await openpecha_api.fetch_edition_recordings(edition_id=edition_id)
    return list(await asyncio.gather(*[_to_recording_response(item) for item in recordings]))


async def create_edition_recording(
    token: str,
    edition_id: str,
    file: UploadFile,
    metadata: RecordingCreateMetadata,
) -> RecordingResponse:
    validate_cms_author_details(token=token)
    await fetch_edition_text_id(edition_id=edition_id)
    validate_recording_audio_file(file)

    content = await file.read()
    recording_id = await openpecha_api.create_edition_recording(
        edition_id=edition_id,
        metadata_json=metadata.to_upstream_json(),
        filename=file.filename or "recording",
        content_type=file.content_type or "application/octet-stream",
        content=content,
    )
    data = await openpecha_api.fetch_recording(recording_id=recording_id)
    return await _to_recording_response(data)


async def get_recording(token: str, recording_id: str) -> RecordingResponse:
    validate_cms_author_details(token=token)
    data = await openpecha_api.fetch_recording(recording_id=recording_id)
    return await _to_recording_response(data)


async def update_recording(
    token: str,
    recording_id: str,
    request: RecordingPatchRequest,
) -> RecordingResponse:
    validate_cms_author_details(token=token)
    payload = request.to_upstream_payload()
    if payload:
        data = await openpecha_api.patch_recording(recording_id=recording_id, payload=payload)
    else:
        data = await openpecha_api.fetch_recording(recording_id=recording_id)
    return await _to_recording_response(data)


async def delete_recording(token: str, recording_id: str) -> None:
    validate_cms_author_details(token=token)
    await openpecha_api.delete_recording(recording_id=recording_id)
