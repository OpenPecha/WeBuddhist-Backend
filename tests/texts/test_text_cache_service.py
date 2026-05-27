import pytest
from unittest.mock import patch, Mock, AsyncMock

from pecha_api.texts.texts_cache_service import (
    update_text_details_cache,
    invalidate_text_cache_on_update,
    get_table_of_content_by_sheet_id_cache,
    set_table_of_content_by_sheet_id_cache,
    delete_table_of_content_by_sheet_id_cache,
    set_text_details_by_id_cache,
    get_text_details_by_id_cache,
    delete_text_details_by_id_cache
)
from pecha_api.texts.texts_response_models import (
    TextDTO,
    TableOfContent,
    TableOfContentType,
)

from pecha_api.cache.cache_enums import CacheType

@pytest.mark.asyncio
async def test_update_text_details_cache_success():
    #Test successful update of text details cache
    updated_text_data = TextDTO(
        id="text_id_1",
        title="Updated Title",
        language="en",
        group_id="group_id_1",
        type="root_text",
        is_published=True,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 05:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="user_1",
        categories=["category_1"],
        views=10
    )

    with patch("pecha_api.texts.texts_cache_service.update_cache", new_callable=AsyncMock, return_value=True) as mock_update_cache, \
         patch("pecha_api.texts.texts_cache_service.Utils.generate_hash_key", return_value="test_hash_key"):
        
        result = await update_text_details_cache(text_id="text_id_1", updated_text_data=updated_text_data)
        
        assert result is True
        assert mock_update_cache.call_count == 2  # Called for both cache types

@pytest.mark.asyncio
async def test_update_text_details_cache_partial_success():
    #Test partial success scenario where only one cache type updates successfully
    updated_text_data = TextDTO(
        id="text_id_1",
        title="Updated Title",
        language="en",
        group_id="group_id_1",
        type="root_text",
        is_published=True,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 05:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="user_1",
        categories=["category_1"],
        views=10
    )

    with patch("pecha_api.texts.texts_cache_service.update_cache", new_callable=AsyncMock, side_effect=[True, False]) as mock_update_cache, \
         patch("pecha_api.texts.texts_cache_service.Utils.generate_hash_key", return_value="test_hash_key"):
        
        result = await update_text_details_cache(text_id="text_id_1", updated_text_data=updated_text_data)
        
        assert result is True
        assert mock_update_cache.call_count == 2

@pytest.mark.asyncio
async def test_update_text_details_cache_all_updates_fail():
    #Test scenario where all cache updates fail and fallback to invalidation
    updated_text_data = TextDTO(
        id="text_id_1",
        title="Updated Title",
        language="en",
        group_id="group_id_1",
        type="root_text",
        is_published=True,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 05:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="user_1",
        categories=["category_1"],
        views=10
    )

    with patch("pecha_api.texts.texts_cache_service.update_cache", new_callable=AsyncMock, return_value=False) as mock_update_cache, \
         patch("pecha_api.texts.texts_cache_service.invalidate_text_related_cache", new_callable=AsyncMock) as mock_invalidate, \
         patch("pecha_api.texts.texts_cache_service.Utils.generate_hash_key", return_value="test_hash_key"):
        
        result = await update_text_details_cache(text_id="text_id_1", updated_text_data=updated_text_data)
        
        assert result is True
        assert mock_update_cache.call_count == 2
        mock_invalidate.assert_called_once_with(text_id="text_id_1")

@pytest.mark.asyncio
async def test_update_text_details_cache_exception_handling():
    #Test exception handling in update_text_details_cache
    updated_text_data = TextDTO(
        id="text_id_1",
        title="Updated Title",
        language="en",
        group_id="group_id_1",
        type="root_text",
        is_published=True,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 05:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="user_1",
        categories=["category_1"],
        views=10
    )

    with patch("pecha_api.texts.texts_cache_service.update_cache", new_callable=AsyncMock, side_effect=Exception("Cache error")) as mock_update_cache, \
         patch("pecha_api.texts.texts_cache_service.invalidate_multiple_cache_keys", new_callable=AsyncMock) as mock_invalidate_multiple, \
         patch("pecha_api.texts.texts_cache_service.invalidate_text_related_cache", new_callable=AsyncMock) as mock_invalidate, \
         patch("pecha_api.texts.texts_cache_service.Utils.generate_hash_key", return_value="test_hash_key"), \
         patch("pecha_api.texts.texts_cache_service.logging.error") as mock_log:
        
        result = await update_text_details_cache(text_id="text_id_1", updated_text_data=updated_text_data)
        
        assert result is False
        mock_invalidate.assert_called_once_with(text_id="text_id_1")
        # Only one error call from update_text_details_cache since invalidate_text_cache_on_update succeeds
        mock_log.assert_called_once()

