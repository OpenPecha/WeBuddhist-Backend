from pecha_api.error_contants import ErrorConstants
from .segments_repository import (
    create_segment,
    get_segment_by_id, 
    get_segments_by_ids,
    get_related_mapped_segments,
    get_related_mapped_segments_batch,
    get_segments_by_text_id,
    delete_segments_by_text_id,
    update_segment_by_id,
    search_segments_by_content,
)
from ...users.users_service import verify_admin_access
from .segments_response_models import (
    CreateSegmentRequest, 
    SegmentResponse, 
    MappingResponse, 
    SegmentDTO, 
    SegmentInfoResponse,
    SegmentRootMappingResponse,
    SegmentUpdateRequest,
    SegmentSearchRequest,
)

from pecha_api.cache.cache_enums import CacheType

from fastapi import HTTPException
from starlette import status

from .segments_utils import SegmentUtils
from ..texts_utils import TextUtils
from ..texts_response_models import TextDTO
from pecha_api.plans.videos.plan_video_service import get_public_plan_videos_by_segment_id

from typing import List, Dict

from .segments_response_models import (
    SegmentTranslationsResponse, 
    ParentSegment, 
    SegmentCommentariesResponse,
    RelatedText, 
    Resources, 
    SegmentInfo, 
    SegmentRootMappingResponse,
    SegmentRootMapping,
    MappedSegmentResponseDTO,
)

from .segments_cache_service import (
    set_segment_info_by_id_cache,
    get_segment_info_by_id_cache,
    get_segment_root_mapping_by_id_cache,
    set_segment_root_mapping_by_id_cache,
    get_segment_translations_by_id_cache,
    set_segment_translations_by_id_cache,
    get_segment_commentaries_by_id_cache,
    set_segment_commentaries_by_id_cache,
    get_segments_details_by_ids_cache,
    set_segments_details_by_ids_cache,
    delete_segments_details_by_ids_cache
)

from pecha_api.uploads.S3_utils import generate_presigned_access_url

from .segments_enum import SegmentType
from ..texts_service import TextUtils
from ..texts_repository import get_text_by_pecha_text_id
from ...users.users_service import validate_user_exists

import logging
from openpecha_api.segments.openpecha_segment_service import (
    fetch_segment_details,
    fetch_segment_content,
    fetch_related_segments,
)
from openpecha_api.text.openpecha_text_service import fetch_text_by_id
from pecha_api.texts.texts_openpecha_service import _extract_title

logger = logging.getLogger(__name__)

async def get_segments_details_by_ids(segment_ids: List[str]) -> Dict[str, SegmentDTO]:
    cached_data: Dict[str, SegmentDTO] = await get_segments_details_by_ids_cache(segment_ids=segment_ids, cache_type=CacheType.SEGMENTS_DETAILS)
    if cached_data is not None:
        return cached_data
    
    segments: Dict[str, SegmentDTO] = await get_segments_by_ids(segment_ids=segment_ids)
    
    await set_segments_details_by_ids_cache(segment_ids=segment_ids, cache_type=CacheType.SEGMENTS_DETAILS, data=segments)
    
    return segments

async def search_segments_by_content_service(
    segment_search_request: SegmentSearchRequest,
) -> SegmentResponse:
    segments = await search_segments_by_content(content=segment_search_request.content)
    return SegmentResponse(segments=segments)


