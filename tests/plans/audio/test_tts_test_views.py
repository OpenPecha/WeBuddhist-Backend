from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from pecha_api.app import api

client = TestClient(api)


def test_tts_test_view_returns_html():
    response = client.get("/view")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TTS Test" in response.text


@patch(
    "pecha_api.plans.audio.tts_test_views.generate_tts_audio",
    return_value=b"RIFF" + b"\x00" * 40,
)
def test_preview_tts_returns_wav(mock_generate):
    response = client.post(
        "/preview",
        json={
            "text": "Hello",
            "language": "en",
            "type": "TEXT_READING",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content[:4] == b"RIFF"
    mock_generate.assert_called_once()


@patch(
    "pecha_api.plans.audio.tts_test_views.generate_tts_audio",
    side_effect=ValueError("Unsupported language for TTS: zh"),
)
def test_preview_tts_returns_400_for_validation_error(mock_generate):
    response = client.post(
        "/preview",
        json={
            "text": "Hello",
            "language": "zh",
        },
    )

    assert response.status_code == 400
    assert "Unsupported language" in response.json()["detail"]


@patch(
    "pecha_api.plans.audio.tts_test_views.generate_tts_audio",
    side_effect=RuntimeError("GEMINI_API_KEY is not configured"),
)
def test_preview_tts_returns_502_for_runtime_error(mock_generate):
    response = client.post(
        "/preview",
        json={
            "text": "Hello",
            "language": "en",
        },
    )

    assert response.status_code == 502
    assert "GEMINI_API_KEY" in response.json()["detail"]
