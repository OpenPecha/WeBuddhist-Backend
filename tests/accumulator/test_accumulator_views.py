import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from starlette import status

from pecha_api.accumulator.accumulator_views import (
    get_all_accumulators,
    get_user_accumulators,
    create_user_accumulator,
    update_user_accumulator,
    delete_user_accumulator,
    get_user_accumulator_history,
)
from pecha_api.accumulator.accumulator_response_models import (
    AccumulatorsResponse,
    PublicAccumulatorsResponse,
    AccumulatorDTO,
    PublicAccumulatorDTO,
    CreateAccumulatorRequest,
    UpdateAccumulatorRequest,
    AccumulatorHistoryResponse,
    AccumulatorHistoryDTO,
    AccumulatorSessionDTO,
)
from pecha_api.accumulator.accumulator_enums import AccumulatorType


class TestDataFactory:
    """Factory for creating test data objects."""

    @staticmethod
    def create_auth_credentials(token="valid_token") -> HTTPAuthorizationCredentials:
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    @staticmethod
    def create_accumulator_dto(
        accumulator_id=None,
        user_id=None,
        accumulator_type=AccumulatorType.USER,
        name="Test Accumulator",
        description=None,
        target_count=108,
        current_count=0,
    ) -> AccumulatorDTO:
        return AccumulatorDTO(
            id=accumulator_id or uuid4(),
            user_id=user_id or uuid4(),
            type=accumulator_type,
            name=name,
            description=description,
            target_count=target_count,
            current_count=current_count,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    @staticmethod
    def create_public_dto(name="Test Accumulator", current_count=0) -> PublicAccumulatorDTO:
        return PublicAccumulatorDTO(
            id=uuid4(),
            type=AccumulatorType.USER,
            name=name,
            target_count=108,
            current_count=current_count,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    @staticmethod
    def create_accumulator_request(
        name="New Accumulator",
        target_count=108,
        current_count=0,
    ) -> CreateAccumulatorRequest:
        return CreateAccumulatorRequest(
            name=name,
            target_count=target_count,
            current_count=current_count,
        )

    @staticmethod
    def create_update_request(name=None, target_count=None, current_count=None) -> UpdateAccumulatorRequest:
        return UpdateAccumulatorRequest(
            name=name,
            target_count=target_count,
            current_count=current_count,
        )


class TestGetAllAccumulators:
    """Test cases for get_all_accumulators endpoint."""

    @patch('pecha_api.accumulator.accumulator_views.get_all_accumulators_service')
    @pytest.mark.asyncio
    async def test_get_all_accumulators_success(self, mock_service):
        """Test successful retrieval of all accumulators."""
        mock_service.return_value = PublicAccumulatorsResponse(
            accumulators=[
                TestDataFactory.create_public_dto(name="Acc 1"),
                TestDataFactory.create_public_dto(name="Acc 2"),
            ],
            total=2,
            skip=0,
            limit=20,
        )

        result = await get_all_accumulators(skip=0, limit=20)

        assert isinstance(result, PublicAccumulatorsResponse)
        assert len(result.accumulators) == 2
        assert result.total == 2
        mock_service.assert_called_once_with(skip=0, limit=20)

    @patch('pecha_api.accumulator.accumulator_views.get_all_accumulators_service')
    @pytest.mark.asyncio
    async def test_get_all_accumulators_empty(self, mock_service):
        """Test get_all_accumulators when no accumulators exist."""
        mock_service.return_value = PublicAccumulatorsResponse(
            accumulators=[], total=0, skip=0, limit=20
        )

        result = await get_all_accumulators(skip=0, limit=20)

        assert len(result.accumulators) == 0
        assert result.total == 0

    @patch('pecha_api.accumulator.accumulator_views.get_all_accumulators_service')
    @pytest.mark.asyncio
    async def test_get_all_accumulators_pagination(self, mock_service):
        """Test get_all_accumulators with custom pagination parameters."""
        mock_service.return_value = PublicAccumulatorsResponse(
            accumulators=[TestDataFactory.create_public_dto()],
            total=10,
            skip=5,
            limit=1,
        )

        result = await get_all_accumulators(skip=5, limit=1)

        assert result.skip == 5
        assert result.limit == 1
        assert result.total == 10
        mock_service.assert_called_once_with(skip=5, limit=1)


class TestGetUserAccumulators:
    """Test cases for get_user_accumulators endpoint."""

    @patch('pecha_api.accumulator.accumulator_views.get_user_accumulators_service')
    @patch('pecha_api.accumulator.accumulator_views.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_get_user_accumulators_success(self, mock_validate, mock_service):
        """Test successful retrieval of user's accumulators."""
        user_id = uuid4()
        token = "valid_token"

        mock_user = MagicMock()
        mock_user.id = user_id
        mock_validate.return_value = mock_user

        mock_service.return_value = AccumulatorsResponse(
            accumulators=[
                TestDataFactory.create_accumulator_dto(user_id=user_id, name="My Acc 1"),
                TestDataFactory.create_accumulator_dto(user_id=user_id, name="My Acc 2"),
            ],
            total=2,
            skip=0,
            limit=20,
        )

        result = await get_user_accumulators(
            credentials=TestDataFactory.create_auth_credentials(token=token),
            skip=0,
            limit=20,
        )

        assert isinstance(result, AccumulatorsResponse)
        assert len(result.accumulators) == 2
        mock_validate.assert_called_once_with(token=token)
        mock_service.assert_called_once_with(user_id=user_id, skip=0, limit=20)

    @patch('pecha_api.accumulator.accumulator_views.validate_and_extract_user_details')
    @pytest.mark.asyncio
    async def test_get_user_accumulators_invalid_token(self, mock_validate):
        """Test get_user_accumulators with invalid authentication token."""
        mock_validate.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_user_accumulators(
                credentials=TestDataFactory.create_auth_credentials(token="invalid_token"),
                skip=0,
                limit=20,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestCreateUserAccumulator:
    """Test cases for create_user_accumulator endpoint."""

    @patch('pecha_api.accumulator.accumulator_views.create_accumulator_service')
    @pytest.mark.asyncio
    async def test_create_user_accumulator_success(self, mock_service):
        """Test successful creation of user accumulator."""
        token = "valid_token"
        request = TestDataFactory.create_accumulator_request(name="New Acc", target_count=108)

        mock_service.return_value = TestDataFactory.create_accumulator_dto(name="New Acc", target_count=108)

        result = await create_user_accumulator(
            request=request,
            credentials=TestDataFactory.create_auth_credentials(token=token),
        )

        assert isinstance(result, AccumulatorDTO)
        assert result.name == "New Acc"
        assert result.type == AccumulatorType.USER
        mock_service.assert_called_once_with(token=token, request=request)

    @patch('pecha_api.accumulator.accumulator_views.create_accumulator_service')
    @pytest.mark.asyncio
    async def test_create_user_accumulator_mantra_not_found(self, mock_service):
        """Test create_user_accumulator when mantra does not exist."""
        request = TestDataFactory.create_accumulator_request()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Mantra not found"},
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_user_accumulator(
                request=request,
                credentials=TestDataFactory.create_auth_credentials(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.accumulator.accumulator_views.create_accumulator_service')
    @pytest.mark.asyncio
    async def test_create_user_accumulator_invalid_token(self, mock_service):
        """Test create_user_accumulator with invalid authentication token."""
        request = TestDataFactory.create_accumulator_request()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

        with pytest.raises(HTTPException) as exc_info:
            await create_user_accumulator(
                request=request,
                credentials=TestDataFactory.create_auth_credentials(token="invalid_token"),
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestUpdateUserAccumulator:
    """Test cases for update_user_accumulator endpoint."""

    @patch('pecha_api.accumulator.accumulator_views.update_accumulator_service')
    @pytest.mark.asyncio
    async def test_update_user_accumulator_success(self, mock_service):
        """Test successful update of user accumulator."""
        token = "valid_token"
        accumulator_id = uuid4()
        request = TestDataFactory.create_update_request(name="Updated", target_count=200)

        mock_service.return_value = TestDataFactory.create_accumulator_dto(
            accumulator_id=accumulator_id, name="Updated", target_count=200
        )

        result = await update_user_accumulator(
            accumulator_id=accumulator_id,
            request=request,
            credentials=TestDataFactory.create_auth_credentials(token=token),
        )

        assert isinstance(result, AccumulatorDTO)
        assert result.name == "Updated"
        mock_service.assert_called_once_with(
            token=token, accumulator_id=accumulator_id, request=request
        )

    @patch('pecha_api.accumulator.accumulator_views.update_accumulator_service')
    @pytest.mark.asyncio
    async def test_update_user_accumulator_not_found(self, mock_service):
        """Test update_user_accumulator when accumulator doesn't exist."""
        request = TestDataFactory.create_update_request(name="Updated")
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Accumulator not found"},
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_user_accumulator(
                accumulator_id=uuid4(),
                request=request,
                credentials=TestDataFactory.create_auth_credentials(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.accumulator.accumulator_views.update_accumulator_service')
    @pytest.mark.asyncio
    async def test_update_user_accumulator_forbidden(self, mock_service):
        """Test update_user_accumulator when user lacks permission."""
        request = TestDataFactory.create_update_request(name="Updated")
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "You don't have permission to update this accumulator"},
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_user_accumulator(
                accumulator_id=uuid4(),
                request=request,
                credentials=TestDataFactory.create_auth_credentials(),
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.accumulator.accumulator_views.update_accumulator_service')
    @pytest.mark.asyncio
    async def test_update_user_accumulator_invalid_token(self, mock_service):
        """Test update_user_accumulator with invalid authentication token."""
        request = TestDataFactory.create_update_request(name="Updated")
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

        with pytest.raises(HTTPException) as exc_info:
            await update_user_accumulator(
                accumulator_id=uuid4(),
                request=request,
                credentials=TestDataFactory.create_auth_credentials(token="invalid_token"),
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteUserAccumulator:
    """Test cases for delete_user_accumulator endpoint."""

    @patch('pecha_api.accumulator.accumulator_views.delete_accumulator_service')
    @pytest.mark.asyncio
    async def test_delete_user_accumulator_success(self, mock_service):
        """Test successful deletion of user accumulator."""
        token = "valid_token"
        accumulator_id = uuid4()
        mock_service.return_value = None

        result = await delete_user_accumulator(
            accumulator_id=accumulator_id,
            credentials=TestDataFactory.create_auth_credentials(token=token),
        )

        assert result is None
        mock_service.assert_called_once_with(token=token, accumulator_id=accumulator_id)

    @patch('pecha_api.accumulator.accumulator_views.delete_accumulator_service')
    @pytest.mark.asyncio
    async def test_delete_user_accumulator_not_found(self, mock_service):
        """Test delete_user_accumulator when accumulator doesn't exist."""
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Accumulator not found"},
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_user_accumulator(
                accumulator_id=uuid4(),
                credentials=TestDataFactory.create_auth_credentials(),
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND

    @patch('pecha_api.accumulator.accumulator_views.delete_accumulator_service')
    @pytest.mark.asyncio
    async def test_delete_user_accumulator_forbidden(self, mock_service):
        """Test delete_user_accumulator when user lacks permission."""
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "You don't have permission to delete this accumulator"},
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_user_accumulator(
                accumulator_id=uuid4(),
                credentials=TestDataFactory.create_auth_credentials(),
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.accumulator.accumulator_views.delete_accumulator_service')
    @pytest.mark.asyncio
    async def test_delete_user_accumulator_invalid_token(self, mock_service):
        """Test delete_user_accumulator with invalid authentication token."""
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_user_accumulator(
                accumulator_id=uuid4(),
                credentials=TestDataFactory.create_auth_credentials(token="invalid_token"),
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetUserAccumulatorHistory:
    """Test cases for get_user_accumulator_history endpoint."""

    @patch('pecha_api.accumulator.accumulator_views.get_accumulator_history_service')
    @pytest.mark.asyncio
    async def test_get_user_accumulator_history_success(self, mock_service):
        """Test successful retrieval of user's accumulator history."""
        token = "valid_token"
        accumulator_id = uuid4()

        mock_service.return_value = AccumulatorHistoryResponse(
            accumulators=[
                AccumulatorHistoryDTO(
                    accumulator_id=accumulator_id,
                    name="Mani",
                    description="Compassion",
                    target_count=108,
                    current_count=300,
                    total_counted=300,
                    sessions=[
                        AccumulatorSessionDTO(count=100, created_at=datetime.utcnow()),
                        AccumulatorSessionDTO(count=200, created_at=datetime.utcnow()),
                    ],
                )
            ],
            total=1,
            skip=0,
            limit=20,
        )

        result = await get_user_accumulator_history(
            credentials=TestDataFactory.create_auth_credentials(token=token),
            skip=0,
            limit=20,
        )

        assert isinstance(result, AccumulatorHistoryResponse)
        assert len(result.accumulators) == 1
        assert result.accumulators[0].name == "Mani"
        assert result.accumulators[0].total_counted == 300
        assert len(result.accumulators[0].sessions) == 2
        mock_service.assert_called_once_with(token=token, skip=0, limit=20)

    @patch('pecha_api.accumulator.accumulator_views.get_accumulator_history_service')
    @pytest.mark.asyncio
    async def test_get_user_accumulator_history_empty(self, mock_service):
        """Test get_user_accumulator_history when user has no history."""
        mock_service.return_value = AccumulatorHistoryResponse(
            accumulators=[], total=0, skip=0, limit=20
        )

        result = await get_user_accumulator_history(
            credentials=TestDataFactory.create_auth_credentials(),
            skip=0,
            limit=20,
        )

        assert len(result.accumulators) == 0
        assert result.total == 0

    @patch('pecha_api.accumulator.accumulator_views.get_accumulator_history_service')
    @pytest.mark.asyncio
    async def test_get_user_accumulator_history_invalid_token(self, mock_service):
        """Test get_user_accumulator_history with invalid authentication token."""
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_user_accumulator_history(
                credentials=TestDataFactory.create_auth_credentials(token="invalid_token"),
                skip=0,
                limit=20,
            )

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
