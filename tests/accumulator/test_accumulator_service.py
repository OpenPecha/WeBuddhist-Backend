import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
from starlette import status

from pecha_api.accumulator.accumulator_service import (
    get_all_accumulators_service,
    get_user_accumulators_service,
    create_accumulator_service,
    update_accumulator_service,
    delete_accumulator_service,
    get_accumulator_history_service,
    convert_accumulator_to_dto,
    convert_accumulator_to_public_dto,
    is_user_created_accumulator,
    validate_mantra_exists,
)
from pecha_api.accumulator.accumulator_response_models import (
    AccumulatorsResponse,
    PublicAccumulatorsResponse,
    AccumulatorDTO,
    PublicAccumulatorDTO,
    CreateAccumulatorRequest,
    UpdateAccumulatorRequest,
    AccumulatorHistoryResponse,
)
from pecha_api.accumulator.accumulator_models import Accumulator
from pecha_api.accumulator.accumulator_history_model import AccumulatorHistory
from pecha_api.accumulator.accumulator_enums import AccumulatorType
from pecha_api.mantra.mantra_model import Mantra  
from pecha_api.mantra.mantra_metadata_model import MantraMetadata  


class TestDataFactory:
    """Factory for creating test data objects."""

    @staticmethod
    def create_mock_metadata(name="Test Accumulator", description=None, language="EN", mala=None):
        """Create a mock AccumulatorMetadata row."""
        metadata = MagicMock()
        metadata.id = uuid4()
        metadata.name = name
        metadata.description = description
        lang = MagicMock()
        lang.value = language
        metadata.language = lang
        metadata.mala = mala
        metadata.mala_image = mala.id if mala is not None else None
        return metadata

    @staticmethod
    def create_mock_accumulator(
        accumulator_id=None,
        user_id=None,
        group_id=None,
        parent_id=None,
        accumulator_type=AccumulatorType.USER,
        name="Test Accumulator",
        description=None,
        target_count=108,
        current_count=0,
        text_id=None,
        mantra_id=None,
        metadata_entries=None,
    ):
        """Create a mock Accumulator model. name/description are placed on a
        single (EN) metadata row unless metadata_entries is given explicitly."""
        accumulator = MagicMock(spec=Accumulator)
        accumulator.id = accumulator_id or uuid4()
        accumulator.user_id = user_id or uuid4()
        accumulator.group_id = group_id
        accumulator.parent_id = parent_id
        accumulator.type = accumulator_type
        accumulator.target_count = target_count
        accumulator.current_count = current_count
        accumulator.text_id = text_id
        accumulator.mantra_id = mantra_id
        if metadata_entries is None:
            metadata_entries = [
                TestDataFactory.create_mock_metadata(name=name, description=description)
            ]
        accumulator.metadata_entries = metadata_entries
        accumulator.created_at = datetime.utcnow()
        accumulator.updated_at = datetime.utcnow()
        return accumulator

    @staticmethod
    def create_mock_user(user_id=None):
        """Create a mock user."""
        user = MagicMock()
        user.id = user_id or uuid4()
        user.email = "test@example.com"
        return user

    @staticmethod
    def create_accumulator_request(preset_id=None) -> CreateAccumulatorRequest:
        """Create a CreateAccumulatorRequest referencing a preset."""
        return CreateAccumulatorRequest(preset_id=preset_id or uuid4())

    @staticmethod
    def create_update_request(
        target_count=None,
        current_count=None,
        text_id=None,
        mantra_id=None,
    ) -> UpdateAccumulatorRequest:
        """Create an UpdateAccumulatorRequest."""
        return UpdateAccumulatorRequest(
            target_count=target_count,
            current_count=current_count,
            text_id=text_id,
            mantra_id=mantra_id,
        )

    @staticmethod
    def create_mock_history(
        accumulator_id=None,
        user_id=None,
        count=10,
    ):
        """Create a mock AccumulatorHistory model."""
        history = MagicMock(spec=AccumulatorHistory)
        history.accumulator_id = accumulator_id or uuid4()
        history.user_id = user_id or uuid4()
        history.count = count
        history.created_at = datetime.utcnow()
        return history


