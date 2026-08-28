from unittest.mock import AsyncMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from pecha_api.app import api
from pecha_api.texts.segments.segments_response_models import (
    ParentSegment,
    SegmentRelatedText,
    SegmentResources,
    V2RelatedSegmentItem,
    V2SegmentCommentariesResponse,
    V2SegmentInfo,
    V2SegmentInfoResponse,
    V2SegmentResponse,
    V2SegmentTextDetail,
    V2SegmentTextGroup,
    V2SegmentTranslationsResponse,
)

client = TestClient(api)

SEGMENTS_ROOT = "/segments"


class TestSegmentsV2GetSegmentEndpoint:
    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_openpecha_segment_details_by_id",
        new_callable=AsyncMock,
    )
    def test_get_segment_without_text_id(self, mock_service):
        mock_service.return_value = V2SegmentResponse(
            segment_id="seg-1",
            content="Segment content",
        )

        response = client.get(f"{SEGMENTS_ROOT}/seg-1")

        assert response.status_code == 200
        data = response.json()
        assert data["segment_id"] == "seg-1"
        assert data["content"] == "Segment content"
        assert data["text"] is None

        mock_service.assert_awaited_once_with(
            segment_id="seg-1",
        )

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_openpecha_segment_details_by_id",
        new_callable=AsyncMock,
    )
    def test_get_segment_returns_text_when_service_includes_detail(self, mock_service):
        mock_service.return_value = V2SegmentResponse(
            segment_id="seg-1",
            content="Segment content",
            text=V2SegmentTextDetail(
                text_id="text-1",
                title="Root Text Title",
                language="bo",
            ),
        )

        response = client.get(f"{SEGMENTS_ROOT}/seg-1")

        assert response.status_code == 200
        data = response.json()
        assert data["text"]["text_id"] == "text-1"
        assert data["text"]["title"] == "Root Text Title"
        assert data["text"]["language"] == "bo"

        mock_service.assert_awaited_once_with(
            segment_id="seg-1",
        )


class TestSegmentsV2TranslationsEndpoint:
    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_translations_by_segment_id_from_openpecha",
        new_callable=AsyncMock,
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

        response = client.get(f"{SEGMENTS_ROOT}/parent-seg-1/translations")

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
        "pecha_api.texts.segments.segments_openpecha_views.get_translations_by_segment_id_from_openpecha",
        new_callable=AsyncMock,
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

        response = client.get(f"{SEGMENTS_ROOT}/parent-seg-1/translations?skip=5&limit=3")

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
        "pecha_api.texts.segments.segments_openpecha_views.get_commentaries_by_segment_id_from_openpecha",
        new_callable=AsyncMock,
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

        response = client.get(f"{SEGMENTS_ROOT}/parent-seg-1/commentaries")

        assert response.status_code == 200
        data = response.json()
        assert len(data["commentaries"]) == 1
        assert data["commentaries"][0]["text_id"] == "text-comm-1"
        assert data["commentaries"][0]["language"] == "bo"
        assert data["commentaries"][0]["segments"][0]["content"] == "Commentary segment content"


class TestSegmentsV2ValidationErrors:
    def test_invalid_skip_negative_for_translations(self):
        response = client.get(f"{SEGMENTS_ROOT}/parent-seg-1/translations?skip=-1")
        assert response.status_code == 422

    def test_invalid_limit_zero_for_translations(self):
        response = client.get(f"{SEGMENTS_ROOT}/parent-seg-1/translations?limit=0")
        assert response.status_code == 422

    def test_invalid_limit_too_large_for_translations(self):
        response = client.get(f"{SEGMENTS_ROOT}/parent-seg-1/translations?limit=101")
        assert response.status_code == 422

    def test_invalid_skip_negative_for_commentaries(self):
        response = client.get(f"{SEGMENTS_ROOT}/parent-seg-1/commentaries?skip=-1")
        assert response.status_code == 422

    def test_invalid_limit_zero_for_commentaries(self):
        response = client.get(f"{SEGMENTS_ROOT}/parent-seg-1/commentaries?limit=0")
        assert response.status_code == 422


class TestSegmentsV2ErrorHandling:
    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_translations_by_segment_id_from_openpecha",
        new_callable=AsyncMock,
    )
    def test_get_translations_not_found(self, mock_service):
        mock_service.side_effect = HTTPException(
            status_code=404,
            detail="Segment with id 'missing-segment' not found",
        )

        response = client.get(f"{SEGMENTS_ROOT}/missing-segment/translations")

        assert response.status_code == 404
        assert "missing-segment" in response.json()["detail"]

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_translations_by_segment_id_from_openpecha",
        new_callable=AsyncMock,
    )
    def test_get_translations_upstream_error(self, mock_service):
        mock_service.side_effect = HTTPException(
            status_code=502,
            detail="Failed to fetch related segments from upstream service",
        )

        response = client.get(f"{SEGMENTS_ROOT}/parent-seg-1/translations")

        assert response.status_code == 502
        assert "upstream" in response.json()["detail"].lower()

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_commentaries_by_segment_id_from_openpecha",
        new_callable=AsyncMock,
    )
    def test_get_commentaries_upstream_error(self, mock_service):
        mock_service.side_effect = HTTPException(
            status_code=502,
            detail="Failed to fetch related segments from upstream service",
        )

        response = client.get(f"{SEGMENTS_ROOT}/parent-seg-1/commentaries")

        assert response.status_code == 502
        assert "upstream" in response.json()["detail"].lower()


