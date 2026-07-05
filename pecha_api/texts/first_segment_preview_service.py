from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from uuid import UUID

from pecha_api.texts.segments.segments_models import Segment
from pecha_api.texts.texts_repository import get_contents_by_id, get_contents_by_text_ids
from pecha_api.texts.texts_toc_utils import (
    FIRST_SEGMENT_PREVIEW_COUNT,
    combine_segment_preview_contents,
    get_first_n_segment_refs_from_table_of_contents,
)

FirstSegmentPreview = Tuple[str, str]


async def resolve_segment_by_ref(segment_ref: str) -> Optional[Segment]:
    try:
        UUID(segment_ref)
        segment = await Segment.get_segment_by_id(segment_id=segment_ref)
        if segment is not None:
            return segment
    except ValueError:
        pass
    return await Segment.get_segment_by_pecha_segment_id(pecha_segment_id=segment_ref)


async def _resolve_preview_segments_for_refs(refs: List[str]) -> List[Segment]:
    resolved_segments: List[Segment] = []
    for ref in refs:
        segment = await resolve_segment_by_ref(ref)
        if segment is not None:
            resolved_segments.append(segment)
    return resolved_segments


async def _preview_from_text_segments(
    text_id: str,
    preview_count: int,
) -> Optional[FirstSegmentPreview]:
    segments = await Segment.get_segments_by_text_id(text_id=text_id)
    if not segments:
        return None

    preview_segments = segments[:preview_count]
    return (
        str(preview_segments[0].id),
        combine_segment_preview_contents([segment.content for segment in preview_segments]),
    )


async def build_first_segment_preview_for_text(
    text_id: str,
    *,
    preview_count: int = FIRST_SEGMENT_PREVIEW_COUNT,
) -> Optional[FirstSegmentPreview]:
    table_of_contents = await get_contents_by_id(text_id=text_id)
    refs = get_first_n_segment_refs_from_table_of_contents(
        table_of_contents,
        preview_count,
    )

    if not refs:
        return await _preview_from_text_segments(text_id, preview_count)

    preview_segments = await _resolve_preview_segments_for_refs(refs)
    if not preview_segments:
        return await _preview_from_text_segments(text_id, preview_count)

    return (
        str(preview_segments[0].id),
        combine_segment_preview_contents([segment.content for segment in preview_segments]),
    )


async def build_first_segment_previews_for_texts(
    text_ids: List[str],
    *,
    preview_count: int = FIRST_SEGMENT_PREVIEW_COUNT,
) -> Dict[str, FirstSegmentPreview]:
    if not text_ids:
        return {}

    normalized_ids = list(dict.fromkeys(text_ids))
    table_of_contents_by_text_id = await get_contents_by_text_ids(text_ids=normalized_ids)
    previews: Dict[str, FirstSegmentPreview] = {}

    for text_id in normalized_ids:
        refs = get_first_n_segment_refs_from_table_of_contents(
            table_of_contents_by_text_id.get(text_id, []),
            preview_count,
        )
        if not refs:
            preview = await _preview_from_text_segments(text_id, preview_count)
            if preview is not None:
                previews[text_id] = preview
            continue

        preview_segments = await _resolve_preview_segments_for_refs(refs)
        if not preview_segments:
            preview = await _preview_from_text_segments(text_id, preview_count)
            if preview is not None:
                previews[text_id] = preview
            continue

        previews[text_id] = (
            str(preview_segments[0].id),
            combine_segment_preview_contents(
                [segment.content for segment in preview_segments]
            ),
        )

    return previews