class TestGetAllAccumulatorsService:
    """Test cases for get_all_accumulators_service function."""

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_all_accumulators')
    def test_get_all_accumulators_service_success(self, mock_get_all, mock_session):
        """Test successful retrieval of all accumulators."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        acc1 = TestDataFactory.create_mock_accumulator(name="Acc 1")
        acc2 = TestDataFactory.create_mock_accumulator(name="Acc 2")
        mock_get_all.return_value = ([acc1, acc2], 2)

        result = get_all_accumulators_service(skip=0, limit=20)

        assert isinstance(result, PublicAccumulatorsResponse)
        assert len(result.accumulators) == 2
        assert result.total == 2
        assert result.skip == 0
        assert result.limit == 20
        # Public DTO must not expose user_id
        assert isinstance(result.accumulators[0], PublicAccumulatorDTO)
        assert not hasattr(result.accumulators[0], "user_id")

        mock_get_all.assert_called_once_with(mock_db, 0, 20)

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_all_accumulators')
    def test_get_all_accumulators_service_empty(self, mock_get_all, mock_session):
        """Test get_all_accumulators_service when no accumulators exist."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        mock_get_all.return_value = ([], 0)

        result = get_all_accumulators_service(skip=0, limit=20)

        assert len(result.accumulators) == 0
        assert result.total == 0

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_all_accumulators')
    def test_get_all_accumulators_service_pagination(self, mock_get_all, mock_session):
        """Test get_all_accumulators_service with custom pagination."""
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        acc1 = TestDataFactory.create_mock_accumulator()
        mock_get_all.return_value = ([acc1], 10)

        result = get_all_accumulators_service(skip=5, limit=1)

        assert result.skip == 5
        assert result.limit == 1
        assert result.total == 10

        mock_get_all.assert_called_once_with(mock_db, 5, 1)


class TestGetUserAccumulatorsService:
    """Test cases for get_user_accumulators_service function."""

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_user_accumulators')
    def test_get_user_accumulators_service_success(self, mock_get_user, mock_session):
        """Test successful retrieval of user's accumulators."""
        user_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        acc1 = TestDataFactory.create_mock_accumulator(user_id=user_id, name="My Acc 1")
        acc2 = TestDataFactory.create_mock_accumulator(user_id=user_id, name="My Acc 2")
        mock_get_user.return_value = ([acc1, acc2], 2)

        result = get_user_accumulators_service(user_id=user_id, skip=0, limit=20)

        assert isinstance(result, AccumulatorsResponse)
        assert len(result.accumulators) == 2
        assert result.total == 2
        assert result.accumulators[0].user_id == user_id

        mock_get_user.assert_called_once_with(mock_db, user_id, 0, 20)

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_user_accumulators')
    def test_get_user_accumulators_service_empty(self, mock_get_user, mock_session):
        """Test get_user_accumulators_service when user has no accumulators."""
        user_id = uuid4()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        mock_get_user.return_value = ([], 0)

        result = get_user_accumulators_service(user_id=user_id, skip=0, limit=20)

        assert len(result.accumulators) == 0
        assert result.total == 0


