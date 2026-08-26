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
    AddGroupRecitationCollectionItemsResponse,
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

    @staticmethod
    def create_add_items_response(
        collection_id=None,
        added_count=0,
        items=None,
    ) -> AddGroupRecitationCollectionItemsResponse:
        return AddGroupRecitationCollectionItemsResponse(
            collection_id=collection_id or uuid4(),
            added_count=added_count,
            items=items or [],
        )


class TestCmsListCollections:
    """Test cases for GET /cms/author/groups/{group_id}/recitation-collections endpoint."""

    @patch('pecha_api.group_recitation_collection.cms_views.cms_list_group_collections_service')
    def test_list_success(self, mock_service):
        """Test successful retrieval of collections."""
        group_id = uuid4()
        collections = [
            TestDataFactory.create_collection_dto(group_id=group_id, name="Collection 1", item_count=5),
            TestDataFactory.create_collection_dto(group_id=group_id, name="Collection 2", item_count=3),
        ]
        mock_service.return_value = TestDataFactory.create_collections_response(
            collections=collections,
            total=2,
        )

        response = client.get(
            f"/cms/author/groups/{group_id}/recitation-collections",
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["collections"]) == 2
        assert data["total"] == 2
        assert data["collections"][0]["name"] == "Collection 1"
        mock_service.assert_called_once()

    @patch('pecha_api.group_recitation_collection.cms_views.cms_list_group_collections_service')
    def test_list_empty(self, mock_service):
        """Test list collections when no collections exist."""
        group_id = uuid4()
        mock_service.return_value = TestDataFactory.create_collections_response(
            collections=[],
            total=0,
        )

        response = client.get(
            f"/cms/author/groups/{group_id}/recitation-collections",
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["collections"]) == 0
        assert data["total"] == 0

    @patch('pecha_api.group_recitation_collection.cms_views.cms_list_group_collections_service')
    def test_list_pagination(self, mock_service):
        """Test list collections with custom pagination."""
        group_id = uuid4()
        mock_service.return_value = TestDataFactory.create_collections_response(
            collections=[TestDataFactory.create_collection_dto()],
            total=10,
            skip=5,
            limit=5,
        )

        response = client.get(
            f"/cms/author/groups/{group_id}/recitation-collections",
            params={"skip": 5, "limit": 5},
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["skip"] == 5
        assert data["limit"] == 5

    def test_list_unauthorized(self):
        """Test list collections without authorization."""
        group_id = uuid4()

        response = client.get(f"/cms/author/groups/{group_id}/recitation-collections")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCmsGetCollectionDetail:
    """Test cases for GET /cms/author/groups/{group_id}/recitation-collections/{collection_id} endpoint."""

    @patch('pecha_api.group_recitation_collection.cms_views.cms_get_group_collection_detail_service')
    @pytest.mark.asyncio
    async def test_get_detail_success(self, mock_service):
        """Test successful retrieval of collection detail."""
        group_id = uuid4()
        collection_id = uuid4()
        items = [
            TestDataFactory.create_item_dto(title="Text 1"),
            TestDataFactory.create_item_dto(title="Text 2"),
        ]
        mock_service.return_value = TestDataFactory.create_collection_detail_dto(
            id=collection_id,
            group_id=group_id,
            name="My Collection",
            items=items,
        )

        response = client.get(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}",
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(collection_id)
        assert data["name"] == "My Collection"
        assert len(data["items"]) == 2

    @patch('pecha_api.group_recitation_collection.cms_views.cms_get_group_collection_detail_service')
    @pytest.mark.asyncio
    async def test_get_detail_not_found(self, mock_service):
        """Test get collection detail when collection doesn't exist."""
        from fastapi import HTTPException
        group_id = uuid4()
        collection_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Collection not found"}
        )

        response = client.get(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}",
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_detail_unauthorized(self):
        """Test get collection detail without authorization."""
        group_id = uuid4()
        collection_id = uuid4()

        response = client.get(f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCmsCreateCollection:
    """Test cases for POST /cms/author/groups/{group_id}/recitation-collections endpoint."""

    @patch('pecha_api.group_recitation_collection.cms_views.cms_create_collection_service')
    def test_create_success(self, mock_service):
        """Test successful creation of collection."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_service.return_value = TestDataFactory.create_collection_detail_dto(
            id=collection_id,
            group_id=group_id,
            name="New Collection",
        )

        payload = {
            "name": "New Collection",
            "img_url": "collections/test.jpg",
        }

        response = client.post(
            f"/cms/author/groups/{group_id}/recitation-collections",
            json=payload,
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == str(collection_id)
        assert data["name"] == "New Collection"
        mock_service.assert_called_once()

    def test_create_unauthorized(self):
        """Test create collection without authorization."""
        group_id = uuid4()
        payload = {"name": "New Collection"}

        response = client.post(
            f"/cms/author/groups/{group_id}/recitation-collections",
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.group_recitation_collection.cms_views.cms_create_collection_service')
    def test_create_group_not_found(self, mock_service):
        """Test create collection when group doesn't exist."""
        from fastapi import HTTPException
        group_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Group not found"}
        )

        payload = {"name": "New Collection"}

        response = client.post(
            f"/cms/author/groups/{group_id}/recitation-collections",
            json=payload,
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestCmsUpdateCollection:
    """Test cases for PATCH /cms/author/groups/{group_id}/recitation-collections/{collection_id} endpoint."""

    @patch('pecha_api.group_recitation_collection.cms_views.cms_update_collection_service')
    def test_update_success(self, mock_service):
        """Test successful update of collection."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_service.return_value = TestDataFactory.create_collection_detail_dto(
            id=collection_id,
            group_id=group_id,
            name="Updated Collection",
        )

        payload = {"name": "Updated Collection"}

        response = client.patch(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}",
            json=payload,
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Collection"
        mock_service.assert_called_once()

    @patch('pecha_api.group_recitation_collection.cms_views.cms_update_collection_service')
    def test_update_not_found(self, mock_service):
        """Test update collection when collection doesn't exist."""
        from fastapi import HTTPException
        group_id = uuid4()
        collection_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Collection not found"}
        )

        payload = {"name": "Updated Collection"}

        response = client.patch(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}",
            json=payload,
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_unauthorized(self):
        """Test update collection without authorization."""
        group_id = uuid4()
        collection_id = uuid4()
        payload = {"name": "Updated Collection"}

        response = client.patch(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}",
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCmsDeleteCollection:
    """Test cases for DELETE /cms/author/groups/{group_id}/recitation-collections/{collection_id} endpoint."""

    @patch('pecha_api.group_recitation_collection.cms_views.cms_delete_collection_service')
    def test_delete_success(self, mock_service):
        """Test successful deletion of collection."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_service.return_value = None

        response = client.delete(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}",
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_service.assert_called_once()

    @patch('pecha_api.group_recitation_collection.cms_views.cms_delete_collection_service')
    def test_delete_not_found(self, mock_service):
        """Test delete collection when collection doesn't exist."""
        from fastapi import HTTPException
        group_id = uuid4()
        collection_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Collection not found"}
        )

        response = client.delete(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}",
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_unauthorized(self):
        """Test delete collection without authorization."""
        group_id = uuid4()
        collection_id = uuid4()

        response = client.delete(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCmsAddItems:
    """Test cases for POST /cms/author/groups/{group_id}/recitation-collections/{collection_id}/items endpoint."""

    @patch('pecha_api.group_recitation_collection.cms_views.cms_add_items_service')
    @pytest.mark.asyncio
    async def test_add_items_success(self, mock_service):
        """Test successful addition of items to collection."""
        group_id = uuid4()
        collection_id = uuid4()
        text_id1 = uuid4()
        text_id2 = uuid4()
        
        items = [
            TestDataFactory.create_item_dto(text_id=text_id1, title="Text 1"),
            TestDataFactory.create_item_dto(text_id=text_id2, title="Text 2"),
        ]
        mock_service.return_value = TestDataFactory.create_add_items_response(
            collection_id=collection_id,
            added_count=2,
            items=items,
        )

        payload = {"text_ids": [str(text_id1), str(text_id2)]}

        response = client.post(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}/items",
            json=payload,
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["collection_id"] == str(collection_id)
        assert data["added_count"] == 2
        assert len(data["items"]) == 2

    @patch('pecha_api.group_recitation_collection.cms_views.cms_add_items_service')
    @pytest.mark.asyncio
    async def test_add_items_collection_not_found(self, mock_service):
        """Test add items when collection doesn't exist."""
        from fastapi import HTTPException
        group_id = uuid4()
        collection_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Collection not found"}
        )

        payload = {"text_ids": [str(uuid4())]}

        response = client.post(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}/items",
            json=payload,
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_add_items_unauthorized(self):
        """Test add items without authorization."""
        group_id = uuid4()
        collection_id = uuid4()
        payload = {"text_ids": [str(uuid4())]}

        response = client.post(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}/items",
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCmsDeleteItem:
    """Test cases for DELETE /cms/author/groups/{group_id}/recitation-collections/{collection_id}/items/{item_id} endpoint."""

    @patch('pecha_api.group_recitation_collection.cms_views.cms_delete_item_service')
    def test_delete_item_success(self, mock_service):
        """Test successful deletion of item from collection."""
        group_id = uuid4()
        collection_id = uuid4()
        item_id = uuid4()
        mock_service.return_value = None

        response = client.delete(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}/items/{item_id}",
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_service.assert_called_once()

    @patch('pecha_api.group_recitation_collection.cms_views.cms_delete_item_service')
    def test_delete_item_not_found(self, mock_service):
        """Test delete item when item doesn't exist."""
        from fastapi import HTTPException
        group_id = uuid4()
        collection_id = uuid4()
        item_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Item not found"}
        )

        response = client.delete(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}/items/{item_id}",
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_item_unauthorized(self):
        """Test delete item without authorization."""
        group_id = uuid4()
        collection_id = uuid4()
        item_id = uuid4()

        response = client.delete(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}/items/{item_id}"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestCmsReorderItems:
    """Test cases for PUT /cms/author/groups/{group_id}/recitation-collections/{collection_id}/items/reorder endpoint."""

    @patch('pecha_api.group_recitation_collection.cms_views.cms_reorder_items_service')
    @pytest.mark.asyncio
    async def test_reorder_success(self, mock_service):
        """Test successful reordering of items."""
        group_id = uuid4()
        collection_id = uuid4()
        item_id1 = uuid4()
        item_id2 = uuid4()
        
        items = [
            TestDataFactory.create_item_dto(id=item_id2, display_order=1),
            TestDataFactory.create_item_dto(id=item_id1, display_order=2),
        ]
        mock_service.return_value = TestDataFactory.create_collection_detail_dto(
            id=collection_id,
            group_id=group_id,
            items=items,
        )

        payload = {"item_ids": [str(item_id2), str(item_id1)]}

        response = client.put(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}/items/reorder",
            json=payload,
            headers={"Authorization": "Bearer admin_token"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["display_order"] == 1
        assert data["items"][1]["display_order"] == 2

    def test_reorder_unauthorized(self):
        """Test reorder items without authorization."""
        group_id = uuid4()
        collection_id = uuid4()
        payload = {"item_ids": [str(uuid4())]}

        response = client.put(
            f"/cms/author/groups/{group_id}/recitation-collections/{collection_id}/items/reorder",
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
