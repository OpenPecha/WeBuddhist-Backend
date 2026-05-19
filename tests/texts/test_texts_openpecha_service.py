import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from pecha_api.texts.texts_openpecha_service import (
    _extract_title,
    _map_external_text_to_dto,
    _languages_in_priority_order,
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


class TestLanguagesInPriorityOrder:
    def test_english_priority(self):
        assert _languages_in_priority_order("en") == ["en", "bo", "zh"]

    def test_tibetan_priority(self):
        assert _languages_in_priority_order("bo") == ["bo", "en", "zh"]

    def test_unknown_language_falls_back_to_english_order(self):
        assert _languages_in_priority_order("fr") == ["en", "bo", "zh"]


class TestGetTextsByCollectionId:
    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_texts_by_category", new_callable=AsyncMock)
    async def test_skip_across_languages(self, mock_fetch_texts):
        async def fake_fetch(category_id, language=None, limit=20, offset=0):
            if language == "en":
                return {"total": 5, "items": []}
            if language == "bo":
                return {
                    "total": 20,
                    "items": [_text_item(f"bo-{offset + i}", "bo") for i in range(limit)],
                }
            return {"total": 0, "items": []}

        mock_fetch_texts.side_effect = fake_fetch

        texts, total = await _get_texts_by_collection_id(
            collection_id="cat-1",
            language="en",
            skip=12,
            limit=10,
        )

        assert total == 25
        assert len(texts) == 10
        assert texts[0].id == "bo-7"

        mock_fetch_texts.assert_any_await(
            category_id="cat-1", language="en", offset=12, limit=10
        )
        mock_fetch_texts.assert_any_await(
            category_id="cat-1", language="bo", offset=7, limit=10
        )

class TestGetTextsByCollectionFromOpenpecha:
    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_category_by_id", new_callable=AsyncMock)
    @patch("pecha_api.texts.texts_openpecha_service.fetch_texts_by_category", new_callable=AsyncMock)
    async def test_get_texts_success(self, mock_fetch_texts, mock_fetch_category):
        mock_fetch_texts.side_effect = [
            {
                "total": 1,
                "items": [{"id": "t-en", "title": {"en": "EN Text"}, "language": "en"}],
            },
            {
                "total": 1,
                "items": [{"id": "t-bo", "title": {"bo": "BO Text"}, "language": "bo"}],
            },
            {"total": 0, "items": []},
        ]
        mock_fetch_category.return_value = {"title": {"en": "Collection"}}

        result = await get_texts_by_collection_from_openpecha(
            collection_id="cat-1",
            language="en",
            skip=0,
            limit=10,
        )

        assert isinstance(result, V2TextsCategoryResponse)
        assert result.collection.id == "cat-1"
        assert result.collection.title == "Collection"
        assert result.total == 2
        assert len(result.texts) == 2
        assert result.texts[0].id == "t-en"
        assert result.texts[1].id == "t-bo"

    @pytest.mark.asyncio
    @patch("pecha_api.texts.texts_openpecha_service.fetch_category_by_id", new_callable=AsyncMock)
    @patch("pecha_api.texts.texts_openpecha_service.fetch_texts_by_category", new_callable=AsyncMock)
    async def test_get_texts_with_pagination(self, mock_fetch_texts, mock_fetch_category):
        async def fake_fetch(category_id, language=None, limit=20, offset=0):
            totals = {"en": 5, "bo": 10, "zh": 3}
            if language == "en":
                return {
                    "total": totals["en"],
                    "items": [
                        {"id": f"t-{offset + i}", "title": {"en": f"Text {offset + i}"}, "language": "en"}
                        for i in range(limit)
                    ],
                }
            return {"total": totals.get(language, 0), "items": []}

        mock_fetch_texts.side_effect = fake_fetch
        mock_fetch_category.return_value = None

        result = await get_texts_by_collection_from_openpecha(
            collection_id="cat-1",
            language="en",
            skip=1,
            limit=1,
        )

        assert result.total == 18
        assert len(result.texts) == 1
        assert result.texts[0].id == "t-1"
        assert result.skip == 1
        assert result.limit == 1

        mock_fetch_texts.assert_any_await(
            category_id="cat-1", language="en", offset=1, limit=1
        )

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
