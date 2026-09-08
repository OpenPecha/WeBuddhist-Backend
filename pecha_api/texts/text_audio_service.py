import asyncio
import json
import logging
import os
import uuid
from io import BytesIO
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
    upload_bytes,
)

from .audio_transcoder import MP3_EXTENSION, MP3_MIME_TYPE, transcode_to_mp3
from .otr_transcript_parser import parse_otr_transcript
from .segments.segments_models import Segment
from .text_audio_models import (
    TextAudio,
    TextAudioOtr,
    TextAudioOtrContentResponse,
    TextAudioOtrResponse,
    TextAudioResponse,
    TextAudioSegmentsResponse,
    TextSegmentContent,
    UpdateTextAudioNameRequest,
    utc_now,
)
from .texts_models import TableOfContent
from .texts_openpecha_service import get_text_by_id_from_openpecha
from .texts_response_models import Section, TableOfContentType, V2TextDTO
from .texts_toc_utils import iter_segment_refs_in_sections

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
        name=audio.name or audio.file_name,
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


async def get_required_text(text_id: str) -> V2TextDTO:
    return await get_text_by_id_from_openpecha(text_id=text_id)


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


def _sorted_sections(sections: List[Section]) -> List[Section]:
    ordered = sorted(sections, key=lambda section: section.section_number)
    for section in ordered:
        section.segments = sorted(
            section.segments, key=lambda segment: segment.segment_number
        )
        if section.sections:
            section.sections = _sorted_sections(section.sections)
    return ordered


async def get_text_segments_in_order(
    token: str, text_id: str
) -> TextAudioSegmentsResponse:
    validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)

    tables_of_content = await TableOfContent.get_table_of_contents_by_text_id(
        text_id=text_id
    )
    # A text can have more than one table of contents (e.g. sheets); the
    # sync feature reads the text itself, so sheets are excluded and only
    # the first remaining table of contents is used as the reading order.
    table_of_content = next(
        (toc for toc in tables_of_content if toc.type != TableOfContentType.SHEET),
        None,
    )
    if table_of_content is None:
        return TextAudioSegmentsResponse(text_id=text_id, segments=[])

    ordered_refs = list(
        iter_segment_refs_in_sections(_sorted_sections(table_of_content.sections))
    )
    if not ordered_refs:
        return TextAudioSegmentsResponse(text_id=text_id, segments=[])

    contents_by_ref = await Segment.get_segment_contents_by_ids(
        segment_ids=ordered_refs
    )
    segments = [
        TextSegmentContent(segment_id=ref, content=contents_by_ref[ref][1])
        for ref in ordered_refs
        if ref in contents_by_ref
    ]
    return TextAudioSegmentsResponse(text_id=text_id, segments=segments)


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
    now = utc_now()
    loop = asyncio.get_event_loop()

    # Everything is stored as MP3 - see audio_transcoder for why.
    converted = await loop.run_in_executor(
        None,
        lambda: transcode_to_mp3(file.file, suffix=extension),
    )
    new_audio_key = f"audio/texts/{uuid.uuid4()}{MP3_EXTENSION}"
    await loop.run_in_executor(
        None,
        lambda: upload_bytes(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=new_audio_key,
            file=BytesIO(converted.content),
            content_type=MP3_MIME_TYPE,
        ),
    )

    source_name = os.path.splitext(file.filename or "audio")[0] or "audio"
    default_file_name = f"{source_name}{MP3_EXTENSION}"
    audio = TextAudio(
        text_id=text_id,
        text_title=text.title,
        audio_key=new_audio_key,
        file_name=default_file_name,
        name=default_file_name,
        mime_type=MP3_MIME_TYPE,
        file_size_bytes=len(converted.content),
        duration_ms=converted.duration_ms or duration_ms,
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


async def update_text_audio_name(
    token: str,
    text_id: str,
    audio_id: str,
    request: UpdateTextAudioNameRequest,
) -> TextAudioResponse:
    validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)
    audio = await get_required_audio(text_id=text_id, audio_id=audio_id)
    audio.name = request.name
    audio.updated_at = utc_now()
    await audio.save()
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

    # Delete the OTR transcripts before the audio itself, and let a failure
    # here propagate instead of swallowing it. That keeps the operation
    # retry-safe rather than truly atomic (which would need a replica-set
    # transaction this deployment doesn't have): if this fails, the audio
    # document is untouched - nothing is lost - the caller gets an honest
    # error instead of a false success, and retrying is a clean no-op delete.
    await TextAudioOtr.find(TextAudioOtr.audio_id == audio_pk).delete()

    # Only now delete the audio metadata. If this fails after the transcripts
    # are already gone, the caller still gets an honest error (never a false
    # success); the audio temporarily exists with zero transcripts, which is
    # a truthful, discoverable state (its OTR list correctly reads empty),
    # and retrying converges cleanly since the step above is now a no-op.
    await audio.delete()

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
    parsed_text, spans = parse_otr_transcript(content.get("text"))
    now = utc_now()
    otr = TextAudioOtr(
        audio_id=str(audio.id),
        text_id=text_id,
        name=otr_name,
        file_name=file.filename or f"{otr_name}.json",
        content=content,
        parsed_text=parsed_text,
        spans=spans,
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
) -> TextAudioOtrContentResponse:
    validate_cms_author_details(token=token)
    await get_required_text(text_id=text_id)
    audio = await get_required_audio(text_id=text_id, audio_id=audio_id)
    otr = await get_required_otr(audio_id=str(audio.id), otr_id=otr_id)
    return TextAudioOtrContentResponse(text=otr.parsed_text, spans=otr.spans)


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
