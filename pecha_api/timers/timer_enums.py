import enum
from sqlalchemy import Enum


class TimerType(enum.Enum):
    PRESET = "preset"
    USER = "user_created"


TimerTypeEnum = Enum(TimerType)
