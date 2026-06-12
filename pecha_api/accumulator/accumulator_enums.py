import enum
from sqlalchemy import Enum


class AccumulatorType(enum.Enum):
    PRESET = "preset"
    USER = "user_created"


AccumulatorTypeEnum = Enum(AccumulatorType)
