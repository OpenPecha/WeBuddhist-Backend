import pytest
from unittest.mock import patch, AsyncMock, Mock, MagicMock
from uuid import uuid4
from fastapi import HTTPException
import httpx

from pecha_api.search.search_response_models import (
    SearchResponse,
    SourceResultItem,
    SheetResultItem,
    TextIndex,
    SegmentMatch,
    SearchType,
    MultilingualSearchResponse,
    MultilingualSourceResult,
    MultilingualSegmentMatch,
    ExternalSearchResponse,
    ExternalSearchResult,
    ExternalSegmentEntity
)
from pecha_api.search.search_service import (
    get_search_results,
    get_multilingual_search_results,
    call_external_search_api,
    build_multilingual_sources,
    apply_pagination_to_sources
)

@pytest.mark.asyncio
async def test_get_search_results_for_source_success():

    mock_elastic_response = _get_mock_elastic_source_response_()

    mock_client = Mock()
    mock_client.search = AsyncMock(return_value=mock_elastic_response)

    with patch("pecha_api.search.search_service.search_client", new_callable=Mock, return_value=mock_client):
        response = await get_search_results(query="query", search_type=SearchType.SOURCE, skip=0, limit=2)

        assert response is not None
        assert isinstance(response, SearchResponse)
        assert response.sheets == []
        assert response.sources != []
        assert response.sources[0] is not None
        assert isinstance(response.sources[0], SourceResultItem)
        assert response.sources[0].text is not None
        assert response.sources[0].text.text_id == "e6370d09-aa0c-4a41-96ef-deffb89c7810"
        assert response.sources[0].text.language == "en"
        assert response.sources[0].text.title == "The Way of the Bodhisattva Claude AI Draft"
        assert response.sources[0].segment_match is not None
        assert len(response.sources[0].segment_match) == 2
        assert isinstance(response.sources[0].segment_match[0], SegmentMatch)
        assert response.sources[0].segment_match[0].segment_id == "2eb76906-f2d5-48ca-9f80-2023ee6b3ad0"
        assert response.search is not None
        assert response.search.text == "query"
        assert response.search.type == SearchType.SOURCE

@pytest.mark.asyncio
async def test_get_search_results_for_source_within_text_success():
    text_id = "e6370d09-aa0c-4a41-96ef-deffb89c7810"
    mock_elastic_response = _get_mock_elastic_source_within_text_response_()
    mock_client = Mock()
    mock_client.search = AsyncMock(return_value=mock_elastic_response)

    with patch("pecha_api.search.search_service.search_client", new_callable=Mock, return_value=mock_client):

        response = await get_search_results(query="query", search_type=SearchType.SOURCE, text_id=text_id, skip=0, limit=10)

        assert response is not None
        assert isinstance(response, SearchResponse)
        assert response.sources != []
        assert len(response.sources) == 1
        assert response.sources[0] is not None
        assert isinstance(response.sources[0], SourceResultItem)
        assert response.sources[0].text is not None
        assert response.sources[0].text.text_id == text_id



def _get_mock_elastic_source_response_():
    return {
        "took": 8,
        "timed_out": False,
        "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
        "hits": {
            "total": {"value": 148, "relation": "eq"},
            "max_score": 3.0705519,
            "hits": [
                {
                    "_index": "pecha-segments",
                    "_id": "aLygYpcB3z3vvVmz7u8a",
                    "_score": 3.0705519,
                    "_source": {
                        "id": "2eb76906-f2d5-48ca-9f80-2023ee6b3ad0",
                        "content": "May all beings hear the sound of Dharma<br>Unceasingly from birds and trees,<br>From all rays of light,<br>And even from the sky itself.",
                        "text_id": "e6370d09-aa0c-4a41-96ef-deffb89c7810",
                        "text": {
                            "title": "The Way of the Bodhisattva Claude AI Draft",
                            "language": "en",
                            "parent_id": "032b9a5f-0712-40d8-b7ec-73c8c94f1c15",
                            "is_published": "true",
                            "created_date": "2025-04-05 04:38:34.436250+00:00",
                            "updated_date": "2025-04-05 04:38:34.436269+00:00",
                            "published_date": "2025-04-05 04:38:34.436287+00:00",
                            "published_by": "pecha",
                            "type": "version",
                            "group_id": "6bdc5225-63c2-4c97-b87f-d68be0b601b3"
                        }
                    }
                },
                {
                    "_index": "pecha-segments",
                    "_id": "u7ygYpcB3z3vvVmz6u2g",
                    "_score": 2.8719563,
                    "_source": {
                        "id": "8d3bc31e-9591-4d67-ab5b-36a239701b10",
                        "content": "Suffering, mental distress,<br>Various forms of fear,<br>And separation from desires -<br>These arise from engaging in harmful actions.",
                        "text_id": "e6370d09-aa0c-4a41-96ef-deffb89c7810",
                        "text": {
                            "title": "The Way of the Bodhisattva Claude AI Draft",
                            "language": "en",
                            "parent_id": "032b9a5f-0712-40d8-b7ec-73c8c94f1c15",
                            "is_published": "true",
                            "created_date": "2025-04-05 04:38:34.436250+00:00",
                            "updated_date": "2025-04-05 04:38:34.436269+00:00",
                            "published_date": "2025-04-05 04:38:34.436287+00:00",
                            "published_by": "pecha",
                            "type": "version",
                            "group_id": "6bdc5225-63c2-4c97-b87f-d68be0b601b3"
                        }
                    }
                }
            ]
        }
    }

