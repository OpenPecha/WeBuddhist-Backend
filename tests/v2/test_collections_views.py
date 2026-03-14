import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from pecha_api.v2.app import api_v2
from pecha_api.collections.collections_response_models import CollectionModel, CollectionsResponse, Pagination


client = TestClient(api_v2)


class TestCollectionsV2Endpoint:
    @patch('pecha_api.v2.collections_views.get_collections_from_openpecha')
    def test_get_collections_success(self, mock_service):
        mock_response = CollectionsResponse(
            parent=None,
            pagination=Pagination(total=2, skip=0, limit=10),
            collections=[
                CollectionModel(
                    id="cat-1",
                    pecha_collection_id="cat-1",
                    title="Discourses",
                    description="Buddhist discourses",
                    has_child=True,
                    language="en",
                    slug="discourses"
                ),
                CollectionModel(
                    id="cat-2",
                    pecha_collection_id="cat-2",
                    title="Vinaya",
                    description="Monastic discipline",
                    has_child=False,
                    language="en",
                    slug="vinaya"
                )
            ]
        )
        mock_service.return_value = mock_response
        
        response = client.get("/collections?language=en")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["collections"]) == 2
        assert data["pagination"]["total"] == 2
        assert data["collections"][0]["title"] == "Discourses"

    @patch('pecha_api.v2.collections_views.get_collections_from_openpecha')
    def test_get_collections_with_parent_id(self, mock_service):
        mock_response = CollectionsResponse(
            parent=CollectionModel(
                id="parent-1",
                pecha_collection_id="parent-1",
                title="Parent Category",
                description="",
                has_child=True,
                language="en",
                slug="parent-category"
            ),
            pagination=Pagination(total=1, skip=0, limit=10),
            collections=[
                CollectionModel(
                    id="child-1",
                    pecha_collection_id="child-1",
                    title="Child Category",
                    description="",
                    has_child=False,
                    language="en",
                    slug="child-category"
                )
            ]
        )
        mock_service.return_value = mock_response
        
        response = client.get("/collections?parent_id=parent-1&language=en")
        
        assert response.status_code == 200
        data = response.json()
        assert data["parent"]["id"] == "parent-1"
        assert len(data["collections"]) == 1

    @patch('pecha_api.v2.collections_views.get_collections_from_openpecha')
    def test_get_collections_with_pagination(self, mock_service):
        mock_response = CollectionsResponse(
            parent=None,
            pagination=Pagination(total=100, skip=10, limit=5),
            collections=[
                CollectionModel(
                    id=f"cat-{i}",
                    pecha_collection_id=f"cat-{i}",
                    title=f"Category {i}",
                    description="",
                    has_child=False,
                    language="en",
                    slug=f"category-{i}"
                ) for i in range(5)
            ]
        )
        mock_service.return_value = mock_response
        
        response = client.get("/collections?skip=10&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["skip"] == 10
        assert data["pagination"]["limit"] == 5
        assert data["pagination"]["total"] == 100

    @patch('pecha_api.v2.collections_views.get_collections_from_openpecha')
    def test_get_collections_empty(self, mock_service):
        mock_response = CollectionsResponse(
            parent=None,
            pagination=Pagination(total=0, skip=0, limit=10),
            collections=[]
        )
        mock_service.return_value = mock_response
        
        response = client.get("/collections")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["collections"]) == 0
        assert data["pagination"]["total"] == 0

    @patch('pecha_api.v2.collections_views.get_collections_from_openpecha')
    def test_get_collections_tibetan_language(self, mock_service):
        mock_response = CollectionsResponse(
            parent=None,
            pagination=Pagination(total=1, skip=0, limit=10),
            collections=[
                CollectionModel(
                    id="cat-1",
                    pecha_collection_id="cat-1",
                    title="མདོ།",
                    description="",
                    has_child=True,
                    language="bo",
                    slug="མདོ།"
                )
            ]
        )
        mock_service.return_value = mock_response
        
        response = client.get("/collections?language=bo")
        
        assert response.status_code == 200
        data = response.json()
        assert data["collections"][0]["title"] == "མདོ།"
        assert data["collections"][0]["language"] == "bo"


class TestCollectionsV2ValidationErrors:
    def test_invalid_skip_negative(self):
        response = client.get("/collections?skip=-1")
        assert response.status_code == 422

    def test_invalid_limit_zero(self):
        response = client.get("/collections?limit=0")
        assert response.status_code == 422

    def test_invalid_limit_too_large(self):
        response = client.get("/collections?limit=101")
        assert response.status_code == 422


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 204
