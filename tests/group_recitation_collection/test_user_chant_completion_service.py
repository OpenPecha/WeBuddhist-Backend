import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import date, datetime, timezone
from fastapi import HTTPException
from starlette import status

from pecha_api.group_recitation_collection.user_chant_completion_service import (
    get_today_completions_service,
    create_chant_completion_service,
    get_completion_day_count_service,
)
from pecha_api.group_recitation_collection.user_chant_completion_response_models import (
    TodayChantCompletionsResponse,
    ChantCompletionDayCountResponse,
)


class MockUser:
    """Mock User model."""
    def __init__(self, id=None, email="test@example.com"):
        self.id = id or uuid4()
        self.email = email


class MockGroup:
    """Mock Group model."""
    def __init__(self, id=None, is_public=True):
        self.id = id or uuid4()
        self.is_public = is_public


class MockGroupMember:
    """Mock GroupMember model."""
    def __init__(self, user_id=None, group_id=None, role="MEMBER"):
        self.user_id = user_id or uuid4()
        self.group_id = group_id or uuid4()
        self.role = role


class MockCollection:
    """Mock GroupRecitationCollection model."""
    def __init__(self, id=None, group_id=None, name="Test Collection"):
        self.id = id or uuid4()
        self.group_id = group_id or uuid4()
        self.name = name


class MockCollectionItem:
    """Mock GroupRecitationCollectionItem model."""
    def __init__(self, id=None, collection_id=None):
        self.id = id or uuid4()
        self.group_recitation_collection_id = collection_id or uuid4()


