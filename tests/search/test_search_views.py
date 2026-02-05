import pytest
from unittest.mock import patch, AsyncMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.search.search_response_models import (
    SearchResponse,
    SourceResultItem,
    SheetResultItem,
    TextIndex,
    SegmentMatch,
    Search,
    MultilingualSearchResponse,
    MultilingualSourceResult,
    MultilingualSegmentMatch
)

from pecha_api.search.search_enums import SearchType, MultilingualSearchType

client = TestClient(api)

def test_search_type_source_success():
    """Test search endpoint with SOURCE search type"""
    mock_search_query = Search(
        text="query",
        type=SearchType.SOURCE
    )
    mock_source_result_item = [
        SourceResultItem(
            text=TextIndex(
                text_id=f"text_id_{i}",
                language="en",
                title="title",
                published_date="2021-01-01"
            ),
            segment_match=[
                SegmentMatch(
                    segment_id=f"segment_id_{i}",
                    content="content"
                )
            ]
        )
        for i in range(1,6)
    ]
    mock_search_results = SearchResponse(
        search=mock_search_query,
        sources=mock_source_result_item,
        skip=0,
        limit=10,
        total=5
    )
    
    with patch("pecha_api.search.search_views.get_search_results", new_callable=AsyncMock, return_value=mock_search_results):
        
        response = client.get("/search?query=query&search_type=SOURCE&skip=0&limit=10")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["search"] is not None
        assert data["search"]["text"] == "query"
        assert data["search"]["type"] == "SOURCE"
        assert data["sources"] is not None
        assert len(data["sources"]) == 5
        assert data["sources"][0] is not None
        assert data["sources"][0]["text"] is not None
        assert data["sources"][0]["text"]["text_id"] == "text_id_1"
        assert data["sources"][0]["text"]["language"] == "en"


def test_search_type_sheet_success():
    """Test search endpoint with SHEET search type"""
    mock_search_query = Search(
        text="sheet query",
        type=SearchType.SHEET
    )
    mock_sheet_result_item = [
        SheetResultItem(
            sheet_id=i,
            sheet_title=f"Sheet Title {i}",
            sheet_summary=f"Sheet summary {i}",
            publisher_id=100 + i,
            publisher_name=f"Publisher {i}",
            publisher_url=f"https://publisher{i}.com",
            publisher_image=f"https://publisher{i}.com/image.jpg",
            publisher_position=f"Position {i}",
            publisher_organization=f"Organization {i}"
        )
        for i in range(1, 4)
    ]
    mock_search_results = SearchResponse(
        search=mock_search_query,
        sheets=mock_sheet_result_item,
        skip=0,
        limit=10,
        total=3
    )
    
    with patch("pecha_api.search.search_views.get_search_results", new_callable=AsyncMock, return_value=mock_search_results):
        
        response = client.get("/search?query=sheet query&search_type=SHEET")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["search"]["text"] == "sheet query"
        assert data["search"]["type"] == "SHEET"
        assert data["sheets"] is not None
        assert len(data["sheets"]) == 3
        assert data["sheets"][0]["sheet_id"] == 1
        assert data["sheets"][0]["sheet_title"] == "Sheet Title 1"
        assert data["sheets"][0]["publisher_name"] == "Publisher 1"
        assert data["total"] == 3


def test_search_with_text_id():
    """Test search endpoint with specific text_id parameter"""
    mock_search_query = Search(
        text="query in text",
        type=SearchType.SOURCE
    )
    mock_search_results = SearchResponse(
        search=mock_search_query,
        sources=[],
        skip=0,
        limit=10,
        total=0
    )
    
    with patch("pecha_api.search.search_views.get_search_results", new_callable=AsyncMock, return_value=mock_search_results) as mock_service:
        
        response = client.get("/search?query=query in text&search_type=SOURCE&text_id=specific_text_123")
        
        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(
            query="query in text",
            search_type=SearchType.SOURCE,
            text_id="specific_text_123",
            skip=0,
            limit=10
        )


def test_search_with_pagination():
    """Test search endpoint with custom pagination"""
    mock_search_query = Search(
        text="paginated query",
        type=SearchType.SOURCE
    )
    mock_search_results = SearchResponse(
        search=mock_search_query,
        sources=[],
        skip=20,
        limit=50,
        total=100
    )
    
    with patch("pecha_api.search.search_views.get_search_results", new_callable=AsyncMock, return_value=mock_search_results):
        
        response = client.get("/search?query=paginated query&search_type=SOURCE&skip=20&limit=50")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["skip"] == 20
        assert data["limit"] == 50
        assert data["total"] == 100


