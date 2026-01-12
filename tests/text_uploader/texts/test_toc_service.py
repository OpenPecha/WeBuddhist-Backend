import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pecha_api.text_uploader.table_of_content.toc_service import TocService


@pytest.mark.asyncio
async def test_order_segments_by_annotation_span_sorts_and_numbers():
    service = TocService()
    annotation_segments = {
        "data": [
            {"id": "s2", "span": {"start": 5, "end": 7}},
            {"id": "s1", "span": {"start": 0, "end": 2}},
            {"id": "s3", "span": {"start": 8, "end": 9}},
        ]
    }

    result = await service.order_segments_by_annotation_span(annotation_segments)

    assert result == [
        {"segment_id": "s1", "segment_number": 1},
        {"segment_id": "s2", "segment_number": 2},
        {"segment_id": "s3", "segment_number": 3},
    ]


def test_create_toc_payload_uses_uuid_and_wraps_segments():
    service = TocService()
    ordered_segments = [
        {"segment_id": "s1", "segment_number": 1},
        {"segment_id": "s2", "segment_number": 2},
    ]

    with patch(
        "pecha_api.text_uploader.table_of_content.toc_service.uuid.uuid4",
        return_value="fixed-uuid",
    ):
        payload = service.create_toc_payload(ordered_segments, text_id="t1")

    assert payload == {
        "text_id": "t1",
        "type": "text",
        "sections": [
            {
                "id": "fixed-uuid",
                "title": "1",
                "section_number": 1,
                "segments": ordered_segments,
            }
        ],
    }


@pytest.mark.asyncio
async def test_upload_toc_builds_payload_and_posts():
    service = TocService()
    text_upload_request = SimpleNamespace(
        destination_url="https://dest.example",
        openpecha_api_url="https://openpecha.example",
        text_id="ignored",
    )

    # Mocks for SegmentService instance methods used by TocService
    service.segment_service.get_segments_annotation_by_pecha_text_id = AsyncMock(
        return_value={"annotations": [{"type": "segmentation", "annotation_id": "ann_1"}]}
    )
    # SegmentService.get_annotation_ids is synchronous.
    service.segment_service.get_annotation_ids = lambda _instance: ["ann_1"]
    service.segment_service.get_segments_by_id_list = AsyncMock(
        return_value={
            "data": [
                {"id": "s2", "span": {"start": 2, "end": 3}},
                {"id": "s1", "span": {"start": 0, "end": 1}},
            ]
        }
    )

    with patch(
        "pecha_api.text_uploader.table_of_content.toc_service.uuid.uuid4",
        return_value="fixed-uuid",
    ), patch(
        "pecha_api.text_uploader.table_of_content.toc_service.post_toc",
        new_callable=AsyncMock,
        return_value={"ok": True},
    ) as mock_post_toc:
        await service.upload_toc(
            text_ids={"local_text_1": "pecha_text_1"},
            text_upload_request=text_upload_request,
            token="tok",
        )

        mock_post_toc.assert_awaited_once()
        posted_payload, posted_destination, posted_token = mock_post_toc.await_args.args

        assert posted_destination == "https://dest.example"
        assert posted_token == "tok"
        assert posted_payload["text_id"] == "local_text_1"
        assert posted_payload["sections"][0]["id"] == "fixed-uuid"
        assert posted_payload["sections"][0]["segments"] == [
            {"segment_id": "s1", "segment_number": 1},
            {"segment_id": "s2", "segment_number": 2},
        ]


