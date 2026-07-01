from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

from pecha_api.plans.media.media_response_models import ImageUrlModel


class GroupAccumulatorMemberSortBy(str, Enum):
    TOTAL = "total"
    TODAY = "today"


class CreateGroupAccumulatorRequest(BaseModel):
    accumulator_id: Optional[UUID] = None
    title: Optional[str] = None
    image_key: Optional[str] = None
    target_count: Optional[int] = Field(None, ge=1)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class UpdateGroupAccumulatorRequest(BaseModel):
    accumulator_id: Optional[UUID] = None
    title: Optional[str] = None
    image_key: Optional[str] = None
    target_count: Optional[int] = Field(None, ge=1)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class GroupAccumulatorDTO(BaseModel):
    id: UUID
    preset_accumulator_id: Optional[UUID] = Field(
        None,
        description="ID of the linked preset accumulator, if any",
    )
    group_id: UUID
    title: Optional[str] = None
    image: Optional[ImageUrlModel] = None
    image_key: Optional[str] = None
    target_count: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_joined: Optional[bool] = Field(
        None,
        description="Whether the authenticated user has joined (null when unauthenticated)",
    )
    member_count: int = Field(
        0,
        description="Number of users who joined this group accumulator",
    )
    created_at: datetime
    updated_at: Optional[datetime] = None


class GroupAccumulatorsResponse(BaseModel):
    accumulators: List[GroupAccumulatorDTO]
    total: int
    skip: int
    limit: int


class SubmitGroupCountRequest(BaseModel):
    current_count: int = Field(..., ge=0, description="User's new absolute current count")


class GroupAccumulatorHistoryItemDTO(BaseModel):
    id: Optional[UUID] = Field(None, description="History entry ID. None if no history was created (e.g., zero delta)")
    user_id: UUID
    count: int
    created_at: datetime


class GroupAccumulatorDetailUserDTO(BaseModel):
    total_count: int = Field(..., description="Authenticated user's count for the active session")
    today_count: int = Field(..., description="Authenticated user's count for today in the request timezone")
    username: Optional[str] = None
    image: Optional[str] = Field(None, description="Presigned URL for the user's avatar")
    fullname: str = Field(..., description="User's display name")


class GroupAccumulatorDetailDTO(BaseModel):
    id: UUID
    preset_accumulator_id: Optional[UUID] = Field(
        None,
        description="ID of the linked preset accumulator, if any",
    )
    group_id: UUID
    title: Optional[str] = None
    image: Optional[ImageUrlModel] = None
    image_key: Optional[str] = None
    target_count: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_count: int = Field(..., description="Total lifetime count from all users")
    total_today_count: int = Field(0, description="Total count from all users for today in the request timezone")
    user: Optional[GroupAccumulatorDetailUserDTO] = Field(
        None,
        description="Authenticated user's profile and counts (null when unauthenticated)",
    )
    is_joined: Optional[bool] = Field(
        None,
        description="Whether the authenticated user has joined (null when unauthenticated)",
    )
    member_count: int = Field(0, description="Number of users who joined this group accumulator")
    created_at: datetime
    updated_at: Optional[datetime] = None


class GroupAccumulatorHistoryResponse(BaseModel):
    group_accumulator: GroupAccumulatorDetailDTO
    history: List[GroupAccumulatorHistoryItemDTO]
    total: int
    skip: int
    limit: int


class GroupAccumulatorMemberDTO(BaseModel):
    user_id: UUID
    username: Optional[str] = None
    fullname: str
    avatar_url: Optional[str] = None
    joined_at: datetime
    total_count: int = Field(0, description="Member's lifetime contribution count")
    today_count: int = Field(0, description="Member's contribution count for today in the request timezone")


class GroupAccumulatorMembersResponse(BaseModel):
    members: List[GroupAccumulatorMemberDTO]
    member_count: int = Field(..., description="Total number of users who joined this group accumulator")
    total: int
    skip: int
    limit: int


class GroupAccumulatorContributionDTO(BaseModel):
    id: UUID
    count: int
    created_at: datetime


class GroupAccumulatorUserSessionDTO(BaseModel):
    id: UUID = Field(..., description="User participation session ID")
    is_active: bool = Field(..., description="True when this is the user's current non-reset session")
    total_counted: int = Field(..., description="Total count contributed during this session")
    created_at: datetime
    deleted_at: Optional[datetime] = Field(None, description="When the user reset this session")
    contributions: List[GroupAccumulatorContributionDTO] = Field(
        default_factory=list,
        description="Individual count submissions during this session",
    )


class GroupAccumulatorUserSessionsResponse(BaseModel):
    group_accumulator: GroupAccumulatorDTO
    sessions: List[GroupAccumulatorUserSessionDTO]
    total: int
    skip: int
    limit: int
