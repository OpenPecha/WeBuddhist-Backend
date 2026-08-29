import pytest
from unittest.mock import patch, AsyncMock, Mock, MagicMock
from uuid import uuid4
from fastapi import HTTPException
from starlette import status

from pecha_api.search.search_response_models import (
    SearchResponse,
    SourceResultItem,
    SheetResultItem,
    TextIndex,
    SegmentMatch,
    SearchType,
    MultilingualSegmentMatch,
    MultilingualSourceResult,
)
from pecha_api.search.search_service import (
    get_search_results,
    get_url_link,
    apply_pagination_to_sources,
    flatten_content_search_matches,
)

TEXT_ID = "BxD11EMUttisysWt8JUyi"
OTHER_TEXT_ID = "0V1UCd0qNSwwIJOEMcZYO"


def _get_mock_content_search_response_():
    """Payload shape returned by OpenPecha GET /v2/content-search."""
    return [
        {
            "text_id": TEXT_ID,
            "edition_id": "EFN4ITwQp82MKaPxkzP5c",
            "segment_ids": ["u8TdJavkWlgv56IL40n0w"],
            "context_span": {"start": 539000, "end": 539118},
            "match_span": {"start": 539016, "end": 539019},
            "score": 3.0705519,
            "context": "May all beings hear the sound of Dharma",
        },
        {
            "text_id": TEXT_ID,
            "edition_id": "EFN4ITwQp82MKaPxkzP5c",
            "segment_ids": ["cGz5CsClCjEB6jOO2Axcq"],
            "context_span": {"start": 539115, "end": 539315},
            "match_span": {"start": 539213, "end": 539216},
            "score": 2.8719563,
            "context": "Suffering, mental distress, various forms of fear",
        },
    ]


def _get_mock_text_payload_(text_id=TEXT_ID):
    """Payload shape returned by OpenPecha GET /v2/texts/{text_id}."""
    return {
        "id": text_id,
        "language": "en",
        "title": {"en": "The Way of the Bodhisattva Claude AI Draft"},
        "alt_titles": [],
        "date": "2025-04-05",
        "license": "public",
    }


@pytest.mark.asyncio
async def test_get_search_results_for_source_success():
    with patch(
        "pecha_api.search.search_service.search_by_content",
        new_callable=AsyncMock,
        return_value=_get_mock_content_search_response_(),
    ), patch(
        "pecha_api.search.search_service.fetch_text_by_id",
        new_callable=AsyncMock,
        return_value=_get_mock_text_payload_(),
    ):
        response = await get_search_results(query="query", search_type=SearchType.SOURCE, skip=0, limit=2)

        assert response is not None
        assert isinstance(response, SearchResponse)
        assert response.sheets == []
        assert response.sources != []
        assert response.sources[0] is not None
        assert isinstance(response.sources[0], SourceResultItem)
        assert response.sources[0].text is not None
        assert response.sources[0].text.text_id == TEXT_ID
        assert response.sources[0].text.language == "en"
        assert response.sources[0].text.title == "The Way of the Bodhisattva Claude AI Draft"
        assert response.sources[0].text.published_date == "2025-04-05"
        assert response.sources[0].segment_match is not None
        assert len(response.sources[0].segment_match) == 2
        assert isinstance(response.sources[0].segment_match[0], SegmentMatch)
        assert response.sources[0].segment_match[0].segment_id == "u8TdJavkWlgv56IL40n0w"
        assert response.total == 2
        assert response.search is not None
        assert response.search.text == "query"
        assert response.search.type == SearchType.SOURCE


@pytest.mark.asyncio
async def test_get_search_results_for_source_within_text_success():
    with patch(
        "pecha_api.search.search_service.search_by_content",
        new_callable=AsyncMock,
        return_value=_get_mock_content_search_response_(),
    ) as mock_search, patch(
        "pecha_api.search.search_service.fetch_text_by_id",
        new_callable=AsyncMock,
        return_value=_get_mock_text_payload_(),
    ):
        response = await get_search_results(
            query="query", search_type=SearchType.SOURCE, text_id=TEXT_ID, skip=0, limit=10
        )

        assert response is not None
        assert isinstance(response, SearchResponse)
        assert response.sources != []
        assert len(response.sources) == 1
        assert response.sources[0] is not None
        assert isinstance(response.sources[0], SourceResultItem)
        assert response.sources[0].text is not None
        assert response.sources[0].text.text_id == TEXT_ID
        assert mock_search.await_args.kwargs["text_id"] == TEXT_ID


