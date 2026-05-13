from unittest.mock import AsyncMock, patch
import pytest
from fastapi import HTTPException, status
import uuid

from pecha_api.error_contants import ErrorConstants
from pecha_api.texts.mappings.mappings_response_models import TextMappingRequest, MappingsModel, TextMapping
from pecha_api.texts.mappings.mappings_service import update_segment_mapping
from pecha_api.texts.segments.segments_models import Mapping
from pecha_api.texts.segments.segments_response_models import SegmentResponse
from pecha_api.texts.segments.segments_enum import SegmentType

@pytest.mark.asyncio
async def test_update_segment_mapping_non_admin():
    """Test update fails when user is not admin"""
    # Arrange
    mapping_request = TextMappingRequest(
        text_mappings=[
            TextMapping(
                text_id="text-1",
                segment_id="segment-1",
                mappings=[MappingsModel(parent_text_id="parent-1", segments=["seg-1"])]
            )
        ]
    )

    with patch('pecha_api.texts.mappings.mappings_service.verify_admin_access', return_value=False):
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_segment_mapping(text_mapping_request=mapping_request, token="Bearer token")

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == ErrorConstants.ADMIN_ERROR_MESSAGE


@pytest.mark.asyncio
async def test_update_segment_mapping_invalid_text():
    """Test update fails when text ID doesn't exist"""
    # Arrange
    text_id = "invalid-text"
    segment_id = "f7e14876-a3af-4652-8c84-8df2c046a105"
    parent_text_id = "c87aae38-ea7a-4d2b-ba0e-fd7dc61e68d1"
    parent_segment_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    mapping_request = TextMappingRequest(
        text_mappings=[
            TextMapping(
                text_id=text_id,
                segment_id=segment_id,
                mappings=[MappingsModel(parent_text_id=parent_text_id, segments=[parent_segment_id])]
            )
        ]
    )

    # Create mock objects for valid IDs only (text_id is invalid)
    mock_parent_text = AsyncMock()
    mock_parent_text.id = uuid.UUID(parent_text_id)
    mock_parent_text.pecha_text_id = parent_text_id

    mock_segment_obj = AsyncMock()
    mock_segment_obj.id = uuid.UUID(segment_id)
    mock_segment_obj.pecha_segment_id = segment_id

    mock_parent_segment_obj = AsyncMock()
    mock_parent_segment_obj.id = uuid.UUID(parent_segment_id)
    mock_parent_segment_obj.pecha_segment_id = parent_segment_id

    with patch('pecha_api.texts.mappings.mappings_service.verify_admin_access', return_value=True), \
            patch('pecha_api.texts.mappings.mappings_service.get_texts_by_pecha_text_ids', new_callable=AsyncMock) as mock_get_texts, \
            patch('pecha_api.texts.mappings.mappings_service.get_segments_by_pecha_segment_ids', new_callable=AsyncMock) as mock_get_segments:

        # Return only valid texts (missing text_id)
        mock_get_texts.return_value = [mock_parent_text]
        mock_get_segments.return_value = [mock_segment_obj, mock_parent_segment_obj]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_segment_mapping(text_mapping_request=mapping_request, token="Bearer token")

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert text_id in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_segment_mapping_invalid_segment():
    """Test update fails when segment ID doesn't exist"""
    # Arrange
    text_id = "8749b360-a55e-441c-b541-f7c6ba2f3c61"
    segment_id = "invalid-segment"
    parent_text_id = "c87aae38-ea7a-4d2b-ba0e-fd7dc61e68d1"
    
    mapping_request = TextMappingRequest(
        text_mappings=[
            TextMapping(
                text_id=text_id,
                segment_id=segment_id,
                mappings=[MappingsModel(parent_text_id=parent_text_id, segments=["seg-1"])]
            )
        ]
    )

    # Create mock text objects
    mock_text = AsyncMock()
    mock_text.id = uuid.UUID(text_id)
    mock_text.pecha_text_id = text_id
    
    mock_parent_text = AsyncMock()
    mock_parent_text.id = uuid.UUID(parent_text_id)
    mock_parent_text.pecha_text_id = parent_text_id

    with patch('pecha_api.texts.mappings.mappings_service.verify_admin_access', return_value=True), \
            patch('pecha_api.texts.mappings.mappings_service.get_texts_by_pecha_text_ids', new_callable=AsyncMock) as mock_get_texts, \
            patch('pecha_api.texts.mappings.mappings_service.get_segments_by_pecha_segment_ids', new_callable=AsyncMock) as mock_get_segments:
        
        # Return texts but no segments (segment_id is invalid)
        mock_get_texts.return_value = [mock_text, mock_parent_text]
        mock_get_segments.return_value = []

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_segment_mapping(text_mapping_request=mapping_request, token="Bearer token")

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert segment_id in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_segment_mapping_invalid_parent_text():
    """Test update fails when parent text ID doesn't exist"""
    # Arrange
    text_id = "8749b360-a55e-441c-b541-f7c6ba2f3c61"
    segment_id = "f7e14876-a3af-4652-8c84-8df2c046a105"
    invalid_parent_text_id = "invalid-parent"
    parent_segment_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    mapping_request = TextMappingRequest(
        text_mappings=[
            TextMapping(
                text_id=text_id,
                segment_id=segment_id,
                mappings=[MappingsModel(parent_text_id=invalid_parent_text_id, segments=[parent_segment_id])]
            )
        ]
    )

    # Create mock text object
    mock_text = AsyncMock()
    mock_text.id = uuid.UUID(text_id)
    mock_text.pecha_text_id = text_id

    # Create mock segment objects
    mock_segment_obj = AsyncMock()
    mock_segment_obj.id = uuid.UUID(segment_id)
    mock_segment_obj.pecha_segment_id = segment_id

    mock_parent_segment_obj = AsyncMock()
    mock_parent_segment_obj.id = uuid.UUID(parent_segment_id)
    mock_parent_segment_obj.pecha_segment_id = parent_segment_id

    with patch('pecha_api.texts.mappings.mappings_service.verify_admin_access', return_value=True), \
            patch('pecha_api.texts.mappings.mappings_service.get_texts_by_pecha_text_ids', new_callable=AsyncMock) as mock_get_texts, \
            patch('pecha_api.texts.mappings.mappings_service.get_segments_by_pecha_segment_ids', new_callable=AsyncMock) as mock_get_segments:

        # Return only valid text (missing parent_text_id)
        mock_get_texts.return_value = [mock_text]
        mock_get_segments.return_value = [mock_segment_obj, mock_parent_segment_obj]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_segment_mapping(text_mapping_request=mapping_request, token="Bearer token")

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert invalid_parent_text_id in exc_info.value.detail