def _get_mock_elastic_source_within_text_response_():
    return {
        "took": 8,
        "timed_out": False,
        "_shards": {"total": 1, "successful": 1, "skipped": 0, "failed": 0},
        "hits": {
            "total": {"value": 148, "relation": "eq"},
            "max_score": 3.0705519,
            "hits": [
                {
                    "_index": "pecha-segments",
                    "_id": "aLygYpcB3z3vvVmz7u8a",
                    "_score": 3.0705519,
                    "_source": {
                        "id": "2eb76906-f2d5-48ca-9f80-2023ee6b3ad0",
                        "content": "May all beings hear the sound of Dharma<br>Unceasingly from birds and trees,<br>From all rays of light,<br>And even from the sky itself.",
                        "text_id": "e6370d09-aa0c-4a41-96ef-deffb89c7810",
                        "text": {
                            "title": "The Way of the Bodhisattva Claude AI Draft",
                            "language": "en",
                            "parent_id": "032b9a5f-0712-40d8-b7ec-73c8c94f1c15",
                            "is_published": "true",
                            "created_date": "2025-04-05 04:38:34.436250+00:00",
                            "updated_date": "2025-04-05 04:38:34.436269+00:00",
                            "published_date": "2025-04-05 04:38:34.436287+00:00",
                            "published_by": "pecha",
                            "type": "version",
                            "group_id": "6bdc5225-63c2-4c97-b87f-d68be0b601b3"
                        }
                    }
                },
                {
                    "_index": "pecha-segments",
                    "_id": "u7ygYpcB3z3vvVmz6u2g",
                    "_score": 2.8719563,
                    "_source": {
                        "id": "8d3bc31e-9591-4d67-ab5b-36a239701b10",
                        "content": "Suffering, mental distress,<br>Various forms of fear,<br>And separation from desires -<br>These arise from engaging in harmful actions.",
                        "text_id": "e6370d09-aa0c-4a41-96ef-deffb89c7810",
                        "text": {
                            "title": "The Way of the Bodhisattva Claude AI Draft",
                            "language": "en",
                            "parent_id": "032b9a5f-0712-40d8-b7ec-73c8c94f1c15",
                            "is_published": "true",
                            "created_date": "2025-04-05 04:38:34.436250+00:00",
                            "updated_date": "2025-04-05 04:38:34.436269+00:00",
                            "published_date": "2025-04-05 04:38:34.436287+00:00",
                            "published_by": "pecha",
                            "type": "version",
                            "group_id": "6bdc5225-63c2-4c97-b87f-d68be0b601b3"
                        }
                    }
                }
            ]
        }
    }

