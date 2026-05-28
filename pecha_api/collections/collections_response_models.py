from typing import List, Optional

from pydantic import BaseModel


class CollectionModel(BaseModel):
    id: str
    pecha_collection_id: Optional[str] = None
    title: str
    description: str
    language: str
    slug: str
    has_child: bool

class V2CollectionModel(BaseModel):
    id: str
    title: str

class Pagination(BaseModel):
    total: int
    skip: int
    limit: int

class CollectionsResponse(BaseModel):
    parent: Optional[CollectionModel]
    pagination: Pagination
    collections: List[CollectionModel]
    
    
