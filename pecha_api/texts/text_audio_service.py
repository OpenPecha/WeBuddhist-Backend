import logging
import mimetypes
import os
import uuid
from typing import Optional

from fastapi import HTTPException, UploadFile
from starlette import status

from pecha_api.config import DEFAULTS, get, get_int
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.uploads.S3_utils import (
    delete_file,
    generate_presigned_access_url,
    upload_file,
)

from .text_audio_models import TextAudio, TextAudioResponse, utc_now
from .texts_models import Text


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


def to_text_audio_response(audio: TextAudio) -> TextAudioResponse:
    return TextAudioResponse(
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


async def get_required_text(text_id: str) -> Text:
    text = await Text.get_text(text_id=text_id)
    if not text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Text not found.",
        )
    return text


async def get_text_audio(token: str, text_id: str) -> Optional[TextAudioResponse]:
    validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)
    audio = await TextAudio.find_one(TextAudio.text_id == text_id)
    return to_text_audio_response(audio) if audio else None


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
    existing = await TextAudio.find_one(TextAudio.text_id == text_id)

    file.file.seek(0)
    upload_file(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=new_audio_key,
        file=file,
    )

    try:
        now = utc_now()
        if existing:
            old_audio_key = existing.audio_key
            existing.text_title = text.title
            existing.audio_key = new_audio_key
            existing.file_name = file.filename or f"audio{extension}"
            existing.mime_type = content_type
            existing.file_size_bytes = file.size
            existing.duration_ms = duration_ms
            existing.created_by = current_author.email
            existing.updated_at = now
            await existing.save()
            audio = existing
        else:
            old_audio_key = None
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
            await audio.insert()
    except Exception:
        delete_file(new_audio_key)
        raise

    if old_audio_key and old_audio_key != new_audio_key:
        try:
            delete_file(old_audio_key)
        except HTTPException:
            logging.exception("Failed to remove replaced text audio: %s", old_audio_key)

    return to_text_audio_response(audio)


async def delete_text_audio(token: str, text_id: str) -> None:
    validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)
    audio = await TextAudio.find_one(TextAudio.text_id == text_id)
    if not audio:
        return
    delete_file(audio.audio_key)
    await audio.delete()
