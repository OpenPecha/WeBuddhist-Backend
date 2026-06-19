from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.security import HTTPAuthorizationCredentials

from pecha_api.mantra.mantra_count_response_models import (
    MantraCountDetailDTO,
    MantraCountSummaryDTO,
    MantraCountsResponse,
)
from pecha_api.mantra.mantra_count_views import (
    get_user_mantra_count_detail,
    get_user_mantra_counts,
)


class TestDataFactory:
    @staticmethod
    def create_auth_credentials(token="valid_token") -> HTTPAuthorizationCredentials:
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestGetUserMantraCountsEndpoint:
    @patch("pecha_api.mantra.mantra_count_views.get_user_mantra_counts_service")
    def test_get_user_mantra_counts_success(self, mock_service):
        mantra_id = uuid4()
        mock_service.return_value = MantraCountsResponse(
            counts=[
                MantraCountSummaryDTO(
                    mantra_id=mantra_id,
                    mantra_title="Medicine Buddha Mantra",
                    private_count=200,
                    allocated_count=0,
                    total_count=200,
                    updated_at=datetime.now(timezone.utc),
                )
            ],
            total=1,
            skip=0,
            limit=20,
        )

        result = get_user_mantra_counts(
            authentication_credential=TestDataFactory.create_auth_credentials(),
            language="en",
            skip=0,
            limit=20,
        )

        assert result.total == 1
        assert len(result.counts) == 1
        mock_service.assert_called_once_with(
            token="valid_token",
            language="en",
            skip=0,
            limit=20,
        )


class TestGetUserMantraCountDetailEndpoint:
    @patch("pecha_api.mantra.mantra_count_views.get_user_mantra_count_detail_service")
    def test_get_user_mantra_count_detail_success(self, mock_service):
        mantra_id = uuid4()
        mock_service.return_value = MantraCountDetailDTO(
            mantra_id=mantra_id,
            mantra_title="Medicine Buddha Mantra",
            private_count=200,
            allocated_count=0,
            total_count=200,
            allocations=[],
            updated_at=datetime.now(timezone.utc),
        )

        result = get_user_mantra_count_detail(
            mantra_id=mantra_id,
            authentication_credential=TestDataFactory.create_auth_credentials(),
            language="en",
        )

        assert result.mantra_id == mantra_id
        assert result.total_count == 200
        mock_service.assert_called_once_with(
            token="valid_token",
            mantra_id=mantra_id,
            language="en",
        )

    @patch("pecha_api.mantra.mantra_count_views.get_user_mantra_count_detail_service")
    def test_get_user_mantra_count_detail_without_language(self, mock_service):
        mantra_id = uuid4()
        mock_service.return_value = MantraCountDetailDTO(
            mantra_id=mantra_id,
            mantra_title="Medicine Buddha Mantra",
            private_count=200,
            allocated_count=0,
            total_count=200,
            allocations=[],
            updated_at=datetime.now(timezone.utc),
        )

        result = get_user_mantra_count_detail(
            mantra_id=mantra_id,
            authentication_credential=TestDataFactory.create_auth_credentials(),
            language=None,
        )

        assert result.mantra_id == mantra_id
        mock_service.assert_called_once_with(
            token="valid_token",
            mantra_id=mantra_id,
            language=None,
        )
