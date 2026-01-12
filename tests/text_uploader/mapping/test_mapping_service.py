import pytest
from unittest.mock import AsyncMock, patch

from pecha_api.text_uploader.mapping.mapping_services import MappingService
from pecha_api.text_uploader.text_uploader_response_model import TextUploadRequest


@pytest.mark.asyncio
async def test_mapping_service_triggers_repo_with_text_ids_and_urls():
    service = MappingService()
    request = TextUploadRequest(
        destination_url="https://dest.example/api/v1",
        openpecha_api_url="https://openpecha.example",
        text_id="T1",
    )

    with patch(
        "pecha_api.text_uploader.mapping.mapping_services.trigger_mapping_repo",
        new_callable=AsyncMock,
    ) as mock_trigger:
        await service.trigger_mapping(
            text_ids={"a": "t1", "b": "t2"},
            text_upload_request=request,
        )

    mock_trigger.assert_awaited_once_with(
        ["t1", "t2"],
        "https://openpecha.example",
        "https://dest.example/api/v1",
    )
