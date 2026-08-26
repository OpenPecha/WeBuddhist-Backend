import pytest
from unittest.mock import patch
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.group_recitation_collection.response_models import (
    GroupRecitationCollectionDTO,
    GroupRecitationCollectionDetailDTO,
    GroupRecitationCollectionItemDTO,
    GroupRecitationCollectionsResponse,
)

client = TestClient(api)


class TestDataFactory:
    """Factory for creating test data objects."""

    @staticmethod
    def create_collection_dto(
        id=None,
        group_id=None,
        name="Test Collection",
        img_url=None,
        item_count=0,
    ) -> GroupRecitationCollectionDTO:
        return GroupRecitationCollectionDTO(
            id=id or uuid4(),
            group_id=group_id or uuid4(),
            name=name,
            img_url=img_url,
            item_count=item_count,
            created_at=datetime.utcnow().isoformat(),
        )

    @staticmethod
    def create_collection_detail_dto(
        id=None,
        group_id=None,
        name="Test Collection",
        img_url=None,
        items=None,
    ) -> GroupRecitationCollectionDetailDTO:
        return GroupRecitationCollectionDetailDTO(
            id=id or uuid4(),
            group_id=group_id or uuid4(),
            name=name,
            img_url=img_url,
            created_at=datetime.utcnow().isoformat(),
            items=items or [],
        )

    @staticmethod
    def create_item_dto(
        id=None,
        text_id=None,
        title="Test Text",
        language="bo",
        type="sutra",
        display_order=1,
    ) -> GroupRecitationCollectionItemDTO:
        return GroupRecitationCollectionItemDTO(
            id=id or uuid4(),
            text_id=text_id or uuid4(),
            title=title,
            language=language,
            type=type,
            display_order=display_order,
        )

    @staticmethod
    def create_collections_response(
        collections=None,
        total=0,
        skip=0,
        limit=20,
    ) -> GroupRecitationCollectionsResponse:
        return GroupRecitationCollectionsResponse(
            collections=collections or [],
            total=total,
            skip=skip,
            limit=limit,
        )


class TestListGroupRecitationCollections:
    """Test cases for GET /author/groups/{group_id}/recitation-collections endpoint."""

    @patch('pecha_api.group_recitation_collection.views.list_group_collections_service')
    @pytest.mark.asyncio
    async def test_list_collections_success(self, mock_service):
        """Test successful retrieval of recitation collections."""
        group_id = uuid4()
        collections = [
            TestDataFactory.create_collection_dto(group_id=group_id, name="Collection 1", item_count=5),
            TestDataFactory.create_collection_dto(group_id=group_id, name="Collection 2", item_count=3),
        ]
        mock_service.return_value = TestDataFactory.create_collections_response(
            collections=collections,
            total=2,
        )

        response = client.get(f"/author/groups/{group_id}/recitation-collections")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["collections"]) == 2
        assert data["total"] == 2
        assert data["skip"] == 0
        assert data["limit"] == 20
        assert data["collections"][0]["name"] == "Collection 1"
        assert data["collections"][0]["item_count"] == 5
        mock_service.assert_called_once()

    @patch('pecha_api.group_recitation_collection.views.list_group_collections_service')
    @pytest.mark.asyncio
    async def test_list_collections_empty(self, mock_service):
        """Test list collections when no collections exist."""
        group_id = uuid4()
        mock_service.return_value = TestDataFactory.create_collections_response(
            collections=[],
            total=0,
        )

        response = client.get(f"/author/groups/{group_id}/recitation-collections")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["collections"]) == 0
        assert data["total"] == 0

    @patch('pecha_api.group_recitation_collection.views.list_group_collections_service')
    @pytest.mark.asyncio
    async def test_list_collections_with_pagination(self, mock_service):
        """Test list collections with custom pagination."""
        group_id = uuid4()
        mock_service.return_value = TestDataFactory.create_collections_response(
            collections=[TestDataFactory.create_collection_dto()],
            total=10,
            skip=5,
            limit=5,
        )

        response = client.get(
            f"/author/groups/{group_id}/recitation-collections",
            params={"skip": 5, "limit": 5}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["skip"] == 5
        assert data["limit"] == 5
        assert data["total"] == 10
        mock_service.assert_called_once()

    @patch('pecha_api.group_recitation_collection.views.list_group_collections_service')
    @pytest.mark.asyncio
    async def test_list_collections_group_not_found(self, mock_service):
        """Test list collections when group doesn't exist."""
        from fastapi import HTTPException
        group_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Group not found"}
        )

        response = client.get(f"/author/groups/{group_id}/recitation-collections")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_recitation_collection.views.list_group_collections_service')
    @pytest.mark.asyncio
    async def test_list_collections_with_timezone(self, mock_service):
        """Test list collections with timezone header."""
        group_id = uuid4()
        mock_service.return_value = TestDataFactory.create_collections_response(
            collections=[TestDataFactory.create_collection_dto()],
            total=1,
        )

        response = client.get(
            f"/author/groups/{group_id}/recitation-collections",
            headers={"X-Timezone": "Asia/Shanghai"}
        )

        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once()


