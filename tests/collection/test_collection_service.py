import pytest
from unittest.mock import patch, AsyncMock

from starlette import status

from pecha_api.collections.collections_service import (
    get_all_collections, 
    create_new_collection, 
    update_existing_collection, 
    delete_existing_collection, 
    get_collection,
    get_collection_by_pecha_collection_id_service
)
from pecha_api.collections.collections_response_models import CollectionModel, CollectionsResponse, CreateCollectionRequest, UpdateCollectionRequest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_get_all_collections():
    with patch("pecha_api.collections.collections_service.verify_admin_access", return_value=True), \
            patch("pecha_api.collections.collections_service.get_collections_cache", new_callable=AsyncMock, return_value=None), \
            patch("pecha_api.collections.collections_service.get_collections_by_parent",
                  new_callable=AsyncMock) as mock_get_collections_by_parent, \
            patch("pecha_api.collections.collections_service.get_child_count", new_callable=AsyncMock, return_value=2), \
            patch("pecha_api.collections.collections_service.set_collections_cache", new_callable=AsyncMock) as mock_set_collections_cache:
        mock_get_collections_by_parent.return_value = [
            AsyncMock(id="id_1", pecha_collection_id="pecha_id_1", titles={"en": "Collection 1"}, slug="collection-1",parent_id=None, has_sub_child=False),
            AsyncMock(id="id_2", pecha_collection_id="pecha_id_2", titles={"en": "Collection 2"}, descriptions={"en": "Description 2"}, slug="collection-2",parent_id=None,has_sub_child=False)
        ]
        response = await get_all_collections(language="en",parent_id=None,skip=0,limit=10)
        assert isinstance(response, CollectionsResponse)
        assert len(response.collections) == 2
        assert response.collections[0].title == "Collection 1"
        assert response.collections[1].has_child == False
        mock_set_collections_cache.assert_called_once()


@pytest.mark.asyncio
async def test_create_new_collection():
    with patch("pecha_api.collections.collections_service.verify_admin_access", return_value=True), \
            patch("pecha_api.collections.collections_service.create_collection", new_callable=AsyncMock) as mock_create_collection:
        mock_create_collection.return_value = AsyncMock(pecha_collection_id="pecha_new_id", titles={"en": "New Collection"}, descriptions={"en": "New Description"}, slug="new-collection",parent_id=None,has_sub_child=False)
        create_collection_request = CreateCollectionRequest(slug="new-collection", titles={"en": "New Collection"}, descriptions={"en": "New Description"},parent_id=None)
        response = await create_new_collection(
            create_collection_request=create_collection_request,
            token="valid_token",
            language="en"
        )
        assert isinstance(response, CollectionModel)
        assert response.title == "New Collection"
        assert response.slug == "new-collection"
        assert response.description == "New Description"
        assert response.has_child == False


@pytest.mark.asyncio
async def test_update_existing_collection():
    with patch("pecha_api.collections.collections_service.verify_admin_access", return_value=True), \
            patch("pecha_api.collections.collections_service.update_collection_titles",
                  new_callable=AsyncMock) as mock_update_collection_titles:
        mock_update_collection_titles.return_value = AsyncMock(pecha_collection_id="pecha_id_1", titles={"en": "Updated Collection"}, descriptions={"en": "Description 1"}, slug="updated-collection",parent_id=None)
        update_collection_request = UpdateCollectionRequest(titles={"en": "Updated Collection"}, descriptions={"en": "New Description"})
        response = await update_existing_collection(collection_id="1", update_collection_request=update_collection_request, token="valid_token",
                                              language="en")
        assert isinstance(response, CollectionModel)
        assert response.title == "Updated Collection"


@pytest.mark.asyncio
async def test_delete_existing_collection():
    with patch("pecha_api.collections.collections_service.verify_admin_access", return_value=True), \
            patch("pecha_api.collections.collections_service.delete_collection", new_callable=AsyncMock) as mock_delete_collection:
        mock_delete_collection.return_value = "id_1"
        response = await delete_existing_collection(collection_id="id_1", token="valid_token")
        assert response == "id_1"


