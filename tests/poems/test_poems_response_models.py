import pytest
from uuid import uuid4

from pydantic import ValidationError

from pecha_api.poems.enums import PoemStatus
from pecha_api.poems.response_models import (
    PoemDTO,
    PoemsResponse,
    CreatePoemRequest,
    UpdatePoemRequest,
)


# =============================================================================
# CreatePoemRequest VALIDATION TESTS
# =============================================================================

def test_create_poem_request_valid():
    """Test valid create request."""
    request = CreatePoemRequest(
        title="Test Poem",
        content="This is the content.",
        author_name="Test Author",
        chapter_name="Chapter 1",
        image_key="images/poem.jpg",
        status=PoemStatus.DRAFT,
    )
    
    assert request.title == "Test Poem"
    assert request.content == "This is the content."
    assert request.author_name == "Test Author"
    assert request.chapter_name == "Chapter 1"
    assert request.status == PoemStatus.DRAFT


def test_create_poem_request_minimal():
    """Test minimal valid create request."""
    request = CreatePoemRequest(
        title="Test",
        content="Content",
        author_name="Author",
    )
    
    assert request.title == "Test"
    assert request.chapter_name is None
    assert request.image_key is None
    assert request.status == PoemStatus.DRAFT


def test_create_poem_request_title_trimmed():
    """Test title is trimmed."""
    request = CreatePoemRequest(
        title="  Trimmed Title  ",
        content="Content",
        author_name="Author",
    )
    
    assert request.title == "Trimmed Title"


def test_create_poem_request_content_trimmed():
    """Test content is trimmed."""
    request = CreatePoemRequest(
        title="Title",
        content="  Trimmed Content  ",
        author_name="Author",
    )
    
    assert request.content == "Trimmed Content"


def test_create_poem_request_author_name_trimmed():
    """Test author_name is trimmed."""
    request = CreatePoemRequest(
        title="Title",
        content="Content",
        author_name="  Trimmed Author  ",
    )
    
    assert request.author_name == "Trimmed Author"


def test_create_poem_request_empty_title_fails():
    """Test empty title validation."""
    with pytest.raises(ValidationError) as exc_info:
        CreatePoemRequest(
            title="",
            content="Content",
            author_name="Author",
        )
    
    assert "title must not be empty" in str(exc_info.value)


def test_create_poem_request_whitespace_title_fails():
    """Test whitespace-only title validation."""
    with pytest.raises(ValidationError) as exc_info:
        CreatePoemRequest(
            title="   ",
            content="Content",
            author_name="Author",
        )
    
    assert "title must not be empty" in str(exc_info.value)


def test_create_poem_request_empty_content_fails():
    """Test empty content validation."""
    with pytest.raises(ValidationError) as exc_info:
        CreatePoemRequest(
            title="Title",
            content="",
            author_name="Author",
        )
    
    assert "content must not be empty" in str(exc_info.value)


def test_create_poem_request_whitespace_content_fails():
    """Test whitespace-only content validation."""
    with pytest.raises(ValidationError) as exc_info:
        CreatePoemRequest(
            title="Title",
            content="   ",
            author_name="Author",
        )
    
    assert "content must not be empty" in str(exc_info.value)


def test_create_poem_request_empty_author_name_fails():
    """Test empty author_name validation."""
    with pytest.raises(ValidationError) as exc_info:
        CreatePoemRequest(
            title="Title",
            content="Content",
            author_name="",
        )
    
    assert "author_name must not be empty" in str(exc_info.value)


def test_create_poem_request_whitespace_author_name_fails():
    """Test whitespace-only author_name validation."""
    with pytest.raises(ValidationError) as exc_info:
        CreatePoemRequest(
            title="Title",
            content="Content",
            author_name="   ",
        )
    
    assert "author_name must not be empty" in str(exc_info.value)


# =============================================================================
# UpdatePoemRequest VALIDATION TESTS
# =============================================================================

