import asyncio
from typing import List, Dict, Tuple
from fastapi import HTTPException
from starlette import status

from pecha_api.error_contants import ErrorConstants
from pecha_api.texts.segments.segments_repository import get_segments_by_pecha_segment_ids
from pecha_api.texts.texts_repository import get_texts_by_pecha_text_ids
from .mappings_repository import (
    update_mappings, 
    get_segments_by_ids
)
from .mappings_response_models import (
    TextMappingRequest, 
    MappingsModel, 
    TextMapping
)
from ..segments.segments_models import Segment, Mapping
from ..segments.segments_response_models import (
    SegmentResponse, 
    SegmentDTO, 
    MappingResponse
)
from ..segments.segments_utils import SegmentUtils
from ..texts_utils import TextUtils
from ...users.users_service import verify_admin_access


# Mappings Service
# ===============

async def update_segment_mapping(text_mapping_request: TextMappingRequest, token: str) -> SegmentResponse:
    # Verify admin access
    is_admin: bool = verify_admin_access(token=token)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorConstants.ADMIN_ERROR_MESSAGE
        )
    text_id_dict, segment_id_dict = await _get_text_and_segment_ids(text_mapping_request=text_mapping_request)
    for tm in text_mapping_request.text_mappings:
        tm.text_id = text_id_dict[tm.text_id]
        tm.segment_id = segment_id_dict[tm.segment_id]
        for map in tm.mappings:
            map.parent_text_id = text_id_dict[map.parent_text_id]
            map.segments = [segment_id_dict[segment] for segment in map.segments]

    # Validate mapping request
    await _validate_mapping_request(text_mapping_request=text_mapping_request)
    
    # Process segments
    segment_dict: Dict[str, List[Mapping]] = _get_segments_from_text_mapping(
        text_mappings=text_mapping_request.text_mappings
    )
    segment_ids: List[str] = list(segment_dict.keys())
    
    # Fetch and validate segments
    segments: List[Segment] = await get_segments_by_ids(segment_ids=segment_ids)
    if not segments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid segments found to update"
        )
    
    # Update segments
    segments_to_update: List[Segment] = await _construct_update_segments(
        segments=segments,
        update_segment_dict=segment_dict
    )
    updated_segments: List[Segment] = await update_mappings(segments=segments_to_update)
    if updated_segments:
        # Convert all segments to SegmentDTO
        segment_dtos = [
            SegmentDTO(
                id=str(segment.id),
                pecha_segment_id=segment.pecha_segment_id,
                text_id=segment.text_id,
                content=segment.content,
                type=segment.type,
                mapping=[MappingResponse(**mapping.model_dump()) for mapping in segment.mapping]
            ) for segment in updated_segments
        ]
        return SegmentResponse(segments=segment_dtos)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorConstants.SEGMENT_MAPPING_ERROR_MESSAGE
        )

async def delete_segment_mapping(text_mapping_request: TextMappingRequest,token: str):
    # Verify admin access
    is_admin: bool = verify_admin_access(token=token)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorConstants.ADMIN_ERROR_MESSAGE
        )
    # Validate mapping request
    #await _validate_mapping_request(text_mapping_request=text_mapping_request)
    # Process segments
    segment_dict: Dict[str, List[Mapping]] = _get_segments_from_text_mapping(
        text_mappings=text_mapping_request.text_mappings
    )
    segment_ids: List[str] = list(segment_dict.keys())

    # Fetch and validate segments
    segments: List[Segment] = await get_segments_by_ids(segment_ids=segment_ids)
    if not segments:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid segments found to update"
        )
    # Update segments
    segments_to_delete: List[Segment] = await _construct_delete_segments(
        segments=segments,
        delete_segment_dict=segment_dict
    )
    deleted_segments: List[Segment] = await update_mappings(segments=segments_to_delete)
    if deleted_segments:
        # Convert all segments to SegmentDTO
        segment_dtos = [
            SegmentDTO(
                id=str(segment.id),
                text_id=segment.text_id,
                content=segment.content,
                type=segment.type,
                mapping=[MappingResponse(**mapping.model_dump()) for mapping in segment.mapping]
            ) for segment in deleted_segments
        ]
        return SegmentResponse(segments=segment_dtos)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorConstants.SEGMENT_MAPPING_ERROR_MESSAGE
        )

async def _get_text_and_segment_ids(text_mapping_request: TextMappingRequest) -> Tuple[Dict[str, str], Dict[str, str]]:
    segment_ids=[]
    text_ids=[]
    for tm in text_mapping_request.text_mappings:
        text_ids.append(tm.text_id)
        segment_ids.append(tm.segment_id)
        for map in tm.mappings:
            text_ids.append(map.parent_text_id)
            for segment in map.segments:
                segment_ids.append(segment)
    texts = await get_texts_by_pecha_text_ids(pecha_text_ids=text_ids)
    segments = await get_segments_by_pecha_segment_ids(pecha_segment_ids=segment_ids)
    text_id_dict = {text.pecha_text_id: str(text.id) for text in texts}
    segment_id_dict = {segment.pecha_segment_id: str(segment.id) for segment in segments}
    return text_id_dict, segment_id_dict

