import asyncio
import json
import logging
import mimetypes
import os
import uuid
from typing import Any, Dict, List, Optional

from beanie import PydanticObjectId
from fastapi import HTTPException, UploadFile
from pymongo.errors import DuplicateKeyError
from starlette import status

from pecha_api.config import DEFAULTS, get, get_int
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.uploads.S3_utils import (
    delete_file,
    generate_presigned_access_url,
    upload_file,
)

from .text_audio_models import (
    TextAudio,
    TextAudioOtr,
    TextAudioOtrResponse,
    TextAudioResponse,
    utc_now,
)
from .texts_models import Text

INVALID_OTR_DETAIL = "Upload a valid OTR/JSON file."


def validate_text_audio_file(file: UploadFile) -> str:
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
    return extension


def validate_otr_file(file: UploadFile) -> None:
    extension = os.path.splitext(file.filename or "")[1].lower()
    if extension not in DEFAULTS["ALLOWED_OTR_EXTENSIONS"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_OTR_DETAIL,
        )
    if file.size and file.size > get_int("MAX_OTR_FILE_SIZE"):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="OTR file is too large.",
        )


def parse_otr_content(raw: bytes) -> Dict[str, Any]:
    """OTR files are JSON documents; only a JSON object is accepted so the
    content can be stored and served back as JSON."""
    try:
        content = json.loads(raw)
    except (UnicodeDecodeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_OTR_DETAIL,
        )
    if not isinstance(content, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_OTR_DETAIL,
        )
    return content


def to_text_audio_response(audio: TextAudio) -> TextAudioResponse:
    return TextAudioResponse(
        id=str(audio.id),
        text_id=audio.text_id,
        text_title=audio.text_title,
        audio_key=audio.audio_key,
        audio_url=generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=audio.audio_key,
        ),
        file_name=audio.file_name,
        mime_type=audio.mime_type,
        file_size_bytes=audio.file_size_bytes,
        duration_ms=audio.duration_ms,
        updated_at=audio.updated_at,
    )


def to_text_audio_otr_response(otr: TextAudioOtr) -> TextAudioOtrResponse:
    return TextAudioOtrResponse(
        id=str(otr.id),
        audio_id=otr.audio_id,
        name=otr.name,
        file_name=otr.file_name,
        updated_at=otr.updated_at,
    )


async def get_required_text(text_id: str) -> Text:
    text = await Text.get_text(text_id=text_id)
    if not text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Text not found.",
        )
    return text


async def get_required_audio(text_id: str, audio_id: str) -> TextAudio:
    audio = None
    if PydanticObjectId.is_valid(audio_id):
        audio = await TextAudio.get(PydanticObjectId(audio_id))
    if not audio or audio.text_id != text_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found.",
        )
    return audio


async def get_required_otr(audio_id: str, otr_id: str) -> TextAudioOtr:
    otr = None
    if PydanticObjectId.is_valid(otr_id):
        otr = await TextAudioOtr.get(PydanticObjectId(otr_id))
    if not otr or otr.audio_id != audio_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OTR not found.",
        )
    return otr


async def get_text_audios(token: str, text_id: str) -> List[TextAudioResponse]:
    validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)
    audios = (
        await TextAudio.find(TextAudio.text_id == text_id)
        .sort("-created_at")
        .to_list()
    )
    return [to_text_audio_response(audio) for audio in audios]


