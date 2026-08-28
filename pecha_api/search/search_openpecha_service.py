import logging
from typing import Any, Dict, List, Optional

from openpecha_api.text.openpecha_text_service import fetch_text_by_id, search_by_content

from pecha_api.texts.segments.segments_models import Segment
from .search_response_models import (
    MultilingualSearchResponse,
    MultilingualSegmentMatch,
    MultilingualSourceResult,
    TextIndex,
)
from .search_service import (
    apply_pagination_to_sources,
    create_empty_search_response,
    fetch_segments_by_ids,
    fetch_text_info,
)

logger = logging.getLogger(__name__)


def _extract_title(title_payload: Any, language: Optional[str] = None) -> str:
    if isinstance(title_payload, dict):
        if language and language in title_payload:
            return title_payload[language]
        for value in title_payload.values():
            if isinstance(value, str) and value.strip():
                return value
        return ""
    if isinstance(title_payload, str):
        return title_payload.strip()
    return ""


def _flatten_content_search_matches(
    content_search_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []
    best_scores: Dict[str, float] = {}

    for result in content_search_results:
        relevance_score = -result.get("score", 0.0)
        context = result.get("context", "")
        text_id = result.get("text_id", "")

        for pecha_segment_id in result.get("segment_ids", []):
            if not pecha_segment_id:
                continue

            existing_score = best_scores.get(pecha_segment_id)
            if existing_score is not None and relevance_score >= existing_score:
                continue

            best_scores[pecha_segment_id] = relevance_score
            matches.append(
                {
                    "text_id": text_id,
                    "pecha_segment_id": pecha_segment_id,
                    "content": context,
                    "relevance_score": relevance_score,
                }
            )

    matches.sort(key=lambda match: match["relevance_score"])
    return matches


async def _fetch_text_info_map(text_ids: List[str]) -> Dict[str, TextIndex]:
    text_info_map = await fetch_text_info(text_ids)

    for text_id in text_ids:
        if text_id in text_info_map:
            continue

        try:
            data = await fetch_text_by_id(text_id)
        except Exception:
            logger.warning("Failed to fetch text %s from OpenPecha", text_id, exc_info=True)
            continue

        if not data:
            continue

        language = data.get("language") or ""
        text_info_map[text_id] = TextIndex(
            text_id=text_id,
            language=language,
            title=_extract_title(data.get("title", {}), language),
            published_date=str(data.get("date") or ""),
        )

    return text_info_map


async def _build_sources_from_content_search_matches(
    matches: List[Dict[str, Any]],
    local_segments_by_pecha: Dict[str, Segment],
) -> List[MultilingualSourceResult]:
    text_to_matches: Dict[str, List[MultilingualSegmentMatch]] = {}
    text_ids: set[str] = set()

    for match in matches:
        pecha_segment_id = match["pecha_segment_id"]
        local_segment = local_segments_by_pecha.get(pecha_segment_id)
        text_id = local_segment.text_id if local_segment else match["text_id"]

        if not text_id:
            continue

        text_ids.add(text_id)
        text_to_matches.setdefault(text_id, []).append(
            MultilingualSegmentMatch(
                segment_id=str(local_segment.id) if local_segment else pecha_segment_id,
                content=local_segment.content if local_segment else match["content"],
                relevance_score=match["relevance_score"],
                pecha_segment_id=pecha_segment_id,
            )
        )

    if not text_ids:
        return []

    text_info_map = await _fetch_text_info_map(list(text_ids))
    sources: List[MultilingualSourceResult] = []

    for text_id, segment_matches in text_to_matches.items():
        if text_id not in text_info_map:
            continue

        segment_matches.sort(key=lambda item: item.relevance_score)
        sources.append(
            MultilingualSourceResult(
                text=text_info_map[text_id],
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
        external_limit = min(limit * 5, 100)

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

        matches = _flatten_content_search_matches(external_data)
        if not matches:
            logger.info("No matches returned from OpenPecha content search")
            return create_empty_search_response(query, search_type, skip, limit)

        pecha_segment_ids = [match["pecha_segment_id"] for match in matches]
        local_segments = await fetch_segments_by_ids(pecha_segment_ids, text_id)
        local_segments_by_pecha = {
            segment.pecha_segment_id: segment
            for segment in local_segments
            if segment.pecha_segment_id
        }

        sources = await _build_sources_from_content_search_matches(
            matches,
            local_segments_by_pecha,
        )

        if not sources:
            return create_empty_search_response(query, search_type, skip, limit)

        paginated_sources = apply_pagination_to_sources(sources, skip, limit)

        return MultilingualSearchResponse(
            query=query,
            search_type=search_type,
            sources=paginated_sources,
            skip=skip,
            limit=limit,
            total=limit,
        )

    except Exception:
        logger.exception("Error in multilingual search")
        raise
