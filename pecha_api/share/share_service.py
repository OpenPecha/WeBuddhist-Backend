from fastapi import HTTPException
import io
import logging
import re
from pathlib import Path
from uuid import UUID
from PIL import Image
from pecha_api.error_contants import ErrorConstants
from starlette.responses import StreamingResponse
from .pecha_text_image_generator import generate_segment_image
from pecha_api.texts.segments.segments_openpecha_service import get_openpecha_segment_details_by_id
from pecha_api.texts.texts_openpecha_service import get_text_by_id_from_openpecha
from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.poems.repository import get_poem_by_id
from pecha_api.poems.enums import PoemStatus
from pecha_api.uploads.S3_utils import download_bytes
import anyio
import anyio.to_thread

from pecha_api.share.share_response_models import (
    ShareRequest,
    ShortUrlResponse
)

from pecha_api.short_url.short_url_service import get_short_url

from pecha_api.error_contants import ErrorConstants

LOGO_PATH = "pecha_api/share/static/img/pecha-logo.png"
IMAGE_PATH = "pecha_api/share/static/img/output.png"
MEDIA_TYPE = "image/png"
WEBP_MEDIA_TYPE = "image/webp"
JPEG_MEDIA_TYPE = "image/jpeg"
IMAGE_MEDIA_TYPES = {
    ".webp": WEBP_MEDIA_TYPE,
    ".png": MEDIA_TYPE,
    ".jpg": JPEG_MEDIA_TYPE,
    ".jpeg": JPEG_MEDIA_TYPE,
}
DEFAULT_OG_TITLE = get("SITE_NAME")
DEFAULT_OG_DESCRIPTION = get("SITE_NAME")
PECHA_FRONTEND_ENDPOINT = "https://webuddhist.com/chapter"
POEM_URL_PATTERN = re.compile(r"/poem/([0-9a-fA-F-]{36})")
# The shortener stores og_title in a varchar(200); a longer title errors the share.
OG_TITLE_MAX_LENGTH = 200


def _extract_poem_id_from_url_(url: str | None) -> str | None:
    """The app embeds the poem id in the share url (…/open/poem/{uuid})."""
    if not url:
        return None
    match = POEM_URL_PATTERN.search(url)
    return match.group(1) if match else None


def _get_poem_image_bytes_(poem_id: str) -> tuple[bytes, str] | None:
    try:
        poem_uuid = UUID(poem_id)
    except (ValueError, AttributeError):
        return None

    with SessionLocal() as db:
        poem = get_poem_by_id(db=db, poem_id=poem_uuid, status=PoemStatus.PUBLISHED)
        if poem is None or not poem.image_key:
            return None
        image_key = poem.image_key

    try:
        image_bytes = download_bytes(bucket_name=get("AWS_BUCKET_NAME"), s3_key=image_key)
    except Exception as error:
        # download_bytes only converts ClientError; transport, timeout and
        # credential failures surface raw, and all must fall back to an image.
        logging.warning(f"Could not download poem image {image_key}: {error}")
        return None

    media_type = IMAGE_MEDIA_TYPES.get(Path(image_key).suffix.lower(), WEBP_MEDIA_TYPE)

    # Uploads are stored as webp, which social crawlers unfurl unreliably, so
    # serve a jpeg instead. A failed conversion falls back to the stored bytes.
    if media_type == WEBP_MEDIA_TYPE:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            converted = io.BytesIO()
            image.convert("RGB").save(converted, format="JPEG", quality=85)
            return converted.getvalue(), JPEG_MEDIA_TYPE
        except (OSError, ValueError) as error:
            logging.warning(f"Could not convert poem image {image_key} to jpeg: {error}")

    return image_bytes, media_type


async def get_generated_image(poem_id: str | None = None):
    try:
        if poem_id is not None:
            try:
                poem_image = await anyio.to_thread.run_sync(_get_poem_image_bytes_, poem_id)
            except Exception as error:
                # A database failure here must still yield an image to the crawler.
                logging.warning(f"Could not resolve poem image for {poem_id}: {error}")
                poem_image = None
            if poem_image is not None:
                image_bytes, media_type = poem_image
                return StreamingResponse(io.BytesIO(image_bytes), media_type=media_type)

        image_path = IMAGE_PATH
        async with await anyio.open_file(image_path, "rb") as file:
            image_bytes = await file.read()

        return StreamingResponse(io.BytesIO(image_bytes), media_type=MEDIA_TYPE)

    except HTTPException as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=ErrorConstants.IMAGE_NOT_FOUND_MESSAGE
        )