def test_search_with_all_parameters():
    """Test search endpoint with all optional parameters"""
    mock_search_query = Search(
        text="full query",
        type=SearchType.SOURCE
    )
    mock_search_results = SearchResponse(
        search=mock_search_query,
        sources=[],
        skip=10,
        limit=25,
        total=50
    )
    
    with patch("pecha_api.search.search_views.get_search_results", new_callable=AsyncMock, return_value=mock_search_results) as mock_service:
        
        response = client.get("/search?query=full query&search_type=SOURCE&text_id=text_456&skip=10&limit=25")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["skip"] == 10
        assert data["limit"] == 25
        assert data["total"] == 50
        
        mock_service.assert_called_once_with(
            query="full query",
            search_type=SearchType.SOURCE,
            text_id="text_456",
            skip=10,
            limit=25
        )


def test_search_empty_results():
    """Test search endpoint with no results found"""
    mock_search_query = Search(
        text="no results query",
        type=SearchType.SOURCE
    )
    mock_search_results = SearchResponse(
        search=mock_search_query,
        sources=[],
        skip=0,
        limit=10,
        total=0
    )
    
    with patch("pecha_api.search.search_views.get_search_results", new_callable=AsyncMock, return_value=mock_search_results):
        
        response = client.get("/search?query=no results query&search_type=SOURCE")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sources"] == []
        assert data["total"] == 0


def test_search_with_default_parameters():
    """Test search endpoint with default parameters (query and search_type are None)"""
    mock_search_query = Search(
        text=None,
        type=None
    )
    mock_search_results = SearchResponse(
        search=mock_search_query,
        sources=[],
        skip=0,
        limit=10,
        total=0
    )
    
    with patch("pecha_api.search.search_views.get_search_results", new_callable=AsyncMock, return_value=mock_search_results) as mock_service:
        
        response = client.get("/search")
        
        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(
            query=None,
            search_type=None,
            text_id=None,
            skip=0,
            limit=10
        )


def test_search_multiple_sources():
    """Test search endpoint with multiple source results"""
    mock_search_query = Search(
        text="multi source query",
        type=SearchType.SOURCE
    )
    mock_sources = [
        SourceResultItem(
            text=TextIndex(
                text_id=f"text_{i}",
                language="en",
                title=f"Title {i}",
                published_date="2024-01-01"
            ),
            segment_match=[
                SegmentMatch(
                    segment_id=f"seg_{i}",
                    content=f"Content {i}"
                )
            ]
        )
        for i in range(1, 6)
    ]
    mock_search_results = SearchResponse(
        search=mock_search_query,
        sources=mock_sources,
        skip=0,
        limit=10,
        total=5
    )
    
    with patch("pecha_api.search.search_views.get_search_results", new_callable=AsyncMock, return_value=mock_search_results):
        
        response = client.get("/search?query=multi source query&search_type=SOURCE")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sources"]) == 5
        assert data["total"] == 5
        assert data["sources"][0]["text"]["text_id"] == "text_1"
        assert data["sources"][4]["text"]["text_id"] == "text_5"


def test_search_service_error():
    """Test search endpoint when service raises an exception"""
    test_client = TestClient(api, raise_server_exceptions=False)
    
    with patch("pecha_api.search.search_views.get_search_results", 
               new_callable=AsyncMock, side_effect=Exception("Service error")):
        
        response = test_client.get("/search?query=error query&search_type=SOURCE")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_multilingual_search_success_hybrid():
    """Test multilingual search with HYBRID search type (default)"""
    mock_segment_matches = [
        MultilingualSegmentMatch(
            segment_id=f"seg_{i}",
            content=f"Content {i}",
            relevance_score=0.9 - ((i - 1) * 0.1),
            pecha_segment_id=f"pecha_seg_{i}"
        )
        for i in range(1, 4)
    ]
    
    mock_source_results = [
        MultilingualSourceResult(
            text=TextIndex(
                text_id="text_123",
                language="bo",
                title="Tibetan Text",
                published_date="2024-01-01"
            ),
            segment_matches=mock_segment_matches
        )
    ]
    
    mock_response = MultilingualSearchResponse(
        query="test query",
        search_type="hybrid",
        sources=mock_source_results,
        skip=0,
        limit=10,
        total=1
    )
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get("/search/multilingual?query=test query")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["query"] == "test query"
        assert data["search_type"] == "hybrid"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["text"]["text_id"] == "text_123"
        assert data["sources"][0]["text"]["language"] == "bo"
        assert len(data["sources"][0]["segment_matches"]) == 3
        assert data["skip"] == 0
        assert data["limit"] == 10
        assert data["total"] == 1


