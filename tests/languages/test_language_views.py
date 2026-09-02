from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.languages import language_service
from pecha_api.languages.language_response_models import LanguageDTO, LanguageListResponse
from pecha_api.languages.language_service import list_languages_service, load_languages
from pecha_api.plans.plans_enums import LanguageCode

client = TestClient(api)

SAMPLE_LANGUAGES = {
    "languages": [
        {
            "code": "en",
            "name": "English",
            "native_name": "English",
            "enabled": True,
        },
        {
            "code": "bo",
            "name": "Tibetan",
            "native_name": "Tibetan",
            "enabled": False,
        },
        {
            "code": "zh",
            "name": "Chinese",
            "native_name": "Chinese",
        },
    ]
}


@pytest.fixture(autouse=True)
def clear_languages_cache():
    load_languages.cache_clear()
    yield
    load_languages.cache_clear()


class TestListLanguagesService:
    @pytest.mark.asyncio
    async def test_list_languages_enabled_only_by_default(self):
        with patch.object(
            language_service,
            "load_languages",
            return_value=SAMPLE_LANGUAGES,
        ):
            response = await list_languages_service()

        assert len(response.languages) == 2
        assert [lang.code for lang in response.languages] == ["en", "zh"]
        assert all(lang.enabled for lang in response.languages)

    @pytest.mark.asyncio
    async def test_list_languages_includes_disabled_when_requested(self):
        with patch.object(
            language_service,
            "load_languages",
            return_value=SAMPLE_LANGUAGES,
        ):
            response = await list_languages_service(enabled_only=False)

        assert len(response.languages) == 3
        assert [lang.code for lang in response.languages] == ["en", "bo", "zh"]
        assert response.languages[1].enabled is False

    @pytest.mark.asyncio
    async def test_list_languages_defaults_enabled_when_missing(self):
        with patch.object(
            language_service,
            "load_languages",
            return_value=SAMPLE_LANGUAGES,
        ):
            response = await list_languages_service(enabled_only=False)

        chinese = next(lang for lang in response.languages if lang.code == "zh")
        assert chinese.enabled is True

    @pytest.mark.asyncio
    async def test_list_languages_empty_when_payload_missing_languages_key(self):
        with patch.object(language_service, "load_languages", return_value={}):
            response = await list_languages_service()

        assert response.languages == []

    @pytest.mark.asyncio
    async def test_list_languages_recitation_only_uses_openpecha_category_languages(self):
        with patch.object(
            language_service,
            "load_languages",
            return_value=SAMPLE_LANGUAGES,
        ), patch.object(
            language_service, "get_cache_data", return_value=None
        ), patch.object(
            language_service, "set_cache", return_value=True
        ), patch.object(
            language_service, "get_config", return_value="test-category-id"
        ), patch.object(
            language_service,
            "fetch_texts_by_category",
        ) as mock_fetch:
            mock_fetch.return_value = {
                "items": [
                    {"id": "t1", "language": "en"},
                    {"id": "t2", "language": "bo"},
                    {"id": "t3", "language": "en"},
                ],
                "has_more": False,
            }

            response = await list_languages_service(recitation_only=True)

        assert [lang.code for lang in response.languages] == ["en", "bo"]
        assert response.languages[0].name == "English"
        assert response.languages[1].name == "Tibetan"
        mock_fetch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_languages_recitation_only_falls_back_to_code_when_unmapped(self):
        with patch.object(
            language_service,
            "load_languages",
            return_value=SAMPLE_LANGUAGES,
        ), patch.object(
            language_service, "get_cache_data", return_value=None
        ), patch.object(
            language_service, "set_cache", return_value=True
        ), patch.object(
            language_service, "get_config", return_value="test-category-id"
        ), patch.object(
            language_service,
            "fetch_texts_by_category",
            return_value={"items": [{"id": "t1", "language": "sa"}], "has_more": False},
        ):
            response = await list_languages_service(recitation_only=True)

        assert len(response.languages) == 1
        assert response.languages[0].code == "sa"
        assert response.languages[0].name == "sa"

    @pytest.mark.asyncio
    async def test_list_languages_recitation_only_paginates_until_no_more(self):
        with patch.object(
            language_service,
            "load_languages",
            return_value=SAMPLE_LANGUAGES,
        ), patch.object(
            language_service, "get_cache_data", return_value=None
        ), patch.object(
            language_service, "set_cache", return_value=True
        ), patch.object(
            language_service, "get_config", return_value="test-category-id"
        ), patch.object(
            language_service, "fetch_texts_by_category"
        ) as mock_fetch:
            mock_fetch.side_effect = [
                {"items": [{"id": "t1", "language": "en"}], "has_more": True},
                {"items": [{"id": "t2", "language": "bo"}], "has_more": False},
            ]

            response = await list_languages_service(recitation_only=True)

        assert [lang.code for lang in response.languages] == ["en", "bo"]
        assert mock_fetch.await_count == 2

    @pytest.mark.asyncio
    async def test_list_languages_recitation_only_uses_cache_when_present(self):
        with patch.object(
            language_service,
            "load_languages",
            return_value=SAMPLE_LANGUAGES,
        ), patch.object(
            language_service, "get_cache_data", return_value=["bo"]
        ), patch.object(
            language_service, "get_config", return_value="test-category-id"
        ), patch.object(
            language_service, "fetch_texts_by_category"
        ) as mock_fetch:
            response = await list_languages_service(recitation_only=True)

        assert [lang.code for lang in response.languages] == ["bo"]
        mock_fetch.assert_not_awaited()


