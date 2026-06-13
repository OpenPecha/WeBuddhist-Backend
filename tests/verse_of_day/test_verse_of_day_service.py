import pytest
from uuid import uuid4
from datetime import date
from unittest.mock import patch, MagicMock, Mock

from pecha_api.verse_of_day.verse_of_day_service import (
    get_verse_of_day,
    get_verse_of_day_by_id_service,
    get_verse_of_day_today_service,
    create_verse_of_day_service,
    build_verses_dict,
    build_public_dto,
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
def sample_verse_metadata():
    """Sample verse metadata mocks for multilingual verses."""
    en_metadata = MagicMock()
    en_metadata.lang = "en"
    en_metadata.verse = "May all beings be happy and free from suffering."
    
    bo_metadata = MagicMock()
    bo_metadata.lang = "bo"
    bo_metadata.verse = ["སེམས་ཅན་ཐམས་ཅད་བདེ་བ་དང་།", "སྡུག་བསྔལ་བྲལ་བར་གྱུར་ཅིག"]
    
    zh_metadata = MagicMock()
    zh_metadata.lang = "zh"
    zh_metadata.verse = "愿一切众生快乐，远离痛苦。"
    
    return [en_metadata, bo_metadata, zh_metadata]


@pytest.fixture
def sample_verse_model(sample_verse_metadata):
    """Sample VerseOfDay model mock with verse_metadata relationship."""
    verse = MagicMock()
    verse.id = uuid4()
    verse.verse_id = "verse-456"
    verse.ref_id = "text-123"
    verse.ref_type = "sutra"
    verse.image_urls = ["https://example.com/image1.jpg", "https://example.com/image2.jpg"]
    verse.group_id = uuid4()
    verse.date = date(2025, 6, 5)
    verse.created_by = "test@example.com"
    verse.verse_metadata = sample_verse_metadata
    return verse


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


@pytest.fixture
def sample_group_metadata():
    """Sample AuthorGroupMetadata objects for multiple languages."""
    en_metadata = MagicMock()
    en_metadata.id = uuid4()
    en_metadata.group_id = uuid4()
    en_metadata.language = "EN"
    en_metadata.title = "English Title"
    en_metadata.sub_title = "English Subtitle"
    en_metadata.description = "English description"
    
    bo_metadata = MagicMock()
    bo_metadata.id = uuid4()
    bo_metadata.group_id = en_metadata.group_id
    bo_metadata.language = "BO"
    bo_metadata.title = "བོད་ཡིག་མིང་།"
    bo_metadata.sub_title = "བོད་ཡིག་ཡན་ལག་མིང་།"
    bo_metadata.description = "བོད་ཡིག་གསལ་བཤད།"
    
    zh_metadata = MagicMock()
    zh_metadata.id = uuid4()
    zh_metadata.group_id = en_metadata.group_id
    zh_metadata.language = "zh"
    zh_metadata.title = "中文标题"
    zh_metadata.sub_title = "中文副标题"
    zh_metadata.description = "中文描述"
    
    return [en_metadata, bo_metadata, zh_metadata]


@pytest.fixture
def sample_verse_with_group_id(sample_verse_metadata):
    """Sample VerseOfDay model with group_id set."""
    verse = MagicMock()
    verse.id = uuid4()
    verse.verse_id = "verse-456"
    verse.ref_id = "text-123"
    verse.ref_type = "sutra"
    verse.image_urls = ["https://example.com/image1.jpg"]
    verse.group_id = uuid4()
    verse.date = date(2025, 6, 5)
    verse.verse_metadata = sample_verse_metadata
    return verse


@pytest.fixture
def sample_verse_without_group_id(sample_verse_metadata):
    """Sample VerseOfDay model without group_id."""
    verse = MagicMock()
    verse.id = uuid4()
    verse.verse_id = "verse-789"
    verse.ref_id = "text-456"
    verse.ref_type = "commentary"
    verse.image_urls = None
    verse.group_id = None
    verse.date = date(2025, 6, 6)
    verse.verse_metadata = sample_verse_metadata
    return verse


# =============================================================================
# get_verse_of_day() TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_service_success(sample_verse_model, mock_db_session):
    """Test successful retrieval of verse with all languages."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_model) as mock_repo:
        
        result = get_verse_of_day()
        
        assert isinstance(result, VerseOfDayPublicResponse)
        assert result.verse_of_day is not None
        assert isinstance(result.verse_of_day, VerseOfDayPublicDTO)
        assert result.verse_of_day.verses is not None
        assert "en" in result.verse_of_day.verses
        assert "bo" in result.verse_of_day.verses
        assert "zh" in result.verse_of_day.verses
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
async def test_get_verse_of_day_service_with_lang_filter(sample_verse_model, mock_db_session):
    """Test retrieval with language filter returns single verse."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_model):
        
        result = get_verse_of_day(lang="en")
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.verse == "May all beings be happy and free from suffering."
        assert result.verse_of_day.verses is None


@pytest.mark.asyncio
async def test_get_verse_of_day_service_with_lang_filter_array(sample_verse_model, mock_db_session):
    """Test retrieval with language filter for array verse."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_model):
        
        result = get_verse_of_day(lang="bo")
        
        assert result.verse_of_day is not None
        assert isinstance(result.verse_of_day.verse, list)
        assert len(result.verse_of_day.verse) == 2
        assert result.verse_of_day.verses is None


@pytest.mark.asyncio
async def test_get_verse_of_day_service_with_group_id(sample_verse_model, mock_db_session):
    """Test retrieval with group_id filter."""
    group_id = uuid4()
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_model) as mock_repo:
        
        result = get_verse_of_day(group_id=group_id)
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.verses is not None
        
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


@pytest.mark.asyncio
async def test_get_verse_of_day_with_group_info_all_languages(sample_verse_with_group_id, sample_group_metadata, mock_db_session):
    """Test returns all group_info when no lang filter."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_with_group_id), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_group_metadata_by_group_id", return_value=sample_group_metadata):
        
        result = get_verse_of_day()
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.group_info is not None
        assert len(result.verse_of_day.group_info) == 3
        languages = [info.language for info in result.verse_of_day.group_info]
        assert "EN" in languages
        assert "BO" in languages
        assert "zh" in languages


