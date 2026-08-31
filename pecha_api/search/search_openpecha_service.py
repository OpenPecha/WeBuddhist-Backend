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
    # The response's `text.text_id` reports the edition_id, not the text_id, so
    # results are grouped by edition even though metadata is fetched by text_id.
    edition_to_matches: Dict[str, List[MultilingualSegmentMatch]] = {}
    edition_to_text_id: Dict[str, str] = {}
    edition_ids: List[str] = []

    for match in matches:
        edition_id = match.get("edition_id") or match["text_id"]
        text_id = match["text_id"]
        if not edition_id or not text_id:
            continue

        if edition_id not in edition_to_matches:
            edition_to_matches[edition_id] = []
            edition_to_text_id[edition_id] = text_id
            edition_ids.append(edition_id)

        edition_to_matches[edition_id].append(
            MultilingualSegmentMatch(
                segment_id=match["pecha_segment_id"],
                content=match["content"],
                relevance_score=match["relevance_score"],
                pecha_segment_id=match["pecha_segment_id"],
            )
        )

    if not edition_ids:
        return []

    unique_text_ids = list(dict.fromkeys(edition_to_text_id.values()))
    text_info_map = await fetch_text_info(unique_text_ids)
    sources: List[MultilingualSourceResult] = []

    for edition_id in edition_ids:
        segment_matches = edition_to_matches[edition_id]
        segment_matches.sort(key=lambda item: item.relevance_score)

        text_info = text_info_map.get(edition_to_text_id[edition_id])
        text = (
            text_info.model_copy(update={"text_id": edition_id})
            if text_info
            else build_placeholder_text_index(edition_id)
        )

        sources.append(
            MultilingualSourceResult(
                text=text,
                segment_matches=segment_matches,
            )
        )

    return sources


async def get_multilingual_search_results(
    query: str,
    search_type: str = "similar",
    text_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> MultilingualSearchResponse:
    try:
        external_limit = min(limit * 5, MAX_EXTERNAL_SEARCH_LIMIT)

        # OpenPecha's content search scopes by edition, so the incoming text_id
        # is sent as edition_id.
        external_data = await search_by_content(
            query=query,
            search_type=search_type,
            limit=external_limit,
            edition_id=text_id,
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
