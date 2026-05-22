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
    Pagination
)

client = TestClient(api)

# Test constants
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

