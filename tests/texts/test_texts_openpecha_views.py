import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from pecha_api.app import api
from pecha_api.texts.texts_response_models import (
    TextDTO,
    TextVersion,
    TextVersionResponse,
    TextsCategoryResponse,
)
from pecha_api.collections.collections_response_models import CollectionModel


client = TestClient(api)

MOCK_TEXT_DTO = TextDTO(
    id="text-123",
    pecha_text_id="pecha-text-123",
    title="Heart Sutra",
    language="bo",
    group_id="group-123",
    type="root_text",
    is_published=True,
    created_date="2025-01-01T00:00:00",
    updated_date="2025-01-01T00:00:00",
    published_date="2025-01-01T00:00:00",
    published_by="pecha",
    categories=["cat-1"],
    views=100,
    source_link="https://example.com",
    ranking=1,
    license="CC0"
)

MOCK_TEXT_VERSION_1 = TextVersion(
    id="version-1",
    title="English Translation",
    parent_id="text-123",
    priority=1,
    language="en",
    type="translation",
    group_id="group-123",
    table_of_contents=[],
    is_published=True,
    created_date="2025-01-01T00:00:00",
    updated_date="2025-01-01T00:00:00",
    published_date="2025-01-01T00:00:00",
    published_by="translator_1",
    source_link="https://translation.com",
    ranking=1,
    license="CC BY"
)

MOCK_TEXT_VERSION_2 = TextVersion(
    id="version-2",
    title="Chinese Translation",
    parent_id="text-123",
    priority=2,
    language="zh",
    type="translation",
    group_id="group-123",
    table_of_contents=[],
    is_published=True,
    created_date="2025-01-02T00:00:00",
    updated_date="2025-01-02T00:00:00",
    published_date="2025-01-02T00:00:00",
    published_by="translator_2",
    source_link=None,
    ranking=2,
    license="CC0"
)


