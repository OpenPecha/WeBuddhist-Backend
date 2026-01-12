import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch

from pecha_api.error_contants import ErrorConstants
from pecha_api.text_uploader.pipeline import pipeline
from pecha_api.text_uploader.text_metadata.text_metadata_model import TextInstanceIds
from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest


@pytest.mark.asyncio
async def test_pipeline_raises_403_when_not_admin():
    request = TextUploadRequest(
        destination_url="LOCAL",
        openpecha_api_url="DEVELOPMENT",
        text_id="T1",
    )

    with patch("pecha_api.text_uploader.pipeline.verify_admin_access", return_value=False):
        with pytest.raises(HTTPException) as exc:
            await pipeline(text_upload_request=request, token="tok")

    assert exc.value.status_code == 403
    assert exc.value.detail == ErrorConstants.ADMIN_ERROR_MESSAGE


@pytest.mark.asyncio
async def test_pipeline_runs_segment_toc_and_returns_new_texts_when_any_new():
    request = TextUploadRequest(
        destination_url="LOCAL",
        openpecha_api_url="DEVELOPMENT",
        text_id="T1",
    )
    instance_ids = TextInstanceIds(
        new_text={"wb_text_1": "pecha_instance_1"},
        all_text={"T1": "pecha_instance_1"},
    )

    with patch("pecha_api.text_uploader.pipeline.verify_admin_access", return_value=True), patch(
        "pecha_api.text_uploader.pipeline.CollectionService"
    ) as MockCollectionService, patch(
        "pecha_api.text_uploader.pipeline.TextMetadataService"
    ) as MockTextMetadataService, patch(
        "pecha_api.text_uploader.pipeline.SegmentService"
    ) as MockSegmentService, patch(
        "pecha_api.text_uploader.pipeline.TocService"
    ) as MockTocService, patch(
        "pecha_api.text_uploader.pipeline.MappingService"
    ) as MockMappingService:
        MockCollectionService.return_value.upload_collections = AsyncMock()
        MockTextMetadataService.return_value.upload_text_metadata_service = AsyncMock(
            return_value=instance_ids
        )
        MockSegmentService.return_value.upload_segments = AsyncMock()
        MockTocService.return_value.upload_toc = AsyncMock()
        MockMappingService.return_value.trigger_mapping = AsyncMock()

        response = await pipeline(text_upload_request=request, token="tok")

        assert response.message == {"wb_text_1": "pecha_instance_1"}

        # Ensure services are wired with the resolved destination/openpecha URLs.
        payload = MockCollectionService.return_value.upload_collections.await_args.kwargs[
            "text_upload_request"
        ]
        assert payload.destination_url.startswith("http")
        assert payload.openpecha_api_url.startswith("https://")
        assert payload.text_id == "T1"

        MockSegmentService.return_value.upload_segments.assert_awaited_once()
        MockTocService.return_value.upload_toc.assert_awaited_once()
        MockMappingService.return_value.trigger_mapping.assert_not_awaited()


@pytest.mark.asyncio
async def test_pipeline_skips_segment_and_toc_when_no_new_texts():
    request = TextUploadRequest(
        destination_url="LOCAL",
        openpecha_api_url="DEVELOPMENT",
        text_id="T1",
    )
    instance_ids = TextInstanceIds(new_text={}, all_text={"T1": "pecha_instance_1"})

    with patch("pecha_api.text_uploader.pipeline.verify_admin_access", return_value=True), patch(
        "pecha_api.text_uploader.pipeline.CollectionService"
    ) as MockCollectionService, patch(
        "pecha_api.text_uploader.pipeline.TextMetadataService"
    ) as MockTextMetadataService, patch(
        "pecha_api.text_uploader.pipeline.SegmentService"
    ) as MockSegmentService, patch(
        "pecha_api.text_uploader.pipeline.TocService"
    ) as MockTocService, patch(
        "pecha_api.text_uploader.pipeline.MappingService"
    ) as MockMappingService:
        MockCollectionService.return_value.upload_collections = AsyncMock()
        MockTextMetadataService.return_value.upload_text_metadata_service = AsyncMock(
            return_value=instance_ids
        )
        MockMappingService.return_value.trigger_mapping = AsyncMock()

        response = await pipeline(text_upload_request=request, token="tok")

        assert response.message == "All texts are already uploaded"
        assert MockSegmentService.called is False
        assert MockTocService.called is False
        MockMappingService.return_value.trigger_mapping.assert_not_awaited()

        payload = MockCollectionService.return_value.upload_collections.await_args.kwargs[
            "text_upload_request"
        ]
        # Mapping is intentionally skipped when destination_url is LOCAL.


@pytest.mark.asyncio
async def test_pipeline_triggers_mapping_when_destination_is_not_local():
    request = TextUploadRequest(
        destination_url="DEVELOPMENT",
        openpecha_api_url="DEVELOPMENT",
        text_id="T1",
    )
    instance_ids = TextInstanceIds(
        new_text={"wb_text_1": "pecha_instance_1"},
        all_text={"T1": "pecha_instance_1"},
    )

    with patch("pecha_api.text_uploader.pipeline.verify_admin_access", return_value=True), patch(
        "pecha_api.text_uploader.pipeline.CollectionService"
    ) as MockCollectionService, patch(
        "pecha_api.text_uploader.pipeline.TextMetadataService"
    ) as MockTextMetadataService, patch(
        "pecha_api.text_uploader.pipeline.SegmentService"
    ) as MockSegmentService, patch(
        "pecha_api.text_uploader.pipeline.TocService"
    ) as MockTocService, patch(
        "pecha_api.text_uploader.pipeline.MappingService"
    ) as MockMappingService:
        MockCollectionService.return_value.upload_collections = AsyncMock()
        MockTextMetadataService.return_value.upload_text_metadata_service = AsyncMock(
            return_value=instance_ids
        )
        MockSegmentService.return_value.upload_segments = AsyncMock()
        MockTocService.return_value.upload_toc = AsyncMock()
        MockMappingService.return_value.trigger_mapping = AsyncMock()

        response = await pipeline(text_upload_request=request, token="tok")

        assert response.message == {"wb_text_1": "pecha_instance_1"}
        MockMappingService.return_value.trigger_mapping.assert_awaited_once()

        trigger_kwargs = MockMappingService.return_value.trigger_mapping.await_args.kwargs
        assert trigger_kwargs["text_ids"] == {"T1": "pecha_instance_1"}

        called_payload = trigger_kwargs["text_upload_request"]
        # Mapping is triggered with the original (enum) request values, not the resolved URL payload.
        assert called_payload.destination_url == "DEVELOPMENT"
        assert called_payload.openpecha_api_url == "DEVELOPMENT"
        assert called_payload.text_id == "T1"

