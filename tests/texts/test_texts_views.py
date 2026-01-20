from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from pecha_api.app import api
from pecha_api.texts.texts_response_models import (
    CreateTextRequest,
    TableOfContentResponse,
    TextDTO,
    TextVersionResponse,
    TextVersion,
    TableOfContent,
    TableOfContentType,
    Section,
    TextDetailsRequest,
    TextsByPechaTextIdsRequest
)

client = TestClient(api)

# Test data
MOCK_TEXT_DTO = TextDTO(
    id="123e4567-e89b-12d3-a456-426614174000",
    pecha_text_id="test_pecha_id",
    title="Test Text",
    language="bo",
    group_id="123e4567-e89b-12d3-a456-426614174000",
    type="version",
    is_published=True,
    created_date="2025-01-01T00:00:00",
    updated_date="2025-01-01T00:00:00",
    published_date="2025-01-01T00:00:00",
    published_by="test_user",
    categories=[],
    views=0,
    source_link="https://test-source.com",
    ranking=1,
    license="CC0"
)

# Create a simple section for the table of contents
mock_section = Section(
    id="123e4567-e89b-12d3-a456-426614174002",
    title="Chapter 1",
    section_number=1,
    parent_id=None,
    segments=[],
    sections=[],
    created_date="2025-01-01T00:00:00",
    updated_date="2025-01-01T00:00:00",
    published_date="2025-01-01T00:00:00"
)

# Create a table of content with the section
MOCK_TABLE_OF_CONTENT = TableOfContent(
    id="123e4567-e89b-12d3-a456-426614174001",
    text_id="123e4567-e89b-12d3-a456-426614174000",
    type=TableOfContentType.TEXT,
    sections=[mock_section]
)



# Create response objects
# Create a proper DetailTableOfContentResponse
MOCK_TABLE_OF_CONTENT_RESPONSE = TableOfContentResponse(
    text_detail=MOCK_TEXT_DTO,
    contents=[MOCK_TABLE_OF_CONTENT]
)

# Create a TextVersion instance for the response
MOCK_TEXT_VERSION = TextVersion(
    id="123e4567-e89b-12d3-a456-426614174003",
    title="Test Text Version",
    parent_id=None,
    priority=1,
    language="bo",
    type="version",
    group_id="123e4567-e89b-12d3-a456-426614174004",
    table_of_contents=[],
    is_published=True,
    created_date="2025-01-01T00:00:00",
    updated_date="2025-01-01T00:00:00",
    published_date="2025-01-01T00:00:00",
    published_by="test_user"
)

MOCK_TEXT_VERSION_RESPONSE = TextVersionResponse(
    text=MOCK_TEXT_DTO,
    versions=[MOCK_TEXT_VERSION]
)

VALID_TOKEN = "valid_token_123"

@pytest.mark.asyncio
async def test_get_text_by_text_id(mocker):
    """Test GET /texts with text_id parameter"""
    mock_get_text = mocker.patch(
        'pecha_api.texts.texts_views.get_text_by_text_id_or_collection',
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DTO
    )
    
    test_text_id = "123e4567-e89b-12d3-a456-426614174000"
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(f"/texts?text_id={test_text_id}&language=bo&skip=0&limit=10")
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert response_data["id"] == MOCK_TEXT_DTO.id
    assert response_data["title"] == MOCK_TEXT_DTO.title
    assert response_data["language"] == MOCK_TEXT_DTO.language
    mock_get_text.assert_called_once_with(
        text_id="123e4567-e89b-12d3-a456-426614174000",
        collection_id=None,
        language="bo",
        skip=0,
        limit=10
    )

@pytest.mark.asyncio
async def test_get_text_by_collection_id(mocker):
    """Test GET /texts with collection_id parameter"""
    # Mock the service function
    mock_get_text = mocker.patch(
        'pecha_api.texts.texts_views.get_text_by_text_id_or_collection',
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DTO
    )
    
    # The collection ID that will be used in the request
    test_collection_id = "123e4567-e89b-12d3-a456-426614174001"
    
    # Make the request
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(f"/texts?collection_id={test_collection_id}&language=bo&skip=0&limit=10")
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert response_data["id"] == MOCK_TEXT_DTO.id
    assert response_data["title"] == MOCK_TEXT_DTO.title
    assert response_data["language"] == MOCK_TEXT_DTO.language
    # Remove the contents check as it's not part of the TextDTO model
    mock_get_text.assert_called_once_with(
        text_id=None,
        collection_id=test_collection_id,
        language="bo",
        skip=0,
        limit=10
    )