@pytest.mark.asyncio
async def test_get_search_results_for_source_paginates_across_matches():
    with patch(
        "pecha_api.search.search_service.search_by_content",
        new_callable=AsyncMock,
        return_value=_get_mock_content_search_response_(),
    ), patch(
        "pecha_api.search.search_service.fetch_text_by_id",
        new_callable=AsyncMock,
        return_value=_get_mock_text_payload_(),
    ):
        response = await get_search_results(query="query", search_type=SearchType.SOURCE, skip=1, limit=1)

        assert len(response.sources) == 1
        assert len(response.sources[0].segment_match) == 1
        # Second best match, since skip=1 drops the top-scoring one.
        assert response.sources[0].segment_match[0].segment_id == "cGz5CsClCjEB6jOO2Axcq"
        assert response.total == 2


@pytest.mark.asyncio
async def test_get_search_results_for_source_keeps_match_when_text_lookup_fails():
    """A stale search index must not silently drop results."""
    with patch(
        "pecha_api.search.search_service.search_by_content",
        new_callable=AsyncMock,
        return_value=_get_mock_content_search_response_(),
    ), patch(
        "pecha_api.search.search_service.fetch_text_by_id",
        new_callable=AsyncMock,
        side_effect=Exception("404 Text not found"),
    ):
        response = await get_search_results(query="query", search_type=SearchType.SOURCE, skip=0, limit=10)

        assert len(response.sources) == 1
        assert response.sources[0].text.text_id == TEXT_ID
        assert response.sources[0].text.title == ""
        assert response.sources[0].text.language == ""
        assert len(response.sources[0].segment_match) == 2


@pytest.mark.asyncio
async def test_get_search_results_for_source_upstream_error_returns_empty():
    with patch(
        "pecha_api.search.search_service.search_by_content",
        new_callable=AsyncMock,
        side_effect=Exception("upstream unavailable"),
    ):
        response = await get_search_results(query="query", search_type=SearchType.SOURCE, skip=0, limit=10)

        assert response.sources == []
        assert response.total == 0
        assert response.search.type == SearchType.SOURCE


@pytest.mark.asyncio
async def test_get_search_results_for_source_unexpected_payload_returns_empty():
    with patch(
        "pecha_api.search.search_service.search_by_content",
        new_callable=AsyncMock,
        return_value={"error": "boom"},
    ):
        response = await get_search_results(query="query", search_type=SearchType.SOURCE, skip=0, limit=10)

        assert response.sources == []
        assert response.total == 0


@pytest.mark.asyncio
async def test_get_search_results_for_sheet_returns_empty():
    response = await get_search_results(query="query", search_type=SearchType.SHEET, skip=0, limit=10)

    assert response.sheets == []
    assert response.total == 0
    assert response.search.type == SearchType.SHEET


@pytest.mark.asyncio
async def test_get_search_results_without_search_type_raises_bad_request():
    with pytest.raises(HTTPException) as exc_info:
        await get_search_results(query="query", search_type=None, skip=0, limit=10)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_flatten_content_search_matches_ranks_by_score():
    matches = flatten_content_search_matches(_get_mock_content_search_response_())

    assert [match["pecha_segment_id"] for match in matches] == [
        "u8TdJavkWlgv56IL40n0w",
        "cGz5CsClCjEB6jOO2Axcq",
    ]
    assert matches[0]["relevance_score"] < matches[1]["relevance_score"]
    assert matches[0]["text_id"] == TEXT_ID


def test_flatten_content_search_matches_expands_multi_segment_hits():
    matches = flatten_content_search_matches(
        [{"text_id": TEXT_ID, "segment_ids": ["seg_a", "seg_b"], "score": 1.0, "context": "shared context"}]
    )

    assert len(matches) == 2
    assert {match["pecha_segment_id"] for match in matches} == {"seg_a", "seg_b"}
    assert all(match["content"] == "shared context" for match in matches)


