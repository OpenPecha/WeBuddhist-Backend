from pydantic import BaseModel
from ..plans.plans_enums import LanguageCode


class UpdateLanguageRequest(BaseModel):
    language: LanguageCode


class UserMetadataDTO(BaseModel):
    language: LanguageCode
    timezone: str

    class Config:
        from_attributes = True
