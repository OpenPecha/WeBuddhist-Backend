import enum
from sqlalchemy import Enum


class AccumulatorType(enum.Enum):
    PRESET = "preset"
    USER = "user_created"


AccumulatorTypeEnum = Enum(
    AccumulatorType,
    name="accumulatortype",
    values_callable=lambda x: [e.value for e in x]
)
