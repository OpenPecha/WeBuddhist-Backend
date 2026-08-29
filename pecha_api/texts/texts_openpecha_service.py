import asyncio
import logging
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
from pecha_api.texts.texts_enums import PaginationDirection
from pecha_api.texts.texts_openpecha_api import (
    fetch_critical_editions,
    fetch_edition_text_id,
    fetch_editions_segmentation,
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
    SegmentSpans,
    SegmentDTO,
    TextDetailDTO,
    TextDetailResponse,
    TextDetailsRequest,
    TextDetailWithContentResponse,
)

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


async def get_titles_and_ids_by_query(
    title: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[TitleSearchResult]:
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="title is required",
        )

    texts, _ = await _get_texts_by_collection_id(
        collection_id=None,
        title=title,
        skip=offset,
        limit=limit,
    )
    if not texts:
        return []

    edition_ids = await asyncio.gather(*[_fetch_first_critical_edition_id(text.id) for text in texts])

    return [
        TitleSearchResult(id=edition_id, title=text.title)
        for text, edition_id in zip(texts, edition_ids)
        if edition_id
    ]


async def _fetch_first_critical_edition_id(text_id: str) -> Optional[str]:
    try:
        editions = await fetch_critical_editions(text_id=text_id)
    except Exception:
        logger.warning("Failed to fetch critical edition for text %s", text_id)
        return None
    return editions[0].id if editions else None


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


_ALL_SEGMENTS_PAGE_SIZE = 500


async def _fetch_all_segments(edition_id: str) -> List[SegmentSpans]:
    all_segments: List[SegmentSpans] = []
    offset = 0
    while True:
        page = await fetch_segmentation_segments(
            edition_id=edition_id, limit=_ALL_SEGMENTS_PAGE_SIZE, offset=offset
        )
        all_segments.extend(page.items)
        if not page.has_more:
            break
        offset += len(page.items)
    return all_segments


def _map_text_detail_dto(text_detail: TextDetailResponse) -> TextDetailDTO:
    title = _extract_title(text_detail.title, text_detail.language)
    date_value = text_detail.date or ""

    return TextDetailDTO(
        id=text_detail.id,
        pecha_text_id=text_detail.bdrc or text_detail.id,
        title=title,
        language=text_detail.language or "",
        group_id=text_detail.category_id or "",
        type="root_text",
        summary="",
        is_published=True,
        created_date=date_value,
        updated_date=date_value,
        published_date=date_value,
        published_by="",
        categories=[text_detail.category_id] if text_detail.category_id else [],
        views=0,
        likes=[],
        source_link=None,
        ranking=None,
        license=text_detail.license,
    )


def _trim_windowed_segments(
    edition_content: str,
    segments: List[SegmentSpans],
    start_position: int,
) -> List[SegmentDTO]:
    return [
        SegmentDTO(
            segment_id=segment.id,
            segment_number=start_position + i,
            content="".join(edition_content[line.start:line.end] for line in segment.lines),
        )
        for i, segment in enumerate(segments)
    ]


def _build_content_dto(
    edition_id: str,
    text_id: str,
    segmentation_id: str,
    segments: List[SegmentDTO],
) -> ContentDTO:
    return ContentDTO(
        id=edition_id,
        text_id=text_id,
        sections=[
            SectionDTO(
                id=segmentation_id,
                title="1",
                section_number=1,
                segments=segments,
            )
        ],
    )