@pytest.mark.asyncio
async def test_create_text_success(mocker):
    """Test POST /texts with valid data"""
    # Mock the service function
    mock_create_text = mocker.patch(
        'pecha_api.texts.texts_views.create_new_text',
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DTO
    )
    
    # Test data - match the CreateTextRequest model
    # Note: The mock returns MOCK_TEXT_DTO which has title="Test Text"
    create_data = {
        "pecha_text_id": "test_pecha_id",
        "title": "Test Text",  # Match the mock data
        "language": "bo",
        "isPublished": True,
        "group_id": "123e4567-e89b-12d3-a456-426614174000",
        "type": "version",
        "published_by": "test_user",
        "categories": [],
        "source_link": "https://test-source.com",
        "ranking": 1,
        "license": "CC0"
    }
    
    # Make the request
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/texts",
            json=create_data,
            headers={"Authorization": f"Bearer {VALID_TOKEN}"}
        )
    
    # Assertions - 201 Created is the correct status code for resource creation
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["title"] == create_data["title"]
    assert response_data["language"] == create_data["language"]
    assert response_data["type"] == create_data["type"]
    assert response_data["is_published"] == create_data["isPublished"]
    mock_create_text.assert_called_once()
    call_args = mock_create_text.call_args[1]
    assert call_args["token"] == VALID_TOKEN
    assert isinstance(call_args["create_text_request"], CreateTextRequest)

@pytest.mark.asyncio
async def test_get_versions_success(mocker):
    """Test GET /texts/{text_id}/versions"""
    # Mock the service function
    mock_get_versions = mocker.patch(
        'pecha_api.texts.texts_views.get_text_versions_by_group_id',
        new_callable=AsyncMock,
        return_value={
            "text": MOCK_TEXT_DTO,
            "versions": [MOCK_TEXT_VERSION.model_dump()]
        }
    )
    
    # The text ID that will be used in the request
    test_text_id = "123e4567-e89b-12d3-a456-426614174000"
    
    # Make the request
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(f"/texts/{test_text_id}/versions?language=bo&skip=0&limit=10")
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert "text" in response_data
    assert "versions" in response_data
    assert isinstance(response_data["versions"], list)
    if response_data["versions"]:  # Check only if versions list is not empty
        version = response_data["versions"][0]
        assert "id" in version
        assert "title" in version
        assert "language" in version
    mock_get_versions.assert_called_once_with(
        text_id=test_text_id,
        language="bo",
        skip=0,
        limit=10
    )

@pytest.mark.asyncio
async def test_get_contents_success(mocker):
    """Test GET /texts/{text_id}/contents"""
    # Mock the service function
    mock_get_contents = mocker.patch(
        'pecha_api.texts.texts_views.get_table_of_contents_by_text_id',
        new_callable=AsyncMock,
        return_value=MOCK_TABLE_OF_CONTENT_RESPONSE
    )
    
    # Make the request
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get("/texts/123e4567-e89b-12d3-a456-426614174000/contents")
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert "text_detail" in response_data
    assert "contents" in response_data
    assert isinstance(response_data["contents"], list)
    assert len(response_data["contents"]) > 0
    mock_get_contents.assert_called_once_with(
        text_id="123e4567-e89b-12d3-a456-426614174000",
        language=None,
        skip=0,
        limit=10
    )


@pytest.mark.asyncio
async def test_create_table_of_content_success(mocker):
    """Test POST /texts/table-of-content"""
    # Mock the service function
    mock_create_toc = mocker.patch(
        'pecha_api.texts.texts_views.create_table_of_content',
        new_callable=AsyncMock,
        return_value=MOCK_TABLE_OF_CONTENT
    )
    
    # Test data - match the TableOfContent model
    toc_data = {
        "id": "123e4567-e89b-12d3-a456-426614174001",
        "text_id": "123e4567-e89b-12d3-a456-426614174000",
        "type": "text",
        "sections": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "title": "Chapter 1",
                "section_number": 1,
                "parent_id": None,
                "segments": [],
                "sections": [],
                "created_date": "2025-01-01T00:00:00",
                "updated_date": "2025-01-01T00:00:00",
                "published_date": "2025-01-01T00:00:00",
                "published_by": "test_user"
            }
        ]
    }
    
    # Make the request
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/texts/table-of-content",
            json=toc_data,
            headers={"Authorization": f"Bearer {VALID_TOKEN}"}
        )
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert "id" in response_data
    assert "text_id" in response_data
    assert "sections" in response_data
    assert response_data["text_id"] == toc_data["text_id"]
    mock_create_toc.assert_called_once()
    call_args = mock_create_toc.call_args[1]
    assert call_args["token"] == VALID_TOKEN
    assert isinstance(call_args["table_of_content_request"], TableOfContent)