def test_flatten_content_search_matches_keeps_best_hit_per_segment():
    matches = flatten_content_search_matches(
        [
            {"text_id": TEXT_ID, "segment_ids": ["seg_a"], "score": 1.0, "context": "weaker"},
            {"text_id": TEXT_ID, "segment_ids": ["seg_a"], "score": 5.0, "context": "stronger"},
        ]
    )

    assert len(matches) == 1
    assert matches[0]["content"] == "stronger"
    assert matches[0]["relevance_score"] == -5.0


def test_flatten_content_search_matches_skips_hits_without_segments():
    matches = flatten_content_search_matches(
        [
            {"text_id": TEXT_ID, "segment_ids": None, "score": 1.0, "context": "no segments"},
            {"text_id": TEXT_ID, "segment_ids": [""], "score": 1.0, "context": "blank segment"},
        ]
    )

    assert matches == []


@pytest.mark.asyncio
async def test_get_url_link_success():
    """get_url_link resolves the owning text through the OpenPecha segment endpoint."""
    with patch(
        "pecha_api.search.search_service.fetch_segment_details",
        new_callable=AsyncMock,
        return_value={"id": "u8TdJavkWlgv56IL40n0w", "text_id": TEXT_ID},
    ):
        result = await get_url_link("u8TdJavkWlgv56IL40n0w")

        assert result is not None
        assert result.text_id == TEXT_ID
        assert result.segment_id == "u8TdJavkWlgv56IL40n0w"


