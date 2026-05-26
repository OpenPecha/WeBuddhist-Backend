from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient
from starlette import status

from pecha_api.app import api
from pecha_api.texts.texts_response_models import TitleSearchResult


@pytest.mark.asyncio
async def test_search_titles_success(mocker):
    """Test GET /texts/title-search returns title search results."""
    mock_results = [
        TitleSearchResult(id="text_1", title="A Title"),
        TitleSearchResult(id="text_2", title="Another Title"),
    ]

    mock_search_titles = mocker.patch(
        "pecha_api.texts.texts_views.get_titles_and_ids_by_query",
        new_callable=AsyncMock,
        return_value=mock_results,
    )

    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get("/texts/title-search?title=Test&limit=20&offset=0")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"id": "text_1", "title": "A Title"},
        {"id": "text_2", "title": "Another Title"},
    ]

    mock_search_titles.assert_called_once_with(
        title="Test",
        author=None,
        limit=20,
        offset=0,
    )
