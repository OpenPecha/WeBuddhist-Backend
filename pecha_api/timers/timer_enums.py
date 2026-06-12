import enum
from sqlalchemy import Enum


class TimerType(enum.Enum):
    PRESET = "preset"
    USER = "user_created"


# Use values_callable to ensure PostgreSQL receives the enum values ("preset", "user_created")
# instead of the enum names ("PRESET", "USER")
TimerTypeEnum = Enum(
    TimerType,
    values_callable=lambda x: [e.value for e in x]
)
