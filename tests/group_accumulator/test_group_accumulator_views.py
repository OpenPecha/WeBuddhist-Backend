import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.group_accumulator.group_accumulator_response_models import (
    GroupAccumulatorDetailDTO,
    GroupAccumulatorHistoryResponse,
    GroupAccumulatorHistoryItemDTO,
    SubmitGroupCountRequest,
)

client = TestClient(api)


class TestDataFactory:
    """Factory for creating test data objects."""

    @staticmethod
    def create_group_accumulator_detail(
        id=None,
        group_id=None,
        accumulator_id=None,
        target_count=108000,
        total_count=5000,
    ) -> GroupAccumulatorDetailDTO:
        return GroupAccumulatorDetailDTO(
            id=id or uuid4(),
            accumulator_id=accumulator_id,
            group_id=group_id or uuid4(),
            target_count=target_count,
            start_date=datetime.utcnow(),
            end_date=None,
            total_count=total_count,
            created_at=datetime.utcnow(),
            updated_at=None,
        )

    @staticmethod
    def create_history_item(
        history_id=None,
        user_id=None,
        count=100,
    ) -> GroupAccumulatorHistoryItemDTO:
        return GroupAccumulatorHistoryItemDTO(
            id=history_id or uuid4(),
            user_id=user_id or uuid4(),
            count=count,
            created_at=datetime.utcnow(),
        )

    @staticmethod
    def create_history_response(
        accumulator_detail=None,
        history_items=None,
        total=0,
    ) -> GroupAccumulatorHistoryResponse:
        return GroupAccumulatorHistoryResponse(
            group_accumulator=accumulator_detail or TestDataFactory.create_group_accumulator_detail(),
            history=history_items or [],
            total=total,
            skip=0,
            limit=20,
        )


class TestGetGroupAccumulator:
    """Test cases for GET /group-accumulators/{group_accumulator_id} endpoint."""

    @patch('pecha_api.group_accumulator.group_accumulator_views.get_group_accumulator_service')
    def test_get_group_accumulator_success(self, mock_service):
        """Test successful retrieval of group accumulator details."""
        group_accumulator_id = uuid4()
        mock_service.return_value = TestDataFactory.create_group_accumulator_detail(
            id=group_accumulator_id,
            total_count=5000,
        )

        response = client.get(f"/group-accumulators/{group_accumulator_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(group_accumulator_id)
        assert data["total_count"] == 5000
        mock_service.assert_called_once_with(group_accumulator_id=group_accumulator_id)

    @patch('pecha_api.group_accumulator.group_accumulator_views.get_group_accumulator_service')
    def test_get_group_accumulator_not_found(self, mock_service):
        """Test get group accumulator when accumulator doesn't exist."""
        from fastapi import HTTPException
        accumulator_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
        )

        response = client.get(f"/group-accumulators/{accumulator_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"]["error"] == "NOT_FOUND"


