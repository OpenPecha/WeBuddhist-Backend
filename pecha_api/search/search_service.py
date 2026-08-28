import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from starlette import status

from .search_enums import SearchType
from .search_response_models import (
    Search,
    SearchResponse,
    SegmentLinkResponse,
    SegmentMatch,
    SourceResultItem,
    TextIndex,
    MultilingualSearchResponse,
    MultilingualSourceResult,
)
from openpecha_api.text.openpecha_text_service import fetch_text_by_id, search_by_content
from openpecha_api.segments.openpecha_segment_service import fetch_segment_details
from pecha_api.texts.texts_openpecha_service import _extract_title

logger = logging.getLogger(__name__)

MAX_SEARCH_LIMIT = 30
MAX_EXTERNAL_SEARCH_LIMIT = 100


async def get_search_results(query: str, search_type: SearchType, text_id: str = None, skip: int = 0, limit: int = 10) -> SearchResponse:

    if SearchType.SOURCE == search_type:
        return await _source_search(
            query=query,
            text_id=text_id,
            skip=skip,
            limit=limit
        )

    if SearchType.SHEET == search_type:
        return _sheet_search(
            query=query,
            skip=skip,
            limit=limit
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="search_type is required and must be one of: SOURCE, SHEET"
    )


async def _source_search(
        query: str,
        text_id: str,
        skip: int,
        limit: int
) -> SearchResponse:
    """Search source content through the OpenPecha content-search API."""
    try:
        # Fetch beyond the requested page so pagination has something to slice.
        external_limit = min((skip + limit) * 2, MAX_EXTERNAL_SEARCH_LIMIT)

        search_results = await search_by_content(
            query=query,
            text_id=text_id,
            limit=external_limit,
        )

        if not isinstance(search_results, list):
            logger.warning("Unexpected OpenPecha content search response type: %s", type(search_results).__name__)
            return _empty_source_response(query=query, skip=skip, limit=limit)

        matches = flatten_content_search_matches(search_results)
        sources = await _build_source_result_items(matches=matches, skip=skip, limit=limit)

        return SearchResponse(
            search=Search(text=query, type=SearchType.SOURCE),
            sources=sources,
            skip=skip,
            limit=limit,
            total=min(MAX_SEARCH_LIMIT, len(matches))
        )

    except Exception:
        logger.exception("Error in source search")
        return _empty_source_response(query=query, skip=skip, limit=limit)


def _empty_source_response(query: str, skip: int, limit: int) -> SearchResponse:
    return SearchResponse(
        search=Search(text=query, type=SearchType.SOURCE),
        sources=[],
        skip=skip,
        limit=limit,
        total=0
    )


