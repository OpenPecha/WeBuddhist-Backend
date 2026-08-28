import asyncio
import logging
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException
from starlette import status

logger = logging.getLogger(__name__)

from openpecha_api.text.openpecha_text_service import fetch_texts_by_category
from pecha_api.cache.cache_enums import CacheType
from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.error_contants import ErrorConstants
from pecha_api.group_recitation_collection.repository import (
    get_collections_by_group_ids,
    get_collection_item_counts as get_group_collection_item_counts,
)
from pecha_api.plans.groups.groups_repository import (
    get_following_group_ids_by_user,
    get_joined_group_ids_by_user,
)
from pecha_api.plans.users.recitation_collection.recitation_collection_repository import (
    get_all_user_collections,
    get_collection_item_counts,
)
from pecha_api.recitations.recication_cache_services import (
    get_recitation_by_text_id_cache,
    get_recitation_list_cache,
    set_recitation_by_text_id_cache,
    set_recitation_list_cache,
)
from pecha_api.recitations.recitations_repository import get_text_images_by_text_ids
from pecha_api.recitations.recitations_response_models import (
    ListRecitationsRequest,
    RecitationCollectionDTO,
    RecitationCollectionItemType,
    RecitationDetailsRequest,
    RecitationDetailsResponse,
    RecitationDTO,
    RecitationSegment,
    RecitationsResponse,
    Segment,
)
from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_service import (
    assert_visible_for_timezone,
    filter_items_for_timezone,
)
from pecha_api.texts.text_openpecha_response_models import (
    SegmentationSegmentResponseModel,
    SegmentContentModel,
)
from pecha_api.texts.texts_openpecha_api import (
    fetch_critical_editions,
    fetch_edition_content,
    fetch_editions_segmentation,
    fetch_segmentation_segments,
)
from pecha_api.texts.texts_openpecha_service import (
    get_text_by_id_from_openpecha,
    get_text_versions_from_openpecha,
    map_external_text_to_dto,
    trim_segment_content,
)
from pecha_api.texts.texts_response_models import V2TextDTO
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.users.users_service import validate_and_extract_user_details
from uuid import UUID

RECITATION_LIST_FETCH_LIMIT = 100  # OpenPecha's /v2/texts caps `limit` at 100
SEGMENTATION_PAGE_SIZE = 200
FIRST_SEGMENT_PREVIEW_CHAR_LIMIT = 500


def get_recitations_with_image_urls(recitations: List[RecitationDTO]) -> List[RecitationDTO]:
    text_ids = [str(recitation.text_id) for recitation in recitations]

    with SessionLocal() as db_session:
        image_keys = get_text_images_by_text_ids(db=db_session, text_ids=text_ids)

    image_url_map: Dict[str, str] = {
        text_id: generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"), s3_key=s3_key
        )
        for text_id, s3_key in image_keys.items()
    }

    return [
        recitation.model_copy(update={"image_url": image_url_map.get(str(recitation.text_id))})
        for recitation in recitations
    ]


def _presigned_image_url(s3_key: str | None) -> str | None:
    if not s3_key:
        return None
    return generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=s3_key,
    )


def _build_individual_collection_dtos(db, user_id: UUID) -> List[RecitationCollectionDTO]:
    collections = get_all_user_collections(db=db, user_id=user_id)
    if not collections:
        return []

    item_counts = get_collection_item_counts(
        db=db,
        collection_ids=[collection.id for collection in collections],
    )
    return [
        RecitationCollectionDTO(
            type=RecitationCollectionItemType.RECITATION_COLLECTION,
            name=collection.name,
            collection_id=collection.id,
            image_url=_presigned_image_url(collection.img_url),
            item_count=item_counts.get(collection.id, 0),
        )
        for collection in collections
    ]


