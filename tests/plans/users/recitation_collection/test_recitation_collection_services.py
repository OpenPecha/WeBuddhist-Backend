import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from fastapi import HTTPException
from starlette import status

from pecha_api.plans.users.recitation_collection.recitation_collection_service import (
    get_user_collections_service,
    get_collection_detail_service,
    create_collection_service,
    add_items_to_collection_service
)
from pecha_api.plans.users.recitation_collection.recitation_collection_response_models import (
    RecitationCollectionsResponse,
    RecitationCollectionDTO,
    RecitationCollectionDetailDTO,
    RecitationCollectionItemDTO,
    CreateCollectionRequest,
    CreateCollectionResponse,
    AddItemsRequest,
    AddItemsResponse
)


class MockUser:
    def __init__(self, id=None):
        self.id = id or uuid4()


class MockCollection:
    def __init__(self, id=None, user_id=None, name="Test Collection", img_url="images/test.jpg", created_at="2025-06-09T10:00:00", updated_at="2025-06-09T10:00:00"):
        self.id = id or uuid4()
        self.user_id = user_id or uuid4()
        self.name = name
        self.img_url = img_url
        self.created_at = created_at
        self.updated_at = updated_at


class MockCollectionItem:
    def __init__(self, id=None, recitation_collection_id=None, text_id=None, display_order=1):
        self.id = id or uuid4()
        self.recitation_collection_id = recitation_collection_id or uuid4()
        self.text_id = text_id or uuid4()
        self.display_order = display_order


class MockTextDTO:
    def __init__(self, title="Test Text", language="bo", type="root_text"):
        self.title = title
        self.language = language
        self.type = type


class TestGetUserCollectionsService:

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_user_collections')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_item_counts')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service._generate_presigned_url')
    @pytest.mark.asyncio
    async def test_get_user_collections_success(
        self,
        mock_presigned_url,
        mock_item_counts,
        mock_get_collections,
        mock_session,
        mock_validate
    ):
        user_id = uuid4()
        collection_id_1 = uuid4()
        collection_id_2 = uuid4()

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        collections = [
            MockCollection(id=collection_id_1, name="Morning Prayers"),
            MockCollection(id=collection_id_2, name="Evening Prayers")
        ]
        mock_get_collections.return_value = (collections, 2)
        mock_item_counts.return_value = {collection_id_1: 5, collection_id_2: 3}
        mock_presigned_url.return_value = "https://presigned-url.com/image.jpg"

        result = await get_user_collections_service(token="valid_token", skip=0, limit=20)

        assert isinstance(result, RecitationCollectionsResponse)
        assert len(result.collections) == 2
        assert result.collections[0].name == "Morning Prayers"
        assert result.collections[0].item_count == 5
        assert result.collections[1].name == "Evening Prayers"
        assert result.collections[1].item_count == 3
        assert result.total == 2

        mock_validate.assert_called_once_with(token="valid_token")
        mock_get_collections.assert_called_once_with(db=mock_db, user_id=user_id, skip=0, limit=20)

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_user_collections')
    @pytest.mark.asyncio
    async def test_get_user_collections_empty(
        self,
        mock_get_collections,
        mock_session,
        mock_validate
    ):
        user_id = uuid4()
        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_collections.return_value = ([], 0)

        result = await get_user_collections_service(token="valid_token", skip=0, limit=20)

        assert isinstance(result, RecitationCollectionsResponse)
        assert len(result.collections) == 0
        assert result.total == 0

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_get_user_collections_invalid_token(self, mock_validate):
        mock_validate.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_user_collections_service(token="invalid_token", skip=0, limit=20)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_user_collections')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_item_counts')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service._generate_presigned_url')
    @pytest.mark.asyncio
    async def test_get_user_collections_with_pagination(
        self,
        mock_presigned_url,
        mock_item_counts,
        mock_get_collections,
        mock_session,
        mock_validate
    ):
        user_id = uuid4()
        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        collections = [MockCollection(name=f"Collection {i}") for i in range(5)]
        mock_get_collections.return_value = (collections, 25)
        mock_item_counts.return_value = {c.id: 2 for c in collections}
        mock_presigned_url.return_value = "https://presigned-url.com/image.jpg"

        result = await get_user_collections_service(token="valid_token", skip=10, limit=5)

        assert len(result.collections) == 5
        assert result.skip == 10
        assert result.limit == 5
        assert result.total == 25

        mock_get_collections.assert_called_once_with(db=mock_db, user_id=user_id, skip=10, limit=5)


