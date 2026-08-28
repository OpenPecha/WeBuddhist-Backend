import asyncio
import logging
from typing import List, Optional

from openpecha_api.segments.openpecha_segment_service import fetch_segment_content

from ..plans_enums import ContentType

logger = logging.getLogger(__name__)


async def _fetch_segment_content_safe(segment_id: str) -> Optional[str]:
    try:
        return await fetch_segment_content(segment_id)
    except Exception:
        logger.exception("Failed to fetch segment content '%s' from openpecha", segment_id)
        return None


async def resolve_subtask_content(
    content_type,
    content: Optional[str],
    segment_ids: Optional[List[str]],
) -> Optional[str]:
    """Live-resolve SOURCE_REFERENCE subtask content from openpecha segments.

    Falls back to the stored `content` value when segment_ids are absent, the
    content type isn't SOURCE_REFERENCE, or the upstream fetch fails/returns
    a missing segment - so stale or malformed pasted-in content never blocks
    a response, it's just superseded by live data when available.
    """
    if content_type != ContentType.SOURCE_REFERENCE or not segment_ids:
        return content

    segment_contents = await asyncio.gather(
        *[_fetch_segment_content_safe(segment_id) for segment_id in segment_ids]
    )

    if any(segment_content is None for segment_content in segment_contents):
        return content

    return "\n".join(segment_contents)


async def resolve_subtasks_content(subtasks) -> List[Optional[str]]:
    """Resolve content for a list of subtask-like objects, preserving order."""
    return await asyncio.gather(
        *[
            resolve_subtask_content(sub_task.content_type, sub_task.content, sub_task.segment_ids)
            for sub_task in subtasks
        ]
    )
