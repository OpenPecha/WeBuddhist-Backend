import pytest
from uuid import uuid4
from datetime import date
from unittest.mock import patch, MagicMock, Mock

from pecha_api.verse_of_day.verse_of_day_service import (
    get_verse_of_day,
    get_verse_of_day_by_id_service,
    get_verse_of_day_today_service,
    create_verse_of_day_service,
)
from pecha_api.verse_of_day.verse_of_day_response_models import (
    VerseOfDayPublicResponse,
    VerseOfDayPublicDTO,
    VerseOfDayDTO,
    CreateVerseOfDayRequest,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def mock_db_session():
    """Mock database session with context manager support."""
    session = MagicMock()
    session.__enter__ = Mock(return_value=session)
    session.__exit__ = Mock(return_value=None)
    return session


@pytest.fixture
def sample_verse_model():
    """Sample VerseOfDay model mock."""
    verse = MagicMock()
    verse.id = uuid4()
    verse.verse = "May all beings be happy and free from suffering."
    verse.verse_id = "verse-456"
    verse.ref_id = "text-123"
    verse.ref_type = "sutra"
    verse.image_urls = ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
    verse.group_id = uuid4()
    verse.date = date(2025, 6, 5)
    verse.created_by = "test@example.com"
    return verse


@pytest.fixture
def sample_create_request():
    """Sample create verse request."""
    return CreateVerseOfDayRequest(
        verse="May all beings be happy and free from suffering.",
        image_urls=["https://example.com/image1.jpg"],
        verse_id="verse-456",
        ref_id="text-123",
        ref_type="sutra",
        group_id=uuid4(),
        date=date(2025, 6, 5)
    )


# =============================================================================
# get_verse_of_day() TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_service_success(sample_verse_model, mock_db_session):
    """Test successful retrieval of verse with DTO transformation."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_model) as mock_repo:
        
        result = get_verse_of_day()
        
        assert isinstance(result, VerseOfDayPublicResponse)
        assert result.verse_of_day is not None
        assert isinstance(result.verse_of_day, VerseOfDayPublicDTO)
        assert result.verse_of_day.verse == sample_verse_model.verse
        assert result.verse_of_day.ref_id == sample_verse_model.ref_id
        assert result.verse_of_day.ref_type == sample_verse_model.ref_type
        assert result.verse_of_day.image_urls == sample_verse_model.image_urls
        assert result.verse_of_day.date == sample_verse_model.date
        
        mock_repo.assert_called_once_with(
            mock_db_session.__enter__.return_value,
            group_id=None,
            filter_date=None
        )


@pytest.mark.asyncio
async def test_get_verse_of_day_service_with_group_id(sample_verse_model, mock_db_session):
    """Test retrieval with group_id filter."""
    group_id = uuid4()
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_model) as mock_repo:
        
        result = get_verse_of_day(group_id=group_id)
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.verse == sample_verse_model.verse
        
        mock_repo.assert_called_once_with(
            mock_db_session.__enter__.return_value,
            group_id=group_id,
            filter_date=None
        )


@pytest.mark.asyncio
async def test_get_verse_of_day_service_with_date(sample_verse_model, mock_db_session):
    """Test retrieval with date filter."""
    filter_date = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_model) as mock_repo:
        
        result = get_verse_of_day(filter_date=filter_date)
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.date == sample_verse_model.date
        
        mock_repo.assert_called_once_with(
            mock_db_session.__enter__.return_value,
            group_id=None,
            filter_date=filter_date
        )


@pytest.mark.asyncio
async def test_get_verse_of_day_service_with_both_filters(sample_verse_model, mock_db_session):
    """Test retrieval with both group_id and date filters."""
    group_id = uuid4()
    filter_date = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_model) as mock_repo:
        
        result = get_verse_of_day(group_id=group_id, filter_date=filter_date)
        
        assert result.verse_of_day is not None
        
        mock_repo.assert_called_once_with(
            mock_db_session.__enter__.return_value,
            group_id=group_id,
            filter_date=filter_date
        )


@pytest.mark.asyncio
async def test_get_verse_of_day_service_not_found(mock_db_session):
    """Test retrieval when no verse is found."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=None) as mock_repo:
        
        result = get_verse_of_day()
        
        assert isinstance(result, VerseOfDayPublicResponse)
        assert result.verse_of_day is None
        
        mock_repo.assert_called_once()


@pytest.mark.asyncio
async def test_get_verse_of_day_service_database_error(mock_db_session):
    """Test handling of database error."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", side_effect=Exception("Database connection error")):
        
        with pytest.raises(Exception, match="Database connection error"):
            get_verse_of_day()


# =============================================================================
# get_verse_of_day_by_id_service() TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_service_success(sample_verse_model, mock_db_session):
    """Test successful retrieval of verse by ID."""
    verse_id = uuid4()
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_id", return_value=sample_verse_model) as mock_repo:
        
        result = get_verse_of_day_by_id_service(verse_id=verse_id)
        
        assert isinstance(result, VerseOfDayPublicResponse)
        assert result.verse_of_day is not None
        assert result.verse_of_day.verse == sample_verse_model.verse
        assert result.verse_of_day.ref_id == sample_verse_model.ref_id
        assert result.verse_of_day.ref_type == sample_verse_model.ref_type
        
        mock_repo.assert_called_once_with(
            mock_db_session.__enter__.return_value,
            verse_id=verse_id
        )


@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_service_not_found(mock_db_session):
    """Test retrieval when verse ID doesn't exist."""
    verse_id = uuid4()
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_id", return_value=None) as mock_repo:
        
        result = get_verse_of_day_by_id_service(verse_id=verse_id)
        
        assert isinstance(result, VerseOfDayPublicResponse)
        assert result.verse_of_day is None
        
        mock_repo.assert_called_once_with(
            mock_db_session.__enter__.return_value,
            verse_id=verse_id
        )


@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_service_database_error(mock_db_session):
    """Test handling of database error."""
    verse_id = uuid4()
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_id", side_effect=Exception("Database error")):
        
        with pytest.raises(Exception, match="Database error"):
            get_verse_of_day_by_id_service(verse_id=verse_id)


# =============================================================================
# get_verse_of_day_today_service() TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_today_service_success(sample_verse_model, mock_db_session):
    """Test successful retrieval of today's verse."""
    today = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.date") as mock_date, \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_today", return_value=sample_verse_model) as mock_repo:
        
        mock_date.today.return_value = today
        
        result = get_verse_of_day_today_service()
        
        assert isinstance(result, VerseOfDayPublicResponse)
        assert result.verse_of_day is not None
        assert result.verse_of_day.verse == sample_verse_model.verse
        assert result.verse_of_day.ref_id == sample_verse_model.ref_id
        
        mock_date.today.assert_called_once()
        mock_repo.assert_called_once_with(
            mock_db_session.__enter__.return_value,
            today=today
        )


