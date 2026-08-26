from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AnalyticsDateRangeDTO(BaseModel):
    start_date: date
    end_date: date


class AnalyticsUserStatsDTO(BaseModel):
    total_users: int = Field(ge=0)
    new_users_this_month: int = Field(ge=0)
    new_users_in_range: int = Field(ge=0)


class AnalyticsTimePointDTO(BaseModel):
    date: date
    new_users: int = Field(ge=0)
    joins: int = Field(ge=0)
    completions: int = Field(ge=0)


class AnalyticsTopPlanDTO(BaseModel):
    id: UUID
    title: str
    series_id: Optional[UUID] = None
    series_name: Optional[str] = None
    join_count: int = Field(ge=0)
    completion_count: int = Field(ge=0)


class AnalyticsOverviewResponse(BaseModel):
    date_range: AnalyticsDateRangeDTO
    users: AnalyticsUserStatsDTO
    top_plans: List[AnalyticsTopPlanDTO]
    timeline: List[AnalyticsTimePointDTO]
    generated_at: datetime