def test_multilingual_search_with_semantic_type():
    """Test multilingual search with SEMANTIC search type"""
    mock_response = MultilingualSearchResponse(
        query="semantic query",
        search_type="semantic",
        sources=[],
        skip=0,
        limit=10,
        total=0
    )
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get("/search/multilingual?query=semantic query&search_type=semantic")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["search_type"] == "semantic"
        assert data["sources"] == []


def test_multilingual_search_with_bm25_type():
    """Test multilingual search with BM25 search type"""
    mock_response = MultilingualSearchResponse(
        query="bm25 query",
        search_type="bm25",
        sources=[],
        skip=0,
        limit=10,
        total=0
    )
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get("/search/multilingual?query=bm25 query&search_type=bm25")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["search_type"] == "bm25"


def test_multilingual_search_with_exact_type():
    """Test multilingual search with EXACT search type"""
    mock_response = MultilingualSearchResponse(
        query="exact query",
        search_type="exact",
        sources=[],
        skip=0,
        limit=10,
        total=0
    )
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get("/search/multilingual?query=exact query&search_type=exact")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["search_type"] == "exact"


def test_multilingual_search_with_text_id():
    """Test multilingual search with specific text_id parameter"""
    mock_response = MultilingualSearchResponse(
        query="query in specific text",
        search_type="hybrid",
        sources=[],
        skip=0,
        limit=10,
        total=0
    )
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get("/search/multilingual?query=query in specific text&text_id=specific_text_123")
        
        assert response.status_code == status.HTTP_200_OK


def test_multilingual_search_with_language():
    """Test multilingual search with language parameter"""
    mock_response = MultilingualSearchResponse(
        query="query with language",
        search_type="hybrid",
        sources=[],
        skip=0,
        limit=10,
        total=0
    )
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get("/search/multilingual?query=query with language&language=bo")
        
        assert response.status_code == status.HTTP_200_OK


def test_multilingual_search_with_pagination():
    """Test multilingual search with custom pagination"""
    mock_response = MultilingualSearchResponse(
        query="paginated query",
        search_type="hybrid",
        sources=[],
        skip=20,
        limit=50,
        total=100
    )
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get("/search/multilingual?query=paginated query&skip=20&limit=50")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["skip"] == 20
        assert data["limit"] == 50
        assert data["total"] == 100


def test_multilingual_search_with_all_parameters():
    """Test multilingual search with all optional parameters"""
    mock_response = MultilingualSearchResponse(
        query="full query",
        search_type="semantic",
        sources=[],
        skip=10,
        limit=25,
        total=50
    )
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get(
            "/search/multilingual?query=full query&search_type=semantic&text_id=text_456&language=en&skip=10&limit=25"
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["search_type"] == "semantic"
        assert data["skip"] == 10
        assert data["limit"] == 25


def test_multilingual_search_empty_results():
    """Test multilingual search with no results found"""
    mock_response = MultilingualSearchResponse(
        query="no results query",
        search_type="hybrid",
        sources=[],
        skip=0,
        limit=10,
        total=0
    )
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get("/search/multilingual?query=no results query")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["sources"] == []
        assert data["total"] == 0


def test_multilingual_search_multiple_sources():
    """Test multilingual search with multiple source results"""
    mock_sources = [
        MultilingualSourceResult(
            text=TextIndex(
                text_id=f"text_{i}",
                language="bo",
                title=f"Text {i}",
                published_date="2024-01-01"
            ),
            segment_matches=[
                MultilingualSegmentMatch(
                    segment_id=f"seg_{i}_1",
                    content=f"Content {i}",
                    relevance_score=0.9,
                    pecha_segment_id=f"pecha_{i}_1"
                )
            ]
        )
        for i in range(1, 6)
    ]
    
    mock_response = MultilingualSearchResponse(
        query="multi source query",
        search_type="hybrid",
        sources=mock_sources,
        skip=0,
        limit=10,
        total=5
    )
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get("/search/multilingual?query=multi source query")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["sources"]) == 5
        assert data["total"] == 5
        assert data["sources"][0]["text"]["text_id"] == "text_1"
        assert data["sources"][4]["text"]["text_id"] == "text_5"


