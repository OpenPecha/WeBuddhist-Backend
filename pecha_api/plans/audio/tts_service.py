import struct

from pecha_api.config import get
from pecha_api.plans.audio.audio_prompt import build_tts_prompt, DEFAULT_VOICE_NAME
from pecha_api.plans.plans_enums import PlanAudioType


def generate_tts_audio(
    content: str,
    audio_type: PlanAudioType,
) -> bytes:
    if not content.strip():
        raise ValueError("Content cannot be empty")

    prompt = build_tts_prompt(transcript=content, audio_type=audio_type)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=get("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            ),
        ],
        config=types.GenerateContentConfig(
            temperature=1,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=DEFAULT_VOICE_NAME
                    )
                )
            ),
        ),
    )

    if not response.candidates or not response.candidates[0].content.parts:
        raise RuntimeError("TTS generation returned no audio data")

    part = response.candidates[0].content.parts[0]
    if not part.inline_data or not part.inline_data.data:
        raise RuntimeError("TTS generation returned no audio data")

    audio_data = part.inline_data.data
    mime_type = part.inline_data.mime_type or "audio/L16;rate=24000"

    return _convert_to_wav(audio_data, mime_type)


def _convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    params = _parse_audio_mime_type(mime_type)
    bits_per_sample = params["bits_per_sample"]
    sample_rate = params["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    return header + audio_data


def _parse_audio_mime_type(mime_type: str) -> dict:
    bits_per_sample = 16
    rate = 24000

    parts = mime_type.split(";")
    for param in parts:
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate = int(param.split("=", 1)[1])
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass

    return {"bits_per_sample": bits_per_sample, "rate": rate}
