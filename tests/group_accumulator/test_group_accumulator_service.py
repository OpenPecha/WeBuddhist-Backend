import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
from starlette import status

from pecha_api.group_accumulator.group_accumulator_service import (
    create_group_accumulator_service,
    get_group_accumulators_service,
    get_group_accumulator_service,
    update_group_accumulator_service,
    delete_group_accumulator_service,
    submit_group_count_service,
    get_group_accumulator_history_service,
    create_group_accumulator_cms_service,
    get_group_accumulators_cms_service,
    get_group_accumulator_cms_service,
    update_group_accumulator_cms_service,
    delete_group_accumulator_cms_service,
    delete_group_accumulator_user_service,
    join_group_accumulator_service,
    get_group_accumulator_members_service,
)
from pecha_api.group_accumulator.group_accumulator_response_models import (
    CreateGroupAccumulatorRequest,
    UpdateGroupAccumulatorRequest,
    SubmitGroupCountRequest,
)


class MockGroupAccumulator:
    """Mock GroupAccumulator model."""
    def __init__(self, id=None, group_id=None, accumulator_id=None, title=None, image_key=None, target_count=108000):
        self.id = id or uuid4()
        self.group_id = group_id or uuid4()
        self.accumulator_id = accumulator_id
        self.title = title
        self.image_key = image_key
        self.target_count = target_count
        self.start_date = datetime.utcnow()
        self.end_date = None
        self.created_at = datetime.utcnow()
        self.updated_at = None


class MockGroupAccumulatorHistory:
    """Mock GroupAccumulatorHistory model."""
    def __init__(self, id=None, group_accumulator_id=None, user_id=None, count=100):
        self.id = id or uuid4()
        self.group_accumulator_id = group_accumulator_id or uuid4()
        self.user_id = user_id or uuid4()
        self.count = count
        self.created_at = datetime.utcnow()


class MockUser:
    """Mock User model."""
    def __init__(self, id=None, email="test@example.com", username="testuser"):
        self.id = id or uuid4()
        self.email = email
        self.username = username


class TestCreateGroupAccumulatorService:
    """Test cases for create_group_accumulator_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.verify_group_exists')
    @patch('pecha_api.group_accumulator.group_accumulator_service.create_group_accumulator')
    def test_create_group_accumulator_success(self, mock_create, mock_verify, mock_session):
        """Test successful creation of group accumulator."""
        group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_verify.return_value = True
        mock_accumulator = MockGroupAccumulator(group_id=group_id, accumulator_id=accumulator_id)
        mock_create.return_value = mock_accumulator

        request = CreateGroupAccumulatorRequest(
            accumulator_id=accumulator_id,
            target_count=108000,
            start_date=datetime.utcnow(),
            end_date=None,
        )

        result = create_group_accumulator_service(group_id=group_id, request=request)

        assert result.id == mock_accumulator.id
        assert result.group_id == group_id
        assert result.accumulator_id == accumulator_id
        assert result.target_count == 108000
        mock_verify.assert_called_once_with(mock_db, group_id)
        mock_create.assert_called_once()

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.verify_group_exists')
    def test_create_group_accumulator_group_not_found(self, mock_verify, mock_session):
        """Test create group accumulator when group doesn't exist."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_verify.return_value = False

        request = CreateGroupAccumulatorRequest(
            target_count=108000,
        )

        with pytest.raises(HTTPException) as exc_info:
            create_group_accumulator_service(group_id=group_id, request=request)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail["error"] == "NOT_FOUND"


