from typing import Dict, List, Optional

from pecha_api.texts.segments.segments_enum import SegmentType
from pecha_api.texts.segments.segments_models import Mapping, Segment


async def get_mapping_segments_by_ids(segment_ids: List[str]) -> List[dict]:
    return await Segment.get_mapping_segments_by_ids(segment_ids=segment_ids)


async def bulk_update_segment_mappings(
    segment_mappings: Dict[str, List[Mapping]],
) -> None:
    await Segment.bulk_set_segment_mappings(segment_mappings=segment_mappings)


async def get_sheet_first_content_by_ids(segment_ids: List[str], segment_type: SegmentType) -> Optional[Segment]:
    return await Segment.get_first_segment_by_ids_and_type(
        segment_ids=segment_ids,
        segment_type=segment_type,
    )
