import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from pecha_api.texts.texts_openpecha_service import (
    _extract_title,
    _map_external_text_to_dto,
    _get_texts_by_collection_id,
    get_texts_by_collection_from_openpecha,
    get_text_by_id_from_openpecha,
)
from pecha_api.texts.texts_response_models import V2TextDTO, V2TextsCategoryResponse


def _text_item(text_id: str, lang: str) -> dict:
    return {
        "id": text_id,
        "title": {lang: f"Title {text_id}"},
        "language": lang,
    }


class TestExtractTitle:
    def test_extract_title_from_dict_with_language(self):
        assert _extract_title({"en": "English", "bo": "Tibetan"}, "bo") == "Tibetan"

    def test_extract_title_fallback_to_first_value(self):
        assert _extract_title({"en": "English", "bo": "Tibetan"}, "fr") == "English"

    def test_extract_title_from_string(self):
        assert _extract_title("  Plain title  ") == "Plain title"


class TestGetTextsByCollectionId:
    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_texts_by_category", new_callable=AsyncMock)
    async def test_passes_skip_and_limit_to_upstream_without_language(self, mock_fetch_texts):
        mock_fetch_texts.return_value = {
            "items": [
                _text_item("t-en", "en"),
                _text_item("t-bo", "bo"),
                _text_item("t-zh", "zh"),
            ],
            "has_more": True,
        }

        texts, has_more = await _get_texts_by_collection_id(
            collection_id="cat-1",
            skip=5,
            limit=3,
        )

        assert [t.id for t in texts] == ["t-en", "t-bo", "t-zh"]
        assert [t.language for t in texts] == ["en", "bo", "zh"]
        assert has_more is True

        mock_fetch_texts.assert_awaited_once_with(
            category_id="cat-1",
            offset=5,
            limit=3,
        )

    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_texts_by_category", new_callable=AsyncMock)
    async def test_returns_empty_list_when_no_items(self, mock_fetch_texts):
        mock_fetch_texts.return_value = {"items": [], "has_more": False}

        texts, has_more = await _get_texts_by_collection_id(
            collection_id="cat-1",
            skip=0,
            limit=10,
        )

        assert texts == []
        assert has_more is False

    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_texts_by_category", new_callable=AsyncMock)
    async def test_defaults_has_more_to_false_when_upstream_omits_it(self, mock_fetch_texts):
        mock_fetch_texts.return_value = {
            "items": [_text_item("t-en", "en")],
        }

        texts, has_more = await _get_texts_by_collection_id(
            collection_id="cat-1",
            skip=0,
            limit=10,
        )

        assert len(texts) == 1
        assert has_more is False

    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_texts_by_category", new_callable=AsyncMock)
    async def test_upstream_failure_maps_to_502(self, mock_fetch_texts):
        mock_fetch_texts.side_effect = Exception("connection refused")

        with pytest.raises(HTTPException) as exc_info:
            await _get_texts_by_collection_id(
                collection_id="cat-1",
                skip=0,
                limit=10,
            )

        assert exc_info.value.status_code == 502


class TestGetTextsByCollectionFromOpenpecha:
    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_category_by_id", new_callable=AsyncMock)
    @patch("pecha_api.texts.texts_openpecha_service.fetch_texts_by_category", new_callable=AsyncMock)
    async def test_get_texts_success(self, mock_fetch_texts, mock_fetch_category):
        mock_fetch_texts.return_value = {
            "items": [
                {"id": "t-en", "title": {"en": "EN Text"}, "language": "en"},
                {"id": "t-bo", "title": {"bo": "BO Text"}, "language": "bo"},
            ],
            "has_more": False,
        }
        mock_fetch_category.return_value = {"title": {"en": "Collection"}}

        result = await get_texts_by_collection_from_openpecha(
            collection_id="cat-1",
            skip=0,
            limit=10,
        )

        assert isinstance(result, V2TextsCategoryResponse)
        assert result.collection.id == "cat-1"
        assert result.collection.title == "Collection"
        assert len(result.texts) == 2
        assert result.texts[0].id == "t-en"
        assert result.texts[1].id == "t-bo"
        assert result.has_more is False

        mock_fetch_texts.assert_awaited_once_with(
            category_id="cat-1",
            offset=0,
            limit=10,
        )

    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_category_by_id", new_callable=AsyncMock)
    @patch("pecha_api.texts.texts_openpecha_service.fetch_texts_by_category", new_callable=AsyncMock)
    async def test_get_texts_with_pagination(self, mock_fetch_texts, mock_fetch_category):
        mock_fetch_texts.return_value = {
            "items": [
                {"id": "t-1", "title": {"en": "Text 1"}, "language": "en"},
            ],
            "has_more": True,
        }
        mock_fetch_category.return_value = None

        result = await get_texts_by_collection_from_openpecha(
            collection_id="cat-1",
            skip=1,
            limit=1,
        )

        assert len(result.texts) == 1
        assert result.texts[0].id == "t-1"
        assert result.skip == 1
        assert result.limit == 1
        assert result.has_more is True

        mock_fetch_texts.assert_awaited_once_with(
            category_id="cat-1",
            offset=1,
            limit=1,
        )

    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_texts_by_category", new_callable=AsyncMock)
    async def test_get_texts_upstream_error(self, mock_fetch_texts):
        mock_fetch_texts.side_effect = Exception("connection refused")

        with pytest.raises(HTTPException) as exc_info:
            await get_texts_by_collection_from_openpecha(collection_id="cat-1")

        assert exc_info.value.status_code == 502

    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_category_by_id", new_callable=AsyncMock)
    @patch("pecha_api.texts.texts_openpecha_service.fetch_texts_by_category", new_callable=AsyncMock)
    async def test_get_texts_category_upstream_error(self, mock_fetch_texts, mock_fetch_category):
        mock_fetch_texts.return_value = {"items": [], "has_more": False}
        mock_fetch_category.side_effect = Exception("connection refused")

        with pytest.raises(HTTPException) as exc_info:
            await get_texts_by_collection_from_openpecha(collection_id="cat-1")

        assert exc_info.value.status_code == 502
        assert "category" in exc_info.value.detail.lower()


class TestGetTextByIdFromOpenpecha:
    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_text_by_id", new_callable=AsyncMock)
    async def test_get_text_by_id_success(self, mock_fetch_text):
        mock_fetch_text.return_value = {
            "id": "t1",
            "title": {"en": "Test Text"},
            "language": "en",
            "license": "CC0",
        }

        result = await get_text_by_id_from_openpecha("t1")

        assert isinstance(result, V2TextDTO)
        assert result.id == "t1"
        assert result.title == "Test Text"
        assert result.language == "en"
        assert result.license == "CC0"

    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_text_by_id", new_callable=AsyncMock)
    async def test_get_text_by_id_not_found(self, mock_fetch_text):
        mock_fetch_text.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_text_by_id_from_openpecha("missing")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_text_by_id", new_callable=AsyncMock)
    async def test_get_text_by_id_upstream_error(self, mock_fetch_text):
        mock_fetch_text.side_effect = Exception("timeout")

        with pytest.raises(HTTPException) as exc_info:
            await get_text_by_id_from_openpecha("t1")

        assert exc_info.value.status_code == 502


class TestMapExternalTextToDto:
    def test_map_external_text_to_dto(self):
        dto = _map_external_text_to_dto(
            {"id": "t1", "title": {"en": "Title"}, "language": "en", "license": "CC0"},
            "en",
        )
        assert dto.id == "t1"
        assert dto.title == "Title"
        assert dto.language == "en"
        assert dto.license == "CC0"