async def _construct_delete_segments(segments: List[Segment], delete_segment_dict: Dict[str, List[Mapping]]) -> List[
    Segment]:
    deleted_segments = []

    for segment in segments:
        segment_id = str(segment.id)
        if segment_id in delete_segment_dict:
            # Get mappings to delete
            mappings_to_delete = delete_segment_dict[segment_id]
            existing_mappings: Dict[str, Mapping] = _get_existing_mappings(segment)
            # Filter out mappings that should be deleted
            remaining_mappings = [
                mapping for mapping in existing_mappings.values()
                if (mapping.text_id, tuple(sorted(mapping.segments))) not in {
                    (delete_map.text_id, tuple(sorted(delete_map.segments)))
                    for delete_map in mappings_to_delete
                }
            ]
            # Update segment with remaining mappings
            segment.mapping = remaining_mappings
            deleted_segments.append(segment)

    return deleted_segments

async def _validate_mapping_request(text_mapping_request: TextMappingRequest) -> bool:
    tasks = [
        asyncio.create_task(_validate_request_info(
            text_id=tm.text_id,
            segment_id=tm.segment_id,
            mappings=tm.mappings
        )) for tm in text_mapping_request.text_mappings
    ]
    try:
        for completed in asyncio.as_completed(tasks):
            result = await completed
            if not result:
                # Cancel all other running tasks
                for task in tasks:
                    if not task.done():
                        task.cancel()
                return False
    except asyncio.CancelledError:
        pass

    return True

def _merge_segment_mappings(existing_mapping: Mapping, new_mapping: Mapping) -> Mapping:
    # Create a set of unique segments and update existing mapping
    unique_segments = set(existing_mapping.segments + new_mapping.segments)
    existing_mapping.segments = list(unique_segments)
    return existing_mapping

def _get_existing_mappings(segment: Segment) -> Dict[str, Mapping]:
    # Create a dictionary of existing mappings by text_id for easy lookup
    return {mapping.text_id: mapping for mapping in (segment.mapping or [])}

def _process_new_mappings(new_mappings: List[Mapping], existing_mappings: Dict[str, Mapping]) -> List[Mapping]:
    merged = []
    processed_text_ids = set()
    
    # Process new mappings
    for new_mapping in new_mappings:
        processed_text_ids.add(new_mapping.text_id)
        if new_mapping.text_id in existing_mappings:
            merged.append(_merge_segment_mappings(
                existing_mappings[new_mapping.text_id],
                new_mapping
            ))
        else:
            merged.append(new_mapping)
    
    # Add unprocessed existing mappings
    merged.extend(
        mapping for text_id, mapping in existing_mappings.items()
        if text_id not in processed_text_ids
    )
    
    return merged

async def _construct_update_segments(segments: List[Segment], update_segment_dict: Dict[str, List[Mapping]]) -> List[Segment]:
    updated_segments = []
    
    for segment in segments:
        segment_id = str(segment.id)
        if segment_id in update_segment_dict:
            existing_mappings = _get_existing_mappings(segment)
            new_mappings = update_segment_dict[segment_id]
            
            segment.mapping = _process_new_mappings(new_mappings, existing_mappings)
            updated_segments.append(segment)
            
    return updated_segments

def _get_segments_from_text_mapping(text_mappings: List[TextMapping]) -> Dict[str, List[Mapping]]:
    segment_dict = {}
    for text_mapping in text_mappings:
        # Convert MappingsModel to Mapping objects
        mappings = [
            Mapping(text_id=m.parent_text_id, segments=m.segments)
            for m in text_mapping.mappings
        ]
        # Ensure segment_id is stored as string
        segment_dict[str(text_mapping.segment_id)] = mappings
    return segment_dict

async def _validate_request_info(text_id: str, segment_id: str, mappings: List[MappingsModel]) -> bool:
    # validate the text id
    await TextUtils.validate_text_exists(text_id=text_id)
    # validate the segment id
    await SegmentUtils.validate_segment_exists(segment_id=segment_id)
    # validate the parent ids
    parent_text_ids = [mapping.parent_text_id for mapping in mappings]
    if text_id in parent_text_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorConstants.SAME_TEXT_MAPPING_ERROR_MESSAGE)
    await TextUtils.validate_texts_exist(text_ids=parent_text_ids)
    # validate segment ids
    segment_ids = [segment for mapping in mappings for segment in mapping.segments]
    await SegmentUtils.validate_segments_exists(segment_ids=segment_ids)
    return True

