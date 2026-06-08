import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from starlette import status

from openpecha_api.segments.openpecha_segment_service import (
    fetch_related_segments,
    fetch_segment_content,
)
from openpecha_api.text.openpecha_text_service import fetch_text_by_id

from .segments_response_models import (
    ParentSegment,
    V2RelatedSegmentItem,
    V2SegmentCommentariesResponse,
    V2SegmentTextGroup,
    V2SegmentTranslationsResponse,
)
from ..texts_openpecha_api import fetch_text_source_link
from ..texts_openpecha_service import _extract_title

logger = logging.getLogger(__name__)

TRANSLATION = "translation"
COMMENTARY = "commentary"


def _classify_text(text_payload: Dict[str, Any]) -> Optional[str]:
    if not text_payload:
        return None
    if text_payload.get("translation_of"):
        return TRANSLATION
    if text_payload.get("commentary_of"):
        return COMMENTARY
    return None


async def _fetch_text_safe(text_id: str) -> Optional[Dict[str, Any]]:
    try:
        return await fetch_text_by_id(text_id)
    except Exception:
        logger.exception("Failed to fetch text %s from upstream", text_id)
        return None


async def _fetch_segment_content_safe(segment_id: str) -> Optional[str]:
    try:
        return await fetch_segment_content(segment_id)
    except Exception:
        logger.exception("Failed to fetch segment content %s from upstream", segment_id)
        return None


async def _fetch_parent_segment(segment_id: str) -> ParentSegment:
    content = await _fetch_segment_content_safe(segment_id)
    if content is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Segment with id '{segment_id}' not found",
        )
    return ParentSegment(segment_id=segment_id, content=content)


async def _get_related_segments_grouped_by_type(
    segment_id: str,
    related_type: str,
    skip: int,
    limit: int,
) -> Tuple[ParentSegment, List[V2SegmentTextGroup], bool]:

    try:
        parent_segment, related_page = await asyncio.gather(
            _fetch_parent_segment(segment_id),
            fetch_related_segments(segment_id=segment_id, limit=limit, offset=skip),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch related segments from upstream service",
        )

    items: List[Dict[str, Any]] = related_page.get("items", []) or []
    has_more = bool(related_page.get("has_more", False))

    if not items:
        return parent_segment, [], has_more

    unique_text_ids: List[str] = []
    seen_text_ids = set()
    for item in items:
        text_id = item.get("text_id")
        if text_id and text_id not in seen_text_ids:
            seen_text_ids.add(text_id)
            unique_text_ids.append(text_id)

    text_payloads, source_links = await asyncio.gather(
        asyncio.gather(*[_fetch_text_safe(text_id) for text_id in unique_text_ids]),
        asyncio.gather(*[fetch_text_source_link(text_id) for text_id in unique_text_ids]),
    )
    text_by_id: Dict[str, Dict[str, Any]] = {
        text_id: payload
        for text_id, payload in zip(unique_text_ids, text_payloads)
        if payload is not None
    }
    source_by_id: Dict[str, Optional[str]] = dict(zip(unique_text_ids, source_links))

    filtered_items = [
        item
        for item in items
        if _classify_text(text_by_id.get(item.get("text_id", ""))) == related_type
    ]

    if not filtered_items:
        return parent_segment, [], has_more

    segment_contents = await asyncio.gather(
        *[_fetch_segment_content_safe(item["id"]) for item in filtered_items]
    )

    grouped: Dict[str, V2SegmentTextGroup] = {}
    group_order: List[str] = []
    for item, content in zip(filtered_items, segment_contents):
        text_id = item.get("text_id", "")
        if not text_id:
            continue
        if text_id not in grouped:
            text_payload = text_by_id.get(text_id, {})
            grouped[text_id] = V2SegmentTextGroup(
                text_id=text_id,
                title=_extract_title(text_payload.get("title", {})),
                language=text_payload.get("language"),
                source_link=source_by_id.get(text_id),
                license=text_payload.get("license"),
                segments=[],
            )
            group_order.append(text_id)
        grouped[text_id].segments.append(
            V2RelatedSegmentItem(id=item["id"], content=content)
        )

    return parent_segment, [grouped[text_id] for text_id in group_order], has_more


async def get_translations_by_segment_id_from_openpecha(
    segment_id: str,
    skip: int = 0,
    limit: int = 10,
) -> V2SegmentTranslationsResponse:
    parent_segment, translations, has_more = await _get_related_segments_grouped_by_type(
        segment_id=segment_id,
        related_type=TRANSLATION,
        skip=skip,
        limit=limit,
    )
    return V2SegmentTranslationsResponse(
        parent_segment=parent_segment,
        translations=translations,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )


async def get_commentaries_by_segment_id_from_openpecha(
    segment_id: str,
    skip: int = 0,
    limit: int = 10,
) -> V2SegmentCommentariesResponse:
    parent_segment, commentaries, has_more = await _get_related_segments_grouped_by_type(
        segment_id=segment_id,
        related_type=COMMENTARY,
        skip=skip,
        limit=limit,
    )
    return V2SegmentCommentariesResponse(
        parent_segment=parent_segment,
        commentaries=commentaries,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )
