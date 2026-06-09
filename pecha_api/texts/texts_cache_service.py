
from pecha_api.utils import Utils

from pecha_api.cache.cache_repository import (
    get_cache_data,
    set_cache,
    clear_cache,
    update_cache,
    invalidate_text_related_cache,
    invalidate_multiple_cache_keys,
)
from .texts_response_models import (
    DetailTableOfContentResponse,
    TextsCategoryResponse,
    TableOfContentResponse,
    TextVersionResponse,
    TextDTO,
    TableOfContent
)
from pecha_api.cache.cache_enums import CacheType

from typing import Optional
import logging
from pecha_api import config

async def set_text_details_cache(text_id: str = None, content_id: str = None, version_id: str = None, skip: int = None, limit: int = None, data: DetailTableOfContentResponse = None, cache_type: CacheType = None):
    #Set text details cache asynchronously.
    payload = [text_id, content_id, version_id, skip, limit, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_time_out = config.get_int("CACHE_TEXT_TIMEOUT")
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=cache_time_out)

async def get_text_details_cache(text_id: str = None, content_id: str = None, version_id: str = None, skip: int = None, limit: int = None, cache_type: CacheType = None) -> DetailTableOfContentResponse:
    #Get text details cache asynchronously.
    payload = [text_id, content_id, version_id, skip, limit, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_data: DetailTableOfContentResponse = await get_cache_data(hash_key =hashed_key)
    if cache_data and isinstance(cache_data, dict):
        cache_data = DetailTableOfContentResponse(**cache_data)
    return cache_data


async def get_text_by_text_id_or_collection_cache(text_id: str = None, collection_id: str = None, language: str = None, skip: int = None, limit: int = None, cache_type: CacheType = None) -> TextsCategoryResponse | TextDTO:
    """Get text by text id or collection cache asynchronously."""
    payload = [text_id, collection_id, language, skip, limit, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_data: TextsCategoryResponse | TextDTO = await get_cache_data(hash_key = hashed_key)
    if cache_data and isinstance(cache_data, dict):
        cache_data = TextsCategoryResponse(**cache_data)
    return cache_data


async def set_text_by_text_id_or_collection_cache(text_id: str = None, collection_id: str = None, language: str = None, skip: int = None, limit: int = None, cache_type: CacheType = None, data: TextsCategoryResponse = None):
    """Set text by text_id or collection cache asynchronously."""
    payload = [text_id, collection_id, language, skip, limit, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_time_out = config.get_int("CACHE_TEXT_TIMEOUT")
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=cache_time_out)

async def get_table_of_contents_by_text_id_cache(text_id: str = None, language: str = None, skip: int = None, limit: int = None, cache_type: CacheType = None) -> TableOfContentResponse:
    """Get table of contents by text id cache asynchronously."""
    payload = [text_id, language, skip, limit, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_data: TableOfContentResponse = await get_cache_data(hash_key = hashed_key)
    if cache_data and isinstance(cache_data, dict):
        cache_data = TableOfContentResponse(**cache_data)
    return cache_data

async def set_table_of_contents_by_text_id_cache(text_id: str = None, language: str = None, skip: int = None, limit: int = None, data: TableOfContentResponse = None, cache_type: CacheType = None):
    """Set table of contents by text_id cache asynchronously."""
    payload = [text_id, language, skip, limit, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_time_out = config.get_int("CACHE_TEXT_TIMEOUT")
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=cache_time_out)

async def get_table_of_content_by_sheet_id_cache(sheet_id: str = None, cache_type: CacheType = None) -> Optional[TableOfContent]:
    payload = [sheet_id, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_data: TableOfContent = await get_cache_data(hash_key = hashed_key)
    if cache_data and isinstance(cache_data, dict):
        cache_data = TableOfContent(**cache_data)
    return cache_data

async def set_table_of_content_by_sheet_id_cache(sheet_id: str = None, cache_type: CacheType = None, data: TableOfContent = None):
    #Set table of content by sheet id cache asynchronously.
    payload = [sheet_id, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_time_out = config.get_int("CACHE_SHEET_TIMEOUT")
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=cache_time_out)
    
async def delete_table_of_content_by_sheet_id_cache(sheet_id: str = None, cache_type: CacheType = None):
    payload = [sheet_id, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    await clear_cache(hash_key = hashed_key)

async def get_text_versions_by_group_id_cache(text_id: str = None, language: str = None, skip: int = None, limit: int = None, cache_type: CacheType = None) -> TextVersionResponse:
    #Get text versions by group_id cache asynchronously.
    payload = [text_id, language, skip, limit, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_data: TextVersionResponse = await get_cache_data(hash_key = hashed_key)
    if cache_data and isinstance(cache_data, dict):
        cache_data = TextVersionResponse(**cache_data)
    return cache_data

async def set_text_versions_by_group_id_cache(text_id: str = None, language: str = None, skip: int = None, limit: int = None, data: TextVersionResponse = None, cache_type: CacheType = None):
    #Set text versions by group_id cache asynchronously.
    payload = [text_id, language, skip, limit, cache_type]
    hashed_key: str = Utils.generate_hash_key(payload = payload)
    cache_time_out = config.get_int("CACHE_TEXT_TIMEOUT")
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=cache_time_out)

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
    #Update cached text details for a specific text_id with new data. Handles both text and sheet instances.
    try:
        # Determine cache types based on whether this is a text or sheet
        is_sheet = cache_type == CacheType.SHEET_DETAIL
        
        # Update primary cache (TEXT_DETAIL for texts, SHEET_DETAIL for sheets)
        primary_cache_payload = [text_id, cache_type]
        primary_cache_hash_key = Utils.generate_hash_key(payload=primary_cache_payload)
        
        # Update TEXTS_BY_ID_OR_COLLECTION cache (used for both texts and sheets)
        texts_by_id_payload = [text_id, None, None, None, None, CacheType.TEXTS_BY_ID_OR_COLLECTION]
        texts_by_id_hash_key = Utils.generate_hash_key(payload=texts_by_id_payload)
        
        # Try to update existing cache entries
        update_results = []
        
        # Update primary cache (text detail or sheet detail)
        cache_time_out = config.get_int("CACHE_TEXT_TIMEOUT")
        is_primary_cache_updated = await update_cache(hash_key=primary_cache_hash_key, value=updated_text_data, cache_time_out=cache_time_out)
        update_results.append(is_primary_cache_updated)
        
        # Update texts by id cache
        is_texts_by_id_updated = await update_cache(hash_key=texts_by_id_hash_key, value=updated_text_data, cache_time_out=cache_time_out)
        update_results.append(is_texts_by_id_updated)
        
        # For sheets, also try to update table of content cache
        if is_sheet:
            try:
                from .texts_service import get_table_of_content_by_sheet_id
                updated_table_of_content = await get_table_of_content_by_sheet_id(sheet_id=text_id)
                if updated_table_of_content:
                    toc_payload = [text_id, CacheType.SHEET_TABLE_OF_CONTENT]
                    toc_hash_key = Utils.generate_hash_key(payload=toc_payload)
                    is_toc_updated = await update_cache(hash_key=toc_hash_key, value=updated_table_of_content, cache_time_out=cache_time_out)
                    update_results.append(is_toc_updated)
            except Exception as e:
                logging.warning(f"Could not update table of content cache for sheet {text_id}: {str(e)}")
        
        # If direct updates failed, fallback to invalidation to ensure cache consistency
        if not any(update_results):
            await invalidate_text_cache_on_update(text_id=text_id, cache_type=cache_type)
            
        return True
    except Exception as e:
        logging.error(f"Error updating text details cache for text_id {text_id}: {str(e)}", exc_info=True)
        # Fallback to cache invalidation to maintain consistency
        await invalidate_text_cache_on_update(text_id=text_id, cache_type=cache_type)
        return False


async def invalidate_text_cache_on_update(text_id: str, cache_type: CacheType = CacheType.TEXT_DETAIL) -> bool:
    #Invalidate all cache entries related to a text when it's updated. Handles both text and sheet instances.
    try:
        # Generate hash keys for all possible cache entries related to this text/sheet
        cache_keys_to_invalidate = []
        
        # Determine if this is a sheet
        is_sheet = cache_type == CacheType.SHEET_DETAIL
        
        # Primary cache (TEXT_DETAIL for texts, SHEET_DETAIL for sheets)
        primary_cache_payload = [text_id, cache_type]
        cache_keys_to_invalidate.append(Utils.generate_hash_key(payload=primary_cache_payload))
        
        # TEXTS_BY_ID_OR_COLLECTION cache (used for both texts and sheets)
        texts_by_id_payload = [text_id, None, None, None, None, CacheType.TEXTS_BY_ID_OR_COLLECTION]
        cache_keys_to_invalidate.append(Utils.generate_hash_key(payload=texts_by_id_payload))
        
        if is_sheet:
            # Sheet-specific cache entries
            
            # SHEET_TABLE_OF_CONTENT cache
            sheet_toc_payload = [text_id, CacheType.SHEET_TABLE_OF_CONTENT]
            cache_keys_to_invalidate.append(Utils.generate_hash_key(payload=sheet_toc_payload))
            
            # SHEETS cache (general sheets listing)
            sheets_payload = [None, None, None, None, None, None, CacheType.SHEETS]
            cache_keys_to_invalidate.append(Utils.generate_hash_key(payload=sheets_payload))
        else:
            # Text-specific cache entries
            
            # TEXT_TABLE_OF_CONTENTS cache
            toc_payload = [text_id, None, None, None, CacheType.TEXT_TABLE_OF_CONTENTS]
            cache_keys_to_invalidate.append(Utils.generate_hash_key(payload=toc_payload))
            
            # TEXT_VERSIONS cache
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