def _build_group_collection_dtos(db, user_id: UUID) -> List[RecitationCollectionDTO]:
    # PAGE groups use follow; COMMUNITY groups use join — include both.
    related_group_ids = list(
        dict.fromkeys(
            get_following_group_ids_by_user(db=db, user_id=user_id)
            + get_joined_group_ids_by_user(db=db, user_id=user_id)
        )
    )
    collections = get_collections_by_group_ids(db=db, group_ids=related_group_ids)
    if not collections:
        return []

    item_counts = get_group_collection_item_counts(
        db=db,
        collection_ids=[collection.id for collection in collections],
    )
    return [
        RecitationCollectionDTO(
            type=RecitationCollectionItemType.GROUP_RECITATION_COLLECTION,
            name=collection.name,
            collection_id=collection.id,
            group_id=collection.group_id,
            image_url=_presigned_image_url(collection.img_url),
            item_count=item_counts.get(collection.id, 0),
        )
        for collection in collections
    ]


def _get_user_collections_for_token(
    token: Optional[str],
    should_include_collections: bool = False,
    should_include_group_collections: bool = False,
) -> List[RecitationCollectionDTO]:
    if not token or (not should_include_collections and not should_include_group_collections):
        return []

    current_user = validate_and_extract_user_details(token=token)
    with SessionLocal() as db:
        collections: List[RecitationCollectionDTO] = []
        if should_include_collections:
            collections.extend(
                _build_individual_collection_dtos(db=db, user_id=current_user.id)
            )
        if should_include_group_collections:
            collections.extend(
                _build_group_collection_dtos(db=db, user_id=current_user.id)
            )
        return collections


async def _fetch_first_edition_id(text_id: str) -> Optional[str]:
    editions = await fetch_critical_editions(text_id=text_id)
    if not editions:
        return None
    return editions[0].id


async def _fetch_first_segmentation_id(edition_id: str) -> Optional[str]:
    segmentations = await fetch_editions_segmentation(edition_id=edition_id)
    if not segmentations:
        return None
    return segmentations[0].id


async def _fetch_segmentation_id_or_none(edition_id: str) -> Optional[str]:
    """Like _fetch_first_segmentation_id, but treats "no segmentation exists for
    this edition" (OpenPecha 404s /v2/editions/{id}/segmentations) as absence
    rather than an error, so callers can fall back to unsegmented content."""
    try:
        return await _fetch_first_segmentation_id(edition_id=edition_id)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            return None
        raise


async def _whole_edition_content_as_segments(edition_id: str) -> List[SegmentContentModel]:
    edition_content = await fetch_edition_content(edition_id=edition_id)
    if not edition_content.content:
        return []
    return [SegmentContentModel(id=edition_id, content=edition_content.content, segment_number=1)]


async def _build_first_segment(text_id: str) -> Optional[Segment]:
    try:
        edition_id = await _fetch_first_edition_id(text_id=text_id)
        if edition_id is None:
            return None
        segmentation_id = await _fetch_segmentation_id_or_none(edition_id=edition_id)

        if segmentation_id is None:
            fallback_segments = await _whole_edition_content_as_segments(edition_id=edition_id)
            if not fallback_segments:
                return None
            whole = fallback_segments[0]
            return Segment(id=whole.id, content=whole.content[:FIRST_SEGMENT_PREVIEW_CHAR_LIMIT])

        segments_page = await fetch_segmentation_segments(
            segmentation_id=segmentation_id, limit=1, offset=0
        )
        if not segments_page.items:
            return None
        edition_content = await fetch_edition_content(edition_id=edition_id)
        trimmed = trim_segment_content(
            edition_content=edition_content.content, segments=segments_page
        )
        if not trimmed.contents:
            return None
        first = trimmed.contents[0]
        return Segment(id=first.id, content=first.content)
    except Exception:
        return None


