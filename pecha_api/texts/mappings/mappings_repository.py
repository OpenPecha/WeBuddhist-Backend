import uuid
from typing import List, Optional
from ..segments.segments_models import Mapping, Segment 
from ..segments.segments_enum import SegmentType

async def update_mapping(segment_id: uuid.UUID, text_id: str, mappings: List[Mapping]) -> Optional[Segment]:
    result = await Segment.get_segment_by_id_and_text_id(segment_id=segment_id, text_id=text_id)
    if result:
        result.mapping = mappings
        await result.save()
        return result
    return None

async def get_segments_by_ids(segment_ids: List[str]) -> List[Segment]:
    return await Segment.get_segments_by_ids(segment_ids=segment_ids)

async def update_mappings(segments: List[Segment]) -> List[Segment]:
    # Update all segments in bulk
    for segment in segments:
        await segment.save()
    return segments

async def get_sheet_first_content_by_ids(segment_ids: List[str], segment_type: SegmentType) -> Optional[Segment]:
   
    # NEW: Efficient - filters at database level
    segment = await Segment.get_first_segment_by_ids_and_type(
        segment_ids=segment_ids, 
        segment_type=segment_type
    )
    return segment
