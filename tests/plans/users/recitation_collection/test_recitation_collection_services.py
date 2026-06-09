import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from fastapi import HTTPException
from starlette import status

from pecha_api.plans.users.recitation_collection.recitation_collection_service import (
    get_user_collections_service,
    get_collection_detail_service
)
from pecha_api.plans.users.recitation_collection.recitation_collection_response_models import (
    RecitationCollectionsResponse,
    RecitationCollectionDTO,
    RecitationCollectionDetailDTO,
    RecitationCollectionItemDTO
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
