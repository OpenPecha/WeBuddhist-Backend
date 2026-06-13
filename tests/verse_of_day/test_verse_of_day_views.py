import pytest
from uuid import uuid4
from datetime import date
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.verse_of_day.verse_of_day_response_models import (
    VerseOfDayPublicResponse,
    VerseOfDayPublicDTO,
    VerseOfDayDTO,
    CreateVerseOfDayRequest,
)


client = TestClient(api)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_verse_public_dto():
    """Sample public verse DTO for testing (all languages)."""
    return VerseOfDayPublicDTO(
        id=uuid4(),
        verses={
            "en": "May all beings be happy and free from suffering.",
            "bo": ["སེམས་ཅན་ཐམས་ཅད་བདེ་བ་དང་།", "སྡུག་བསྔལ་བྲལ་བར་གྱུར་ཅིག"],
            "zh": "愿一切众生快乐，远离痛苦。"
        },
        image_urls=["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
        ref_id="text-123",
        ref_type="sutra",
        date=date(2025, 6, 5)
    )


@pytest.fixture
def sample_verse_public_response(sample_verse_public_dto):
    """Sample public response with verse."""
    return VerseOfDayPublicResponse(verse_of_day=sample_verse_public_dto)


@pytest.fixture
def sample_empty_response():
    """Sample response with no verse found."""
    return VerseOfDayPublicResponse(verse_of_day=None)


@pytest.fixture
def sample_verse_dto():
    """Sample full verse DTO for creation response."""
    return VerseOfDayDTO(
        id=uuid4(),
        verses={
            "en": "May all beings be happy and free from suffering.",
            "bo": ["སེམས་ཅན་ཐམས་ཅད་བདེ་བ་དང་།", "སྡུག་བསྔལ་བྲལ་བར་གྱུར་ཅིག"],
            "zh": "愿一切众生快乐，远离痛苦。"
        },
        image_urls=["https://example.com/image1.jpg"],
        verse_id="verse-456",
        ref_id="text-123",
        ref_type="sutra",
        group_id=uuid4(),
        date=date(2025, 6, 5)
    )


@pytest.fixture
def sample_create_request():
    """Sample create verse request with multilingual verses."""
    return CreateVerseOfDayRequest(
        verses={
            "en": "May all beings be happy and free from suffering.",
            "bo": ["སེམས་ཅན་ཐམས་ཅད་བདེ་བ་དང་།", "སྡུག་བསྔལ་བྲལ་བར་གྱུར་ཅིག"],
            "zh": "愿一切众生快乐，远离痛苦。"
        },
        image_urls=["https://example.com/image1.jpg"],
        verse_id="verse-456",
        ref_id="text-123",
        ref_type="sutra",
        group_id=uuid4(),
        date=date(2025, 6, 5)
    )


# =============================================================================
# GET /verse-of-day TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_success(sample_verse_public_response):
    """Test successful retrieval of verse of day with no filters."""
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day", return_value=sample_verse_public_response) as mock_service:
        response = client.get("/verse-of-day")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "verse_of_day" in data
        assert data["verse_of_day"] is not None
        assert "verses" in data["verse_of_day"]
        assert "en" in data["verse_of_day"]["verses"]
        assert data["verse_of_day"]["ref_id"] == "text-123"
        assert data["verse_of_day"]["ref_type"] == "sutra"
        assert "image_urls" in data["verse_of_day"]
        assert "date" in data["verse_of_day"]
        
        mock_service.assert_called_once_with(group_id=None, filter_date=None, lang=None)


@pytest.mark.asyncio
async def test_get_verse_of_day_with_group_id_filter(sample_verse_public_response):
    """Test retrieval of verse filtered by group_id."""
    group_id = uuid4()
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day", return_value=sample_verse_public_response) as mock_service:
        response = client.get(f"/verse-of-day?group_id={group_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["verse_of_day"] is not None
        mock_service.assert_called_once_with(group_id=group_id, filter_date=None, lang=None)


@pytest.mark.asyncio
async def test_get_verse_of_day_with_date_filter(sample_verse_public_response):
    """Test retrieval of verse filtered by date."""
    filter_date = date(2025, 6, 5)
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day", return_value=sample_verse_public_response) as mock_service:
        response = client.get(f"/verse-of-day?date=2025-06-05")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["verse_of_day"] is not None
        mock_service.assert_called_once_with(group_id=None, filter_date=filter_date, lang=None)


@pytest.mark.asyncio
async def test_get_verse_of_day_with_both_filters(sample_verse_public_response):
    """Test retrieval of verse with both group_id and date filters."""
    group_id = uuid4()
    filter_date = date(2025, 6, 5)
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day", return_value=sample_verse_public_response) as mock_service:
        response = client.get(f"/verse-of-day?group_id={group_id}&date=2025-06-05")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["verse_of_day"] is not None
        mock_service.assert_called_once_with(group_id=group_id, filter_date=filter_date, lang=None)


@pytest.mark.asyncio
async def test_get_verse_of_day_not_found(sample_empty_response):
    """Test retrieval when no verse is found."""
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day", return_value=sample_empty_response) as mock_service:
        response = client.get("/verse-of-day")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["verse_of_day"] is None
        mock_service.assert_called_once_with(group_id=None, filter_date=None, lang=None)


@pytest.mark.asyncio
async def test_get_verse_of_day_invalid_uuid():
    """Test retrieval with invalid group_id UUID format."""
    response = client.get("/verse-of-day?group_id=invalid-uuid")
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_verse_of_day_invalid_date():
    """Test retrieval with invalid date format."""
    response = client.get("/verse-of-day?date=invalid-date")
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_verse_of_day_database_error():
    """Test handling of database error."""
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day", side_effect=HTTPException(status_code=500, detail="Database connection error")) as mock_service:
        response = client.get("/verse-of-day")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] == "Database connection error"
        mock_service.assert_called_once_with(group_id=None, filter_date=None, lang=None)


# =============================================================================
# GET /verse-of-day/today TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_today_success(sample_verse_public_response):
    """Test successful retrieval of today's verse."""
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day_today_service", return_value=sample_verse_public_response) as mock_service:
        response = client.get("/verse-of-day/today")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "verse_of_day" in data
        assert data["verse_of_day"] is not None
        assert "verses" in data["verse_of_day"]
        assert data["verse_of_day"]["ref_id"] == "text-123"
        
        mock_service.assert_called_once_with(lang=None)


@pytest.mark.asyncio
async def test_get_verse_of_day_today_not_found(sample_empty_response):
    """Test retrieval when no verse exists for today."""
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day_today_service", return_value=sample_empty_response) as mock_service:
        response = client.get("/verse-of-day/today")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["verse_of_day"] is None
        mock_service.assert_called_once_with(lang=None)


@pytest.mark.asyncio
async def test_get_verse_of_day_today_database_error():
    """Test handling of database error for today's verse."""
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day_today_service", side_effect=HTTPException(status_code=500, detail="Database connection error")) as mock_service:
        response = client.get("/verse-of-day/today")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] == "Database connection error"
        mock_service.assert_called_once_with(lang=None)