@pytest.mark.asyncio
async def test_get_verse_of_day_today_service_not_found(mock_db_session):
    """Test retrieval when no verse exists for today."""
    today = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.date") as mock_date, \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_today", return_value=None) as mock_repo:
        
        mock_date.today.return_value = today
        
        result = get_verse_of_day_today_service()
        
        assert isinstance(result, VerseOfDayPublicResponse)
        assert result.verse_of_day is None
        
        mock_repo.assert_called_once()


@pytest.mark.asyncio
async def test_get_verse_of_day_today_service_database_error(mock_db_session):
    """Test handling of database error."""
    today = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.date") as mock_date, \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_today", side_effect=Exception("Database error")):
        
        mock_date.today.return_value = today
        
        with pytest.raises(Exception, match="Database error"):
            get_verse_of_day_today_service()


# =============================================================================
# create_verse_of_day_service() TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_create_verse_of_day_service_success(sample_verse_model, sample_create_request, mock_db_session):
    """Test successful creation of verse of day."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.create_verse_of_day", return_value=sample_verse_model) as mock_repo:
        
        result = create_verse_of_day_service(
            request=sample_create_request,
            created_by="test@example.com"
        )
        
        assert isinstance(result, VerseOfDayDTO)
        assert result.id == sample_verse_model.id
        assert result.verse == sample_verse_model.verse
        assert result.verse_id == sample_verse_model.verse_id
        assert result.ref_id == sample_verse_model.ref_id
        assert result.ref_type == sample_verse_model.ref_type
        assert result.image_urls == sample_verse_model.image_urls
        assert result.group_id == sample_verse_model.group_id
        assert result.date == sample_verse_model.date
        
        mock_repo.assert_called_once()


@pytest.mark.asyncio
async def test_create_verse_of_day_service_with_optional_fields(mock_db_session):
    """Test creation with optional fields (image_urls and group_id)."""
    request = CreateVerseOfDayRequest(
        verse="Simple verse without extras.",
        verse_id="verse-simple",
        ref_id="text-simple",
        ref_type="commentary",
        date=date(2025, 6, 6)
    )
    
    created_verse = MagicMock()
    created_verse.id = uuid4()
    created_verse.verse = request.verse
    created_verse.verse_id = request.verse_id
    created_verse.ref_id = request.ref_id
    created_verse.ref_type = request.ref_type
    created_verse.image_urls = None
    created_verse.group_id = None
    created_verse.date = request.date
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.create_verse_of_day", return_value=created_verse) as mock_repo:
        
        result = create_verse_of_day_service(
            request=request,
            created_by="test@example.com"
        )
        
        assert isinstance(result, VerseOfDayDTO)
        assert result.verse == request.verse
        assert result.image_urls is None
        assert result.group_id is None
        
        mock_repo.assert_called_once()


@pytest.mark.asyncio
async def test_create_verse_of_day_service_database_error(sample_create_request, mock_db_session):
    """Test handling of database error during creation."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.create_verse_of_day", side_effect=Exception("Database error")):
        
        with pytest.raises(Exception, match="Database error"):
            create_verse_of_day_service(
                request=sample_create_request,
                created_by="test@example.com"
            )