class TestGetCollectionDetailService:

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_by_id')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_items')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_texts_by_ids')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service._generate_presigned_url')
    @pytest.mark.asyncio
    async def test_get_collection_detail_success(
        self,
        mock_presigned_url,
        mock_get_texts,
        mock_get_items,
        mock_get_collection,
        mock_session,
        mock_validate
    ):
        user_id = uuid4()
        collection_id = uuid4()
        text_id_1 = uuid4()
        text_id_2 = uuid4()

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_collection = MockCollection(id=collection_id, name="Morning Prayers")
        mock_get_collection.return_value = mock_collection

        items = [
            MockCollectionItem(text_id=text_id_1, display_order=1),
            MockCollectionItem(text_id=text_id_2, display_order=2)
        ]
        mock_get_items.return_value = items

        mock_get_texts.return_value = {
            str(text_id_1): MockTextDTO(title="Heart Sutra", language="bo"),
            str(text_id_2): MockTextDTO(title="Diamond Sutra", language="en")
        }
        mock_presigned_url.return_value = "https://presigned-url.com/image.jpg"

        result = await get_collection_detail_service(token="valid_token", collection_id=collection_id)

        assert isinstance(result, RecitationCollectionDetailDTO)
        assert result.id == collection_id
        assert result.name == "Morning Prayers"
        assert len(result.items) == 2
        assert result.items[0].title == "Heart Sutra"
        assert result.items[1].title == "Diamond Sutra"

        mock_validate.assert_called_once_with(token="valid_token")
        mock_get_collection.assert_called_once_with(db=mock_db, collection_id=collection_id, user_id=user_id)

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_by_id')
    @pytest.mark.asyncio
    async def test_get_collection_detail_not_found(
        self,
        mock_get_collection,
        mock_session,
        mock_validate
    ):
        user_id = uuid4()
        collection_id = uuid4()

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_collection.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_collection_detail_service(token="valid_token", collection_id=collection_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_by_id')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_items')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service._generate_presigned_url')
    @pytest.mark.asyncio
    async def test_get_collection_detail_empty_items(
        self,
        mock_presigned_url,
        mock_get_items,
        mock_get_collection,
        mock_session,
        mock_validate
    ):
        user_id = uuid4()
        collection_id = uuid4()

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_collection = MockCollection(id=collection_id, name="Empty Collection")
        mock_get_collection.return_value = mock_collection
        mock_get_items.return_value = []
        mock_presigned_url.return_value = "https://presigned-url.com/image.jpg"

        result = await get_collection_detail_service(token="valid_token", collection_id=collection_id)

        assert isinstance(result, RecitationCollectionDetailDTO)
        assert result.name == "Empty Collection"
        assert len(result.items) == 0

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_get_collection_detail_invalid_token(self, mock_validate):
        collection_id = uuid4()

        mock_validate.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_collection_detail_service(token="invalid_token", collection_id=collection_id)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_by_id')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_items')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_texts_by_ids')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service._generate_presigned_url')
    @pytest.mark.asyncio
    async def test_get_collection_detail_filters_missing_texts(
        self,
        mock_presigned_url,
        mock_get_texts,
        mock_get_items,
        mock_get_collection,
        mock_session,
        mock_validate
    ):
        user_id = uuid4()
        collection_id = uuid4()
        text_id_1 = uuid4()
        text_id_2 = uuid4()

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_collection = MockCollection(id=collection_id, name="Test Collection")
        mock_get_collection.return_value = mock_collection

        items = [
            MockCollectionItem(text_id=text_id_1, display_order=1),
            MockCollectionItem(text_id=text_id_2, display_order=2)
        ]
        mock_get_items.return_value = items

        mock_get_texts.return_value = {
            str(text_id_1): MockTextDTO(title="Heart Sutra")
        }
        mock_presigned_url.return_value = "https://presigned-url.com/image.jpg"

        result = await get_collection_detail_service(token="valid_token", collection_id=collection_id)

        assert len(result.items) == 1
        assert result.items[0].title == "Heart Sutra"


