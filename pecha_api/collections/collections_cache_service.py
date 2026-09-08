from pecha_api.utils import Utils

from pecha_api.cache.cache_repository import (
    get_cache_data,
    set_cache,
)
from pecha_api import config
from .collections_response_models import CollectionModel
from pecha_api.cache.cache_enums import CacheType


async def get_collection_detail_cache(collection_id: str = None, language: str = None, cache_type: CacheType = None) -> CollectionModel:
    """Get collection detail cache asynchronously."""
    payload = [collection_id, language, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload=payload)
    cache_data: CollectionModel = await get_cache_data(hash_key=hashed_key)
    if cache_data and isinstance(cache_data, dict):
        cache_data = CollectionModel(**cache_data)
    return cache_data

async def set_collection_detail_cache(collection_id: str = None, language: str = None, data: CollectionModel = None, cache_type: CacheType = None):
    """Set collection detail cache asynchronously."""
    payload = [collection_id, language, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload=payload)
    cache_time_out = config.get_int("CACHE_COLLECTION_TIMEOUT")
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=cache_time_out)