class TestGetTodayCompletionsService:
    """Test cases for get_today_completions_service function."""

    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.validate_and_extract_user_details')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_user_completions_today')
    def test_get_today_completions_success(
        self,
        mock_get_completions,
        mock_get_collection,
        mock_get_group,
        mock_validate_user,
        mock_session,
    ):
        """Test successful retrieval of today's completions."""
        token = "valid_token"
        user_id = uuid4()
        group_id = uuid4()
        collection_id = uuid4()
        chant_id_1 = uuid4()
        chant_id_2 = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser(id=user_id)
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_collection.return_value = MockCollection(id=collection_id, group_id=group_id)
        mock_get_completions.return_value = [chant_id_1, chant_id_2]

        result = get_today_completions_service(
            token=token,
            group_id=group_id,
            collection_id=collection_id,
        )

        assert isinstance(result, TodayChantCompletionsResponse)
        assert len(result.completed_chant_ids) == 2
        assert chant_id_1 in result.completed_chant_ids
        assert chant_id_2 in result.completed_chant_ids
        assert result.date == date.today().isoformat()
        mock_validate_user.assert_called_once_with(token=token)
        mock_get_group.assert_called_once_with(db=mock_db, group_id=group_id)

    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.validate_and_extract_user_details')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_by_id')
    def test_get_today_completions_group_not_found(
        self,
        mock_get_group,
        mock_validate_user,
        mock_session,
    ):
        """Test error when group doesn't exist."""
        token = "valid_token"
        user_id = uuid4()
        group_id = uuid4()
        collection_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser(id=user_id)
        mock_get_group.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_today_completions_service(
                token=token,
                group_id=group_id,
                collection_id=collection_id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestGetCompletionDayCountService:
    """Test cases for get_completion_day_count_service function."""

    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.validate_and_extract_user_details')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_member')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.count_unique_completion_days')
    def test_get_day_count_success(
        self,
        mock_count_days,
        mock_get_collection,
        mock_get_member,
        mock_get_group,
        mock_validate_user,
        mock_session,
    ):
        """Test successful retrieval of unique completion day count."""
        token = "valid_token"
        user_id = uuid4()
        group_id = uuid4()
        collection_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser(id=user_id)
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_member.return_value = MockGroupMember(user_id=user_id, group_id=group_id)
        mock_get_collection.return_value = MockCollection(id=collection_id, group_id=group_id)
        mock_count_days.return_value = 7

        result = get_completion_day_count_service(
            token=token,
            group_id=group_id,
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

    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.validate_and_extract_user_details')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_by_id')
    def test_get_day_count_group_not_found(
        self,
        mock_get_group,
        mock_validate_user,
        mock_session,
    ):
        """Test error when group doesn't exist."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser()
        mock_get_group.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_completion_day_count_service(
                token="valid_token",
                group_id=uuid4(),
                collection_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.validate_and_extract_user_details')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_member')
    def test_get_day_count_not_member(
        self,
        mock_get_member,
        mock_get_group,
        mock_validate_user,
        mock_session,
    ):
        """Test error when user is not a group member."""
        group_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser()
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_member.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_completion_day_count_service(
                token="valid_token",
                group_id=group_id,
                collection_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.validate_and_extract_user_details')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_member')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_collection_by_id')
    def test_get_day_count_collection_not_found(
        self,
        mock_get_collection,
        mock_get_member,
        mock_get_group,
        mock_validate_user,
        mock_session,
    ):
        """Test error when collection doesn't exist in the group."""
        user_id = uuid4()
        group_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser(id=user_id)
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_member.return_value = MockGroupMember(user_id=user_id, group_id=group_id)
        mock_get_collection.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_completion_day_count_service(
                token="valid_token",
                group_id=group_id,
                collection_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestCreateChantCompletionService:
    """Test cases for create_chant_completion_service function."""

    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.validate_and_extract_user_details')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_collection_item_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.check_completion_exists')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.create_chant_completion')
    def test_create_completion_success(
        self,
        mock_create_completion,
        mock_check_exists,
        mock_get_item,
        mock_get_collection,
        mock_get_group,
        mock_validate_user,
        mock_session,
    ):
        """Test successful creation of chant completion."""
        token = "valid_token"
        user_id = uuid4()
        group_id = uuid4()
        collection_id = uuid4()
        chant_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser(id=user_id)
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_collection.return_value = MockCollection(id=collection_id, group_id=group_id)
        mock_get_item.return_value = MockCollectionItem(id=chant_id, collection_id=collection_id)
        mock_check_exists.return_value = False

        create_chant_completion_service(
            token=token,
            group_id=group_id,
            collection_id=collection_id,
            chant_id=chant_id,
        )

        mock_create_completion.assert_called_once()
        call_args = mock_create_completion.call_args
        assert call_args.kwargs['user_id'] == user_id
        assert call_args.kwargs['chant_id'] == chant_id
        assert call_args.kwargs['collection_id'] == collection_id
        assert call_args.kwargs['completion_date'] == date.today()

    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.validate_and_extract_user_details')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_collection_item_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.check_completion_exists')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.create_chant_completion')
    def test_create_completion_idempotent(
        self,
        mock_create_completion,
        mock_check_exists,
        mock_get_item,
        mock_get_collection,
        mock_get_group,
        mock_validate_user,
        mock_session,
    ):
        """Test idempotent behavior when already completed today."""
        token = "valid_token"
        user_id = uuid4()
        group_id = uuid4()
        collection_id = uuid4()
        chant_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser(id=user_id)
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_collection.return_value = MockCollection(id=collection_id, group_id=group_id)
        mock_get_item.return_value = MockCollectionItem(id=chant_id, collection_id=collection_id)
        mock_check_exists.return_value = True

        create_chant_completion_service(
            token=token,
            group_id=group_id,
            collection_id=collection_id,
            chant_id=chant_id,
        )

        mock_create_completion.assert_not_called()

    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.SessionLocal')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.validate_and_extract_user_details')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_group_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_collection_by_id')
    @patch('pecha_api.group_recitation_collection.user_chant_completion_service.get_collection_item_by_id')
    def test_create_completion_chant_not_in_collection(
        self,
        mock_get_item,
        mock_get_collection,
        mock_get_group,
        mock_validate_user,
        mock_session,
    ):
        """Test error when chant doesn't exist in collection."""
        token = "valid_token"
        user_id = uuid4()
        group_id = uuid4()
        collection_id = uuid4()
        chant_id = uuid4()

        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_validate_user.return_value = MockUser(id=user_id)
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_get_collection.return_value = MockCollection(id=collection_id, group_id=group_id)
        mock_get_item.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            create_chant_completion_service(
                token=token,
                group_id=group_id,
                collection_id=collection_id,
                chant_id=chant_id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
