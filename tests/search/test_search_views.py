import uuid
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.search.search_response_models import (
    TextIndex,
    MultilingualSearchResponse,
    MultilingualSourceResult,
    MultilingualSegmentMatch
)
from pecha_api.plans.plans_response_models import PlansResponse, PlanDTO, AuthorDTO
from pecha_api.plans.plans_enums import PlanStatus

from pecha_api.search.search_enums import MultilingualSearchType

client = TestClient(api)


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


def test_multilingual_search_with_search_type():
    """Test multilingual search with search_type parameter"""
    mock_response = MultilingualSearchResponse(
        query="query with search type",
        search_type="semantic",
        sources=[],
        skip=0,
        limit=10,
        total=0
    )
    
    with patch("pecha_api.search.search_views.get_multilingual_search_results", 
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get("/search/multilingual?query=query with search type&search_type=semantic")
        
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
            "/search/multilingual?query=full query&search_type=semantic&text_id=text_456&skip=10&limit=25"
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
    from pecha_api.search.search_response_models import SegmentLinkResponse

    mock_response = SegmentLinkResponse(text_id="text123", segment_id="segment456")

    with patch("pecha_api.search.search_views.get_url_link_service", new_callable=AsyncMock, return_value=mock_response):
        response = client.get("/search/chat/pecha_seg_123")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["text_id"] == "text123"
        assert data["segment_id"] == "segment456"


def test_get_url_link_segment_not_found():
    """Test get_url_link endpoint when segment is not found"""
    with patch(
        "pecha_api.search.search_views.get_url_link_service",
        new_callable=AsyncMock,
        side_effect=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pecha segment not found"),
    ):
        response = client.get("/search/chat/nonexistent_segment_id")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Pecha segment not found"


def test_get_url_link_with_special_characters():
    """Test get_url_link endpoint with special characters in pecha_segment_id"""
    from pecha_api.search.search_response_models import SegmentLinkResponse

    mock_response = SegmentLinkResponse(text_id="text-abc-123", segment_id="seg_456_xyz")

    with patch("pecha_api.search.search_views.get_url_link_service", new_callable=AsyncMock, return_value=mock_response):
        response = client.get("/search/chat/pecha-seg_123-xyz")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["text_id"] == "text-abc-123"
        assert data["segment_id"] == "seg_456_xyz"


def test_get_url_link_service_error():
    """Test get_url_link endpoint when service raises an exception"""
    with patch(
        "pecha_api.search.search_service.Segment.get_segment_by_pecha_segment_id",
        new_callable=AsyncMock,
        side_effect=Exception("Service error"),
    ):
        response = client.get("/search/chat/error_segment_id")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_get_url_link_with_uuid_format():
    """Test get_url_link endpoint with UUID-like pecha_segment_id"""
    from pecha_api.search.search_response_models import SegmentLinkResponse

    mock_response = SegmentLinkResponse(
        text_id="550e8400-e29b-41d4-a716-446655440000",
        segment_id="660e8400-e29b-41d4-a716-446655440001",
    )

    with patch("pecha_api.search.search_views.get_url_link_service", new_callable=AsyncMock, return_value=mock_response):
        response = client.get("/search/chat/550e8400-e29b-41d4-a716-446655440000")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["text_id"] == "550e8400-e29b-41d4-a716-446655440000"
        assert data["segment_id"] == "660e8400-e29b-41d4-a716-446655440001"


def test_get_url_link_empty_pecha_segment_id():
    """Test get_url_link endpoint with empty pecha_segment_id"""
    response = client.get("/search/chat/")
    
    assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_307_TEMPORARY_REDIRECT]