class TestCreateAccumulatorService:
    """Test cases for create_accumulator_service function (preset -> user copy)."""

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.commit_accumulator')
    @patch('pecha_api.accumulator.accumulator_service.add_accumulator')
    @patch('pecha_api.accumulator.accumulator_service.get_user_accumulator_by_parent')
    @patch('pecha_api.accumulator.accumulator_service.get_preset_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_create_accumulator_service_success(
        self, mock_validate, mock_get_preset, mock_get_by_parent, mock_add, mock_commit, mock_session
    ):
        """First tap (no existing accumulator for the preset) creates a new row
        whose parent_id links back to the preset."""
        user_id = uuid4()
        preset_id = uuid4()
        group_id = uuid4()
        mantra_id = uuid4()
        token = "valid_token"

        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=user_id)
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        preset = TestDataFactory.create_mock_accumulator(
            accumulator_id=preset_id,
            user_id=None,
            group_id=group_id,
            accumulator_type=AccumulatorType.PRESET,
            name="Refuge Prayer",
            target_count=111111,
            mantra_id=mantra_id,
        )
        mock_get_preset.return_value = preset
        mock_get_by_parent.return_value = None  # nothing exists yet -> create

        request = TestDataFactory.create_accumulator_request(preset_id=preset_id)

        # commit stamps server-side timestamps (as the DB would) and echoes the row.
        def _commit(_db, accumulator):
            accumulator.created_at = datetime.utcnow()
            accumulator.updated_at = datetime.utcnow()
            return accumulator
        mock_commit.side_effect = _commit

        result = create_accumulator_service(token=token, request=request)

        assert isinstance(result, AccumulatorDTO)
        assert result.metadata[0].name == "Refuge Prayer"
        assert result.target_count == 111111
        assert result.type == AccumulatorType.USER
        assert result.user_id == user_id
        assert result.group_id == group_id
        assert result.parent_id == preset_id
        assert result.current_count == 0

        mock_validate.assert_called_once_with(token=token)
        mock_get_preset.assert_called_once_with(mock_db, preset_id)
        mock_get_by_parent.assert_called_once_with(mock_db, user_id, preset_id)
        mock_add.assert_called_once()
        mock_commit.assert_called_once()

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.add_accumulator')
    @patch('pecha_api.accumulator.accumulator_service.get_user_accumulator_by_parent')
    @patch('pecha_api.accumulator.accumulator_service.get_preset_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_create_accumulator_service_rejects_duplicate(
        self, mock_validate, mock_get_preset, mock_get_by_parent, mock_add, mock_session
    ):
        """Tapping a preset the user already created an accumulator from is
        rejected with 409: no second row, no reset."""
        user_id = uuid4()
        preset_id = uuid4()
        token = "valid_token"

        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=user_id)
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        mock_get_preset.return_value = TestDataFactory.create_mock_accumulator(
            accumulator_id=preset_id, accumulator_type=AccumulatorType.PRESET
        )
        existing = TestDataFactory.create_mock_accumulator(
            user_id=user_id, accumulator_type=AccumulatorType.USER,
            parent_id=preset_id, current_count=540,
        )
        mock_get_by_parent.return_value = existing

        request = TestDataFactory.create_accumulator_request(preset_id=preset_id)

        with pytest.raises(HTTPException) as exc_info:
            create_accumulator_service(token=token, request=request)

        assert exc_info.value.status_code == status.HTTP_409_CONFLICT
        assert existing.current_count == 540  # untouched, no reset
        mock_get_by_parent.assert_called_once_with(mock_db, user_id, preset_id)
        mock_add.assert_not_called()       # no new accumulator created

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.add_history_row')
    @patch('pecha_api.accumulator.accumulator_service.commit_accumulator')
    @patch('pecha_api.accumulator.accumulator_service.add_accumulator')
    @patch('pecha_api.accumulator.accumulator_service.get_user_accumulator_by_parent')
    @patch('pecha_api.accumulator.accumulator_service.get_preset_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_create_accumulator_service_no_history_on_create(
        self, mock_validate, mock_get_preset, mock_get_by_parent, mock_add, mock_commit, mock_add_history, mock_session
    ):
        """Creating from a preset starts at count 0 and writes no history row."""
        user_id = uuid4()
        preset_id = uuid4()
        token = "valid_token"

        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=user_id)
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_preset.return_value = TestDataFactory.create_mock_accumulator(
            accumulator_id=preset_id, accumulator_type=AccumulatorType.PRESET
        )
        mock_get_by_parent.return_value = None

        def _commit(_db, accumulator):
            accumulator.created_at = datetime.utcnow()
            accumulator.updated_at = datetime.utcnow()
            return accumulator
        mock_commit.side_effect = _commit

        request = TestDataFactory.create_accumulator_request(preset_id=preset_id)
        create_accumulator_service(token=token, request=request)

        mock_add_history.assert_not_called()

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_preset_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_create_accumulator_service_preset_not_found(
        self, mock_validate, mock_get_preset, mock_session
    ):
        """A preset_id that matches no preset raises 404."""
        token = "valid_token"
        mock_validate.return_value = TestDataFactory.create_mock_user()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_preset.return_value = None

        request = TestDataFactory.create_accumulator_request(preset_id=uuid4())

        with pytest.raises(HTTPException) as exc_info:
            create_accumulator_service(token=token, request=request)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_create_accumulator_service_invalid_token(self, mock_validate):
        """Test create_accumulator_service with invalid token."""
        mock_validate.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

        request = TestDataFactory.create_accumulator_request()

        with pytest.raises(HTTPException) as exc_info:
            create_accumulator_service(token="invalid_token", request=request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateAccumulatorService:
    """Test cases for update_accumulator_service function."""

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.update_accumulator')
    @patch('pecha_api.accumulator.accumulator_service.get_accumulator_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_update_accumulator_service_success(self, mock_validate, mock_get, mock_update, mock_session):
        """Test successful update of accumulator."""
        user_id = uuid4()
        accumulator_id = uuid4()
        token = "valid_token"

        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=user_id)
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        existing = TestDataFactory.create_mock_accumulator(
            accumulator_id=accumulator_id, user_id=user_id, name="Old Name"
        )
        mock_get.return_value = existing
        mock_update.return_value = existing

        request = TestDataFactory.create_update_request(target_count=200)

        result = await update_accumulator_service(token=token, accumulator_id=accumulator_id, request=request)

        assert isinstance(result, AccumulatorDTO)
        assert existing.target_count == 200
        mock_get.assert_called_once_with(mock_db, accumulator_id)
        mock_update.assert_called_once_with(mock_db, existing)

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.add_history_row')
    @patch('pecha_api.accumulator.accumulator_service.update_accumulator')
    @patch('pecha_api.accumulator.accumulator_service.get_accumulator_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_update_accumulator_service_records_positive_delta(
        self, mock_validate, mock_get, mock_update, mock_add_history, mock_session
    ):
        """Increasing current_count records the delta in history."""
        user_id = uuid4()
        accumulator_id = uuid4()
        token = "valid_token"

        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=user_id)
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        existing = TestDataFactory.create_mock_accumulator(
            accumulator_id=accumulator_id, user_id=user_id, current_count=100
        )
        mock_get.return_value = existing
        mock_update.return_value = existing

        request = TestDataFactory.create_update_request(current_count=150)

        await update_accumulator_service(token=token, accumulator_id=accumulator_id, request=request)

        assert existing.current_count == 150
        mock_add_history.assert_called_once()
        _, kwargs = mock_add_history.call_args
        assert kwargs["count"] == 50

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.add_history_row')
    @patch('pecha_api.accumulator.accumulator_service.update_accumulator')
    @patch('pecha_api.accumulator.accumulator_service.get_accumulator_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_update_accumulator_service_no_history_on_decrease(
        self, mock_validate, mock_get, mock_update, mock_add_history, mock_session
    ):
        """Decreasing current_count updates the value but records no history."""
        user_id = uuid4()
        accumulator_id = uuid4()
        token = "valid_token"

        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=user_id)
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        existing = TestDataFactory.create_mock_accumulator(
            accumulator_id=accumulator_id, user_id=user_id, current_count=100
        )
        mock_get.return_value = existing
        mock_update.return_value = existing

        request = TestDataFactory.create_update_request(current_count=40)

        await update_accumulator_service(token=token, accumulator_id=accumulator_id, request=request)

        assert existing.current_count == 40
        mock_add_history.assert_not_called()

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_accumulator_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_update_accumulator_service_not_found(self, mock_validate, mock_get, mock_session):
        """Test update_accumulator_service when accumulator doesn't exist."""
        token = "valid_token"
        mock_validate.return_value = TestDataFactory.create_mock_user()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get.return_value = None

        request = TestDataFactory.create_update_request()

        with pytest.raises(HTTPException) as exc_info:
            await update_accumulator_service(token=token, accumulator_id=uuid4(), request=request)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_accumulator_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_update_accumulator_service_not_owner(self, mock_validate, mock_get, mock_session):
        """Test update_accumulator_service when user is not the owner."""
        token = "valid_token"
        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=uuid4())
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get.return_value = TestDataFactory.create_mock_accumulator(user_id=uuid4())

        request = TestDataFactory.create_update_request()

        with pytest.raises(HTTPException) as exc_info:
            await update_accumulator_service(token=token, accumulator_id=uuid4(), request=request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_accumulator_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_update_accumulator_service_preset_forbidden(self, mock_validate, mock_get, mock_session):
        """Test update_accumulator_service when trying to update a preset accumulator."""
        user_id = uuid4()
        token = "valid_token"
        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=user_id)
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get.return_value = TestDataFactory.create_mock_accumulator(
            user_id=user_id, accumulator_type=AccumulatorType.PRESET
        )

        request = TestDataFactory.create_update_request()

        with pytest.raises(HTTPException) as exc_info:
            await update_accumulator_service(token=token, accumulator_id=uuid4(), request=request)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_update_accumulator_service_invalid_token(self, mock_validate):
        """Test update_accumulator_service with invalid token."""
        mock_validate.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

        request = TestDataFactory.create_update_request()

        with pytest.raises(HTTPException) as exc_info:
            await update_accumulator_service(token="invalid_token", accumulator_id=uuid4(), request=request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteAccumulatorService:
    """Test cases for delete_accumulator_service function."""

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.delete_accumulator')
    @patch('pecha_api.accumulator.accumulator_service.get_accumulator_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_delete_accumulator_service_success(self, mock_validate, mock_get, mock_delete, mock_session):
        """Test successful deletion of accumulator."""
        user_id = uuid4()
        accumulator_id = uuid4()
        token = "valid_token"

        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=user_id)
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        existing = TestDataFactory.create_mock_accumulator(accumulator_id=accumulator_id, user_id=user_id)
        mock_get.return_value = existing

        result = delete_accumulator_service(token=token, accumulator_id=accumulator_id)

        assert result is None
        mock_get.assert_called_once_with(mock_db, accumulator_id)
        mock_delete.assert_called_once_with(mock_db, existing)

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_accumulator_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_delete_accumulator_service_not_found(self, mock_validate, mock_get, mock_session):
        """Test delete_accumulator_service when accumulator doesn't exist."""
        token = "valid_token"
        mock_validate.return_value = TestDataFactory.create_mock_user()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            delete_accumulator_service(token=token, accumulator_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_accumulator_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_delete_accumulator_service_not_owner(self, mock_validate, mock_get, mock_session):
        """Test delete_accumulator_service when user is not the owner."""
        token = "valid_token"
        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=uuid4())
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get.return_value = TestDataFactory.create_mock_accumulator(user_id=uuid4())

        with pytest.raises(HTTPException) as exc_info:
            delete_accumulator_service(token=token, accumulator_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_accumulator_by_id')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_delete_accumulator_service_preset_forbidden(self, mock_validate, mock_get, mock_session):
        """Test delete_accumulator_service when trying to delete a preset accumulator."""
        user_id = uuid4()
        token = "valid_token"
        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=user_id)
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get.return_value = TestDataFactory.create_mock_accumulator(
            user_id=user_id, accumulator_type=AccumulatorType.PRESET
        )

        with pytest.raises(HTTPException) as exc_info:
            delete_accumulator_service(token=token, accumulator_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_delete_accumulator_service_invalid_token(self, mock_validate):
        """Test delete_accumulator_service with invalid token."""
        mock_validate.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

        with pytest.raises(HTTPException) as exc_info:
            delete_accumulator_service(token="invalid_token", accumulator_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetAccumulatorHistoryService:
    """Test cases for get_accumulator_history_service function."""

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_user_accumulator_history')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_get_accumulator_history_service_success(self, mock_validate, mock_get_history, mock_session):
        """Test successful retrieval of accumulator history."""
        user_id = uuid4()
        accumulator_id = uuid4()
        token = "valid_token"

        mock_validate.return_value = TestDataFactory.create_mock_user(user_id=user_id)
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db

        accumulator = TestDataFactory.create_mock_accumulator(
            accumulator_id=accumulator_id, name="Mani", current_count=300
        )
        session1 = TestDataFactory.create_mock_history(accumulator_id=accumulator_id, count=100)
        session2 = TestDataFactory.create_mock_history(accumulator_id=accumulator_id, count=200)

        mock_get_history.return_value = ([(accumulator, 300, [session1, session2])], 1)

        result = get_accumulator_history_service(token=token, skip=0, limit=20)

        assert isinstance(result, AccumulatorHistoryResponse)
        assert len(result.accumulators) == 1
        assert result.accumulators[0].metadata[0].name == "Mani"
        assert result.accumulators[0].total_counted == 300
        assert len(result.accumulators[0].sessions) == 2
        assert result.total == 1

        mock_validate.assert_called_once_with(token=token)
        mock_get_history.assert_called_once_with(mock_db, user_id, 0, 20)

    @patch('pecha_api.accumulator.accumulator_service.SessionLocal')
    @patch('pecha_api.accumulator.accumulator_service.get_user_accumulator_history')
    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_get_accumulator_history_service_empty(self, mock_validate, mock_get_history, mock_session):
        """Test get_accumulator_history_service when user has no history."""
        token = "valid_token"
        mock_validate.return_value = TestDataFactory.create_mock_user()
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        mock_get_history.return_value = ([], 0)

        result = get_accumulator_history_service(token=token, skip=0, limit=20)

        assert len(result.accumulators) == 0
        assert result.total == 0

    @patch('pecha_api.accumulator.accumulator_service.validate_and_extract_user_details')
    def test_get_accumulator_history_service_invalid_token(self, mock_validate):
        """Test get_accumulator_history_service with invalid token."""
        mock_validate.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

        with pytest.raises(HTTPException) as exc_info:
            get_accumulator_history_service(token="invalid_token", skip=0, limit=20)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestHelperFunctions:
    """Test cases for helper/conversion functions."""

    def test_convert_accumulator_to_dto(self):
        """Test conversion of Accumulator model to AccumulatorDTO."""
        accumulator_id = uuid4()
        user_id = uuid4()
        accumulator = TestDataFactory.create_mock_accumulator(
            accumulator_id=accumulator_id,
            user_id=user_id,
            name="Mani",
            description="Compassion mantra",
            target_count=108,
            current_count=42,
        )

        result = convert_accumulator_to_dto(accumulator)

        assert isinstance(result, AccumulatorDTO)
        assert result.id == accumulator_id
        assert result.user_id == user_id
        assert result.metadata[0].name == "Mani"
        assert result.metadata[0].description == "Compassion mantra"
        assert result.target_count == 108
        assert result.current_count == 42
        assert result.type == AccumulatorType.USER

    def test_convert_accumulator_to_dto_none_current_count_defaults_zero(self):
        """A None current_count should be coerced to 0 in the DTO."""
        accumulator = TestDataFactory.create_mock_accumulator(current_count=None)

        result = convert_accumulator_to_dto(accumulator)

        assert result.current_count == 0

    def test_convert_accumulator_to_public_dto_omits_user_id(self):
        """Public DTO should not carry user_id and exposes the row id as id."""
        accumulator = TestDataFactory.create_mock_accumulator()

        result = convert_accumulator_to_public_dto(accumulator)

        assert isinstance(result, PublicAccumulatorDTO)
        assert not hasattr(result, "user_id")
        assert not hasattr(result, "preset_id")
        assert result.id == accumulator.id

    def test_is_user_created_accumulator_user_type(self):
        """is_user_created_accumulator returns True for USER type."""
        accumulator = TestDataFactory.create_mock_accumulator(accumulator_type=AccumulatorType.USER)
        assert is_user_created_accumulator(accumulator) is True

    def test_is_user_created_accumulator_preset_type(self):
        """is_user_created_accumulator returns False for PRESET type."""
        accumulator = TestDataFactory.create_mock_accumulator(accumulator_type=AccumulatorType.PRESET)
        assert is_user_created_accumulator(accumulator) is False

    @patch('pecha_api.accumulator.accumulator_service.mantra_exists')
    def test_validate_mantra_exists_found(self, mock_mantra_exists):
        """validate_mantra_exists is a no-op when the mantra exists."""
        mock_mantra_exists.return_value = True
        # Should not raise
        validate_mantra_exists(MagicMock(), uuid4())

    @patch('pecha_api.accumulator.accumulator_service.mantra_exists')
    def test_validate_mantra_exists_not_found(self, mock_mantra_exists):
        """validate_mantra_exists raises 404 when the mantra is missing."""
        mock_mantra_exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            validate_mantra_exists(MagicMock(), uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
