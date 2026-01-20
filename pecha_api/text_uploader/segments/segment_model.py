from pydantic import BaseModel
from typing import Any, Optional

class Segment(BaseModel):
    content: str
    type: str

class SegmentModel(BaseModel):
    text_id: str
    segments: list[Segment]

class ManifestationModel(BaseModel):
    job_id: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None