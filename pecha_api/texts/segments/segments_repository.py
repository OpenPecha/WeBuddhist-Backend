from __future__ import annotations

from uuid import UUID

from pecha_api.constants import Constants
from .segments_models import Segment
from .segments_response_models import (
    CreateSegmentRequest,
    SegmentContentBulkUpdateRequest,
    SegmentDTO,
    MappingResponse,
    SegmentUpdateRequest,
)
import logging
from beanie.exceptions import CollectionWasNotInitialized
from typing import List, Dict, Optional
from fastapi import HTTPException
from starlette import status
from pecha_api.error_contants import ErrorConstants

async def get_segments_by_pecha_segment_ids(pecha_segment_ids: List[str]) -> List[SegmentDTO]:
    try:
        return await Segment.get_segments_by_pecha_segment_ids(pecha_segment_ids=pecha_segment_ids)
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return []

async def get_segment_by_id(segment_id: str) -> SegmentDTO | None:
    try:
        segment = await Segment.get_segment_by_id(segment_id=segment_id)
        return segment
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return None

async def get_segments_by_text_id(text_id: str) -> List[SegmentDTO]:
    try:
        segments = await Segment.get_segments_by_text_id(text_id=text_id)
        return segments
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return []


async def get_segment_details_by_id(segment_id: str):
    return await Segment.get_segment_details(segment_id=segment_id)

async def check_segment_exists(segment_id: UUID) -> bool:
    try:
        is_segment_exists = await Segment.check_exists(segment_id=segment_id)
        return is_segment_exists
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return False


async def check_all_segment_exists(segment_ids: List[UUID]) -> bool:
    try:
        is_segment_exists = await Segment.exists_all(segment_ids=segment_ids, batch_size=Constants.QUERY_BATCH_SIZE)
        return is_segment_exists
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return False


async def get_segments_by_ids(segment_ids: List[str]) -> Dict[str, SegmentDTO]:
    try:
        if not segment_ids:
            return {}
        list_of_segments_detail = await Segment.get_segments_by_ids(segment_ids=segment_ids)
        return {str(segment.id): SegmentDTO(
            id=str(segment.id),
            text_id=segment.text_id,
            content=segment.content,
            mapping=[MappingResponse(**mapping.model_dump()) for mapping in segment.mapping],
            type=segment.type
        ) for segment in list_of_segments_detail}
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return {}


async def create_segment(create_segment_request: CreateSegmentRequest) -> List[Segment]:
    new_segment_list = [
        Segment(
            pecha_segment_id=segment.pecha_segment_id,
            text_id=create_segment_request.text_id,
            content=segment.content,
            mapping=segment.mapping,
            type=segment.type
        )
        for segment in create_segment_request.segments
    ]
    # Store the insert result but don't return it directly
    await Segment.insert_many(new_segment_list)

    return new_segment_list

async def get_related_mapped_segments(parent_segment_id: str) -> List[SegmentDTO]:
    try:
        segments = await Segment.get_related_mapped_segments(parent_segment_id=parent_segment_id)
        return segments
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return []


async def get_related_mapped_segments_batch(
    parent_segment_ids: List[str]
) -> Dict[str, List[SegmentDTO]]:

    try:
        if not parent_segment_ids:
            return {}
        segments_dict = await Segment.get_related_mapped_segments_batch(
            parent_segment_ids=parent_segment_ids
        )
        result: Dict[str, List[SegmentDTO]] = {}
        for parent_id, segments in segments_dict.items():
            result[parent_id] = [
                SegmentDTO(
                    id=str(segment.id),
                    text_id=segment.text_id,
                    content=segment.content,
                    mapping=[MappingResponse(**mapping.model_dump()) for mapping in segment.mapping] if segment.mapping else [],
                    type=segment.type
                )
                for segment in segments
            ]
        return result
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return {}

async def delete_segments_by_text_id(text_id: str):
    try:
        await Segment.delete_segment_by_text_id(text_id=text_id)
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return False


async def update_segment_by_id(segment_update_request: SegmentUpdateRequest) -> SegmentDTO | None:
    try:
        for segment_update in segment_update_request.segments:
            segment = await Segment.get_segment_by_pecha_segment_id(pecha_segment_id=segment_update.pecha_segment_id)
            if not segment:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE)
            segment.content = segment_update.content
            await segment.save()
        
        return segment
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return None


async def update_segment_content_bulk(
    bulk_update_request: SegmentContentBulkUpdateRequest,
) -> List[SegmentDTO]:
    try:
        if not bulk_update_request.segments:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ErrorConstants.INVALID_UPDATE_REQUEST)

        segment_ids: List[str] = [segment_update.id for segment_update in bulk_update_request.segments]
        segments = await Segment.get_segments_by_ids(segment_ids=segment_ids)
        segments_by_id: Dict[str, Segment] = {str(segment.id): segment for segment in segments}

        missing_ids = [segment_id for segment_id in segment_ids if segment_id not in segments_by_id]
        if missing_ids:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE)

        updated_segments: List[SegmentDTO] = []

        for segment_update in bulk_update_request.segments:
            segment = segments_by_id[segment_update.id]
            segment.content = segment_update.content
            await segment.save()

            updated_segments.append(
                SegmentDTO(
                    id=str(segment.id),
                    pecha_segment_id=segment.pecha_segment_id,
                    text_id=segment.text_id,
                    content=segment.content,
                    mapping=[MappingResponse(**mapping.model_dump()) for mapping in segment.mapping] if segment.mapping else [],
                    type=segment.type,
                )
            )

        return updated_segments
    except CollectionWasNotInitialized as e:
        logging.debug(e)
        return []