@pytest.mark.asyncio
async def test_create_new_collection_unauthorized():
    with patch("pecha_api.collections.collections_service.verify_admin_access", return_value=False):
        create_collection_request = CreateCollectionRequest(slug="new-collection", titles={"en": "New Collection"},descriptions={"en": "New Description"},parent_id=None)
        try:
            await create_new_collection(create_collection_request=create_collection_request, token="invalid_token", language="en")
        except HTTPException as e:
            assert e.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@patch("pecha_api.collections.collections_service.verify_admin_access", return_value=False)
async def test_update_existing_collection_unauthorized(mock_verify_admin_access):
    update_collection_request = UpdateCollectionRequest(titles={"en": "Updated Collection"}, descriptions={"en": "Updated Descriptions"})
    try:
        await update_existing_collection(collection_id="1", update_collection_request=update_collection_request, token="invalid_token",
                                   language=None)
    except HTTPException as e:
        assert e.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@patch("pecha_api.collections.collections_service.verify_admin_access", return_value=False)
async def test_delete_existing_collection_unauthorized(mock_verify_admin_access):
    try:
        await delete_existing_collection(collection_id="1", token="invalid_token")
    except HTTPException as e:
        assert e.status_code == status.HTTP_403_FORBIDDEN


# New test cases for uncovered scenarios

@pytest.mark.asyncio
async def test_get_collection_with_none_id():
    """Test get_collection when collection_id is None - should return None"""
    response = await get_collection(collection_id=None, language="en")
    assert response is None


@pytest.mark.asyncio
async def test_get_collection_cache_hit():
    """Test get_collection when data is found in cache"""
    cached_collection = CollectionModel(
        id="cached_id",
        pecha_collection_id="pecha_cached_id",
        title="Cached Collection",
        description="Cached Description", 
        language="en",
        slug="cached-collection",
        has_child=False
    )
    
    with patch("pecha_api.collections.collections_service.get_collection_detail_cache", new_callable=AsyncMock) as mock_cache_get:
        mock_cache_get.return_value = cached_collection
        
        response = await get_collection(collection_id="cached_id", language="en")
        
        assert response == cached_collection
        mock_cache_get.assert_called_once()


@pytest.mark.asyncio
async def test_get_collection_cache_miss_collection_found():
    """Test get_collection when cache miss but collection found in database"""
    mock_db_collection = AsyncMock(
        pecha_collection_id="pecha_db_id",
        titles={"en": "DB Collection", "es": "Colección DB"},
        descriptions={"en": "DB Description", "es": "Descripción DB"},
        slug="db-collection",
        has_sub_child=True
    )
    
    with patch("pecha_api.collections.collections_service.get_collection_detail_cache", new_callable=AsyncMock, return_value=None) as mock_cache_get, \
         patch("pecha_api.collections.collections_service.get_collection_by_id", new_callable=AsyncMock) as mock_db_get, \
         patch("pecha_api.collections.collections_service.set_collection_detail_cache", new_callable=AsyncMock) as mock_cache_set, \
         patch("pecha_api.collections.collections_service.Utils.get_value_from_dict", side_effect=["DB Collection", "DB Description"]):
        
        mock_db_get.return_value = mock_db_collection
        
        response = await get_collection(collection_id="db_id", language="en")
        
        assert isinstance(response, CollectionModel)
        assert response.id == "db_id" 
        assert response.title == "DB Collection"
        assert response.description == "DB Description"
        assert response.slug == "db-collection"
        assert response.has_child == True
        assert response.language == "en"
        
        mock_cache_get.assert_called_once()
        mock_db_get.assert_called_once_with(collection_id="db_id")
        mock_cache_set.assert_called_once()


