import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from openpecha_api.collection.openpecha_collection_service import fetch_category_by_id


@pytest.mark.asyncio
@patch("openpecha_api.collection.openpecha_collection_service.get_authenticated_open_pecha_client")
async def test_fetch_category_by_id(mock_get_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "cat-1", "title": {"en": "Discourses"}}
    mock_response.raise_for_status = MagicMock()

    mock_http = AsyncMock()
    mock_http.get.return_value = mock_response
    mock_get_client.return_value.get_async_httpx_client.return_value = mock_http

    result = await fetch_category_by_id("cat-1")

    assert result["id"] == "cat-1"
    mock_http.get.assert_awaited_once_with("/v2/categories/cat-1")