async def get_segment_details_by_id(segment_id: str, text_details: bool = False) -> SegmentDTO:
    """
    Get segment details by ID using OpenPecha API (Neo4j).
    """
    
    # Fetch segment details and content from OpenPecha API
    try:
        segment_details = await fetch_segment_details(segment_id)
    except Exception as e:
        logger.error(f"Failed to fetch segment {segment_id} from OpenPecha API: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Segment not found: {str(e)}"
        )
    
    if not segment_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE
        )
    
    # Fetch content separately
    try:
        content = await fetch_segment_content(segment_id)
    except Exception:
        content = ""
    
    text_id = segment_details.get("text_id", "")
    
    # Build mapping from related segments
    mapping_responses: List[MappingResponse] = []
    try:
        related_page = await fetch_related_segments(segment_id=segment_id, limit=100, offset=0)
        items = related_page.get("items", []) or []
        
        # Group related segments by text_id
        mapping_by_text: Dict[str, List[str]] = {}
        for item in items:
            item_text_id = item.get("text_id")
            item_segment_id = item.get("id")
            if item_text_id and item_segment_id:
                if item_text_id not in mapping_by_text:
                    mapping_by_text[item_text_id] = []
                mapping_by_text[item_text_id].append(item_segment_id)
        
        mapping_responses = [
            MappingResponse(text_id=tid, segments=seg_ids)
            for tid, seg_ids in mapping_by_text.items()
        ]
    except Exception:
        # If related segments fetch fails, return empty mapping
        mapping_responses = []
    
    # Determine segment type from OpenPecha response
    segment_type_str = segment_details.get("type", "source")
    try:
        segment_type = SegmentType(segment_type_str)
    except ValueError:
        segment_type = SegmentType.SOURCE
    
    # Fetch text details if requested
    text = None
    if text_details and text_id:
        try:
            text_payload = await fetch_text_by_id(text_id)
            if text_payload:
                text = TextDTO(
                    id=text_id,
                    pecha_text_id=text_payload.get("pecha_text_id"),
                    title=_extract_title(text_payload.get("title", {})),
                    language=text_payload.get("language"),
                    group_id=text_payload.get("group_id", ""),
                    type=text_payload.get("type", ""),
                    summary=text_payload.get("summary", ""),
                    is_published=text_payload.get("is_published", False),
                    created_date=text_payload.get("created_date", ""),
                    updated_date=text_payload.get("updated_date", ""),
                    published_date=text_payload.get("published_date", ""),
                    published_by=text_payload.get("published_by", ""),
                    categories=text_payload.get("categories"),
                    views=text_payload.get("views", 0),
                    likes=text_payload.get("likes", []),
                    source_link=text_payload.get("source_link"),
                    ranking=text_payload.get("ranking"),
                    license=text_payload.get("license"),
                )
        except Exception:
            text = None
    
    response = SegmentDTO(
        id=segment_id,
        pecha_segment_id=segment_details.get("pecha_segment_id", segment_id),
        text_id=text_id,
        content=content or "",
        mapping=mapping_responses,
        type=segment_type,
        text=text
    )
    return response

async def create_new_segment(create_segment_request: CreateSegmentRequest, token: str) -> SegmentResponse:
    is_valid_user = validate_user_exists(token=token)
    if is_valid_user:
        await TextUtils.validate_text_exists(text_id=create_segment_request.text_id)
        new_segment = await create_segment(create_segment_request=create_segment_request)
        segments =  [
            SegmentDTO(
                id=str(segment.id),
                pecha_segment_id=str(segment.pecha_segment_id),
                text_id=segment.text_id,
                content=segment.content,
                mapping= [MappingResponse(**mapping.model_dump()) for mapping in segment.mapping],
                type=segment.type
            )
            for segment in new_segment
        ]
        return SegmentResponse(segments=segments)
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ErrorConstants.TOKEN_ERROR_MESSAGE)

async def get_translations_by_segment_id(segment_id: str) -> SegmentTranslationsResponse:
    """
    Get translations for a given segment ID.
    """
    
    is_valid_segment = await SegmentUtils.validate_segment_exists(segment_id=segment_id)
    if not is_valid_segment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE)

    cache_data = await get_segment_translations_by_id_cache(
        segment_id=segment_id, cache_type=CacheType.SEGMENT_TRANSLATIONS
    )
    if cache_data:
        return cache_data

    parent_segment = await get_segment_by_id(segment_id=segment_id)
    mapped_segments = await get_related_mapped_segments(parent_segment_id=segment_id)
    translations = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(segments=mapped_segments, type="version")
    response = SegmentTranslationsResponse(
        parent_segment=ParentSegment(
            segment_id=str(parent_segment.id),
            content=parent_segment.content
        ),
        translations=translations
    )

    await set_segment_translations_by_id_cache(
        segment_id=segment_id, cache_type=CacheType.SEGMENT_TRANSLATIONS, data=response
    )
    return response