async def get_text_detail_by_id(
    edition_id: str,
    text_details_request: TextDetailsRequest,
) -> TextDetailWithContentResponse:
    text_id = await fetch_edition_text_id(edition_id=edition_id)
    text_detail = await fetch_text_detail(text_id=text_id)

    segmentations = await fetch_editions_segmentation(edition_id=edition_id)
    if not segmentations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No segmentation found for edition '{edition_id}'",
        )

    edition_content = await fetch_edition_content(edition_id=edition_id)
    all_segments = await _fetch_all_segments(edition_id=edition_id)

    text_detail_dto = _map_text_detail_dto(text_detail)
    total_segments = len(all_segments)
    size = text_details_request.size

    if total_segments == 0:
        return TextDetailWithContentResponse(
            text_detail=text_detail_dto,
            content=_build_content_dto(edition_id=edition_id, text_id=text_id, segmentation_id=segmentations[0].id, segments=[]),
            size=size,
            pagination_direction=text_details_request.direction.value,
            current_segment_position=0,
            total_segments=0,
        )

    if text_details_request.start is not None and text_details_request.end is not None:
        window_start = max(0, text_details_request.start - 1)
        window_end = max(window_start, min(text_details_request.end, total_segments))
        current_position = window_start + 1
    else:
        if text_details_request.segment_id:
            anchor_index = next(
                (i for i, segment in enumerate(all_segments) if segment.id == text_details_request.segment_id),
                None,
            )
            if anchor_index is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Segment with id '{text_details_request.segment_id}' not found",
                )
        else:
            anchor_index = 0

        if text_details_request.direction == PaginationDirection.NEXT:
            window_start = anchor_index
            window_end = min(anchor_index + size, total_segments)
        else:
            window_start = max(0, anchor_index - size + 1)
            window_end = anchor_index + 1
        current_position = anchor_index + 1

    windowed_segments = _trim_windowed_segments(
        edition_content=edition_content.content,
        segments=all_segments[window_start:window_end],
        start_position=window_start + 1,
    )

    return TextDetailWithContentResponse(
        text_detail=text_detail_dto,
        content=_build_content_dto(edition_id=edition_id, text_id=text_id, segmentation_id=segmentations[0].id, segments=windowed_segments),
        size=size,
        pagination_direction=text_details_request.direction.value,
        current_segment_position=current_position,
        total_segments=total_segments,
        has_more_up=window_start > 0,
        has_more_down=window_end < total_segments,
    )


def trim_segment_content(edition_content: str, segments: SegmentationSegmentResponseModel) -> SegmentContentResponse:
    result = []
    for i, segment in enumerate(segments.items):
        content = "".join(edition_content[line.start:line.end] for line in segment.lines)
        result.append(SegmentContentModel(id=segment.id, content=content, segment_number=i+1))
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


def filter_versions_by_language(
    versions: List[TextVersion],
    language: Optional[str]
) -> List[TextVersion]:
    if not language:
        return versions
    return [v for v in versions if v.language == language]


def paginate_versions(
    versions: List[TextVersion],
    skip: int,
    limit: int
) -> List[TextVersion]:
    return versions[skip:skip + limit]


async def get_text_versions_from_openpecha(
    text_id: str,
    language: Optional[str] = None,
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
        return await _fetch_versions_from_parent(translation_of, root_text, language, skip, limit)

    # If both commentary_of and translation_of are null, check translations and commentaries lists
    if not commentary_of and not translation_of:
        translation_ids = text_data.get("translations", [])
        commentary_ids = text_data.get("commentaries", [])

        # If there are translations or commentaries, fetch versions from the first available ID
        related_ids = translation_ids + commentary_ids
        if related_ids:
            # Fetch versions from the first related text
            return await _fetch_versions_from_related(related_ids[0], root_text, language, skip, limit)

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

    filtered_versions = filter_versions_by_language(versions, language)

    paginated_versions = paginate_versions(filtered_versions, skip, limit)

    return TextVersionResponse(
        text=root_text,
        versions=paginated_versions
    )


async def _fetch_versions_from_parent(
    parent_id: str,
    original_text: TextDTO,
    language: Optional[str],
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

    filtered_versions = filter_versions_by_language(versions, language)

    paginated_versions = paginate_versions(filtered_versions, skip, limit)

    return TextVersionResponse(
        text=original_text,
        versions=paginated_versions
    )


async def _fetch_versions_from_related(
    related_id: str,
    original_text: TextDTO,
    language: Optional[str],
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
        return await _fetch_versions_from_parent(translation_of, original_text, language, skip, limit)

    # Otherwise, get translations from the related text itself
    translation_ids = related_data.get("translations", [])

    if not translation_ids:
        return TextVersionResponse(text=original_text, versions=[])

    translation_details = await fetch_translation_details(translation_ids)

    versions = [
        map_external_text_to_text_version(item, item.get("language"))
        for item in translation_details
    ]

    filtered_versions = filter_versions_by_language(versions, language)

    paginated_versions = paginate_versions(filtered_versions, skip, limit)

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






async def search_text_content(
    query: str,
    search_type: Optional[str] = None,
    limit: Optional[int] = 10,
    text_id: Optional[str] = None,
    edition_id: Optional[str] = None,
) -> Dict[str, Any]:
    
 return await search_by_content(query, search_type, limit, text_id, edition_id)