@pytest.mark.asyncio
async def test_invalidate_text_cache_on_update_success():
    #Test successful invalidation of all text-related cache entries
    with patch("pecha_api.texts.texts_cache_service.invalidate_multiple_cache_keys", new_callable=AsyncMock) as mock_invalidate_multiple, \
         patch("pecha_api.texts.texts_cache_service.invalidate_text_related_cache", new_callable=AsyncMock) as mock_invalidate_text, \
         patch("pecha_api.texts.texts_cache_service.Utils.generate_hash_key", return_value="test_hash_key"):
        
        result = await invalidate_text_cache_on_update(text_id="text_id_1")
        
        assert result is True
        mock_invalidate_multiple.assert_called_once()
        mock_invalidate_text.assert_called_once_with(text_id="text_id_1")
        
        # Verify that hash keys are generated for all cache types
        args, kwargs = mock_invalidate_multiple.call_args
        assert "hash_keys" in kwargs
        assert len(kwargs["hash_keys"]) == 4  # Four different cache types

@pytest.mark.asyncio
async def test_invalidate_text_cache_on_update_exception_handling():
    #Test exception handling in invalidate_text_cache_on_update
    with patch("pecha_api.texts.texts_cache_service.invalidate_multiple_cache_keys", new_callable=AsyncMock, side_effect=Exception("Invalidation error")) as mock_invalidate_multiple, \
         patch("pecha_api.texts.texts_cache_service.Utils.generate_hash_key", return_value="test_hash_key"), \
         patch("pecha_api.texts.texts_cache_service.logging.error") as mock_log:
        
        result = await invalidate_text_cache_on_update(text_id="text_id_1")
        
        assert result is False
        mock_log.assert_called_once()

@pytest.mark.asyncio
async def test_invalidate_text_cache_on_update_hash_key_generation():
    #Test that correct hash keys are generated for different cache types
    def mock_generate_hash_key(payload):
        # Find the CacheType in the payload (it's at different indices)
        cache_type = None
        for item in payload:
            if hasattr(item, 'value'):  # CacheType enum has .value attribute
                cache_type = item
                break
        if cache_type:
            return f"hash_{cache_type.value}"
        return "hash_unknown"
    
    with patch("pecha_api.texts.texts_cache_service.invalidate_multiple_cache_keys", new_callable=AsyncMock) as mock_invalidate_multiple, \
         patch("pecha_api.texts.texts_cache_service.invalidate_text_related_cache", new_callable=AsyncMock), \
         patch("pecha_api.texts.texts_cache_service.Utils.generate_hash_key", side_effect=mock_generate_hash_key) as mock_hash:
        
        result = await invalidate_text_cache_on_update(text_id="text_id_1")
        
        assert result is True
        
        # Verify hash key generation calls
        assert mock_hash.call_count == 4
        
        # Verify the correct cache types are used
        args, kwargs = mock_invalidate_multiple.call_args
        expected_hash_keys = [
            "hash_text_detail",
            "hash_texts_by_id_or_collection", 
            "hash_text_table_of_contents",
            "hash_text_versions"
        ]
        assert kwargs["hash_keys"] == expected_hash_keys

@pytest.mark.asyncio
async def test_get_table_of_content_by_sheet_id_cache_empty_cache():
    #Test get_table_of_content_by_sheet_id_cache with empty cache#
    with patch("pecha_api.texts.texts_cache_service.get_cache_data", new_callable=AsyncMock, return_value=None):
        response = await get_table_of_content_by_sheet_id_cache(sheet_id="sheet_id", cache_type=CacheType.SHEET_TABLE_OF_CONTENT)
        
        assert response is None

@pytest.mark.asyncio
async def test_get_table_of_content_by_sheet_id_cache_with_data():
    #Test get_table_of_content_by_sheet_id_cache with cached data#
    mock_cache_data = TableOfContent(
        id="table_of_content_id",
        text_id="text_id_1",
        type=TableOfContentType.SHEET,
        sections=[]
    )
    
    with patch("pecha_api.texts.texts_cache_service.get_cache_data", new_callable=AsyncMock, return_value=mock_cache_data):
        response = await get_table_of_content_by_sheet_id_cache(sheet_id="sheet_id", cache_type=CacheType.SHEET_TABLE_OF_CONTENT)
        
        assert response is not None
        assert isinstance(response, TableOfContent)
        assert response.id == "table_of_content_id"

