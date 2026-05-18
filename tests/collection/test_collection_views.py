import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
from starlette import status
from httpx import AsyncClient, ASGITransport

from pecha_api.app import api
from pecha_api.collections.collections_response_models import (
    CollectionModel,
    CollectionsResponse,
    CreateCollectionRequest,
    UpdateCollectionRequest,
    Pagination
)

client = TestClient(api)

# Test constants
VALID_TOKEN = "valid_admin_token"
INVALID_TOKEN = "invalid_token"
COLLECTION_ID = "60d21b4667d0d8992e610c85"

# Mock data
MOCK_COLLECTION = CollectionModel(
    id=COLLECTION_ID,
    pecha_collection_id="pecha_60d21b4667d0d8992e610c85",
    title="Test Collection",
    description="Test Description",
    language="en",
    slug="test-collection",
    has_child=False
)

MOCK_COLLECTIONS_RESPONSE = CollectionsResponse(
    parent=None,
    pagination=Pagination(total=2, skip=0, limit=10),
    collections=[
        MOCK_COLLECTION,
        CollectionModel(
            id="60d21b4667d0d8992e610c86",
            pecha_collection_id="pecha_60d21b4667d0d8992e610c86",
            title="Another Collection",
            description="Another Description",
            language="en",
            slug="another-collection",
            has_child=True
        )
    ]
)

MOCK_CREATE_REQUEST = CreateCollectionRequest(
    slug="new-collection",
    titles={"en": "New Collection"},
    descriptions={"en": "New Description"},
    parent_id=None
)

MOCK_UPDATE_REQUEST = UpdateCollectionRequest(
    titles={"en": "Updated Collection"},
    descriptions={"en": "Updated Description"}
)


# Tests for GET /collections endpoint

@pytest.mark.asyncio
async def test_read_collections_success():
    # Test successful retrieval of collections
    with patch("pecha_api.collections.collections_views.get_all_collections",
               new_callable=AsyncMock, return_value=MOCK_COLLECTIONS_RESPONSE):
        
        response = client.get("/collections")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["pagination"]["total"] == 2
        assert len(data["collections"]) == 2
        assert data["collections"][0]["title"] == "Test Collection"
        assert data["collections"][1]["has_child"] == True


@pytest.mark.asyncio
async def test_read_collections_with_filters():
    # Test reading collections with query parameters
    with patch("pecha_api.collections.collections_views.get_all_collections",
               new_callable=AsyncMock, return_value=MOCK_COLLECTIONS_RESPONSE):
        
        response = client.get("/collections", params={
            "parent_id": COLLECTION_ID,
            "language": "bo",
            "skip": 10,
            "limit": 5
        })
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_read_collections_service_error():
    # Test handling of service errors
    with patch("pecha_api.collections.collections_views.get_all_collections",
               new_callable=AsyncMock, side_effect=HTTPException(
                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                   detail="Internal server error"
               )):
        
        response = client.get("/collections")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


# Tests for POST /collections endpoint

@pytest.mark.asyncio
async def test_create_collection_success():
    # Test successful collection creation
    with patch("pecha_api.collections.collections_views.create_new_collection",
               new_callable=AsyncMock, return_value=MOCK_COLLECTION):
        
        response = client.post("/collections",
                             json=MOCK_CREATE_REQUEST.model_dump(),
                             headers={"Authorization": f"Bearer {VALID_TOKEN}"},
                             params={"language": "en"})
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "Test Collection"
        assert data["slug"] == "test-collection"
        assert data["has_child"] == False


@pytest.mark.asyncio
async def test_create_collection_without_auth():
    # Test collection creation without authentication
    response = client.post("/collections",
                         json=MOCK_CREATE_REQUEST.model_dump())
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_create_collection_invalid_data():
    # Test collection creation with invalid data
    invalid_data = {
        "slug": "",  # Empty slug should fail validation
        "titles": {},  # Empty titles
        "descriptions": {},
        "parent_id": None
    }
    
    response = client.post("/collections",
                         json=invalid_data,
                         headers={"Authorization": f"Bearer {VALID_TOKEN}"})
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Tests for PUT /collections/{collection_id} endpoint

@pytest.mark.asyncio
async def test_update_collection_success():
    # Test successful collection update
    updated_collection = CollectionModel(
        id=COLLECTION_ID,
        pecha_collection_id="pecha_60d21b4667d0d8992e610c85",
        title="Updated Collection",
        description="Updated Description",
        language="en",
        slug="test-collection",
        has_child=False
    )
    
    with patch("pecha_api.collections.collections_views.update_existing_collection",
               new_callable=AsyncMock, return_value=updated_collection):
        
        response = client.put(f"/collections/{COLLECTION_ID}",
                            json=MOCK_UPDATE_REQUEST.model_dump(),
                            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
                            params={"language": "en"})
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        data = response.json()
        assert data["title"] == "Updated Collection"
        assert data["description"] == "Updated Description"