@pytest.mark.asyncio
async def test_create_verse_of_day_service_model_creation(sample_create_request, mock_db_session):
    """Test that VerseOfDay model is created with correct fields."""
    created_verse = MagicMock()
    created_verse.id = uuid4()
    created_verse.verse = sample_create_request.verse
    created_verse.verse_id = sample_create_request.verse_id
    created_verse.ref_id = sample_create_request.ref_id
    created_verse.ref_type = sample_create_request.ref_type
    created_verse.image_urls = sample_create_request.image_urls
    created_verse.group_id = sample_create_request.group_id
    created_verse.date = sample_create_request.date
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.VerseOfDay") as mock_model, \
         patch("pecha_api.verse_of_day.verse_of_day_service.create_verse_of_day", return_value=created_verse) as mock_repo:
        
        result = create_verse_of_day_service(
            request=sample_create_request,
            created_by="test@example.com"
        )
        
        mock_model.assert_called_once_with(
            verse=sample_create_request.verse,
            verse_id=sample_create_request.verse_id,
            ref_id=sample_create_request.ref_id,
            ref_type=sample_create_request.ref_type,
            image_urls=sample_create_request.image_urls,
            group_id=sample_create_request.group_id,
            date=sample_create_request.date,
            created_by="test@example.com"
        )
        
        assert result.verse == sample_create_request.verse


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_service_empty_image_urls(mock_db_session):
    """Test verse with empty image_urls array."""
    verse = MagicMock()
    verse.verse = "Simple verse."
    verse.ref_id = "text-empty"
    verse.ref_type = "commentary"
    verse.image_urls = []
    verse.date = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=verse):
        
        result = get_verse_of_day()
        
        assert result.verse_of_day.image_urls == []


@pytest.mark.asyncio
async def test_get_verse_of_day_service_none_image_urls(mock_db_session):
    """Test verse with None image_urls."""
    verse = MagicMock()
    verse.verse = "Simple verse."
    verse.ref_id = "text-none"
    verse.ref_type = "commentary"
    verse.image_urls = None
    verse.date = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=verse):
        
        result = get_verse_of_day()
        
        assert result.verse_of_day.image_urls is None
