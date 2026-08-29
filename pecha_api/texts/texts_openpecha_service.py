import asyncio
import logging

import httpx
from typing import Optional, Dict, Any, List, Tuple

from fastapi import HTTPException
from starlette import status

from pecha_api.texts.texts_response_models import (
    TextDTO,
    TextVersion,
    TextVersionResponse,
    TitleSearchResult,
    V2TextDTO,
    V2TextsCategoryResponse,
)
from pecha_api.collections.collections_response_models import V2CollectionModel
from openpecha_api.text.openpecha_text_service import fetch_texts_by_category, fetch_text_by_id, search_by_content
from openpecha_api.collection.openpecha_collection_service import fetch_category_by_id
from openpecha_api.segments.openpecha_segment_service import fetch_segment_details
from pecha_api.texts.texts_openpecha_api import (
    fetch_critical_editions,
    fetch_edition_content,
    fetch_segmentation_segments,
    fetch_text_detail,
    fetch_text_source_link,
)
from pecha_api.texts.text_openpecha_response_models import (
    ContentDTO,
    SectionDTO,
    SegmentationSegmentResponseModel,
    SegmentContentModel,
    SegmentContentResponse,
    SegmentDTO,
    TextDetailDTO,
    TextDetailResponse,
    TextDetailsRequest,
    TextDetailWithContentResponse,
)
from pecha_api.texts.texts_enums import PaginationDirection
from pecha_api.cache.cache_enums import CacheType
from pecha_api.cache.cache_repository import get_cache_data, set_cache
from pecha_api.utils import Utils
from pecha_api import config

logger = logging.getLogger(__name__)


def _extract_title(title_payload: Any, language: Optional[str] = None) -> str:
    if isinstance(title_payload, dict):
        if language and language in title_payload:
            return title_payload[language]
        for val in title_payload.values():
            if isinstance(val, str) and val.strip():
                return val
        return ""
    if isinstance(title_payload, str):
        return title_payload.strip()
    return ""


def _map_external_text_to_dto(item: Dict[str, Any], language: Optional[str] = None) -> V2TextDTO:
    title = _extract_title(item.get("title", {}), language)

    return V2TextDTO(
        id=item.get("id", ""),
        title=title,
        language=item.get("language") or "",
        license=item.get("license"),
    )


def map_external_text_to_dto(item: Dict[str, Any], language: Optional[str] = None) -> TextDTO:
    title = _extract_title(item.get("title", {}), language)
    date_value = item.get("date") or ""

    return TextDTO(
        id=item.get("id", ""),
        pecha_text_id=item.get("bdrc") or item.get("id", ""),
        title=title,
        language=item.get("language") or "",
        group_id=item.get("category_id") or "",
        type="root_text",
        summary="",
        is_published=True,
        created_date=date_value,
        updated_date=date_value,
        published_date=date_value,
        published_by="",
        categories=[item.get("category_id")] if item.get("category_id") else [],
        views=0,
        likes=[],
        source_link=item.get("source_link"),
        ranking=None,
        license=item.get("license"),
    )


async def _fetch_text_detail_with_source(text_id: str) -> Optional[Dict[str, Any]]:
    try:
        data = await fetch_text_by_id(text_id)
        if not data:
            return None
        source_link = await fetch_text_source_link(text_id)
        if source_link:
            data["source_link"] = source_link
        return data
    except Exception as e:
        logger.warning("Failed to fetch text %s: %s", text_id, e)
        return None


async def _get_texts_by_collection_id(
    collection_id: Optional[str],
    skip: int,
    limit: int,
    title: Optional[str] = None,
) -> Tuple[List[V2TextDTO], bool]:
    try:
        page = await fetch_texts_by_category(
            category_id=collection_id,
            title=title,
            offset=skip,
            limit=limit,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch texts from upstream service",
        )

    items = page.get("items", [])
    has_more = bool(page.get("has_more", False))
    texts = [_map_external_text_to_dto(item) for item in items]

    return texts, has_more