@pytest.mark.asyncio
async def test_get_multilingual_search_results_success():
    """Test successful multilingual search with all components"""
   
    mock_external_response = ExternalSearchResponse(
        query="test query",
        search_type="hybrid",
        results=[
            ExternalSearchResult(
                id="pecha_seg_1",
                distance=0.9,
                entity=ExternalSegmentEntity(text="Content 1")
            ),
            ExternalSearchResult(
                id="pecha_seg_2",
                distance=0.8,
                entity=ExternalSegmentEntity(text="Content 2")
            )
        ],
        count=2
    )
    
    mock_segment_1 = Mock()
    mock_segment_1.id = uuid4()
    mock_segment_1.content = "Content 1"
    mock_segment_1.text_id = "text_123"
    mock_segment_1.pecha_segment_id = "pecha_seg_1"
    
    mock_segment_2 = Mock()
    mock_segment_2.id = uuid4()
    mock_segment_2.content = "Content 2"
    mock_segment_2.text_id = "text_123"
    mock_segment_2.pecha_segment_id = "pecha_seg_2"
    
    mock_segments = [mock_segment_1, mock_segment_2]
    
    mock_text = Mock()
    mock_text.title = "Test Text"
    mock_text.language = "bo"
    mock_text.created_at = "2024-01-01"
    
    with patch("pecha_api.search.search_service.call_external_search_api", new_callable=AsyncMock, return_value=mock_external_response), \
         patch("pecha_api.search.search_service.Segment.get_segments_by_pecha_ids", new_callable=AsyncMock, return_value=mock_segments), \
         patch("pecha_api.search.search_service.Text.get_text", new_callable=AsyncMock, return_value=mock_text):
        
        response = await get_multilingual_search_results(
            query="test query",
            search_type="hybrid",
            skip=0,
            limit=10
        )
        
        assert response is not None
        assert isinstance(response, MultilingualSearchResponse)
        assert response.query == "test query"
        assert response.search_type == "hybrid"
        assert len(response.sources) == 1
        assert response.sources[0].text.text_id == "text_123"
        assert len(response.sources[0].segment_matches) == 2
        assert response.total == 10  


@pytest.mark.asyncio
async def test_get_multilingual_search_results_with_text_id():
    """Test multilingual search with specific text_id"""
    mock_external_response = ExternalSearchResponse(
        query="test query",
        search_type="hybrid",
        results=[
            ExternalSearchResult(
                id="pecha_seg_1",
                distance=0.9,
                entity=ExternalSegmentEntity(text="Content 1")
            )
        ],
        count=1
    )
    
    mock_segment = Mock()
    mock_segment.id = uuid4()
    mock_segment.content = "Content 1"
    mock_segment.text_id = "specific_text_123"
    mock_segment.pecha_segment_id = "pecha_seg_1"
    
    mock_text = Mock()
    mock_text.title = "Specific Text"
    mock_text.language = "en"
    mock_text.created_at = "2024-01-01"
    
    with patch("pecha_api.search.search_service.Text.get_text", new_callable=AsyncMock, return_value=mock_text), \
         patch("pecha_api.search.search_service.call_external_search_api", new_callable=AsyncMock, return_value=mock_external_response), \
         patch("pecha_api.search.search_service.Segment.get_segments_by_pecha_ids", new_callable=AsyncMock, return_value=[mock_segment]):
        
        response = await get_multilingual_search_results(
            query="test query",
            text_id="specific_text_123",
            skip=0,
            limit=10
        )
        
        assert response is not None
        assert len(response.sources) == 1
        assert response.sources[0].text.text_id == "specific_text_123"


@pytest.mark.asyncio
async def test_get_multilingual_search_results_no_external_results():
    """Test multilingual search when external API returns no results"""
    mock_external_response = ExternalSearchResponse(
        query="test query",
        search_type="hybrid",
        results=[],
        count=0
    )
    
    with patch("pecha_api.search.search_service.call_external_search_api", new_callable=AsyncMock, return_value=mock_external_response):
        
        response = await get_multilingual_search_results(
            query="test query",
            search_type="hybrid",
            skip=0,
            limit=10
        )
        
        assert response is not None
        assert response.sources == []
        assert response.total == 0


@pytest.mark.asyncio
async def test_get_multilingual_search_results_no_segments_found():
    """Test multilingual search when no internal segments match external IDs"""
    mock_external_response = ExternalSearchResponse(
        query="test query",
        search_type="hybrid",
        results=[
            ExternalSearchResult(
                id="pecha_seg_1",
                distance=0.9,
                entity=ExternalSegmentEntity(text="Content 1")
            )
        ],
        count=1
    )
    
    with patch("pecha_api.search.search_service.call_external_search_api", new_callable=AsyncMock, return_value=mock_external_response), \
         patch("pecha_api.search.search_service.Segment.get_segments_by_pecha_ids", new_callable=AsyncMock, return_value=[]):
        
        response = await get_multilingual_search_results(
            query="test query",
            search_type="hybrid",
            skip=0,
            limit=10
        )
        
        assert response is not None
        assert response.sources == []
        assert response.total == 0