class TestLoadLanguages:
    def test_load_languages_raises_when_file_missing(self, tmp_path: Path):
        missing_file = tmp_path / "missing_languages.json"

        with patch.object(language_service, "LANGUAGES_JSON_PATH", missing_file):
            with pytest.raises(HTTPException) as exc_info:
                load_languages()

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc_info.value.detail == "Languages configuration is not available"

    def test_load_languages_reads_json_file(self, tmp_path: Path):
        languages_file = tmp_path / "languages.json"
        languages_file.write_text(
            '{"languages":[{"code":"en","name":"English","native_name":"English","enabled":true}]}',
            encoding="utf-8",
        )

        with patch.object(language_service, "LANGUAGES_JSON_PATH", languages_file):
            payload = load_languages()

        assert payload["languages"][0]["code"] == "en"


class TestListLanguagesEndpoint:
    def test_get_languages_returns_enabled_by_default(self):
        mock_response = LanguageListResponse(
            languages=[
                LanguageDTO(
                    code="en",
                    name="English",
                    native_name="English",
                    enabled=True,
                )
            ]
        )

        with patch(
            "pecha_api.languages.language_views.list_languages_service",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_service:
            response = client.get("/languages")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["languages"] == [
            {
                "code": "en",
                "name": "English",
                "native_name": "English",
                "enabled": True,
            }
        ]
        mock_service.assert_called_once_with(enabled_only=True, recitation_only=False)

    def test_get_languages_passes_enabled_only_false(self):
        mock_response = LanguageListResponse(languages=[])

        with patch(
            "pecha_api.languages.language_views.list_languages_service",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_service:
            response = client.get("/languages?enabled_only=false")

        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(enabled_only=False, recitation_only=False)

    def test_get_languages_passes_recitation_only_true(self):
        mock_response = LanguageListResponse(languages=[])

        with patch(
            "pecha_api.languages.language_views.list_languages_service",
            new_callable=AsyncMock,
            return_value=mock_response,
        ) as mock_service:
            response = client.get("/languages?recitation_only=true")

        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(enabled_only=True, recitation_only=True)

    def test_get_languages_integration_returns_real_data(self):
        response = client.get("/languages")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "languages" in body
        assert len(body["languages"]) >= 1
        assert {"code", "name", "native_name", "enabled"} <= set(body["languages"][0])


class TestLanguageCodeSync:
    def test_language_code_enum_matches_languages_json(self):
        payload = load_languages()
        json_codes = {
            entry["code"].upper()
            for entry in payload.get("languages", [])
        }
        enum_codes = {code.value for code in LanguageCode}

        assert enum_codes == json_codes, (
            "LanguageCode enum must match pecha_api/languages/languages.json. "
            f"Missing in enum: {sorted(json_codes - enum_codes)}. "
            f"Extra in enum: {sorted(enum_codes - json_codes)}."
        )
