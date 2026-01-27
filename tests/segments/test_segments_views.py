from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import status, HTTPException
from uuid import uuid4
from pecha_api.app import api

from pecha_api.texts.segments.segments_response_models import (
    CreateSegmentRequest, 
    CreateSegment,
    SegmentTranslationsResponse,
    SegmentTranslation,
    SegmentDTO,
    SegmentUpdateRequest,
    SegmentUpdate,
    SegmentContentBulkUpdateRequest,
    SegmentContentUpdate,
)
from pecha_api.texts.texts_response_models import TextDTO


from pecha_api.error_contants import ErrorConstants
from pecha_api.texts.segments.segments_response_models import ParentSegment
from pecha_api.texts.segments.segments_enum import SegmentType

client = TestClient(api)

@patch("pecha_api.texts.segments.segments_views.get_segment_details_by_id")
def test_get_segment_without_text_details_success(mock_get_segment_details_by_id):
    segment_id = str(uuid4())
    mock_response = SegmentDTO(
        id=segment_id,
        text_id="text_id",
        content="content",
        mapping=[],
        type=SegmentType.SOURCE
    )
    mock_get_segment_details_by_id.return_value = mock_response
    response = client.get(f"/api/v1/segments/{segment_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == segment_id
    assert data["text_id"] == "text_id"
    assert data["content"] == "content"
    assert data["text"] is None

@patch("pecha_api.texts.segments.segments_views.get_segment_details_by_id")
def test_get_segment_with_text_details_success(mock_get_segment_details_by_id):
    segment_id = str(uuid4())
    text_id = str(uuid4())
    mock_response = SegmentDTO(
        id=segment_id,
        text_id="text_id",
        content="content",
        mapping=[],
        type=SegmentType.SOURCE,
        text=TextDTO(
            id=text_id,
            title="title",
            language="language",
            type="type",
            group_id="group_id",
            is_published=True,
            created_date="2021-01-01",
            updated_date="2021-01-01",
            published_date="2021-01-01",
            published_by="admin",
            categories=["category1", "category2"],
            parent_id=None
        )
    )
    mock_get_segment_details_by_id.return_value = mock_response
    response = client.get(f"/api/v1/segments/{segment_id}?text_details=True")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == segment_id
    assert data["text"] is not None
    assert data["text"]["id"] == text_id
    assert data["text"]["title"] == "title"


@patch("pecha_api.texts.segments.segments_views.get_translations_by_segment_id")
def test_get_translations_success(mock_get_translations):
    # Mock data
    segment_id = str(uuid4())
    mock_response = SegmentTranslationsResponse(
        parent_segment=ParentSegment(
            segment_id=segment_id,
            content="Test segment content"
        ),
        translations=[
            SegmentTranslation(
                segment_id="segment_id_1",
                text_id="text1",
                title='title',
                source='source',
                language='en',
                content="Translation 1"
            ),
            SegmentTranslation(
                segment_id="segment_id_2",
                text_id="text2",
                title='title2',
                source='source2',
                language='bo',
                content="Translation 2"
            )
        ]
    )
    
    # Mock the service function
    mock_get_translations.return_value = mock_response
    # Make request
    response = client.get(f"/api/v1/segments/{segment_id}/translations")
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["parent_segment"]["segment_id"] == segment_id
    assert data["parent_segment"]["content"] == "Test segment content"
    assert len(data["translations"]) == 2
    
    # Verify first translation
    assert data["translations"][0]["text_id"] == "text1"
    assert data["translations"][0]["title"] == "title"
    assert data["translations"][0]["source"] == "source"
    assert data["translations"][0]["language"] == "en"
    assert data["translations"][0]["content"] == "Translation 1"
    
    # Verify second translation
    assert data["translations"][1]["text_id"] == "text2"
    assert data["translations"][1]["language"] == "bo"

@patch("pecha_api.texts.segments.segments_views.get_translations_by_segment_id")
def test_get_translations_with_pagination(mock_get_translations):
    segment_id = str(uuid4())
    mock_response = SegmentTranslationsResponse(
        parent_segment=ParentSegment(
            segment_id=segment_id,
            content="Test segment content"
        ),
        translations=[
            SegmentTranslation(
                segment_id=f"segment_id_{i}",
                text_id=f"text{i}",
                title=f"title{i}",
                source=f"source{i}",
                language='en',
                content=f"Translation {i}"
            ) for i in range(5)
        ]
    )
    
    mock_get_translations.return_value = mock_response
    response = client.get(f"/api/v1/segments/{segment_id}/translations?skip=2&limit=3")
    
    assert response.status_code == status.HTTP_200_OK
    mock_get_translations.assert_called_with(segment_id=segment_id)

@patch("pecha_api.texts.segments.segments_views.get_translations_by_segment_id")
def test_get_translations_not_found(mock_get_translations):
    segment_id = str(uuid4())
    mock_get_translations.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE
    )
    
    response = client.get(f"/api/v1/segments/{segment_id}/translations")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == ErrorConstants.SEGMENT_NOT_FOUND_MESSAGE

@patch("pecha_api.texts.segments.segments_views.create_new_segment")
def test_create_segment_success(mock_create_segment):
    # Mock data
    segment_id = str(uuid4())
    segment_request = CreateSegmentRequest(
        text_id="text123",
        segments=[
            CreateSegment(
                content="New segment content",
                mapping=[],
                type=SegmentType.SOURCE
            )
        ]
    )
    mock_response = {
        "segments": [
            {
            "id": segment_id,
            "text_id": segment_request.text_id,
            "content": segment_request.segments[0].content,
            "mapping": segment_request.segments[0].mapping,
            "type": segment_request.segments[0].type
            }
        ]

    }
    mock_create_segment.return_value = mock_response
    
    # Make request with auth token
    response = client.post(
        "/api/v1/segments",
        json=segment_request.model_dump(mode="json"),
        headers={"Authorization": "Bearer test_token"}
    )
    
    # Assert response
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    
    # Verify segment
    assert data['segments'][0]["text_id"] == segment_request.text_id
    assert data['segments'][0]["content"] == segment_request.segments[0].content
    assert data['segments'][0]["id"] == segment_id