@pytest.mark.asyncio
async def test_get_multilingual_search_results_text_not_found():
    """Test multilingual search when text_id doesn't exist"""
    mock_external_response = ExternalSearchResponse(
        query="test query",
        search_type="hybrid",
        results=[
            ExternalSearchResult(
                id="pecha_seg_1",
                distance=0.9,
                entity=ExternalSegmentEntity(text="Content 1")
            )
        ],
        count=1
    )
    
    mock_segment = Mock()
    mock_segment.id = uuid4()
    mock_segment.content = "Content 1"
    mock_segment.text_id = "text_123"
    mock_segment.pecha_segment_id = "pecha_seg_1"
    
    mock_text = Mock()
    mock_text.title = "Test Text"
    mock_text.language = "bo"
    mock_text.created_at = "2024-01-01"
    
    with patch("pecha_api.search.search_service.Text.get_text", new_callable=AsyncMock, side_effect=[None, mock_text]), \
         patch("pecha_api.search.search_service.call_external_search_api", new_callable=AsyncMock, return_value=mock_external_response), \
         patch("pecha_api.search.search_service.Segment.get_segments_by_pecha_ids", new_callable=AsyncMock, return_value=[mock_segment]):
        
        response = await get_multilingual_search_results(
            query="test query",
            text_id="nonexistent_text",
            skip=0,
            limit=10
        )
        
        assert response is not None
        assert len(response.sources) == 1


@pytest.mark.asyncio
async def test_get_multilingual_search_results_with_language():
    """Test multilingual search with language parameter"""
    mock_external_response = ExternalSearchResponse(
        query="test query",
        search_type="hybrid",
        results=[],
        count=0
    )
    
    with patch("pecha_api.search.search_service.call_external_search_api", new_callable=AsyncMock, return_value=mock_external_response) as mock_call:
        
        await get_multilingual_search_results(
            query="test query",
            language="bo",
            skip=0,
            limit=10
        )
        
        mock_call.assert_called_once()
        call_args = mock_call.call_args
        assert call_args.kwargs["language"] == "bo"


@pytest.mark.asyncio
async def test_get_multilingual_search_results_different_search_types():
    """Test multilingual search with different search types"""
    mock_external_response = ExternalSearchResponse(
        query="test query",
        search_type="semantic",
        results=[],
        count=0
    )
    
    with patch("pecha_api.search.search_service.call_external_search_api", new_callable=AsyncMock, return_value=mock_external_response):
        
        response = await get_multilingual_search_results(
            query="test query",
            search_type="semantic",
            skip=0,
            limit=10
        )
        
        assert response.search_type == "semantic"


@pytest.mark.asyncio
async def test_call_external_search_api_success():
    """Test successful call to external search API"""
    mock_response_data = {
        "query": "test query",
        "search_type": "hybrid",
        "results": [
            {
                "id": "pecha_seg_1",
                "distance": 0.9,
                "entity": {"text": "Content 1"}
            }
        ],
        "count": 1
    }
    
    mock_http_response = Mock()
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.raise_for_status = Mock()
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_http_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        
        response = await call_external_search_api(
            query="test query",
            search_type="hybrid",
            limit=10
        )
        
        assert response is not None
        assert isinstance(response, ExternalSearchResponse)
        assert response.query == "test query"
        assert len(response.results) == 1


@pytest.mark.asyncio
async def test_call_external_search_api_with_language_bo():
    """Test external API call with Tibetan language filter"""
    mock_response_data = {
        "query": "test query",
        "search_type": "hybrid",
        "results": [],
        "count": 0
    }
    
    mock_http_response = Mock()
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.raise_for_status = Mock()
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_http_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        
        await call_external_search_api(
            query="test query",
            language="bo",
            limit=10
        )
        
        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]
        assert "filter" in payload
        assert "language" in payload["filter"]
        assert payload["filter"]["language"] == ["bo", "tib"]


