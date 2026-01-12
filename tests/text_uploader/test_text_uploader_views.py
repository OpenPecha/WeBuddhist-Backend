from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import pytest

from pecha_api.app import api
from pecha_api.error_contants import ErrorConstants
from pecha_api.text_uploader.text_uploader_response_model import TextUploadResponse

client = TestClient(api)


class TestTextUploaderViews:
    """Test cases for text uploader views."""

    @pytest.fixture
    def mock_text_upload_request(self):
        """Fixture for text upload request data."""
        return {
            "destination_url": "DEVELOPMENT",
            "openpecha_api_url": "DEVELOPMENT",
            "text_id": "test_text_123"
        }

    @pytest.fixture
    def admin_token(self):
        """Fixture for admin authentication token."""
        return "Bearer admin_test_token"

    @pytest.fixture
    def non_admin_token(self):
        """Fixture for non-admin authentication token."""
        return "Bearer non_admin_test_token"

    def test_upload_text_success_with_admin_token(self, mock_text_upload_request, admin_token):
        """Test successful text upload with admin token."""
        with patch("pecha_api.text_uploader.text_uploader_views.pipeline", new_callable=AsyncMock) as mock_pipeline:
            mock_pipeline.return_value = TextUploadResponse(message={"text_1": "instance_1"})

            response = client.post(
                "/text-uploader",
                json=mock_text_upload_request,
                headers={"Authorization": admin_token}
            )

            assert response.status_code == 200
            assert response.json() == {"message": {"text_1": "instance_1"}}
            mock_pipeline.assert_called_once()

    def test_upload_text_forbidden_with_non_admin_token(self, mock_text_upload_request, non_admin_token):
        """Test text upload fails with non-admin token (403 Forbidden)."""
        with patch("pecha_api.text_uploader.pipeline.verify_admin_access") as mock_verify_admin:
            mock_verify_admin.return_value = False

            response = client.post(
                "/text-uploader",
                json=mock_text_upload_request,
                headers={"Authorization": non_admin_token}
            )

            assert response.status_code == 403
            assert response.json()["detail"] == ErrorConstants.ADMIN_ERROR_MESSAGE

    def test_upload_text_unauthorized_without_token(self, mock_text_upload_request):
        """Test text upload fails without authentication token (401 Unauthorized)."""
        response = client.post(
            "/text-uploader",
            json=mock_text_upload_request
        )

        assert response.status_code == 403

    def test_upload_text_invalid_request_missing_destination_url(self, admin_token):
        """Test text upload fails with missing destination_url."""
        invalid_request = {
            "openpecha_api_url": "DEVELOPMENT",
            "text_id": "test_text_123"
        }

        response = client.post(
            "/text-uploader",
            json=invalid_request,
            headers={"Authorization": admin_token}
        )

        assert response.status_code == 422

    def test_upload_text_invalid_request_missing_openpecha_api_url(self, admin_token):
        """Test text upload fails with missing openpecha_api_url."""
        invalid_request = {
            "destination_url": "DEVELOPMENT",
            "text_id": "test_text_123"
        }

        response = client.post(
            "/text-uploader",
            json=invalid_request,
            headers={"Authorization": admin_token}
        )

        assert response.status_code == 422

    def test_upload_text_invalid_request_missing_text_id(self, admin_token):
        """Test text upload fails with missing text_id."""
        invalid_request = {
            "destination_url": "DEVELOPMENT",
            "openpecha_api_url": "DEVELOPMENT"
        }

        response = client.post(
            "/text-uploader",
            json=invalid_request,
            headers={"Authorization": admin_token}
        )

        assert response.status_code == 422

    def test_upload_text_empty_request_body(self, admin_token):
        """Test text upload fails with empty request body."""
        response = client.post(
            "/text-uploader",
            json={},
            headers={"Authorization": admin_token}
        )

        assert response.status_code == 422

    def test_upload_text_pipeline_exception_handling(self, mock_text_upload_request, admin_token):
        """Test that exceptions from pipeline are properly propagated."""
        with patch("pecha_api.text_uploader.text_uploader_views.pipeline", new_callable=AsyncMock) as mock_pipeline:
            mock_pipeline.side_effect = Exception("Pipeline processing failed")

            with pytest.raises(Exception) as exc_info:
                response = client.post(
                    "/text-uploader",
                    json=mock_text_upload_request,
                    headers={"Authorization": admin_token}
                )

            assert str(exc_info.value) == "Pipeline processing failed"

    def test_upload_text_with_special_characters_in_text_id(self, admin_token):
        """Test text upload with special characters in text_id."""
        request_with_special_chars = {
            "destination_url": "DEVELOPMENT",
            "openpecha_api_url": "DEVELOPMENT",
            "text_id": "test_text_!@#$%^&*()"
        }

        with patch("pecha_api.text_uploader.text_uploader_views.pipeline", new_callable=AsyncMock) as mock_pipeline:
            mock_pipeline.return_value = TextUploadResponse(message={"text_special": "instance_special"})

            response = client.post(
                "/text-uploader",
                json=request_with_special_chars,
                headers={"Authorization": admin_token}
            )

            assert response.status_code == 200
            assert response.json() == {"message": {"text_special": "instance_special"}}

    def test_upload_text_with_extra_fields(self, admin_token):
        """Test text upload with extra fields in request (should be ignored by Pydantic)."""
        request_with_extra_fields = {
            "destination_url": "DEVELOPMENT",
            "openpecha_api_url": "DEVELOPMENT",
            "text_id": "test_text_123",
            "extra_field": "should_be_ignored"
        }

        with patch("pecha_api.text_uploader.text_uploader_views.pipeline", new_callable=AsyncMock) as mock_pipeline:
            mock_pipeline.return_value = TextUploadResponse(message={"text_extra": "instance_extra"})

            response = client.post(
                "/text-uploader",
                json=request_with_extra_fields,
                headers={"Authorization": admin_token}
            )

            assert response.status_code == 200
            assert response.json() == {"message": {"text_extra": "instance_extra"}}

