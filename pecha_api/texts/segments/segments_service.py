from pecha_api.error_contants import ErrorConstants
from .segments_repository import (
    create_segment,
    get_segments_by_ids,
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
    SegmentUpdateRequest,
    SegmentSearchRequest,
)

from pecha_api.cache.cache_enums import CacheType

from fastapi import HTTPException
from starlette import status

from ..texts_utils import TextUtils

from typing import List, Dict

from .segments_cache_service import (
    get_segments_details_by_ids_cache,
    set_segments_details_by_ids_cache,
)

from ..texts_repository import get_text_by_pecha_text_id
from ...users.users_service import validate_user_exists

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