@pytest.mark.asyncio
async def test_get_url_link_segment_not_found():
    """Upstream 404s surface as a 404, not a 500."""
    with patch(
        "pecha_api.search.search_service.fetch_segment_details",
        new_callable=AsyncMock,
        side_effect=Exception("404 Segment not found"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_url_link("nonexistent_segment_id")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Pecha segment not found"


@pytest.mark.asyncio
async def test_get_url_link_segment_without_text_id():
    with patch(
        "pecha_api.search.search_service.fetch_segment_details",
        new_callable=AsyncMock,
        return_value={"id": "u8TdJavkWlgv56IL40n0w"},
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_url_link("u8TdJavkWlgv56IL40n0w")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Pecha segment not found"


@pytest.mark.asyncio
async def test_get_url_link_with_special_characters():
    with patch(
        "pecha_api.search.search_service.fetch_segment_details",
        new_callable=AsyncMock,
        return_value={"id": "pecha-seg_123-xyz", "text_id": "text-abc-123"},
    ):
        result = await get_url_link("pecha-seg_123-xyz")

        assert result.text_id == "text-abc-123"
        assert result.segment_id == "pecha-seg_123-xyz"


@pytest.mark.asyncio
async def test_get_url_link_with_long_pecha_segment_id():
    long_segment_id = "a" * 500

    with patch(
        "pecha_api.search.search_service.fetch_segment_details",
        new_callable=AsyncMock,
        return_value={"id": long_segment_id, "text_id": TEXT_ID},
    ):
        result = await get_url_link(long_segment_id)

        assert result.text_id == TEXT_ID
        assert result.segment_id == long_segment_id


@pytest.mark.asyncio
async def test_get_url_link_multiple_calls():
    with patch(
        "pecha_api.search.search_service.fetch_segment_details",
        new_callable=AsyncMock,
    ) as mock_get:
        mock_get.return_value = {"id": "seg1", "text_id": "text1"}
        result1 = await get_url_link("seg1")
        assert result1.text_id == "text1"
        assert result1.segment_id == "seg1"

        mock_get.return_value = {"id": "seg2", "text_id": "text2"}
        result2 = await get_url_link("seg2")
        assert result2.text_id == "text2"
        assert result2.segment_id == "seg2"

        assert mock_get.await_count == 2


def test_apply_pagination_to_sources_basic():
    """Test basic pagination with skip and limit"""
    text_info = TextIndex(text_id="text_123", language="bo", title="Test", published_date="")
    
    matches = [
        MultilingualSegmentMatch(segment_id=str(uuid4()), content=f"Content {i}", relevance_score=float(i), pecha_segment_id=f"seg_{i}")
        for i in range(10)
    ]
    
    sources = [MultilingualSourceResult(text=text_info, segment_matches=matches)]
    
    paginated = apply_pagination_to_sources(sources, skip=0, limit=5)
    
    total_matches = sum(len(s.segment_matches) for s in paginated)
    assert total_matches == 5


def test_apply_pagination_to_sources_with_skip():
    """Test pagination with skip parameter"""
    text_info = TextIndex(text_id="text_123", language="bo", title="Test", published_date="")
    
    matches = [
        MultilingualSegmentMatch(segment_id=str(uuid4()), content=f"Content {i}", relevance_score=float(i), pecha_segment_id=f"seg_{i}")
        for i in range(10)
    ]
    
    sources = [MultilingualSourceResult(text=text_info, segment_matches=matches)]
    
    paginated = apply_pagination_to_sources(sources, skip=3, limit=5)
    
    total_matches = sum(len(s.segment_matches) for s in paginated)
    assert total_matches == 5
    
    all_paginated_matches = []
    for source in paginated:
        all_paginated_matches.extend(source.segment_matches)
    
    scores = [m.relevance_score for m in all_paginated_matches]
    assert scores == [3.0, 4.0, 5.0, 6.0, 7.0]


def test_apply_pagination_to_sources_multiple_texts():
    """Test pagination across multiple text sources"""
    text_info_1 = TextIndex(text_id="text_1", language="bo", title="Test 1", published_date="")
    text_info_2 = TextIndex(text_id="text_2", language="en", title="Test 2", published_date="")
    
    matches_1 = [
        MultilingualSegmentMatch(segment_id=str(uuid4()), content=f"Content 1-{i}", relevance_score=float(i), pecha_segment_id=f"seg_1_{i}")
        for i in range(5)
    ]
    
    matches_2 = [
        MultilingualSegmentMatch(segment_id=str(uuid4()), content=f"Content 2-{i}", relevance_score=float(i + 0.5), pecha_segment_id=f"seg_2_{i}")
        for i in range(5)
    ]
    
    sources = [
        MultilingualSourceResult(text=text_info_1, segment_matches=matches_1),
        MultilingualSourceResult(text=text_info_2, segment_matches=matches_2)
    ]
    
    paginated = apply_pagination_to_sources(sources, skip=0, limit=6)
    
    total_matches = sum(len(s.segment_matches) for s in paginated)
    assert total_matches == 6


def test_apply_pagination_to_sources_empty():
    """Test pagination with empty sources"""
    sources = []
    
    paginated = apply_pagination_to_sources(sources, skip=0, limit=10)
    
    assert paginated == []


def test_apply_pagination_to_sources_skip_beyond_total():
    """Test pagination when skip exceeds total results"""
    text_info = TextIndex(text_id="text_123", language="bo", title="Test", published_date="")
    
    matches = [
        MultilingualSegmentMatch(segment_id=str(uuid4()), content=f"Content {i}", relevance_score=float(i), pecha_segment_id=f"seg_{i}")
        for i in range(5)
    ]
    
    sources = [MultilingualSourceResult(text=text_info, segment_matches=matches)]
    
    paginated = apply_pagination_to_sources(sources, skip=10, limit=5)
    
    total_matches = sum(len(s.segment_matches) for s in paginated)
    assert total_matches == 0


def test_apply_pagination_to_sources_sorting():
    """Test that pagination selects top results by relevance score"""
    text_info_1 = TextIndex(text_id="text_1", language="bo", title="Test 1", published_date="")
    text_info_2 = TextIndex(text_id="text_2", language="en", title="Test 2", published_date="")
    
    matches_1 = [
        MultilingualSegmentMatch(segment_id=str(uuid4()), content="A", relevance_score=1.0, pecha_segment_id="seg_a"),
        MultilingualSegmentMatch(segment_id=str(uuid4()), content="C", relevance_score=3.0, pecha_segment_id="seg_c"),
    ]
    
    matches_2 = [
        MultilingualSegmentMatch(segment_id=str(uuid4()), content="B", relevance_score=2.0, pecha_segment_id="seg_b"),
        MultilingualSegmentMatch(segment_id=str(uuid4()), content="D", relevance_score=4.0, pecha_segment_id="seg_d"),
    ]
    
    sources = [
        MultilingualSourceResult(text=text_info_1, segment_matches=matches_1),
        MultilingualSourceResult(text=text_info_2, segment_matches=matches_2)
    ]
    
    paginated = apply_pagination_to_sources(sources, skip=0, limit=2)
    
    all_matches = []
    for source in paginated:
        all_matches.extend(source.segment_matches)
    
    assert len(all_matches) == 2
    scores = sorted([m.relevance_score for m in all_matches])
    assert scores == [1.0, 2.0]
