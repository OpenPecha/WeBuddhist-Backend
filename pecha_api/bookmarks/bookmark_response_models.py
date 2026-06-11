from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional
from datetime import datetime


class CreateBookmarkRequest(BaseModel):
    text_id: UUID
    verse_id: str
    name: Optional[str] = None


class BookmarkDTO(BaseModel):
    id: UUID
    text_id: UUID
    verse_id: str
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class BookmarksResponse(BaseModel):
    bookmarks: List[BookmarkDTO]
