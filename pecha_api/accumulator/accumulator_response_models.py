from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from .accumulator_enums import AccumulatorType
from ..plans.plans_enums import LanguageCode


class AccumulatorMetadataDTO(BaseModel):
    """Per-language name/description for an accumulator."""
    language: LanguageCode
    name: str
    description: Optional[str] = None


class PresetMantraDTO(BaseModel):
    """Mantra content for a preset, resolved for a single language."""
    id: UUID
    mantra: str
    title: Optional[str] = None
    pronunciation: Optional[str] = None
    audio_url: Optional[str] = None
    mala_image_id: Optional[UUID] = None
    mala_image_url: Optional[str] = Field(
        None,
        description="Presigned S3 URL for the mantra's default mala image",
    )


class AccumulatorDTO(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    parent_id: Optional[UUID] = Field(None, description="The preset this accumulator was created from")
    type: AccumulatorType
    target_count: Optional[int] = None
    current_count: int
    text_id: Optional[UUID] = None
    mantra_id: Optional[UUID] = None
    mala_image_id: Optional[UUID] = None
    mala_image_url: Optional[str] = Field(None, description="Presigned S3 URL for the chosen mala image (None when no image is set)")
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
    mantra: Optional[PresetMantraDTO] = None
    mala_image_id: Optional[UUID] = None
    mala_image_url: Optional[str] = Field(None, description="Presigned S3 URL for the chosen mala image (None when no image is set)")
    metadata: List[AccumulatorMetadataDTO] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


class PublicAccumulatorsResponse(BaseModel):
    accumulators: List[PublicAccumulatorDTO]
    total: int
    skip: int
    limit: int


class CreateAccumulatorRequest(BaseModel):
    parent_id: UUID = Field(..., description="Id of the public preset the user tapped (the `id` from GET /accumulators/presets); its fields are copied into the new user accumulator and stored as the new row's parent_id")


class UpdateAccumulatorRequest(BaseModel):
    target_count: Optional[int] = None
    current_count: Optional[int] = Field(None, ge=0, description="New absolute current count")
    text_id: Optional[UUID] = None
    mantra_id: Optional[UUID] = None


class UpdateMalaImageRequest(BaseModel):
    mala_image_id: UUID = Field(..., description="Id of the mala image (from the mala_images catalog) to set on the accumulator")


class AccumulatorSessionDTO(BaseModel):
    count: int
    created_at: datetime


class AccumulatorHistoryDTO(BaseModel):
    accumulator_id: UUID
    parent_id: Optional[UUID] = Field(None, description="The preset this accumulator was created from")
    target_count: Optional[int] = None
    current_count: int
    total_counted: int
    mala_image_id: Optional[UUID] = None
    mala_image_url: Optional[str] = Field(None, description="Presigned S3 URL for the chosen mala image (None when no image is set)")
    metadata: List[AccumulatorMetadataDTO] = []
    sessions: List[AccumulatorSessionDTO]


class AccumulatorHistoryResponse(BaseModel):
    accumulators: List[AccumulatorHistoryDTO]
    total: int
    skip: int
    limit: int


class AccumulatorGroupDTO(BaseModel):
    """Group accumulator information with user's total count."""
    group_accumulator_id: UUID
    group_id: UUID
    title: Optional[str] = None
    target_count: Optional[int] = None
    user_total_count: int = Field(..., description="Authenticated user's total count for this group accumulator")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime


class AccumulatorGroupsResponse(BaseModel):
    """Response for groups using a specific accumulator."""
    groups: List[AccumulatorGroupDTO]
    total: int
    skip: int
    limit: int
