from unittest.mock import patch

from fastapi.testclient import TestClient
from pecha_api.app import api
from fastapi import HTTPException

from pecha_api.texts.mappings.mappings_response_models import MappingSegmentResponse, MappingSegmentDTO
from pecha_api.texts.segments.segments_response_models import MappingResponse
from pecha_api.texts.segments.segments_enum import SegmentType

client = TestClient(api)

text_mapping_request = {
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


@patch("pecha_api.texts.mappings.mappings_views.update_segment_mapping")
def test_create_text_mapping(mock_update_mapping):
    # Arrange
    test_token = "test_token"
    mapping_response = MappingResponse(
        text_id="e55d66bc-0b2c-4575-afe1-c357856b1592",
        segments=[
            "5bbe24b9-625e-41bf-b6aa-a949f26a7c05",
            "83311e49-7e8b-413d-95c3-80d2cdea5158"
        ]
    )
    section_response = MappingSegmentResponse(
        segments=[
            MappingSegmentDTO(
                id="cce14575-ebc3-43aa-bcce-777676f3b2e2",
                text_id="2ff4215e-bc9e-4d16-8d7e-b4adea3c6ef9",
                type=SegmentType.SOURCE,
                mapping=[mapping_response]

            )
        ]
    )
    mock_update_mapping.return_value = section_response
    response = client.post(
        "/mappings",
        headers={"Authorization": f"Bearer {test_token}"},
        json=text_mapping_request
    )

    # Assert
    assert response.status_code == 201
    assert response.json() == section_response.model_dump(mode="json")


def test_create_text_mapping_403():
    # Act
    response = client.post(
        "/mappings",
        json={"text_id": "123"}
    )

    # Assert
    assert response.status_code == 403


@patch("pecha_api.texts.mappings.mappings_views.update_segment_mapping")
def test_create_text_mapping_404_text_not_found(mock_update_mapping):
    mock_update_mapping.side_effect = HTTPException(
        status_code=404,
        detail="Text not found"
    )

    response = client.post(
        "/mappings",
        headers={"Authorization": "Bearer token"},
        json=text_mapping_request
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Text not found"


@patch("pecha_api.texts.mappings.mappings_views.update_segment_mapping")
def test_create_text_mapping_404_segment_not_found(mock_update_mapping):
    mock_update_mapping.side_effect = HTTPException(
        status_code=404,
        detail="Segment not found"
    )

    response = client.post(
        "/mappings",
        headers={"Authorization": "Bearer token"},
        json=text_mapping_request
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Segment not found"


@patch("pecha_api.texts.mappings.mappings_views.update_segment_mapping")
def test_create_text_mapping_404_parent_text_not_found(mock_update_mapping):
    mock_update_mapping.side_effect = HTTPException(
        status_code=404,
        detail="Parent text not found"
    )

    response = client.post(
        "/mappings",
        headers={"Authorization": "Bearer token"},
        json=text_mapping_request
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Parent text not found"


@patch("pecha_api.texts.mappings.mappings_views.update_segment_mapping")
def test_create_text_mapping_404_parent_segment_not_found(mock_update_mapping):
    mock_update_mapping.side_effect = HTTPException(
        status_code=404,
        detail="Parent segment not found"
    )

    response = client.post(
        "/mappings",
        headers={"Authorization": "Bearer token"},
        json=text_mapping_request
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Parent segment not found"
