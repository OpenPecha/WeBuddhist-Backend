import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
from starlette import status

from pecha_api.group_recitation_collection.service import (
    list_group_collections_service,
    get_group_collection_detail_service,
    _build_items_dto,
    _validate_group_is_public,
)
from pecha_api.group_recitation_collection.response_models import (
    GroupRecitationCollectionsResponse,
    GroupRecitationCollectionDetailDTO,
)


class MockGroupRecitationCollection:
    """Mock GroupRecitationCollection model."""
    def __init__(self, id=None, group_id=None, name="Test Collection", img_url=None):
        self.id = id or uuid4()
        self.group_id = group_id or uuid4()
        self.name = name
        self.img_url = img_url
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.deleted_at = None


class MockGroupRecitationCollectionItem:
    """Mock GroupRecitationCollectionItem model."""
    def __init__(self, id=None, text_id=None, display_order=1):
        self.id = id or uuid4()
        self.text_id = text_id or uuid4()
        self.display_order = display_order
        self.deleted_at = None


class MockGroup:
    """Mock Group model."""
    def __init__(self, id=None, is_public=True):
        self.id = id or uuid4()
        self.is_public = is_public


class MockText:
    """Mock Text from MongoDB."""
    def __init__(self, title="Test Text", language="bo", type="sutra"):
        self.title = title
        self.language = language
        self.type = type


