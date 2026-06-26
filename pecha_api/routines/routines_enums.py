import enum
from sqlalchemy import Enum


class SessionType(enum.Enum):
    PLAN = "PLAN"
    SERIES = "SERIES"
    RECITATION = "RECITATION"
    RECITATION_COLLECTION = "RECITATION_COLLECTION"
    TIMER = "TIMER"
    ACCUMULATOR = "ACCUMULATOR"
    
SessionTypeEnum = Enum(SessionType)