from unittest.mock import patch

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


@patch(
    "pecha_api.plans.audio.tts_test_views.generate_tts_audio",
    return_value=b"RIFF" + b"\x00" * 40,
)
def test_preview_tts_returns_wav(mock_generate):
    response = _post_tts_preview(language="en", type="TEXT_READING")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content[:4] == b"RIFF"
    mock_generate.assert_called_once()


@patch(
    "pecha_api.plans.audio.tts_test_views.generate_tts_audio",
    side_effect=RuntimeError("TTS generation returned no audio data"),
)
def test_preview_tts_returns_502_for_runtime_error(mock_generate):
    response = _post_tts_preview(language="en")

    assert response.status_code == 502
    assert "no audio data" in response.json()["detail"]


@patch(
    "pecha_api.plans.audio.tts_test_views.generate_tts_audio",
    return_value=b"RIFF" + b"\x00" * 40,
)
def test_preview_tts_returns_wav_for_non_tibetan_language(mock_generate):
    response = _post_tts_preview(language="zh", type="TEXT_READING")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    mock_generate.assert_called_once()


@patch(
    "pecha_api.plans.audio.tts_test_views.generate_tts_audio",
    side_effect=ValueError("Content cannot be empty"),
)
def test_preview_tts_returns_400_for_validation_error(mock_generate):
    response = client.post("/preview", json={"text": "   ", "language": "en"})

    assert response.status_code == 400
    assert "Content cannot be empty" in response.json()["detail"]


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