async def get_commentaries_by_segment_id(
        segment_id: str
) -> SegmentCommentariesResponse:
    
    is_valid_segment = await SegmentUtils.validate_segment_exists(segment_id=segment_id)
    if not is_valid_segment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE)

    cache_data = await get_segment_commentaries_by_id_cache(
        segment_id=segment_id, cache_type=CacheType.SEGMENT_COMMENTARIES
    )
    if cache_data:
        return cache_data

    parent_segment = await get_segment_by_id(segment_id=segment_id)
    mapped_segments = await get_related_mapped_segments(parent_segment_id=segment_id)
    commentaries = await SegmentUtils.filter_segment_mapping_by_type_or_text_id(segments=mapped_segments, type="commentary")
    response = SegmentCommentariesResponse(
        parent_segment=ParentSegment(
            segment_id=segment_id,
            content=parent_segment.content
        ),
        commentaries=commentaries
    )

    await set_segment_commentaries_by_id_cache(
        segment_id=segment_id, cache_type=CacheType.SEGMENT_COMMENTARIES, data=response
    )
    return response

async def get_info_by_segment_id(segment_id: str) -> SegmentInfoResponse:
    """
    Get segment info by ID using OpenPecha API (Neo4j).
    Videos are fetched from PostgreSQL and attached to the response.
    """
    # Videos are author-editable and change more often than the rest of the
    # segment info, so they are intentionally NOT cached: the cached response
    # always holds an empty video list, and live videos are attached on every
    # request (both cache hit and miss) so edits are reflected immediately.
    cache_data = await get_segment_info_by_id_cache(segment_id=segment_id, cache_type=CacheType.SEGMENT_INFO)
    if cache_data:
        try:
            cache_data.segment_info.videos = get_public_plan_videos_by_segment_id(segment_id=segment_id).videos
        except Exception:
            cache_data.segment_info.videos = []
        return cache_data
    
    # Fetch segment details from OpenPecha API
    try:
        segment_details = await fetch_segment_details(segment_id)
    except Exception as e:
        logger.error(f"Failed to fetch segment info {segment_id} from OpenPecha API: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE
        )
    
    text_id = segment_details.get("text_id")
    if not text_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text ID not found for segment '{segment_id}'"
        )
    
    # Fetch text details from OpenPecha API
    try:
        text_payload = await fetch_text_by_id(text_id)
    except Exception as e:
        logger.error(f"Failed to fetch text {text_id} from OpenPecha API: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found"
        )
    
    if not text_payload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found"
        )
    
    # Get counts from text payload
    translations_count = len(text_payload.get("translations", []))
    commentaries_count = len(text_payload.get("commentaries", []))
    
    # Determine root_text count
    root_text_count = 0
    if text_payload.get("commentary_of") or text_payload.get("translation_of"):
        root_text_count = 1
    
    response = SegmentInfoResponse(
        segment_info=SegmentInfo(
            segment_id=segment_id,
            text_id=text_id,
            translations=translations_count,
            related_text=RelatedText(
                commentaries=commentaries_count,
                root_text=root_text_count
            ),
            resources=Resources(
                sheets=0
            )
        )
    )
    
    # Cache the response WITHOUT videos, then attach live videos before returning.
    await set_segment_info_by_id_cache(
        segment_id=segment_id,
        cache_type=CacheType.SEGMENT_INFO,
        data=response
    )
    try:
        response.segment_info.videos = get_public_plan_videos_by_segment_id(segment_id=segment_id).videos
    except Exception:
        # Video fetch may fail if segment_id is not UUID format (OpenPecha uses different IDs)
        response.segment_info.videos = []
    return response

