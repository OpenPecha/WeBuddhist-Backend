from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from beanie import Document
from pydantic import BaseModel, Field, field_validator
from pymongo import ASCENDING, IndexModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TextAudio(Document):
    text_id: str
    text_title: str
    audio_key: str
    file_name: str
    # Editable display name, defaulting to file_name at upload time. Optional
    # so documents written before this field existed still load; callers
    # should read via TextAudioResponse, which falls back to file_name.
    name: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_ms: Optional[int] = None
    created_by: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    # S3 keys that were displaced but failed to delete. Retried
    # opportunistically when this audio is deleted.
    pending_cleanup_keys: List[str] = Field(default_factory=list)

    class Settings:
        collection = "text_audio"
        # A text can have many audios now. The compound index (whose name
        # differs from the old unique text_id_1 index) lets init_beanie's
        # allow_index_dropping remove the old unique constraint on startup.
        indexes = [
            IndexModel([("text_id", ASCENDING), ("created_at", ASCENDING)]),
        ]


class TextAudioOtr(Document):
    audio_id: str
    text_id: str
    name: str
    file_name: str
    content: Dict[str, Any]
    created_by: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    class Settings:
        collection = "text_audio_otr"
        indexes = [
            IndexModel([("audio_id", ASCENDING), ("name", ASCENDING)], unique=True),
        ]


class TextAudioResponse(BaseModel):
    id: str
    text_id: str
    text_title: str
    audio_key: str
    audio_url: str
    name: str
    file_name: str
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_ms: Optional[int] = None
    updated_at: datetime


class UpdateTextAudioNameRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Audio name is required.")
        return stripped


class TextAudioOtrResponse(BaseModel):
    id: str
    audio_id: str
    name: str
    file_name: str
    updated_at: datetime