# =============================================================================
# GET /verse-of-day/{id} TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_success(sample_verse_public_response):
    """Test successful retrieval of verse by ID."""
    verse_id = uuid4()
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day_by_id_service", return_value=sample_verse_public_response) as mock_service:
        response = client.get(f"/verse-of-day/{verse_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "verse_of_day" in data
        assert data["verse_of_day"] is not None
        assert "verses" in data["verse_of_day"]
        
        mock_service.assert_called_once_with(verse_id=verse_id, lang=None)


@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_not_found(sample_empty_response):
    """Test retrieval when verse ID doesn't exist."""
    verse_id = uuid4()
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day_by_id_service", return_value=sample_empty_response) as mock_service:
        response = client.get(f"/verse-of-day/{verse_id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["verse_of_day"] is None
        mock_service.assert_called_once_with(verse_id=verse_id, lang=None)


@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_invalid_uuid():
    """Test retrieval with invalid UUID format."""
    response = client.get("/verse-of-day/invalid-uuid")
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_database_error():
    """Test handling of database error when fetching by ID."""
    verse_id = uuid4()
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day_by_id_service", side_effect=HTTPException(status_code=500, detail="Database connection error")) as mock_service:
        response = client.get(f"/verse-of-day/{verse_id}")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] == "Database connection error"
        mock_service.assert_called_once_with(verse_id=verse_id, lang=None)


# =============================================================================
# POST /verse-of-day TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_create_verse_of_day_success(sample_verse_dto):
    """Test successful creation of verse of day with authentication."""
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    
    with patch("pecha_api.verse_of_day.verse_of_day_views.validate_and_extract_user_details", return_value=mock_user) as mock_validate, \
         patch("pecha_api.verse_of_day.verse_of_day_views.create_verse_of_day_service", return_value=sample_verse_dto) as mock_create:
        
        request_data = {
            "verses": {
                "en": "May all beings be happy and free from suffering.",
                "bo": ["སེམས་ཅན་ཐམས་ཅད་བདེ་བ་དང་།", "སྡུག་བསྔལ་བྲལ་བར་གྱུར་ཅིག"],
                "zh": "愿一切众生快乐，远离痛苦。"
            },
            "image_urls": ["https://example.com/image1.jpg"],
            "verse_id": "verse-456",
            "ref_id": "text-123",
            "ref_type": "sutra",
            "group_id": str(uuid4()),
            "date": "2025-06-05"
        }
        
        response = client.post(
            "/verse-of-day",
            json=request_data,
            headers={"Authorization": "Bearer valid-token"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert "id" in data
        assert "verses" in data
        assert data["verse_id"] == sample_verse_dto.verse_id
        assert data["ref_id"] == sample_verse_dto.ref_id
        assert data["ref_type"] == sample_verse_dto.ref_type
        
        mock_validate.assert_called_once_with("valid-token")
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_create_verse_of_day_with_optional_fields(sample_verse_dto):
    """Test creation with optional fields (image_urls and group_id)."""
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    
    with patch("pecha_api.verse_of_day.verse_of_day_views.validate_and_extract_user_details", return_value=mock_user) as mock_validate, \
         patch("pecha_api.verse_of_day.verse_of_day_views.create_verse_of_day_service", return_value=sample_verse_dto) as mock_create:
        
        request_data = {
            "verses": {"en": "May all beings be happy."},
            "verse_id": "verse-789",
            "ref_id": "text-456",
            "ref_type": "tantra",
            "date": "2025-06-06"
        }
        
        response = client.post(
            "/verse-of-day",
            json=request_data,
            headers={"Authorization": "Bearer valid-token"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        mock_validate.assert_called_once_with("valid-token")
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_create_verse_of_day_missing_required_fields():
    """Test creation with missing required fields."""
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    
    with patch("pecha_api.verse_of_day.verse_of_day_views.validate_and_extract_user_details", return_value=mock_user):
        request_data = {
            "verses": {"en": "May all beings be happy."}
        }
        
        response = client.post(
            "/verse-of-day",
            json=request_data,
            headers={"Authorization": "Bearer valid-token"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_verse_of_day_invalid_token():
    """Test creation with invalid authentication token."""
    with patch("pecha_api.verse_of_day.verse_of_day_views.validate_and_extract_user_details", side_effect=HTTPException(status_code=401, detail="Invalid token")) as mock_validate:
        
        request_data = {
            "verses": {"en": "May all beings be happy."},
            "verse_id": "verse-789",
            "ref_id": "text-456",
            "ref_type": "tantra",
            "date": "2025-06-06"
        }
        
        response = client.post(
            "/verse-of-day",
            json=request_data,
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid token"
        mock_validate.assert_called_once_with("invalid-token")


@pytest.mark.asyncio
async def test_create_verse_of_day_missing_auth():
    """Test creation without authentication header."""
    request_data = {
        "verses": {"en": "May all beings be happy."},
        "verse_id": "verse-789",
        "ref_id": "text-456",
        "ref_type": "tantra",
        "date": "2025-06-06"
    }
    
    response = client.post(
        "/verse-of-day",
        json=request_data
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_create_verse_of_day_database_error():
    """Test handling of database error during creation."""
    mock_user = MagicMock()
    mock_user.email = "test@example.com"
    
    with patch("pecha_api.verse_of_day.verse_of_day_views.validate_and_extract_user_details", return_value=mock_user) as mock_validate, \
         patch("pecha_api.verse_of_day.verse_of_day_views.create_verse_of_day_service", side_effect=HTTPException(status_code=500, detail="Database error")) as mock_create:
        
        request_data = {
            "verses": {"en": "May all beings be happy."},
            "verse_id": "verse-789",
            "ref_id": "text-456",
            "ref_type": "tantra",
            "date": "2025-06-06"
        }
        
        response = client.post(
            "/verse-of-day",
            json=request_data,
            headers={"Authorization": "Bearer valid-token"}
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["detail"] == "Database error"
        mock_validate.assert_called_once_with("valid-token")
        mock_create.assert_called_once()


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_with_empty_image_urls():
    """Test verse with empty image_urls array."""
    verse_dto = VerseOfDayPublicDTO(
        id=uuid4(),
        verses={"en": "Simple verse without images."},
        image_urls=[],
        ref_id="text-empty",
        ref_type="commentary",
        date=date(2025, 6, 5)
    )
    response_dto = VerseOfDayPublicResponse(verse_of_day=verse_dto)
    
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day", return_value=response_dto) as mock_service:
        response = client.get("/verse-of-day")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["verse_of_day"]["image_urls"] == []
        mock_service.assert_called_once_with(group_id=None, filter_date=None, lang=None)


@pytest.mark.asyncio
async def test_get_verse_of_day_with_none_image_urls():
    """Test verse with None image_urls."""
    verse_dto = VerseOfDayPublicDTO(
        id=uuid4(),
        verses={"en": "Simple verse without images."},
        image_urls=None,
        ref_id="text-none",
        ref_type="commentary",
        date=date(2025, 6, 5)
    )
    response_dto = VerseOfDayPublicResponse(verse_of_day=verse_dto)
    
    with patch("pecha_api.verse_of_day.verse_of_day_views.get_verse_of_day", return_value=response_dto) as mock_service:
        response = client.get("/verse-of-day")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["verse_of_day"]["image_urls"] is None
        mock_service.assert_called_once_with(group_id=None, filter_date=None, lang=None)