@pytest.mark.asyncio
async def test_call_external_search_api_with_title():
    """Test external API call with title filter"""
    mock_response_data = {
        "query": "test query",
        "search_type": "hybrid",
        "results": [],
        "count": 0
    }
    
    mock_http_response = Mock()
    mock_http_response.json.return_value = mock_response_data
    mock_http_response.raise_for_status = Mock()
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_http_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        
        await call_external_search_api(
            query="test query",
            title="Specific Title",
            limit=10
        )
        
        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]
        assert "filter" in payload
        assert "title" in payload["filter"]
        assert payload["filter"]["title"] == ["Specific Title"]


@pytest.mark.asyncio
async def test_call_external_search_api_http_error():
    """Test external API call when HTTP error occurs"""
    mock_http_response = Mock()
    mock_http_response.status_code = 500
    mock_http_response.text = "Internal Server Error"
    
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.HTTPStatusError(
        "Server error",
        request=Mock(),
        response=mock_http_response
    ))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        
        with pytest.raises(HTTPException) as exc_info:
            await call_external_search_api(
                query="test query",
                limit=10
            )
        
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_call_external_search_api_request_error():
    """Test external API call when request fails"""
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        
        with pytest.raises(HTTPException) as exc_info:
            await call_external_search_api(
                query="test query",
                limit=10
            )
        
        assert exc_info.value.status_code == 500
        assert "Failed to connect" in exc_info.value.detail


@pytest.mark.asyncio
async def test_build_multilingual_sources_success():
    """Test building multilingual sources from segments"""

    mock_segment_1 = Mock()
    mock_segment_1.id = uuid4()
    mock_segment_1.content = "Content 1"
    mock_segment_1.text_id = "text_123"
    mock_segment_1.pecha_segment_id = "pecha_seg_1"
    
    mock_segment_2 = Mock()
    mock_segment_2.id = uuid4()
    mock_segment_2.content = "Content 2"
    mock_segment_2.text_id = "text_123"
    mock_segment_2.pecha_segment_id = "pecha_seg_2"
    
    segments = [mock_segment_1, mock_segment_2]
    
    results_map = {
        "pecha_seg_1": {"distance": 0.9, "content": "Content 1"},
        "pecha_seg_2": {"distance": 0.8, "content": "Content 2"}
    }
    
    mock_text = Mock()
    mock_text.title = "Test Text"
    mock_text.language = "bo"
    mock_text.created_at = "2024-01-01"
    
    with patch("pecha_api.search.search_service.Text.get_text", new_callable=AsyncMock, return_value=mock_text):
        
        final_display_sources = await build_multilingual_sources(segments, results_map)
        
        assert len(final_display_sources) == 1
        assert isinstance(final_display_sources[0], MultilingualSourceResult)
        assert final_display_sources[0].text.text_id == "text_123"
        assert len(final_display_sources[0].segment_matches) == 2
        assert final_display_sources[0].segment_matches[0].relevance_score <= final_display_sources[0].segment_matches[1].relevance_score


@pytest.mark.asyncio
async def test_build_multilingual_sources_multiple_texts():
    """Test building sources from segments across multiple texts"""
    mock_segment_1 = Mock()
    mock_segment_1.id = uuid4()
    mock_segment_1.content = "Content 1"
    mock_segment_1.text_id = "text_123"
    mock_segment_1.pecha_segment_id = "pecha_seg_1"
    
    mock_segment_2 = Mock()
    mock_segment_2.id = uuid4()
    mock_segment_2.content = "Content 2"
    mock_segment_2.text_id = "text_456"
    mock_segment_2.pecha_segment_id = "pecha_seg_2"
    
    segments = [mock_segment_1, mock_segment_2]
    
    results_map = {
        "pecha_seg_1": {"distance": 0.9, "content": "Content 1"},
        "pecha_seg_2": {"distance": 0.8, "content": "Content 2"}
    }
    
    mock_text_1 = Mock()
    mock_text_1.title = "Test Text 1"
    mock_text_1.language = "bo"
    mock_text_1.created_at = "2024-01-01"
    
    mock_text_2 = Mock()
    mock_text_2.title = "Test Text 2"
    mock_text_2.language = "en"
    mock_text_2.created_at = "2024-01-02"
    
    with patch("pecha_api.search.search_service.Text.get_text", new_callable=AsyncMock, side_effect=[mock_text_1, mock_text_2]):
        
        final_display_sources = await build_multilingual_sources(segments, results_map)
        
        assert len(final_display_sources) == 2
        assert final_display_sources[0].text.text_id == "text_123"
        assert final_display_sources[1].text.text_id == "text_456"