class TestCreateCollectionService:

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.save_collection')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service._generate_presigned_url')
    @pytest.mark.asyncio
    async def test_create_collection_success(
        self,
        mock_presigned_url,
        mock_save_collection,
        mock_session,
        mock_validate
    ):
        """Test successful collection creation"""
        user_id = uuid4()
        collection_id = uuid4()

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        saved_collection = MockCollection(
            id=collection_id,
            user_id=user_id,
            name="Morning Prayers",
            img_url="images/collections/test.jpg"
        )
        mock_save_collection.return_value = saved_collection
        mock_presigned_url.return_value = "https://presigned-url.com/test.jpg"

        request = CreateCollectionRequest(name="Morning Prayers", img_url="images/collections/test.jpg")
        result = await create_collection_service(token="valid_token", request=request)

        assert isinstance(result, CreateCollectionResponse)
        assert result.id == collection_id
        assert result.name == "Morning Prayers"
        assert result.img_url == "https://presigned-url.com/test.jpg"

        mock_validate.assert_called_once_with(token="valid_token")
        mock_save_collection.assert_called_once()

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.save_collection')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service._generate_presigned_url')
    @pytest.mark.asyncio
    async def test_create_collection_without_image(
        self,
        mock_presigned_url,
        mock_save_collection,
        mock_session,
        mock_validate
    ):
        """Test creating collection without image URL"""
        user_id = uuid4()
        collection_id = uuid4()

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        saved_collection = MockCollection(
            id=collection_id,
            user_id=user_id,
            name="No Image Collection",
            img_url=""
        )
        mock_save_collection.return_value = saved_collection
        mock_presigned_url.return_value = None

        request = CreateCollectionRequest(name="No Image Collection", img_url="")
        result = await create_collection_service(token="valid_token", request=request)

        assert result.name == "No Image Collection"
        assert result.img_url is None

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_create_collection_invalid_token(self, mock_validate):
        """Test creating collection with invalid token"""
        mock_validate.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

        request = CreateCollectionRequest(name="Test Collection", img_url="images/test.jpg")

        with pytest.raises(HTTPException) as exc_info:
            await create_collection_service(token="invalid_token", request=request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.save_collection')
    @pytest.mark.asyncio
    async def test_create_collection_database_error(
        self,
        mock_save_collection,
        mock_session,
        mock_validate
    ):
        """Test database error during collection creation"""
        user_id = uuid4()
        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_save_collection.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": "Database error"}
        )

        request = CreateCollectionRequest(name="Test Collection", img_url="images/test.jpg")

        with pytest.raises(HTTPException) as exc_info:
            await create_collection_service(token="valid_token", request=request)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.save_collection')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service._generate_presigned_url')
    @pytest.mark.asyncio
    async def test_create_collection_with_special_characters(
        self,
        mock_presigned_url,
        mock_save_collection,
        mock_session,
        mock_validate
    ):
        """Test creating collection with special characters and Tibetan text"""
        user_id = uuid4()
        collection_id = uuid4()
        special_name = "Morning Prayers 🙏 - དུས་གསུམ་སངས་རྒྱས།"

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        saved_collection = MockCollection(
            id=collection_id,
            user_id=user_id,
            name=special_name,
            img_url="images/test.jpg"
        )
        mock_save_collection.return_value = saved_collection
        mock_presigned_url.return_value = "https://presigned-url.com/test.jpg"

        request = CreateCollectionRequest(name=special_name, img_url="images/test.jpg")
        result = await create_collection_service(token="valid_token", request=request)

        assert result.name == special_name


