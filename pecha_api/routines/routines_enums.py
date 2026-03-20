import enum
from sqlalchemy import Enum


class SessionType(enum.Enum):
    PLAN = "PLAN"
    RECITATION = "RECITATION"
    
SessionTypeEnum = Enum(SessionType)