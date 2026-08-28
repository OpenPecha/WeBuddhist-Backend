import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from openpecha_api.text.openpecha_text_service import fetch_texts_by_category, fetch_text_by_id


def _mock_http_client(response_payload):
    mock_response = MagicMock()
    mock_response.json.return_value = response_payload
    mock_response.raise_for_status = MagicMock()

    mock_http = AsyncMock()
    mock_http.get.return_value = mock_response
    return mock_http


@pytest.mark.asyncio
@patch("openpecha_api.text.openpecha_text_service.get_authenticated_open_pecha_client")
async def test_fetch_texts_by_category(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"items": [{"id": "t1"}]}
    )

    result = await fetch_texts_by_category("cat-1", language="en", limit=10, offset=0)

    assert result["items"][0]["id"] == "t1"
    http = mock_get_client.return_value.get_async_httpx_client.return_value
    http.get.assert_awaited_once_with(
        "/v2/texts",
        params={"category_id": "cat-1", "limit": 10, "offset": 0, "language": "en"},
    )


@pytest.mark.asyncio
@patch("openpecha_api.text.openpecha_text_service.get_authenticated_open_pecha_client")
async def test_fetch_texts_by_category_omits_category_id_when_not_provided(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"items": []}
    )

    await fetch_texts_by_category(limit=10, offset=0)

    http = mock_get_client.return_value.get_async_httpx_client.return_value
    params = http.get.await_args.kwargs["params"]
    assert "category_id" not in params
    assert params == {"limit": 10, "offset": 0}


@pytest.mark.asyncio
@patch("openpecha_api.text.openpecha_text_service.get_authenticated_open_pecha_client")
async def test_fetch_texts_by_category_omits_title_when_not_provided(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"items": []}
    )

    await fetch_texts_by_category("cat-1", limit=10, offset=0)

    http = mock_get_client.return_value.get_async_httpx_client.return_value
    params = http.get.await_args.kwargs["params"]
    assert "title" not in params


@pytest.mark.asyncio
@patch("openpecha_api.text.openpecha_text_service.get_authenticated_open_pecha_client")
async def test_fetch_texts_by_category_omits_title_when_empty_string(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"items": []}
    )

    await fetch_texts_by_category("cat-1", title="", limit=10, offset=0)

    http = mock_get_client.return_value.get_async_httpx_client.return_value
    params = http.get.await_args.kwargs["params"]
    assert "title" not in params


@pytest.mark.asyncio
@patch("openpecha_api.text.openpecha_text_service.get_authenticated_open_pecha_client")
async def test_fetch_texts_by_category_with_title_filter(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"items": [{"id": "t1"}]}
    )

    result = await fetch_texts_by_category(
        "cat-1", language="en", title="sutra", limit=10, offset=0
    )

    assert result["items"][0]["id"] == "t1"
    http = mock_get_client.return_value.get_async_httpx_client.return_value
    http.get.assert_awaited_once_with(
        "/v2/texts",
        params={
            "category_id": "cat-1",
            "limit": 10,
            "offset": 0,
            "language": "en",
            "title": "sutra",
        },
    )


@pytest.mark.asyncio
@patch("openpecha_api.text.openpecha_text_service.get_authenticated_open_pecha_client")
async def test_fetch_text_by_id(mock_get_client):
    mock_get_client.return_value.get_async_httpx_client.return_value = _mock_http_client(
        {"id": "t1", "title": {"en": "Title"}}
    )

    result = await fetch_text_by_id("t1")

    assert result["id"] == "t1"
    http = mock_get_client.return_value.get_async_httpx_client.return_value
    http.get.assert_awaited_once_with("/v2/texts/t1")
