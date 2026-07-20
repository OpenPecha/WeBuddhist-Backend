from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.languages import language_service
from pecha_api.languages.language_response_models import LanguageDTO, LanguageListResponse
from pecha_api.languages.language_service import list_languages_service, load_languages

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
    def test_list_languages_enabled_only_by_default(self):
        with patch.object(
            language_service,
            "load_languages",
            return_value=SAMPLE_LANGUAGES,
        ):
            response = list_languages_service()

        assert len(response.languages) == 2
        assert [lang.code for lang in response.languages] == ["en", "zh"]
        assert all(lang.enabled for lang in response.languages)

    def test_list_languages_includes_disabled_when_requested(self):
        with patch.object(
            language_service,
            "load_languages",
            return_value=SAMPLE_LANGUAGES,
        ):
            response = list_languages_service(enabled_only=False)

        assert len(response.languages) == 3
        assert [lang.code for lang in response.languages] == ["en", "bo", "zh"]
        assert response.languages[1].enabled is False

    def test_list_languages_defaults_enabled_when_missing(self):
        with patch.object(
            language_service,
            "load_languages",
            return_value=SAMPLE_LANGUAGES,
        ):
            response = list_languages_service(enabled_only=False)

        chinese = next(lang for lang in response.languages if lang.code == "zh")
        assert chinese.enabled is True

    def test_list_languages_empty_when_payload_missing_languages_key(self):
        with patch.object(language_service, "load_languages", return_value={}):
            response = list_languages_service()

        assert response.languages == []


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
        mock_service.assert_called_once_with(enabled_only=True)

    def test_get_languages_passes_enabled_only_false(self):
        mock_response = LanguageListResponse(languages=[])

        with patch(
            "pecha_api.languages.language_views.list_languages_service",
            return_value=mock_response,
        ) as mock_service:
            response = client.get("/languages?enabled_only=false")

        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once_with(enabled_only=False)

    def test_get_languages_integration_returns_real_data(self):
        response = client.get("/languages")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert "languages" in body
        assert len(body["languages"]) >= 1
        assert {"code", "name", "native_name", "enabled"} <= set(body["languages"][0])
