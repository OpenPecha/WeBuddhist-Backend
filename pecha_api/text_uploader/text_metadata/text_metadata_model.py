from pydantic import BaseModel
from typing import Optional, List, Dict


class TextGroupPayload(BaseModel):
  
    pecha_text_id: Optional[str] = None
    title: str | None = None
    language: Optional[str] = None
    isPublished: bool = False
    group_id: Optional[str] = None
    published_by: Optional[str] = None
    type: str
    categories: Optional[List[str]] = None
    views: Optional[int] = 0
    source_link: Optional[str] = None
    ranking: Optional[int] = None
    license: Optional[str] = None

class CriticalInstance(BaseModel):
    id: str
    bdrc: Optional[str] = None
    wiki: Optional[str] = None
    type: str
    source: str
    colophon: Optional[str] = None
    incipit_title: Optional[str] = None
    alt_incipit_titles: List[str] = []
    biblography_annotation: Optional[str] = None

class CriticalInstanceResponse(BaseModel):
    critical_instances: List[CriticalInstance]

class TextInstanceIds(BaseModel):
    new_text: Dict[str, str]
    all_text: Dict[str, str]