@pytest.mark.asyncio
async def test_get_verse_of_day_with_group_info_filtered_by_lang(sample_verse_with_group_id, sample_group_metadata, mock_db_session):
    """Test returns only ZH group_info when lang=zh."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_with_group_id), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_group_metadata_by_group_id", return_value=sample_group_metadata):
        
        result = get_verse_of_day(lang="zh")
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.group_info is not None
        assert len(result.verse_of_day.group_info) == 1
        assert result.verse_of_day.group_info[0].language == "zh"
        assert result.verse_of_day.group_info[0].title == "中文标题"


@pytest.mark.asyncio
async def test_get_verse_of_day_with_group_info_case_insensitive(sample_verse_with_group_id, sample_group_metadata, mock_db_session):
    """Test language filter works with different cases (zh, ZH, Zh)."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_with_group_id), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_group_metadata_by_group_id", return_value=sample_group_metadata):
        
        result = get_verse_of_day(lang="ZH")
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.group_info is not None
        assert len(result.verse_of_day.group_info) == 1
        assert result.verse_of_day.group_info[0].language == "zh"


@pytest.mark.asyncio
async def test_get_verse_of_day_without_group_id(sample_verse_without_group_id, mock_db_session):
    """Test returns None group_info when verse has no group_id."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_without_group_id):
        
        result = get_verse_of_day()
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.group_info is None


@pytest.mark.asyncio
async def test_get_verse_of_day_with_empty_group_metadata(sample_verse_with_group_id, mock_db_session):
    """Test returns None group_info when group has no metadata."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=sample_verse_with_group_id), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_group_metadata_by_group_id", return_value=[]):
        
        result = get_verse_of_day()
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.group_info is None