@pytest.mark.asyncio
async def test_update_segment_mapping_invalid_parent_segment():
    """Test update fails when parent segment ID doesn't exist"""
    # Arrange
    text_id = "8749b360-a55e-441c-b541-f7c6ba2f3c61"
    segment_id = "f7e14876-a3af-4652-8c84-8df2c046a105"
    parent_text_id = "c87aae38-ea7a-4d2b-ba0e-fd7dc61e68d1"
    invalid_parent_segment = "invalid-seg"
    
    mapping_request = TextMappingRequest(
        text_mappings=[
            TextMapping(
                text_id=text_id,
                segment_id=segment_id,
                mappings=[MappingsModel(parent_text_id=parent_text_id, segments=[invalid_parent_segment])]
            )]
    )

    # Create mock text objects
    mock_text = AsyncMock()
    mock_text.id = uuid.UUID(text_id)
    mock_text.pecha_text_id = text_id
    
    mock_parent_text = AsyncMock()
    mock_parent_text.id = uuid.UUID(parent_text_id)
    mock_parent_text.pecha_text_id = parent_text_id

    # Create mock segment object
    mock_segment_obj = AsyncMock()
    mock_segment_obj.id = uuid.UUID(segment_id)
    mock_segment_obj.pecha_segment_id = segment_id

    with patch('pecha_api.texts.mappings.mappings_service.verify_admin_access', return_value=True), \
            patch('pecha_api.texts.mappings.mappings_service.get_texts_by_pecha_text_ids', new_callable=AsyncMock) as mock_get_texts, \
            patch('pecha_api.texts.mappings.mappings_service.get_segments_by_pecha_segment_ids', new_callable=AsyncMock) as mock_get_segments:
        
        # Return texts and segment but not parent segment (invalid_parent_segment is missing)
        mock_get_texts.return_value = [mock_text, mock_parent_text]
        mock_get_segments.return_value = [mock_segment_obj]

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await update_segment_mapping(text_mapping_request=mapping_request, token="Bearer token")

        assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert invalid_parent_segment in exc_info.value.detail
