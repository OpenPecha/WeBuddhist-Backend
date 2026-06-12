from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from ..plans.plans_enums import LanguageCode


class MantraDTO(BaseModel):
    id: UUID
    audio_url: Optional[str] = None
    text: str
    meaning: Optional[str] = None
    language: LanguageCode

    class Config:
        from_attributes = True


class MantraResponse(BaseModel):
    mantras: List[MantraDTO]
