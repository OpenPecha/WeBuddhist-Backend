import pytest
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, Mock

from fastapi import HTTPException

from pecha_api.poems.enums import PoemStatus
from pecha_api.poems.cms_service import (
    cms_list_poems_service,
    cms_get_poem_detail_service,
    cms_create_poem_service,
    cms_update_poem_service,
    cms_delete_poem_service,
)
from pecha_api.poems.response_models import (
    PoemDTO,
    PoemsResponse,
    CreatePoemRequest,
    UpdatePoemRequest,
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
def mock_author():
    """Mock CMS author."""
    author = MagicMock()
    author.email = "cms_author@example.com"
    author.id = uuid4()
    return author


@pytest.fixture
def sample_poem_model():
    """Sample Poem model mock."""
    poem = MagicMock()
    poem.id = uuid4()
    poem.title = "The Jewel Ornament of Liberation"
    poem.content = "# Chapter 1\n\nAll beings have Buddha nature..."
    poem.author_name = "Gampopa"
    poem.chapter_name = "Buddha Nature"
    poem.image_key = "images/poem_images/uuid1/cover.jpg"
    poem.status = PoemStatus.PUBLISHED
    poem.published_at = datetime(2025, 6, 5, 12, 0, 0, tzinfo=timezone.utc)
    poem.created_at = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    poem.updated_at = datetime(2025, 6, 5, 12, 0, 0, tzinfo=timezone.utc)
    poem.deleted_at = None
    poem.created_by = "admin@example.com"
    poem.updated_by = None
    return poem


@pytest.fixture
def sample_draft_poem():
    """Sample draft Poem model."""
    poem = MagicMock()
    poem.id = uuid4()
    poem.title = "Draft Poem"
    poem.content = "This is a draft."
    poem.author_name = "Author"
    poem.chapter_name = None
    poem.image_key = None
    poem.status = PoemStatus.DRAFT
    poem.published_at = None
    poem.created_at = datetime(2025, 6, 7, 10, 0, 0, tzinfo=timezone.utc)
    poem.updated_at = datetime(2025, 6, 7, 10, 0, 0, tzinfo=timezone.utc)
    poem.deleted_at = None
    poem.created_by = "admin@example.com"
    poem.updated_by = None
    return poem


@pytest.fixture
def sample_create_request():
    """Sample create poem request."""
    return CreatePoemRequest(
        title="New Poem",
        content="This is the content of the new poem.",
        author_name="Test Author",
        chapter_name="Chapter 1",
        image_key="images/poem_images/new/cover.jpg",
        status=PoemStatus.DRAFT,
    )


@pytest.fixture
def sample_update_request():
    """Sample update poem request."""
    return UpdatePoemRequest(
        title="Updated Title",
        content="Updated content.",
        status=PoemStatus.PUBLISHED,
    )


# =============================================================================
# cms_list_poems_service() TESTS
# =============================================================================

def test_cms_list_poems_service_success(sample_poem_model, mock_db_session, mock_author):
    """Test successful CMS listing of poems."""
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.get_poems_list", return_value=([sample_poem_model], 1)), \
         patch("pecha_api.poems.cms_service._build_poem_dto") as mock_build:
        
        mock_build.return_value = PoemDTO(
            id=sample_poem_model.id,
            title=sample_poem_model.title,
            content=sample_poem_model.content,
            author_name=sample_poem_model.author_name,
            chapter_name=sample_poem_model.chapter_name,
            language="EN",
            image_url="https://presigned.url",
            status="PUBLISHED",
            published_at="2025-06-05T12:00:00+00:00",
            created_at="2025-06-01T10:00:00+00:00",
            updated_at="2025-06-05T12:00:00+00:00",
        )

        result = cms_list_poems_service(token="valid_token", skip=0, limit=20)
        
        assert isinstance(result, PoemsResponse)
        assert len(result.poems) == 1
        assert result.total == 1


def test_cms_list_poems_service_with_status_filter(sample_draft_poem, mock_db_session, mock_author):
    """Test CMS listing with status filter."""
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.get_poems_list", return_value=([sample_draft_poem], 1)) as mock_repo, \
         patch("pecha_api.poems.cms_service._build_poem_dto") as mock_build:
        
        mock_build.return_value = PoemDTO(
            id=sample_draft_poem.id,
            title=sample_draft_poem.title,
            content=sample_draft_poem.content,
            author_name=sample_draft_poem.author_name,
            chapter_name=None,
            language="EN",
            image_url=None,
            status="DRAFT",
            published_at=None,
            created_at="2025-06-07T10:00:00+00:00",
            updated_at="2025-06-07T10:00:00+00:00",
        )

        result = cms_list_poems_service(
            token="valid_token",
            skip=0,
            limit=20,
            status_filter=PoemStatus.DRAFT,
        )
        
        assert len(result.poems) == 1
        mock_repo.assert_called_once()
        call_kwargs = mock_repo.call_args[1]
        assert call_kwargs["status"] == PoemStatus.DRAFT


def test_cms_list_poems_service_invalid_token(mock_db_session):
    """Test CMS listing with invalid token."""
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", side_effect=HTTPException(status_code=401, detail="Invalid token")):
        
        with pytest.raises(HTTPException) as exc_info:
            cms_list_poems_service(token="invalid_token")
        
        assert exc_info.value.status_code == 401


# =============================================================================
# cms_get_poem_detail_service() TESTS
# =============================================================================

def test_cms_get_poem_detail_service_success(sample_poem_model, mock_db_session, mock_author):
    """Test successful CMS retrieval of poem by ID."""
    poem_id = sample_poem_model.id
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.get_poem_by_id", return_value=sample_poem_model), \
         patch("pecha_api.poems.cms_service._build_poem_dto") as mock_build:
        
        mock_build.return_value = PoemDTO(
            id=poem_id,
            title=sample_poem_model.title,
            content=sample_poem_model.content,
            author_name=sample_poem_model.author_name,
            chapter_name=sample_poem_model.chapter_name,
            language="EN",
            image_url="https://presigned.url",
            status="PUBLISHED",
            published_at="2025-06-05T12:00:00+00:00",
            created_at="2025-06-01T10:00:00+00:00",
            updated_at="2025-06-05T12:00:00+00:00",
        )

        result = cms_get_poem_detail_service(token="valid_token", poem_id=poem_id)

        assert isinstance(result, PoemDTO)
        assert result.id == poem_id


def test_cms_get_poem_detail_service_draft(sample_draft_poem, mock_db_session, mock_author):
    """Test CMS can retrieve draft poems."""
    poem_id = sample_draft_poem.id
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.get_poem_by_id", return_value=sample_draft_poem), \
         patch("pecha_api.poems.cms_service._build_poem_dto") as mock_build:
        
        mock_build.return_value = PoemDTO(
            id=poem_id,
            title=sample_draft_poem.title,
            content=sample_draft_poem.content,
            author_name=sample_draft_poem.author_name,
            chapter_name=None,
            language="EN",
            image_url=None,
            status="DRAFT",
            published_at=None,
            created_at="2025-06-07T10:00:00+00:00",
            updated_at="2025-06-07T10:00:00+00:00",
        )

        result = cms_get_poem_detail_service(token="valid_token", poem_id=poem_id)

        assert result.status == "DRAFT"


def test_cms_get_poem_detail_service_not_found(mock_db_session, mock_author):
    """Test CMS retrieval when poem doesn't exist."""
    poem_id = uuid4()
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.get_poem_by_id", return_value=None):
        
        with pytest.raises(HTTPException) as exc_info:
            cms_get_poem_detail_service(token="valid_token", poem_id=poem_id)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Poem not found"


# =============================================================================
# cms_create_poem_service() TESTS
# =============================================================================

def test_cms_create_poem_service_draft(sample_create_request, mock_db_session, mock_author):
    """Test creating a draft poem."""
    created_poem = MagicMock()
    created_poem.id = uuid4()
    created_poem.title = sample_create_request.title
    created_poem.content = sample_create_request.content
    created_poem.author_name = sample_create_request.author_name
    created_poem.chapter_name = sample_create_request.chapter_name
    created_poem.image_key = sample_create_request.image_key
    created_poem.status = PoemStatus.DRAFT
    created_poem.published_at = None
    created_poem.created_at = datetime.now(timezone.utc)
    created_poem.updated_at = datetime.now(timezone.utc)
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.Poem", return_value=created_poem), \
         patch("pecha_api.poems.cms_service.create_poem", return_value=created_poem), \
         patch("pecha_api.poems.cms_service._build_poem_dto") as mock_build:
        
        mock_build.return_value = PoemDTO(
            id=created_poem.id,
            title=created_poem.title,
            content=created_poem.content,
            author_name=created_poem.author_name,
            chapter_name=created_poem.chapter_name,
            language="EN",
            image_url="https://presigned.url",
            status="DRAFT",
            published_at=None,
            created_at=created_poem.created_at.isoformat(),
            updated_at=created_poem.updated_at.isoformat(),
        )
        
        result = cms_create_poem_service(token="valid_token", request=sample_create_request)
        
        assert isinstance(result, PoemDTO)
        assert result.status == "DRAFT"
        assert result.published_at is None


def test_cms_create_poem_service_published(mock_db_session, mock_author):
    """Test creating a published poem sets published_at."""
    request = CreatePoemRequest(
        title="Published Poem",
        content="Content here.",
        author_name="Author",
        status=PoemStatus.PUBLISHED,
    )
    
    created_poem = MagicMock()
    created_poem.id = uuid4()
    created_poem.title = request.title
    created_poem.content = request.content
    created_poem.author_name = request.author_name
    created_poem.chapter_name = None
    created_poem.image_key = None
    created_poem.status = PoemStatus.PUBLISHED
    created_poem.published_at = datetime.now(timezone.utc)
    created_poem.created_at = datetime.now(timezone.utc)
    created_poem.updated_at = datetime.now(timezone.utc)
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.Poem", return_value=created_poem), \
         patch("pecha_api.poems.cms_service.create_poem", return_value=created_poem) as mock_create, \
         patch("pecha_api.poems.cms_service._build_poem_dto") as mock_build:
        
        mock_build.return_value = PoemDTO(
            id=created_poem.id,
            title=created_poem.title,
            content=created_poem.content,
            author_name=created_poem.author_name,
            chapter_name=None,
            language="EN",
            image_url=None,
            status="PUBLISHED",
            published_at=created_poem.published_at.isoformat(),
            created_at=created_poem.created_at.isoformat(),
            updated_at=created_poem.updated_at.isoformat(),
        )
        
        result = cms_create_poem_service(token="valid_token", request=request)
        
        assert result.status == "PUBLISHED"
        assert result.published_at is not None


def test_cms_create_poem_service_invalid_token():
    """Test creating poem with invalid token."""
    request = CreatePoemRequest(
        title="Test",
        content="Content",
        author_name="Author",
    )
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", side_effect=HTTPException(status_code=401, detail="Invalid token")):
        
        with pytest.raises(HTTPException) as exc_info:
            cms_create_poem_service(token="invalid_token", request=request)
        
        assert exc_info.value.status_code == 401


# =============================================================================
# cms_update_poem_service() TESTS
# =============================================================================

def test_cms_update_poem_service_success(sample_poem_model, sample_update_request, mock_db_session, mock_author):
    """Test successful poem update."""
    poem_id = sample_poem_model.id
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.get_poem_by_id", return_value=sample_poem_model), \
         patch("pecha_api.poems.cms_service.update_poem", return_value=sample_poem_model), \
         patch("pecha_api.poems.cms_service._build_poem_dto") as mock_build:
        
        mock_build.return_value = PoemDTO(
            id=poem_id,
            title=sample_update_request.title,
            content=sample_update_request.content,
            author_name=sample_poem_model.author_name,
            chapter_name=sample_poem_model.chapter_name,
            language="EN",
            image_url="https://presigned.url",
            status="PUBLISHED",
            published_at="2025-06-05T12:00:00+00:00",
            created_at="2025-06-01T10:00:00+00:00",
            updated_at="2025-06-08T10:00:00+00:00",
        )
        
        result = cms_update_poem_service(
            token="valid_token",
            poem_id=poem_id,
            request=sample_update_request,
        )
        
        assert isinstance(result, PoemDTO)
        assert result.title == sample_update_request.title


def test_cms_update_poem_service_publish_sets_published_at(sample_draft_poem, mock_db_session, mock_author):
    """Test that publishing a draft sets published_at."""
    poem_id = sample_draft_poem.id
    request = UpdatePoemRequest(status=PoemStatus.PUBLISHED)
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.get_poem_by_id", return_value=sample_draft_poem), \
         patch("pecha_api.poems.cms_service.update_poem", return_value=sample_draft_poem) as mock_update, \
         patch("pecha_api.poems.cms_service._build_poem_dto") as mock_build:
        
        mock_build.return_value = PoemDTO(
            id=poem_id,
            title=sample_draft_poem.title,
            content=sample_draft_poem.content,
            author_name=sample_draft_poem.author_name,
            chapter_name=None,
            language="EN",
            image_url=None,
            status="PUBLISHED",
            published_at=datetime.now(timezone.utc).isoformat(),
            created_at="2025-06-07T10:00:00+00:00",
            updated_at="2025-06-08T10:00:00+00:00",
        )
        
        result = cms_update_poem_service(
            token="valid_token",
            poem_id=poem_id,
            request=request,
        )
        
        assert sample_draft_poem.published_at is not None


def test_cms_update_poem_service_not_found(mock_db_session, mock_author):
    """Test updating non-existent poem."""
    poem_id = uuid4()
    request = UpdatePoemRequest(title="Updated")
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.get_poem_by_id", return_value=None):
        
        with pytest.raises(HTTPException) as exc_info:
            cms_update_poem_service(token="valid_token", poem_id=poem_id, request=request)
        
        assert exc_info.value.status_code == 404


# =============================================================================
# cms_delete_poem_service() TESTS
# =============================================================================

def test_cms_delete_poem_service_success(sample_poem_model, mock_db_session, mock_author):
    """Test successful soft delete."""
    poem_id = sample_poem_model.id
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.get_poem_by_id", return_value=sample_poem_model), \
         patch("pecha_api.poems.cms_service.soft_delete_poem") as mock_delete:
        
        cms_delete_poem_service(token="valid_token", poem_id=poem_id)
        
        mock_delete.assert_called_once_with(
            db=mock_db_session.__enter__.return_value,
            poem=sample_poem_model,
            deleted_by=mock_author.email,
        )


def test_cms_delete_poem_service_not_found(mock_db_session, mock_author):
    """Test deleting non-existent poem."""
    poem_id = uuid4()
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", return_value=mock_author), \
         patch("pecha_api.poems.cms_service.SessionLocal", return_value=mock_db_session), \
         patch("pecha_api.poems.cms_service.get_poem_by_id", return_value=None):
        
        with pytest.raises(HTTPException) as exc_info:
            cms_delete_poem_service(token="valid_token", poem_id=poem_id)
        
        assert exc_info.value.status_code == 404


def test_cms_delete_poem_service_invalid_token():
    """Test deleting with invalid token."""
    poem_id = uuid4()
    
    with patch("pecha_api.poems.cms_service.validate_cms_author_details", side_effect=HTTPException(status_code=401, detail="Invalid token")):
        
        with pytest.raises(HTTPException) as exc_info:
            cms_delete_poem_service(token="invalid_token", poem_id=poem_id)
        
        assert exc_info.value.status_code == 401