async def upload_text_audio(
    token: str,
    text_id: str,
    file: UploadFile,
    duration_ms: Optional[int] = None,
) -> TextAudioResponse:
    current_author = validate_cms_author_details(token=token)
    text = await get_required_text(text_id=text_id)
    extension = validate_text_audio_file(file)
    content_type = (
        file.content_type
        or mimetypes.guess_type(file.filename or "")[0]
        or "audio/mpeg"
    )
    new_audio_key = f"audio/texts/{uuid.uuid4()}{extension}"
    now = utc_now()
    loop = asyncio.get_event_loop()

    file.file.seek(0)
    await loop.run_in_executor(
        None,
        lambda: upload_file(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=new_audio_key,
            file=file,
        ),
    )

    audio = TextAudio(
        text_id=text_id,
        text_title=text.title,
        audio_key=new_audio_key,
        file_name=file.filename or f"audio{extension}",
        mime_type=content_type,
        file_size_bytes=file.size,
        duration_ms=duration_ms,
        created_by=current_author.email,
        created_at=now,
        updated_at=now,
    )
    try:
        await audio.insert()
    except Exception:
        await loop.run_in_executor(None, lambda: delete_file(new_audio_key))
        raise
    return to_text_audio_response(audio)


async def delete_text_audio(token: str, text_id: str, audio_id: str) -> None:
    validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)
    audio = await get_required_audio(text_id=text_id, audio_id=audio_id)
    audio_pk = str(audio.id)
    keys_to_delete = list(dict.fromkeys(
        key for key in [audio.audio_key, *audio.pending_cleanup_keys] if key
    ))
    loop = asyncio.get_event_loop()

    # Delete the audio metadata first (source of truth). Once this succeeds,
    # the audio no longer exists from the application's perspective - it is
    # unreachable via get_required_audio - so a subsequent failure to remove
    # its OTR transcripts or S3 objects below only leaves orphaned data
    # behind instead of a record that still points at children which no
    # longer exist (OTRs) or a file that no longer exists (S3).
    await audio.delete()

    try:
        await TextAudioOtr.find(TextAudioOtr.audio_id == audio_pk).delete()
    except Exception:
        logging.exception(
            "Failed to remove OTR transcripts for deleted audio %s. Records orphaned.",
            audio_pk,
        )

    for key in keys_to_delete:
        try:
            await loop.run_in_executor(None, lambda k=key: delete_file(k))
        except HTTPException as e:
            logging.exception("Failed to remove text audio from S3 %s: %s. Object orphaned.", key, e)


async def get_text_audio_otrs(
    token: str,
    text_id: str,
    audio_id: str,
) -> List[TextAudioOtrResponse]:
    validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)
    audio = await get_required_audio(text_id=text_id, audio_id=audio_id)
    otrs = (
        await TextAudioOtr.find(TextAudioOtr.audio_id == str(audio.id))
        .sort("+name")
        .to_list()
    )
    return [to_text_audio_otr_response(otr) for otr in otrs]


async def upload_text_audio_otr(
    token: str,
    text_id: str,
    audio_id: str,
    file: UploadFile,
    name: Optional[str] = None,
) -> TextAudioOtrResponse:
    current_author = validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)
    audio = await get_required_audio(text_id=text_id, audio_id=audio_id)
    validate_otr_file(file)
    content = parse_otr_content(await file.read())
    otr_name = (name or os.path.splitext(file.filename or "")[0]).strip()
    if not otr_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTR name is required.",
        )
    now = utc_now()
    otr = TextAudioOtr(
        audio_id=str(audio.id),
        text_id=text_id,
        name=otr_name,
        file_name=file.filename or f"{otr_name}.json",
        content=content,
        created_by=current_author.email,
        created_at=now,
        updated_at=now,
    )
    try:
        await otr.insert()
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An OTR with this name already exists for this audio.",
        )
    return to_text_audio_otr_response(otr)


async def get_text_audio_otr_content(
    token: str,
    text_id: str,
    audio_id: str,
    otr_id: str,
) -> Dict[str, Any]:
    validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)
    audio = await get_required_audio(text_id=text_id, audio_id=audio_id)
    otr = await get_required_otr(audio_id=str(audio.id), otr_id=otr_id)
    return otr.content


async def delete_text_audio_otr(
    token: str,
    text_id: str,
    audio_id: str,
    otr_id: str,
) -> None:
    validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)
    audio = await get_required_audio(text_id=text_id, audio_id=audio_id)
    otr = await get_required_otr(audio_id=str(audio.id), otr_id=otr_id)
    await otr.delete()
