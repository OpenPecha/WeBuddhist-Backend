from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from pecha_api.app import api
from pecha_api.texts.segments.segments_response_models import (
    ParentSegment,
    V2RelatedSegmentItem,
    V2SegmentCommentariesResponse,
    V2SegmentResponse,
    V2SegmentTextDetail,
    V2SegmentTextGroup,
    V2SegmentTranslationsResponse,
)

client = TestClient(api)


class TestSegmentsV2GetSegmentEndpoint:
    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_openpecha_segment_details_by_id"
    )
    def test_get_segment_without_text_id(self, mock_service):
        mock_service.return_value = V2SegmentResponse(
            segment_id="seg-1",
            content="Segment content",
        )

        response = client.get("/v2/segments/seg-1")

        assert response.status_code == 200
        data = response.json()
        assert data["segment_id"] == "seg-1"
        assert data["content"] == "Segment content"
        assert data["text"] is None

        mock_service.assert_awaited_once_with(
            segment_id="seg-1",
            text_id=None,
        )

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_openpecha_segment_details_by_id"
    )
    def test_get_segment_with_text_id(self, mock_service):
        mock_service.return_value = V2SegmentResponse(
            segment_id="seg-1",
            content="Segment content",
            text=V2SegmentTextDetail(
                text_id="text-1",
                title="Root Text Title",
                language="bo",
            ),
        )

        response = client.get("/v2/segments/seg-1?text_id=text-1")

        assert response.status_code == 200
        data = response.json()
        assert data["text"]["text_id"] == "text-1"
        assert data["text"]["title"] == "Root Text Title"
        assert data["text"]["language"] == "bo"

        mock_service.assert_awaited_once_with(
            segment_id="seg-1",
            text_id="text-1",
        )


class TestSegmentsV2TranslationsEndpoint:
    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_translations_by_segment_id_from_openpecha"
    )
    def test_get_translations_success(self, mock_service):
        mock_service.return_value = V2SegmentTranslationsResponse(
            parent_segment=ParentSegment(
                segment_id="parent-seg-1",
                content="Parent segment content",
            ),
            translations=[
                V2SegmentTextGroup(
                    text_id="text-trans-1",
                    title="The Way of the Bodhisattva Easy to Read",
                    language="en",
                    segments=[
                        V2RelatedSegmentItem(
                            id="seg-trans-1",
                            content="In the Sanskrit language of India...",
                        ),
                        V2RelatedSegmentItem(
                            id="seg-trans-2",
                            content="Second translation segment",
                        ),
                    ],
                )
            ],
            skip=0,
            limit=10,
            has_more=True,
        )

        response = client.get("/v2/segments/parent-seg-1/translations")

        assert response.status_code == 200
        data = response.json()
        assert data["parent_segment"]["segment_id"] == "parent-seg-1"
        assert data["parent_segment"]["content"] == "Parent segment content"
        assert len(data["translations"]) == 1
        assert data["translations"][0]["text_id"] == "text-trans-1"
        assert data["translations"][0]["title"] == "The Way of the Bodhisattva Easy to Read"
        assert len(data["translations"][0]["segments"]) == 2
        assert data["has_more"] is True

        mock_service.assert_awaited_once_with(
            segment_id="parent-seg-1",
            skip=0,
            limit=10,
        )

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_translations_by_segment_id_from_openpecha"
    )
    def test_get_translations_with_pagination(self, mock_service):
        mock_service.return_value = V2SegmentTranslationsResponse(
            parent_segment=ParentSegment(
                segment_id="parent-seg-1",
                content="Parent segment content",
            ),
            translations=[],
            skip=5,
            limit=3,
            has_more=False,
        )

        response = client.get("/v2/segments/parent-seg-1/translations?skip=5&limit=3")

        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 5
        assert data["limit"] == 3
        assert data["translations"] == []

        mock_service.assert_awaited_once_with(
            segment_id="parent-seg-1",
            skip=5,
            limit=3,
        )


class TestSegmentsV2CommentariesEndpoint:
    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_commentaries_by_segment_id_from_openpecha"
    )
    def test_get_commentaries_success(self, mock_service):
        mock_service.return_value = V2SegmentCommentariesResponse(
            parent_segment=ParentSegment(
                segment_id="parent-seg-1",
                content="Parent segment content",
            ),
            commentaries=[
                V2SegmentTextGroup(
                    text_id="text-comm-1",
                    title="Commentary on Bodhicaryavatara",
                    language="bo",
                    segments=[
                        V2RelatedSegmentItem(
                            id="seg-comm-1",
                            content="Commentary segment content",
                        )
                    ],
                )
            ],
            skip=0,
            limit=10,
            has_more=False,
        )

        response = client.get("/v2/segments/parent-seg-1/commentaries")

        assert response.status_code == 200
        data = response.json()
        assert len(data["commentaries"]) == 1
        assert data["commentaries"][0]["text_id"] == "text-comm-1"
        assert data["commentaries"][0]["language"] == "bo"
        assert data["commentaries"][0]["segments"][0]["content"] == "Commentary segment content"


class TestSegmentsV2ValidationErrors:
    def test_invalid_skip_negative_for_translations(self):
        response = client.get("/v2/segments/parent-seg-1/translations?skip=-1")
        assert response.status_code == 422

    def test_invalid_limit_zero_for_translations(self):
        response = client.get("/v2/segments/parent-seg-1/translations?limit=0")
        assert response.status_code == 422

    def test_invalid_limit_too_large_for_translations(self):
        response = client.get("/v2/segments/parent-seg-1/translations?limit=101")
        assert response.status_code == 422

    def test_invalid_skip_negative_for_commentaries(self):
        response = client.get("/v2/segments/parent-seg-1/commentaries?skip=-1")
        assert response.status_code == 422

    def test_invalid_limit_zero_for_commentaries(self):
        response = client.get("/v2/segments/parent-seg-1/commentaries?limit=0")
        assert response.status_code == 422


class TestSegmentsV2ErrorHandling:
    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_translations_by_segment_id_from_openpecha"
    )
    def test_get_translations_not_found(self, mock_service):
        mock_service.side_effect = HTTPException(
            status_code=404,
            detail="Segment with id 'missing-segment' not found",
        )

        response = client.get("/v2/segments/missing-segment/translations")

        assert response.status_code == 404
        assert "missing-segment" in response.json()["detail"]

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_translations_by_segment_id_from_openpecha"
    )
    def test_get_translations_upstream_error(self, mock_service):
        mock_service.side_effect = HTTPException(
            status_code=502,
            detail="Failed to fetch related segments from upstream service",
        )

        response = client.get("/v2/segments/parent-seg-1/translations")

        assert response.status_code == 502
        assert "upstream" in response.json()["detail"].lower()

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_commentaries_by_segment_id_from_openpecha"
    )
    def test_get_commentaries_upstream_error(self, mock_service):
        mock_service.side_effect = HTTPException(
            status_code=502,
            detail="Failed to fetch related segments from upstream service",
        )

        response = client.get("/v2/segments/parent-seg-1/commentaries")

        assert response.status_code == 502
        assert "upstream" in response.json()["detail"].lower()
