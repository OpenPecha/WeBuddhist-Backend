from pydantic import BaseModel, field_validator
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from pecha_api.bookmarks.bookmark_enums import BookmarkType


class CreateBookmarkRequest(BaseModel):
    type: BookmarkType
    source_id: str
    name: Optional[str] = None

    @field_validator("source_id")
    @classmethod
    def _validate_source_id(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError("source_id must not be empty")

        bookmark_type = info.data.get("type")
        if bookmark_type is not None and bookmark_type != BookmarkType.VERSE:
            try:
                return str(UUID(value))
            except ValueError:
                raise ValueError(f"source_id must be a valid UUID for type {bookmark_type.value}")
        return value


class BookmarkDTO(BaseModel):
    id: UUID
    type: BookmarkType
    source_id: str
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    text_id: Optional[str] = None
    text_title: Optional[str] = None
    segment_id: Optional[str] = None
    verse_id: Optional[str] = None
    segment_content: Optional[str] = None


class BookmarksResponse(BaseModel):
    bookmarks: List[BookmarkDTO]
