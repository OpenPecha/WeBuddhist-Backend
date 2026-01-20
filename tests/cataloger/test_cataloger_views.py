import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from fastapi import HTTPException
from starlette import status

from pecha_api.app import api
from pecha_api.cataloger.cataloger_response_model import (
    CatalogedTextsDetailsResponse,
    Relation,
    CatalogedTextsResponse,
    CatalogedTexts,
    Metadata
)

client = TestClient(api)

# Test constants
TEXT_ID = "test_text_123"
RELATED_TEXT_ID_1 = "related_text_1"
RELATED_TEXT_ID_2 = "related_text_2"
CATEGORY_ID = "cat_123"

# Mock data
MOCK_METADATA_1 = Metadata(
    text_id=RELATED_TEXT_ID_1,
    title={"en": "Related Text 1", "bo": "འབྲེལ་བ་དང་པོ།"},
    language="en"
)

MOCK_METADATA_2 = Metadata(
    text_id=RELATED_TEXT_ID_2,
    title={"bo": "འབྲེལ་བ་གཉིས་པ།"},
    language="bo"
)

MOCK_RELATION_1 = Relation(
    relation_type="translation",
    status=False,
    metadata=MOCK_METADATA_1
)

MOCK_RELATION_2 = Relation(
    relation_type="commentary",
    status=False,
    metadata=MOCK_METADATA_2
)

MOCK_CATALOGED_TEXT_RESPONSE = CatalogedTextsDetailsResponse(
    title={"en": "Test Title", "bo": "བརྟག་དཔྱད་མིང་།"},
    category_id=CATEGORY_ID,
    status=False,
    relations=[MOCK_RELATION_1, MOCK_RELATION_2]
)
@pytest.fixture
def mock_empty_response():
    return CatalogedTextsResponse(texts=[])

@pytest.fixture
def mock_single_text_response():
    return CatalogedTextsResponse(
        texts=[
            CatalogedTexts(
                text_id="text_1",
                title={"bo": "བོད་ཡིག", "en": "Tibetan Text"},
                language="bo",
                type="critical",
                status=False,
            )
        ]
    )
# Tests for GET /cataloger/texts/{text_id} endpoint

