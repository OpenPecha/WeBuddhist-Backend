from typing import List

from pydantic import BaseModel


class UserStreakResponse(BaseModel):
    streak: int


class StreakStats(BaseModel):
    current: int
    highest: int
    week: List[int]


class UserStatsResponse(BaseModel):
    streak: StreakStats
    total_timer: int
    total_accumulated: int
    total_practice_days: int
