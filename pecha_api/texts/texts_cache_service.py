
from pecha_api.utils import Utils

from pecha_api.cache.cache_repository import (
    get_cache_data,
    set_cache,
    clear_cache,
    update_cache,
    invalidate_text_related_cache,
    invalidate_multiple_cache_keys,
)
from .texts_response_models import TextDTO

from pecha_api.cache.cache_enums import CacheType

import logging
from pecha_api import config

async def set_text_details_by_id_cache(text_id: str = None, cache_type: CacheType = None, data: TextDTO = None):
    """Set text details by id cache asynchronously."""
    payload = [text_id, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_time_out = config.get_int("CACHE_TEXT_TIMEOUT")
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=cache_time_out)

async def get_text_details_by_id_cache(text_id: str = None, cache_type: CacheType = None) -> TextDTO:
    payload = [text_id, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_data: TextDTO = await get_cache_data(hash_key = hashed_key)
    if cache_data and isinstance(cache_data, dict):
        cache_data = TextDTO(**cache_data)
    return cache_data

async def delete_text_details_by_id_cache(text_id: str = None, cache_type: CacheType = None):
    payload = [text_id, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    await clear_cache(hash_key = hashed_key)


async def update_text_details_cache(text_id: str, updated_text_data: TextDTO, cache_type: CacheType = CacheType.TEXT_DETAIL) -> bool:
    try:
        primary_cache_payload = [text_id, cache_type]
        primary_cache_hash_key = Utils.generate_hash_key(payload=primary_cache_payload)
        
        texts_by_id_payload = [text_id, None, None, None, None, CacheType.TEXTS_BY_ID_OR_COLLECTION]
        texts_by_id_hash_key = Utils.generate_hash_key(payload=texts_by_id_payload)
        
        update_results = []
        
        cache_time_out = config.get_int("CACHE_TEXT_TIMEOUT")
        is_primary_cache_updated = await update_cache(hash_key=primary_cache_hash_key, value=updated_text_data, cache_time_out=cache_time_out)
        update_results.append(is_primary_cache_updated)
        
        is_texts_by_id_updated = await update_cache(hash_key=texts_by_id_hash_key, value=updated_text_data, cache_time_out=cache_time_out)
        update_results.append(is_texts_by_id_updated)
        
        if not any(update_results):
            await invalidate_text_cache_on_update(text_id=text_id, cache_type=cache_type)
            
        return True
    except Exception as e:
        logging.error(f"Error updating text details cache for text_id {text_id}: {str(e)}", exc_info=True)
        await invalidate_text_cache_on_update(text_id=text_id, cache_type=cache_type)
        return False


async def invalidate_text_cache_on_update(text_id: str, cache_type: CacheType = CacheType.TEXT_DETAIL) -> bool:
    try:
        cache_keys_to_invalidate = []
        
        primary_cache_payload = [text_id, cache_type]
        cache_keys_to_invalidate.append(Utils.generate_hash_key(payload=primary_cache_payload))
        
        texts_by_id_payload = [text_id, None, None, None, None, CacheType.TEXTS_BY_ID_OR_COLLECTION]
        cache_keys_to_invalidate.append(Utils.generate_hash_key(payload=texts_by_id_payload))
        
        toc_payload = [text_id, None, None, None, CacheType.TEXT_TABLE_OF_CONTENTS]
        cache_keys_to_invalidate.append(Utils.generate_hash_key(payload=toc_payload))
        
        versions_payload = [text_id, None, None, None, CacheType.TEXT_VERSIONS]
        cache_keys_to_invalidate.append(Utils.generate_hash_key(payload=versions_payload))
        
        # Invalidate specific cache keys
        await invalidate_multiple_cache_keys(hash_keys=cache_keys_to_invalidate)
        
        # Also do a broader invalidation to catch any cache entries we might have missed
        await invalidate_text_related_cache(text_id=text_id)
        
        return True
    except Exception as e:
        logging.error(f"Error invalidating cache for text_id {text_id}: {str(e)}", exc_info=True)
        return False