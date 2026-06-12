from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from starlette import status

from pecha_api.plans.audio.tts_service import generate_tts_audio
from pecha_api.plans.plans_enums import MonlamVoiceName, PlanAudioType

tts_test_router = APIRouter(tags=["TTS Test"])

_TTS_TEST_HTML = Path(__file__).resolve().parent / "static" / "tts_test.html"


class PreviewTtsRequest(BaseModel):
    text: str = Field(min_length=1)
    language: str
    type: PlanAudioType = PlanAudioType.TEXT_READING
    voice_name: MonlamVoiceName = MonlamVoiceName.DOLKAR_LHASA_FEMALE


@tts_test_router.get("/view", include_in_schema=False)
def get_tts_test_view() -> FileResponse:
    return FileResponse(_TTS_TEST_HTML, media_type="text/html")


@tts_test_router.post("/preview", include_in_schema=False)
def preview_tts(request: PreviewTtsRequest) -> Response:
    try:
        wav_bytes = generate_tts_audio(
            content=request.text,
            audio_type=request.type,
            language=request.language,
            voice_name=request.voice_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return Response(content=wav_bytes, media_type="audio/wav")