@pytest.mark.asyncio
async def test_get_collection_cache_miss_collection_not_found():
    """Test get_collection when cache miss and collection not found in database"""
    with patch("pecha_api.collections.collections_service.get_collection_detail_cache", new_callable=AsyncMock, return_value=None), \
         patch("pecha_api.collections.collections_service.get_collection_by_id", new_callable=AsyncMock, return_value=None):
        
        response = await get_collection(collection_id="nonexistent_id", language="en")
        
        assert response is None


@pytest.mark.asyncio
async def test_get_all_collections_cache_hit():
    """Test get_all_collections when data is found in cache"""
    cached_response = CollectionsResponse(
        parent=None,
        pagination={"total": 1, "skip": 0, "limit": 10},
        collections=[
            CollectionModel(
                id="cached_id",
                pecha_collection_id="pecha_cached_id",
                title="Cached Collection",
                description="Cached Description",
                language="en", 
                slug="cached-collection",
                has_child=False
            )
        ]
    )
    
    with patch("pecha_api.collections.collections_service.get_collections_cache", new_callable=AsyncMock) as mock_cache_get:
        mock_cache_get.return_value = cached_response
        
        response = await get_all_collections(language="en", parent_id=None, skip=0, limit=10)
        
        assert response == cached_response
        mock_cache_get.assert_called_once()


@pytest.mark.asyncio 
async def test_get_all_collections_with_default_language():
    """Test get_all_collections when language is None - should use default language"""
    with patch("pecha_api.collections.collections_service.get_collections_cache", new_callable=AsyncMock, return_value=None), \
         patch("pecha_api.collections.collections_service.get_child_count", new_callable=AsyncMock, return_value=1), \
         patch("pecha_api.collections.collections_service.get_collection", new_callable=AsyncMock, return_value=None), \
         patch("pecha_api.collections.collections_service.get_collections_by_parent", new_callable=AsyncMock) as mock_get_collections, \
         patch("pecha_api.collections.collections_service.set_collections_cache", new_callable=AsyncMock), \
         patch("pecha_api.collections.collections_service.get", return_value="en") as mock_get_config:
        
        mock_get_collections.return_value = [
            AsyncMock(id="test_id", pecha_collection_id="pecha_test_id", titles={"en": "Test"}, descriptions={"en": "Test Desc"}, slug="test", has_sub_child=False)
        ]
        
        response = await get_all_collections(language=None, parent_id=None, skip=0, limit=10)
        
        mock_get_config.assert_called_with("DEFAULT_LANGUAGE")
        assert isinstance(response, CollectionsResponse)


@pytest.mark.asyncio
async def test_create_new_collection_with_default_language():
    """Test create_new_collection when language is None - should use default language"""
    with patch("pecha_api.collections.collections_service.verify_admin_access", return_value=True), \
         patch("pecha_api.collections.collections_service.create_collection", new_callable=AsyncMock) as mock_create, \
         patch("pecha_api.collections.collections_service.get", return_value="en") as mock_get_config, \
         patch("pecha_api.collections.collections_service.Utils.get_value_from_dict", side_effect=["New Collection", "New Description"]):
        
        mock_create.return_value = AsyncMock(
            id="new_id",
            pecha_collection_id="pecha_new_id",
            titles={"en": "New Collection"},
            descriptions={"en": "New Description"},
            slug="new-collection", 
            has_sub_child=False
        )
        
        create_request = CreateCollectionRequest(
            slug="new-collection",
            titles={"en": "New Collection"},
            descriptions={"en": "New Description"},
            parent_id=None
        )
        
        response = await create_new_collection(
            create_collection_request=create_request,
            token="valid_token", 
            language=None
        )
        
        mock_get_config.assert_called_with("DEFAULT_LANGUAGE")
        assert isinstance(response, CollectionModel)
        assert response.language == "en"