# =============================================================================
# get_verse_of_day_by_id_service() TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_service_success(sample_verse_model, mock_db_session):
    """Test successful retrieval of verse by ID with all languages."""
    verse_id = uuid4()
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_id", return_value=sample_verse_model) as mock_repo:
        
        result = get_verse_of_day_by_id_service(verse_id=verse_id)
        
        assert isinstance(result, VerseOfDayPublicResponse)
        assert result.verse_of_day is not None
        assert result.verse_of_day.verses is not None
        assert "en" in result.verse_of_day.verses
        assert result.verse_of_day.ref_id == sample_verse_model.ref_id
        assert result.verse_of_day.ref_type == sample_verse_model.ref_type
        
        mock_repo.assert_called_once_with(
            mock_db_session.__enter__.return_value,
            verse_id=verse_id
        )


@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_service_with_lang(sample_verse_model, mock_db_session):
    """Test retrieval by ID with language filter."""
    verse_id = uuid4()
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_id", return_value=sample_verse_model):
        
        result = get_verse_of_day_by_id_service(verse_id=verse_id, lang="zh")
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.verse == "愿一切众生快乐，远离痛苦。"
        assert result.verse_of_day.verses is None


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


@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_with_group_info_all_languages(sample_verse_with_group_id, sample_group_metadata, mock_db_session):
    """Test returns all group_info."""
    verse_id = uuid4()
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_id", return_value=sample_verse_with_group_id), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_group_metadata_by_group_id", return_value=sample_group_metadata):
        
        result = get_verse_of_day_by_id_service(verse_id=verse_id)
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.group_info is not None
        assert len(result.verse_of_day.group_info) == 3


@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_with_group_info_filtered(sample_verse_with_group_id, sample_group_metadata, mock_db_session):
    """Test returns filtered group_info by lang."""
    verse_id = uuid4()
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_id", return_value=sample_verse_with_group_id), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_group_metadata_by_group_id", return_value=sample_group_metadata):
        
        result = get_verse_of_day_by_id_service(verse_id=verse_id, lang="EN")
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.group_info is not None
        assert len(result.verse_of_day.group_info) == 1
        assert result.verse_of_day.group_info[0].language == "EN"


@pytest.mark.asyncio
async def test_get_verse_of_day_by_id_without_group_id(sample_verse_without_group_id, mock_db_session):
    """Test returns None group_info."""
    verse_id = uuid4()
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_id", return_value=sample_verse_without_group_id):
        
        result = get_verse_of_day_by_id_service(verse_id=verse_id)
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.group_info is None


# =============================================================================
# get_verse_of_day_today_service() TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_today_service_success(sample_verse_model, mock_db_session):
    """Test successful retrieval of today's verse with all languages."""
    today = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.date") as mock_date, \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_today", return_value=sample_verse_model) as mock_repo:
        
        mock_date.today.return_value = today
        
        result = get_verse_of_day_today_service()
        
        assert isinstance(result, VerseOfDayPublicResponse)
        assert result.verse_of_day is not None
        assert result.verse_of_day.verses is not None
        assert "en" in result.verse_of_day.verses
        assert result.verse_of_day.ref_id == sample_verse_model.ref_id
        
        mock_date.today.assert_called_once()
        mock_repo.assert_called_once_with(
            mock_db_session.__enter__.return_value,
            today=today
        )


@pytest.mark.asyncio
async def test_get_verse_of_day_today_service_with_lang(sample_verse_model, mock_db_session):
    """Test retrieval of today's verse with language filter."""
    today = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.date") as mock_date, \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_today", return_value=sample_verse_model):
        
        mock_date.today.return_value = today
        
        result = get_verse_of_day_today_service(lang="en")
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.verse == "May all beings be happy and free from suffering."
        assert result.verse_of_day.verses is None


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


