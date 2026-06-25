from typing import Optional
from uuid import UUID

from pecha_api.bookmarks.bookmark_enums import BookmarkType
from pecha_api.bookmarks.bookmark_models import Bookmark
from pecha_api.texts.segments.segments_models import Segment
from pecha_api.texts.segments.segments_repository import get_segment_by_id
from pecha_api.texts.texts_repository import (
    get_first_segment_table_of_content,
    get_texts_by_id,
)


async def _resolve_segment_by_ref(segment_ref: str) -> Optional[Segment]:
    try:
        UUID(segment_ref)
        segment = await get_segment_by_id(segment_id=segment_ref)
        if segment:
            return segment
    except ValueError:
        pass
    return await Segment.get_segment_by_pecha_segment_id(pecha_segment_id=segment_ref)


async def _resolve_text_segment(
    text_id: str,
    verse_id: Optional[str],
) -> tuple[Optional[str], Optional[Segment]]:
    if verse_id:
        segment = await _resolve_segment_by_ref(verse_id)
        if segment and segment.text_id == text_id:
            return str(segment.id), segment

    segment_id, _ = await get_first_segment_table_of_content(text_id=text_id)
    if segment_id:
        segment = await get_segment_by_id(segment_id=segment_id)
        return segment_id, segment

    segment = await Segment.get_first_segment_by_text_id(text_id=text_id)
    if segment:
        return str(segment.id), segment

    return None, None


async def enrich_text_bookmark(bookmark: Bookmark) -> dict:
    verse_id: Optional[str] = None
    text_id: Optional[str] = None

    if bookmark.type == BookmarkType.VERSE:
        verse_id = bookmark.source_id
        segment = await _resolve_segment_by_ref(verse_id)
        if not segment:
            return {}
        text_id = segment.text_id
        segment_id = str(segment.id)
    elif bookmark.type == BookmarkType.TEXT:
        text_id = bookmark.source_id
        if bookmark.name:
            candidate = await _resolve_segment_by_ref(bookmark.name)
            if candidate and candidate.text_id == text_id:
                verse_id = bookmark.name
        segment_id, segment = await _resolve_text_segment(text_id=text_id, verse_id=verse_id)
        if not segment_id:
            return {}
    else:
        return {}

    text = await get_texts_by_id(text_id=text_id)

    result = {
        "text_id": text_id,
        "text_title": text.title if text else None,
        "segment_id": segment_id,
        "segment_content": segment.content if segment else None,
    }

    if verse_id:
        result["verse_id"] = verse_id

    return result
