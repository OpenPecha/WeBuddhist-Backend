from unittest.mock import AsyncMock, patch

import pytest

from pecha_api.search.search_openpecha_service import get_multilingual_search_results

TEXT_ID = "BxD11EMUttisysWt8JUyi"
EDITION_ID = "EFN4ITwQp82MKaPxkzP5c"


def _get_mock_content_search_response_():
    """Payload shape returned by OpenPecha GET /v2/content-search."""
    return [
        {
            "text_id": TEXT_ID,
            "edition_id": EDITION_ID,
            "segment_ids": ["u8TdJavkWlgv56IL40n0w"],
            "context_span": {"start": 539000, "end": 539118},
            "match_span": {"start": 539016, "end": 539019},
            "score": 3.0705519,
            "context": "May all beings hear the sound of Dharma",
        },
    ]


def _get_mock_text_payload_():
    """Payload shape returned by OpenPecha GET /v2/texts/{text_id}."""
    return {
        "id": TEXT_ID,
        "language": "en",
        "title": {"en": "The Way of the Bodhisattva"},
        "alt_titles": [],
        "date": "2025-04-05",
        "license": "public",
    }


@pytest.mark.asyncio
async def test_text_id_is_sent_upstream_as_edition_id():
    """The endpoint keeps the `text_id` name, but OpenPecha filters by edition."""
    with patch(
        "pecha_api.search.search_openpecha_service.search_by_content",
        new_callable=AsyncMock,
        return_value=_get_mock_content_search_response_(),
    ) as mock_search_by_content, patch(
        "pecha_api.search.search_service.fetch_text_by_id",
        new_callable=AsyncMock,
        return_value=_get_mock_text_payload_(),
    ):
        await get_multilingual_search_results(
            query="buddha", search_type="exact", text_id=EDITION_ID, skip=0, limit=10
        )

    kwargs = mock_search_by_content.await_args.kwargs
    assert kwargs["edition_id"] == EDITION_ID
    assert "text_id" not in kwargs


@pytest.mark.asyncio
async def test_no_edition_filter_is_sent_when_text_id_is_omitted():
    with patch(
        "pecha_api.search.search_openpecha_service.search_by_content",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock_search_by_content:
        response = await get_multilingual_search_results(query="buddha", skip=0, limit=10)

    assert mock_search_by_content.await_args.kwargs["edition_id"] is None
    assert response.sources == []
    assert response.total == 0


@pytest.mark.asyncio
async def test_results_are_grouped_by_edition_and_report_the_edition_id():
    """Filtering is by edition, and the response reports the edition id as text_id
    (metadata is still fetched from OpenPecha by the real upstream text id)."""
    with patch(
        "pecha_api.search.search_openpecha_service.search_by_content",
        new_callable=AsyncMock,
        return_value=_get_mock_content_search_response_(),
    ), patch(
        "pecha_api.search.search_service.fetch_text_by_id",
        new_callable=AsyncMock,
        return_value=_get_mock_text_payload_(),
    ):
        response = await get_multilingual_search_results(
            query="buddha", text_id=EDITION_ID, skip=0, limit=10
        )

    assert len(response.sources) == 1
    assert response.sources[0].text.text_id == EDITION_ID
    assert response.sources[0].segment_matches[0].pecha_segment_id == "u8TdJavkWlgv56IL40n0w"


@pytest.mark.asyncio
async def test_empty_upstream_result_returns_empty_response():
    with patch(
        "pecha_api.search.search_openpecha_service.search_by_content",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = await get_multilingual_search_results(
            query="buddha", text_id=EDITION_ID, skip=0, limit=10
        )

    assert response.query == "buddha"
    assert response.sources == []
    assert response.total == 0
