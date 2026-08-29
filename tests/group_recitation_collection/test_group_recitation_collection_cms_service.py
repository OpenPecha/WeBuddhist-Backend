import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime, timezone as tz
from fastapi import HTTPException
from starlette import status

from pecha_api.group_recitation_collection.cms_service import (
    cms_list_group_collections_service,
    cms_get_group_collection_detail_service,
    cms_create_collection_service,
    cms_update_collection_service,
    cms_delete_collection_service,
    cms_add_items_service,
    cms_delete_item_service,
    cms_reorder_items_service,
)
from pecha_api.group_recitation_collection.response_models import (
    CreateGroupRecitationCollectionRequest,
    UpdateGroupRecitationCollectionRequest,
    GroupRecitationCollectionsResponse,
    GroupRecitationCollectionDetailDTO,
    AddGroupRecitationCollectionItemsResponse,
)


class MockGroupRecitationCollection:
    """Mock GroupRecitationCollection model."""
    def __init__(self, id=None, group_id=None, name="Test Collection", img_url=None):
        self.id = id or uuid4()
        self.group_id = group_id or uuid4()
        self.name = name
        self.img_url = img_url
        self.created_at = datetime.now(tz.utc)
        self.updated_at = datetime.now(tz.utc)
        self.deleted_at = None
        self.created_by = uuid4()
        self.updated_by = uuid4()


class MockGroupRecitationCollectionItem:
    """Mock GroupRecitationCollectionItem model."""
    def __init__(self, id=None, text_id=None, display_order=1):
        self.id = id or uuid4()
        self.text_id = str(text_id or uuid4())
        self.display_order = display_order
        self.deleted_at = None


class MockGroup:
    """Mock Group model."""
    def __init__(self, id=None):
        self.id = id or uuid4()
        # Published by default; these cases test is_public on live groups.
        self.status = "PUBLISHED"


class MockAuthor:
    """Mock Author model."""
    def __init__(self, id=None):
        self.id = id or uuid4()


class MockText:
    """Mock Text from MongoDB."""
    def __init__(self, title="Test Text", language="bo", type="sutra"):
        self.title = title
        self.language = language
        self.type = type


class TestCmsListGroupCollectionsService:
    """Test cases for cms_list_group_collections_service function."""

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_read_group_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_collections')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_item_counts')
    def test_list_success(
        self, mock_item_counts, mock_get_collections, mock_require_read, 
        mock_get_group, mock_validate, mock_session
    ):
        """Test successful retrieval of collections."""
        group_id = uuid4()
        author = MockAuthor()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = author
        mock_get_group.return_value = MockGroup(id=group_id)
        
        collection1 = MockGroupRecitationCollection(id=uuid4(), group_id=group_id, name="Collection 1")
        collection2 = MockGroupRecitationCollection(id=uuid4(), group_id=group_id, name="Collection 2")
        mock_get_collections.return_value = ([collection1, collection2], 2)
        mock_item_counts.return_value = {collection1.id: 5, collection2.id: 3}

        result = cms_list_group_collections_service(
            token="admin_token",
            group_id=group_id,
            skip=0,
            limit=20,
        )

        assert isinstance(result, GroupRecitationCollectionsResponse)
        assert len(result.collections) == 2
        assert result.total == 2
        assert result.collections[0].name == "Collection 1"
        assert result.collections[0].item_count == 5
        mock_validate.assert_called_once_with(token="admin_token")
        mock_require_read.assert_called_once_with(db=mock_db, group_id=group_id, author=author)

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_read_group_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_collections')
    def test_list_empty(
        self, mock_get_collections, mock_require_read, mock_get_group, mock_validate, mock_session
    ):
        """Test list collections when no collections exist."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_collections.return_value = ([], 0)

        result = cms_list_group_collections_service(token="admin_token", group_id=group_id)

        assert len(result.collections) == 0
        assert result.total == 0

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_read_group_content')
    def test_list_permission_denied(
        self, mock_require_read, mock_get_group, mock_validate, mock_session
    ):
        """Test list collections when user lacks permission."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_require_read.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Permission denied"}
        )

        with pytest.raises(HTTPException) as exc_info:
            cms_list_group_collections_service(token="user_token", group_id=group_id)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestCmsGetGroupCollectionDetailService:
    """Test cases for cms_get_group_collection_detail_service function."""

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_read_group_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_items')
    @patch('pecha_api.group_recitation_collection.cms_service._build_items_dto')
    @pytest.mark.asyncio
    async def test_get_detail_success(
        self, mock_build_items, mock_get_items, mock_get_collection,
        mock_require_read, mock_get_group, mock_validate, mock_session
    ):
        """Test successful retrieval of collection detail."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        
        collection = MockGroupRecitationCollection(id=collection_id, group_id=group_id, name="My Collection")
        mock_get_collection.return_value = collection
        
        items = [MockGroupRecitationCollectionItem(display_order=1)]
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
        ]

        result = await cms_get_group_collection_detail_service(
            token="admin_token",
            group_id=group_id,
            collection_id=collection_id,
        )

        assert isinstance(result, GroupRecitationCollectionDetailDTO)
        assert result.id == collection_id
        assert result.name == "My Collection"
        assert len(result.items) == 1

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_read_group_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    @pytest.mark.asyncio
    async def test_get_detail_not_found(
        self, mock_get_collection, mock_require_read, mock_get_group, mock_validate, mock_session
    ):
        """Test get collection detail when collection doesn't exist."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_collection.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await cms_get_group_collection_detail_service(
                token="admin_token",
                group_id=group_id,
                collection_id=collection_id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_read_group_content')
    @pytest.mark.asyncio
    async def test_get_detail_permission_denied(
        self, mock_require_read, mock_get_group, mock_validate, mock_session
    ):
        """Test get collection detail when user lacks permission."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_require_read.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Permission denied"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await cms_get_group_collection_detail_service(
                token="user_token",
                group_id=group_id,
                collection_id=collection_id,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestCmsCreateCollectionService:
    """Test cases for cms_create_collection_service function."""

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.create_collection')
    def test_create_success(
        self, mock_create, mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test successful creation of collection."""
        group_id = uuid4()
        author = MockAuthor()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = author
        mock_get_group.return_value = MockGroup(id=group_id)
        
        created_collection = MockGroupRecitationCollection(
            id=uuid4(),
            group_id=group_id,
            name="New Collection",
        )
        mock_create.return_value = created_collection

        request = CreateGroupRecitationCollectionRequest(
            name="New Collection",
            img_url="collections/test.jpg",
        )

        result = cms_create_collection_service(
            token="admin_token",
            group_id=group_id,
            request=request,
        )

        assert isinstance(result, GroupRecitationCollectionDetailDTO)
        assert result.name == "New Collection"
        assert len(result.items) == 0
        mock_create.assert_called_once()

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    def test_create_group_not_found(self, mock_get_group, mock_validate, mock_session):
        """Test create collection when group doesn't exist."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = None

        request = CreateGroupRecitationCollectionRequest(name="New Collection")

        with pytest.raises(HTTPException) as exc_info:
            cms_create_collection_service(
                token="admin_token",
                group_id=group_id,
                request=request,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    def test_create_permission_denied(
        self, mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test create collection when user lacks permission."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_require_create.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Permission denied"}
        )

        request = CreateGroupRecitationCollectionRequest(name="New Collection")

        with pytest.raises(HTTPException) as exc_info:
            cms_create_collection_service(
                token="user_token",
                group_id=group_id,
                request=request,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestCmsUpdateCollectionService:
    """Test cases for cms_update_collection_service function."""

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.update_collection')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_items')
    def test_update_success(
        self, mock_get_items, mock_update, mock_get_collection,
        mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test successful update of collection."""
        group_id = uuid4()
        collection_id = uuid4()
        author = MockAuthor()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = author
        mock_get_group.return_value = MockGroup(id=group_id)
        
        collection = MockGroupRecitationCollection(
            id=collection_id,
            group_id=group_id,
            name="Old Name",
        )
        mock_get_collection.return_value = collection
        mock_get_items.return_value = []

        request = UpdateGroupRecitationCollectionRequest(name="Updated Name")

        result = cms_update_collection_service(
            token="admin_token",
            group_id=group_id,
            collection_id=collection_id,
            request=request,
        )

        assert result.name == "Updated Name"
        assert collection.name == "Updated Name"
        mock_update.assert_called_once()

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    def test_update_not_found(
        self, mock_get_collection, mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test update collection when collection doesn't exist."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_collection.return_value = None

        request = UpdateGroupRecitationCollectionRequest(name="Updated Name")

        with pytest.raises(HTTPException) as exc_info:
            cms_update_collection_service(
                token="admin_token",
                group_id=group_id,
                collection_id=collection_id,
                request=request,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    def test_update_permission_denied(
        self, mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test update collection when user lacks permission."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_require_create.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Permission denied"}
        )

        request = UpdateGroupRecitationCollectionRequest(name="Updated Name")

        with pytest.raises(HTTPException) as exc_info:
            cms_update_collection_service(
                token="user_token",
                group_id=group_id,
                collection_id=collection_id,
                request=request,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestCmsDeleteCollectionService:
    """Test cases for cms_delete_collection_service function."""

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.soft_delete_collection')
    def test_delete_success(
        self, mock_soft_delete, mock_get_collection, mock_require_create,
        mock_get_group, mock_validate, mock_session
    ):
        """Test successful deletion of collection."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        
        collection = MockGroupRecitationCollection(id=collection_id, group_id=group_id)
        mock_get_collection.return_value = collection

        cms_delete_collection_service(
            token="admin_token",
            group_id=group_id,
            collection_id=collection_id,
        )

        mock_soft_delete.assert_called_once_with(db=mock_db, collection=collection)

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    def test_delete_not_found(
        self, mock_get_collection, mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test delete collection when collection doesn't exist."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_collection.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            cms_delete_collection_service(
                token="admin_token",
                group_id=group_id,
                collection_id=collection_id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    def test_delete_permission_denied(
        self, mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test delete collection when user lacks permission."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_require_create.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Permission denied"}
        )

        with pytest.raises(HTTPException) as exc_info:
            cms_delete_collection_service(
                token="user_token",
                group_id=group_id,
                collection_id=collection_id,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestCmsAddItemsService:
    """Test cases for cms_add_items_service function."""

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.TextUtils.validate_text_exists')
    @patch('pecha_api.group_recitation_collection.cms_service.get_max_display_order')
    @patch('pecha_api.group_recitation_collection.cms_service.create_collection_items')
    @patch('pecha_api.group_recitation_collection.cms_service._build_items_dto')
    @pytest.mark.asyncio
    async def test_add_items_success(
        self, mock_build_items, mock_create_items, mock_max_order, mock_validate_text,
        mock_get_collection, mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test successful addition of items to collection."""
        group_id = uuid4()
        collection_id = uuid4()
        text_id1 = uuid4()
        text_id2 = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        
        collection = MockGroupRecitationCollection(id=collection_id, group_id=group_id)
        mock_get_collection.return_value = collection
        mock_validate_text.return_value = None
        mock_max_order.return_value = 0
        
        saved_items = [
            MockGroupRecitationCollectionItem(text_id=text_id1, display_order=1),
            MockGroupRecitationCollectionItem(text_id=text_id2, display_order=2),
        ]
        mock_create_items.return_value = saved_items
        
        from pecha_api.group_recitation_collection.response_models import GroupRecitationCollectionItemDTO
        mock_build_items.return_value = [
            GroupRecitationCollectionItemDTO(
                id=saved_items[0].id,
                text_id=str(text_id1),
                title="Text 1",
                language="bo",
                type="sutra",
                display_order=1,
            ),
            GroupRecitationCollectionItemDTO(
                id=saved_items[1].id,
                text_id=str(text_id2),
                title="Text 2",
                language="bo",
                type="sutra",
                display_order=2,
            ),
        ]

        result = await cms_add_items_service(
            token="admin_token",
            group_id=group_id,
            collection_id=collection_id,
            text_ids=[text_id1, text_id2],
        )

        assert isinstance(result, AddGroupRecitationCollectionItemsResponse)
        assert result.collection_id == collection_id
        assert result.added_count == 2
        assert len(result.items) == 2

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    @pytest.mark.asyncio
    async def test_add_items_collection_not_found(
        self, mock_get_collection, mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test add items when collection doesn't exist."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_collection.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await cms_add_items_service(
                token="admin_token",
                group_id=group_id,
                collection_id=collection_id,
                text_ids=[uuid4()],
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.TextUtils.validate_text_exists')
    @pytest.mark.asyncio
    async def test_add_items_text_not_found(
        self, mock_validate_text, mock_get_collection, mock_require_create,
        mock_get_group, mock_validate, mock_session
    ):
        """Test add items when text doesn't exist."""
        group_id = uuid4()
        collection_id = uuid4()
        text_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        
        collection = MockGroupRecitationCollection(id=collection_id, group_id=group_id)
        mock_get_collection.return_value = collection
        mock_validate_text.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Text not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            await cms_add_items_service(
                token="admin_token",
                group_id=group_id,
                collection_id=collection_id,
                text_ids=[text_id],
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestCmsDeleteItemService:
    """Test cases for cms_delete_item_service function."""

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_item_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.soft_delete_collection_item')
    def test_delete_item_success(
        self, mock_soft_delete, mock_get_item, mock_get_collection,
        mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test successful deletion of item from collection."""
        group_id = uuid4()
        collection_id = uuid4()
        item_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        
        collection = MockGroupRecitationCollection(id=collection_id, group_id=group_id)
        mock_get_collection.return_value = collection
        
        item = MockGroupRecitationCollectionItem(id=item_id)
        mock_get_item.return_value = item

        cms_delete_item_service(
            token="admin_token",
            group_id=group_id,
            collection_id=collection_id,
            item_id=item_id,
        )

        mock_soft_delete.assert_called_once_with(db=mock_db, item=item)

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_item_by_id')
    def test_delete_item_not_found(
        self, mock_get_item, mock_get_collection, mock_require_create,
        mock_get_group, mock_validate, mock_session
    ):
        """Test delete item when item doesn't exist."""
        group_id = uuid4()
        collection_id = uuid4()
        item_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        
        collection = MockGroupRecitationCollection(id=collection_id, group_id=group_id)
        mock_get_collection.return_value = collection
        mock_get_item.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            cms_delete_item_service(
                token="admin_token",
                group_id=group_id,
                collection_id=collection_id,
                item_id=item_id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestCmsReorderItemsService:
    """Test cases for cms_reorder_items_service function."""

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_items')
    @patch('pecha_api.group_recitation_collection.cms_service.update_item_display_orders')
    @patch('pecha_api.group_recitation_collection.cms_service._build_items_dto')
    @pytest.mark.asyncio
    async def test_reorder_success(
        self, mock_build_items, mock_update_orders, mock_get_items, mock_get_collection,
        mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test successful reordering of items."""
        group_id = uuid4()
        collection_id = uuid4()
        item_id1 = uuid4()
        item_id2 = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        
        collection = MockGroupRecitationCollection(id=collection_id, group_id=group_id)
        mock_get_collection.return_value = collection
        
        items = [
            MockGroupRecitationCollectionItem(id=item_id1, display_order=1),
            MockGroupRecitationCollectionItem(id=item_id2, display_order=2),
        ]
        mock_get_items.return_value = items
        
        from pecha_api.group_recitation_collection.response_models import GroupRecitationCollectionItemDTO
        mock_build_items.return_value = [
            GroupRecitationCollectionItemDTO(
                id=item_id2,
                text_id=str(uuid4()),
                title="Text 2",
                language="bo",
                type="sutra",
                display_order=1,
            ),
            GroupRecitationCollectionItemDTO(
                id=item_id1,
                text_id=str(uuid4()),
                title="Text 1",
                language="bo",
                type="sutra",
                display_order=2,
            ),
        ]

        result = await cms_reorder_items_service(
            token="admin_token",
            group_id=group_id,
            collection_id=collection_id,
            item_ids=[item_id2, item_id1],
        )

        assert isinstance(result, GroupRecitationCollectionDetailDTO)
        assert len(result.items) == 2
        mock_update_orders.assert_called_once()

    @patch('pecha_api.group_recitation_collection.cms_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.cms_service.validate_and_extract_author_details')
    @patch('pecha_api.group_recitation_collection.cms_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.cms_service.require_can_create_content')
    @patch('pecha_api.group_recitation_collection.cms_service.get_collection_by_id')
    @pytest.mark.asyncio
    async def test_reorder_not_found(
        self, mock_get_collection, mock_require_create, mock_get_group, mock_validate, mock_session
    ):
        """Test reorder items when collection doesn't exist."""
        group_id = uuid4()
        collection_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate.return_value = MockAuthor()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_collection.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await cms_reorder_items_service(
                token="admin_token",
                group_id=group_id,
                collection_id=collection_id,
                item_ids=[uuid4()],
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