async def get_texts_by_collection_from_openpecha(
    collection_id: Optional[str] = None,
    language: Optional[str] = None,
    title: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> V2TextsCategoryResponse:
    texts, has_more = await _get_texts_by_collection_id(
        collection_id=collection_id,
        title=title,
        skip=skip,
        limit=limit,
    )

    collection: Optional[V2CollectionModel] = None
    if collection_id:
        category_title = ""
        try:
            category_data = await fetch_category_by_id(collection_id, language=language)
            if category_data:
                category_title = _extract_title(category_data.get("title", {}), language)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to fetch category title from upstream service",
            )

        collection = V2CollectionModel(
            id=collection_id,
            title=category_title,
        )

    return V2TextsCategoryResponse(
        collection=collection,
        texts=texts,
        skip=skip,
        limit=limit,
        has_more=has_more,
    )


async def get_text_by_id_from_openpecha(text_id: str) -> V2TextDTO:
    try:
        data = await fetch_text_by_id(text_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch text from upstream service",
        )

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found",
        )

    return _map_external_text_to_dto(data, data.get("language"))


async def get_text_detail_by_id(text_id: str, offset: int, limit: int) -> TextDetailResponse:
    text_detail = await fetch_text_detail(text_id=text_id)
    edition_details = await fetch_critical_editions(text_id=text_id)
    if not edition_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No critical editions found for text with id '{text_id}'",
        )
    text_detail.edition_details = edition_details
    edition_id = edition_details[0].id
    # Segments hang off the edition's segmentation, so the edition id addresses them directly.
    edition_content = await fetch_edition_content(edition_id=edition_id)
    segments = await fetch_segmentation_segments(edition_id=edition_id, limit=limit, offset=offset)
    segment_contents = trim_segment_content(edition_content=edition_content.content, segments=segments)
    text_detail.segments = segment_contents
    return text_detail


def trim_segment_content(edition_content: str, segments: SegmentationSegmentResponseModel) -> SegmentContentResponse:
    result = []
    for i, segment in enumerate(segments.items):
        content = "".join(edition_content[line.start:line.end] for line in segment.lines)
        # Numbered by position in the whole text, so paging does not restart at 1.
        result.append(SegmentContentModel(id=segment.id, content=content, segment_number=segments.offset + i + 1))
    return SegmentContentResponse(contents=result, has_more=segments.has_more, offset=segments.offset, limit=segments.limit)
async def fetch_translation_details(translation_ids: List[str]) -> List[Dict[str, Any]]:
    results = await asyncio.gather(
        *[_fetch_text_detail_with_source(translation_id) for translation_id in translation_ids]
    )
    return [item for item in results if item is not None]


def map_external_text_to_text_version(item: Dict[str, Any], language: Optional[str] = None) -> TextVersion:
    title = _extract_title(item.get("title", {}), language)
    date_value = item.get("date") or ""

    return TextVersion(
        id=item.get("id", ""),
        title=title,
        parent_id=item.get("translation_of") or item.get("commentary_of"),
        priority=None,
        language=item.get("language") or "",
        type="translation",
        group_id=item.get("category_id") or "",
        table_of_contents=[],
        is_published=True,
        created_date=date_value,
        updated_date=date_value,
        published_date=date_value,
        published_by="",
        source_link=item.get("source_link"),
        ranking=None,
        license=item.get("license"),
    )


def paginate_versions(
    versions: List[TextVersion],
    skip: int,
    limit: int
) -> List[TextVersion]:
    return versions[skip:skip + limit]


