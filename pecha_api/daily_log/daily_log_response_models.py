from pydantic import BaseModel


class UserStreakResponse(BaseModel):
    streak: int
