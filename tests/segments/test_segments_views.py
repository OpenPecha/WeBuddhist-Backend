from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import status
from pecha_api.app import api

from pecha_api.texts.segments.segments_response_models import (
    SegmentDTO,
    SegmentResponse,
)


from pecha_api.texts.segments.segments_enum import SegmentType

client = TestClient(api)


@patch("pecha_api.texts.segments.segments_views.search_segments_by_content_service")
def test_search_segments_success(mock_search_segments_by_content_service):
    segment_id = "seg-1"
    mock_response = SegmentResponse(
        segments=[
            SegmentDTO(
                id=segment_id,
                pecha_segment_id="pecha-seg-1",
                text_id="text_id",
                content="བོད་ཀྱི་རིག་གནས།",
                mapping=[],
                type=SegmentType.SOURCE,
            )
        ]
    )
    mock_search_segments_by_content_service.return_value = mock_response

    response = client.post(
        "/api/v1/segments/search",
        json={"content": "རིག་གནས"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["segments"]) == 1
    assert data["segments"][0]["id"] == segment_id
    assert data["segments"][0]["content"] == "བོད་ཀྱི་རིག་གནས།"
    mock_search_segments_by_content_service.assert_called_once()


def test_search_segments_empty_content_validation_error():
    response = client.post(
        "/api/v1/segments/search",
        json={"content": ""},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@patch("pecha_api.texts.segments.segments_views.search_segments_by_content_service")
def test_search_segments_no_results(mock_search_segments_by_content_service):
    mock_search_segments_by_content_service.return_value = SegmentResponse(segments=[])

    response = client.post(
        "/api/v1/segments/search",
        json={"content": "nonexistent content"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["segments"] == []