def test_multilingual_search_service_error():
    """Test multilingual search when service raises an exception"""
    test_client = TestClient(api, raise_server_exceptions=False)
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, side_effect=Exception("Service error")):
        
        response = test_client.get("/search/multilingual?query=error query")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_multilingual_search_missing_query():
    """Test multilingual search without required query parameter"""
    response = client.get("/search/multilingual")
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_multilingual_search_invalid_pagination():
    """Test multilingual search with invalid pagination parameters"""
    response = client.get("/search/multilingual?query=test&skip=-1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    response = client.get("/search/multilingual?query=test&limit=101")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    response = client.get("/search/multilingual?query=test&limit=0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_url_link_success():
    """Test get_url_link endpoint with valid pecha_segment_id"""
    mock_url = "/chapter?text_id=text123&segment_id=segment456"
    
    with patch("pecha_api.search.search_views.get_url_link_service", new_callable=AsyncMock, return_value=mock_url):
        response = client.get("/search/chat/pecha_seg_123")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_url
        assert "/chapter?text_id=" in response.json()
        assert "segment_id=" in response.json()


def test_get_url_link_segment_not_found():
    """Test get_url_link endpoint when segment is not found"""
    with patch("pecha_api.search.search_views.get_url_link_service", new_callable=AsyncMock, return_value=""):
        response = client.get("/search/chat/nonexistent_segment_id")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == ""


def test_get_url_link_with_special_characters():
    """Test get_url_link endpoint with special characters in pecha_segment_id"""
    mock_url = "/chapter?text_id=text-abc-123&segment_id=seg_456_xyz"
    
    with patch("pecha_api.search.search_views.get_url_link_service", new_callable=AsyncMock, return_value=mock_url):
        response = client.get("/search/chat/pecha-seg_123-xyz")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_url


def test_get_url_link_service_error():
    """Test get_url_link endpoint when service raises an exception"""
    with patch("pecha_api.search.search_views.get_url_link_service", new_callable=AsyncMock, return_value=""):
        response = client.get("/search/chat/error_segment_id")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == ""


def test_get_url_link_with_uuid_format():
    """Test get_url_link endpoint with UUID-like pecha_segment_id"""
    mock_url = "/chapter?text_id=550e8400-e29b-41d4-a716-446655440000&segment_id=660e8400-e29b-41d4-a716-446655440001"
    
    with patch("pecha_api.search.search_views.get_url_link_service", new_callable=AsyncMock, return_value=mock_url):
        response = client.get("/search/chat/550e8400-e29b-41d4-a716-446655440000")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_url
        assert "text_id=" in response.json()
        assert "segment_id=" in response.json()


def test_get_url_link_empty_pecha_segment_id():
    """Test get_url_link endpoint with empty pecha_segment_id"""
    response = client.get("/search/chat/")
    
    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_307_TEMPORARY_REDIRECT]


def test_get_url_link_with_long_pecha_segment_id():
    """Test get_url_link endpoint with very long pecha_segment_id"""
    long_segment_id = "a" * 500
    mock_url = "/chapter?text_id=text123&segment_id=seg456"
    
    with patch("pecha_api.search.search_views.get_url_link_service", new_callable=AsyncMock, return_value=mock_url):
        response = client.get(f"/search/chat/{long_segment_id}")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == mock_url


def test_knowledge_base_search_scope_all():
    """Test knowledge_base_search endpoint with scope='all'"""
    mock_result = {
        "titles": [
            {"id": "text_1", "title": "Text 1"},
            {"id": "text_2", "title": "Text 2"},
            {"id": "text_3", "title": "Text 3"}
        ],
        "content": {
            "query": "test query",
            "search_type": "hybrid",
            "sources": [
                {
                    "text": {
                        "text_id": "content_text_1",
                        "language": "bo",
                        "title": "Content Text 1",
                        "published_date": "2024-01-01"
                    },
                    "segment_matches": [
                        {
                            "segment_id": "seg_1",
                            "content": "Content 1",
                            "relevance_score": 0.9,
                            "pecha_segment_id": "pecha_1"
                        }
                    ]
                }
            ],
            "skip": 0,
            "limit": 3,
            "total": 1
        },
        "authors": [
            {"id": "author_1", "title": "Author 1"},
            {"id": "author_2", "title": "Author 2"},
            {"id": "author_3", "title": "Author 3"}
        ]
    }
    
    with patch("pecha_api.search.search_views.knowledge_base_search_service", new_callable=AsyncMock, return_value=mock_result):
        
        response = client.get("/search/knowledge-base?query=test query&scope=all")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "titles" in data
        assert "content" in data
        assert "authors" in data
        assert len(data["titles"]) == 3
        assert len(data["authors"]) == 3
        assert data["content"] is not None