class TestGetGroupRecitationCollectionDetail:
    """Test cases for GET /author/groups/recitation-collections/{collection_id} endpoint."""

    @patch('pecha_api.group_recitation_collection.views.get_group_collection_detail_service')
    @pytest.mark.asyncio
    async def test_get_collection_detail_success(self, mock_service):
        """Test successful retrieval of collection detail with items."""
        group_id = uuid4()
        collection_id = uuid4()
        items = [
            TestDataFactory.create_item_dto(title="Text 1", display_order=1),
            TestDataFactory.create_item_dto(title="Text 2", display_order=2),
        ]
        mock_service.return_value = TestDataFactory.create_collection_detail_dto(
            id=collection_id,
            group_id=group_id,
            name="My Collection",
            items=items,
        )

        response = client.get(f"/author/groups/recitation-collections/{collection_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(collection_id)
        assert data["group_id"] == str(group_id)
        assert data["name"] == "My Collection"
        assert len(data["items"]) == 2
        assert data["items"][0]["title"] == "Text 1"
        assert data["items"][1]["title"] == "Text 2"
        mock_service.assert_called_once_with(
            collection_id=collection_id,
            timezone_name=None,
            user_id=None,
        )

    @patch('pecha_api.group_recitation_collection.views.get_group_collection_detail_service')
    @pytest.mark.asyncio
    async def test_get_collection_detail_legacy_group_scoped_route(self, mock_service):
        """Test the legacy group-scoped detail URL still works and scopes by group."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_service.return_value = TestDataFactory.create_collection_detail_dto(
            id=collection_id,
            group_id=group_id,
            name="My Collection",
        )

        response = client.get(f"/author/groups/{group_id}/recitation-collections/{collection_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(collection_id)
        assert data["group_id"] == str(group_id)
        mock_service.assert_called_once_with(
            collection_id=collection_id,
            timezone_name=None,
            group_id=group_id,
            user_id=None,
        )

    @patch('pecha_api.group_recitation_collection.views.get_group_collection_detail_service')
    @pytest.mark.asyncio
    async def test_get_collection_detail_not_found(self, mock_service):
        """Test get collection detail when collection doesn't exist."""
        from fastapi import HTTPException
        collection_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Collection not found"}
        )

        response = client.get(f"/author/groups/recitation-collections/{collection_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_recitation_collection.views.get_group_collection_detail_service')
    @pytest.mark.asyncio
    async def test_get_collection_detail_with_timezone(self, mock_service):
        """Test get collection detail with timezone header."""
        collection_id = uuid4()
        mock_service.return_value = TestDataFactory.create_collection_detail_dto(
            id=collection_id,
        )

        response = client.get(
            f"/author/groups/recitation-collections/{collection_id}",
            headers={"X-Timezone": "Asia/Shanghai"}
        )

        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(
            collection_id=collection_id,
            timezone_name="Asia/Shanghai",
            user_id=None,
        )
