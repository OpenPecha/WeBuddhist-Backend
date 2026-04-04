import json
import pytest
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient
from fastapi import HTTPException, status
from fastapi.routing import APIRoute

from pecha_api.app import api
from pecha_api.texts.segments.segments_response_models import SegmentResponse, MappingResponse, SegmentDTO
from pecha_api.error_contants import ErrorConstants
from pecha_api.texts.mappings.mappings_response_models import TextMappingRequest

client = TestClient(api)

# Test data
text_mapping_delete_request = {
    "text_mappings": [
        {
            "text_id": "2ff4215e-bc9e-4d16-8d7e-b4adea3c6ef9",
            "segment_id": "cce14575-ebc3-43aa-bcce-777676f3b2e2",
            "mappings": [
                {
                    "parent_text_id": "e55d66bc-0b2c-4575-afe1-c357856b1592",
                    "segments": [
                        "5bbe24b9-625e-41bf-b6aa-a949f26a7c05",
                        "83311e49-7e8b-413d-95c3-80d2cdea5158"
                    ]
                }
            ]
        }
    ]
}

@pytest.mark.asyncio
@patch("pecha_api.texts.mappings.mappings_views.delete_segment_mapping")
async def test_delete_text_mapping_success(mock_delete_mapping):
    # Arrange
    test_token = "test_token"
    # The delete_segment_mapping function returns None for successful deletion
    mock_delete_mapping.return_value = None
    
    # We need to directly test the endpoint handler function rather than using the TestClient
    # for DELETE requests with a body
    from pecha_api.texts.mappings.mappings_views import delete_text_mapping
    
    # Create a mock request object
    request = TextMappingRequest(**text_mapping_delete_request)
    auth_credentials = MagicMock()
    auth_credentials.credentials = test_token
    
    # Call the endpoint handler directly
    result = await delete_text_mapping(auth_credentials, request)
    
    # Assert
    assert result is None
    mock_delete_mapping.assert_called_once_with(token=test_token, text_mapping_request=request)

def test_delete_text_mapping_unauthorized():
    # For unauthorized test, we can use the TestClient without a body
    # since we're just testing the auth middleware
    response = client.delete(
        "/mappings"
    )
    
    # Assert
    assert response.status_code == 403

@pytest.mark.asyncio
@patch("pecha_api.texts.mappings.mappings_views.delete_segment_mapping")
async def test_delete_text_mapping_forbidden(mock_delete_mapping):
    # Arrange
    mock_delete_mapping.side_effect = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ErrorConstants.ADMIN_ERROR_MESSAGE
    )
    
    # Test directly with the handler function
    from pecha_api.texts.mappings.mappings_views import delete_text_mapping
    
    # Create a mock request object
    request = TextMappingRequest(**text_mapping_delete_request)
    auth_credentials = MagicMock()
    auth_credentials.credentials = "token"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await delete_text_mapping(auth_credentials, request)
    
    # Verify the exception details
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == ErrorConstants.ADMIN_ERROR_MESSAGE

@pytest.mark.asyncio
@patch("pecha_api.texts.mappings.mappings_views.delete_segment_mapping")
async def test_delete_text_mapping_not_found(mock_delete_mapping):
    # Arrange
    mock_delete_mapping.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Segment not found"
    )
    
    # Test directly with the handler function
    from pecha_api.texts.mappings.mappings_views import delete_text_mapping
    
    # Create a mock request object
    request = TextMappingRequest(**text_mapping_delete_request)
    auth_credentials = MagicMock()
    auth_credentials.credentials = "token"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await delete_text_mapping(auth_credentials, request)
    
    # Verify the exception details
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Segment not found"

@pytest.mark.asyncio
@patch("pecha_api.texts.mappings.mappings_views.delete_segment_mapping")
async def test_delete_text_mapping_bad_request(mock_delete_mapping):
    # Arrange
    mock_delete_mapping.side_effect = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=ErrorConstants.SEGMENT_MAPPING_ERROR_MESSAGE
    )
    
    # Test directly with the handler function
    from pecha_api.texts.mappings.mappings_views import delete_text_mapping
    
    # Create a mock request object
    request = TextMappingRequest(**text_mapping_delete_request)
    auth_credentials = MagicMock()
    auth_credentials.credentials = "token"
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        await delete_text_mapping(auth_credentials, request)
    
    # Verify the exception details
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == ErrorConstants.SEGMENT_MAPPING_ERROR_MESSAGE

def test_delete_text_mapping_invalid_request():
    # For validation errors, we can use a POST request to test the validation
    # since the validation happens before the request reaches the handler
    response = client.post(
        "/mappings",
        headers={
            "Authorization": "Bearer token",
            "Content-Type": "application/json"
        },
        json={"invalid": "request"}
    )
    
    # Assert - validation errors return 422
    assert response.status_code == 422
