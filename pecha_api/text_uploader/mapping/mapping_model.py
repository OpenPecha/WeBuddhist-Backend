from pydantic import BaseModel
from typing import List

class TriggerMappingPayload(BaseModel):
    text_ids: List[str]
    source: str
    destination: str

