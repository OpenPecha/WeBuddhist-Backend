from typing import List

from pydantic import BaseModel


class LanguageDTO(BaseModel):
    code: str
    name: str
    native_name: str
    enabled: bool


class LanguageListResponse(BaseModel):
    languages: List[LanguageDTO]