async def _fetch_recitation_texts_from_openpecha(
    language: str,
    search: Optional[str],
    skip: int,
    limit: int,
) -> Tuple[List[RecitationDTO], int]:
    try:
        page = await fetch_texts_by_category(
            category_id=get("RECITATION_CATEGORY_ID"),
            language=language,
            title=search,
            limit=RECITATION_LIST_FETCH_LIMIT,
            offset=0,
        )
    except Exception:
        logger.exception("Failed to fetch recitations from OpenPecha category %s", get("RECITATION_CATEGORY_ID"))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch recitations from upstream service",
        )

    items = page.get("items", [])
    texts = [map_external_text_to_dto(item, language) for item in items]
    total = len(texts)
    paginated = texts[skip: skip + limit]

    recitations = [RecitationDTO(title=text.title, text_id=text.id) for text in paginated]
    return recitations, total


async def get_list_of_recitations_service(
    request: ListRecitationsRequest,
) -> RecitationsResponse:
    cached_data: Optional[RecitationsResponse] = await get_recitation_list_cache(
        language=request.language,
        search=request.search,
        skip=request.skip,
        limit=request.limit,
        cache_type=CacheType.RECITATION_LIST,
    )

    if cached_data is not None:
        recitations = cached_data.recitations
        total = cached_data.total
    else:
        recitations, total = await _fetch_recitation_texts_from_openpecha(
            language=request.language,
            search=request.search,
            skip=request.skip,
            limit=request.limit,
        )
        first_segments = await asyncio.gather(
            *[_build_first_segment(text_id=recitation.text_id) for recitation in recitations]
        )
        recitations = [
            recitation.model_copy(update={"first_segment": first_segment})
            for recitation, first_segment in zip(recitations, first_segments)
        ]
        await set_recitation_list_cache(
            language=request.language,
            search=request.search,
            skip=request.skip,
            limit=request.limit,
            cache_type=CacheType.RECITATION_LIST,
            data=RecitationsResponse(
                recitations=recitations,
                collections=[],
                skip=request.skip,
                limit=request.limit,
                total=total,
            ),
        )

    recitations_with_images = get_recitations_with_image_urls(recitations=recitations)
    visible_recitations = filter_items_for_timezone(
        recitations_with_images,
        timezone_name=request.timezone_name,
        item_type=RestrictedItemType.RECITATION,
        id_of=lambda recitation: recitation.text_id,
    )

    return RecitationsResponse(
        recitations=visible_recitations,
        collections=_get_user_collections_for_token(
            token=request.token,
            should_include_collections=request.should_include_collections,
            should_include_group_collections=request.should_include_group_collections,
        ),
        skip=request.skip,
        limit=request.limit,
        total=total,
    )


async def _fetch_full_edition_segments(text_id: str) -> List[SegmentContentModel]:
    edition_id = await _fetch_first_edition_id(text_id=text_id)
    if edition_id is None:
        return []
    segmentation_id = await _fetch_segmentation_id_or_none(edition_id=edition_id)
    if segmentation_id is None:
        return await _whole_edition_content_as_segments(edition_id=edition_id)

    all_segments = []
    offset = 0
    while True:
        page = await fetch_segmentation_segments(
            segmentation_id=segmentation_id, limit=SEGMENTATION_PAGE_SIZE, offset=offset
        )
        all_segments.extend(page.items)
        if not page.has_more or not page.items:
            break
        offset += SEGMENTATION_PAGE_SIZE

    if not all_segments:
        return await _whole_edition_content_as_segments(edition_id=edition_id)

    edition_content = await fetch_edition_content(edition_id=edition_id)
    combined_segments = SegmentationSegmentResponseModel(
        items=all_segments, has_more=False, offset=0, limit=len(all_segments)
    )
    trimmed = trim_segment_content(edition_content=edition_content.content, segments=combined_segments)
    return trimmed.contents


async def _safe_fetch_full_edition_segments(text_id: str) -> List[SegmentContentModel]:
    try:
        return await _fetch_full_edition_segments(text_id=text_id)
    except Exception:
        return []