def flatten_content_search_matches(
    content_search_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Flatten OpenPecha content-search hits into one entry per segment.

    A hit covers a matched span and can span several segments, so the same
    segment can appear under more than one hit; only its best hit is kept.
    Scores are negated so ascending order puts the most relevant match first.
    """
    matches: List[Dict[str, Any]] = []
    match_index_by_segment: Dict[str, int] = {}

    for result in content_search_results:
        relevance_score = -result.get("score", 0.0)
        context = result.get("context", "")
        text_id = result.get("text_id", "")

        for pecha_segment_id in result.get("segment_ids", []) or []:
            if not pecha_segment_id:
                continue

            match = {
                "text_id": text_id,
                "pecha_segment_id": pecha_segment_id,
                "content": context,
                "relevance_score": relevance_score,
            }

            existing_index = match_index_by_segment.get(pecha_segment_id)
            if existing_index is None:
                match_index_by_segment[pecha_segment_id] = len(matches)
                matches.append(match)
            elif relevance_score < matches[existing_index]["relevance_score"]:
                matches[existing_index] = match

    matches.sort(key=lambda match: match["relevance_score"])
    return matches


async def _build_source_result_items(
    matches: List[Dict[str, Any]],
    skip: int,
    limit: int
) -> List[SourceResultItem]:
    page = matches[skip:skip + limit]
    if not page:
        return []

    text_info_map = await fetch_text_info([match["text_id"] for match in page])

    grouped: Dict[str, List[SegmentMatch]] = {}
    group_order: List[str] = []
    for match in page:
        text_id = match["text_id"]
        if not text_id:
            continue
        if text_id not in grouped:
            grouped[text_id] = []
            group_order.append(text_id)
        grouped[text_id].append(
            SegmentMatch(
                segment_id=match["pecha_segment_id"],
                content=match["content"]
            )
        )

    return [
        SourceResultItem(
            text=text_info_map.get(text_id) or build_placeholder_text_index(text_id),
            segment_match=grouped[text_id]
        )
        for text_id in group_order
    ]


def _sheet_search(query: str, skip: int, limit: int) -> SearchResponse:
    return SearchResponse(
        search=Search(
            text=query,
            type=SearchType.SHEET
        ),
        sheets=[],
        skip=skip,
        limit=limit,
        total=0
    )


def build_placeholder_text_index(text_id: str) -> TextIndex:
    """Stand-in metadata so a match is still returned when its text cannot be fetched."""
    return TextIndex(text_id=text_id, language="", title="", published_date="")


async def _fetch_text_safe(text_id: str) -> Optional[Dict[str, Any]]:
    try:
        return await fetch_text_by_id(text_id)
    except Exception:
        # Upstream 404s are routine when the search index is ahead of the graph.
        logger.warning("Failed to fetch text %s from OpenPecha", text_id)
        return None


async def fetch_text_info(text_ids: List[str]) -> Dict[str, TextIndex]:
    unique_text_ids = list(dict.fromkeys(text_id for text_id in text_ids if text_id))
    if not unique_text_ids:
        return {}

    payloads = await asyncio.gather(*[_fetch_text_safe(text_id) for text_id in unique_text_ids])

    text_info_map: Dict[str, TextIndex] = {}
    for text_id, payload in zip(unique_text_ids, payloads):
        if not payload:
            continue
        language = payload.get("language") or ""
        text_info_map[text_id] = TextIndex(
            text_id=text_id,
            language=language,
            title=_extract_title(payload.get("title", {}), language),
            published_date=str(payload.get("date") or "")
        )
    return text_info_map


def create_empty_search_response(
    query: str,
    search_type: str,
    skip: int,
    limit: int
) -> MultilingualSearchResponse:
    return MultilingualSearchResponse(
        query=query,
        search_type=search_type,
        sources=[],
        skip=skip,
        limit=limit,
        total=0
    )


def apply_pagination_to_sources(
    sources: List[MultilingualSourceResult],
    skip: int,
    limit: int
) -> List[MultilingualSourceResult]:

    all_matches = []
    for source in sources:
        for match in source.segment_matches:
            all_matches.append((source.text, match))

    all_matches.sort(key=lambda x: x[1].relevance_score)

    paginated_matches = all_matches[skip:skip + limit]

    text_to_matches: Dict[str, tuple] = {}
    for text_info, match in paginated_matches:
        text_key = text_info.text_id
        if text_key not in text_to_matches:
            text_to_matches[text_key] = (text_info, [])
        text_to_matches[text_key][1].append(match)

    paginated_sources = [
        MultilingualSourceResult(text=text_info, segment_matches=matches)
        for text_info, matches in text_to_matches.values()
    ]

    return paginated_sources


async def get_url_link(pecha_segment_id: str) -> SegmentLinkResponse:
    try:
        segment_details = await fetch_segment_details(pecha_segment_id)
    except Exception:
        logger.warning("Failed to fetch segment %s from OpenPecha", pecha_segment_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pecha segment not found")

    text_id = segment_details.get("text_id") if isinstance(segment_details, dict) else None
    if not text_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pecha segment not found")

    return SegmentLinkResponse(
        text_id=text_id,
        segment_id=pecha_segment_id,
    )