@pytest.mark.asyncio
async def test_build_multilingual_sources_missing_text():
    """Test building sources when text is not found"""
    mock_segment = Mock()
    mock_segment.id = uuid4()
    mock_segment.content = "Content 1"
    mock_segment.text_id = "text_123"
    mock_segment.pecha_segment_id = "pecha_seg_1"
    
    segments = [mock_segment]
    results_map = {
        "pecha_seg_1": {"distance": 0.9, "content": "Content 1"}
    }
    
    with patch("pecha_api.search.search_service.Text.get_text", new_callable=AsyncMock, return_value=None):
        
        final_display_sources = await build_multilingual_sources(segments, results_map)
        
        assert len(final_display_sources) == 0


@pytest.mark.asyncio
async def test_build_multilingual_sources_segment_not_in_results_map():
    """Test building sources when segment pecha_id not in results map"""
    mock_segment = Mock()
    mock_segment.id = uuid4()
    mock_segment.content = "Content 1"
    mock_segment.text_id = "text_123"
    mock_segment.pecha_segment_id = "pecha_seg_unknown"
    
    segments = [mock_segment]
    results_map = {
        "pecha_seg_1": {"distance": 0.9, "content": "Content 1"}
    }
    
    mock_text = Mock()
    mock_text.title = "Test Text"
    mock_text.language = "bo"
    mock_text.created_at = "2024-01-01"
    
    with patch("pecha_api.search.search_service.Text.get_text", new_callable=AsyncMock, return_value=mock_text):
        
        final_display_sources = await build_multilingual_sources(segments, results_map)
        
        assert len(final_display_sources) == 1
        assert len(final_display_sources[0].segment_matches) == 0


@pytest.mark.asyncio
async def test_build_multilingual_sources_sorting():
    """Test that segment matches are sorted by relevance score"""
    segments = []
    results_map = {}
    
    for i in range(5):
        mock_segment = Mock()
        mock_segment.id = uuid4()
        mock_segment.content = f"Content {i}"
        mock_segment.text_id = "text_123"
        mock_segment.pecha_segment_id = f"pecha_seg_{i}"
        segments.append(mock_segment)
        
        results_map[f"pecha_seg_{i}"] = {
            "distance": 0.5 + (i * 0.1),
            "content": f"Content {i}"
        }
    
    mock_text = Mock()
    mock_text.title = "Test Text"
    mock_text.language = "bo"
    mock_text.created_at = "2024-01-01"
    
    with patch("pecha_api.search.search_service.Text.get_text", new_callable=AsyncMock, return_value=mock_text):
        
        final_display_sources = await build_multilingual_sources(segments, results_map)
        
        assert len(final_display_sources) == 1
        assert len(final_display_sources[0].segment_matches) == 5
        
        scores = [match.relevance_score for match in final_display_sources[0].segment_matches]
        assert scores == sorted(scores)


@pytest.mark.asyncio
async def test_get_url_link_success():
    """Test get_url_link service with valid pecha_segment_id"""
    from pecha_api.search.search_service import get_url_link
    
    mock_segment = Mock()
    mock_segment.id = uuid4()
    mock_segment.text_id = "text123"
    mock_segment.pecha_segment_id = "pecha_seg_123"
    
    with patch("pecha_api.search.search_service.Segment.get_segment_by_pecha_segment_id", new_callable=AsyncMock, return_value=mock_segment):
        result = await get_url_link("pecha_seg_123")
        
        assert result is not None
        assert result == f"/chapter?text_id=text123&segment_id={str(mock_segment.id)}"
        assert "text_id=" in result
        assert "segment_id=" in result


@pytest.mark.asyncio
async def test_get_url_link_segment_not_found():
    """Test get_url_link service when segment is not found"""
    from pecha_api.search.search_service import get_url_link
    from pecha_api.plans.response_message import PECHA_SEGMENT_NOT_FOUND
    
    with patch("pecha_api.search.search_service.Segment.get_segment_by_pecha_segment_id", new_callable=AsyncMock, return_value=None):
        result = await get_url_link("nonexistent_segment_id")
        
        assert result == PECHA_SEGMENT_NOT_FOUND
        assert result == "Pecha segment not found"