@pytest.mark.asyncio
async def test_update_collection_without_auth():
    # Test collection update without authentication
    response = client.put(f"/collections/{COLLECTION_ID}",
                        json=MOCK_UPDATE_REQUEST.model_dump())
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_update_collection_invalid_data():
    # Test collection update with invalid data
    invalid_data = {
        "titles": {},  # Empty titles should fail validation
        "descriptions": {}
    }
    
    response = client.put(f"/collections/{COLLECTION_ID}",
                        json=invalid_data,
                        headers={"Authorization": f"Bearer {VALID_TOKEN}"})
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Tests for DELETE /collections/{collection_id} endpoint

@pytest.mark.asyncio
async def test_delete_collection_success():
    # Test successful collection deletion
    with patch("pecha_api.collections.collections_views.delete_existing_collection",
               new_callable=AsyncMock, return_value=COLLECTION_ID):
        
        response = client.delete(f"/collections/{COLLECTION_ID}",
                               headers={"Authorization": f"Bearer {VALID_TOKEN}"})
        
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_collection_without_auth():
    # Test collection deletion without authentication
    response = client.delete(f"/collections/{COLLECTION_ID}")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_delete_collection_invalid_token():
    # Test collection deletion with invalid token - patch where views imports it
    with patch("pecha_api.collections.collections_views.delete_existing_collection",
               new_callable=AsyncMock, side_effect=HTTPException(
                   status_code=status.HTTP_403_FORBIDDEN,
                   detail="Admin access required"
               )):
        
        response = client.delete(f"/collections/{COLLECTION_ID}",
                               headers={"Authorization": f"Bearer {INVALID_TOKEN}"})
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_delete_collection_not_found():
    # Test deleting non-existent collection - patch where views imports it
    with patch("pecha_api.collections.collections_views.delete_existing_collection",
               new_callable=AsyncMock, side_effect=HTTPException(
                   status_code=status.HTTP_404_NOT_FOUND,
                   detail="Collection not found"
               )):
        
        response = client.delete(f"/collections/{COLLECTION_ID}",
                               headers={"Authorization": f"Bearer {VALID_TOKEN}"})
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_collection_with_children():
    # Test deleting collection that has children - patch where views imports it
    with patch("pecha_api.collections.collections_views.delete_existing_collection",
               new_callable=AsyncMock, side_effect=HTTPException(
                   status_code=status.HTTP_400_BAD_REQUEST,
                   detail="Cannot delete collection with children"
               )):
        
        response = client.delete(f"/collections/{COLLECTION_ID}",
                               headers={"Authorization": f"Bearer {VALID_TOKEN}"})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# Tests for GET /text-uploader/collections/{pecha_collection_id} endpoint

@pytest.mark.asyncio
async def test_get_collection_by_pecha_collection_id_success():
    # Test successful retrieval of collection by pecha_collection_id
    pecha_collection_id = "pecha_60d21b4667d0d8992e610c85"
    expected_collection_id = "60d21b4667d0d8992e610c85"
    
    with patch("pecha_api.text_uploader.collections.uploader_collections_views.get_collection_by_pecha_collection_id_service",
               new_callable=AsyncMock, return_value=expected_collection_id):
        
        response = client.get(f"/text-uploader/collections/{pecha_collection_id}")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_collection_id


@pytest.mark.asyncio
async def test_get_collection_by_pecha_collection_id_not_found():
    # Test retrieval when pecha_collection_id doesn't exist
    pecha_collection_id = "nonexistent_pecha_id"
    
    with patch("pecha_api.text_uploader.collections.uploader_collections_views.get_collection_by_pecha_collection_id_service",
               new_callable=AsyncMock, return_value=None):
        
        response = client.get(f"/text-uploader/collections/{pecha_collection_id}")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() is None


@pytest.mark.asyncio
async def test_get_collection_by_pecha_collection_id_service_error():
    # Test handling of service errors
    pecha_collection_id = "pecha_error_id"
    
    with patch("pecha_api.text_uploader.collections.uploader_collections_views.get_collection_by_pecha_collection_id_service",
               new_callable=AsyncMock, side_effect=HTTPException(
                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                   detail="Internal server error"
               )):
        
        response = client.get(f"/text-uploader/collections/{pecha_collection_id}")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

