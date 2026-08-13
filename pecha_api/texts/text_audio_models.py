from datetime import datetime, timezone
from typing import List, Optional

from beanie import Document, Indexed
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TextAudio(Document):
    text_id: Indexed(str, unique=True)
    text_title: str
    audio_key: str
    file_name: str
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_ms: Optional[int] = None
    created_by: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    # S3 keys that were displaced (by replacement) but failed to delete.
    # Retried opportunistically on the next upload/delete for this text.
    pending_cleanup_keys: List[str] = Field(default_factory=list)

    class Settings:
        collection = "text_audio"


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
