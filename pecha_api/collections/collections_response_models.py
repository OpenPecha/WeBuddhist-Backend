from typing import Dict, List, Optional

from pydantic import BaseModel


class CreateCollectionRequest(BaseModel):
    pecha_collection_id: Optional[str] = None
    slug: str
    titles: Dict[str, str]
    descriptions: Dict[str, str]
    parent_id: Optional[str]

class UpdateCollectionRequest(BaseModel):
    titles: Dict[str, str]
    descriptions: Dict[str, str]

class CollectionModel(BaseModel):
    id: str
    pecha_collection_id: Optional[str] = None
    title: str
    description: str
    language: str
    slug: str
    has_child: bool

class Pagination(BaseModel):
    total: int
    skip: int
    limit: int

class CollectionsResponse(BaseModel):
    parent: Optional[CollectionModel]
    pagination: Pagination
    collections: List[CollectionModel]
    
    