@pytest.mark.asyncio
async def test_get_verse_of_day_today_with_group_info_all_languages(sample_verse_with_group_id, sample_group_metadata, mock_db_session):
    """Test returns all group_info."""
    today = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.date") as mock_date, \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_today", return_value=sample_verse_with_group_id), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_group_metadata_by_group_id", return_value=sample_group_metadata):
        
        mock_date.today.return_value = today
        
        result = get_verse_of_day_today_service()
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.group_info is not None
        assert len(result.verse_of_day.group_info) == 3


@pytest.mark.asyncio
async def test_get_verse_of_day_today_with_group_info_filtered(sample_verse_with_group_id, sample_group_metadata, mock_db_session):
    """Test returns filtered group_info by lang."""
    today = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.date") as mock_date, \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_today", return_value=sample_verse_with_group_id), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_group_metadata_by_group_id", return_value=sample_group_metadata):
        
        mock_date.today.return_value = today
        
        result = get_verse_of_day_today_service(lang="BO")
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.group_info is not None
        assert len(result.verse_of_day.group_info) == 1
        assert result.verse_of_day.group_info[0].language == "BO"


@pytest.mark.asyncio
async def test_get_verse_of_day_today_without_group_id(sample_verse_without_group_id, mock_db_session):
    """Test returns None group_info."""
    today = date(2025, 6, 5)
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.date") as mock_date, \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_today", return_value=sample_verse_without_group_id):
        
        mock_date.today.return_value = today
        
        result = get_verse_of_day_today_service()
        
        assert result.verse_of_day is not None
        assert result.verse_of_day.group_info is None


# =============================================================================
# create_verse_of_day_service() TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_create_verse_of_day_service_success(sample_verse_model, sample_create_request, mock_db_session):
    """Test successful creation of verse of day with multilingual verses."""
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.create_verse_of_day", return_value=sample_verse_model) as mock_create, \
         patch("pecha_api.verse_of_day.verse_of_day_service.create_verse_metadata_bulk") as mock_metadata:
        
        result = create_verse_of_day_service(
            request=sample_create_request,
            created_by="test@example.com"
        )
        
        assert isinstance(result, VerseOfDayDTO)
        assert result.id == sample_verse_model.id
        assert result.verses == sample_create_request.verses
        assert result.verse_id == sample_verse_model.verse_id
        assert result.ref_id == sample_verse_model.ref_id
        assert result.ref_type == sample_verse_model.ref_type
        assert result.image_urls == sample_verse_model.image_urls
        assert result.group_id == sample_verse_model.group_id
        assert result.date == sample_verse_model.date
        
        mock_create.assert_called_once()
        mock_metadata.assert_called_once_with(
            mock_db_session.__enter__.return_value,
            sample_verse_model.id,
            sample_create_request.verses
        )