def test_knowledge_base_search_scope_title():
    """Test knowledge_base_search endpoint with scope='title'"""
    mock_result = {
        "titles": [
            {"id": "text_1", "title": "Text 1"},
            {"id": "text_2", "title": "Text 2"}
        ]
    }
    
    with patch("pecha_api.search.search_views.knowledge_base_search_service", new_callable=AsyncMock, return_value=mock_result) as mock_service:
        
        response = client.get("/search/knowledge-base?query=test query&scope=title&limit=10&offset=0")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "titles" in data
        assert len(data["titles"]) == 2
        
        mock_service.assert_called_once_with(
            scope="title",
            query="test query",
            offset=0,
            limit=10
        )


def test_knowledge_base_search_scope_author():
    """Test knowledge_base_search endpoint with scope='author'"""
    mock_result = {
        "authors": [
            {"id": "author_1", "title": "Author 1"},
            {"id": "author_2", "title": "Author 2"}
        ]
    }
    
    with patch("pecha_api.search.search_views.knowledge_base_search_service", new_callable=AsyncMock, return_value=mock_result) as mock_service:
        
        response = client.get("/search/knowledge-base?query=test author&scope=author&limit=10&offset=0")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "authors" in data
        assert len(data["authors"]) == 2
        
        mock_service.assert_called_once_with(
            scope="author",
            query="test author",
            offset=0,
            limit=10
        )


def test_knowledge_base_search_default_parameters():
    """Test knowledge_base_search endpoint with default parameters"""
    mock_result = {
        "titles": [],
        "content": None,
        "authors": []
    }
    
    with patch("pecha_api.search.search_views.knowledge_base_search_service", new_callable=AsyncMock, return_value=mock_result) as mock_service:
        
        response = client.get("/search/knowledge-base?query=test")
        
        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(
            scope="all",
            query="test",
            offset=0,
            limit=10
        )


def test_knowledge_base_search_with_custom_pagination():
    """Test knowledge_base_search endpoint with custom pagination"""
    mock_result = {
        "titles": [{"id": "text_1", "title": "Text 1"}]
    }
    
    with patch("pecha_api.search.search_views.knowledge_base_search_service", new_callable=AsyncMock, return_value=mock_result) as mock_service:
        
        response = client.get("/search/knowledge-base?query=test&scope=title&offset=5&limit=20")
        
        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(
            scope="title",
            query="test",
            offset=5,
            limit=20
        )


def test_knowledge_base_search_empty_results():
    """Test knowledge_base_search endpoint with empty results"""
    mock_result = {
        "titles": []
    }
    
    with patch("pecha_api.search.search_views.knowledge_base_search_service", new_callable=AsyncMock, return_value=mock_result):
        
        response = client.get("/search/knowledge-base?query=nonexistent&scope=title")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["titles"] == []


def test_knowledge_base_search_scope_all_empty_content():
    """Test knowledge_base_search endpoint with scope='all' when content is empty"""
    mock_result = {
        "titles": [{"id": "text_1", "title": "Text 1"}],
        "content": None,
        "authors": [{"id": "author_1", "title": "Author 1"}]
    }
    
    with patch("pecha_api.search.search_views.knowledge_base_search_service", new_callable=AsyncMock, return_value=mock_result):
        
        response = client.get("/search/knowledge-base?query=test&scope=all")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] is None
        assert len(data["titles"]) == 1
        assert len(data["authors"]) == 1


def test_knowledge_base_search_service_error():
    """Test knowledge_base_search endpoint when service raises an exception"""
    test_client = TestClient(api, raise_server_exceptions=False)
    
    with patch("pecha_api.search.search_views.knowledge_base_search_service", 
               new_callable=AsyncMock, side_effect=Exception("Service error")):
        
        response = test_client.get("/search/knowledge-base?query=test&scope=all")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR