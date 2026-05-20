import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from pecha_api.texts.texts_openpecha_service import (
    get_text_versions_from_openpecha,
    get_text_by_id_from_openpecha,
    get_texts_by_collection_from_openpecha,
    get_text_commentaries_from_openpecha,
    map_external_text_to_dto,
    map_external_text_to_text_version,
    filter_versions_by_language,
    paginate_versions,
    fetch_text_from_external_api,
    fetch_translation_details,
    _extract_title,
    _get_language_priority_order,
    _validate_text_id,
)
from pecha_api.texts.texts_response_models import (
    TextDTO,
    TextVersion,
    TextVersionResponse,
    TextsCategoryResponse,
)

MOCK_EXTERNAL_TEXT_DATA = {
    "id": "text-123",
    "bdrc": "bdrc-123",
    "title": {"en": "Heart Sutra", "bo": "ཤེས་རབ་སྙིང་པོ།"},
    "language": "bo",
    "category_id": "cat-1",
    "date": "2025-01-01",
    "license": "CC0",
    "translations": ["trans-1", "trans-2"],
    "commentaries": ["comm-1"]
}

MOCK_TRANSLATION_DATA = {
    "id": "trans-1",
    "title": {"en": "English Translation"},
    "language": "en",
    "translation_of": "text-123",
    "category_id": "cat-1",
    "date": "2025-01-02",
    "license": "CC BY"
}


class TestExtractTitle:
    """Tests for _extract_title helper function."""

    def test_extract_title_from_dict_with_language(self):
        """Test extracting title when language key exists."""
        title_payload = {"en": "English Title", "bo": "བོད་ཡིག"}
        result = _extract_title(title_payload, "en")
        assert result == "English Title"

    def test_extract_title_from_dict_fallback(self):
        """Test extracting title when language key doesn't exist."""
        title_payload = {"en": "English Title", "bo": "བོད་ཡིག"}
        result = _extract_title(title_payload, "zh")
        assert result == "English Title"

    def test_extract_title_from_string(self):
        """Test extracting title from string payload."""
        title_payload = "Simple Title"
        result = _extract_title(title_payload, "en")
        assert result == "Simple Title"

    def test_extract_title_empty_dict(self):
        """Test extracting title from empty dict."""
        title_payload = {}
        result = _extract_title(title_payload, "en")
        assert result == ""

    def test_extract_title_none_language(self):
        """Test extracting title with None language."""
        title_payload = {"en": "English Title"}
        result = _extract_title(title_payload, None)
        assert result == "English Title"


class TestGetLanguagePriorityOrder:
    """Tests for _get_language_priority_order helper function."""

    def test_english_priority_order(self):
        """Test language priority order for English."""
        result = _get_language_priority_order("en")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_tibetan_priority_order(self):
        """Test language priority order for Tibetan."""
        result = _get_language_priority_order("bo")
        assert isinstance(result, list)

    def test_unknown_language_fallback(self):
        """Test fallback for unknown language."""
        result = _get_language_priority_order("unknown")
        assert isinstance(result, list)


class TestValidateTextId:
    """Tests for _validate_text_id helper function."""

    def test_valid_alphanumeric_id(self):
        """Test valid alphanumeric text ID."""
        result = _validate_text_id("text123")
        assert result == "text123"

    def test_valid_id_with_hyphen(self):
        """Test valid text ID with hyphen."""
        result = _validate_text_id("text-123")
        assert result == "text-123"

    def test_valid_id_with_underscore(self):
        """Test valid text ID with underscore."""
        result = _validate_text_id("text_123")
        assert result == "text_123"

    def test_valid_mixed_case_id(self):
        """Test valid mixed case text ID."""
        result = _validate_text_id("Text-ABC_123")
        assert result == "Text-ABC_123"

    def test_invalid_empty_id(self):
        """Test that empty text ID raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_text_id("")
        assert exc_info.value.status_code == 400
        assert "Invalid text ID format" in exc_info.value.detail

    def test_invalid_id_with_path_traversal(self):
        """Test that path traversal attempt raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_text_id("../../../etc/passwd")
        assert exc_info.value.status_code == 400

    def test_invalid_id_with_slash(self):
        """Test that text ID with slash raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_text_id("text/123")
        assert exc_info.value.status_code == 400

    def test_invalid_id_with_special_chars(self):
        """Test that text ID with special characters raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_text_id("text@123!")
        assert exc_info.value.status_code == 400

    def test_invalid_id_with_spaces(self):
        """Test that text ID with spaces raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            _validate_text_id("text 123")
        assert exc_info.value.status_code == 400


class TestMapExternalTextToDto:
    """Tests for map_external_text_to_dto function."""

    def test_map_complete_data(self):
        """Test mapping complete external text data."""
        result = map_external_text_to_dto(MOCK_EXTERNAL_TEXT_DATA, "en")

        assert isinstance(result, TextDTO)
        assert result.id == "text-123"
        assert result.pecha_text_id == "bdrc-123"
        assert result.title == "Heart Sutra"
        assert result.language == "bo"
        assert result.group_id == "cat-1"
        assert result.type == "root_text"
        assert result.is_published is True
        assert result.license == "CC0"

    def test_map_minimal_data(self):
        """Test mapping minimal external text data."""
        minimal_data = {"id": "min-123"}
        result = map_external_text_to_dto(minimal_data, "en")

        assert result.id == "min-123"
        assert result.pecha_text_id == "min-123"
        assert result.title == ""
        assert result.language == ""

    def test_map_with_bdrc_fallback(self):
        """Test pecha_text_id uses bdrc when available."""
        data_with_bdrc = {"id": "id-123", "bdrc": "bdrc-456"}
        result = map_external_text_to_dto(data_with_bdrc, "en")

        assert result.pecha_text_id == "bdrc-456"

    def test_map_categories_from_category_id(self):
        """Test categories list is populated from category_id."""
        data = {"id": "id-123", "category_id": "cat-abc"}
        result = map_external_text_to_dto(data, "en")

        assert result.categories == ["cat-abc"]


class TestMapExternalTextToTextVersion:
    """Tests for map_external_text_to_text_version function."""

    def test_map_translation_data(self):
        """Test mapping translation data to TextVersion."""
        result = map_external_text_to_text_version(MOCK_TRANSLATION_DATA, "en")

        assert isinstance(result, TextVersion)
        assert result.id == "trans-1"
        assert result.title == "English Translation"
        assert result.parent_id == "text-123"
        assert result.language == "en"
        assert result.type == "translation"
        assert result.license == "CC BY"

    def test_map_commentary_data(self):
        """Test mapping commentary data to TextVersion."""
        commentary_data = {
            "id": "comm-1",
            "title": {"en": "Commentary"},
            "language": "bo",
            "commentary_of": "text-123",
            "date": "2025-01-01"
        }
        result = map_external_text_to_text_version(commentary_data, "en")

        assert result.parent_id == "text-123"


class TestFilterVersionsByLanguage:
    """Tests for filter_versions_by_language function."""

    def test_filter_with_language(self):
        """Test filtering versions by specific language."""
        versions = [
            TextVersion(
                id="v1", title="English", parent_id=None, priority=1,
                language="en", type="translation", group_id="g1",
                table_of_contents=[], is_published=True,
                created_date="2025-01-01", updated_date="2025-01-01",
                published_date="2025-01-01", published_by="user"
            ),
            TextVersion(
                id="v2", title="Tibetan", parent_id=None, priority=2,
                language="bo", type="translation", group_id="g1",
                table_of_contents=[], is_published=True,
                created_date="2025-01-01", updated_date="2025-01-01",
                published_date="2025-01-01", published_by="user"
            )
        ]

        result = filter_versions_by_language(versions, "en")

        assert len(result) == 1
        assert result[0].language == "en"

    def test_filter_without_language(self):
        """Test that all versions are returned when language is None."""
        versions = [
            TextVersion(
                id="v1", title="English", parent_id=None, priority=1,
                language="en", type="translation", group_id="g1",
                table_of_contents=[], is_published=True,
                created_date="2025-01-01", updated_date="2025-01-01",
                published_date="2025-01-01", published_by="user"
            ),
            TextVersion(
                id="v2", title="Tibetan", parent_id=None, priority=2,
                language="bo", type="translation", group_id="g1",
                table_of_contents=[], is_published=True,
                created_date="2025-01-01", updated_date="2025-01-01",
                published_date="2025-01-01", published_by="user"
            )
        ]

        result = filter_versions_by_language(versions, None)

        assert len(result) == 2

    def test_filter_no_matches(self):
        """Test filtering when no versions match the language."""
        versions = [
            TextVersion(
                id="v1", title="English", parent_id=None, priority=1,
                language="en", type="translation", group_id="g1",
                table_of_contents=[], is_published=True,
                created_date="2025-01-01", updated_date="2025-01-01",
                published_date="2025-01-01", published_by="user"
            )
        ]

        result = filter_versions_by_language(versions, "zh")

        assert len(result) == 0


class TestPaginateVersions:
    """Tests for paginate_versions function."""

    def test_paginate_first_page(self):
        """Test pagination for first page."""
        versions = [MagicMock(id=f"v{i}") for i in range(10)]

        result = paginate_versions(versions, skip=0, limit=5)

        assert len(result) == 5

    def test_paginate_second_page(self):
        """Test pagination for second page."""
        versions = [MagicMock(id=f"v{i}") for i in range(10)]

        result = paginate_versions(versions, skip=5, limit=5)

        assert len(result) == 5

    def test_paginate_beyond_data(self):
        """Test pagination when skip exceeds data length."""
        versions = [MagicMock(id=f"v{i}") for i in range(5)]

        result = paginate_versions(versions, skip=10, limit=5)

        assert len(result) == 0

    def test_paginate_partial_page(self):
        """Test pagination when remaining items are less than limit."""
        versions = [MagicMock(id=f"v{i}") for i in range(7)]

        result = paginate_versions(versions, skip=5, limit=5)

        assert len(result) == 2


# =============================================================================
# Service Function Tests - get_text_versions_from_openpecha
# =============================================================================

class TestGetTextVersionsFromOpenpecha:
    """Tests for get_text_versions_from_openpecha service function."""

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    @patch('pecha_api.texts.texts_openpecha_service.fetch_translation_details')
    async def test_get_text_versions_success(self, mock_fetch_translations, mock_fetch_text):
        """Test successful retrieval of text versions."""
        mock_fetch_text.return_value = MOCK_EXTERNAL_TEXT_DATA
        mock_fetch_translations.return_value = [MOCK_TRANSLATION_DATA]

        result = await get_text_versions_from_openpecha(
            text_id="text-123",
            language=None,
            skip=0,
            limit=10
        )

        assert isinstance(result, TextVersionResponse)
        assert result.text is not None
        assert result.text.id == "text-123"
        assert len(result.versions) == 1
        mock_fetch_text.assert_called_once_with("text-123")

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    async def test_get_text_versions_text_not_found(self, mock_fetch_text):
        """Test 404 error when text is not found."""
        mock_fetch_text.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_text_versions_from_openpecha(
                text_id="nonexistent",
                language=None,
                skip=0,
                limit=10
            )

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    async def test_get_text_versions_no_translations(self, mock_fetch_text):
        """Test response when text has no translations."""
        text_without_translations = {
            "id": "text-123",
            "title": {"en": "Test"},
            "language": "bo",
            "translations": []
        }
        mock_fetch_text.return_value = text_without_translations

        result = await get_text_versions_from_openpecha(
            text_id="text-123",
            language=None,
            skip=0,
            limit=10
        )

        assert result.text is not None
        assert len(result.versions) == 0

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    @patch('pecha_api.texts.texts_openpecha_service.fetch_translation_details')
    async def test_get_text_versions_with_language_filter(self, mock_fetch_translations, mock_fetch_text):
        """Test filtering versions by language."""
        mock_fetch_text.return_value = MOCK_EXTERNAL_TEXT_DATA
        mock_fetch_translations.return_value = [
            {"id": "t1", "title": {"en": "English"}, "language": "en", "translation_of": "text-123"},
            {"id": "t2", "title": {"bo": "Tibetan"}, "language": "bo", "translation_of": "text-123"}
        ]

        result = await get_text_versions_from_openpecha(
            text_id="text-123",
            language="en",
            skip=0,
            limit=10
        )

        assert len(result.versions) == 1
        assert result.versions[0].language == "en"

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    @patch('pecha_api.texts.texts_openpecha_service.fetch_translation_details')
    async def test_get_text_versions_with_pagination(self, mock_fetch_translations, mock_fetch_text):
        """Test pagination of versions."""
        mock_fetch_text.return_value = MOCK_EXTERNAL_TEXT_DATA
        mock_fetch_translations.return_value = [
            {"id": f"t{i}", "title": {"en": f"Trans {i}"}, "language": "en", "translation_of": "text-123"}
            for i in range(5)
        ]

        result = await get_text_versions_from_openpecha(
            text_id="text-123",
            language=None,
            skip=2,
            limit=2
        )

        assert len(result.versions) == 2


# =============================================================================
# Service Function Tests - get_text_by_id_from_openpecha
# =============================================================================

class TestGetTextByIdFromOpenpecha:
    """Tests for get_text_by_id_from_openpecha service function."""

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_by_id')
    async def test_get_text_by_id_success(self, mock_fetch):
        """Test successful retrieval of a single text."""
        mock_fetch.return_value = MOCK_EXTERNAL_TEXT_DATA

        result = await get_text_by_id_from_openpecha("text-123")

        assert isinstance(result, TextDTO)
        assert result.id == "text-123"
        mock_fetch.assert_called_once_with("text-123")

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_by_id')
    async def test_get_text_by_id_not_found(self, mock_fetch):
        """Test 404 error when text is not found."""
        mock_fetch.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_text_by_id_from_openpecha("nonexistent")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_by_id')
    async def test_get_text_by_id_upstream_error(self, mock_fetch):
        """Test 502 error when upstream service fails."""
        mock_fetch.side_effect = Exception("Connection refused")

        with pytest.raises(HTTPException) as exc_info:
            await get_text_by_id_from_openpecha("text-123")

        assert exc_info.value.status_code == 502


# =============================================================================
# Service Function Tests - get_texts_by_collection_from_openpecha
# =============================================================================

class TestGetTextsByCollectionFromOpenpecha:
    """Tests for get_texts_by_collection_from_openpecha service function."""

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_texts_by_category')
    async def test_get_texts_by_collection_success(self, mock_fetch):
        """Test successful retrieval of texts by collection."""
        # The service iterates through language priority list, so we need to
        # return items only for the first call and empty for subsequent calls
        mock_fetch.side_effect = [
            {"items": [MOCK_EXTERNAL_TEXT_DATA]},  # First language call
            {"items": []},  # Second language call
            {"items": []},  # Third language call (if any)
        ]

        result = await get_texts_by_collection_from_openpecha(
            collection_id="cat-1",
            language="en",
            skip=0,
            limit=10
        )

        assert isinstance(result, TextsCategoryResponse)
        assert result.collection.id == "cat-1"
        assert len(result.texts) >= 1
        assert result.total >= 1

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_texts_by_category')
    async def test_get_texts_by_collection_empty(self, mock_fetch):
        """Test response when collection has no texts."""
        mock_fetch.return_value = {"items": []}

        result = await get_texts_by_collection_from_openpecha(
            collection_id="empty-cat",
            language="en",
            skip=0,
            limit=10
        )

        assert len(result.texts) == 0
        assert result.total == 0

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_texts_by_category')
    async def test_get_texts_by_collection_upstream_error(self, mock_fetch):
        """Test 502 error when upstream service fails."""
        mock_fetch.side_effect = Exception("Timeout")

        with pytest.raises(HTTPException) as exc_info:
            await get_texts_by_collection_from_openpecha(
                collection_id="cat-1",
                language="en",
                skip=0,
                limit=10
            )

        assert exc_info.value.status_code == 502


# =============================================================================
# Service Function Tests - get_text_commentaries_from_openpecha
# =============================================================================

class TestGetTextCommentariesFromOpenpecha:
    """Tests for get_text_commentaries_from_openpecha service function."""

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    @patch('pecha_api.texts.texts_openpecha_service.fetch_commentary_details')
    async def test_get_commentaries_success(self, mock_fetch_commentaries, mock_fetch_text):
        """Test successful retrieval of commentaries."""
        mock_fetch_text.return_value = {
            "id": "text-123",
            "title": {"en": "Root Text"},
            "language": "bo",
            "commentaries": ["comm-1", "comm-2"]
        }
        mock_fetch_commentaries.return_value = [
            {"id": "comm-1", "title": {"en": "Commentary 1"}, "language": "bo"},
            {"id": "comm-2", "title": {"en": "Commentary 2"}, "language": "en"}
        ]

        result = await get_text_commentaries_from_openpecha(
            text_id="text-123",
            skip=0,
            limit=10
        )

        assert len(result) == 2
        assert all(isinstance(c, TextDTO) for c in result)

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    async def test_get_commentaries_text_not_found(self, mock_fetch_text):
        """Test 404 error when text is not found."""
        mock_fetch_text.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_text_commentaries_from_openpecha(
                text_id="nonexistent",
                skip=0,
                limit=10
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    async def test_get_commentaries_no_commentaries(self, mock_fetch_text):
        """Test response when text has no commentaries."""
        mock_fetch_text.return_value = {
            "id": "text-123",
            "title": {"en": "Root Text"},
            "language": "bo",
            "commentaries": []
        }

        result = await get_text_commentaries_from_openpecha(
            text_id="text-123",
            skip=0,
            limit=10
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    @patch('pecha_api.texts.texts_openpecha_service.fetch_commentary_details')
    async def test_get_commentaries_with_pagination(self, mock_fetch_commentaries, mock_fetch_text):
        """Test pagination of commentaries."""
        mock_fetch_text.return_value = {
            "id": "text-123",
            "title": {"en": "Root Text"},
            "language": "bo",
            "commentaries": ["c1", "c2", "c3", "c4", "c5"]
        }
        mock_fetch_commentaries.return_value = [
            {"id": f"c{i}", "title": {"en": f"Commentary {i}"}, "language": "bo"}
            for i in range(1, 6)
        ]

        result = await get_text_commentaries_from_openpecha(
            text_id="text-123",
            skip=2,
            limit=2
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    @patch('pecha_api.texts.texts_openpecha_service.fetch_commentary_details')
    async def test_get_commentaries_skip_beyond_total(self, mock_fetch_commentaries, mock_fetch_text):
        """Test pagination when skip exceeds total commentaries."""
        mock_fetch_text.return_value = {
            "id": "text-123",
            "title": {"en": "Root Text"},
            "language": "bo",
            "commentaries": ["c1", "c2"]
        }
        mock_fetch_commentaries.return_value = [
            {"id": "c1", "title": {"en": "Commentary 1"}, "language": "bo"},
            {"id": "c2", "title": {"en": "Commentary 2"}, "language": "bo"}
        ]

        result = await get_text_commentaries_from_openpecha(
            text_id="text-123",
            skip=10,
            limit=5
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    @patch('pecha_api.texts.texts_openpecha_service.fetch_commentary_details')
    async def test_get_commentaries_verifies_dto_mapping(self, mock_fetch_commentaries, mock_fetch_text):
        """Test that commentaries are correctly mapped to TextDTO."""
        mock_fetch_text.return_value = {
            "id": "text-123",
            "title": {"en": "Root Text"},
            "language": "bo",
            "commentaries": ["comm-1"]
        }
        mock_fetch_commentaries.return_value = [
            {
                "id": "comm-1",
                "bdrc": "bdrc-comm-1",
                "title": {"en": "Commentary Title", "bo": "བསྟན་བཅོས།"},
                "language": "bo",
                "category_id": "cat-1",
                "date": "2025-01-01",
                "license": "CC BY"
            }
        ]

        result = await get_text_commentaries_from_openpecha(
            text_id="text-123",
            skip=0,
            limit=10
        )

        assert len(result) == 1
        commentary = result[0]
        assert commentary.id == "comm-1"
        assert commentary.pecha_text_id == "bdrc-comm-1"
        assert commentary.language == "bo"
        assert commentary.license == "CC BY"

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    async def test_get_commentaries_missing_commentaries_key(self, mock_fetch_text):
        """Test response when commentaries key is missing from text data."""
        mock_fetch_text.return_value = {
            "id": "text-123",
            "title": {"en": "Root Text"},
            "language": "bo"
        }

        result = await get_text_commentaries_from_openpecha(
            text_id="text-123",
            skip=0,
            limit=10
        )

        assert len(result) == 0

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    @patch('pecha_api.texts.texts_openpecha_service.fetch_commentary_details')
    async def test_get_commentaries_partial_fetch_failure(self, mock_fetch_commentaries, mock_fetch_text):
        """Test that partial failures in fetching commentaries don't break the response."""
        mock_fetch_text.return_value = {
            "id": "text-123",
            "title": {"en": "Root Text"},
            "language": "bo",
            "commentaries": ["c1", "c2", "c3"]
        }
        mock_fetch_commentaries.return_value = [
            {"id": "c1", "title": {"en": "Commentary 1"}, "language": "bo"}
        ]

        result = await get_text_commentaries_from_openpecha(
            text_id="text-123",
            skip=0,
            limit=10
        )

        assert len(result) == 1
        assert result[0].id == "c1"


class TestFetchCommentaryDetails:
    """Tests for fetch_commentary_details function."""

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    async def test_fetch_commentary_details_success(self, mock_fetch):
        """Test successful fetch of commentary details."""
        mock_fetch.return_value = {
            "id": "comm-1",
            "title": {"en": "Commentary"},
            "language": "bo"
        }

        from pecha_api.texts.texts_openpecha_service import fetch_commentary_details
        result = await fetch_commentary_details(["comm-1"])

        assert len(result) == 1
        assert result[0]["id"] == "comm-1"

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    async def test_fetch_commentary_details_partial_failure(self, mock_fetch):
        """Test that partial failures don't break the entire operation."""
        mock_fetch.side_effect = [
            {"id": "comm-1", "title": {"en": "Commentary 1"}, "language": "bo"},
            HTTPException(status_code=404, detail="Not found"),
            {"id": "comm-3", "title": {"en": "Commentary 3"}, "language": "bo"}
        ]

        from pecha_api.texts.texts_openpecha_service import fetch_commentary_details
        result = await fetch_commentary_details(["comm-1", "comm-2", "comm-3"])

        assert len(result) == 2
        assert result[0]["id"] == "comm-1"
        assert result[1]["id"] == "comm-3"

    @pytest.mark.asyncio
    async def test_fetch_commentary_details_empty_list(self):
        """Test fetching with empty commentary list."""
        from pecha_api.texts.texts_openpecha_service import fetch_commentary_details
        result = await fetch_commentary_details([])

        assert len(result) == 0

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    async def test_fetch_commentary_details_all_failures(self, mock_fetch):
        """Test when all commentary fetches fail."""
        mock_fetch.side_effect = HTTPException(status_code=502, detail="Upstream error")

        from pecha_api.texts.texts_openpecha_service import fetch_commentary_details
        result = await fetch_commentary_details(["comm-1", "comm-2"])

        assert len(result) == 0


# =============================================================================
# External API Function Tests
# =============================================================================

class TestFetchTextFromExternalApi:
    """Tests for fetch_text_from_external_api function."""

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.httpx.AsyncClient')
    @patch('pecha_api.texts.texts_openpecha_service.get')
    async def test_fetch_text_success(self, mock_config_get, mock_client_class):
        """Test successful fetch from external API."""
        mock_config_get.return_value = "http://api.example.com"
        
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_EXTERNAL_TEXT_DATA
        mock_response.raise_for_status = MagicMock()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        result = await fetch_text_from_external_api("text-123")

        assert result == MOCK_EXTERNAL_TEXT_DATA

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.httpx.AsyncClient')
    @patch('pecha_api.texts.texts_openpecha_service.get')
    async def test_fetch_text_http_error(self, mock_config_get, mock_client_class):
        """Test handling of HTTP errors."""
        import httpx
        
        mock_config_get.return_value = "http://api.example.com"
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError("Not found", request=MagicMock(), response=mock_response)
        )
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client_class.return_value = mock_client

        with pytest.raises(HTTPException) as exc_info:
            await fetch_text_from_external_api("nonexistent")

        assert exc_info.value.status_code == 502


class TestFetchTranslationDetails:
    """Tests for fetch_translation_details function."""

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    async def test_fetch_translations_success(self, mock_fetch):
        """Test successful fetch of translation details."""
        mock_fetch.return_value = MOCK_TRANSLATION_DATA

        result = await fetch_translation_details(["trans-1"])

        assert len(result) == 1
        assert result[0]["id"] == "trans-1"

    @pytest.mark.asyncio
    @patch('pecha_api.texts.texts_openpecha_service.fetch_text_from_external_api')
    async def test_fetch_translations_partial_failure(self, mock_fetch):
        """Test that partial failures don't break the entire operation."""
        mock_fetch.side_effect = [
            MOCK_TRANSLATION_DATA,
            HTTPException(status_code=404, detail="Not found")
        ]

        result = await fetch_translation_details(["trans-1", "trans-2"])

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_fetch_translations_empty_list(self):
        """Test fetching with empty translation list."""
        result = await fetch_translation_details([])

        assert len(result) == 0