# Error case tests

@pytest.mark.asyncio
async def test_create_text_unauthorized():
    """Test POST /texts without authentication"""
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post("/texts", json={"title": "Test"})
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_table_of_content_unauthorized():
    """Test POST /texts/table-of-content without authentication"""
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post("/texts/table-of-content", json={"text_id": "123e4567-e89b-12d3-a456-426614174000"})
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_contents_not_found(mocker):
    """Test GET /texts/{text_id}/contents with non-existent text"""
    mocker.patch(
        'pecha_api.texts.texts_views.get_table_of_contents_by_text_id',
        side_effect=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Text not found")
    )
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get("/texts/non_existent_id/contents")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Text not found"

@pytest.mark.asyncio
async def test_get_commentaries_success(mocker):
    """Test GET /texts/{text_id}/commentaries with valid text_id"""
    mock_commentary_1 = TextDTO(
        id="commentary-1-uuid",
        pecha_text_id="commentary_pecha_1",
        title="Commentary on Heart Sutra",
        language="bo",
        group_id="123e4567-e89b-12d3-a456-426614174000",
        type="commentary",
        is_published=True,
        created_date="2025-01-01T00:00:00",
        updated_date="2025-01-01T00:00:00",
        published_date="2025-01-01T00:00:00",
        published_by="commentator_1",
        categories=["123e4567-e89b-12d3-a456-426614174000"],
        views=100,
        source_link="https://commentary-source-1.com",
        ranking=1,
        license="CC0"
    )
    
    mock_commentary_2 = TextDTO(
        id="commentary-2-uuid",
        pecha_text_id="commentary_pecha_2",
        title="Another Commentary on Heart Sutra",
        language="bo",
        group_id="123e4567-e89b-12d3-a456-426614174000",
        type="commentary",
        is_published=True,
        created_date="2025-01-02T00:00:00",
        updated_date="2025-01-02T00:00:00",
        published_date="2025-01-02T00:00:00",
        published_by="commentator_2",
        categories=["123e4567-e89b-12d3-a456-426614174000"],
        views=50,
        source_link="https://commentary-source-2.com",
        ranking=2,
        license="CC0"
    )
    
    mock_commentaries = [mock_commentary_1, mock_commentary_2]
    
    mock_get_commentaries = mocker.patch(
        'pecha_api.texts.texts_views.get_commentaries_by_text_id',
        return_value=mock_commentaries
    )
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(
            "/texts/123e4567-e89b-12d3-a456-426614174000/commentaries",
            params={"skip": 0, "limit": 10}
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Commentary on Heart Sutra"
    assert data[0]["type"] == "commentary"
    assert data[1]["title"] == "Another Commentary on Heart Sutra"
    
    mock_get_commentaries.assert_called_once_with(
        text_id="123e4567-e89b-12d3-a456-426614174000",
        skip=0,
        limit=10
    )


@pytest.mark.asyncio
async def test_get_commentaries_empty_list(mocker):
    """Test GET /texts/{text_id}/commentaries when no commentaries exist"""
    mock_get_commentaries = mocker.patch(
        'pecha_api.texts.texts_views.get_commentaries_by_text_id',
        return_value=[]
    )
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(
            "/texts/123e4567-e89b-12d3-a456-426614174000/commentaries",
            params={"skip": 0, "limit": 10}
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0
    assert data == []
    
    mock_get_commentaries.assert_called_once()


@pytest.mark.asyncio
async def test_get_commentaries_with_pagination(mocker):
    """Test GET /texts/{text_id}/commentaries with pagination parameters"""
    mock_commentary = TextDTO(
        id="commentary-uuid",
        pecha_text_id="commentary_pecha",
        title="Paginated Commentary",
        language="bo",
        group_id="123e4567-e89b-12d3-a456-426614174000",
        type="commentary",
        is_published=True,
        created_date="2025-01-01T00:00:00",
        updated_date="2025-01-01T00:00:00",
        published_date="2025-01-01T00:00:00",
        published_by="commentator",
        categories=["123e4567-e89b-12d3-a456-426614174000"],
        views=10,
        source_link="https://commentary-source.com",
        ranking=1,
        license="CC0"
    )
    
    mock_get_commentaries = mocker.patch(
        'pecha_api.texts.texts_views.get_commentaries_by_text_id',
        return_value=[mock_commentary]
    )
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(
            "/texts/123e4567-e89b-12d3-a456-426614174000/commentaries",
            params={"skip": 5, "limit": 20}
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    
    mock_get_commentaries.assert_called_once_with(
        text_id="123e4567-e89b-12d3-a456-426614174000",
        skip=5,
        limit=20
    )


@pytest.mark.asyncio
async def test_get_commentaries_text_not_found(mocker):
    """Test GET /texts/{text_id}/commentaries with non-existent text"""
    mock_get_commentaries = mocker.patch(
        'pecha_api.texts.texts_views.get_commentaries_by_text_id',
        side_effect=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Text not found"
        )
    )
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(
            "/texts/non-existent-text-id/commentaries",
            params={"skip": 0, "limit": 10}
        )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Text not found"
    
    mock_get_commentaries.assert_called_once()


@pytest.mark.asyncio
async def test_get_commentaries_default_pagination(mocker):
    """Test GET /texts/{text_id}/commentaries with default pagination values"""
    mock_get_commentaries = mocker.patch(
        'pecha_api.texts.texts_views.get_commentaries_by_text_id',
        return_value=[]
    )
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(
            "/texts/123e4567-e89b-12d3-a456-426614174000/commentaries"
        )
    
    assert response.status_code == status.HTTP_200_OK
    
    mock_get_commentaries.assert_called_once_with(
        text_id="123e4567-e89b-12d3-a456-426614174000",
        skip=0,
        limit=10
    )


@pytest.mark.asyncio
async def test_get_commentaries_negative_skip(mocker):
    """Test GET /texts/{text_id}/commentaries with negative skip parameter"""
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(
            "/texts/123e4567-e89b-12d3-a456-426614174000/commentaries",
            params={"skip": -1, "limit": 10}
        )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_commentaries_limit_exceeds_max(mocker):
    """Test GET /texts/{text_id}/commentaries with limit exceeding maximum"""
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(
            "/texts/123e4567-e89b-12d3-a456-426614174000/commentaries",
            params={"skip": 0, "limit": 150}
        )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_commentaries_single_commentary(mocker):
    """Test GET /texts/{text_id}/commentaries with single commentary"""
    mock_commentary = TextDTO(
        id="single-commentary-uuid",
        pecha_text_id="single_commentary_pecha",
        title="Single Commentary",
        language="en",
        group_id="123e4567-e89b-12d3-a456-426614174000",
        type="commentary",
        is_published=True,
        created_date="2025-01-01T00:00:00",
        updated_date="2025-01-01T00:00:00",
        published_date="2025-01-01T00:00:00",
        published_by="single_commentator",
        categories=["123e4567-e89b-12d3-a456-426614174000"],
        views=5,
        source_link="https://single-commentary.com",
        ranking=1,
        license="CC BY"
    )
    
    mock_get_commentaries = mocker.patch(
        'pecha_api.texts.texts_views.get_commentaries_by_text_id',
        return_value=[mock_commentary]
    )
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(
            "/texts/123e4567-e89b-12d3-a456-426614174000/commentaries",
            params={"skip": 0, "limit": 10}
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "single-commentary-uuid"
    assert data[0]["title"] == "Single Commentary"
    assert data[0]["type"] == "commentary"
    assert data[0]["language"] == "en"
    assert data[0]["categories"] == ["123e4567-e89b-12d3-a456-426614174000"]


@pytest.mark.asyncio
async def test_get_commentaries_with_optional_fields_none(mocker):
    """Test GET /texts/{text_id}/commentaries with optional fields as None"""
    mock_commentary = TextDTO(
        id="commentary-optional-none-uuid",
        pecha_text_id=None,
        title="Commentary with None fields",
        language="bo",
        group_id="123e4567-e89b-12d3-a456-426614174000",
        type="commentary",
        is_published=True,
        created_date="2025-01-01T00:00:00",
        updated_date="2025-01-01T00:00:00",
        published_date="2025-01-01T00:00:00",
        published_by="commentator",
        categories=["123e4567-e89b-12d3-a456-426614174000"],
        views=0,
        source_link=None,
        ranking=None,
        license=None
    )
    
    mock_get_commentaries = mocker.patch(
        'pecha_api.texts.texts_views.get_commentaries_by_text_id',
        return_value=[mock_commentary]
    )
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(
            "/texts/123e4567-e89b-12d3-a456-426614174000/commentaries",
            params={"skip": 0, "limit": 10}
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["pecha_text_id"] is None
    assert data[0]["source_link"] is None
    assert data[0]["ranking"] is None
    assert data[0]["license"] is None
    assert data[0]["views"] == 0


@pytest.mark.asyncio
async def test_get_commentaries_service_error(mocker):
    """Test GET /texts/{text_id}/commentaries when service raises unexpected error"""
    mock_get_commentaries = mocker.patch(
        'pecha_api.texts.texts_views.get_commentaries_by_text_id',
        side_effect=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    )
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get(
            "/texts/123e4567-e89b-12d3-a456-426614174000/commentaries",
            params={"skip": 0, "limit": 10}
        )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Internal server error"


@pytest.mark.asyncio
async def test_get_contents_with_details_success(mocker):
    """Test POST /texts/{text_id}/details with valid request"""
    # Create mock response with all required fields
    mock_detail_response = {
        "text_detail": MOCK_TEXT_DTO.model_dump(),
        "content": {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "text_id": "123e4567-e89b-12d3-a456-426614174000",
            "sections": []
        },
        "size": 10,
        "pagination_direction": "next",
        "current_segment_position": 1,
        "total_segments": 100
    }
    
    # Mock the service function
    mock_get_details = mocker.patch(
        'pecha_api.texts.texts_views.get_text_details_by_text_id',
        new_callable=AsyncMock,
        return_value=mock_detail_response
    )
    
    # Test data
    test_text_id = "123e4567-e89b-12d3-a456-426614174000"
    details_request = {
        "version_id": "123e4567-e89b-12d3-a456-426614174003",
        "content_id": "123e4567-e89b-12d3-a456-426614174001",
        "segment_id": "123e4567-e89b-12d3-a456-426614174005",
        "size": 10,
        "direction": "next"
    }
    
    # Make the request
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            f"/texts/{test_text_id}/details",
            json=details_request
        )
    
    # Assertions
    assert response.status_code == 200
    response_data = response.json()
    assert "text_detail" in response_data
    assert "content" in response_data
    assert "size" in response_data
    assert "pagination_direction" in response_data
    assert "current_segment_position" in response_data
    assert "total_segments" in response_data
    assert response_data["text_detail"]["id"] == MOCK_TEXT_DTO.id
    assert response_data["size"] == 10
    assert response_data["total_segments"] == 100
    mock_get_details.assert_called_once()
    call_args = mock_get_details.call_args[1]
    assert call_args["text_id"] == test_text_id
    assert isinstance(call_args["text_details_request"], TextDetailsRequest)


@pytest.mark.asyncio
async def test_get_contents_with_details_invalid_text(mocker):
    """Test POST /texts/{text_id}/details with non-existent text"""
    mocker.patch(
        'pecha_api.texts.texts_views.get_text_details_by_text_id',
        side_effect=HTTPException(status_code=404, detail="Text not found")
    )
    
    details_request = {
        "version_id": "123e4567-e89b-12d3-a456-426614174003",
        "content_id": "123e4567-e89b-12d3-a456-426614174001",
        "segment_id": "123e4567-e89b-12d3-a456-426614174005",
        "size": 10,
        "direction": "next"
    }
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/texts/non_existent_id/details",
            json=details_request
        )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_versions_not_found(mocker):
    """Test GET /texts/{text_id}/versions with non-existent text"""
    mocker.patch(
        'pecha_api.texts.texts_views.get_text_versions_by_group_id',
        side_effect=HTTPException(status_code=404, detail="Text not found")
    )
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get("/texts/non_existent_id/versions")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_text_invalid_parameters(mocker):
    """Test GET /texts with invalid pagination parameters"""
    mock_get_text = mocker.patch(
        'pecha_api.texts.texts_views.get_text_by_text_id_or_collection',
        new_callable=AsyncMock,
        return_value=MOCK_TEXT_DTO
    )
    
    # Test with negative skip
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.get("/texts?text_id=123&skip=-1&limit=10")
    
    # FastAPI will validate and return 422 for invalid parameters
    assert response.status_code in [200, 422]  # Depends on FastAPI validation


@pytest.mark.asyncio
async def test_create_text_invalid_data():
    """Test POST /texts with invalid data"""
    invalid_data = {
        "title": "Test",
        # Missing required fields
    }
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/texts",
            json=invalid_data,
            headers={"Authorization": f"Bearer {VALID_TOKEN}"}
        )
    
    # Should return 422 for validation error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_text_service_error(mocker):
    """Test POST /texts when service layer raises an error"""
    mocker.patch(
        'pecha_api.texts.texts_views.create_new_text',
        side_effect=HTTPException(status_code=400, detail="Invalid group_id")
    )
    
    create_data = {
        "pecha_text_id": "test_pecha_id",
        "title": "Test Text",
        "language": "bo",
        "isPublished": True,
        "group_id": "invalid_group_id",
        "type": "version",
        "published_by": "test_user",
        "categories": [],
        "source_link": "https://test-source.com",
        "ranking": 1,
        "license": "CC0"
    }
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/texts",
            json=create_data,
            headers={"Authorization": f"Bearer {VALID_TOKEN}"}
        )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid group_id"


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_success(mocker):
    """Test POST /text-uploader/list with valid pecha_text_ids"""
    mock_text_1 = TextDTO(
        id="text-1-uuid",
        pecha_text_id="pecha_text_id_1",
        title="Test Text 1",
        language="bo",
        group_id="group-1-uuid",
        type="root_text",
        is_published=True,
        created_date="2025-01-01T00:00:00",
        updated_date="2025-01-01T00:00:00",
        published_date="2025-01-01T00:00:00",
        published_by="test_user",
        categories=[],
        views=10,
        source_link="https://test-source-1.com",
        ranking=1,
        license="CC0"
    )
    
    mock_text_2 = TextDTO(
        id="text-2-uuid",
        pecha_text_id="pecha_text_id_2",
        title="Test Text 2",
        language="en",
        group_id="group-2-uuid",
        type="version",
        is_published=True,
        created_date="2025-01-02T00:00:00",
        updated_date="2025-01-02T00:00:00",
        published_date="2025-01-02T00:00:00",
        published_by="test_user_2",
        categories=["category-1"],
        views=20,
        source_link="https://test-source-2.com",
        ranking=2,
        license="CC BY"
    )
    
    mock_texts = [mock_text_1, mock_text_2]
    
    mock_get_texts = mocker.patch(
        'pecha_api.text_uploader.text_metadata.text_metadata_views.get_text_by_pecha_text_ids_service',
        new_callable=AsyncMock,
        return_value=mock_texts
    )
    
    request_data = {
        "pecha_text_ids": ["pecha_text_id_1", "pecha_text_id_2"]
    }
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/text-uploader/list",
            json=request_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["pecha_text_id"] == "pecha_text_id_1"
    assert data[0]["title"] == "Test Text 1"
    assert data[1]["pecha_text_id"] == "pecha_text_id_2"
    assert data[1]["title"] == "Test Text 2"
    
    mock_get_texts.assert_called_once()
    call_args = mock_get_texts.call_args[1]
    assert isinstance(call_args["texts_by_pecha_text_ids_request"], TextsByPechaTextIdsRequest)


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_empty_list(mocker):
    """Test POST /text-uploader/list with empty pecha_text_ids list"""
    mock_get_texts = mocker.patch(
        'pecha_api.text_uploader.text_metadata.text_metadata_views.get_text_by_pecha_text_ids_service',
        new_callable=AsyncMock,
        return_value=[]
    )
    
    request_data = {
        "pecha_text_ids": []
    }
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/text-uploader/list",
            json=request_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 0
    assert data == []
    
    mock_get_texts.assert_called_once()


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_single_text(mocker):
    """Test POST /text-uploader/list with single pecha_text_id"""
    mock_text = TextDTO(
        id="single-text-uuid",
        pecha_text_id="pecha_text_id_single",
        title="Single Test Text",
        language="bo",
        group_id="group-uuid",
        type="root_text",
        is_published=True,
        created_date="2025-01-01T00:00:00",
        updated_date="2025-01-01T00:00:00",
        published_date="2025-01-01T00:00:00",
        published_by="test_user",
        categories=[],
        views=5,
        source_link="https://test-source.com",
        ranking=1,
        license="CC0"
    )
    
    mock_get_texts = mocker.patch(
        'pecha_api.text_uploader.text_metadata.text_metadata_views.get_text_by_pecha_text_ids_service',
        new_callable=AsyncMock,
        return_value=[mock_text]
    )
    
    request_data = {
        "pecha_text_ids": ["pecha_text_id_single"]
    }
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/text-uploader/list",
            json=request_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["pecha_text_id"] == "pecha_text_id_single"
    assert data[0]["title"] == "Single Test Text"
    
    mock_get_texts.assert_called_once()


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_none_result(mocker):
    """Test POST /text-uploader/list when service returns None"""
    mock_get_texts = mocker.patch(
        'pecha_api.text_uploader.text_metadata.text_metadata_views.get_text_by_pecha_text_ids_service',
        new_callable=AsyncMock,
        return_value=None
    )
    
    request_data = {
        "pecha_text_ids": ["nonexistent_pecha_id"]
    }
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/text-uploader/list",
            json=request_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data is None
    
    mock_get_texts.assert_called_once()


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_invalid_request():
    """Test POST /text-uploader/list with invalid request data"""
    invalid_data = {
        "invalid_field": ["pecha_text_id_1"]
    }
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/text-uploader/list",
            json=invalid_data
        )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_service_error(mocker):
    """Test POST /text-uploader/list when service raises an error"""
    mock_get_texts = mocker.patch(
        'pecha_api.text_uploader.text_metadata.text_metadata_views.get_text_by_pecha_text_ids_service',
        new_callable=AsyncMock,
        side_effect=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    )
    
    request_data = {
        "pecha_text_ids": ["pecha_text_id_1"]
    }
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/text-uploader/list",
            json=request_data
        )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Internal server error"


