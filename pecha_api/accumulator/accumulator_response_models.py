from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from .accumulator_enums import AccumulatorType
from ..plans.plans_enums import LanguageCode


class AccumulatorMetadataDTO(BaseModel):
    """Per-language name/description plus the chosen mala image. mala_image_url
    is a presigned S3 URL ready for the frontend (None when no image is set)."""
    language: LanguageCode
    name: str
    description: Optional[str] = None
    mala_image_id: Optional[UUID] = None
    mala_image_url: Optional[str] = None


class AccumulatorDTO(BaseModel):
    id: UUID
    user_id: UUID
    group_id: Optional[UUID] = None
    parent_id: Optional[UUID] = Field(None, description="The preset this accumulator was created from")
    type: AccumulatorType
    target_count: Optional[int] = None
    current_count: int
    text_id: Optional[UUID] = None
    mantra_id: Optional[UUID] = None
    metadata: List[AccumulatorMetadataDTO] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class AccumulatorsResponse(BaseModel):
    accumulators: List[AccumulatorDTO]
    total: int
    skip: int
    limit: int


class PublicAccumulatorDTO(BaseModel):
    """Preset shape for the public list endpoint. Exposes the row `id` (the
    value the app sends as preset_id to POST /accumulators/user) and omits
    user_id so other users' ids are not disclosed. group_id is kept for future
    CMS grouping."""
    id: UUID
    group_id: Optional[UUID] = None
    type: AccumulatorType
    target_count: Optional[int] = None
    current_count: int
    text_id: Optional[UUID] = None
    mantra_id: Optional[UUID] = None
    metadata: List[AccumulatorMetadataDTO] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class PublicAccumulatorsResponse(BaseModel):
    accumulators: List[PublicAccumulatorDTO]
    total: int
    skip: int
    limit: int


class CreateAccumulatorRequest(BaseModel):
    preset_id: UUID = Field(..., description="Id of the public preset the user tapped; its fields are copied into the new user accumulator")


class UpdateAccumulatorRequest(BaseModel):
    target_count: Optional[int] = None
    current_count: Optional[int] = Field(None, ge=0, description="New absolute current count")
    text_id: Optional[UUID] = None
    mantra_id: Optional[UUID] = None


class UpdateMalaImageRequest(BaseModel):
    mala_image_id: UUID = Field(..., description="Id of the mala image (from the mala_images catalog) to set")
    language: LanguageCode = Field(..., description="Language of the accumulator metadata row to update")


class AccumulatorSessionDTO(BaseModel):
    count: int
    created_at: datetime


class AccumulatorHistoryDTO(BaseModel):
    accumulator_id: UUID
    parent_id: Optional[UUID] = Field(None, description="The preset this accumulator was created from")
    target_count: Optional[int] = None
    current_count: int
    total_counted: int
    metadata: List[AccumulatorMetadataDTO] = []
    sessions: List[AccumulatorSessionDTO]


class AccumulatorHistoryResponse(BaseModel):
    accumulators: List[AccumulatorHistoryDTO]
    total: int
    skip: int
    limit: int