@pytest.mark.asyncio
async def test_get_url_link_with_uuid_segment_id():
    """Test get_url_link service with UUID-formatted segment ID"""
    from pecha_api.search.search_service import get_url_link
    
    segment_uuid = uuid4()
    text_uuid = uuid4()
    
    mock_segment = Mock()
    mock_segment.id = segment_uuid
    mock_segment.text_id = str(text_uuid)
    mock_segment.pecha_segment_id = str(uuid4())
    
    with patch("pecha_api.search.search_service.Segment.get_segment_by_pecha_segment_id", new_callable=AsyncMock, return_value=mock_segment):
        result = await get_url_link(mock_segment.pecha_segment_id)
        
        assert result is not None
        assert result == f"/chapter?text_id={str(text_uuid)}&segment_id={str(segment_uuid)}"
        assert str(text_uuid) in result
        assert str(segment_uuid) in result


@pytest.mark.asyncio
async def test_get_url_link_with_special_characters():
    """Test get_url_link service with special characters in pecha_segment_id"""
    from pecha_api.search.search_service import get_url_link
    
    mock_segment = Mock()
    mock_segment.id = uuid4()
    mock_segment.text_id = "text-abc-123"
    mock_segment.pecha_segment_id = "pecha-seg_123-xyz"
    
    with patch("pecha_api.search.search_service.Segment.get_segment_by_pecha_segment_id", new_callable=AsyncMock, return_value=mock_segment):
        result = await get_url_link("pecha-seg_123-xyz")
        
        assert result is not None
        assert result == f"/chapter?text_id=text-abc-123&segment_id={str(mock_segment.id)}"


@pytest.mark.asyncio
async def test_get_url_link_database_exception():
    """Test get_url_link service when database raises an exception"""
    from pecha_api.search.search_service import get_url_link
    
    with patch("pecha_api.search.search_service.Segment.get_segment_by_pecha_segment_id", new_callable=AsyncMock, side_effect=Exception("Database connection error")):
        result = await get_url_link("error_segment_id")
        
        assert result == ""


@pytest.mark.asyncio
async def test_get_url_link_with_long_pecha_segment_id():
    """Test get_url_link service with very long pecha_segment_id"""
    from pecha_api.search.search_service import get_url_link
    
    long_segment_id = "a" * 500
    
    mock_segment = Mock()
    mock_segment.id = uuid4()
    mock_segment.text_id = "text123"
    mock_segment.pecha_segment_id = long_segment_id
    
    with patch("pecha_api.search.search_service.Segment.get_segment_by_pecha_segment_id", new_callable=AsyncMock, return_value=mock_segment):
        result = await get_url_link(long_segment_id)
        
        assert result is not None
        assert result == f"/chapter?text_id=text123&segment_id={str(mock_segment.id)}"


@pytest.mark.asyncio
async def test_get_url_link_with_empty_text_id():
    """Test get_url_link service when segment has empty text_id"""
    from pecha_api.search.search_service import get_url_link
    
    mock_segment = Mock()
    mock_segment.id = uuid4()
    mock_segment.text_id = ""
    mock_segment.pecha_segment_id = "pecha_seg_123"
    
    with patch("pecha_api.search.search_service.Segment.get_segment_by_pecha_segment_id", new_callable=AsyncMock, return_value=mock_segment):
        result = await get_url_link("pecha_seg_123")
        
        assert result is not None
        assert result == f"/chapter?text_id=&segment_id={str(mock_segment.id)}"


