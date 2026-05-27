from pecha_api.utils import Utils
from pecha_api.cache.cache_repository import (
    get_cache_data,
    set_cache,
)
from pecha_api import config
from .segments_response_models import (
    SegmentDTO,
)
from typing import Dict, List
from pecha_api.cache.cache_enums import CacheType

async def get_segments_details_by_ids_cache(segment_ids: List[str] = None, cache_type: CacheType = None) -> Dict[str, SegmentDTO]:
    payload = list(segment_ids) + [cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_data: Dict[str, SegmentDTO] = await get_cache_data(hash_key = hashed_key)
    if cache_data and isinstance(cache_data, dict):
        cache_data = {k: SegmentDTO(**v) for k, v in cache_data.items()}
    return cache_data

async def set_segments_details_by_ids_cache(segment_ids: List[str] = None, cache_type: CacheType = None, data: Dict[str, SegmentDTO] = None):
    payload = list(segment_ids) + [cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_time_out = config.get_int("CACHE_TEXT_TIMEOUT")
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=cache_time_out)