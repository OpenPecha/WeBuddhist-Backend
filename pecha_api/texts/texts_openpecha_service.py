import logging
from typing import Optional, Dict, Any, List, Tuple

from fastapi import HTTPException
from starlette import status

from pecha_api.texts.texts_response_models import (
    TextDTO,
    TextVersion,
    TextVersionResponse,
    V2TextDTO,
    V2TextsCategoryResponse,
)
from pecha_api.collections.collections_response_models import V2CollectionModel
from openpecha_api.text.openpecha_text_service import fetch_texts_by_category, fetch_text_by_id
from openpecha_api.collection.openpecha_collection_service import fetch_category_by_id
from pecha_api.texts.texts_openpecha_api import fetch_critical_editions, fetch_text_detail, fetch_editions_segmentation, fetch_segmentation_segments, fetch_edition_content
from pecha_api.texts.text_openpecha_response_models import (
    SegmentationSegmentResponseModel,
    SegmentContentModel,
    SegmentContentResponse,
    TextDetailResponse,
    TextDetailWithContentResponse,
    TextDetailDTO,
    ContentDTO,
    SectionDTO,
    SegmentDTO,
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
        source_link=None,
        ranking=None,
        license=item.get("license"),
    )


async def _get_texts_by_collection_id(
    collection_id: str,
    skip: int,
    limit: int,
) -> Tuple[List[V2TextDTO], bool]:
    try:
        page = await fetch_texts_by_category(
            category_id=collection_id,
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
    collection_id: str,
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
) -> V2TextsCategoryResponse:
    texts, has_more = await _get_texts_by_collection_id(
        collection_id=collection_id,
        skip=skip,
        limit=limit,
    )

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


async def get_text_detail_by_id(text_id: str, offset: int, limit: int) -> TextDetailWithContentResponse:
    text_detail = await fetch_text_detail(text_id=text_id)
    edition_details = await fetch_critical_editions(text_id=text_id)
    if not edition_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"No critical editions found for text with id '{text_id}'",
        )
    segmentations = await fetch_editions_segmentation(edition_id=edition_details[0].id)
    edition_content = await fetch_edition_content(edition_id=edition_details[0].id)
    segments = await fetch_segmentation_segments(segmentation_id=segmentations[0].id, limit=limit, offset=offset)
    
    # Build segment DTOs
    segment_dtos = []
    for i, segment in enumerate(segments.items):
        content = "".join(edition_content.content[line.start:line.end] for line in segment.lines)
        segment_dtos.append(SegmentDTO(
            segment_id=segment.id,
            segment_number=offset + i + 1,
            content=content,
            translation=None
        ))
    
    # Extract title as string
    title_str = _extract_title(text_detail.title, text_detail.language)
    date_str = text_detail.date or ""
    
    # Build TextDetailDTO
    text_detail_dto = TextDetailDTO(
        id=text_detail.id,
        pecha_text_id=text_detail.bdrc or text_detail.id,
        title=title_str,
        language=text_detail.language,
        group_id=text_detail.category_id,
        type="version",
        summary="",
        is_published=True,
        created_date=date_str,
        updated_date=date_str,
        published_date=date_str,
        published_by="",
        categories=[text_detail.category_id] if text_detail.category_id else [],
        views=0,
        likes=[],
        source_link=text_detail.wiki or "unknown",
        ranking=None,
        license=text_detail.license or "unknown"
    )
    
    # Build a single section containing all segments
    section = SectionDTO(
        id=segmentations[0].id if segmentations else "",
        title="1",
        section_number=1,
        parent_id=None,
        segments=segment_dtos,
        sections=[],
        created_date=None,
        updated_date=None,
        published_date=None
    )
    
    # Build ContentDTO
    content_dto = ContentDTO(
        id=edition_details[0].id,
        text_id=text_detail.id,
        sections=[section]
    )
    
    # Calculate total segments (estimate based on has_more)
    total_segments = offset + len(segment_dtos)
    if segments.has_more:
        total_segments += 1  # Indicate there are more
    
    return TextDetailWithContentResponse(
        text_detail=text_detail_dto,
        content=content_dto,
        size=len(segment_dtos),
        pagination_direction="next",
        current_segment_position=offset + 1 if segment_dtos else 0,
        total_segments=total_segments
    )


def trim_segment_content(edition_content: str, segments: SegmentationSegmentResponseModel) -> SegmentContentResponse:
    result = []
    for i, segment in enumerate(segments.items):
        content = "".join(edition_content[line.start:line.end] for line in segment.lines)
        result.append(SegmentContentModel(id=segment.id, content=content, segment_number=i+1))
    return SegmentContentResponse(contents=result, has_more=segments.has_more, offset=segments.offset, limit=segments.limit)
async def fetch_translation_details(translation_ids: List[str]) -> List[Dict[str, Any]]:
    translation_details = []
    for translation_id in translation_ids:
        try:
            data = await fetch_text_by_id(translation_id)
            if data:
                translation_details.append(data)
        except Exception as e:
            logger.warning(f"Failed to fetch translation {translation_id}: {e}")
            continue
    return translation_details


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
        source_link=None,
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
    commentary_details = []
    for commentary_id in commentary_ids:
        try:
            data = await fetch_text_by_id(commentary_id)
            if data:
                commentary_details.append(data)
        except Exception as e:
            logger.warning(f"Failed to fetch commentary {commentary_id}: {e}")
            continue
    return commentary_details


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