@pytest.mark.asyncio
async def test_get_table_of_content_by_sheet_id_cache_with_dict_response():
    #Test get_table_of_content_by_sheet_id_cache when cache returns dict and needs conversion#
    mock_cache_dict = {
        "id": "table_of_content_id",
        "text_id": "text_id_1",
        "type": "sheet",
        "sections": []
    }
    
    with patch("pecha_api.texts.texts_cache_service.get_cache_data", new_callable=AsyncMock, return_value=mock_cache_dict):
        response = await get_table_of_content_by_sheet_id_cache(sheet_id="sheet_id", cache_type=CacheType.SHEET_TABLE_OF_CONTENT)
        
        assert response is not None
        assert isinstance(response, TableOfContent)
        assert response.id == "table_of_content_id"

@pytest.mark.asyncio
async def test_set_table_of_content_by_sheet_id_cache_success():
    #Test set_table_of_content_by_sheet_id_cache success#
    mock_cache_data = TableOfContent(
        id="table_of_content_id",
        text_id="text_id_1",
        type=TableOfContentType.SHEET,
        sections=[]
    )
    
    with patch("pecha_api.texts.texts_cache_service.set_cache", new_callable=AsyncMock):
        await set_table_of_content_by_sheet_id_cache(sheet_id="sheet_id", cache_type=CacheType.SHEET_TABLE_OF_CONTENT, data=mock_cache_data)

@pytest.mark.asyncio
async def test_delete_table_of_content_by_sheet_id_cache_success():
    #Test delete_table_of_content_by_sheet_id_cache success#
    with patch("pecha_api.texts.texts_cache_service.clear_cache", new_callable=AsyncMock):
        await delete_table_of_content_by_sheet_id_cache(sheet_id="sheet_id", cache_type=CacheType.SHEET_TABLE_OF_CONTENT)

@pytest.mark.asyncio
async def test_set_text_details_by_id_cache_success():
    #Test set_text_details_by_id_cache success#
    mock_text_data = TextDTO(
        id="id_1",
        title="title_1",
        language="en",
        group_id="group_id_1",
        type="type_1",
        is_published=True,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 04:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="published_by_1",
        categories=[],
        views=0
    )
    
    with patch("pecha_api.texts.texts_cache_service.set_cache", new_callable=AsyncMock):
        await set_text_details_by_id_cache(text_id="text_id", cache_type=CacheType.TEXT_DETAIL, data=mock_text_data)

@pytest.mark.asyncio
async def test_get_text_details_by_id_cache_empty_cache():
    #Test get_text_details_by_id_cache with empty cache#
    with patch("pecha_api.texts.texts_cache_service.get_cache_data", new_callable=AsyncMock, return_value=None):
        response = await get_text_details_by_id_cache(text_id="text_id", cache_type=CacheType.TEXT_DETAIL)
        
        assert response is None

@pytest.mark.asyncio
async def test_get_text_details_by_id_cache_with_data():
    #Test get_text_details_by_id_cache with cached data#
    mock_text_data = TextDTO(
        id="id_1",
        title="title_1",
        language="en",
        group_id="group_id_1", 
        type="type_1",
        is_published=True,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 04:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="published_by_1",
        categories=[],
        views=0
    )
    
    with patch("pecha_api.texts.texts_cache_service.get_cache_data", new_callable=AsyncMock, return_value=mock_text_data):
        response = await get_text_details_by_id_cache(text_id="text_id", cache_type=CacheType.TEXT_DETAIL)
        
        assert response is not None
        assert isinstance(response, TextDTO)
        assert response.id == "id_1"

@pytest.mark.asyncio
async def test_get_text_details_by_id_cache_with_dict_response():
    #Test get_text_details_by_id_cache when cache returns dict and needs conversion#
    mock_cache_dict = {
        "id": "id_1",
        "title": "title_1",
        "language": "en",
        "group_id": "group_id_1",
        "type": "type_1", 
        "is_published": True,
        "created_date": "2025-03-16 04:40:54.757652",
        "updated_date": "2025-03-16 04:40:54.757652",
        "published_date": "2025-03-16 04:40:54.757652",
        "published_by": "published_by_1",
        "categories": [],
        "views": 0
    }
    
    with patch("pecha_api.texts.texts_cache_service.get_cache_data", new_callable=AsyncMock, return_value=mock_cache_dict):
        response = await get_text_details_by_id_cache(text_id="text_id", cache_type=CacheType.TEXT_DETAIL)
        
        assert response is not None
        assert isinstance(response, TextDTO)
        assert response.id == "id_1"

@pytest.mark.asyncio
async def test_delete_text_details_by_id_cache_success():
    #Test delete_text_details_by_id_cache success#
    with patch("pecha_api.texts.texts_cache_service.clear_cache", new_callable=AsyncMock):
        await delete_text_details_by_id_cache(text_id="text_id", cache_type=CacheType.TEXT_DETAIL)

