import httpx

from pecha_api.config import get
from pecha_api.plans.plans_enums import MonlamVoiceName

DEFAULT_MONLAM_VOICE_NAME = MonlamVoiceName.DOLKAR_LHASA_FEMALE.value


def generate_monlam_tts_audio(content: str, voice_name: str | None = None) -> bytes:
    if not content.strip():
        raise ValueError("Content cannot be empty")

    base_url = get("MONLAM_BASE_URL").rstrip("/")
    api_key = get("MONLAM_API_KEY")
    if not api_key:
        raise RuntimeError("MONLAM_API_KEY is not configured")

    payload = {
        "text": content,
        "provider": get("MONLAM_TTS_PROVIDER"),
        "model_name": get("MONLAM_TTS_MODEL_NAME"),
    }
    resolved_voice_name = voice_name or get("MONLAM_TTS_VOICE_NAME") or DEFAULT_MONLAM_VOICE_NAME
    payload["voice_name"] = resolved_voice_name

    try:
        response = httpx.post(
            f"{base_url}/api/v1/text-to-speech/stream",
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=300.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        raise RuntimeError(
            f"Monlam TTS request failed with status {exc.response.status_code}: {detail}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError(f"Monlam TTS request failed: {exc}") from exc

    wav_bytes = response.content
    if not wav_bytes or wav_bytes[:4] != b"RIFF":
        raise RuntimeError("Monlam TTS generation returned invalid audio data")

    return wav_bytes