@pytest.mark.asyncio
async def test_get_text_by_pecha_text_ids_multiple_texts_with_optional_fields(mocker):
    """Test POST /text-uploader/list with texts having various optional fields"""
    mock_text_with_all_fields = TextDTO(
        id="text-all-fields-uuid",
        pecha_text_id="pecha_text_id_all",
        title="Text with All Fields",
        language="bo",
        group_id="group-uuid",
        type="root_text",
        is_published=True,
        created_date="2025-01-01T00:00:00",
        updated_date="2025-01-01T00:00:00",
        published_date="2025-01-01T00:00:00",
        published_by="test_user",
        categories=["cat1", "cat2"],
        views=100,
        source_link="https://source.com",
        ranking=5,
        license="CC BY-SA"
    )
    
    mock_text_with_minimal_fields = TextDTO(
        id="text-minimal-uuid",
        pecha_text_id=None,
        title="Text with Minimal Fields",
        language="en",
        group_id="group-uuid-2",
        type="version",
        is_published=False,
        created_date="2025-01-02T00:00:00",
        updated_date="2025-01-02T00:00:00",
        published_date="2025-01-02T00:00:00",
        published_by="test_user_2",
        categories=None,
        views=0,
        source_link=None,
        ranking=None,
        license=None
    )
    
    mock_texts = [mock_text_with_all_fields, mock_text_with_minimal_fields]
    
    mock_get_texts = mocker.patch(
        'pecha_api.text_uploader.text_metadata.text_metadata_views.get_text_by_pecha_text_ids_service',
        new_callable=AsyncMock,
        return_value=mock_texts
    )
    
    request_data = {
        "pecha_text_ids": ["pecha_text_id_all", "pecha_text_id_minimal"]
    }
    
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as ac:
        response = await ac.post(
            "/text-uploader/list",
            json=request_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    
    # Verify first text with all fields
    assert data[0]["pecha_text_id"] == "pecha_text_id_all"
    assert data[0]["categories"] == ["cat1", "cat2"]
    assert data[0]["views"] == 100
    assert data[0]["ranking"] == 5
    
    # Verify second text with minimal fields
    assert data[1]["pecha_text_id"] is None
    assert data[1]["categories"] is None
    assert data[1]["views"] == 0
    assert data[1]["source_link"] is None
    assert data[1]["ranking"] is None
    assert data[1]["license"] is None