async def _fetch_language_segment_map(
    languages: List[str],
    candidates: List,
) -> Dict[str, List[SegmentContentModel]]:
    language_to_text_id: Dict[str, str] = {}
    for candidate in candidates:
        if candidate.language and candidate.language not in language_to_text_id:
            language_to_text_id[candidate.language] = candidate.id

    relevant_languages = [language for language in languages if language in language_to_text_id]
    if not relevant_languages:
        return {}

    fetched = await asyncio.gather(
        *[
            _safe_fetch_full_edition_segments(text_id=language_to_text_id[language])
            for language in relevant_languages
        ]
    )
    return dict(zip(relevant_languages, fetched))


def _segments_bucket_for_index(
    languages: List[str],
    language_segments: Dict[str, List[SegmentContentModel]],
    index: int,
) -> Dict[str, Segment]:
    bucket: Dict[str, Segment] = {}
    for language in languages:
        segments = language_segments.get(language)
        if not segments or index >= len(segments):
            continue
        segment = segments[index]
        bucket[language] = Segment(id=segment.id, content=segment.content)
    return bucket


def _build_recitation_segments(
    root_language: str,
    language_segments: Dict[str, List[SegmentContentModel]],
    recitation_details_request: RecitationDetailsRequest,
) -> List[RecitationSegment]:
    root_segments = language_segments.get(root_language, [])

    return [
        RecitationSegment(
            recitation=_segments_bucket_for_index(
                recitation_details_request.recitation, language_segments, index
            ),
            translations=_segments_bucket_for_index(
                recitation_details_request.translations, language_segments, index
            ),
            transliterations=_segments_bucket_for_index(
                recitation_details_request.transliterations, language_segments, index
            ),
            adaptations=_segments_bucket_for_index(
                recitation_details_request.adaptations, language_segments, index
            ),
        )
        for index in range(len(root_segments))
    ]


async def get_recitation_details_service(
    text_id: str,
    recitation_details_request: RecitationDetailsRequest,
    timezone_name: Optional[str] = None,
) -> RecitationDetailsResponse:
    assert_visible_for_timezone(
        timezone_name=timezone_name,
        item_type=RestrictedItemType.RECITATION,
        item_id=text_id,
        not_found_detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE,
    )

    cached_data: RecitationDetailsResponse = await get_recitation_by_text_id_cache(text_id=text_id, recitation_details_request=recitation_details_request, cache_type=CacheType.RECITATION_DETAILS)
    if cached_data is not None:
        return cached_data

    text_detail: V2TextDTO = await get_text_details_by_text_id(text_id=text_id)

    version_response = await get_text_versions_from_openpecha(text_id=text_id)
    candidates = [version_response.text] + list(version_response.versions or [])

    root_text = None
    for candidate in candidates:
        if candidate.language == recitation_details_request.language and root_text is None:
            root_text = candidate
    if root_text is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)

    requested_languages = {recitation_details_request.language}
    requested_languages.update(recitation_details_request.recitation)
    requested_languages.update(recitation_details_request.translations)
    requested_languages.update(recitation_details_request.transliterations)
    requested_languages.update(recitation_details_request.adaptations)

    language_segments = await _fetch_language_segment_map(
        languages=list(requested_languages),
        candidates=candidates,
    )

    segments = _build_recitation_segments(
        root_language=recitation_details_request.language,
        language_segments=language_segments,
        recitation_details_request=recitation_details_request,
    )

    recitation_details_response = RecitationDetailsResponse(
        text_id=text_detail.id,
        title=text_detail.title,
        segments=segments
    )

    await set_recitation_by_text_id_cache(
        text_id=text_id,
        recitation_details_request=recitation_details_request,
        cache_type=CacheType.RECITATION_DETAILS,
        data=recitation_details_response
    )

    return recitation_details_response

async def get_text_details_by_text_id(text_id: str) -> V2TextDTO:
    return await get_text_by_id_from_openpecha(text_id=text_id)