async def get_text_versions_from_openpecha(
    text_id: str,
    skip: int = 0,
    limit: int = 10
) -> TextVersionResponse:

    try:
        text_data = await fetch_text_by_id(text_id)
    except Exception:
        logger.exception("Failed to fetch text from upstream service")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch text from upstream service",
        )

    if not text_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found",
        )

    root_text = map_external_text_to_dto(text_data, text_data.get("language"))

    commentary_of = text_data.get("commentary_of")
    translation_of = text_data.get("translation_of")

    # If translation_of is not null, fetch versions from the parent text
    if translation_of:
        return await _fetch_versions_from_parent(translation_of, root_text, skip, limit)

    # If both commentary_of and translation_of are null, check translations and commentaries lists
    if not commentary_of and not translation_of:
        translation_ids = text_data.get("translations", [])
        commentary_ids = text_data.get("commentaries", [])

        # If there are translations or commentaries, fetch versions from the first available ID
        related_ids = translation_ids + commentary_ids
        if related_ids:
            # Fetch versions from the first related text
            return await _fetch_versions_from_related(related_ids[0], root_text, skip, limit)

    # Default: fetch translations directly from this text
    translation_ids = text_data.get("translations", [])

    if not translation_ids:
        return TextVersionResponse(
            text=root_text,
            versions=[]
        )

    translation_details = await fetch_translation_details(translation_ids)

    versions = [
        map_external_text_to_text_version(item, item.get("language"))
        for item in translation_details
    ]

    paginated_versions = paginate_versions(versions, skip, limit)

    return TextVersionResponse(
        text=root_text,
        versions=paginated_versions
    )


async def _fetch_versions_from_parent(
    parent_id: str,
    original_text: TextDTO,
    skip: int,
    limit: int
) -> TextVersionResponse:
    """Fetch versions from a parent text (translation_of)."""
    try:
        parent_data = await fetch_text_by_id(parent_id)
    except Exception:
        logger.warning(f"Failed to fetch parent text {parent_id}, returning empty versions")
        return TextVersionResponse(text=original_text, versions=[])

    if not parent_data:
        return TextVersionResponse(text=original_text, versions=[])

    translation_ids = parent_data.get("translations", [])

    if not translation_ids:
        return TextVersionResponse(text=original_text, versions=[])

    translation_details = await fetch_translation_details(translation_ids)

    versions = [
        map_external_text_to_text_version(item, item.get("language"))
        for item in translation_details
    ]

    paginated_versions = paginate_versions(versions, skip, limit)

    return TextVersionResponse(
        text=original_text,
        versions=paginated_versions
    )


async def _fetch_versions_from_related(
    related_id: str,
    original_text: TextDTO,
    skip: int,
    limit: int
) -> TextVersionResponse:
    """Fetch versions from a related text (from translations or commentaries list)."""
    try:
        related_data = await fetch_text_by_id(related_id)
    except Exception:
        logger.warning(f"Failed to fetch related text {related_id}, returning empty versions")
        return TextVersionResponse(text=original_text, versions=[])

    if not related_data:
        return TextVersionResponse(text=original_text, versions=[])

    # Check if the related text has a translation_of pointing to a parent
    translation_of = related_data.get("translation_of")
    if translation_of:
        return await _fetch_versions_from_parent(translation_of, original_text, skip, limit)

    # Otherwise, get translations from the related text itself
    translation_ids = related_data.get("translations", [])

    if not translation_ids:
        return TextVersionResponse(text=original_text, versions=[])

    translation_details = await fetch_translation_details(translation_ids)

    versions = [
        map_external_text_to_text_version(item, item.get("language"))
        for item in translation_details
    ]

    paginated_versions = paginate_versions(versions, skip, limit)

    return TextVersionResponse(
        text=original_text,
        versions=paginated_versions
    )


async def fetch_commentary_details(commentary_ids: List[str]) -> List[Dict[str, Any]]:
    results = await asyncio.gather(
        *[_fetch_text_detail_with_source(commentary_id) for commentary_id in commentary_ids]
    )
    return [item for item in results if item is not None]