def test_update_poem_request_all_fields():
    """Test update request with all fields."""
    request = UpdatePoemRequest(
        title="Updated Title",
        content="Updated content.",
        author_name="Updated Author",
        chapter_name="Updated Chapter",
        image_key="images/updated.jpg",
        status=PoemStatus.PUBLISHED,
    )
    
    assert request.title == "Updated Title"
    assert request.content == "Updated content."
    assert request.status == PoemStatus.PUBLISHED


def test_update_poem_request_partial():
    """Test partial update request."""
    request = UpdatePoemRequest(title="Only Title Updated")
    
    assert request.title == "Only Title Updated"
    assert request.content is None
    assert request.author_name is None
    assert request.status is None


def test_update_poem_request_empty():
    """Test empty update request is valid."""
    request = UpdatePoemRequest()
    
    assert request.title is None
    assert request.content is None
    assert request.author_name is None


def test_update_poem_request_title_trimmed():
    """Test title is trimmed in update."""
    request = UpdatePoemRequest(title="  Trimmed  ")
    
    assert request.title == "Trimmed"


def test_update_poem_request_empty_title_fails():
    """Test empty title in update fails."""
    with pytest.raises(ValidationError) as exc_info:
        UpdatePoemRequest(title="")
    
    assert "title must not be empty" in str(exc_info.value)


def test_update_poem_request_whitespace_title_fails():
    """Test whitespace-only title in update fails."""
    with pytest.raises(ValidationError) as exc_info:
        UpdatePoemRequest(title="   ")
    
    assert "title must not be empty" in str(exc_info.value)


def test_update_poem_request_empty_content_fails():
    """Test empty content in update fails."""
    with pytest.raises(ValidationError) as exc_info:
        UpdatePoemRequest(content="")
    
    assert "content must not be empty" in str(exc_info.value)


def test_update_poem_request_empty_author_name_fails():
    """Test empty author_name in update fails."""
    with pytest.raises(ValidationError) as exc_info:
        UpdatePoemRequest(author_name="")
    
    assert "author_name must not be empty" in str(exc_info.value)


# =============================================================================
# PoemDTO TESTS
# =============================================================================

def test_poem_dto_creation():
    """Test PoemDTO creation."""
    poem_id = uuid4()
    dto = PoemDTO(
        id=poem_id,
        title="Test Poem",
        content="Test content",
        author_name="Test Author",
        chapter_name="Chapter 1",
        image_url="https://example.com/image.jpg",
        status="PUBLISHED",
        published_at="2025-06-05T12:00:00+00:00",
        created_at="2025-06-01T10:00:00+00:00",
        updated_at="2025-06-05T12:00:00+00:00",
    )
    
    assert dto.id == poem_id
    assert dto.title == "Test Poem"
    assert dto.status == "PUBLISHED"


def test_poem_dto_optional_fields():
    """Test PoemDTO with optional fields as None."""
    poem_id = uuid4()
    dto = PoemDTO(
        id=poem_id,
        title="Test",
        content="Content",
        author_name="Author",
        chapter_name=None,
        image_url=None,
        status="DRAFT",
        published_at=None,
        created_at="2025-06-01T10:00:00+00:00",
        updated_at="2025-06-01T10:00:00+00:00",
    )
    
    assert dto.chapter_name is None
    assert dto.image_url is None
    assert dto.published_at is None


# =============================================================================
# PoemsResponse TESTS
# =============================================================================

def test_poems_response_creation():
    """Test PoemsResponse creation."""
    poem_id = uuid4()
    dto = PoemDTO(
        id=poem_id,
        title="Test",
        content="Content",
        author_name="Author",
        status="PUBLISHED",
        created_at="2025-06-01T10:00:00+00:00",
        updated_at="2025-06-01T10:00:00+00:00",
    )
    
    response = PoemsResponse(
        poems=[dto],
        skip=0,
        limit=20,
        total=1,
    )
    
    assert len(response.poems) == 1
    assert response.skip == 0
    assert response.limit == 20
    assert response.total == 1


def test_poems_response_empty():
    """Test empty PoemsResponse."""
    response = PoemsResponse(
        poems=[],
        skip=0,
        limit=20,
        total=0,
    )
    
    assert len(response.poems) == 0
    assert response.total == 0
