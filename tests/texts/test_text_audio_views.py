from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.texts import text_audio_views
from pecha_api.texts.text_audio_models import TextAudioResponse

VIEWS = "pecha_api.texts.text_audio_views"

VALID_TOKEN = "valid_token"
TEXT_ID = "text-123"
AUDIO_KEY = "audio/texts/chant.mp3"
AUDIO_ENDPOINT = f"/cms/texts/{TEXT_ID}/audio"


def _audio_response() -> TextAudioResponse:
    return TextAudioResponse(
        text_id=TEXT_ID,
        text_title="Heart Sutra",
        audio_key=AUDIO_KEY,
        audio_url=f"https://cdn.test/{AUDIO_KEY}",
        file_name="chant.mp3",
        mime_type="audio/mpeg",
        file_size_bytes=2048,
        duration_ms=90000,
        updated_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )


def _audio_file(filename: str = "chant.mp3", content_type: str = "audio/mpeg") -> dict:
    return {"file": (filename, b"fake audio bytes", content_type)}


@pytest.fixture
def audio_app():
    app = FastAPI()
    app.include_router(text_audio_views.text_audio_router)
    return app


@pytest.fixture
def authenticated_client(audio_app):
    audio_app.dependency_overrides[text_audio_views.oauth2_scheme] = lambda: (
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=VALID_TOKEN)
    )

    yield TestClient(audio_app)

    audio_app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client(audio_app):
    return TestClient(audio_app)


class TestFetchTextAudio:
    def test_stored_audio_is_returned(self, authenticated_client):
        with patch(f"{VIEWS}.get_text_audio", new_callable=AsyncMock) as fetch:
            fetch.return_value = _audio_response()

            response = authenticated_client.get(AUDIO_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["audio_key"] == AUDIO_KEY
        fetch.assert_awaited_once_with(token=VALID_TOKEN, text_id=TEXT_ID)

    def test_null_is_returned_when_a_text_has_no_audio(self, authenticated_client):
        with patch(f"{VIEWS}.get_text_audio", new_callable=AsyncMock) as fetch:
            fetch.return_value = None

            response = authenticated_client.get(AUDIO_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() is None

    def test_missing_text_returns_not_found(self, authenticated_client):
        with patch(f"{VIEWS}.get_text_audio", new_callable=AsyncMock) as fetch:
            fetch.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found.",
            )

            response = authenticated_client.get(AUDIO_ENDPOINT)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_request_without_a_token_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.get(AUDIO_ENDPOINT)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestReplaceTextAudio:
    def test_upload_returns_created(self, authenticated_client):
        with patch(f"{VIEWS}.upload_text_audio", new_callable=AsyncMock) as upload:
            upload.return_value = _audio_response()

            response = authenticated_client.post(
                AUDIO_ENDPOINT,
                files=_audio_file(),
                data={"duration_ms": 90000},
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["audio_url"] == f"https://cdn.test/{AUDIO_KEY}"
        assert upload.await_args.kwargs["token"] == VALID_TOKEN
        assert upload.await_args.kwargs["text_id"] == TEXT_ID
        assert upload.await_args.kwargs["duration_ms"] == 90000

    def test_duration_is_optional(self, authenticated_client):
        with patch(f"{VIEWS}.upload_text_audio", new_callable=AsyncMock) as upload:
            upload.return_value = _audio_response()

            response = authenticated_client.post(AUDIO_ENDPOINT, files=_audio_file())

        assert response.status_code == status.HTTP_201_CREATED
        assert upload.await_args.kwargs["duration_ms"] is None

    def test_missing_file_is_rejected(self, authenticated_client):
        response = authenticated_client.post(AUDIO_ENDPOINT)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_unsupported_file_error_is_surfaced(self, authenticated_client):
        with patch(f"{VIEWS}.upload_text_audio", new_callable=AsyncMock) as upload:
            upload.side_effect = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported audio file. Use MP3, M4A, WAV, AAC, or OGG.",
            )

            response = authenticated_client.post(
                AUDIO_ENDPOINT,
                files=_audio_file(filename="notes.pdf", content_type="application/pdf"),
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_request_without_a_token_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.post(AUDIO_ENDPOINT, files=_audio_file())

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRemoveTextAudio:
    def test_delete_returns_no_content(self, authenticated_client):
        with patch(f"{VIEWS}.delete_text_audio", new_callable=AsyncMock) as remove:
            remove.return_value = None

            response = authenticated_client.delete(AUDIO_ENDPOINT)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not response.content
        remove.assert_awaited_once_with(token=VALID_TOKEN, text_id=TEXT_ID)

    def test_missing_text_returns_not_found(self, authenticated_client):
        with patch(f"{VIEWS}.delete_text_audio", new_callable=AsyncMock) as remove:
            remove.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found.",
            )

            response = authenticated_client.delete(AUDIO_ENDPOINT)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_request_without_a_token_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.delete(AUDIO_ENDPOINT)

        assert response.status_code == status.HTTP_403_FORBIDDEN
