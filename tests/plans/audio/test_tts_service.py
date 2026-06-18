from unittest.mock import MagicMock, patch

import pytest

from pecha_api.plans.audio.tts_service import (
    _convert_to_wav,
    _normalize_language,
    _parse_audio_mime_type,
    generate_tts_audio,
)
from pecha_api.plans.plans_enums import PlanAudioType

_EN_RECITATION = {
    "content": "Hello world",
    "audio_type": PlanAudioType.RECITATION,
    "language": "en",
}


def _configure_gemini_client(mock_client_cls, response):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = response
    mock_client_cls.return_value = mock_client
    return mock_client


def _build_gemini_audio_response(*, audio_data=b"\x00\x01\x02\x03", inline_data=None):
    if inline_data is None:
        inline_data = MagicMock(data=audio_data, mime_type="audio/L16;rate=24000")
    part = MagicMock(inline_data=inline_data)
    content = MagicMock(parts=[part])
    candidate = MagicMock(content=content)
    return MagicMock(candidates=[candidate])


def test_normalize_language():
    assert _normalize_language("EN") == "en"
    assert _normalize_language(" bo ") == "bo"
    assert _normalize_language("") == "en"


def test_parse_audio_mime_type_defaults():
    result = _parse_audio_mime_type("audio/L16;rate=24000")
    assert result == {"bits_per_sample": 16, "rate": 24000}


def test_parse_audio_mime_type_custom_rate_and_bits():
    result = _parse_audio_mime_type("audio/L8;rate=44100")
    assert result == {"bits_per_sample": 8, "rate": 44100}


def test_parse_audio_mime_type_invalid_values_use_defaults():
    result = _parse_audio_mime_type("audio/Lbad;rate=not-a-number")
    assert result == {"bits_per_sample": 16, "rate": 24000}


def test_convert_to_wav_produces_valid_header():
    audio_data = b"\x00\x01\x02\x03"
    wav_bytes = _convert_to_wav(audio_data, "audio/L16;rate=24000")

    assert wav_bytes[:4] == b"RIFF"
    assert wav_bytes[8:12] == b"WAVE"
    assert wav_bytes[-4:] == audio_data


def test_generate_tts_audio_rejects_empty_content():
    with pytest.raises(ValueError, match="Content cannot be empty"):
        generate_tts_audio(content="   ", audio_type=PlanAudioType.RECITATION)


def test_generate_tts_audio_rejects_unsupported_language():
    with pytest.raises(ValueError, match="Unsupported language for TTS"):
        generate_tts_audio(
            content="Hello",
            audio_type=PlanAudioType.RECITATION,
            language="zh",
        )


@patch("pecha_api.plans.audio.tts_service.generate_monlam_tts_audio")
def test_generate_tts_audio_routes_bo_to_monlam(mock_monlam):
    mock_monlam.return_value = b"RIFF" + b"\x00" * 40

    result = generate_tts_audio(
        content="བཀྲ་ཤིས་བདེ་ལེགས",
        audio_type=PlanAudioType.TEXT_READING,
        language="bo",
    )

    mock_monlam.assert_called_once_with(
        "བཀྲ་ཤིས་བདེ་ལེགས",
        voice_name=None,
    )
    assert result[:4] == b"RIFF"


@patch("pecha_api.plans.audio.tts_service.generate_monlam_tts_audio")
def test_generate_tts_audio_passes_voice_name_to_monlam(mock_monlam):
    mock_monlam.return_value = b"RIFF" + b"\x00" * 40

    generate_tts_audio(
        content="བཀྲ་ཤིས་བདེ་ལེགས",
        audio_type=PlanAudioType.TEXT_READING,
        language="bo",
        voice_name="yangchen_lhasa_female",
    )

    mock_monlam.assert_called_once_with(
        "བཀྲ་ཤིས་བདེ་ལེགས",
        voice_name="yangchen_lhasa_female",
    )


@patch("google.genai.Client")
@patch("pecha_api.plans.audio.tts_service.get", return_value="test-api-key")
def test_generate_tts_audio_routes_en_to_gemini(mock_get, mock_client_cls):
    audio_data = b"\x00\x01\x02\x03"
    _configure_gemini_client(mock_client_cls, _build_gemini_audio_response(audio_data=audio_data))

    result = generate_tts_audio(**_EN_RECITATION)

    assert result[:4] == b"RIFF"
    assert result.endswith(audio_data)


@patch("google.genai.Client")
@patch("pecha_api.plans.audio.tts_service.get", return_value=None)
def test_generate_tts_audio_raises_when_api_key_missing(mock_get, mock_client_cls):
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not configured"):
        generate_tts_audio(**_EN_RECITATION)
    mock_client_cls.assert_not_called()


@patch("google.genai.Client")
@patch("pecha_api.plans.audio.tts_service.get", return_value="test-api-key")
def test_generate_tts_audio_raises_when_no_inline_data(mock_get, mock_client_cls):
    inline_data = MagicMock(data=None, mime_type="audio/L16;rate=24000")
    _configure_gemini_client(
        mock_client_cls,
        _build_gemini_audio_response(inline_data=inline_data),
    )

    with pytest.raises(RuntimeError, match="no audio data"):
        generate_tts_audio(**_EN_RECITATION)


@patch("pecha_api.plans.audio.tts_service.get", return_value=None)
def test_generate_tts_audio_raises_when_gemini_key_missing(mock_get):
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY is not configured"):
        generate_tts_audio(
            content="Hello world",
            audio_type=PlanAudioType.RECITATION,
            language="en",
        )


@patch("google.genai.Client")
@patch("pecha_api.plans.audio.tts_service.get", return_value="test-api-key")
def test_generate_tts_audio_raises_when_no_candidates(mock_get, mock_client_cls):
    _configure_gemini_client(mock_client_cls, MagicMock(candidates=[]))

    with pytest.raises(RuntimeError, match="no audio data"):
        generate_tts_audio(**_EN_RECITATION)


@patch("google.genai.Client")
@patch("pecha_api.plans.audio.tts_service.get", return_value="test-api-key")
def test_generate_tts_audio_raises_when_candidate_content_is_none(mock_get, mock_client_cls):
    candidate = MagicMock(content=None)
    _configure_gemini_client(mock_client_cls, MagicMock(candidates=[candidate]))

    with pytest.raises(RuntimeError, match="no audio data"):
        generate_tts_audio(**_EN_RECITATION)
