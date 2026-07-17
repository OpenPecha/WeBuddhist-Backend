from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from pecha_api.app import api

client = TestClient(api)


def _post_tts_preview(**payload):
    return client.post("/preview", json={"text": "Hello", **payload})


def test_tts_test_view_returns_html():
    response = client.get("/view")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TTS Test" in response.text
    assert "worker API" in response.text


@patch(
    "pecha_api.plans.audio.tts_test_views.generate_audio_from_text",
    new_callable=AsyncMock,
    return_value={
        "audio_url": "https://s3.example.com/preview.wav",
        "audio_duration_ms": 1500,
        "s3_key": "audio/tts-preview/preview.wav",
    },
)
def test_preview_tts_returns_worker_audio_metadata(mock_generate):
    response = _post_tts_preview(language="en", type="TEXT_READING")

    assert response.status_code == 200
    body = response.json()
    assert body["audio_url"] == "https://s3.example.com/preview.wav"
    assert body["audio_duration_ms"] == 1500
    assert body["s3_key"] == "audio/tts-preview/preview.wav"
    mock_generate.assert_awaited_once()


@patch(
    "pecha_api.plans.audio.tts_test_views.generate_audio_from_text",
    new_callable=AsyncMock,
    side_effect=RuntimeError("Worker TTS request failed"),
)
def test_preview_tts_returns_502_for_runtime_error(mock_generate):
    response = _post_tts_preview(language="en")

    assert response.status_code == 502
    assert "Worker TTS request failed" in response.json()["detail"]


@patch(
    "pecha_api.plans.audio.tts_test_views.generate_audio_from_text",
    new_callable=AsyncMock,
    return_value={
        "audio_url": "https://s3.example.com/zh.wav",
        "audio_duration_ms": 900,
        "s3_key": "audio/tts-preview/zh.wav",
    },
)
def test_preview_tts_supports_non_tibetan_language(mock_generate):
    response = _post_tts_preview(language="zh", type="TEXT_READING")

    assert response.status_code == 200
    assert response.json()["audio_url"] == "https://s3.example.com/zh.wav"
    mock_generate.assert_awaited_once()


def test_preview_tts_returns_400_for_empty_text():
    response = client.post("/preview", json={"text": "   ", "language": "en"})

    assert response.status_code == 400
    assert "Content cannot be empty" in response.json()["detail"]
