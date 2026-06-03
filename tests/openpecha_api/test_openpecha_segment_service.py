import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from openpecha_api.segments.openpecha_segment_service import (
    fetch_related_segments,
    fetch_segment_content,
    fetch_segment_details,
)


def _mock_http_client(response_payload):
    mock_response = MagicMock()
    mock_response.json.return_value = response_payload
    mock_response.raise_for_status = MagicMock()

    mock_http = AsyncMock()
    mock_http.get.return_value = mock_response
    return mock_http


@pytest.mark.asyncio
@patch("openpecha_api.segments.openpecha_segment_service.get_authenticated_open_pecha_client")
async def test_fetch_related_segments(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"items": [{"id": "seg-1"}]}
    )

    result = await fetch_related_segments("seg-1", limit=5, offset=2)

    assert result["items"][0]["id"] == "seg-1"
    http = mock_get_client.return_value.get_async_httpx_client.return_value
    http.get.assert_awaited_once_with(
        "/v2/segments/seg-1/related",
        params={"limit": 5, "offset": 2},
    )


@pytest.mark.asyncio
@patch("openpecha_api.segments.openpecha_segment_service.get_authenticated_open_pecha_client")
async def test_fetch_segment_content_string_response(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        "segment text"
    )

    result = await fetch_segment_content("seg-1")

    assert result == "segment text"


@pytest.mark.asyncio
@patch("openpecha_api.segments.openpecha_segment_service.get_authenticated_open_pecha_client")
async def test_fetch_segment_content_dict_with_content_key(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"content": "from content key"}
    )

    result = await fetch_segment_content("seg-1")

    assert result == "from content key"


@pytest.mark.asyncio
@patch("openpecha_api.segments.openpecha_segment_service.get_authenticated_open_pecha_client")
async def test_fetch_segment_content_dict_with_text_key(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"text": "from text key"}
    )

    result = await fetch_segment_content("seg-1")

    assert result == "from text key"


@pytest.mark.asyncio
@patch("openpecha_api.segments.openpecha_segment_service.get_authenticated_open_pecha_client")
async def test_fetch_segment_content_dict_with_value_key(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"value": "from value key"}
    )

    result = await fetch_segment_content("seg-1")

    assert result == "from value key"


@pytest.mark.asyncio
@patch("openpecha_api.segments.openpecha_segment_service.get_authenticated_open_pecha_client")
async def test_fetch_segment_content_unrecognized_dict_returns_none(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"other": "value"}
    )

    result = await fetch_segment_content("seg-1")

    assert result is None


@pytest.mark.asyncio
@patch("openpecha_api.segments.openpecha_segment_service.get_authenticated_open_pecha_client")
async def test_fetch_segment_details(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"id": "seg-1", "type": "segment"}
    )

    result = await fetch_segment_details("seg-1")

    assert result["id"] == "seg-1"
    http = mock_get_client.return_value.get_async_httpx_client.return_value
    http.get.assert_awaited_once_with("/v2/segments/seg-1")