@pytest.mark.asyncio
async def test_update_existing_collection_with_default_language():
    """Test update_existing_collection when language is None - should use default language"""
    with patch("pecha_api.collections.collections_service.verify_admin_access", return_value=True), \
         patch("pecha_api.collections.collections_service.update_collection_titles", new_callable=AsyncMock) as mock_update, \
         patch("pecha_api.collections.collections_service.get", return_value="en") as mock_get_config, \
         patch("pecha_api.collections.collections_service.Utils.get_value_from_dict", side_effect=["Updated Collection", "Updated Description"]):
        
        mock_update.return_value = AsyncMock(
            pecha_collection_id="pecha_test_id",
            titles={"en": "Updated Collection"},
            descriptions={"en": "Updated Description"}, 
            slug="updated-collection",
            has_sub_child=True
        )
        
        update_request = UpdateCollectionRequest(
            titles={"en": "Updated Collection"},
            descriptions={"en": "Updated Description"}
        )
        
        response = await update_existing_collection(
            collection_id="test_id",
            update_collection_request=update_request,
            token="valid_token",
            language=None
        )
        
        mock_get_config.assert_called_with("DEFAULT_LANGUAGE") 
        assert isinstance(response, CollectionModel)
        assert response.language == "en"


@pytest.mark.asyncio
async def test_get_all_collections_cache_miss_with_parent():
    """Test get_all_collections cache miss scenario with parent_id provided"""
    parent_collection = CollectionModel(
        id="parent_id",
        pecha_collection_id="pecha_parent_id",
        title="Parent Collection",
        description="Parent Description",
        language="en",
        slug="parent-collection", 
        has_child=True
    )
    
    with patch("pecha_api.collections.collections_service.get_collections_cache", new_callable=AsyncMock, return_value=None), \
         patch("pecha_api.collections.collections_service.get_child_count", new_callable=AsyncMock, return_value=2), \
         patch("pecha_api.collections.collections_service.get_collection", new_callable=AsyncMock, return_value=parent_collection), \
         patch("pecha_api.collections.collections_service.get_collections_by_parent", new_callable=AsyncMock) as mock_get_collections, \
         patch("pecha_api.collections.collections_service.set_collections_cache", new_callable=AsyncMock) as mock_cache_set, \
         patch("pecha_api.collections.collections_service.Utils.get_value_from_dict", side_effect=["Child 1", "Child 1 Desc", "Child 2", "Child 2 Desc"]):
        
        mock_get_collections.return_value = [
            AsyncMock(id="child1", pecha_collection_id="pecha_child1", titles={"en": "Child 1"}, descriptions={"en": "Child 1 Desc"}, slug="child-1", has_sub_child=False),
            AsyncMock(id="child2", pecha_collection_id="pecha_child2", titles={"en": "Child 2"}, descriptions={"en": "Child 2 Desc"}, slug="child-2", has_sub_child=False)
        ]
        
        response = await get_all_collections(language="en", parent_id="parent_id", skip=0, limit=10)
        
        assert isinstance(response, CollectionsResponse)
        assert response.parent == parent_collection
        assert len(response.collections) == 2
        assert response.pagination.total == 2
        mock_cache_set.assert_called_once()


@pytest.mark.asyncio
async def test_get_collection_by_pecha_collection_id_service_found():
    """Test get_collection_by_pecha_collection_id_service when collection is found"""
    with patch("pecha_api.collections.collections_service.get_collection_id_by_pecha_collection_id", 
               new_callable=AsyncMock, return_value="collection_id_123"):
        
        result = await get_collection_by_pecha_collection_id_service(pecha_collection_id="pecha_123")
        
        assert result == "collection_id_123"


@pytest.mark.asyncio
async def test_get_collection_by_pecha_collection_id_service_not_found():
    """Test get_collection_by_pecha_collection_id_service when collection is not found"""
    with patch("pecha_api.collections.collections_service.get_collection_id_by_pecha_collection_id",
               new_callable=AsyncMock, return_value=None):
        
        result = await get_collection_by_pecha_collection_id_service(pecha_collection_id="nonexistent_pecha_id")
        
        assert result is None