@pytest.mark.asyncio
async def test_update_text_details_cache_for_sheet_success():
    #Test update_text_details_cache for sheet with successful table of content update#
    updated_text_data = TextDTO(
        id="sheet_id_1",
        title="Updated Sheet Title",
        language="en",
        group_id="group_id_1",
        type="sheet",
        is_published=True,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 05:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="user_1",
        categories=["category_1"],
        views=10
    )
    
    mock_table_of_content = TableOfContent(
        id="toc_id",
        text_id="sheet_id_1",
        type=TableOfContentType.SHEET,
        sections=[]
    )
    
    with patch("pecha_api.texts.texts_cache_service.update_cache", new_callable=AsyncMock, return_value=True) as mock_update_cache, \
         patch("pecha_api.texts.texts_cache_service.Utils.generate_hash_key", return_value="test_hash_key"), \
         patch("pecha_api.texts.texts_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=mock_table_of_content):
        
        result = await update_text_details_cache(text_id="sheet_id_1", updated_text_data=updated_text_data, cache_type=CacheType.SHEET_DETAIL)
        
        assert result is True
        assert mock_update_cache.call_count == 3  # Called for primary cache, texts_by_id cache, and table of content cache

@pytest.mark.asyncio
async def test_update_text_details_cache_for_sheet_with_toc_exception():
    #Test update_text_details_cache for sheet when table of content update raises exception#
    updated_text_data = TextDTO(
        id="sheet_id_1",
        title="Updated Sheet Title",
        language="en",
        group_id="group_id_1",
        type="sheet",
        is_published=True,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 05:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="user_1",
        categories=["category_1"],
        views=10
    )
    
    with patch("pecha_api.texts.texts_cache_service.update_cache", new_callable=AsyncMock, return_value=True) as mock_update_cache, \
         patch("pecha_api.texts.texts_cache_service.Utils.generate_hash_key", return_value="test_hash_key"), \
         patch("pecha_api.texts.texts_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, side_effect=Exception("TOC error")), \
         patch("pecha_api.texts.texts_cache_service.logging.warning") as mock_log_warning:
        
        result = await update_text_details_cache(text_id="sheet_id_1", updated_text_data=updated_text_data, cache_type=CacheType.SHEET_DETAIL)
        
        assert result is True
        assert mock_update_cache.call_count == 2  # Called for primary cache and texts_by_id cache only
        mock_log_warning.assert_called_once()

@pytest.mark.asyncio
async def test_update_text_details_cache_for_sheet_with_none_toc():
    #Test update_text_details_cache for sheet when table of content returns None#
    updated_text_data = TextDTO(
        id="sheet_id_1",
        title="Updated Sheet Title",
        language="en",
        group_id="group_id_1",
        type="sheet",
        is_published=True,
        created_date="2025-03-16 04:40:54.757652",
        updated_date="2025-03-16 05:40:54.757652",
        published_date="2025-03-16 04:40:54.757652",
        published_by="user_1",
        categories=["category_1"],
        views=10
    )
    
    with patch("pecha_api.texts.texts_cache_service.update_cache", new_callable=AsyncMock, return_value=True) as mock_update_cache, \
         patch("pecha_api.texts.texts_cache_service.Utils.generate_hash_key", return_value="test_hash_key"), \
         patch("pecha_api.texts.texts_service.get_table_of_content_by_sheet_id", new_callable=AsyncMock, return_value=None):
        
        result = await update_text_details_cache(text_id="sheet_id_1", updated_text_data=updated_text_data, cache_type=CacheType.SHEET_DETAIL)
        
        assert result is True
        assert mock_update_cache.call_count == 2  # Called for primary cache and texts_by_id cache only

@pytest.mark.asyncio
async def test_invalidate_text_cache_on_update_for_sheet():
    #Test invalidate_text_cache_on_update for sheet with sheet-specific cache types#
    with patch("pecha_api.texts.texts_cache_service.invalidate_multiple_cache_keys", new_callable=AsyncMock) as mock_invalidate_multiple, \
         patch("pecha_api.texts.texts_cache_service.invalidate_text_related_cache", new_callable=AsyncMock) as mock_invalidate_text, \
         patch("pecha_api.texts.texts_cache_service.Utils.generate_hash_key", return_value="test_hash_key"):
        
        result = await invalidate_text_cache_on_update(text_id="sheet_id_1", cache_type=CacheType.SHEET_DETAIL)
        
        assert result is True
        mock_invalidate_multiple.assert_called_once()
        mock_invalidate_text.assert_called_once_with(text_id="sheet_id_1")
        
        # Verify that hash keys are generated for sheet-specific cache types
        args, kwargs = mock_invalidate_multiple.call_args
        assert "hash_keys" in kwargs
        assert len(kwargs["hash_keys"]) == 4  # Four different cache types for sheets
