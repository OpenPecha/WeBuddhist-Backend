import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import date
from fastapi import HTTPException
from starlette import status

from pecha_api.plans.users.recitation_collection.recitation_collection_completion_service import (
    get_today_completions_service,
    create_chant_completion_service,
    get_completion_day_count_service,
)
from pecha_api.plans.users.recitation_collection.recitation_collection_completion_response_models import (
    TodayChantCompletionsResponse,
    ChantCompletionDayCountResponse,
)


class MockUser:
    """Mock User model."""
    def __init__(self, id=None, email="test@example.com"):
        self.id = id or uuid4()
        self.email = email


class MockCollection:
    """Mock RecitationCollection model."""
    def __init__(self, id=None, user_id=None, name="Test Collection"):
        self.id = id or uuid4()
        self.user_id = user_id or uuid4()
        self.name = name


class MockCollectionItem:
    """Mock RecitationCollectionItem model."""
    def __init__(self, id=None, collection_id=None):
        self.id = id or uuid4()
        self.recitation_collection_id = collection_id or uuid4()


MODULE = "pecha_api.plans.users.recitation_collection.recitation_collection_completion_service"


class TestGetTodayCompletionsService:
    """Test cases for get_today_completions_service function."""

    @patch(f'{MODULE}.SessionLocal')
    @patch(f'{MODULE}.validate_and_extract_user_details')
    @patch(f'{MODULE}.get_collection_by_id')
    @patch(f'{MODULE}.get_user_completions_today')
    def test_get_today_completions_success(
        self,
        mock_get_completions,
        mock_get_collection,
        mock_validate_user,
        mock_session,
    ):
        """Test successful retrieval of today's completions."""
        token = "valid_token"
        user_id = uuid4()
        collection_id = uuid4()
        chant_id_1 = uuid4()
        chant_id_2 = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser(id=user_id)
        mock_get_collection.return_value = MockCollection(id=collection_id, user_id=user_id)
        mock_get_completions.return_value = [chant_id_1, chant_id_2]

        result = get_today_completions_service(
            token=token,
            collection_id=collection_id,
        )

        assert isinstance(result, TodayChantCompletionsResponse)
        assert len(result.completed_chant_ids) == 2
        assert chant_id_1 in result.completed_chant_ids
        assert chant_id_2 in result.completed_chant_ids
        assert result.date == date.today().isoformat()
        mock_validate_user.assert_called_once_with(token=token)
        mock_get_collection.assert_called_once_with(db=mock_db, collection_id=collection_id, user_id=user_id)

    @patch(f'{MODULE}.SessionLocal')
    @patch(f'{MODULE}.validate_and_extract_user_details')
    @patch(f'{MODULE}.get_collection_by_id')
    def test_get_today_completions_collection_not_found(
        self,
        mock_get_collection,
        mock_validate_user,
        mock_session,
    ):
        """Test error when the collection doesn't exist or isn't owned by the user."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser()
        mock_get_collection.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_today_completions_service(
                token="valid_token",
                collection_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestGetCompletionDayCountService:
    """Test cases for get_completion_day_count_service function."""

    @patch(f'{MODULE}.SessionLocal')
    @patch(f'{MODULE}.validate_and_extract_user_details')
    @patch(f'{MODULE}.get_collection_by_id')
    @patch(f'{MODULE}.count_unique_completion_days')
    def test_get_day_count_success(
        self,
        mock_count_days,
        mock_get_collection,
        mock_validate_user,
        mock_session,
    ):
        """Test successful retrieval of unique completion day count."""
        token = "valid_token"
        user_id = uuid4()
        collection_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser(id=user_id)
        mock_get_collection.return_value = MockCollection(id=collection_id, user_id=user_id)
        mock_count_days.return_value = 7

        result = get_completion_day_count_service(
            token=token,
            collection_id=collection_id,
        )

        assert isinstance(result, ChantCompletionDayCountResponse)
        assert result.collection_id == collection_id
        assert result.day_count == 7
        mock_count_days.assert_called_once_with(
            db=mock_db,
            user_id=user_id,
            collection_id=collection_id,
        )

    @patch(f'{MODULE}.SessionLocal')
    @patch(f'{MODULE}.validate_and_extract_user_details')
    @patch(f'{MODULE}.get_collection_by_id')
    def test_get_day_count_collection_not_found(
        self,
        mock_get_collection,
        mock_validate_user,
        mock_session,
    ):
        """Test error when collection doesn't exist."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser()
        mock_get_collection.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_completion_day_count_service(
                token="valid_token",
                collection_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestCreateChantCompletionService:
    """Test cases for create_chant_completion_service function."""

    @patch(f'{MODULE}.SessionLocal')
    @patch(f'{MODULE}.validate_and_extract_user_details')
    @patch(f'{MODULE}.get_collection_by_id')
    @patch(f'{MODULE}.get_collection_item_by_id')
    @patch(f'{MODULE}.check_completion_exists')
    @patch(f'{MODULE}.create_chant_completion')
    def test_create_completion_success(
        self,
        mock_create_completion,
        mock_check_exists,
        mock_get_item,
        mock_get_collection,
        mock_validate_user,
        mock_session,
    ):
        """Test successful creation of chant completion."""
        token = "valid_token"
        user_id = uuid4()
        collection_id = uuid4()
        chant_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser(id=user_id)
        mock_get_collection.return_value = MockCollection(id=collection_id, user_id=user_id)
        mock_get_item.return_value = MockCollectionItem(id=chant_id, collection_id=collection_id)
        mock_check_exists.return_value = False

        create_chant_completion_service(
            token=token,
            collection_id=collection_id,
            chant_id=chant_id,
        )

        mock_create_completion.assert_called_once()
        call_args = mock_create_completion.call_args
        assert call_args.kwargs['user_id'] == user_id
        assert call_args.kwargs['chant_id'] == chant_id
        assert call_args.kwargs['collection_id'] == collection_id
        assert call_args.kwargs['completion_date'] == date.today()

    @patch(f'{MODULE}.SessionLocal')
    @patch(f'{MODULE}.validate_and_extract_user_details')
    @patch(f'{MODULE}.get_collection_by_id')
    @patch(f'{MODULE}.get_collection_item_by_id')
    @patch(f'{MODULE}.check_completion_exists')
    @patch(f'{MODULE}.create_chant_completion')
    def test_create_completion_idempotent(
        self,
        mock_create_completion,
        mock_check_exists,
        mock_get_item,
        mock_get_collection,
        mock_validate_user,
        mock_session,
    ):
        """Test idempotent behavior when already completed today."""
        collection_id = uuid4()
        chant_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser()
        mock_get_collection.return_value = MockCollection(id=collection_id)
        mock_get_item.return_value = MockCollectionItem(id=chant_id, collection_id=collection_id)
        mock_check_exists.return_value = True

        create_chant_completion_service(
            token="valid_token",
            collection_id=collection_id,
            chant_id=chant_id,
        )

        mock_create_completion.assert_not_called()

    @patch(f'{MODULE}.SessionLocal')
    @patch(f'{MODULE}.validate_and_extract_user_details')
    @patch(f'{MODULE}.get_collection_by_id')
    @patch(f'{MODULE}.get_collection_item_by_id')
    def test_create_completion_chant_not_in_collection(
        self,
        mock_get_item,
        mock_get_collection,
        mock_validate_user,
        mock_session,
    ):
        """Test error when chant doesn't exist in collection."""
        collection_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser()
        mock_get_collection.return_value = MockCollection(id=collection_id)
        mock_get_item.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            create_chant_completion_service(
                token="valid_token",
                collection_id=collection_id,
                chant_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch(f'{MODULE}.SessionLocal')
    @patch(f'{MODULE}.validate_and_extract_user_details')
    @patch(f'{MODULE}.get_collection_by_id')
    def test_create_completion_collection_not_found(
        self,
        mock_get_collection,
        mock_validate_user,
        mock_session,
    ):
        """Test error when collection doesn't exist or isn't owned by the user."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser()
        mock_get_collection.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            create_chant_completion_service(
                token="valid_token",
                collection_id=uuid4(),
                chant_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