async def get_text_commentaries_from_openpecha(
    text_id: str,
    skip: int = 0,
    limit: int = 10
) -> List[TextDTO]:

    try:
        text_data = await fetch_text_by_id(text_id)
    except Exception:
        logger.exception("Failed to fetch text from upstream service")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch text from upstream service",
        )

    if not text_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found",
        )

    commentary_of = text_data.get("commentary_of")
    translation_of = text_data.get("translation_of")

    # If commentary_of is not null, fetch commentaries from the parent text
    if commentary_of:
        return await _fetch_commentaries_from_parent(commentary_of, skip, limit)

    # If both commentary_of and translation_of are null, check translations and commentaries lists
    if not commentary_of and not translation_of:
        translation_ids = text_data.get("translations", [])
        commentary_ids = text_data.get("commentaries", [])

        # If there are translations or commentaries, fetch commentaries from the first available ID
        related_ids = translation_ids + commentary_ids
        if related_ids:
            return await _fetch_commentaries_from_related(related_ids[0], skip, limit)

    # Default: fetch commentaries directly from this text
    commentary_ids = text_data.get("commentaries", [])

    if not commentary_ids:
        return []

    commentary_details = await fetch_commentary_details(commentary_ids)

    commentaries = [
        map_external_text_to_dto(item, item.get("language"))
        for item in commentary_details
    ]

    paginated_commentaries = commentaries[skip:skip + limit]

    return paginated_commentaries


async def _fetch_commentaries_from_parent(
    parent_id: str,
    skip: int,
    limit: int
) -> List[TextDTO]:
    """Fetch commentaries from a parent text (commentary_of)."""
    try:
        parent_data = await fetch_text_by_id(parent_id)
    except Exception:
        logger.warning(f"Failed to fetch parent text {parent_id}, returning empty commentaries")
        return []

    if not parent_data:
        return []

    commentary_ids = parent_data.get("commentaries", [])

    if not commentary_ids:
        return []

    commentary_details = await fetch_commentary_details(commentary_ids)

    commentaries = [
        map_external_text_to_dto(item, item.get("language"))
        for item in commentary_details
    ]

    return commentaries[skip:skip + limit]


async def _fetch_commentaries_from_related(
    related_id: str,
    skip: int,
    limit: int
) -> List[TextDTO]:
    """Fetch commentaries from a related text (from translations or commentaries list)."""
    try:
        related_data = await fetch_text_by_id(related_id)
    except Exception:
        logger.warning(f"Failed to fetch related text {related_id}, returning empty commentaries")
        return []

    if not related_data:
        return []

    # Check if the related text has a commentary_of pointing to a parent
    commentary_of = related_data.get("commentary_of")
    if commentary_of:
        return await _fetch_commentaries_from_parent(commentary_of, skip, limit)

    # Otherwise, get commentaries from the related text itself
    commentary_ids = related_data.get("commentaries", [])

    if not commentary_ids:
        return []

    commentary_details = await fetch_commentary_details(commentary_ids)

    commentaries = [
        map_external_text_to_dto(item, item.get("language"))
        for item in commentary_details
    ]

    return commentaries[skip:skip + limit]




CONTENT_SEARCH_URL = "http://13.250.189.160/v2/content-search"


async def search_text_content(
    query: str,
    search_type: Optional[str] = None,
    limit: Optional[int] = 10,
    text_id: Optional[str] = None,
    edition_id: Optional[str] = None,
) -> Dict[str, Any]:
    
 return await search_by_content(query, search_type, limit, text_id, edition_id)

async def get_titles_by_query_from_openpecha(
    title: str,
    limit: int = 20,
    offset: int = 0,
) -> List[TitleSearchResult]:
    """Title lookup backed entirely by OpenPecha.

    Replaces the legacy title-search, which fetched titles from OpenPecha and
    then re-resolved them to ids through Mongo by exact title-string match.
    """
    try:
        data = await fetch_texts_by_category(
            title=title,
            limit=limit,
            offset=offset,
        )
    except Exception:
        logger.exception("Failed to search texts by title from upstream")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to search texts by title from upstream service",
        )

    results: List[TitleSearchResult] = []
    for item in data.get("items", []) or []:
        if not isinstance(item, dict):
            continue
        text_id = item.get("id")
        if not text_id:
            continue
        title_value = _extract_title(item.get("title", {}), item.get("language"))
        if not title_value:
            continue
        results.append(TitleSearchResult(id=text_id, title=title_value))

    return results


