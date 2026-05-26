from pecha_api.utils import Utils

from pecha_api.cache.cache_repository import (
    get_cache_data,
    set_cache
)
from pecha_api import config
from .groups_response_models import (
    GroupDTO
)
from pecha_api.cache.cache_enums import CacheType

async def get_group_by_id_cache(group_id: str = None, cache_type: CacheType = None) -> GroupDTO:
    """Get group by id cache asynchronously."""
    payload = [group_id, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_data: GroupDTO = await get_cache_data(hash_key = hashed_key)
    if cache_data and isinstance(cache_data, dict):
        cache_data = GroupDTO(**cache_data)
    return cache_data

async def set_group_by_id_cache(group_id: str = None, cache_type: CacheType = None, data: GroupDTO = None):
    """Set group by id cache asynchronously."""
    payload = [group_id, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_time_out = config.get_int("CACHE_TEXT_TIMEOUT")
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=cache_time_out)