class TestGetTextVersionsEndpoint:
    """Tests for GET /v2/texts/{text_id}/versions endpoint."""

    @patch('pecha_api.texts.texts_openpecha_views.get_text_versions_from_openpecha')
    def test_get_text_versions_success(self, mock_service):
        """Test successful retrieval of text versions."""
        mock_response = TextVersionResponse(
            text=MOCK_TEXT_DTO,
            versions=[MOCK_TEXT_VERSION_1, MOCK_TEXT_VERSION_2]
        )
        mock_service.return_value = mock_response

        response = client.get("/v2/texts/text-123/versions")

        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "versions" in data
        assert data["text"]["id"] == "text-123"
        assert data["text"]["title"] == "Heart Sutra"
        assert len(data["versions"]) == 2
        assert data["versions"][0]["id"] == "version-1"
        assert data["versions"][1]["id"] == "version-2"
        mock_service.assert_called_once_with(
            text_id="text-123",
            language=None,
            skip=0,
            limit=10
        )

    @patch('pecha_api.texts.texts_openpecha_views.get_text_versions_from_openpecha')
    def test_get_text_versions_with_language_filter(self, mock_service):
        """Test retrieval of text versions filtered by language."""
        mock_response = TextVersionResponse(
            text=MOCK_TEXT_DTO,
            versions=[MOCK_TEXT_VERSION_1]
        )
        mock_service.return_value = mock_response

        response = client.get("/v2/texts/text-123/versions?language=en")

        assert response.status_code == 200
        data = response.json()
        assert len(data["versions"]) == 1
        assert data["versions"][0]["language"] == "en"
        mock_service.assert_called_once_with(
            text_id="text-123",
            language="en",
            skip=0,
            limit=10
        )

    @patch('pecha_api.texts.texts_openpecha_views.get_text_versions_from_openpecha')
    def test_get_text_versions_with_pagination(self, mock_service):
        """Test retrieval of text versions with pagination parameters."""
        mock_response = TextVersionResponse(
            text=MOCK_TEXT_DTO,
            versions=[MOCK_TEXT_VERSION_2]
        )
        mock_service.return_value = mock_response

        response = client.get("/v2/texts/text-123/versions?skip=1&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert len(data["versions"]) == 1
        mock_service.assert_called_once_with(
            text_id="text-123",
            language=None,
            skip=1,
            limit=5
        )

    @patch('pecha_api.texts.texts_openpecha_views.get_text_versions_from_openpecha')
    def test_get_text_versions_empty_versions(self, mock_service):
        """Test retrieval when text has no versions."""
        mock_response = TextVersionResponse(
            text=MOCK_TEXT_DTO,
            versions=[]
        )
        mock_service.return_value = mock_response

        response = client.get("/v2/texts/text-123/versions")

        assert response.status_code == 200
        data = response.json()
        assert data["text"]["id"] == "text-123"
        assert len(data["versions"]) == 0

    @patch('pecha_api.texts.texts_openpecha_views.get_text_versions_from_openpecha')
    def test_get_text_versions_with_all_parameters(self, mock_service):
        """Test retrieval with all query parameters."""
        mock_response = TextVersionResponse(
            text=MOCK_TEXT_DTO,
            versions=[MOCK_TEXT_VERSION_1]
        )
        mock_service.return_value = mock_response

        response = client.get("/v2/texts/text-123/versions?language=bo&skip=2&limit=20")

        assert response.status_code == 200
        mock_service.assert_called_once_with(
            text_id="text-123",
            language="bo",
            skip=2,
            limit=20
        )


class TestGetTextVersionsErrorHandling:
    """Tests for error handling in GET /v2/texts/{text_id}/versions endpoint."""

    @patch('pecha_api.texts.texts_openpecha_views.get_text_versions_from_openpecha')
    def test_get_text_versions_not_found(self, mock_service):
        """Test 404 error when text is not found."""
        mock_service.side_effect = HTTPException(
            status_code=404,
            detail="Text with id 'nonexistent' not found"
        )

        response = client.get("/v2/texts/nonexistent/versions")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch('pecha_api.texts.texts_openpecha_views.get_text_versions_from_openpecha')
    def test_get_text_versions_upstream_error(self, mock_service):
        """Test 502 error when upstream service fails."""
        mock_service.side_effect = HTTPException(
            status_code=502,
            detail="Failed to fetch text from external API"
        )

        response = client.get("/v2/texts/text-123/versions")

        assert response.status_code == 502
        assert "external" in response.json()["detail"].lower() or "failed" in response.json()["detail"].lower()

    @patch('pecha_api.texts.texts_openpecha_views.get_text_versions_from_openpecha')
    def test_get_text_versions_internal_error(self, mock_service):
        """Test 500 error for unexpected internal errors."""
        mock_service.side_effect = HTTPException(
            status_code=500,
            detail="Internal server error"
        )

        response = client.get("/v2/texts/text-123/versions")

        assert response.status_code == 500


class TestGetTextVersionsResponseStructure:
    """Tests for response structure validation."""

    @patch('pecha_api.texts.texts_openpecha_views.get_text_versions_from_openpecha')
    def test_response_contains_all_text_fields(self, mock_service):
        """Test that response contains all expected text fields."""
        mock_response = TextVersionResponse(
            text=MOCK_TEXT_DTO,
            versions=[MOCK_TEXT_VERSION_1]
        )
        mock_service.return_value = mock_response

        response = client.get("/v2/texts/text-123/versions")

        assert response.status_code == 200
        text_data = response.json()["text"]
        assert "id" in text_data
        assert "title" in text_data
        assert "language" in text_data
        assert "type" in text_data
        assert "is_published" in text_data
        assert "created_date" in text_data
        assert "categories" in text_data

    @patch('pecha_api.texts.texts_openpecha_views.get_text_versions_from_openpecha')
    def test_response_contains_all_version_fields(self, mock_service):
        """Test that response contains all expected version fields."""
        mock_response = TextVersionResponse(
            text=MOCK_TEXT_DTO,
            versions=[MOCK_TEXT_VERSION_1]
        )
        mock_service.return_value = mock_response

        response = client.get("/v2/texts/text-123/versions")

        assert response.status_code == 200
        version_data = response.json()["versions"][0]
        assert "id" in version_data
        assert "title" in version_data
        assert "language" in version_data
        assert "type" in version_data
        assert "is_published" in version_data
        assert "parent_id" in version_data

    @patch('pecha_api.texts.texts_openpecha_views.get_text_versions_from_openpecha')
    def test_response_with_optional_fields_none(self, mock_service):
        """Test response when optional fields are None."""
        version_with_none = TextVersion(
            id="version-none",
            title="Version with None fields",
            parent_id=None,
            priority=None,
            language="en",
            type="translation",
            group_id="group-123",
            table_of_contents=[],
            is_published=True,
            created_date="2025-01-01T00:00:00",
            updated_date="2025-01-01T00:00:00",
            published_date="2025-01-01T00:00:00",
            published_by="translator",
            source_link=None,
            ranking=None,
            license=None
        )
        mock_response = TextVersionResponse(
            text=MOCK_TEXT_DTO,
            versions=[version_with_none]
        )
        mock_service.return_value = mock_response

        response = client.get("/v2/texts/text-123/versions")

        assert response.status_code == 200
        version_data = response.json()["versions"][0]
        assert version_data["parent_id"] is None
        assert version_data["priority"] is None
        assert version_data["source_link"] is None
        assert version_data["ranking"] is None
        assert version_data["license"] is None


# =============================================================================
# GET /v2/texts/{text_id} - View Layer Tests
# =============================================================================

class TestGetTextByIdEndpoint:
    """Tests for GET /v2/texts/{text_id} endpoint."""

    @patch('pecha_api.texts.texts_openpecha_views.get_text_by_id_from_openpecha')
    def test_get_text_by_id_success(self, mock_service):
        """Test successful retrieval of a single text."""
        mock_service.return_value = MOCK_TEXT_DTO

        response = client.get("/v2/texts/text-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "text-123"
        assert data["title"] == "Heart Sutra"
        assert data["language"] == "bo"
        mock_service.assert_called_once_with(text_id="text-123")

    @patch('pecha_api.texts.texts_openpecha_views.get_text_by_id_from_openpecha')
    def test_get_text_by_id_not_found(self, mock_service):
        """Test 404 error when text is not found."""
        mock_service.side_effect = HTTPException(
            status_code=404,
            detail="Text with id 'nonexistent' not found"
        )

        response = client.get("/v2/texts/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch('pecha_api.texts.texts_openpecha_views.get_text_by_id_from_openpecha')
    def test_get_text_by_id_upstream_error(self, mock_service):
        """Test 502 error when upstream service fails."""
        mock_service.side_effect = HTTPException(
            status_code=502,
            detail="Failed to fetch text from upstream service"
        )

        response = client.get("/v2/texts/text-123")

        assert response.status_code == 502


# =============================================================================
# GET /v2/texts/collection/{collection_id} - View Layer Tests
# =============================================================================

class TestGetTextsByCollectionEndpoint:
    """Tests for GET /v2/texts/collection/{collection_id} endpoint."""

    @patch('pecha_api.texts.texts_openpecha_views.get_texts_by_collection_from_openpecha')
    def test_get_texts_by_collection_success(self, mock_service):
        """Test successful retrieval of texts by collection."""
        mock_collection = CollectionModel(
            id="collection-1",
            pecha_collection_id="collection-1",
            title="Sutras",
            description="Buddhist sutras",
            language="en",
            slug="sutras",
            has_child=False
        )
        mock_response = TextsCategoryResponse(
            collection=mock_collection,
            texts=[MOCK_TEXT_DTO],
            total=1,
            skip=0,
            limit=10
        )
        mock_service.return_value = mock_response

        response = client.get("/v2/texts/collection/collection-1")

        assert response.status_code == 200
        data = response.json()
        assert data["collection"]["id"] == "collection-1"
        assert len(data["texts"]) == 1
        assert data["total"] == 1
        mock_service.assert_called_once_with(
            collection_id="collection-1",
            language=None,
            skip=0,
            limit=10
        )

    @patch('pecha_api.texts.texts_openpecha_views.get_texts_by_collection_from_openpecha')
    def test_get_texts_by_collection_with_language(self, mock_service):
        """Test retrieval with language filter."""
        mock_collection = CollectionModel(
            id="collection-1",
            pecha_collection_id="collection-1",
            title="མདོ།",
            description="",
            language="bo",
            slug="sutras",
            has_child=False
        )
        mock_response = TextsCategoryResponse(
            collection=mock_collection,
            texts=[MOCK_TEXT_DTO],
            total=1,
            skip=0,
            limit=10
        )
        mock_service.return_value = mock_response

        response = client.get("/v2/texts/collection/collection-1?language=bo")

        assert response.status_code == 200
        mock_service.assert_called_once_with(
            collection_id="collection-1",
            language="bo",
            skip=0,
            limit=10
        )

    @patch('pecha_api.texts.texts_openpecha_views.get_texts_by_collection_from_openpecha')
    def test_get_texts_by_collection_empty(self, mock_service):
        """Test retrieval when collection has no texts."""
        mock_collection = CollectionModel(
            id="collection-empty",
            pecha_collection_id="collection-empty",
            title="Empty Collection",
            description="",
            language="en",
            slug="empty",
            has_child=False
        )
        mock_response = TextsCategoryResponse(
            collection=mock_collection,
            texts=[],
            total=0,
            skip=0,
            limit=10
        )
        mock_service.return_value = mock_response

        response = client.get("/v2/texts/collection/collection-empty")

        assert response.status_code == 200
        data = response.json()
        assert len(data["texts"]) == 0
        assert data["total"] == 0


# =============================================================================
# GET /v2/texts/{text_id}/commentaries - View Layer Tests
# =============================================================================

class TestGetTextCommentariesEndpoint:
    """Tests for GET /v2/texts/{text_id}/commentaries endpoint."""

    @patch('pecha_api.texts.texts_openpecha_views.get_text_commentaries_from_openpecha')
    def test_get_text_commentaries_success(self, mock_service):
        """Test successful retrieval of text commentaries."""
        mock_commentary = TextDTO(
            id="commentary-1",
            pecha_text_id="pecha-commentary-1",
            title="Commentary on Heart Sutra",
            language="bo",
            group_id="group-123",
            type="commentary",
            is_published=True,
            created_date="2025-01-01T00:00:00",
            updated_date="2025-01-01T00:00:00",
            published_date="2025-01-01T00:00:00",
            published_by="commentator",
            categories=["cat-1"],
            views=50,
            source_link=None,
            ranking=1,
            license="CC0"
        )
        mock_service.return_value = [mock_commentary]

        response = client.get("/v2/texts/text-123/commentaries")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "commentary-1"
        assert data[0]["type"] == "commentary"
        mock_service.assert_called_once_with(
            text_id="text-123",
            skip=0,
            limit=10
        )

    @patch('pecha_api.texts.texts_openpecha_views.get_text_commentaries_from_openpecha')
    def test_get_text_commentaries_multiple(self, mock_service):
        """Test retrieval of multiple commentaries."""
        mock_commentaries = [
            TextDTO(
                id=f"commentary-{i}",
                pecha_text_id=f"pecha-commentary-{i}",
                title=f"Commentary {i}",
                language="bo" if i % 2 == 0 else "en",
                group_id="group-123",
                type="commentary",
                is_published=True,
                created_date="2025-01-01T00:00:00",
                updated_date="2025-01-01T00:00:00",
                published_date="2025-01-01T00:00:00",
                published_by=f"commentator-{i}",
                categories=["cat-1"],
                views=i * 10,
                source_link=None,
                ranking=i,
                license="CC0"
            )
            for i in range(1, 4)
        ]
        mock_service.return_value = mock_commentaries

        response = client.get("/v2/texts/text-123/commentaries")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["id"] == "commentary-1"
        assert data[1]["id"] == "commentary-2"
        assert data[2]["id"] == "commentary-3"

    @patch('pecha_api.texts.texts_openpecha_views.get_text_commentaries_from_openpecha')
    def test_get_text_commentaries_empty(self, mock_service):
        """Test retrieval when text has no commentaries."""
        mock_service.return_value = []

        response = client.get("/v2/texts/text-123/commentaries")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    @patch('pecha_api.texts.texts_openpecha_views.get_text_commentaries_from_openpecha')
    def test_get_text_commentaries_with_pagination(self, mock_service):
        """Test retrieval with pagination parameters."""
        mock_service.return_value = []

        response = client.get("/v2/texts/text-123/commentaries?skip=5&limit=20")

        assert response.status_code == 200
        mock_service.assert_called_once_with(
            text_id="text-123",
            skip=5,
            limit=20
        )

    @patch('pecha_api.texts.texts_openpecha_views.get_text_commentaries_from_openpecha')
    def test_get_text_commentaries_with_skip_only(self, mock_service):
        """Test retrieval with only skip parameter."""
        mock_service.return_value = []

        response = client.get("/v2/texts/text-123/commentaries?skip=10")

        assert response.status_code == 200
        mock_service.assert_called_once_with(
            text_id="text-123",
            skip=10,
            limit=10
        )

    @patch('pecha_api.texts.texts_openpecha_views.get_text_commentaries_from_openpecha')
    def test_get_text_commentaries_with_limit_only(self, mock_service):
        """Test retrieval with only limit parameter."""
        mock_service.return_value = []

        response = client.get("/v2/texts/text-123/commentaries?limit=50")

        assert response.status_code == 200
        mock_service.assert_called_once_with(
            text_id="text-123",
            skip=0,
            limit=50
        )

    def test_get_text_commentaries_invalid_skip(self):
        """Test validation error for negative skip."""
        response = client.get("/v2/texts/text-123/commentaries?skip=-1")
        assert response.status_code == 422

    def test_get_text_commentaries_invalid_limit(self):
        """Test validation error for limit exceeding maximum."""
        response = client.get("/v2/texts/text-123/commentaries?limit=101")
        assert response.status_code == 422


class TestGetTextCommentariesErrorHandling:
    """Tests for error handling in GET /v2/texts/{text_id}/commentaries endpoint."""

    @patch('pecha_api.texts.texts_openpecha_views.get_text_commentaries_from_openpecha')
    def test_get_text_commentaries_not_found(self, mock_service):
        """Test 404 error when text is not found."""
        mock_service.side_effect = HTTPException(
            status_code=404,
            detail="Text with id 'nonexistent' not found"
        )

        response = client.get("/v2/texts/nonexistent/commentaries")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch('pecha_api.texts.texts_openpecha_views.get_text_commentaries_from_openpecha')
    def test_get_text_commentaries_upstream_error(self, mock_service):
        """Test 502 error when upstream service fails."""
        mock_service.side_effect = HTTPException(
            status_code=502,
            detail="Failed to fetch commentaries from external API"
        )

        response = client.get("/v2/texts/text-123/commentaries")

        assert response.status_code == 502

    @patch('pecha_api.texts.texts_openpecha_views.get_text_commentaries_from_openpecha')
    def test_get_text_commentaries_internal_error(self, mock_service):
        """Test 500 error for unexpected internal errors."""
        mock_service.side_effect = HTTPException(
            status_code=500,
            detail="Internal server error"
        )

        response = client.get("/v2/texts/text-123/commentaries")

        assert response.status_code == 500


class TestGetTextCommentariesResponseStructure:
    """Tests for response structure validation of commentaries endpoint."""

    @patch('pecha_api.texts.texts_openpecha_views.get_text_commentaries_from_openpecha')
    def test_commentary_contains_all_required_fields(self, mock_service):
        """Test that each commentary contains all expected fields."""
        mock_commentary = TextDTO(
            id="commentary-1",
            pecha_text_id="pecha-commentary-1",
            title="Commentary Title",
            language="bo",
            group_id="group-123",
            type="commentary",
            is_published=True,
            created_date="2025-01-01T00:00:00",
            updated_date="2025-01-01T00:00:00",
            published_date="2025-01-01T00:00:00",
            published_by="commentator",
            categories=["cat-1"],
            views=100,
            source_link="https://example.com",
            ranking=1,
            license="CC BY"
        )
        mock_service.return_value = [mock_commentary]

        response = client.get("/v2/texts/text-123/commentaries")

        assert response.status_code == 200
        data = response.json()[0]
        assert "id" in data
        assert "pecha_text_id" in data
        assert "title" in data
        assert "language" in data
        assert "group_id" in data
        assert "type" in data
        assert "is_published" in data
        assert "created_date" in data
        assert "updated_date" in data
        assert "published_date" in data
        assert "published_by" in data
        assert "categories" in data
        assert "views" in data
        assert "source_link" in data
        assert "ranking" in data
        assert "license" in data

    @patch('pecha_api.texts.texts_openpecha_views.get_text_commentaries_from_openpecha')
    def test_commentary_with_optional_fields_none(self, mock_service):
        """Test response when optional fields are None."""
        mock_commentary = TextDTO(
            id="commentary-1",
            pecha_text_id="pecha-commentary-1",
            title="Commentary Title",
            language="bo",
            group_id="group-123",
            type="commentary",
            is_published=True,
            created_date="2025-01-01T00:00:00",
            updated_date="2025-01-01T00:00:00",
            published_date="2025-01-01T00:00:00",
            published_by="commentator",
            categories=[],
            views=0,
            source_link=None,
            ranking=None,
            license=None
        )
        mock_service.return_value = [mock_commentary]

        response = client.get("/v2/texts/text-123/commentaries")

        assert response.status_code == 200
        data = response.json()[0]
        assert data["source_link"] is None
        assert data["ranking"] is None
        assert data["license"] is None
        assert data["categories"] == []
        assert data["views"] == 0
