from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from starlette import status

from pecha_api.plans.audio.worker_client import generate_audio_from_text
from pecha_api.plans.plans_enums import MonlamVoiceName, PlanAudioType

tts_test_router = APIRouter(tags=["CMS TTS Test"])

_TTS_TEST_HTML = Path(__file__).resolve().parent / "static" / "tts_test.html"


class PreviewTtsRequest(BaseModel):
    text: str = Field(min_length=1)
    language: str
    type: PlanAudioType = PlanAudioType.TEXT_READING
    voice_name: MonlamVoiceName = MonlamVoiceName.DOLKAR_LHASA_FEMALE


class PreviewTtsResponse(BaseModel):
    audio_url: str
    audio_duration_ms: int
    s3_key: str


@tts_test_router.get("/view", include_in_schema=False)
def get_tts_test_view() -> FileResponse:
    return FileResponse(_TTS_TEST_HTML, media_type="text/html")


@tts_test_router.post(
    "/preview",
    include_in_schema=False,
    response_model=PreviewTtsResponse,
)
async def preview_tts(request: PreviewTtsRequest) -> PreviewTtsResponse:
    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content cannot be empty",
        )

    try:
        result = await generate_audio_from_text(
            text=request.text,
            language=request.language,
            audio_type=request.type,
            voice_name=request.voice_name,
            s3_key_prefix="audio/tts-preview",
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Worker TTS request failed: {exc}",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return PreviewTtsResponse(**result)
