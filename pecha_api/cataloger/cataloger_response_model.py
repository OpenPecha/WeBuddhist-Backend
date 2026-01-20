from pydantic import BaseModel, Field
from typing import Dict, List

class Metadata(BaseModel):
    text_id: str
    title: Dict[str, str] = Field(default_factory=dict)
    language: str

class Relation(BaseModel):
    relation_type: str
    status: bool
    metadata: Metadata

class CatalogedTextsDetailsResponse(BaseModel):
    title: Dict[str, str] = Field(default_factory=dict)
    category_id: str
    status: bool
    relations: List[Relation]

class ExternalPechaTextResponse(BaseModel):
    title: Dict[str, str] = Field(default_factory=dict)
    type: str
    category_id: str

class ExternalPechaInstanceRelatedResponse(BaseModel):
    title: Dict[str, str] = Field(default_factory=dict)
    text_id: str
    language: str
    relation_type: str

class CatalogedTexts(BaseModel):
    text_id: str
    title: Dict[str, str] = Field(default_factory=dict)
    language: str
    type: str
    status: bool

class CatalogedTextsResponse(BaseModel):
    texts: List[CatalogedTexts]
