from unittest.mock import MagicMock, patch

import httpx
import pytest

from pecha_api.plans.audio.monlam_tts_service import generate_monlam_tts_audio


def test_generate_monlam_tts_audio_rejects_empty_content():
    with pytest.raises(ValueError, match="Content cannot be empty"):
        generate_monlam_tts_audio("   ")


@patch("pecha_api.plans.audio.monlam_tts_service.get")
@patch("pecha_api.plans.audio.monlam_tts_service.httpx.post")
def test_generate_monlam_tts_audio_success(mock_post, mock_get):
    mock_get.side_effect = lambda key: {
        "MONLAM_BASE_URL": "https://new-stag.monlam.ai",
        "MONLAM_API_KEY": "monlam_test_key",
        "MONLAM_TTS_VOICE_NAME": "dolkar_lhasa_female",
        "MONLAM_TTS_PROVIDER": "monlamai",
        "MONLAM_TTS_MODEL_NAME": "monlamai-tts",
    }[key]

    wav_bytes = b"RIFF" + b"\x00" * 40
    mock_response = MagicMock()
    mock_response.content = wav_bytes
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    result = generate_monlam_tts_audio("བཀྲ་ཤིས་བདེ་ལེགས")

    assert result == wav_bytes
    mock_post.assert_called_once_with(
        "https://new-stag.monlam.ai/api/v1/text-to-speech/stream",
        headers={
            "X-API-Key": "monlam_test_key",
            "Content-Type": "application/json",
        },
        json={
            "text": "བཀྲ་ཤིས་བདེ་ལེགས",
            "provider": "monlamai",
            "model_name": "monlamai-tts",
            "voice_name": "dolkar_lhasa_female",
        },
        timeout=300.0,
    )


@patch("pecha_api.plans.audio.monlam_tts_service.get")
@patch("pecha_api.plans.audio.monlam_tts_service.httpx.post")
def test_generate_monlam_tts_audio_uses_request_voice_name(mock_post, mock_get):
    mock_get.side_effect = lambda key: {
        "MONLAM_BASE_URL": "https://new-stag.monlam.ai",
        "MONLAM_API_KEY": "monlam_test_key",
        "MONLAM_TTS_VOICE_NAME": "dolkar_lhasa_female",
        "MONLAM_TTS_PROVIDER": "monlamai",
        "MONLAM_TTS_MODEL_NAME": "monlamai-tts",
    }[key]

    mock_response = MagicMock()
    mock_response.content = b"RIFF" + b"\x00" * 40
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    generate_monlam_tts_audio("བཀྲ་ཤིས་བདེ་ལེགས", voice_name="yangchen_lhasa_female")

    assert mock_post.call_args.kwargs["json"]["voice_name"] == "yangchen_lhasa_female"


@patch("pecha_api.plans.audio.monlam_tts_service.get")
def test_generate_monlam_tts_audio_requires_api_key(mock_get):
    mock_get.side_effect = lambda key: {
        "MONLAM_BASE_URL": "https://new-stag.monlam.ai",
        "MONLAM_API_KEY": "",
        "MONLAM_TTS_VOICE_NAME": "dolkar_lhasa_female",
        "MONLAM_TTS_PROVIDER": "monlamai",
        "MONLAM_TTS_MODEL_NAME": "monlamai-tts",
    }[key]

    with pytest.raises(RuntimeError, match="MONLAM_API_KEY is not configured"):
        generate_monlam_tts_audio("བཀྲ་ཤིས་བདེ་ལེགས")


@patch("pecha_api.plans.audio.monlam_tts_service.get")
@patch("pecha_api.plans.audio.monlam_tts_service.httpx.post")
def test_generate_monlam_tts_audio_raises_on_http_error(mock_post, mock_get):
    mock_get.side_effect = lambda key: {
        "MONLAM_BASE_URL": "https://new-stag.monlam.ai",
        "MONLAM_API_KEY": "monlam_test_key",
        "MONLAM_TTS_VOICE_NAME": "dolkar_lhasa_female",
        "MONLAM_TTS_PROVIDER": "monlamai",
        "MONLAM_TTS_MODEL_NAME": "monlamai-tts",
    }[key]

    mock_response = MagicMock()
    mock_response.status_code = 402
    mock_response.text = "Payment Required"
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Payment Required",
        request=MagicMock(),
        response=mock_response,
    )
    mock_post.return_value = mock_response

    with pytest.raises(RuntimeError, match="Monlam TTS request failed with status 402"):
        generate_monlam_tts_audio("བཀྲ་ཤིས་བདེ་ལེགས")


@patch("pecha_api.plans.audio.monlam_tts_service.get")
@patch("pecha_api.plans.audio.monlam_tts_service.httpx.post")
def test_generate_monlam_tts_audio_raises_on_invalid_response(mock_post, mock_get):
    mock_get.side_effect = lambda key: {
        "MONLAM_BASE_URL": "https://new-stag.monlam.ai",
        "MONLAM_API_KEY": "monlam_test_key",
        "MONLAM_TTS_VOICE_NAME": "dolkar_lhasa_female",
        "MONLAM_TTS_PROVIDER": "monlamai",
        "MONLAM_TTS_MODEL_NAME": "monlamai-tts",
    }[key]

    mock_response = MagicMock()
    mock_response.content = b"not-a-wav"
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    with pytest.raises(RuntimeError, match="invalid audio data"):
        generate_monlam_tts_audio("བཀྲ་ཤིས་བདེ་ལེགས")
