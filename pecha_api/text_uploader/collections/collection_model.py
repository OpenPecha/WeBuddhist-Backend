from pydantic import BaseModel
from typing import Optional, Dict

class CollectionPayload(BaseModel):
    pecha_collection_id: Optional[str] = None
    slug: str
    titles: Dict[str, str]
    descriptions: Dict[str, str]
    parent_id: Optional[str]


    