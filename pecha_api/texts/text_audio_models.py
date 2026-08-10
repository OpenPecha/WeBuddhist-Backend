from datetime import datetime, timezone
from typing import Optional

from beanie import Document
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TextAudio(Document):
    text_id: str
    text_title: str
    audio_key: str
    file_name: str
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_ms: Optional[int] = None
    created_by: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        collection = "text_audio"
        indexes = [
            "text_id",
        ]


class TextAudioResponse(BaseModel):
    text_id: str
    text_title: str
    audio_key: str
    audio_url: str
    file_name: str
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_ms: Optional[int] = None
    updated_at: datetime