def test_get_url_link_with_long_pecha_segment_id():
    """Test get_url_link endpoint with very long pecha_segment_id"""
    from pecha_api.search.search_response_models import SegmentLinkResponse

    long_segment_id = "a" * 500
    mock_response = SegmentLinkResponse(text_id="text123", segment_id="seg456")

    with patch("pecha_api.search.search_views.get_url_link_service", new_callable=AsyncMock, return_value=mock_response):
        response = client.get(f"/search/chat/{long_segment_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["text_id"] == "text123"
        assert data["segment_id"] == "seg456"


# ============================================================================
# Tests for GET /search/plans endpoint
# ============================================================================

@pytest.mark.asyncio
async def test_search_plans_success():
    """Test search plans endpoint returns author's plans"""
    author_id = uuid.uuid4()
    plan_id = uuid.uuid4()
    
    mock_plans_response = PlansResponse(
        plans=[
            PlanDTO(
                id=plan_id,
                title="Test Plan",
                description="Test Description",
                language="en",
                total_days=7,
                status=PlanStatus.DRAFT,
                subscription_count=0,
                author=AuthorDTO(
                    id=author_id,
                    firstname="Test",
                    lastname="Author",
                    image_url="https://example.com/avatar.jpg"
                )
            )
        ],
        skip=0,
        limit=20,
        total=1
    )
    
    with patch("pecha_api.search.search_views.get_filtered_plans", 
               new_callable=AsyncMock, return_value=mock_plans_response):
        response = client.get(
            "/search/plans",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert len(data["plans"]) == 1
        assert data["plans"][0]["title"] == "Test Plan"


@pytest.mark.asyncio
async def test_search_plans_with_filters():
    """Test search plans endpoint with tag and search filters"""
    mock_plans_response = PlansResponse(
        plans=[],
        skip=0,
        limit=20,
        total=0
    )
    
    with patch("pecha_api.search.search_views.get_filtered_plans", 
               new_callable=AsyncMock, return_value=mock_plans_response) as mock_service:
        response = client.get(
            "/search/plans?tag=meditation&search=mindfulness",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(
            token="test-token",
            search="mindfulness",
            sort_by="created_at",
            sort_order="desc",
            skip=0,
            limit=20,
            tag="meditation",
            language=None,
        )


@pytest.mark.asyncio
async def test_search_plans_with_pagination():
    """Test search plans endpoint with pagination"""
    mock_plans_response = PlansResponse(
        plans=[],
        skip=10,
        limit=5,
        total=50
    )
    
    with patch("pecha_api.search.search_views.get_filtered_plans", 
               new_callable=AsyncMock, return_value=mock_plans_response):
        response = client.get(
            "/search/plans?skip=10&limit=5",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["skip"] == 10
        assert data["limit"] == 5
        assert data["total"] == 50


def test_search_plans_missing_authorization():
    """Test search plans endpoint without authorization header"""
    response = client.get("/search/plans")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_search_plans_invalid_token():
    """Test search plans endpoint with invalid token"""
    with patch("pecha_api.search.search_views.get_filtered_plans", 
               new_callable=AsyncMock, 
               side_effect=HTTPException(status_code=401, detail="Invalid token")):
        response = client.get(
            "/search/plans",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_search_plans_empty_results():
    """Test search plans endpoint with no results"""
    mock_plans_response = PlansResponse(
        plans=[],
        skip=0,
        limit=20,
        total=0
    )

    with patch("pecha_api.search.search_views.get_filtered_plans", 
               new_callable=AsyncMock, return_value=mock_plans_response):
        response = client.get(
            "/search/plans",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["plans"] == []
        assert data["total"] == 0


@pytest.mark.asyncio
async def test_search_plans_with_language_filter():
    """Test search plans endpoint with language filter"""
    mock_plans_response = PlansResponse(plans=[], skip=0, limit=20, total=0)

    with patch(
        "pecha_api.search.search_views.get_filtered_plans",
        new_callable=AsyncMock,
        return_value=mock_plans_response,
    ) as mock_service:
        response = client.get(
            "/search/plans?language=EN", headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(
            token="test-token",
            search=None,
            sort_by="created_at",
            sort_order="desc",
            skip=0,
            limit=20,
            tag=None,
            language="EN",
        )