class TestAddItemsToCollectionService:

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_by_id')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.TextUtils.validate_text_exists')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_max_display_order_for_collection')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.save_collection_items')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_texts_by_ids')
    @pytest.mark.asyncio
    async def test_add_items_single_success(
        self,
        mock_get_texts,
        mock_save_items,
        mock_max_order,
        mock_validate_text,
        mock_get_collection,
        mock_session,
        mock_validate
    ):
        """Test successfully adding single item to collection"""
        user_id = uuid4()
        collection_id = uuid4()
        text_id = uuid4()

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_collection = MockCollection(id=collection_id, user_id=user_id)
        mock_get_collection.return_value = mock_collection

        mock_validate_text.return_value = None
        mock_max_order.return_value = 0

        saved_item = MockCollectionItem(
            recitation_collection_id=collection_id,
            text_id=text_id,
            display_order=1
        )
        mock_save_items.return_value = [saved_item]

        mock_get_texts.return_value = {
            str(text_id): MockTextDTO(title="Heart Sutra", language="bo", type="root_text")
        }

        request = AddItemsRequest(text_ids=[text_id])
        result = await add_items_to_collection_service(
            token="valid_token",
            collection_id=collection_id,
            request=request
        )

        assert isinstance(result, AddItemsResponse)
        assert result.collection_id == collection_id
        assert result.added_count == 1
        assert len(result.items) == 1
        assert result.items[0].title == "Heart Sutra"
        assert result.items[0].display_order == 1

        mock_validate.assert_called_once_with(token="valid_token")
        mock_get_collection.assert_called_once_with(db=mock_db, collection_id=collection_id, user_id=user_id)

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_by_id')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.TextUtils.validate_text_exists')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_max_display_order_for_collection')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.save_collection_items')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_texts_by_ids')
    @pytest.mark.asyncio
    async def test_add_items_multiple_success(
        self,
        mock_get_texts,
        mock_save_items,
        mock_max_order,
        mock_validate_text,
        mock_get_collection,
        mock_session,
        mock_validate
    ):
        """Test successfully adding multiple items to collection"""
        user_id = uuid4()
        collection_id = uuid4()
        text_ids = [uuid4(), uuid4(), uuid4()]

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_collection = MockCollection(id=collection_id, user_id=user_id)
        mock_get_collection.return_value = mock_collection

        mock_validate_text.return_value = None
        mock_max_order.return_value = 0

        saved_items = [
            MockCollectionItem(recitation_collection_id=collection_id, text_id=text_ids[i], display_order=i+1)
            for i in range(3)
        ]
        mock_save_items.return_value = saved_items

        mock_get_texts.return_value = {
            str(text_ids[0]): MockTextDTO(title="Text 1", language="bo", type="root_text"),
            str(text_ids[1]): MockTextDTO(title="Text 2", language="en", type="translation"),
            str(text_ids[2]): MockTextDTO(title="Text 3", language="sa", type="commentary")
        }

        request = AddItemsRequest(text_ids=text_ids)
        result = await add_items_to_collection_service(
            token="valid_token",
            collection_id=collection_id,
            request=request
        )

        assert result.added_count == 3
        assert len(result.items) == 3
        assert result.items[0].display_order == 1
        assert result.items[2].display_order == 3

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_by_id')
    @pytest.mark.asyncio
    async def test_add_items_collection_not_found(
        self,
        mock_get_collection,
        mock_session,
        mock_validate
    ):
        """Test adding items to non-existent collection"""
        user_id = uuid4()
        collection_id = uuid4()
        text_id = uuid4()

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_get_collection.return_value = None

        request = AddItemsRequest(text_ids=[text_id])

        with pytest.raises(HTTPException) as exc_info:
            await add_items_to_collection_service(
                token="valid_token",
                collection_id=collection_id,
                request=request
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_by_id')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.TextUtils.validate_text_exists')
    @pytest.mark.asyncio
    async def test_add_items_text_not_found(
        self,
        mock_validate_text,
        mock_get_collection,
        mock_session,
        mock_validate
    ):
        """Test adding non-existent text to collection"""
        user_id = uuid4()
        collection_id = uuid4()
        text_id = uuid4()

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_collection = MockCollection(id=collection_id, user_id=user_id)
        mock_get_collection.return_value = mock_collection

        mock_validate_text.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": f"Text with ID {text_id} not found"}
        )

        request = AddItemsRequest(text_ids=[text_id])

        with pytest.raises(HTTPException) as exc_info:
            await add_items_to_collection_service(
                token="valid_token",
                collection_id=collection_id,
                request=request
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_add_items_invalid_token(self, mock_validate):
        """Test adding items with invalid token"""
        collection_id = uuid4()
        text_id = uuid4()

        mock_validate.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

        request = AddItemsRequest(text_ids=[text_id])

        with pytest.raises(HTTPException) as exc_info:
            await add_items_to_collection_service(
                token="invalid_token",
                collection_id=collection_id,
                request=request
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_by_id')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.TextUtils.validate_text_exists')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_max_display_order_for_collection')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.save_collection_items')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_texts_by_ids')
    @pytest.mark.asyncio
    async def test_add_items_display_order_continuation(
        self,
        mock_get_texts,
        mock_save_items,
        mock_max_order,
        mock_validate_text,
        mock_get_collection,
        mock_session,
        mock_validate
    ):
        """Test that display order continues from existing items"""
        user_id = uuid4()
        collection_id = uuid4()
        text_ids = [uuid4(), uuid4()]

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_collection = MockCollection(id=collection_id, user_id=user_id)
        mock_get_collection.return_value = mock_collection

        mock_validate_text.return_value = None
        mock_max_order.return_value = 10

        saved_items = [
            MockCollectionItem(recitation_collection_id=collection_id, text_id=text_ids[0], display_order=11),
            MockCollectionItem(recitation_collection_id=collection_id, text_id=text_ids[1], display_order=12)
        ]
        mock_save_items.return_value = saved_items

        mock_get_texts.return_value = {
            str(text_ids[0]): MockTextDTO(title="Text 1"),
            str(text_ids[1]): MockTextDTO(title="Text 2")
        }

        request = AddItemsRequest(text_ids=text_ids)
        result = await add_items_to_collection_service(
            token="valid_token",
            collection_id=collection_id,
            request=request
        )

        assert result.items[0].display_order == 11
        assert result.items[1].display_order == 12

    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.validate_and_extract_user_details')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.SessionLocal')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_collection_by_id')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.TextUtils.validate_text_exists')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.get_max_display_order_for_collection')
    @patch('pecha_api.plans.users.recitation_collection.recitation_collection_service.save_collection_items')
    @pytest.mark.asyncio
    async def test_add_items_duplicate_error(
        self,
        mock_save_items,
        mock_max_order,
        mock_validate_text,
        mock_get_collection,
        mock_session,
        mock_validate
    ):
        """Test duplicate item error handling"""
        user_id = uuid4()
        collection_id = uuid4()
        text_id = uuid4()

        mock_validate.return_value = MockUser(id=user_id)

        mock_db = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_db)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        mock_collection = MockCollection(id=collection_id, user_id=user_id)
        mock_get_collection.return_value = mock_collection

        mock_validate_text.return_value = None
        mock_max_order.return_value = 5

        mock_save_items.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": "duplicate key value violates unique constraint"}
        )

        request = AddItemsRequest(text_ids=[text_id])

        with pytest.raises(HTTPException) as exc_info:
            await add_items_to_collection_service(
                token="valid_token",
                collection_id=collection_id,
                request=request
            )

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
