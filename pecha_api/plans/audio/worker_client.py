import httpx
from typing import Optional
from pecha_api.config import get
from pecha_api.plans.plans_enums import PlanAudioType, MonlamVoiceName


async def generate_audio_from_text(
    text: str,
    language: str,
    audio_type: PlanAudioType = PlanAudioType.TEXT_READING,
    voice_name: MonlamVoiceName = MonlamVoiceName.DOLKAR_LHASA_FEMALE,
    s3_key_prefix: Optional[str] = None,
) -> dict:

    worker_url = get("WORKER_API_URL")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{worker_url}/audio/generate",
            json={
                "text": text,
                "language": language,
                "type": audio_type.value if hasattr(audio_type, 'value') else audio_type,
                "voice_name": voice_name.value if hasattr(voice_name, 'value') else voice_name,
                "s3_key_prefix": s3_key_prefix,
            },
        )
        response.raise_for_status()
        return response.json()