# ============================================================================
# POST /{text_id}/details - production-shaped response, sourced from OpenPecha
# ============================================================================

SEGMENT_PAGE_FETCH_LIMIT = 100  # upstream caps limit at 100


async def _count_edition_segments(edition_id: str) -> int:
    """Total segments in an edition's segmentation.

    Upstream exposes no count, so this pages through at the maximum limit and
    caches the result per edition to keep it off the per-request path.
    """
    cache_key = Utils.generate_hash_key(payload=[edition_id, CacheType.SEGMENTS_DETAILS])
    cached_total = await get_cache_data(hash_key=cache_key)
    if isinstance(cached_total, int):
        return cached_total

    total = 0
    offset = 0
    while True:
        page = await fetch_segmentation_segments(
            edition_id=edition_id,
            limit=SEGMENT_PAGE_FETCH_LIMIT,
            offset=offset,
        )
        total += len(page.items)
        if not page.has_more or not page.items:
            break
        offset += SEGMENT_PAGE_FETCH_LIMIT

    await set_cache(
        hash_key=cache_key,
        value=total,
        cache_time_out=config.get_int("CACHE_TEXT_TIMEOUT"),
    )
    return total


async def _resolve_anchor_position(segment_id: Optional[str]) -> int:
    """1-based position of the cursor segment; 1 when absent or unresolvable.

    A segment's `reference` is its 0-based index within the segmentation, so a
    single lookup replaces walking the whole table of contents.
    """
    if not segment_id:
        return 1
    try:
        segment = await fetch_segment_details(segment_id)
    except (httpx.HTTPStatusError, httpx.RequestError):
        logger.warning("Could not resolve position for segment %s", segment_id)
        return 1

    reference = (segment or {}).get("reference")
    try:
        return int(reference) + 1
    except (TypeError, ValueError):
        logger.warning("Segment %s has a non-numeric reference %r", segment_id, reference)
        return 1


def _resolve_range_bounds(
    start: Optional[int],
    end: Optional[int],
    size: int,
    total_segments: int,
) -> Tuple[int, int, int]:
    """Inclusive 1-based page bounds from explicit start/end positions."""
    if start is not None and end is not None:
        page_start_pos = max(1, min(start, total_segments))
        page_end_pos = max(page_start_pos, min(end, total_segments))
        return page_start_pos, page_end_pos, page_end_pos

    if start is not None:
        page_start_pos = max(1, min(start, total_segments))
        page_end_pos = min(page_start_pos + size - 1, total_segments)
        return page_start_pos, page_end_pos, page_end_pos

    page_end_pos = max(1, min(end, total_segments))
    page_start_pos = max(1, page_end_pos - size + 1)
    return page_start_pos, page_end_pos, page_end_pos


def _resolve_page_bounds(
    anchor_position: int,
    direction: PaginationDirection,
    size: int,
    total_segments: int,
    start: Optional[int] = None,
    end: Optional[int] = None,
) -> Tuple[int, int, int]:
    """Inclusive 1-based page bounds, matching the cursor semantics clients rely on.

    NEXT pages forward from the anchor (which stays in the page); PREVIOUS pages
    backward and ends on it.
    """
    if start is not None or end is not None:
        return _resolve_range_bounds(
            start=start,
            end=end,
            size=size,
            total_segments=total_segments,
        )

    anchor_index = anchor_position - 1
    if direction == PaginationDirection.PREVIOUS:
        page_start_pos = max(0, anchor_index - size + 1) + 1
        page_end_pos = anchor_index + 1
    else:
        page_start_pos = anchor_index + 1
        page_end_pos = min(anchor_index + size, total_segments)

    return page_start_pos, page_end_pos, anchor_position