class TestSegmentsV2InfoEndpoint:
    """Tests for the GET /segments/{segment_id}/info endpoint."""

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_segment_info_by_id_from_openpecha",
        new_callable=AsyncMock,
    )
    def test_get_segment_info_success(self, mock_service):
        """Test successful retrieval of segment info."""
        mock_service.return_value = V2SegmentInfoResponse(
            segment_info=V2SegmentInfo(
                segment_id="048576e2-b2bc-4275-9d6c-220ca7357f3c",
                text_id="e159959d-2c0c-4f48-b02c-fbdc8c4a98e3",
                translations=5,
                related_text=SegmentRelatedText(
                    commentaries=7,
                    root_text=0,
                ),
                resources=SegmentResources(
                    sheets=0,
                ),
            )
        )

        response = client.get(f"{SEGMENTS_ROOT}/048576e2-b2bc-4275-9d6c-220ca7357f3c/info")

        assert response.status_code == 200
        data = response.json()
        assert data["segment_info"]["segment_id"] == "048576e2-b2bc-4275-9d6c-220ca7357f3c"
        assert data["segment_info"]["text_id"] == "e159959d-2c0c-4f48-b02c-fbdc8c4a98e3"
        assert data["segment_info"]["translations"] == 5
        assert data["segment_info"]["related_text"]["commentaries"] == 7
        assert data["segment_info"]["related_text"]["root_text"] == 0
        assert data["segment_info"]["resources"]["sheets"] == 0

        mock_service.assert_awaited_once_with(
            segment_id="048576e2-b2bc-4275-9d6c-220ca7357f3c",
        )

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_segment_info_by_id_from_openpecha",
        new_callable=AsyncMock,
    )
    def test_get_segment_info_with_root_text(self, mock_service):
        """Test segment info when text is a translation (has root_text)."""
        mock_service.return_value = V2SegmentInfoResponse(
            segment_info=V2SegmentInfo(
                segment_id="seg-trans-1",
                text_id="text-trans-1",
                translations=0,
                related_text=SegmentRelatedText(
                    commentaries=0,
                    root_text=1,
                ),
                resources=SegmentResources(
                    sheets=0,
                ),
            )
        )

        response = client.get(f"{SEGMENTS_ROOT}/seg-trans-1/info")

        assert response.status_code == 200
        data = response.json()
        assert data["segment_info"]["related_text"]["root_text"] == 1
        assert data["segment_info"]["translations"] == 0

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_segment_info_by_id_from_openpecha",
        new_callable=AsyncMock,
    )
    def test_get_segment_info_with_no_related_texts(self, mock_service):
        """Test segment info when text has no translations or commentaries."""
        mock_service.return_value = V2SegmentInfoResponse(
            segment_info=V2SegmentInfo(
                segment_id="seg-1",
                text_id="text-1",
                translations=0,
                related_text=SegmentRelatedText(
                    commentaries=0,
                    root_text=0,
                ),
                resources=SegmentResources(
                    sheets=0,
                ),
            )
        )

        response = client.get(f"{SEGMENTS_ROOT}/seg-1/info")

        assert response.status_code == 200
        data = response.json()
        assert data["segment_info"]["translations"] == 0
        assert data["segment_info"]["related_text"]["commentaries"] == 0
        assert data["segment_info"]["related_text"]["root_text"] == 0

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_segment_info_by_id_from_openpecha",
        new_callable=AsyncMock,
    )
    def test_get_segment_info_not_found(self, mock_service):
        """Test 404 when segment is not found."""
        mock_service.side_effect = HTTPException(
            status_code=404,
            detail="Segment with id 'missing-segment' not found",
        )

        response = client.get(f"{SEGMENTS_ROOT}/missing-segment/info")

        assert response.status_code == 404
        assert "missing-segment" in response.json()["detail"]

    @patch(
        "pecha_api.texts.segments.segments_openpecha_views.get_segment_info_by_id_from_openpecha",
        new_callable=AsyncMock,
    )
    def test_get_segment_info_text_not_found(self, mock_service):
        """Test 404 when text associated with segment is not found."""
        mock_service.side_effect = HTTPException(
            status_code=404,
            detail="Text with id 'text-123' not found",
        )

        response = client.get(f"{SEGMENTS_ROOT}/seg-1/info")

        assert response.status_code == 404
        assert "text-123" in response.json()["detail"].lower()