async def _has_retrievable_image_(poem_id: str) -> bool:
    # Resolves the image the way /share/image will, so the two cannot disagree.
    try:
        poem_image = await anyio.to_thread.run_sync(_get_poem_image_bytes_, poem_id)
        return poem_image is not None
    except Exception as error:
        logging.warning(f"Could not verify poem image for {poem_id}: {error}")
        return False


async def generate_short_url(share_request: ShareRequest) -> ShortUrlResponse:
    og_description = DEFAULT_OG_DESCRIPTION
    if share_request.poem_id is None:
        share_request.poem_id = _extract_poem_id_from_url_(share_request.url)

    # Clearing poem_id when the image is unavailable matters: the poem path skips
    # generation below, and output.png still holds the previous share's image.
    poem_title = None
    if share_request.poem_id is not None:
        poem_title = await anyio.to_thread.run_sync(_get_poem_title_, share_request.poem_id)
        if poem_title is None or not await _has_retrievable_image_(share_request.poem_id):
            share_request.poem_id = None

    if share_request.logo:
        _generate_logo_image_(share_request=share_request)

    if share_request.poem_id is None:
        await _generate_segment_content_image_(share_request=share_request)

    payload = _generate_short_url_payload_(
        share_request=share_request,
        og_description=og_description,
        poem_title=poem_title,
    )
    short_url: ShortUrlResponse = await get_short_url(payload=payload)

    return short_url



def _generate_logo_image_(share_request: ShareRequest):
    generate_segment_image(
        text_color=share_request.text_color,
        bg_color=share_request.bg_color,
        logo_path=LOGO_PATH
    )

async def _generate_segment_content_image_(share_request: ShareRequest):
    main_content_text = get("SITE_NAME")
    reference_text = get("SITE_NAME")
    language = share_request.language
    if share_request.segment_id is not None:
        segment_details = await get_openpecha_segment_details_by_id(
            segment_id=share_request.segment_id,
        )
        main_content_text = segment_details.content
        reference_text = segment_details.text.title
        language = segment_details.text.language
    elif share_request.text_id is not None:
        text_detail = await get_text_by_id_from_openpecha(text_id=share_request.text_id)
        main_content_text = text_detail.title
        language = text_detail.language

    generate_segment_image(
        text=main_content_text,
        ref_str=reference_text,
        lang=language,
        text_color=share_request.text_color,
        bg_color=share_request.bg_color,
        logo_path=LOGO_PATH
    )



def _generate_short_url_payload_(share_request: ShareRequest, og_description: str, poem_title: str | None = None) -> dict:

    if share_request.url is None:
        share_request.url = _generate_url_(
            segment_id=share_request.segment_id,
            content_id=share_request.content_id,
            text_id=share_request.text_id,
            content_index=share_request.content_index,
        )

    pecha_backend_endpoint = get("PECHA_BACKEND_ENDPOINT")
    og_title = DEFAULT_OG_TITLE
    if share_request.poem_id is not None:
        # Resolved per request, so unlike a presigned s3 url it never expires.
        image_url = f"{pecha_backend_endpoint}/share/image?poem_id={share_request.poem_id}"
        if poem_title:
            og_title = poem_title[:OG_TITLE_MAX_LENGTH]
    elif share_request.segment_id is not None:
        image_url = f"{pecha_backend_endpoint}/share/image?segment_id={share_request.segment_id}&language={share_request.language}&logo={share_request.logo}"
    else:
        image_url = f"{pecha_backend_endpoint}/share/image?text_id={share_request.text_id}&language={share_request.language}&logo={share_request.logo}"
    payload = {
        "url": share_request.url,
        "og_title": og_title,
        "og_description": og_description,
        "og_image": image_url,
        "tags": share_request.tags
    }
    return payload


def _get_poem_title_(poem_id: str) -> str | None:
    try:
        poem_uuid = UUID(poem_id)
    except (ValueError, AttributeError):
        return None

    with SessionLocal() as db:
        poem = get_poem_by_id(db=db, poem_id=poem_uuid, status=PoemStatus.PUBLISHED)
        return poem.title if poem is not None else None

def _generate_url_(
        content_id: str,
        content_index: int,
        text_id: str,
        segment_id: str | None = None,
) -> str:
    if segment_id is None:
        return f"{PECHA_FRONTEND_ENDPOINT}?contentId={content_id}&text_id={text_id}&contentIndex={content_index}"
    return f"{PECHA_FRONTEND_ENDPOINT}?segment_id={segment_id}&contentId={content_id}&text_id={text_id}&contentIndex={content_index}"
