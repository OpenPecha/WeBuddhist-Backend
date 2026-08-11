import asyncio
import logging
import mimetypes
import os
import uuid
from datetime import datetime
from typing import Optional

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


def _build_audio_metadata(
    text_id: str,
    text_title: str,
    new_audio_key: str,
    file: UploadFile,
    content_type: str,
    duration_ms: Optional[int],
    author_email: str,
    now: datetime,
) -> TextAudio:
    """Build a new TextAudio metadata object."""
    extension = os.path.splitext(file.filename or "")[1].lower()
    return TextAudio(
        text_id=text_id,
        text_title=text_title,
        audio_key=new_audio_key,
        file_name=file.filename or f"audio{extension}",
        mime_type=content_type,
        file_size_bytes=file.size,
        duration_ms=duration_ms,
        created_by=author_email,
        created_at=now,
        updated_at=now,
    )


def _update_audio_metadata(
    audio: TextAudio,
    text_title: str,
    new_audio_key: str,
    file: UploadFile,
    content_type: str,
    duration_ms: Optional[int],
    author_email: str,
    now: datetime,
) -> None:
    """Update existing TextAudio metadata fields."""
    extension = os.path.splitext(file.filename or "")[1].lower()
    audio.text_title = text_title
    audio.audio_key = new_audio_key
    audio.file_name = file.filename or f"audio{extension}"
    audio.mime_type = content_type
    audio.file_size_bytes = file.size
    audio.duration_ms = duration_ms
    audio.created_by = author_email
    audio.updated_at = now


async def _persist_audio_metadata(
    text_id: str,
    new_audio_key: str,
    audio_metadata: TextAudio,
    loop,
) -> tuple[TextAudio, Optional[str]]:
    """Persist audio metadata (insert or update), handling concurrent uploads."""
    try:
        await audio_metadata.insert()
        return audio_metadata, None
    except DuplicateKeyError:
        # Concurrent upload detected; fetch and update instead
        existing = await TextAudio.find_one(TextAudio.text_id == text_id)
        if existing:
            old_audio_key = existing.audio_key
            existing.audio_key = audio_metadata.audio_key
            existing.text_title = audio_metadata.text_title
            existing.file_name = audio_metadata.file_name
            existing.mime_type = audio_metadata.mime_type
            existing.file_size_bytes = audio_metadata.file_size_bytes
            existing.duration_ms = audio_metadata.duration_ms
            existing.created_by = audio_metadata.created_by
            existing.updated_at = audio_metadata.updated_at
            await existing.save()
            return existing, old_audio_key
        raise


async def _cleanup_audio_files(loop, audio: TextAudio, new_audio_key: str, old_audio_key: Optional[str]) -> None:
    """Best-effort cleanup of S3 objects displaced by a replacement.

    A key that fails to delete (the one just displaced, or one left over from
    a previous failed cleanup) is persisted on the document instead of only
    being logged, so it is retried on the next upload rather than lost.
    """
    candidates = list(audio.pending_cleanup_keys)
    if old_audio_key and old_audio_key != new_audio_key:
        candidates.append(old_audio_key)
    candidates = list(dict.fromkeys(key for key in candidates if key and key != new_audio_key))
    if not candidates:
        return

    still_pending = []
    for key in candidates:
        try:
            await loop.run_in_executor(None, lambda k=key: delete_file(k))
        except HTTPException:
            logging.exception("Failed to remove replaced text audio: %s", key)
            still_pending.append(key)

    if still_pending != audio.pending_cleanup_keys:
        audio.pending_cleanup_keys = still_pending
        await audio.save()


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

    # Upload to S3
    file.file.seek(0)
    await loop.run_in_executor(
        None,
        lambda: upload_file(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=new_audio_key,
            file=file,
        ),
    )

    # Handle metadata persistence
    try:
        existing = await TextAudio.find_one(TextAudio.text_id == text_id)
        if existing:
            old_audio_key = existing.audio_key
            _update_audio_metadata(existing, text.title, new_audio_key, file, content_type, duration_ms, current_author.email, now)
            await existing.save()
            audio = existing
        else:
            audio_metadata = _build_audio_metadata(text_id, text.title, new_audio_key, file, content_type, duration_ms, current_author.email, now)
            audio, old_audio_key = await _persist_audio_metadata(text_id, new_audio_key, audio_metadata, loop)
    except DuplicateKeyError:
        await loop.run_in_executor(None, lambda: delete_file(new_audio_key))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Audio for this text is being uploaded concurrently"
        )
    except Exception:
        await loop.run_in_executor(None, lambda: delete_file(new_audio_key))
        raise

    # Cleanup old audio if applicable
    await _cleanup_audio_files(loop, audio, new_audio_key, old_audio_key)
    return to_text_audio_response(audio)


async def delete_text_audio(token: str, text_id: str) -> None:
    validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)
    audio = await TextAudio.find_one(TextAudio.text_id == text_id)
    if not audio:
        return
    keys_to_delete = list(dict.fromkeys(
        key for key in [audio.audio_key, *audio.pending_cleanup_keys] if key
    ))
    loop = asyncio.get_event_loop()

    # Delete metadata first (source of truth). Once this succeeds, the audio
    # no longer exists from the application's perspective, so a subsequent
    # S3 failure below only orphans storage instead of leaving a record that
    # still points at a file which no longer exists.
    await audio.delete()

    for key in keys_to_delete:
        try:
            await loop.run_in_executor(None, lambda k=key: delete_file(k))
        except HTTPException as e:
            logging.exception("Failed to remove text audio from S3 %s: %s. Object orphaned.", key, e)