class TestGetGroupAccumulatorsService:
    """Test cases for get_group_accumulators_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulators')
    def test_get_group_accumulators_success(self, mock_get, mock_session):
        """Test successful retrieval of group accumulators."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_accumulators = [
            MockGroupAccumulator(group_id=group_id),
            MockGroupAccumulator(group_id=group_id),
        ]
        mock_get.return_value = (mock_accumulators, 2)

        result = get_group_accumulators_service(group_id=group_id, skip=0, limit=20)

        assert len(result.accumulators) == 2
        assert result.total == 2
        assert result.skip == 0
        assert result.limit == 20
        mock_get.assert_called_once_with(mock_db, group_id, 0, 20)

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulators')
    def test_get_group_accumulators_empty(self, mock_get, mock_session):
        """Test get group accumulators when no accumulators exist."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get.return_value = ([], 0)

        result = get_group_accumulators_service(group_id=group_id)

        assert len(result.accumulators) == 0
        assert result.total == 0


class TestGetGroupAccumulatorService:
    """Test cases for get_group_accumulator_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_joiners_count')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_count_in_range')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_total_count')
    def test_get_group_accumulator_success(
        self, mock_total, mock_today, mock_joiners_count, mock_get, mock_session
    ):
        """Test successful retrieval of group accumulator."""
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_accumulator = MockGroupAccumulator(id=accumulator_id)
        mock_get.return_value = mock_accumulator
        mock_total.return_value = 5000
        mock_today.return_value = 108
        mock_joiners_count.return_value = 12

        result = get_group_accumulator_service(group_accumulator_id=accumulator_id)

        assert result.id == accumulator_id
        assert result.total_count == 5000
        assert result.total_today_count == 108
        assert result.member_count == 12
        mock_get.assert_called_once_with(mock_db, accumulator_id)
        mock_total.assert_called_once_with(mock_db, accumulator_id)

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_get_group_accumulator_not_found(self, mock_get, mock_session):
        """Test get group accumulator when it doesn't exist."""
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_group_accumulator_service(group_accumulator_id=accumulator_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail["error"] == "NOT_FOUND"


class TestUpdateGroupAccumulatorService:
    """Test cases for update_group_accumulator_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.update_group_accumulator')
    def test_update_group_accumulator_success(self, mock_update, mock_get, mock_session):
        """Test successful update of group accumulator."""
        group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_accumulator = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_get.return_value = mock_accumulator
        mock_update.return_value = mock_accumulator

        request = UpdateGroupAccumulatorRequest(
            target_count=216000,
        )

        result = update_group_accumulator_service(
            group_id=group_id,
            group_accumulator_id=accumulator_id,
            request=request,
        )

        assert result.id == accumulator_id
        mock_get.assert_called_once_with(mock_db, accumulator_id)
        mock_update.assert_called_once()

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_update_group_accumulator_not_found(self, mock_get, mock_session):
        """Test update group accumulator when it doesn't exist."""
        group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get.return_value = None

        request = UpdateGroupAccumulatorRequest(
            target_count=216000,
        )

        with pytest.raises(HTTPException) as exc_info:
            update_group_accumulator_service(
                group_id=group_id,
                group_accumulator_id=accumulator_id,
                request=request,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_update_group_accumulator_wrong_group(self, mock_get, mock_session):
        """Test update group accumulator when it belongs to different group."""
        group_id = uuid4()
        different_group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_accumulator = MockGroupAccumulator(id=accumulator_id, group_id=different_group_id)
        mock_get.return_value = mock_accumulator

        request = UpdateGroupAccumulatorRequest(
            target_count=216000,
        )

        with pytest.raises(HTTPException) as exc_info:
            update_group_accumulator_service(
                group_id=group_id,
                group_accumulator_id=accumulator_id,
                request=request,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail["error"] == "FORBIDDEN"


class TestDeleteGroupAccumulatorService:
    """Test cases for delete_group_accumulator_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.delete_group_accumulator')
    def test_delete_group_accumulator_success(self, mock_delete, mock_get, mock_session):
        """Test successful deletion of group accumulator."""
        group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_accumulator = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_get.return_value = mock_accumulator

        delete_group_accumulator_service(
            group_id=group_id,
            group_accumulator_id=accumulator_id,
        )

        mock_get.assert_called_once_with(mock_db, accumulator_id)
        mock_delete.assert_called_once_with(mock_db, mock_accumulator)

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_delete_group_accumulator_not_found(self, mock_get, mock_session):
        """Test delete group accumulator when it doesn't exist."""
        group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            delete_group_accumulator_service(
                group_id=group_id,
                group_accumulator_id=accumulator_id,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_delete_group_accumulator_wrong_group(self, mock_get, mock_session):
        """Test delete group accumulator when it belongs to different group."""
        group_id = uuid4()
        different_group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_accumulator = MockGroupAccumulator(id=accumulator_id, group_id=different_group_id)
        mock_get.return_value = mock_accumulator

        with pytest.raises(HTTPException) as exc_info:
            delete_group_accumulator_service(
                group_id=group_id,
                group_accumulator_id=accumulator_id,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.delete_group_accumulator')
    def test_delete_group_accumulator_soft_delete(self, mock_delete, mock_get, mock_session):
        """Test that delete performs soft delete (sets deleted_at)."""
        group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_accumulator = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_get.return_value = mock_accumulator

        delete_group_accumulator_service(
            group_id=group_id,
            group_accumulator_id=accumulator_id,
        )

        # Verify delete_group_accumulator was called (which sets deleted_at)
        mock_delete.assert_called_once_with(mock_db, mock_accumulator)
        # Verify the accumulator object was passed to delete function
        assert mock_delete.call_args[0][1] == mock_accumulator


class TestSubmitGroupCountService:
    """Test cases for submit_group_count_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_and_extract_user_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.is_user_joined_group_accumulator')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_user_group_accumulator_count')
    @patch('pecha_api.group_accumulator.group_accumulator_service.add_group_history_row')
    def test_submit_group_count_success(self, mock_add_history, mock_get_count, mock_joined, mock_get_acc, mock_validate, mock_session):
        """Test successful submission of group count."""
        accumulator_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_user = MockUser(id=user_id)
        mock_validate.return_value = mock_user
        mock_accumulator = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_get_acc.return_value = mock_accumulator
        mock_joined.return_value = True
        mock_get_count.return_value = 50
        mock_history = MockGroupAccumulatorHistory(
            group_accumulator_id=accumulator_id,
            user_id=user_id,
            count=50,
        )
        mock_add_history.return_value = mock_history

        request = SubmitGroupCountRequest(current_count=100)

        result, is_created = submit_group_count_service(
            token="valid_token",
            group_accumulator_id=accumulator_id,
            request=request,
        )

        assert result.count == 50
        assert result.user_id == user_id
        assert is_created is True
        mock_validate.assert_called_once_with(token="valid_token")
        mock_get_acc.assert_called_once_with(mock_db, accumulator_id)
        mock_joined.assert_called_once_with(
            db=mock_db,
            group_accumulator_id=accumulator_id,
            user_id=user_id,
        )
        mock_get_count.assert_called_once_with(
            db=mock_db,
            group_accumulator_id=accumulator_id,
            user_id=user_id,
        )
        mock_add_history.assert_called_once_with(
            db=mock_db,
            group_accumulator_id=accumulator_id,
            user_id=user_id,
            count=50,
        )

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_and_extract_user_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.is_user_joined_group_accumulator')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_user_group_accumulator_count')
    def test_submit_group_count_zero_delta(self, mock_get_count, mock_joined, mock_get_acc, mock_validate, mock_session):
        """Test submit group count when delta is zero returns is_created=False."""
        accumulator_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_user = MockUser(id=user_id)
        mock_validate.return_value = mock_user
        mock_accumulator = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_get_acc.return_value = mock_accumulator
        mock_joined.return_value = True
        mock_get_count.return_value = 100

        request = SubmitGroupCountRequest(current_count=100)

        result, is_created = submit_group_count_service(
            token="valid_token",
            group_accumulator_id=accumulator_id,
            request=request,
        )

        assert result.count == 0
        assert result.user_id == user_id
        assert is_created is False

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_and_extract_user_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.is_user_joined_group_accumulator')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_user_group_accumulator_count')
    def test_submit_group_count_negative_delta(self, mock_get_count, mock_joined, mock_get_acc, mock_validate, mock_session):
        """Test submit group count when delta is negative returns is_created=False."""
        accumulator_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_user = MockUser(id=user_id)
        mock_validate.return_value = mock_user
        mock_accumulator = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_get_acc.return_value = mock_accumulator
        mock_joined.return_value = True
        mock_get_count.return_value = 150

        request = SubmitGroupCountRequest(current_count=100)

        result, is_created = submit_group_count_service(
            token="valid_token",
            group_accumulator_id=accumulator_id,
            request=request,
        )

        assert result.count == 0
        assert is_created is False

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_and_extract_user_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.is_user_joined_group_accumulator')
    def test_submit_group_count_not_member(self, mock_joined, mock_get_acc, mock_validate, mock_session):
        """Test submit group count when user has not joined the group accumulator."""
        accumulator_id = uuid4()
        user_id = uuid4()
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_user = MockUser(id=user_id)
        mock_validate.return_value = mock_user
        mock_accumulator = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_get_acc.return_value = mock_accumulator
        mock_joined.return_value = False

        request = SubmitGroupCountRequest(current_count=100)

        with pytest.raises(HTTPException) as exc_info:
            submit_group_count_service(
                token="valid_token",
                group_accumulator_id=accumulator_id,
                request=request,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "join" in exc_info.value.detail["message"]

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_and_extract_user_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_submit_group_count_accumulator_not_found(self, mock_get_acc, mock_validate, mock_session):
        """Test submit group count when accumulator doesn't exist."""
        accumulator_id = uuid4()
        user_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_user = MockUser(id=user_id)
        mock_validate.return_value = mock_user
        mock_get_acc.return_value = None

        request = SubmitGroupCountRequest(current_count=100)

        with pytest.raises(HTTPException) as exc_info:
            submit_group_count_service(
                token="valid_token",
                group_accumulator_id=accumulator_id,
                request=request,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestGetGroupAccumulatorHistoryService:
    """Test cases for get_group_accumulator_history_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_history')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_total_count')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_count_in_range')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_joiners_count')
    def test_get_history_success(
        self, mock_joiners_count, mock_today, mock_total, mock_history, mock_get_acc, mock_session
    ):
        """Test successful retrieval of group accumulator history."""
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_accumulator = MockGroupAccumulator(id=accumulator_id)
        mock_get_acc.return_value = mock_accumulator
        mock_history_items = [
            MockGroupAccumulatorHistory(group_accumulator_id=accumulator_id, count=100),
            MockGroupAccumulatorHistory(group_accumulator_id=accumulator_id, count=50),
        ]
        mock_history.return_value = (mock_history_items, 2)
        mock_total.return_value = 150
        mock_today.return_value = 150
        mock_joiners_count.return_value = 4

        result = get_group_accumulator_history_service(
            group_accumulator_id=accumulator_id,
            skip=0,
            limit=20,
        )

        assert len(result.history) == 2
        assert result.total == 2
        assert result.group_accumulator.total_count == 150
        assert result.group_accumulator.total_today_count == 150
        mock_get_acc.assert_called_once_with(mock_db, accumulator_id)
        mock_history.assert_called_once_with(
            mock_db, accumulator_id, 0, 20, range_start=None, range_end=None
        )
        mock_total.assert_called_once_with(mock_db, accumulator_id)

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_get_history_accumulator_not_found(self, mock_get_acc, mock_session):
        """Test get history when accumulator doesn't exist."""
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_acc.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_group_accumulator_history_service(
                group_accumulator_id=accumulator_id,
                skip=0,
                limit=20,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class MockAuthor:
    """Mock Author model for CMS tests."""
    def __init__(self, id=None, user_id=None):
        self.id = id or uuid4()
        self.user_id = user_id or uuid4()


class TestCreateGroupAccumulatorCmsService:
    """Test cases for create_group_accumulator_cms_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_cms_author_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.require_can_create_content')
    @patch('pecha_api.group_accumulator.group_accumulator_service.verify_group_exists')
    @patch('pecha_api.group_accumulator.group_accumulator_service.create_group_accumulator')
    def test_create_cms_success(self, mock_create, mock_verify, mock_perm, mock_auth, mock_session):
        """Test successful CMS creation with proper authorization."""
        group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockAuthor()
        mock_verify.return_value = True
        mock_create.return_value = MockGroupAccumulator(
            group_id=group_id,
            accumulator_id=accumulator_id,
        )

        request = CreateGroupAccumulatorRequest(
            accumulator_id=accumulator_id,
            target_count=108000,
        )

        result = create_group_accumulator_cms_service(
            token="valid_token",
            group_id=group_id,
            request=request,
        )

        assert result.group_id == group_id
        mock_auth.assert_called_once_with(token="valid_token")
        mock_perm.assert_called_once()

    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_cms_author_details')
    def test_create_cms_invalid_token(self, mock_auth):
        """Test CMS creation with invalid token."""
        mock_auth.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

        request = CreateGroupAccumulatorRequest(target_count=108000)

        with pytest.raises(HTTPException) as exc_info:
            create_group_accumulator_cms_service(
                token="invalid_token",
                group_id=uuid4(),
                request=request,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetGroupAccumulatorsCmsService:
    """Test cases for get_group_accumulators_cms_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_cms_author_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.require_can_read_group_content')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulators')
    def test_get_accumulators_cms_success(self, mock_get, mock_perm, mock_auth, mock_session):
        """Test successful CMS list with proper authorization."""
        group_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockAuthor()
        mock_get.return_value = ([MockGroupAccumulator(group_id=group_id)], 1)

        result = get_group_accumulators_cms_service(
            token="valid_token",
            group_id=group_id,
            skip=0,
            limit=20,
        )

        assert result.total == 1
        mock_auth.assert_called_once_with(token="valid_token")
        mock_perm.assert_called_once()


class TestGetGroupAccumulatorCmsService:
    """Test cases for get_group_accumulator_cms_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_cms_author_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.require_can_read_group_content')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_joiners_count')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_count_in_range')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_total_count')
    def test_get_single_cms_success(
        self, mock_total, mock_today, mock_joiners, mock_get, mock_perm, mock_auth, mock_session
    ):
        """Test successful CMS get single with proper authorization."""
        group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockAuthor()
        mock_get.return_value = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_total.return_value = 5000
        mock_today.return_value = 0
        mock_joiners.return_value = 0

        result = get_group_accumulator_cms_service(
            token="valid_token",
            group_id=group_id,
            group_accumulator_id=accumulator_id,
        )

        assert result.id == accumulator_id
        assert result.total_count == 5000
        mock_auth.assert_called_once_with(token="valid_token")

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_cms_author_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.require_can_read_group_content')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_get_single_cms_not_found(self, mock_get, mock_perm, mock_auth, mock_session):
        """Test CMS get single when accumulator not found."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockAuthor()
        mock_get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_group_accumulator_cms_service(
                token="valid_token",
                group_id=uuid4(),
                group_accumulator_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_cms_author_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.require_can_read_group_content')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_get_single_cms_wrong_group(self, mock_get, mock_perm, mock_auth, mock_session):
        """Test CMS get single when accumulator belongs to different group."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockAuthor()
        mock_get.return_value = MockGroupAccumulator(group_id=uuid4())

        with pytest.raises(HTTPException) as exc_info:
            get_group_accumulator_cms_service(
                token="valid_token",
                group_id=uuid4(),
                group_accumulator_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestUpdateGroupAccumulatorCmsService:
    """Test cases for update_group_accumulator_cms_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_cms_author_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.require_can_change_status')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.update_group_accumulator')
    def test_update_cms_success(self, mock_update, mock_get, mock_perm, mock_auth, mock_session):
        """Test successful CMS update with proper authorization."""
        group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockAuthor()
        mock_acc = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_get.return_value = mock_acc
        mock_update.return_value = mock_acc

        request = UpdateGroupAccumulatorRequest(target_count=216000)

        result = update_group_accumulator_cms_service(
            token="valid_token",
            group_id=group_id,
            group_accumulator_id=accumulator_id,
            request=request,
        )

        assert result.id == accumulator_id
        mock_auth.assert_called_once_with(token="valid_token")
        mock_perm.assert_called_once()


class TestDeleteGroupAccumulatorCmsService:
    """Test cases for delete_group_accumulator_cms_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_cms_author_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.require_can_change_status')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.delete_group_accumulator')
    def test_delete_cms_success(self, mock_delete, mock_get, mock_perm, mock_auth, mock_session):
        """Test successful CMS delete with proper authorization."""
        group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockAuthor()
        mock_get.return_value = MockGroupAccumulator(id=accumulator_id, group_id=group_id)

        delete_group_accumulator_cms_service(
            token="valid_token",
            group_id=group_id,
            group_accumulator_id=accumulator_id,
        )

        mock_auth.assert_called_once_with(token="valid_token")
        mock_perm.assert_called_once()
        mock_delete.assert_called_once()

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_cms_author_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.require_can_change_status')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_delete_cms_not_found(self, mock_get, mock_perm, mock_auth, mock_session):
        """Test CMS delete when accumulator not found."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockAuthor()
        mock_get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            delete_group_accumulator_cms_service(
                token="valid_token",
                group_id=uuid4(),
                group_accumulator_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteGroupAccumulatorUserService:
    """Test cases for delete_group_accumulator_user_service."""

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_and_extract_user_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.is_user_joined_group')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.delete_group_accumulator')
    def test_delete_user_success(self, mock_delete, mock_get, mock_joined, mock_auth, mock_session):
        """Test successful user delete with group membership."""
        group_id = uuid4()
        accumulator_id = uuid4()
        user_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockUser(id=user_id)
        mock_get.return_value = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_joined.return_value = True

        delete_group_accumulator_user_service(
            token="valid_token",
            group_accumulator_id=accumulator_id,
        )

        mock_auth.assert_called_once_with(token="valid_token")
        mock_get.assert_called_once_with(mock_db, accumulator_id)
        mock_joined.assert_called_once_with(db=mock_db, group_id=group_id, user_id=user_id)
        mock_delete.assert_called_once()

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_and_extract_user_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.is_user_joined_group')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_delete_user_not_member(self, mock_get, mock_joined, mock_auth, mock_session):
        """Test user delete when not a group member."""
        group_id = uuid4()
        accumulator_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockUser()
        mock_get.return_value = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_joined.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            delete_group_accumulator_user_service(
                token="valid_token",
                group_accumulator_id=accumulator_id,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "member" in exc_info.value.detail["message"]

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_and_extract_user_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_delete_user_not_found(self, mock_get, mock_auth, mock_session):
        """Test user delete when accumulator not found."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockUser()
        mock_get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            delete_group_accumulator_user_service(
                token="valid_token",
                group_accumulator_id=uuid4(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_and_extract_user_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.is_user_joined_group')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    def test_delete_user_wrong_group(self, mock_get, mock_joined, mock_auth, mock_session):
        """Test user delete when user is not a member of the group."""
        group_id = uuid4()
        accumulator_id = uuid4()
        user_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockUser(id=user_id)
        mock_get.return_value = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_joined.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            delete_group_accumulator_user_service(
                token="valid_token",
                group_accumulator_id=accumulator_id,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestJoinGroupAccumulatorService:
    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.validate_and_extract_user_details')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service._assert_group_allows_join')
    @patch('pecha_api.group_accumulator.group_accumulator_service.upsert_group_join')
    @patch('pecha_api.group_accumulator.group_accumulator_service.upsert_group_accumulator_join')
    def test_join_success(
        self,
        mock_accumulator_join,
        mock_group_join,
        mock_assert_join,
        mock_get_group,
        mock_get_acc,
        mock_auth,
        mock_session,
    ):
        accumulator_id = uuid4()
        group_id = uuid4()
        user_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_auth.return_value = MockUser(id=user_id)
        mock_get_acc.return_value = MockGroupAccumulator(id=accumulator_id, group_id=group_id)
        mock_get_group.return_value = MagicMock(is_public=True)

        join_group_accumulator_service(token="valid_token", group_accumulator_id=accumulator_id)

        mock_group_join.assert_called_once_with(db=mock_db, group_id=group_id, user_id=user_id)
        mock_accumulator_join.assert_called_once_with(
            db=mock_db,
            group_accumulator_id=accumulator_id,
            user_id=user_id,
        )


class TestGetGroupAccumulatorMembersService:
    @patch('pecha_api.group_accumulator.group_accumulator_service.SessionLocal')
    @patch('pecha_api.group_accumulator.group_accumulator_service.get_group_accumulator_by_id')
    @patch('pecha_api.group_accumulator.group_accumulator_service.list_group_accumulator_joiners_paginated')
    @patch('pecha_api.group_accumulator.group_accumulator_service._user_fullname')
    @patch('pecha_api.group_accumulator.group_accumulator_service._user_avatar_url')
    def test_get_members_success(
        self,
        mock_avatar,
        mock_fullname,
        mock_list_joiners,
        mock_get_acc,
        mock_session,
    ):
        accumulator_id = uuid4()
        user_id = uuid4()
        joined_at = datetime.utcnow()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_acc.return_value = MockGroupAccumulator(id=accumulator_id)
        mock_user = MockUser(id=user_id)
        mock_list_joiners.return_value = ([(mock_user, joined_at, 500, 108)], 1)
        mock_fullname.return_value = "Test User"
        mock_avatar.return_value = "https://example.com/avatar.jpg"

        result = get_group_accumulator_members_service(group_accumulator_id=accumulator_id)

        assert result.member_count == 1
        assert result.total == 1
        assert result.members[0].user_id == user_id
        assert result.members[0].fullname == "Test User"
        assert result.members[0].joined_at == joined_at
        assert result.members[0].total_count == 500
        assert result.members[0].today_count == 108
