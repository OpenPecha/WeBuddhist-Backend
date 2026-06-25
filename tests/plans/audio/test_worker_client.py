import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx

from pecha_api.plans.audio.worker_client import generate_audio_from_text
from pecha_api.plans.plans_enums import PlanAudioType, MonlamVoiceName


@pytest.mark.asyncio
async def test_generate_audio_from_text_success():
    """Test successful audio generation via worker API"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "s3_key": "audio/plan_subtasks/test.wav",
        "audio_url": "https://s3.example.com/test.wav",
        "audio_duration_ms": 3000,
    }
    mock_response.raise_for_status = MagicMock()

    with patch("pecha_api.plans.audio.worker_client.get", return_value="http://worker-api:8001/api/v1"), \
         patch("httpx.AsyncClient") as mock_client:
        
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_client.return_value = mock_async_client

        result = await generate_audio_from_text(
            text="Test content",
            language="bo",
            audio_type=PlanAudioType.TEXT_READING,
            voice_name=MonlamVoiceName.DOLKAR_LHASA_FEMALE,
            s3_key_prefix="audio/plan_subtasks/test",
        )

        mock_async_client.post.assert_called_once_with(
            "http://worker-api:8001/api/v1/audio/generate",
            json={
                "text": "Test content",
                "language": "bo",
                "type": "TEXT_READING",
                "voice_name": "dolkar_lhasa_female",
                "s3_key_prefix": "audio/plan_subtasks/test",
            },
        )
        assert result == {
            "s3_key": "audio/plan_subtasks/test.wav",
            "audio_url": "https://s3.example.com/test.wav",
            "audio_duration_ms": 3000,
        }


@pytest.mark.asyncio
async def test_generate_audio_from_text_with_defaults():
    """Test audio generation with default parameters"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "s3_key": "audio/default.wav",
        "audio_url": "https://s3.example.com/default.wav",
        "audio_duration_ms": 1500,
    }
    mock_response.raise_for_status = MagicMock()

    with patch("pecha_api.plans.audio.worker_client.get", return_value="http://localhost:8001/api/v1"), \
         patch("httpx.AsyncClient") as mock_client:
        
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_client.return_value = mock_async_client

        result = await generate_audio_from_text(
            text="Default test",
            language="en",
        )

        call_args = mock_async_client.post.call_args
        assert call_args[1]["json"]["type"] == "TEXT_READING"
        assert call_args[1]["json"]["voice_name"] == "dolkar_lhasa_female"
        assert call_args[1]["json"]["s3_key_prefix"] is None
        assert result["s3_key"] == "audio/default.wav"


@pytest.mark.asyncio
async def test_generate_audio_from_text_with_recitation_type():
    """Test audio generation with RECITATION audio type"""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "s3_key": "audio/recitation.wav",
        "audio_url": "https://s3.example.com/recitation.wav",
        "audio_duration_ms": 5000,
    }
    mock_response.raise_for_status = MagicMock()

    with patch("pecha_api.plans.audio.worker_client.get", return_value="http://worker:8001/api/v1"), \
         patch("httpx.AsyncClient") as mock_client:
        
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_client.return_value = mock_async_client

        result = await generate_audio_from_text(
            text="Recitation text",
            language="bo",
            audio_type=PlanAudioType.RECITATION,
            voice_name=MonlamVoiceName.YANGCHEN_LHASA_FEMALE,
        )

        call_args = mock_async_client.post.call_args
        assert call_args[1]["json"]["type"] == "RECITATION"
        assert call_args[1]["json"]["voice_name"] == "yangchen_lhasa_female"


@pytest.mark.asyncio
async def test_generate_audio_from_text_raises_on_http_error():
    """Test that HTTP errors are raised properly"""
    with patch("pecha_api.plans.audio.worker_client.get", return_value="http://worker:8001/api/v1"), \
         patch("httpx.AsyncClient") as mock_client:
        
        mock_async_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=MagicMock(),
            response=MagicMock(status_code=500),
        )
        mock_async_client.post.return_value = mock_response
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_client.return_value = mock_async_client

        with pytest.raises(httpx.HTTPStatusError):
            await generate_audio_from_text(
                text="Error test",
                language="bo",
            )


@pytest.mark.asyncio
async def test_generate_audio_from_text_uses_correct_timeout():
    """Test that the client uses the correct timeout"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"s3_key": "test.wav", "audio_url": "url", "audio_duration_ms": 1000}
    mock_response.raise_for_status = MagicMock()

    with patch("pecha_api.plans.audio.worker_client.get", return_value="http://worker:8001/api/v1"), \
         patch("httpx.AsyncClient") as mock_client:
        
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_client.return_value = mock_async_client

        await generate_audio_from_text(text="Test", language="bo")

        mock_client.assert_called_once_with(timeout=120.0)
