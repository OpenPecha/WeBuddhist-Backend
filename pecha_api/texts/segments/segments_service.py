from .segments_repository import (
    get_segments_by_ids,
)
from .segments_response_models import (
    SegmentDTO,
)

from pecha_api.cache.cache_enums import CacheType

from typing import List, Dict

from .segments_cache_service import (
    get_segments_details_by_ids_cache,
    set_segments_details_by_ids_cache,
)

async def get_segments_details_by_ids(segment_ids: List[str]) -> Dict[str, SegmentDTO]:
    cached_data: Dict[str, SegmentDTO] = await get_segments_details_by_ids_cache(segment_ids=segment_ids, cache_type=CacheType.SEGMENTS_DETAILS)
    if cached_data is not None:
        return cached_data
    
    segments: Dict[str, SegmentDTO] = await get_segments_by_ids(segment_ids=segment_ids)
    
    await set_segments_details_by_ids_cache(segment_ids=segment_ids, cache_type=CacheType.SEGMENTS_DETAILS, data=segments)
    
    return segments
