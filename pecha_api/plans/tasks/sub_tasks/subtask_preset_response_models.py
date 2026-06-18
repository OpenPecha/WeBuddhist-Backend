from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class PresetRequest(BaseModel):
    version_id: str
    language: str


class PresetResponse(BaseModel):
    id: str
    subtask_id: str
    version_id: str
    language: str
    created_at: str
    created_by: str
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