@pytest.mark.asyncio
async def test_create_verse_of_day_service_with_optional_fields(mock_db_session):
    """Test creation with optional fields (image_urls and group_id)."""
    request = CreateVerseOfDayRequest(
        verses={"en": "Simple verse without extras."},
        verse_id="verse-simple",
        ref_id="text-simple",
        ref_type="commentary",
        date=date(2025, 6, 6)
    )
    
    created_verse = MagicMock()
    created_verse.id = uuid4()
    created_verse.verse_id = request.verse_id
    created_verse.ref_id = request.ref_id
    created_verse.ref_type = request.ref_type
    created_verse.image_urls = None
    created_verse.group_id = None
    created_verse.date = request.date
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.create_verse_of_day", return_value=created_verse), \
         patch("pecha_api.verse_of_day.verse_of_day_service.create_verse_metadata_bulk"):
        
        result = create_verse_of_day_service(
            request=request,
            created_by="test@example.com"
        )
        
        assert isinstance(result, VerseOfDayDTO)
        assert result.verses == {"en": "Simple verse without extras."}
        assert result.image_urls is None
        assert result.group_id is None


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
    created_verse.verse_id = sample_create_request.verse_id
    created_verse.ref_id = sample_create_request.ref_id
    created_verse.ref_type = sample_create_request.ref_type
    created_verse.image_urls = sample_create_request.image_urls
    created_verse.group_id = sample_create_request.group_id
    created_verse.date = sample_create_request.date
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.VerseOfDay") as mock_model, \
         patch("pecha_api.verse_of_day.verse_of_day_service.create_verse_of_day", return_value=created_verse), \
         patch("pecha_api.verse_of_day.verse_of_day_service.create_verse_metadata_bulk"):
        
        result = create_verse_of_day_service(
            request=sample_create_request,
            created_by="test@example.com"
        )
        
        mock_model.assert_called_once_with(
            verse_id=sample_create_request.verse_id,
            ref_id=sample_create_request.ref_id,
            ref_type=sample_create_request.ref_type,
            image_urls=sample_create_request.image_urls,
            group_id=sample_create_request.group_id,
            date=sample_create_request.date,
            created_by="test@example.com"
        )
        
        assert result.verses == sample_create_request.verses


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_get_verse_of_day_service_empty_image_urls(mock_db_session):
    """Test verse with empty image_urls array."""
    verse = MagicMock()
    verse.id = uuid4()
    verse.ref_id = "text-empty"
    verse.ref_type = "commentary"
    verse.image_urls = []
    verse.date = date(2025, 6, 5)
    verse.verse_metadata = []
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=verse):
        
        result = get_verse_of_day()
        
        assert result.verse_of_day.image_urls == []


@pytest.mark.asyncio
async def test_get_verse_of_day_service_none_image_urls(mock_db_session):
    """Test verse with None image_urls."""
    verse = MagicMock()
    verse.id = uuid4()
    verse.ref_id = "text-none"
    verse.ref_type = "commentary"
    verse.image_urls = None
    verse.date = date(2025, 6, 5)
    verse.verse_metadata = []
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=verse):
        
        result = get_verse_of_day()
        
        assert result.verse_of_day.image_urls is None


@pytest.mark.asyncio
async def test_get_verse_of_day_service_empty_verse_metadata(mock_db_session):
    """Test verse with no verse_metadata entries."""
    verse = MagicMock()
    verse.id = uuid4()
    verse.ref_id = "text-no-metadata"
    verse.ref_type = "commentary"
    verse.image_urls = None
    verse.date = date(2025, 6, 5)
    verse.verse_metadata = []
    
    with patch("pecha_api.verse_of_day.verse_of_day_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.verse_of_day.verse_of_day_service.get_verse_of_day_by_filters", return_value=verse):
        
        result = get_verse_of_day()
        
        assert result.verse_of_day.verses is None


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

def test_build_verses_dict(sample_verse_metadata):
    """Test build_verses_dict helper function."""
    result = build_verses_dict(sample_verse_metadata)
    
    assert "en" in result
    assert "bo" in result
    assert "zh" in result
    assert result["en"] == "May all beings be happy and free from suffering."
    assert isinstance(result["bo"], list)
    assert len(result["bo"]) == 2


def test_build_verses_dict_empty():
    """Test build_verses_dict with empty list."""
    result = build_verses_dict([])
    
    assert result == {}


def test_build_public_dto_all_languages(sample_verse_model):
    """Test build_public_dto returns all languages when no lang filter."""
    result = build_public_dto(sample_verse_model)
    
    assert result.verses is not None
    assert result.verse is None
    assert "en" in result.verses
    assert "bo" in result.verses
    assert "zh" in result.verses


def test_build_public_dto_single_language(sample_verse_model):
    """Test build_public_dto returns single verse when lang filter provided."""
    result = build_public_dto(sample_verse_model, lang="en")
    
    assert result.verse == "May all beings be happy and free from suffering."
    assert result.verses is None


def test_build_public_dto_invalid_language(sample_verse_model):
    """Test build_public_dto returns all languages when invalid lang provided."""
    result = build_public_dto(sample_verse_model, lang="fr")
    
    assert result.verses is not None
    assert result.verse is None