class TestSubmitGroupCount:
    """Test cases for POST /group-accumulators/{group_accumulator_id}/count endpoint."""

    @patch('pecha_api.group_accumulator.group_accumulator_views.submit_group_count_service')
    def test_submit_group_count_success(self, mock_service):
        """Test successful submission of group count."""
        accumulator_id = uuid4()
        user_id = uuid4()
        mock_service.return_value = (
            TestDataFactory.create_history_item(
                user_id=user_id,
                count=100,
            ),
            True,  # is_created
        )

        payload = {"current_count": 100}
        response = client.post(
            f"/group-accumulators/{accumulator_id}",
            json=payload,
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["count"] == 100
        assert data["user_id"] == str(user_id)
        mock_service.assert_called_once()

    @patch('pecha_api.group_accumulator.group_accumulator_views.submit_group_count_service')
    def test_submit_group_count_unauthorized(self, mock_service):
        """Test submit group count without authorization."""
        accumulator_id = uuid4()
        payload = {"current_count": 100}

        response = client.post(
            f"/group-accumulators/{accumulator_id}",
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_service.assert_not_called()

    @patch('pecha_api.group_accumulator.group_accumulator_views.submit_group_count_service')
    def test_submit_group_count_invalid_payload(self, mock_service):
        """Test submit group count with invalid payload."""
        accumulator_id = uuid4()
        payload = {"current_count": -10}

        response = client.post(
            f"/group-accumulators/{accumulator_id}",
            json=payload,
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.assert_not_called()

    @patch('pecha_api.group_accumulator.group_accumulator_views.submit_group_count_service')
    def test_submit_group_count_zero_delta(self, mock_service):
        """Test submit group count when delta is zero (no change) returns 200 OK."""
        accumulator_id = uuid4()
        user_id = uuid4()
        mock_service.return_value = (
            TestDataFactory.create_history_item(
                user_id=user_id,
                count=0,
            ),
            False,  # is_created = False for no-op
        )

        payload = {"current_count": 50}
        response = client.post(
            f"/group-accumulators/{accumulator_id}",
            json=payload,
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == status.HTTP_200_OK  # 200 for no-op, not 201
        data = response.json()
        assert data["count"] == 0

    @patch('pecha_api.group_accumulator.group_accumulator_views.submit_group_count_service')
    def test_submit_group_count_not_member(self, mock_service):
        """Test submit group count when user is not a group member."""
        from fastapi import HTTPException
        accumulator_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "You must be a member of this group"}
        )

        payload = {"current_count": 100}
        response = client.post(
            f"/group-accumulators/{accumulator_id}",
            json=payload,
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "member" in response.json()["detail"]["message"]


class TestUpdateGroupCount:
    """Test cases for PUT /group-accumulators/{group_accumulator_id}/count endpoint."""

    @patch('pecha_api.group_accumulator.group_accumulator_views.submit_group_count_service')
    def test_update_group_count_success(self, mock_service):
        """Test successful update of group count."""
        accumulator_id = uuid4()
        user_id = uuid4()
        mock_service.return_value = (
            TestDataFactory.create_history_item(
                user_id=user_id,
                count=50,
            ),
            True,  # is_created
        )

        payload = {"current_count": 150}
        response = client.put(
            f"/group-accumulators/{accumulator_id}",
            json=payload,
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == status.HTTP_201_CREATED  # 201 when created
        data = response.json()
        assert data["count"] == 50
        mock_service.assert_called_once()

    @patch('pecha_api.group_accumulator.group_accumulator_views.submit_group_count_service')
    def test_update_group_count_unauthorized(self, mock_service):
        """Test update group count without authorization."""
        accumulator_id = uuid4()
        payload = {"current_count": 150}

        response = client.put(
            f"/group-accumulators/{accumulator_id}",
            json=payload,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_service.assert_not_called()


class TestGetGroupAccumulatorHistory:
    """Test cases for GET /group-accumulators/{group_accumulator_id}/count endpoint."""

    @patch('pecha_api.group_accumulator.group_accumulator_views.get_group_accumulator_history_service')
    def test_get_history_success(self, mock_service):
        """Test successful retrieval of group accumulator history."""
        accumulator_id = uuid4()
        history_items = [
            TestDataFactory.create_history_item(count=100),
            TestDataFactory.create_history_item(count=50),
        ]
        mock_service.return_value = TestDataFactory.create_history_response(
            history_items=history_items,
            total=2,
        )

        response = client.get(f"/group-accumulators/{accumulator_id}/history")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["history"]) == 2
        assert data["total"] == 2
        assert data["skip"] == 0
        assert data["limit"] == 20
        mock_service.assert_called_once_with(
            group_accumulator_id=accumulator_id,
            skip=0,
            limit=20,
        )

    @patch('pecha_api.group_accumulator.group_accumulator_views.get_group_accumulator_history_service')
    def test_get_history_with_pagination(self, mock_service):
        """Test get history with custom pagination parameters."""
        accumulator_id = uuid4()
        mock_service.return_value = TestDataFactory.create_history_response(
            history_items=[TestDataFactory.create_history_item()],
            total=10,
        )

        response = client.get(
            f"/group-accumulators/{accumulator_id}/history",
            params={"skip": 5, "limit": 5}
        )

        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(
            group_accumulator_id=accumulator_id,
            skip=5,
            limit=5,
        )

    @patch('pecha_api.group_accumulator.group_accumulator_views.get_group_accumulator_history_service')
    def test_get_history_empty(self, mock_service):
        """Test get history when no history exists."""
        accumulator_id = uuid4()
        mock_service.return_value = TestDataFactory.create_history_response(
            history_items=[],
            total=0,
        )

        response = client.get(f"/group-accumulators/{accumulator_id}/history")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["history"]) == 0
        assert data["total"] == 0

    @patch('pecha_api.group_accumulator.group_accumulator_views.get_group_accumulator_history_service')
    def test_get_history_not_found(self, mock_service):
        """Test get history when accumulator doesn't exist."""
        from fastapi import HTTPException
        accumulator_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
        )

        response = client.get(f"/group-accumulators/{accumulator_id}/history")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDeleteGroupAccumulator:
    """Test cases for DELETE /group-accumulators/{group_accumulator_id} endpoint."""

    @patch('pecha_api.group_accumulator.group_accumulator_views.delete_group_accumulator_user_service')
    def test_delete_group_accumulator_success(self, mock_service):
        """Test successful soft deletion of group accumulator."""
        group_accumulator_id = uuid4()
        mock_service.return_value = None

        response = client.delete(
            f"/group-accumulators/{group_accumulator_id}",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_service.assert_called_once_with(
            token="valid_token",
            group_accumulator_id=group_accumulator_id,
        )

    @patch('pecha_api.group_accumulator.group_accumulator_views.delete_group_accumulator_user_service')
    def test_delete_group_accumulator_unauthorized(self, mock_service):
        """Test delete group accumulator without authorization."""
        group_accumulator_id = uuid4()

        response = client.delete(
            f"/group-accumulators/{group_accumulator_id}"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        mock_service.assert_not_called()

    @patch('pecha_api.group_accumulator.group_accumulator_views.delete_group_accumulator_user_service')
    def test_delete_group_accumulator_not_member(self, mock_service):
        """Test delete group accumulator when user is not a group member."""
        from fastapi import HTTPException
        group_accumulator_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "You must be a member of this group"}
        )

        response = client.delete(
            f"/group-accumulators/{group_accumulator_id}",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"]["message"] == "You must be a member of this group"

    @patch('pecha_api.group_accumulator.group_accumulator_views.delete_group_accumulator_user_service')
    def test_delete_group_accumulator_not_found(self, mock_service):
        """Test delete group accumulator when it doesn't exist."""
        from fastapi import HTTPException
        group_accumulator_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "NOT_FOUND", "message": "Group accumulator not found"}
        )

        response = client.delete(
            f"/group-accumulators/{group_accumulator_id}",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"]["error"] == "NOT_FOUND"

    @patch('pecha_api.group_accumulator.group_accumulator_views.delete_group_accumulator_user_service')
    def test_delete_group_accumulator_wrong_group(self, mock_service):
        """Test delete group accumulator when it belongs to different group."""
        from fastapi import HTTPException
        group_accumulator_id = uuid4()
        mock_service.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "FORBIDDEN", "message": "Group accumulator does not belong to this group"}
        )

        response = client.delete(
            f"/group-accumulators/{group_accumulator_id}",
            headers={"Authorization": "Bearer valid_token"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"]["error"] == "FORBIDDEN"