def _build_text_detail_dto(text_id: str, text_payload: TextDetailResponse, source_link: Optional[str]) -> TextDetailDTO:
    """Map an OpenPecha text onto the client-facing DTO.

    OpenPecha has no equivalent of the publishing/engagement fields, so those are
    filled with neutral defaults rather than read from a second store.
    """
    return TextDetailDTO(
        id=text_id,
        pecha_text_id=text_payload.bdrc or text_id,
        title=_extract_title(text_payload.title, text_payload.language),
        language=text_payload.language or "",
        group_id="",
        type="root_text",
        summary="",
        is_published=True,
        created_date="",
        updated_date="",
        published_date=str(text_payload.date or ""),
        published_by="",
        categories=[text_payload.category_id] if text_payload.category_id else [],
        views=0,
        likes=[],
        source_link=source_link,
        ranking=None,
        license=text_payload.license,
    )


async def get_text_details_by_text_id_from_openpecha(
    text_id: str,
    text_details_request: TextDetailsRequest,
) -> TextDetailWithContentResponse:
    text_payload = await fetch_text_detail(text_id=text_id)
    edition_details = await fetch_critical_editions(text_id=text_id)
    if not edition_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No critical editions found for text with id '{text_id}'",
        )
    text_payload.edition_details = edition_details
    edition_id = edition_details[0].id

    total_segments, anchor_position = await asyncio.gather(
        _count_edition_segments(edition_id=edition_id),
        _resolve_anchor_position(text_details_request.segment_id),
    )

    if total_segments == 0:
        return _build_empty_details_response(
            text_id=text_id,
            text_payload=text_payload,
            text_details_request=text_details_request,
        )

    page_start_pos, page_end_pos, current_segment_position = _resolve_page_bounds(
        anchor_position=anchor_position,
        direction=text_details_request.direction,
        size=text_details_request.size,
        total_segments=total_segments,
        start=text_details_request.start,
        end=text_details_request.end,
    )
    page_length = max(0, page_end_pos - page_start_pos + 1)

    edition_content, segments = await asyncio.gather(
        fetch_edition_content(edition_id=edition_id),
        fetch_segmentation_segments(
            edition_id=edition_id,
            limit=min(page_length, SEGMENT_PAGE_FETCH_LIMIT),
            offset=page_start_pos - 1,
        ),
    )
    segment_contents = trim_segment_content(
        edition_content=edition_content.content,
        segments=segments,
    )

    source_link = await fetch_text_source_link(text_id)

    return TextDetailWithContentResponse(
        text_detail=_build_text_detail_dto(text_id, text_payload, source_link),
        content=ContentDTO(
            id=edition_id,
            text_id=text_id,
            # Upstream exposes no table-of-contents structure yet, so the page is
            # returned as one section rather than an invented hierarchy.
            sections=[
                SectionDTO(
                    id=edition_id,
                    title=_extract_title(text_payload.title, text_payload.language),
                    section_number=1,
                    segments=[
                        SegmentDTO(
                            segment_id=segment.id,
                            segment_number=segment.segment_number,
                            content=segment.content,
                        )
                        for segment in segment_contents.contents
                    ],
                )
            ],
        ),
        size=text_details_request.size,
        pagination_direction=text_details_request.direction.value,
        current_segment_position=current_segment_position,
        total_segments=total_segments,
        has_more_up=page_start_pos > 1,
        has_more_down=page_end_pos < total_segments,
    )


def _build_empty_details_response(
    text_id: str,
    text_payload: TextDetailResponse,
    text_details_request: TextDetailsRequest,
) -> TextDetailWithContentResponse:
    return TextDetailWithContentResponse(
        text_detail=_build_text_detail_dto(text_id, text_payload, None),
        content=ContentDTO(id="", text_id=text_id, sections=[]),
        size=text_details_request.size,
        pagination_direction=text_details_request.direction.value,
        current_segment_position=0,
        total_segments=0,
    )
