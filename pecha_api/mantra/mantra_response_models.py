from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

from ..plans.plans_enums import LanguageCode


class MantraMetadataDTO(BaseModel):
    id: UUID
    text: str
    meaning: Optional[str] = None
    transliteration: Optional[str] = None
    language: LanguageCode

    class Config:
        from_attributes = True


class MantraDTO(BaseModel):
    id: UUID
    audio_url: Optional[str] = None
    mala_image_id: Optional[UUID] = None
    mala_image_url: Optional[str] = None
    metadata: List[MantraMetadataDTO] = []

    class Config:
        from_attributes = True


class MantraResponse(BaseModel):
    mantras: List[MantraDTO]
