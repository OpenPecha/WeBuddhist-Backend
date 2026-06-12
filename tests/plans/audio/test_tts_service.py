import struct
from unittest.mock import MagicMock, patch

import pytest

from pecha_api.plans.audio.tts_service import (
    _convert_to_wav,
    _parse_audio_mime_type,
    generate_tts_audio,
)
from pecha_api.plans.plans_enums import PlanAudioType


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


@patch("google.genai.Client")
@patch("pecha_api.plans.audio.tts_service.get", return_value="test-api-key")
def test_generate_tts_audio_success(mock_get, mock_client_cls):
    audio_data = b"\x00\x01\x02\x03"
    inline_data = MagicMock(data=audio_data, mime_type="audio/L16;rate=24000")
    part = MagicMock(inline_data=inline_data)
    content = MagicMock(parts=[part])
    candidate = MagicMock(content=content)
    response = MagicMock(candidates=[candidate])

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = response
    mock_client_cls.return_value = mock_client

    result = generate_tts_audio(content="Hello world", audio_type=PlanAudioType.RECITATION)

    assert result[:4] == b"RIFF"
    assert result.endswith(audio_data)
    mock_client.models.generate_content.assert_called_once()


@patch("google.genai.Client")
@patch("pecha_api.plans.audio.tts_service.get", return_value="test-api-key")
def test_generate_tts_audio_raises_when_no_candidates(mock_get, mock_client_cls):
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(candidates=[])
    mock_client_cls.return_value = mock_client

    with pytest.raises(RuntimeError, match="no audio data"):
        generate_tts_audio(content="Hello world", audio_type=PlanAudioType.RECITATION)
