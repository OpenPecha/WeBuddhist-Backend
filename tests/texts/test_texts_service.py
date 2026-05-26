from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException

from pecha_api.texts.texts_service import (
    extract_title_for_language,
    get_titles_and_ids_by_query,
)


@pytest.mark.asyncio
async def test_get_titles_and_ids_by_query_success():
    """Test get_titles_and_ids_by_query returns title search results."""
    mock_response_data = [
        {"title": {"en": "A Title"}, "language": "en"},
        {"title": {"bo": "མཚན"}, "language": "bo"},
        {"title": {"en": "A Title"}, "language": "en"},
    ]

    mock_http_response = Mock()
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_http_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    class MockText:
        def __init__(self, text_id: str, title: str):
            self.id = text_id
            self.title = title

    mock_texts = [
        MockText(text_id="id_1", title="A Title"),
        MockText(text_id="id_2", title="མཚན"),
    ]

    with patch("pecha_api.texts.texts_service.EXTERNAL_TITLE_SEARCH_API_URL", "https://external.example"), patch(
        "httpx.AsyncClient", return_value=mock_client
    ), patch(
        "pecha_api.texts.texts_service.get_texts_by_titles",
        new_callable=AsyncMock,
        return_value=mock_texts,
    ) as mock_get_texts:
        result = await get_titles_and_ids_by_query(
            title="Test",
            author=None,
            limit=20,
            offset=0,
        )

    assert len(result) == 2
    assert result[0].id == "id_1"
    assert result[0].title == "A Title"
    assert result[1].id == "id_2"
    assert result[1].title == "མཚན"

    call_args = mock_client.get.call_args
    assert call_args.kwargs["params"]["title"] == "Test"
    assert call_args.kwargs["params"]["limit"] == 20
    assert call_args.kwargs["params"]["offset"] == 0

    mock_get_texts.assert_awaited_once()
    called_titles = mock_get_texts.call_args.kwargs["titles"]
    assert "A Title" in called_titles
    assert "མཚན" in called_titles


def test_extract_title_for_language_variants():
    """Test extract_title_for_language with dict, string, and other payloads."""
    assert extract_title_for_language({"bo": "མཚན", "en": "Title"}, "bo") == "མཚན"
    assert extract_title_for_language({"en": "  ", "zh": "Title"}, "fr") == "Title"
    assert extract_title_for_language("  A Title  ", "bo") == "A Title"
    assert extract_title_for_language(12345, "bo") is None


@pytest.mark.asyncio
async def test_get_titles_and_ids_by_query_requires_title_or_author():
    """Test get_titles_and_ids_by_query requires title or author."""
    with pytest.raises(HTTPException) as exc_info:
        await get_titles_and_ids_by_query(title=None, author=None, limit=10, offset=0)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_titles_and_ids_by_query_missing_external_url():
    """Test get_titles_and_ids_by_query raises when API URL is missing."""
    with patch("pecha_api.texts.texts_service.EXTERNAL_TITLE_SEARCH_API_URL", None):
        with pytest.raises(HTTPException) as exc_info:
            await get_titles_and_ids_by_query(title="Test", author=None, limit=10, offset=0)

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_get_titles_and_ids_by_query_author_param_and_empty_titles():
    """Test get_titles_and_ids_by_query with author-only and no valid titles."""
    mock_response_data = [
        {"title": {"en": "  "}},
        "not-a-dict",
    ]

    mock_http_response = Mock()
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.raise_for_status = Mock()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_http_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("pecha_api.texts.texts_service.EXTERNAL_TITLE_SEARCH_API_URL", "https://external.example"), patch(
        "httpx.AsyncClient", return_value=mock_client
    ), patch("pecha_api.texts.texts_service.get_texts_by_titles", new_callable=AsyncMock) as mock_get_texts:
        result = await get_titles_and_ids_by_query(
            title=None,
            author="Author",
            limit=20,
            offset=0,
        )

    assert result == []
    call_args = mock_client.get.call_args
    assert call_args.kwargs["params"]["author"] == "Author"
    assert "title" not in call_args.kwargs["params"]
    mock_get_texts.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_titles_and_ids_by_query_http_status_error():
    """Test get_titles_and_ids_by_query handles HTTPStatusError."""
    mock_request = httpx.Request("GET", "https://external.example/v2/texts")
    mock_response = httpx.Response(500, request=mock_request)

    mock_http_response = Mock()
    mock_http_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Server error",
        request=mock_request,
        response=mock_response,
    )

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_http_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("pecha_api.texts.texts_service.EXTERNAL_TITLE_SEARCH_API_URL", "https://external.example"), patch(
        "httpx.AsyncClient", return_value=mock_client
    ), patch(
        "pecha_api.texts.texts_service.handle_http_status_error",
        side_effect=HTTPException(status_code=502, detail="Bad Gateway"),
    ) as mock_handle:
        with pytest.raises(HTTPException) as exc_info:
            await get_titles_and_ids_by_query(title="Test", author=None, limit=10, offset=0)

    assert exc_info.value.status_code == 502
    mock_handle.assert_called_once()


@pytest.mark.asyncio
async def test_get_titles_and_ids_by_query_request_error():
    """Test get_titles_and_ids_by_query handles RequestError."""
    mock_request = httpx.Request("GET", "https://external.example/v2/texts")
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("Network error", request=mock_request))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("pecha_api.texts.texts_service.EXTERNAL_TITLE_SEARCH_API_URL", "https://external.example"), patch(
        "httpx.AsyncClient", return_value=mock_client
    ), patch(
        "pecha_api.texts.texts_service.handle_request_error",
        side_effect=HTTPException(status_code=503, detail="Service unavailable"),
    ) as mock_handle:
        with pytest.raises(HTTPException) as exc_info:
            await get_titles_and_ids_by_query(title="Test", author=None, limit=10, offset=0)

    assert exc_info.value.status_code == 503
    mock_handle.assert_called_once()