def test_create_segment_unauthorized():
    segment_request = CreateSegmentRequest(
        text_id="text123",
        segments=[
            CreateSegment(
                content="New segment content",
                mapping=[],
                type=SegmentType.SOURCE
            )
        ]
    )
    
    # Make request without auth token
    response = client.post(
        "/api/v1/segments",
        json=segment_request.model_dump(mode="json")
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

@patch("pecha_api.texts.segments.segments_views.update_segments_service")
def test_update_segment_success(mock_update_segments_service):
    # Mock data
    segment_id = str(uuid4())
    segment_update_request = SegmentUpdateRequest(
        pecha_text_id="pecha_text_123",
        segments=[
            SegmentUpdate(
                pecha_segment_id="pecha_segment_123",
                content="Updated segment content"
            )
        ]
    )
    
    mock_response = SegmentDTO(
        id=segment_id,
        pecha_segment_id="pecha_segment_123",
        text_id="text123",
        content="Updated segment content",
        mapping=[],
        type=SegmentType.SOURCE
    )
    
    mock_update_segments_service.return_value = mock_response
    
    # Make request with auth token
    response = client.put(
        "/api/v1/segments",
        json=segment_update_request.model_dump(mode="json"),
        headers={"Authorization": "Bearer admin_token"}
    )
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK

def test_update_segment_unauthorized():
    segment_update_request = SegmentUpdateRequest(
        pecha_text_id="pecha_text_123",
        segments=[
            SegmentUpdate(
                pecha_segment_id="pecha_segment_123",
                content="Updated segment content"
            )
        ]
    )
    
    # Make request without auth token
    response = client.put(
        "/api/v1/segments",
        json=segment_update_request.model_dump(mode="json")
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN

@patch("pecha_api.texts.segments.segments_views.update_segments_service")
def test_update_segment_forbidden(mock_update_segments_service):
    segment_update_request = SegmentUpdateRequest(
        pecha_text_id="pecha_text_123",
        segments=[
            SegmentUpdate(
                pecha_segment_id="pecha_segment_123",
                content="Updated segment content"
            )
        ]
    )
    
    # Mock the service to raise a 403 Forbidden exception
    mock_update_segments_service.side_effect = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ErrorConstants.ADMIN_ERROR_MESSAGE
    )
    
    # Make request with non-admin token
    response = client.put(
        "/api/v1/segments",
        json=segment_update_request.model_dump(mode="json"),
        headers={"Authorization": "Bearer user_token"}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == ErrorConstants.ADMIN_ERROR_MESSAGE

@patch("pecha_api.texts.segments.segments_views.update_segments_service")
def test_update_segment_text_not_found(mock_update_segments_service):
    segment_update_request = SegmentUpdateRequest(
        pecha_text_id="invalid_pecha_text_id",
        segments=[
            SegmentUpdate(
                pecha_segment_id="pecha_segment_123",
                content="Updated segment content"
            )
        ]
    )
    
    # Mock the service to raise a 404 Not Found exception
    mock_update_segments_service.side_effect = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ErrorConstants.TEXT_NOT_FOUND_MESSAGE
    )
    
    response = client.put(
        "/api/v1/segments",
        json=segment_update_request.model_dump(mode="json"),
        headers={"Authorization": "Bearer admin_token"}
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == ErrorConstants.TEXT_NOT_FOUND_MESSAGE


@patch("pecha_api.texts.segments.segments_views.update_segment_content_bulk_service")
def test_update_segment_content_bulk_success(mock_update_bulk_service):
    request = SegmentContentBulkUpdateRequest(
        segments=[SegmentContentUpdate(id=str(uuid4()), content="Updated content")]
    )

    mock_segment = SegmentDTO(
        id=str(uuid4()),
        pecha_segment_id="pecha-1",
        text_id="text-1",
        content="Updated content",
        mapping=[],
        type=SegmentType.SOURCE,
    )
    mock_update_bulk_service.return_value = [mock_segment]

    response = client.put(
        "/api/v1/segments/content",
        json=request.model_dump(mode="json"),
        headers={"Authorization": "Bearer admin_token"},
    )

    assert response.status_code == status.HTTP_200_OK
    mock_update_bulk_service.assert_called_once()


def test_update_segment_content_bulk_unauthorized():
    request = SegmentContentBulkUpdateRequest(
        segments=[SegmentContentUpdate(id=str(uuid4()), content="Updated content")]
    )

    response = client.put(
        "/api/v1/segments/content",
        json=request.model_dump(mode="json"),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("pecha_api.texts.segments.segments_views.update_segment_content_bulk_service")
def test_update_segment_content_bulk_forbidden(mock_update_bulk_service):
    request = SegmentContentBulkUpdateRequest(
        segments=[SegmentContentUpdate(id=str(uuid4()), content="Updated content")]
    )

    mock_update_bulk_service.side_effect = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=ErrorConstants.ADMIN_ERROR_MESSAGE,
    )

    response = client.put(
        "/api/v1/segments/content",
        json=request.model_dump(mode="json"),
        headers={"Authorization": "Bearer user_token"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == ErrorConstants.ADMIN_ERROR_MESSAGE