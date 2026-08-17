from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.texts import text_audio_views
from pecha_api.texts.text_audio_models import TextAudioOtrResponse, TextAudioResponse

VIEWS = "pecha_api.texts.text_audio_views"

VALID_TOKEN = "valid_token"
TEXT_ID = "text-123"
AUDIO_ID = "64b000000000000000000001"
OTR_ID = "64b000000000000000000002"
AUDIO_KEY = "audio/texts/chant.mp3"
AUDIOS_ENDPOINT = f"/cms/texts/{TEXT_ID}/audios"
AUDIO_ENDPOINT = f"{AUDIOS_ENDPOINT}/{AUDIO_ID}"
OTRS_ENDPOINT = f"{AUDIO_ENDPOINT}/otr"
OTR_ENDPOINT = f"{OTRS_ENDPOINT}/{OTR_ID}"

OTR_CONTENT = {"text": "<p>transcript</p>", "media": "", "media-time": ""}


def _audio_response() -> TextAudioResponse:
    return TextAudioResponse(
        id=AUDIO_ID,
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


def _otr_response() -> TextAudioOtrResponse:
    return TextAudioOtrResponse(
        id=OTR_ID,
        audio_id=AUDIO_ID,
        name="228",
        file_name="228.otr",
        updated_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )


def _audio_file(filename: str = "chant.mp3", content_type: str = "audio/mpeg") -> dict:
    return {"file": (filename, b"fake audio bytes", content_type)}


def _otr_file(filename: str = "228.otr", content: bytes = b'{"text": "hi"}') -> dict:
    return {"file": (filename, content, "application/json")}


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


class TestFetchTextAudios:
    def test_stored_audios_are_returned(self, authenticated_client):
        with patch(f"{VIEWS}.get_text_audios", new_callable=AsyncMock) as fetch:
            fetch.return_value = [_audio_response()]

            response = authenticated_client.get(AUDIOS_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()[0]["id"] == AUDIO_ID
        assert response.json()[0]["audio_key"] == AUDIO_KEY
        fetch.assert_awaited_once_with(token=VALID_TOKEN, text_id=TEXT_ID)

    def test_empty_list_is_returned_when_a_text_has_no_audio(self, authenticated_client):
        with patch(f"{VIEWS}.get_text_audios", new_callable=AsyncMock) as fetch:
            fetch.return_value = []

            response = authenticated_client.get(AUDIOS_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_missing_text_returns_not_found(self, authenticated_client):
        with patch(f"{VIEWS}.get_text_audios", new_callable=AsyncMock) as fetch:
            fetch.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Text not found.",
            )

            response = authenticated_client.get(AUDIOS_ENDPOINT)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_request_without_a_token_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.get(AUDIOS_ENDPOINT)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAddTextAudio:
    def test_upload_returns_created(self, authenticated_client):
        with patch(f"{VIEWS}.upload_text_audio", new_callable=AsyncMock) as upload:
            upload.return_value = _audio_response()

            response = authenticated_client.post(
                AUDIOS_ENDPOINT,
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

            response = authenticated_client.post(AUDIOS_ENDPOINT, files=_audio_file())

        assert response.status_code == status.HTTP_201_CREATED
        assert upload.await_args.kwargs["duration_ms"] is None

    def test_missing_file_is_rejected(self, authenticated_client):
        response = authenticated_client.post(AUDIOS_ENDPOINT)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_unsupported_file_error_is_surfaced(self, authenticated_client):
        with patch(f"{VIEWS}.upload_text_audio", new_callable=AsyncMock) as upload:
            upload.side_effect = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported audio file. Use MP3, M4A, WAV, AAC, or OGG.",
            )

            response = authenticated_client.post(
                AUDIOS_ENDPOINT,
                files=_audio_file(filename="notes.pdf", content_type="application/pdf"),
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_request_without_a_token_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.post(AUDIOS_ENDPOINT, files=_audio_file())

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRemoveTextAudio:
    def test_delete_returns_no_content(self, authenticated_client):
        with patch(f"{VIEWS}.delete_text_audio", new_callable=AsyncMock) as remove:
            remove.return_value = None

            response = authenticated_client.delete(AUDIO_ENDPOINT)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not response.content
        remove.assert_awaited_once_with(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            audio_id=AUDIO_ID,
        )

    def test_missing_audio_returns_not_found(self, authenticated_client):
        with patch(f"{VIEWS}.delete_text_audio", new_callable=AsyncMock) as remove:
            remove.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio not found.",
            )

            response = authenticated_client.delete(AUDIO_ENDPOINT)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_request_without_a_token_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.delete(AUDIO_ENDPOINT)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestFetchTextAudioOtrs:
    def test_stored_otrs_are_returned(self, authenticated_client):
        with patch(f"{VIEWS}.get_text_audio_otrs", new_callable=AsyncMock) as fetch:
            fetch.return_value = [_otr_response()]

            response = authenticated_client.get(OTRS_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()[0]["name"] == "228"
        fetch.assert_awaited_once_with(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            audio_id=AUDIO_ID,
        )

    def test_missing_audio_returns_not_found(self, authenticated_client):
        with patch(f"{VIEWS}.get_text_audio_otrs", new_callable=AsyncMock) as fetch:
            fetch.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio not found.",
            )

            response = authenticated_client.get(OTRS_ENDPOINT)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_request_without_a_token_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.get(OTRS_ENDPOINT)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestAddTextAudioOtr:
    def test_upload_returns_created(self, authenticated_client):
        with patch(f"{VIEWS}.upload_text_audio_otr", new_callable=AsyncMock) as upload:
            upload.return_value = _otr_response()

            response = authenticated_client.post(
                OTRS_ENDPOINT,
                files=_otr_file(),
                data={"name": "228"},
            )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["name"] == "228"
        assert upload.await_args.kwargs["token"] == VALID_TOKEN
        assert upload.await_args.kwargs["text_id"] == TEXT_ID
        assert upload.await_args.kwargs["audio_id"] == AUDIO_ID
        assert upload.await_args.kwargs["name"] == "228"

    def test_name_is_optional(self, authenticated_client):
        with patch(f"{VIEWS}.upload_text_audio_otr", new_callable=AsyncMock) as upload:
            upload.return_value = _otr_response()

            response = authenticated_client.post(OTRS_ENDPOINT, files=_otr_file())

        assert response.status_code == status.HTTP_201_CREATED
        assert upload.await_args.kwargs["name"] is None

    def test_missing_file_is_rejected(self, authenticated_client):
        response = authenticated_client.post(OTRS_ENDPOINT)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_invalid_otr_error_is_surfaced(self, authenticated_client):
        with patch(f"{VIEWS}.upload_text_audio_otr", new_callable=AsyncMock) as upload:
            upload.side_effect = HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Upload a valid OTR/JSON file.",
            )

            response = authenticated_client.post(
                OTRS_ENDPOINT,
                files=_otr_file(content=b"not json"),
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Upload a valid OTR/JSON file."

    def test_duplicate_name_conflict_is_surfaced(self, authenticated_client):
        with patch(f"{VIEWS}.upload_text_audio_otr", new_callable=AsyncMock) as upload:
            upload.side_effect = HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An OTR with this name already exists for this audio.",
            )

            response = authenticated_client.post(OTRS_ENDPOINT, files=_otr_file())

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_request_without_a_token_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.post(OTRS_ENDPOINT, files=_otr_file())

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestFetchTextAudioOtrJson:
    def test_otr_content_is_returned_as_json(self, authenticated_client):
        with patch(
            f"{VIEWS}.get_text_audio_otr_content", new_callable=AsyncMock
        ) as fetch:
            fetch.return_value = OTR_CONTENT

            response = authenticated_client.get(OTR_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == OTR_CONTENT
        fetch.assert_awaited_once_with(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            audio_id=AUDIO_ID,
            otr_id=OTR_ID,
        )

    def test_missing_otr_returns_not_found(self, authenticated_client):
        with patch(
            f"{VIEWS}.get_text_audio_otr_content", new_callable=AsyncMock
        ) as fetch:
            fetch.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OTR not found.",
            )

            response = authenticated_client.get(OTR_ENDPOINT)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_request_without_a_token_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.get(OTR_ENDPOINT)

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestRemoveTextAudioOtr:
    def test_delete_returns_no_content(self, authenticated_client):
        with patch(f"{VIEWS}.delete_text_audio_otr", new_callable=AsyncMock) as remove:
            remove.return_value = None

            response = authenticated_client.delete(OTR_ENDPOINT)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not response.content
        remove.assert_awaited_once_with(
            token=VALID_TOKEN,
            text_id=TEXT_ID,
            audio_id=AUDIO_ID,
            otr_id=OTR_ID,
        )

    def test_missing_otr_returns_not_found(self, authenticated_client):
        with patch(f"{VIEWS}.delete_text_audio_otr", new_callable=AsyncMock) as remove:
            remove.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OTR not found.",
            )

            response = authenticated_client.delete(OTR_ENDPOINT)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_request_without_a_token_is_rejected(self, unauthenticated_client):
        response = unauthenticated_client.delete(OTR_ENDPOINT)

        assert response.status_code == status.HTTP_403_FORBIDDEN
