import pytest
from unittest.mock import AsyncMock, patch

from pecha_api.text_uploader.segments.segment_service import SegmentService
from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest


def test_segment_service_parse_segments_content_slices_base_text():
    service = SegmentService()
    base_text = "abcdef"
    segments = [
        {"id": "s1", "span": {"start": 0, "end": 3}},
        {"id": "s2", "span": {"start": 3, "end": 6}},
    ]

    parsed = service.parse_segments_content(segments_annotation=segments, base_text=base_text)
    assert parsed == [
        {"segment_id": "s1", "content": "abc"},
        {"segment_id": "s2", "content": "def"},
    ]


def test_segment_service_get_annotation_ids_filters_segmentation_only():
    service = SegmentService()
    instance = {
        "annotations": [
            {"type": "topic", "annotation_id": "x"},
            {"type": "segmentation", "annotation_id": "seg_1"},
            {"type": "segmentation", "annotation_id": "seg_2"},
        ]
    }

    assert service.get_annotation_ids(instance) == ["seg_1", "seg_2"]


@pytest.mark.asyncio
async def test_segment_service_is_text_segments_uploaded_true_when_any_segments_exist():
    service = SegmentService()
    with patch(
        "pecha_api.text_uploader.segments.segment_service.get_segments_by_text_id",
        new_callable=AsyncMock,
        return_value=[{"id": "1"}],
    ):
        assert await service.is_text_segments_uploaded("t1") is True


@pytest.mark.asyncio
async def test_segment_service_upload_bulk_segments_batches_and_posts():
    service = SegmentService()
    request = TextUploadRequest(
        destination_url="https://dest.example/api/v1",
        openpecha_api_url="https://openpecha.example",
        text_id="T1",
    )
    segments_content = [{"segment_id": f"s{i}", "content": f"c{i}"} for i in range(401)]

    with patch(
        "pecha_api.text_uploader.segments.segment_service.post_segments",
        new_callable=AsyncMock,
        return_value={"ok": True},
    ) as mock_post:
        await service.upload_bulk_segments(
            text_id="wb_text_1",
            segments_content=segments_content,
            text_upload_request=request,
            token="tok",
        )

    assert mock_post.await_count == 2
    first_payload = mock_post.await_args_list[0].args[0]
    second_payload = mock_post.await_args_list[1].args[0]
    assert first_payload["text_id"] == "wb_text_1"
    assert len(first_payload["segments"]) == 400
    assert len(second_payload["segments"]) == 1
    assert first_payload["segments"][0]["type"] == "source"


@pytest.mark.asyncio
async def test_segment_service_get_segments_by_id_list_calls_repo():
    service = SegmentService()
    request = TextUploadRequest(
        destination_url="https://dest.example/api/v1",
        openpecha_api_url="https://openpecha.example",
        text_id="T1",
    )

    with patch(
        "pecha_api.text_uploader.segments.segment_service.get_segments_by_id",
        new_callable=AsyncMock,
        return_value={"data": [{"id": "ann"}]},
    ) as mock_get:
        result = await service.get_segments_by_id_list("ann_1", request)

    assert result == {"data": [{"id": "ann"}]}
    mock_get.assert_awaited_once_with("ann_1", "https://openpecha.example")


@pytest.mark.asyncio
async def test_segment_service_upload_segments_skips_when_already_uploaded():
    service = SegmentService()
    request = TextUploadRequest(
        destination_url="https://dest.example/api/v1",
        openpecha_api_url="https://openpecha.example",
        text_id="T1",
    )

    with patch.object(
        service, "is_text_segments_uploaded", new_callable=AsyncMock, return_value=True
    ), patch(
        "pecha_api.text_uploader.segments.segment_service.get_segments_annotation",
        new_callable=AsyncMock,
    ) as mock_get_annotation:
        await service.upload_segments(
            text_upload_request=request,
            text_ids={"wb_text_1": "pecha_instance_1"},
            token="tok",
        )

    assert mock_get_annotation.called is False

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pecha_api.text_uploader.segments.segment_service import SegmentService


def test_get_annotation_ids_filters_segmentation_only():
    service = SegmentService()
    instance = {
        "annotations": [
            {"type": "note", "annotation_id": "a0"},
            {"type": "segmentation", "annotation_id": "a1"},
            {"type": "segmentation", "annotation_id": "a2"},
        ]
    }

    assert service.get_annotation_ids(instance) == ["a1", "a2"]


def test_get_annotation_ids_handles_none_annotations():
    service = SegmentService()
    assert service.get_annotation_ids({"annotations": None}) == []


def test_parse_segments_content_slices_base_text():
    service = SegmentService()
    base_text = "abcdef"
    segments_annotation = [
        {"id": "s1", "span": {"start": 0, "end": 2}},
        {"id": "s2", "span": {"start": 2, "end": 6}},
    ]

    assert service.parse_segments_content(segments_annotation, base_text) == [
        {"segment_id": "s1", "content": "ab"},
        {"segment_id": "s2", "content": "cdef"},
    ]


@pytest.mark.asyncio
async def test_is_text_segments_uploaded_true_when_any_segments_exist():
    service = SegmentService()
    with patch(
        "pecha_api.text_uploader.segments.segment_service.get_segments_by_text_id",
        new_callable=AsyncMock,
        return_value=[{"id": "seg_1"}],
    ):
        assert await service.is_text_segments_uploaded("text_1") is True


@pytest.mark.asyncio
async def test_upload_bulk_segments_batches_and_posts_payload():
    service = SegmentService()
    text_upload_request = SimpleNamespace(destination_url="https://dest.example")
    token = "t0k3n"

    # 401 segments -> two batches (400 + 1)
    segments_content = [
        {"segment_id": f"s{i}", "content": f"c{i}"} for i in range(401)
    ]

    with patch(
        "pecha_api.text_uploader.segments.segment_service.post_segments",
        new_callable=AsyncMock,
        return_value={"ok": True},
    ) as mock_post_segments:
        await service.upload_bulk_segments(
            text_id="text_1",
            segments_content=segments_content,
            text_upload_request=text_upload_request,
            token=token,
        )

        assert mock_post_segments.await_count == 2

        first_payload = mock_post_segments.await_args_list[0].args[0]
        second_payload = mock_post_segments.await_args_list[1].args[0]

        assert first_payload["text_id"] == "text_1"
        assert len(first_payload["segments"]) == 400
        assert first_payload["segments"][0] == {
            "pecha_segment_id": "s0",
            "content": "c0",
            "type": "source",
        }

        assert second_payload["text_id"] == "text_1"
        assert len(second_payload["segments"]) == 1
        assert second_payload["segments"][0] == {
            "pecha_segment_id": "s400",
            "content": "c400",
            "type": "source",
        }

        # Verify destination/token plumbing (payload, destination_url, token)
        assert mock_post_segments.await_args_list[0].args[1:] == (
            "https://dest.example",
            token,
        )