@pytest.mark.asyncio
async def test_read_cataloged_texts_details_success():
    # Test successful retrieval of cataloged text details
    with patch("pecha_api.cataloger.cataloger_views.get_cataloged_texts_details",
               new_callable=AsyncMock, return_value=MOCK_CATALOGED_TEXT_RESPONSE):
        
        response = client.get(f"/cataloger/texts/{TEXT_ID}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["title"] == {"en": "Test Title", "bo": "བརྟག་དཔྱད་མིང་།"}
        assert data["category_id"] == CATEGORY_ID
        assert data["status"] is False
        assert len(data["relations"]) == 2
        assert data["relations"][0]["relation_type"] == "translation"
        assert data["relations"][0]["metadata"]["text_id"] == RELATED_TEXT_ID_1
        assert data["relations"][1]["relation_type"] == "commentary"


@pytest.mark.asyncio
async def test_read_cataloged_texts_details_no_relations():
    # Test cataloged text details with no relations
    mock_response = CatalogedTextsDetailsResponse(
        title={"en": "Text Without Relations"},
        category_id=CATEGORY_ID,
        status=False,
        relations=[]
    )
    
    with patch("pecha_api.cataloger.cataloger_views.get_cataloged_texts_details",
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get(f"/cataloger/texts/{TEXT_ID}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["title"] == {"en": "Text Without Relations"}
        assert len(data["relations"]) == 0


@pytest.mark.asyncio
async def test_read_cataloged_texts_details_various_relation_types():
    # Test cataloged text details with various relation types
    relation_types = ["translation", "commentary", "reference", "source", "derivative"]
    
    mock_relations = [
        Relation(
            relation_type=rel_type,
            status=False,
            metadata=Metadata(
                text_id=f"text_{rel_type}",
                title={"en": f"{rel_type.capitalize()} Text"},
                language="en"
            )
        )
        for rel_type in relation_types
    ]
    
    mock_response = CatalogedTextsDetailsResponse(
        title={"en": "Text with Various Relations"},
        category_id="cat_various",
        status=False,
        relations=mock_relations
    )
    
    with patch("pecha_api.cataloger.cataloger_views.get_cataloged_texts_details",
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get("/cataloger/texts/text_various_relations")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["relations"]) == 5
        returned_relation_types = [rel["relation_type"] for rel in data["relations"]]
        assert set(returned_relation_types) == set(relation_types)


@pytest.mark.asyncio
async def test_read_cataloged_texts_details_service_error():
    # Test handling of service errors
    with patch("pecha_api.cataloger.cataloger_views.get_cataloged_texts_details",
               new_callable=AsyncMock, side_effect=HTTPException(
                   status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                   detail="Internal server error"
               )):
        
        response = client.get(f"/cataloger/texts/{TEXT_ID}")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_read_cataloged_texts_details_not_found():
    # Test handling of non-existent text
    with patch("pecha_api.cataloger.cataloger_views.get_cataloged_texts_details",
               new_callable=AsyncMock, side_effect=HTTPException(
                   status_code=status.HTTP_404_NOT_FOUND,
                   detail="Text not found"
               )):
        
        response = client.get("/cataloger/texts/nonexistent_text")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_read_cataloged_texts_details_external_api_error():
    # Test handling of external API errors
    with patch("pecha_api.cataloger.cataloger_views.get_cataloged_texts_details",
               new_callable=AsyncMock, side_effect=HTTPException(
                   status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                   detail="External service unavailable"
               )):
        
        response = client.get(f"/cataloger/texts/{TEXT_ID}")
        
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


@pytest.mark.asyncio
async def test_read_cataloged_texts_details_multilingual_titles():
    # Test cataloged text with multilingual titles
    mock_response = CatalogedTextsDetailsResponse(
        title={
            "en": "English Title",
            "bo": "བོད་སྐད་མིང་།",
            "zh": "中文标题"
        },
        category_id=CATEGORY_ID,
        status=False,
        relations=[
            Relation(
                relation_type="translation",
                status=False,
                metadata=Metadata(
                    text_id="multi_lang_text",
                    title={
                        "en": "Related English",
                        "bo": "འབྲེལ་བོད་སྐད།"
                    },
                    language="en"
                )
            )
        ]
    )
    
    with patch("pecha_api.cataloger.cataloger_views.get_cataloged_texts_details",
               new_callable=AsyncMock, return_value=mock_response):
        
        response = client.get(f"/cataloger/texts/{TEXT_ID}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert len(data["title"]) == 3
        assert data["title"]["en"] == "English Title"
        assert data["title"]["bo"] == "བོད་སྐད་མིང་།"
        assert data["title"]["zh"] == "中文标题"


@pytest.mark.asyncio
async def test_read_cataloged_texts_details_response_structure():
    # Test response structure validation
    with patch("pecha_api.cataloger.cataloger_views.get_cataloged_texts_details",
               new_callable=AsyncMock, return_value=MOCK_CATALOGED_TEXT_RESPONSE):
        
        response = client.get(f"/cataloger/texts/{TEXT_ID}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Validate all required fields are present
        required_fields = ["title", "category_id", "status", "relations"]
        for field in required_fields:
            assert field in data
        
        # Validate relation structure
        if data["relations"]:
            relation_required_fields = ["relation_type", "status", "metadata"]
            for rel in data["relations"]:
                for field in relation_required_fields:
                    assert field in rel
                
                # Validate metadata structure
                metadata_required_fields = ["text_id", "title", "language"]
                for field in metadata_required_fields:
                    assert field in rel["metadata"]

@pytest.mark.asyncio
async def test_read_cataloged_texts_with_search(mocker, mock_single_text_response):
    mock_get_cataloged_texts = mocker.patch(
        "pecha_api.cataloger.cataloger_views.get_cataloged_texts",
        new_callable=AsyncMock,
        return_value=mock_single_text_response,
    )

    async with AsyncClient(
        transport=ASGITransport(app=api), base_url="http://test"
    ) as ac:
        response = await ac.get("/cataloger/texts?search=Tibetan")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["texts"]) == 1
    assert data["texts"][0]["text_id"] == "text_1"
    mock_get_cataloged_texts.assert_called_once_with(search="Tibetan", skip=0, limit=10)


@pytest.mark.asyncio
async def test_read_cataloged_texts_with_params(mocker, mock_empty_response):
    mock_get_cataloged_texts = mocker.patch(
        "pecha_api.cataloger.cataloger_views.get_cataloged_texts",
        new_callable=AsyncMock,
        return_value=mock_empty_response,
    )

    async with AsyncClient(
        transport=ASGITransport(app=api), base_url="http://test"
    ) as ac:
        response = await ac.get("/cataloger/texts?skip=20&limit=5")

    assert response.status_code == status.HTTP_200_OK
    mock_get_cataloged_texts.assert_called_once_with(search=None, skip=20, limit=5)


@pytest.mark.asyncio
async def test_read_cataloged_texts_default_params(mocker, mock_single_text_response):
    mock_get_cataloged_texts = mocker.patch(
        "pecha_api.cataloger.cataloger_views.get_cataloged_texts",
        new_callable=AsyncMock,
        return_value=mock_single_text_response,
    )

    async with AsyncClient(
        transport=ASGITransport(app=api), base_url="http://test"
    ) as ac:
        response = await ac.get("/cataloger/texts")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["texts"]) == 1
    assert data["texts"][0]["text_id"] == "text_1"
    mock_get_cataloged_texts.assert_called_once_with(search=None, skip=0, limit=10)