@pytest.mark.asyncio
async def test_get_url_link_multiple_calls():
    """Test get_url_link service with multiple sequential calls"""
    from pecha_api.search.search_service import get_url_link
    
    mock_segment1 = Mock()
    mock_segment1.id = uuid4()
    mock_segment1.text_id = "text1"
    mock_segment1.pecha_segment_id = "seg1"
    
    mock_segment2 = Mock()
    mock_segment2.id = uuid4()
    mock_segment2.text_id = "text2"
    mock_segment2.pecha_segment_id = "seg2"
    
    with patch("pecha_api.search.search_service.Segment.get_segment_by_pecha_segment_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_segment1
        result1 = await get_url_link("seg1")
        assert result1 == f"/chapter?text_id=text1&segment_id={str(mock_segment1.id)}"
        
        mock_get.return_value = mock_segment2
        result2 = await get_url_link("seg2")
        assert result2 == f"/chapter?text_id=text2&segment_id={str(mock_segment2.id)}"
        
        assert mock_get.call_count == 2


@pytest.mark.asyncio
async def test_get_url_link_none_segment_id():
    """Test get_url_link service when segment.id is None"""
    from pecha_api.search.search_service import get_url_link
    
    mock_segment = Mock()
    mock_segment.id = None
    mock_segment.text_id = "text123"
    mock_segment.pecha_segment_id = "pecha_seg_123"
    
    with patch("pecha_api.search.search_service.Segment.get_segment_by_pecha_segment_id", new_callable=AsyncMock, return_value=mock_segment):
        result = await get_url_link("pecha_seg_123")
        
        assert result is not None
        assert result == f"/chapter?text_id=text123&segment_id=None"

@pytest.mark.asyncio
async def test_get_multilingual_search_external_limit_calculation():
    """Test that external API is called with limit * 5, max 100"""
    mock_external_response = ExternalSearchResponse(
        query="test query",
        search_type="hybrid",
        results=[],
        count=0
    )
    
    with patch("pecha_api.search.search_service.call_external_search_api", new_callable=AsyncMock, return_value=mock_external_response) as mock_call:
        
        await get_multilingual_search_results(
            query="test query",
            search_type="hybrid",
            skip=0,
            limit=10
        )
        
        call_args = mock_call.call_args
        assert call_args.kwargs["limit"] == 50  # 10 * 5 = 50


@pytest.mark.asyncio
async def test_get_multilingual_search_external_limit_max_cap():
    """Test that external API limit is capped at 100"""
    mock_external_response = ExternalSearchResponse(
        query="test query",
        search_type="hybrid",
        results=[],
        count=0
    )
    
    with patch("pecha_api.search.search_service.call_external_search_api", new_callable=AsyncMock, return_value=mock_external_response) as mock_call:
        
        await get_multilingual_search_results(
            query="test query",
            search_type="hybrid",
            skip=0,
            limit=30
        )
        
        call_args = mock_call.call_args
        assert call_args.kwargs["limit"] == 100  # min(30 * 5, 100) = 100


@pytest.mark.asyncio
async def test_get_multilingual_search_total_returns_limit():
    """Test that total returns the set limit value"""
    mock_external_response = ExternalSearchResponse(
        query="test query",
        search_type="hybrid",
        results=[
            ExternalSearchResult(id="pecha_seg_1", distance=0.9, entity=ExternalSegmentEntity(text="Content 1")),
            ExternalSearchResult(id="pecha_seg_2", distance=0.8, entity=ExternalSegmentEntity(text="Content 2")),
            ExternalSearchResult(id="pecha_seg_3", distance=0.7, entity=ExternalSegmentEntity(text="Content 3")),
        ],
        count=100  
    )
    
    mock_segment_1 = Mock()
    mock_segment_1.id = uuid4()
    mock_segment_1.content = "Content 1"
    mock_segment_1.text_id = "text_123"
    mock_segment_1.pecha_segment_id = "pecha_seg_1"
    
    mock_segment_2 = Mock()
    mock_segment_2.id = uuid4()
    mock_segment_2.content = "Content 2"
    mock_segment_2.text_id = "text_123"
    mock_segment_2.pecha_segment_id = "pecha_seg_2"
    
    mock_segments = [mock_segment_1, mock_segment_2]
    
    mock_text = Mock()
    mock_text.title = "Test Text"
    mock_text.language = "bo"
    mock_text.created_at = "2024-01-01"
    
    with patch("pecha_api.search.search_service.call_external_search_api", new_callable=AsyncMock, return_value=mock_external_response), \
         patch("pecha_api.search.search_service.Segment.get_segments_by_pecha_ids", new_callable=AsyncMock, return_value=mock_segments), \
         patch("pecha_api.search.search_service.Text.get_text", new_callable=AsyncMock, return_value=mock_text):
        
        response = await get_multilingual_search_results(
            query="test query",
            search_type="hybrid",
            skip=0,
            limit=10
        )
        
        assert response.total == 10


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