class TestListGroupCollectionsService:
    """Test cases for list_group_collections_service function."""

    @patch('pecha_api.group_recitation_collection.service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.service.get_group_collections')
    @patch('pecha_api.group_recitation_collection.service.get_collection_item_counts')
    @patch('pecha_api.group_recitation_collection.service.filter_items_for_timezone')
    @pytest.mark.asyncio
    async def test_list_collections_success(
        self, mock_filter, mock_item_counts, mock_get_collections, mock_get_group, mock_session
    ):
        """Test successful retrieval of collections with item counts."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_group.return_value = MockGroup(id=group_id, is_public=True)
        
        collection1 = MockGroupRecitationCollection(id=uuid4(), group_id=group_id, name="Collection 1")
        collection2 = MockGroupRecitationCollection(id=uuid4(), group_id=group_id, name="Collection 2")
        mock_get_collections.return_value = ([collection1, collection2], 2)
        mock_item_counts.return_value = {collection1.id: 5, collection2.id: 3}
        mock_filter.side_effect = lambda items, **kwargs: items

        result = await list_group_collections_service(group_id=group_id, skip=0, limit=20)

        assert isinstance(result, GroupRecitationCollectionsResponse)
        assert len(result.collections) == 2
        assert result.total == 2
        assert result.skip == 0
        assert result.limit == 20
        assert result.collections[0].name == "Collection 1"
        assert result.collections[0].item_count == 5
        assert result.collections[1].item_count == 3
        mock_get_group.assert_called_once_with(db=mock_db, group_id=group_id)
        mock_get_collections.assert_called_once_with(db=mock_db, group_id=group_id, skip=0, limit=20)

    @patch('pecha_api.group_recitation_collection.service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.service.get_group_collections')
    @pytest.mark.asyncio
    async def test_list_collections_empty(self, mock_get_collections, mock_get_group, mock_session):
        """Test list collections when no collections exist."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_group.return_value = MockGroup(id=group_id, is_public=True)
        mock_get_collections.return_value = ([], 0)

        result = await list_group_collections_service(group_id=group_id)

        assert len(result.collections) == 0
        assert result.total == 0

    @patch('pecha_api.group_recitation_collection.service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    @pytest.mark.asyncio
    async def test_list_collections_group_not_public(self, mock_get_group, mock_session):
        """Test list collections when group is not public."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_group.return_value = MockGroup(id=group_id, is_public=False)

        with pytest.raises(HTTPException) as exc_info:
            await list_group_collections_service(group_id=group_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_recitation_collection.service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.service.get_group_collections')
    @patch('pecha_api.group_recitation_collection.service.get_collection_item_counts')
    @patch('pecha_api.group_recitation_collection.service.filter_items_for_timezone')
    @pytest.mark.asyncio
    async def test_list_collections_region_filtered(
        self, mock_filter, mock_item_counts, mock_get_collections, mock_get_group, mock_session
    ):
        """Test list collections with timezone filtering."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_group.return_value = MockGroup(id=group_id, is_public=True)
        
        collection1 = MockGroupRecitationCollection(id=uuid4(), group_id=group_id)
        collection2 = MockGroupRecitationCollection(id=uuid4(), group_id=group_id)
        mock_get_collections.return_value = ([collection1, collection2], 2)
        mock_filter.return_value = [collection1]  # Filter out collection2
        mock_item_counts.return_value = {collection1.id: 5}

        result = await list_group_collections_service(
            group_id=group_id,
            timezone_name="Asia/Shanghai"
        )

        assert len(result.collections) == 1
        mock_filter.assert_called_once()


class TestGetGroupCollectionDetailService:
    """Test cases for get_group_collection_detail_service function."""

    @patch('pecha_api.group_recitation_collection.service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.service.get_collection_without_group_filter')
    @patch('pecha_api.group_recitation_collection.service.get_collection_items')
    @patch('pecha_api.group_recitation_collection.service._build_items_dto')
    @patch('pecha_api.group_recitation_collection.service.filter_items_for_timezone')
    @pytest.mark.asyncio
    async def test_get_detail_success(
        self, mock_filter, mock_build_items, mock_get_items, mock_get_collection, mock_get_group, mock_session
    ):
        """Test successful retrieval of collection detail with items."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_group.return_value = MockGroup(id=group_id, is_public=True)
        
        collection = MockGroupRecitationCollection(id=collection_id, group_id=group_id, name="My Collection")
        mock_get_collection.return_value = collection
        mock_filter.return_value = [collection]
        
        items = [
            MockGroupRecitationCollectionItem(display_order=1),
            MockGroupRecitationCollectionItem(display_order=2),
        ]
        mock_get_items.return_value = items
        
        from pecha_api.group_recitation_collection.response_models import GroupRecitationCollectionItemDTO
        mock_build_items.return_value = [
            GroupRecitationCollectionItemDTO(
                id=items[0].id,
                text_id=items[0].text_id,
                title="Text 1",
                language="bo",
                type="sutra",
                display_order=1,
            ),
            GroupRecitationCollectionItemDTO(
                id=items[1].id,
                text_id=items[1].text_id,
                title="Text 2",
                language="bo",
                type="sutra",
                display_order=2,
            ),
        ]

        result = await get_group_collection_detail_service(
            collection_id=collection_id,
        )

        assert isinstance(result, GroupRecitationCollectionDetailDTO)
        assert result.id == collection_id
        assert result.name == "My Collection"
        assert result.group_id == group_id
        assert len(result.items) == 2
        mock_get_collection.assert_called_once_with(db=mock_db, collection_id=collection_id)
        mock_get_group.assert_called_once_with(db=mock_db, group_id=group_id)
        mock_get_items.assert_called_once_with(db=mock_db, collection_id=collection_id)

    @patch('pecha_api.group_recitation_collection.service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.service.get_collection_without_group_filter')
    @pytest.mark.asyncio
    async def test_get_detail_not_found(self, mock_get_collection, mock_get_group, mock_session):
        """Test get collection detail when collection doesn't exist."""
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_collection.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_group_collection_detail_service(collection_id=collection_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        mock_get_group.assert_not_called()

    @patch('pecha_api.group_recitation_collection.service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.service.get_collection_without_group_filter')
    @pytest.mark.asyncio
    async def test_get_detail_group_mismatch(self, mock_get_collection, mock_get_group, mock_session):
        """Test 404 when the legacy group-scoped call passes a different group_id."""
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_collection.return_value = MockGroupRecitationCollection(
            id=collection_id, group_id=uuid4()
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_group_collection_detail_service(
                collection_id=collection_id,
                group_id=uuid4(),  # different group
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        mock_get_group.assert_not_called()

    @patch('pecha_api.group_recitation_collection.service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.service.get_collection_without_group_filter')
    @pytest.mark.asyncio
    async def test_get_detail_group_not_public(self, mock_get_collection, mock_get_group, mock_session):
        """Test get collection detail when the owning group is not public."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_collection.return_value = MockGroupRecitationCollection(
            id=collection_id, group_id=group_id
        )
        mock_get_group.return_value = MockGroup(id=group_id, is_public=False)

        with pytest.raises(HTTPException) as exc_info:
            await get_group_collection_detail_service(collection_id=collection_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_recitation_collection.service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.service.get_collection_without_group_filter')
    @patch('pecha_api.group_recitation_collection.service.filter_items_for_timezone')
    @pytest.mark.asyncio
    async def test_get_detail_region_restricted(
        self, mock_filter, mock_get_collection, mock_get_group, mock_session
    ):
        """Test get collection detail when filtered by timezone."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_group.return_value = MockGroup(id=group_id, is_public=True)

        collection = MockGroupRecitationCollection(id=collection_id, group_id=group_id)
        mock_get_collection.return_value = collection
        mock_filter.return_value = []  # Filtered out

        with pytest.raises(HTTPException) as exc_info:
            await get_group_collection_detail_service(
                collection_id=collection_id,
                timezone_name="Asia/Shanghai"
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestBuildItemsDto:
    """Test cases for _build_items_dto function."""

    @patch('pecha_api.group_recitation_collection.service.get_texts_by_ids')
    @pytest.mark.asyncio
    async def test_build_items_dto_success(self, mock_get_texts):
        """Test building item DTOs with text metadata from MongoDB."""
        text_id1 = uuid4()
        text_id2 = uuid4()
        items = [
            MockGroupRecitationCollectionItem(text_id=text_id1, display_order=1),
            MockGroupRecitationCollectionItem(text_id=text_id2, display_order=2),
        ]
        
        mock_get_texts.return_value = {
            str(text_id1): MockText(title="Text 1", language="bo", type="sutra"),
            str(text_id2): MockText(title="Text 2", language="en", type="prayer"),
        }

        result = await _build_items_dto(items)

        assert len(result) == 2
        assert result[0].text_id == text_id1
        assert result[0].title == "Text 1"
        assert result[0].language == "bo"
        assert result[0].type == "sutra"
        assert result[0].display_order == 1
        assert result[1].title == "Text 2"
        mock_get_texts.assert_called_once_with(text_ids=[str(text_id1), str(text_id2)])

    @pytest.mark.asyncio
    async def test_build_items_dto_empty(self):
        """Test building item DTOs with empty list."""
        result = await _build_items_dto([])
        assert result == []


class TestValidateGroupIsPublic:
    """Test cases for _validate_group_is_public function."""

    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    def test_validate_group_is_public_success(self, mock_get_group):
        """Test validation passes for public group."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_get_group.return_value = MockGroup(id=group_id, is_public=True)

        # Should not raise exception
        _validate_group_is_public(mock_db, group_id)
        mock_get_group.assert_called_once_with(db=mock_db, group_id=group_id)

    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    def test_validate_group_is_public_non_public_group(self, mock_get_group):
        """Test validation fails for non-public group."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_get_group.return_value = MockGroup(id=group_id, is_public=False)

        with pytest.raises(HTTPException) as exc_info:
            _validate_group_is_public(mock_db, group_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_recitation_collection.service.get_group_by_id')
    def test_validate_group_is_public_non_existent_group(self, mock_get_group):
        """Test validation fails for non-existent group."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_get_group.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            _validate_group_is_public(mock_db, group_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