async def get_root_text_mapping_by_segment_id(segment_id: str) -> SegmentRootMappingResponse:
    """
    Get root text mapping for a segment using OpenPecha API (Neo4j).
    Returns the root texts that this segment's text is a translation/commentary of.
    """
    cache_data = await get_segment_root_mapping_by_id_cache(
        segment_id=segment_id, cache_type=CacheType.SEGMENT_ROOT_TEXT
    )
    if cache_data:
        return cache_data

    # Fetch segment details and content from OpenPecha API
    try:
        segment_details = await fetch_segment_details(segment_id)
    except Exception as e:
        logger.error(f"Failed to fetch segment {segment_id} from OpenPecha API: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE
        )
    
    # Fetch segment content
    try:
        segment_content = await fetch_segment_content(segment_id)
    except Exception:
        segment_content = ""
    
    text_id = segment_details.get("text_id")
    if not text_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text ID not found for segment '{segment_id}'"
        )
    
    # Fetch text details to get root text info (translation_of or commentary_of)
    try:
        text_payload = await fetch_text_by_id(text_id)
    except Exception as e:
        logger.error(f"Failed to fetch text {text_id} from OpenPecha API: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Text with id '{text_id}' not found"
        )
    
    segment_root_mapping: List[SegmentRootMapping] = []
    
    # Get root text IDs (the text this is a translation/commentary of)
    root_text_id = text_payload.get("translation_of") or text_payload.get("commentary_of")
    
    if root_text_id:
        # Fetch root text details
        try:
            root_text_payload = await fetch_text_by_id(root_text_id)
            if root_text_payload:
                # Fetch related segments from the root text
                try:
                    related_page = await fetch_related_segments(
                        segment_id=segment_id,
                        limit=100,
                        offset=0,
                        text_id=root_text_id
                    )
                    items = related_page.get("items", []) or []
                    
                    # Build mapped segments list
                    mapped_segments: List[MappedSegmentResponseDTO] = []
                    for item in items:
                        item_content = ""
                        try:
                            item_content = await fetch_segment_content(item["id"]) or ""
                        except Exception:
                            pass
                        mapped_segments.append(MappedSegmentResponseDTO(
                            segment_id=item["id"],
                            content=item_content
                        ))
                    
                    if mapped_segments:
                        from pecha_api.texts.texts_openpecha_service import _extract_title
                        segment_root_mapping.append(SegmentRootMapping(
                            text_id=root_text_id,
                            title=_extract_title(root_text_payload.get("title", {})),
                            language=root_text_payload.get("language", ""),
                            segments=mapped_segments
                        ))
                except Exception as e:
                    logger.error(f"Failed to fetch related segments for root text {root_text_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to fetch root text {root_text_id}: {e}")
    
    response = SegmentRootMappingResponse(
        parent_segment=ParentSegment(
            segment_id=segment_id,
            content=segment_content or ""
        ),
        segment_root_mapping=segment_root_mapping
    )

    await set_segment_root_mapping_by_id_cache(
        segment_id=segment_id, cache_type=CacheType.SEGMENT_ROOT_TEXT, data=response
    )
    return response
async def fetch_segments_by_text_id(text_id: str) -> List[SegmentDTO]:
    segments = await get_segments_by_text_id(text_id=text_id)
    return segments

async def remove_segments_by_text_id(text_id: str):
    is_valid_text = await TextUtils.validate_text_exists(text_id=text_id)
    if not is_valid_text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
    return await delete_segments_by_text_id(text_id=text_id)


async def update_segments_service(token: str, segment_update_request: SegmentUpdateRequest):
    is_admin = verify_admin_access(token=token)
    if is_admin:    
        text = await get_text_by_pecha_text_id(pecha_text_id=segment_update_request.pecha_text_id)
        if not text:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE)
        
        return await update_segment_by_id(segment_update_request=segment_update_request) 


    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ErrorConstants.ADMIN_ERROR_MESSAGE)