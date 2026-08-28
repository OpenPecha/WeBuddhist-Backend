import logging
from typing import Any, Dict, List, Optional

from openpecha_api.text.openpecha_text_service import search_by_content

from .search_response_models import (
    MultilingualSearchResponse,
    MultilingualSegmentMatch,
    MultilingualSourceResult,
)
from .search_service import (
    MAX_EXTERNAL_SEARCH_LIMIT,
    apply_pagination_to_sources,
    build_placeholder_text_index,
    create_empty_search_response,
    fetch_text_info,
    flatten_content_search_matches,
)

logger = logging.getLogger(__name__)


async def _build_sources_from_content_search_matches(
    matches: List[Dict[str, Any]],
) -> List[MultilingualSourceResult]:
    text_to_matches: Dict[str, List[MultilingualSegmentMatch]] = {}
    text_ids: List[str] = []

    for match in matches:
        text_id = match["text_id"]
        if not text_id:
            continue

        if text_id not in text_to_matches:
            text_to_matches[text_id] = []
            text_ids.append(text_id)

        text_to_matches[text_id].append(
            MultilingualSegmentMatch(
                segment_id=match["pecha_segment_id"],
                content=match["content"],
                relevance_score=match["relevance_score"],
                pecha_segment_id=match["pecha_segment_id"],
            )
        )

    if not text_ids:
        return []

    text_info_map = await fetch_text_info(text_ids)
    sources: List[MultilingualSourceResult] = []

    for text_id in text_ids:
        segment_matches = text_to_matches[text_id]
        segment_matches.sort(key=lambda item: item.relevance_score)
        sources.append(
            MultilingualSourceResult(
                text=text_info_map.get(text_id) or build_placeholder_text_index(text_id),
                segment_matches=segment_matches,
            )
        )

    return sources


async def get_multilingual_search_results(
    query: str,
    search_type: str = "similar",
    text_id: Optional[str] = None,
    edition_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> MultilingualSearchResponse:
    try:
        external_limit = min(limit * 5, MAX_EXTERNAL_SEARCH_LIMIT)

        external_data = await search_by_content(
            query=query,
            search_type=search_type,
            limit=external_limit,
            text_id=text_id,
            edition_id=edition_id,
        )

        if not isinstance(external_data, list):
            logger.warning(
                "Unexpected OpenPecha content search response type: %s",
                type(external_data).__name__,
            )
            return create_empty_search_response(query, search_type, skip, limit)

        matches = flatten_content_search_matches(external_data)
        if not matches:
            logger.info("No matches returned from OpenPecha content search")
            return create_empty_search_response(query, search_type, skip, limit)

        sources = await _build_sources_from_content_search_matches(matches)

        if not sources:
            return create_empty_search_response(query, search_type, skip, limit)

        paginated_sources = apply_pagination_to_sources(sources, skip, limit)

        return MultilingualSearchResponse(
            query=query,
            search_type=search_type,
            sources=paginated_sources,
            skip=skip,
            limit=limit,
            total=len(matches),
        )

    except Exception:
        logger.exception("Error in multilingual search")
        raise
